from datetime import date, timedelta

from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from django.urls import reverse

from beneficiary.models import Beneficiary
from cite.models import Cite

def make_user(username, password='pass1234'):
    return User.objects.create_user(username=username, password=password)


def make_beneficiary():
    return Beneficiary.objects.create(
        id='BEN-2026-0001',
        name='Laura Torres',
        location='Cali, Valle',
        phone='3001234567',
        email='laura@test.com',
        colombian_identification='1001234567',
    )


def make_cite(beneficiary, state=Cite.STATE_PENDING, days_offset=0):
    return Cite.objects.create(
        beneficiary=beneficiary,
        date_assigned=date.today() + timedelta(days=days_offset),
        modality_cite=Cite.MODALITY_INPERSON,
        state_cite=state,
        request_cite=Cite.CHANNEL_WEB,
        description='Consulta de prueba',
    )

class CreateCiteTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user('user_cite')
        self.client.login(username='user_cite', password='pass1234')
        self.beneficiary = make_beneficiary()
        self.url = reverse('create_cite', args=[self.beneficiary.pk])

    def test_agendar_cita_con_datos_validos_guarda_en_db(self):
        data = {
            'modality_cite': Cite.MODALITY_INPERSON,
            'request_cite': Cite.CHANNEL_WEB,
            'date_assigned': str(date.today()),
            'description': 'Primera consulta',
        }
        self.client.post(self.url, data)
        self.assertEqual(Cite.objects.count(), 1)

    def test_agendar_cita_redirige_al_detalle_del_beneficiario(self):
        data = {
            'modality_cite': Cite.MODALITY_VIRTUAL,
            'request_cite': Cite.CHANNEL_EMAIL,
            'date_assigned': str(date.today()),
            'description': 'Consulta virtual',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_detail', args=[self.beneficiary.pk]))

    def test_agendar_cita_sin_descripcion_falla(self):
        data = {
            'modality_cite': Cite.MODALITY_INPERSON,
            'request_cite': Cite.CHANNEL_WEB,
            'date_assigned': str(date.today()),
            'description': '',
        }
        self.client.post(self.url, data)
        self.assertEqual(Cite.objects.count(), 0)

    def test_agendar_cita_sin_sesion_redirige_al_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_agendar_cita_sin_fecha_asigna_fecha_de_hoy(self):
        data = {
            'modality_cite': Cite.MODALITY_PHONE,
            'request_cite': Cite.CHANNEL_PHONE,
            'date_assigned': '',
            'description': 'Sin fecha explícita',
        }
        self.client.post(self.url, data)
        if Cite.objects.exists():
            cita = Cite.objects.first()
            self.assertEqual(cita.date_assigned, date.today())

    def test_agendar_cita_a_beneficiario_inexistente_retorna_404(self):
        url = reverse('create_cite', args=['BEN-9999-9999'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_cita_creada_tiene_estado_pendiente_por_defecto(self):
        data = {
            'modality_cite': Cite.MODALITY_INPERSON,
            'request_cite': Cite.CHANNEL_WEB,
            'date_assigned': str(date.today()),
            'description': 'Revisión estado inicial',
        }
        self.client.post(self.url, data)
        cita = Cite.objects.first()
        self.assertEqual(cita.state_cite, Cite.STATE_PENDING)

class CancelCiteTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user('user_cancel')
        self.client.login(username='user_cancel', password='pass1234')
        self.beneficiary = make_beneficiary()

    def test_cancelar_cita_pendiente_cambia_estado_en_db(self):
        cita = make_cite(self.beneficiary)
        url = reverse('cancel_cite', args=[cita.pk])
        self.client.post(url)
        cita.refresh_from_db()
        self.assertEqual(cita.state_cite, Cite.STATE_CANCELED)

    def test_cancelar_cita_redirige_a_lista_de_citas(self):
        cita = make_cite(self.beneficiary)
        url = reverse('cancel_cite', args=[cita.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_cites', args=[self.beneficiary.pk]))

    def test_cancelar_cita_no_elimina_el_registro(self):
        cita = make_cite(self.beneficiary)
        url = reverse('cancel_cite', args=[cita.pk])
        self.client.post(url)
        self.assertEqual(Cite.objects.count(), 1)

    def test_cancelar_cita_inexistente_retorna_404(self):
        url = reverse('cancel_cite', args=[9999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_cancelar_via_get_no_cambia_estado(self):
        cita = make_cite(self.beneficiary)
        url = reverse('cancel_cite', args=[cita.pk])
        self.client.get(url)
        cita.refresh_from_db()
        self.assertNotEqual(cita.state_cite, Cite.STATE_CANCELED)

class RescheduleCiteTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user('user_reschedule')
        self.client.login(username='user_reschedule', password='pass1234')
        self.beneficiary = make_beneficiary()

    def test_reprogramar_cita_actualiza_fecha_en_db(self):
        cita = make_cite(self.beneficiary)
        nueva_fecha = date.today() + timedelta(days=7)
        url = reverse('reschedule_cite', args=[cita.pk])
        self.client.post(url, {'date_assigned': str(nueva_fecha)})
        cita.refresh_from_db()
        self.assertEqual(cita.date_assigned, nueva_fecha)

    def test_reprogramar_cita_redirige_a_lista_de_citas(self):
        cita = make_cite(self.beneficiary)
        nueva_fecha = date.today() + timedelta(days=5)
        url = reverse('reschedule_cite', args=[cita.pk])
        response = self.client.post(url, {'date_assigned': str(nueva_fecha)})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_cites', args=[self.beneficiary.pk]))

    def test_reprogramar_cita_con_fecha_invalida_no_actualiza(self):
        cita = make_cite(self.beneficiary)
        fecha_original = cita.date_assigned
        url = reverse('reschedule_cite', args=[cita.pk])
        self.client.post(url, {'date_assigned': 'no-es-una-fecha'})
        cita.refresh_from_db()
        self.assertEqual(cita.date_assigned, fecha_original)

    def test_reprogramar_cita_inexistente_retorna_404(self):
        url = reverse('reschedule_cite', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_reschedule_muestra_formulario_con_fecha_actual(self):
        cita = make_cite(self.beneficiary)
        url = reverse('reschedule_cite', args=[cita.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        fecha_formateada = cita.date_assigned.strftime('%d/%m/%Y')
        self.assertContains(response, fecha_formateada)

class RegisterCiteAttendanceTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user('user_attendance')
        self.client.login(username='user_attendance', password='pass1234')
        self.beneficiary = make_beneficiary()

    def test_registrar_asistencia_en_cita_pasada(self):
        cita = make_cite(self.beneficiary, days_offset=-1)
        url = reverse('register_cite_attendance', args=[cita.pk, 'asistio'])
        self.client.post(url)
        cita.refresh_from_db()
        self.assertEqual(cita.state_cite, Cite.STATE_ATTENDED)

    def test_registrar_no_asistencia_en_cita_pasada(self):
        cita = make_cite(self.beneficiary, days_offset=-1)
        url = reverse('register_cite_attendance', args=[cita.pk, 'no-asistio'])
        self.client.post(url)
        cita.refresh_from_db()
        self.assertEqual(cita.state_cite, Cite.STATE_NO_SHOW)

    def test_no_se_puede_registrar_asistencia_en_cita_futura(self):
        cita = make_cite(self.beneficiary, days_offset=3)
        url = reverse('register_cite_attendance', args=[cita.pk, 'asistio'])
        self.client.post(url)
        cita.refresh_from_db()
        self.assertNotEqual(cita.state_cite, Cite.STATE_ATTENDED)

    def test_no_se_puede_registrar_asistencia_en_cita_cancelada(self):
        cita = make_cite(self.beneficiary, state=Cite.STATE_CANCELED, days_offset=-1)
        url = reverse('register_cite_attendance', args=[cita.pk, 'asistio'])
        self.client.post(url)
        cita.refresh_from_db()
        self.assertEqual(cita.state_cite, Cite.STATE_CANCELED)

    def test_estado_invalido_no_modifica_la_cita(self):
        cita = make_cite(self.beneficiary, days_offset=-1)
        url = reverse('register_cite_attendance', args=[cita.pk, 'estado-inventado'])
        self.client.post(url)
        cita.refresh_from_db()
        self.assertEqual(cita.state_cite, Cite.STATE_PENDING)

    def test_via_get_no_registra_asistencia(self):
        cita = make_cite(self.beneficiary, days_offset=-1)
        url = reverse('register_cite_attendance', args=[cita.pk, 'asistio'])
        self.client.get(url)
        cita.refresh_from_db()
        self.assertNotEqual(cita.state_cite, Cite.STATE_ATTENDED)
