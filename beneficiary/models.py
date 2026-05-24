import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class EncryptedCharField(models.CharField):
    """Campo que cifra automáticamente al guardar y descifra al leer."""

    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        from core.encryption import decrypt
        return decrypt(value)

    def get_prep_value(self, value):
        if not value:
            return value
        from core.encryption import encrypt
        return encrypt(value)


class Beneficiary(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    id = models.CharField(
        max_length=200,
        verbose_name="Número de Identificación",
        primary_key=True,
        editable=False,
    )
    colombian_identification = EncryptedCharField(
        max_length=512, 
        verbose_name="Cédula de Ciudadanía", 
        default=''
    )
    location = models.CharField(max_length=300, verbose_name="Ubicación")
    phone = EncryptedCharField(
        max_length=512, 
        verbose_name="Teléfono"
    )
    email = models.EmailField(verbose_name="Correo electrónico")
    date_register = models.DateField(auto_now_add=True, verbose_name="Fecha de registro")

    class Meta:
        verbose_name = "Beneficiario"
        verbose_name_plural = "Beneficiarios"
        ordering = ['-date_register']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self._generate_id()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_id(cls):
        year = timezone.now().year
        prefix = f'BEN-{year}-'
        last = cls.objects.filter(id__startswith=prefix).order_by('-id').first()
        if last:
            last_sequence = int(last.id.split('-')[-1])
            next_sequence = last_sequence + 1
        else:
            next_sequence = 1
        return f'{prefix}{next_sequence:04d}'


def beneficiary_document_path(instance, file_name):
    extension = os.path.splitext(file_name)[1]
    return f'beneficiary/{instance.beneficiary.name}/Documento_Identidad{extension}'


class DocumentBeneficiary(models.Model):
    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        verbose_name="Beneficiario",
        related_name="documentos"
    )
    file = models.FileField(
        upload_to=beneficiary_document_path,
        verbose_name='Archivo'
    )
    date_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Carga'
    )

    class Meta:
        verbose_name = 'Documento de Identidad del Beneficiario'
        verbose_name_plural = 'Documentos de Identidad del Beneficiario'
        ordering = ['-date_upload']

    def __str__(self):
        return f"Documento de {self.beneficiary.name}"


class DataDeletionRequest(models.Model):
    STATUS_PENDING = 'pendiente'
    STATUS_APPROVED = 'aprobado'
    STATUS_REJECTED = 'rechazado'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_APPROVED, 'Aprobado'),
        (STATUS_REJECTED, 'Rechazado'),
    ]

    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='data_deletion_requests',
        verbose_name='Beneficiario',
    )
    request_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de solicitud',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Estado de la solicitud',
    )
    reason = models.TextField(
        blank=True,
        verbose_name='Motivo de la solicitud',
    )

    class Meta:
        verbose_name = 'Solicitud de eliminacion de datos'
        verbose_name_plural = 'Solicitudes de eliminacion de datos'
        ordering = ['-request_date']

    def __str__(self):
        return f'Solicitud {self.beneficiary.name} - {self.get_status_display()}'


class BeneficiaryAuditLog(models.Model):

    ACTION_CHOICES = [
        ('CREATED',        'Beneficiario registrado'),
        ('VIEWED',         'Datos consultados'),
        ('UPDATED',        'Datos actualizados'),
        ('DELETED',        'Beneficiario eliminado'),
        ('DOC_UPLOADED',   'Documento cargado'),
        ('DOC_DELETED',    'Documento eliminado'),
        ('DEACTIVATED',    'Beneficiario desactivado'),
        ('REACTIVATED',    'Beneficiario reactivado'),
        ('DATA_EXPORT',    'Datos exportados'),
        ('DELETE_REQUEST', 'Solicitud de eliminación registrada'),
        ('CITE_ATTENDED',  'Asistencia registrada'),
        ('CITE_MISSED',    'Inasistencia registrada'),
    ]

    beneficiary = models.ForeignKey(
        'Beneficiary',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='Beneficiario',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario que realizó la acción',
    )
    action         = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Acción')
    description    = models.TextField(verbose_name='Descripción')
    changed_fields = models.JSONField(
        null=True, blank=True,
        verbose_name='Campos modificados',
        help_text='Diccionario: { "Campo": { "anterior": "...", "nuevo": "..." } }',
    )
    beneficiary_document = models.CharField(max_length=30, blank=True, verbose_name='Documento')
    beneficiary_name     = models.CharField(max_length=200, blank=True, verbose_name='Nombre')
    timestamp  = models.DateTimeField(default=timezone.now, verbose_name='Fecha y hora')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Dirección IP')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Bitácora de Beneficiario'
        verbose_name_plural = 'Bitácora de Beneficiarios'
        indexes = [
            models.Index(fields=['beneficiary', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        user_str = self.user.get_full_name() if self.user else 'Sistema'
        return (
            f"[{self.timestamp:%d/%m/%Y %H:%M}] "
            f"{user_str} — {self.get_action_display()} — "
            f"{self.beneficiary_name or self.beneficiary_document}"
        )
