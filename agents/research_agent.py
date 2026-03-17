import os
import time
import json
from typing import List, Dict
import streamlit as st
from services.genai_client import get_genai_client

LLM_MODEL = "gemini-2.5-flash-lite"

# Prompt builder
def _build_prompt(
    user_input: str,
    ranked_papers: List[Dict],
    max_hypotheses: int
) -> str:
    """
    Compact, grounded prompt for hypothesis generation.
    """

    paper_blocks = []
    for idx, paper in enumerate(ranked_papers, start=1):
        paper_blocks.append(
            f"""
Paper {idx}:
Title: {paper.get('title', '')}
Source: {paper.get('source', '')}
Abstract: {paper.get('abstract', '')[:800]}
"""
        )

    papers_text = "\n".join(paper_blocks)


    prompt = f"""
You are an interdisciplinary research assistant.

Your task is to generate {max_hypotheses} NON-OBVIOUS, TESTABLE research hypotheses
by connecting ideas across different scientific disciplines.

IMPORTANT STRUCTURE RULES (STRICT):

For EACH hypothesis, output the following JSON structure:

{{
  "id": "<unique_id>",
  "title": "<short descriptive title>",
  "disciplines": ["<discipline 1>", "<discipline 2>", "..."],

  "hypothesis": "<A single, clear, testable hypothesis statement>",

  "rationale": "<Pure conceptual and mechanistic reasoning explaining WHY this hypothesis makes sense.
                Do NOT mention papers, authors, studies, or prior work here.
                This must read like theoretical reasoning only.>",

  "evidence": [
    "<Paper title or short identifier> – <1 line describing HOW this paper supports the hypothesis>",
    "<Paper title or short identifier> – <1 line describing HOW this paper supports the hypothesis>"

    "recommendation_tag": {{
    "label": "<ONE of: Most Recommended | Under-Explored | Well-Studied Extension | No Direct Prior Work | High-Risk Exploratory | High Actionability>",
    "reason": "<One short sentence explaining why>"
  }}

   "suggested_next_focus": "<One short sentence suggesting how the researcher should refine or redirect exploration next>"

  ]
}}

CRITICAL CONSTRAINTS:
- RATIONALE must NOT cite papers or studies.
- EVIDENCE must ONLY contain references to existing research papers.
- Do NOT repeat the same content in rationale and evidence.
- Favor interdisciplinary links that are rare or unexpected.
- Avoid obvious or well-established connections.
- Do NOT use generic phrases like “cross-disciplinary” alone.
- Explicitly state what makes this connection surprising or rare.
- Exactly ONE hypothesis must be labeled "Most Recommended".
- Other hypotheses must use different labels.
- Always generate at least one insight badge.
- Prefer different insight types across hypotheses when possible.
- Labels must reflect literature coverage and feasibility.
- Suggested next focus must suggest a direction, not restate hypotheses.
- Suggested next focus must be based on gaps or patterns observed across all hypotheses.
- Do NOT mention models, APIs, or implementation details.

Context for hypothesis generation:
User input:
{user_input}

Relevant papers:
{ranked_papers}

Output ONLY valid JSON. No markdown. No explanations.
"""

    return prompt


# --------------------------------------------------
# Main agent function
# --------------------------------------------------
def generate_hypotheses(
    user_input: str,
    ranked_papers: List[Dict],
    max_hypotheses: int = 3
) -> Dict:

    if not user_input or len(user_input.strip()) < 30:
        return {"error": "User input too short to generate meaningful hypotheses."}

    if not ranked_papers:
        return {"error": "No ranked papers available for hypothesis generation."}

    prompt = _build_prompt(
        user_input=user_input,
        ranked_papers=ranked_papers,
        max_hypotheses=max_hypotheses
    )

    # Retry loop (clean, single)
    for attempt in range(3):
        try:
            client = get_genai_client()
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt
            )

            text = (response.text or "").strip()
            if text:
                return {"raw_text": text}

        except Exception:
            time.sleep(2)

    # Final graceful fallback
    return {
        "error": "Hypothesis generation temporarily unavailable."
    }
