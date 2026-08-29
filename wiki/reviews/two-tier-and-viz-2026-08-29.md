# Codex Review — Two-Tier Protocol + Frontend Viz + Round-1 Fixes (2026-08-29)

Reviewed commit `e5c9eab` (round-1 fixes to the architecture-synthesis findings). Full raw output:
`two-tier-and-viz-2026-08-29.raw.txt` (gitignored). Curated findings + resolutions in full at
`implementation/06_DECISION_LOG.md`'s "Codex review findings — round 2" section — summary here:

**7 second-order findings on the round-1 fixes themselves, all fixed, none declined:**
- 3× P1: unit-temperature softmax saturates on RRF's tiny score gaps (needs a calibrated
  temperature); the offline-model fix treated prefetch as equal to bundling (bundling is now
  required); the evaluator shim generator was described but not actually required by step 0.1's
  checklist.
- 3× P2: Phase 1's validation-split number wasn't comparable to Phase 0's full-200 number; the
  phase-closeout sequence didn't wait for outstanding step-level reviews; Phase 2.5 had a
  phase-review pointed at a necessarily-empty diff.
- 1× P3: the viz spec's preference-vector sparkline would have plotted an always-≈1 value (EMA
  vectors are unit-normalized) — fixed to plot turn-over-turn cosine stability instead.

A healthy sign: the review loop caught real issues in its own previous fixes, not just first drafts.
