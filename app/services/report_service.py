# app/services/report_service.py
"""F-004 weekly stakeholder status reports."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime
from typing import Any

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.integrations.github_service import GitHubService
from app.integrations.hex_service import HexService
from app.lib.llm import call_ai
from app.lib.prompts import Prompts
from app.lib.retry import llm_retry
from app.models.blocker import BlockerCard
from app.repositories.blocker_repo import BlockerRepository
from app.repositories.report_repo import ReportRepository
from app.services import review_service
from app.services.context_builder import get_context_snapshot

log = structlog.get_logger()


def _stakeholder_emails() -> list[str]:
    raw = settings.STAKEHOLDER_EMAILS or ""
    return [x.strip() for x in raw.split(",") if x.strip()]


def _format_closed_tickets(mon: dict[str, Any], gh: dict[str, Any]) -> str:
    lines: list[str] = []
    for t in mon.get("tickets") or []:
        st = str(t.get("state") or "").lower()
        if st in ("done", "closed", "complete"):
            lines.append(json.dumps(t, default=str))
    if not lines and gh:
        lines.append(f"Commits/PR activity (snapshot): {json.dumps(gh, default=str)[:6000]}")
    return "\n".join(lines) if lines else "(none)"


def _next_week_tickets(mon: dict[str, Any]) -> str:
    tickets = mon.get("tickets") or []
    openish = [
        t
        for t in tickets
        if str(t.get("state") or "").lower() not in ("done", "closed", "complete")
    ]
    return json.dumps(openish[:3], indent=2, default=str)


def _format_blockers(cards: list[BlockerCard]) -> str:
    if not cards:
        return "(none)"
    lines = []
    for b in cards:
        lines.append(f"- {b.engineer}: {b.description} ({b.type})")
    return "\n".join(lines)


@llm_retry(max_retries=2)
async def _call_report_llm(user_prompt: str) -> str:
    return await call_ai(
        system=Prompts.REPORT_SYSTEM,
        user=user_prompt,
        task="general",
        temperature=0.4,
        max_tokens=1500,
    )


class ReportService:
    @staticmethod
    async def get_current(db: AsyncIOMotorDatabase) -> dict[str, Any] | None:
        return await ReportRepository.find_current_week(db)

    @staticmethod
    async def get_history(db: AsyncIOMotorDatabase, n: int = 4) -> list[dict[str, Any]]:
        return await ReportRepository.find_history(db, n=n)

    @staticmethod
    async def generate_report(db: AsyncIOMotorDatabase) -> dict[str, Any]:
        week_id = ReportRepository.iso_week_id()
        if await ReportRepository.find_sent_for_week(db, week_id):
            raise ValueError(
                "Weekly report already finalized for this week — cannot regenerate.",
            )

        ctx = await get_context_snapshot()
        mon = ctx.get("monday") or {}
        gh = ctx.get("github") or {}

        merged, resolved, active = await asyncio.gather(
            GitHubService.get_merged_pull_requests(7),
            BlockerRepository.find_resolved(7, db),
            BlockerRepository.find_active(db),
        )

        week_end = date.today().isoformat()
        user_prompt = Prompts.REPORT_USER.format(
            week_end_date=week_end,
            sprint_name=str(mon.get("sprint_name") or "Current sprint"),
            days_remaining=str(mon.get("days_remaining") or "unknown"),
            closed_tickets=_format_closed_tickets(mon, gh),
            merged_prs=json.dumps(merged, indent=2, default=str)[:8000],
            resolved_blockers=_format_blockers(resolved),
            active_blockers=_format_blockers(active),
            next_week_tickets=_next_week_tickets(mon),
        )

        body = (await _call_report_llm(user_prompt)).strip()
        sprint_data = {
            "week_id": week_id,
            "sprint": mon,
            "merged_pr_count": len(merged),
        }
        hex_url = await HexService.generate_sprint_dashboard(sprint_data)
        if hex_url:
            body = f"{body}\n\n---\nSprint dashboard: {hex_url}"

        subject = f"Engineering weekly — week ending {week_end}"

        await ReportRepository.delete_drafts_for_week(db, week_id)
        saved = await ReportRepository.insert(
            {
                "week_id": week_id,
                "subject": subject,
                "body": body,
                "hex_embed_url": hex_url,
                "status": "draft",
            },
            db,
        )

        await review_service.stage_action(
            action_type="gmail_send",
            title="Review weekly status report email",
            description="Approve to send stakeholder digest",
            data={
                "to": _stakeholder_emails(),
                "subject": subject,
                "body": body,
                "report_id": saved.get("id"),
            },
            reasoning="Generated with Gemini via Lava from project context (GitHub, Monday, blockers).",
            workflow="reports",
            db=db,
        )

        log.info("report.generated", week_id=week_id, report_id=saved.get("id"))
        return saved

    @staticmethod
    async def edit_report(
        report_id: str,
        body: str,
        db: AsyncIOMotorDatabase,
    ) -> dict[str, Any]:
        existing = await ReportRepository.find_by_id(report_id, db)
        if not existing:
            raise ValueError("Report not found")
        if existing.get("status") == "sent":
            raise ValueError("Cannot edit a report that was already sent")
        updated = await ReportRepository.update(report_id, {"body": body}, db)
        if not updated:
            raise ValueError("Failed to update report")
        return updated

    @staticmethod
    async def send_report(report_id: str, db: AsyncIOMotorDatabase) -> dict[str, Any]:
        existing = await ReportRepository.find_by_id(report_id, db)
        if not existing:
            raise ValueError("Report not found")
        if existing.get("status") == "sent":
            raise ValueError("Already sent")

        subject = str(existing.get("subject") or "")
        body = str(existing.get("body") or "")
        to = _stakeholder_emails()

        staged = await review_service.stage_action(
            action_type="gmail_send",
            title="Send weekly status report to stakeholders",
            description="Deliver email to stakeholders from the approved draft",
            data={
                "to": to,
                "subject": subject,
                "body": body,
                "report_id": report_id,
            },
            reasoning="PM triggered send from PilotPM reports UI.",
            workflow="reports",
            db=db,
        )

        await ReportRepository.update(
            report_id,
            {"status": "sent", "sent_at": datetime.now(UTC).isoformat()},
            db,
        )

        return {
            "ok": True,
            "message": "Queued for send",
            "staged_action": staged,
        }
