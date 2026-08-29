# 04 — Agent & Workstream Progress

One row per workstream. Update the moment a workstream starts, finishes, or blocks — this table
plus `status.md`'s "Next Workstream" section is what a fresh session reads to know exactly where
things stand.

| Workstream | Owner/Agent | Status | Started | Finished | Remaining |
|---|---|---|---|---|---|
| Project scaffolding (wiki, CLAUDE.md, status.md, git) | main session | done | 2026-08-26 | 2026-08-26 | — |
| External resource import (participant repo, kit, venv) | background agent | done | 2026-08-26 | 2026-08-26 | — (checksum verified, venv confirmed stdlib-only, baseline sanity run succeeded — see `wiki/07_external_resources.md`, `wiki/08_evaluation_log.md`) |
| Research: intent routing (Buying vs Browsing) | research agent 1 | done | 2026-08-26 | 2026-08-26 | — |
| Research: hybrid in-memory retrieval architectures | research agent 2 | done | 2026-08-26 | 2026-08-26 | — |
| Research: LLM semantic reranking | research agent 3 | done | 2026-08-26 | 2026-08-26 | — |
| Research: dialogue state tracking (accumulation vs override) | research agent 4 | done | 2026-08-26 | 2026-08-26 | — |
| Research: proactive clarification generation | research agent 5 | done | 2026-08-26 | 2026-08-26 | — |
| Research: context distillation & personalization | research agent 6 | done | 2026-08-26 | 2026-08-26 | — |
| Research: adaptive/dynamic runtime orchestration | research agent 7 | done | 2026-08-26 | 2026-08-26 | — |
| Research: evaluation metrics & benchmarks | research agent 8 | done | 2026-08-26 | 2026-08-26 | — |
| Research: prior art + starter kit online inspection | research agent 9 | done | 2026-08-26 | 2026-08-26 | — |
| Research synthesis: master Dos & Don'ts + ground-truth simulator mechanics | main session | done | 2026-08-26 | 2026-08-26 | `research/DOS_AND_DONTS.md`, `wiki/09_simulator_mechanics.md` |
| User-provided idea corpus review (`/My Ideas/` — 10 files, independent design+research pass) | main session | done | 2026-08-29 | 2026-08-29 | cross-checked against research + ground truth, merged into `implementation/` |
| Architecture synthesis: implementation/ corpus (12 documents, all open questions resolved) | main session | done | 2026-08-29 | 2026-08-29 | see `implementation/00_INDEX.md` |
| Two-tier codex review wiring (per-step + per-phase) in build plan + CLAUDE.md | main session | done | 2026-08-29 | 2026-08-29 | — |
| Frontend visualization design + published prototype ("Embedding Explorer") | main session | done | 2026-08-29 | 2026-08-29 | `implementation/13_FRONTEND_VISUALIZATION.md`; real Three.js build is optional/time-permitting, not on critical path |
| Architecture-synthesis codex review + full triage (7 findings, all fixed) | main session | done | 2026-08-29 | 2026-08-29 | see `wiki/reviews/architecture-synthesis-2026-08-29.md` |
| Phase 0 implementation (src/copilot/: state, catalog, nlu, intent_router, retrieval, rejection_memory, preference, overgenerality, ranker, turn_policy, agent, logging, phrasing, tools/install_shim.py, tools/run_eval.py) | main session | in progress | 2026-08-29 | — | full evaluator run against 200 dev sessions + phase-level codex review + closeout |
| Pillar I — Intent routing & hybrid retrieval pipeline | main session | in progress | 2026-08-29 | — | code written (`intent_router.py`, `retrieval.py`, `catalog.py`), pending full-loop evaluator validation |
| Pillar II — Dialog state machine & clarification | main session | in progress | 2026-08-29 | — | code written (`state.py`, `nlu.py`, `rejection_memory.py`, `overgenerality.py`), 19 unit tests passing |
| Pillar III — Context distillation & adaptive orchestration | main session | in progress | 2026-08-29 | — | code written (`preference.py`); orchestrator kept as inline decision functions for Phase 0, not a separate state-machine module yet |
| Pillar IV — Evaluator integration & metrics tracking | main session | in progress | 2026-08-29 | — | `tools/install_shim.py` + `tools/run_eval.py` written and shim-import verified; awaiting full 200-session run |
| Submission packaging (README, demo video, Devpost writeup) | unassigned | not started | — | — | scheduled as Phase 5, `implementation/05_BUILD_PLAN.md` |

## Status legend
`not started` → `in progress` → `blocked` (note why + who/what unblocks it) → `done`.
