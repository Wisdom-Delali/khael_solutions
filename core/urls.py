"""
core/urls.py — all URL patterns under the 'core' namespace.
"""
from django.urls import path
from core.views import (
    # Auth
    LoginView, LogoutView,
    # Users
    UserListView, UserCreateView, UserEditView, UserDeactivateView,
    # Departments
    DepartmentListView, DepartmentCreateView, DepartmentEditView,
    # Dashboard
    DashboardView,
    # Jobs
    JobListView, JobCreateView, JobDetailView, JobEditView,
    JobStatusUpdateView, RecordResourceUsageView,
    # Resources
    ResourceListView, ResourceCreateView, ResourceEditView, ResourceDetailView,
    # Purchases
    PurchaseListView, PurchaseCreateView, PurchaseDetailView,
    # Alerts
    AlertListView, AlertResolveView, RunAlertChecksView,
    # Payments
    PaymentCreateView,
    # Reports
    ReportListView, ReportDetailView, GenerateReportView,
)

app_name = 'core'

urlpatterns = [
    # ── Auth ──────────────────────────────────────────
    path('auth/login/',  LoginView.as_view(),  name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # ── Dashboard ─────────────────────────────────────
    path('',          DashboardView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # ── Users ─────────────────────────────────────────
    path('users/',                      UserListView.as_view(),       name='user_list'),
    path('users/create/',               UserCreateView.as_view(),     name='user_create'),
    path('users/<int:pk>/edit/',        UserEditView.as_view(),       name='user_edit'),
    path('users/<int:pk>/toggle-active/', UserDeactivateView.as_view(), name='user_toggle_active'),

    # ── Departments ───────────────────────────────────
    path('departments/',                  DepartmentListView.as_view(),   name='department_list'),
    path('departments/create/',           DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/',    DepartmentEditView.as_view(),   name='department_edit'),

    # ── Jobs ──────────────────────────────────────────
    path('jobs/',                           JobListView.as_view(),         name='job_list'),
    path('jobs/create/',                    JobCreateView.as_view(),       name='job_create'),
    path('jobs/<int:pk>/',                  JobDetailView.as_view(),       name='job_detail'),
    path('jobs/<int:pk>/edit/',             JobEditView.as_view(),         name='job_edit'),
    path('jobs/<int:pk>/status/',           JobStatusUpdateView.as_view(), name='job_status_update'),
    path('jobs/<int:job_pk>/record-usage/', RecordResourceUsageView.as_view(), name='record_usage'),
    path('jobs/<int:job_pk>/payment/',      PaymentCreateView.as_view(),   name='payment_create'),

    # ── Resources ─────────────────────────────────────
    path('resources/',               ResourceListView.as_view(),   name='resource_list'),
    path('resources/create/',        ResourceCreateView.as_view(), name='resource_create'),
    path('resources/<int:pk>/',      ResourceDetailView.as_view(), name='resource_detail'),
    path('resources/<int:pk>/edit/', ResourceEditView.as_view(),   name='resource_edit'),

    # ── Purchases ─────────────────────────────────────
    path('purchases/',           PurchaseListView.as_view(),   name='purchase_list'),
    path('purchases/create/',    PurchaseCreateView.as_view(), name='purchase_create'),
    path('purchases/<int:pk>/',  PurchaseDetailView.as_view(), name='purchase_detail'),

    # ── Alerts ────────────────────────────────────────
    path('alerts/',                  AlertListView.as_view(),    name='alert_list'),
    path('alerts/<int:pk>/resolve/', AlertResolveView.as_view(), name='alert_resolve'),
    path('alerts/run-checks/',       RunAlertChecksView.as_view(), name='run_checks'),

    # ── Reports ───────────────────────────────────────
    path('reports/',              ReportListView.as_view(),    name='report_list'),
    path('reports/generate/',     GenerateReportView.as_view(), name='generate_report'),
    path('reports/<int:pk>/',     ReportDetailView.as_view(),  name='report_detail'),
]
