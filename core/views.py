"""
core/views.py — all application views in one place.

Sections:
  1. Auth & User Management
  2. Dashboard
  3. Job Views
  4. Resource Views
  5. Purchase Views
  6. Alert Views
  7. Payment Views
  8. Report Views
"""
from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from core.models import (
    User, Department, DepartmentMember,
    Job, Resource, Purchase, Alert, Payment, Report,
)
from core.permissions import ManagerRequiredMixin, StaffRequiredMixin
from core.services import (
    # Job
    get_jobs_for_user, create_job, update_job_status, edit_job, get_job_timeline,
    # Resource
    get_resource_list, get_low_stock_resources, record_resource_usage,
    get_job_usage_summary, create_purchase,
    # Alert
    run_all_checks,
    # Payment / alert hooks
    check_overdue_payment_alert,
    # Report
    generate_report,
)


# ══════════════════════════════════════════════════════════
# 1. AUTH & USER MANAGEMENT
# ══════════════════════════════════════════════════════════

class LoginView(View):
    template_name = 'login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'core:dashboard'))
        messages.error(request, 'Invalid username or password.')
        return render(request, self.template_name, {'username': username})


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('core:login')


class UserListView(ManagerRequiredMixin, View):
    template_name = 'users/user_list.html'

    def get(self, request):
        return render(request, self.template_name, {
            'users':       User.objects.all().prefetch_related('department_memberships__department'),
            'departments': Department.objects.all(),
        })


class UserCreateView(ManagerRequiredMixin, View):
    template_name = 'users/user_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'departments': Department.objects.all(),
            'roles':       User.Role.choices,
            'action':      'Create',
        })

    def post(self, request):
        username = request.POST.get('username', '').strip()
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('core:user_create')

        user = User.objects.create_user(
            username=username,
            first_name=request.POST.get('first_name', '').strip(),
            last_name=request.POST.get('last_name',  '').strip(),
            email=request.POST.get('email', '').strip(),
            password=request.POST.get('password', ''),
            role=request.POST.get('role', User.Role.STAFF),
        )
        dept_id = request.POST.get('department')
        if dept_id:
            DepartmentMember.objects.create(
                user=user, department=get_object_or_404(Department, pk=dept_id)
            )
        messages.success(request, f'User "{username}" created successfully.')
        return redirect('core:user_list')


class UserEditView(ManagerRequiredMixin, View):
    template_name = 'users/user_form.html'

    def get(self, request, pk):
        edit_user = get_object_or_404(User, pk=pk)
        return render(request, self.template_name, {
            'edit_user':   edit_user,
            'departments': Department.objects.all(),
            'roles':       User.Role.choices,
            'current_dept': edit_user.get_department(),
            'action':      'Edit',
        })

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name  = request.POST.get('last_name',  '').strip()
        user.email      = request.POST.get('email',      '').strip()
        user.role       = request.POST.get('role', user.role)
        new_pw = request.POST.get('password', '').strip()
        if new_pw:
            user.set_password(new_pw)
        user.save()

        dept_id = request.POST.get('department')
        if dept_id:
            DepartmentMember.objects.update_or_create(
                user=user,
                defaults={'department': get_object_or_404(Department, pk=dept_id)},
            )
        messages.success(request, f'User "{user.username}" updated successfully.')
        return redirect('core:user_list')


class UserDeactivateView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect('core:user_list')
        user.is_active = not user.is_active
        user.save()
        messages.success(request, f'User "{user.username}" {"activated" if user.is_active else "deactivated"}.')
        return redirect('core:user_list')


class DepartmentListView(ManagerRequiredMixin, View):
    template_name = 'departments/department_list.html'

    def get(self, request):
        return render(request, self.template_name, {
            'departments': Department.objects.prefetch_related('members__user').select_related('hod'),
        })


class DepartmentCreateView(ManagerRequiredMixin, View):
    template_name = 'departments/department_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'managers': User.objects.filter(role__in=['manager', 'super_admin']),
            'action':   'Create',
        })

    def post(self, request):
        name = request.POST.get('name', '').strip()
        if Department.objects.filter(name=name).exists():
            messages.error(request, 'A department with this name already exists.')
            return redirect('core:department_create')
        hod_id = request.POST.get('hod')
        Department.objects.create(
            name=name,
            description=request.POST.get('description', '').strip(),
            hod=get_object_or_404(User, pk=hod_id) if hod_id else None,
        )
        messages.success(request, f'Department "{name}" created.')
        return redirect('core:department_list')


