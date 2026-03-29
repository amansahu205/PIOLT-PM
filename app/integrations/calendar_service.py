# app/integrations/calendar_service.py
"""
Google Calendar event creation.
Primary: Google Calendar REST API via service account (GOOGLE_SERVICE_ACCOUNT_JSON).
Fallback: ICS attachment via SMTP email (works without any Google setup).
"""

from __future__ import annotations

import base64
import json
import uuid
from datetime import UTC, datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx
import structlog

from app.config import settings

log = structlog.get_logger()

_CALENDAR_API = "https://www.googleapis.com/calendar/v3"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPES = "https://www.googleapis.com/auth/calendar"


def _parse_sa_json() -> dict | None:
    raw = (settings.GOOGLE_SERVICE_ACCOUNT_JSON or "").strip()
    if not raw:
        return None
    try:
        # Accept raw JSON or base64-encoded JSON
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return json.loads(base64.b64decode(raw).decode())
    except Exception as e:
        log.warning("calendar.sa_json_parse_failed", error=str(e))
        return None


async def _get_access_token(sa: dict) -> str | None:
    """Mint a short-lived access token from a service account."""
    try:
        import time

        import jwt  # PyJWT — available via python-jose transitive dep or standalone

        now = int(time.time())
        claim = {
            "iss": sa["client_email"],
            "scope": _SCOPES,
            "aud": _TOKEN_URL,
            "iat": now,
            "exp": now + 3600,
        }
        signed = jwt.encode(claim, sa["private_key"], algorithm="RS256")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _TOKEN_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": signed,
                },
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
    except Exception as e:
        log.warning("calendar.token_failed", error=str(e))
        return None


def _parse_datetime(value: str, default_offset_hours: int = 1) -> datetime:
    """Parse ISO8601 or fall back to next clean hour."""
    if not value:
        base = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        return base + timedelta(hours=default_offset_hours)
    try:
        s = value.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except Exception:
        base = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        return base + timedelta(hours=default_offset_hours)


def _build_ics(title: str, start: datetime, end: datetime, attendees: list[str], description: str) -> str:
    uid = str(uuid.uuid4())
    fmt = "%Y%m%dT%H%M%SZ"
    now_str = datetime.now(UTC).strftime(fmt)
    start_str = start.astimezone(UTC).strftime(fmt)
    end_str = end.astimezone(UTC).strftime(fmt)

    attendee_lines = "\n".join(
        f"ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=NEEDS-ACTION;RSVP=TRUE:mailto:{e.strip()}"
        for e in attendees
        if e.strip()
    )
    organizer = f"ORGANIZER;CN=PilotPM:mailto:{settings.SMTP_USER or 'noreply@pilotpm.ai'}"
    desc_line = "DESCRIPTION:" + description.replace("\n", "\\n")

    return "\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PilotPM//Voice Agent//EN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_str}",
        f"DTSTART:{start_str}",
        f"DTEND:{end_str}",
        f"SUMMARY:{title}",
        desc_line,
        organizer,
        attendee_lines,
        "END:VEVENT",
        "END:VCALENDAR",
    ])


async def _send_ics_email(
    title: str,
    attendees: list[str],
    start: datetime,
    end: datetime,
    description: str,
) -> dict[str, Any]:
    """Fallback: send calendar invite as ICS email attachment."""
    import asyncio
    import smtplib

    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return {"success": False, "error": "SMTP not configured — set SMTP_HOST/USER/PASSWORD"}

    ics_content = _build_ics(title, start, end, attendees, description)

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Meeting Invite: {title}"
    msg["From"] = settings.SMTP_USER
    msg["To"] = ", ".join(e.strip() for e in attendees if e.strip())

    body = MIMEText(
        f"You have been invited to: {title}\n"
        f"When: {start.strftime('%A, %B %d %Y at %H:%M UTC')}\n"
        f"Duration: {int((end - start).total_seconds() // 60)} minutes\n\n"
        f"{description}",
        "plain",
    )
    msg.attach(body)

    ics_part = MIMEApplication(ics_content.encode(), _subtype="ics")
    ics_part.add_header("Content-Disposition", "attachment", filename="invite.ics")
    ics_part.add_header("Content-Type", 'text/calendar; method="REQUEST"')
    msg.attach(ics_part)

    def _send() -> None:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
            s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)

    try:
        await asyncio.to_thread(_send)
        log.info("calendar.ics_sent", title=title, attendees=len(attendees))
        return {
            "success": True,
            "method": "ics_email",
            "message": f"Calendar invite for '{title}' sent to {', '.join(attendees)}",
        }
    except Exception as e:
        log.warning("calendar.ics_send_failed", error=str(e))
        return {"success": False, "error": str(e)}


async def create_event(
    *,
    title: str,
    attendees: list[str],
    start_time: str = "",
    duration_minutes: int = 30,
    description: str = "",
) -> dict[str, Any]:
    """
    Create a calendar event. Returns dict with success + link/message.

    Primary path: Google Calendar API (requires GOOGLE_SERVICE_ACCOUNT_JSON).
    Fallback path: ICS invite email via SMTP.
    """
    start = _parse_datetime(start_time)
    end = start + timedelta(minutes=duration_minutes)

    sa = _parse_sa_json()
    if not sa:
        log.info("calendar.no_sa_json_using_ics_fallback")
        return await _send_ics_email(title, attendees, start, end, description)

    token = await _get_access_token(sa)
    if not token:
        return await _send_ics_email(title, attendees, start, end, description)

    event_body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        "attendees": [{"email": e.strip()} for e in attendees if e.strip()],
        "conferenceData": {
            "createRequest": {
                "requestId": f"pilotpm-{uuid.uuid4().hex[:8]}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    calendar_id = settings.GOOGLE_CALENDAR_ID or "primary"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_CALENDAR_API}/calendars/{calendar_id}/events",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=event_body,
                params={"conferenceDataVersion": "1"},
            )
            resp.raise_for_status()
            data = resp.json()

        html_link = data.get("htmlLink", "")
        entry_points = data.get("conferenceData", {}).get("entryPoints", [])
        meet_link = next((ep.get("uri", "") for ep in entry_points if ep.get("entryPointType") == "video"), "")

        log.info("calendar.event_created", title=title, link=html_link)
        return {
            "success": True,
            "method": "google_calendar",
            "event_link": html_link,
            "meet_link": meet_link,
            "message": (
                f"Meeting '{title}' created for {start.strftime('%A %B %d at %H:%M UTC')}."
                + (f" Google Meet: {meet_link}" if meet_link else "")
            ),
        }
    except Exception as e:
        log.warning("calendar.api_failed_fallback_ics", error=str(e))
        return await _send_ics_email(title, attendees, start, end, description)
