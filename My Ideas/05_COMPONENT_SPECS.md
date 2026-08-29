# 05 — Component Specs

Concrete-enough-to-implement-from specs for every Phase 0 module, plus interface sketches for the
gated Phase 2/3 modules. Function signatures are suggestions, not contracts — adapt to whatever the
real evaluator harness expects once `docs/04_OPEN_QUESTIONS.md` Q1/Q2/Q9 are confirmed.

## `agent/state.py` — DialogState

```python
from dataclasses import dataclass, field

@dataclass
class DialogState:
    slots: dict = field(default_factory=dict)              # {"category": "dress", "price_max": 80}
    rejected_hard: dict = field(default_factory=dict)      # {"color": ["green"]}
    rejected_soft: dict = field(default_factory=dict)      # {"style": ["floral"]}  -- confidence-weighted
    rejected_soft_confidence: dict = field(default_factory=dict)  # {"style": 0.5}  0=weak, 1=strong
    buying_intent_score: float = 0.5
    turn_count: int = 0
    candidate_pool: list = field(default_factory=list)     # current ranked parent_asin list
    pool_entropy: float = 0.0
    facet_utility_history: dict = field(default_factory=dict)  # Phase 2 bandit input only

    @property
    def turns_remaining(self) -> int:
        return 10 - self.turn_count


def diff_and_update(state: DialogState, new_message: str, nlu_output: dict) -> DialogState:
    """
    nlu_output is whatever the NLU/intent-detector step produces for this turn:
      {
        "slot_updates": {"price_max": 80},        # only fields that changed
        "rejection_signal": {"type": "explicit"|"comparative"|"vague"|"implicit",
                              "attribute": "color"|None, "value": "green"|None},
        "override_detected": bool,                 # e.g. "actually, forget the dress" style pivot
      }
    Only overwrite slot fields that actually changed -- do not reset the whole state on an
    ambiguous message. See Decision D2 in 03_DECISION_LOG.md for why a full reset kills MTTC.
    """
    for k, v in nlu_output.get("slot_updates", {}).items():
        state.slots[k] = v

    rej = nlu_output.get("rejection_signal")
    if rej:
        _apply_rejection(state, rej)

    if nlu_output.get("override_detected"):
        _handle_override(state, nlu_output)

    state.turn_count += 1
    return state


def _apply_rejection(state: DialogState, rej: dict):
    """Three-tier confidence system -- see Decision D5."""
    if rej["type"] == "explicit" and rej["attribute"]:
        state.rejected_hard.setdefault(rej["attribute"], []).append(rej["value"])
    elif rej["type"] in ("comparative", "vague") and rej["attribute"]:
        state.rejected_soft.setdefault(rej["attribute"], []).append(rej["value"])
        state.rejected_soft_confidence[rej["attribute"]] = 0.5
    elif rej["type"] == "implicit":
        # do NOT invent a specific attribute here -- log only a generic weak negative
        # on the last-shown top candidate, per the correction in Decision D5.
        state.rejected_soft.setdefault("_generic", []).append(state.candidate_pool[0] if state.candidate_pool else None)
        state.rejected_soft_confidence["_generic"] = 0.2


def _handle_override(state: DialogState, nlu_output: dict):
    """Clear only the slots the override actually contradicts, keep the rest.
    e.g. occasion changes but size/color/budget usually don't -- see the worked
    example in 01_ARCHITECTURE.md and the original design document's Part 3.2."""
    for k in nlu_output.get("invalidated_slots", []):
        state.slots.pop(k, None)
```

## `agent/rejection_memory.py` — filter application

```python
def apply_rejection_filter(candidates: list[dict], state: DialogState) -> list[dict]:
    """
    candidates: list of product dicts with at least {"parent_asin", "attributes": {...}}
    Strips hard-rejected attribute values entirely; applies a score penalty (not removal)
    for soft-rejected ones, scaled by confidence.
    """
    filtered = []
    for c in candidates:
        if _matches_hard_rejection(c, state.rejected_hard):
            continue  # dropped entirely
        penalty = _soft_rejection_penalty(c, state.rejected_soft, state.rejected_soft_confidence)
        c["_rejection_penalty"] = penalty  # ranker.py reads this
        filtered.append(c)
    return filtered
```

## `agent/retrieval.py` — hybrid retrieval with RRF

