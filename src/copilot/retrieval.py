"""Hybrid retrieval: BM25 + dense + metadata, fused via Reciprocal Rank Fusion.

See implementation/04_SYSTEM_DESIGN.md (retrieval.py section) for the design and the codex-review
correction this implements: metadata is a genuine third fusion leg, always active, not only a
Buying-track hard filter.
"""
from __future__ import annotations

from .catalog import CatalogIndex


def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60,
                            restrict_to: set | None = None) -> dict[str, float]:
    """Returns {doc_id: fused_score}, NOT just an ordered id list -- callers need the actual score
    (for the entropy gate and preference-boost addition), not only the ranking. Self-caught before
    implementation: the original draft returned only `sorted(scores)` (ids), which would have
    silently forced every downstream `_score` to a meaningless 0.0 placeholder."""
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            if restrict_to is not None and doc_id not in restrict_to:
                continue
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return scores


def retrieve_candidates(
    query_text: str,
    slots: dict,
    apply_hard_filter: bool,
    catalog_index: CatalogIndex,
    k_pool: int = 60,
) -> list[dict]:
    """`apply_hard_filter` is decided by orchestrator.route_retrieval_breadth(), not derived here --
    Phase 1.4 (FR-8): retrieval is a pure mechanism, the orchestrator layer owns strategy decisions
    (this used to inline `buying_intent_score > 0.6` directly in this function)."""
    bm25_ranked = catalog_index.bm25_search(query_text, top_n=150)
    dense_ranked = catalog_index.dense_search(query_text, top_n=150)
    metadata_ranked = catalog_index.metadata_rank(slots, top_n=150)

    lists = [r for r in (bm25_ranked, dense_ranked, metadata_ranked) if r]
    if not lists:
        return []

    restrict_to = None
    if apply_hard_filter:
        hard = catalog_index.apply_hard_filters(slots)
        if hard:
            restrict_to = hard

    fused = reciprocal_rank_fusion(lists, restrict_to=restrict_to)
    if not fused and restrict_to is not None:
        # Hard filter was too aggressive and emptied the pool -- fall back to unfiltered fusion
        # rather than returning nothing (never let a filter produce a total dead end).
        fused = reciprocal_rank_fusion(lists)

    top_ids = sorted(fused, key=fused.get, reverse=True)[:k_pool]
    candidates = catalog_index.hydrate(top_ids)
    for c in candidates:
        c["_score"] = fused.get(c["parent_asin"], 0.0)
    return candidates
