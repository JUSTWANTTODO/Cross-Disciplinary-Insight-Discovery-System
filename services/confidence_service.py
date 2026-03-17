from typing import List, Dict


def compute_confidence(
    hypothesis_text: str,
    disciplines: List[str],
    evidence: List[str],
    similarity_score: float | None = None
) -> Dict:
    """
    Compute a heuristic confidence score for a research hypothesis.

    Returns:
    {
        confidence: float,
        label: str,
        why_non_obvious: List[str]
    }
    """

    # -------------------------
    # A. Evidence grounding
    # -------------------------
    evidence_count = len(evidence)

    if evidence_count >= 3:
        evidence_strength = 1.0
    elif evidence_count == 2:
        evidence_strength = 0.75
    elif evidence_count == 1:
        evidence_strength = 0.45
    else:
        evidence_strength = 0.25

    # -------------------------
    # B. Intent alignment
    # -------------------------
    if similarity_score is not None:
        intent_alignment = min(max(similarity_score, 0.0), 1.0)
    else:
        intent_alignment = 0.45  # conservative fallback

    # -------------------------
    # C. Interdisciplinarity signal
    # -------------------------
    discipline_count = len(set(disciplines))

    if discipline_count <= 1:
        interdisciplinarity = 0.3
    elif discipline_count == 2:
        interdisciplinarity = 0.6
    else:
        interdisciplinarity = 0.85

    # -------------------------
    # Final confidence
    # -------------------------
    confidence = round(
        0.45 * evidence_strength +
        0.35 * intent_alignment +
        0.20 * interdisciplinarity,
        2
    )

    # -------------------------
    # Human-readable label
    # -------------------------
    if confidence >= 0.75:
        label = "High"
    elif confidence >= 0.5:
        label = "Moderate"
    else:
        label = "Exploratory"

        
    return {
    "confidence": confidence,
    "label": label
}
