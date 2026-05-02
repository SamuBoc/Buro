"""
HU-17: Recordatorios automáticos de citas.
El job send_cite_reminders() se ejecuta diariamente a las 8:00 AM.
Envía un correo al beneficiario con citas programadas para el día siguiente.
"""

import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def send_cite_reminders():
    """
    HU-17: Busca citas programadas para mañana que aún no tienen recordatorio enviado
    y envía un correo al beneficiario.
    """
    from .models import Cite

    tomorrow = date.today() + timedelta(days=1)

    pending_cites = Cite.objects.filter(
        date_assigned=tomorrow,
        reminder_sent=False,
        state_cite__in=[Cite.STATE_PENDING, Cite.STATE_CONFIRMED],
    ).select_related('beneficiary')

    sent_count = 0
    error_count = 0

    for cite in pending_cites:
        beneficiary = cite.beneficiary
        recipient_email = beneficiary.email

        if not recipient_email:
            logger.warning(
                "Cite #%s: beneficiary %s has no email. Skipping reminder.",
                cite.id,
                beneficiary.name,
            )
            continue

        subject = f'[Buró Jurídico ICESI] Recordatorio de cita — {cite.date_assigned.strftime("%d/%m/%Y")}'

        plain_body = (
            f'Estimado/a {beneficiary.name},\n\n'
            f'Le recordamos que tiene una cita programada para mañana '
            f'{cite.date_assigned.strftime("%d/%m/%Y")}.\n\n'
            f'Modalidad: {cite.get_modality_cite_display()}\n'
            f'Estado: {cite.state_cite}\n\n'
            f'Por favor comuníquese con el Consultorio Jurídico ICESI si necesita reprogramar.\n\n'
            f'Buró Jurídico — Universidad ICESI'
        )

        html_body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head><meta charset="UTF-8"></head>
        <body style="font-family:Arial,sans-serif;background:#f4f6f9;margin:0;padding:0;">
          <div style="max-width:600px;margin:30px auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1);">
            <div style="background:#1a3a5c;padding:24px 32px;text-align:center;">
              <h1 style="color:#fff;font-size:20px;margin:0;">Buró Jurídico ICESI</h1>
              <p style="color:#a0aec0;font-size:13px;margin:4px 0 0;">Recordatorio de Cita</p>
            </div>
            <div style="padding:32px;color:#2d3748;font-size:15px;line-height:1.6;">
              <p>Estimado/a <strong>{beneficiary.name}</strong>,</p>
              <p>Le recordamos que tiene una cita programada para <strong>mañana {cite.date_assigned.strftime("%d/%m/%Y")}</strong>.</p>
              <div style="background:#f7fafc;border-left:4px solid #1a3a5c;border-radius:4px;padding:16px 20px;margin:20px 0;">
                <p style="margin:0;"><strong>Modalidad:</strong> {cite.get_modality_cite_display()}</p>
                <p style="margin:8px 0 0;"><strong>Estado:</strong> {cite.state_cite}</p>
              </div>
              <p style="font-size:13px;color:#718096;">
                Si necesita reprogramar, comuníquese con nosotros a la brevedad.
              </p>
            </div>
            <div style="background:#f7fafc;padding:20px 32px;text-align:center;font-size:12px;color:#718096;border-top:1px solid #e2e8f0;">
              <p>© Buró Jurídico ICESI — Universidad ICESI, Cali, Colombia</p>
              <p>Este mensaje es generado automáticamente. No responda a este correo.</p>
            </div>
          </div>
        </body>
        </html>
        """

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)

            cite.reminder_sent = True
            cite.save(update_fields=['reminder_sent'])
            sent_count += 1

            logger.info(
                "Reminder sent to %s for cite #%s on %s",
                recipient_email,
                cite.id,
                cite.date_assigned,
            )

        except Exception as exc:
            error_count += 1
            logger.error(
                "Failed to send reminder to %s for cite #%s: %s",
                recipient_email,
                cite.id,
                exc,
            )

    logger.info(
        "Reminder job finished. Sent: %d | Errors: %d | Date: %s",
        sent_count,
        error_count,
        tomorrow,
    )