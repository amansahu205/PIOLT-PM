"""Daily standup digest background job."""

import structlog

from app.db.mongo import get_db
from app.services.standup_service import StandupService

log = structlog.get_logger()


async def run_standup_job() -> None:
    log.info("job.standup.start")
    try:
        db = get_db()
        digest = await StandupService.generate_digest(db)
        log.info(
            "job.standup.complete",
            engineers=len(digest.get("digest", [])),
        )
    except Exception as e:
        log.error("job.standup.failed", error=str(e))