class DepartmentEditView(ManagerRequiredMixin, View):
    template_name = 'departments/department_form.html'

    def get(self, request, pk):
        dept = get_object_or_404(Department, pk=pk)
        return render(request, self.template_name, {
            'dept':     dept,
            'managers': User.objects.filter(role__in=['manager', 'super_admin']),
            'action':   'Edit',
        })

    def post(self, request, pk):
        dept = get_object_or_404(Department, pk=pk)
        dept.name        = request.POST.get('name', dept.name).strip()
        dept.description = request.POST.get('description', dept.description).strip()
        hod_id           = request.POST.get('hod')
        dept.hod         = get_object_or_404(User, pk=hod_id) if hod_id else None
        dept.save()
        messages.success(request, f'Department "{dept.name}" updated.')
        return redirect('core:department_list')


# ══════════════════════════════════════════════════════════
# 2. DASHBOARD
# ══════════════════════════════════════════════════════════

@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    template_name = 'dashboard.html'

    def get(self, request):
        user = request.user
        now  = timezone.now()

        if user.role in ['super_admin', 'manager']:
            all_jobs = Job.objects.all()
        else:
            dept = user.get_department()
            all_jobs = Job.objects.filter(department=dept) if dept else Job.objects.none()

        low_stock = []
        if user.role in ['super_admin', 'manager']:
            low_stock = Resource.objects.filter(quantity__lte=models_reorder_level())[:5]

        return render(request, self.template_name, {
            'total_jobs':       all_jobs.count(),
            'pending_jobs':     all_jobs.filter(status=Job.Status.PENDING).count(),
            'in_progress_jobs': all_jobs.filter(status=Job.Status.IN_PROGRESS).count(),
            'completed_jobs':   all_jobs.filter(status=Job.Status.COMPLETED).count(),
            'overdue_jobs':     all_jobs.filter(
                due_date__lt=now.date(),
                status__in=[Job.Status.PENDING, Job.Status.IN_PROGRESS]
            ).count(),
            'unresolved_alerts':   Alert.objects.filter(resolved=False).order_by('-created_at')[:5],
            'low_stock_resources': low_stock,
            'recent_jobs':         all_jobs.select_related('department', 'assigned_to').order_by('-created_at')[:8],
            'now': now,
        })


def models_reorder_level():
    from django.db.models import F
    return F('reorder_level')


# ══════════════════════════════════════════════════════════
# 3. JOB VIEWS
# ══════════════════════════════════════════════════════════

@method_decorator(login_required, name='dispatch')
class JobListView(View):
    template_name = 'jobs/job_list.html'

    def get(self, request):
        jobs            = get_jobs_for_user(request.user)
        status_filter   = request.GET.get('status')
        priority_filter = request.GET.get('priority')
        dept_filter     = request.GET.get('department')
        stype_filter    = request.GET.get('service_type')

        if status_filter:   jobs = jobs.filter(status=status_filter)
        if priority_filter: jobs = jobs.filter(priority=priority_filter)
        if stype_filter:    jobs = jobs.filter(service_type=stype_filter)
        if dept_filter and request.user.role in ['super_admin', 'manager']:
            jobs = jobs.filter(department_id=dept_filter)

        return render(request, self.template_name, {
            'jobs':             jobs,
            'departments':      Department.objects.all(),
            'status_choices':   Job.Status.choices,
            'priority_choices': Job.Priority.choices,
            'service_type_choices': Job.ServiceType.choices,
            'selected_status':       status_filter,
            'selected_priority':     priority_filter,
            'selected_dept':         dept_filter,
            'selected_service_type': stype_filter,
        })


