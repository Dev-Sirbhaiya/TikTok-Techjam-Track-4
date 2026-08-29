# 09 — Supervisor Questions

Everything resolvable from the docs/code already has been (see `06_DECISION_LOG.md`'s resolved
`/My Ideas/` open questions). What's left here are genuine calls only you can make — decisions that
trade off time, risk, or preference rather than facts that can be looked up.

## SQ1 — Will an external LLM API actually be used, and which one?
The organizer provides no credits/keys; Phase 0 is designed to fully function and beat the baseline
with zero LLM calls (D-LLM-TIER). If you want to use one anyway (for the slot-extraction arbiter and/or
the listwise-rerank booster), which provider/model, and what's the cost tolerance? This doesn't block
starting Phase 0 — the code is written provider-agnostic behind an `llm_client` parameter that's `None`
by default — but it does affect whether Ablation 4 (`08_ABLATION_MATRIX.md`) is worth running early.

## SQ2 — How far into Phase 2+ should we actually push, given the real clock?
Today is 2026-08-29; submissions close 2026-09-01 12:00 — roughly 72 hours, minus time for the demo
video and writeup. `05_BUILD_PLAN.md`'s phases are ordered by ROI, but only you can decide the actual
risk tolerance for attempting Phase 2 (multi-interest/bandit) vs. stopping at Phase 1 and investing the
remaining time in calibration + a polished writeup. Recommendation embedded in the plan: don't start
Phase 2 until Phase 0/1 are fully passing and their numbers are recorded — but the decision to *attempt*
Phase 2 at all, given remaining hours, is yours to make when you get there.

## SQ3 — Team size / division of labor?
`03_SYSTEM_ARCHITECTURE.md`'s module decoupling (separate files, narrow interfaces) was designed partly
so a team could parallelize without blocking each other. If this is solo, the phase-by-phase sequential
order in `05_BUILD_PLAN.md` is the right path. If there's a team, natural parallel splits are: (a)
retrieval + fusion (0.1-0.2), (b) dialog state + rejection memory + override detection (0.4-0.6), (c)
reranker + turn policy + orchestrator (0.9-0.10) — each depends on 0.1's gazetteer/catalog load but not
heavily on each other until 0.11's integration.

## SQ4 — Demo video scope and timing?
Phase 5.4 needs a recorded walkthrough. Given no UI is built (correctly, per spec), this will be an
API-usage/inference-example walkthrough — worth deciding early whether this is a live terminal
recording of `python -m evaluator.local_evaluator` plus a narrated single session trace, or something
more produced. Doesn't block coding, but recording it needs a stable, working Phase 0/1 system, not the
final hour's system.

## SQ5 — Is there anything time-sensitive outside this repo (workshop notes, teammate input, updated
organizer guidance) that should be folded in before Phase 0 starts?
The 2026-08-28 technical workshop (Track 4, 4-4:45pm) may have surfaced organizer clarifications not
captured in the written docs. If you attended or have notes, worth a quick check against
`wiki/00_problem_statement.md` and this corpus before committing to Phase 0 — cheap to check now,
expensive to discover a contradiction mid-build.
