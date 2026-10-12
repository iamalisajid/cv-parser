"""Google OAuth login endpoints."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel

from backend.auth import create_session_token, get_current_user
from config import GOOGLE_CLIENT_ID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class GoogleLoginRequest(BaseModel):
    credential: str


class AuthResponse(BaseModel):
    token: str
    user: dict[str, Any]


@router.post("/google", response_model=AuthResponse)
async def google_login(body: GoogleLoginRequest):
    """Verify a Google ID token and return a session JWT."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured")

    try:
        id_info = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        logger.warning("Google token verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = id_info.get("email", "").strip().lower()
    if not id_info.get("email_verified"):
        raise HTTPException(status_code=403, detail="Google email is not verified")
    allowed_domain = os.getenv("ALLOWED_EMAIL_DOMAIN", "").strip().lower()
    if not allowed_domain:
        raise HTTPException(status_code=503, detail="ALLOWED_EMAIL_DOMAIN is not configured")
    if not email.endswith(f"@{allowed_domain}"):
        raise HTTPException(
            status_code=403,
            detail=f"Only @{allowed_domain} accounts are allowed",
        )

    payload = {
        "sub": id_info["sub"],
        "email": email,
        "name": id_info.get("name", ""),
        "picture": id_info.get("picture", ""),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }

    token = create_session_token(payload)
    user = {
        "email": payload["email"],
        "name": payload["name"],
        "picture": payload["picture"],
    }

    return AuthResponse(token=token, user=user)


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return {
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
    }
