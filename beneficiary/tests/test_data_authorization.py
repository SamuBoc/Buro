import io

from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from accounts.constants import ROLE_SECRETARIA
from beneficiary.models import Beneficiary


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


def fake_pdf():
    return SimpleUploadedFile(
        name='cedula.pdf',
        content=b'%PDF-1.4 fake content',
        content_type='application/pdf'
    )


def datos_base(**overrides):
    base = {
        'name': 'Carlos Ruiz',
        'colombian_identification': '1012345678',
        'location': 'Medellin, Antioquia',
        'phone': '3109876543',
        'email': 'carlos@test.com',
        'file': fake_pdf(),
    }
    base.update(overrides)
    return base


class DataAuthorizationAcceptedTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('sec_hu3', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_hu3', password='pass1234')

    def test_registro_exitoso_con_autorizacion_marcada(self):
        """POSITIVO: Con la autorización marcada, el beneficiario se guarda en la DB."""
        data = datos_base()
        data['allow_conditions'] = True
        self.client.post(reverse('beneficiary_register'), data)
        self.assertTrue(Beneficiary.objects.filter(email='carlos@test.com').exists())

    def test_con_autorizacion_marcada_redirige_a_lista(self):
        """POSITIVO: Aceptar la autorización y enviar el formulario redirige correctamente."""
        data = datos_base()
        data['allow_conditions'] = True
        response = self.client.post(reverse('beneficiary_register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_list'))

    def test_formulario_contiene_campo_autorizacion(self):
        """POSITIVO: El formulario de registro incluye el campo de autorización de datos."""
        response = self.client.get(reverse('beneficiary_register'))
        self.assertContains(response, 'allow_conditions')


class DataAuthorizationRejectedTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('sec_hu3b', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_hu3b', password='pass1234')

    def test_registro_bloqueado_sin_autorizacion(self):
        """NEGATIVO: Sin marcar la autorización, el beneficiario NO se guarda en la DB."""
        data = datos_base()
        self.client.post(reverse('beneficiary_register'), data)
        self.assertFalse(Beneficiary.objects.filter(email='carlos@test.com').exists())

    def test_sin_autorizacion_el_formulario_vuelve_a_mostrarse(self):
        """NEGATIVO: Sin autorización, el sistema devuelve el formulario con código 200."""
        data = datos_base()
        response = self.client.post(reverse('beneficiary_register'), data)
        self.assertEqual(response.status_code, 200)

    def test_sin_autorizacion_con_todos_los_demas_campos_completos(self):
        """NEGATIVO: Aunque todos los demás campos estén bien, sin autorización no se registra."""
        data = datos_base()
        response = self.client.post(reverse('beneficiary_register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Beneficiary.objects.count(), 0)

    def test_autorizacion_con_valor_falso_bloquea_registro(self):
        """NEGATIVO: Enviar allow_conditions=False explícitamente también bloquea el registro."""
        data = datos_base()
        data['allow_conditions'] = False
        self.client.post(reverse('beneficiary_register'), data)
        self.assertFalse(Beneficiary.objects.filter(email='carlos@test.com').exists())