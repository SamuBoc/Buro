from django.contrib.auth.models import User, Group
from django.core import mail
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from beneficiary.models import Beneficiary
from cases.models import Case, Notification


def make_beneficiary():
    return Beneficiary.objects.create(
        name='Pedro Perez',
        location='Cali',
        phone='3001234567',
        email='pedro@test.com',
    )

def make_case(beneficiary=None):
    if beneficiary is None:
        beneficiary = make_beneficiary()
    return Case.objects.create(
        sala=Case.ROOM_CIVIL,
        description='Problema de arrendamiento',
        beneficiary=beneficiary,
    )

def make_user(username='testuser', password='pass1234', group_name=None):
    user = User.objects.create_user(
        username=username, password=password, email=f'{username}@test.com'
    )
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


class NotificationModelTest(TestCase):

    def setUp(self):
        self.user = make_user('notif_model_user')
        self.beneficiary = make_beneficiary()
        self.case = make_case(self.beneficiary)
        self.notification = Notification.objects.create(
            recipient_user=self.user,
            case=self.case,
            notification_type='STATUS_CHANGE',
            title=f'Actualización del caso {self.case.code}',
            message='Su caso cambió de estado.',
            previous_status=Case.STATE_PENDING,
            new_status=Case.STATE_ASSIGNED,
        )

    def test_notification_fields_correct_on_creation(self):
        n = self.notification
        self.assertEqual(n.recipient_user, self.user)
        self.assertEqual(n.case, self.case)
        self.assertEqual(n.notification_type, 'STATUS_CHANGE')
        self.assertEqual(n.previous_status, Case.STATE_PENDING)
        self.assertEqual(n.new_status, Case.STATE_ASSIGNED)
        self.assertFalse(n.is_read)
        self.assertIsNone(n.read_at)

    def test_mark_as_read_sets_is_read_and_read_at(self):
        self.notification.mark_as_read()
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)

    def test_mark_as_read_idempotent(self):
        self.notification.mark_as_read()
        first_read_at = self.notification.read_at
        self.notification.mark_as_read()
        self.assertEqual(self.notification.read_at, first_read_at)

    def test_notification_default_unread(self):
        n = Notification.objects.create(
            recipient_user=self.user,
            case=self.case,
            notification_type='GENERAL',
            title='Test',
            message='Mensaje.',
        )
        self.assertFalse(n.is_read)
        self.assertIsNone(n.read_at)

    def test_notification_str_unread_label(self):
        self.assertIn('No leída', str(self.notification))

    def test_notification_str_read_label(self):
        self.notification.mark_as_read()
        self.assertIn('Leída', str(self.notification))

    def test_notification_ordering_newest_first(self):
        n2 = Notification.objects.create(
            recipient_user=self.user,
            case=self.case,
            notification_type='GENERAL',
            title='Segunda',
            message='Segunda.',
        )
        Notification.objects.filter(pk=n2.pk).update(
            created_at=timezone.now() + timezone.timedelta(seconds=1)
        )
        self.assertGreater(n2.id, self.notification.id)
        notifications = Notification.objects.filter(recipient_user=self.user)
        self.assertEqual(notifications.first().id, n2.id)

    def test_notification_without_status_fields_is_valid(self):
        n = Notification.objects.create(
            recipient_user=self.user,
            case=self.case,
            notification_type='GENERAL',
            title='Sin estados',
            message='Sin cambio de estado.',
        )
        self.assertIsNone(n.previous_status)
        self.assertIsNone(n.new_status)

    def test_notification_volume_200_records(self):
        notifs = [
            Notification(
                recipient_user=self.user,
                case=self.case,
                notification_type='GENERAL',
                title=f'Notif #{i}',
                message=f'Mensaje #{i}.',
            )
            for i in range(200)
        ]
        Notification.objects.bulk_create(notifs)
        total = Notification.objects.filter(recipient_user=self.user).count()
        self.assertGreaterEqual(total, 200)


class NotificationViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user('notif_view_user')
        self.other_user = make_user('otro_usuario')
        self.beneficiary = make_beneficiary()
        self.case = make_case(self.beneficiary)
        self.notification = Notification.objects.create(
            recipient_user=self.user,
            case=self.case,
            notification_type='STATUS_CHANGE',
            title='Cambio de estado',
            message='Su caso fue actualizado.',
            previous_status=Case.STATE_PENDING,
            new_status=Case.STATE_ASSIGNED,
        )

    def test_notification_list_requires_login(self):
        url = reverse('notification_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_notification_list_shows_own_notifications(self):
        self.client.login(username='notif_view_user', password='pass1234')
        url = reverse('notification_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.notification, response.context['notifications'])

    def test_notification_list_hides_other_user_notifications(self):
        self.client.login(username='otro_usuario', password='pass1234')
        url = reverse('notification_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.notification, response.context['notifications'])

    def test_mark_notification_read_marks_and_redirects(self):
        self.client.login(username='notif_view_user', password='pass1234')
        url = reverse('mark_notification_read', args=[self.notification.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_notification_read_forbidden_for_other_user(self):
        self.client.login(username='otro_usuario', password='pass1234')
        url = reverse('mark_notification_read', args=[self.notification.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_mark_all_notifications_read(self):
        Notification.objects.create(
            recipient_user=self.user,
            case=self.case,
            notification_type='GENERAL',
            title='Segunda',
            message='Otra.',
        )
        self.client.login(username='notif_view_user', password='pass1234')
        url = reverse('mark_all_notifications_read')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        unread = Notification.objects.filter(
            recipient_user=self.user, is_read=False
        ).count()
        self.assertEqual(unread, 0)

    def test_mark_all_when_none_unread_does_not_fail(self):
        self.notification.mark_as_read()
        self.client.login(username='notif_view_user', password='pass1234')
        url = reverse('mark_all_notifications_read')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        unread = Notification.objects.filter(
            recipient_user=self.user, is_read=False
        ).count()
        self.assertEqual(unread, 0)

    def test_unread_count_ajax_returns_correct_count(self):
        self.client.login(username='notif_view_user', password='pass1234')
        url = reverse('unread_count')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['unread_count'], 1)

    def test_unread_count_decreases_after_mark_read(self):
        self.notification.mark_as_read()
        self.client.login(username='notif_view_user', password='pass1234')
        url = reverse('unread_count')
        response = self.client.get(url)
        self.assertEqual(response.json()['unread_count'], 0)

    def test_unread_count_correct_with_many_notifications(self):
        notifs = [
            Notification(
                recipient_user=self.user,
                case=self.case,
                notification_type='GENERAL',
                title=f'Notif #{i}',
                message=f'Msg #{i}.',
            )
            for i in range(49)
        ]
        Notification.objects.bulk_create(notifs)
        self.client.login(username='notif_view_user', password='pass1234')
        url = reverse('unread_count')
        response = self.client.get(url)
        self.assertEqual(response.json()['unread_count'], 50)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class BeneficiaryStatusEmailTest(TestCase):
    """
    Verifica que _create_status_notification envía un email al beneficiario
    cuando el estado de su caso cambia (HU-13).

    Estos tests cubren el falso positivo previo: los tests anteriores solo
    verificaban notificaciones internas (modelo Notification) y dejaban sin
    probar el requisito principal de HU-13.
    """

    def setUp(self):
        self.secretaria = make_user('secretaria_hu13', group_name='secretaria')
        self.beneficiary = make_beneficiary()   # email='pedro@test.com'
        self.case = make_case(self.beneficiary)

    def _change_state(self, new_state, triggered_by=None):
        """Cambia el estado del caso simulando la señal con _request asignado."""
        from django.test import RequestFactory
        from cases.signals import _create_status_notification

        previous = self.case.state
        self.case.state = new_state

        if triggered_by:
            factory = RequestFactory()
            request = factory.get('/')
            request.user = triggered_by
            self.case._request = request

        self.case.save()
        return previous


    def test_beneficiary_receives_email_on_manual_status_change(self):
        """El beneficiario recibe email cuando la secretaria cambia el estado."""
        mail.outbox.clear()
        self._change_state(Case.STATE_ASSIGNED, triggered_by=self.secretaria)

        beneficiary_emails = [m for m in mail.outbox if self.beneficiary.email in m.to]
        self.assertGreaterEqual(
            len(beneficiary_emails), 1,
            'El beneficiario no recibió ningún email tras el cambio de estado.',
        )

    def test_beneficiary_email_contains_case_code(self):
        """El email al beneficiario menciona el código del caso."""
        mail.outbox.clear()
        self._change_state(Case.STATE_ASSIGNED, triggered_by=self.secretaria)

        beneficiary_emails = [m for m in mail.outbox if self.beneficiary.email in m.to]
        self.assertTrue(
            any(self.case.code in (m.subject + m.body) for m in beneficiary_emails),
            f'Ningún email al beneficiario menciona el código de caso {self.case.code}.',
        )

    def test_beneficiary_email_contains_new_status(self):
        """El email al beneficiario menciona el nuevo estado."""
        mail.outbox.clear()
        self._change_state(Case.STATE_ASSIGNED, triggered_by=self.secretaria)

        beneficiary_emails = [m for m in mail.outbox if self.beneficiary.email in m.to]
        self.assertTrue(
            any(Case.STATE_ASSIGNED in m.body for m in beneficiary_emails),
            'Ningún email al beneficiario menciona el nuevo estado del caso.',
        )

    def test_internal_notification_also_created_for_triggered_by(self):
        """La notificación interna del sistema sigue creándose para quien hizo el cambio."""
        mail.outbox.clear()
        self._change_state(Case.STATE_ASSIGNED, triggered_by=self.secretaria)

        internal = Notification.objects.filter(
            recipient_user=self.secretaria,
            notification_type='STATUS_CHANGE',
        )
        self.assertTrue(
            internal.exists(),
            'No se creó notificación interna para la secretaria que hizo el cambio.',
        )

    def test_beneficiary_receives_email_on_automatic_status_change(self):
        """
        El beneficiario recibe email incluso cuando el cambio de estado es
        automático (triggered_by=None), por ejemplo en asignación por scheduler.
        """
        mail.outbox.clear()
        self._change_state(Case.STATE_ASSIGNED, triggered_by=None)

        beneficiary_emails = [m for m in mail.outbox if self.beneficiary.email in m.to]
        self.assertGreaterEqual(
            len(beneficiary_emails), 1,
            'El beneficiario no recibió email en un cambio de estado automático.',
        )

    def test_no_internal_notification_on_automatic_change(self):
        """No se crea notificación interna cuando el cambio es automático (triggered_by=None)."""
        initial_count = Notification.objects.count()
        self._change_state(Case.STATE_ASSIGNED, triggered_by=None)

        self.assertEqual(
            Notification.objects.count(), initial_count,
            'Se creó una notificación interna para un cambio automático sin triggered_by.',
        )


    def test_no_email_sent_when_beneficiary_has_no_email(self):
        """
        Si el beneficiario no tiene email registrado no se intenta el envío
        y el flujo no lanza excepción.
        """
        self.beneficiary.email = ''
        self.beneficiary.save()
        mail.outbox.clear()

        try:
            self._change_state(Case.STATE_ASSIGNED, triggered_by=self.secretaria)
        except Exception as exc:
            self.fail(f'El cambio de estado lanzó una excepción inesperada: {exc}')

        beneficiary_emails = [m for m in mail.outbox if '' in m.to]
        self.assertEqual(len(beneficiary_emails), 0)