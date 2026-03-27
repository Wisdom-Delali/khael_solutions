from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        try:
            from core.scheduler import start_scheduler
            start_scheduler()
        except Exception:
            pass  # Scheduler may not be available during migrations or tests
