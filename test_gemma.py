
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMMA_API_KEY")
model = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")

if not api_key:
    raise RuntimeError(
        "API key not found. Check your .env file."
    )

client = genai.Client(api_key=api_key)

complaint = """
The water cooler on the second floor of Block B
has not been working for two days. Students cannot
get drinking water from it.
"""

prompt = f"""
You are CampusFix AI, an assistant that analyzes campus complaints.

Analyze this complaint and return a JSON object with:
category, location, priority, summary, suggested_action, department.

Priority must be Low, Medium, or High.
Do not invent missing facts.

Complaint:
{complaint}
"""

print(f"Testing model: {model}")

response = client.models.generate_content(
    model=model,
    contents=prompt,
)

if not response.text:
    raise RuntimeError("The model returned an empty response.")

print("\n--- MODEL RESPONSE ---")
print(response.text)
print("\n--- TEST PASSED ---")
