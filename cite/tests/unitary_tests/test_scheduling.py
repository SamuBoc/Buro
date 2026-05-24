from datetime import date, timedelta

from django.contrib.auth.models import User, Group
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.constants import ROLE_SECRETARIA, ROLE_ESTUDIANTE, ROLE_PROFESOR
from beneficiary.models import Beneficiary
from cite.models import Cite


def make_user(username, password='pass1234', group_name=None):
    user = User.objects.create_user(username=username, password=password)
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def make_beneficiary():
    return Beneficiary.objects.create(
        id='BEN-2026-0001',
        name='Laura Torres',
        location='Cali, Valle',
        phone='3001234567',
        email='laura@test.com',
        colombian_identification='1001234567',
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


class CiteCreationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user('user_cite', group_name=ROLE_SECRETARIA)
        self.client.login(username='user_cite', password='pass1234')
        self.beneficiary = make_beneficiary()
        self.url = reverse('create_cite', args=[self.beneficiary.pk])

    def test_valid_data_saves_cite_to_db(self):
        data = {
            'modality_cite': Cite.MODALITY_INPERSON,
            'request_cite': Cite.CHANNEL_WEB,
            'date_assigned': str(timezone.now()),
            'description': 'First consultation',
        }
        self.client.post(self.url, data)
        self.assertEqual(Cite.objects.count(), 1)

    def test_valid_data_redirects_to_beneficiary_detail(self):
        data = {
            'modality_cite': Cite.MODALITY_VIRTUAL,
            'request_cite': Cite.CHANNEL_EMAIL,
            'date_assigned': str(timezone.now()),
            'description': 'Virtual consultation',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('beneficiary_detail', args=[self.beneficiary.pk]))

    def test_missing_description_does_not_save(self):
        data = {
            'modality_cite': Cite.MODALITY_INPERSON,
            'request_cite': Cite.CHANNEL_WEB,
            'date_assigned': str(timezone.now()),
            'description': '',
        }
        self.client.post(self.url, data)
        self.assertEqual(Cite.objects.count(), 0)

    def test_unauthenticated_user_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_new_cite_defaults_to_pending_state(self):
        data = {
            'modality_cite': Cite.MODALITY_INPERSON,
            'request_cite': Cite.CHANNEL_WEB,
            'date_assigned': str(timezone.now()),
            'description': 'Check initial state',
        }
        self.client.post(self.url, data)
        cite = Cite.objects.first()
        self.assertEqual(cite.state_cite, Cite.STATE_PENDING)

    def test_nonexistent_beneficiary_returns_404(self):
        url = reverse('create_cite', args=['BEN-9999-9999'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class CiteModalitySelectionTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('user_modality', group_name=ROLE_SECRETARIA)
        self.client.login(username='user_modality', password='pass1234')
        self.beneficiary = make_beneficiary()

    def test_selected_modality_is_saved_correctly(self):
        response = self.client.post(
            reverse('create_cite', args=[self.beneficiary.id]),
            {
                'modality_cite': Cite.MODALITY_PHONE,
                'request_cite': Cite.CHANNEL_WEB,
                'description': 'Phone consultation',
            }
        )
        self.assertEqual(response.status_code, 302)
        cite = Cite.objects.first()
        self.assertEqual(cite.modality_cite, Cite.MODALITY_PHONE)

    def test_missing_modality_returns_validation_error(self):
        response = self.client.post(
            reverse('create_cite', args=[self.beneficiary.id]),
            {
                'modality_cite': '',
                'request_cite': Cite.CHANNEL_WEB,
                'description': 'General orientation',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Cite.objects.count(), 0)
        self.assertContains(response, 'Debes seleccionar una modalidad valida para continuar.')


class CiteCancellationTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('user_cancel', group_name=ROLE_SECRETARIA)
        self.client.login(username='user_cancel', password='pass1234')
        self.beneficiary = make_beneficiary()

    def test_cancellation_updates_state_to_cancelled(self):
        cite = make_cite(self.beneficiary)
        self.client.post(reverse('cancel_cite', args=[cite.pk]))
        cite.refresh_from_db()
        self.assertEqual(cite.state_cite, Cite.STATE_CANCELED)

    def test_cancellation_redirects_to_cite_list(self):
        cite = make_cite(self.beneficiary)
        response = self.client.post(reverse('cancel_cite', args=[cite.pk]))
        self.assertRedirects(response, reverse('beneficiary_cites', args=[self.beneficiary.pk]))

    def test_cancellation_does_not_delete_record(self):
        cite = make_cite(self.beneficiary)
        self.client.post(reverse('cancel_cite', args=[cite.pk]))
        self.assertEqual(Cite.objects.count(), 1)

    def test_nonexistent_cite_returns_404(self):
        response = self.client.post(reverse('cancel_cite', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_get_request_does_not_cancel_cite(self):
        cite = make_cite(self.beneficiary)
        self.client.get(reverse('cancel_cite', args=[cite.pk]))
        cite.refresh_from_db()
        self.assertNotEqual(cite.state_cite, Cite.STATE_CANCELED)


class CiteReschedulingTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('user_reschedule', group_name=ROLE_SECRETARIA)
        self.client.login(username='user_reschedule', password='pass1234')
        self.beneficiary = make_beneficiary()

    def test_rescheduling_updates_date_in_db(self):
        cite = make_cite(self.beneficiary)
        new_date = timezone.now() + timedelta(days=7)
        self.client.post(reverse('reschedule_cite', args=[cite.pk]), {'date_assigned': str(new_date)})
        cite.refresh_from_db()
        self.assertEqual(cite.date_assigned, new_date)

    def test_rescheduling_redirects_to_cite_list(self):
        cite = make_cite(self.beneficiary)
        new_date = date.today() + timedelta(days=5)
        response = self.client.post(reverse('reschedule_cite', args=[cite.pk]), {'date_assigned': str(new_date)})
        self.assertRedirects(response, reverse('beneficiary_cites', args=[self.beneficiary.pk]))

    def test_invalid_date_does_not_update_cite(self):
        cite = make_cite(self.beneficiary)
        original_date = cite.date_assigned
        self.client.post(reverse('reschedule_cite', args=[cite.pk]), {'date_assigned': 'not-a-date'})
        cite.refresh_from_db()
        self.assertEqual(cite.date_assigned, original_date)

    def test_nonexistent_cite_returns_404(self):
        response = self.client.get(reverse('reschedule_cite', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_get_request_shows_form_with_current_date(self):
        cite = make_cite(self.beneficiary)
        response = self.client.get(reverse('reschedule_cite', args=[cite.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, cite.date_assigned.strftime('%d/%m/%Y'))


class CiteAccessControlTest(TestCase):
    """
    Verifica que estudiantes y profesores no pueden crear, cancelar ni
    reprogramar citas. Solo secretaria y administrador tienen acceso (HU-16).
    """

    def setUp(self):
        self.client = Client()
        self.beneficiary = make_beneficiary()
        self.cite = make_cite(self.beneficiary)
        self.create_url = reverse('create_cite', args=[self.beneficiary.pk])
        self.cancel_url = reverse('cancel_cite', args=[self.cite.pk])
        self.reschedule_url = reverse('reschedule_cite', args=[self.cite.pk])

    def _assert_forbidden(self, url, method='get'):
        """Verifica que la vista devuelve 302 (redirección a forbidden/login)."""
        response = getattr(self.client, method)(url)
        self.assertEqual(
            response.status_code, 302,
            f'Se esperaba 302 en {url} pero se obtuvo {response.status_code}.',
        )

    def test_student_cannot_create_cite(self):
        """NEGATIVO: Un estudiante no puede agendar citas."""
        make_user('est_create', group_name=ROLE_ESTUDIANTE)
        self.client.login(username='est_create', password='pass1234')
        self._assert_forbidden(self.create_url, method='get')

    def test_student_cannot_cancel_cite(self):
        """NEGATIVO: Un estudiante no puede cancelar citas."""
        make_user('est_cancel', group_name=ROLE_ESTUDIANTE)
        self.client.login(username='est_cancel', password='pass1234')
        self._assert_forbidden(self.cancel_url, method='post')
        self.cite.refresh_from_db()
        self.assertNotEqual(
            self.cite.state_cite, Cite.STATE_CANCELED,
            'La cita no debe haberse cancelado tras intento de un estudiante.',
        )

    def test_student_cannot_reschedule_cite(self):
        """NEGATIVO: Un estudiante no puede reprogramar citas."""
        make_user('est_reschedule', group_name=ROLE_ESTUDIANTE)
        self.client.login(username='est_reschedule', password='pass1234')
        self._assert_forbidden(self.reschedule_url, method='get')

    def test_professor_cannot_create_cite(self):
        """NEGATIVO: Un profesor no puede agendar citas."""
        make_user('prof_create', group_name=ROLE_PROFESOR)
        self.client.login(username='prof_create', password='pass1234')
        self._assert_forbidden(self.create_url, method='get')

    def test_professor_cannot_cancel_cite(self):
        """NEGATIVO: Un profesor no puede cancelar citas."""
        make_user('prof_cancel', group_name=ROLE_PROFESOR)
        self.client.login(username='prof_cancel', password='pass1234')
        self._assert_forbidden(self.cancel_url, method='post')
        self.cite.refresh_from_db()
        self.assertNotEqual(self.cite.state_cite, Cite.STATE_CANCELED)

    def test_professor_cannot_reschedule_cite(self):
        """NEGATIVO: Un profesor no puede reprogramar citas."""
        make_user('prof_reschedule', group_name=ROLE_PROFESOR)
        self.client.login(username='prof_reschedule', password='pass1234')
        self._assert_forbidden(self.reschedule_url, method='get')

    def test_secretaria_can_create_cite(self):
        """POSITIVO: La secretaria sí puede agendar citas."""
        make_user('sec_create', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_create', password='pass1234')
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)

    def test_secretaria_can_cancel_cite(self):
        """POSITIVO: La secretaria sí puede cancelar citas."""
        make_user('sec_cancel', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_cancel', password='pass1234')
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, 302)
        self.cite.refresh_from_db()
        self.assertEqual(self.cite.state_cite, Cite.STATE_CANCELED)