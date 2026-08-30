# Status

> Read this after `wiki/INDEX.md` at the start of every session. See `CLAUDE.md` §3–4 for the
> rules that keep this file honest — it must always name a concrete next workstream, and every
> work-phase completion must update it.

Last updated: 2026-08-30 (Phase 5.6: diagnosed and fixed the buying-track retrieval-recall gap —
new guaranteed-path headline score 0.471193, up from 0.406428)

## Current phase

**Phases 0 through 5.6 are all DONE.** Full chronological detail lives in `wiki/03_design_log.md`
(one dated entry per phase/finding) and `wiki/08_evaluation_log.md` (every evaluator run). This
section is the current-state summary only — don't duplicate narrative here, update it there.

**Score progression** (full 200-session evaluator, `TechnicalScore = 0.50×HitRate@10 + 0.30×MRR +
0.20×Efficiency`):

| Stage | TechnicalScore | Notes |
|---|---|---|
| Organizer's baseline | 0.1067 | unmodified weak BM25 starter |
| Phase 0 | 0.3284 | first working hybrid agent |
| Phase 1 | 0.4087 | calibration + named adaptive orchestrator |
| Phase 2 (corrected) | 0.4093 | reproducibility bug fix reversed one ablation's verdict |
| Phase 3 | 0.4093 | unchanged (3.1/3.2 didn't touch scored code) |
| Phase 3.5, guaranteed path (no API key) | 0.4064 | superseded below |
| Phase 3.5, optional (`ANTHROPIC_API_KEY` present) | 0.4299 | superseded below |
| **Phase 5.6, final, guaranteed path (no API key)** | **0.4712** | **realistic expected competition score** |
| Phase 5.6, optional (`ANTHROPIC_API_KEY` present) | not yet re-measured | attempted, killed mid-run by an interrupt; the old +6.4pp ceiling delta is stale, don't assume it still applies on top of 0.4712 |

**Report 0.471193 as the expected competition score in any writeup** — up from 0.406428
(+15.9%), the largest single improvement of the project, from diagnosing and fixing a real gap in
the Buying-track hard filter (see "Phase 5.6" below). The organizer does not provide
`ANTHROPIC_API_KEY` for official grading, so the optional LLM-booster ceiling remains inert during
real judging regardless of its number — report the guaranteed figure as the expected score.

**Phase 5.6 — buying-track retrieval-recall fix (2026-08-30)**: after Phase 5.4/5.5's packaging
work, a new diagnostic (`tools/diagnose_buying_recall.py`, not scored-path code) directly measured
*why* buying underperformed — something no prior fix attempt this session had actually checked
first. It found 37.5% of buying-scenario targets never reached the fused candidate pool at all (vs.
26.2% for browsing) and, via an isolation test forcing the existing hard filter off, proved that
filter had ZERO effect on this — it only ever restricted on category/brand/budget, never on the
disclosed material/color/style hard constraint itself (brand is structurally almost never disclosed
per resolved-Q2, so the filter reduced to "category-only" for most buying sessions). A new
`EXTENDED_HARD_FILTER_ATTRS` flag (`catalog.py`'s `apply_hard_filters`, new `_by_material`/
`_by_color`/`_by_style` indices) also restricts on those attributes when disclosed. Ablated per this
project's pre-registration discipline: training split (n=160) +7.7% TechnicalScore; **validation
split (n=40, held out) +14.8% TechnicalScore, +16.7% HitRate@10** — a clean win on BOTH splits,
unlike several earlier buying-track attempts (weighted RRF, slate hedging, query nudge) that looked
good on training and failed or reversed on validation. **ENABLED by default.** Full 200-session
guaranteed-path exit: TechnicalScore 0.471193 (HitRate@10 0.55, MRR 0.347643, MTTC 6.405) — buying's
own hit rate rose to 0.475, from roughly 0.36-0.39 across every prior measurement this session. See
`wiki/08_evaluation_log.md` and `implementation/06_DECISION_LOG.md` for the full account.

**A major process failure and recovery happened earlier in Phase 3.5/4/5's work**: roughly a dozen
`codex exec review` attempts across this session appeared to fail (short, incomplete-looking
output), and were logged as an environment blocker. One review's actual verdict was eventually found
sitting in its session transcript, never having reached the redirected output file at all —
`codex exec review`'s final verdict can render through a channel plain file redirection doesn't
reliably capture, even when the review fully completed. **6 of these "failed" reviews across this
session had actually completed with real findings**, unread for hours. All 9 findings were recovered
and triaged (fix or explicit decline, per protocol) — see `wiki/03_design_log.md`'s "recovered
reviews" entry for the full account, and `CLAUDE.md` for the process fix so this can't recur silently.
Two were genuine submission-breaking bugs (an embedding-cache path that resolved against the wrong
working directory, defeating the whole point of bundling it; a build script that could silently ship
an incomplete bundle) that would very likely have gone unnoticed until official scoring. One reversed
a previously-reported "shipped win" (slate hedging) after the review correctly caught that its
held-out validation result was a wash, not a confirmed improvement, and that the reasoning used to
ship it anyway ("training split suggests it's real, validation just lacks power") was exactly the
kind of post-hoc rationalization this project's own pre-registration rule exists to prevent.
Separately, a distinct, genuinely-incomplete-review failure mode (not the redirect bug) was found and
documented the same day — see `CLAUDE.md`'s protocol note.

**A major process failure and recovery happened late in Phase 3.5/4/5's work**: roughly a dozen
`codex exec review` attempts across this session appeared to fail (short, incomplete-looking
output), and were logged as an environment blocker. One review's actual verdict was eventually found
sitting in its session transcript, never having reached the redirected output file at all —
`codex exec review`'s final verdict can render through a channel plain file redirection doesn't
reliably capture, even when the review fully completed. **6 of these "failed" reviews across this
session had actually completed with real findings**, unread for hours. All 9 findings were recovered
and triaged (fix or explicit decline, per protocol) — see `wiki/03_design_log.md`'s "recovered
reviews" entry for the full account, and `CLAUDE.md` for the process fix so this can't recur silently.
Two were genuine submission-breaking bugs (an embedding-cache path that resolved against the wrong
working directory, defeating the whole point of bundling it; a build script that could silently ship
an incomplete bundle) that would very likely have gone unnoticed until official scoring. One reversed
a previously-reported "shipped win" (slate hedging) after the review correctly caught that its
held-out validation result was a wash, not a confirmed improvement, and that the reasoning used to
ship it anyway ("training split suggests it's real, validation just lacks power") was exactly the
kind of post-hoc rationalization this project's own pre-registration rule exists to prevent.

**What shipped (guaranteed path, always active)**:
- Hybrid BM25 + dense + metadata retrieval, RRF fusion, cross-encoder reranking (Phase 0).
- Calibrated clarification thresholds, named adaptive orchestrator (Phase 1).
- Retriever-disagreement VoI signal, multi-interest, contextual bandit — all three ablated,
  **all three cut** after a reproducibility bug fix reversed VoI's original "kept" verdict (Phase 2).
- Systematically-verified-robust clarification thresholds; comparative feedback confirmed
  structurally impossible against the actual simulator, correctly not built (Phase 3).
- Extended hard-filter attributes (material/color/style, not just category/brand/budget) for
  Buying-track retrieval — the single largest win of the project, +15.9% TechnicalScore (Phase 5.6).

**What shipped (optional, requires a local API key, inert during official grading)**:
- LLM listwise reranker (Claude Haiku 4.5) — genuine win when a key is present (Phase 3.5),
  re-verified after a recovered review found the original "determinism fix" attempt was itself
  broken (unsupported SDK parameter silently crashed and disabled the whole mechanism).

**What was tried and honestly declined** (all documented with real ablation numbers, not hidden):
query-vector nudging, rerank-pool-depth widening, weighted RRF fusion (metadata leg), portfolio/
slate hedging (reversed after shipping — see above), and Phase 4's 1-step lookahead question
selector — each looked reasonable on paper or even won on the training split, but didn't survive
validation-split confirmation or a mandatory higher-bar gate. Full reasoning for each is in
`wiki/03_design_log.md`'s 2026-08-30 entries.

**Reproducibility**: a real hash-seed nondeterminism bug (`catalog.py`'s `set` iteration order) was
found and fixed — the agent's behavior on the deterministic simulator is verified byte-identical
across repeated runs of the same config. A separate, much smaller (~0.6pp) source of numeric drift
was identified and accepted: regenerating the catalog embedding cache from scratch produces tiny
floating-point differences from a prior cache due to ordinary multi-threaded BLAS non-associativity —
stable once a given cache file is fixed, not a control-flow bug.

## Next workstream

**Phase 5 — submission packaging. 5.1, 5.2, 5.3, 5.6, and 5.7 are done.** `submission/` has been
rebuilt (gitignored, a build artifact) with the buying-track fix included —
**re-run `tools/build_submission.py` before actually submitting** if `src/copilot/` or
`docs/SUBMISSION_README.md` change again. **Codex review is conclusively unavailable this session**:
11 consecutive attempts failed today across 6 distinct commits (`2fe00dd`, `77829e1`, `d6ce4ac`,
`4d8e52e`, `8668665`, `abcf9bb`), in both sequential and parallel invocation, spanning diff sizes
1-20 files — ruling out diff size and parallelism as the cause. All 6 commits accepted as
manually-reviewed-only. Don't attempt codex review again this session unless the environment
changes.

**Phase 5.6's fix also improved intent_override as a side effect** (never-in-pool 20%→10%, since
those sessions share buying's turn-1 disclosure before the pivot). Post-fix diagnostic shows
buying's remaining gap shifted from mostly-recall to mostly-ranking (in-pool-but-not-top10 rose
23.8%→30.0% even as never-in-pool nearly halved) — see `wiki/08_evaluation_log.md`.

**A large batch of research-backed next ideas is logged in `wiki/06_future_ideas.md`, awaiting a
decision, not yet implemented**: using the evaluator's own unused `user_profile` field (free,
per-session signal ignored since Phase 0), BM25F field weighting, RRF per-source weight tuning,
cross-encoder ensembling (directly relevant given the ranking-not-recall finding above), offline
doc2query-T5 document expansion, and (lower priority / deferred) SPLADE and ColBERT-style
late-interaction retrieval. None of these are scored-behavior changes yet — all require proper
train/validation ablation before shipping, per this project's standing discipline.

