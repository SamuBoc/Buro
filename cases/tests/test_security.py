import os

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_ESTUDIANTE, ROLE_PROFESOR
from beneficiary.models import Beneficiary
from cases.models import Case, CaseAuditLog, CaseDocument
from core.encryption import compute_hmac, decrypt, encrypt, verify_integrity

TEST_ENCRYPTION_KEY = 'c2VjcmV0a2V5Zm9ydGVzdGluZ3B1cnBvc2VzMTIzNDU2Nzg='


def _make_user(username, role):
    user = User.objects.create_user(username, password='testpass123')
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    return user


def _make_case(student=None):
    beneficiary = Beneficiary.objects.create(
        name='Beneficiario Seguridad',
        location='Cali',
        phone='3001234567',
        email='seg@test.com',
        colombian_identification='123456789',
    )
    return Case.objects.create(
        sala=Case.ROOM_CIVIL,
        description='Caso de prueba seguridad',
        beneficiary=beneficiary,
        assigned_student=student,
        status=Case.STATUS_COMPLETE,
    )


@override_settings(
    ENCRYPTION_KEY='c2VjcmV0a2V5Zm9ydGVzdGluZ3B1cnBvc2VzMTIzNDU2Nzg='
)
class EncryptionUtilsTest(TestCase):

    def test_encrypt_returns_different_value(self):
        original = '123456789'
        encrypted = encrypt(original)
        self.assertNotEqual(original, encrypted)

    def test_decrypt_returns_original_value(self):
        original = '3001234567'
        self.assertEqual(decrypt(encrypt(original)), original)

    def test_encrypt_empty_string_returns_empty(self):
        self.assertEqual(encrypt(''), '')

    def test_decrypt_empty_string_returns_empty(self):
        self.assertEqual(decrypt(''), '')

    def test_decrypt_invalid_token_returns_empty(self):
        self.assertEqual(decrypt('token_invalido'), '')

    def test_hmac_same_value_same_result(self):
        value = 'dato_critico'
        self.assertEqual(compute_hmac(value), compute_hmac(value))

    def test_verify_integrity_valid(self):
        value = 'dato_critico'
        self.assertTrue(verify_integrity(value, compute_hmac(value)))

    def test_verify_integrity_tampered(self):
        value = 'dato_critico'
        self.assertFalse(verify_integrity(value + '_modificado', compute_hmac(value)))


@override_settings(
    ENCRYPTION_KEY='c2VjcmV0a2V5Zm9ydGVzdGluZ3B1cnBvc2VzMTIzNDU2Nzg=',
    MEDIA_ROOT='/tmp/test_media_hu35/',
)
class EncryptedFieldTest(TestCase):

    def test_colombian_identification_stored_encrypted(self):
        beneficiary = Beneficiary.objects.create(
            name='Test Cifrado',
            location='Cali',
            phone='3001111111',
            email='cifrado@test.com',
            colombian_identification='987654321',
        )
        raw = Beneficiary.objects.filter(
            pk=beneficiary.pk
        ).values('colombian_identification').first()['colombian_identification']
        self.assertNotEqual(raw, '987654321')

    def test_colombian_identification_decrypted_on_read(self):
        beneficiary = Beneficiary.objects.create(
            name='Test Descifrado',
            location='Cali',
            phone='3002222222',
            email='descifrado@test.com',
            colombian_identification='111222333',
        )
        loaded = Beneficiary.objects.get(pk=beneficiary.pk)
        self.assertEqual(loaded.colombian_identification, '111222333')

    def test_phone_stored_encrypted(self):
        beneficiary = Beneficiary.objects.create(
            name='Test Phone',
            location='Cali',
            phone='3009876543',
            email='phone@test.com',
            colombian_identification='000111222',
        )
        raw = Beneficiary.objects.filter(
            pk=beneficiary.pk
        ).values('phone').first()['phone']
        self.assertNotEqual(raw, '3009876543')


@override_settings(
    ENCRYPTION_KEY='c2VjcmV0a2V5Zm9ydGVzdGluZ3B1cnBvc2VzMTIzNDU2Nzg=',
    MEDIA_ROOT='/tmp/test_media_hu35/',
)
class ProtectedFileAccessTest(TestCase):

    def setUp(self):
        self.student  = _make_user('est_seg', ROLE_ESTUDIANTE)
        self.student2 = _make_user('est_seg2', ROLE_ESTUDIANTE)
        self.profesor = _make_user('prof_seg', ROLE_PROFESOR)
        self.case     = _make_case(student=self.student)

        os.makedirs('/tmp/test_media_hu35/', exist_ok=True)
        uploaded = SimpleUploadedFile('test_doc.pdf', b'contenido pdf', content_type='application/pdf')
        self.document = CaseDocument.objects.create(case=self.case, file=uploaded)
        self.url = reverse('serve_case_document', args=[self.document.pk])

    def test_assigned_student_can_access_file(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_profesor_can_access_file(self):
        self.client.force_login(self.profesor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unassigned_student_cannot_access_file(self):
        self.client.force_login(self.student2)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_user_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_failed_access_logged_in_audit(self):
        self.client.force_login(self.student2)
        self.client.get(self.url)
        self.assertTrue(
            CaseAuditLog.objects.filter(
                case=self.case,
                action='SECURITY_DENIED',
                user=self.student2,
            ).exists()
        )

    def test_successful_access_not_logged_as_denied(self):
        self.client.force_login(self.profesor)
        self.client.get(self.url)
        self.assertFalse(
            CaseAuditLog.objects.filter(
                case=self.case,
                action='SECURITY_DENIED',
            ).exists()
        )