import shutil
from datetime import timedelta
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils import timezone

from accounts.constants import (
    ROLE_ADMINISTRADOR,
    ROLE_ESTUDIANTE,
    ROLE_PROFESOR,
    ROLE_SECRETARIA,
)
from accounts.models import UserProfile
from beneficiary.models import Beneficiary
from cases.forms import CaseForm
from cases.models import Case, CaseDocument, CaseReassignmentLog, Notification
from cases.services import auto_assign_case, get_available_student


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
            id='1001001001',
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
            id='2002002002',
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
        self.assigned_student.profile.supervising_professor = self.profesor
        self.assigned_student.profile.save()

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


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class HU32CaseDraftTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
        self.secretaria = User.objects.create_user(
            username='secretaria_hu32',
            password='clave_segura_123'
        )
        self.secretaria.groups.add(self.secretaria_group)

        self.beneficiary = Beneficiary.objects.create(
            id='3203203203',
            name='Juliana Ruiz',
            location='Cali',
            phone='3001234560',
            email='juliana@example.com',
        )

    def test_secretaria_can_save_incomplete_case_as_draft(self):
        self.client.force_login(self.secretaria)

        response = self.client.post(
            reverse('case_create'),
            {
                'description': 'Borrador sin informacion completa',
                'submit_action': 'draft',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        created_case = Case.objects.get(created_by=self.secretaria)
        self.assertEqual(created_case.status, Case.STATUS_DRAFT)
        self.assertEqual(created_case.description, 'Borrador sin informacion completa')
        self.assertIsNone(created_case.beneficiary)
        self.assertIsNone(created_case.sala)

    def test_existing_user_draft_is_loaded_on_form(self):
        draft_case = Case.objects.create(
            description='Texto recuperado del borrador',
            created_by=self.secretaria,
            status=Case.STATUS_DRAFT,
            beneficiary=self.beneficiary,

        )

        self.client.force_login(self.secretaria)
        response = self.client.get(reverse('case_create'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['draft_case'], draft_case)
        self.assertContains(response, 'Texto recuperado del borrador')

    def test_user_can_see_only_own_drafts_in_draft_list(self):
        own_draft = Case.objects.create(
            description='Borrador propio',
            created_by=self.secretaria,
            status=Case.STATUS_DRAFT,
            beneficiary=self.beneficiary,
        )
        other_user = User.objects.create_user(
            username='otra_secretaria_hu32',
            password='clave_segura_123'
        )
        other_user.groups.add(self.secretaria_group)
        Case.objects.create(
            description='Borrador ajeno',
            created_by=other_user,
            status=Case.STATUS_DRAFT,
        )

        self.client.force_login(self.secretaria)
        response = self.client.get(reverse('case_draft_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_draft.code)
        self.assertNotContains(response, 'Borrador ajeno')

    def test_user_can_continue_editing_existing_draft(self):
        draft_case = Case.objects.create(
            description='Version inicial del borrador',
            created_by=self.secretaria,
            status=Case.STATUS_DRAFT,
            beneficiary=self.beneficiary,
        )

        self.client.force_login(self.secretaria)
        response = self.client.post(
            reverse('case_edit_draft', args=[draft_case.pk]),
            {
                'sala': Case.ROOM_CIVIL,
                'description': 'Version actualizada del borrador',
                'beneficiary': self.beneficiary.pk,
                'submit_action': 'draft',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        draft_case.refresh_from_db()
        self.assertEqual(draft_case.status, Case.STATUS_DRAFT)
        self.assertEqual(draft_case.sala, Case.ROOM_CIVIL)
        self.assertEqual(draft_case.description, 'Version actualizada del borrador')
        self.assertEqual(draft_case.beneficiary, self.beneficiary)

    def test_draft_form_allows_partial_submission_without_documents(self):
        form = CaseForm(
            data={
                'description': 'Formulario parcial',
            },
            allow_partial=True,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['documents'], [])

    def test_complete_submission_requires_documents(self):
        form = CaseForm(
            data={
                'sala': Case.ROOM_CIVIL,
                'description': 'Caso completo sin archivos',
                'beneficiary': self.beneficiary.pk,
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn('documents', form.errors)

    def test_user_can_complete_draft_and_is_redirected_to_detail(self):
        draft_case = Case.objects.create(
            description='Borrador listo para completar',
            created_by=self.secretaria,
            status=Case.STATUS_DRAFT,
            beneficiary=self.beneficiary,
        )
        student_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)
        student = User.objects.create_user(
            username='estudiante_hu32',
            first_name='Juan',
            last_name='Rios',
            password='clave_segura_123',
        )
        student.groups.add(student_group)

        self.client.force_login(self.secretaria)
        uploaded_file = SimpleUploadedFile(
            'borrador.pdf',
            b'%PDF-1.4 borrador completado',
            content_type='application/pdf',
        )

        response = self.client.post(
            reverse('case_edit_draft', args=[draft_case.pk]),
            {
                'sala': Case.ROOM_PENAL,
                'description': 'Caso completado desde borrador',
                'beneficiary': self.beneficiary.pk,
                'assigned_student': student.pk,
                'submit_action': 'complete',
                'documents': uploaded_file,
            },
        )

        self.assertEqual(response.status_code, 302)
        draft_case.refresh_from_db()
        self.assertEqual(draft_case.status, Case.STATUS_COMPLETE)
        self.assertEqual(draft_case.beneficiary, self.beneficiary)
        self.assertTrue(
            response.url.endswith(reverse('case_detail', kwargs={'pk': draft_case.pk}))
        )

    def test_other_user_cannot_edit_foreign_draft(self):
        draft_case = Case.objects.create(
            description='Borrador privado',
            created_by=self.secretaria,
            status=Case.STATUS_DRAFT,
            beneficiary=self.beneficiary,
        )
        other_secretaria = User.objects.create_user(
            username='secretaria_hu32_2',
            password='clave_segura_123',
        )
        other_secretaria.groups.add(self.secretaria_group)

        self.client.force_login(other_secretaria)
        response = self.client.get(
            reverse('case_edit_draft', args=[draft_case.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse('case_draft_list'))
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('No tienes permisos para editar este borrador.', messages)


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
            id='3003003003',
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


class HU10CaseRejectionTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
        self.profesor_group, _ = Group.objects.get_or_create(name=ROLE_PROFESOR)

        self.secretaria = User.objects.create_user(
            username='secretaria_hu10',
            password='testpass123'
        )
        self.secretaria.groups.add(self.secretaria_group)

        self.profesor = User.objects.create_user(
            username='profesor_hu10',
            password='testpass123'
        )
        self.profesor.groups.add(self.profesor_group)

        self.beneficiary = Beneficiary.objects.create(
            id='3103103103',
            name='Ana Rojas',
            location='Bogota',
            phone='3009876543',
            email='ana.rojas@example.com'
        )

        self.case = Case.objects.create(
            sala=Case.ROOM_CIVIL,
            description='Caso para validar rechazo',
            beneficiary=self.beneficiary,
            state=Case.STATE_PENDING,
        )

    def test_secretaria_can_reject_case_with_reason(self):
        self.client.force_login(self.secretaria)

        response = self.client.post(
            reverse('case_reject', args=[self.case.pk]),
            {'rejection_reason': 'No competencia del consultorio juridico.'},
        )

        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.state, Case.STATE_REJECTED)
        self.assertEqual(
            self.case.rejection_reason,
            'No competencia del consultorio juridico.'
        )

    def test_secretaria_cannot_reject_case_without_reason(self):
        self.client.force_login(self.secretaria)

        response = self.client.post(
            reverse('case_reject', args=[self.case.pk]),
            {'rejection_reason': '   '},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.case.refresh_from_db()
        self.assertEqual(self.case.state, Case.STATE_PENDING)
        self.assertIsNone(self.case.rejection_reason)
        self.assertContains(response, 'Debe ingresar una causal de rechazo válida.')

    def test_profesor_can_reject_case_with_reason(self):
        self.client.force_login(self.profesor)

        response = self.client.post(
            reverse('case_reject', args=[self.case.pk]),
            {'rejection_reason': 'El asunto no es de naturaleza juridica.'},
        )

        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.state, Case.STATE_REJECTED)
        self.assertEqual(
            self.case.rejection_reason,
            'El asunto no es de naturaleza juridica.'
        )


class HU11DeadlineTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
        self.profesor_group, _ = Group.objects.get_or_create(name=ROLE_PROFESOR)
        self.student_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)

        self.secretaria = User.objects.create_user(
            username='secretaria_hu11',
            password='testpass123'
        )
        self.secretaria.groups.add(self.secretaria_group)

        self.profesor = User.objects.create_user(
            username='profesor_hu11',
            password='testpass123'
        )
        self.profesor.groups.add(self.profesor_group)

        self.student = User.objects.create_user(
            username='estudiante_hu11',
            password='testpass123'
        )
        self.student.groups.add(self.student_group)

        self.beneficiary = Beneficiary.objects.create(
            id='4004004004',
            name='Maria Lopez',
            location='Cali',
            phone='3001112233',
            email='maria@example.com'
        )

        self.case = Case.objects.create(
            sala=Case.ROOM_PENAL,
            description='Caso con vencimiento próximo',
            beneficiary=self.beneficiary,
            assigned_student=self.student,
            state=Case.STATE_ASSIGNED,
        )

    def test_secretary_can_register_deadline_from_case_detail(self):
        self.client.login(username='secretaria_hu11', password='testpass123')

        deadline_value = timezone.localdate() + timedelta(days=7)
        response = self.client.post(
            reverse('case_update_deadline', args=[self.case.pk]),
            {'deadline_date': deadline_value.isoformat()},
        )

        self.assertEqual(response.status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.deadline_date, deadline_value)

    def test_deadline_alert_command_creates_notifications_once(self):
        self.case.deadline_date = timezone.localdate() + timedelta(days=2)
        self.case.save(update_fields=['deadline_date'])

        call_command('generate_deadline_alerts', days=3)

        notifications = Notification.objects.filter(case=self.case, notification_type='DEADLINE')
        self.assertEqual(notifications.count(), 2)
        self.assertTrue(notifications.filter(recipient_user=self.student).exists())
        self.assertTrue(notifications.filter(recipient_user=self.secretaria).exists())
        self.assertTrue(notifications.filter(recipient_user=self.profesor).exists())

        call_command('generate_deadline_alerts', days=3)

        self.assertEqual(
            Notification.objects.filter(case=self.case, notification_type='DEADLINE').count(),
            3,
        )


class CaseQuickViewPriorityTests(TestCase):
    def setUp(self):
        self.client = Client()
        secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)

        self.secretaria = User.objects.create_user(
            username='secretaria_quick_view',
            password='testpass123'
        )
        self.secretaria.groups.add(secretaria_group)

        self.beneficiary = Beneficiary.objects.create(
            id='5005005005',
            name='Pedro Martinez',
            location='Medellin',
            phone='3005556677',
            email='pedro@example.com'
        )

    def test_case_list_shows_deadline_status_and_priority_colors(self):
        today = timezone.localdate()

        overdue_case = Case.objects.create(
            sala=Case.ROOM_CIVIL,
            description='Caso vencido',
            beneficiary=self.beneficiary,
            deadline_date=today - timedelta(days=1),
        )
        high_case = Case.objects.create(
            sala=Case.ROOM_LABORAL,
            description='Caso alta prioridad',
            beneficiary=self.beneficiary,
            deadline_date=today + timedelta(days=2),
        )
        no_deadline_case = Case.objects.create(
            sala=Case.ROOM_PENAL,
            description='Caso sin fecha limite',
            beneficiary=self.beneficiary,
        )

        self.client.force_login(self.secretaria)
        response = self.client.get(reverse('case_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, overdue_case.code)
        self.assertContains(response, high_case.code)
        self.assertContains(response, no_deadline_case.code)

        self.assertContains(response, 'priority-critical')
        self.assertContains(response, 'priority-high')
        self.assertContains(response, 'priority-none')
        self.assertContains(response, 'Vencido hace 1 dia(s)')
        self.assertContains(response, 'Vence en 2 dia(s)')
        self.assertContains(response, 'Sin fecha limite')


class HU31RoleAccessControlTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
        self.student_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)
        self.profesor_group, _ = Group.objects.get_or_create(name=ROLE_PROFESOR)
        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMINISTRADOR)

        self.secretaria = User.objects.create_user(
            username='secretaria_hu31', password='clave_segura_123'
        )
        self.secretaria.groups.add(self.secretaria_group)

        self.student = User.objects.create_user(
            username='estudiante_hu31', password='clave_segura_123'
        )
        self.student.groups.add(self.student_group)

        self.profesor = User.objects.create_user(
            username='profesor_hu31', password='clave_segura_123'
        )
        self.profesor.groups.add(self.profesor_group)

        self.admin = User.objects.create_user(
            username='admin_hu31', password='clave_segura_123'
        )
        self.admin.groups.add(self.admin_group)

    def test_secretaria_can_access_case_create(self):
        self.client.force_login(self.secretaria)
        response = self.client.get(reverse('case_create'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_case_create(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('case_create'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_case_create(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('case_create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(reverse('no_permission'), response.url)

    def test_profesor_cannot_access_case_create(self):
        self.client.force_login(self.profesor)
        response = self.client.get(reverse('case_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('no_permission'), response.url)

    def test_anonymous_user_redirected_to_login_on_case_create(self):
        response = self.client.get(reverse('case_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_anonymous_user_redirected_to_login_on_case_list(self):
        response = self.client.get(reverse('case_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_any_authenticated_user_can_access_case_list(self):
        for user in [self.secretaria, self.student, self.profesor, self.admin]:
            self.client.force_login(user)
            response = self.client.get(reverse('case_list'))
            self.assertEqual(
                response.status_code, 200,
                f'{user.username} deberia poder ver la lista de casos'
            )

    def test_superuser_bypasses_role_restriction(self):
        superuser = User.objects.create_superuser(
            username='super_hu31', password='clave_segura_123'
        )
        self.client.force_login(superuser)
        response = self.client.get(reverse('case_create'))
        self.assertEqual(response.status_code, 200)


class HU7AutoAssignCaseTests(TestCase):

    def setUp(self):
        self.student_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)

        self.student_a = User.objects.create_user(
            username='estudiante_a_hu7', first_name='Ana', last_name='Lopez',
            password='clave_segura_123'
        )
        self.student_a.groups.add(self.student_group)
        self.student_a.profile.max_cases = 3
        self.student_a.profile.student_code = 'EST001'
        self.student_a.profile.availability = True
        self.student_a.profile.save()

        self.student_b = User.objects.create_user(
            username='estudiante_b_hu7', first_name='Luis', last_name='Garcia',
            password='clave_segura_123'
        )
        self.student_b.groups.add(self.student_group)
        self.student_b.profile.max_cases = 3
        self.student_b.profile.student_code = 'EST002'
        self.student_b.profile.availability = True
        self.student_b.profile.save()

        self.beneficiary = Beneficiary.objects.create(
            id='4004004004',
            name='Maria Test', location='Cali',
            phone='3009999999', email='maria@test.com',
        )

    def _create_case(self, student=None):
        case = Case.objects.create(
            sala=Case.ROOM_CIVIL,
            description='Caso auto test',
            beneficiary=self.beneficiary,
            assigned_student=student,
            state=Case.STATE_ASSIGNED if student else Case.STATE_PENDING,
        )
        return case

    def test_auto_assign_picks_student_with_least_load(self):
        self._create_case(student=self.student_a)
        self._create_case(student=self.student_a)

        new_case = Case.objects.create(
            sala=Case.ROOM_PENAL,
            description='Caso nuevo para asignar',
            beneficiary=self.beneficiary,
        )
        assigned = auto_assign_case(new_case)

        self.assertEqual(assigned, self.student_b)
        new_case.refresh_from_db()
        self.assertEqual(new_case.assigned_student, self.student_b)
        self.assertEqual(new_case.state, Case.STATE_ASSIGNED)

    def test_auto_assign_returns_none_when_all_students_at_capacity(self):
        self.student_a.profile.max_cases = 1
        self.student_a.profile.save()
        self.student_b.profile.max_cases = 1
        self.student_b.profile.save()

        self._create_case(student=self.student_a)
        self._create_case(student=self.student_b)

        new_case = Case.objects.create(
            sala=Case.ROOM_LABORAL,
            description='Caso sin estudiantes disponibles',
            beneficiary=self.beneficiary,
        )
        assigned = auto_assign_case(new_case)

        self.assertIsNone(assigned)
        new_case.refresh_from_db()
        self.assertIsNone(new_case.assigned_student)
        self.assertEqual(new_case.state, Case.STATE_NO_STUDENTS)

    def test_auto_assign_with_no_students_in_system(self):
        self.student_a.groups.clear()
        self.student_b.groups.clear()

        new_case = Case.objects.create(
            sala=Case.ROOM_FAMILIA,
            description='Caso sin estudiantes registrados',
            beneficiary=self.beneficiary,
        )
        assigned = auto_assign_case(new_case)

        self.assertIsNone(assigned)
        new_case.refresh_from_db()
        self.assertEqual(new_case.state, Case.STATE_NO_STUDENTS)

    def test_get_available_student_respects_max_cases(self):
        self.student_a.profile.max_cases = 2
        self.student_a.profile.save()
        self.student_b.profile.max_cases = 2
        self.student_b.profile.save()

        self._create_case(student=self.student_a)
        self._create_case(student=self.student_a)

        student = get_available_student()
        self.assertEqual(student, self.student_b)

    def test_get_available_student_skips_inactive_users(self):
        self.student_a.is_active = False
        self.student_a.save()

        student = get_available_student()
        self.assertEqual(student, self.student_b)

    def test_auto_assign_via_view_secretaria(self):
        secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
        secretaria = User.objects.create_user(
            username='secretaria_hu7', password='clave_segura_123'
        )
        secretaria.groups.add(secretaria_group)
        self.client.force_login(secretaria)

        test_file = SimpleUploadedFile(
            'documento.pdf',
            b'%PDF-1.4 test',
            content_type='application/pdf',
        )

        response = self.client.post(reverse('case_create'), {
            'sala': Case.ROOM_CIVIL,
            'description': 'Caso creado por secretaria para auto-asignar',
            'beneficiary': self.beneficiary.pk,
            'documents': test_file,
        })

        self.assertEqual(response.status_code, 302)
        created_case = Case.objects.order_by('-created_at').first()
        self.assertIsNotNone(created_case.assigned_student)
        self.assertIn(
            created_case.assigned_student,
            [self.student_a, self.student_b]
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
class HU37ReportByStateTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()
        self.url = reverse('case_report_by_state')

        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMINISTRADOR)
        self.profesor_group, _ = Group.objects.get_or_create(name=ROLE_PROFESOR)
        self.secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
        self.estudiante_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)

        self.admin_user = User.objects.create_user(
            username='admin_hu37',
            password='clave_segura_123',
        )
        self.admin_user.groups.add(self.admin_group)

        self.estudiante_user = User.objects.create_user(
            username='estudiante_hu37',
            password='clave_segura_123',
        )
        self.estudiante_user.groups.add(self.estudiante_group)

        self.secretaria_user = User.objects.create_user(
            username='secretaria_hu37',
            password='clave_segura_123',
        )
        self.secretaria_user.groups.add(self.secretaria_group)

        self.beneficiary = Beneficiary.objects.create(
            name='Reporte Test',
            location='Cali',
            phone='3000000000',
            email='reporte@test.com',
        )

        self.case_pending = Case.objects.create(
            sala=Case.ROOM_CIVIL,
            description='Caso pendiente',
            beneficiary=self.beneficiary,
            state=Case.STATE_PENDING,
        )
        self.case_assigned_1 = Case.objects.create(
            sala=Case.ROOM_PENAL,
            description='Caso asignado 1',
            beneficiary=self.beneficiary,
            state=Case.STATE_ASSIGNED,
        )
        self.case_assigned_2 = Case.objects.create(
            sala=Case.ROOM_PENAL,
            description='Caso asignado 2',
            beneficiary=self.beneficiary,
            state=Case.STATE_ASSIGNED,
        )
        self.case_rejected = Case.objects.create(
            sala=Case.ROOM_LABORAL,
            description='Caso rechazado',
            beneficiary=self.beneficiary,
            state=Case.STATE_REJECTED,
        )

    def _rows_by_state(self, response):
        return {row['estado']: row for row in response.context['rows']}

    def test_admin_can_view_report(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 4)

    def test_profesor_can_view_report(self):
        profesor = User.objects.create_user(
            username='profesor_hu37',
            password='clave_segura_123',
        )
        profesor.groups.add(self.profesor_group)
        self.client.force_login(profesor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_estudiante_is_denied(self):
        self.client.force_login(self.estudiante_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_secretaria_is_denied(self):
        self.client.force_login(self.secretaria_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_counts_per_state_are_correct(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        rows = self._rows_by_state(response)

        self.assertEqual(rows[Case.STATE_PENDING]['cantidad'], 1)
        self.assertEqual(rows[Case.STATE_ASSIGNED]['cantidad'], 2)
        self.assertEqual(rows[Case.STATE_REJECTED]['cantidad'], 1)
        self.assertEqual(rows[Case.STATE_NO_STUDENTS]['cantidad'], 0)

    def test_percentages_sum_to_100_when_data_exists(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        total_pct = sum(row['porcentaje'] for row in response.context['rows'])
        self.assertAlmostEqual(total_pct, 100.0, places=0)

    def test_filter_by_sala(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url, {'sala': Case.ROOM_PENAL})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 2)
        rows = self._rows_by_state(response)
        self.assertEqual(rows[Case.STATE_ASSIGNED]['cantidad'], 2)
        self.assertEqual(rows[Case.STATE_PENDING]['cantidad'], 0)

    def test_filter_by_date_range_excludes_outside_cases(self):
        old_case = Case.objects.create(
            sala=Case.ROOM_CIVIL,
            description='Caso antiguo',
            beneficiary=self.beneficiary,
            state=Case.STATE_PENDING,
        )
        Case.objects.filter(pk=old_case.pk).update(
            created_at=timezone.now() - timedelta(days=365)
        )

        self.client.force_login(self.admin_user)
        today = timezone.localdate()
        response = self.client.get(self.url, {
            'desde': (today - timedelta(days=7)).isoformat(),
            'hasta': today.isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 4)

    def test_invalid_sala_filter_is_ignored(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url, {'sala': 'fake-sala'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 4)
        self.assertEqual(response.context['filtro_sala'], '')

    def test_invalid_date_filter_is_ignored(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url, {'desde': 'not-a-date'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 4)


class HU36ReportBySalaTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = Client()
        self.url = reverse('case_report_by_sala')

        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMINISTRADOR)
        self.profesor_group, _ = Group.objects.get_or_create(name=ROLE_PROFESOR)
        self.secretaria_group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
        self.estudiante_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)

        self.admin_user = User.objects.create_user(
            username='admin_hu36', password='clave_segura_123',
        )
        self.admin_user.groups.add(self.admin_group)

        self.estudiante_user = User.objects.create_user(
            username='estudiante_hu36', password='clave_segura_123',
        )
        self.estudiante_user.groups.add(self.estudiante_group)

        self.secretaria_user = User.objects.create_user(
            username='secretaria_hu36', password='clave_segura_123',
        )
        self.secretaria_user.groups.add(self.secretaria_group)

        self.beneficiary = Beneficiary.objects.create(
            name='Reporte Sala Test',
            location='Cali',
            phone='3001111111',
            email='reportesala@test.com',
        )

        self.case_civil = Case.objects.create(
            sala=Case.ROOM_CIVIL,
            description='Caso civil',
            beneficiary=self.beneficiary,
            state=Case.STATE_PENDING,
        )
        self.case_penal_1 = Case.objects.create(
            sala=Case.ROOM_PENAL,
            description='Caso penal 1',
            beneficiary=self.beneficiary,
            state=Case.STATE_ASSIGNED,
        )
        self.case_penal_2 = Case.objects.create(
            sala=Case.ROOM_PENAL,
            description='Caso penal 2',
            beneficiary=self.beneficiary,
            state=Case.STATE_ASSIGNED,
        )
        self.case_laboral = Case.objects.create(
            sala=Case.ROOM_LABORAL,
            description='Caso laboral',
            beneficiary=self.beneficiary,
            state=Case.STATE_REJECTED,
        )

    def _rows_by_sala(self, response):
        return {row['sala']: row for row in response.context['rows']}

    def test_admin_can_view_report(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 4)

    def test_profesor_can_view_report(self):
        profesor = User.objects.create_user(
            username='profesor_hu36', password='clave_segura_123',
        )
        profesor.groups.add(self.profesor_group)
        self.client.force_login(profesor)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_estudiante_is_denied(self):
        self.client.force_login(self.estudiante_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_secretaria_is_denied(self):
        self.client.force_login(self.secretaria_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_counts_per_sala_are_correct(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        rows = self._rows_by_sala(response)
        self.assertEqual(rows['Civil']['cantidad'], 1)
        self.assertEqual(rows['Penal']['cantidad'], 2)
        self.assertEqual(rows['Laboral']['cantidad'], 1)
        self.assertEqual(rows['Publico']['cantidad'], 0)
        self.assertEqual(rows['Familia']['cantidad'], 0)

    def test_percentages_sum_to_100_when_data_exists(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)
        total_pct = sum(row['porcentaje'] for row in response.context['rows'])
        self.assertAlmostEqual(total_pct, 100.0, places=0)

    def test_filter_by_estado(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url, {'estado': Case.STATE_ASSIGNED})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 2)
        rows = self._rows_by_sala(response)
        self.assertEqual(rows['Penal']['cantidad'], 2)
        self.assertEqual(rows['Civil']['cantidad'], 0)

    def test_filter_by_date_range_excludes_outside_cases(self):
        old_case = Case.objects.create(
            sala=Case.ROOM_FAMILIA,
            description='Caso antiguo',
            beneficiary=self.beneficiary,
            state=Case.STATE_PENDING,
        )
        Case.objects.filter(pk=old_case.pk).update(
            created_at=timezone.now() - timedelta(days=365)
        )
        self.client.force_login(self.admin_user)
        today = timezone.localdate()
        response = self.client.get(self.url, {
            'desde': (today - timedelta(days=7)).isoformat(),
            'hasta': today.isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 4)

    def test_invalid_estado_filter_is_ignored(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url, {'estado': 'estado-inexistente'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 4)
        self.assertEqual(response.context['filtro_estado'], '')

    def test_invalid_date_filter_is_ignored(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url, {'desde': 'not-a-date'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 4)
