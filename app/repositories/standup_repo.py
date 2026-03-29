# app/repositories/standup_repo.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import BaseRepository


def _standup_window_start() -> datetime:
    """Most recent 6:00 UTC boundary (standup day start)."""
    now = datetime.now(UTC)
    six = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if now < six:
        six = six - timedelta(days=1)
    return six


class StandupRepository(BaseRepository):
    collection_name = "standup_digests"

    @classmethod
    async def find_today(cls, db: AsyncIOMotorDatabase) -> dict | None:
        """Digest with generated_at after today's 6am (UTC window)."""
        start = _standup_window_start()
        # ISO strings sort correctly for comparison when stored consistently
        cursor = (
            cls._col(db)
            .find({"generated_at": {"$gte": start.isoformat()}})
            .sort("generated_at", -1)
            .limit(1)
        )
        docs = await cursor.to_list(length=1)
        return docs[0] if docs else None

    @classmethod
    async def insert(cls, digest: dict, db: AsyncIOMotorDatabase) -> dict:
        payload = dict(digest)
        result = await cls._col(db).insert_one(payload)
        payload["_id"] = str(result.inserted_id)
        return payload

    @classmethod
    async def find_recent(cls, db: AsyncIOMotorDatabase, n: int = 7) -> list[dict]:
        cursor = cls._col(db).find({}).sort("generated_at", -1).limit(n)
        return await cursor.to_list(length=n)
