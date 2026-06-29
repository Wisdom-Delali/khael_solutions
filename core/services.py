"""
core/services.py — all business logic in one place.

Sections:
  1. Job Service          — create, update, edit jobs; role-aware querying
  2. Resource Service     — purchases, usage recording, stock queries
  3. Alert Service        — 5 rule-based checks + composite sweeps
  4. Report Service       — data aggregation, OpenAI prompt, report generation
"""
import json
import re
from decimal import Decimal
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.conf import settings

from core.utils import DecimalEncoder


# ══════════════════════════════════════════════════════════
# 1. JOB SERVICE
# ══════════════════════════════════════════════════════════

def get_jobs_for_user(user):
    """Role-aware job queryset: staff see only their department."""
    from core.models import Job
    if user.role in ['super_admin', 'manager']:
        return Job.objects.all().select_related('department', 'assigned_to', 'created_by')
    dept = user.get_department()
    if dept:
        return Job.objects.filter(department=dept).select_related(
            'department', 'assigned_to', 'created_by'
        )
    return Job.objects.none()


@transaction.atomic
def create_job(title, department, created_by, description='', assigned_to=None,
               client_name='', client_contact='', priority=None, service_type=None,
               price=None, start_date=None, due_date=None):
    from core.models import Job, JobUpdate
    if priority is None:
        priority = Job.Priority.MEDIUM
    if service_type is None:
        service_type = Job.ServiceType.GENERAL

    job = Job.objects.create(
        title=title, department=department, created_by=created_by,
        description=description, assigned_to=assigned_to,
        client_name=client_name, client_contact=client_contact,
        priority=priority, service_type=service_type,
        price=price, start_date=start_date, due_date=due_date,
        status=Job.Status.PENDING,
    )
    JobUpdate.objects.create(
        job=job, updated_by=created_by,
        status=Job.Status.PENDING, comment='Job created.',
    )
    return job


@transaction.atomic
def update_job_status(job, new_status, updated_by, comment=''):
    from core.models import Job, JobUpdate
    old_status = job.status
    job.status = new_status
    if new_status == Job.Status.COMPLETED:
        job.completed_at = timezone.now()
    elif old_status == Job.Status.COMPLETED:
        job.completed_at = None
    job.save()
    JobUpdate.objects.create(
        job=job, updated_by=updated_by, status=new_status,
        comment=comment or f'Status changed from {old_status} to {new_status}.',
    )
    run_job_alert_checks(job)
    return job


@transaction.atomic
def edit_job(job, updated_by, **kwargs):
    from core.models import JobUpdate
    allowed = {
        'title', 'description', 'priority', 'service_type', 'price',
        'start_date', 'due_date', 'assigned_to', 'client_name', 'client_contact',
    }
    for field, value in kwargs.items():
        if field in allowed:
            setattr(job, field, value)
    job.save()
    JobUpdate.objects.create(
        job=job, updated_by=updated_by, status=job.status, comment='Job details updated.',
    )
    run_job_alert_checks(job)
    return job


def get_job_timeline(job):
    return job.updates.select_related('updated_by').order_by('timestamp')


# ══════════════════════════════════════════════════════════
# 2. RESOURCE SERVICE
# ══════════════════════════════════════════════════════════

@transaction.atomic
def create_purchase(created_by, items, notes=''):
    """
    items: [{'resource': Resource, 'quantity': Decimal, 'unit_cost': Decimal}, ...]
    """
    from core.models import Purchase, PurchaseResource, ResourceHistory
    purchase = Purchase.objects.create(created_by=created_by, notes=notes)
    total = Decimal('0')

    for item in items:
        resource  = item['resource']
        qty       = item['quantity']
        unit_cost = item['unit_cost']

        if resource.unit_cost != unit_cost:
            ResourceHistory.objects.create(
                resource=resource, purchase=purchase,
                old_price=resource.unit_cost, new_price=unit_cost,
            )
            resource.unit_cost = unit_cost

        PurchaseResource.objects.create(
            purchase=purchase, resource=resource,
            quantity=qty, unit_cost=unit_cost,
        )
        resource.quantity += qty
        resource.save()
        total += qty * unit_cost

    purchase.purchase_total = total
    purchase.save()

    for item in items:
        check_low_stock_alert(item['resource'])

    return purchase


