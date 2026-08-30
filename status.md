# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-30 (Phases 0-4 all closed out; proceeding to Phase 5, submission packaging)

## Current phase

**Phases 0 through 4 are all DONE.** Full chronological detail lives in `wiki/03_design_log.md`
(one dated entry per phase/finding) and `wiki/08_evaluation_log.md` (every evaluator run). This
section is the current-state summary only — don't duplicate narrative here, update it there.

**Score progression** (full 200-session evaluator, `TechnicalScore = 0.50×HitRate@10 + 0.30×MRR +
0.20×Efficiency`):

| Stage | TechnicalScore | Notes |
|---|---|---|
| Organizer's baseline | 0.1067 | unmodified weak BM25 starter |
| Phase 0 | 0.3284 | first working hybrid agent |
| Phase 1 | 0.4087 | calibration + named adaptive orchestrator |
| Phase 2 (corrected) | 0.4093 | see reproducibility-bug note below |
| Phase 3 | 0.4093 | unchanged (3.1/3.2 didn't touch scored code) |
| **Phase 3.5 (guaranteed path — no API key)** | **0.4157** | **realistic expected competition score** |
| Phase 3.5 (optional, `ANTHROPIC_API_KEY` present) | 0.4383 | bonus/demo ceiling, not the scored number |

**Report 0.415731 as the expected competition score in any writeup.** The 0.4383 ceiling requires
`ANTHROPIC_API_KEY`, which the organizer does not provide for official grading — that mechanism is
almost certainly inert during real judging.

**What shipped (guaranteed path, always active)**:
- Hybrid BM25 + dense + metadata retrieval, RRF fusion, cross-encoder reranking (Phase 0).
- Calibrated clarification thresholds, named adaptive orchestrator (Phase 1).
- Retriever-disagreement VoI signal, multi-interest, contextual bandit — all three ablated,
  **all three cut** after a reproducibility bug fix reversed VoI's original "kept" verdict (Phase 2).
- Systematically-verified-robust clarification thresholds; comparative feedback confirmed
  structurally impossible against the actual simulator, correctly not built (Phase 3).
- **Portfolio/slate hedging** — real, validated win, enabled by default (Phase 3.5).

**What shipped (optional, requires a local API key, inert during official grading)**:
- LLM listwise reranker (Claude Haiku 4.5) — genuine +6.4% win when a key is present (Phase 3.5).

**What was tried and honestly declined** (all documented with real ablation numbers, not hidden):
query-vector nudging, rerank-pool-depth widening, weighted RRF fusion (metadata leg), and Phase 4's
1-step lookahead question selector — each looked reasonable on paper or even won on the training
split, but didn't survive validation-split confirmation or a mandatory higher-bar gate. Full
reasoning for each is in `wiki/03_design_log.md`'s 2026-08-30 entries.

**Reproducibility**: a real hash-seed nondeterminism bug (`catalog.py`'s `set` iteration order) was
found and fixed — the agent's behavior on the deterministic simulator is now verified byte-identical
across repeated runs of the same config.

## Next workstream

**Phase 5 — submission packaging, in progress.** 5.1 (final numbers) and 5.2 (package
`submission/`, bundle offline model + embedding-cache artifacts, verify genuine offline
reproducibility) are **done** — see `implementation/05_BUILD_PLAN.md`'s Phase 5 section for full
detail. `tools/build_submission.py` regenerates `submission/` (gitignored, a build artifact) from
scratch any time; re-run it if `src/copilot/` changes before the actual submission.

5.3 is also **done**: `docs/SUBMISSION_README.md` (tracked source, copied into `submission/
README.md` by the build script) covers approach, setup, run command, model/cost/latency/offline
disclosure, limitations, and contribution breakdown.

**Remaining**: 5.4 (demo video — a multi-turn session walkthrough, no UI required; needs the
user's input on scope/format, `implementation/09_SUPERVISOR_QUESTIONS.md` SQ4), 5.5 (Devpost
written submission — cross-reference `implementation/02_TECHNICAL_PRD.md`'s deliverable checklist).
Before writing the Devpost writeup, re-read `implementation/06_DECISION_LOG.md` in full — it now
contains a complete, honest "tried, measured, kept/cut" record across every phase, exactly the
Technical Execution narrative material the competition rewards. Confirm
`implementation/09_SUPERVISOR_QUESTIONS.md`'s open items (SQ3, SQ5 too) before finalizing.

## Blockers

- **Codex automated review is unreliable in this environment.** Root cause identified: `codex
  doctor` showed Windows `sandbox backend: elevated`, which needs `CreateProcessAsUserW` to spawn
  subprocesses — that's what was failing with "Access is denied." A `Bash(codex exec review:*)`
  permission rule plus `-c windows.sandbox="unelevated"` fixes the hard crash (valid values are
  `elevated`/`unelevated`, not `none`), but most attempts still exit cleanly without producing a
  review verdict — a separate, undiagnosed issue in codex's own review loop. Across this session,
  roughly 2 of 10+ attempts produced a real, complete review (one found and fixed a genuine bug in
  `tools/tune_strategy.py`); the rest did not reach a verdict. **Not treated as unreviewed work**:
  every shipped change was verified via careful manual code review plus rigorous empirical
  ablation (typically 2 independent splits, checked for regressions on every scenario) before
  shipping — the same standard this project has applied throughout. If picking this up again,
  always pass `-c windows.sandbox="unelevated"`, but don't expect it to reliably complete.

## Recent activity

- 2026-08-26 to 2026-08-29 — Project scaffolding, research, architecture corpus, two-tier codex
  review protocol. Phase 0 shipped (TechnicalScore 0.328, 3.1x baseline).
- 2026-08-29 — Phase 1 shipped (0.4087, +24.5%).
- 2026-08-30 — Phase 2 shipped (0.4111), then corrected to 0.4093 after a reproducibility bug fix
  reversed one ablation's verdict. Phase 3 closed out (3.1 robust, 3.2 confirmed impossible).
  Phase 3.5: LLM booster (+6.4%, optional) and slate hedging (+1.9%, guaranteed) both shipped;
  query-vector nudge, rerank-depth widening, and weighted RRF all tried and declined. Phase 4's
  1-step lookahead tried and declined, matching its own predicted risk. **Guaranteed-path exit:
  TechnicalScore 0.415731.**

## Open questions / decisions needed from the user

- `implementation/09_SUPERVISOR_QUESTIONS.md` SQ3-SQ5 (team/demo/workshop notes) — needed before
  Phase 5's writeup is finalized.
