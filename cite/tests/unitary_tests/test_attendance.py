from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from beneficiary.models import Beneficiary, BeneficiaryAuditLog
from cite.models import Cite


def make_user(username, password='pass1234'):
    return User.objects.create_user(username=username, password=password)


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
        make_user('user_attendance')
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