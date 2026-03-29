# app/services/voice_service.py
"""F-005 Voice agent — ElevenLabs + Twilio context injection."""

from __future__ import annotations

from typing import Any

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.repositories.transcript_repo import TranscriptRepository
from app.services.context_builder import get_context_for_voice

log = structlog.get_logger()

_MAX_PROMPT_CHARS = 12_000


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
