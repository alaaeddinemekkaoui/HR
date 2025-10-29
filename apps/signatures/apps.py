from django.apps import AppConfig


class SignaturesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.signatures'
    verbose_name = 'Electronic Signatures'

    def ready(self):
        import apps.signatures.signals