@method_decorator(login_required, name='dispatch')
class JobCreateView(View):
    template_name = 'jobs/job_form.html'

    def _get_departments(self, user):
        if user.role in ['super_admin', 'manager']:
            return Department.objects.all()
        dept = user.get_department()
        return Department.objects.filter(pk=dept.pk) if dept else Department.objects.none()

    def get(self, request):
        return render(request, self.template_name, {
            'departments':          self._get_departments(request.user),
            'staff_users':          User.objects.filter(role=User.Role.STAFF, is_active=True),
            'priority_choices':     Job.Priority.choices,
            'service_type_choices': Job.ServiceType.choices,
            'action': 'Create',
        })

    def post(self, request):
        try:
            dept         = get_object_or_404(Department, pk=request.POST.get('department'))
            assigned_id  = request.POST.get('assigned_to')
            assigned_to  = get_object_or_404(User, pk=assigned_id) if assigned_id else None

            job = create_job(
                title=request.POST.get('title', '').strip(),
                department=dept,
                created_by=request.user,
                description=request.POST.get('description', '').strip(),
                assigned_to=assigned_to,
                client_name=request.POST.get('client_name', '').strip(),
                client_contact=request.POST.get('client_contact', '').strip(),
                priority=request.POST.get('priority', Job.Priority.MEDIUM),
                service_type=request.POST.get('service_type', Job.ServiceType.GENERAL),
                price=request.POST.get('price') or None,
                start_date=request.POST.get('start_date') or None,
                due_date=request.POST.get('due_date') or None,
            )
            messages.success(request, f'Job "{job.title}" created successfully.')
            return redirect('core:job_detail', pk=job.pk)
        except Exception as e:
            messages.error(request, f'Error creating job: {e}')
            return redirect('core:job_create')


@method_decorator(login_required, name='dispatch')
class JobDetailView(View):
    template_name = 'jobs/job_detail.html'

    def get(self, request, pk):
        job             = get_object_or_404(get_jobs_for_user(request.user), pk=pk)
        timeline        = get_job_timeline(job)
        usages, total   = get_job_usage_summary(job)
        payments        = job.payments.select_related('recorded_by').order_by('-payment_date')
        return render(request, self.template_name, {
            'job':            job,
            'timeline':       timeline,
            'usages':         usages,
            'usage_total':    total,
            'alerts':         job.alerts.all(),
            'payments':       payments,
            'total_paid':     job.total_paid(),
            'status_choices': Job.Status.choices,
        })


@method_decorator(login_required, name='dispatch')
class JobEditView(View):
    template_name = 'jobs/job_form.html'

    def get(self, request, pk):
        job = get_object_or_404(get_jobs_for_user(request.user), pk=pk)
        return render(request, self.template_name, {
            'job':                  job,
            'departments':          Department.objects.all(),
            'staff_users':          User.objects.filter(role=User.Role.STAFF, is_active=True),
            'priority_choices':     Job.Priority.choices,
            'service_type_choices': Job.ServiceType.choices,
            'action': 'Edit',
        })

    def post(self, request, pk):
        job = get_object_or_404(get_jobs_for_user(request.user), pk=pk)
        try:
            assigned_id = request.POST.get('assigned_to')
            assigned_to = get_object_or_404(User, pk=assigned_id) if assigned_id else None
            edit_job(
                job=job, updated_by=request.user,
                title=request.POST.get('title', job.title).strip(),
                description=request.POST.get('description', job.description).strip(),
                client_name=request.POST.get('client_name', job.client_name).strip(),
                client_contact=request.POST.get('client_contact', job.client_contact).strip(),
                priority=request.POST.get('priority', job.priority),
                service_type=request.POST.get('service_type', job.service_type),
                price=request.POST.get('price') or None,
                start_date=request.POST.get('start_date') or None,
                due_date=request.POST.get('due_date') or None,
                assigned_to=assigned_to,
            )
            messages.success(request, 'Job updated successfully.')
            return redirect('core:job_detail', pk=job.pk)
        except Exception as e:
            messages.error(request, f'Error updating job: {e}')
            return redirect('core:job_edit', pk=pk)


@method_decorator(login_required, name='dispatch')
class JobStatusUpdateView(View):
    def post(self, request, pk):
        job        = get_object_or_404(get_jobs_for_user(request.user), pk=pk)
        new_status = request.POST.get('status')
        if new_status not in [s[0] for s in Job.Status.choices]:
            messages.error(request, 'Invalid status.')
            return redirect('core:job_detail', pk=pk)
        update_job_status(job, new_status, request.user, request.POST.get('comment', '').strip())
        messages.success(request, f'Job status updated to "{job.get_status_display()}".')
        return redirect('core:job_detail', pk=pk)


# ══════════════════════════════════════════════════════════
# 4. RESOURCE VIEWS
# ══════════════════════════════════════════════════════════

@method_decorator(login_required, name='dispatch')
class ResourceListView(View):
    template_name = 'resources/resource_list.html'

    def get(self, request):
        resources = get_resource_list()
        low_stock = get_low_stock_resources()
        return render(request, self.template_name, {
            'resources':    resources,
            'low_stock_ids': set(low_stock.values_list('pk', flat=True)),
        })


