"""Encrypt/decrypt LinkedIn OAuth tokens (pattern from topcx-auth)."""

from __future__ import annotations

from datetime import datetime, timezone

from cryptography.fernet import Fernet

import config
from src.database import get_db


def _fernet() -> Fernet:
    key = config.FERNET_KEY
    if not key:
        raise ValueError("FERNET_KEY not set in environment")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(val: str) -> bytes:
    if not val:
        return val
    return _fernet().encrypt(val.encode())


def decrypt_token(val) -> str:
    if not val:
        return val
    try:
        raw = val if isinstance(val, bytes) else val.encode()
        return _fernet().decrypt(raw).decode()
    except Exception:
        return val if isinstance(val, str) else val.decode()


async def store_tokens(
    person_urn: str,
    access_token: str,
    refresh_token: str | None,
    expires_in: int,
    profile: dict,
) -> None:
    """Upsert encrypted LinkedIn tokens."""
    db = get_db()
    now = datetime.now(timezone.utc)

    await db.linkedin_tokens.update_one(
        {"person_urn": person_urn},
        {
            "$set": {
                "access_token": encrypt_token(access_token),
                "refresh_token": encrypt_token(refresh_token) if refresh_token else None,
                "expires_at": datetime.fromtimestamp(
                    now.timestamp() + expires_in, tz=timezone.utc
                ),
                "profile": profile,
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


async def get_tokens() -> dict | None:
    """Retrieve and decrypt the stored LinkedIn tokens (single-user)."""
    db = get_db()
    doc = await db.linkedin_tokens.find_one()
    if not doc or not doc.get("access_token"):
        return None

    return {
        "person_urn": doc["person_urn"],
        "access_token": decrypt_token(doc["access_token"]),
        "refresh_token": decrypt_token(doc["refresh_token"]) if doc.get("refresh_token") else None,
        "expires_at": doc["expires_at"],
        "profile": doc.get("profile", {}),
    }


async def get_connection_status() -> dict:
    """Return LinkedIn connection status without decrypting tokens."""
    db = get_db()
    doc = await db.linkedin_tokens.find_one()
    if not doc or not doc.get("access_token"):
        return {"connected": False}

    return {
        "connected": True,
        "person_urn": doc["person_urn"],
        "profile": doc.get("profile", {}),
        "expires_at": doc["expires_at"].isoformat() if doc.get("expires_at") else None,
    }


async def delete_tokens() -> None:
    """Remove all stored tokens (disconnect)."""
    db = get_db()
    await db.linkedin_tokens.delete_many({})


async def update_tokens(person_urn: str, access_token: str, refresh_token: str | None, expires_in: int) -> None:
    """Update tokens after a refresh."""
    db = get_db()
    now = datetime.now(timezone.utc)
    update = {
        "access_token": encrypt_token(access_token),
        "expires_at": datetime.fromtimestamp(now.timestamp() + expires_in, tz=timezone.utc),
        "updated_at": now,
    }
    if refresh_token:
        update["refresh_token"] = encrypt_token(refresh_token)

    await db.linkedin_tokens.update_one({"person_urn": person_urn}, {"$set": update})
