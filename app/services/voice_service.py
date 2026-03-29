# app/services/voice_service.py
"""F-005 Voice agent — ElevenLabs + Twilio context injection."""

from __future__ import annotations

import time
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
# Twilio may hit the webhook twice per call (e.g. trial "press any key" / Gather). ElevenLabs
# register-call is only valid once per live leg — reuse TwiML for the same CallSid briefly.
_TWIML_BY_CALL_SID: dict[str, tuple[float, str]] = {}
_TWIML_CACHE_TTL_S = 180.0
_TWIML_CACHE_MAX = 128


def _twiml_cache_get(call_sid: str) -> str | None:
    sid = (call_sid or "").strip()
    if not sid:
        return None
    now = time.monotonic()
    hit = _TWIML_BY_CALL_SID.get(sid)
    if not hit:
        return None
    age = now - hit[0]
    if age > _TWIML_CACHE_TTL_S:
        del _TWIML_BY_CALL_SID[sid]
        return None
    return hit[1]


def _twiml_cache_set(call_sid: str, twiml: str) -> None:
    sid = (call_sid or "").strip()
    if not sid or not twiml:
        return
    now = time.monotonic()
    while len(_TWIML_BY_CALL_SID) >= _TWIML_CACHE_MAX:
        oldest = min(_TWIML_BY_CALL_SID.items(), key=lambda kv: kv[1][0])[0]
        del _TWIML_BY_CALL_SID[oldest]
    _TWIML_BY_CALL_SID[sid] = (now, twiml)


