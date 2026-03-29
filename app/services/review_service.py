# app/services/review_service.py
"""Review queue staging (F-011 subset for standup)."""

from __future__ import annotations

from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

import structlog

log = structlog.get_logger()


async def stage_action(
    action_type: str,
    title: str,
    description: str,
    data: dict,
    reasoning: str | list,
    workflow: str,
    db: AsyncIOMotorDatabase,
) -> dict:
    """Create a pending review action in MongoDB."""
    doc = {
        "type": action_type,
        "title": title,
        "description": description,
        "data": data,
        "reasoning": reasoning,
        "workflow": workflow,
        "status": "pending",
        "created_at": datetime.now(UTC).isoformat(),
    }
    col = db["review_queue"]
    result = await col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    log.info("review.staged", action_type=action_type, workflow=workflow, id=doc["_id"])
    return doc


async def list_pending(db: AsyncIOMotorDatabase) -> list[dict]:
    """Return pending review_queue items (newest first)."""
    col = db["review_queue"]
    out: list[dict] = []
    async for doc in col.find({"status": "pending"}).sort("created_at", -1):
        d = dict(doc)
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
        out.append(d)
    return out


async def approve_action(action_id: str, db: AsyncIOMotorDatabase) -> dict | None:
    """Mark a review item approved."""
    try:
        oid = ObjectId(action_id)
    except Exception:
        return None
    col = db["review_queue"]
    now = datetime.now(UTC).isoformat()
    result = await col.update_one(
        {"_id": oid, "status": "pending"},
        {"$set": {"status": "approved", "resolved_at": now}},
    )
    if result.matched_count == 0:
        return None
    doc = await col.find_one({"_id": oid})
    if not doc:
        return None
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    log.info("review.approved", action_id=action_id)
    return d


async def reject_action(
    action_id: str,
    reason: str,
    db: AsyncIOMotorDatabase,
) -> dict | None:
    """Mark a review item rejected."""
    try:
        oid = ObjectId(action_id)
    except Exception:
        return None
    col = db["review_queue"]
    now = datetime.now(UTC).isoformat()
    result = await col.update_one(
        {"_id": oid, "status": "pending"},
        {"$set": {"status": "rejected", "resolved_at": now, "reject_reason": reason}},
    )
    if result.matched_count == 0:
        return None
    doc = await col.find_one({"_id": oid})
    if not doc:
        return None
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    log.info("review.rejected", action_id=action_id)
    return d


def format_digest_for_slack(digest: dict) -> str:
    lines = [f"*PilotPM Standup — {digest.get('generated_at', 'today')}*\n"]
    for eng in digest.get("digest", []):
        emoji = {"on_track": "🟢", "blocked": "🔴", "check_in": "🟡"}.get(eng["status"], "⚪")
        lines.append(f"{emoji} *{eng['engineer']}*: {eng.get('did', 'no activity')}")
        if eng.get("blocker"):
            lines.append(f"   Blocked: {eng['blocker']}")
    lines.append(f"\n_{digest.get('summary', '')}_")
    return "\n".join(lines)
