"""Phase 2.1: multi-interest hypothesis vectors (K>1), gated behind ENABLE_MULTI_INTEREST.

implementation/06_DECISION_LOG.md D3 -- highest-scrutiny item in the whole corpus: MIND/ComiRec are
trained architectures with no reusable checkpoint; this inherits the *idea* (K vectors, soft
routing, probabilistic fusion), not their evidence. Mandatory K-sweep ablation before shipping;
"if K=1 ties or wins, do not ship K>1" is the explicit governing rule, not a formality.

Scope note: given real time constraints in a 72-hour build, this tests K=2 vs K=1 only (not the
full K=1/2/3/4 sweep implementation/08_ABLATION_MATRIX.md Ablation 1 describes) -- if K=2 doesn't
clearly beat K=1, there is no reason to test K=3/4 (more hypotheses is strictly more failure
surface for a mechanism that isn't even earning its keep at K=2).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

ENABLE_MULTI_INTEREST = False  # Ablated on the 40-session validation split (wiki/08_evaluation_log.md):
# K=2 TechnicalScore=0.3649/HitRate@10=0.425/MRR=0.283 vs K=1 (same commit) 0.3825/0.45/0.298 --
# K=1 wins on every metric. Per the explicit governing rule ("if K=1 ties or wins, do not ship
# K>1"), multi-interest is DISABLED. Module kept for the writeup's "tried, measured, cut" record.
SPAWN_THRESHOLD = 0.35  # cosine similarity below which a turn's signal spawns a 2nd hypothesis
K_MAX = 2


class MultiInterestState:
    """Lives alongside (not replacing) DialogState.pref_vector_pos -- when disabled, behaves as a
    single-vector pass-through so the K=1 control path is exactly Phase 1's preference.py, not a
    reimplementation that could itself introduce discrepancies."""

    def __init__(self) -> None:
        self.vectors: list[np.ndarray] = []
        self.weights: list[float] = []  # naive turn-count-based mass per hypothesis

    def update(self, turn_embedding: Optional[np.ndarray], alpha: float = 0.35) -> None:
        if turn_embedding is None:
            return
        if not ENABLE_MULTI_INTEREST or not self.vectors:
            self._update_single(turn_embedding, alpha)
            return
        sims = [float(np.dot(turn_embedding, v)) for v in self.vectors]
        best_idx = int(np.argmax(sims))
        if sims[best_idx] < SPAWN_THRESHOLD and len(self.vectors) < K_MAX:
            self.vectors.append(turn_embedding / (np.linalg.norm(turn_embedding) + 1e-9))
            self.weights.append(1.0)
        else:
            v = alpha * turn_embedding + (1 - alpha) * self.vectors[best_idx]
            self.vectors[best_idx] = v / (np.linalg.norm(v) + 1e-9)
            self.weights[best_idx] += 1.0

    def _update_single(self, turn_embedding: np.ndarray, alpha: float) -> None:
        if not self.vectors:
            self.vectors = [turn_embedding / (np.linalg.norm(turn_embedding) + 1e-9)]
            self.weights = [1.0]
        else:
            v = alpha * turn_embedding + (1 - alpha) * self.vectors[0]
            self.vectors[0] = v / (np.linalg.norm(v) + 1e-9)

    def boost(self, product_embedding: Optional[np.ndarray], lam: float = 0.15) -> float:
        if product_embedding is None or not self.vectors:
            return 0.0
        total_w = sum(self.weights) or 1.0
        probs = [w / total_w for w in self.weights]
        return lam * sum(p * float(np.dot(product_embedding, v)) for p, v in zip(probs, self.vectors))
