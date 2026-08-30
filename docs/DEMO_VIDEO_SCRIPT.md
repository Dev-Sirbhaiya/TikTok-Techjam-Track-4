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

Run one real session end-to-end against the actual agent using `tools/trace_session.py` (built for
this recording — see below), showing the customer message and agent response for each turn in the
terminal. Use **`--sample-id public_0005`**: a real Buying-scenario session from
`data/public_set.jsonl`, verified to hit on turn 3 at rank 1 (`external/techjam-conversational-
search/results.json`'s own recorded session list, not cherry-picked by re-running until something
looked good) — clean enough to narrate turn-by-turn without the recording running long on a miss.

```bash
python tools/trace_session.py --sample-id public_0005
```

First run after a fresh checkout hits the network once for the two bundled models (`Warning: ...
unauthenticated requests to the HF Hub` — harmless, just the local dev cache warming; the actual
submission bundles both models locally per `docs/SUBMISSION_README.md`, so this line never appears
in the scored path). Silence that warning or trim it in editing if it looks noisy on screen.

Narrate over each turn as it prints (matches the actual `public_0005` trace):
- Turn 1: the opening message already discloses category ("Outdoor & Work Snow & Cold Weather")
  and one hard constraint ("leather") — point out this is the Buying-scenario's defining trait, and
  that the agent asks about color next rather than committing immediately, because the pool is
  still too broad.
- Turn 3: the customer's reply itself reveals a new, richer constraint (an actual product
  description snippet) in response to the agent's use_case question — point out this is the
  simulator's *reactive-only* disclosure model (`wiki/09_simulator_mechanics.md`): the agent has to
  ask the right thing to get this, it's never volunteered.
- The hit: target `B074G1JP8Z` lands at **rank 1** on **turn 3** — connect this directly to the
  scoring formula on screen (`reciprocal_rank = 1/rank`, `MTTC` counts turns like this one).

## Section 4 — Honest results + what was tried and cut (60–90s)

> "On the 200-session public dev set, this scores 0.471 TechnicalScore against the organizer's
> unmodified baseline of 0.107 — about 4.4x. An optional LLM reranking pass adds a bit more when a
> local Claude API key is present, but that's not the number we're reporting as the expected
> competition score, since the organizer doesn't provide hosted credentials for official grading."

Show the score progression table from `status.md` on screen for a few seconds.

> "A good chunk of development time went into things that didn't make the cut — a query-embedding
> nudge toward accumulated preferences, widening the reranked candidate pool, reweighting the
> metadata fusion signal, portfolio-style slate hedging, and a one-step lookahead question selector.
> Every one of these was ablated on two independent data splits before a decision was made, and one
> — slate hedging — actually shipped once, then got reversed after a code review caught that its
> held-out validation result was a wash, not a real win. What eventually worked was building a
> diagnostic instead of guessing another fix: a small tool that measured whether the hidden target
> even reached the retrieval pool at all. It found the Buying scenario's own hard filter wasn't
> actually filtering on the thing that defines a buying request — extending it to do so raised the
> overall score by 16%, the single biggest jump of the project. Every one of these attempts, failed
> and successful, is disclosed honestly in the writeup, not just the wins."

## Section 5 — Close (15–20s)

> "Full development history, every ablation, every decision and why, is in the repo's `wiki/` and
> `implementation/` directories — this was kept as a living record throughout, not reconstructed
> after the fact. Thanks for watching."

Show `wiki/INDEX.md` or the repo's file tree for the last few seconds.

## Open items before recording

- **Confirm** the terminal-recording format above is acceptable (vs. a more produced alternative) —
  proceeding on this default per auto-mode guidance; flag if a different format is wanted.
- Session ID is already chosen and verified (`public_0005`, hits turn 3 rank 1) — `tools/
  trace_session.py` is built, tested, and produces the exact trace narrated above.
- Upload target: YouTube, **public** (required for Devpost linking).
