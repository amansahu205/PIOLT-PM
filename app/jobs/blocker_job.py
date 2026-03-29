"""Background job: blocker scan during work hours (scheduled in scheduler.py)."""

import structlog

from app.db.mongo import get_db
from app.services.blocker_service import BlockerService

log = structlog.get_logger()


async def run_blocker_job() -> None:
    log.info("job.blocker.start")
    try:
        db = get_db()
        blockers = await BlockerService.run_blocker_scan(db)
        log.info("job.blocker.complete", count=len(blockers))
    except Exception as e:
        log.error("job.blocker.failed", error=str(e))
