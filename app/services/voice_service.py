# app/services/voice_service.py
"""F-005 Voice agent — ElevenLabs + Twilio context injection."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.repositories.transcript_repo import TranscriptRepository
from app.services.context_builder import get_context_for_voice

log = structlog.get_logger()

_MAX_PROMPT_CHARS = 12_000
_ELEVENLABS_REGISTER_URL = "https://api.elevenlabs.io/v1/convai/twilio/register-call"


def _build_system_prompt(ctx: dict[str, Any]) -> str:
    lines = [
        "You are PilotPM, an AI project management assistant on a live phone call.",
        "Answer only using the context below. Be concise, helpful, and professional.",
        "",
        f"Sprint: {ctx.get('sprint_name', 'unknown')}",
        f"Days remaining: {ctx.get('days_remaining', 'unknown')}",
        f"Data refreshed: {ctx.get('refresh_timestamp', '')}",
        f"Sprint velocity (progress indicator): {ctx.get('velocity_pct', 'unknown')}",
        f"Active blocker signals (count): {ctx.get('blocker_count', 0)}",
        "",
        "Blockers / risks:",
        ctx.get("blockers_summary", ""),
        "",
        "Latest standup digest:",
        ctx.get("standup_summary", ""),
        "",
        "Recent engineering activity:",
        ctx.get("recent_activity", ""),
    ]
    text = "\n".join(lines)
    if len(text) > _MAX_PROMPT_CHARS:
        text = text[:_MAX_PROMPT_CHARS] + "\n...(truncated)"
    return text


class VoiceService:
    @staticmethod
    async def get_twiml_for_twilio_inbound(
        *,
        from_number: str,
        to_number: str,
        agent_id: str,
        system_prompt: str,
    ) -> str:
        """
        Ask ElevenLabs for TwiML that connects this Twilio call to the ConvAI agent.
        Uses the official register-call API (correct Stream URL + protocol for Twilio).
        """
        to = (to_number or "").strip() or (settings.TWILIO_PHONE or "").strip()
        frm = (from_number or "").strip() or "unknown"
        if not to:
            raise ValueError("Missing To / TWILIO_PHONE for ElevenLabs register-call")

        key = (settings.ELEVENLABS_API_KEY or "").strip()
        if not key:
            raise ValueError("ELEVENLABS_API_KEY is required for Twilio voice")

        prompt = (system_prompt or "")[:_MAX_PROMPT_CHARS]

        payload: dict[str, Any] = {
            "agent_id": agent_id,
            "from_number": frm,
            "to_number": to,
            "direction": "inbound",
            "conversation_initiation_client_data": {
                "conversation_config_override": {
                    "agent": {
                        "prompt": {
                            "prompt": prompt,
                        },
                    },
                },
                "source_info": {"source": "twilio", "version": "pilotpm"},
            },
        }

        headers = {
            "xi-api-key": key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post(_ELEVENLABS_REGISTER_URL, headers=headers, json=payload)

        if not r.is_success:
            log.error(
                "voice.elevenlabs_register_call_failed",
                status_code=r.status_code,
                body_preview=(r.text or "")[:800],
            )
            r.raise_for_status()

        # API returns TwiML XML as plain text / XML body
        twiml = (r.text or "").strip()
        if not twiml.startswith("<?xml") and not twiml.startswith("<Response"):
            log.warning("voice.elevenlabs_unexpected_body", preview=twiml[:200])
        return twiml

    @staticmethod
    async def get_voice_context(db: AsyncIOMotorDatabase) -> dict[str, Any]:
        assert db is not None
        ctx = await get_context_for_voice()
        system_prompt = _build_system_prompt(ctx)
        return {
            "agent_id": settings.ELEVENLABS_AGENT_ID,
            "system_prompt": system_prompt,
            "context": ctx,
        }

    @staticmethod
    async def get_voice_context_summary(db: AsyncIOMotorDatabase) -> dict[str, Any]:
        assert db is not None
        ctx = await get_context_for_voice()
        return {
            "refresh_timestamp": ctx.get("refresh_timestamp"),
            "sprint_name": ctx.get("sprint_name"),
            "days_remaining": ctx.get("days_remaining"),
            "velocity_pct": ctx.get("velocity_pct"),
            "blocker_count": ctx.get("blocker_count"),
            "blockers_summary": ctx.get("blockers_summary"),
            "standup_summary": ctx.get("standup_summary"),
            "recent_activity": ctx.get("recent_activity"),
            "agent_id": settings.ELEVENLABS_AGENT_ID,
        }

    @staticmethod
    async def log_call_start(
        call_sid: str,
        caller: str,
        db: AsyncIOMotorDatabase,
    ) -> dict[str, Any]:
        row = await TranscriptRepository.log_call_start(call_sid, caller, db)
        log.info("voice.call_logged", call_sid=call_sid, caller=caller)
        return row

    @staticmethod
    async def get_transcripts(
        limit: int,
        db: AsyncIOMotorDatabase,
    ) -> list[dict[str, Any]]:
        return await TranscriptRepository.find_recent(db, n=min(limit, 50))
