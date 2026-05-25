from datetime import date, timedelta

from django.contrib.auth.models import User, Group
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.constants import ROLE_SECRETARIA, ROLE_ESTUDIANTE, ROLE_PROFESOR
from beneficiary.models import Beneficiary, BeneficiaryAuditLog
from cite.models import Cite


def make_user(username, password='pass1234', group_name=None):
    user = User.objects.create_user(username=username, password=password)
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def make_beneficiary():
    return Beneficiary.objects.create(
        name='Laura Diaz',
        location='Cali',
        phone='3001234567',
        email='laura@example.com',
    )


def make_cite(beneficiary, state=Cite.STATE_PENDING, days_offset=0):
    return Cite.objects.create(
        beneficiary=beneficiary,
        date_assigned=timezone.now() + timedelta(days=days_offset),
        modality_cite=Cite.MODALITY_INPERSON,
        state_cite=state,
        request_cite=Cite.CHANNEL_WEB,
        description='Test appointment',
    )


class CiteAttendanceTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('user_attendance', group_name=ROLE_SECRETARIA)
        self.client.login(username='user_attendance', password='pass1234')
        self.beneficiary = make_beneficiary()

    def test_attended_status_set_for_past_cite(self):
        cite = make_cite(self.beneficiary, days_offset=-1)
        self.client.post(reverse('register_cite_attendance', args=[cite.pk, 'asistio']))
        cite.refresh_from_db()
        self.assertEqual(cite.state_cite, Cite.STATE_ATTENDED)

    def test_no_show_status_set_for_past_cite(self):
        cite = make_cite(self.beneficiary, days_offset=-1)
        self.client.post(reverse('register_cite_attendance', args=[cite.pk, 'no-asistio']))
        cite.refresh_from_db()
        self.assertEqual(cite.state_cite, Cite.STATE_NO_SHOW)

    def test_attendance_creates_audit_log_entry(self):
        cite = make_cite(self.beneficiary)
        self.client.post(reverse('register_cite_attendance', args=[cite.id, 'asistio']))
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='CITE_ATTENDED'
        ).first()
        self.assertIsNotNone(log)
        self.assertIn('asistió', log.description)

    def test_no_show_creates_audit_log_entry(self):
        cite = make_cite(self.beneficiary)
        self.client.post(reverse('register_cite_attendance', args=[cite.id, 'no-asistio']))
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='CITE_MISSED'
        ).first()
        self.assertIsNotNone(log)
        self.assertIn('no asistió', log.description)

    def test_cannot_register_attendance_for_future_cite(self):
        cite = make_cite(self.beneficiary, days_offset=3)
        self.client.post(reverse('register_cite_attendance', args=[cite.pk, 'asistio']))
        cite.refresh_from_db()
        self.assertNotEqual(cite.state_cite, Cite.STATE_ATTENDED)

    def test_cannot_register_attendance_for_cancelled_cite(self):
        cite = make_cite(self.beneficiary, state=Cite.STATE_CANCELED, days_offset=-1)
        self.client.post(reverse('register_cite_attendance', args=[cite.pk, 'asistio']))
        cite.refresh_from_db()
        self.assertEqual(cite.state_cite, Cite.STATE_CANCELED)
        self.assertEqual(
            BeneficiaryAuditLog.objects.filter(
                beneficiary=self.beneficiary, action='CITE_ATTENDED'
            ).count(), 0
        )

    def test_duplicate_attendance_not_registered(self):
        cite = make_cite(self.beneficiary)
        self.client.post(reverse('register_cite_attendance', args=[cite.id, 'asistio']))
        self.client.post(reverse('register_cite_attendance', args=[cite.id, 'asistio']))
        cite.refresh_from_db()
        self.assertEqual(cite.state_cite, Cite.STATE_ATTENDED)
        self.assertEqual(
            BeneficiaryAuditLog.objects.filter(
                beneficiary=self.beneficiary, action='CITE_ATTENDED'
            ).count(), 1
        )

    def test_invalid_status_does_not_modify_cite_or_log(self):
        cite = make_cite(self.beneficiary, days_offset=-1)
        initial_log_count = BeneficiaryAuditLog.objects.filter(beneficiary=self.beneficiary).count()
        self.client.post(reverse('register_cite_attendance', args=[cite.pk, 'invalid-status']))
        cite.refresh_from_db()
        self.assertEqual(cite.state_cite, Cite.STATE_PENDING)
        self.assertEqual(
            BeneficiaryAuditLog.objects.filter(beneficiary=self.beneficiary).count(),
            initial_log_count
        )

    def test_get_request_does_not_register_attendance(self):
        cite = make_cite(self.beneficiary, days_offset=-1)
        self.client.get(reverse('register_cite_attendance', args=[cite.pk, 'asistio']))
        cite.refresh_from_db()
        self.assertNotEqual(cite.state_cite, Cite.STATE_ATTENDED)


class CiteAttendanceAccessControlTest(TestCase):
    """
    Verifica que estudiantes y profesores no pueden registrar asistencia.
    Solo secretaria y administrador tienen acceso (HU-18).

    Antes este archivo usaba un usuario sin rol en setUp, lo que significaba
    que se probaba el happy path sin restricción de rol — coincidiendo con el
    bug (la vista no tenía @role_required). Ahora ambos problemas están corregidos.
    """

    def setUp(self):
        self.client = Client()
        self.beneficiary = make_beneficiary()
        # Cita en el pasado para que la lógica interna de validación no interfiera
        self.cite = make_cite(self.beneficiary, days_offset=-1)
        self.url = reverse('register_cite_attendance', args=[self.cite.pk, 'asistio'])

    def test_student_cannot_register_attendance(self):
        """NEGATIVO: Un estudiante no puede registrar asistencia a una cita."""
        make_user('est_attendance', group_name=ROLE_ESTUDIANTE)
        self.client.login(username='est_attendance', password='pass1234')
        response = self.client.post(self.url)
        self.assertEqual(
            response.status_code, 302,
            'Se esperaba redirección (302) al intentar registrar asistencia como estudiante.',
        )
        self.cite.refresh_from_db()
        self.assertNotEqual(
            self.cite.state_cite, Cite.STATE_ATTENDED,
            'El estado de la cita no debe cambiar tras intento de un estudiante.',
        )

    def test_professor_cannot_register_attendance(self):
        """NEGATIVO: Un profesor no puede registrar asistencia a una cita."""
        make_user('prof_attendance', group_name=ROLE_PROFESOR)
        self.client.login(username='prof_attendance', password='pass1234')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.cite.refresh_from_db()
        self.assertNotEqual(self.cite.state_cite, Cite.STATE_ATTENDED)

    def test_unauthenticated_user_cannot_register_attendance(self):
        """NEGATIVO: Un usuario no autenticado no puede registrar asistencia."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])
        self.cite.refresh_from_db()
        self.assertNotEqual(self.cite.state_cite, Cite.STATE_ATTENDED)

    def test_secretaria_can_register_attendance(self):
        """POSITIVO: La secretaria sí puede registrar asistencia."""
        make_user('sec_att', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_att', password='pass1234')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.cite.refresh_from_db()
        self.assertEqual(
            self.cite.state_cite, Cite.STATE_ATTENDED,
            'La secretaria debe poder registrar asistencia correctamente.',
        )