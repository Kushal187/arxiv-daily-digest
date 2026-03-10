from __future__ import annotations

import hashlib
import math
from functools import lru_cache


EMBED_DIM = 384


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / magnitude for value in vector]


def _hash_embedding(text: str) -> list[float]:
    vector = [0.0] * EMBED_DIM
    tokens = [token for token in text.lower().split() if token]
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for index in range(EMBED_DIM):
            byte = digest[index % len(digest)]
            vector[index] += (byte / 255.0) - 0.5

    return _normalize(vector)


@lru_cache(maxsize=1)
def _load_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None

    try:
        return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception:
        return None


def embed_text(text: str) -> list[float]:
    model = _load_sentence_transformer()
    if model is None:
        return _hash_embedding(text)

    result = model.encode([text], normalize_embeddings=True)[0]
    return [float(value) for value in result]


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"
