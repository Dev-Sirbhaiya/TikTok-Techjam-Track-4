"""Phase 3.5: nudge the dense-retrieval QUERY embedding itself toward accumulated positive
preference signal, gated behind ENABLE_QUERY_VECTOR_NUDGE.

Complementary to, not a replacement for, preference.py/multi_interest.py's existing ranking-time
boost (FR-7, Phase 0/2.1): that only REORDERS candidates BM25/dense-on-text already fetched into
the pool -- it can never recover a candidate that text-based retrieval missed entirely. This nudges
the vector retrieval itself uses to search, so a positively-revealed preference that the
accumulated query TEXT doesn't capture well (e.g. a style/aesthetic signal that's more legible in
embedding space than in the literal disclosed words) has a chance to pull in genuinely new
candidates, not just reorder the ones already found.

Distinct from Phase 3.2's cut comparative-feedback idea: that needed the simulator to critique
SHOWN items ("closer to the second one"), which it structurally cannot produce
(implementation/06_DECISION_LOG.md D9). This uses signal the simulator already reliably produces in
abundance -- ordinary revealed slot values (wiki/09_simulator_mechanics.md) -- already flowing into
`preference.py`/`multi_interest.py`'s tracked vectors; it just also applies that vector one stage
earlier, at retrieval time.
"""
from __future__ import annotations

from typing import Optional

ENABLE_QUERY_VECTOR_NUDGE = False  # Ablated 2026-08-30 (guaranteed path, LLM booster off, slate
# hedging on to isolate this mechanism's own effect): validation split (n=40) ON 0.377333/0.45/
# 0.269444/7.425 vs OFF 0.376071/0.45/0.270238/7.5 -- essentially a wash. Training split (n=160,
# confirmatory) ON 0.415642/0.5/0.27589/6.85625 vs OFF 0.425645/0.5125/0.281734/6.75625 -- a
# consistent REGRESSION on every metric on the larger split (browsing and buying both down).
# Plausible cause: nudging only the dense leg's search vector away from the literal current-turn
# text reduces the BM25/dense complementarity RRF fusion relies on (BM25 still anchors to the raw
# text; dense now drifts toward a coarser historical average), rather than adding genuinely new
# recall the way the motivating idea intended. CUT -- a well-motivated idea that didn't earn its
# keep on this data. Module kept for the writeup's "tried, measured, cut" record.

NUDGE_WEIGHT = 0.2  # blend weight toward the accumulated preference vector; 0 = no-op


def nudge_query_embedding(query_embedding, preference_vector: Optional["object"],
                           weight: float = NUDGE_WEIGHT):
    """Blend the text-derived query embedding with the accumulated positive-preference vector and
    renormalize. No-op (returns `query_embedding` unchanged) when disabled, when no preference
    signal has been accumulated yet (early-session turns), or when either input is missing."""
    if not ENABLE_QUERY_VECTOR_NUDGE or preference_vector is None or query_embedding is None:
        return query_embedding
    import numpy as np
    blended = (1 - weight) * query_embedding + weight * preference_vector
    norm = np.linalg.norm(blended)
    return blended / norm if norm > 1e-9 else query_embedding
