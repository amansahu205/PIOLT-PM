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
        Returns an embed URL when Hex accepts the request; otherwise None.
        Endpoint layout varies by Hex workspace — failures degrade to plain-text reports.
        """
        if not (settings.HEX_API_KEY or "").strip():
            log.warning("hex.no_api_key")
            return None
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.post(
                    "https://us-east-1.api.hex.tech/v1/notebook/runs",
                    headers={
                        "Authorization": f"Bearer {settings.HEX_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={"parameters": sprint_data},
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
                url = data.get("embedUrl") or data.get("embed_url") or data.get("url")
                if url:
                    return str(url)
        except Exception as e:
            log.warning("hex.generate_sprint_dashboard.failed", error=str(e))
            return None

        log.warning("hex.no_embed_url_in_response")
        return None
