"""Ticket endpoints. Reports are always saved, even when AI analysis fails."""
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

import database
from models import (CATEGORIES, MODEL_VERIFICATION, PRIORITIES, STATUSES, StatusUpdate, TicketOut)

# Bharath's module. If it isn't merged yet, tickets are saved with ai_status "not_run".
try:
    from ai import gemma_service
    from ai.schemas import AIServiceError
except ImportError:
    gemma_service = None

    class AIServiceError(Exception):  # stand-in so the except clause below still works
        ai_status = "unavailable"

log = logging.getLogger("campusfix")
router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
MAX_IMAGE_MB = float(os.getenv("MAX_IMAGE_MB", "5"))
MAX_IMAGE_BYTES = int(MAX_IMAGE_MB * 1024 * 1024)
MAX_DESCRIPTION = 2000
MAX_LOCATION = 200


class InvalidAnalysis(Exception):
    pass


def sniff_image(data: bytes):
    """Identify the image from its first bytes, not from the filename or declared type."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", ".webp"
    return None


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise InvalidAnalysis(name)
    return value.strip()


def _str_list(value, name):
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise InvalidAnalysis(name)
    return [x.strip() for x in value if x.strip()]


def validate_analysis(result, has_image: bool) -> dict:
    """Re-check the AI result against our allowed values before it touches the database."""
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    try:
        out = {
            "title": _text(data["title"], "title")[:200],
            "category": data["category"],
            "priority": data["priority"],
            "priority_reason": _text(data["priority_reason"], "priority_reason"),
            "evidence_summary": _text(data["evidence_summary"], "evidence_summary"),
            "verification_status": data["verification_status"],
            "recommended_next_step": _text(data["recommended_next_step"], "recommended_next_step"),
            "observations": _str_list(data.get("observations", []), "observations"),
            "assumptions": _str_list(data.get("assumptions", []), "assumptions"),
        }
    except KeyError as exc:
        raise InvalidAnalysis(str(exc))
    if out["category"] not in CATEGORIES or out["priority"] not in PRIORITIES \
            or out["verification_status"] not in MODEL_VERIFICATION:
        raise InvalidAnalysis("enum")
    # The service sets these from what really happened; an image can't be analysed if none was sent.
    out["image_analyzed"] = bool(data.get("image_analyzed")) and has_image
    provider = data.get("ai_provider")
    out["ai_provider"] = provider.strip() if isinstance(provider, str) and provider.strip() else None
    return out


def placeholder_analysis(description: str) -> dict:
    title = description if len(description) <= 80 else description[:77].rstrip() + "..."
    return {
        "title": title,
        "category": "other",
        "priority": "medium",
        "priority_reason": "AI triage unavailable — placeholder priority; staff must review.",
        "evidence_summary": "No AI analysis was performed. Staff should review the description and any attached photo.",
        "verification_status": "not_assessed",
        "recommended_next_step": "Staff should review this report and assign a category and priority manually.",
        "observations": [],
        "assumptions": [],
        "image_analyzed": False,
        "ai_provider": None,
    }


def run_analysis(description, location, image_bytes, image_mime):
    """Returns (ticket fields, ai_status). Never raises: a failed analysis becomes a placeholder."""
    if gemma_service is None:
        return placeholder_analysis(description), "not_run"
    try:
        result = gemma_service.analyze_report(description, location, image_bytes, image_mime)
        return validate_analysis(result, image_bytes is not None), "ok"
    except AIServiceError as exc:
        status = getattr(exc, "ai_status", "unavailable")
        log.warning("AI analysis failed (%s): %s", status, getattr(exc, "message", ""))
        if status not in ("unavailable", "invalid_output", "unsupported_input"):
            status = "unavailable"
        return placeholder_analysis(description), status
    except InvalidAnalysis as exc:
        log.warning("AI result failed validation: %s", exc)
        return placeholder_analysis(description), "invalid_output"
    except Exception:
        log.exception("Unexpected error during AI analysis")
        return placeholder_analysis(description), "unavailable"


@router.post("/tickets", response_model=TicketOut, status_code=201)
def create_ticket(
    description: str = Form(...),
    location: str = Form(...),
    image: Optional[UploadFile] = File(None),
):
    description, location = description.strip(), location.strip()
    if not description:
        raise HTTPException(422, "description is required.")
    if not location:
        raise HTTPException(422, "location is required.")
    if len(description) > MAX_DESCRIPTION:
        raise HTTPException(422, f"description is too long (max {MAX_DESCRIPTION} characters).")
    if len(location) > MAX_LOCATION:
        raise HTTPException(422, f"location is too long (max {MAX_LOCATION} characters).")

    image_bytes = image_mime = ext = None
    if image is not None and image.filename:
        data = image.file.read(MAX_IMAGE_BYTES + 1)
        if data:  # an empty file part means "no image"
            if len(data) > MAX_IMAGE_BYTES:
                raise HTTPException(413, f"Image too large (max {MAX_IMAGE_MB:g} MB).")
            sniffed = sniff_image(data)
            if sniffed is None:
                raise HTTPException(415, "Unsupported image type. Allowed: JPEG, PNG, WebP.")
            image_bytes, (image_mime, ext) = data, sniffed

    fields, ai_status = run_analysis(description, location, image_bytes, image_mime)
    fields.update(description=description, location=location, ai_status=ai_status, image_path=None)

    saved_path = None
    if image_bytes is not None:
        UPLOAD_DIR.mkdir(exist_ok=True)
        fields["image_path"] = uuid.uuid4().hex + ext  # random name, never the client's
        saved_path = UPLOAD_DIR / fields["image_path"]
        saved_path.write_bytes(image_bytes)
    try:
        ticket_id = database.create_ticket(fields)
    except Exception:
        if saved_path is not None:
            saved_path.unlink(missing_ok=True)
        log.exception("Could not save ticket")
        raise HTTPException(500, "Could not save the report. Please try again.")
    return database.get_ticket(ticket_id)


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(status: Optional[str] = None, priority: Optional[str] = None):
    if status and status not in STATUSES:
        raise HTTPException(422, f"Invalid status. Allowed: {', '.join(STATUSES)}.")
    if priority and priority not in PRIORITIES:
        raise HTTPException(422, f"Invalid priority. Allowed: {', '.join(PRIORITIES)}.")
    return database.list_tickets(status, priority)


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int):
    ticket = database.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(404, f"Ticket {ticket_id} not found")
    return ticket


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: StatusUpdate):
    ticket = database.update_ticket_status(ticket_id, payload.status)
    if ticket is None:
        raise HTTPException(404, f"Ticket {ticket_id} not found")
    return ticket
