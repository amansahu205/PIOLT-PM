# app/repositories/base.py
"""
Base async repository with common collection access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase


class BaseRepository:
    collection_name: str = ""

    @classmethod
    def _col(cls, db: AsyncIOMotorDatabase):
        return db[cls.collection_name]
