"""
APScheduler configuration for daily analysis job.
Runs the analysis pipeline every weekday at 6:00 AM Eastern Time.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from app.core.config import settings

scheduler = AsyncIOScheduler()


def configure_scheduler() -> AsyncIOScheduler:
    """Configure and return the scheduler with the daily analysis job."""
    from app.services.daily_engine import run_daily_analysis

    eastern = pytz.timezone("US/Eastern")

    if settings.daily_analysis_enabled:
        scheduler.add_job(
            run_daily_analysis,
            CronTrigger(
                hour=settings.daily_analysis_hour,
                minute=settings.daily_analysis_minute,
                day_of_week="mon-fri",
                timezone=eastern,
            ),
            id="daily_analysis",
            name="Daily Pre-Market Analysis",
            replace_existing=True,
            misfire_grace_time=3600,  # Allow 1 hour grace period
        )

    return scheduler
