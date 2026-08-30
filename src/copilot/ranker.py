"""Cross-encoder reranking (guaranteed, no-API stage) + optional single-pass listwise LLM booster.
NFR-2: the cross-encoder path must fully function with zero external LLM calls. See
implementation/06_DECISION_LOG.md D-LLM-TIER.
"""
from __future__ import annotations

import json
import re

ENABLE_LLM_BOOSTER = True  # Ablation 4 (implementation/08_ABLATION_MATRIX.md). Claude Haiku
# listwise reranker, ablated on both splits.
#
# RE-VERIFIED 2026-08-30 after a codex review (recovered from the session transcript -- see
# wiki/03_design_log.md's "recovered reviews" entry) found the original ablation used a
# non-deterministic call (no explicit sampling control) and an unbounded timeout. The first fix
# attempt (temperature=0) turned out to be worse than the problem it fixed: the installed
# anthropic SDK doesn't accept that parameter at all, so it crashed every single call and silently
# disabled the booster entirely (the except-and-fallback swallowed the TypeError) -- the earlier
# "re-verified" numbers under that broken state were spuriously IDENTICAL to OFF. Removed the
# unsupported kwarg, kept the bounded timeout (8s, 0 retries -- also from the same review, a real
# fix: the SDK's long default timeout/retry policy could block an ambiguous turn for minutes on a
# slow/unreachable endpoint). Re-ablated with the actually-working fix: validation (n=40) ON
# 0.45/0.303681/7.4/**0.388104** vs OFF 0.425/0.266667/7.6/**0.3605**; training (n=160,
# confirmatory) ON 0.51875/0.321029/6.6625/**0.442434** vs OFF 0.5/0.280952/6.81875/**0.417911** --
# a genuine, consistent win on every metric on both splits. KEPT ENABLED.
#
# CRITICAL CAVEAT, not a formality: NFR-2 / D-LLM-TIER still holds -- the organizer provides no
# hosted model credentials, so `agent.py` only constructs an `llm_client` when `ANTHROPIC_API_KEY`
# is present locally (this session's own `.env`, gitignored, never shipped). The official private-
# set grading environment will almost certainly run WITHOUT this key, meaning `llm_client is None`
# and this entire block never fires regardless of this flag -- the numbers above are real and
# validated, but they describe an optional, environment-dependent ceiling, not the expected scored
# submission result. The guaranteed, always-applicable number is the cross-encoder-only baseline
# (see wiki/08_evaluation_log.md for the current figure). Report both, never just the boosted one.

_LLM_BOOSTER_MODEL = "claude-haiku-4-5-20251001"  # fast/cheap -- this is a reranking nudge, not deep reasoning

_cross_encoder_model = None


def _get_cross_encoder():
    global _cross_encoder_model
    if _cross_encoder_model is None:
        from sentence_transformers import CrossEncoder
        from .model_paths import resolve as _resolve_model_path
        _cross_encoder_model = CrossEncoder(
            _resolve_model_path("ms-marco-MiniLM-L-6-v2", "cross-encoder/ms-marco-MiniLM-L-6-v2"))
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

    if ENABLE_LLM_BOOSTER and llm_client is not None:
        top_n = [c for c, _ in ranked[:12]]
        try:
            boosted = _llm_listwise_rerank(top_n, query, llm_client)
            return boosted + [c for c, _ in ranked[12:]]
        except Exception:
            pass  # NFR-2: any LLM failure (network, parse, quota) falls back to cross-encoder order
    return [c for c, _ in ranked]


def _llm_listwise_rerank(shortlist: list[dict], query: str, llm_client) -> list[dict]:
    """Single-pass listwise rerank, no sliding window (research/03): show the model the whole
    shortlist at once and ask for a best-to-worst permutation, rather than pairwise/windowed
    comparisons that would multiply API calls. Raises on any failure so the caller's `except
    Exception: pass` falls back to the guaranteed cross-encoder order (NFR-2)."""
    listing = "\n".join(f"{i+1}. {_candidate_text(c)}" for i, c in enumerate(shortlist))
    prompt = (
        f"A shopper is looking for: {query or 'a product (no specific details given yet)'}\n\n"
        f"Candidate products:\n{listing}\n\n"
        f"Return ONLY a JSON array of the candidate numbers (1-{len(shortlist)}), reordered from "
        "best match to worst match for the shopper. No other text."
    )
    # Codex review (2026-08-30) correctly flagged that omitting an explicit temperature leaves
    # sampling enabled in principle, risking non-reproducible permutations. The fix attempted here
    # first (temperature=0) does not work: the installed anthropic SDK (1.2.0)'s messages.create()
    # does not accept a `temperature` parameter at all in this API version (confirmed via
    # inspect.signature -- it crashed every single call with TypeError, which the except-and-
    # fallback below silently swallowed, completely disabling the booster without any visible
    # error). Removed the unsupported kwarg. Empirically, repeated identical calls to this
    # endpoint returned byte-identical permutations across 3 trials with no temperature control at
    # all, suggesting this model/endpoint is already low-variance by default -- but this is an
    # observation, not a guarantee, and the underlying concern (no explicit determinism control
    # available in this SDK surface) is a real, documented limitation, not fully resolved.
    response = llm_client.messages.create(
        model=_LLM_BOOSTER_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    match = re.search(r"\[[\d,\s]+\]", text)
    if not match:
        raise ValueError("no JSON array in LLM response")
    order = json.loads(match.group(0))
    if sorted(order) != list(range(1, len(shortlist) + 1)):
        raise ValueError("LLM response is not a valid permutation of the shortlist")
    return [shortlist[i - 1] for i in order]
