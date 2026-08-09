"""
Shared FastAPI dependencies.

Why: route handlers should ask for what they need via `Depends(...)`, not
reach into globals. This keeps handlers testable — override `get_llm_dep`
in tests to inject a fake provider with zero network calls.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer()


def get_llm_dep() -> LLMProvider:
    return get_llm_provider()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Every protected route depends on this. Centralizing auth here means
    token validation logic exists in exactly one place — change it once,
    every route benefits.
    """
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = await UserRepository(db).get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
