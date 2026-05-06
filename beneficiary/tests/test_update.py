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


def make_beneficiary(name='Laura Torres', email='laura@test.com'):
    return Beneficiary.objects.create(
        name=name,
        colombian_identification='1001234567',
        location='Cali, Valle',
        phone='3001234567',
        email=email,
    )


class BeneficiaryUpdateAccessTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.secretaria = make_user('sec_hu5', group_name=ROLE_SECRETARIA)
        self.administrador = make_user('adm_hu5', group_name=ROLE_ADMINISTRADOR)
        self.sin_rol = make_user('libre_hu5')
        self.beneficiary = make_beneficiary()

    def test_secretaria_puede_acceder_al_formulario_de_edicion(self):
        """POSITIVO: La secretaria puede acceder al formulario de edición de un beneficiario."""
        self.client.login(username='sec_hu5', password='pass1234')
        url = reverse('beneficiary_update', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_administrador_puede_acceder_al_formulario_de_edicion(self):
        """POSITIVO: El administrador también puede acceder al formulario de edición."""
        self.client.login(username='adm_hu5', password='pass1234')
        url = reverse('beneficiary_update', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_usuario_sin_rol_no_puede_editar(self):
        """NEGATIVO: Un usuario sin rol permitido es bloqueado al intentar editar."""
        self.client.login(username='libre_hu5', password='pass1234')
        url = reverse('beneficiary_update', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_formulario_de_edicion_viene_prellenado(self):
        """POSITIVO: Al abrir el formulario de edición, los campos tienen los datos actuales."""
        self.client.login(username='sec_hu5', password='pass1234')
        url = reverse('beneficiary_update', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertContains(response, 'Laura Torres')

    def test_edicion_de_beneficiario_inexistente_retorna_404(self):
        """NEGATIVO: Intentar editar un beneficiario que no existe retorna error 404."""
        self.client.login(username='sec_hu5', password='pass1234')
        url = reverse('beneficiary_update', args=['id_que_no_existe'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class BeneficiaryUpdateSuccessTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('sec_hu5b', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_hu5b', password='pass1234')
        self.beneficiary = make_beneficiary()

    def _url(self):
        return reverse('beneficiary_update', args=[self.beneficiary.pk])

    def _datos_actualizados(self, **overrides):
        base = {
            'name': 'Laura Torres',
            'colombian_identification': '1001234567',
            'location': 'Bogota, Cundinamarca',
            'phone': '3109999999',
            'email': 'laura@test.com',
        }
        base.update(overrides)
        return base

    def test_actualizacion_exitosa_redirige_a_lista(self):
        """POSITIVO: Guardar cambios válidos redirige a la lista de beneficiarios."""
        response = self.client.post(self._url(), self._datos_actualizados())
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_list'))

    def test_actualizacion_cambia_el_telefono_en_db(self):
        """POSITIVO: El teléfono modificado se actualiza correctamente en la base de datos."""
        self.client.post(self._url(), self._datos_actualizados(phone='3150000000'))
        actualizado = Beneficiary.objects.get(pk=self.beneficiary.pk)
        self.assertEqual(actualizado.phone, '3150000000')

    def test_actualizacion_cambia_la_ubicacion_en_db(self):
        """POSITIVO: La ubicación modificada se actualiza correctamente en la base de datos."""
        self.client.post(self._url(), self._datos_actualizados(location='Barranquilla, Atlantico'))
        actualizado = Beneficiary.objects.get(pk=self.beneficiary.pk)
        self.assertEqual(actualizado.location, 'Barranquilla, Atlantico')

    def test_actualizacion_cambia_el_email_en_db(self):
        """POSITIVO: El correo electrónico modificado se actualiza correctamente en la base de datos."""
        self.client.post(self._url(), self._datos_actualizados(email='nuevo@test.com'))
        actualizado = Beneficiary.objects.get(pk=self.beneficiary.pk)
        self.assertEqual(actualizado.email, 'nuevo@test.com')


class BeneficiaryUpdateValidationTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('sec_hu5c', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_hu5c', password='pass1234')
        self.beneficiary = make_beneficiary()

    def test_cancelar_no_modifica_los_datos(self):
        """POSITIVO: Al cancelar, los datos originales se mantienen."""
        response = self.client.get(reverse('beneficiary_list'))
        intacto = Beneficiary.objects.get(pk=self.beneficiary.pk)
        self.assertEqual(intacto.name, 'Laura Torres')
        self.assertEqual(response.status_code, 200)

    def test_actualizacion_falla_con_email_invalido(self):
        """NEGATIVO: Enviar un email con formato inválido no actualiza el registro."""
        url = reverse('beneficiary_update', args=[self.beneficiary.pk])
        data = {
            'name': 'Laura Torres',
            'colombian_identification': '1001234567',
            'location': 'Cali, Valle',
            'phone': '3001234567',
            'email': 'esto-no-es-email',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        sin_cambios = Beneficiary.objects.get(pk=self.beneficiary.pk)
        self.assertEqual(sin_cambios.email, 'laura@test.com')

    def test_actualizacion_falla_con_nombre_vacio(self):
        """NEGATIVO: Enviar el nombre vacío no actualiza el registro."""
        url = reverse('beneficiary_update', args=[self.beneficiary.pk])
        data = {
            'name': '',
            'colombian_identification': '1001234567',
            'location': 'Cali, Valle',
            'phone': '3001234567',
            'email': 'laura@test.com',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        sin_cambios = Beneficiary.objects.get(pk=self.beneficiary.pk)
        self.assertEqual(sin_cambios.name, 'Laura Torres')