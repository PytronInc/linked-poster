"""Pydantic v2 models for the LinkedIn AutoPoster."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PostStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class PostType(str, Enum):
    text = "text"
    image = "image"


class Tone(str, Enum):
    professional = "professional"
    casual = "casual"
    thought_leadership = "thought-leadership"
    storytelling = "storytelling"


class AIPostType(str, Enum):
    text = "text"
    insight = "insight"
    article_share = "article_share"
    poll_intro = "poll_intro"


# --- Post Queue ---

class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000)
    post_type: PostType = PostType.text
    status: PostStatus = PostStatus.draft
    scheduled_time: Optional[datetime] = None


class PostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=3000)
    post_type: Optional[PostType] = None
    status: Optional[PostStatus] = None
    scheduled_time: Optional[datetime] = None


class PostReorder(BaseModel):
    post_ids: list[str]


# --- AI Generation ---

class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    tone: Tone = Tone.professional
    post_type: AIPostType = AIPostType.text
    additional_context: Optional[str] = None


class ImproveRequest(BaseModel):
    content: str = Field(..., min_length=1)
    instructions: Optional[str] = None


# --- Settings ---

class TimeSlot(BaseModel):
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)


class DaySchedule(BaseModel):
    enabled: bool = True
    slots: list[TimeSlot] = []


class ScheduleSettings(BaseModel):
    timezone: str = "UTC"
    daily_cap: int = Field(10, ge=1, le=50)
    schedule: dict[str, DaySchedule] = Field(default_factory=lambda: {
        "monday": DaySchedule(slots=[TimeSlot(hour=9, minute=0), TimeSlot(hour=12, minute=30)]),
        "tuesday": DaySchedule(slots=[TimeSlot(hour=9, minute=0), TimeSlot(hour=12, minute=30)]),
        "wednesday": DaySchedule(slots=[TimeSlot(hour=9, minute=0), TimeSlot(hour=12, minute=30)]),
        "thursday": DaySchedule(slots=[TimeSlot(hour=9, minute=0), TimeSlot(hour=12, minute=30)]),
        "friday": DaySchedule(slots=[TimeSlot(hour=9, minute=0), TimeSlot(hour=12, minute=30)]),
        "saturday": DaySchedule(enabled=False, slots=[]),
        "sunday": DaySchedule(enabled=False, slots=[]),
    })


class AISettings(BaseModel):
    provider: str = "openai"
    default_tone: Tone = Tone.professional
    default_post_type: AIPostType = AIPostType.text


# --- Auth ---

class LoginRequest(BaseModel):
    password: str