class ResourceCreateView(ManagerRequiredMixin, View):
    template_name = 'resources/resource_form.html'

    def get(self, request):
        return render(request, self.template_name, {'action': 'Create'})

    def post(self, request):
        try:
            Resource.objects.create(
                title=request.POST.get('title', '').strip(),
                unit=request.POST.get('unit', '').strip(),
                quantity=request.POST.get('quantity', 0),
                unit_cost=request.POST.get('unit_cost', 0),
                reorder_level=request.POST.get('reorder_level', 10),
            )
            messages.success(request, 'Resource created successfully.')
            return redirect('core:resource_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
            return redirect('core:resource_create')


class ResourceEditView(ManagerRequiredMixin, View):
    template_name = 'resources/resource_form.html'

    def get(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        return render(request, self.template_name, {'resource': resource, 'action': 'Edit'})

    def post(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        resource.title        = request.POST.get('title', resource.title).strip()
        resource.unit         = request.POST.get('unit',  resource.unit).strip()
        resource.reorder_level = request.POST.get('reorder_level', resource.reorder_level)
        resource.save()
        messages.success(request, 'Resource updated.')
        return redirect('core:resource_list')


@method_decorator(login_required, name='dispatch')
class ResourceDetailView(View):
    template_name = 'resources/resource_detail.html'

    def get(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        return render(request, self.template_name, {
            'resource':     resource,
            'price_history': resource.price_history.select_related('purchase').order_by('-created_at'),
            'usages':        resource.usages.select_related('job', 'recorded_by').order_by('-recorded_at'),
        })


@method_decorator(login_required, name='dispatch')
class RecordResourceUsageView(View):
    template_name = 'resources/record_usage.html'

    def get(self, request, job_pk):
        job = get_object_or_404(get_jobs_for_user(request.user), pk=job_pk)
        return render(request, self.template_name, {
            'job': job, 'resources': get_resource_list(),
        })

    def post(self, request, job_pk):
        job = get_object_or_404(get_jobs_for_user(request.user), pk=job_pk)
        try:
            resource = get_object_or_404(Resource, pk=request.POST.get('resource'))
            record_resource_usage(
                job=job, resource=resource,
                quantity=request.POST.get('quantity'),
                recorded_by=request.user,
            )
            messages.success(request, f'Usage of "{resource.title}" recorded.')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('core:job_detail', pk=job.pk)


# ══════════════════════════════════════════════════════════
# 5. PURCHASE VIEWS
# ══════════════════════════════════════════════════════════

class PurchaseListView(ManagerRequiredMixin, View):
    template_name = 'purchases/purchase_list.html'

    def get(self, request):
        return render(request, self.template_name, {
            'purchases': Purchase.objects.prefetch_related('items__resource').order_by('-created_at'),
        })


class PurchaseCreateView(ManagerRequiredMixin, View):
    template_name = 'purchases/purchase_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'resources': Resource.objects.all().order_by('title'),
        })

    def post(self, request):
        resource_ids = request.POST.getlist('resource[]')
        quantities   = request.POST.getlist('quantity[]')
        unit_costs   = request.POST.getlist('unit_cost[]')
        notes        = request.POST.get('notes', '').strip()

        if not resource_ids:
            messages.error(request, 'Please add at least one item.')
            return redirect('core:purchase_create')

        items = []
        try:
            for rid, qty, uc in zip(resource_ids, quantities, unit_costs):
                items.append({
                    'resource':  get_object_or_404(Resource, pk=rid),
                    'quantity':  Decimal(qty),
                    'unit_cost': Decimal(uc),
                })
        except Exception as e:
            messages.error(request, f'Invalid input: {e}')
            return redirect('core:purchase_create')

        purchase = create_purchase(created_by=request.user, items=items, notes=notes)
        messages.success(request, f'Purchase #{purchase.pk} recorded. Stock updated.')
        return redirect('core:purchase_list')


class PurchaseDetailView(ManagerRequiredMixin, View):
    template_name = 'purchases/purchase_detail.html'

    def get(self, request, pk):
        purchase = get_object_or_404(
            Purchase.objects.prefetch_related('items__resource', 'price_changes__resource'), pk=pk
        )
        return render(request, self.template_name, {'purchase': purchase})


# ══════════════════════════════════════════════════════════
# 6. ALERT VIEWS
# ══════════════════════════════════════════════════════════

@method_decorator(login_required, name='dispatch')
class AlertListView(View):
    template_name = 'alerts/alert_list.html'

    def get(self, request):
        alerts           = Alert.objects.select_related('job__department', 'resource', 'resolved_by').order_by('resolved', '-created_at')
        resolved_filter  = request.GET.get('resolved', '')
        type_filter      = request.GET.get('type', '')
        severity_filter  = request.GET.get('severity', '')

        if resolved_filter == 'true':  alerts = alerts.filter(resolved=True)
        elif resolved_filter == 'false': alerts = alerts.filter(resolved=False)
        if type_filter:     alerts = alerts.filter(alert_type=type_filter)
        if severity_filter: alerts = alerts.filter(severity=severity_filter)

        return render(request, self.template_name, {
            'alerts':           alerts,
            'alert_types':      Alert.AlertType.choices,
            'severity_choices': Alert.Severity.choices,
            'unresolved_count': Alert.objects.filter(resolved=False).count(),
            'selected_resolved': resolved_filter,
            'selected_type':     type_filter,
            'selected_severity': severity_filter,
        })


class AlertResolveView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk)
        if alert.resolved:
            messages.info(request, 'Alert already resolved.')
        else:
            alert.resolve(request.user)
            messages.success(request, 'Alert marked as resolved.')
        return redirect('core:alert_list')


class RunAlertChecksView(ManagerRequiredMixin, View):
    def get(self, request):
        run_all_checks()
        messages.success(request, 'Alert checks completed.')
        return redirect('core:alert_list')

    def post(self, request):
        run_all_checks()
        messages.success(request, 'Alert checks completed.')
        return redirect('core:alert_list')


# ══════════════════════════════════════════════════════════
# 7. PAYMENT VIEWS
# ══════════════════════════════════════════════════════════

class PaymentCreateView(ManagerRequiredMixin, View):
    template_name = 'payments/payment_form.html'

    def get(self, request, job_pk):
        job = get_object_or_404(Job, pk=job_pk)
        return render(request, self.template_name, {
            'job':            job,
            'method_choices': Payment.Method.choices,
            'today':          timezone.now().date(),
            'total_paid':     job.total_paid(),
        })

    def post(self, request, job_pk):
        job = get_object_or_404(Job, pk=job_pk)
        try:
            Payment.objects.create(
                job=job,
                amount=Decimal(request.POST.get('amount')),
                payment_date=request.POST.get('payment_date'),
                payment_method=request.POST.get('payment_method', Payment.Method.CASH),
                reference=request.POST.get('reference', '').strip(),
                notes=request.POST.get('notes', '').strip(),
                recorded_by=request.user,
            )
            check_overdue_payment_alert(job)
            messages.success(request, f'Payment recorded for job "{job.title}".')
        except Exception as e:
            messages.error(request, f'Error recording payment: {e}')
        return redirect('core:job_detail', pk=job.pk)


# ══════════════════════════════════════════════════════════
# 8. REPORT VIEWS
# ══════════════════════════════════════════════════════════

class ReportListView(ManagerRequiredMixin, View):
    template_name = 'reports/report_list.html'

    def get(self, request):
        return render(request, self.template_name, {
            'reports': Report.objects.select_related('generated_by').order_by('-created_at'),
        })


class ReportDetailView(ManagerRequiredMixin, View):
    template_name = 'reports/report_detail.html'

    def get(self, request, pk):
        return render(request, self.template_name, {
            'report': get_object_or_404(Report, pk=pk),
        })


class GenerateReportView(ManagerRequiredMixin, View):
    template_name = 'reports/generate_report.html'

    def get(self, request):
        today = timezone.now().date()
        return render(request, self.template_name, {
            'default_start': today - timedelta(days=7),
            'default_end':   today,
        })

    def post(self, request):
        try:
            period_start = date.fromisoformat(request.POST.get('period_start'))
            period_end   = date.fromisoformat(request.POST.get('period_end'))
            if period_start > period_end:
                messages.error(request, 'Start date must be before end date.')
                return redirect('core:generate_report')

            messages.info(request, 'Generating AI report… this may take a few seconds.')
            report = generate_report(
                period_start=period_start, period_end=period_end,
                generated_by=request.user, report_type=Report.ReportType.ON_DEMAND,
            )
            messages.success(request, f'Report generated for {period_start} to {period_end}.')
            return redirect('core:report_detail', pk=report.pk)
        except Exception as e:
            messages.error(request, f'Report generation failed: {e}')
            return redirect('core:generate_report')
