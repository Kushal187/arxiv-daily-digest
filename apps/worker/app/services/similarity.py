from __future__ import annotations

import numpy as np


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0

    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    norm_a = np.linalg.norm(a) or 1.0
    norm_b = np.linalg.norm(b) or 1.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def batch_cosine_similarity(target: list[float], candidates: list[list[float]]) -> list[float]:
    """Compute cosine similarity between one vector and many candidates using numpy."""
    if not target or not candidates:
        return []

    t = np.asarray(target, dtype=np.float64)
    mat = np.asarray(candidates, dtype=np.float64)
    norm_t = np.linalg.norm(t) or 1.0
    norms = np.linalg.norm(mat, axis=1)
    norms[norms == 0] = 1.0
    scores = mat @ t / (norms * norm_t)
    return scores.tolist()


def max_similarity(target: list[float], candidates: list[list[float]]) -> float:
    """Return the maximum cosine similarity between target and a set of candidate vectors."""
    if not candidates:
        return 0.0

    scores = batch_cosine_similarity(target, candidates)
    return max(scores) if scores else 0.0
