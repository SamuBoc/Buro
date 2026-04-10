import os

from django.db import models
from django.utils import timezone

from beneficiary.models import Beneficiary


class Case(models.Model):
    ROOM_CIVIL = 'civil'
    ROOM_LABORAL = 'laboral'
    ROOM_PENAL = 'penal'
    ROOM_PUBLICO = 'publico'
    ROOM_FAMILIA = 'familia'

    ROOM_CHOICES = [
        (ROOM_CIVIL, 'Civil'),
        (ROOM_LABORAL, 'Laboral'),
        (ROOM_PENAL, 'Penal'),
        (ROOM_PUBLICO, 'Publico'),
        (ROOM_FAMILIA, 'Familia'),
    ]

    DEFAULT_STATE = 'Registrado - Pendiente asignacion'

    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Codigo'
    )
    sala = models.CharField(
        max_length=20,
        choices=ROOM_CHOICES,
        verbose_name='Sala juridica'
    )
    description = models.TextField(verbose_name='Descripcion del problema')
    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='cases',
        verbose_name='Beneficiario'
    )
    state = models.CharField(
        max_length=100,
        default=DEFAULT_STATE,
        verbose_name='Estado'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creacion'
    )

    class Meta:
        verbose_name = 'Caso'
        verbose_name_plural = 'Casos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} - {self.beneficiary.name}'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    @classmethod
    def generate_code(cls):
        year = timezone.now().year
        prefix = f'CJ-{year}-'
        last_case = cls.objects.filter(code__startswith=prefix).order_by('-code').first()

        if last_case:
            last_sequence = int(last_case.code.split('-')[-1])
            next_sequence = last_sequence + 1
        else:
            next_sequence = 1

        return f'{prefix}{next_sequence:04d}'


def case_document_upload_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    return f'case_documents/{instance.case.code}/{timezone.now().strftime("%Y%m%d%H%M%S%f")}{extension}'


class CaseDocument(models.Model):
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Caso'
    )
    file = models.FileField(
        upload_to=case_document_upload_path,
        verbose_name='Archivo'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de carga'
    )

    class Meta:
        verbose_name = 'Documento del caso'
        verbose_name_plural = 'Documentos del caso'
        ordering = ['-uploaded_at']

    def __str__(self):
        return os.path.basename(self.file.name)
