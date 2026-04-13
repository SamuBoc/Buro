"""
Tests - HU-1: Registrar nuevo beneficiario en el sistema
Requerimiento Funcional: RF1, RF2 (CAS1.1)

Criterios de aceptación cubiertos:
  - Scenario: Registro exitoso de beneficiario
  - Scenario: Campos obligatorios incompletos
"""

from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from django.urls import reverse

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
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


def datos_validos(**overrides):
    """Retorna un diccionario con datos completos y válidos para el formulario."""
    base = {
        'id': '1001',
        'name': 'Maria Lopez',
        'location': 'Cali, Valle',
        'phone': '3001234567',
        'email': 'maria@test.com',
        'allow_conditions': True,
    }
    base.update(overrides)
    return base

class HU1_AccesoFormularioTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.secretaria = make_user('sec_hu1', group_name=ROLE_SECRETARIA)
        self.administrador = make_user('adm_hu1', group_name=ROLE_ADMINISTRADOR)
        self.sin_rol = make_user('libre_hu1')

    def test_secretaria_puede_acceder_al_formulario(self):
        """POSITIVO: La secretaria con sesión activa puede ver el formulario de registro."""
        self.client.login(username='sec_hu1', password='pass1234')
        response = self.client.get(reverse('beneficiary_register'))
        self.assertEqual(response.status_code, 200)

    def test_administrador_puede_acceder_al_formulario(self):
        """POSITIVO: El administrador puede acceder al formulario de registro."""
        self.client.login(username='adm_hu1', password='pass1234')
        response = self.client.get(reverse('beneficiary_register'))
        self.assertEqual(response.status_code, 200)

    def test_usuario_sin_rol_no_puede_acceder(self):
        """NEGATIVO: Un usuario sin rol permitido es bloqueado y redirigido."""
        self.client.login(username='libre_hu1', password='pass1234')
        response = self.client.get(reverse('beneficiary_register'))
        self.assertEqual(response.status_code, 302)

    def test_sin_sesion_redirige_al_login(self):
        """NEGATIVO: Sin sesión activa, el sistema redirige al login."""
        response = self.client.get(reverse('beneficiary_register'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

class HU1_RegistroExitosoTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.secretaria = make_user('sec_hu1b', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_hu1b', password='pass1234')

    def test_registro_con_datos_completos_guarda_en_db(self):
        """POSITIVO: Enviar el formulario completo crea el beneficiario en la base de datos."""
        self.client.post(reverse('beneficiary_register'), datos_validos())
        self.assertTrue(Beneficiary.objects.filter(id='1001').exists())

    def test_registro_exitoso_redirige_a_lista(self):
        """POSITIVO: Tras un registro exitoso, el sistema redirige a la lista de beneficiarios."""
        response = self.client.post(reverse('beneficiary_register'), datos_validos())
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_list'))

    def test_registro_guarda_nombre_correctamente(self):
        """POSITIVO: El nombre ingresado se almacena exactamente como fue enviado."""
        self.client.post(reverse('beneficiary_register'), datos_validos())
        beneficiario = Beneficiary.objects.get(id='1001')
        self.assertEqual(beneficiario.name, 'Maria Lopez')

    def test_registro_guarda_email_correctamente(self):
        """POSITIVO: El correo electrónico se almacena correctamente en la DB."""
        self.client.post(reverse('beneficiary_register'), datos_validos())
        beneficiario = Beneficiary.objects.get(id='1001')
        self.assertEqual(beneficiario.email, 'maria@test.com')

    def test_registro_asigna_fecha_automaticamente(self):
        """POSITIVO: La fecha de registro se asigna sola al crear el beneficiario."""
        self.client.post(reverse('beneficiary_register'), datos_validos())
        beneficiario = Beneficiary.objects.get(id='1001')
        self.assertIsNotNone(beneficiario.date_register)

class HU1_CamposIncompletosTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.secretaria = make_user('sec_hu1c', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_hu1c', password='pass1234')

    def test_falla_sin_nombre(self):
        """NEGATIVO: El formulario no se guarda si el nombre está vacío."""
        response = self.client.post(reverse('beneficiary_register'), datos_validos(name=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Beneficiary.objects.filter(id='1001').exists())

    def test_falla_sin_documento_de_identidad(self):
        """NEGATIVO: El formulario no se guarda si el número de identificación está vacío."""
        data = datos_validos()
        data['id'] = ''
        response = self.client.post(reverse('beneficiary_register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Beneficiary.objects.count(), 0)

    def test_falla_sin_ubicacion(self):
        """NEGATIVO: El formulario no se guarda si la ubicación está vacía."""
        response = self.client.post(reverse('beneficiary_register'), datos_validos(location=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Beneficiary.objects.filter(id='1001').exists())

    def test_falla_sin_telefono(self):
        """NEGATIVO: El formulario no se guarda si el teléfono está vacío."""
        response = self.client.post(reverse('beneficiary_register'), datos_validos(phone=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Beneficiary.objects.filter(id='1001').exists())

    def test_falla_sin_email(self):
        """NEGATIVO: El formulario no se guarda si el correo electrónico está vacío."""
        response = self.client.post(reverse('beneficiary_register'), datos_validos(email=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Beneficiary.objects.filter(id='1001').exists())

    def test_falla_con_email_invalido(self):
        """NEGATIVO: El formulario rechaza un correo con formato incorrecto."""
        response = self.client.post(
            reverse('beneficiary_register'),
            datos_validos(email='esto-no-es-un-correo')
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Beneficiary.objects.filter(id='1001').exists())

    def test_no_se_registran_dos_beneficiarios_con_mismo_id(self):
        """NEGATIVO: No se puede registrar un beneficiario con un ID que ya existe en el sistema."""
        self.client.post(reverse('beneficiary_register'), datos_validos())
        response = self.client.post(
            reverse('beneficiary_register'),
            datos_validos(name='Otro Nombre', email='otro@test.com')
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Beneficiary.objects.count(), 1)
