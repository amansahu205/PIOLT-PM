# app/repositories/blocker_repo.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.blocker import BlockerCard
from app.repositories.base import BaseRepository


class BlockerRepository(BaseRepository):
    collection_name = "blockers"

    @staticmethod
    def _to_card(doc: dict) -> BlockerCard:
        d = dict(doc)
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
        return BlockerCard.model_validate(d)

    @classmethod
    async def find_active(cls, db: AsyncIOMotorDatabase) -> list[BlockerCard]:
        cursor = cls._col(db).find({"status": "active"}).sort("detected_at", -1)
        out: list[BlockerCard] = []
        async for doc in cursor:
            out.append(cls._to_card(doc))
        return out

    @classmethod
    async def find_resolved(cls, days: int, db: AsyncIOMotorDatabase) -> list[BlockerCard]:
        since = datetime.now(UTC) - timedelta(days=days)
        cursor = cls._col(db).find(
            {
                "status": {"$in": ["dismissed", "resolved"]},
                "updated_at": {"$gte": since},
            }
        ).sort("updated_at", -1)
        out: list[BlockerCard] = []
        async for doc in cursor:
            out.append(cls._to_card(doc))
        return out

    @classmethod
    async def find_by_id(cls, blocker_id: str, db: AsyncIOMotorDatabase) -> BlockerCard | None:
        doc = None
        try:
            doc = await cls._col(db).find_one({"_id": ObjectId(blocker_id)})
        except (InvalidId, TypeError):
            doc = await cls._col(db).find_one({"id": blocker_id})
        if not doc:
            return None
        return cls._to_card(doc)

    @classmethod
    async def insert(cls, blocker: BlockerCard, db: AsyncIOMotorDatabase) -> BlockerCard:
        data = blocker.model_dump(exclude={"id"}, exclude_none=True)
        if data.get("detected_at") and data["detected_at"].tzinfo is None:
            data["detected_at"] = data["detected_at"].replace(tzinfo=UTC)
        now = datetime.now(UTC)
        if not data.get("updated_at"):
            data["updated_at"] = now
        result = await cls._col(db).insert_one(data)
        created = await cls._col(db).find_one({"_id": result.inserted_id})
        return cls._to_card(created)

    @classmethod
    async def update_status(
        cls,
        blocker_id: str,
        status: str,
        dismissed_reason: str | None,
        db: AsyncIOMotorDatabase,
    ) -> BlockerCard | None:
        filt: dict
        try:
            filt = {"_id": ObjectId(blocker_id)}
        except (InvalidId, TypeError):
            filt = {"id": blocker_id}

        update = {
            "$set": {
                "status": status,
                "dismissed_reason": dismissed_reason,
                "updated_at": datetime.now(UTC),
            }
        }
        await cls._col(db).update_one(filt, update)
        doc = await cls._col(db).find_one(filt)
        return cls._to_card(doc) if doc else None
