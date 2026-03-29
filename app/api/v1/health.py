from fastapi import APIRouter

from app.db.mongo import get_db

router = APIRouter()


@router.get("/health")
async def health():
    try:
        get_db()
        mongo_ok = True
    except RuntimeError:
        mongo_ok = False
    return {"status": "ok", "gemini_via_lava": True, "mongo": mongo_ok}