**5.4 and 5.5 now have working drafts, not just a plan**:
- `docs/DEMO_VIDEO_SCRIPT.md` — a full recordable script (terminal-recording format, ~4-6 min),
  proposing a default for SQ4's open format question, with a specific, already-verified session
  (`public_0005`, hits turn 3 rank 1) picked from `results.json`'s own recorded sessions rather than
  cherry-picked by re-running. `tools/trace_session.py` (new, tested) runs one real public-set
  session end-to-end and prints a readable per-turn trace for the recording — reuses the organizer's
  own `initial_message`/`customer_reply` simulation functions directly, so the traced behavior is
  identical to a real scored run. **Self-caught while first testing it**: constructing `Agent` from
  the repo root's cwd (instead of matching `tools/run_eval.py`'s convention of running with
  `cwd=<participant repo>`) missed the real embedding cache entirely and silently launched a
  ~14.5-minute full-catalog re-encode — fixed with an explicit `os.chdir`, re-verified fast
  (cache-hit) after the fix.
- `docs/DEVPOST_WRITEUP.md` — a full draft covering every standard Devpost section, built from this
  project's own real numbers and honest ablation history (including the slate-hedging reversal and
  the codex-review recovery episode as genuine technical narrative, not just a footnote). A few
  fields are deliberately left as placeholders — repo/video URLs (don't exist yet) and confirmation
  of SQ3 (team size, currently states "solo" per the existing README) and SQ5 (workshop notes this
  repo has no visibility into) — everything else is ready to paste into Devpost's form as-is.

**Remaining before actual submission**: record the video per the script, fill in
`docs/DEVPOST_WRITEUP.md`'s bracketed placeholders once the repo/video are public, and get the
user's confirmation on SQ3/SQ5 (see `implementation/09_SUPERVISOR_QUESTIONS.md`).

**If picking up codex review again**: always pass `-c windows.sandbox="unelevated"` (fixes a hard
crash vs. the default), but ALSO always check the session transcript directly if the `.raw.txt`
looks short/incomplete — see `CLAUDE.md`'s protocol note and `tools/extract_review.py`. Do not
conclude a review "found nothing" from a short raw.txt alone. **New, distinct finding (2026-08-30)**:
a review can also genuinely fail to complete — not a redirect issue, the transcript itself has no
`ExitedReviewMode` event. Seen 3 times today across two unrelated commits, one 20 files and one 8
files, so it's not a diff-size problem — a current environment-level reliability issue with the
review synthesis step. Don't retry more than once; accept manual-review-only past that (both
`2fe00dd` and `77829e1` are on that basis now).

