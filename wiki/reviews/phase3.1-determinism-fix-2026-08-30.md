# Codex Review: Phase 3.1 Determinism Fix + Phase 2 Re-ablation

**Commit reviewed**: `7be9ba7` ("Fix hash-seed nondeterminism bug; re-ablate Phase 2, reverse VoI to cut")
**Date**: 2026-08-30
**Raw output**: `phase3.1-determinism-fix-2026-08-30.raw.txt` (gitignored)

## Summary

Codex's own assessment: "The determinism fixes and production defaults appear sound, but the new
tuning harness does not isolate candidate configurations from its parent environment. That can
invalidate the Phase 3.1 sweep and make its reported winner irreproducible."

## Findings

1. **[P2] Clear inherited strategy overrides before each rollout** — `tools/tune_strategy.py:44`.
   `env = dict(os.environ)` carries any `COPILOT_*` variable already present in the invoking shell
   into every subprocess, so a candidate that omits that key — including `baseline: {}` — silently
   runs with the inherited value rather than `strategy_config.py`'s committed default. The logged
   output only shows the JSON overrides, so a contaminated run would look reproducible without
   being so.

   **Status: FIXED.** `run_one()` now pops every entry in `ENV_VAR_BY_KEY.values()` from the
   subprocess environment before applying the candidate's own overrides, guaranteeing each omitted
   key resolves to `strategy_config.py`'s hardcoded default regardless of the invoking shell's state.

   **Verified no actual contamination occurred**: checked the invoking shell (`env | grep COPILOT_`)
   before applying the fix — no such variables were present, so none of this session's reported
   sweep results (round 1, round 2, round 3, or the extreme-value checks) were affected. Fixed
   anyway for correctness and to protect any future re-run of this harness.

## Not flagged, but worth recording

The review's own framing ("determinism fixes and production defaults appear sound") is itself part
of the record — codex independently found no issue with the core fix (sorted iteration in
`catalog.py`'s `bm25_search`/`metadata_rank` and the gazetteer's colors/materials) or with the
reversed VoI ablation decision.
