"""
JWT session tokens.

Why JWT instead of server-side sessions: stateless auth means any backend
replica can verify a request without a shared session store — simpler to
scale horizontally. Trade-off: tokens can't be instantly revoked before
expiry, so we keep expiry short-ish (7 days) and this is a place to add a
Redis-backed denylist later if instant revocation becomes a requirement.
"""

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> uuid.UUID | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None
