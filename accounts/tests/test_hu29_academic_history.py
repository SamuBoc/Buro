from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_ESTUDIANTE, ROLE_PROFESOR
from beneficiary.models import Beneficiary
from cases.models import Case, CaseEvaluation, CaseReassignmentLog


class HU29AcademicHistoryTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_group = Group.objects.create(name=ROLE_ADMINISTRADOR)
        self.professor_group = Group.objects.create(name=ROLE_PROFESOR)
        self.student_group = Group.objects.create(name=ROLE_ESTUDIANTE)

        self.admin_user = User.objects.create_user(
            username='admin_hu29',
            password='clave_segura_123',
            first_name='Ana',
            last_name='Admin',
        )
        self.admin_user.groups.add(self.admin_group)

        self.professor_user = User.objects.create_user(
            username='profesor_hu29',
            password='clave_segura_123',
            first_name='Paula',
            last_name='Profesor',
        )
        self.professor_user.groups.add(self.professor_group)

        self.student_user = User.objects.create_user(
            username='estudiante_hu29',
            password='clave_segura_123',
            first_name='Luis',
            last_name='Estudiante',
        )
        self.student_user.groups.add(self.student_group)
        self.student_user.profile.student_code = '20262001'
        self.student_user.profile.save()

        self.other_student = User.objects.create_user(
            username='estudiante_hu29_b',
            password='clave_segura_123',
            first_name='Maria',
            last_name='Apoyo',
        )
        self.other_student.groups.add(self.student_group)

        self.beneficiary = Beneficiary.objects.create(
            name='Beneficiario HU29',
            colombian_identification='987654321',
            location='Cali',
            phone='3009876543',
            email='beneficiario_hu29@test.com',
        )

        self.active_case = Case.objects.create(
            sala=Case.ROOM_CIVIL,
            description='Caso activo del estudiante',
            beneficiary=self.beneficiary,
            assigned_student=self.student_user,
            status=Case.STATUS_COMPLETE,
            state=Case.STATE_ASSIGNED,
        )

        self.historic_case = Case.objects.create(
            sala=Case.ROOM_PENAL,
            description='Caso reasignado',
            beneficiary=self.beneficiary,
            assigned_student=self.student_user,
            status=Case.STATUS_COMPLETE,
            state=Case.STATE_ASSIGNED,
        )
        self.historic_case.assigned_student = self.other_student
        self.historic_case.save(update_fields=['assigned_student'])
        CaseReassignmentLog.objects.create(
            case=self.historic_case,
            old_student=self.student_user,
            new_student=self.other_student,
            changed_by=self.admin_user,
        )

        CaseEvaluation.objects.create(
            case=self.active_case,
            student=self.student_user,
            professor=self.professor_user,
            score=4,
            feedback='Buen manejo del caso y comunicacion con el beneficiario.',
        )

    def test_professor_can_view_academic_history(self):
        self.client.login(username='profesor_hu29', password='clave_segura_123')

        response = self.client.get(reverse('academic_student_history', args=[self.student_user.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_case.code)
        self.assertContains(response, self.historic_case.code)

    def test_professor_sees_feedback_in_history(self):
        self.client.login(username='profesor_hu29', password='clave_segura_123')

        response = self.client.get(reverse('academic_student_history', args=[self.student_user.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buen manejo del caso y comunicacion con el beneficiario.')

    def test_professor_can_register_feedback(self):
        self.client.login(username='profesor_hu29', password='clave_segura_123')

        response = self.client.post(
            reverse('academic_student_add_evaluation', args=[self.student_user.pk]),
            data={
                'case': self.active_case.pk,
                'score': 5,
                'feedback': 'Excelente desempeno academico.',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            CaseEvaluation.objects.filter(
                student=self.student_user,
                case=self.active_case,
                feedback='Excelente desempeno academico.',
            ).exists()
        )
