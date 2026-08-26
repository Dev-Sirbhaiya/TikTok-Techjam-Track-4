# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-26 (project scaffolding phase)

## Current phase

**Project scaffolding & governance setup** (pre-build — challenge window opens 2026-08-29 12:00).
Living wiki, `CLAUDE.md` enforcement rules, git repo, and external resource import are being set up
so build time starting 08-29 goes straight into implementation.

## Next workstream

**Verify the imported participant kit, then start Pillar I (Intent Routing & Hybrid Retrieval
Pipeline).**

Concretely, once the background import agent reports back:
1. Confirm `wiki/07_external_resources.md`'s verification checklist is fully checked off
   (catalog checksum verified, starter BM25 agent runs against the local evaluator, venv installs
   cleanly).
2. Read the participant kit's Agent interface / API contract and the starter BM25 agent's code —
   log what's reusable vs. what needs replacing in `wiki/03_design_log.md`.
3. Run the unmodified starter agent through the local evaluator once, record the baseline in
   `wiki/08_evaluation_log.md` (this is the regression floor everything else is measured against).
4. Begin designing the intent router (Buying vs. Browsing dual-track split) — log the design in
   `wiki/01_architecture.md` and the key decision in `wiki/02_design_decisions.md` before writing
   code.

## Blockers

- None yet. If the background import agent reports `codex` unavailable, a clone/download failure,
  or a checksum mismatch, it goes here with enough detail to unblock in one read.

## Recent activity

- 2026-08-26 — Read and digested all four source docs; confirmed hackathon scope, timeline, hard
  constraints, and evaluation metrics (`wiki/00_problem_statement.md`).
- 2026-08-26 — Initialized git repo, built living wiki (`wiki/`), wrote `CLAUDE.md` enforcement
  rules for the commit + codex-review + wiki-update work-phase loop.
- 2026-08-26 — Launched background agent to clone the participant repo, download/verify the
  participant kit release, and set up the Python venv — see `wiki/07_external_resources.md` for
  outcome once it reports back.

## Open questions / decisions needed from the user

- None blocking right now. Architecture choices for Pillars I–III (retrieval weighting, ranking
  approach, LLM choice if any) will surface real decisions once the starter kit is inspected —
  those will be raised explicitly, not assumed.
