"""Auth router: admin login + LinkedIn OAuth initiate/callback."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response, HTTPException
from itsdangerous import URLSafeTimedSerializer

import config
from src.schemas import LoginRequest
from src.linkedin_oauth import build_auth_url, exchange_code, get_user_info
from src.token_store import store_tokens, get_connection_status, delete_tokens

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_signer = URLSafeTimedSerializer(config.SESSION_SECRET)
SESSION_COOKIE = "li_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

# In-memory OAuth state storage (single-user tool)
_oauth_states: dict[str, datetime] = {}


def _set_session(response: Response) -> None:
    token = _signer.dumps({"authenticated": True})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=config.COOKIE_SECURE,
        domain=config.COOKIE_DOMAIN,
    )


def verify_session(request: Request) -> bool:
    cookie = request.cookies.get(SESSION_COOKIE)
    if not cookie:
        return False
    try:
        data = _signer.loads(cookie, max_age=SESSION_MAX_AGE)
        return data.get("authenticated") is True
    except Exception:
        return False


def require_auth(request: Request) -> None:
    if not verify_session(request):
        raise HTTPException(status_code=401, detail="Not authenticated")


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    if body.password != config.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    _set_session(response)
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, domain=config.COOKIE_DOMAIN)
    return {"ok": True}


@router.get("/me")
async def me(request: Request):
    if not verify_session(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"authenticated": True}


@router.get("/linkedin/initiate")
async def linkedin_initiate(request: Request):
    require_auth(request)
    url, state = build_auth_url()
    _oauth_states[state] = datetime.now(timezone.utc)
    # Clean old states (older than 10 min)
    cutoff = datetime.now(timezone.utc).timestamp() - 600
    for k in [k for k, v in _oauth_states.items() if v.timestamp() < cutoff]:
        _oauth_states.pop(k, None)
    return {"url": url}


@router.get("/linkedin/callback")
async def linkedin_callback(request: Request, code: str, state: str):
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    _oauth_states.pop(state, None)

    try:
        token_data = await exchange_code(code)
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 5184000)  # 60 days default

        user_info = await get_user_info(access_token)
        person_urn = user_info.get("sub", "")
        profile = {
            "name": user_info.get("name", ""),
            "email": user_info.get("email", ""),
            "picture": user_info.get("picture", ""),
        }

        await store_tokens(person_urn, access_token, refresh_token, expires_in, profile)
        logger.info(f"LinkedIn connected for {profile.get('name', person_urn)}")

        # Redirect to frontend
        return Response(
            status_code=302,
            headers={"Location": f"{config.FRONTEND_URL}?linkedin=connected"},
        )
    except Exception as e:
        logger.error(f"LinkedIn OAuth callback failed: {e}")
        return Response(
            status_code=302,
            headers={"Location": f"{config.FRONTEND_URL}?linkedin=error&message={str(e)}"},
        )


@router.get("/linkedin/status")
async def linkedin_status(request: Request):
    require_auth(request)
    return await get_connection_status()


@router.post("/linkedin/disconnect")
async def linkedin_disconnect(request: Request):
    require_auth(request)
    await delete_tokens()
    return {"ok": True}
