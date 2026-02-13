import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "local")

# MongoDB
MONGO_CONNECTION_STRING = os.getenv(
    "MONGO_CONNECTION_STRING",
    "mongodb://admin:password123@localhost:27018/linkedin_autoposter?authSource=admin",
)
MONGO_DB_NAME = "linkedin_autoposter"

# Admin password (single-user tool)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-in-production")
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me-session-secret")

# LinkedIn OAuth
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")

# Fernet key for token encryption
FERNET_KEY = os.getenv("FERNET_KEY", "")

# AI provider: "openai" or "anthropic"
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Environment-specific config
ENV_CONFIG = {
    "local": {
        "linkedin_callback_url": "http://localhost:8010/api/auth/linkedin/callback",
        "frontend_url": "http://localhost:3010",
    },
    "prod": {
        "linkedin_callback_url": "https://linkedin.topcx.ai/api/auth/linkedin/callback",
        "frontend_url": "https://linkedin.topcx.ai",
    },
}


def get_env_config(key: str) -> str:
    return ENV_CONFIG.get(ENV, ENV_CONFIG["local"])[key]


LINKEDIN_CALLBACK_URL = get_env_config("linkedin_callback_url")
FRONTEND_URL = get_env_config("frontend_url")

# CORS origins
if ENV == "prod":
    CORS_ORIGINS: list[str] = [
        "https://linkedin.topcx.ai",
    ]
else:
    CORS_ORIGINS: list[str] = [
        "http://localhost:3010",
        "http://localhost:8010",
    ]

# Cookie settings
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".topcx.ai" if ENV == "prod" else None)
COOKIE_SECURE = ENV == "prod"
