import os
import sys

from django.apps import AppConfig
from django.conf import settings


class CiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cite'
    verbose_name = 'Gestion de Citas'

    def ready(self):
        if not getattr(settings, 'ENABLE_APP_SCHEDULERS', False):
            return

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

        from .scheduler import send_cite_reminders

        try:
            scheduler = BackgroundScheduler()
            scheduler.add_jobstore(DjangoJobStore(), 'default')
            scheduler.add_job(
                send_cite_reminders,
                trigger=CronTrigger(hour=8, minute=0),
                id='send_cite_reminders',
                name='Recordatorios automaticos de citas',
                replace_existing=True,
            )
            scheduler.start()
        except Exception:
            # No bloquea el arranque si las tablas del scheduler aun no existen.
            return
