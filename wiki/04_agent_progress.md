# 04 — Agent & Workstream Progress

One row per workstream. Update the moment a workstream starts, finishes, or blocks — this table
plus `status.md`'s "Next Workstream" section is what a fresh session reads to know exactly where
things stand.

| Workstream | Owner/Agent | Status | Started | Finished | Remaining |
|---|---|---|---|---|---|
| Project scaffolding (wiki, CLAUDE.md, status.md, git) | main session | done | 2026-08-26 | 2026-08-26 | — |
| External resource import (participant repo, kit, venv) | background agent | done | 2026-08-26 | 2026-08-26 | — (checksum verified, venv confirmed stdlib-only, baseline sanity run succeeded — see `wiki/07_external_resources.md`, `wiki/08_evaluation_log.md`) |
| Research: intent routing (Buying vs Browsing) | research agent 1 | in progress | 2026-08-26 | — | `research/01_intent_routing.md` |
| Research: hybrid in-memory retrieval architectures | research agent 2 | in progress | 2026-08-26 | — | `research/02_hybrid_retrieval.md` |
| Research: LLM semantic reranking | research agent 3 | in progress | 2026-08-26 | — | `research/03_llm_reranking.md` |
| Research: dialogue state tracking (accumulation vs override) | research agent 4 | in progress | 2026-08-26 | — | `research/04_dialogue_state_tracking.md` |
| Research: proactive clarification generation | research agent 5 | in progress | 2026-08-26 | — | `research/05_clarification_generation.md` |
| Research: context distillation & personalization | research agent 6 | in progress | 2026-08-26 | — | `research/06_context_distillation.md` |
| Research: adaptive/dynamic runtime orchestration | research agent 7 | in progress | 2026-08-26 | — | `research/07_adaptive_orchestration.md` |
| Research: evaluation metrics & benchmarks | research agent 8 | in progress | 2026-08-26 | — | `research/08_evaluation_benchmarks.md` |
| Research: prior art + starter kit online inspection | research agent 9 | in progress | 2026-08-26 | — | `research/09_prior_art_and_starter_kit.md` |
| Research synthesis: master Dos & Don'ts | unassigned | not started | — | — | blocked on agents 1-9 finishing |
| Pillar I — Intent routing & hybrid retrieval pipeline | unassigned | not started | — | — | blocked on research synthesis + starter kit verification |
| Pillar II — Dialog state machine & clarification | unassigned | not started | — | — | everything |
| Pillar III — Context distillation & adaptive orchestration | unassigned | not started | — | — | everything |
| Pillar IV — Evaluator integration & metrics tracking | unassigned | not started | — | — | everything |
| Submission packaging (README, demo video, Devpost writeup) | unassigned | not started | — | — | everything |

## Status legend
`not started` → `in progress` → `blocked` (note why + who/what unblocks it) → `done`.
