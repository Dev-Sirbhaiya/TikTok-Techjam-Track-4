# Master Dos & Don'ts — Synthesized from Research 01-09 + Verified Ground Truth

Compiled 2026-08-26 from all 9 research files plus direct source-code verification of the
participant repo (`external/techjam-conversational-search/`, see `wiki/09_simulator_mechanics.md`).
This is pre-architecture synthesis for ideation — nothing here is a committed design decision until
it lands in `wiki/01_architecture.md` with a matching `wiki/02_design_decisions.md` entry.

**How to read this:** each pillar section gives the converged recommendation across all research,
then explicit Dos/Don'ts. Where research disagreed or flagged genuine ambiguity, that's called out
rather than papered over. Ground-truth facts (verified against actual code) are marked **[GROUND
TRUTH]**; everything else is research-derived judgment, marked **[RESEARCH]**.

---

## 0. Build-order priority (do this first) — from the actual scoring formula

**[GROUND TRUTH]** `TechnicalScore = 0.50×HitRate@10 + 0.30×MRR + 0.20×Efficiency`,
`Efficiency = clip((11-MTTC)/10, 0, 1)`. MRR is mathematically bounded above by HitRate@10, and a
failed session scores exactly 0 on Efficiency too (miss = turn 11). **This makes retrieval coverage
the highest-leverage, must-do-first investment; ranking precision second; turn-efficiency last, and
only as a gate, never as a goal in itself.**

### Dos
- Do build and validate retrieval (Hit Rate@10) against the 200 public dev sessions before touching
  reranking or clarification policy — it's the largest weight and gates the other two.
- Do treat a clarifying question as something that must pay for itself in expected hit-rate/MRR
  gain, never as a way to "buy efficiency" — efficiency is zero on any failed session regardless of
  how few turns were spent trying.
- Do report all three raw sub-metrics when iterating locally, not just the blended score.

### Don'ts
- Don't invest early effort in minimizing turns before coverage/precision are solid.
- Don't assume the private 800-session set uses identical weights — the public formula is a strong
  working assumption, not a guarantee; don't over-fit by sacrificing HR@10 to chase Efficiency.

---

## 1. Ground truth about the eval harness itself (read `wiki/09_simulator_mechanics.md` in full)

**[GROUND TRUTH]** These are facts, not research inferences — verified directly against
`evaluator/local_evaluator.py`, `starter/agent.py`, and the docs.

### Dos
- Do edit `starter/agent.py`'s `Agent` class in place for local dev — the evaluator hardcodes
  `from starter.agent import Agent` with no override flag. Keep real logic in a separate module and
  make `starter/agent.py` a thin re-export, since the final submission format (`docs/submission_rules.md`)
  is a different standalone layout (`agent.py` + `requirements.txt` + `README.md` + `src/`).
- Do exploit that **category is disclosed in the opening message in 100% of sessions**, every
  scenario — free signal from turn 1 regardless of Buying/Browsing routing.
- Do build clarification-attribute selection against the *actual* `classify_constraint()` keyword
  taxonomy (budget → material → color → size → style → use_case → else feature) since the simulator
  only reveals info when `ask_attribute` matches this exact heuristic.
- Do handle Intent Override explicitly: a hit before the scripted override turn (3 or 4) never
  counts, and the override fires unconditionally regardless of agent behavior.
- Do handle Boundary scenarios: the first clarification question of any kind gets a one-time
  non-answer; don't re-ask the same dimension after that.
- Do rely on the catalog's real `price` field for budget filtering rather than expecting it via
  clarification — budget/brand are structurally weak clarification channels (see `wiki/09`).

### Don'ts
- Don't modify `evaluator/local_evaluator.py` or public labels — explicitly disallowed.
- Don't assume `ask_attribute` free text or synonyms outside the 10-value enum do anything —
  the simulator keys strictly off the enum field, not the natural-language `message`.
- Don't assume generous CPU/memory/timeout headroom at final judging — no numeric limits are
  published; build defensively (bounded candidate sizes, no unbounded loops).

---

## 2. Pillar I — Intent Routing & Hybrid Retrieval Pipeline

