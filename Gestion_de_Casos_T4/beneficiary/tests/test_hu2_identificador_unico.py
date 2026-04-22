from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

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


def make_beneficiary(name='Ana Lopez', email='ana@test.com'):
    return Beneficiary.objects.create(
        name=name,
        location='Cali',
        phone='3009876543',
        email=email,
    )


class HU2_GeneracionIdTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.secretaria = make_user('sec_hu2', group_name=ROLE_SECRETARIA)

    def test_id_se_genera_automaticamente_al_crear(self):
        b = make_beneficiary()
        self.assertIsNotNone(b.id)
        self.assertNotEqual(b.id, '')

    def test_id_tiene_formato_correcto(self):
        b = make_beneficiary()
        year = timezone.now().year
        self.assertRegex(b.id, rf'^BEN-{year}-\d{{4}}$')

    def test_id_se_asocia_al_beneficiario_correcto(self):
        b = make_beneficiary(email='unico@test.com')
        recuperado = Beneficiary.objects.get(email='unico@test.com')
        self.assertEqual(recuperado.id, b.id)

    def test_ids_son_secuenciales(self):
        b1 = make_beneficiary(email='b1@test.com')
        b2 = make_beneficiary(name='Carlos Ruiz', email='b2@test.com')
        seq1 = int(b1.id.split('-')[-1])
        seq2 = int(b2.id.split('-')[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_id_generado_via_formulario(self):
        self.client.login(username='sec_hu2', password='pass1234')
        self.client.post(reverse('beneficiary_register'), {
            'name': 'Laura Gómez',
            'location': 'Cali',
            'phone': '3001112233',
            'email': 'laura@test.com',
            'allow_conditions': True,
        })
        b = Beneficiary.objects.get(email='laura@test.com')
        self.assertTrue(b.id.startswith('BEN-'))


class HU2_PrevencionDuplicadosTest(TestCase):

    def test_dos_beneficiarios_no_comparten_id(self):
        b1 = make_beneficiary(email='b1@test.com')
        b2 = make_beneficiary(name='Otro', email='b2@test.com')
        self.assertNotEqual(b1.id, b2.id)

    def test_id_unico_en_base_de_datos(self):
        b1 = make_beneficiary(email='original@test.com')
        with self.assertRaises(Exception):
            Beneficiary.objects.create(
                id=b1.id,
                name='Duplicado',
                location='Cali',
                phone='3000000000',
                email='duplicado@test.com',
            )

    def test_id_no_se_sobreescribe_al_actualizar(self):
        b = make_beneficiary(email='editar@test.com')
        id_original = b.id
        b.phone = '3111111111'
        b.save()
        b.refresh_from_db()
        self.assertEqual(b.id, id_original)


class HU2_VolumenTest(TestCase):

    def test_50_beneficiarios_tienen_ids_unicos(self):
        ids = []
        for i in range(50):
            b = Beneficiary.objects.create(
                name=f'Beneficiario {i}',
                location='Cali',
                phone=f'300{i:07d}',
                email=f'ben{i}@test.com',
            )
            ids.append(b.id)
        self.assertEqual(len(ids), len(set(ids)))

    def test_ids_son_todos_del_formato_correcto_en_volumen(self):
        year = timezone.now().year
        for i in range(20):
            b = Beneficiary.objects.create(
                name=f'Ben {i}',
                location='Cali',
                phone=f'300{i:07d}',
                email=f'vol{i}@test.com',
            )
            self.assertRegex(b.id, rf'^BEN-{year}-\d{{4}}$')