import tempfile

from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.constants import (
    ROLE_ADMINISTRADOR,
    ROLE_ESTUDIANTE,
    ROLE_PROFESOR,
    ROLE_SECRETARIA,
)
from cases.models import Case, CommunicationInteraction
from beneficiary.models import Beneficiary


_TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def _make_user(username, role):
    user = User.objects.create_user(username=username, password='pass1234')
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    return user


def _make_case(created_by, assigned_student=None):
    beneficiary = Beneficiary.objects.create(
        name='Beneficiario HU23',
        location='Cali',
        phone='3001234567',
        email='hu23@test.com',
    )
    return Case.objects.create(
        beneficiary=beneficiary,
        created_by=created_by,
        assigned_student=assigned_student,
    )


def _make_interaction_with_audio(case, user, media_root):
    audio = SimpleUploadedFile('rec.webm', b'audio_data', content_type='audio/webm')
    return CommunicationInteraction.objects.create(
        case=case,
        registered_by=user,
        interaction_type=CommunicationInteraction.TYPE_CALL,
        direction=CommunicationInteraction.DIRECTION_OUT,
        description='Grabación de prueba',
        audio_file=audio,
    )


@override_settings(STORAGES=_TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class ServeCallRecordingTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = _make_user('admin_hu23', ROLE_ADMINISTRADOR)
        self.profesor = _make_user('profesor_hu23', ROLE_PROFESOR)
        self.secretaria = _make_user('secretaria_hu23', ROLE_SECRETARIA)
        self.student_assigned = _make_user('student_assigned', ROLE_ESTUDIANTE)
        self.student_other = _make_user('student_other', ROLE_ESTUDIANTE)

        self.case = _make_case(self.admin, assigned_student=self.student_assigned)
        self.media_root = tempfile.mkdtemp()
        self.interaction = _make_interaction_with_audio(self.case, self.admin, self.media_root)
        self.url = reverse('serve_call_recording', args=[self.interaction.pk])

    def test_administrador_puede_acceder(self):
        self.client.login(username='admin_hu23', password='pass1234')
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302])

    def test_profesor_puede_acceder(self):
        self.client.login(username='profesor_hu23', password='pass1234')
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302])

    def test_secretaria_no_puede_acceder(self):
        self.client.login(username='secretaria_hu23', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_estudiante_asignado_puede_acceder(self):
        self.client.login(username='student_assigned', password='pass1234')
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 302])

    def test_estudiante_no_asignado_no_puede_acceder(self):
        self.client.login(username='student_other', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_sin_login_redirige_a_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    def test_interaccion_sin_audio_retorna_404(self):
        interaction_sin_audio = CommunicationInteraction.objects.create(
            case=self.case,
            registered_by=self.admin,
            interaction_type=CommunicationInteraction.TYPE_CALL,
            direction=CommunicationInteraction.DIRECTION_OUT,
            description='Sin grabación',
        )
        url = reverse('serve_call_recording', args=[interaction_sin_audio.pk])
        self.client.login(username='admin_hu23', password='pass1234')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_acceso_denegado_registra_en_audit_log(self):
        from cases.models import CaseAuditLog
        self.client.login(username='secretaria_hu23', password='pass1234')
        self.client.get(self.url)
        log = CaseAuditLog.objects.filter(
            case=self.case,
            action='SECURITY_DENIED',
        ).last()
        self.assertIsNotNone(log)
        self.assertIn('secretaria_hu23', log.description)

    def test_template_muestra_candado_para_secretaria(self):
        self.client.login(username='secretaria_hu23', password='pass1234')
        response = self.client.get(
            reverse('case_detail', args=[self.case.pk])
        )
        self.assertContains(response, 'bi-lock-fill')

    def test_template_muestra_reproductor_para_admin(self):
        self.client.login(username='admin_hu23', password='pass1234')
        response = self.client.get(
            reverse('case_detail', args=[self.case.pk])
        )
        self.assertContains(response, '<audio controls')
