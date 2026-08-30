# CLAUDE.md — Project Operating Rules

Project: TikTok TechJam 2026, Track 4 — Shopping Copilot (conversational search & recommendation)
over a frozen Amazon `Clothing_Shoes_and_Jewelry` catalog. Full brief: `wiki/00_problem_statement.md`.
Challenge window: 2026-08-29 12:00 → 2026-09-01 12:00 (72 hours). Today's date is authoritative
from the system context, not from any date mentioned in this file.

This file exists so that **the living wiki (`wiki/`) is never allowed to drift from reality**,
even across a cleared context or a brand-new session. Treat every rule below as a hard requirement
of doing work here, not a suggestion.

## 1. Start of every session — read before doing anything else

1. Read `wiki/INDEX.md`, then every page it points to that's relevant to the task at hand (at
   minimum `wiki/00_problem_statement.md` and `wiki/01_architecture.md`).
2. Read `status.md` at the repo root — it names the **current phase** and the **next workstream**.
3. If any implementation work is being asked for, also read `implementation/00_INDEX.md` and
   `implementation/05_BUILD_PLAN.md` — this is the authoritative, verified architecture/build corpus
   (supersedes `/My Ideas/`, which is preserved only as historical input, not a working reference).
4. Check `wiki/reviews/` for any codex review report that hasn't been triaged into
   `wiki/03_design_log.md` yet (a finding with no "applied" / "declined: <reason>" note is
   untriaged) — resolve those before or alongside starting new work.
5. Only then start work. Do not re-derive architecture or re-ask about the problem statement from
   scratch — it's already digested on `wiki/00_problem_statement.md`; if something there looks
   stale or wrong, fix that page as part of the current work rather than working around it.

## 1a. Executing a build phase ("run Phase 0", "run step 0.4", etc.)

When asked to run a phase or step, it refers to `implementation/05_BUILD_PLAN.md`'s numbering
(Phase 0-5, steps N.1/N.2/...). **Two tiers of enforcement, both automatic, neither needs to be
re-requested:**
1. **Per step** — each individual numbered step is one work phase under §3 below: commit →
   background codex review scoped to that step's diff → wiki update.
