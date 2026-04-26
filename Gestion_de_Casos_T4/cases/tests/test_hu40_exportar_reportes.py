from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from django.urls import reverse

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
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


def make_case(beneficiary=None):
    if beneficiary is None:
        beneficiary = make_beneficiary()
    return Case.objects.create(
        sala=Case.ROOM_CIVIL,
        description='Problema de arrendamiento',
        beneficiary=beneficiary,
    )


class HU40_ExportExcelTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu40', group_name=ROLE_ADMINISTRADOR)
        self.secretaria = make_user('sec_hu40', group_name=ROLE_SECRETARIA)
        self.beneficiary = make_beneficiary()
        self.case = make_case(self.beneficiary)

    def test_admin_descarga_excel_correctamente(self):
        """POSITIVO: El administrador puede exportar el reporte en formato Excel."""
        self.client.login(username='admin_hu40', password='pass1234')
        response = self.client.get(reverse('export_cases_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_excel_tiene_header_de_descarga_correcto(self):
        """POSITIVO: La respuesta Excel incluye el nombre de archivo correcto."""
        self.client.login(username='admin_hu40', password='pass1234')
        response = self.client.get(reverse('export_cases_excel'))
        self.assertIn('reporte_casos.xlsx', response['Content-Disposition'])

    def test_secretaria_no_puede_exportar_excel(self):
        """NEGATIVO: Una secretaria no tiene acceso a la exportación de reportes."""
        self.client.login(username='sec_hu40', password='pass1234')
        response = self.client.get(reverse('export_cases_excel'))
        self.assertEqual(response.status_code, 302)

    def test_sin_sesion_redirige_al_login_excel(self):
        """NEGATIVO: Sin sesión activa el sistema redirige al login."""
        response = self.client.get(reverse('export_cases_excel'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])


class HU40_ExportPDFTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu40_pdf', group_name=ROLE_ADMINISTRADOR)
        self.secretaria = make_user('sec_hu40_pdf', group_name=ROLE_SECRETARIA)
        self.beneficiary = make_beneficiary(email='pedro2@test.com')
        self.case = make_case(self.beneficiary)

    def test_admin_descarga_pdf_correctamente(self):
        """POSITIVO: El administrador puede exportar el reporte en formato PDF."""
        self.client.login(username='admin_hu40_pdf', password='pass1234')
        response = self.client.get(reverse('export_cases_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_pdf_tiene_header_de_descarga_correcto(self):
        """POSITIVO: La respuesta PDF incluye el nombre de archivo correcto."""
        self.client.login(username='admin_hu40_pdf', password='pass1234')
        response = self.client.get(reverse('export_cases_pdf'))
        self.assertIn('reporte_casos.pdf', response['Content-Disposition'])

    def test_secretaria_no_puede_exportar_pdf(self):
        """NEGATIVO: Una secretaria no tiene acceso a la exportación en PDF."""
        self.client.login(username='sec_hu40_pdf', password='pass1234')
        response = self.client.get(reverse('export_cases_pdf'))
        self.assertEqual(response.status_code, 302)

    def test_sin_sesion_redirige_al_login_pdf(self):
        """NEGATIVO: Sin sesión activa el sistema redirige al login."""
        response = self.client.get(reverse('export_cases_pdf'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])


class HU40_VolumenTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu40_vol', group_name=ROLE_ADMINISTRADOR)

    def test_exportacion_excel_con_100_casos(self):
        """VOLUMEN: La exportación Excel funciona correctamente con 100 casos."""
        for i in range(100):
            b = Beneficiary.objects.create(
                name=f'Beneficiario {i}',
                location='Cali',
                phone=f'300{i:07d}',
                email=f'ben{i}@test.com',
            )
            Case.objects.create(
                sala=Case.ROOM_CIVIL,
                description=f'Caso de prueba {i}',
                beneficiary=b,
            )
        self.client.login(username='admin_hu40_vol', password='pass1234')
        response = self.client.get(reverse('export_cases_excel'))
        self.assertEqual(response.status_code, 200)

    def test_exportacion_pdf_con_100_casos(self):
        """VOLUMEN: La exportación PDF funciona correctamente con 100 casos."""
        for i in range(100):
            b = Beneficiary.objects.create(
                name=f'Beneficiario Vol {i}',
                location='Cali',
                phone=f'301{i:07d}',
                email=f'vol{i}@test.com',
            )
            Case.objects.create(
                sala=Case.ROOM_CIVIL,
                description=f'Caso volumen {i}',
                beneficiary=b,
            )
        self.client.login(username='admin_hu40_vol', password='pass1234')
        response = self.client.get(reverse('export_cases_pdf'))
        self.assertEqual(response.status_code, 200)