@transaction.atomic
def record_resource_usage(job, resource, quantity, recorded_by):
    from core.models import ResourceUsage
    quantity = Decimal(str(quantity))

    if quantity > resource.quantity:
        raise ValueError('Not enough stock available for this resource.')

    usage = ResourceUsage.objects.create(
        job=job, resource=resource, quantity=quantity,
        unit_cost=resource.unit_cost, recorded_by=recorded_by,
    )
    resource.quantity -= quantity
    resource.save()
    check_low_stock_alert(resource)
    check_abnormal_expense_alert(job)
    return usage


def get_resource_list():
    from core.models import Resource
    return Resource.objects.all().order_by('title')


def get_low_stock_resources():
    from core.models import Resource
    return Resource.objects.filter(quantity__lte=F('reorder_level'))


def get_job_usage_summary(job):
    usages = job.resource_usages.select_related('resource', 'recorded_by')
    total  = sum(u.line_total() for u in usages)
    return usages, total


# ══════════════════════════════════════════════════════════
# 3. ALERT SERVICE
# ══════════════════════════════════════════════════════════

def _alert_exists(alert_type, job=None, resource=None):
    from core.models import Alert
    qs = Alert.objects.filter(alert_type=alert_type, resolved=False)
    if job:      qs = qs.filter(job=job)
    if resource: qs = qs.filter(resource=resource)
    return qs.exists()


def _create_alert(alert_type, severity, message, job=None, resource=None):
    from core.models import Alert
    if not _alert_exists(alert_type, job=job, resource=resource):
        Alert.objects.create(
            alert_type=alert_type, severity=severity,
            message=message, job=job, resource=resource,
        )


def _resolve_alert_if_exists(alert_type, job=None, resource=None):
    from core.models import Alert
    qs = Alert.objects.filter(alert_type=alert_type, resolved=False)
    if job:      qs = qs.filter(job=job)
    if resource: qs = qs.filter(resource=resource)
    qs.update(resolved=True, resolved_at=timezone.now())


def check_overdue_job_alert(job):
    from core.models import Job, Alert
    if job.status in [Job.Status.COMPLETED, Job.Status.CANCELLED]:
        _resolve_alert_if_exists(Alert.AlertType.OVERDUE_JOB, job=job)
        return
    if job.is_overdue():
        days_late = (timezone.now().date() - job.due_date).days
        _create_alert(
            alert_type=Alert.AlertType.OVERDUE_JOB,
            severity=Alert.Severity.CRITICAL if days_late > 3 else Alert.Severity.WARNING,
            message=(
                f'Job "{job.title}" (#{job.pk}) is {days_late} day(s) overdue. '
                f'Due: {job.due_date}, Department: {job.department}.'
            ),
            job=job,
        )
    else:
        _resolve_alert_if_exists(Alert.AlertType.OVERDUE_JOB, job=job)


def check_abnormal_expense_alert(job):
    from core.models import Alert
    total_expenses = job.total_expenses()
    global_cap     = getattr(settings, 'GLOBAL_EXPENSE_CAP', 5000.00)

    if job.price and total_expenses > job.price:
        overage = total_expenses - job.price
        _create_alert(
            alert_type=Alert.AlertType.ABNORMAL_EXPENSE,
            severity=Alert.Severity.CRITICAL,
            message=(
                f'Job "{job.title}" (#{job.pk}) expenses (GHS {total_expenses:.2f}) '
                f'exceed budget of GHS {job.price:.2f} by GHS {overage:.2f}.'
            ),
            job=job,
        )
    elif total_expenses > global_cap:
        _create_alert(
            alert_type=Alert.AlertType.ABNORMAL_EXPENSE,
            severity=Alert.Severity.WARNING,
            message=(
                f'Job "{job.title}" (#{job.pk}) expenses (GHS {total_expenses:.2f}) '
                f'exceed the global cap of GHS {global_cap:.2f}.'
            ),
            job=job,
        )
    else:
        _resolve_alert_if_exists(Alert.AlertType.ABNORMAL_EXPENSE, job=job)


