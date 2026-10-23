
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .schemas import AIServiceError, AnalysisResult

# Load .env from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMMA_API_KEY")
MODEL = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")

MAX_IMAGE_SIZE = 5 * 1024 * 1024
SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

# Temporary diagnostic timeout: 60 seconds.
client = (
    genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(timeout=60_000),
    )
    if API_KEY
    else None
)


def analyze_report(
    description: str,
    location: str,
    image_bytes: bytes | None = None,
    image_mime: str | None = None,
) -> dict:
    """Analyze a campus maintenance report using Gemma."""

    if client is None:
        raise AIServiceError(
            "unavailable",
            "AI analysis is temporarily unavailable.",
        )

    if not isinstance(description, str) or not description.strip():
        raise AIServiceError(
            "unsupported_input",
            "A non-empty report description is required.",
        )

    if not isinstance(location, str) or not location.strip():
        raise AIServiceError(
            "unsupported_input",
            "A valid report location is required.",
        )

    if image_bytes is not None:
        if image_mime not in SUPPORTED_IMAGE_TYPES:
            raise AIServiceError(
                "unsupported_input",
                "The provided image format is not supported.",
            )

        if len(image_bytes) > MAX_IMAGE_SIZE:
            raise AIServiceError(
                "unsupported_input",
                "The image must be 5 MB or smaller.",
            )

    prompt = f"""
You are an assistant analyzing campus maintenance reports.

Report description: {description}
Reported location: {location}

Return ONLY a valid JSON object with these fields:
{{
  "title": "Short issue title",
  "category": "plumbing",
  "priority": "medium",
  "priority_reason": "Reason for the priority",
  "observations": ["Observation supported by the report"],
  "assumptions": ["Any assumption that needs confirmation"],
  "evidence_summary": "Summary of available evidence",
  "verification_status": "needs_review",
  "recommended_next_step": "Practical next action"
}}

Allowed category values:
plumbing, electrical, hvac, structural, furniture, cleanliness,
it_network, safety, other.

Allowed priority values:
low, medium, high, urgent.

Allowed verification_status values:
consistent, needs_review, insufficient.

Do not invent observations or claim that an issue has been physically
verified. If information is uncertain, use needs_review or insufficient.
"""

    try:
        contents = [prompt]

        if image_bytes is not None:
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image_mime,
                )
            )

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        if not response.text:
            raise ValueError("The model returned an empty response.")

        data = json.loads(response.text)

        # These values are determined by the actual request, not the model.
        data["image_analyzed"] = image_bytes is not None
        data["ai_provider"] = "gemma"

        validated = AnalysisResult.model_validate(data)
        return validated.model_dump()

    except AIServiceError:
        raise

    except Exception as exc:
        # Diagnostic output; never expose the API key.
        message = str(exc).replace(API_KEY or "", "[REDACTED]")
        print("DEBUG exception type:", type(exc).__name__)
        print("DEBUG exception message:", message)

        raise AIServiceError(
            "unavailable",
            "AI analysis is temporarily unavailable.",
        ) from exc
