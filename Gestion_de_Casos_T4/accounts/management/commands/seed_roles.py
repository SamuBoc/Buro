from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from accounts.constants import ALL_ROLES


class Command(BaseCommand):
    help = 'Crea los grupos de roles del sistema si no existen.'

    def handle(self, *args, **options):
        created = []
        existing = []

        for role in ALL_ROLES:
            group, was_created = Group.objects.get_or_create(name=role)
            if was_created:
                created.append(role)
            else:
                existing.append(role)

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'Roles creados: {", ".join(created)}'
            ))
        if existing:
            self.stdout.write(
                f'Roles ya existentes: {", ".join(existing)}'
            )
