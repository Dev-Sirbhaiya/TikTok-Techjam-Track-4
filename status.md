# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-29 (Phase 1 shipped and closed out; continuing directly into Phase 2)

## Current phase

**Phase 1 — DONE.** Calibration (train/validation split, ratio-gated facet selection) + named
adaptive orchestrator, codex-reviewed (4 findings, all fixed), benchmarked: **TechnicalScore
0.4087, HitRate@10 0.485, MRR 0.2867, MTTC 6.99 — up +24.5% from Phase 0's 0.328379, zero
regressions across all four scenarios.** The buying-track regression flagged at Phase 0 exit is
fully recovered. Full history in `wiki/08_evaluation_log.md`. User's standing `/goal`: continue
directly through Phase 2 → 3 without stopping to ask, benchmarking at each phase.

**Operational note**: evaluator runs launched via explicit background (`run_in_background: true`)
were killed externally three times in a row during Phase 1 for unclear reasons; running in the
**foreground** instead (accepting the ~10-min tool cap, which auto-backgrounds long runs) worked
reliably. Prefer foreground for evaluator runs going forward unless proven otherwise.

## Next workstream

**Run `implementation/05_BUILD_PLAN.md` Phase 2 (steps 2.1-2.3): gated ablations.**

Every item here is ablation-gated per `implementation/08_ABLATION_MATRIX.md` — build behind a flag,
measure against the Phase 1 exit baseline (0.4087) on the training split, keep only if it wins,
using the same 160/40 split as Phase 1 (`tools/session_split.json`). Concretely: 2.1 multi-interest
hypothesis vectors (K=1/2/3/4 sweep, `phase2/multi_interest.py`); 2.2 contextual bandit action
policy (static vs. adaptive, `phase2/action_policy.py`); 2.3 value-of-information question
selection upgrade (only with a genuinely live-computable proxy — never the ground-truth target
rank). Given real build-time pressure (this is Phase 2 of a 5-phase plan within a 72-hour window),
weigh each ablation's time cost against its plausible payoff — Phase 1 already delivered strong
gains; Phase 2's items are explicitly the "real payoff, real cost" tier, not required for a
submittable system. Then Phase 2's phase-level review + closeout, then Phase 3 per the standing goal.

## Blockers

None.

## Recent activity

- 2026-08-26 to 2026-08-29 (early) — Project scaffolding, research, architecture corpus, two-tier
  codex review protocol. Full detail in `wiki/03_design_log.md`.
- 2026-08-29 — **Phase 0 shipped**: `src/copilot/` implemented, codex-reviewed (7 findings fixed),
  benchmarked (TechnicalScore 0.328379, 3.1x baseline). One honest finding flagged forward (buying
  regression) rather than hidden.
- 2026-08-29 — **Phase 1 shipped**: calibration split, ratio-gated facet selection, named adaptive
  orchestrator, codex-reviewed (4 findings fixed), benchmarked (TechnicalScore 0.408714, +24.5%,
  buying regression fully recovered). See `wiki/03_design_log.md` for full detail including the
  background-task-killing operational note.

## Open questions / decisions needed from the user

- `implementation/09_SUPERVISOR_QUESTIONS.md` SQ1 (LLM provider choice, if any — not needed so far,
  every gain to date is from the no-LLM guaranteed path) and SQ3-SQ5 (team/demo/workshop notes).
  SQ2 is answered by the standing `/goal`: continue through Phase 3.
