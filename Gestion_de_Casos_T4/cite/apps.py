from django.apps import AppConfig


class CiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cite'
    verbose_name = 'Gestión de Citas'

    def ready(self):
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from django_apscheduler.jobstores import DjangoJobStore
        from .scheduler import send_cite_reminders

        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), 'default')

        scheduler.add_job(
            send_cite_reminders,
            trigger=CronTrigger(hour=8, minute=0),
            id='send_cite_reminders',
            name='Recordatorios automáticos de citas',
            replace_existing=True,
        )

        scheduler.start()