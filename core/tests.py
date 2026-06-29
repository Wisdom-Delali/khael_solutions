"""
core/tests.py — Unit and integration tests for Khael Solutions.

Coverage:
  - Models        : User, Department, Job, Resource, Payment, Alert
  - Services      : create_job, update_job_status, record_resource_usage,
                    create_purchase, alert checks, run_all_checks
  - Views (HTTP)  : login, dashboard, job CRUD, resource CRUD, payment,
                    alert list/resolve, user management, department management
"""
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.utils import timezone

from core.models import (
    User, Department, DepartmentMember,
    Job, JobUpdate,
    Resource, ResourceUsage, ResourceHistory,
    Purchase, PurchaseResource,
    Payment,
    Alert,
)
from core import services
from core.views import JobsReportView


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def make_user(username='testuser', role=User.Role.MANAGER, password='pass1234'):
    return User.objects.create_user(username=username, password=password, role=role)


def make_department(name='Test Dept', hod=None):
    return Department.objects.create(name=name, hod=hod)


def make_resource(title='Paper', quantity=100, unit_cost=5, reorder_level=10):
    return Resource.objects.create(
        title=title, unit='reams',
        quantity=Decimal(str(quantity)),
        unit_cost=Decimal(str(unit_cost)),
        reorder_level=Decimal(str(reorder_level)),
    )


def make_job(dept, user, title='Test Job', status=Job.Status.PENDING, due_date=None, price=None):
    return Job.objects.create(
        title=title, department=dept, created_by=user,
        status=status, priority=Job.Priority.MEDIUM,
        service_type=Job.ServiceType.GENERAL,
        due_date=due_date, price=price,
    )


# ══════════════════════════════════════════════════════════
# MODEL TESTS
# ══════════════════════════════════════════════════════════

class UserModelTest(TestCase):

    def test_role_helpers(self):
        admin = make_user('admin', User.Role.SUPER_ADMIN)
        mgr   = make_user('mgr',   User.Role.MANAGER)
        staff = make_user('staff', User.Role.STAFF)

        self.assertTrue(admin.is_super_admin())
        self.assertFalse(admin.is_manager())

        self.assertTrue(mgr.is_manager())
        self.assertFalse(mgr.is_super_admin())

        self.assertTrue(staff.is_staff_member())
        self.assertFalse(staff.is_manager())

    def test_str(self):
        u = make_user('alice', User.Role.STAFF)
        self.assertIn('alice', str(u))

    def test_get_department_no_membership(self):
        u = make_user('bob')
        self.assertIsNone(u.get_department())

    def test_get_department_with_membership(self):
        u    = make_user('carol')
        dept = make_department('IT')
        DepartmentMember.objects.create(user=u, department=dept)
        self.assertEqual(u.get_department(), dept)


class DepartmentModelTest(TestCase):

    def test_str(self):
        dept = make_department('Printing')
        self.assertEqual(str(dept), 'Printing')

    def test_hod_assignment(self):
        mgr  = make_user('mgr')
        dept = make_department('Network', hod=mgr)
        self.assertEqual(dept.hod, mgr)


