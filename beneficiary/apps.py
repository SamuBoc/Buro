from django.apps import AppConfig


class BeneficiaryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'beneficiary'
    verbose_name = 'Gestión de Beneficiarios'

    def ready(self):
        import beneficiary.signals