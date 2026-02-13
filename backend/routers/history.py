"""Published posts history."""

from __future__ import annotations

from bson import Binary
from fastapi import APIRouter, Request

from routers.auth import require_auth
from src.database import get_db

router = APIRouter(prefix="/api/history", tags=["history"])


def _serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("image_data"), (bytes, Binary)):
        doc["has_image"] = True
        del doc["image_data"]
    else:
        doc["has_image"] = bool(doc.get("image_urn"))
    for field in ("scheduled_time", "published_at", "created_at", "updated_at"):
        if doc.get(field):
            doc[field] = doc[field].isoformat()
    return doc


@router.get("")
async def list_history(request: Request, skip: int = 0, limit: int = 50):
    require_auth(request)
    db = get_db()
    cursor = (
        db.post_queue.find(
            {"status": {"$in": ["published", "failed"]}},
            {"image_data": 0},
        )
        .sort("published_at", -1)
        .skip(skip)
        .limit(limit)
    )
    posts = [_serialize(doc) async for doc in cursor]
    total = await db.post_queue.count_documents(
        {"status": {"$in": ["published", "failed"]}}
    )
    return {"posts": posts, "total": total}
