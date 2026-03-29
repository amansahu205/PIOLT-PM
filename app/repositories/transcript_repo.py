# app/repositories/transcript_repo.py
from __future__ import annotations

from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import BaseRepository


class TranscriptRepository(BaseRepository):
    collection_name = "call_transcripts"

    @classmethod
    async def log_call_start(
        cls,
        call_sid: str,
        caller: str,
        db: AsyncIOMotorDatabase,
    ) -> dict:
        """
        Idempotent per CallSid — Twilio trial accounts (and some gathers) may POST the voice
        webhook more than once for the same call; duplicate inserts must not fail.
        """
        now = datetime.now(UTC).isoformat()
        await cls._col(db).update_one(
            {"call_sid": call_sid},
            {
                "$setOnInsert": {
                    "call_sid": call_sid,
                    "caller": caller,
                    "started_at": now,
                    "called_at": now,
                    "status": "in_progress",
                }
            },
            upsert=True,
        )
        doc = await cls._col(db).find_one({"call_sid": call_sid})
        if not doc:
            return {}
        out = dict(doc)
        if "_id" in out:
            out["id"] = str(out.pop("_id"))
        return out

    @classmethod
    async def log_call_end(
        cls,
        call_sid: str,
        duration: int | float | None,
        db: AsyncIOMotorDatabase,
    ) -> bool:
        ended = datetime.now(UTC).isoformat()
        update = {
            "$set": {
                "ended_at": ended,
                "status": "completed",
                "duration_seconds": float(duration) if duration is not None else None,
            }
        }
        r = await cls._col(db).update_one({"call_sid": call_sid}, update)
        return r.matched_count > 0

    @classmethod
    async def find_recent(cls, db: AsyncIOMotorDatabase, n: int = 10) -> list[dict]:
        cursor = cls._col(db).find({}).sort("called_at", -1).limit(n)
        out: list[dict] = []
        async for doc in cursor:
            d = dict(doc)
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
            out.append(d)
        return out
