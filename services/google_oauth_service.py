"""
Google OAuth flow.

Scopes requested are deliberately narrow:
- userinfo.email / userinfo.profile: identify the user
- gmail.readonly: read emails for AI analysis
- gmail.send: required ONLY for the future "send approved reply" action —
  note this does NOT mean InboxIQ auto-sends. The app never calls this
  scope's API without an explicit user click on "Send" in the UI. This is
  enforced in the reply-sending service (Stage 6), not just documented here.
"""

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import settings

GMAIL_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def _build_flow() -> Flow:
    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }
    return Flow.from_client_config(
        client_config, scopes=GMAIL_SCOPES, redirect_uri=settings.google_redirect_uri
    )


def get_authorization_url() -> tuple[str, str]:
    """Returns (auth_url, state) — state should be stored (e.g. signed cookie) and verified on callback."""
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",       # required to get a refresh_token
        prompt="consent",            # forces refresh_token on repeat logins too
        include_granted_scopes="true",
    )
    return auth_url, state


def exchange_code_for_credentials(code: str) -> Credentials:
    flow = _build_flow()
    flow.fetch_token(code=code)
    return flow.credentials


def get_userinfo(credentials: Credentials) -> dict:
    service = build("oauth2", "v2", credentials=credentials)
    return service.userinfo().get().execute()
