"""Cron script: check queue and publish due posts.

Runs every 5 minutes via cron. Also handles proactive token refresh.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import os

# Ensure the app root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from src.database import get_db, close_client  # noqa: E402
from src.token_store import get_tokens, update_tokens  # noqa: E402
from src.linkedin_oauth import refresh_access_token  # noqa: E402
from src.linkedin_api import (  # noqa: E402
    publish_text_post,
    initialize_image_upload,
    upload_image_binary,
    publish_image_post,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAILY_CAP = 10


async def _refresh_token_if_needed(tokens: dict) -> dict:
    """Proactively refresh token if within 7 days of expiry."""
    from datetime import datetime, timezone, timedelta

    if not tokens.get("expires_at") or not tokens.get("refresh_token"):
        return tokens

    days_until_expiry = (tokens["expires_at"] - datetime.now(timezone.utc)).days
    if days_until_expiry <= 7:
        logger.info(f"Token expires in {days_until_expiry} days, refreshing...")
        try:
            new_data = await refresh_access_token(tokens["refresh_token"])
            await update_tokens(
                tokens["person_urn"],
                new_data["access_token"],
                new_data.get("refresh_token"),
                new_data.get("expires_in", 5184000),
            )
            tokens["access_token"] = new_data["access_token"]
            logger.info("Token refreshed successfully")
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")

    return tokens


async def _publish_post(post: dict, access_token: str, person_urn: str) -> dict:
    """Publish a single post and return the result."""
    if post.get("image_data"):
        init = await initialize_image_upload(access_token, person_urn)
        await upload_image_binary(
            init["upload_url"],
            access_token,
            post["image_data"],
            post.get("image_content_type", "image/jpeg"),
        )
        return await publish_image_post(
            access_token, person_urn, post["content"], init["image_urn"]
        )
    else:
        return await publish_text_post(access_token, person_urn, post["content"])


async def run():
    from datetime import datetime, timezone

    db = get_db()
    now = datetime.now(timezone.utc)

    # Check daily cap
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    published_today = await db.post_queue.count_documents({
        "status": "published",
        "published_at": {"$gte": today_start},
    })
    if published_today >= DAILY_CAP:
        logger.info(f"Daily cap reached ({published_today}/{DAILY_CAP}), skipping")
        return

    # Get LinkedIn tokens
    tokens = await get_tokens()
    if not tokens:
        logger.warning("No LinkedIn tokens found, skipping")
        return

    tokens = await _refresh_token_if_needed(tokens)
    access_token = tokens["access_token"]
    person_urn = tokens["person_urn"]

    # Find due posts
    due_posts = db.post_queue.find({
        "status": "scheduled",
        "scheduled_time": {"$lte": now},
    }).sort("scheduled_time", 1).limit(DAILY_CAP - published_today)

    published = 0
    async for post in due_posts:
        post_id = post["_id"]
        logger.info(f"Publishing post {post_id}...")

        # Mark as publishing
        await db.post_queue.update_one(
            {"_id": post_id},
            {"$set": {"status": "publishing", "updated_at": now}},
        )

        try:
            result = await _publish_post(post, access_token, person_urn)
            await db.post_queue.update_one(
                {"_id": post_id},
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
            published += 1
            logger.info(f"Published post {post_id} -> {result.get('post_id')}")

        except Exception as e:
            logger.error(f"Failed to publish post {post_id}: {e}")
            await db.post_queue.update_one(
                {"_id": post_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

    logger.info(f"Cron complete: {published} posts published")


if __name__ == "__main__":
    asyncio.run(run())
    close_client()
