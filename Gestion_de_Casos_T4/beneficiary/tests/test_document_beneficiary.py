"""
Tests unitarios - Documento de Identidad del Beneficiario
Clase: DocumentBeneficiary
Cubre: modelo, carga al registrar, actualización al editar, persistencia y detalle
"""

import io
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from accounts.constants import ROLE_SECRETARIA, ROLE_ADMINISTRADOR
from beneficiary.models import Beneficiary, DocumentBeneficiary


def make_user(username, password='pass1234', group_name=None):
    user = User.objects.create_user(username=username, password=password)
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def make_beneficiary():
    return Beneficiary.objects.create(
        name='Laura Torres',
        location='Cali, Valle',
        phone='3001234567',
        email='laura@test.com',
        colombian_identification='1001234567',
    )


def make_fake_file(name='documento.pdf', content=b'%PDF-fake-content', content_type='application/pdf'):
    """Genera un archivo simulado para subir en los formularios."""
    return SimpleUploadedFile(name, content, content_type=content_type)


def datos_beneficiario_validos():
    return {
        'name': 'Carlos Ruiz',
        'colombian_identification': '9876543210',
        'location': 'Medellin, Antioquia',
        'phone': '3109876543',
        'email': 'carlos@test.com',
        'allow_conditions': True,
    }

class DocumentBeneficiaryModelTest(TestCase):

    def setUp(self):
        self.beneficiary = make_beneficiary()

    def test_documento_se_guarda_correctamente_en_db(self):
        doc = DocumentBeneficiary.objects.create(
            beneficiary=self.beneficiary,
            file=make_fake_file(),
        )
        self.assertEqual(DocumentBeneficiary.objects.count(), 1)
        self.assertEqual(doc.beneficiary, self.beneficiary)

    def test_str_retorna_nombre_del_beneficiario(self):
        doc = DocumentBeneficiary.objects.create(
            beneficiary=self.beneficiary,
            file=make_fake_file(),
        )
        self.assertIn('Laura Torres', str(doc))

    def test_date_upload_se_asigna_automaticamente(self):
        doc = DocumentBeneficiary.objects.create(
            beneficiary=self.beneficiary,
            file=make_fake_file(),
        )
        self.assertIsNotNone(doc.date_upload)

    def test_eliminar_beneficiario_elimina_su_documento(self):
        DocumentBeneficiary.objects.create(
            beneficiary=self.beneficiary,
            file=make_fake_file(),
        )
        self.beneficiary.delete()
        self.assertEqual(DocumentBeneficiary.objects.count(), 0)

    def test_beneficiario_sin_documento_retorna_none(self):
        resultado = DocumentBeneficiary.objects.filter(beneficiary=self.beneficiary).first()
        self.assertIsNone(resultado)

    def test_ruta_del_archivo_incluye_nombre_del_beneficiario(self):
        doc = DocumentBeneficiary.objects.create(
            beneficiary=self.beneficiary,
            file=make_fake_file('cedula.pdf'),
        )
        self.assertIn('Laura Torres', doc.file.name)

class DocumentoAlRegistrarTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('sec_doc', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_doc', password='pass1234')
        self.url = reverse('beneficiary_register')

    def test_registro_con_documento_crea_beneficiario_y_documento(self):
        data = datos_beneficiario_validos()
        data['file'] = make_fake_file()
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(Beneficiary.objects.count(), 1)
        self.assertEqual(DocumentBeneficiary.objects.count(), 1)

    def test_registro_con_documento_redirige_a_lista(self):
        data = datos_beneficiario_validos()
        data['file'] = make_fake_file()
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_list'))

    def test_registro_sin_documento_no_guarda_nada(self):
        data = datos_beneficiario_validos()
        # Sin 'file'
        self.client.post(self.url, data, format='multipart')
        self.assertEqual(Beneficiary.objects.count(), 0)
        self.assertEqual(DocumentBeneficiary.objects.count(), 0)

    def test_documento_queda_asociado_al_beneficiario_correcto(self):
        data = datos_beneficiario_validos()
        data['file'] = make_fake_file()
        self.client.post(self.url, data, format='multipart')
        beneficiario = Beneficiary.objects.first()
        documento = DocumentBeneficiary.objects.first()
        self.assertEqual(documento.beneficiary, beneficiario)

    def test_registro_con_archivo_png_es_aceptado(self):
        data = datos_beneficiario_validos()
        data['file'] = make_fake_file('foto.png', b'\x89PNG-fake', 'image/png')
        self.client.post(self.url, data, format='multipart')
        self.assertEqual(DocumentBeneficiary.objects.count(), 1)

    def test_registro_con_archivo_jpg_es_aceptado(self):
        data = datos_beneficiario_validos()
        data['file'] = make_fake_file('foto.jpg', b'\xff\xd8\xff-fake', 'image/jpeg')
        self.client.post(self.url, data, format='multipart')
        self.assertEqual(DocumentBeneficiary.objects.count(), 1)

class DocumentoAlEditarTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('sec_upd', group_name=ROLE_SECRETARIA)
        self.client.login(username='sec_upd', password='pass1234')
        self.beneficiary = make_beneficiary()
        self.documento = DocumentBeneficiary.objects.create(
            beneficiary=self.beneficiary,
            file=make_fake_file('original.pdf'),
        )
        self.url = reverse('beneficiary_update', args=[self.beneficiary.pk])

    def _datos_edicion(self, **overrides):
        base = {
            'name': 'Laura Torres',
            'colombian_identification': '1001234567',
            'location': 'Cali, Valle',
            'phone': '3001234567',
            'email': 'laura@test.com',
        }
        base.update(overrides)
        return base

    def test_editar_sin_nuevo_archivo_mantiene_documento_existente(self):
        self.client.post(self.url, self._datos_edicion(), format='multipart')
        self.assertEqual(DocumentBeneficiary.objects.count(), 1)
        doc_actual = DocumentBeneficiary.objects.first()
        self.assertIn('Documento_Identidad', doc_actual.file.name)

    def test_editar_con_nuevo_archivo_reemplaza_el_documento(self):
        data = self._datos_edicion()
        data['file'] = make_fake_file('nuevo.pdf')
        self.client.post(self.url, data, format='multipart')
        self.assertEqual(DocumentBeneficiary.objects.count(), 1)
        doc_actual = DocumentBeneficiary.objects.first()
        self.assertIn('Documento_Identidad', doc_actual.file.name)

    def test_edicion_exitosa_redirige_a_lista(self):
        response = self.client.post(self.url, self._datos_edicion(), format='multipart')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_list'))

    def test_no_se_duplica_el_documento_al_editar(self):
        data = self._datos_edicion()
        data['file'] = make_fake_file('reemplazo.pdf')
        self.client.post(self.url, data, format='multipart')
        self.assertEqual(DocumentBeneficiary.objects.count(), 1)

class DocumentoEnDetalleTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user('user_det', group_name=ROLE_SECRETARIA)
        self.client.login(username='user_det', password='pass1234')
        self.beneficiary = make_beneficiary()

    def test_detalle_muestra_enlace_de_documento_si_existe(self):
        DocumentBeneficiary.objects.create(
            beneficiary=self.beneficiary,
            file=make_fake_file('cedula.pdf'),
        )
        url = reverse('beneficiary_detail', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertContains(response, 'documento')

    def test_detalle_indica_sin_documento_si_no_existe(self):
        url = reverse('beneficiary_detail', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertContains(response, 'Sin documento')

    def test_detalle_pasa_documento_en_contexto(self):
        doc = DocumentBeneficiary.objects.create(
            beneficiary=self.beneficiary,
            file=make_fake_file('cedula.pdf'),
        )
        url = reverse('beneficiary_detail', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertEqual(response.context['documento'], doc)

    def test_detalle_contexto_documento_es_none_sin_archivo(self):
        url = reverse('beneficiary_detail', args=[self.beneficiary.pk])
        response = self.client.get(url)
        self.assertIsNone(response.context['documento'])
