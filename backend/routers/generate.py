"""AI content generation endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, HTTPException

from routers.auth import require_auth
from src.schemas import GenerateRequest, ImproveRequest
from src.ai_generator import generate_posts, improve_post

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generate", tags=["generate"])


@router.post("")
async def generate(request: Request, body: GenerateRequest):
    require_auth(request)
    try:
        variants = await generate_posts(
            topic=body.topic,
            tone=body.tone.value,
            post_type=body.post_type.value,
            additional_context=body.additional_context,
        )
        return {"variants": variants}
    except Exception as e:
        logger.error(f"AI generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@router.post("/improve")
async def improve(request: Request, body: ImproveRequest):
    require_auth(request)
    try:
        improved = await improve_post(
            content=body.content,
            instructions=body.instructions,
        )
        return {"improved": improved}
    except Exception as e:
        logger.error(f"AI improve failed: {e}")
        raise HTTPException(status_code=500, detail=f"Improve failed: {e}")
