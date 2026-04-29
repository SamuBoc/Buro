from datetime import date

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from beneficiary.models import Beneficiary, BeneficiaryAuditLog
from cite.models import Cite


def make_user(username='benef_hu15', password='pass1234'):
	return User.objects.create_user(
		username=username,
		password=password,
		email=f'{username}@test.com'
	)


def make_beneficiary():
	return Beneficiary.objects.create(
		name='Laura Diaz',
		location='Cali',
		phone='3001234567',
		email='laura@example.com',
	)


def make_cite(beneficiary, state=Cite.STATE_PENDING):
	return Cite.objects.create(
		beneficiary=beneficiary,
		date_assigned=date.today(),
		modality_cite=Cite.MODALITY_INPERSON,
		request_cite=Cite.CHANNEL_WEB,
		description='Cita de prueba.',
		state_cite=state,
	)


class HU15SeleccionTipoAtencionTest(TestCase):

	def setUp(self):
		self.client = Client()
		self.user = make_user()
		self.beneficiary = make_beneficiary()
		self.client.login(username='benef_hu15', password='pass1234')

	def test_seleccion_modalidad_registra_cita(self):
		"""POSITIVO: al seleccionar modalidad, la cita se registra con ese valor."""
		response = self.client.post(
			reverse('create_cite', args=[self.beneficiary.id]),
			{
				'modality_cite': Cite.MODALITY_PHONE,
				'request_cite': Cite.CHANNEL_WEB,
				'description': 'Necesito asesoria sobre contrato laboral.',
			}
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(Cite.objects.count(), 1)
		cite = Cite.objects.first()
		self.assertEqual(cite.modality_cite, Cite.MODALITY_PHONE)
		self.assertEqual(cite.beneficiary, self.beneficiary)

	def test_modalidad_no_seleccionada_muestra_error(self):
		"""NEGATIVO: si no selecciona modalidad, el sistema solicita una opcion valida."""
		response = self.client.post(
			reverse('create_cite', args=[self.beneficiary.id]),
			{
				'modality_cite': '',
				'request_cite': Cite.CHANNEL_WEB,
				'description': 'Necesito orientacion general.',
			}
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(Cite.objects.count(), 0)
		self.assertContains(response, 'Debes seleccionar una modalidad valida para continuar.')


class HU18RegistroAsistenciaTest(TestCase):

	def setUp(self):
		self.client = Client()
		self.user = make_user(username='sec_hu18')
		self.beneficiary = make_beneficiary()
		self.cite = make_cite(self.beneficiary)
		self.client.login(username='sec_hu18', password='pass1234')

	def test_registrar_asistencia_actualiza_estado_y_log(self):
		response = self.client.post(
			reverse('register_cite_attendance', args=[self.cite.id, 'asistio'])
		)

		self.assertEqual(response.status_code, 302)
		self.cite.refresh_from_db()
		self.assertEqual(self.cite.state_cite, Cite.STATE_ATTENDED)
		log = BeneficiaryAuditLog.objects.filter(
			beneficiary=self.beneficiary,
			action='CITE_ATTENDED'
		).first()
		self.assertIsNotNone(log)
		self.assertIn('asistió', log.description)

	def test_registrar_inasistencia_actualiza_estado_y_log(self):
		response = self.client.post(
			reverse('register_cite_attendance', args=[self.cite.id, 'no-asistio'])
		)

		self.assertEqual(response.status_code, 302)
		self.cite.refresh_from_db()
		self.assertEqual(self.cite.state_cite, Cite.STATE_NO_SHOW)
		log = BeneficiaryAuditLog.objects.filter(
			beneficiary=self.beneficiary,
			action='CITE_MISSED'
		).first()
		self.assertIsNotNone(log)
		self.assertIn('no asistió', log.description)