**[RESEARCH, converged across files 01 & 02]** Route via a cheap hybrid (catalog-derived gazetteers
+ lightweight embedding similarity), reserving any LLM call for genuinely ambiguous turns. Retrieval
itself should be BM25 (`bm25s` or the starter's SQLite FTS5) + a small sentence-transformer
(BGE-small-en-v1.5 or MiniLM) + dict/inverted-index hard filters, fused via Reciprocal Rank Fusion.
FAISS run locally is fine (it's a library, not a hosted DB) but unnecessary at 50K items — brute-force
NumPy cosine similarity is already sub-20ms.

### Dos
- Do derive brand/size/color/category/price vocabularies from the frozen catalog at load time —
  free, grounded, zero-training.
- Do treat hard constraints (Buying track) as pre-filters that exclude, and soft preferences as
  boosts that reorder without excluding.
- Do apply hard filters *before* similarity scoring (filter-then-rank), never as a post-hoc filter
  on an already-computed top-k.
- Do re-evaluate intent lightly every turn from accumulated state, not freeze it at session start.
- Do cap the LLM-reranker-facing candidate set at roughly 10-75 items (see Pillar I ranking below)
  — this, not the ANN library choice, is the dominant lever on latency/MTTC.
- Do use MMR or category-balanced resampling for the Browsing track's diversity requirement.

### Don'ts
- Don't default to an LLM call on every turn for intent classification if a gazetteer/embedding
  signal already resolves it confidently.
- Don't promote every mentioned attribute to a hard filter automatically — over-strict filtering
  causes zero-result dead ends that tank Hit Rate.
- Don't reach for a hosted/managed vector DB (Pinecone, Milvus, Zilliz Cloud) — explicitly
  disallowed, and unnecessary at 50K items regardless.
- Don't fine-tune the embedding model on the catalog — compensate for generic-embedder weakness on
  short/noisy shopper queries with BM25 + query-side prompt normalization instead.
- Don't combine raw BM25 and cosine scores via naive averaging without normalization — use RRF.

---

## 3. Pillar I (cont.) — LLM Semantic Ranking

**[RESEARCH, file 03]** Default to a cross-encoder (e.g. `ms-marco-MiniLM-L-6-v2`, or FlashRank) as
the *guaranteed*, no-API, in-memory reranking stage — 2025-2026 benchmarks show a calibrated
cross-encoder can match or beat general LLM rerankers on NDCG at a fraction of the latency. Layer an
optional single-pass listwise LLM rerank (≤10-15 candidates, no sliding window) on top only when an
API/local model is available. This directly targets the org's explicit "no guaranteed paid LLM API"
reality.

### Dos
- Do keep the reranker's input to a small shortlist (≤10-50, ideally ≤15 if an LLM is in the loop).
- Do treat a strong cross-encoder as a first-class deliverable, not a fallback.
- Do use opaque short IDs (`[1]`,`[2]`...) in any LLM ranking prompt, request an ordered-ID-list
  output, never re-emit full titles.
- Do add a confidence-based early exit: skip reranking entirely when the fused retrieval score
  margin is already decisive.
- Do fuse retrieval score + reranker rank + business signals (price-fit, rating) via RRF or a
  hand-tuned weighted blend — this is explicitly permitted "local scoring-logic tuning."

### Don'ts
- Don't rerank the full retrieval pool with an LLM — cost/latency scale roughly linearly with list
  size for little relevance gain past ~100 items.
- Don't use pointwise LLM scoring (one call per candidate) as the primary mechanism — worst
  latency/cost/accuracy combination among LLM paradigms per benchmarks.
- Don't make "LLM Semantic Ranking" only satisfiable when a paid API key is present — build the
  cross-encoder path as the real default, not a degraded fallback.
- Don't feed the full raw dialogue transcript into the reranker prompt every turn if it can be
  reduced to structured slots — unnecessary prompt growth against the turn budget.

---

## 4. Pillar II — Dialogue State Tracking (Accumulation vs. Override)

**[RESEARCH, file 04, validated against GROUND TRUTH mechanics in `wiki/09`]** Use one
schema-constrained LLM extraction call per turn (function-calling/JSON-schema style, FnCTOD/ParsingDST
pattern) emitting explicit per-slot operations (ADD/KEEP/UPDATE/CLEAR — the SOM-DST taxonomy), layered
with deterministic rules for the override case — never trust the LLM alone to both detect and apply a
pivot, since literature shows models can "leak" old state even after correctly acknowledging a shift.

### Dos
- Do treat a **category/domain change as the dominant, highest-precision override signal**,
  detected by a deterministic rule (the catalog's category taxonomy is small and known), not an LLM
  judgment call.
- Do use simple negation/reset keyword cues ("actually", "never mind", "instead") as a cheap
  secondary override trigger.
- Do keep decay/TTL logic (slot confidence fading after ~3-4 unreinforced turns) separate from
  override/clear logic — decay demotes ranking weight, override hard-clears; conflating them
  reintroduces the exact ambiguity the design is meant to eliminate.
- Do pass the full turn history to the extraction step each turn — at ≤10 turns this is well within
  the regime where LLMs stay reliable; no compression engineering needed here.
- Do prioritize preventing wasted/incorrect turns (bad merge or bad clear) over maximizing slot
  extraction recall, since MTTC penalizes turns spent recovering from a bad state update.

### Don'ts
- Don't implement or adapt a trained neural DST model (SOM-DST, TRADE) — needs labeled training
  data, violates the no-FM-training constraint; reuse the *operation taxonomy*, not the weights.
- Don't add confirmation turns ("just to confirm, you want...") — text input is pre-cleaned, these
  are pure waste against MTTC.
- Don't build a continuous/tunable decay function — sessions are too short (≤10 turns) to matter;
  a simple confirmed/inferred tag + small turn-count TTL is sufficient.
- Don't run a multi-stage pipeline (separate shift-detection call, separate extraction call) purely
  for architectural cleanliness — each added LLM call is added latency the turn budget can't absorb.

---

## 5. Pillar II (cont.) — Proactive Clarification / Over-Generality

**[RESEARCH, file 05]** Compute normalized Shannon entropy over the top-K retrieval/rerank scores
immediately after retrieval, before any expensive ranking step, as the Over-Generality trigger
(formula and calibration from arXiv:2509.06185 — direct prior art for this exact mechanism). When
triggered, pick the facet with highest entropy of its value distribution *among the live candidate
pool* (CIKM'13 Probabilistic Entropy method) and ask a structured, closed-choice question using real
catalog values.

### Dos
- Do compute the trigger from statistics already available post-retrieval (score entropy, pool
  size, top-1/top-2 gap) — no extra model call needed.
- Do phrase clarifications as closed, concrete, catalog-grounded choices (2-4 real values), not
  open-ended free text.
- Do enforce hard guardrails around the statistical trigger: a pool-size/entropy floor (skip
  clarifying if already confident), a turn-index ceiling (no clarification after ~turn 7-8 of 10,
  since a late clarification with no runway to act on it is pure waste), and a diminishing-returns
  guard (don't ask a second question on the same dimension if the first didn't shrink the pool).
- Do treat every clarification as spending exactly 1 of 10 turns against an expected-turns-saved
  calculation, not a free action.

### Don'ts
- Don't ask because the pool is "large" in absolute terms — use entropy/score shape; a large pool
  with one dominant top score is still confidently answerable.
- Don't default to open-ended free-text clarification — structured choices converge faster and
  are cheaper to parse into the closed `ask_attribute` enum the actual evaluator expects.
- Don't clarify repeatedly on a low-information dimension that didn't shrink the pool last time.
- Don't rely on any fine-tuned clarification-generation model — template generation over live
  facet values is the training-free substitute.

---

## 6. Pillar III — Context Distillation & Personalization

**[RESEARCH, file 06 — includes an important interpretive flag]** "Long-term user profile" almost
certainly means, given the single-isolated-session eval constraint, a **within-session, slower-decaying
accumulation layer**, distinct from a fast-moving short-term/recent-turn layer — not a literal
cross-session persistent store (which the eval setup can't exercise or reward). Build two in-memory,
non-parametric EMA-updated vectors (positive/negative affinity) plus the decayed slot dict, applied as
an **additive ranking-time boost**, not just a retrieval filter.

### Dos
- Do treat "long-term" as the whole-session-history component and "short-term" as the recent-turn
  component, both scoped to the single session, both purely in-memory.
- Do use weight-free online updates (EMA, decayed attention) — cheap, matches the 10-turn budget,
  and matches what strong session-based-recommendation baselines already show is sufficient.
- Do let personalization act as a ranking-time additive boost on top of base relevance, not only a
  retrieval filter — this is what actually moves MRR/Hit@K turn-over-turn.
- Do track negative/rejected signal separately from positive signal.
- Do keep a compact natural-language "memory note" (not the full raw transcript) as what's re-fed
  into any LLM prompt each turn — write-before-compaction, not re-summarize-from-scratch.
- Do keep a `ProfileStore` interface seam (even if just a dict keyed by session id in v1) as a
  cheap hedge in case the eval harness turns out to group sessions differently than assumed.

### Don'ts
- Don't build a persistent, externally-stored, cross-session/cross-user profile database — it
  contradicts "in-memory only" / "single isolated session" and can't be exercised by the eval.
- Don't confuse this with Snell et al.'s "context distillation" (fine-tuning a model on a prompt) —
  that's a training-time technique, explicitly out of scope and irrelevant at this scale.
- Don't adopt a literal trained sequential-rec model (GRU4Rec/SASRec proper) — use them only as a
  conceptual template for the update rule.
- Don't let the profile only gate retrieval and stop there — without a ranking-time effect too, the
  "progressively better-targeted" behavior won't show up in the scored metrics.

---

## 7. Pillar III (cont.) — Adaptive Runtime Orchestration

**[RESEARCH, file 07]** Translate "Dynamic Context Programming / runtime re-orchestration" into a
**small explicit state machine (5-8 states) with rule-based, signal-gated transitions**, not a
free-form "LLM decides everything" controller. This sits deliberately on the predictable end of the
predictability-adaptability frontier — appropriate for a 72-hour build that needs to be regression-
tested against Hit Rate@K/MRR/MTTC.

### Dos
- Do name and enumerate every adaptive decision point explicitly (aim for 3-5, not 10+): e.g.
  retrieval blend weighting, rerank-skip-on-high-confidence, clarification aggressiveness scaled by
  turns remaining.
- Do gate every adaptive branch on cheap, already-computed signals (candidate-pool size, score
  margin, slot-fill confidence, turns-remaining) rather than an extra LLM judgment call.
- Do bias every adaptive mechanism toward *saving* turns/latency, since MTTC and the 10-turn cap
  are hard constraints.
- Do log the routing decision and its triggering signal at each turn — makes the system's
  adaptivity demonstrable in the demo and debuggable during tuning.

### Don'ts
- Don't build a fully autonomous plan-and-replan or orchestrator-workers-style controller — added
  unpredictability costs more eval-tuning time than it could plausibly gain in a hackathon window.
- Don't try to reproduce Self-RAG/Adaptive-RAG's trained classifiers — both require fine-tuning;
  use their *design idea* (skip/adjust based on a confidence signal), not their implementation.
- Don't let the state machine grow past a handful of states "just in case" — each additional
  branch multiplies paths that need separate eval validation within 72 hours.
- Don't make the adaptive logic implicit inside one giant "use your judgment" LLM prompt — least
  controllable, least testable, and undercuts the ability to demonstrate the capability to judges.

---

## 8. Cross-cutting Dos & Don'ts (apply everywhere)

### Dos
- Do keep everything in-process/in-memory: stdlib `sqlite3` FTS5 or `bm25s`, small in-RAM NumPy
  vector arrays, dict-based inverted indexes — no external service of any kind beyond an optional
  LLM API call.
- Do disclose model choice, approximate cost, token usage, latency, and any offline fallback, from
  turn 1 — required by the submission rules, easier to build in than bolt on later.
- Do validate every design choice against the 200 public dev sessions, watching for overfitting to
  the exact deterministic simulator heuristics (the private 800-session set uses the same mechanics
  but different underlying products).

### Don'ts
- Don't use a hosted/industrial vector DB cluster, train or fine-tune any foundation model, process
  images/multi-modal input, or build a UI — all explicitly out of scope.
- Don't let any session exceed 10 turns under any code path — structurally prevent it, don't just
  "usually" respect it.
- Don't mutate the catalog or reference identifiers outside it.
- Don't commit API keys/secrets, or make official scoring depend on an undeclared external service.
