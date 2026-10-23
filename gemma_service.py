
import json
import os
import re
from typing import Literal

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, ValidationError

load_dotenv()

API_KEY = os.getenv("GEMMA_API_KEY")
MODEL_NAME = os.getenv(
    "GEMMA_MODEL",
    "gemma-4-26b-a4b-it",
)


class ComplaintAnalysis(BaseModel):
    category: str
    location: str
    priority: Literal["Low", "Medium", "High"]
    summary: str
    suggested_action: str
    department: str


def analyze_complaint(complaint: str) -> dict:
    """Analyze a campus complaint using Gemma 4."""

    if not API_KEY:
        raise RuntimeError("GEMMA_API_KEY is missing.")

    if not complaint or not complaint.strip():
        raise ValueError("Complaint cannot be empty.")

    client = genai.Client(api_key=API_KEY)

    prompt = f"""
You are CampusFix AI, a campus complaint analysis assistant.

Analyze the complaint and return one JSON object with exactly
these fields:
- category
- location
- priority
- summary
- suggested_action
- department

Rules:
1. Priority must be Low, Medium, or High.
2. Do not invent facts that are not provided.
3. Use "Unknown" for a location that is not specified.
4. Recommend a practical action.
5. Return JSON only, without Markdown fences.

Complaint:
{complaint}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError("Gemma returned an empty response.")

    # Handle responses that contain Markdown JSON fences.
    text = response.text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
        result = ComplaintAnalysis.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise RuntimeError(
            "Gemma returned invalid complaint data."
        ) from exc

    return result.model_dump()


if __name__ == "__main__":
    sample = (
        "The water cooler on the second floor of Block B "
        "has not been working for two days."
    )

    result = analyze_complaint(sample)
    print(json.dumps(result, indent=2))
