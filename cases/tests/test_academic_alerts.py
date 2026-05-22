import datetime
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone

from accounts.constants import ROLE_ESTUDIANTE, ROLE_PROFESOR, ROLE_SECRETARIA
from beneficiary.models import Beneficiary
from cases.models import Case, Notification
from cases.services import auto_assign_case, generate_deadline_alerts, reassign_case


def _make_user(username, role, email=None):
    user = User.objects.create_user(
        username, password='testpass123', email=email or f'{username}@icesi.edu.co'
    )
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    return user


def _make_case(student=None):
    beneficiary = Beneficiary.objects.create(
        name='Beneficiario HU28',
        location='Cali',
        phone='3001234567',
        email='ben@test.com',
    )
    return Case.objects.create(
        sala=Case.ROOM_CIVIL,
        description='Caso prueba alertas',
        beneficiary=beneficiary,
        assigned_student=student,
        status=Case.STATUS_COMPLETE,
    )


# ── Notificaciones de asignación ──────────────────────────────────────────────

class AssignmentNotificationTest(TestCase):

    def setUp(self):
        self.student  = _make_user('est_hu28', ROLE_ESTUDIANTE)
        self.profesor = _make_user('prof_hu28', ROLE_PROFESOR)

    def test_auto_assign_creates_notification_for_student(self):
        case = _make_case()
        auto_assign_case(case)
        self.assertTrue(
            Notification.objects.filter(
                case=case,
                notification_type='ASSIGNMENT',
                recipient_user=self.student,
            ).exists()
        )

    def test_auto_assign_creates_notification_for_profesor(self):
        case = _make_case()
        auto_assign_case(case)
        self.assertTrue(
            Notification.objects.filter(
                case=case,
                notification_type='ASSIGNMENT',
                recipient_user=self.profesor,
            ).exists()
        )

    def test_auto_assign_no_notification_when_no_student_available(self):
        case = _make_case()
        # sin estudiantes disponibles (max_cases=0)
        self.student.profile.max_cases = 0
        self.student.profile.save()
        auto_assign_case(case)
        self.assertFalse(
            Notification.objects.filter(
                case=case,
                notification_type='ASSIGNMENT',
            ).exists()
        )

    def test_reassign_creates_notification_for_new_student(self):
        student2 = _make_user('est_hu28_b', ROLE_ESTUDIANTE)
        secretaria = _make_user('sec_hu28', ROLE_SECRETARIA)
        case = _make_case(student=self.student)
        reassign_case(case, student2, secretaria)
        self.assertTrue(
            Notification.objects.filter(
                case=case,
                notification_type='ASSIGNMENT',
                recipient_user=student2,
            ).exists()
        )

    def test_assignment_notification_title_contains_case_code(self):
        case = _make_case()
        auto_assign_case(case)
        notif = Notification.objects.filter(
            case=case,
            notification_type='ASSIGNMENT',
            recipient_user=self.student,
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn(case.code, notif.title)

    def test_assignment_notification_message_contains_beneficiary(self):
        case = _make_case()
        auto_assign_case(case)
        notif = Notification.objects.filter(
            case=case,
            notification_type='ASSIGNMENT',
            recipient_user=self.student,
        ).first()
        self.assertIn(case.beneficiary.name, notif.message)


# ── Alertas de vencimiento ────────────────────────────────────────────────────

class DeadlineAlertNotificationTest(TestCase):

    def setUp(self):
        self.student  = _make_user('est_dl', ROLE_ESTUDIANTE)
        self.profesor = _make_user('prof_dl', ROLE_PROFESOR)

    def _make_case_with_deadline(self, days_ahead):
        case = _make_case(student=self.student)
        case.deadline_date = timezone.localdate() + datetime.timedelta(days=days_ahead)
        case.deadline_alert_sent_at = None
        case.save(update_fields=['deadline_date', 'deadline_alert_sent_at'])
        return case

    def test_deadline_alert_creates_notification_within_range(self):
        case = self._make_case_with_deadline(days_ahead=2)
        generate_deadline_alerts(days_ahead=3)
        self.assertTrue(
            Notification.objects.filter(
                case=case,
                notification_type='DEADLINE',
            ).exists()
        )

    def test_deadline_alert_notifies_assigned_student(self):
        case = self._make_case_with_deadline(days_ahead=2)
        generate_deadline_alerts(days_ahead=3)
        self.assertTrue(
            Notification.objects.filter(
                case=case,
                notification_type='DEADLINE',
                recipient_user=self.student,
            ).exists()
        )

    def test_deadline_alert_notifies_profesor(self):
        case = self._make_case_with_deadline(days_ahead=2)
        generate_deadline_alerts(days_ahead=3)
        self.assertTrue(
            Notification.objects.filter(
                case=case,
                notification_type='DEADLINE',
                recipient_user=self.profesor,
            ).exists()
        )

    def test_deadline_alert_not_sent_twice(self):
        case = self._make_case_with_deadline(days_ahead=2)
        generate_deadline_alerts(days_ahead=3)
        generate_deadline_alerts(days_ahead=3)
        count = Notification.objects.filter(
            case=case,
            notification_type='DEADLINE',
            recipient_user=self.student,
        ).count()
        self.assertEqual(count, 1)

    def test_deadline_alert_not_created_outside_range(self):
        case = self._make_case_with_deadline(days_ahead=10)
        generate_deadline_alerts(days_ahead=3)
        self.assertFalse(
            Notification.objects.filter(
                case=case,
                notification_type='DEADLINE',
            ).exists()
        )

    def test_deadline_alert_title_contains_case_code(self):
        case = self._make_case_with_deadline(days_ahead=1)
        generate_deadline_alerts(days_ahead=3)
        notif = Notification.objects.filter(
            case=case,
            notification_type='DEADLINE',
            recipient_user=self.student,
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn(case.code, notif.title)


# ── Envío de emails ───────────────────────────────────────────────────────────

class AssignmentEmailTest(TestCase):

    def setUp(self):
        self.student  = _make_user('est_email', ROLE_ESTUDIANTE, email='est@icesi.edu.co')
        self.profesor = _make_user('prof_email', ROLE_PROFESOR,  email='prof@icesi.edu.co')

    @patch('cases.email_utils.send_case_assignment_email')
    def test_assignment_email_called_on_notification_create(self, mock_send):
        case = _make_case()
        auto_assign_case(case)
        self.assertTrue(mock_send.called)

    @patch('cases.email_utils.send_case_assignment_email')
    def test_assignment_email_not_called_when_no_student(self, mock_send):
        self.student.profile.max_cases = 0
        self.student.profile.save()
        case = _make_case()
        auto_assign_case(case)
        mock_send.assert_not_called()


class DeadlineEmailTest(TestCase):

    def setUp(self):
        self.student = _make_user('est_dl_email', ROLE_ESTUDIANTE, email='est_dl@icesi.edu.co')

    @patch('cases.email_utils.send_deadline_alert_email')
    def test_deadline_email_called_on_alert_generation(self, mock_send):
        case = _make_case(student=self.student)
        case.deadline_date = timezone.localdate() + datetime.timedelta(days=2)
        case.deadline_alert_sent_at = None
        case.save(update_fields=['deadline_date', 'deadline_alert_sent_at'])
        generate_deadline_alerts(days_ahead=3)
        self.assertTrue(mock_send.called)

    @patch('cases.email_utils.send_deadline_alert_email')
    def test_deadline_email_not_called_when_already_sent(self, mock_send):
        case = _make_case(student=self.student)
        case.deadline_date = timezone.localdate() + datetime.timedelta(days=2)
        case.deadline_alert_sent_at = timezone.now()
        case.save(update_fields=['deadline_date', 'deadline_alert_sent_at'])
        generate_deadline_alerts(days_ahead=3)
        mock_send.assert_not_called()