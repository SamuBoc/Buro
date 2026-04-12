from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Case, CaseAuditLog, Notification
from .email_utils import send_case_status_email


@receiver(pre_save, sender=Case)
def case_pre_save(sender, instance, **kwargs):
    """Guarda el estado actual antes de que se aplique el cambio."""
    if instance.pk:
        try:
            old = Case.objects.get(pk=instance.pk)
            instance._previous_status = old.status
        except Case.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Case)
def case_post_save(sender, instance, created, **kwargs):

    request = getattr(instance, '_request', None)
    ip      = _get_client_ip(request) if request else None
    user    = request.user if request and request.user.is_authenticated else None

    if created:
        CaseAuditLog.objects.create(
            case=instance,
            user=user,
            action='CREATED',
            description=f'Caso {instance.radicado} creado. Sala: {instance.sala}. Asunto: {instance.asunto}.',
            case_radicado=instance.radicado,
            ip_address=ip,
        )
    else:
        previous_status = getattr(instance, '_previous_status', None)
        current_status  = instance.status

        if previous_status and previous_status != current_status:
            CaseAuditLog.objects.create(
                case=instance,
                user=user,
                action='STATUS_CHANGED',
                description=(
                    f'Estado del caso {instance.radicado} cambió '
                    f'de "{previous_status}" a "{current_status}".'
                ),
                previous_status=previous_status,
                new_status=current_status,
                case_radicado=instance.radicado,
                ip_address=ip,
            )
            _create_status_notification(instance, previous_status, current_status, user)
        else:
            CaseAuditLog.objects.create(
                case=instance,
                user=user,
                action='UPDATED',
                description=f'Caso {instance.radicado} actualizado.',
                case_radicado=instance.radicado,
                ip_address=ip,
            )


@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created, **kwargs):

    if created and instance.notification_type == 'STATUS_CHANGE':
        send_case_status_email(instance)


def _create_status_notification(case, previous_status, new_status, triggered_by):
    beneficiary = getattr(case, 'beneficiary', None)
    if not beneficiary:
        return

    recipient = getattr(beneficiary, 'user', None)
    if not recipient:
        return

    status_messages = {
        'Nuevo':       'Su caso ha sido recibido y registrado en el sistema.',
        'En estudio':  'Su caso está siendo estudiado por el estudiante asignado.',
        'En revisión': 'Su caso está siendo revisado por el profesor supervisor.',
        'Cerrado':     'Su caso ha sido cerrado. Gracias por confiar en el Consultorio Jurídico ICESI.',
        'Rechazado':   'Su caso no puede ser atendido en este momento. Contáctenos para más información.',
    }
    detail = status_messages.get(new_status, f'El estado de su caso ha cambiado a: {new_status}.')

    Notification.objects.create(
        recipient_user=recipient,
        case=case,
        notification_type='STATUS_CHANGE',
        title=f'Actualización de su caso {case.radicado}',
        message=(
            f'Estimado/a {beneficiary.full_name},\n\n'
            f'Le informamos que el estado de su caso ({case.radicado}) '
            f'ha cambiado de "{previous_status}" a "{new_status}".\n\n'
            f'{detail}\n\n'
            f'Para más información comuníquese con el Consultorio Jurídico ICESI.'
        ),
        previous_status=previous_status,
        new_status=new_status,
    )


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_case_file_action(case, user, action, filename, ip=None):
    
    label = 'adjuntado' if action == 'FILE_UPLOADED' else 'eliminado'
    CaseAuditLog.objects.create(
        case=case,
        user=user,
        action=action,
        description=f'Archivo "{filename}" {label} del caso {case.radicado}.',
        case_radicado=case.radicado,
        ip_address=ip,
    )