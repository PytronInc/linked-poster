"""Post queue CRUD, image upload, publish-now, and reorder."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from bson import ObjectId, Binary
from fastapi import APIRouter, Request, HTTPException, UploadFile, File

from routers.auth import require_auth
from src.database import get_db
from src.schemas import PostCreate, PostUpdate, PostReorder
from src.token_store import get_tokens
from src.linkedin_api import (
    publish_text_post,
    initialize_image_upload,
    upload_image_binary,
    publish_image_post,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("image_data"), (bytes, Binary)):
        doc["has_image"] = True
        del doc["image_data"]
    else:
        doc["has_image"] = bool(doc.get("image_urn"))
    if doc.get("scheduled_time"):
        doc["scheduled_time"] = doc["scheduled_time"].isoformat()
    if doc.get("published_at"):
        doc["published_at"] = doc["published_at"].isoformat()
    if doc.get("created_at"):
        doc["created_at"] = doc["created_at"].isoformat()
    if doc.get("updated_at"):
        doc["updated_at"] = doc["updated_at"].isoformat()
    return doc


@router.get("/queue")
async def list_queue(request: Request):
    require_auth(request)
    db = get_db()
    cursor = db.post_queue.find(
        {"status": {"$in": ["draft", "scheduled"]}},
        {"image_data": 0},
    ).sort("queue_order", 1)
    posts = [_serialize(doc) async for doc in cursor]
    return {"posts": posts}


@router.post("")
async def create_post(request: Request, body: PostCreate):
    require_auth(request)
    db = get_db()
    now = datetime.now(timezone.utc)

    # Get max queue_order
    last = await db.post_queue.find_one(
        {"status": {"$in": ["draft", "scheduled"]}},
        sort=[("queue_order", -1)],
    )
    next_order = (last.get("queue_order", 0) + 1) if last else 1

    doc = {
        "content": body.content,
        "post_type": body.post_type.value,
        "status": body.status.value,
        "scheduled_time": body.scheduled_time,
        "queue_order": next_order,
        "image_urn": None,
        "linkedin_post_id": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.post_queue.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


@router.put("/reorder")
async def reorder_queue(request: Request, body: PostReorder):
    require_auth(request)
    db = get_db()
    for i, pid in enumerate(body.post_ids):
        await db.post_queue.update_one(
            {"_id": ObjectId(pid)},
            {"$set": {"queue_order": i + 1, "updated_at": datetime.now(timezone.utc)}},
        )
    return {"ok": True}


@router.put("/{post_id}")
async def update_post(request: Request, post_id: str, body: PostUpdate):
    require_auth(request)
    db = get_db()

    update_fields = body.model_dump(exclude_none=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Convert enum values
    if "post_type" in update_fields:
        update_fields["post_type"] = update_fields["post_type"].value
    if "status" in update_fields:
        update_fields["status"] = update_fields["status"].value

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.post_queue.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": update_fields},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")

    doc = await db.post_queue.find_one({"_id": ObjectId(post_id)}, {"image_data": 0})
    return _serialize(doc)


@router.delete("/{post_id}")
async def delete_post(request: Request, post_id: str):
    require_auth(request)
    db = get_db()
    result = await db.post_queue.delete_one({"_id": ObjectId(post_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"ok": True}


@router.post("/{post_id}/image")
async def upload_image(request: Request, post_id: str, file: UploadFile = File(...)):
    require_auth(request)
    db = get_db()

    post = await db.post_queue.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    image_data = await file.read()
    if len(image_data) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 10 MB)")

    await db.post_queue.update_one(
        {"_id": ObjectId(post_id)},
        {
            "$set": {
                "image_data": Binary(image_data),
                "image_content_type": file.content_type,
                "post_type": "image",
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return {"ok": True, "has_image": True}


@router.delete("/{post_id}/image")
async def delete_image(request: Request, post_id: str):
    require_auth(request)
    db = get_db()
    result = await db.post_queue.update_one(
        {"_id": ObjectId(post_id)},
        {
            "$set": {
                "post_type": "text",
                "updated_at": datetime.now(timezone.utc),
            },
            "$unset": {
                "image_data": "",
                "image_content_type": "",
                "image_urn": "",
            },
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"ok": True}


@router.post("/{post_id}/publish-now")
async def publish_now(request: Request, post_id: str):
    require_auth(request)
    db = get_db()

    post = await db.post_queue.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["status"] in ("published", "publishing"):
        raise HTTPException(status_code=400, detail=f"Post is already {post['status']}")

    tokens = await get_tokens()
    if not tokens:
        raise HTTPException(status_code=400, detail="LinkedIn not connected")

    access_token = tokens["access_token"]
    person_urn = tokens["person_urn"]

    # Mark as publishing
    await db.post_queue.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"status": "publishing", "updated_at": datetime.now(timezone.utc)}},
    )

    try:
        if post.get("image_data"):
            # 3-step image upload
            init = await initialize_image_upload(access_token, person_urn)
            await upload_image_binary(
                init["upload_url"],
                access_token,
                post["image_data"],
                post.get("image_content_type", "image/jpeg"),
            )
            result = await publish_image_post(
                access_token, person_urn, post["content"], init["image_urn"]
            )
        else:
            result = await publish_text_post(access_token, person_urn, post["content"])

        await db.post_queue.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$set": {
                    "status": "published",
                    "linkedin_post_id": result.get("post_id"),
                    "published_at": datetime.now(timezone.utc),
                    "error": None,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$unset": {"image_data": ""},
            },
        )
        return {"ok": True, "post_id": result.get("post_id")}

    except Exception as e:
        logger.error(f"Publish failed for {post_id}: {e}")
        await db.post_queue.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        raise HTTPException(status_code=500, detail=str(e))
