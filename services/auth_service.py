"""
Auth service — orchestrates the OAuth callback: exchange code, fetch
profile, upsert User + GmailAccount, issue our own JWT.

Kept out of the route handler so it's unit-testable without spinning up
FastAPI, and reusable if we ever add a CLI or admin tool that needs to
provision users.
"""

from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import GmailAccount, User
from app.repositories.user_repository import UserRepository
from app.services.google_oauth_service import exchange_code_for_credentials, get_userinfo


async def handle_google_callback(session: AsyncSession, code: str) -> str:
    """Runs the full callback flow and returns an InboxIQ JWT for the user."""
    credentials: Credentials = exchange_code_for_credentials(code)
    profile = get_userinfo(credentials)

    repo = UserRepository(session)
    user = await repo.get_by_email(profile["email"])

    if user is None:
        user = User(
            email=profile["email"],
            full_name=profile.get("name"),
            picture_url=profile.get("picture"),
        )
        await repo.create(user)

    gmail_account = await repo.get_gmail_account(user.id)
    expiry = credentials.expiry or datetime.now(timezone.utc)
    if gmail_account is None:
        gmail_account = GmailAccount(
            user_id=user.id,
            google_sub=profile["id"],
            access_token=credentials.token,
            refresh_token=credentials.refresh_token or "",
            token_expiry=expiry,
            scopes=" ".join(credentials.scopes or []),
        )
        session.add(gmail_account)
    else:
        gmail_account.access_token = credentials.token
        if credentials.refresh_token:  # Google only returns this on first consent
            gmail_account.refresh_token = credentials.refresh_token
        gmail_account.token_expiry = expiry

    await session.commit()
    return create_access_token(user.id)