class JobModelTest(TestCase):

    def setUp(self):
        self.user = make_user('u1')
        self.dept = make_department()

    def test_is_overdue_false_when_no_due_date(self):
        job = make_job(self.dept, self.user)
        self.assertFalse(job.is_overdue())

    def test_is_overdue_true_when_past_due(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        job = make_job(self.dept, self.user, due_date=yesterday)
        self.assertTrue(job.is_overdue())

    def test_is_overdue_false_when_completed(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        job = make_job(self.dept, self.user, due_date=yesterday, status=Job.Status.COMPLETED)
        self.assertFalse(job.is_overdue())

    def test_total_paid_zero_with_no_payments(self):
        job = make_job(self.dept, self.user)
        self.assertEqual(job.total_paid(), 0)

    def test_total_paid_sums_payments(self):
        job = make_job(self.dept, self.user)
        Payment.objects.create(
            job=job, amount=Decimal('100.00'),
            payment_date=date.today(), payment_method=Payment.Method.CASH,
        )
        Payment.objects.create(
            job=job, amount=Decimal('50.00'),
            payment_date=date.today(), payment_method=Payment.Method.MOBILE_MONEY,
        )
        self.assertEqual(job.total_paid(), Decimal('150.00'))

    def test_total_expenses_zero_no_usage(self):
        job = make_job(self.dept, self.user)
        self.assertEqual(job.total_expenses(), 0)

    def test_str_contains_title(self):
        job = make_job(self.dept, self.user, title='Big Print Job')
        self.assertIn('Big Print Job', str(job))


class ResourceModelTest(TestCase):

    def test_is_low_stock_true(self):
        r = make_resource(quantity=5, reorder_level=10)
        self.assertTrue(r.is_low_stock())

    def test_is_low_stock_false(self):
        r = make_resource(quantity=50, reorder_level=10)
        self.assertFalse(r.is_low_stock())

    def test_is_low_stock_at_boundary(self):
        r = make_resource(quantity=10, reorder_level=10)
        self.assertTrue(r.is_low_stock())  # quantity <= reorder_level

    def test_str(self):
        r = make_resource('Paper', 50)
        self.assertIn('Paper', str(r))


class PaymentModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.dept = make_department()
        self.job  = make_job(self.dept, self.user)

    def test_str(self):
        p = Payment.objects.create(
            job=self.job, amount=Decimal('200.00'),
            payment_date=date.today(), payment_method=Payment.Method.CASH,
        )
        self.assertIn('200.00', str(p))


class AlertModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.dept = make_department()
        self.job  = make_job(self.dept, self.user)

    def test_resolve(self):
        alert = Alert.objects.create(
            alert_type=Alert.AlertType.OVERDUE_JOB,
            severity=Alert.Severity.WARNING,
            message='Test alert', job=self.job,
        )
        self.assertFalse(alert.resolved)
        alert.resolve(self.user)
        self.assertTrue(alert.resolved)
        self.assertIsNotNone(alert.resolved_at)
        self.assertEqual(alert.resolved_by, self.user)


# ══════════════════════════════════════════════════════════
# SERVICE TESTS
# ══════════════════════════════════════════════════════════

class CreateJobServiceTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.dept = make_department()

    def test_creates_job_and_initial_update(self):
        job = services.create_job(
            title='Print Banners', department=self.dept, created_by=self.user,
        )
        self.assertEqual(job.status, Job.Status.PENDING)
        self.assertEqual(job.service_type, Job.ServiceType.GENERAL)
        self.assertEqual(job.updates.count(), 1)
        self.assertEqual(job.updates.first().comment, 'Job created.')

    def test_service_type_stored(self):
        job = services.create_job(
            title='Network Setup', department=self.dept, created_by=self.user,
            service_type=Job.ServiceType.NETWORK_IT,
        )
        self.assertEqual(job.service_type, Job.ServiceType.NETWORK_IT)

    def test_price_stored(self):
        job = services.create_job(
            title='Promo Video', department=self.dept, created_by=self.user,
            price=Decimal('1500.00'),
        )
        self.assertEqual(job.price, Decimal('1500.00'))


class UpdateJobStatusServiceTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.dept = make_department()
        self.job  = services.create_job('Job A', self.dept, self.user)

    def test_status_changes(self):
        services.update_job_status(self.job, Job.Status.IN_PROGRESS, self.user)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.Status.IN_PROGRESS)

    def test_completed_at_set_on_completion(self):
        services.update_job_status(self.job, Job.Status.COMPLETED, self.user)
        self.job.refresh_from_db()
        self.assertIsNotNone(self.job.completed_at)

    def test_completed_at_cleared_when_re_opened(self):
        services.update_job_status(self.job, Job.Status.COMPLETED, self.user)
        services.update_job_status(self.job, Job.Status.IN_PROGRESS, self.user)
        self.job.refresh_from_db()
        self.assertIsNone(self.job.completed_at)

    def test_update_log_created(self):
        count_before = self.job.updates.count()
        services.update_job_status(self.job, Job.Status.IN_PROGRESS, self.user, comment='Starting now')
        self.assertEqual(self.job.updates.count(), count_before + 1)


class EditJobServiceTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.dept = make_department()
        self.job  = services.create_job('Old Title', self.dept, self.user)

    def test_edit_allowed_fields(self):
        services.edit_job(self.job, self.user, title='New Title', priority=Job.Priority.HIGH)
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, 'New Title')
        self.assertEqual(self.job.priority, Job.Priority.HIGH)

    def test_edit_ignores_disallowed_fields(self):
        original_status = self.job.status
        services.edit_job(self.job, self.user, status=Job.Status.COMPLETED)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, original_status)


