"""Cross-encoder reranking (guaranteed, no-API stage) + optional single-pass listwise LLM booster.
NFR-2: the cross-encoder path must fully function with zero external LLM calls. See
implementation/06_DECISION_LOG.md D-LLM-TIER.
"""
from __future__ import annotations

_cross_encoder_model = None


def _get_cross_encoder():
    global _cross_encoder_model
    if _cross_encoder_model is None:
        from sentence_transformers import CrossEncoder
        _cross_encoder_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _cross_encoder_model


def _state_to_query_text(state, query_terms: list[str]) -> str:
    parts = list(dict.fromkeys(query_terms))  # de-dup, preserve order
    for key in ("category", "material", "color", "size", "style", "use_case", "budget"):
        v = state.slots.get(key)
        if v and str(v) not in parts:
            parts.append(str(v))
    return " ".join(str(p) for p in parts)[:800]


def _candidate_text(c: dict) -> str:
    p = c.get("product", {})
    title = p.get("title") or ""
    features = p.get("features") or []
    feat_text = " ".join(str(f) for f in features[:3]) if isinstance(features, list) else ""
    price = p.get("price")
    price_text = f"price ${price}" if isinstance(price, (int, float)) else ""
    return f"{title} {feat_text} {price_text}".strip()[:400]


def rerank(shortlist: list[dict], state, query_terms: list[str], margin_skip: float = 0.35,
           llm_client=None) -> list[dict]:
    """`margin_skip` is on the cross-encoder's own raw output scale, which is a different
    (uncalibrated) scale from the RRF-based `_score`/entropy fields elsewhere in this pipeline --
    same class of scale-calibration issue as `overgenerality.DEFAULT_TEMPERATURE`. It only affects
    *whether* the confidence-based early-exit fires (an efficiency optimization), never
    correctness (the non-early-exit path produces the same ranking either way) -- calibrate
    empirically in Phase 1.3 once real evaluator data is available, same as the entropy gate."""
    if len(shortlist) <= 3:
        return shortlist
    try:
        model = _get_cross_encoder()
        query = _state_to_query_text(state, query_terms)
        pairs = [(query, _candidate_text(c)) for c in shortlist]
        scores = model.predict(pairs)
    except Exception:
        # Cross-encoder unavailable (e.g. model not downloaded) -- degrade to fused-score order
        # rather than failing the turn. NFR-2: never a hard dependency.
        return sorted(shortlist, key=lambda c: -c.get("_score", 0.0))

    for c, s in zip(shortlist, scores):
        c["_cross_encoder_score"] = float(s)  # kept distinct from the RRF-scale `_score`
    ranked = sorted(zip(shortlist, scores), key=lambda t: -t[1])
    if len(ranked) > 1 and (ranked[0][1] - ranked[1][1]) >= margin_skip:
        return [c for c, _ in ranked]

    if llm_client is not None:
        top_n = [c for c, _ in ranked[:12]]
        try:
            boosted = _llm_listwise_rerank(top_n, state, llm_client)
            return boosted + [c for c, _ in ranked[12:]]
        except Exception:
            pass
    return [c for c, _ in ranked]


def _llm_listwise_rerank(shortlist: list[dict], state, llm_client) -> list[dict]:  # pragma: no cover
    """Single-pass listwise rerank, no sliding window (research/03) -- stubbed until an LLM client
    is actually configured (Phase 0 does not require one, per NFR-2 / D-LLM-TIER)."""
    raise NotImplementedError("LLM booster not configured in Phase 0 -- caller must catch and fall back")
