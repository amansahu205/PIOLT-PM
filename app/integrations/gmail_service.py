# app/integrations/gmail_service.py
"""Stakeholder email delivery — SMTP (Gmail-compatible) when configured."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

import structlog

from app.config import settings

log = structlog.get_logger()


def _send_sync(to_emails: list[str], subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = ", ".join(to_emails)
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


async def send_email(to_emails: list[str], subject: str, body: str) -> bool:
    """
    Send email to recipients. Uses SMTP_* from settings when set; otherwise no-op.
    """
    cleaned = [e.strip() for e in to_emails if e and e.strip()]
    if not cleaned:
        log.warning("gmail.no_recipients")
        return False

    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        log.warning("gmail.smtp_not_configured")
        return False

    try:
        await asyncio.to_thread(_send_sync, cleaned, subject, body)
        log.info("gmail.sent", recipients=len(cleaned))
        return True
    except Exception as e:
        log.warning("gmail.send_failed", error=str(e))
        return False
