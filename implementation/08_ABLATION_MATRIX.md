# 08 — Ablation Matrix

Supersedes `/My Ideas/06_ABLATIONS_AND_METRICS.md` — same governing rule and procedure (well-designed
originally), extended with the internal-baseline steps this corpus adds in Phase 0/1.

## The rule

> A technique being real, published, and well-cited is never sufficient justification for keeping it
> in this system. If a component doesn't measurably improve held-out results on our own dev sessions,
> it gets removed or demoted — never kept because a paper exists for it.

## Metric-tracking discipline (from Phase 0 step 0.3 onward)

1. Log all three raw metrics (HitRate@10, MRR, MTTC) plus derived Efficiency/TechnicalScore after
   **every** change, not just phase ends — append-only in `wiki/08_evaluation_log.md`, never overwrite.
2. **Two permanent control groups**, not one: (a) the organizer's own weak BM25 baseline (0.125 /
   0.068034 / 9.81 / 0.10671 — already recorded), and (b) this project's Phase 0 step 0.3 naive
   stateless baseline (recorded fresh, since it already includes hybrid retrieval + RRF, unlike (a)).
   Compare every later number against both.
3. Watch metric trade-offs, not just aggregate improvement — a feature that helps MRR but hurts MTTC
   needs a tuning pass before being called "kept."
4. Split-aware evaluation from Phase 3 onward: hold out a validation subset per `10_PRE_REGISTRATION.md`
   so offline tuning (D13) isn't validated on the data it was fit to.

## Internal (non-gated) baseline checkpoints — required, not optional

| Checkpoint | What it measures | Where |
|---|---|---|
| Baseline A | Organizer's weak BM25 starter, unmodified | Already recorded, `wiki/08_evaluation_log.md` |
| Baseline B | This project's hybrid-retrieval-but-stateless floor | Phase 0 step 0.3 |
| Phase 0 exit | Full Phase 0 system | Phase 0 step 0.11 |
| Phase 1 exit | + calibrated thresholds, orchestrator polish | Phase 1 step 1.4 |

## Mandatory ablations for Phase 2/3 items

### Ablation 1 — Multi-interest K sweep (gates D3)
**Procedure**: K=1 (disabled) vs. K=2/3/4, full 200 dev sessions (or training split once
`10_PRE_REGISTRATION.md`'s split exists). **Watch**: HitRate@10 and MRR primarily, MTTC as a check (a
more-accurate-but-slower-to-converge system may not net-win under the efficiency weight). **Decision
rule**: keep K=1 unless some K>1 shows a non-trivial (not run-to-run-noise-sized) TechnicalScore gain;
if kept, use the smallest K capturing most of the gain.

### Ablation 2 — Static vs. adaptive action policy (gates D11)
**Procedure**: static Phase 0/1 question-selection vs. bandit-adjusted version, same dev sessions.
**Watch**: MTTC primarily, HitRate@10 as a check (shouldn't converge to bad guesses faster). **Decision
rule**: keep only if MTTC improves without a HitRate@10 drop; a close/inconsistent result is a
legitimate "tried, measured, not a clear win" writeup point, not a failure — ship the simpler static
version if so.

### Ablation 3 — Before vs. after offline strategy optimization (gates D13)
**Procedure**: hand-tuned Phase 0/1 thresholds ("before") vs. SkillOpt-style rollout-optimized
thresholds ("after"), both evaluated on a **held-out validation split never used for the optimization
itself** (see `10_PRE_REGISTRATION.md`). **Decision rule**: keep only if "after" beats "before" on the
held-out split specifically — a win only on the training split is meaningless by construction. Skip
entirely if time is short; lowest-risk Phase 2/3 item, but not risk-free if built and never validated.

### Ablation 4 (new) — Cross-encoder-only vs. cross-encoder + LLM booster (gates the D-LLM-TIER optional path)
**Procedure**: run Phase 0's reranker with the LLM booster disabled vs. enabled (when a key is
configured), same dev sessions. **Watch**: MRR primarily (this is a ranking-precision mechanism),
latency/token cost as a feasibility check. **Decision rule**: only enable the LLM booster by default in
the shipped configuration if it shows a real MRR gain that justifies the added latency/cost/dependency
risk (R2 in `07_RISK_REGISTER.md`) — the cross-encoder-only path must remain fully functional and be
the documented default regardless of this ablation's outcome (NFR-2 is non-negotiable, not gated).

