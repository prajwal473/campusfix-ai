"""Validated schemas and safe errors for AI complaint analysis."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal[
    "plumbing",
    "electrical",
    "hvac",
    "structural",
    "furniture",
    "cleanliness",
    "it_network",
    "safety",
    "other",
]
Priority = Literal["low", "medium", "high", "urgent"]
VerificationStatus = Literal["consistent", "needs_review", "insufficient"]


class AnalysisResult(BaseModel):
    """Validated output consumed by the CampusFix ticket API."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    category: Category
    priority: Priority
    priority_reason: str = Field(min_length=1, max_length=1000)
    observations: list[str] = Field(default_factory=list, max_length=20)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    evidence_summary: str = Field(min_length=1, max_length=2000)
    verification_status: VerificationStatus
    recommended_next_step: str = Field(min_length=1, max_length=1000)
    image_analyzed: bool
    ai_provider: str = Field(min_length=1, max_length=200)

    @field_validator(
        "title",
        "priority_reason",
        "evidence_summary",
        "recommended_next_step",
        "ai_provider",
    )
    @classmethod
    def strip_required_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("observations", "assumptions")
    @classmethod
    def strip_list_items(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values if isinstance(item, str) and item.strip()]
        return cleaned


class AIServiceError(Exception):
    """Safe, typed error raised when AI analysis cannot be completed."""

    ALLOWED_STATUSES = {"unavailable", "invalid_output", "unsupported_input"}

    def __init__(self, ai_status: str, message: str) -> None:
        if ai_status not in self.ALLOWED_STATUSES:
            ai_status = "unavailable"
        # Only callers' predefined safe messages should be passed here.
        safe_messages = {
            "unavailable": "AI analysis is temporarily unavailable.",
            "invalid_output": "AI returned an output that could not be validated.",
            "unsupported_input": "The supplied complaint or image input is unsupported.",
        }
        self.ai_status = ai_status
        self.message = safe_messages[ai_status]
        super().__init__(self.message)
