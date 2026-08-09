"""
Import all models here so `Base.metadata` is fully populated for Alembic's
autogenerate — a model defined but never imported is invisible to Alembic
and silently excluded from migrations. This is a common footgun; centralize
imports to avoid it.
"""

from app.models.user import GmailAccount, User, WritingPreference  # noqa: F401
from app.models.email import ActionItem, EmailCategory, EmailMessage, EmailThread, FollowUp, Priority  # noqa: F401
