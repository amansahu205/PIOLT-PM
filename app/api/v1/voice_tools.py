# app/api/v1/voice_tools.py
"""
ElevenLabs Client Tool webhooks — called during a live voice call when the agent
decides to execute a tool (send_email, schedule_meeting).

Configure in ElevenLabs dashboard → your Agent → Tools → Server Tool:
  Tool name:   send_email          URL: https://<your-backend>/api/v1/voice/tools/send_email
  Tool name:   schedule_meeting    URL: https://<your-backend>/api/v1/voice/tools/schedule_meeting

ElevenLabs POSTs:
  { "tool_call_id": "...", "parameters": { ...tool params... } }

We return:
  { "result": "human-readable confirmation string" }

The agent reads the result string aloud to the caller.
"""

from __future__ import annotations

import hmac
import hashlib
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import settings
from app.integrations.gmail_service import send_email
from app.integrations.calendar_service import create_event

log = structlog.get_logger()
router = APIRouter()


# ── Request/response models ───────────────────────────────────────────────────

class ToolCallRequest(BaseModel):
    tool_call_id: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    result: str


# ── Signature verification (optional but recommended) ─────────────────────────

def _verify_secret(request: Request, body: bytes) -> None:
    """
    If ELEVENLABS_TOOL_SECRET is set, verify the X-ElevenLabs-Signature header.
    Skip verification in dev or if secret is not configured.
    """
    secret = (settings.ELEVENLABS_TOOL_SECRET or "").strip()
    if not secret:
        return  # No secret configured — skip (fine for hackathon)

    sig_header = request.headers.get("X-ElevenLabs-Signature", "")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig_header, f"sha256={expected}"):
        raise HTTPException(status_code=401, detail="Invalid tool webhook signature")


# ── send_email tool ───────────────────────────────────────────────────────────

class SendEmailParams(BaseModel):
    recipient_email: str = ""
    subject: str = "Message from PilotPM"
    body: str = ""
    # ElevenLabs may send extras — ignore them
    model_config = {"extra": "ignore"}


@router.post("/tools/send_email", response_model=ToolCallResponse)
async def tool_send_email(request: Request):
    """
    ElevenLabs calls this when the caller says something like:
    'Send a status update to the team' or 'Email [name] about the blocker'.
    """
    raw = await request.body()
    _verify_secret(request, raw)

    payload = ToolCallRequest.model_validate_json(raw)
    params = SendEmailParams.model_validate(payload.parameters)

    log.info(
        "voice_tool.send_email",
        tool_call_id=payload.tool_call_id,
        recipient=params.recipient_email,
        subject=params.subject,
    )

    if not params.recipient_email:
        return ToolCallResponse(result="I need a recipient email address. Who should I send it to?")

    if not params.body:
        return ToolCallResponse(result="I need a message body. What should the email say?")

    # Use STAKEHOLDER_EMAILS as fallback list when caller says "the team" / "stakeholders"
    recipients = [params.recipient_email]
    if params.recipient_email.lower() in ("team", "stakeholders", "the team"):
        stakeholders = [e.strip() for e in settings.STAKEHOLDER_EMAILS.split(",") if e.strip()]
        if stakeholders:
            recipients = stakeholders
        else:
            return ToolCallResponse(
                result="STAKEHOLDER_EMAILS is not configured. Please set it in your .env file."
            )

    success = await send_email(recipients, params.subject, params.body)
    if success:
        names = ", ".join(recipients)
        return ToolCallResponse(result=f"Done! Email sent to {names} with subject '{params.subject}'.")
    else:
        return ToolCallResponse(
            result="Email could not be sent — SMTP is not configured. Check SMTP_HOST, SMTP_USER, and SMTP_PASSWORD."
        )


# ── schedule_meeting tool ─────────────────────────────────────────────────────

class ScheduleMeetingParams(BaseModel):
    title: str = "Meeting"
    attendees: list[str] = Field(default_factory=list)
    start_time: str = ""  # ISO8601 or empty (defaults to next hour)
    duration_minutes: int = 30
    description: str = ""
    model_config = {"extra": "ignore"}


@router.post("/tools/schedule_meeting", response_model=ToolCallResponse)
async def tool_schedule_meeting(request: Request):
    """
    ElevenLabs calls this when the caller says something like:
    'Schedule a sprint planning meeting tomorrow at 2pm' or
    'Book a call with the team on Friday'.
    """
    raw = await request.body()
    _verify_secret(request, raw)

    payload = ToolCallRequest.model_validate_json(raw)
    params = ScheduleMeetingParams.model_validate(payload.parameters)

    log.info(
        "voice_tool.schedule_meeting",
        tool_call_id=payload.tool_call_id,
        title=params.title,
        attendees=params.attendees,
        start_time=params.start_time,
    )

    # If no attendees, use stakeholder list
    attendees = params.attendees
    if not attendees:
        stakeholders = [e.strip() for e in settings.STAKEHOLDER_EMAILS.split(",") if e.strip()]
        attendees = stakeholders

    result = await create_event(
        title=params.title,
        attendees=attendees,
        start_time=params.start_time,
        duration_minutes=params.duration_minutes,
        description=params.description or f"Scheduled via PilotPM voice agent.",
    )

    if result.get("success"):
        return ToolCallResponse(result=result["message"])
    else:
        err = result.get("error", "unknown error")
        return ToolCallResponse(
            result=f"Could not create the meeting: {err}. Please check your Google Calendar or SMTP configuration."
        )
