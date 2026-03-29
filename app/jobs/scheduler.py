# app/jobs/scheduler.py
"""
APScheduler — BACKEND_STRUCTURE §15.

Jobs:
  context_refresh — every 15 minutes (IntervalTrigger)
  daily_standup     — 09:00 America/New_York
  blocker_poll      — every 15 min, hours 8–20 ET (CronTrigger)
  weekly_report     — Friday 17:00 America/New_York
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

import structlog

log = structlog.get_logger()
scheduler = AsyncIOScheduler(timezone="America/New_York")


async def start_scheduler() -> None:
    from app.jobs.blocker_job import run_blocker_job
    from app.jobs.context_job import run_context_job
    from app.jobs.report_job import run_report_job
    from app.jobs.standup_job import run_standup_job

    scheduler.add_job(
        run_context_job,
        IntervalTrigger(minutes=15),
        id="context_refresh",
        name="Refresh project context snapshot",
        replace_existing=True,
        misfire_grace_time=60,
    )

    scheduler.add_job(
        run_standup_job,
        CronTrigger(hour=9, minute=0, timezone="America/New_York"),
        id="daily_standup",
        name="Generate daily standup digest",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        run_blocker_job,
        CronTrigger(hour="8-20", minute="*/15", timezone="America/New_York"),
        id="blocker_poll",
        name="Scan for new blockers",
        replace_existing=True,
        misfire_grace_time=60,
    )

    scheduler.add_job(
        run_report_job,
        CronTrigger(day_of_week="fri", hour=17, minute=0, timezone="America/New_York"),
        id="weekly_report",
        name="Generate Friday status report",
        replace_existing=True,
        misfire_grace_time=600,
    )

    scheduler.start()
    log.info("scheduler.started", jobs=len(scheduler.get_jobs()))


async def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
    log.info("scheduler.stopped")
