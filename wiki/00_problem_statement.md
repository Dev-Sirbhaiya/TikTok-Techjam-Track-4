# 00 — Problem Statement (Canonical Digest)

**Source of truth (unedited originals):** `/Tiktok_Problem.md`, `/Amazon_Dataset_Description.md`,
`/Important_Links.md`, `/Tiktok_Mail.md`. This page is the condensed, load-bearing summary agents
should work from; if it ever disagrees with the originals, the originals win — fix this page.

## Event

TikTok TechJam 2026 — **Track 4: Shopping Copilot (E-Commerce AI Conversational Search &
Recommendations)**.

## Timeline

| Date | Event |
|---|---|
| 2026-08-27 12:00 | Problem statements released (public) |
| 2026-08-28 13:00–18:00 | Technical workshops (webinars); Track 4 session 16:00–16:45 |
| 2026-08-29 12:00 | **72-hour challenge window opens** |
| 2026-09-01 12:00 | **Submission deadline (Devpost)** |
| 2026-09-08 | Finalists announced |
| 2026-09-11 | Grand Final, TikTok Singapore |

We are pre-build (today: 2026-08-26). Everything in this repo right now is setup/scaffolding done
ahead of the 08-29 start so that build time is spent building, not orienting.

## The challenge

Architect a next-generation conversational shopping agent that goes beyond static keyword search —
deep intent understanding, runtime architectural agility, commercial efficiency — evaluated against
the frozen Amazon dataset kit.

### Pillar I — Core Architecture: Intent Routing & Hybrid Pipeline
- **Dual-track routing**: detect intent instantly → "Buying" (high-precision filter track, locks
  hard constraints) vs "Browsing" (diverse dense retrieval track, cross-category matching).
- **Pipeline base**: in-memory `Multi-Route Retrieval → LLM Semantic Ranking`, combining keyword,
  category, and vector similarity signals.

### Pillar II — Dialog Strategy: Multi-Turn Scenario Evolution
- **Dynamic state machine**: handle incremental slot accumulation *and* abrupt intent override
  (slot erasure/rewrite) gracefully.
- **Proactive guidance**: on over-generality (candidate pool overload), cut retrieval and emit a
  structured clarification prompt that converges the user, rather than dumping results.

### Pillar III — Self-Evolution: Dynamic Context Programming
- **Runtime adaptation**: personalized context distillation from dialog history — update
  short-term session state and long-term user profile continuously.
- **Adaptive orchestration**: re-orchestrate the workflow/strategy at runtime based on accumulated
  context (the agent should refine its own guidance logic as the session progresses).

### Pillar IV — Evaluation Matrix
Anchored on the final purchased record per session:
- **Coverage** — Hit Rate@K (retrieval-stage recall/boundary capability).
- **Precision** — MRR / Top-K Hit Rate (does ranking push the true item to the top).
- **Efficiency** — MTTC, Mean Turns To Conversion (fewer turns to the right product = higher score;
  unnecessary clarification is penalized).

## Hard constraints — never violate these

| Constraint | Detail |
|---|---|
| **Max turns** | 10 turns per session, hard limit. Exceeding it = forced termination **and zero score**. |
| **Catalog is read-only** | No structural mutation, no mock ASIN injection, ever. |
| **No heavy vector DB** | Must run **entirely in-memory** — no external industrial vector DB clusters. |
| **Text only** | No multi-modal processing — text catalog, structured metadata, text dialog only. |
| **No FM training** | No training or full-parameter fine-tuning of base foundation LLMs (light prompt/scoring tuning is fine). |
| **No UI** | Out of scope; evaluated purely via automated backend APIs / headless pipelines. |

## Allowed assumptions
- Input text is pre-cleaned (no typo/ASR-noise correction needed).
- Catalog, pricing, category tree are static for the duration.
- Each session is a single isolated user (no concurrency stress).

## Data & resources provided by organizer
- Frozen catalog: **50,000 products**, `Clothing_Shoes_and_Jewelry` category, Amazon Reviews 2023.
- 200 labeled **public** dev sessions (local iteration) + 800 private eval sessions (final scoring,
  disjoint users/targets from the public set).
- Weak BM25 starter agent (Python), deterministic local evaluator (Hit Rate@10, MRR, MTTC,
  combined TechnicalScore), published Agent interface + API contract, SHA256 checksum for the
  catalog.
- We do **not** need to pull the full upstream Amazon Reviews 2023 dataset — the organizer's frozen
  kit is authoritative. See [07_external_resources.md](07_external_resources.md) for exactly what
  was imported and from where.
- No hosted model access/API keys are provided by the organizer; a paid LLM is not required.

## Deliverables (submission requirements)
1. Written project description on Devpost (approach, tools, APIs, libraries, datasets used).
2. Public GitHub repo: structured/commented code, README (overview, setup, repro steps, limitations
   & what you'd improve, contribution breakdown).
3. Demo video on YouTube (public) linked from Devpost — walkthrough/API-usage video is acceptable
   since there's no UI.

## TechnicalScore formula (verified against `evaluator/local_evaluator.py`, not just the README)

```
Efficiency     = clip((11 - MTTC) / 10, 0, 1)
TechnicalScore = 0.50 * HitRate@10 + 0.30 * MRR + 0.20 * Efficiency
```

Coverage (retrieval) is weighted highest at 50%, precision (ranking) 30%, efficiency (turns) 20%.
Weak BM25 starter baseline: TechnicalScore ≈ 0.10671 (see `wiki/08_evaluation_log.md`). Given these
weights, retrieval recall is the single highest-leverage lever, then ranking precision, then
turn-efficiency — this should guide build-order priority (research agent 8's conclusion,
independently confirmed against the actual evaluator source, not just its docs).

## Judging weights
Technical Execution 35% · Innovation & Problem Insight 20% · Impact & Relevance 20% ·
Feasibility & Practicality 15% · Presentation & Communication 10% (final event only).

## Key links
- Participant repo: https://github.com/TechJam2026/techjam-conversational-search
- Participant kit release: https://github.com/TechJam2026/techjam-conversational-search/releases/tag/participant-kit
- Amazon Reviews 2023 (HF): https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
- Amazon Reviews 2023 (GitHub, loaders): https://github.com/hyp1231/AmazonReviews2023
- Amazon Reviews 2023 docs: https://amazon-reviews-2023.github.io/
