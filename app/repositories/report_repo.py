# app/repositories/report_repo.py
from __future__ import annotations

from datetime import UTC, date, datetime

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository):
    collection_name = "status_reports"

    @staticmethod
    def iso_week_id() -> str:
        d = date.today()
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"

    @staticmethod
    def _with_id(doc: dict | None) -> dict | None:
        if not doc:
            return None
        out = dict(doc)
        if "_id" in out:
            out["id"] = str(out.pop("_id"))
        return out

    @classmethod
    async def find_current_week(cls, db: AsyncIOMotorDatabase) -> dict | None:
        wid = cls.iso_week_id()
        cursor = (
            cls._col(db)
            .find({"week_id": wid})
            .sort("updated_at", -1)
            .limit(1)
        )
        docs = await cursor.to_list(length=1)
        return cls._with_id(docs[0]) if docs else None

    @classmethod
    async def find_sent_for_week(cls, db: AsyncIOMotorDatabase, week_id: str) -> dict | None:
        doc = await cls._col(db).find_one({"week_id": week_id, "status": "sent"})
        return cls._with_id(doc)

    @classmethod
    async def find_history(cls, db: AsyncIOMotorDatabase, n: int = 4) -> list[dict]:
        cursor = cls._col(db).find({}).sort("updated_at", -1).limit(n)
        out: list[dict] = []
        async for doc in cursor:
            wid = cls._with_id(doc)
            if wid:
                out.append(wid)
        return out

    @classmethod
    async def find_by_id(cls, report_id: str, db: AsyncIOMotorDatabase) -> dict | None:
        doc = None
        try:
            doc = await cls._col(db).find_one({"_id": ObjectId(report_id)})
        except (InvalidId, TypeError):
            doc = await cls._col(db).find_one({"id": report_id})
        return cls._with_id(doc)

    @classmethod
    async def insert(cls, report: dict, db: AsyncIOMotorDatabase) -> dict:
        payload = dict(report)
        payload.pop("_id", None)
        payload.pop("id", None)
        now = datetime.now(UTC).isoformat()
        payload.setdefault("created_at", now)
        payload.setdefault("updated_at", now)
        result = await cls._col(db).insert_one(payload)
        created = await cls._col(db).find_one({"_id": result.inserted_id})
        return cls._with_id(created) or {}

    @classmethod
    async def update(cls, report_id: str, data: dict, db: AsyncIOMotorDatabase) -> dict | None:
        filt: dict
        try:
            filt = {"_id": ObjectId(report_id)}
        except (InvalidId, TypeError):
            filt = {"id": report_id}

        merge = dict(data)
        merge["updated_at"] = datetime.now(UTC).isoformat()
        await cls._col(db).update_one(filt, {"$set": merge})
        doc = await cls._col(db).find_one(filt)
        return cls._with_id(doc)

    @classmethod
    async def delete_drafts_for_week(cls, db: AsyncIOMotorDatabase, week_id: str) -> int:
        r = await cls._col(db).delete_many({"week_id": week_id, "status": "draft"})
        return int(r.deleted_count)