def _build_system_prompt(ctx: dict[str, Any]) -> str:
    lines = [
        "You are PilotPM, an AI project management assistant on a live phone call.",
        "Answer only using the context below. Be concise, helpful, and professional.",
        "Do not make up information — if data is unavailable, say so.",
        "",
        "## Actions you can take",
        "You have two tools available. Use them when the caller asks:",
        "",
        "1. send_email — Call this when the caller says anything like:",
        "   'send an email', 'email the team', 'send a status update', 'notify [person]'.",
        "   Required parameters: recipient_email, subject, body.",
        "   If the caller says 'the team' or 'stakeholders', use recipient_email='stakeholders'.",
        "   Always confirm the action with the caller before calling the tool.",
        "",
        "2. schedule_meeting — Call this when the caller says anything like:",
        "   'schedule a meeting', 'book a call', 'set up a standup', 'block some time'.",
        "   Required: title. Optional: attendees (list), start_time (ISO8601), duration_minutes, description.",
        "   Confirm the time and attendees with the caller before scheduling.",
        "",
        "## Project context",
        f"Sprint: {ctx.get('sprint_name', 'unknown')}",
        f"Days remaining: {ctx.get('days_remaining', 'unknown')}",
        f"Data refreshed: {ctx.get('refresh_timestamp', '')}",
        f"Sprint velocity: {ctx.get('velocity_pct', 'unknown')}",
        f"Active blocker signals: {ctx.get('blocker_count', 0)}",
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
        call_sid: str = "",
    ) -> str:
        """
        Ask ElevenLabs for TwiML that connects this Twilio call to the ConvAI agent.
        Uses the official register-call API (correct Stream URL + protocol for Twilio).
        """
        cached = _twiml_cache_get(call_sid)
        if cached:
            log.info("voice.twiml_cache_hit", call_sid=(call_sid or "").strip())
            return cached

        to = (to_number or "").strip() or (settings.TWILIO_PHONE or "").strip()
        frm = (from_number or "").strip() or "unknown"
        if not to:
            raise ValueError("Missing To / TWILIO_PHONE for ElevenLabs register-call")

        key = (settings.ELEVENLABS_API_KEY or "").strip()
        if not key:
            raise ValueError("ELEVENLABS_API_KEY is required for Twilio voice")

        if not (agent_id or "").strip():
            raise ValueError("ELEVENLABS_AGENT_ID is empty — set it in Railway / .env")

        prompt = (system_prompt or "")[:_MAX_PROMPT_CHARS]

        base_payload: dict[str, Any] = {
            "agent_id": agent_id,
            "from_number": frm,
            "to_number": to,
            "direction": "inbound",
        }
        # Doc-aligned: https://elevenlabs.io/docs/eleven-agents/phone-numbers/twilio-integration/register-call
        with_dynamic_vars: dict[str, Any] = {
            **base_payload,
            "conversation_initiation_client_data": {
                "dynamic_variables": {
                    "caller_number": frm,
                    "pilotpm_context": prompt,
                },
            },
        }
        with_prompt_override: dict[str, Any] = {
            **base_payload,
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

        async def _post_and_extract_twiml(
            body: dict[str, Any], *, label: str
        ) -> tuple[str, int, str]:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(_ELEVENLABS_REGISTER_URL, headers=headers, json=body)
            ct = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
            if not resp.is_success:
                log.error(
                    "voice.elevenlabs_register_call_failed",
                    request=label,
                    status_code=resp.status_code,
                    content_type=ct,
                    body_preview=(resp.text or "")[:1200],
                )
                if resp.status_code == 404:
                    try:
                        data = resp.json()
                        detail = data.get("detail")
                        if isinstance(detail, dict) and detail.get("code") == "document_not_found":
                            raise ValueError(
                                "ElevenLabs: no agent with this ID — open Conversational AI in the same "
                                "account as your API key, copy the agent ID, set ELEVENLABS_AGENT_ID on Railway."
                            )
                    except ValueError:
                        raise
                    except Exception:
                        pass
                resp.raise_for_status()

            raw = (resp.text or "").strip()
            twiml = raw
            if raw.startswith("{") or ct == "application/json":
                try:
                    data = resp.json()
                    if isinstance(data, dict):
                        twiml = (
                            data.get("twiml")
                            or data.get("twilio_response")
                            or data.get("xml")
                            or data.get("response")
                            or raw
                        )
                        if not isinstance(twiml, str):
                            twiml = raw
                except Exception:
                    twiml = raw
            return (twiml or "").strip(), resp.status_code, ct

        attempts: tuple[tuple[str, dict[str, Any]], ...] = (
            ("dynamic_variables", with_dynamic_vars),
            ("conversation_config_override", with_prompt_override),
            ("minimal", base_payload),
        )
        for attempt, payload in attempts:
            try:
                twiml, _status, ct = await _post_and_extract_twiml(payload, label=attempt)
            except httpx.HTTPStatusError as e:
                if attempt in ("dynamic_variables", "conversation_config_override") and e.response.status_code in (
                    400,
                    422,
                ):
                    log.warning(
                        "voice.elevenlabs_register_http_retry",
                        attempt=attempt,
                        status_code=e.response.status_code,
                        body_preview=(e.response.text or "")[:800],
                    )
                    continue
                raise
            if twiml.startswith("<?xml") or twiml.startswith("<Response"):
                if attempt == "minimal":
                    log.warning(
                        "voice.elevenlabs_used_minimal_payload",
                        hint="Connected without context injection (earlier payload shapes failed or returned non-TwiML).",
                    )
                elif attempt == "conversation_config_override":
                    log.info(
                        "voice.elevenlabs_used_prompt_override",
                        hint="dynamic_variables rejected or skipped; agent may ignore {{pilotpm_context}}.",
                    )
                log.info(
                    "voice.elevenlabs_register_ok",
                    attempt=attempt,
                    twiml_len=len(twiml),
                    twiml_preview=twiml[:180],
                )
                _twiml_cache_set(call_sid, twiml)
                return twiml
            log.warning(
                "voice.elevenlabs_not_twiml_retry",
                attempt=attempt,
                content_type=ct,
                preview=twiml[:400],
            )

        raise ValueError(
            "ElevenLabs register-call did not return TwiML XML — check ELEVENLABS_AGENT_ID, "
            "API key, and agent Voice/Advanced audio: μ-law 8000 Hz (Twilio). "
            "See https://elevenlabs.io/docs/eleven-agents/phone-numbers/twilio-integration/register-call"
        )

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
