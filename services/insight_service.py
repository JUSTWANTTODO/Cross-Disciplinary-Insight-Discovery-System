# services/insight_service.py
import json
import re
import streamlit as st
from services.genai_client import get_genai_client

# --------------------------------------------------
# Constants
# --------------------------------------------------
INSIGHT_MODEL = "gemini-2.5-flash-lite"
MAX_BADGES = 3


# --------------------------------------------------
# Safe JSON extraction
# --------------------------------------------------
def safe_json_extract(text: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {"badges": []}

    try:
        data = json.loads(match.group())
        if not isinstance(data, dict):
            return {"badges": []}

        badges = data.get("badges", [])
        if not isinstance(badges, list):
            return {"badges": []}

        return {"badges": badges[:MAX_BADGES]}

    except Exception:
        return {"badges": []}


# --------------------------------------------------
# Insight badge generator (SAFE + BOUNDED)
# --------------------------------------------------
@st.cache_data(show_spinner=False, max_entries=256)
def generate_insight_badges(hypothesis, disciplines, papers):
    if not hypothesis or len(hypothesis) < 20:
        return {"badges": []}

    # 🔒 Truncate inputs to avoid runaway prompts
    disciplines = disciplines[:3] if isinstance(disciplines, list) else disciplines
    papers = papers[:2] if isinstance(papers, list) else papers

    prompt = f"""
You are a research assistant.

Given a hypothesis and related literature, identify up to 3 concise insight labels.

Each label must be:
- 2–4 words
- Meaningful to researchers
- Not generic

Also provide a one-sentence explanation per label.

Hypothesis:
{hypothesis}

Disciplines:
{disciplines}

Related papers:
{papers}

Output JSON ONLY:
{{
  "badges": [
    {{
      "label": "Assumption Shift",
      "explanation": "Introduces biological traits as drivers of network centrality, which models usually treat as structural."
    }}
  ]
}}

IMPORTANT:
- Highlight DIFFERENT novelty aspects when possible
- Do NOT repeat the same label unless unavoidable
"""

    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model=INSIGHT_MODEL,
            contents=prompt
        )

        text = (response.text or "").strip()
        if not text:
            return {"badges": []}

        return safe_json_extract(text)

    except Exception as e:
        print(f"[Insight Error] {e}")
        return {"badges": []}
