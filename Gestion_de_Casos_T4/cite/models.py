from django.db import models
from beneficiary.models import Beneficiary
from datetime import date


class Cite(models.Model):
    id = models.AutoField(verbose_name="Id de cita", primary_key=True)

    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        verbose_name="Beneficiario",
        related_name="cites"
    )

    date_assigned = models.DateField()
    
    MODALITY_INPERSON = 'PRESENCIAL'
    MODALITY_PHONE = 'TELEFONICA'
    MODALITY_VIRTUAL = 'VIRTUAL'

    MODALITY_CHOICES = [
        (MODALITY_INPERSON, 'Presencial'),
        (MODALITY_PHONE, 'Telefonica'),
        (MODALITY_VIRTUAL, 'Virtual'),
    ]

    modality_cite = models.CharField(
        max_length=20,
        choices=MODALITY_CHOICES,
        default=MODALITY_INPERSON,
        verbose_name="Modalidad"
    )

    STATE_PENDING = 'Pendiente'
    STATE_CONFIRMED = 'Confirmada'
    STATE_CANCELED = 'Cancelada'
    STATE_SOLVE = "Atendida"
    STATE_ATTENDED = 'Asistió'
    STATE_NO_SHOW = 'No asistió'

    STATE_CHOICES = [
        (STATE_PENDING, 'Pendiente'),
        (STATE_CONFIRMED, 'Confirmada'),
        (STATE_CANCELED, 'Cancelada'),
        (STATE_SOLVE, 'Atendida'),
        (STATE_ATTENDED, 'Asistió'),
        (STATE_NO_SHOW, 'No asistió'),
    ]

    state_cite = models.CharField(
        max_length=20,
        choices=STATE_CHOICES,
        default=STATE_PENDING,
        verbose_name="Estado"
    )

    CHANNEL_INPERSON = 'Presencial'
    CHANNEL_PHONE = 'Telefonica'
    CHANNEL_WEB = 'Página Web'
    CHANNEL_EMAIL = 'Correo Electronico'

    CHANNEL_CHOICES = [
        (CHANNEL_INPERSON, 'Presencial'),
        (CHANNEL_PHONE, 'Telefonica'),
        (CHANNEL_WEB, 'Pagina Web'),
        (CHANNEL_EMAIL, 'Correo Electronico'),
    ]

    request_cite = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default=CHANNEL_WEB,
        verbose_name="Medio de Solicitud"
    )

    description = models.CharField(max_length=2000, verbose_name='Descripcion')

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['-id']

    def __str__(self):
        return f"Cita #{self.id} - {self.beneficiary.name} ({self.get_modality_cite_display()})"
