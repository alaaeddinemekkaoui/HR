from django.apps import AppConfig


class LeavesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.leaves'
    verbose_name = 'Leaves'

    def ready(self):
        # Import signals to register them
        import apps.leaves.signals
