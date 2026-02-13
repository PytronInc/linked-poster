"""LinkedIn Posts API client (version 202601)."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

POSTS_URL = "https://api.linkedin.com/rest/posts"
IMAGES_URL = "https://api.linkedin.com/rest/images"

LINKEDIN_VERSION = "202601"
HEADERS_BASE = {
    "LinkedIn-Version": LINKEDIN_VERSION,
    "X-Restli-Protocol-Version": "2.0.0",
}


def _headers(access_token: str) -> dict:
    return {
        **HEADERS_BASE,
        "Authorization": f"Bearer {access_token}",
    }


async def publish_text_post(access_token: str, person_urn: str, text: str) -> dict:
    """Publish a text-only post to LinkedIn."""
    body = {
        "author": f"urn:li:person:{person_urn}",
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            POSTS_URL,
            json=body,
            headers={**_headers(access_token), "Content-Type": "application/json"},
            timeout=30,
        )
        if resp.status_code == 201:
            post_id = resp.headers.get("x-restli-id", "")
            logger.info(f"Published text post: {post_id}")
            return {"success": True, "post_id": post_id}

        logger.error(f"LinkedIn post failed: {resp.status_code} {resp.text}")
        resp.raise_for_status()


async def initialize_image_upload(access_token: str, person_urn: str) -> dict:
    """Step 1: Initialize image upload to get upload URL."""
    body = {
        "initializeUploadRequest": {
            "owner": f"urn:li:person:{person_urn}",
        }
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{IMAGES_URL}?action=initializeUpload",
            json=body,
            headers={**_headers(access_token), "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "upload_url": data["value"]["uploadUrl"],
            "image_urn": data["value"]["image"],
        }


async def upload_image_binary(upload_url: str, access_token: str, image_data: bytes, content_type: str) -> None:
    """Step 2: Upload the image binary to LinkedIn's upload URL."""
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            upload_url,
            content=image_data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": content_type,
            },
            timeout=60,
        )
        resp.raise_for_status()


async def publish_image_post(access_token: str, person_urn: str, text: str, image_urn: str) -> dict:
    """Step 3: Create a post with an attached image."""
    body = {
        "author": f"urn:li:person:{person_urn}",
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {
            "media": {
                "title": "Image",
                "id": image_urn,
            }
        },
        "lifecycleState": "PUBLISHED",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            POSTS_URL,
            json=body,
            headers={**_headers(access_token), "Content-Type": "application/json"},
            timeout=30,
        )
        if resp.status_code == 201:
            post_id = resp.headers.get("x-restli-id", "")
            logger.info(f"Published image post: {post_id}")
            return {"success": True, "post_id": post_id}

        logger.error(f"LinkedIn image post failed: {resp.status_code} {resp.text}")
        resp.raise_for_status()
