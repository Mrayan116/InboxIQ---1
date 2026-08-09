"""
User & auth-related models.

OAuth tokens live on their own table (not on User) so we can later support
multiple connected accounts per user (Stage: multi-account) without a
migration that reshapes User.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    gmail_account: Mapped["GmailAccount | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    writing_preference: Mapped["WritingPreference | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class GmailAccount(Base):
    """
    Stores the OAuth tokens needed to call the Gmail API on the user's
    behalf. `refresh_token` is what lets us fetch new access tokens without
    the user re-authenticating every hour.

    NOTE: in production, encrypt access_token/refresh_token at rest (e.g.
    via a KMS-backed field encryption library). Left as plain text here to
    keep Stage 2 focused on the auth *flow*; flagged as a follow-up.
    """

    __tablename__ = "gmail_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    access_token: Mapped[str] = mapped_column(String(2048), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(2048), nullable=False)
    token_expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scopes: Mapped[str] = mapped_column(String(1024), nullable=False)
    history_id: Mapped[str | None] = mapped_column(String(64), nullable=True)  # for incremental sync

    user: Mapped["User"] = relationship(back_populates="gmail_account")


class WritingPreference(Base):
    """User-configurable style applied when generating smart replies."""

    __tablename__ = "writing_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    tone: Mapped[str] = mapped_column(String(50), default="professional")  # professional/friendly/short/formal/enthusiastic
    signature: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    user: Mapped["User"] = relationship(back_populates="writing_preference")
