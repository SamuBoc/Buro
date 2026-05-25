from django.contrib.auth.models import User, Group
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.constants import (
    ROLE_ADMINISTRADOR,
    ROLE_ESTUDIANTE,
    ROLE_PROFESOR,
    ROLE_SECRETARIA,
)
from beneficiary.models import Beneficiary
from cases.models import Case, CommunicationInteraction


_TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def _make_user(username, role):
    user = User.objects.create_user(username=username, password='pass1234')
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.add(group)
    return user


def _make_case(created_by):
    b = Beneficiary.objects.create(
        name='Test Beneficiary',
        location='Cali',
        phone='3000000000',
        email='test@test.com',
    )
    return Case.objects.create(
        beneficiary=b,
        created_by=created_by,
        sala=Case.ROOM_CIVIL,
        description='test',
    )


def _make_interaction(case, user, interaction_type, direction='saliente'):
    return CommunicationInteraction.objects.create(
        case=case,
        registered_by=user,
        interaction_type=interaction_type,
        direction=direction,
        description='test interaction',
    )


@override_settings(STORAGES=_TEST_STORAGES)
class CommunicationMetricsAccessTest(TestCase):
    def setUp(self):
        self.admin = _make_user('admin_hu24', ROLE_ADMINISTRADOR)
        self.profesor = _make_user('prof_hu24', ROLE_PROFESOR)
        self.secretaria = _make_user('sec_hu24', ROLE_SECRETARIA)
        self.estudiante = _make_user('est_hu24', ROLE_ESTUDIANTE)
        self.url = reverse('communication_metrics')

    def test_administrador_puede_acceder(self):
        self.client.login(username='admin_hu24', password='pass1234')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'cases/communication_metrics.html')

    def test_profesor_no_puede_acceder(self):
        self.client.login(username='prof_hu24', password='pass1234')
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 200)

    def test_secretaria_no_puede_acceder(self):
        self.client.login(username='sec_hu24', password='pass1234')
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 200)

    def test_estudiante_no_puede_acceder(self):
        self.client.login(username='est_hu24', password='pass1234')
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 200)

    def test_sin_login_redirige(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])


@override_settings(STORAGES=_TEST_STORAGES)
class CommunicationMetricsDataTest(TestCase):
    def setUp(self):
        self.admin = _make_user('admin_data', ROLE_ADMINISTRADOR)
        self.case = _make_case(self.admin)
        self.url = reverse('communication_metrics')
        self.client.login(username='admin_data', password='pass1234')

    def test_metricas_agrupan_por_canal(self):
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_CALL)
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_CALL)
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_MESSAGE)

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

        metrics = resp.context['metrics']
        types = {m['type']: m['count'] for m in metrics}
        self.assertEqual(types.get(CommunicationInteraction.TYPE_CALL), 2)
        self.assertEqual(types.get(CommunicationInteraction.TYPE_MESSAGE), 1)

    def test_total_es_suma_de_todas_las_interacciones(self):
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_EMAIL)
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_PRESENCIAL)

        resp = self.client.get(self.url)
        self.assertEqual(resp.context['total'], 2)

    def test_filtro_por_canal_retorna_solo_ese_tipo(self):
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_CALL)
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_CALL)
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_MESSAGE)

        resp = self.client.get(self.url, {'tipo': CommunicationInteraction.TYPE_CALL})
        self.assertEqual(resp.status_code, 200)

        interactions = resp.context['interactions']
        for i in interactions:
            self.assertEqual(i.interaction_type, CommunicationInteraction.TYPE_CALL)
        self.assertEqual(interactions.count(), 2)

    def test_filtro_vacio_retorna_todas(self):
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_CALL)
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_EMAIL)

        resp = self.client.get(self.url)
        self.assertEqual(resp.context['interactions'].count(), 2)

    def test_sin_interacciones_total_es_cero(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.context['total'], 0)
        self.assertEqual(len(resp.context['metrics']), 0)

    def test_template_muestra_tarjetas_por_canal(self):
        _make_interaction(self.case, self.admin, CommunicationInteraction.TYPE_CALL)

        resp = self.client.get(self.url)
        self.assertContains(resp, 'Llamada')

    def test_template_muestra_filtro(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, 'Filtrar por canal')

    def test_tipo_choices_en_contexto(self):
        resp = self.client.get(self.url)
        self.assertIn('tipo_choices', resp.context)
        self.assertEqual(
            list(resp.context['tipo_choices']),
            list(CommunicationInteraction.TYPE_CHOICES),
        )
