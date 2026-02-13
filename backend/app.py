import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from src.database import get_db, close_client
from routers.auth import router as auth_router
from routers.posts import router as posts_router
from routers.generate import router as generate_router
from routers.settings import router as settings_router
from routers.history import router as history_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _create_indexes():
    """Create MongoDB indexes on startup."""
    db = get_db()
    await db.linkedin_tokens.create_index([("person_urn", 1)], unique=True)
    await db.post_queue.create_index([("status", 1), ("scheduled_time", 1)])
    await db.post_queue.create_index([("status", 1)])
    await db.post_queue.create_index([("queue_order", 1)])
    await db.settings.create_index([("setting_key", 1)], unique=True)
    logger.info("MongoDB indexes ensured")


@asynccontextmanager
async def lifespan(application: FastAPI):
    await _create_indexes()
    yield
    close_client()


app = FastAPI(
    title="LinkedIn AutoPoster",
    description="AI-powered LinkedIn post scheduling and publishing",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(generate_router)
app.include_router(settings_router)
app.include_router(history_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "linkedin-autoposter"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8010, reload=(config.ENV == "local"))
