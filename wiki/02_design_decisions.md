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
