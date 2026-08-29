"""Phase 2.3/2.5: value-of-information question selection, upgrading pure entropy with a
retriever-disagreement signal. CRITICAL constraint (implementation/06_DECISION_LOG.md D6/D7):
this must be a LIVE-COMPUTABLE proxy -- BM25/dense ranking disagreement (computed in
retrieval.retriever_disagreement, always cheap and safe), never the ground-truth target rank,
which the live agent never has access to mid-session.

GATED behind USE_DISAGREEMENT_SIGNAL -- ablate on vs. off before enabling by default
(implementation/08_ABLATION_MATRIX.md). Only this module's use of the signal is experimental;
computing the signal itself (retrieval.py) is not.
"""
from __future__ import annotations

USE_DISAGREEMENT_SIGNAL = True  # Ablated on the 40-session validation split (wiki/08_evaluation_log.md):
# ON TechnicalScore=0.4022/MRR=0.2972/MTTC=7.225 vs OFF 0.3933/0.2743/7.325 -- consistent, if modest,
# win across 3 of 4 metrics with HitRate@10 tied. KEPT.


def adjusted_clarify_threshold(base_low: float, disagreement: float, weight: float = 0.15) -> float:
    """Higher retriever disagreement lowers the entropy bar for triggering clarification --
    when BM25 and dense genuinely disagree about what's relevant, that's itself evidence the
    query is ambiguous, independent of what the (possibly still-concentrated) fused score
    distribution looks like on its own. No-op (returns base_low unchanged) if the flag is off."""
    if not USE_DISAGREEMENT_SIGNAL:
        return base_low
    return max(0.05, base_low - weight * disagreement)
