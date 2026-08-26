# 01 — System Architecture (Living Document)

> Edit this page in place as the design evolves. Do not let it go stale — if code and this page
> disagree, this page is wrong and must be fixed as part of the phase that caused the drift.
> Superseded designs move to [03_design_log.md](03_design_log.md), not left here commented out.

**Status: not yet designed.** Build has not started (challenge window opens 2026-08-29). This page
will be filled in as Pillar I–III designs are decided — see [00](00_problem_statement.md) for the
requirements driving the design.

## Planned shape (placeholder — replace as decisions land)

```
                         ┌─────────────────────┐
   user turn ──────────▶ │   Intent Router       │  (Buying vs Browsing)
                         └─────────┬────────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                     ▼
        Filter Track (Buying)               Dense/Diverse Track (Browsing)
        - hard constraint lock               - cross-category retrieval
                 │                                     │
                 └─────────────────┬─────────────────┘
                                   ▼
                    Multi-Route Retrieval (keyword + category + vector)
                                   ▼
                        LLM Semantic Ranking
                                   ▼
                    Over-generality check ──▶ clarification prompt (cut retrieval, ask, loop)
                                   ▼
                        Ranked results / turn response
                                   ▼
              Dialog State Tracker (slots: accumulate / override)
                                   ▼
        Context Distillation (session state + long-term profile) ──▶ feeds back into router/ranker
```

## Components (fill in as implemented — link to [05_completed_components.md](05_completed_components.md))

| Component | Owns which pillar | Status | Notes |
|---|---|---|---|
| Intent Router | I | not started | |
| Retrieval layer (keyword/category/vector, in-memory) | I | not started | must stay in-memory per constraints |
| LLM Semantic Ranker | I | not started | |
| Dialog State Tracker | II | not started | incremental slots + override handling |
| Clarification Generator | II | not started | triggered on over-generality |
| Context Distillation / Profile Store | III | not started | session-scoped + persistent profile |
| Adaptive Orchestrator | III | not started | runtime re-orchestration logic |
| Evaluator harness integration | IV | not started | wraps organizer's local evaluator |

## Open design questions
- (none logged yet — add as they come up, resolve into [02_design_decisions.md](02_design_decisions.md))
