import re

MAX_CHARS = 4000  # ideal for downstream LLM + embeddings


def remove_references_section(text: str) -> str:
    patterns = [
        r"\nreferences\b.*",
        r"\nbibliography\b.*"
    ]
    for pattern in patterns:
        text = re.split(pattern, text, flags=re.IGNORECASE | re.DOTALL)[0]
    return text


def remove_inline_citations(text: str) -> str:
    # Remove [1], (2020), [12,13]
    text = re.sub(r"\[[0-9,\s]+\]", "", text)
    text = re.sub(r"\(\d{4}\)", "", text)
    return text


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


MAX_CHARS = 2000  # HARD LIMIT for everything downstream


def truncate_text(text: str, max_chars: int = MAX_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = remove_references_section(text)
    text = remove_inline_citations(text)

    text = re.sub(r"[^\w\s.,;:()\-+=/%]", "", text)

    text = normalize_whitespace(text)
    text = truncate_text(text)  # ← enforced here

    return text
