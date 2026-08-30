"""Hybrid retrieval: BM25 + dense + metadata, fused via Reciprocal Rank Fusion.

See implementation/04_SYSTEM_DESIGN.md (retrieval.py section) for the design and the codex-review
correction this implements: metadata is a genuine third fusion leg, always active, not only a
Buying-track hard filter.
"""
from __future__ import annotations

from .catalog import CatalogIndex


def retriever_disagreement(bm25_ranked: list[str], dense_ranked: list[str], top_n: int = 20) -> float:
    """0 = BM25 and dense fully agree on the top-N (low ambiguity); 1 = no overlap at all (high
    ambiguity -- a live-computable hint clarification may be worth more than usual). Lives here
    (not phase2/) because it's a cheap, always-safe-to-compute retrieval diagnostic; phase2/voi.py
    holds the GATED decision of whether to actually let it influence the clarify threshold --
    implementation/06_DECISION_LOG.md D6/D7: never conflate a live-computable signal like this
    with anything requiring ground truth the live agent doesn't have."""
    if not bm25_ranked or not dense_ranked:
        return 0.0
    a = set(bm25_ranked[:top_n])
    b = set(dense_ranked[:top_n])
    if not a or not b:
        return 0.0
    overlap = len(a & b) / min(len(a), len(b))
    return 1.0 - overlap


def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60,
                            restrict_to: set | None = None,
                            weights: list[float] | None = None) -> dict[str, float]:
    """Returns {doc_id: fused_score}, NOT just an ordered id list -- callers need the actual score
    (for the entropy gate and preference-boost addition), not only the ranking. Self-caught before
    implementation: the original draft returned only `sorted(scores)` (ids), which would have
    silently forced every downstream `_score` to a meaningless 0.0 placeholder.

    `weights`, if given, must match `ranked_lists` 1:1 -- each leg's contribution is scaled by its
    weight before summing (plain/unweighted RRF when omitted, i.e. every weight is 1.0). Phase 3.5
    (strategy_config.METADATA_RRF_WEIGHT) uses this to test whether the metadata leg -- an exact-
    match signal, unlike BM25/dense's fuzzy relevance -- deserves more trust in the fusion."""
    if weights is None:
        weights = [1.0] * len(ranked_lists)
    scores: dict[str, float] = {}
    for ranked, weight in zip(ranked_lists, weights):
        # CORRECTED per codex review (2026-08-30): a weight of exactly 0.0 -- documented as
        # "drop this leg entirely" -- used to still insert every one of that leg's ids into
        # `scores` with a zero contribution. That made `fused` truthy purely from spurious
        # zero-score entries even when no BM25/dense candidate survived a hard filter, silently
        # suppressing the "hard filter emptied the pool" fallback and letting arbitrary
        # zero-score candidates fill the final pool. A zero-weight leg must contribute nothing.
        if weight == 0.0:
            continue
        for rank, doc_id in enumerate(ranked):
            if restrict_to is not None and doc_id not in restrict_to:
                continue
            scores[doc_id] = scores.get(doc_id, 0.0) + weight / (k + rank + 1)
    return scores


def retrieve_candidates(
    query_text: str,
    slots: dict,
    apply_hard_filter: bool,
    catalog_index: CatalogIndex,
    k_pool: int = 60,
    query_embedding_hook=None,
) -> tuple[list[dict], float]:
    """`apply_hard_filter` is decided by orchestrator.route_retrieval_breadth(), not derived here --
    Phase 1.4 (FR-8): retrieval is a pure mechanism, the orchestrator layer owns strategy decisions
    (this used to inline `buying_intent_score > 0.6` directly in this function).

    `query_embedding_hook`, if given, is forwarded to `catalog_index.dense_search()` -- Phase 3.5
    (phase2/query_nudge.py) uses it to nudge the dense search vector toward accumulated positive
    preference; retrieval.py stays decoupled from phase2/ (no import), same pattern as
    overgenerality.py's utility_fn.

    Returns (candidates, bm25_dense_disagreement) -- Phase 2.3/2.5 (phase2/voi.py) needs the
    disagreement signal, computed here (not recomputed by the caller) since the BM25/dense
    searches already happened -- recomputing them a second time would double retrieval cost."""
    from .strategy_config import BM25_RRF_WEIGHT, DENSE_RRF_WEIGHT, ENABLE_BM25F, METADATA_RRF_WEIGHT

    bm25_ranked = (catalog_index.bm25f_search(query_text, top_n=150) if ENABLE_BM25F
                   else catalog_index.bm25_search(query_text, top_n=150))
    dense_ranked = catalog_index.dense_search(query_text, top_n=150, query_embedding_hook=query_embedding_hook)
    metadata_ranked = catalog_index.metadata_rank(slots, top_n=150)
    disagreement = retriever_disagreement(bm25_ranked, dense_ranked)

    legs = [(bm25_ranked, BM25_RRF_WEIGHT), (dense_ranked, DENSE_RRF_WEIGHT), (metadata_ranked, METADATA_RRF_WEIGHT)]
    legs = [(r, w) for r, w in legs if r]
    if not legs:
        return [], disagreement
    lists = [r for r, _ in legs]
    weights = [w for _, w in legs]

    restrict_to = None
    if apply_hard_filter:
        hard = catalog_index.apply_hard_filters(slots)
        if hard:
            restrict_to = hard

    fused = reciprocal_rank_fusion(lists, restrict_to=restrict_to, weights=weights)
    if not fused and restrict_to is not None:
        # Hard filter was too aggressive and emptied the pool -- fall back to unfiltered fusion
        # rather than returning nothing (never let a filter produce a total dead end).
        fused = reciprocal_rank_fusion(lists, weights=weights)

    top_ids = sorted(fused, key=fused.get, reverse=True)[:k_pool]
    candidates = catalog_index.hydrate(top_ids)
    for c in candidates:
        c["_score"] = fused.get(c["parent_asin"], 0.0)
    return candidates, disagreement
