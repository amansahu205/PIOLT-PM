"""Context snapshot refresh job."""

import structlog

from app.services.context_builder import build_context_snapshot

log = structlog.get_logger()


async def run_context_job() -> None:
    try:
        snapshot = await build_context_snapshot()
        sources = snapshot.get("sources_available", {})
        log.info("job.context.refreshed", sources=sources)
    except Exception as e:
        log.error("job.context.failed", error=str(e))
