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
| NLU / Slot Extraction | I, II | not started | rule/gazetteer primary, LLM optional arbiter — never a hard dependency |
| Intent Router | I | not started | gazetteer hard-match → embedding vote → LLM arbiter only on disagreement |
| Retrieval layer (BM25 + dense + metadata, in-memory) | I | not started | `bm25s`/FTS5 + `bge-small-en-v1.5` + dict inverted index, RRF fusion |
| Cross-Encoder Reranker (+ optional LLM booster) | I | not started | `ms-marco-MiniLM-L-6-v2` guaranteed stage; LLM never required |
| Dialog State Tracker (`DialogState`) | II | not started | slots, rejected_hard/soft (tiered), turn count, candidate pool |
| Change-Point / Override Detector | II | not started | deterministic category-conflict rule + negation cues |
| Question Selector / Over-Generality Gate | II | not started | Shannon entropy over post-retrieval scores, CIKM'13 max-entropy facet |
| Preference-Vector Boost | III | not started | EMA positive/negative affinity, additive ranking-time boost — the concrete "long-term profile" implementation |
| Adaptive Orchestrator | III | not started | small explicit state machine, signal-gated, not LLM-decided |
| Evaluator harness integration | IV | not started | thin re-export wiring `starter/agent.py` → `src/copilot/agent.py` |

## Where the detail actually lives

- **High-level design + diagram + rationale**: `implementation/03_SYSTEM_ARCHITECTURE.md`
- **Low-level design, data structures, pseudocode**: `implementation/04_SYSTEM_DESIGN.md`
- **Phased build plan (numbered steps)**: `implementation/05_BUILD_PLAN.md`
- **Every decision + rationale + resolved open questions**: `implementation/06_DECISION_LOG.md`

## Open design questions
- None blocking Phase 0 start — see `implementation/09_SUPERVISOR_QUESTIONS.md` for the genuine
  remaining calls (LLM provider choice, how far into Phase 2+ to push given the clock).
