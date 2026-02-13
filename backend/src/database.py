"""Motor MongoDB async singleton (pattern from topcx-inbound)."""

from __future__ import annotations

import motor.motor_asyncio

import config

_client: motor.motor_asyncio.AsyncIOMotorClient | None = None


def get_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_CONNECTION_STRING)
    return _client


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    return get_client()[config.MONGO_DB_NAME]


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
