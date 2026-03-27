"""
core/scheduler.py — APScheduler configuration for scheduled background tasks.

Tasks:
  - Weekly AI report: every Monday at 07:00 (Africa/Accra)
  - Daily alert sweep: every day at 00:01
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django.conf import settings

logger = logging.getLogger(__name__)

_scheduler = None


def weekly_report_job():
    from core.services import generate_weekly_report_auto
    try:
        report = generate_weekly_report_auto()
        logger.info(f"Weekly report generated: Report #{report.pk}")
    except Exception as e:
        logger.error(f"Weekly report generation failed: {e}")


def daily_alert_sweep_job():
    from core.services import run_all_checks
    try:
        run_all_checks()
        logger.info("Daily alert sweep completed.")
    except Exception as e:
        logger.error(f"Daily alert sweep failed: {e}")


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    _scheduler.add_jobstore(DjangoJobStore(), "default")

    _scheduler.add_job(
        weekly_report_job,
        trigger=CronTrigger(day_of_week="mon", hour=7, minute=0),
        id="weekly_ai_report",
        name="Generate Weekly AI Report",
        replace_existing=True,
        jobstore="default",
    )
    _scheduler.add_job(
        daily_alert_sweep_job,
        trigger=CronTrigger(hour=0, minute=1),
        id="daily_alert_sweep",
        name="Daily Alert Sweep",
        replace_existing=True,
        jobstore="default",
    )

    _scheduler.start()
    logger.info("Scheduler started: weekly report + daily alert sweep registered.")
