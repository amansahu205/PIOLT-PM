# app/db/mongo.py
"""
Async MongoDB client via Motor.
Single client instance — reused across all requests.
"""

import certifi
import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

log = structlog.get_logger()

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_mongo() -> None:
    global _client, _db
    # Use certifi CA bundle — Railpack/Docker runtimes often have an empty or stale
    # system store; without this, Atlas TLS can fail with TLSV1_ALERT_INTERNAL_ERROR.
    _client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=10,
        tlsCAFile=certifi.where(),
    )
    _db = _client[settings.MONGODB_DB]
    # Verify connection
    await _client.admin.command("ping")
    log.info("mongo.connected", db=settings.MONGODB_DB)
    # Ensure indexes
    from app.db.indexes import ensure_indexes

    await ensure_indexes(_db)


async def close_mongo() -> None:
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        log.info("mongo.disconnected")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("MongoDB not connected — call connect_mongo() first")
    return _db


def get_collection(name: str):
    return get_db()[name]
