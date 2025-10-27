from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.employees'
    label = 'employees'
    
    def ready(self):
        # Import signal handlers to register them
        try:
            import apps.employees.signals  # noqa: F401
        except Exception:
            # Avoid raising at import time; if signals fail to import, log in future
            pass
