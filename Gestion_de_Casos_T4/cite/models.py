from django.db import models
from beneficiary.models import Beneficiary

class Cite(models.Model):
    id = models.AutoField(max_length=20, verbose_name="Id de cita", primary_key=True)

    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        verbose_name="Beneficiario",
        related_name="cites"
    )

    VIRTUAL_MODALITY = 'Virtual'
    INPERSON_MODALITY = 'Presencial'

    modality_cite = models.CharField(max_length=100, default=INPERSON_MODALITY, verbose_name="Modalidad")

    STATE_PENDING = 'Pendiente'
    STATE_CONFIRMED = 'Confirmada'
    STATE_CANCELED = 'Cancelada'
    STATE_SOLVE = "Atendida"

    state_cite = models.CharField(max_length=100, default=STATE_PENDING, verbose_name="Estado")

    CHANNEL_INPERSON = 'Presencial'
    CHANNEL_PHONE = 'Telefonica'
    CHANNEL_WEB = 'Página Web'
    CHANNEL_EMAIL = 'Correo Electronico'

    request_cite = models.CharField(max_length=100, default='Página Web', verbose_name="Medio de Solicitud")

    description = models.CharField(max_length=2000, verbose_name= 'Descripción')
