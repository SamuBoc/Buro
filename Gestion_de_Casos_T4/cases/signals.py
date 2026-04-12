from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .email_utils import send_case_status_email
from .models import Case, CaseAuditLog, CaseDocument, Notification


@receiver(pre_save, sender=Case)
def case_pre_save(sender, instance, **kwargs):
    """Guarda el estado actual antes de que se aplique el cambio."""
    if instance.pk:
        try:
            old = Case.objects.get(pk=instance.pk)
            instance._previous_state = old.state
        except Case.DoesNotExist:
            instance._previous_state = None
    else:
        instance._previous_state = None


@receiver(post_save, sender=Case)
def case_post_save(sender, instance, created, **kwargs):
    request = getattr(instance, '_request', None)
    ip = _get_client_ip(request) if request else None
    user = request.user if request and request.user.is_authenticated else None

    if created:
        CaseAuditLog.objects.create(
            case=instance,
            user=user,
            action='CREATED',
            description=f'Caso {instance.code} creado. Sala: {instance.sala}.',
            case_radicado=instance.code,
            ip_address=ip,
        )
        return

    previous_state = getattr(instance, '_previous_state', None)
    current_state = instance.state

    if previous_state and previous_state != current_state:
        CaseAuditLog.objects.create(
            case=instance,
            user=user,
            action='STATUS_CHANGED',
            description=(
                f'Estado del caso {instance.code} cambio '
                f'de "{previous_state}" a "{current_state}".'
            ),
            previous_status=previous_state,
            new_status=current_state,
            case_radicado=instance.code,
            ip_address=ip,
        )
        _create_status_notification(instance, previous_state, current_state)
    else:
        CaseAuditLog.objects.create(
            case=instance,
            user=user,
            action='UPDATED',
            description=f'Caso {instance.code} actualizado.',
            case_radicado=instance.code,
            ip_address=ip,
        )


@receiver(post_save, sender=CaseDocument)
def case_document_post_save(sender, instance, created, **kwargs):
    if not created:
        return

    request = getattr(instance, '_request', None)
    ip = _get_client_ip(request) if request else None
    user = request.user if request and request.user.is_authenticated else None

    CaseAuditLog.objects.create(
        case=instance.case,
        user=user,
        action='FILE_UPLOADED',
        description=f'Archivo "{instance.file.name}" adjuntado al caso {instance.case.code}.',
        case_radicado=instance.case.code,
        ip_address=ip,
    )


@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created, **kwargs):
    if created and instance.notification_type == 'STATUS_CHANGE':
        send_case_status_email(instance)


def _create_status_notification(case, previous_state, new_state):
    if not case.assigned_student:
        return

    Notification.objects.create(
        recipient_user=case.assigned_student,
        case=case,
        notification_type='STATUS_CHANGE',
        title=f'Actualizacion del caso {case.code}',
        message=(
            f'El estado del caso {case.code} cambio '
            f'de "{previous_state}" a "{new_state}".'
        ),
        previous_status=previous_state,
        new_status=new_state,
    )


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
