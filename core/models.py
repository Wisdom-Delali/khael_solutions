"""
core/models.py — all application models in one place.

Models:
  Auth & Users   : User, Department, DepartmentMember
  Jobs           : Job, JobUpdate
  Inventory      : Resource, ResourceHistory, ResourceUsage
  Purchasing     : Purchase, PurchaseResource
  Payments       : Payment
  Alerts         : Alert
  Reporting      : Report
"""
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


# ══════════════════════════════════════════════════════════
# CLIENT MODEL
# ══════════════════════════════════════════════════════════

class Client(models.Model):
    """
    Client database. Phone number is the primary key.
    Clients without phone numbers are stored with a NOPH_<hex> key
    and grouped via no_phone=True in the UI.
    """
    phone      = models.CharField(max_length=50, primary_key=True)
    name       = models.CharField(max_length=200)
    no_phone   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def display_phone(self):
        return '—' if self.no_phone else self.phone

    def __str__(self):
        if self.no_phone:
            return f"{self.name} (No Phone)"
        return f"{self.name} ({self.phone})"

    class Meta:
        ordering = ['name']


# ══════════════════════════════════════════════════════════
# AUTH & USER MODELS
# ══════════════════════════════════════════════════════════

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        MANAGER     = 'manager',     'Manager/Admin'
        STAFF       = 'staff',       'Department Staff'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)

    groups = models.ManyToManyField(
        'auth.Group', related_name='core_user_set', blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', related_name='core_user_set', blank=True,
    )

    def is_super_admin(self):   return self.role == self.Role.SUPER_ADMIN
    def is_manager(self):       return self.role == self.Role.MANAGER
    def is_staff_member(self):  return self.role == self.Role.STAFF

    def get_department(self):
        try:
            return self.department_memberships.department
        except DepartmentMember.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']


class Department(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    hod         = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='headed_departments', verbose_name='Head of Department',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.name

    class Meta:
        ordering = ['name']


class DepartmentMember(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='department_memberships',
    )
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='members',
    )
    date_joined = models.DateField(auto_now_add=True)

    def __str__(self): return f"{self.user.username} → {self.department.name}"

    class Meta:
        ordering = ['department', 'user__username']


# ══════════════════════════════════════════════════════════
# JOB MODELS
# ══════════════════════════════════════════════════════════

class Job(models.Model):
    class Status(models.TextChoices):
        PENDING     = 'pending',     'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED   = 'completed',   'Completed'
        CANCELLED   = 'cancelled',   'Cancelled'
        ON_HOLD     = 'on_hold',     'On Hold / Delayed'

    class Priority(models.TextChoices):
        LOW    = 'low',    'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH   = 'high',   'High'
        URGENT = 'urgent', 'Urgent'

    class ServiceType(models.TextChoices):
        PRINTING   = 'printing',   'Printing Services'
        NETWORK_IT = 'network_it', 'Network & IT'
        MULTIMEDIA = 'multimedia', 'Multimedia Production'
        GENERAL    = 'general',    'General Services'

    department  = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='jobs')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_jobs',
    )
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_jobs',
    )

    # Client info
    client_name    = models.CharField(max_length=200, blank=True)
    client_contact = models.CharField(max_length=100, blank=True)

    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    service_type = models.CharField(
        max_length=20, choices=ServiceType.choices, default=ServiceType.GENERAL,
        help_text='Type of service being provided',
    )
    status   = models.CharField(max_length=20, choices=Status.choices,   default=Status.PENDING)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)

    price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Quoted price / budget (used for expense alerts and payment tracking)',
    )

    start_date   = models.DateField(null=True, blank=True)
    due_date     = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_overdue(self):
        if self.due_date and self.status in [self.Status.PENDING, self.Status.IN_PROGRESS]:
            return timezone.now().date() > self.due_date
        return False

    def total_expenses(self):
        from django.db.models import Sum
        result = self.resource_usages.aggregate(total=Sum(
            models.ExpressionWrapper(
                models.F('quantity') * models.F('unit_cost'),
                output_field=models.DecimalField(),
            )
        ))
        return result['total'] or 0

    def total_paid(self):
        from django.db.models import Sum
        result = self.payments.aggregate(total=Sum('amount'))
        return result['total'] or 0

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title} — {self.department}"

    class Meta:
        ordering = ['-created_at']


class JobType(models.Model):
    """
    Reusable job type / template. Auto-created from job titles; can be
    enriched with defaults so staff pick from a list instead of typing free text.
    """
    title                = models.CharField(max_length=255, unique=True)
    service_type         = models.CharField(
        max_length=20, choices=Job.ServiceType.choices, blank=True,
    )
    default_price        = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    description_template = models.TextField(blank=True)
    created_at           = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.title

    class Meta:
        ordering = ['title']


class JobUpdate(models.Model):
    job        = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    status    = models.CharField(max_length=20, choices=Job.Status.choices)
    comment   = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job #{self.job.pk} → {self.get_status_display()} at {self.timestamp:%Y-%m-%d %H:%M}"

    class Meta:
        ordering = ['-timestamp']


# ══════════════════════════════════════════════════════════
# RESOURCE / INVENTORY MODELS
# ══════════════════════════════════════════════════════════

