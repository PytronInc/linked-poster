"""Schedule and AI preferences settings."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from routers.auth import require_auth
from src.database import get_db
from src.schemas import ScheduleSettings, AISettings

router = APIRouter(prefix="/api/settings", tags=["settings"])


async def _get_setting(key: str, default: dict) -> dict:
    db = get_db()
    doc = await db.settings.find_one({"setting_key": key})
    if doc:
        doc.pop("_id", None)
        doc.pop("setting_key", None)
        doc.pop("updated_at", None)
        return doc
    return default


async def _set_setting(key: str, data: dict) -> dict:
    db = get_db()
    await db.settings.update_one(
        {"setting_key": key},
        {"$set": {**data, "setting_key": key, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return data


@router.get("/schedule")
async def get_schedule(request: Request):
    require_auth(request)
    defaults = ScheduleSettings().model_dump()
    return await _get_setting("schedule", defaults)


@router.put("/schedule")
async def update_schedule(request: Request, body: ScheduleSettings):
    require_auth(request)
    return await _set_setting("schedule", body.model_dump())


@router.get("/ai")
async def get_ai_settings(request: Request):
    require_auth(request)
    defaults = AISettings().model_dump()
    return await _get_setting("ai", defaults)


@router.put("/ai")
async def update_ai_settings(request: Request, body: AISettings):
    require_auth(request)
    return await _set_setting("ai", body.model_dump())
