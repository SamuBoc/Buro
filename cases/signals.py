from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import logging

from core.utils import get_client_ip
from .models import Case, CaseAuditLog, Notification
from .email_utils import send_case_status_email, send_case_assignment_email

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Case)
def case_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Case.objects.get(pk=instance.pk)
            instance._previous_status = old.state
        except Case.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Case)
def case_post_save(sender, instance, created, **kwargs):
    request = getattr(instance, '_request', None)
    ip      = get_client_ip(request) if request else None
    user    = request.user if request and request.user.is_authenticated else None

    if created:
        CaseAuditLog.objects.create(
            case=instance,
            user=user,
            action='CREATED',
            description=(
                f'Caso {instance.code} creado. '
                f'Sala: {instance.sala}. '
                f'Descripción: {instance.description}.'
            ),
            case_radicado=instance.code,
            ip_address=ip,
        )
    else:
        previous_status = getattr(instance, '_previous_status', None)
        current_status  = instance.state

        if previous_status and previous_status != current_status:
            if getattr(instance, '_skip_status_log', False):
                return

            CaseAuditLog.objects.create(
                case=instance,
                user=user,
                action='STATUS_CHANGED',
                description=(
                    f'Estado del caso {instance.code} cambió '
                    f'de "{previous_status}" a "{current_status}".'
                ),
                previous_status=previous_status,
                new_status=current_status,
                case_radicado=instance.code,
                ip_address=ip,
            )
            _create_status_notification(instance, previous_status, current_status, user)
        else:
            CaseAuditLog.objects.create(
                case=instance,
                user=user,
                action='UPDATED',
                description=f'Caso {instance.code} actualizado.',
                case_radicado=instance.code,
                ip_address=ip,
            )


@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.notification_type == 'STATUS_CHANGE':
        send_case_status_email(instance)
    elif instance.notification_type == 'ASSIGNMENT':
        send_case_assignment_email(instance)


def _create_status_notification(case, previous_status, new_status, triggered_by):
    status_messages = {
        'Registrado - Pendiente asignacion': 'El caso ha sido recibido y registrado en el sistema.',
        'Asignado a estudiante':             'El caso ha sido asignado a un estudiante.',
        'Sin estudiantes disponibles':       'El caso fue registrado pero no hay estudiantes disponibles.',
    }
    detail = status_messages.get(new_status, f'El estado del caso ha cambiado a: {new_status}.')

    if triggered_by:
        Notification.objects.create(
            recipient_user=triggered_by,
            case=case,
            notification_type='STATUS_CHANGE',
            title=f'Cambio de estado — {case.code}',
            message=(
                f'El estado del caso {case.code} '
                f'(Beneficiario: {case.beneficiary.name}) '
                f'ha cambiado de "{previous_status}" a "{new_status}".\n\n'
                f'{detail}'
            ),
            previous_status=previous_status,
            new_status=new_status,
        )

    if case.beneficiary and case.beneficiary.email:
        from mail.views import notify_beneficiary
        try:
            notify_beneficiary(
                case.beneficiary.id,
                f'Actualización de su caso {case.code}',
                (
                    f'El estado de su caso {case.code} '
                    f'ha cambiado de "{previous_status}" a "{new_status}".\n\n'
                    f'{detail}'
                ),
            )
        except Exception as exc:
            logger.error(
                'Failed to notify beneficiary %s for case %s: %s',
                case.beneficiary.id, case.code, exc,
            )


def log_case_file_action(case, user, action, filename, ip=None):
    label = 'adjuntado' if action == 'FILE_UPLOADED' else 'eliminado'
    CaseAuditLog.objects.create(
        case=case,
        user=user,
        action=action,
        description=f'Archivo "{filename}" {label} del caso {case.code}.',
        case_radicado=case.code,
        ip_address=ip,
    )