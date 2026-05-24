"""
Tests - HU-38: Generar metricas de asistencia de usuarios a citas
Requerimiento Funcional: RF36 (REP7.3)
"""

from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

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


def make_cite(beneficiary, state, days_offset=0):
    return Cite.objects.create(
        beneficiary=beneficiary,
        date_assigned=timezone.now + timedelta(days=days_offset),
        modality_cite=Cite.MODALITY_INPERSON,
        state_cite=state,
        request_cite=Cite.CHANNEL_WEB,
        description='Consulta juridica.',
    )


class HU38_AccesoReporteTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu38', group_name=ROLE_ADMINISTRADOR)
        self.secretaria = make_user('sec_hu38', group_name=ROLE_SECRETARIA)
        self.estudiante = make_user('est_hu38')

    def test_admin_accede_al_reporte(self):
        """POSITIVO: El administrador puede ver las metricas de asistencia."""
        self.client.login(username='admin_hu38', password='pass1234')
        response = self.client.get(reverse('cite_attendance_report'))
        self.assertEqual(response.status_code, 200)

    def test_secretaria_accede_al_reporte(self):
        """POSITIVO: La secretaria puede ver las metricas de asistencia."""
        self.client.login(username='sec_hu38', password='pass1234')
        response = self.client.get(reverse('cite_attendance_report'))
        self.assertEqual(response.status_code, 200)

    def test_estudiante_no_puede_acceder(self):
        """NEGATIVO: Un estudiante no puede acceder a las metricas."""
        self.client.login(username='est_hu38', password='pass1234')
        response = self.client.get(reverse('cite_attendance_report'))
        self.assertEqual(response.status_code, 302)


class HU38_CalculoMetricasTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu38_calc', group_name=ROLE_ADMINISTRADOR)
        self.beneficiary = make_beneficiary()

    def test_reporte_calcula_porcentajes(self):
        """POSITIVO: Calcula porcentaje de asistencia y no asistencia."""
        make_cite(self.beneficiary, state=Cite.STATE_ATTENDED, days_offset=-1)
        make_cite(self.beneficiary, state=Cite.STATE_ATTENDED, days_offset=-2)
        make_cite(self.beneficiary, state=Cite.STATE_NO_SHOW, days_offset=-3)

        self.client.login(username='admin_hu38_calc', password='pass1234')
        response = self.client.get(reverse('cite_attendance_report'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 3)
        self.assertEqual(response.context['attended_count'], 2)
        self.assertEqual(response.context['no_show_count'], 1)
        self.assertAlmostEqual(response.context['attendance_percentage'], 66.7, places=1)
        self.assertAlmostEqual(response.context['no_show_percentage'], 33.3, places=1)

    def test_reporte_filtra_por_fechas(self):
        """POSITIVO: Filtra registros de asistencia por rango de fechas."""
        make_cite(self.beneficiary, state=Cite.STATE_ATTENDED, days_offset=-10)
        make_cite(self.beneficiary, state=Cite.STATE_NO_SHOW, days_offset=-1)

        self.client.login(username='admin_hu38_calc', password='pass1234')
        desde = (date.today() + timedelta(days=-2)).strftime('%Y-%m-%d')
        hasta = date.today().strftime('%Y-%m-%d')
        response = self.client.get(reverse('cite_attendance_report'), {
            'desde': desde,
            'hasta': hasta,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 1)
        self.assertEqual(response.context['attended_count'], 0)
        self.assertEqual(response.context['no_show_count'], 1)


class HU38_ExportMetricasTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_hu38_exp', group_name=ROLE_ADMINISTRADOR)
        self.secretaria = make_user('sec_hu38_exp', group_name=ROLE_SECRETARIA)
        self.beneficiary = make_beneficiary(email='exp38@test.com')
        make_cite(self.beneficiary, state=Cite.STATE_ATTENDED, days_offset=-1)

    def test_admin_exporta_excel(self):
        """POSITIVO: El administrador puede exportar las metricas en Excel."""
        self.client.login(username='admin_hu38_exp', password='pass1234')
        response = self.client.get(reverse('cite_attendance_report_excel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_admin_exporta_pdf(self):
        """POSITIVO: El administrador puede exportar las metricas en PDF."""
        self.client.login(username='admin_hu38_exp', password='pass1234')
        response = self.client.get(reverse('cite_attendance_report_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_excel_tiene_nombre_correcto(self):
        """POSITIVO: El archivo Excel descargado tiene el nombre correcto."""
        self.client.login(username='admin_hu38_exp', password='pass1234')
        response = self.client.get(reverse('cite_attendance_report_excel'))
        self.assertIn('reporte_asistencia.xlsx', response['Content-Disposition'])

    def test_pdf_tiene_nombre_correcto(self):
        """POSITIVO: El archivo PDF descargado tiene el nombre correcto."""
        self.client.login(username='admin_hu38_exp', password='pass1234')
        response = self.client.get(reverse('cite_attendance_report_pdf'))
        self.assertIn('reporte_asistencia.pdf', response['Content-Disposition'])

    def test_secretaria_exporta_excel(self):
        """POSITIVO: La secretaria tambien puede exportar las metricas."""
        self.client.login(username='sec_hu38_exp', password='pass1234')
        response = self.client.get(reverse('cite_attendance_report_excel'))
        self.assertEqual(response.status_code, 200)
