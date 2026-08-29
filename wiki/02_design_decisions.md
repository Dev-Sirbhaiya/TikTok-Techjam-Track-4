# 02 — Design Decisions (Append-Only ADR Log)

Append a new entry per non-trivial decision. Never edit or delete a past entry — if a decision is
reversed, add a new entry that supersedes it and link back. This is the record of *why*, which
`01_architecture.md` (the record of *what, currently*) intentionally omits.

## Template

```
## DD-<NNN> — <title>
- Date: YYYY-MM-DD
- Phase / workstream: <name>
- Decision: <what was decided>
- Alternatives considered: <what else, and why rejected>
- Why: <the actual reasoning — constraints, tradeoffs, eval impact>
- Status: proposed | accepted | superseded by DD-<NNN>
```

---

## DD-001 — Governance scaffolding before build start
- Date: 2026-08-26
- Phase / workstream: Project setup
- Decision: Set up living wiki, CLAUDE.md enforcement rules, status.md, git repo, and external
  resource import *before* any solution code is written, ahead of the 2026-08-29 challenge start.
- Alternatives considered: Start coding directly and document post-hoc — rejected because context
  loss across sessions during a 72-hour crunch is expensive, and undocumented architecture
  decisions made under time pressure are exactly the ones worth losing least.
- Why: The hackathon window is only 72 hours; a session/context reset mid-challenge must not cost
  re-discovery time. Also: codex-review + git-commit + wiki-update per phase needs the scaffolding
  in place from phase 1 to be enforceable at all.
- Status: accepted

## DD-002 — Solution architecture decided; full log lives in `implementation/06_DECISION_LOG.md`
- Date: 2026-08-29
- Phase / workstream: Architecture synthesis (user-provided ideas + 9-file research corpus + verified ground truth)
- Decision: The full architecture, build plan, and every individual design decision (D1-D17,
  D-PROFILE, D-PACKAGING, D-LLM-TIER, D-LATENCY) live in `implementation/06_DECISION_LOG.md`, not
  duplicated here — this page (`01_architecture.md`) stays a condensed summary pointer. Every open
  question from the user's own `/My Ideas/04_OPEN_QUESTIONS.md` was resolved against the actual
  evaluator/starter-agent source code, not inference.
- Alternatives considered: Duplicate full decision detail into this wiki page — rejected as
  maintenance burden with no benefit; one authoritative location per `CLAUDE.md`'s own rule.
- Why: `implementation/` is purpose-built as the detailed planning corpus (PRD, system design,
  build plan with numbered phases, ablation matrix, risk register, pre-registration); `wiki/` stays
  the living, kept-current summary + progress record per its original design.
- Status: accepted
