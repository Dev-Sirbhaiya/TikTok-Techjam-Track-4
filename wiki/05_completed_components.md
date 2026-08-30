# 05 — Completed Components

Inventory of pieces that are actually done and verified — not "written", but working. Each entry
should let a new session trust the component without re-reading its code.

Format per entry:
```
### <component name>
- Location: <path(s)>
- What it does: <one or two sentences>
- Verified by: <test/eval command and result, or manual check performed>
- Completed: YYYY-MM-DD (workstream: <name>)
```

---

**Note (2026-08-30):** this page was never populated per-component as Phases 0-5.3 shipped, despite
`CLAUDE.md`'s rule to update it every phase — that's real drift, not "nothing was built." The
authoritative per-phase status/verification lives in `wiki/04_agent_progress.md` (one row per
workstream, what's done and how it was verified) and `wiki/08_evaluation_log.md` (every evaluator
run with numbers) — check those first. Entries below start from Phase 5.4/5.5's new tooling, since
this is the first time since the gap was noticed that new pieces are being added.

### `tools/trace_session.py`
- Location: `tools/trace_session.py`
- What it does: runs one real public-set session end-to-end through the actual agent and prints a
  readable per-turn trace (customer message, agent response, hit/miss), reusing the organizer's own
  `initial_message`/`customer_reply`/`materialize_hidden_fields` simulation functions directly so
  the traced behavior is identical to a real scored run. Built for the Phase 5.4 demo video
  recording, not a scored-path tool.
- Verified by: manual run, `python tools/trace_session.py --sample-id public_0005` — clean 3-turn
  trace ending in a hit at rank 1, matching `results.json`'s recorded outcome for that session. An
  earlier test run (before the cwd fix below) surfaced a real bug, not just validated the happy
  path.
- Completed: 2026-08-30 (workstream: Phase 5.4 demo video prep). **Self-caught bug, same day**:
  first test run hung for 7+ minutes instead of the expected ~10-15s, because `Agent` was
  constructed with the process cwd at the repo root while the embedding cache artifact actually
  lives under the participant repo's `data/` dir (an artifact of `tools/run_eval.py` running the
  evaluator with `cwd=<participant repo>`) — a cache miss silently launches a ~14.5-minute
  full-catalog re-encode. Fixed with an explicit `os.chdir(PARTICIPANT_REPO)` before constructing
  `Agent`, matching the eval convention; re-verified fast (cache hit) after the fix.

### `tools/diagnose_buying_recall.py`
- Location: `tools/diagnose_buying_recall.py`
- What it does: for every session, measures whether the hidden target ever reaches the fused/
  filtered candidate pool (before rerank) vs. reaches it but never the final top-10 vs. hits.
  Monkeypatches `retrieve_candidates`/`route_retrieval_breadth` at the point `agent.py` calls them
  (no scored file edited) so it's pure measurement, safe to run against the full 200-session set.
  This is what found the buying-track gap's actual root cause (see D-HARD-FILTER-EXT).
- Verified by: full 200-session run (all scenarios) plus a buying-only `--no-hard-filter` isolation
  run — see `wiki/08_evaluation_log.md`'s 2026-08-30 rows for the exact numbers.
- Completed: 2026-08-30 (workstream: Phase 5.6)

### `docs/DEMO_VIDEO_SCRIPT.md` / `docs/DEVPOST_WRITEUP.md`
- Location: `docs/DEMO_VIDEO_SCRIPT.md`, `docs/DEVPOST_WRITEUP.md`
- What it does: a recordable script for the Phase 5.4 demo video and a full draft of every standard
  Devpost section for Phase 5.5, both built from this project's real, current numbers and honest
  ablation history rather than placeholder text.
- Verified by: cross-checked against `implementation/02_TECHNICAL_PRD.md`'s deliverable checklist
  and `status.md`'s current score table for numeric accuracy.
- Completed: 2026-08-30 (workstream: Phase 5.4/5.5 drafting) — still needs the user's confirmation
  on SQ3/SQ5 and the actual repo/video URLs before publishing; see `status.md`.
