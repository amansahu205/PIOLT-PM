# app/integrations/hex_service.py
"""Hex analytics embed (optional — failures are non-fatal)."""

from __future__ import annotations

import httpx
import structlog

from app.config import settings

log = structlog.get_logger()


class HexService:
    """Request a shareable Hex embed URL from sprint snapshot data."""

    @staticmethod
    async def generate_sprint_dashboard(sprint_data: dict) -> str | None:
        """
        Returns a runUrl when Hex accepts the request; otherwise None.
        Failures degrade gracefully to plain-text reports.
        """
        api_key = (settings.HEX_API_KEY or "").strip()
        project_id = (settings.HEX_PROJECT_ID or "").strip()
        if not api_key:
            log.warning("hex.no_api_key")
            return None
        if not project_id:
            log.warning("hex.no_project_id")
            return None
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.post(
                    f"https://app.hex.tech/api/v1/projects/{project_id}/runs",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"inputParams": sprint_data},
                )
                if r.status_code >= 400:
                    log.warning(
                        "hex.api_non_success",
                        status=r.status_code,
                        body_preview=r.text[:200],
                    )
                    return None
                try:
                    data = r.json()
                except Exception:
                    log.warning("hex.invalid_json_response")
                    return None
                url = data.get("runUrl")
                if url:
                    return str(url)
        except Exception as e:
            log.warning("hex.generate_sprint_dashboard.failed", error=str(e))
            return None

        log.warning("hex.no_run_url_in_response")
        return None
