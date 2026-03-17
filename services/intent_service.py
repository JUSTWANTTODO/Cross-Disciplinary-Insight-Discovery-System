import os
from services.genai_client import get_genai_client

INTENT_MODEL = "gemini-2.5-flash-lite"


def normalize_intent(user_text: str) -> str:
    prompt = f"""
Rewrite the following user input into a clear, explicit academic search query.
Do NOT add new domains.
Do NOT narrow the scope.
Only clarify intent.

User input:
{user_text}

Output:
One sentence suitable for searching research papers.
"""
    client = get_genai_client()
    response = client.models.generate_content(
    model=INTENT_MODEL,
    contents=prompt
)
    try:

        intent_text = (response.text or "").strip()
        return intent_text if intent_text else user_text

    except Exception:
        # graceful fallback
        return user_text