## Blockers

- **Codex automated review's redirected-output capture is unreliable, but this is now a documented,
  worked-around process issue, not a coverage gap.** Root cause of the original hard crashes:
  `codex doctor` showed Windows `sandbox backend: elevated`, needing `CreateProcessAsUserW`, which
  failed with "Access is denied" — fixed via a `Bash(codex exec review:*)` permission rule plus
  `-c windows.sandbox="unelevated"`. Separately, and more importantly: a review's final verdict can
  render through a channel that plain file redirection doesn't reliably capture, making a fully
  *completed* review look like a failure in the saved `.raw.txt`. **This was not caught until several
  hours after the fact** — 6 reviews across this session were wrongly logged as failed and their
  findings sat unread. All were recovered from `~/.codex/sessions/**/*<session-id>*.jsonl` (search
  for `"type":"ExitedReviewMode"`) and fully triaged. Going forward: never conclude a review "found
  nothing" from a short raw.txt — always check the transcript first.

## Recent activity

- 2026-08-26 to 2026-08-29 — Project scaffolding, research, architecture corpus, two-tier codex
  review protocol. Phase 0 shipped (TechnicalScore 0.328, 3.1x baseline).
- 2026-08-29 — Phase 1 shipped (0.4087, +24.5%).
- 2026-08-30 — Phase 2 shipped (0.4111), then corrected to 0.4093 after a reproducibility bug fix
  reversed one ablation's verdict. Phase 3 closed out (3.1 robust, 3.2 confirmed impossible).
  Phase 3.5/4 built and ablated 5 new mechanisms (LLM booster, slate hedging, query nudge,
  rerank-depth widening, weighted RRF, Phase 4 lookahead). Phase 5.1-5.3 packaged the submission.
  **Then**: discovered codex reviews were silently succeeding without reaching redirected output;
  recovered and triaged 6 reviews / 9 findings, including 2 submission-breaking P1 bugs and a
  reversal of the slate hedging decision. **Final corrected guaranteed-path exit: TechnicalScore
  0.406428** (optional ceiling with a key: 0.429943).

## Open questions / decisions needed from the user

- `implementation/09_SUPERVISOR_QUESTIONS.md` SQ3-SQ5 (team/demo/workshop notes) — needed before
  Phase 5's writeup is finalized.
