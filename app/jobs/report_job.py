"""Weekly status report job — Friday 5pm ET (see scheduler.py)."""

import structlog

from app.db.mongo import get_db
from app.services.report_service import ReportService

log = structlog.get_logger()


async def run_report_job() -> None:
    log.info("job.report.start")
    try:
        db = get_db()
        await ReportService.generate_report(db)
        log.info("job.report.complete")
    except ValueError as e:
        log.warning("job.report.skipped", reason=str(e))
    except Exception as e:
        log.error("job.report.failed", error=str(e))
