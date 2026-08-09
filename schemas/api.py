"""API-layer request/response models -- kept separate from ORM models so
the DB schema is free to evolve without breaking the public API contract."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    picture_url: str | None

    model_config = {"from_attributes": True}


class EmailListItem(BaseModel):
    id: uuid.UUID
    sender: str
    subject: str
    snippet: str
    received_at: datetime
    priority: str | None
    category: str | None
    importance_score: int | None
    ai_summary_short: str | None
    is_phishing_suspected: bool

    model_config = {"from_attributes": True}


class EmailDetail(EmailListItem):
    body_text: str
    ai_summary_detailed: str | None
    ai_summary_bullets: list[str] | None
    priority_reason: str | None
    phishing_reason: str | None
    importance_positive_signals: list[str] | None
    importance_negative_signals: list[str] | None

    model_config = {"from_attributes": True}


class SyncTriggerResponse(BaseModel):
    task_id: str
    status: str


class ActionItemOut(BaseModel):
    id: uuid.UUID
    description: str
    due_date: datetime | None
    is_completed: bool
    email_message_id: uuid.UUID

    model_config = {"from_attributes": True}


class ToneAnalysisRequest(BaseModel):
    draft_body: str
    recipient_context: str | None = None


class SimplifyRequest(BaseModel):
    body: str
