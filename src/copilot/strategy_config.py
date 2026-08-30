"""Phase 3.1: the tunable strategy surface, in one place.

Before this module existed, the values 3.1 tunes were hardcoded literals scattered across
overgenerality.py, agent.py, and phase2/voi.py -- fine for Phase 0/1's hand-set, spot-checked
values (implementation/10_PRE_REGISTRATION.md exempts those), but exactly what the pre-registration
says needs a genuine train/validation split once a *systematic* search is doing the choosing.

Each constant reads an env-var override at import time, read fresh by every subprocess `tools/
tune_strategy.py` launches -- no monkeypatching, no stale bound-default footguns, and each rollout
is a real, independent process exercising the real code path end to end (the evaluator's own
harness), not a simulated re-scoring of cached candidates.
"""
from __future__ import annotations

import os


def _float(name: str, default: float) -> float:
    v = os.environ.get(name)
    return float(v) if v is not None else default


def _int(name: str, default: int) -> int:
    v = os.environ.get(name)
    return int(v) if v is not None else default


def _bool(name: str, default: bool) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


# overgenerality.should_clarify: the base entropy threshold above which a turn is a clarification
# candidate at all (before phase2/voi.py's disagreement-based adjustment). Phase 0's initial guess.
# Phase 3.1 systematically swept this against the training split (tools/tune_strategy.py) and found
# it's inert across [0.01, 0.7] -- byte-identical TechnicalScore at 0.01/0.2/0.3/0.4/0.5/0.7 -- then
# degrades catastrophically at 0.99 (0.4176 -> 0.188 on the training split). The entropy distribution
# this pipeline actually produces (DEFAULT_TEMPERATURE=0.02's peaked softmax) is effectively bimodal:
# turns are either clearly ambiguous (entropy well above 0.7) or already resolved by another gate
# (pool_size/turns_remaining), with little continuous middle ground for this threshold to discriminate
# within. No value in the searched range beat the default; 0.3 stays, with comfortable margin before
# the degradation cliff. See wiki/08_evaluation_log.md's Phase 3.1 rows for the full sweep.
CLARIFY_BASE_LOW = _float("COPILOT_CLARIFY_BASE_LOW", 0.3)

# overgenerality.should_clarify: don't bother clarifying once the candidate pool is already this
# small -- committing is cheap and a facet question on a tiny pool rarely helps.
CLARIFY_MIN_POOL_TO_BOTHER = _int("COPILOT_CLARIFY_MIN_POOL_TO_BOTHER", 4)

# overgenerality.should_clarify: stop attempting clarification once fewer than
# (10 - CLARIFY_NO_ASK_AFTER_TURN) turns remain, reserving the tail of the session for commits.
CLARIFY_NO_ASK_AFTER_TURN = _int("COPILOT_CLARIFY_NO_ASK_AFTER_TURN", 7)

# phase2/voi.py adjusted_clarify_threshold: how strongly BM25/dense retriever disagreement lowers
# the clarify threshold (kept per Phase 2's ablation -- this tunes its strength, not whether it's on).
VOI_DISAGREEMENT_WEIGHT = _float("COPILOT_VOI_DISAGREEMENT_WEIGHT", 0.15)

# agent.py's per-candidate negative-preference penalty: score -= NEG_BOOST_WEIGHT * cosine(emb, neg_vec).
NEG_BOOST_WEIGHT = _float("COPILOT_NEG_BOOST_WEIGHT", 0.10)

# retrieval.reciprocal_rank_fusion: the metadata leg's weight relative to BM25/dense (both fixed at
# 1.0). Default 1.0 = plain, unweighted RRF (all three legs equal) -- the historical behavior.
# TESTED 2026-08-30 (guaranteed path, both splits): training split showed a clean, monotonic trend
# favoring LOWER weight (0.0 best: TechnicalScore 0.433666 vs baseline 0.425645; every tested value
# above 1.0 regressed sharply, e.g. 3.0 -> 0.329179). But weight=0.0 did NOT replicate on the
# held-out validation split (0.361333 vs baseline 0.376071 -- WORSE, the opposite direction). Per
# 10_PRE_REGISTRATION.md/Ablation 3's explicit rule ("a win only on the training split is
# meaningless by construction"), this is a decline, not a keep -- classic overfitting-to-training-
# split trap. Left at the default 1.0; kept tunable here in case a future session wants to
# investigate further (e.g. whether the effect is scenario-specific, buying vs. browsing) rather
# than a single global weight.
METADATA_RRF_WEIGHT = _float("COPILOT_METADATA_RRF_WEIGHT", 1.0)

# retrieval.reciprocal_rank_fusion: BM25/dense legs' weights relative to each other and to
# METADATA_RRF_WEIGHT above (both were previously hardcoded at 1.0, never tunable). UNTESTED, added
# 2026-08-30 per external research's #2-ranked (by effort-to-impact) suggestion -- cheap, no
# training involved, same overfitting risk any threshold sweep has (existing split discipline
# covers it).
BM25_RRF_WEIGHT = _float("COPILOT_BM25_RRF_WEIGHT", 1.0)
DENSE_RRF_WEIGHT = _float("COPILOT_DENSE_RRF_WEIGHT", 1.0)

