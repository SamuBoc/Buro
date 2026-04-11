from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from beneficiary.models import Beneficiary

from .models import Case, CaseReassignmentLog


class CaseReassignmentTests(TestCase):
    def setUp(self):
        self.secretaria_group, _ = Group.objects.get_or_create(name='secretaria')
        self.estudiante_group, _ = Group.objects.get_or_create(name='estudiante')

        self.secretary = User.objects.create_user(
            username='secretaria1',
            password='testpass123'
        )
        self.secretary.groups.add(self.secretaria_group)

        self.old_student = User.objects.create_user(
            username='estudiante1',
            password='testpass123',
            first_name='Ana',
            last_name='Lopez'
        )
        self.old_student.groups.add(self.estudiante_group)

        self.new_student = User.objects.create_user(
            username='estudiante2',
            password='testpass123',
            first_name='Luis',
            last_name='Perez'
        )
        self.new_student.groups.add(self.estudiante_group)

        self.beneficiary = Beneficiary.objects.create(
            name='Carlos Gomez',
            location='Bogota',
            phone='3000000000',
            email='carlos@example.com'
        )

        self.case = Case.objects.create(
            sala=Case.ROOM_CIVIL,
            description='Caso de prueba',
            beneficiary=self.beneficiary,
            assigned_student=self.old_student,
            state=Case.STATE_ASSIGNED,
        )

    def test_secretary_can_reassign_case_and_create_log(self):
        self.client.login(username='secretaria1', password='testpass123')

        response = self.client.post(
            reverse('case_reassign', args=[self.case.pk]),
            {'assigned_student': self.new_student.pk}
        )

        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.assigned_student, self.new_student)
        self.assertEqual(self.case.state, Case.STATE_ASSIGNED)
        self.assertTrue(
            CaseReassignmentLog.objects.filter(
                case=self.case,
                old_student=self.old_student,
                new_student=self.new_student,
                changed_by=self.secretary,
            ).exists()
        )

    def test_user_without_permissions_cannot_reassign(self):
        User.objects.create_user(username='visitante', password='testpass123')
        self.client.login(username='visitante', password='testpass123')

        response = self.client.post(
            reverse('case_reassign', args=[self.case.pk]),
            {'assigned_student': self.new_student.pk}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('no_permission'), response.url)
        self.case.refresh_from_db()
        self.assertEqual(self.case.assigned_student, self.old_student)