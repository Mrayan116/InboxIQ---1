from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.auth_service import handle_google_callback
from app.services.google_oauth_service import get_authorization_url

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
async def google_login():
    """Frontend redirects the browser here to kick off consent."""
    auth_url, state = get_authorization_url()
    # In production: store `state` in a short-lived signed cookie and verify
    # it on callback to prevent CSRF. Omitted here for brevity — flagged as
    # a Stage 2 follow-up before shipping to real users.
    return RedirectResponse(auth_url)


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    jwt_token = await handle_google_callback(db, code)
    # Redirect back to the frontend with the token. In production, prefer
    # setting this as an httpOnly cookie over a URL param.
    return RedirectResponse(f"{settings.frontend_origin}/auth/complete?token={jwt_token}")
