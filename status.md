# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-29 (architecture decided, implementation corpus complete, ready to build)

## Current phase

**Architecture & planning — complete. Zero implementation code written yet.** Challenge window is
open (2026-08-29 12:00 → 2026-09-01 12:00). The user's own `/My Ideas/` design pass was reviewed,
cross-checked against `research/DOS_AND_DONTS.md` and verified ground truth, and merged into
`implementation/` — a 12-document corpus (problem framing, PRD, system architecture + diagram, system
design + pseudocode, phased build plan numbered 0.1-5.5, decision log resolving every open question,
risk register, ablation matrix, supervisor questions, pre-registration, future work, build memo).
`implementation/00_INDEX.md` is the entry point.

## Next workstream

**Run `implementation/05_BUILD_PLAN.md` Phase 0, starting at step 0.1.**

Say "run Phase 0" (or name a specific step, e.g. "run 0.4") and it executes — `CLAUDE.md` §1a binds
this to the commit → background codex review → wiki update loop automatically, per step, no need to
ask for that separately. Phase 0 builds the full hybrid-retrieval floor (BM25 + dense + metadata +
RRF, dialog state, rejection memory, intent router, preference-vector boost, entropy-gated
clarification, cross-encoder reranker, turn policy) and must clear the organizer's baseline
(HitRate@10 0.125, MRR 0.068034, MTTC 9.81, TechnicalScore 0.10671) before Phase 1 starts — exit
criteria and success thresholds are pre-registered in `implementation/10_PRE_REGISTRATION.md`.

Two genuine open items to flag to the user before/while building (not blocking start):
`implementation/09_SUPERVISOR_QUESTIONS.md` SQ1 (LLM provider choice, if any) and SQ2 (how far into
gated Phase 2+ work to push given the real clock).

## Blockers

- None. `codex` CLI is now authenticated (user ran `codex login`) and confirmed working
  (`codex exec "say ready"` succeeded, v0.150.1) — the review half of the work-phase loop is fully
  operational again as of 2026-08-29.

## Recent activity

- 2026-08-26 — Project scaffolding, external resource import (baseline recorded: HitRate@10 0.125 /
  MRR 0.068034 / MTTC 9.81 / TechnicalScore 0.10671), 9-agent deep research phase, ground-truth
  simulator mechanics captured (`wiki/09_simulator_mechanics.md`). See prior entries below and
  `wiki/03_design_log.md` for full detail.
- 2026-08-29 — **Codex re-authenticated** (user ran `codex login`) — review loop unblocked.
- 2026-08-29 — **User provided `/My Ideas/`**, a 10-file independent design + research pass, flagged
  by the user as "not ground truth." Reviewed in full; independently converged with our own research
  on most major calls (RRF, tiered rejection memory, cutting cross-session personalization) — good
  cross-validation. Directly sampled 30,000+ `catalog.jsonl` records to resolve its one remaining
  data-schema open question (confirmed `details` has zero cross-item schema consistency, even within
  one leaf category). Resolved all 10 of its open questions (Q1-Q10) against actual evaluator source.
- 2026-08-29 — **Built `implementation/`** — the authoritative architecture/build corpus, superseding
  `/My Ideas/` (kept as historical input) and filling a real gap (explicit within-session
  preference-vector ranking boost for Pillar III). Updated `CLAUDE.md` (§1a) so "run Phase N"/"run
  step N.M" map unambiguously to `implementation/05_BUILD_PLAN.md` with the enforcement loop
  automatic. Updated `wiki/01_architecture.md` and `wiki/02_design_decisions.md` (DD-002) to point to
  it. See `wiki/03_design_log.md` for full detail.

## Open questions / decisions needed from the user

- `implementation/09_SUPERVISOR_QUESTIONS.md` SQ1-SQ5 — LLM provider choice (if any), how far into
  gated Phase 2+ to push given real time remaining, team/solo division of labor, demo video scope,
  and whether the 2026-08-28 workshop surfaced anything not yet captured. None of these block
  starting Phase 0.
