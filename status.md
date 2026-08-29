# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-30 (Phase 3 closed out; Phase 3.5's Ablation 4 shipped a genuine +6.4% optional
LLM-booster win; continuing Phase 3.5's remaining items)

## Current phase

**Phase 3 — DONE.** While starting Phase 3.1 (offline strategy tuning), the very first step
surfaced a real reproducibility bug: `catalog.py`'s BM25/metadata ranking and gazetteer lookups
iterated plain Python `set`s whose order is hash-randomized per process, so the agent's behavior
on the same deterministic simulator sessions was not actually reproducible run-to-run. Fixed at
the source (sorted iteration). Because the bug's noise magnitude was comparable to several of
Phase 2's reported ablation margins, honestly re-ran all three Phase 2 ablations with the fixed
code: **VoI signal reversed from KEPT to CUT** (the originally-reported modest win was entirely a
noise artifact — ON/OFF are byte-identical across all 200 dev sessions once fixed); multi-interest
and bandit stay CUT, now with cleaner, re-verified reasoning. **Corrected full 200-session exit:
TechnicalScore 0.40927, HitRate@10 0.49, MRR 0.278234, MTTC 6.96** (supersedes the earlier
buggy-measurement 0.411066; nearly unchanged in aggregate, materially different in mechanism story).

**3.1 (systematic threshold tuning)**: swept `should_clarify`'s three knobs across both splits —
every value in a wide, sensible range matched the hand-set defaults byte-for-byte; only genuinely
extreme values degraded sharply. Per Ablation 3's decision rule, defaults are kept unchanged — a
systematically-verified "already robust" result.

**3.2 (comparative feedback)**: confirmed structurally impossible before building anything — direct
inspection of `evaluator/local_evaluator.py` found `customer_reply()` never receives the agent's
recommendation list, and the complete, exhaustive set of simulator turns contains no comparative-
language generation path at all. Cut, not deferred (`implementation/06_DECISION_LOG.md` D9).

No change to the scored `Agent`'s runtime behavior occurred during 3.1/3.2's own work, so
TechnicalScore 0.40927 stands as Phase 3's exit number too. Full detail:
`wiki/03_design_log.md`'s 2026-08-30 entries, `wiki/08_evaluation_log.md`.

**Codex review status**: the phase's one substantive logic commit (`7be9ba7`) got a full,
successful review (1 finding, fixed). The broader phase-level `--base`-diff review failed 3
consecutive attempts for environment/sandbox reasons — see Blockers below.

**Operational note**: evaluator runs launched via explicit background (`run_in_background: true`)
were killed externally three times in a row during Phase 1 for unclear reasons; running in the
**foreground** instead (accepting the ~10-min tool cap, which auto-backgrounds long runs) worked
reliably. Prefer foreground for evaluator runs going forward unless proven otherwise.

## Current phase (cont.) — Phase 3.5 in progress: real LLM listwise reranker shipped

User provided a personal `ANTHROPIC_API_KEY` (`.env` at repo root, gitignored) and asked explicitly
for higher accuracy given the competition's stakes. Implemented `ranker.py`'s previously-stubbed
`_llm_listwise_rerank()` for real (single-pass Claude Haiku 4.5, gated behind the cross-encoder's
own margin-skip so it only fires on genuinely ambiguous shortlists) and ran Ablation 4 for the first
time on real data: validation (n=40) ON 0.403042 vs OFF 0.375938; training (n=160) ON 0.442173 vs
OFF 0.417604 — a consistent win on every metric on both splits, MRR +14.4% on training, zero
regressions. **Enabled by default.** Full 200-session confirmatory run: **TechnicalScore 0.43531**
(+6.4% over the guaranteed baseline).

**Critical caveat — do not lose this in future summaries**: the organizer provides no hosted model
credentials for official grading, and this key exists only in this session's local `.env`, never
shipped in the submission. The official private-set score will almost certainly be measured
*without* this key, meaning this mechanism is inert during real judging. **The realistic expected
submission score remains TechnicalScore 0.40927** (the guaranteed cross-encoder-only path); 0.43531
is a validated bonus/stretch number for the writeup and demo, never "the" score. Full detail:
`implementation/06_DECISION_LOG.md` D-LLM-TIER, `implementation/08_ABLATION_MATRIX.md` Ablation 4.

## Next workstream

**Continue `implementation/05_BUILD_PLAN.md` Phase 3.5's remaining items.**

Ablation 4 (LLM booster) is done. Remaining: portfolio/slate hedging (reserve top slots for
highest-confidence matches, hedge remaining slots across plausible alternative interpretations —
its original rationale, "esp. if 2.1's multi-interest is kept," no longer applies since
multi-interest was cut in Phase 2, so evaluate on its own merits); uncertainty calibration (check
whether entropy/confidence actually correlates with real hit-rate outcomes on held-out sessions —
cheap, since already-logged per-turn entropy via `logging_.py` can be bucketed against actual hit
outcomes with no new agent code); counterfactual/synthetic rollout augmentation (only if the
evaluator is confirmed genuinely replayable with counterfactual actions — the most expensive item,
decide last). Given the LLM booster's strong result, also worth a quick look: whether an LLM-assisted
query-understanding/expansion step (pre-retrieval) shows similar gains, time permitting — but only
after the three build-plan items above are resolved. Then Phase 3.5's exit codex review, full
200-session benchmark, phase-closeout, then Phase 4 per the standing goal.

## Blockers

- **Phase 3 exit-level codex review (`--base 4aeaaff`, the whole-phase diff) failed 3 consecutive
  attempts** (2026-08-30), each for environment/sandbox reasons, not code issues: attempts 1-2 hit
  repeated `pwsh.exe` `CreateProcessAsUserW` "Access is denied" errors that ate the whole turn before
  falling back to `cmd.exe`; attempt 3 got further but then hit a sandboxed Python `tempfile`
  failure ("No usable temporary directory found") while trying to run the test suite itself. Per
  `CLAUDE.md`'s instruction to log rather than silently skip: **not treating this as "phase
  unreviewed"** — the phase's one substantive logic commit (`7be9ba7`, the determinism fix + Phase 2
  re-ablation) already got a full, successful `codex exec review --commit` pass that found and fixed
  a real bug (`wiki/reviews/phase3.1-determinism-fix-2026-08-30.md`); only the broader consolidated
  `--base`-diff review specifically is blocked. If codex becomes reliable again for `--base`-style
  reviews, run it against `4aeaaff` before Phase 3.5's own review to close this gap retroactively.

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
