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
| **Phase 0 implementation + closeout** (src/copilot/ full hybrid agent, 26 unit tests, 2 codex reviews fully triaged, real 200-session evaluator numbers) | main session | **done** | 2026-08-29 | 2026-08-29 | TechnicalScore 0.328 (3.1x baseline) — see `wiki/08_evaluation_log.md`; buying-track calibration flagged for Phase 1.3 |
| Pillar I — Intent routing & hybrid retrieval pipeline | main session | done (Phase 0) | 2026-08-29 | 2026-08-29 | validated end-to-end against 200 sessions |
| Pillar II — Dialog state machine & clarification | main session | done (Phase 0) | 2026-08-29 | 2026-08-29 | 26 unit tests passing, validated end-to-end |
| Pillar III — Context distillation & adaptive orchestration | main session | done (Phase 0), Phase 1.4 pending | 2026-08-29 | 2026-08-29 | preference vectors done; named adaptive state machine deferred to Phase 1.4 |
| Pillar IV — Evaluator integration & metrics tracking | main session | done (Phase 0) | 2026-08-29 | 2026-08-29 | `tools/run_eval.py` is the standing "one command to run" |
| **Phase 1 implementation + closeout** (calibration split, ratio-gated facet selection, named orchestrator, 1 codex review fully triaged) | main session | **done** | 2026-08-29 | 2026-08-29 | TechnicalScore 0.4087 (+24.5% vs Phase 0) — see `wiki/08_evaluation_log.md`; buying-track regression from Phase 0 fully recovered |
| **Phase 2 implementation + closeout** (3 gated ablations; codex review's 3 findings fixed; then a Phase 3.1-discovered reproducibility bug forced re-ablation of all 3 — VoI reversed kept→cut, all three now cut) | main session | **done, corrected** | 2026-08-30 | 2026-08-30 | Corrected TechnicalScore 0.40927 (supersedes buggy-measurement 0.4111) — see `wiki/08_evaluation_log.md` and `wiki/03_design_log.md`'s Phase 3.1 entry |
| Phase 3 — offline tuning + comparative feedback | main session | in progress | 2026-08-30 | — | per user's continue-iterating directive |
| Submission packaging (README, demo video, Devpost writeup) | unassigned | not started | — | — | scheduled as Phase 5, `implementation/05_BUILD_PLAN.md` |

## Status legend
`not started` → `in progress` → `blocked` (note why + who/what unblocks it) → `done`.
