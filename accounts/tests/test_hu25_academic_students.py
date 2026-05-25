from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.constants import (
    ROLE_ADMINISTRADOR,
    ROLE_ESTUDIANTE,
    ROLE_PROFESOR,
    ROLE_SECRETARIA,
)
from beneficiary.models import Beneficiary
from cases.models import Case


class HU25AcademicStudentsTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin_group = Group.objects.create(name=ROLE_ADMINISTRADOR)
        self.secretary_group = Group.objects.create(name=ROLE_SECRETARIA)
        self.student_group = Group.objects.create(name=ROLE_ESTUDIANTE)
        self.professor_group = Group.objects.create(name=ROLE_PROFESOR)

        self.admin_user = User.objects.create_user(
            username='admin_hu25',
            password='clave_segura_123',
            first_name='Ana',
            last_name='Admin',
            email='admin_hu25@test.com',
        )
        self.admin_user.groups.add(self.admin_group)

        self.secretary_user = User.objects.create_user(
            username='secretaria_hu25',
            password='clave_segura_123',
            first_name='Sara',
            last_name='Secretaria',
            email='secretaria_hu25@test.com',
        )
        self.secretary_user.groups.add(self.secretary_group)

        self.professor_user = User.objects.create_user(
            username='profesor_hu25',
            password='clave_segura_123',
            first_name='Pedro',
            last_name='Profesor',
            email='profesor_hu25@test.com',
        )
        self.professor_user.groups.add(self.professor_group)

        self.student_user = User.objects.create_user(
            username='estudiante_hu25',
            password='clave_segura_123',
            first_name='Laura',
            last_name='Martinez',
            email='estudiante_hu25@test.com',
        )
        self.student_user.groups.add(self.student_group)
        self.student_user.profile.student_code = '20261001'
        self.student_user.profile.max_cases = 6
        self.student_user.profile.availability = True
        self.student_user.profile.preferred_room = 'civil'
        self.student_user.profile.save()

        self.beneficiary = Beneficiary.objects.create(
            name='Beneficiario HU25',
            colombian_identification='123456789',
            location='Cali',
            phone='3001234567',
            email='beneficiario_hu25@test.com',
        )

        self.case_assigned = Case.objects.create(
            sala='civil',
            description='Caso asignado al estudiante',
            beneficiary=self.beneficiary,
            assigned_student=self.student_user,
            status=Case.STATUS_COMPLETE,
            state=Case.STATE_ASSIGNED,
        )

    def _registration_payload(self, **overrides):
        payload = {
            'first_name': 'Carlos',
            'last_name': 'Ramirez',
            'email': 'carlos.ramirez@test.com',
            'username': 'carlos_hu25',
            'student_code': '20261002',
            'max_cases': 4,
            'availability': 'on',
            'preferred_room': 'penal',
            'password': 'ClaveSegura123',
        }
        payload.update(overrides)
        return payload

    def test_admin_can_register_academic_student(self):
        self.client.login(username='admin_hu25', password='clave_segura_123')

        response = self.client.post(
            reverse('academic_student_register'),
            data=self._registration_payload(),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        created_user = User.objects.get(username='carlos_hu25')
        self.assertEqual(created_user.first_name, 'Carlos')
        self.assertEqual(created_user.profile.student_code, '20261002')
        self.assertEqual(created_user.profile.max_cases, 4)
        self.assertTrue(created_user.profile.availability)
        self.assertEqual(created_user.profile.preferred_room, 'penal')

    def test_registered_student_is_added_to_student_group(self):
        self.client.login(username='admin_hu25', password='clave_segura_123')

        self.client.post(
            reverse('academic_student_register'),
            data=self._registration_payload(
                username='grupo_hu25',
                email='grupo_hu25@test.com',
                student_code='20261003',
            ),
            follow=True,
        )

        created_user = User.objects.get(username='grupo_hu25')
        self.assertTrue(created_user.groups.filter(name=ROLE_ESTUDIANTE).exists())

    def test_admin_can_view_student_list(self):
        self.client.login(username='admin_hu25', password='clave_segura_123')

        response = self.client.get(reverse('academic_student_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Laura Martinez')
        self.assertContains(response, '20261001')
        self.assertContains(response, 'Civil')

    def test_secretary_cannot_access_student_detail(self):
        self.client.login(username='secretaria_hu25', password='clave_segura_123')

        response = self.client.get(
            reverse('academic_student_detail', args=[self.student_user.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Acceso restringido', status_code=403)

    def test_student_role_cannot_access_student_management_views(self):
        self.client.login(username='estudiante_hu25', password='clave_segura_123')

        list_response = self.client.get(reverse('academic_student_list'), follow=True)
        register_response = self.client.get(reverse('academic_student_register'), follow=True)
        detail_response = self.client.get(
            reverse('academic_student_detail', args=[self.student_user.pk]),
            follow=True,
        )

        self.assertEqual(list_response.status_code, 403)
        self.assertContains(list_response, 'Acceso restringido', status_code=403)
        self.assertEqual(register_response.status_code, 403)
        self.assertContains(register_response, 'Acceso restringido', status_code=403)
        self.assertEqual(detail_response.status_code, 403)
        self.assertContains(detail_response, 'Acceso restringido', status_code=403)

    def test_professor_role_can_access_student_management_views(self):
        self.client.login(username='profesor_hu25', password='clave_segura_123')

        response = self.client.get(reverse('academic_student_list'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Laura Martinez')

    def test_active_cases_count_is_calculated_from_assigned_cases(self):
        self.client.login(username='admin_hu25', password='clave_segura_123')

        Case.objects.create(
            sala='penal',
            description='Segundo caso activo',
            beneficiary=self.beneficiary,
            assigned_student=self.student_user,
            status=Case.STATUS_COMPLETE,
            state=Case.STATE_ASSIGNED,
        )
        Case.objects.create(
            sala='familia',
            description='Borrador no debe contar',
            beneficiary=self.beneficiary,
            assigned_student=self.student_user,
            status=Case.STATUS_DRAFT,
            state=Case.STATE_PENDING,
        )

        list_response = self.client.get(reverse('academic_student_list'))
        detail_response = self.client.get(
            reverse('academic_student_detail', args=[self.student_user.pk])
        )

        self.assertContains(list_response, '<td>2</td>', html=True)
        self.assertContains(detail_response, '<div class="fw-semibold">2</div>', html=True)

    def test_student_code_must_be_unique(self):
        self.client.login(username='admin_hu25', password='clave_segura_123')

        response = self.client.post(
            reverse('academic_student_register'),
            data=self._registration_payload(
                username='duplicado_hu25',
                email='duplicado_hu25@test.com',
                student_code='20261001',
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ya existe un estudiante con este codigo.')