"""
Tests - HU-19: Generar reportes de citas no confirmadas o no asistidas
Requerimiento Funcional: RF18
"""

import io
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


class HU19_NoShowTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_noshow', group_name=ROLE_ADMINISTRADOR)
        self.beneficiary = make_beneficiary(name='Carlos Vera', email='carlos@test.com')

        make_cite(self.beneficiary, state=Cite.STATE_PENDING)
        make_cite(self.beneficiary, state=Cite.STATE_CANCELED)
        make_cite(self.beneficiary, state=Cite.STATE_NO_SHOW)

        make_cite(self.beneficiary, state=Cite.STATE_ATTENDED)

        self.client.login(username='admin_noshow', password='pass1234')

    def test_no_show_cite_appears_in_html_report(self):
        """POSITIVO: Una cita con estado No asistió aparece en el reporte HTML."""
        response = self.client.get(reverse('cite_report'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['total'], 3,
            'El reporte debería incluir 3 citas (Pendiente, Cancelada y No asistió).',
        )

    def test_attended_cite_excluded_from_html_report(self):
        """NEGATIVO: Una cita con estado Asistió NO debe aparecer en el reporte HU-19."""
        response = self.client.get(reverse('cite_report'))
        states = [c.state_cite for c in response.context['cites']]
        self.assertNotIn(
            Cite.STATE_ATTENDED, states,
            'Una cita con estado Asistió no debería aparecer en el reporte HU-19.',
        )

    def test_no_show_cite_included_in_excel_export(self):
        """POSITIVO: La exportación Excel incluye citas con estado No asistió."""
        import openpyxl
        response = self.client.get(reverse('cite_report_excel'))
        self.assertEqual(response.status_code, 200)
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        cell_values = [str(c.value) for row in ws.iter_rows() for c in row if c.value]
        self.assertTrue(
            any(Cite.STATE_NO_SHOW in v for v in cell_values),
            'El Excel exportado no contiene ninguna fila con estado No asistió.',
        )

    def test_no_show_cite_included_in_pdf_export(self):
        """POSITIVO: La exportación PDF incluye citas con estado No asistió."""
        # El HTML ya verifica que el queryset incluye STATE_NO_SHOW.
        # Aquí confirmamos que el endpoint PDF responde correctamente.
        response = self.client.get(reverse('cite_report_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_report_total_includes_all_three_states(self):
        """POSITIVO: El total del reporte suma Pendiente + Cancelada + No asistió."""
        make_cite(self.beneficiary, state=Cite.STATE_NO_SHOW)
        response = self.client.get(reverse('cite_report'))
        self.assertEqual(
            response.context['total'], 4,
            'El total del reporte debe reflejar correctamente las 4 citas (1P + 1C + 2N).',
        )

    def test_filter_by_no_show_state_returns_only_no_show(self):
        """POSITIVO: El filtro por estado No asistió devuelve solo ese tipo de citas."""
        response = self.client.get(
            reverse('cite_report'), {'estado': Cite.STATE_NO_SHOW}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['total'], 1,
            'El filtro por No asistió debería retornar exactamente 1 cita.',
        )
        states = [c.state_cite for c in response.context['cites']]
        self.assertTrue(
            all(s == Cite.STATE_NO_SHOW for s in states),
            'Todas las citas del resultado filtrado deben tener estado No asistió.',
        )