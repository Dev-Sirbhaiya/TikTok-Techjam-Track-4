# Devpost Written Submission — Draft (Phase 5.5)

**Status: draft, ready for final polish.** Content below is accurate as of the latest evaluator run
(`status.md`). Fill in the bracketed items (`[repo URL]`, `[video URL]`, `[SQ3/SQ5 notes]`) before
publishing — those are genuinely outside this repo's own knowledge; see the note at the bottom.
Cross-checked against `implementation/02_TECHNICAL_PRD.md`'s deliverable checklist: this covers
item 1 (Devpost description) fully; items 2-4 live in the repo README / demo video /
`docs/SUBMISSION_README.md` respectively and are linked from here, not duplicated.

---

## Project name

Shopping Copilot — Conversational Search for TikTok TechJam 2026, Track 4

## Elevator pitch (one line)

A text-only conversational agent that finds the right product from a 50,000-item Amazon catalog in
as few turns as possible — hybrid retrieval, calibrated clarification, and an honestly-documented
ablation trail, with zero required LLM calls.

## Inspiration

Track 4's brief asks for something narrower and harder than a chatbot wrapper around a search box:
an agent that has to *route* intent (a shopper stating a hard constraint upfront behaves
differently from one still browsing), *manage a real dialog state* across an abrupt change of mind,
and *know when it has enough information to commit* rather than always asking one more question —
all under a hard 10-turn cap where an unnecessary clarification directly costs score. That's a
genuine information-seeking problem, not a search-relevance demo, and it's what shaped every
architectural decision below.

## What it does

Every turn, the agent:
1. Extracts slot updates from the shopper's free-text message (category, material, color, size,
   style, brand, budget, feature, use case).
2. Routes Buying-vs-Browsing intent and updates a persistent dialog state — accumulating slots
   normally, but detecting and correctly handling an abrupt intent override (the shopper changing
   their mind mid-session) rather than just appending contradictory constraints.
3. Retrieves candidates from three fused signals — BM25 keyword search, dense embedding similarity
   (`bge-small-en-v1.5`), and metadata filtering — combined with Reciprocal Rank Fusion.
4. Reranks the shortlist with a cross-encoder (`ms-marco-MiniLM-L-6-v2`).
5. Decides whether to ask a clarifying question or commit to recommendations, based on a calibrated
   entropy measure over the current score distribution — the over-generality gate that keeps the
   agent from either dumping an undifferentiated pool of results or asking needless questions on an
   already-converged pool.

No LLM call is required anywhere in this path — the always-scored path runs entirely on local,
bundled, open-weight models. An optional Claude Haiku listwise-reranking pass activates only when a
local API key is present (never assumed for official grading, since the organizer provides none).

## How we built it

`[Python / libraries — cross-reference implementation/02_TECHNICAL_PRD.md's tooling list and fill
in the exact final stack: sentence-transformers, numpy, hand-rolled BM25, the organizer's evaluator
harness. Datasets: Amazon Reviews 2023, Clothing_Shoes_and_Jewelry category, organizer-frozen
50,000-item catalog kit.]`

Development ran phase-by-phase against the organizer's own local evaluator (200 labeled public dev
sessions), with every non-trivial change validated on a held-out split before being kept — see
"Challenges" below for why that discipline mattered more than it might sound.

## Accomplishments we're proud of

- **TechnicalScore 0.406** on the full 200-session public dev set (`Hit Rate@10 = 0.485`,
  `MRR = 0.278`, `MTTC = 6.98`), against the organizer's unmodified baseline of **0.107** — roughly
  a **3.8x** improvement, with zero required LLM calls in the scored path.
- A named, logged adaptive orchestrator (`orchestration_decisions` in the per-turn rationale log) —
  every retrieval-breadth, rerank-depth, and turn-policy decision is explainable after the fact, not
  a black box.
- A real train/validation split discipline held to throughout, including reversing our own already-
  shipped decision (see Challenges) rather than keeping a change that only won on the split we'd
  tuned it against.

