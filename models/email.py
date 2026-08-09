"""
Email domain models.

Design note: we mirror Gmail's thread/message structure (EmailThread has
many EmailMessages) because several features — thread summarization,
timeline extraction — need to reason over a whole conversation, not a
single message in isolation.

AI-derived fields (summary, priority, is_phishing, etc.) are stored
denormalized on EmailMessage rather than in a separate "analysis" table.
Trade-off: simpler queries and no joins for the common case (render inbox
list with priority badges); cost is a wider table and re-running analysis
means overwriting columns rather than versioning history. Acceptable for
V1 — revisit if we need audit history of AI outputs.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Priority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EmailCategory(str, enum.Enum):
    """
    AI Inbox Organization (separate axis from Priority): what KIND of email
    this is and how much it matters overall, vs. Priority's "how soon."
    """

    IMPORTANT = "important"
    REQUIRES_ACTION = "requires_action"
    INFORMATIONAL = "informational"
    NEWSLETTER_MARKETING = "newsletter_marketing"
    LOW_VALUE = "low_value"


class EmailThread(Base):
    __tablename__ = "email_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    gmail_thread_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(998), default="")
    thread_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # timeline/status, Stage 5
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["EmailMessage"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan", order_by="EmailMessage.received_at"
    )


class EmailMessage(Base):
    __tablename__ = "email_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email_threads.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    gmail_message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    sender: Mapped[str] = mapped_column(String(998))
    sender_domain: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(998), default="")
    snippet: Mapped[str] = mapped_column(Text, default="")
    body_text: Mapped[str] = mapped_column(Text, default="")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # --- AI-derived fields ---
    ai_summary_short: Mapped[str | None] = mapped_column(Text, nullable=True)   # "15-second" summary
    ai_summary_detailed: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary_bullets: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    priority: Mapped[Priority | None] = mapped_column(Enum(Priority), nullable=True, index=True)
    priority_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[EmailCategory | None] = mapped_column(Enum(EmailCategory), nullable=True, index=True)
    importance_score: Mapped[int | None] = mapped_column(nullable=True, index=True)  # 0-100
    importance_positive_signals: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    importance_negative_signals: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list

    is_phishing_suspected: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    phishing_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    thread: Mapped["EmailThread"] = relationship(back_populates="messages")
    action_items: Mapped[list["ActionItem"]] = relationship(
        back_populates="email_message", cascade="all, delete-orphan"
    )


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    email_message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email_messages.id"), nullable=False)

    description: Mapped[str] = mapped_column(String(500), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    email_message: Mapped["EmailMessage"] = relationship(back_populates="action_items")


class FollowUp(Base):
    """Tracks outgoing emails awaiting a reply, for the Follow-Up Assistant."""

    __tablename__ = "follow_ups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email_threads.id"), nullable=False)

    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    remind_after_days: Mapped[int] = mapped_column(default=7)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)  # True once a reply arrives or user dismisses
    suggested_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
