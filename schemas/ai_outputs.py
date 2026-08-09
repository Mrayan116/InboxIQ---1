"""
Structured output schemas for AI features.

Why Pydantic here specifically: we ask the LLM for json_mode output and
validate it against these models immediately. If the model returns
malformed JSON or a missing field, we fail loudly (ValidationError) instead
of shipping garbage into the database or UI. This is the contract between
"the LLM said something" and "the app trusts it."
"""

from pydantic import BaseModel, Field


class SummaryResult(BaseModel):
    short_summary: str = Field(description="One sentence, readable in ~15 seconds")
    detailed_summary: str = Field(description="2-4 sentence paragraph")
    bullet_points: list[str] = Field(description="3-6 key points")


class PriorityResult(BaseModel):
    priority: str = Field(description="one of: critical, high, medium, low")
    reason: str = Field(description="one sentence explaining the classification")


class ImportanceResult(BaseModel):
    category: str = Field(
        description="one of: important, requires_action, informational, newsletter_marketing, low_value"
    )
    importance_score: int = Field(ge=0, le=100, description="0-100, how much this email matters to the user")
    positive_signals: list[str] = Field(description="specific reasons raising importance, e.g. 'from important contact'")
    negative_signals: list[str] = Field(description="specific reasons lowering importance, e.g. 'automated message'")


class ActionItemResult(BaseModel):
    description: str
    due_date: str | None = Field(default=None, description="ISO 8601 date if a deadline is mentioned, else null")


class ActionItemExtractionResult(BaseModel):
    action_items: list[ActionItemResult]


class ToneAnalysisResult(BaseModel):
    detected_tone: str = Field(description="e.g. professional, aggressive, passive, friendly, confident, formal")
    concerns: list[str] = Field(description="specific issues found, empty list if none")
    suggestions: list[str] = Field(description="concrete rewrite suggestions, empty list if none")
    overall_assessment: str


class PhishingAnalysisResult(BaseModel):
    is_suspicious: bool
    risk_signals: list[str] = Field(description="specific red flags found, e.g. 'urgent password reset request'")
    explanation: str = Field(description="plain-English explanation of why this is/isn't suspicious")


class SmartReplyOption(BaseModel):
    style: str = Field(description="professional, friendly, or concise")
    body: str


class SmartReplyResult(BaseModel):
    options: list[SmartReplyOption]


class ThreadSummaryResult(BaseModel):
    timeline: list[str] = Field(description="chronological key events, one per list item")
    key_decisions: list[str]
    open_questions: list[str]
    current_status: str
