# app/integrations/hex_service.py
"""Hex analytics embed (optional — failures are non-fatal)."""

from __future__ import annotations

import asyncio

import httpx
import structlog

from app.config import settings

log = structlog.get_logger()

_HEX_BASE = "https://app.hex.tech/api/v1"
_TERMINAL_STATUSES = {"COMPLETED", "ERRORED", "KILLED", "UNABLE_TO_ALLOCATE_KERNEL"}
_POLL_INTERVAL = 3  # seconds between status checks
_POLL_TIMEOUT = 60  # max seconds to wait for completion


class HexService:
    """Trigger and poll Hex project runs for sprint analytics dashboards."""

    @staticmethod
    async def generate_sprint_dashboard(sprint_data: dict) -> str | None:
        """
        Triggers a Hex project run, polls until COMPLETED, returns the runUrl.
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

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # --- Trigger the run ---
                r = await client.post(
                    f"{_HEX_BASE}/projects/{project_id}/runs",
                    headers=headers,
                    json={
                        "inputParams": sprint_data,
                        "updatePublishedResults": True,
                        "useCachedSqlResults": False,
                    },
                )
                if r.status_code >= 400:
                    log.warning(
                        "hex.trigger_failed",
                        status=r.status_code,
                        body_preview=r.text[:200],
                    )
                    return None

                try:
                    data = r.json()
                except Exception:
                    log.warning("hex.invalid_json_response")
                    return None

                run_id = data.get("runId")
                run_url = data.get("runUrl")

                if not run_id:
                    log.warning("hex.no_run_id_in_response")
                    return run_url  # best-effort fallback

                log.info("hex.run_triggered", run_id=run_id)

                # --- Poll until terminal status ---
                elapsed = 0
                while elapsed < _POLL_TIMEOUT:
                    await asyncio.sleep(_POLL_INTERVAL)
                    elapsed += _POLL_INTERVAL

                    status_r = await client.get(
                        f"{_HEX_BASE}/projects/{project_id}/runs/{run_id}",
                        headers=headers,
                    )
                    if status_r.status_code >= 400:
                        log.warning("hex.poll_failed", status=status_r.status_code)
                        break

                    try:
                        status_data = status_r.json()
                    except Exception:
                        break

                    status = status_data.get("status", "")
                    run_url = status_data.get("runUrl") or run_url

                    log.info("hex.run_status", status=status, elapsed=elapsed)

                    if status in _TERMINAL_STATUSES:
                        if status == "COMPLETED":
                            return str(run_url) if run_url else None
                        else:
                            log.warning("hex.run_non_completed", status=status)
                            return None

                log.warning("hex.poll_timeout", run_id=run_id)
                return str(run_url) if run_url else None

        except Exception as e:
            log.warning("hex.generate_sprint_dashboard.failed", error=str(e))
            return None
