import os
import sys

from django.apps import AppConfig


class CasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cases'
    verbose_name = 'Gestión de Casos'

    def ready(self):
        import cases.signals  # noqa: F401 — registrar señales

        management_commands_to_skip = {
            'check',
            'makemigrations',
            'migrate',
            'showmigrations',
            'test',
            'shell',
            'collectstatic',
        }
        if any(command in sys.argv for command in management_commands_to_skip):
            return

        # Evita iniciar el scheduler dos veces con el autoreloader de runserver.
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from django_apscheduler.jobstores import DjangoJobStore
        from .scheduler import send_deadline_alerts   # HU-28

        try:
            scheduler = BackgroundScheduler()
            scheduler.add_jobstore(DjangoJobStore(), 'default')
            scheduler.add_job(
                send_deadline_alerts,
                trigger=CronTrigger(hour=7, minute=0),
                id='send_deadline_alerts',
                name='Alertas automáticas de vencimiento de casos',
                replace_existing=True,
            )
            scheduler.start()
        except Exception:
            # No bloquea el arranque si las tablas del scheduler aún no existen.
            return