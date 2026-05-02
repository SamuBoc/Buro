"""
Tests - HU-19: Generar reportes de citas no confirmadas o no asistidas
Requerimiento Funcional: RF18
"""

from datetime import date, timedelta

from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from django.urls import reverse

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
from beneficiary.models import Beneficiary
from cite.models import Cite


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


def make_beneficiary(name='Ana Lopez', email='ana@test.com'):
    return Beneficiary.objects.create(
        name=name,
        location='Cali',
        phone='3001234567',
        email=email,
    )


def make_cite(beneficiary, state=Cite.STATE_PENDING):
    return Cite.objects.create(
        beneficiary=beneficiary,
        date_assigned=date.today() + timedelta(days=3),
        modality_cite=Cite.MODALITY_INPERSON,
        state_cite=state,
        request_cite=Cite.CHANNEL_WEB,
        description='Consulta jurídica.',
    )


class HU19_AccesoReporteTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu19', group_name=ROLE_ADMINISTRADOR)
        self.secretaria = make_user('sec_hu19', group_name=ROLE_SECRETARIA)
        self.estudiante = make_user('est_hu19')
        self.beneficiary = make_beneficiary()
        make_cite(self.beneficiary, state=Cite.STATE_PENDING)
        make_cite(self.beneficiary, state=Cite.STATE_CANCELED)

    def test_admin_accede_al_reporte(self):
        """POSITIVO: El administrador puede ver el reporte de citas."""
        self.client.login(username='admin_hu19', password='pass1234')
        response = self.client.get(reverse('cite_report'))
        self.assertEqual(response.status_code, 200)

    def test_secretaria_accede_al_reporte(self):
        """POSITIVO: La secretaria puede ver el reporte de citas."""
        self.client.login(username='sec_hu19', password='pass1234')
        response = self.client.get(reverse('cite_report'))
        self.assertEqual(response.status_code, 200)

    def test_reporte_muestra_citas_pendientes_y_canceladas(self):
        """POSITIVO: El reporte incluye citas en estado Pendiente y Cancelada."""
        self.client.login(username='admin_hu19', password='pass1234')
        response = self.client.get(reverse('cite_report'))
        self.assertEqual(response.context['total'], 2)

    def test_estudiante_no_puede_acceder(self):
        """NEGATIVO: Un estudiante no puede acceder al reporte."""
        self.client.login(username='est_hu19', password='pass1234')
        response = self.client.get(reverse('cite_report'))
        self.assertEqual(response.status_code, 302)

    def test_sin_sesion_redirige_al_login(self):
        """NEGATIVO: Sin sesión activa redirige al login."""
        response = self.client.get(reverse('cite_report'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])


class HU19_ExportReporteTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu19_exp', group_name=ROLE_ADMINISTRADOR)
        self.secretaria = make_user('sec_hu19_exp', group_name=ROLE_SECRETARIA)
        b = make_beneficiary(email='exp@test.com')
        make_cite(b)

    def test_admin_exporta_excel(self):
        """POSITIVO: El administrador puede exportar el reporte en Excel."""
        self.client.login(username='admin_hu19_exp', password='pass1234')
        response = self.client.get(reverse('cite_report_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_admin_exporta_pdf(self):
        """POSITIVO: El administrador puede exportar el reporte en PDF."""
        self.client.login(username='admin_hu19_exp', password='pass1234')
        response = self.client.get(reverse('cite_report_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_excel_tiene_nombre_correcto(self):
        """POSITIVO: El archivo Excel descargado tiene el nombre correcto."""
        self.client.login(username='admin_hu19_exp', password='pass1234')
        response = self.client.get(reverse('cite_report_excel'))
        self.assertIn('reporte_citas.xlsx', response['Content-Disposition'])

    def test_pdf_tiene_nombre_correcto(self):
        """POSITIVO: El archivo PDF descargado tiene el nombre correcto."""
        self.client.login(username='admin_hu19_exp', password='pass1234')
        response = self.client.get(reverse('cite_report_pdf'))
        self.assertIn('reporte_citas.pdf', response['Content-Disposition'])

    def test_secretaria_exporta_excel(self):
        """POSITIVO: La secretaria también puede exportar el reporte."""
        self.client.login(username='sec_hu19_exp', password='pass1234')
        response = self.client.get(reverse('cite_report_excel'))
        self.assertEqual(response.status_code, 200)


class HU19_VolumenTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu19_vol', group_name=ROLE_ADMINISTRADOR)

    def test_reporte_con_50_citas(self):
        """VOLUMEN: El reporte maneja correctamente 50 citas."""
        for i in range(50):
            b = Beneficiary.objects.create(
                name=f'Beneficiario {i}',
                location='Cali',
                phone=f'300{i:07d}',
                email=f'vol{i}@test.com',
            )
            Cite.objects.create(
                beneficiary=b,
                date_assigned=date.today() + timedelta(days=i % 10 + 1),
                modality_cite=Cite.MODALITY_INPERSON,
                state_cite=Cite.STATE_PENDING,
                request_cite=Cite.CHANNEL_WEB,
                description=f'Consulta {i}.',
            )
        self.client.login(username='admin_hu19_vol', password='pass1234')
        response = self.client.get(reverse('cite_report'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 50)