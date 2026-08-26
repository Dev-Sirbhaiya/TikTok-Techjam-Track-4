# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-26 (deep research phase complete)

## Current phase

**Deep research phase — complete.** All 9 parallel research agents finished (intent routing,
hybrid retrieval, LLM reranking, dialogue state tracking, clarification generation, context
distillation/personalization, adaptive orchestration, evaluation benchmarks, prior art + starter
kit), synthesized into `research/DOS_AND_DONTS.md`, and cross-verified against the actual cloned
participant repo source (not just web-fetched docs) — ground truth captured in
`wiki/09_simulator_mechanics.md`. Pre-build — challenge window opens 2026-08-29 12:00.

## Next workstream

**Ideate with the user on Pillars I-III architecture, informed by `research/DOS_AND_DONTS.md` and
`wiki/09_simulator_mechanics.md` — no code yet, per explicit user instruction to research first.**

Concretely, once the user is ready to ideate:
1. Walk through the build-order priority from `research/DOS_AND_DONTS.md` §0: retrieval coverage
   first (highest TechnicalScore weight, gates MRR mathematically), then ranking precision, then
   turn-efficiency as a gate not a goal.
2. Decide concretely, per pillar, from the ranked options each research file lays out — e.g.
   Pillar I: gazetteer+embedding hybrid intent router vs. single LLM-call router; BM25+dense+RRF
   retrieval stack and specific embedding model choice; cross-encoder-guaranteed reranker with
   optional LLM booster. Each decision becomes a `wiki/02_design_decisions.md` entry and gets
   reflected in `wiki/01_architecture.md`.
3. Resolve the one flagged ambiguity that needs a call either way before Pillar III design locks
   in: "long-term user profile" interpretation (research/06 recommends within-session slow-decay
   layer, not cross-session store — see that file's dedicated section).
4. Once Pillars I-III have a decided shape, plan implementation phases (each phase = commit +
   background codex review + wiki update per `CLAUDE.md` §3) and update this section with the
   first concrete implementation workstream.

## Blockers

- **`codex` CLI is installed but not authenticated** — `codex exec review --commit e5560788...`
  failed with `401 Unauthorized: refresh_token_invalidated` (session expired/revoked). The
  CLAUDE.md work-phase review step cannot run until this is fixed.
  **Action needed from the user**: run `! codex login` to re-authenticate, then re-run the review
  with `codex exec review --commit e5560788b47cbd8c4afb27584d55f87adbd28a61 --title "Project
  scaffolding: living wiki + CLAUDE.md governance"` to get the deferred first review. Until then,
  future phases should still commit + update the wiki on schedule; codex review kicks off as soon
  as it's usable again, and any backlog gets reviewed against `--base` ranges spanning the skipped
  phases rather than being skipped entirely.

## Recent activity

- 2026-08-26 — Read and digested all four source docs; confirmed hackathon scope, timeline, hard
  constraints, and evaluation metrics (`wiki/00_problem_statement.md`).
- 2026-08-26 — Initialized git repo, built living wiki (`wiki/`), wrote `CLAUDE.md` enforcement
  rules for the commit + codex-review + wiki-update work-phase loop.
- 2026-08-26 — **External resource import completed successfully, no blockers.** Participant repo
  cloned (`external/techjam-conversational-search/` @ `9a35be5`), participant kit downloaded and
  **SHA256-verified** (`data/participant-kit/`), venv set up at `.venv/` (confirmed stdlib-only —
  no dependencies to install), and the unmodified starter BM25 agent run through the local
  evaluator: **Hit Rate@10 0.125, MRR 0.068034, MTTC 9.81, TechnicalScore 0.10671** — this is now
  our regression floor (`wiki/08_evaluation_log.md`). Full detail in
  `wiki/07_external_resources.md` (checklist fully checked off).
- 2026-08-26 — **Deep research phase completed, all 9 agents, no blockers.** `research/0X_*.md`
  covers all four problem-statement pillars plus evaluation methodology and prior art, each with
  citations and topic-scoped Dos/Don'ts. Synthesized into `research/DOS_AND_DONTS.md`. In parallel,
  personally verified the actual evaluator/starter-agent source code (not just docs) and captured
  ground-truth session/scoring mechanics in new page `wiki/09_simulator_mechanics.md` — confirmed
  the TechnicalScore formula directly from source, confirmed category is disclosed turn-1 in every
  scenario, confirmed the exact clarification-reveal heuristic, confirmed local dev requires
  editing `starter/agent.py` in place (hardcoded import, no override flag).

## Open questions / decisions needed from the user

- **Ready for ideation now.** Architecture choices for Pillars I–III are laid out with ranked
  options in `research/DOS_AND_DONTS.md` — none are decided yet, all await the ideation session.
- Whether an external LLM API will actually be used (org provides no credits/keys) — affects
  whether the reranker/orchestrator design should assume an LLM is available or build the
  no-paid-API cross-encoder path as primary (research leans toward the latter regardless).
- Confirm the "long-term user profile" interpretation (research/06's recommended reading: a
  within-session, slow-decaying layer, not cross-session persistence) before Pillar III design
  locks in — flagged as a genuine ambiguity in the problem statement, not resolvable from the docs
  alone.
- `codex login` still needed to unblock the codex-review half of the work-phase loop (see
  Blockers) — not urgent for research/ideation, but should happen before the first implementation
  phase so review coverage doesn't have a growing backlog.
