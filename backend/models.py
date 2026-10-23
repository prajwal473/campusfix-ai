"""Allowed values and Pydantic models. One place so routes and validation agree."""
from typing import Literal, Optional

from pydantic import BaseModel

CATEGORIES = ("plumbing", "electrical", "hvac", "structural", "furniture",
              "cleanliness", "it_network", "safety", "other")
PRIORITIES = ("low", "medium", "high", "urgent")
STATUSES = ("open", "in_progress", "resolved", "closed")
MODEL_VERIFICATION = ("consistent", "needs_review", "insufficient")   # what the model may return
VERIFICATION = MODEL_VERIFICATION + ("not_assessed",)                  # not_assessed is backend-only
AI_STATUSES = ("ok", "unavailable", "invalid_output", "unsupported_input", "not_run")

Status = Literal["open", "in_progress", "resolved", "closed"]


class StatusUpdate(BaseModel):
    status: Status


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    location: str
    category: str
    priority: str
    priority_reason: str
    evidence_summary: str
    verification_status: str
    recommended_next_step: str
    status: str
    image_url: Optional[str] = None
    ai_provider: Optional[str] = None
    created_at: str
    ai_status: str
    observations: list[str]
    assumptions: list[str]
    image_analyzed: bool
    updated_at: str
