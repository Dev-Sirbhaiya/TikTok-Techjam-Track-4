# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-26 (project scaffolding phase)

## Current phase

**Deep research phase** (pre-build — challenge window opens 2026-08-29 12:00). Ten agents running
in parallel right now: 1 importing the participant kit + dataset + venv (`external/`, `data/`,
`.venv/`), 9 researching the technical dimensions of the four problem-statement pillars into
`research/*.md` (see `research/README.md` for the live index). Explicitly research-only — nothing
gets implemented until research + synthesis is done and reviewed with the user (ideation is next,
per user instruction).

## Next workstream

**Once all 9 research agents + the import agent finish: synthesize, then ideate with the user
before writing any code.**

Import workstream is **done** (checksum verified, baseline recorded — see Recent Activity). Left:
1. Once all 9 research agents finish: read `research/01_*.md` through `research/09_*.md`. Write
   `research/DOS_AND_DONTS.md` — a single master list merging every file's Dos/Don'ts section,
   deduplicated, organized by pillar, cross-checked against the hard constraints in
   `wiki/00_problem_statement.md`.
2. Cross-reference research agent 9's starter-kit findings (gathered via web inspection) against
   the actual cloned repo at `external/techjam-conversational-search/` (now available locally) to
   confirm the Agent interface / API contract / evaluator understanding is accurate — correct
   agent 9's file if it inferred something the real code contradicts.
3. Bring the synthesized findings + Dos/Don'ts back to the user for ideation on Pillars I-III
   before any architecture gets written into `wiki/01_architecture.md` — user explicitly asked to
   ideate together after research, not before.

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
- 2026-08-26 — Launched 9 parallel deep-research agents into `research/0X_*.md` covering all four
  problem-statement pillars plus evaluation methodology and prior art — still running, see
  `research/README.md`.

## Open questions / decisions needed from the user

- None blocking right now. Architecture choices for Pillars I–III (retrieval weighting, ranking
  approach, LLM choice if any) will surface real decisions once the starter kit is inspected —
  those will be raised explicitly, not assumed.
