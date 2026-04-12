from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Beneficiary, BeneficiaryAuditLog


@receiver(pre_save, sender=Beneficiary)
def beneficiary_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Beneficiary.objects.get(pk=instance.pk)
            instance._old_data = {
                'full_name': old.full_name,
                'address':   old.address,
                'phone':     old.phone,
                'email':     old.email,
                'is_active': old.is_active,
            }
        except Beneficiary.DoesNotExist:
            instance._old_data = {}
    else:
        instance._old_data = {}


@receiver(post_save, sender=Beneficiary)
def beneficiary_post_save(sender, instance, created, **kwargs):

    request = getattr(instance, '_request', None)
    ip      = _get_client_ip(request) if request else None
    user    = request.user if request and request.user.is_authenticated else None

    if created:
        BeneficiaryAuditLog.objects.create(
            beneficiary=instance,
            user=user,
            action='CREATED',
            description=f'Beneficiario {instance.full_name} registrado en el sistema.',
            beneficiary_document=instance.document_number,
            beneficiary_name=instance.full_name,
            ip_address=ip,
        )
    else:
        old_data = getattr(instance, '_old_data', {})
        fields_to_track = {
            'full_name': 'Nombre completo',
            'address':   'Dirección',
            'phone':     'Teléfono',
            'email':     'Correo electrónico',
            'is_active': 'Estado activo',
        }
        changed = {
            label: {'anterior': str(old_data.get(field)), 'nuevo': str(getattr(instance, field, None))}
            for field, label in fields_to_track.items()
            if old_data.get(field) != getattr(instance, field, None)
        }

        if changed:
            parts = [f'{k}: "{v["anterior"]}" → "{v["nuevo"]}"' for k, v in changed.items()]
            BeneficiaryAuditLog.objects.create(
                beneficiary=instance,
                user=user,
                action='UPDATED',
                description=f'Datos actualizados para {instance.full_name}: {"; ".join(parts)}.',
                changed_fields=changed,
                beneficiary_document=instance.document_number,
                beneficiary_name=instance.full_name,
                ip_address=ip,
            )


def log_beneficiary_view(beneficiary, user, ip=None):
   
    BeneficiaryAuditLog.objects.create(
        beneficiary=beneficiary,
        user=user,
        action='VIEWED',
        description=f'Datos del beneficiario {beneficiary.full_name} consultados.',
        beneficiary_document=beneficiary.document_number,
        beneficiary_name=beneficiary.full_name,
        ip_address=ip,
    )


def log_beneficiary_doc_action(beneficiary, user, action, filename, ip=None):
   
    label = 'cargado' if action == 'DOC_UPLOADED' else 'eliminado'
    BeneficiaryAuditLog.objects.create(
        beneficiary=beneficiary,
        user=user,
        action=action,
        description=f'Documento "{filename}" {label} para {beneficiary.full_name}.',
        beneficiary_document=beneficiary.document_number,
        beneficiary_name=beneficiary.full_name,
        ip_address=ip,
    )


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')