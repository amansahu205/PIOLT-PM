# app/repositories/sprint_repo.py
from __future__ import annotations

from datetime import UTC, datetime

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import BaseRepository


class SprintRepository(BaseRepository):
    collection_name = "sprint_plans"

    @classmethod
    async def find_draft(cls, db: AsyncIOMotorDatabase) -> dict | None:
        cursor = cls._col(db).find({"status": "draft"}).sort("updated_at", -1).limit(1)
        docs = await cursor.to_list(length=1)
        return docs[0] if docs else None

    @classmethod
    async def find_current(cls, db: AsyncIOMotorDatabase) -> dict | None:
        cursor = cls._col(db).find({"status": "active"}).sort("updated_at", -1).limit(1)
        docs = await cursor.to_list(length=1)
        return docs[0] if docs else None

    @classmethod
    async def insert(cls, plan: dict, db: AsyncIOMotorDatabase) -> dict:
        payload = dict(plan)
        payload.pop("_id", None)
        payload.pop("id", None)
        now = datetime.now(UTC).isoformat()
        payload.setdefault("updated_at", now)
        result = await cls._col(db).insert_one(payload)
        created = await cls._col(db).find_one({"_id": result.inserted_id})
        return cls._with_id(created) if created else {}

    @classmethod
    async def update(cls, plan_id: str, data: dict, db: AsyncIOMotorDatabase) -> dict | None:
        filt: dict
        try:
            filt = {"_id": ObjectId(plan_id)}
        except (InvalidId, TypeError):
            filt = {"id": plan_id}

        merge = dict(data)
        merge["updated_at"] = datetime.now(UTC).isoformat()
        await cls._col(db).update_one(filt, {"$set": merge})
        doc = await cls._col(db).find_one(filt)
        return cls._with_id(doc) if doc else None

    @classmethod
    async def delete_drafts(cls, db: AsyncIOMotorDatabase) -> int:
        r = await cls._col(db).delete_many({"status": "draft"})
        return int(r.deleted_count)

    @classmethod
    async def get_sprint_number(cls, db: AsyncIOMotorDatabase) -> int:
        cursor = (
            cls._col(db)
            .find({"sprint_number": {"$exists": True}})
            .sort("sprint_number", -1)
            .limit(1)
        )
        docs = await cursor.to_list(length=1)
        if not docs or docs[0].get("sprint_number") is None:
            return 1
        return int(docs[0]["sprint_number"]) + 1

    @staticmethod
    def _with_id(doc: dict) -> dict:
        out = dict(doc)
        if "_id" in out:
            out["id"] = str(out.pop("_id"))
        return out
