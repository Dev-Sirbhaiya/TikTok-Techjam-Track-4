# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-30 (Phase 2 re-ablated after a reproducibility bug fix; mid-Phase-3.1; codex
review + commit for this round still pending)

## Current phase

**Phase 2 — DONE, numbers corrected.** While starting Phase 3.1 (offline strategy tuning), the
very first step surfaced a real bug: `catalog.py`'s BM25/metadata ranking and gazetteer lookups
iterated plain Python `set`s whose order is hash-randomized per process, so the agent's behavior
on the same deterministic simulator sessions was not actually reproducible run-to-run. Fixed at
the source (sorted iteration, not an env-var workaround — see `wiki/03_design_log.md`'s full
writeup). Because the bug's noise magnitude was comparable to several of Phase 2's reported
ablation margins, honestly **re-ran all three Phase 2 ablations** with the fixed code: **VoI
signal reversed from KEPT to CUT** (originally reported as a modest win; with determinism fixed,
ON and OFF are byte-identical across all 200 dev sessions — the win was entirely a noise artifact);
multi-interest and bandit stay CUT, now with cleaner, re-verified reasoning. **Corrected full
200-session exit: TechnicalScore 0.40927, HitRate@10 0.49, MRR 0.278234, MTTC 6.96** — supersedes
the earlier (buggy-measurement) 0.411066 number, though the aggregate is nearly unchanged at this
sample size (the bug's impact was diluted by averaging over 200 sessions, even though it flipped
conclusions at n=40). Full detail in `wiki/03_design_log.md`'s 2026-08-30 (cont.) "Phase 3.1:
reproducibility bug" entry and `wiki/08_evaluation_log.md`.

**Not yet done for this round** (in progress): commit these fixes, then per the two-tier review
protocol run `codex exec review` against the diff before closing this out. User's standing
`/goal`: continue through Phase 3 without stopping to ask, benchmarking at each phase.

**Operational note**: evaluator runs launched via explicit background (`run_in_background: true`)
were killed externally three times in a row during Phase 1 for unclear reasons; running in the
**foreground** instead (accepting the ~10-min tool cap, which auto-backgrounds long runs) worked
reliably. Prefer foreground for evaluator runs going forward unless proven otherwise.

## Next workstream

**Run `implementation/05_BUILD_PLAN.md` Phase 3 (steps 3.1-3.2): offline self-evolution +
comparative feedback.**

3.1 — SkillOpt-style offline strategy tuning: rollout → score → edit → validate loop against the
**training split** (`tools/session_split.json`), producing a tuned strategy document (thresholds,
facet priorities, fusion weights) rather than hand-guessed values; validate the result against the
**held-out validation split**, never the training split (`08_ABLATION_MATRIX.md` Ablation 3 —
keep only if "after" beats "before" on the held-out split specifically). 3.2 — comparative
feedback: parse comparative language ("closer to the second one, but less flashy") through the
existing NLU/state path, apply a Rocchio-style update that is bounded and positive-heavy (high
weight on original signal, small positive-feedback weight, near-zero/heavily-damped negative term,
cap feedback at k≤5 — per the negative literature on query drift, `research/06` / `/My Ideas/` D9).
Then Phase 3's exit codex review (explicitly check whether 3.1's tuning loop leaked
validation-split data into training — a specific, checkable failure mode), full 200-session
benchmark, phase-closeout, then Phase 3.5 per the standing goal.

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
- 2026-08-30 — **Phase 2 shipped**: VoI signal kept, multi-interest + bandit cut (both matching
  their a priori risk assessments), codex-reviewed (3 findings fixed — bandit reward-tracking bugs,
  test order-dependency), bandit ablation honestly re-run post-fix (verdict held, more decisively),
  benchmarked (TechnicalScore 0.411066, +0.6%). See `wiki/03_design_log.md`'s 2026-08-30 entry.

## Open questions / decisions needed from the user

- `implementation/09_SUPERVISOR_QUESTIONS.md` SQ1 (LLM provider choice, if any — not needed so far,
  every gain to date is from the no-LLM guaranteed path) and SQ3-SQ5 (team/demo/workshop notes).
  SQ2 is answered by the standing `/goal`: continue through Phase 3.
