# 10 — Pre-Registration

Committed **before** Phase 0 building starts, so later tuning can't quietly redefine "success" to fit
whatever number comes out. If any of this needs to change later, the change and its reason get logged
in `06_DECISION_LOG.md` as a new dated entry — never a silent edit to this file's original numbers.

## Evaluation protocol

- **Primary tool**: the organizer's own `evaluator/local_evaluator.py`, run unmodified via
  `python -m evaluator.local_evaluator` from `external/techjam-conversational-search/`, against
  `data/public_set.jsonl` (200 sessions) for all local development.
- **Metrics tracked every run**: `hit_rate_at_10`, `mrr`, `mttc`, derived `efficiency`, derived
  `technical_score` (formula verified against source — `06_DECISION_LOG.md` resolved-Q9), plus the
  per-scenario breakdown (`buying`/`browsing`/`intent_override`/`boundary`).
- **Logging location**: `wiki/08_evaluation_log.md`, append-only, one row per run with date, commit
  hash, variant description, all metrics, and a notes column for anything unusual observed.

## Train/validation split (for Phase 3.1 offline tuning and Phase 2/3 ablations only)

Phase 0/1 development and calibration use the **full 200 public sessions** — there's no held-out
concern yet because nothing is being "trained" against them (thresholds are hand-set and spot-checked,
not optimized by a search procedure). **Once Phase 3.1's offline tuning loop (or any automated
threshold search) is built**, split the 200 public sessions into:
- **160 training** (used by the rollout → score → edit → validate loop to propose changes)
- **40 validation** (used only to accept/reject a proposed change — never touched by the optimizer)

Split deterministically by `sample_id` hash (not random each run) so it's reproducible across sessions
and doesn't silently change between runs. Record the exact split (which `sample_id`s are in which set)
in `wiki/08_evaluation_log.md` the first time it's used.

**Why this matters**: the 800 private sessions (4x the public set) are what's actually judged, and they
share the same scenario mix but different underlying products (`06_DECISION_LOG.md` resolved-Q8) — an
optimizer that's allowed to see its own validation data will report an inflated number that doesn't
generalize. This is the single most common failure mode in this kind of iterative tuning.

## Success thresholds, committed now

| Milestone | Metric floor (must clear) | Stretch target |
|---|---|---|
| Phase 0 exit | HitRate@10 and MTTC both measurably better than 0.125 / 9.81 (the organizer's baseline) | TechnicalScore ≥ 0.25 (roughly 2.3x the baseline's 0.107) |
| Phase 1 exit | No regression on any of the three metrics vs. Phase 0 exit | TechnicalScore ≥ 0.32 |
| Any Phase 2+ item | Wins its mandatory ablation per `08_ABLATION_MATRIX.md` — no exceptions | — |
| Final (Phase 5.1) | Whatever Phase 0/1 (+ any won Phase 2+ ablations) achieve, honestly reported | — |

These are planning targets to aim at, not scored thresholds the organizer imposes — if Phase 0 clears
its floor but misses the stretch target, that is still a successful, submittable Phase 0 per
`05_BUILD_PLAN.md`'s exit criteria (which only require clearing the baseline, not hitting a specific
number). The stretch targets exist so "we hit a nice round number, let's stop tuning" doesn't happen
before the metric floor is actually cleared with margin.

## What counts as "beating the baseline" (avoiding a goalpost-moving trap)

"Baseline" means the organizer's own unmodified weak BM25 starter (HitRate@10 0.125, MRR 0.068034,
MTTC 9.81, TechnicalScore 0.10671), run against the same 200 public sessions we use — not this
project's own internal Phase 0 step 0.3 checkpoint (that's Baseline B in `08_ABLATION_MATRIX.md`, a
useful internal comparison point, but not "the baseline" for exit-criteria purposes).

## Assumptions locked in now (revisit only via a new `06_DECISION_LOG.md` entry, not silently)

- The private 800-session set uses the same `TechnicalScore` formula and weights as documented
  (0.50/0.30/0.20) — no evidence otherwise, but genuinely unconfirmed for the private set specifically.
- No numeric CPU/memory/timeout limit applies locally during development; final judging may impose
  unpublished ones (D-LATENCY) — design defensively, don't assume this locks in.
- `codex exec review` is available and authenticated as of this writing (2026-08-29) — if it becomes
  unavailable again mid-build, `status.md`'s Blockers protocol handles it without stopping other work.
