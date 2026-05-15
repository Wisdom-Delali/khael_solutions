from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core.models import (
    User, Department, DepartmentMember,
    Job, JobUpdate,
    Resource, ResourceHistory, ResourceUsage, ResourceTemplate,
    Purchase, PurchaseResource,
    Payment,
    Alert,
    Report,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('username', 'get_full_name', 'email', 'role', 'is_active')
    list_filter   = ('role', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets     = BaseUserAdmin.fieldsets + (
        ('Role & Access', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Access', {'fields': ('role',)}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ('name', 'hod', 'created_at')
    search_fields = ('name',)


@admin.register(DepartmentMember)
class DepartmentMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'date_joined')
    list_filter  = ('department',)


class JobUpdateInline(admin.TabularInline):
    model           = JobUpdate
    extra           = 0
    fields          = ('status', 'comment', 'updated_by', 'timestamp')
    readonly_fields = ('timestamp',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display  = ('title', 'department', 'service_type', 'status', 'priority', 'due_date', 'assigned_to')
    list_filter   = ('status', 'priority', 'service_type', 'department')
    search_fields = ('title', 'client_name')
    inlines       = [JobUpdateInline]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'quantity', 'unit', 'unit_cost', 'reorder_level')


@admin.register(ResourceHistory)
class ResourceHistoryAdmin(admin.ModelAdmin):
    list_display = ('resource', 'old_price', 'new_price', 'created_at')


@admin.register(ResourceUsage)
class ResourceUsageAdmin(admin.ModelAdmin):
    list_display = ('resource', 'job', 'quantity', 'unit_cost', 'recorded_at')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('pk', 'purchase_total', 'created_by', 'created_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('job', 'amount', 'payment_date', 'payment_method', 'recorded_by')
    list_filter  = ('payment_method',)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'severity', 'resolved', 'created_at', 'job', 'resource')
    list_filter  = ('alert_type', 'severity', 'resolved')


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'period_start', 'period_end', 'generated_by', 'created_at')


@admin.register(ResourceTemplate)
class ResourceTemplateAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'resource', 'default_quantity')
    list_filter  = ('service_type',)
