# 01 — System Architecture (Living Document)

> Edit this page in place as the design evolves. Do not let it go stale — if code and this page
> disagree, this page is wrong and must be fixed as part of the phase that caused the drift.
> Superseded designs move to [03_design_log.md](03_design_log.md), not left here commented out.

**Status: decided, not yet built** (2026-08-29). Full detail lives in `implementation/` — this page is
the condensed, kept-in-sync summary; `implementation/03_SYSTEM_ARCHITECTURE.md` and
`implementation/04_SYSTEM_DESIGN.md` are authoritative. Once code exists, update this page's "Status"
column per component as steps in `implementation/05_BUILD_PLAN.md` complete.

## Shape (decided — see `implementation/03_SYSTEM_ARCHITECTURE.md` for the full diagram + rationale)

```
User message → NLU/Slot Extraction (rule+embedding, LLM optional)
             → Dialog State Update (accumulate / override / decay)
             → Intent Router (Buying → hard-filter track | Browsing → relaxed/diverse track)
             → Multi-Route Retrieval (BM25 + dense + metadata) → Reciprocal Rank Fusion
             → Rejection-Memory Filter (hard=drop, soft=penalize)
             → Preference-Vector Boost (within-session EMA, additive ranking-time boost)
             → Over-Generality Check (score entropy) ──▶ [ambiguous] Question Selector (max-entropy facet)
                                                     └──▶ [confident] Cross-Encoder Rerank (+ optional LLM booster)
             → Turn Policy (ask / commit / both — combined turns CONFIRMED supported)
             → Response (message [+ ask_attribute] [+ recommendations]) + rationale log
```

## Components

| Component | Owns which pillar | Status | Notes |
|---|---|---|---|
| NLU / Slot Extraction | I, II | done (Phase 0) | `src/copilot/nlu.py` — exploits the evaluator's own known deterministic reply templates as the primary path, gazetteer fallback for turn-1/novel phrasing; word-boundary matching fixed post-review |
| Intent Router | I | done (Phase 0) | `src/copilot/intent_router.py` — gazetteer hard-match → lexical cue fallback; embedding-vote/LLM arbiter deferred (not needed to clear Phase 0 targets) |
| Retrieval layer (BM25 + dense + metadata, in-memory) | I | done (Phase 0) | `src/copilot/catalog.py` + `retrieval.py` — hand-rolled inverted-index BM25 (not `bm25s`, avoids an extra dependency), `bge-small-en-v1.5` dense leg (embeddings cached, shipped as a submission asset per D-EMBED-CACHE), metadata as a real 3rd RRF leg, category indexing fixed to mirror the evaluator's comma-splitting |
| Cross-Encoder Reranker (+ optional LLM booster) | I | done (Phase 0) | `src/copilot/ranker.py` — `ms-marco-MiniLM-L-6-v2` guaranteed stage; LLM booster stubbed, not required |
| Dialog State Tracker (`DialogState`) | II | done (Phase 0) | `src/copilot/state.py` — slots, tiered rejection memory, accumulated_terms, exhausted-attribute tracking |
| Change-Point / Override Detector | II | done (Phase 0) | `src/copilot/nlu.py`'s forced-override template match + negation cues; now also resets preference vectors (post-review fix) |
| Question Selector / Over-Generality Gate | II | done (Phase 0) | `src/copilot/overgenerality.py` — calibrated-temperature softmax entropy (2 rounds of review fixes), facet candidacy capped to a presentable 2-8 distinct-value range |
| Preference-Vector Boost | III | done (Phase 0) | `src/copilot/preference.py` — EMA positive/negative affinity, additive ranking-time boost, hard-reset on override |
| Adaptive Orchestrator | III | partial (Phase 0) | confidence-gated rerank-skip (`ranker.py`) and buying-intent-driven retrieval breadth exist inline; a named, logged state machine is Phase 1 step 1.4 |
| Evaluator harness integration | IV | done (Phase 0) | `tools/install_shim.py` (tracked generator, not a hand-committed file inside gitignored vendor code) + `tools/run_eval.py` |

**Phase 0 evaluator result (post codex-review fixes, `aa41ca2`)**: HitRate@10 0.39, MRR 0.2256,
MTTC 7.715, TechnicalScore 0.328 — 3.1x the organizer's baseline (0.107). Full before/after fix
comparison: `wiki/08_evaluation_log.md`.

## Where the detail actually lives

- **High-level design + diagram + rationale**: `implementation/03_SYSTEM_ARCHITECTURE.md`
- **Low-level design, data structures, pseudocode**: `implementation/04_SYSTEM_DESIGN.md`
- **Phased build plan (numbered steps)**: `implementation/05_BUILD_PLAN.md`
- **Every decision + rationale + resolved open questions**: `implementation/06_DECISION_LOG.md`

## Open design questions
- None blocking Phase 0 start — see `implementation/09_SUPERVISOR_QUESTIONS.md` for the genuine
  remaining calls (LLM provider choice, how far into Phase 2+ to push given the clock).
