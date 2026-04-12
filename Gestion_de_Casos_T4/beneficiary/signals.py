from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Beneficiary, BeneficiaryAuditLog


@receiver(pre_save, sender=Beneficiary)
def beneficiary_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Beneficiary.objects.get(pk=instance.pk)
            instance._old_data = {
                'name': old.name,
                'location': old.location,
                'phone': old.phone,
                'email': old.email,
            }
        except Beneficiary.DoesNotExist:
            instance._old_data = {}
    else:
        instance._old_data = {}


@receiver(post_save, sender=Beneficiary)
def beneficiary_post_save(sender, instance, created, **kwargs):
    request = getattr(instance, '_request', None)
    ip = _get_client_ip(request) if request else None
    user = request.user if request and request.user.is_authenticated else None

    if created:
        BeneficiaryAuditLog.objects.create(
            beneficiary=instance,
            user=user,
            action='CREATED',
            description=f'Beneficiario {instance.name} registrado en el sistema.',
            beneficiary_name=instance.name,
            ip_address=ip,
        )
        return

    old_data = getattr(instance, '_old_data', {})
    fields_to_track = {
        'name': 'Nombre',
        'location': 'Ubicacion',
        'phone': 'Telefono',
        'email': 'Correo electronico',
    }
    changed = {
        label: {'anterior': str(old_data.get(field)), 'nuevo': str(getattr(instance, field, None))}
        for field, label in fields_to_track.items()
        if old_data.get(field) != getattr(instance, field, None)
    }

    if changed:
        parts = [f'{k}: "{v["anterior"]}" -> "{v["nuevo"]}"' for k, v in changed.items()]
        BeneficiaryAuditLog.objects.create(
            beneficiary=instance,
            user=user,
            action='UPDATED',
            description=f'Datos actualizados para {instance.name}: {"; ".join(parts)}.',
            changed_fields=changed,
            beneficiary_name=instance.name,
            ip_address=ip,
        )


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
