# Implementation Corpus — Index

This is the **authoritative, verified** architecture and build corpus for the TikTok TechJam 2026
Track 4 Shopping Copilot. It supersedes `/My Ideas/` (raw brainstorm + a first structured pass —
excellent input, but self-described by the user as "not ground truth") by merging it with:

- `research/01-09_*.md` + `research/DOS_AND_DONTS.md` — 9 parallel deep-research agents' findings
- `wiki/09_simulator_mechanics.md` — ground truth read directly from the organizer's actual source
  code (`evaluator/local_evaluator.py`, `starter/agent.py`, `docs/*.json/.md`), not inferred
- A direct sample of `catalog.jsonl` (30,000+ records) resolving the one remaining open question
  about metadata schema consistency

**Every open question from `/My Ideas/04_OPEN_QUESTIONS.md` is resolved in this corpus** — see
`06_DECISION_LOG.md`'s "Resolved from `/My Ideas/` Open Questions" section and
`09_SUPERVISOR_QUESTIONS.md` for what's left (only genuine user-facing calls remain).

**Say "run Phase 0" (or name any phase/step, e.g. "run 0.3") and it executes** — `CLAUDE.md` binds
phase/step completion to the commit → background codex review → wiki update loop automatically; you
do not need to ask for that separately.

## Reading order

| # | Document | Purpose |
|---|---|---|
| 01 | [Problem Framing](01_PROBLEM_FRAMING.md) | Restated problem, success criteria, design space, what "good" means here |
| 02 | [Technical PRD](02_TECHNICAL_PRD.md) | Functional & non-functional requirements, interfaces, in/out of scope |
| 03 | [System Architecture](03_SYSTEM_ARCHITECTURE.md) | High-level design, turn-level data flow diagram, component map |
| 04 | [System Design](04_SYSTEM_DESIGN.md) | Low-level design: data structures, algorithms, pseudocode per module |
| 05 | [Build Plan](05_BUILD_PLAN.md) | Phased plan, numbered N.M steps, exit criteria, file-by-file tasks |
| 06 | [Decision Log](06_DECISION_LOG.md) | Every architecture decision (D1-D24+), alternatives considered, status, and — critically — every `/My Ideas/` open question resolved against ground truth |
| 07 | [Risk Register](07_RISK_REGISTER.md) | What could go wrong, likelihood/impact, mitigation, owner-of-watch |
| 08 | [Ablation Matrix](08_ABLATION_MATRIX.md) | Mandatory gates for every Phase 2+ item, procedure, decision rule |
| 09 | [Supervisor Questions](09_SUPERVISOR_QUESTIONS.md) | Real open calls only you can make — everything resolvable from docs/code already is |
| 10 | [Pre-Registration](10_PRE_REGISTRATION.md) | Eval protocol, train/validation split, and success thresholds committed *before* building, to prevent post-hoc metric shopping |
| 11 | [Future Work](11_FUTURE_WORK.md) | Speculative/stretch ideas (world-model-lite, etc.) explicitly out of the committed build |
| 12 | [Build Memo](12_BUILD_MEMO.md) | One-page narrative summary — read this if you only read one file |
| 13 | [Frontend Visualization](13_FRONTEND_VISUALIZATION.md) | The "Embedding Explorer" demo/debug tool — 3D embedding space + dialog state + retrieval funnel. Not part of the scored path. Includes a link to a live interactive prototype. |

## Relationship to other folders

- `/My Ideas/` — left untouched as historical input; every good idea in it is folded in here
  (rejection-memory tiers, ablation discipline, phased floor-first strategy), every claim in it is
  either confirmed or corrected against ground truth here, nothing from it is silently dropped.
- `/research/` — the literature/prior-art layer this corpus builds on; cited by file+section
  throughout rather than re-derived.
- `/wiki/` — the living project memory (progress, design log, evaluation log) that gets updated as
  `implementation/` phases are actually executed. `implementation/` is the *plan*; `wiki/` is the
  *running record of what actually happened*.