def check_scheduling_conflict(job):
    from core.models import Job, Alert
    if not job.assigned_to or not job.start_date or not job.due_date:
        return
    overlapping = Job.objects.filter(
        assigned_to=job.assigned_to, department=job.department,
        status__in=[Job.Status.PENDING, Job.Status.IN_PROGRESS],
        start_date__lte=job.due_date, due_date__gte=job.start_date,
    ).exclude(pk=job.pk)
    if overlapping.exists():
        conflict_titles = ', '.join(f'"{j.title}" (#{j.pk})' for j in overlapping[:3])
        _create_alert(
            alert_type=Alert.AlertType.SCHEDULING_CONFLICT,
            severity=Alert.Severity.WARNING,
            message=(
                f'Staff member "{job.assigned_to.get_full_name() or job.assigned_to.username}" '
                f'has overlapping jobs in {job.department}: {conflict_titles}.'
            ),
            job=job,
        )
    else:
        _resolve_alert_if_exists(Alert.AlertType.SCHEDULING_CONFLICT, job=job)


def check_overdue_payment_alert(job):
    from core.models import Job, Alert
    if job.status != Job.Status.COMPLETED or not job.price or not job.completed_at:
        _resolve_alert_if_exists(Alert.AlertType.OVERDUE_PAYMENT, job=job)
        return

    total_paid  = job.total_paid()
    outstanding = job.price - total_paid

    if outstanding <= 0:
        _resolve_alert_if_exists(Alert.AlertType.OVERDUE_PAYMENT, job=job)
        return

    days_since = (timezone.now() - job.completed_at).days
    if days_since > 7:
        _create_alert(
            alert_type=Alert.AlertType.OVERDUE_PAYMENT,
            severity=Alert.Severity.WARNING,
            message=(
                f'Job "{job.title}" (#{job.pk}) completed {days_since} day(s) ago. '
                f'Outstanding: GHS {outstanding:.2f} of GHS {job.price:.2f}. '
                f'Please record payment.'
            ),
            job=job,
        )


def check_low_stock_alert(resource):
    from core.models import Alert
    if resource.is_low_stock():
        _create_alert(
            alert_type=Alert.AlertType.LOW_STOCK,
            severity=Alert.Severity.WARNING,
            message=(
                f'Resource "{resource.title}" is low on stock: '
                f'{resource.quantity} {resource.unit} remaining '
                f'(reorder level: {resource.reorder_level} {resource.unit}). '
                f'Please arrange a purchase.'
            ),
            resource=resource,
        )
    else:
        _resolve_alert_if_exists(Alert.AlertType.LOW_STOCK, resource=resource)


def run_job_alert_checks(job):
    """Run all 4 job-related checks. Called after any job save/update."""
    check_overdue_job_alert(job)
    check_abnormal_expense_alert(job)
    check_scheduling_conflict(job)
    check_overdue_payment_alert(job)


def run_all_checks():
    """Periodic sweep — called by scheduler daily."""
    from core.models import Job, Resource
    active_jobs = Job.objects.filter(
        status__in=[Job.Status.PENDING, Job.Status.IN_PROGRESS, Job.Status.COMPLETED]
    ).select_related('department', 'assigned_to')
    for job in active_jobs:
        run_job_alert_checks(job)
    for resource in Resource.objects.all():
        check_low_stock_alert(resource)


# ══════════════════════════════════════════════════════════
# 4. REPORT SERVICE
# ══════════════════════════════════════════════════════════

