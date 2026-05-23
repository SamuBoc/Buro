from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_ESTUDIANTE, ROLE_PROFESOR, ROLE_SECRETARIA
from beneficiary.models import Beneficiary
from cases.models import Case


def make_user(username, password='pass1234', group_name=None):
    user = User.objects.create_user(
        username=username,
        password=password,
        email=f'{username}@test.com'
    )
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def make_beneficiary(name='Pedro Perez', email='pedro@test.com'):
    return Beneficiary.objects.create(
        name=name,
        location='Cali',
        phone='3001234567',
        email=email,
    )


def make_case(beneficiary=None, **kwargs):
    if beneficiary is None:
        beneficiary = make_beneficiary()
    defaults = {
        'sala': Case.ROOM_CIVIL,
        'description': 'Problema de arrendamiento',
        'beneficiary': beneficiary,
    }
    defaults.update(kwargs)
    return Case.objects.create(**defaults)


class AcademicDashboardAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_acad', group_name=ROLE_ADMINISTRADOR)
        self.profesor = make_user('prof_acad', group_name=ROLE_PROFESOR)
        self.secretaria = make_user('sec_acad', group_name=ROLE_SECRETARIA)
        self.estudiante = make_user('stud_acad', group_name=ROLE_ESTUDIANTE)

    def test_admin_can_access_dashboard(self):
        self.client.login(username='admin_acad', password='pass1234')
        response = self.client.get(reverse('academic_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_profesor_can_access_dashboard(self):
        self.client.login(username='prof_acad', password='pass1234')
        response = self.client.get(reverse('academic_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_secretaria_can_access_dashboard(self):
        self.client.login(username='sec_acad', password='pass1234')
        response = self.client.get(reverse('academic_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_estudiante_is_redirected(self):
        self.client.login(username='stud_acad', password='pass1234')
        response = self.client.get(reverse('academic_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse('academic_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])


class AcademicDashboardMetricsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.profesor = make_user('prof_acad_metrics', group_name=ROLE_PROFESOR)
        self.student_one = make_user('stud_metrics_1', group_name=ROLE_ESTUDIANTE)
        self.student_two = make_user('stud_metrics_2', group_name=ROLE_ESTUDIANTE)
        self.beneficiary = make_beneficiary(email='metrics@test.com')

        today = timezone.localdate()
        make_case(
            beneficiary=self.beneficiary,
            assigned_student=self.student_one,
            deadline_date=today - timedelta(days=2),
            state=Case.STATE_ASSIGNED,
        )
        make_case(
            beneficiary=self.beneficiary,
            assigned_student=self.student_one,
            deadline_date=None,
            state=Case.STATE_ASSIGNED,
        )
        make_case(
            beneficiary=self.beneficiary,
            assigned_student=self.student_two,
            deadline_date=today + timedelta(days=3),
            state=Case.STATE_ASSIGNED,
        )

    def test_dashboard_context_metrics(self):
        self.client.force_login(self.profesor)
        response = self.client.get(reverse('academic_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_students'], 2)
        self.assertEqual(response.context['total_assigned_cases'], 3)
        self.assertEqual(response.context['total_overdue_cases'], 1)
        self.assertEqual(response.context['total_without_deadline_cases'], 1)

    def test_student_detail_metrics(self):
        self.client.force_login(self.profesor)
        response = self.client.get(
            reverse('academic_student_detail', args=[self.student_one.id])
        )
        self.assertEqual(response.status_code, 200)
        metrics = response.context['metrics']
        self.assertEqual(metrics['total_cases'], 2)
        self.assertEqual(metrics['overdue_cases'], 1)
        self.assertEqual(metrics['without_deadline_cases'], 1)
        self.assertEqual(metrics['rejected_cases'], 0)

    def test_student_detail_includes_rejected_cases_metric(self):
        make_case(
            beneficiary=self.beneficiary,
            assigned_student=self.student_two,
            deadline_date=None,
            state=Case.STATE_REJECTED,
        )
        self.client.force_login(self.profesor)
        response = self.client.get(
            reverse('academic_student_detail', args=[self.student_two.id])
        )
        metrics = response.context['metrics']
        self.assertEqual(metrics['rejected_cases'], 1)

    def test_dashboard_can_filter_by_student(self):
        self.client.force_login(self.profesor)
        response = self.client.get(
            reverse('academic_dashboard'),
            {'estudiante': str(self.student_one.id)},
        )
        self.assertEqual(response.status_code, 200)
        students = list(response.context['students'])
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0], self.student_one)
        self.assertEqual(response.context['total_assigned_cases'], 2)

    def test_dashboard_sala_filter_hides_students_without_cases_in_selected_sala(self):
        make_case(
            beneficiary=self.beneficiary,
            assigned_student=self.student_two,
            sala=Case.ROOM_PENAL,
            deadline_date=timezone.localdate() + timedelta(days=5),
            state=Case.STATE_ASSIGNED,
        )
        self.client.force_login(self.profesor)
        response = self.client.get(
            reverse('academic_dashboard'),
            {'sala': Case.ROOM_PENAL},
        )
        self.assertEqual(response.status_code, 200)
        students = list(response.context['students'])
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0], self.student_two)


class AcademicDashboardExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_acad_export', group_name=ROLE_ADMINISTRADOR)
        self.profesor = make_user('prof_acad_export', group_name=ROLE_PROFESOR)
        self.secretaria = make_user('sec_acad_export', group_name=ROLE_SECRETARIA)

    def test_admin_can_export_excel(self):
        self.client.login(username='admin_acad_export', password='pass1234')
        response = self.client.get(reverse('academic_dashboard_export_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_profesor_can_export_excel(self):
        self.client.login(username='prof_acad_export', password='pass1234')
        response = self.client.get(reverse('academic_dashboard_export_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_secretaria_cannot_export_excel(self):
        self.client.login(username='sec_acad_export', password='pass1234')
        response = self.client.get(reverse('academic_dashboard_export_excel'))
        self.assertEqual(response.status_code, 302)

    def test_admin_can_export_pdf(self):
        self.client.login(username='admin_acad_export', password='pass1234')
        response = self.client.get(reverse('academic_dashboard_export_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_profesor_can_export_pdf(self):
        self.client.login(username='prof_acad_export', password='pass1234')
        response = self.client.get(reverse('academic_dashboard_export_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_secretaria_cannot_export_pdf(self):
        self.client.login(username='sec_acad_export', password='pass1234')
        response = self.client.get(reverse('academic_dashboard_export_pdf'))
        self.assertEqual(response.status_code, 302)
