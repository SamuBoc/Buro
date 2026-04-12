from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Beneficiary(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    location = models.CharField(max_length=300, verbose_name="Ubicación")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Correo electrónico")
    date_register = models.DateField(auto_now_add=True, verbose_name="Fecha de registro")

    class Meta:
        verbose_name = "Beneficiario"
        verbose_name_plural = "Beneficiarios"
        ordering = ['-date_register']

    def __str__(self):
        return self.name

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
