import io
import tempfile
import time
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_ESTUDIANTE, ROLE_SECRETARIA
from cases.models import Case, CommunicationInteraction, CaseAuditLog, CallSession
from beneficiary.models import Beneficiary

_FAKE_CLOUDINARY_RESPONSE = {
    'public_id': 'media/call_recordings/test/grabacion',
    'secure_url': 'https://res.cloudinary.com/test/raw/upload/v1/grabacion.webm',
    'url': 'http://res.cloudinary.com/test/raw/upload/v1/grabacion.webm',
    'resource_type': 'raw',
    'type': 'upload',
    'format': 'webm',
    'version': 1,
    'tags': [],
}


def _make_user(username, role):
    user = User.objects.create_user(username=username, password='pass1234')
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    return user


def _make_case(created_by):
    beneficiary = Beneficiary.objects.create(
        name='Beneficiario Test',
        location='Cali',
        phone='3001234567',
        email='b@test.com',
    )
    return Case.objects.create(beneficiary=beneficiary, created_by=created_by)


class CreateCallSessionTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = _make_user('admin_hu22', ROLE_ADMINISTRADOR)
        self.case = _make_case(self.admin)
        self.url = reverse('create_call_session', args=[self.case.pk])

    def test_crea_sesion_y_retorna_room_id(self):
        self.client.login(username='admin_hu22', password='pass1234')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('roomId', data)
        self.assertTrue(CallSession.objects.filter(room_id=data['roomId']).exists())

    def test_sin_login_redirige(self):
        response = self.client.post(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_usuario_sin_permiso_obtiene_403(self):
        estudiante = _make_user('est_hu22', ROLE_ESTUDIANTE)
        self.client.login(username='est_hu22', password='pass1234')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_metodo_get_retorna_405(self):
        self.client.login(username='admin_hu22', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


_TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(STORAGES=_TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class UploadCallRecordingTests(TestCase):

    def setUp(self):
        self.cloudinary_patch = patch('cloudinary.uploader.upload', return_value=_FAKE_CLOUDINARY_RESPONSE)
        self.cloudinary_patch.start()
        self.client = Client()
        self.admin = _make_user('admin_upload', ROLE_ADMINISTRADOR)
        self.case = _make_case(self.admin)
        self.url = reverse('upload_call_recording', args=[self.case.pk])

    def tearDown(self):
        self.cloudinary_patch.stop()

    def _fake_audio(self):
        return SimpleUploadedFile('grabacion.webm', b'fake_audio_bytes', content_type='audio/webm')

    def test_subida_crea_interaction_con_audio(self):
        self.client.login(username='admin_upload', password='pass1234')
        response = self.client.post(self.url, {
            'audio': self._fake_audio(),
            'description': 'Llamada de prueba',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        interaction = CommunicationInteraction.objects.get(pk=response.json()['interaction_id'])
        self.assertEqual(interaction.interaction_type, CommunicationInteraction.TYPE_CALL)
        self.assertTrue(bool(interaction.audio_file))

    def test_subida_registra_en_audit_log(self):
        self.client.login(username='admin_upload', password='pass1234')
        self.client.post(self.url, {'audio': self._fake_audio()})
        self.assertTrue(
            CaseAuditLog.objects.filter(case=self.case, action='COMMUNICATION').exists()
        )

    def test_sin_audio_retorna_400(self):
        self.client.login(username='admin_upload', password='pass1234')
        response = self.client.post(self.url, {'description': 'sin archivo'})
        self.assertEqual(response.status_code, 400)

    def test_metodo_get_retorna_405(self):
        self.client.login(username='admin_upload', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_usuario_sin_permiso_obtiene_403(self):
        estudiante = _make_user('est_upload', ROLE_ESTUDIANTE)
        self.client.login(username='est_upload', password='pass1234')
        response = self.client.post(self.url, {'audio': self._fake_audio()})
        self.assertEqual(response.status_code, 403)

    def test_error_en_guardado_se_registra_en_audit_log(self):
        self.client.login(username='admin_upload', password='pass1234')
        with patch('cases.models.CommunicationInteraction.objects.create', side_effect=Exception('fallo storage')):
            response = self.client.post(self.url, {'audio': self._fake_audio()})
        self.assertEqual(response.status_code, 500)
        self.assertTrue(
            CaseAuditLog.objects.filter(
                case=self.case,
                action='COMMUNICATION',
                description__icontains='Error',
            ).exists()
        )
