from django.shortcuts import render

# Needed to send mails
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404

# Data from beneficiary
from beneficiary.models import Beneficiary

# Maining main to send info to beneficiaries
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


def notify_beneficiary(pk, subject, message):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)

    if subject and message:
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [beneficiary.email]
            )
        except Exception as exc:
            logger.error(
                "Fallo el envio de correo al beneficiario pk=%s: %s",
                pk,
                exc,
            )