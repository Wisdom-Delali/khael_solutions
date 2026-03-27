from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        import sys
        # Skip scheduler during management commands that don't need it
        # (migrate, makemigrations, test, shell, collectstatic, etc.)
        _skip_commands = {'migrate', 'makemigrations', 'test', 'shell',
                          'collectstatic', 'check', 'inspectdb', 'showmigrations'}
        if sys.argv and len(sys.argv) > 1 and sys.argv[1] in _skip_commands:
            return
        try:
            from core.scheduler import start_scheduler
            start_scheduler()
        except Exception:
            pass
