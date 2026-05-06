from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
from beneficiary.models import Beneficiary, BeneficiaryAuditLog, DataDeletionRequest


def make_user(username, password='pass1234', group_name=None, is_superuser=False):
    if is_superuser:
        return User.objects.create_superuser(
            username=username,
            password=password,
            email=f'{username}@test.com',
        )

    user = User.objects.create_user(
        username=username,
        password=password,
        email=f'{username}@test.com',
    )
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def make_beneficiary(name='Laura Torres', email='laura@test.com'):
    return Beneficiary.objects.create(
        name=name,
        colombian_identification='1001234567',
        location='Cali, Valle',
        phone='3001234567',
        email=email,
    )


class DataDeletionSecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu34', group_name=ROLE_ADMINISTRADOR)
        self.secretaria = make_user('sec_hu34', group_name=ROLE_SECRETARIA)
        self.sin_rol = make_user('libre_hu34')
        self.beneficiary = make_beneficiary()

    def test_usuario_anonimo_es_redirigido_al_login_para_solicitar_eliminacion(self):
        response = self.client.get(
            reverse('data_deletion_request_create', args=[self.beneficiary.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_solo_admin_puede_ver_lista_de_solicitudes(self):
        self.client.login(username='libre_hu34', password='pass1234')
        response = self.client.get(reverse('data_deletion_request_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('no_permission'), response.url)

    def test_admin_puede_ver_lista_de_solicitudes(self):
        self.client.login(username='admin_hu34', password='pass1234')
        response = self.client.get(reverse('data_deletion_request_list'))
        self.assertEqual(response.status_code, 200)


class DataDeletionRequestTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.secretaria = make_user('sec_hu34b', group_name=ROLE_SECRETARIA)
        self.beneficiary = make_beneficiary()

    def test_usuario_autenticado_puede_registrar_solicitud(self):
        self.client.login(username='sec_hu34b', password='pass1234')
        response = self.client.post(
            reverse('data_deletion_request_create', args=[self.beneficiary.pk]),
            {
                'reason': 'Deseo ejercer mi derecho de supresion.',
                'confirm_request': 'on',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        request_obj = DataDeletionRequest.objects.get(beneficiary=self.beneficiary)
        self.assertEqual(request_obj.status, DataDeletionRequest.STATUS_PENDING)
        self.assertEqual(request_obj.reason, 'Deseo ejercer mi derecho de supresion.')

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('La solicitud de eliminacion de datos fue registrada correctamente.', messages)

    def test_registrar_solicitud_no_elimina_beneficiario(self):
        self.client.login(username='sec_hu34b', password='pass1234')
        self.client.post(
            reverse('data_deletion_request_create', args=[self.beneficiary.pk]),
            {
                'reason': 'No deseo conservar mis datos.',
                'confirm_request': 'on',
            },
        )

        self.assertTrue(Beneficiary.objects.filter(pk=self.beneficiary.pk).exists())

    def test_registrar_solicitud_crea_traza_en_bitacora(self):
        self.client.login(username='sec_hu34b', password='pass1234')
        self.client.post(
            reverse('data_deletion_request_create', args=[self.beneficiary.pk]),
            {
                'reason': 'Solicitud de eliminacion.',
                'confirm_request': 'on',
            },
        )

        self.assertTrue(
            BeneficiaryAuditLog.objects.filter(
                beneficiary=self.beneficiary,
                action='DELETE_REQUEST',
            ).exists()
        )

    def test_confirmacion_es_obligatoria_para_registrar_solicitud(self):
        self.client.login(username='sec_hu34b', password='pass1234')
        response = self.client.post(
            reverse('data_deletion_request_create', args=[self.beneficiary.pk]),
            {
                'reason': 'Intento sin confirmar.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(DataDeletionRequest.objects.filter(beneficiary=self.beneficiary).exists())


class DataDeletionListTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu34b', group_name=ROLE_ADMINISTRADOR)
        self.beneficiary_a = make_beneficiary(name='Ana Torres', email='ana@test.com')
        self.beneficiary_b = make_beneficiary(name='Luis Gomez', email='luis@test.com')

        DataDeletionRequest.objects.create(
            beneficiary=self.beneficiary_a,
            status=DataDeletionRequest.STATUS_PENDING,
            reason='Solicitud pendiente.',
        )
        DataDeletionRequest.objects.create(
            beneficiary=self.beneficiary_b,
            status=DataDeletionRequest.STATUS_APPROVED,
            reason='Solicitud aprobada.',
        )

    def test_admin_puede_filtrar_solicitudes_por_estado(self):
        self.client.login(username='admin_hu34b', password='pass1234')
        response = self.client.get(
            reverse('data_deletion_request_list'),
            {'status': DataDeletionRequest.STATUS_PENDING},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ana Torres')
        self.assertNotContains(response, 'Luis Gomez')