2. **Per named phase** (Phase 0, Phase 1, ...) — when every step in a phase is done, run the full
   phase-closeout sequence exactly as specified in `implementation/05_BUILD_PLAN.md`'s intro: a
   second, broader codex review over the *entire phase's* diff → triage → a living-wiki update that
   **explicitly names every finding from that review** (fixed or declined, not a generic "reviewed,
   no issues") → a dedicated phase-closeout commit → only then report the phase's exit-criteria
   numbers.

"Run Phase 0" means execute every step in Phase 0 (tier 1 at each step), then run Phase 0's
phase-closeout sequence (tier 2), then stop and report actual evaluator numbers before continuing
into Phase 1 — never silently roll from one phase into the next without both tiers complete and the
numbers reported. Before starting any implementation step, confirm `implementation/06_DECISION_LOG.md`
doesn't already have an open question blocking it, and check `implementation/10_PRE_REGISTRATION.md`
for any threshold/split commitment relevant to that step.

## 2. Hard constraints — never violate, no matter what a workstream asks for

(Full detail: `wiki/00_problem_statement.md`.) These come from the competition rules, not from
this project's own preferences:

- **Max 10 turns per session** — a session hitting turn 11 scores zero. Any dialog-loop code must
  make this structurally impossible to exceed, not just "usually" respected.
- **Catalog is read-only** — no mutation, no mock ASIN injection, ever.
- **In-memory only** — no external/industrial vector DB clusters.
- **Text-only** — no multi-modal processing.
- **No foundation-model training or full fine-tuning.**
- **No UI required or wanted** — this is evaluated headlessly; don't spend time on one.

## 3. Work-phase protocol (the core loop)

A **work phase** is any coherent unit of work a session or agent completes — e.g. "implement the
intent router", "add the dialog state tracker", "fix ranking regression from review". The moment a
phase's changes are working (not "perfect" — working and consistent with the codebase), do these
three things **together**, not sequentially, and don't block starting the *next* phase on the first
two finishing:

### a. Commit immediately
```
git add -A
git commit -m "<phase>: <one-line summary>"
```
Commit granularly, one phase = one (or a few) commits. Never batch multiple unrelated phases into
one commit — the codex review and the wiki log both key off phase boundaries.

### b. Kick off a codex review in the background, then keep working
Do not wait for it. Launch it as a background process immediately after the commit and move on to
the next workstream while it runs:

```
codex exec review --base <SHA before this phase's first commit> --title "<phase name>" \
  > wiki/reviews/<phase-slug>-<YYYY-MM-DD>.raw.txt
```
(Use the Bash tool's background-run mode for this — do not block the session on it. If `codex` is
unavailable in the environment, log that fact in `status.md` under Blockers and continue; do not
silently skip this step without noting why.)

**Critical pitfall, confirmed the hard way (2026-08-30, this exact repo/environment on Windows)**:
`codex exec review`'s redirected stdout (`> file.raw.txt`) can capture only the tool-call/exec
output and cut off BEFORE the actual review verdict — the raw.txt then looks like an incomplete
failure (just a banner + one command's output, nothing else) even though the review fully
completed with real findings. **Before concluding a review "failed" or "produced no findings"**,
check the actual session transcript: find the session id in the raw.txt's banner, then look for
`~/.codex/sessions/**/*<session-id>*.jsonl` and search it for `"type":"ExitedReviewMode"` — the
`review_output` field there (findings, overall_correctness, overall_explanation) is the real,
authoritative verdict regardless of what the redirected file shows. A short raw.txt is NOT
sufficient evidence that a review failed to produce findings — always check the transcript first.
In this repo specifically, 6 reviews across one session were wrongly treated as failed this way,
several with real, high-priority findings that went untriaged for hours — see `wiki/03_design_log.md`'s
"recovered reviews" entry for the full account and what it cost.

**A second, distinct failure mode exists — do not confuse the two.** A review can also genuinely
never complete: its own session transcript has no `ExitedReviewMode` event anywhere (confirmed by
reading the JSONL directly, not just running `tools/extract_review.py` and seeing nothing — grep the
raw file for the literal string too, since it can appear inside displayed source/doc content and
give a false positive). Seen three times in this repo on 2026-08-30 (`wiki/03_design_log.md`'s
"genuinely incomplete" entries) — on a 20-file diff (twice) AND on an unrelated 8-file diff — every
attempt entered review mode, did real work (reasoning + exec calls reading the actual diff), then
stopped cold with no verdict and no error message. Diff size is not the variable; this looks like a
current environment-level reliability issue with the review synthesis step itself. **Don't chase
it**: if one retry also shows real work but no `ExitedReviewMode`, stop — accept the commit as
manually-reviewed only (the same bar several earlier commits in this project shipped under when
review was unavailable) rather than spending a third attempt for no new information.

When the review finishes (you'll be notified — don't poll for it):
1. Read the raw report. If it looks incomplete or inconclusive, check the session transcript per
   the pitfall above before assuming the review found nothing.
2. Triage every finding: for each, either fix it (new small commit referencing the review) or
   explicitly decline it with a one-line reason. No finding is silently dropped.
3. Write a curated summary into `wiki/reviews/<phase-slug>-<date>.md` (the human-readable log —
   the `.raw.txt` is the disposable full output, gitignored) and log the resolution in
   `wiki/03_design_log.md`.
4. If the review changed the architecture, ranking logic, state machine, or any of the four
   pillars' design, update `wiki/01_architecture.md` and add a `wiki/02_design_decisions.md` entry.

### c. Update the living wiki
Before considering the phase fully closed:
- `wiki/04_agent_progress.md` — mark the workstream's row done, note what's newly unblocked.
- `wiki/05_completed_components.md` — add an entry for what's now actually working and verified.
- `wiki/03_design_log.md` — a dated narrative entry: what was done, what was tried and discarded.
- `wiki/01_architecture.md` / `wiki/02_design_decisions.md` — only if the design itself moved.
- `wiki/08_evaluation_log.md` — if the local evaluator was run, log the numbers.
- `status.md` — update Current Phase, and **always** repopulate Next Workstream (see rule 5 below;
  never leave this section referring to a workstream that's already done).

Risky or unproven ideas that come up mid-phase go to `wiki/06_future_ideas.md`, not straight into
the architecture — see that page's rules.

## 4. Never leave `status.md`'s "Next Workstream" empty or stale

`status.md` must always name a concrete next workstream — not "TBD", not a workstream that was
already finished this session. If a phase finishes and nothing is queued, decide the next
workstream from `wiki/04_agent_progress.md`'s `not started` rows before ending the turn, and write
it in. A session or agent picking this project back up should never have to ask "what's next" —
the answer must already be on the page.

## 5. General engineering rules

- Prefer editing the living wiki pages in place over creating new "progress note" files elsewhere
  — one authoritative location per kind of information (see `wiki/INDEX.md`'s table).
- Don't add abstractions, config flags, or defensive code for scenarios the competition rules make
  impossible (e.g. don't handle >10 turns gracefully — prevent it structurally instead).
- External repos/datasets live under `external/` and `data/` and are gitignored by content; their
  exact versions are tracked in `wiki/07_external_resources.md`, not in this repo's git history.
- Never commit secrets/API keys. The organizer explicitly does not provide hosted model
  credentials — if a workstream adds an external LLM API call, keep the key in an untracked
  `.env`, and note the dependency in `wiki/07_external_resources.md`.