```python
def retrieve_candidates(query_text: str, state: DialogState, catalog_index, k_pool=50) -> list[dict]:
    """
    catalog_index bundles a BM25 index (e.g. rank_bm25.BM25Okapi) and a dense index
    (numpy matrix of embeddings + a sentence-transformers model, or faiss-cpu in-memory).
    """
    bm25_ranked = catalog_index.bm25_search(query_text, top_n=100)      # list of parent_asin, ranked
    dense_ranked = catalog_index.dense_search(query_text, top_n=100)    # list of parent_asin, ranked
    fused = reciprocal_rank_fusion([bm25_ranked, dense_ranked], k=60)
    return catalog_index.hydrate(fused[:k_pool])  # attach full product dicts


def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60) -> list[str]:
    """Standard RRF: score(doc) = sum(1 / (k + rank)) across all lists it appears in.
    Do NOT hand-tune a weighted sum of raw scores -- see Decision D1."""
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)
```

## `agent/question_selector.py` — information-gain facet selection

```python
def select_best_question(candidates: list[dict], already_filled_slots: set[str],
                          attribute_enum: list[str]) -> str | None:
    """
    attribute_enum: the CONFIRMED list from Q2 in 04_OPEN_QUESTIONS.md -- do not
    invent facet names outside this list when actually asking (internal slots can
    be richer, see Decision D10, but the externally-asked attribute must be one of these).
    Returns the attribute with the lowest expected remaining pool size, or None if
    every candidate attribute is already filled / pool is already small enough to commit.
    """
    best_attr, best_expected_size = None, float("inf")
    for attr in attribute_enum:
        if attr in already_filled_slots:
            continue
        expected_size = expected_pool_reduction(candidates, attr)
        if expected_size < best_expected_size:
            best_attr, best_expected_size = attr, expected_size
    return best_attr


def expected_pool_reduction(candidates: list[dict], attribute: str) -> float:
    """
    Group candidates by their value for `attribute`. For each possible value,
    compute the resulting pool size if the user's answer matched that value.
    Return the *expected* pool size, weighted by how common each value currently is.
    Equivalent to (and can be framed in the writeup as) Shannon entropy reduction.
    """
    from collections import Counter
    values = [c["attributes"].get(attribute) for c in candidates if c["attributes"].get(attribute)]
    if not values:
        return float(len(candidates))  # asking about this attribute wouldn't narrow anything
    counts = Counter(values)
    total = len(values)
    return sum((count / total) * count for count in counts.values())
```

## `agent/turn_policy.py` — ask vs. commit decision

```python
def should_ask_or_commit(state: DialogState, top_candidate_score: float, pool_size: int,
                          base_threshold: float = 0.7, decay_rate: float = 0.05) -> str:
    """
    Returns "commit", "ask", or "both" (if Q1 confirms combined turns are allowed --
    see Decision D14). Threshold gets more lenient as turns run out so the system is
    forced toward a decision before hitting the 10-turn cap.
    """
    turns_left = state.turns_remaining
    threshold = base_threshold - (decay_rate * (10 - turns_left))
    if top_candidate_score >= threshold or turns_left <= 1:
        return "commit"
    if pool_size <= 10:
        return "both"  # confident enough to show candidates AND still narrow further
    return "ask"
```

**If running out of turns with only moderate confidence** (per the original use-case notes): don't burn
the last turn on a question with no payoff — return "here are my top 3 guesses" rather than asking a
clarifying question that can't be acted on before the cap.

## `agent/ranker.py` — scoring function

```python
def rank_candidates(candidates: list[dict], state: DialogState, weights: dict) -> list[dict]:
    """
    weights: {"rrf_score": 1.0, "rejection_penalty": -2.0, "price_fit": 0.5, ...}
    -- tunable, ideally via the Phase 3 offline optimization pass (Decision D13)
    rather than hand-guessed. Start with a simple weighted sum here; this is a
    scoring FUNCTION, not the retrieval fusion (which must stay RRF-based per D1).
    """
    for c in candidates:
        c["_score"] = sum(weights.get(k, 0.0) * c.get(k, 0.0) for k in weights)
        c["_score"] += weights.get("rejection_penalty", 0.0) * c.get("_rejection_penalty", 0.0)
    return sorted(candidates, key=lambda c: c["_score"], reverse=True)


def llm_rerank(shortlist: list[dict], state: DialogState, llm_client) -> list[dict]:
    """Only call this on a short list (top ~20-30), per Decision D12 -- decision-path
    compression. Skip entirely if len(shortlist) <= 3; nothing left to meaningfully re-rank."""
    if len(shortlist) <= 3:
        return shortlist
    # ... construct a prompt from state + shortlist, parse a re-ordering back out
```

