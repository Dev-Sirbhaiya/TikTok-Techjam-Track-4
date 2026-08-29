"""EMA within-session preference vectors -- the concrete implementation of D-PROFILE's "long-term
user profile" interpretation (implementation/06_DECISION_LOG.md). Additive ranking-time boost only,
never a retrieval filter.
"""
from __future__ import annotations

from typing import Optional

import numpy as np


def _ema(prev: Optional[np.ndarray], new: np.ndarray, alpha: float) -> np.ndarray:
    if prev is None:
        v = new
    else:
        v = alpha * new + (1 - alpha) * prev
    norm = np.linalg.norm(v)
    return v / (norm + 1e-9)


def update_preference_vectors(state, turn_embedding: Optional[np.ndarray], signal: str,
                               alpha_pos: float = 0.35, alpha_neg: float = 0.35) -> None:
    if turn_embedding is None:
        return
    if signal == "positive":
        state.pref_vector_pos = _ema(state.pref_vector_pos, turn_embedding, alpha_pos)
    elif signal == "negative":
        state.pref_vector_neg = _ema(state.pref_vector_neg, turn_embedding, alpha_neg)


def preference_boost(product_embedding: Optional[np.ndarray], state, lam: float = 0.15, mu: float = 0.10) -> float:
    if product_embedding is None:
        return 0.0
    boost = 0.0
    if state.pref_vector_pos is not None:
        boost += lam * float(np.dot(product_embedding, state.pref_vector_pos))
    if state.pref_vector_neg is not None:
        boost -= mu * float(np.dot(product_embedding, state.pref_vector_neg))
    return boost


def vector_stability(prev: Optional[np.ndarray], current: Optional[np.ndarray]) -> float:
    """Turn-over-turn cosine similarity between consecutive preference vectors -- the metric the
    Embedding Explorer visualization plots (NOT raw norm, which is always ~=1 since _ema()
    re-normalizes every update; see implementation/13_FRONTEND_VISUALIZATION.md's round-2 fix)."""
    if prev is None or current is None:
        return 0.0
    return float(np.dot(prev, current))
