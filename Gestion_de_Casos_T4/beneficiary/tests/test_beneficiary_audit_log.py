from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from django.urls import reverse

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
from beneficiary.models import Beneficiary, BeneficiaryAuditLog
from beneficiary.signals import log_beneficiary_view, log_beneficiary_doc_action


def make_beneficiary(name='Ana Lopez', email='ana@test.com'):
    return Beneficiary.objects.create(
        name=name,
        location='Cali',
        phone='3009876543',
        email=email,
    )

def make_user(username='testuser', password='pass1234', group_name=None):
    user = User.objects.create_user(
        username=username, password=password, email=f'{username}@test.com'
    )
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


class BeneficiaryAuditLogModelTest(TestCase):

    def setUp(self):
        self.user = make_user('admin_hu33', group_name=ROLE_ADMINISTRADOR)
        self.beneficiary = make_beneficiary()

    def test_audit_log_created_on_beneficiary_creation(self):
        logs = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='CREATED'
        )
        self.assertEqual(logs.count(), 1)

    def test_audit_log_stores_beneficiary_name(self):
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='CREATED'
        ).first()
        self.assertEqual(log.beneficiary_name, 'Ana Lopez')

    def test_audit_log_updated_on_tracked_field_change(self):
        self.beneficiary.phone = '3111111111'
        self.beneficiary.save()
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='UPDATED'
        ).first()
        self.assertIsNotNone(log)
        self.assertIsNotNone(log.changed_fields)
        self.assertIn('Teléfono', log.changed_fields)

    def test_audit_log_changed_fields_stores_old_and_new(self):
        old_phone = self.beneficiary.phone
        self.beneficiary.phone = '3222222222'
        self.beneficiary.save()
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='UPDATED'
        ).first()
        self.assertIsNotNone(log.changed_fields)
        self.assertIn('Teléfono', log.changed_fields)
        self.assertEqual(log.changed_fields['Teléfono']['anterior'], old_phone)
        self.assertEqual(log.changed_fields['Teléfono']['nuevo'], '3222222222')

    def test_no_updated_log_when_no_field_changed(self):
        self.beneficiary.save()
        logs = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='UPDATED'
        )
        self.assertEqual(logs.count(), 0)

    def test_log_beneficiary_view_creates_viewed_log(self):
        log_beneficiary_view(self.beneficiary, self.user)
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='VIEWED'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)

    def test_log_doc_uploaded_creates_correct_log(self):
        log_beneficiary_doc_action(
            self.beneficiary, self.user, 'DOC_UPLOADED', 'cedula.pdf'
        )
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='DOC_UPLOADED'
        ).first()
        self.assertIsNotNone(log)
        self.assertIn('cedula.pdf', log.description)

    def test_log_doc_deleted_creates_correct_log(self):
        log_beneficiary_doc_action(
            self.beneficiary, self.user, 'DOC_DELETED', 'cedula.pdf'
        )
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='DOC_DELETED'
        ).first()
        self.assertIsNotNone(log)
        self.assertIn('cedula.pdf', log.description)

    def test_audit_log_preserved_after_beneficiary_deleted(self):
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='CREATED'
        ).first()
        log_id = log.id
        self.beneficiary.delete()
        log_after = BeneficiaryAuditLog.objects.get(id=log_id)
        self.assertIsNone(log_after.beneficiary)

    def test_audit_log_ordering_newest_first(self):
        log_beneficiary_view(self.beneficiary, self.user)
        log_beneficiary_doc_action(
            self.beneficiary, self.user, 'DOC_UPLOADED', 'doc.pdf'
        )
        logs = BeneficiaryAuditLog.objects.filter(beneficiary=self.beneficiary)
        self.assertGreaterEqual(logs[0].timestamp, logs[1].timestamp)

    def test_audit_log_str_contains_beneficiary_name(self):
        log = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary, action='CREATED'
        ).first()
        self.assertIn('Ana Lopez', str(log))

    def test_audit_log_without_user_is_valid(self):
        log = BeneficiaryAuditLog.objects.create(
            beneficiary=self.beneficiary,
            user=None,
            action='VIEWED',
            description='Vista sin usuario.',
            beneficiary_name=self.beneficiary.name,
        )
        self.assertIsNone(log.user)

    def test_audit_log_stores_ip_address(self):
        log = BeneficiaryAuditLog.objects.create(
            beneficiary=self.beneficiary,
            user=self.user,
            action='VIEWED',
            description='Vista con IP.',
            beneficiary_name=self.beneficiary.name,
            ip_address='10.0.0.1',
        )
        self.assertEqual(log.ip_address, '10.0.0.1')

    def test_audit_log_volume_500_records(self):
        logs_to_create = [
            BeneficiaryAuditLog(
                beneficiary=self.beneficiary,
                action='VIEWED',
                description=f'Vista #{i}.',
                beneficiary_name=self.beneficiary.name,
            )
            for i in range(500)
        ]
        BeneficiaryAuditLog.objects.bulk_create(logs_to_create)
        total = BeneficiaryAuditLog.objects.filter(
            beneficiary=self.beneficiary
        ).count()
        self.assertGreaterEqual(total, 500)

    def test_audit_log_isolation_between_beneficiaries(self):
        # FIX: removed id='1002' — el ID es auto-generado por el sistema (HU-2)
        other = make_beneficiary(name='Carlos Ruiz', email='carlos@test.com')
        log_beneficiary_view(self.beneficiary, self.user)
        log_beneficiary_view(other, self.user)
        logs_ana = BeneficiaryAuditLog.objects.filter(beneficiary=self.beneficiary)
        logs_carlos = BeneficiaryAuditLog.objects.filter(beneficiary=other)
        for log in logs_ana:
            self.assertNotEqual(log.beneficiary, other)
        for log in logs_carlos:
            self.assertNotEqual(log.beneficiary, self.beneficiary)


class BeneficiaryAuditLogViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_bv', group_name=ROLE_ADMINISTRADOR)
        self.secretaria = make_user('sec_bv', group_name=ROLE_SECRETARIA)
        self.estudiante = make_user('est_bv')
        # FIX: removed id='2001' — el ID es auto-generado por el sistema (HU-2)
        self.beneficiary = make_beneficiary('Carlos Ruiz', 'carlos@test.com')

    def test_beneficiary_audit_log_accessible_by_admin(self):
        self.client.login(username='admin_bv', password='pass1234')
        url = reverse('beneficiary_audit_log', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_beneficiary_audit_log_accessible_by_secretaria(self):
        self.client.login(username='sec_bv', password='pass1234')
        url = reverse('beneficiary_audit_log', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_beneficiary_audit_log_denied_to_student(self):
        self.client.login(username='est_bv', password='pass1234')
        url = reverse('beneficiary_audit_log', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_beneficiary_audit_log_requires_login(self):
        url = reverse('beneficiary_audit_log', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_beneficiary_audit_log_nonexistent_returns_404(self):
        self.client.login(username='admin_bv', password='pass1234')
        url = reverse('beneficiary_audit_log', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_global_beneficiary_audit_log_accessible_by_admin(self):
        self.client.login(username='admin_bv', password='pass1234')
        url = reverse('global_beneficiary_audit_log')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_global_beneficiary_audit_log_denied_to_secretaria(self):
        self.client.login(username='sec_bv', password='pass1234')
        url = reverse('global_beneficiary_audit_log')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_global_beneficiary_audit_log_denied_to_student(self):
        self.client.login(username='est_bv', password='pass1234')
        url = reverse('global_beneficiary_audit_log')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)