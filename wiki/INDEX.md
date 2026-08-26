# Living Wiki — Index

**Read this file, then `status.md` at repo root, at the start of every session — before touching code.**
See `/CLAUDE.md` for the enforcement rules that keep this wiki authoritative.

This wiki is the persistent memory of the project. If context is cleared or a new
session starts, everything needed to pick up exactly where the last one left off
lives here. Nothing important should exist only in a chat transcript.

## Pages

| # | Page | Purpose |
|---|------|---------|
| 00 | [Problem Statement](00_problem_statement.md) | Condensed, canonical brief: pillars, constraints, limits, eval metrics, timeline |
| 01 | [Architecture](01_architecture.md) | Current system design — living document, edited in place as the design evolves |
| 02 | [Design Decisions](02_design_decisions.md) | Append-only ADR log — every non-trivial decision, with the alternatives rejected and why |
| 03 | [Design Log](03_design_log.md) | Chronological narrative — what was tried, what broke, what changed and why |
| 04 | [Agent & Workstream Progress](04_agent_progress.md) | Table of every workstream: owner/agent, status, started, finished, remaining |
| 05 | [Completed Components](05_completed_components.md) | Inventory of finished, working pieces with file pointers and how to verify them |
| 06 | [Future / Risky Ideas](06_future_ideas.md) | Ideation backlog — speculative or risky ideas not yet approved for the main line |
| 07 | [External Resources & Datasets](07_external_resources.md) | What's imported from GitHub/HF, exact versions/commits/checksums, where it lives locally |
| 08 | [Evaluation Log](08_evaluation_log.md) | Hit Rate@K / MRR / MTTC results per iteration, tracked over time |
| — | [Codex Review Reports](reviews/) | One file per phase review, named `<phase-slug>-<date>.md` |

## Non-negotiable rules for this wiki

1. **Update, don't append-and-forget.** Architecture and progress pages reflect *current* truth. Move stale content to the Design Log instead of leaving two contradictory versions lying around.
2. **Every work phase completion writes to this wiki** before that phase is considered done — update `04_agent_progress.md`, `05_completed_components.md`, and `01_architecture.md`/`02_design_decisions.md` if the design changed.
3. **Every codex review's findings get triaged**: applied fixes are noted in `03_design_log.md` and the relevant page; declined findings are recorded with a one-line reason (not silently dropped).
4. **Nothing risky ships straight to the main design.** New non-trivial or unproven ideas go to `06_future_ideas.md` first; promote them into `01_architecture.md` only once decided.
