from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
from beneficiary.models import Beneficiary
from cases.models import Case, CaseAuditLog
from cases.signals import log_case_file_action



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



class CaseAuditLogModelTest(TestCase):

    def setUp(self):
        self.user = make_user('admin_hu9', group_name=ROLE_ADMINISTRADOR)
        self.beneficiary = make_beneficiary()
        self.case = make_case(self.beneficiary)

    def test_audit_log_created_on_case_creation(self):
        logs = CaseAuditLog.objects.filter(case=self.case, action='CREATED')
        self.assertEqual(logs.count(), 1)

    def test_audit_log_stores_timestamp(self):
        log = CaseAuditLog.objects.filter(case=self.case, action='CREATED').first()
        self.assertIsNotNone(log.timestamp)

    def test_audit_log_status_changed_stores_states(self):
        old_state = self.case.state
        CaseAuditLog.objects.create(
            case=self.case,
            user=self.user,
            action='STATUS_CHANGED',
            description='Cambio de estado.',
            previous_status=old_state,
            new_status=Case.STATE_ASSIGNED,
            case_radicado=self.case.code,
        )
        log = CaseAuditLog.objects.filter(
            case=self.case, action='STATUS_CHANGED'
        ).first()
        self.assertEqual(log.previous_status, old_state)
        self.assertEqual(log.new_status, Case.STATE_ASSIGNED)

    def test_audit_log_stores_user(self):
        log = CaseAuditLog.objects.create(
            case=self.case,
            user=self.user,
            action='UPDATED',
            description='Update.',
            case_radicado=self.case.code,
        )
        self.assertEqual(log.user, self.user)

    def test_audit_log_stores_ip_address(self):
        log = CaseAuditLog.objects.create(
            case=self.case,
            action='VIEWED',
            description='Vista.',
            case_radicado=self.case.code,
            ip_address='192.168.1.10',
        )
        self.assertEqual(log.ip_address, '192.168.1.10')

    def test_audit_log_ordering_newest_first(self):
        CaseAuditLog.objects.create(
            case=self.case, action='UPDATED',
            description='Update 1.', case_radicado=self.case.code,
            timestamp=timezone.now(),
        )
        CaseAuditLog.objects.create(
            case=self.case, action='VIEWED',
            description='Vista.', case_radicado=self.case.code,
            timestamp=timezone.now(),
        )
        logs = CaseAuditLog.objects.filter(case=self.case)
        self.assertGreaterEqual(logs[0].timestamp, logs[1].timestamp)

    def test_audit_log_preserved_after_case_deleted(self):
        log = CaseAuditLog.objects.filter(case=self.case, action='CREATED').first()
        log_id = log.id
        self.case.delete()
        log_after = CaseAuditLog.objects.get(id=log_id)
        self.assertIsNone(log_after.case)

    def test_audit_log_str_contains_case_code(self):
        log = CaseAuditLog.objects.filter(case=self.case, action='CREATED').first()
        self.assertIn(self.case.code, str(log))

    def test_audit_log_all_10_action_types_valid(self):
        actions = [
            'CREATED', 'UPDATED', 'STATUS_CHANGED', 'ASSIGNED',
            'REASSIGNED', 'FILE_UPLOADED', 'FILE_DELETED',
            'REJECTED', 'CLOSED', 'VIEWED',
        ]
        for action in actions:
            log = CaseAuditLog.objects.create(
                case=self.case, action=action,
                description=f'Test {action}.', case_radicado=self.case.code,
            )
            self.assertEqual(log.action, action)

    def test_log_case_file_action_uploaded(self):
        log_case_file_action(self.case, self.user, 'FILE_UPLOADED', 'contrato.pdf')
        log = CaseAuditLog.objects.filter(
            case=self.case, action='FILE_UPLOADED'
        ).first()
        self.assertIsNotNone(log)
        self.assertIn('contrato.pdf', log.description)

    def test_log_case_file_action_deleted(self):
        log_case_file_action(self.case, self.user, 'FILE_DELETED', 'contrato.pdf')
        log = CaseAuditLog.objects.filter(
            case=self.case, action='FILE_DELETED'
        ).first()
        self.assertIsNotNone(log)

    def test_audit_log_without_user_is_valid(self):
        log = CaseAuditLog.objects.create(
            case=self.case,
            user=None,
            action='CREATED',
            description='Creado por sistema.',
            case_radicado=self.case.code,
        )
        self.assertIsNone(log.user)
        self.assertEqual(log.action, 'CREATED')

    def test_audit_log_without_ip_is_valid(self):
        log = CaseAuditLog.objects.create(
            case=self.case,
            action='UPDATED',
            description='Sin IP.',
            case_radicado=self.case.code,
            ip_address=None,
        )
        self.assertIsNone(log.ip_address)

    def test_audit_log_volume_500_records(self):
        logs_to_create = [
            CaseAuditLog(
                case=self.case,
                action='VIEWED',
                description=f'Vista #{i}.',
                case_radicado=self.case.code,
            )
            for i in range(500)
        ]
        CaseAuditLog.objects.bulk_create(logs_to_create)
        total = CaseAuditLog.objects.filter(case=self.case).count()
        self.assertGreaterEqual(total, 500)

    def test_audit_log_ordering_with_many_records(self):
        logs_to_create = [
            CaseAuditLog(
                case=self.case,
                action='UPDATED',
                description=f'Update #{i}.',
                case_radicado=self.case.code,
                timestamp=timezone.now(),
            )
            for i in range(100)
        ]
        CaseAuditLog.objects.bulk_create(logs_to_create)
        logs = CaseAuditLog.objects.filter(case=self.case)
        for i in range(len(logs) - 1):
            self.assertGreaterEqual(logs[i].timestamp, logs[i + 1].timestamp)


class CaseAuditLogViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_view_hu9', group_name=ROLE_ADMINISTRADOR)
        self.secretaria = make_user('sec_view_hu9', group_name=ROLE_SECRETARIA)
        self.estudiante = make_user('est_view_hu9')
        self.beneficiary = make_beneficiary()
        self.case = make_case(self.beneficiary)

    def test_case_audit_log_accessible_by_admin(self):
        self.client.login(username='admin_view_hu9', password='pass1234')
        url = reverse('case_audit_log', args=[self.case.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_case_audit_log_accessible_by_secretaria(self):
        self.client.login(username='sec_view_hu9', password='pass1234')
        url = reverse('case_audit_log', args=[self.case.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_case_audit_log_denied_to_unassigned_student(self):
        self.client.login(username='est_view_hu9', password='pass1234')
        url = reverse('case_audit_log', args=[self.case.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_case_audit_log_requires_login(self):
        url = reverse('case_audit_log', args=[self.case.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_case_audit_log_nonexistent_case_returns_404(self):
        self.client.login(username='admin_view_hu9', password='pass1234')
        url = reverse('case_audit_log', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_global_audit_log_accessible_by_admin(self):
        self.client.login(username='admin_view_hu9', password='pass1234')
        url = reverse('global_audit_log')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_global_audit_log_denied_to_secretaria(self):
        self.client.login(username='sec_view_hu9', password='pass1234')
        url = reverse('global_audit_log')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_global_audit_log_denied_to_student(self):
        self.client.login(username='est_view_hu9', password='pass1234')
        url = reverse('global_audit_log')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)