"""
core/context_processors.py
Injects global context variables available in every template.
"""


def global_context(request):
    """Provides alert_count to all templates so the sidebar badge always works."""
    if not request.user.is_authenticated:
        return {}
    from core.models import Alert
    return {
        'alert_count': Alert.objects.filter(resolved=False).count(),
    }
