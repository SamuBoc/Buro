import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def send_case_status_email(notification):
   
    if notification.notification_type != 'STATUS_CHANGE':
        return

    recipient_email = notification.recipient_user.email
    if not recipient_email:
        logger.warning(
            "Notification %s: recipient %s has no email. Skipping.",
            notification.pk,
            notification.recipient_user.username,
        )
        return

    subject = f'[Consultorio Jurídico ICESI] {notification.title}'

    context = {
        'notification':     notification,
        'beneficiary_name': notification.recipient_user.get_full_name(),
        'case_radicado':    notification.case.code,
        'case_asunto':      notification.case.description,
        'previous_status':  notification.previous_status,
        'new_status':       notification.new_status,
        'message':          notification.message,
        'support_email':    getattr(settings, 'DEFAULT_FROM_EMAIL', 'consultorio@icesi.edu.co'),
    }

    html_body  = render_to_string('cases/email/status_change_email.html', context)
    plain_body = render_to_string('cases/email/status_change_email.txt',  context)

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)

        logger.info(
            "Status email sent to %s | case %s | %s -> %s",
            recipient_email,
            notification.case.code,
            notification.previous_status,
            notification.new_status,
        )
    except Exception as exc:
        logger.error(
            "Failed to send email to %s | case %s | error: %s",
            recipient_email,
            notification.case.code,
            exc,
        )