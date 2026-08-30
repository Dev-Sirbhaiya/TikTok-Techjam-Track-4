# Demo Video Script — Draft (Phase 5.4)

**Status: draft, proposed default per `implementation/09_SUPERVISOR_QUESTIONS.md` SQ4.** SQ4 left
the exact format open ("live terminal recording... or something more produced"). This script
assumes the terminal-recording option — it's the lower-risk, faster-to-produce choice and the spec
explicitly accepts an API-usage walkthrough for a no-UI backend/NLP submission. Swap the recording
mechanics below if a more produced format is wanted instead; the narration content doesn't change.

**Target length**: 4–6 minutes. No editing required beyond a straight screen capture + voiceover —
optional light cuts between sections if the recording runs long.

## Recording setup

- Terminal, large font (readable at 1080p), light or dark theme — whichever has been used
  throughout development, for consistency with anything else shown.
- Have `.venv` already activated and `cwd` at the repo root before recording starts (don't waste
  video time on `pip install`).
- Pre-warm the catalog/model load once *before* recording (the ~10-15s one-time load at `Agent`
  construction is real but not interesting to watch cold — mention it verbally instead, see below).

## Section 1 — Problem framing (30–45s, talking head or slide, or voiceover over the repo's README)

> "This is a conversational shopping copilot for TikTok TechJam 2026's Track 4 — a text-only agent
> that has to find the right product from a frozen 50,000-item Amazon catalog in as few turns as
> possible, entirely in-memory, with no UI, and a hard 10-turn cap per session. It's scored on
> retrieval coverage (Hit Rate@10), ranking precision (MRR), and turn efficiency (MTTC)."

Show `wiki/00_problem_statement.md`'s TechnicalScore formula on screen for 3-4 seconds.

## Section 2 — Architecture, one pass (45–60s)

Show the pipeline diagram from `wiki/01_architecture.md` (`Shape` section) on screen while narrating:

> "Every turn: extract slot updates from the user's message, route Buying-versus-Browsing intent,
> retrieve candidates from three fused signals — BM25 keyword search, dense embedding similarity,
> and metadata filtering — rerank the shortlist with a cross-encoder, then decide whether to ask a
> clarifying question or commit to a recommendation, based on how uncertain the score distribution
> still is. No LLM call is required anywhere in this path — the required, always-scored path runs
> entirely on local, bundled, open-weight models."

## Section 3 — Live multi-turn session trace (2–3 minutes, the core of the video)

Run one real session end-to-end against the actual evaluator/agent, showing the request and
response JSON for each turn in the terminal. Pick a **Buying** scenario for the walkthrough (the
scenario where the agent's behavior — locking a hard constraint, converging fast — is most legible
on screen) with a real, non-cherry-picked session ID from `data/public_set.jsonl`.

Suggested command (adjust to whatever `tools/run_eval.py` or a small ad-hoc script currently
exposes for single-session tracing — a `--session-id` / `--verbose` single-session mode is worth
adding to `tools/run_eval.py` before recording if it doesn't already print a clean per-turn trace):

```bash
python -m tools.run_eval --session-id <buying-session-id> --verbose
```

Narrate over each turn as it prints:
- Turn 1: point out the opening message already discloses category + one hard constraint; show the
  agent's intent routing decision and initial retrieval pool size in the logged rationale.
- A middle turn where the agent asks a clarifying question: point out *why* — the logged entropy
  value crossing the calibrated threshold — not just that it asked something.
- The hit turn: point out the rank of the target `parent_asin` in the returned top-10 and which
  turn it landed on, and connect that back to MRR/MTTC directly.

## Section 4 — Honest results + what was tried and cut (60–90s)

> "On the 200-session public dev set, this scores 0.406 TechnicalScore against the organizer's
> unmodified baseline of 0.107 — about 3.8x. With a local Claude API key present, an optional LLM
> reranking pass pushes that to 0.430, but that's not the number we're reporting as the expected
> competition score, since the organizer doesn't provide hosted credentials for official grading."

Show the score progression table from `status.md` on screen for a few seconds.

> "A good chunk of development time went into things that didn't make the cut — a query-embedding
> nudge toward accumulated preferences, widening the reranked candidate pool, reweighting the
> metadata fusion signal, portfolio-style slate hedging, and a one-step lookahead question selector.
> Every one of these was ablated on two independent data splits before a decision was made, and one
> — slate hedging — actually shipped once, then got reversed after a code review caught that its
> held-out validation result was a wash, not a real win. That's disclosed honestly in the writeup,
> not hidden — the discipline of not shipping a change that only wins on the split you tuned it on
> is itself part of the technical approach, not just a footnote."

## Section 5 — Close (15–20s)

> "Full development history, every ablation, every decision and why, is in the repo's `wiki/` and
> `implementation/` directories — this was kept as a living record throughout, not reconstructed
> after the fact. Thanks for watching."

Show `wiki/INDEX.md` or the repo's file tree for the last few seconds.

## Open items before recording

- **Confirm** the terminal-recording format above is acceptable (vs. a more produced alternative) —
  proceeding on this default per auto-mode guidance; flag if a different format is wanted.
- **Pick the actual session ID** to trace live — should be chosen once, in advance, not live on
  camera (avoids an unlucky miss scenario on the recording).
- If `tools/run_eval.py` doesn't yet have a clean single-session `--verbose` trace mode, add one
  before recording — this is a small, low-risk addition, not a scored-path change.
- Upload target: YouTube, **public** (required for Devpost linking).
