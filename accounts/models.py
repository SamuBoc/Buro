from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROOM_CIVIL = 'civil'
    ROOM_LABORAL = 'laboral'
    ROOM_PENAL = 'penal'
    ROOM_PUBLICO = 'publico'
    ROOM_FAMILIA = 'familia'

    ROOM_CHOICES = [
        (ROOM_CIVIL, 'Civil'),
        (ROOM_LABORAL, 'Laboral'),
        (ROOM_PENAL, 'Penal'),
        (ROOM_PUBLICO, 'Publico'),
        (ROOM_FAMILIA, 'Familia'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuario'
    )
    student_code = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Codigo estudiantil'
    )
    max_cases = models.PositiveIntegerField(
        default=5,
        verbose_name='Capacidad maxima de casos'
    )
    availability = models.BooleanField(
        default=True,
        verbose_name='Disponible'
    )
    preferred_room = models.CharField(
        max_length=20,
        choices=ROOM_CHOICES,
        null=True,
        blank=True,
        verbose_name='Sala preferente'
    )

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f'Perfil de {self.user.username}'

    @property
    def active_cases(self):
        """Calcula los casos activos asignados al estudiante sin persistirlos."""
        return self.user.assigned_cases.exclude(status='borrador').count()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
