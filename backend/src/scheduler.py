"""Optimal time slot calculation for auto-scheduling posts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.database import get_db
from src.schemas import ScheduleSettings


async def get_schedule_settings() -> ScheduleSettings:
    db = get_db()
    doc = await db.settings.find_one({"setting_key": "schedule"})
    if doc:
        doc.pop("_id", None)
        doc.pop("setting_key", None)
        doc.pop("updated_at", None)
        return ScheduleSettings(**doc)
    return ScheduleSettings()


async def get_next_available_slots(count: int = 5) -> list[datetime]:
    """Calculate the next available posting slots based on schedule settings."""
    settings = await get_schedule_settings()
    db = get_db()

    now = datetime.now(timezone.utc)
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    slots: list[datetime] = []

    # Look ahead up to 14 days
    for day_offset in range(14):
        date = now + timedelta(days=day_offset)
        day_name = day_names[date.weekday()]
        day_schedule = settings.schedule.get(day_name)

        if not day_schedule or not day_schedule.enabled:
            continue

        for slot in day_schedule.slots:
            slot_time = date.replace(
                hour=slot.hour, minute=slot.minute, second=0, microsecond=0
            )
            if slot_time <= now:
                continue

            # Check if this slot is already taken
            existing = await db.post_queue.count_documents({
                "status": "scheduled",
                "scheduled_time": slot_time,
            })
            if existing > 0:
                continue

            slots.append(slot_time)
            if len(slots) >= count:
                return slots

    return slots


async def auto_schedule_drafts() -> int:
    """Assign time slots to draft posts in queue order. Returns count scheduled."""
    db = get_db()
    settings = await get_schedule_settings()

    drafts = db.post_queue.find(
        {"status": "draft", "scheduled_time": None},
    ).sort("queue_order", 1)

    draft_list = await drafts.to_list(length=settings.daily_cap)
    if not draft_list:
        return 0

    slots = await get_next_available_slots(count=len(draft_list))
    scheduled = 0

    for draft, slot in zip(draft_list, slots):
        await db.post_queue.update_one(
            {"_id": draft["_id"]},
            {
                "$set": {
                    "status": "scheduled",
                    "scheduled_time": slot,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        scheduled += 1

    return scheduled