**RESULT, CORRECTED 2026-08-30 after a recovered codex review** (see
`wiki/03_design_log.md`'s "recovered reviews" entry — the original ablation used a call with no
explicit sampling control and no bounded timeout; a "determinism fix" attempt broke the booster
entirely before being properly fixed): validation split (n=40) ON 0.45/0.303681/7.4/**0.388104**
vs OFF 0.425/0.266667/7.6/**0.3605**; training split (n=160) ON
0.51875/0.321029/6.6625/**0.442434** vs OFF 0.5/0.280952/6.81875/**0.417911**. Consistent win on
every metric on both splits, confirming the original conclusion survives once the implementation
actually works. **ENABLED by default** (`ranker.ENABLE_LLM_BOOSTER = True`). Per NFR-2, this never
becomes a hard dependency — `agent.py` only constructs a client when `ANTHROPIC_API_KEY` is
present, and any failure falls back to the guaranteed cross-encoder order. **The organizer's stated
no-hosted-credentials policy means the official grading run will almost certainly have no such key,
so this mechanism is expected to be inert during real judging** — the guaranteed cross-encoder-only
number (full 200 sessions: TechnicalScore **0.406428**) remains the realistic expected submission
score. Full detail: `implementation/06_DECISION_LOG.md` D-LLM-TIER, `wiki/08_evaluation_log.md`.

### Ablation 6 (new, Phase 3.5) — Portfolio/slate hedging on vs. off (gates the calibration-driven hedging item)
**Motivation**: `tools/calibration_check.py` (2026-08-30) found sessions reaching a genuinely FORCED
commit (out of turns, or nothing productive left to ask) are ~100% still at high entropy (0.7-1.0)
and hit at a dismal 2.97% rate — pure top-K-by-score recommends near-duplicates of the single most-
likely interpretation exactly when that interpretation is least likely to be right.
**RESULT**: validation split (n=40, LLM booster off to isolate) ON 0.376071 vs OFF 0.375938 —
**a genuine wash, not a win** (HitRate@10 identical, 0.45 both; only a hairline MRR difference);
training split (n=160, confirmatory) ON **0.425645** vs OFF 0.417604 (+1.9% TechnicalScore, gains
concentrated in `buying`). **Originally shipped ENABLED, then REVERSED** (recovered codex review):
per `10_PRE_REGISTRATION.md`'s own rule ("a win only on the training split is meaningless by
construction"), a validation-split wash does not satisfy the acceptance bar, however plausible the
training-split signal looks — "the validation sample is probably just too small to detect a real
effect" is exactly the post-hoc reasoning the split discipline exists to rule out, not a legitimate
way past a failed check. **DISABLED** (`phase2/slate_hedging.py`, `ENABLE_SLATE_HEDGING = False`).
Module kept for the writeup's "tried, looked promising, held-out check didn't confirm it, correctly
declined on review" record — itself a demonstration of the discipline catching a mistake, not just
validating good ideas.

### Ablation 7 (new, Phase 3.5) — Query-vector nudge on vs. off (user-suggested)
**Motivation**: nudge the dense retrieval QUERY EMBEDDING itself toward accumulated positive
preference signal, not just post-hoc reranking — could in principle expand retrieval recall rather
than only reorder an already-fetched pool.
**RESULT**: validation split (n=40) ON 0.377333 vs OFF 0.376071 (a wash); training split (n=160,
confirmatory) ON 0.415642 vs OFF **0.425645** — a consistent regression on every metric on the
larger split. Plausible cause: nudging only the dense leg away from the literal current-turn text
reduces the BM25/dense complementarity RRF fusion relies on. **CUT**
(`phase2/query_nudge.py`, `ENABLE_QUERY_VECTOR_NUDGE = False`).

### Ablation 5 (new) — Preference-vector boost on vs. off (gates D-PROFILE's ranking effect)
**Procedure**: Phase 0 with `preference_boost()` disabled vs. enabled. **Watch**: MRR/HitRate@10 on
turn 3+ specifically (early turns have little preference signal accumulated yet — the effect should
show up as the session progresses, not from turn 1). **Decision rule**: keep if it shows the
"progressively better-targeted" effect Pillar III describes; if it shows no measurable effect,
demote its weight (`lam`/`mu` in `04_SYSTEM_DESIGN.md`) toward zero rather than ripping out the
mechanism entirely (it's cheap to keep at low weight and directly serves a named pillar in the
writeup even at a small measured effect, unlike the heavier Phase 2 items).

## What to do with ablation results in the writeup

Every ablation run — kept or cut — is genuine deliverable material: it demonstrates deliberate,
capable decision-making (Technical Execution, 35% weight) with concrete evidence rather than assertion.
"We tested K=2/3/4 against K=1, found no significant TechnicalScore improvement, and shipped the
simpler system" is a legitimate, defensible technical story. Include actual before/after numbers, not
just the conclusion, in Phase 5.5's Devpost writeup and the README's limitations section.