class Resource(models.Model):
    title        = models.CharField(max_length=200)
    unit         = models.CharField(max_length=50, help_text='e.g. reams, metres, units, litres')
    quantity     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.DecimalField(
        max_digits=10, decimal_places=2, default=10,
        help_text='Alert when quantity falls at or below this level',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_low_stock(self): return self.quantity <= self.reorder_level

    def __str__(self): return f"{self.title} ({self.quantity} {self.unit})"

    class Meta:
        ordering = ['title']


class ResourceHistory(models.Model):
    resource  = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='price_history')
    purchase  = models.ForeignKey(
        'Purchase', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='price_changes',
    )
    old_price  = models.DecimalField(max_digits=10, decimal_places=2)
    new_price  = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.resource.title}: {self.old_price} → {self.new_price}"

    class Meta:
        ordering = ['-created_at']


class ResourceUsage(models.Model):
    job      = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='resource_usages')
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT, related_name='usages')
    quantity  = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Cost per unit at time of usage (snapshot)',
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    def line_total(self): return self.quantity * self.unit_cost

    def __str__(self):
        return f"{self.resource.title} × {self.quantity} for Job #{self.job.pk}"

    class Meta:
        ordering = ['-recorded_at']


# ══════════════════════════════════════════════════════════
# RESOURCE TEMPLATE MODEL
# ══════════════════════════════════════════════════════════

class ResourceTemplate(models.Model):
    """
    Default resources to suggest when a job of a given service type is opened.
    Managers configure these in admin; suggestions appear on the job detail page.
    """
    service_type     = models.CharField(max_length=20, choices=Job.ServiceType.choices)
    resource         = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='templates')
    default_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    class Meta:
        unique_together = [('service_type', 'resource')]
        ordering = ['service_type', 'resource__title']

    def __str__(self):
        return f"{self.get_service_type_display()} → {self.resource.title} × {self.default_quantity}"


# ══════════════════════════════════════════════════════════
# PURCHASE MODELS
# ══════════════════════════════════════════════════════════

class Purchase(models.Model):
    purchase_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='purchases',
    )
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase #{self.pk} — GHS {self.purchase_total} on {self.created_at:%Y-%m-%d}"

    class Meta:
        ordering = ['-created_at']


class PurchaseResource(models.Model):
    purchase  = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    resource  = models.ForeignKey(Resource, on_delete=models.PROTECT, related_name='purchase_items')
    quantity  = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def line_total(self): return self.quantity * self.unit_cost

    def __str__(self):
        return f"{self.resource.title} × {self.quantity} @ {self.unit_cost}"


# ══════════════════════════════════════════════════════════
# PAYMENT MODEL
# ══════════════════════════════════════════════════════════

class Payment(models.Model):
    class Method(models.TextChoices):
        CASH          = 'cash',          'Cash'
        MOBILE_MONEY  = 'mobile_money',  'Mobile Money'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        CHEQUE        = 'cheque',        'Cheque'

    job            = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='payments')
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date   = models.DateField()
    payment_method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    reference      = models.CharField(max_length=100, blank=True, help_text='Receipt or transaction number')
    recorded_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment GHS {self.amount} for Job #{self.job.pk} on {self.payment_date}"

    class Meta:
        ordering = ['-payment_date']


# ══════════════════════════════════════════════════════════
# RECEIPT MODEL
# ══════════════════════════════════════════════════════════

class Receipt(models.Model):
    """Auto-created when a Payment is recorded. UUID is used for the public link."""
    uuid       = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    payment    = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt {str(self.uuid)[:8].upper()} — Job #{self.payment.job.pk}"

    class Meta:
        ordering = ['-created_at']


# ══════════════════════════════════════════════════════════
# ALERT MODEL
# ══════════════════════════════════════════════════════════

class Alert(models.Model):
    class AlertType(models.TextChoices):
        OVERDUE_JOB          = 'overdue_job',          'Overdue Job'
        ABNORMAL_EXPENSE     = 'abnormal_expense',     'Abnormal Expense'
        SCHEDULING_CONFLICT  = 'scheduling_conflict',  'Scheduling Conflict'
        OVERDUE_PAYMENT      = 'overdue_payment',      'Overdue Payment'
        LOW_STOCK            = 'low_stock',            'Low Stock / Reorder Required'

    class Severity(models.TextChoices):
        INFO     = 'info',     'Info'
        WARNING  = 'warning',  'Warning'
        CRITICAL = 'critical', 'Critical'

    job      = models.ForeignKey(Job,      on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')

    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    severity   = models.CharField(max_length=10, choices=Severity.choices, default=Severity.WARNING)
    message    = models.TextField()

    resolved    = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resolved_alerts',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def resolve(self, user):
        self.resolved    = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.get_alert_type_display()} — {self.created_at:%Y-%m-%d}"

    class Meta:
        ordering = ['-created_at']


# ══════════════════════════════════════════════════════════
# REPORT MODEL
# ══════════════════════════════════════════════════════════

class Report(models.Model):
    class ReportType(models.TextChoices):
        WEEKLY       = 'weekly',       'Weekly Summary'
        ON_DEMAND    = 'on_demand',    'On-Demand Report'
        CUSTOM_QUERY = 'custom_query', 'Custom Query'

    period_start  = models.DateField()
    period_end    = models.DateField()
    generated_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='generated_reports',
        help_text='Null if auto-generated by scheduler',
    )
    report_type       = models.CharField(max_length=20, choices=ReportType.choices, default=ReportType.ON_DEMAND)
    query_text        = models.TextField(blank=True, help_text='User-entered natural language query (custom queries only)')
    summary_text      = models.TextField(help_text='AI-generated narrative summary from OpenAI')
    raw_data_snapshot = models.JSONField(default=dict, help_text='Operational stats sent to OpenAI')
    created_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_report_type_display()} — {self.period_start} to {self.period_end}"

    class Meta:
        ordering = ['-created_at']