def aggregate_operational_data(period_start: date, period_end: date) -> dict:
    from core.models import Job, Alert, Resource, ResourceUsage, Purchase

    jobs_in_period      = Job.objects.filter(created_at__date__range=(period_start, period_end))
    completed_in_period = Job.objects.filter(
        completed_at__date__range=(period_start, period_end), status=Job.Status.COMPLETED,
    )

    job_stats = {
        'total_created': jobs_in_period.count(),
        'completed':     completed_in_period.count(),
        'pending':       jobs_in_period.filter(status=Job.Status.PENDING).count(),
        'in_progress':   jobs_in_period.filter(status=Job.Status.IN_PROGRESS).count(),
        'cancelled':     jobs_in_period.filter(status=Job.Status.CANCELLED).count(),
        'on_hold':       jobs_in_period.filter(status=Job.Status.ON_HOLD).count(),
        'overdue':       Job.objects.filter(
            due_date__lt=timezone.now().date(),
            status__in=[Job.Status.PENDING, Job.Status.IN_PROGRESS]
        ).count(),
    }

    dept_breakdown = list(
        jobs_in_period.values('department__name')
        .annotate(count=Count('id'), completed=Count('id', filter=Q(status='completed')))
        .order_by('-count')
    )

    usages_in_period = ResourceUsage.objects.filter(
        recorded_at__date__range=(period_start, period_end)
    )
    total_resource_cost = sum(
        u.quantity * u.unit_cost for u in usages_in_period.only('quantity', 'unit_cost')
    )
    resource_stats = {
        'total_usage_records': usages_in_period.count(),
        'total_cost': float(total_resource_cost),
        'top_resources': list(
            usages_in_period.values('resource__title')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')[:5]
        ),
    }

    purchases_in_period = Purchase.objects.filter(
        created_at__date__range=(period_start, period_end)
    )
    purchase_stats = {
        'count':       purchases_in_period.count(),
        'total_spend': float(purchases_in_period.aggregate(t=Sum('purchase_total'))['t'] or 0),
    }

    alerts_in_period = Alert.objects.filter(
        created_at__date__range=(period_start, period_end)
    )
    alert_stats = {
        'total':    alerts_in_period.count(),
        'resolved': alerts_in_period.filter(resolved=True).count(),
        'unresolved': alerts_in_period.filter(resolved=False).count(),
        'by_type': list(
            alerts_in_period.values('alert_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
    }

    low_stock_count = Resource.objects.filter(quantity__lte=F('reorder_level')).count()

    return {
        'period':              {'start': str(period_start), 'end': str(period_end)},
        'jobs':                job_stats,
        'departments':         dept_breakdown,
        'resources':           resource_stats,
        'purchases':           purchase_stats,
        'alerts':              alert_stats,
        'low_stock_resources': low_stock_count,
    }


def build_prompt(data: dict) -> str:
    return f"""You are a business intelligence analyst for Khael Solutions, a service company \
        operating printing, network, and multimedia departments in Ghana.

        Based on the following operational data for the period {data['period']['start']} \
        to {data['period']['end']}, write a professional operational summary report.

        The report should:
        1. Start with a brief executive summary (2-3 sentences)
        2. Highlight job performance (completions, delays, overdue work)
        3. Comment on resource and expense trends
        4. Note any significant alerts or anomalies
        5. Provide 2-3 actionable recommendations for management
        6. Use clear, professional language suitable for a manager

        OPERATIONAL DATA:
        {json.dumps(data, indent=2, cls=DecimalEncoder)}

        Write the report in plain paragraphs (no markdown headers). Be concise but insightful.
        """


def call_openai_api(prompt: str) -> str:
    from openai import OpenAI
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return "[AI report unavailable: OPENAI_API_KEY not set.]"
    client   = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional business intelligence analyst."},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=800,
        temperature=0.5,
    )
    return response.choices[0].message.content.strip()


def generate_report(period_start: date, period_end: date,
                    generated_by=None, report_type=None) -> 'Report':
    from core.models import Report
    if report_type is None:
        report_type = Report.ReportType.ON_DEMAND
    data         = aggregate_operational_data(period_start, period_end)
    prompt       = build_prompt(data)
    summary_text = call_openai_api(prompt)
    return Report.objects.create(
        period_start=period_start, period_end=period_end,
        generated_by=generated_by, report_type=report_type,
        summary_text=summary_text,
        raw_data_snapshot=json.loads(json.dumps(data, cls=DecimalEncoder)),
    )


# ══════════════════════════════════════════════════════════
# 5. SMS & RECEIPT SERVICE
# ══════════════════════════════════════════════════════════

def send_sms(content, number):
    """Send SMS via SMSOnlineGH API. Auth token read from settings.SMSONLINE_API_KEY."""
    import http.client
    # Strip or replace non-ASCII characters that SMS gateways may reject
    content = content.encode('ascii', errors='replace').decode('ascii')
    headers = {
        'Host': 'api.smsonlinegh.com',
        'Authorization': f'key {settings.SMSONLINE_API_KEY}',
        'Content-Type': 'application/xml; charset=utf-8',
    }
    payload = (
        "<request><messages><message>"
        f"<text>{content}</text>"
        "<type>0</type>"
        f"<sender>{settings.SMS_SENDER_ID}</sender>"
        "<destinations><item>"
        f"<to>{number}</to>"
        "</item></destinations>"
        "</message></messages></request>"
    )
    conn = http.client.HTTPSConnection("api.smsonlinegh.com")
    conn.request("POST", "/v4/message/sms/send", payload, headers)
    res = conn.getresponse()
    return res.read().decode("utf-8")


def generate_receipt_pdf(payment):
    """Generate a PDF receipt for a Payment."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    # Header
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'], fontSize=20, spaceAfter=4,
    )
    story.append(Paragraph("KhaelSolutions Enterprise", title_style))
    story.append(Paragraph("Payment Receipt", styles['Heading2']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.5 * cm))

    job = payment.job
    receipt = payment.receipt
    desc = job.description or '—'
    if len(desc) > 120:
        desc = desc[:120] + '...'

    data = [
        ["Receipt No:",      str(receipt.uuid)[:8].upper()],
        ["Date:",            payment.payment_date.strftime("%d %B %Y")],
        ["Client Name:",     job.client_name or '—'],
        ["Client Contact:",  job.client_contact or '—'],
        ["Job Title:",       job.title],
        ["Description:",     desc],
        ["Payment Method:",  payment.get_payment_method_display()],
        ["Reference:",       payment.reference or '—'],
        ["Amount Paid:",     f"GHS {payment.amount}"],
    ]

    table = Table(data, colWidths=[5 * cm, 12 * cm])
    table.setStyle(TableStyle([
        ('FONTNAME',     (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',     (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',     (0, 0), (-1, -1), 11),
        ('TEXTCOLOR',    (0, 0), (0, -1), colors.HexColor('#6c757d')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('BOX',          (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('INNERGRID',    (0, 0), (-1, -1), 0.25, colors.HexColor('#dee2e6')),
        ('TOPPADDING',   (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 8),
        ('LEFTPADDING',  (0, 0), (-1, -1), 10),
        # Highlight amount row
        ('BACKGROUND',   (0, -1), (-1, -1), colors.HexColor('#d1fae5')),
        ('FONTNAME',     (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, -1), (-1, -1), 13),
    ]))
    story.append(table)
    story.append(Spacer(1, 1 * cm))

    if payment.notes:
        story.append(Paragraph(f"<b>Notes:</b> {payment.notes}", styles['Normal']))
        story.append(Spacer(1, 0.5 * cm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6')))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Thank you for your payment.", styles['Normal']))
    story.append(Paragraph(
        f"Generated: {timezone.now().strftime('%d %B %Y at %H:%M')}",
        styles['Normal'],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def detect_query_date_range(query: str, today: date) -> tuple[date, date]:
    """
    Parse natural-language date references in a query and return (start, end).
    Falls back to the last 90 days when no recognisable reference is found.
    """
    q = query.lower()

    # "last N days" / "past N days"
    m = re.search(r'(?:last|past)\s+(\d+)\s+days?', q)
    if m:
        n = int(m.group(1))
        return today - timedelta(days=n - 1), today

    # "last N weeks"
    m = re.search(r'(?:last|past)\s+(\d+)\s+weeks?', q)
    if m:
        n = int(m.group(1))
        return today - timedelta(weeks=n), today

    # "last N months"
    m = re.search(r'(?:last|past)\s+(\d+)\s+months?', q)
    if m:
        n = int(m.group(1))
        return today.replace(day=1) - timedelta(days=1) - timedelta(days=30 * (n - 1)), today

    if 'yesterday' in q:
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday

    if 'today' in q:
        return today, today

    if 'this week' in q:
        return today - timedelta(days=today.weekday()), today

    if 'last week' in q:
        start = today - timedelta(days=today.weekday() + 7)
        end   = start + timedelta(days=6)
        return start, end

    if 'this month' in q:
        return today.replace(day=1), today

    if 'last month' in q:
        first_this = today.replace(day=1)
        last_prev  = first_this - timedelta(days=1)
        return last_prev.replace(day=1), last_prev

    if 'this year' in q:
        return today.replace(month=1, day=1), today

    if 'last year' in q:
        return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)

    # Default: 90-day window
    return today - timedelta(days=90), today


def _jobs_for_period(period_start: date, period_end: date) -> list:
    """Return individual job records for the period, for inclusion in the GPT prompt."""
    from core.models import Job
    jobs = (
        Job.objects.filter(created_at__date__range=(period_start, period_end))
        .select_related('department', 'assigned_to')
        .order_by('-created_at')[:100]
    )
    result = []
    for j in jobs:
        result.append({
            'id':           j.pk,
            'title':        j.title,
            'client':       j.client_name or None,
            'department':   str(j.department),
            'service_type': j.get_service_type_display(),
            'status':       j.get_status_display(),
            'priority':     j.get_priority_display(),
            'price':        float(j.price) if j.price else None,
            'assigned_to':  j.assigned_to.get_full_name() or j.assigned_to.username if j.assigned_to else None,
            'created_at':   j.created_at.strftime('%Y-%m-%d'),
            'due_date':     str(j.due_date) if j.due_date else None,
            'overdue':      j.is_overdue(),
        })
    return result


def build_custom_query_prompt(query: str, data: dict, today: date) -> str:
    period = data.get('period', {})
    period_desc = (
        f"{period.get('start')} to {period.get('end')}"
        if period.get('start') != period.get('end')
        else period.get('start')
    )
    return f"""You are a business intelligence analyst for Khael Solutions, a service company \
operating printing, network, and multimedia departments in Ghana.

Today's date is {today}. The operational data below covers the period: {period_desc}.

A manager has asked the following question:
"{query}"

Answer it precisely using the data below. If individual job records are included under \
"job_records", list them specifically (title, client, status, department). \
Use plain paragraphs. Be concise and specific with numbers (GHS amounts, counts, percentages).

OPERATIONAL DATA:
{json.dumps(data, indent=2, cls=DecimalEncoder)}
"""


def generate_custom_query_report(query: str, generated_by=None) -> 'Report':
    """Run a natural-language BI query. Detects date references and fetches the right range."""
    from core.models import Report, Job, Payment
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth

    today        = timezone.now().date()
    period_start, period_end = detect_query_date_range(query, today)

    data = aggregate_operational_data(period_start, period_end)

    # Individual job records for the detected period
    data['job_records'] = _jobs_for_period(period_start, period_end)

    # Revenue by service type
    data['revenue_by_service_type'] = list(
        Payment.objects.filter(payment_date__range=(period_start, period_end))
        .values('job__service_type')
        .annotate(total_revenue=Sum('amount'), payment_count=Count('id'))
        .order_by('-total_revenue')
    )

    # Revenue by month
    data['revenue_by_month'] = [
        {
            'month': str(r['month']),
            'total': float(r['total'] or 0),
        }
        for r in Payment.objects.filter(payment_date__range=(period_start, period_end))
        .annotate(month=TruncMonth('payment_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    ]

    # Top clients by revenue
    data['top_clients_by_revenue'] = list(
        Payment.objects.filter(payment_date__range=(period_start, period_end))
        .values('job__client_name')
        .annotate(total_revenue=Sum('amount'))
        .order_by('-total_revenue')[:10]
    )

    # Jobs by title (top 20)
    data['jobs_by_title'] = list(
        Job.objects.filter(created_at__date__range=(period_start, period_end))
        .values('title')
        .annotate(count=Count('id'), total_paid=Sum('payments__amount'))
        .order_by('-count')[:20]
    )

    prompt       = build_custom_query_prompt(query, data, today)
    summary_text = call_openai_api(prompt)

    return Report.objects.create(
        period_start=period_start,
        period_end=period_end,
        generated_by=generated_by,
        report_type=Report.ReportType.CUSTOM_QUERY,
        query_text=query,
        summary_text=summary_text,
        raw_data_snapshot=json.loads(json.dumps(data, cls=DecimalEncoder)),
    )


def generate_weekly_report_auto():
    from core.models import Report
    today        = timezone.now().date()
    period_end   = today - timedelta(days=1)
    period_start = period_end - timedelta(days=6)
    return generate_report(
        period_start=period_start, period_end=period_end,
        generated_by=None, report_type=Report.ReportType.WEEKLY,
    )
