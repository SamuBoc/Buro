from django.core.management.base import BaseCommand

from cases.services import generate_deadline_alerts


class Command(BaseCommand):
    help = 'Genera alertas de vencimiento para casos con fecha limite cercana.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Cantidad de dias de anticipacion para generar alertas.',
        )

    def handle(self, *args, **options):
        created_notifications = generate_deadline_alerts(days_ahead=options['days'])
        self.stdout.write(self.style.SUCCESS(
            f'Alertas de vencimiento generadas: {created_notifications}'
        ))
