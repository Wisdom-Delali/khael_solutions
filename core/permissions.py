"""
core/permissions.py
Reusable permission mixins and decorators for role-based access control.
Usage:
    class MyView(SuperAdminOrManagerRequiredMixin, View): ...
    
    @role_required('super_admin', 'manager')
    def my_view(request): ...
"""
from functools import wraps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


# ─────────────────────────────────────────────
# Class-Based View Mixins
# ─────────────────────────────────────────────

class RoleRequiredMixin(LoginRequiredMixin):
    """Base mixin — subclasses define allowed_roles."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['super_admin']


class ManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['super_admin', 'manager']


class StaffRequiredMixin(LoginRequiredMixin):
    """All authenticated users (any role) can access."""
    pass


class SuperAdminOrManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['super_admin', 'manager']


# ─────────────────────────────────────────────
# Function-Based View Decorators
# ─────────────────────────────────────────────

def role_required(*roles):
    """
    Decorator for function-based views.
    Usage: @role_required('manager', 'super_admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login')
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def staff_or_manager_required(view_func):
    """Allow any authenticated user."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        return view_func(request, *args, **kwargs)
    return wrapper