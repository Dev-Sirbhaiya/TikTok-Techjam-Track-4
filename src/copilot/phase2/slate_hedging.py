"""Phase 3.5: portfolio/slate hedging, gated behind ENABLE_SLATE_HEDGING.

Motivated by a concrete diagnostic finding, not speculation (tools/calibration_check.py, run
2026-08-30 against the full 200-session dev set): sessions that reach a genuinely FORCED commit
(out of turns, or should_clarify says stop asking) rather than resolving earlier during an "ask"
turn's already-populated recommendations are overwhelmingly still highly ambiguous at that point
(100% of them measured at commit-time entropy 0.7-1.0) and hit at a dismal 2.97% rate. Pure
top-K-by-score recommends near-duplicates of the single most-likely interpretation, which is a poor
bet exactly when that interpretation is least likely to be right.

Original build-plan framing ("esp. if 2.1's multi-interest is kept") no longer applies -- 2.1 was
cut in Phase 2 (its spawn condition never triggers on this dataset's single-hidden-target sessions,
see phase2/multi_interest.py) -- so this hedges across FACET diversity in the ranked candidate pool
itself, not across multiple tracked interest vectors.
"""
from __future__ import annotations

ENABLE_SLATE_HEDGING = True  # Ablated 2026-08-30 (guaranteed path, LLM booster off to isolate the
# effect): validation split (n=40) ON 0.376071/0.45/0.270238/7.5 vs OFF 0.375938/0.45/0.269792/7.5
# -- essentially flat (too few forced-commit sessions at this sample size to show an effect).
# Training split (n=160, confirmatory): ON 0.425645/0.5125/0.281734/6.75625 vs OFF
# 0.417604/0.5/0.280345/6.825 -- a real, modest win (+1.9% TechnicalScore, +2.5% HitRate@10), gains
# concentrated in `buying` (+7.7% hit rate) exactly as the calibration finding predicted (buying's
# hard-filtered pools are a common source of high-entropy forced commits), zero regression on any
# scenario. KEPT ENABLED.

HEDGE_ENTROPY_THRESHOLD = 0.7  # matches the calibration finding: forced-commit sessions cluster here
_RESERVED_TOP = 0.6  # fraction of top_k slots kept as pure best-by-score; the rest hedge for diversity
_DIVERSITY_FACETS = ("color", "material", "style", "category")


def hedge_slate(ranked: list[dict], top_k: int, entropy: float) -> list[dict]:
    """Reserve the top slots for the highest-confidence matches; when the pool is still
    ambiguous at commit time, fill the remaining slots by greedily maximizing facet diversity
    among the candidates that didn't make the reserved cut, instead of continuing straight down
    the same (possibly near-duplicate) score-ranked list. No-op below the entropy threshold or
    once the reserved slots already cover the full request."""
    if not ENABLE_SLATE_HEDGING or entropy < HEDGE_ENTROPY_THRESHOLD or len(ranked) <= top_k:
        return ranked[:top_k]

    reserved_n = max(1, int(top_k * _RESERVED_TOP))
    slate = ranked[:reserved_n]
    seen_values = {facet: {c.get("attributes", {}).get(facet) for c in slate} for facet in _DIVERSITY_FACETS}

    remaining = ranked[reserved_n:]
    hedged: list[dict] = []
    for c in remaining:
        if len(slate) + len(hedged) >= top_k:
            break
        attrs = c.get("attributes", {})
        introduces_new = any(
            attrs.get(facet) is not None and attrs.get(facet) not in seen_values[facet]
            for facet in _DIVERSITY_FACETS
        )
        if introduces_new:
            hedged.append(c)
            for facet in _DIVERSITY_FACETS:
                if attrs.get(facet) is not None:
                    seen_values[facet].add(attrs[facet])

    slots_left = top_k - len(slate) - len(hedged)
    if slots_left > 0:
        already_in = {id(c) for c in slate + hedged}
        backfill = [c for c in remaining if id(c) not in already_in][:slots_left]
        hedged.extend(backfill)

    return slate + hedged