## `agent/agent.py` — orchestrator (the turn loop)

```python
def respond(session_id: str, user_message: str, turn: int, top_k: int, state_store: dict,
            catalog_index, attribute_enum: list[str]) -> dict:
    state = state_store.get(session_id, DialogState())

    nlu_output = run_nlu(user_message, state)                      # intent_detector.py
    state = diff_and_update(state, user_message, nlu_output)       # state.py

    candidates = retrieve_candidates(user_message, state, catalog_index)   # retrieval.py
    candidates = apply_rejection_filter(candidates, state)                 # rejection_memory.py
    ranked = rank_candidates(candidates, state, weights=DEFAULT_WEIGHTS)   # ranker.py

    state.candidate_pool = [c["parent_asin"] for c in ranked]
    top_score = ranked[0]["_score"] if ranked else 0.0

    decision = should_ask_or_commit(state, top_score, len(ranked))         # turn_policy.py

    response = {"message": "", "ask_attribute": None, "recommendations": []}
    if decision in ("ask", "both"):
        response["ask_attribute"] = select_best_question(
            ranked, set(state.slots.keys()), attribute_enum)               # question_selector.py
        response["message"] = phrase_question(response["ask_attribute"], state)
    if decision in ("commit", "both"):
        response["recommendations"] = [c["parent_asin"] for c in ranked[:top_k]]
        if decision == "commit":
            response["message"] = phrase_recommendation(ranked[:top_k], state)

    state_store[session_id] = state
    return response
```

## Phase 2+ module interface sketches (build only if gated ablation wins)

```python
# agent/multi_interest.py -- only if Decision D3's K-ablation wins
def route_turn_to_interests(utterance_embedding, interest_vectors: list, attention_fn) -> list[float]:
    """Returns soft assignment weights over existing interest vectors; spawn a new
    one if none score above a similarity threshold. See 01_ARCHITECTURE.md for the
    context-conditioned encoding formula."""

def fuse_multi_interest_scores(product, interest_vectors: list, probabilities: list[float]) -> float:
    """Score(product) = sum(p_k * cosine_sim(v_k, product_embedding))"""

# agent/action_policy.py -- only if Decision D11's bandit-vs-static ablation wins
def update_facet_value_estimate(facet: str, state_features: dict, observed_delta_h: float,
                                 alpha: float = 0.3) -> None:
    """Q_{t+1}(a|context) = (1-alpha) * Q_t(a|context) + alpha * observed_delta_h
    -- LIVE reward is entropy reduction ONLY, never target-aware terms. See Decision D7."""
```

## Tech stack (unchanged from the original teammate plan, endorsed as-is)

| Component | Choice | Why |
|---|---|---|
| Language | Python | Matches starter kit and evaluator |
| Retrieval | `rank_bm25` + `sentence-transformers` | Free, in-memory, no external vector DB |
| Vector index | numpy cosine similarity, or `faiss-cpu` in in-memory mode | Fast enough for 50k products |
| Ranking | Manual scoring function; optional LLM API for top ~20-30 re-rank | Low cost/latency, no fine-tuning needed |
| Dialog state | Plain Python dataclass / dict | No database needed, sessions are isolated |
| Evaluation | The organizer's provided local evaluator | Use theirs so numbers are trustworthy |

## Repo structure (unchanged from the original teammate plan)

```
techjam-shopping-copilot/
├── agent/
│   ├── intent_detector.py
│   ├── state.py
│   ├── retrieval.py
│   ├── rejection_memory.py
│   ├── ranker.py
│   ├── question_selector.py
│   ├── turn_policy.py
│   ├── agent.py
│   ├── multi_interest.py        # Phase 2, only if ablation wins
│   ├── action_policy.py         # Phase 2, only if ablation wins
│   └── comparative.py           # Phase 3
├── data/
│   ├── catalog.json
│   └── dev_sessions.json
├── eval/
│   └── run_evaluator.py
├── tools/
│   └── offline_tune.py          # Phase 3
├── tests/
│   └── test_*.py
├── notebooks/
│   └── exploration.ipynb
└── README.md
```
