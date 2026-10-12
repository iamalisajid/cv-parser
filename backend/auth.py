"""Authentication dependency for FastAPI routes."""

from __future__ import annotations

from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import JWT_SECRET

if len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET must be set to a random value of at least 32 characters")

_bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"


def create_session_token(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_session_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        return decode_session_token(creds.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
