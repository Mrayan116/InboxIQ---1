"""
Thin wrapper around the Gmail API. Keeps google-api-python-client's verbose
response shapes out of the rest of the app -- callers get plain dicts with
the fields InboxIQ actually needs.
"""

import base64
from datetime import datetime, timezone
from email.utils import parseaddr

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import settings
from app.models.user import GmailAccount


def _credentials_from_account(account: GmailAccount) -> Credentials:
    return Credentials(
        token=account.access_token,
        refresh_token=account.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=account.scopes.split(" "),
    )


def _decode_body(payload: dict) -> str:
    """Gmail nests body parts recursively; walk them looking for text/plain."""
    if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result
    return ""


def _header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


class GmailService:
    def __init__(self, account: GmailAccount) -> None:
        self._service = build("gmail", "v1", credentials=_credentials_from_account(account))

    def list_recent_message_ids(self, max_results: int = 25) -> list[str]:
        response = self._service.users().messages().list(
            userId="me", maxResults=max_results, labelIds=["INBOX"]
        ).execute()
        return [m["id"] for m in response.get("messages", [])]

    def get_message(self, message_id: str) -> dict:
        raw = self._service.users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()

        headers = raw["payload"].get("headers", [])
        sender_raw = _header(headers, "From")
        _, sender_email = parseaddr(sender_raw)
        domain = sender_email.split("@")[-1] if "@" in sender_email else ""

        return {
            "gmail_message_id": raw["id"],
            "gmail_thread_id": raw["threadId"],
            "subject": _header(headers, "Subject"),
            "sender": sender_raw,
            "sender_domain": domain,
            "snippet": raw.get("snippet", ""),
            "body_text": _decode_body(raw["payload"]),
            "received_at": datetime.fromtimestamp(int(raw["internalDate"]) / 1000, tz=timezone.utc),
        }
