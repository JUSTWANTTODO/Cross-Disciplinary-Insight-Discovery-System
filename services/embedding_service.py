# services/embedding_service.py
import math
import re
from typing import List, Dict
import streamlit as st
from services.genai_client import get_genai_client

# --------------------------------------------------
# Constants
# --------------------------------------------------
EMBEDDING_MODEL = "text-embedding-004"
QUERY_MIN_LENGTH = 10
DOC_MIN_LENGTH = 30
CHUNK_SIZE = 500
MAX_CHUNKS = 5   # 🔒 HARD SAFETY LIMIT


# --------------------------------------------------
# Text normalization
# --------------------------------------------------
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


# --------------------------------------------------
# Embedding utility (SAFE + CACHED)

def embed_text(text: str, min_length: int = 10) -> List[float]:
    if not text or len(text.strip()) < min_length:
        return []

    try:
        client = get_genai_client()

        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=normalize_text(text)
        )

        vector = response.embeddings[0].values

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0:
            return []

        return [x / norm for x in vector]

    except Exception as e:
        print(f"[Embedding Error] {e}")
        return []


# --------------------------------------------------
# Similarity
# --------------------------------------------------
def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    return sum(a * b for a, b in zip(vec_a, vec_b))


# --------------------------------------------------
# Ranking logic (SAFE)
# --------------------------------------------------
def rank_papers_by_similarity(
    query_text: str,
    papers: List[Dict],
    top_k: int = 5
) -> List[Dict]:

    query_embedding = embed_text(query_text, min_length=QUERY_MIN_LENGTH)

    if not query_embedding:
        print("[Embedding Warning] Query embedding failed, returning fallback results")
        return [
            {**p, "similarity_score": 0.0}
            for p in papers[:top_k]
        ]

    scored_papers = []

    for paper in papers:
        abstract = paper.get("abstract", "").strip()
        if not abstract:
            continue

        # 🔒 LIMIT chunks to prevent runaway embedding calls
        chunks = [
            abstract[i:i + CHUNK_SIZE]
            for i in range(0, len(abstract), CHUNK_SIZE)
        ][:MAX_CHUNKS]

        best_score = 0.0

        for chunk in chunks:
            chunk_embedding = embed_text(chunk, min_length=DOC_MIN_LENGTH)
            if not chunk_embedding:
                continue

            best_score = max(
                best_score,
                cosine_similarity(query_embedding, chunk_embedding)
            )

        scored_papers.append({
            **paper,
            "similarity_score": round(best_score, 4)
        })

    if not scored_papers:
        return [
            {**p, "similarity_score": 0.0}
            for p in papers[:top_k]
        ]

    scored_papers.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored_papers[:top_k]
