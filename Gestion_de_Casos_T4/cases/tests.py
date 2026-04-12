import shutil
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from accounts.constants import (
    ROLE_ESTUDIANTE,
    ROLE_PROFESOR,
    ROLE_SECRETARIA,
)
from beneficiary.models import Beneficiary
from cases.forms import CaseForm
from cases.models import Case, CaseDocument, CaseReassignmentLog


TEST_MEDIA_ROOT = Path(settings.BASE_DIR) / 'test_media'


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class HU6CaseRegistrationTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()

        self.secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
        self.student_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)

        self.secretaria = User.objects.create_user(
            username='secretaria_hu6',
            password='clave_segura_123'
        )
        self.secretaria.groups.add(self.secretaria_group)

        self.student = User.objects.create_user(
            username='estudiante_hu6',
            first_name='Ana',
            last_name='Torres',
            password='clave_segura_123'
        )
        self.student.groups.add(self.student_group)

        self.beneficiary = Beneficiary.objects.create(
            name='Laura Perez',
            location='Cali',
            phone='3001234567',
            email='laura@example.com',
        )

    def test_case_code_is_generated_incrementally(self):
        first_case = Case.objects.create(
            sala=Case.ROOM_CIVIL,
            description='Primer caso de prueba',
            beneficiary=self.beneficiary,
        )
        second_case = Case.objects.create(
            sala=Case.ROOM_PENAL,
            description='Segundo caso de prueba',
            beneficiary=self.beneficiary,
        )

        self.assertRegex(first_case.code, r'^CJ-\d{4}-0001$')
        self.assertRegex(second_case.code, r'^CJ-\d{4}-0002$')

    def test_case_form_rejects_invalid_file_extension(self):
        invalid_file = SimpleUploadedFile(
            'evidencia.exe',
            b'archivo no permitido',
            content_type='application/octet-stream',
        )
        form = CaseForm(
            data={
                'sala': Case.ROOM_CIVIL,
                'description': 'Caso con archivo invalido',
                'beneficiary': self.beneficiary.pk,
                'assigned_student': self.student.pk,
            },
            files=MultiValueDict({'documents': [invalid_file]}),
        )

        self.assertFalse(form.is_valid())
        self.assertIn('documents', form.errors)

    def test_assigned_student_field_only_shows_students(self):
        profesor_group, _ = Group.objects.get_or_create(name=ROLE_PROFESOR)
        professor = User.objects.create_user(
            username='profesor_hu6',
            password='clave_segura_123'
        )
        professor.groups.add(profesor_group)

        form = CaseForm()
        available_students = list(form.fields['assigned_student'].queryset)

        self.assertIn(self.student, available_students)
        self.assertNotIn(professor, available_students)

    def test_case_and_documents_are_saved_correctly(self):
        uploaded_file = SimpleUploadedFile(
            'soporte.pdf',
            b'%PDF-1.4 archivo de prueba',
            content_type='application/pdf',
        )
        form = CaseForm(
            data={
                'sala': Case.ROOM_LABORAL,
                'description': 'Conflicto laboral con soporte adjunto',
                'beneficiary': self.beneficiary.pk,
                'assigned_student': self.student.pk,
            },
            files=MultiValueDict({'documents': [uploaded_file]}),
        )

        self.assertTrue(form.is_valid(), form.errors)

        created_case = form.save()
        CaseDocument.objects.create(case=created_case, file=uploaded_file)

        self.assertEqual(created_case.beneficiary, self.beneficiary)
        self.assertEqual(created_case.assigned_student, self.student)
        self.assertEqual(created_case.state, Case.STATE_PENDING)
        self.assertEqual(created_case.documents.count(), 1)
        self.assertEqual(CaseDocument.objects.filter(case=created_case).count(), 1)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class HU12CaseAccessControlTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
        self.profesor_group, _ = Group.objects.get_or_create(name=ROLE_PROFESOR)
        self.student_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)

        self.secretaria = User.objects.create_user(
            username='secretaria_hu12',
            password='clave_segura_123'
        )
        self.secretaria.groups.add(self.secretaria_group)

        self.profesor = User.objects.create_user(
            username='profesor_hu12',
            password='clave_segura_123'
        )
        self.profesor.groups.add(self.profesor_group)

        self.assigned_student = User.objects.create_user(
            username='estudiante_asignado_hu12',
            password='clave_segura_123'
        )
        self.assigned_student.groups.add(self.student_group)

        self.other_student = User.objects.create_user(
            username='estudiante_no_asignado_hu12',
            password='clave_segura_123'
        )
        self.other_student.groups.add(self.student_group)

        self.beneficiary = Beneficiary.objects.create(
            name='Carlos Ramirez',
            location='Bogota',
            phone='3112223344',
            email='carlos@example.com',
        )

        self.case = Case.objects.create(
            sala=Case.ROOM_FAMILIA,
            description='Caso para pruebas de acceso',
            beneficiary=self.beneficiary,
            assigned_student=self.assigned_student,
            state=Case.STATE_ASSIGNED,
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse('case_detail', kwargs={'pk': self.case.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_secretaria_can_access_case_detail(self):
        self.client.force_login(self.secretaria)

        response = self.client.get(reverse('case_detail', kwargs={'pk': self.case.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.case.code)

    def test_profesor_can_access_case_detail(self):
        self.client.force_login(self.profesor)

        response = self.client.get(reverse('case_detail', kwargs={'pk': self.case.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.case.code)

    def test_assigned_student_can_access_case_detail(self):
        self.client.force_login(self.assigned_student)

        response = self.client.get(reverse('case_detail', kwargs={'pk': self.case.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Estudiante asignado')

    def test_unassigned_student_is_redirected_with_error_message(self):
        self.client.force_login(self.other_student)

        response = self.client.get(reverse('case_detail', kwargs={'pk': self.case.pk}), follow=True)

        self.assertRedirects(response, reverse('case_list'))
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('No tienes permisos para acceder a este caso.', messages)


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