# catalog.apply_hard_filters: whether to ALSO hard-restrict on disclosed material/color/style slots,
# not just category/brand/budget. Added 2026-08-30 after tools/diagnose_buying_recall.py found
# 37.5% of buying-scenario targets never reach the fused candidate pool at all (vs. 26.2% for
# browsing), and a --no-hard-filter run confirmed toggling the EXISTING filter changes nothing for
# buying (it only ever restricted on category for most buying sessions -- brand is structurally
# almost never disclosed per resolved-Q2, budget only sometimes). Ablated on both splits despite the
# real risk that material/color/style being single-regex-match, best-effort catalog attributes
# (catalog._attributes_for) could wrongly exclude a genuinely-matching product whose text mentions a
# different material/color first: training (n=160) TechnicalScore 0.476056 vs baseline 0.441967
# (+7.7%); validation (n=40, held out) TechnicalScore 0.445604 vs baseline 0.388292 (+14.8%,
# HitRate@10 +16.7%, MRR +5.8%, MTTC improved) -- a clean win on BOTH splits, not a training-only
# mirage. **ENABLED by default** per the pre-registration's own accept rule (held-out split
# confirms). See wiki/08_evaluation_log.md for the full ablation and wiki/03_design_log.md for the
# diagnostic that found this.
EXTENDED_HARD_FILTER_ATTRS = _bool("COPILOT_EXTENDED_HARD_FILTER_ATTRS", True)

# agent.reset(): whether to seed MultiInterestState from the evaluator-provided
# `user_profile.preference_tags` before turn 1, instead of starting from nothing. UNTESTED, off by
# default pending ablation -- added 2026-08-30 after noticing `user_profile` (a real per-session
# signal the evaluator hands us at reset(), e.g. preference_tags=["fit","comfort","durability"])
# had been received and discarded since Phase 0 ("reserved for Phase 1+ personalization," never
# revisited). This is a per-SESSION prior only -- there is no cross-session user identifier
# anywhere in the session data, so this cannot and does not persist across sessions.
ENABLE_PROFILE_SEEDING = _bool("COPILOT_ENABLE_PROFILE_SEEDING", False)

# agent.py's per-candidate rank-time boost from phase2.quality_boost.bayesian_quality_score(),
# using the catalog's own average_rating/rating_number fields (also unused since Phase 0). UNTESTED,
# off by default pending ablation -- see phase2/quality_boost.py for the shrinkage rationale.
ENABLE_QUALITY_BOOST = _bool("COPILOT_ENABLE_QUALITY_BOOST", False)
QUALITY_BOOST_WEIGHT = _float("COPILOT_QUALITY_BOOST_WEIGHT", 0.05)

# ranker.rerank(): average a second pretrained cross-encoder's (z-scored) score in with the first's,
# instead of trusting one model. UNTESTED, off by default pending ablation -- see ranker.py's
# comment for the full rationale and the margin_skip caveat.
ENABLE_CROSS_ENCODER_ENSEMBLE = _bool("COPILOT_ENABLE_CROSS_ENCODER_ENSEMBLE", False)

# retrieval.retrieve_candidates(): use catalog.bm25f_search() (field-weighted) instead of plain
# catalog.bm25_search() for the BM25 fusion leg. UNTESTED, off by default pending ablation -- see
# catalog.bm25f_search()'s docstring for the rationale.
ENABLE_BM25F = _bool("COPILOT_ENABLE_BM25F", False)


def as_dict() -> dict:
    """For logging a run's exact effective config next to its evaluator result."""
    return {
        "CLARIFY_BASE_LOW": CLARIFY_BASE_LOW,
        "CLARIFY_MIN_POOL_TO_BOTHER": CLARIFY_MIN_POOL_TO_BOTHER,
        "CLARIFY_NO_ASK_AFTER_TURN": CLARIFY_NO_ASK_AFTER_TURN,
        "VOI_DISAGREEMENT_WEIGHT": VOI_DISAGREEMENT_WEIGHT,
        "NEG_BOOST_WEIGHT": NEG_BOOST_WEIGHT,
        "METADATA_RRF_WEIGHT": METADATA_RRF_WEIGHT,
        "EXTENDED_HARD_FILTER_ATTRS": EXTENDED_HARD_FILTER_ATTRS,
        "ENABLE_PROFILE_SEEDING": ENABLE_PROFILE_SEEDING,
        "ENABLE_QUALITY_BOOST": ENABLE_QUALITY_BOOST,
        "QUALITY_BOOST_WEIGHT": QUALITY_BOOST_WEIGHT,
        "ENABLE_CROSS_ENCODER_ENSEMBLE": ENABLE_CROSS_ENCODER_ENSEMBLE,
        "ENABLE_BM25F": ENABLE_BM25F,
        "BM25_RRF_WEIGHT": BM25_RRF_WEIGHT,
        "DENSE_RRF_WEIGHT": DENSE_RRF_WEIGHT,
    }