class ResourceUsageServiceTest(TestCase):

    def setUp(self):
        self.user     = make_user()
        self.dept     = make_department()
        self.job      = services.create_job('Job B', self.dept, self.user)
        self.resource = make_resource(quantity=50, unit_cost=10)

    def test_usage_deducts_stock(self):
        services.record_resource_usage(self.job, self.resource, 20, self.user)
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.quantity, Decimal('30'))

    def test_usage_raises_on_insufficient_stock(self):
        with self.assertRaises(ValueError):
            services.record_resource_usage(self.job, self.resource, 200, self.user)

    def test_usage_creates_record(self):
        services.record_resource_usage(self.job, self.resource, 5, self.user)
        self.assertEqual(self.job.resource_usages.count(), 1)

    def test_line_total(self):
        usage = services.record_resource_usage(self.job, self.resource, 3, self.user)
        # qty 3 x unit_cost 10 = 30
        self.assertEqual(usage.line_total(), Decimal('30'))

    def test_total_expenses_after_usage(self):
        services.record_resource_usage(self.job, self.resource, 4, self.user)
        # 4 x 10 = 40
        self.assertEqual(self.job.total_expenses(), Decimal('40'))


class CreatePurchaseServiceTest(TestCase):

    def setUp(self):
        self.user     = make_user()
        self.resource = make_resource(quantity=10, unit_cost=5)

    def test_purchase_increases_stock(self):
        services.create_purchase(
            created_by=self.user,
            items=[{'resource': self.resource, 'quantity': Decimal('20'), 'unit_cost': Decimal('5')}],
        )
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.quantity, Decimal('30'))

    def test_purchase_total_calculated(self):
        purchase = services.create_purchase(
            created_by=self.user,
            items=[{'resource': self.resource, 'quantity': Decimal('10'), 'unit_cost': Decimal('8')}],
        )
        self.assertEqual(purchase.purchase_total, Decimal('80'))

    def test_price_change_records_history(self):
        # resource starts at cost 5, buy at cost 8 -> history entry
        services.create_purchase(
            created_by=self.user,
            items=[{'resource': self.resource, 'quantity': Decimal('5'), 'unit_cost': Decimal('8')}],
        )
        self.assertEqual(self.resource.price_history.count(), 1)
        history = self.resource.price_history.first()
        self.assertEqual(history.old_price, Decimal('5'))
        self.assertEqual(history.new_price, Decimal('8'))


# ══════════════════════════════════════════════════════════
# ALERT SERVICE TESTS
# ══════════════════════════════════════════════════════════

class AlertServiceTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.dept = make_department()

    def test_overdue_job_creates_alert(self):
        yesterday = timezone.now().date() - timedelta(days=5)
        job = make_job(self.dept, self.user, due_date=yesterday)
        services.check_overdue_job_alert(job)
        self.assertTrue(
            Alert.objects.filter(alert_type=Alert.AlertType.OVERDUE_JOB, job=job, resolved=False).exists()
        )

    def test_overdue_job_no_alert_when_on_time(self):
        tomorrow = timezone.now().date() + timedelta(days=1)
        job = make_job(self.dept, self.user, due_date=tomorrow)
        services.check_overdue_job_alert(job)
        self.assertFalse(
            Alert.objects.filter(alert_type=Alert.AlertType.OVERDUE_JOB, job=job, resolved=False).exists()
        )

    def test_overdue_job_resolves_alert_when_completed(self):
        yesterday = timezone.now().date() - timedelta(days=2)
        job = make_job(self.dept, self.user, due_date=yesterday)
        services.check_overdue_job_alert(job)
        self.assertEqual(Alert.objects.filter(resolved=False).count(), 1)

        job.status = Job.Status.COMPLETED
        job.save()
        services.check_overdue_job_alert(job)
        self.assertEqual(Alert.objects.filter(resolved=False).count(), 0)

    def test_no_duplicate_alerts(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        job = make_job(self.dept, self.user, due_date=yesterday)
        services.check_overdue_job_alert(job)
        services.check_overdue_job_alert(job)  # second call
        self.assertEqual(
            Alert.objects.filter(alert_type=Alert.AlertType.OVERDUE_JOB, job=job).count(), 1
        )

    def test_abnormal_expense_alert_budget_overrun(self):
        resource = make_resource(quantity=100, unit_cost=10)
        job = make_job(self.dept, self.user, price=Decimal('50.00'))
        services.record_resource_usage(job, resource, 10, self.user)  # expenses=100 > budget=50
        self.assertTrue(
            Alert.objects.filter(alert_type=Alert.AlertType.ABNORMAL_EXPENSE, job=job, resolved=False).exists()
        )

    def test_low_stock_alert_created(self):
        resource = make_resource(quantity=5, reorder_level=10)
        services.check_low_stock_alert(resource)
        self.assertTrue(
            Alert.objects.filter(alert_type=Alert.AlertType.LOW_STOCK, resource=resource, resolved=False).exists()
        )

    def test_low_stock_alert_resolved_when_restocked(self):
        resource = make_resource(quantity=5, reorder_level=10)
        services.check_low_stock_alert(resource)
        resource.quantity = Decimal('50')
        resource.save()
        services.check_low_stock_alert(resource)
        self.assertEqual(Alert.objects.filter(resolved=False).count(), 0)

    def test_run_all_checks_no_errors(self):
        # Smoke test: should not raise
        make_job(self.dept, self.user, status=Job.Status.PENDING)
        make_resource(quantity=5, reorder_level=10)
        services.run_all_checks()


# ══════════════════════════════════════════════════════════
# VIEW TESTS
# ══════════════════════════════════════════════════════════

class AuthViewTest(TestCase):

    def test_login_page_loads(self):
        response = self.client.get(reverse('core:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_with_valid_credentials(self):
        make_user('viewuser', password='viewpass')
        response = self.client.post(reverse('core:login'), {
            'username': 'viewuser', 'password': 'viewpass',
        })
        self.assertRedirects(response, reverse('core:dashboard'))

    def test_login_with_bad_credentials(self):
        response = self.client.post(reverse('core:login'), {
            'username': 'nobody', 'password': 'wrong',
        })
        self.assertEqual(response.status_code, 200)  # re-renders login

    def test_redirect_to_login_when_unauthenticated(self):
        response = self.client.get(reverse('core:dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('core:login')}?next={reverse('core:dashboard')}",
        )

    def test_logout_redirects(self):
        make_user('logoutuser', password='logoutpass')
        self.client.login(username='logoutuser', password='logoutpass')
        response = self.client.post(reverse('core:logout'))
        self.assertRedirects(response, reverse('core:login'))


class DashboardViewTest(TestCase):

    def setUp(self):
        self.user = make_user('dash', password='pass')
        self.client.login(username='dash', password='pass')

    def test_dashboard_loads(self):
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)


class JobViewTest(TestCase):

    def setUp(self):
        self.user = make_user('jobuser', password='pass')
        self.dept = make_department('Print')
        self.client.login(username='jobuser', password='pass')

    def test_job_list_loads(self):
        response = self.client.get(reverse('core:job_list'))
        self.assertEqual(response.status_code, 200)

    def test_job_create_get(self):
        response = self.client.get(reverse('core:job_create'))
        self.assertEqual(response.status_code, 200)

    def test_job_create_post(self):
        self.client.post(reverse('core:job_create'), {
            'title':        'Banner Print',
            'department':   self.dept.pk,
            'service_type': 'printing',
            'priority':     'medium',
            'description':  '',
        })
        self.assertEqual(Job.objects.filter(title='Banner Print').count(), 1)

    def test_job_detail_loads(self):
        job = make_job(self.dept, self.user, title='Detail Job')
        response = self.client.get(reverse('core:job_detail', args=[job.pk]))
        self.assertEqual(response.status_code, 200)

    def test_job_edit_get(self):
        job = make_job(self.dept, self.user, title='Edit Me')
        response = self.client.get(reverse('core:job_edit', args=[job.pk]))
        self.assertEqual(response.status_code, 200)

    def test_job_status_update(self):
        job = make_job(self.dept, self.user)
        self.client.post(reverse('core:job_status_update', args=[job.pk]), {
            'status': 'in_progress', 'comment': 'Started',
        })
        job.refresh_from_db()
        self.assertEqual(job.status, 'in_progress')


class ResourceViewTest(TestCase):

    def setUp(self):
        self.user = make_user('resuser', password='pass')
        self.client.login(username='resuser', password='pass')

    def test_resource_list_loads(self):
        response = self.client.get(reverse('core:resource_list'))
        self.assertEqual(response.status_code, 200)

    def test_resource_create_get(self):
        response = self.client.get(reverse('core:resource_create'))
        self.assertEqual(response.status_code, 200)

    def test_resource_create_post(self):
        self.client.post(reverse('core:resource_create'), {
            'title':         'Toner',
            'unit':          'units',
            'quantity':      '50',
            'unit_cost':     '120.00',
            'reorder_level': '5',
        })
        self.assertEqual(Resource.objects.filter(title='Toner').count(), 1)

    def test_resource_detail_loads(self):
        r = make_resource('A4 Paper')
        response = self.client.get(reverse('core:resource_detail', args=[r.pk]))
        self.assertEqual(response.status_code, 200)


class PaymentViewTest(TestCase):

    def setUp(self):
        self.user = make_user('payuser', password='pass')
        self.dept = make_department()
        self.job  = make_job(self.dept, self.user, status=Job.Status.COMPLETED)
        self.client.login(username='payuser', password='pass')

    def test_payment_form_get(self):
        response = self.client.get(reverse('core:payment_create', args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)

    def test_payment_form_post(self):
        self.client.post(reverse('core:payment_create', args=[self.job.pk]), {
            'amount':         '500.00',
            'payment_date':   date.today().isoformat(),
            'payment_method': 'cash',
            'reference':      'REC-001',
            'notes':          '',
        })
        self.assertEqual(Payment.objects.filter(job=self.job).count(), 1)
        p = Payment.objects.get(job=self.job)
        self.assertEqual(p.amount, Decimal('500.00'))


class AlertViewTest(TestCase):

    def setUp(self):
        self.user = make_user('alertuser', password='pass')
        self.dept = make_department()
        self.client.login(username='alertuser', password='pass')

    def test_alert_list_loads(self):
        response = self.client.get(reverse('core:alert_list'))
        self.assertEqual(response.status_code, 200)

    def test_run_checks_redirects(self):
        response = self.client.post(reverse('core:run_checks'))
        self.assertRedirects(response, reverse('core:alert_list'))

    def test_alert_resolve(self):
        job   = make_job(self.dept, self.user)
        alert = Alert.objects.create(
            alert_type=Alert.AlertType.OVERDUE_JOB,
            severity=Alert.Severity.WARNING,
            message='Test', job=job,
        )
        self.client.post(reverse('core:alert_resolve', args=[alert.pk]))
        alert.refresh_from_db()
        self.assertTrue(alert.resolved)


class ReportViewTest(TestCase):

    def setUp(self):
        self.manager = make_user('reportmanager', role=User.Role.MANAGER, password='pass')
        self.factory = RequestFactory()
        settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

    def test_jobs_report_renders_for_jobs_without_assigned_user(self):
        dept = make_department('Reports Dept')
        make_job(dept, self.manager, title='Unassigned Job')

        request = self.factory.get(reverse('core:jobs_report'), {
            'start_date': '2000-01-01',
            'end_date': '2100-12-31',
            'filter_by': 'created_by',
            'user_id': str(self.manager.pk),
        })
        request.user = self.manager

        response = JobsReportView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unassigned Job')
        self.assertContains(response, '—')


class UserManagementViewTest(TestCase):

    def setUp(self):
        self.admin = make_user('admin', role=User.Role.SUPER_ADMIN, password='pass')
        self.client.login(username='admin', password='pass')

    def test_user_list_loads(self):
        response = self.client.get(reverse('core:user_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_create_get(self):
        response = self.client.get(reverse('core:user_create'))
        self.assertEqual(response.status_code, 200)

    def test_user_create_post(self):
        self.client.post(reverse('core:user_create'), {
            'username':   'newstaff',
            'first_name': 'New',
            'last_name':  'Staff',
            'email':      'new@example.com',
            'role':       'staff',
            'department': '',
            'password':   'securepass123',
        })
        self.assertTrue(User.objects.filter(username='newstaff').exists())

    def test_user_toggle_active(self):
        target = make_user('toggleme', password='pass')
        self.assertTrue(target.is_active)
        self.client.post(reverse('core:user_toggle_active', args=[target.pk]))
        target.refresh_from_db()
        self.assertFalse(target.is_active)


class DepartmentViewTest(TestCase):

    def setUp(self):
        self.admin = make_user('deptadmin', role=User.Role.SUPER_ADMIN, password='pass')
        self.client.login(username='deptadmin', password='pass')

    def test_department_list_loads(self):
        response = self.client.get(reverse('core:department_list'))
        self.assertEqual(response.status_code, 200)

    def test_department_create_get(self):
        response = self.client.get(reverse('core:department_create'))
        self.assertEqual(response.status_code, 200)

    def test_department_create_post(self):
        self.client.post(reverse('core:department_create'), {
            'name':        'Reprographics',
            'description': 'Handles all print jobs',
            'hod':         '',
        })
        self.assertTrue(Department.objects.filter(name='Reprographics').exists())

    def test_department_edit_get(self):
        dept = make_department('IT Support')
        response = self.client.get(reverse('core:department_edit', args=[dept.pk]))
        self.assertEqual(response.status_code, 200)
