import os

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from beneficiary.models import Beneficiary


class Case(models.Model):
    STATUS_DRAFT = 'borrador'
    STATUS_COMPLETE = 'completo'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Borrador'),
        (STATUS_COMPLETE, 'Completo'),
    ]

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

    STATE_PENDING = 'Registrado - Pendiente asignacion'
    STATE_ASSIGNED = 'Asignado a estudiante'
    STATE_NO_STUDENTS = 'Sin estudiantes disponibles'
    STATE_REJECTED = 'Rechazado'

    DEFAULT_STATE = STATE_PENDING

    code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Codigo'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_COMPLETE,
        verbose_name='Estado del formulario'
    )
    sala = models.CharField(
        max_length=20,
        choices=ROOM_CHOICES,
        null=True,
        blank=True,
        verbose_name='Sala juridica'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descripcion del problema'
    )
    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cases',
        verbose_name='Beneficiario'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cases',
        verbose_name='Creado por'
    )
    assigned_student = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases',
        verbose_name='Estudiante asignado'
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
    deadline_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha limite de atencion'
    )
    deadline_alert_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Alerta de vencimiento enviada el'
    )
    rejection_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='Causal de rechazo'
    )

    class Meta:
        verbose_name = 'Caso'
        verbose_name_plural = 'Casos'
        ordering = ['-created_at']

    def __str__(self):
        beneficiary_name = self.beneficiary.name if self.beneficiary else 'Sin beneficiario'
        return f'{self.code} - {beneficiary_name}'

    def save(self, *args, **kwargs):
        if self.pk:
            previous_case = Case.objects.filter(pk=self.pk).only('deadline_date').first()
            if previous_case and previous_case.deadline_date != self.deadline_date:
                self.deadline_alert_sent_at = None
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


class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ('STATUS_CHANGE', 'Cambio de estado'),
        ('ASSIGNMENT',    'Asignación de estudiante'),
        ('DEADLINE',      'Alerta de vencimiento'),
        ('GENERAL',       'Información general'),
    ]

    recipient_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Destinatario',
    )
    case = models.ForeignKey(
        'Case',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Caso relacionado',
    )
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, default='STATUS_CHANGE'
    )
    title   = models.CharField(max_length=200, verbose_name='Título')
    message = models.TextField(verbose_name='Mensaje')

    previous_status = models.CharField(max_length=50, blank=True, null=True)
    new_status      = models.CharField(max_length=50, blank=True, null=True)

    is_read    = models.BooleanField(default=False, verbose_name='Leída')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Creada el')
    read_at    = models.DateTimeField(null=True, blank=True, verbose_name='Leída el')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        indexes = [
            models.Index(fields=['recipient_user', 'is_read']),
            models.Index(fields=['case']),
        ]

    def __str__(self):
        estado = 'Leída' if self.is_read else 'No leída'
        return f"[{estado}] {self.title} → {self.recipient_user.get_full_name()}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class CaseAuditLog(models.Model):

    ACTION_CHOICES = [
        ('CREATED',         'Caso creado'),
        ('UPDATED',         'Caso actualizado'),
        ('STATUS_CHANGED',  'Estado cambiado'),
        ('ASSIGNED',        'Estudiante asignado'),
        ('REASSIGNED',      'Caso reasignado'),
        ('FILE_UPLOADED',   'Archivo adjuntado'),
        ('FILE_DELETED',    'Archivo eliminado'),
        ('REJECTED',        'Caso rechazado'),
        ('CLOSED',          'Caso cerrado'),
        ('VIEWED',          'Caso consultado'),
        ('SECURITY_DENIED', 'Acceso denegado'),
        ('CREATED',        'Caso creado'),
        ('UPDATED',        'Caso actualizado'),
        ('STATUS_CHANGED', 'Estado cambiado'),
        ('ASSIGNED',       'Estudiante asignado'),
        ('REASSIGNED',     'Caso reasignado'),
        ('FILE_UPLOADED',  'Archivo adjuntado'),
        ('FILE_DELETED',   'Archivo eliminado'),
        ('REJECTED',       'Caso rechazado'),
        ('CLOSED',         'Caso cerrado'),
        ('VIEWED',         'Caso consultado'),
        ('COMMUNICATION',  'Interacción de comunicación'),
    ]

    case = models.ForeignKey(
        'Case',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='Caso',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario responsable',
    )
    action          = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Acción')
    description     = models.TextField(verbose_name='Descripción de la acción')
    previous_status = models.CharField(max_length=50, blank=True, null=True, verbose_name='Estado anterior')
    new_status      = models.CharField(max_length=50, blank=True, null=True, verbose_name='Estado nuevo')
    case_radicado   = models.CharField(max_length=50, blank=True, verbose_name='Radicado del caso')
    timestamp       = models.DateTimeField(default=timezone.now, verbose_name='Fecha y hora')
    ip_address      = models.GenericIPAddressField(null=True, blank=True, verbose_name='Dirección IP')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Bitácora de Caso'
        verbose_name_plural = 'Bitácora de Casos'
        indexes = [
            models.Index(fields=['case', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        user_str = self.user.get_full_name() if self.user else 'Sistema'
        return f"[{self.timestamp:%d/%m/%Y %H:%M}] {user_str} — {self.get_action_display()} — {self.case_radicado}"


class CaseReassignmentLog(models.Model):
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='reassignment_logs',
        verbose_name='Caso'
    )
    old_student = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Estudiante anterior'
    )
    new_student = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name='Estudiante nuevo'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='case_reassignment_logs',
        verbose_name='Reasignado por'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de registro'
    )

    class Meta:
        verbose_name = 'Bitacora de reasignacion'
        verbose_name_plural = 'Bitacora de reasignaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.case.code} - reasignado'



class CommunicationInteraction(models.Model):
    TYPE_MESSAGE    = 'mensaje'
    TYPE_CALL       = 'llamada'
    TYPE_EMAIL      = 'correo'
    TYPE_PRESENCIAL = 'presencial'

    TYPE_CHOICES = [
        (TYPE_MESSAGE,    'Mensaje'),
        (TYPE_CALL,       'Llamada'),
        (TYPE_EMAIL,      'Correo electrónico'),
        (TYPE_PRESENCIAL, 'Presencial'),
    ]

    DIRECTION_IN  = 'entrante'
    DIRECTION_OUT = 'saliente'

    DIRECTION_CHOICES = [
        (DIRECTION_IN,  'Entrante'),
        (DIRECTION_OUT, 'Saliente'),
    ]

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='interactions',
        verbose_name='Caso',
    )
    registered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registered_interactions',
        verbose_name='Registrado por',
    )
    interaction_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Tipo de interacción',
    )
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        verbose_name='Dirección',
    )
    description = models.TextField(verbose_name='Descripción')
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha y hora',
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Interacción de comunicación'
        verbose_name_plural = 'Interacciones de comunicación'
        indexes = [
            models.Index(fields=['case', '-timestamp']),
        ]

    def __str__(self):
        return (
            f'{self.get_interaction_type_display()} — '
            f'{self.case.code} — '
            f'{self.timestamp:%d/%m/%Y %H:%M}'
        )