## Challenges we ran into

The honest accounting matters more here than a highlight reel:

- **Buying and Intent-Override scenarios lag Browsing/Boundary in hit rate.** Several targeted
  fixes were tried — widening the reranked candidate pool, reweighting the metadata fusion signal,
  a query-embedding nudge toward accumulated preference, portfolio-style "slate hedging" for
  high-uncertainty commits — every one honestly ablated on two independent data splits. Most
  regressed or failed to replicate on held-out data outright. One, slate hedging, initially looked
  like a real win on the training split and shipped — then an adversarial code review caught that
  its held-out validation result was a genuine wash (identical Hit Rate@10 with or without it), not
  a confirmed improvement, and that the reasoning used to justify shipping anyway ("the validation
  sample is probably just underpowered") was exactly the kind of post-hoc rationalization the
  project's own pre-registered evaluation protocol exists to rule out. It was reversed. That gap in
  the Buying track is real and unresolved — the design log documents exactly what was tried and why
  each attempt didn't hold up, which is itself useful signal that the bottleneck likely lives in
  retrieval precision under hard filtering, not clarification-turn policy.
- **A code-review process gap of our own making.** A batch of automated code reviews appeared to
  fail outright (short, incomplete-looking output) and were logged as an environment limitation for
  several hours. It turned out several of them had actually completed successfully — the verdict
  was rendering through a channel that simple output redirection didn't reliably capture. Once
  found, all of them were recovered directly from the tool's session transcripts and triaged
  properly; two were genuine bugs that would very likely have shipped unnoticed to official scoring
  (a bundled asset path that resolved against the wrong working directory, and a build script that
  could silently produce an incomplete submission). The fix — always check the underlying transcript
  before trusting a short, inconclusive-looking report — is now a documented part of the team's own
  process going forward.

## What we learned

Ablation discipline only works if it's applied to *itself*, not just to the feature being tested —
the slate-hedging reversal above happened specifically because a validation-split "wash" was almost
rationalized away as measurement noise instead of a real answer. The most valuable technical
artifact this project produced may not be the retrieval pipeline itself but the habit of writing
down, and honoring, a pre-registered accept/reject rule before looking at the result.

## What's next

- A genuine offline optimization loop over a wider hyperparameter space (only a targeted sweep was
  run here).
- A deeper investigation into *why* the retrieval pipeline specifically underperforms on
  hard-filtered (Buying-track) pools, rather than only tuning around the symptom.
- The one-step "world-model-lite" lookahead question selector was built and correctly declined
  (didn't clear a higher bar than the existing entropy heuristic); a two-step extension was never
  attempted given that result, but remains a plausible next experiment if the underlying entropy
  signal itself improves.

## Built with

`[final language/library/model list — pull directly from docs/SUBMISSION_README.md's "Models,
cost, and offline behavior" table plus requirements.txt, so this list never drifts out of sync with
what's actually shipped]`

## Links

- GitHub repo: `[repo URL]`
- Demo video (YouTube, public): `[video URL — see docs/DEMO_VIDEO_SCRIPT.md]`
- Full development history (every ablation, decision, and why): linked from the repo's `wiki/` and
  `implementation/` directories, kept as a living record throughout rather than reconstructed after
  the fact.

---

## What still needs a human before this is publish-ready

- **SQ3** (team size / division of labor): `docs/SUBMISSION_README.md` currently states "Single
  contributor" — confirm this is still accurate before the "Contribution breakdown" section goes to
  Devpost (Devpost's own submission form asks for this separately from the written description too).
- **SQ5** (workshop notes / organizer clarifications from the 2026-08-28 Track 4 session): if there
  were any verbal clarifications not captured in `wiki/00_problem_statement.md`, they should be
  cross-checked against this writeup's claims (especially the TechnicalScore formula and scenario
  mix) before publishing — nothing in this repo's own sources suggests a contradiction, but this
  repo has no visibility into the workshop itself.
- Fill in the bracketed `[...]` placeholders above once the repo is public and the video is
  uploaded.
