# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-29 (Phase 0 shipped and closed out; continuing directly into Phase 1)

## Current phase

**Phase 0 — DONE.** Full hybrid-retrieval agent (`src/copilot/`) implemented, unit-tested (26
passing), codex-reviewed twice (architecture docs + implementation code, 14 total findings across
both, all fixed), and benchmarked against the real 200-session evaluator: **TechnicalScore 0.328,
HitRate@10 0.39, MRR 0.2256, MTTC 7.715 — 3.1x the organizer's baseline (0.107)**. Full before/after
fix comparison in `wiki/08_evaluation_log.md`; one honest finding flagged forward (buying-track
regressed slightly after the review fixes, flagged as a Phase 1.3 calibration target, not reverted).
User has set a standing goal to continue directly through Phase 1 → 2 → 3 without stopping to ask,
benchmarking at each phase.

## Next workstream

**Run `implementation/05_BUILD_PLAN.md` Phase 1 (steps 1.1-1.4): cheap refinements + calibration.**

Concretely: 1.1 audit for leftover weighted-sum logic (should already be clean — RRF was correct
from the start); 1.2 confirm the entropy formula matches the spec exactly (it does, post both review
rounds); **1.3 is the important one this time**: create the pre-registered 160/40 train/validation
split, then sweep `overgenerality.py`'s `temperature`/`low`/`high` and `ranker.py`'s `margin_skip` —
specifically targeting the buying-track regression noted in `wiki/08_evaluation_log.md`; 1.4 add the
named, logged adaptive-orchestration branch points (FR-8 completion). Then Phase 1's phase-level
review + closeout, then directly into Phase 2 (gated ablations: multi-interest, bandit, VoI) per the
user's standing goal — do not stop to ask before continuing into Phase 2.

## Blockers

None.

## Recent activity

- 2026-08-26 to 2026-08-29 (early) — Project scaffolding, research, architecture corpus
  (`implementation/`), two-tier codex review protocol. Full detail in `wiki/03_design_log.md`.
- 2026-08-29 — **Phase 0 implemented and shipped.** `src/copilot/` (14 modules), `tools/install_shim.py`
  + `tools/run_eval.py`, 26 unit tests. Self-caught 6 real bugs during implementation (BM25 full-scan,
  O(n) embedding lookup, retrieval losing accumulated context, multi-value slot overwrite, scale-
  mismatch risk, slow embedding text) before any review touched the code.
- 2026-08-29 — **Real environment finding (D-EMBED-CACHE)**: catalog dense-embedding throughput was
  inconsistent in this dev sandbox; resolved by treating it as a one-time cost, cached and shipped as
  a submission asset (`implementation/06_DECISION_LOG.md`).
- 2026-08-29 — **Codex review of the Phase 0 implementation**: 7 findings (4 P1, 3 P2), all fixed —
  clarification declines misread as rejections, missing askable facets, price/entropy cardinality
  dominance, cache-failure retry storm, override not resetting preference vectors, category
  comma-split mismatch, word-boundary bug. See `wiki/reviews/phase0-implementation-2026-08-29.md`.
- 2026-08-29 — **Phase 0 closed out**: real 200-session evaluator numbers recorded (both pre- and
  post-fix, honestly compared — see Current Phase above), wiki updated, committed. TechnicalScore
  0.328, 3.1x baseline.

## Open questions / decisions needed from the user

- `implementation/09_SUPERVISOR_QUESTIONS.md` SQ1 (LLM provider choice, if any — Phase 0-1 need none)
  and SQ3-SQ5 (team/demo/workshop notes). SQ2 (how far into Phase 2+) is now answered by the
  standing `/goal`: continue through Phase 3.
