# 05 — Build Plan

Supersedes `/My Ideas/02_BUILD_PLAN.md` + `08_ADVANCED_PHASES.md`, merged into one numbered sequence
and corrected against ground truth. **Today is 2026-08-29 — the 72-hour build window is open (closes
2026-09-01 12:00).**

## How phase execution maps to `CLAUDE.md`'s enforcement loop

**Each numbered step below (e.g. `0.3`, `1.2`) is one "work phase" per `CLAUDE.md` §3.** Completing a
step triggers, automatically, without being asked again: (a) an immediate git commit, (b) a background
`codex exec review` kicked off without blocking further work, (c) a living-wiki update
(`wiki/03_design_log.md`, `wiki/04_agent_progress.md`, `wiki/05_completed_components.md`,
`wiki/08_evaluation_log.md` when the evaluator is run, `status.md`'s Next Workstream). Saying **"run
Phase 0"** means: execute 0.1 → 0.11 in order, each triggering that loop, stopping at the Phase 0 exit
criteria to report actual numbers before continuing (do not silently roll into Phase 1). Saying **"run
0.4"** means just that one step. No further instruction is needed for the review/commit/wiki loop to
happen — it is not optional and does not need to be re-requested per step.

## The one rule that governs every phase past Phase 1

> A technique being real, published, and well-cited is never sufficient justification for keeping it
> in this system. If a component doesn't measurably improve held-out results on our own dev sessions,
> it gets removed or demoted — never kept because a paper exists for it.

Re-run the evaluator after every addition past Phase 1 and log HitRate@10/MRR/MTTC/TechnicalScore to
`wiki/08_evaluation_log.md`. See `08_ABLATION_MATRIX.md` for the mandatory gates.

---

## Phase 0 — The floor (non-negotiable; nothing past this starts until it's done and evaluated)

**Goal: a complete, submittable system that clearly beats the baseline** (HitRate@10 0.125, MRR
0.068034, MTTC 9.81, TechnicalScore 0.10671 — `wiki/08_evaluation_log.md`), using the full hybrid
architecture from day one (per the user's own instruction: RRF, hybrid retrieval, keyword, and
metadata are Phase 0 items, not later refinements — a plain BM25-only system is *not* an acceptable
Phase 0 in this build, unlike a generic "minimum viable" framing).

### 0.1 — Repository scaffolding + catalog/session loading
- Create `src/copilot/` package skeleton (empty modules per `04_SYSTEM_DESIGN.md`'s layout).
- Load `catalog.jsonl` (50K products) and `data/public_set.jsonl` (200 sessions) into memory; build
  the gazetteer (brand/color/material/size vocabularies scanned from `details`/`categories`/`title`).
  **Remember**: `details` has zero keys common across items even within one leaf category (verified —
  `06_DECISION_LOG.md` resolved-Q7) — the gazetteer must scan values generically, not assume fields.
- Acceptance: catalog loads in <5s, gazetteer produces non-empty brand/color/material/size sets.

### 0.2 — BM25 + dense retrieval + RRF fusion (the hybrid retrieval floor)
- Implement `retrieval.py`: `bm25s` (or reuse starter's SQLite FTS5) sparse leg; `bge-small-en-v1.5`
  dense leg, catalog embedded once offline and cached; `reciprocal_rank_fusion()`.
- Implement the metadata/structured filter: dict-based inverted index over category/price-bucket/brand.
- Acceptance: given a query string, returns a fused top-60 candidate list with all three signals
  contributing (spot-check: a brand-name query should surface that brand near the top via the metadata
  filter even if BM25/dense alone wouldn't rank it first).

### 0.3 — Naive end-to-end wiring (control-group baseline)
- Wire retrieval directly into `starter/agent.py`'s re-exported `Agent` with a **fixed question
  order** (category → price → color → size) and no memory across turns — this is the internal control
  group, not the shipped system.
- Run the evaluator (`python -m evaluator.local_evaluator`). **Log this number in
  `wiki/08_evaluation_log.md` — it is the baseline every subsequent step is compared against**, distinct
  from the organizer's own BM25-only baseline.

### 0.4 — `DialogState` + slot accumulation across turns
- Implement `state.py` (`DialogState` dataclass) and `nlu.py`'s gazetteer/regex extraction path
  (no LLM dependency yet — that's optional and added in 0.5).
- Wire into `agent.py`: turn 2+ now reads accumulated slots instead of only the latest message.
- Test explicitly against one Intent Override sample and one Boundary sample from `public_set.jsonl`
  by hand-tracing expected behavior against `wiki/09_simulator_mechanics.md`'s documented mechanics.
- Acceptance: re-run evaluator; HitRate@10/MTTC should improve over 0.3's stateless baseline (state
  alone, even before rejection memory or smart questions, should reduce wasted repeat-queries).

### 0.5 — Change-point / override detection (deterministic rule, not LLM judgment)
- Implement the category-conflict rule: if the newly-extracted top-level category differs from the
  currently-held one, clear category-dependent slots (color/size/style/material), keep
  category-independent ones (budget). Add negation/reset keyword cues ("actually", "never mind",
  "instead") as a secondary trigger. Log every override to `state.override_history`.
- Acceptance: the hand-traced Intent Override sample from 0.4 now correctly clears stale slots at the
  scripted override turn.

### 0.6 — Rejection memory (three-tier confidence)
- Implement `rejection_memory.py`: explicit → hard (drop); comparative/vague → soft (penalize,
  confidence 0.5); implicit → soft, weak (confidence 0.2), **logged as a generic negative on the
  last-shown item only — never infer a specific attribute cause from a bare "what else do you have?"**
- Acceptance: a hand-constructed rejection scenario shows hard-rejected values fully excluded and
  soft-rejected values present but demoted in the ranked output.

### 0.7 — Intent router (Buying vs. Browsing)
- Implement `intent_router.py`: gazetteer hard-constraint match ⇒ Buying; else embedding-similarity
  vote against hand-authored exemplars; no LLM arbiter yet in Phase 0 (optional, add only if time
  allows and a key is configured — see 0.9).
- Wire `buying_intent_score` into retrieval breadth (Buying ⇒ apply the hard filter; Browsing ⇒ relaxed
  filter + diversity via category-balanced resampling of the top dense candidates).
- Acceptance: re-run evaluator; check the per-scenario breakdown (`buying`/`browsing` rows) for
  directionally sensible behavior (Buying sessions should show tighter candidate pools by turn 2-3).

### 0.8 — Preference-vector boost (FR-7 — fills the gap `/My Ideas/` didn't cover)
- Implement `preference.py`: EMA-updated positive/negative affinity vectors, updated from each turn's
  extracted signal (explicit statement > rejection > generic), applied as an additive ranking-time
  boost, never a retrieval filter.
- Acceptance: on a multi-turn session where preference should visibly sharpen (e.g. repeated rejections
  of one style), later-turn MRR on the same/narrowed pool visibly improves versus 0.7's output — this
  is the internal validation check for "progressively better-targeted" (Pillar III).

### 0.9 — Over-generality gate + question selector (entropy-based, exact formula)
- Implement `overgenerality.py`: `score_entropy()` over post-retrieval top-K scores, `should_clarify()`
  guardrails (pool-size floor, turn-index ceiling ~turn 7-8, diminishing-returns guard), and
  `select_best_question()` (CIKM'13 max-entropy facet selection over the live pool, restricted to the
  11-value confirmed enum, excluding `brand`/`other` from default selection — see `06_DECISION_LOG.md`
  resolved-Q2's `brand` caveat). Phrase questions as closed, catalog-grounded choices ("black, red, or
  floral print?"), never open-ended free text.
- Acceptance: calibrate `low`/`high` entropy thresholds against the 200 dev sessions; confirm the
  clarification rate is neither near-0% (never asks) nor near-100% (always asks) — both extremes are
  documented failure modes (`research/05`).

### 0.10 — Reranker: cross-encoder default + optional LLM booster
- Implement `ranker.py`: `cross-encoder/ms-marco-MiniLM-L-6-v2` as the guaranteed stage; confidence
  margin early-exit; optional single-pass listwise LLM rerank on ≤12 candidates gated behind an env var
  (never required — NFR-2). Wire the confirmed **combined ask+recommend** turn action (`"both"`) into
  `turn_policy.py` and `agent.py`.
- Also implement `logging_.py` (one-line-per-candidate rationale) — cheap, high debugging value, good
  demo material, not required by the spec but directly serves FR-10.
- Acceptance: re-run evaluator with the reranker enabled vs. disabled (a quick internal ablation, not
  the formal Phase 2 ablation) — MRR should improve without HitRate@10 regressing.

### 0.11 — Full-loop integration test + Phase 0 exit
- Run the complete pipeline against all 200 public dev sessions. Fix any crashes/regressions surfaced
  by scenario type (check the `buying`/`browsing`/`intent_override`/`boundary` breakdown specifically —
  Intent Override and Boundary are the scenarios most likely to expose bugs, per `wiki/09`'s documented
  mechanics).
- Disclose model choice, approximate cost, token usage, latency, and offline-fallback status in a draft
  `README.md` section (submission rules require this — cheaper to start now than bolt on at Phase 5).

**Phase 0 exit criteria**: full run against all 200 dev sessions, no crashes, all four metrics logged
in `wiki/08_evaluation_log.md`, and the system **clearly beats the baseline on HitRate@10 and MTTC at
minimum** (target: meaningfully above 0.125 HitRate@10 and below 9.81 MTTC — exact target thresholds
are set in `10_PRE_REGISTRATION.md` before this phase starts, not adjusted afterward to fit whatever
number comes out).

---

## Phase 1 — Cheap, high-confidence refinements (immediately after Phase 0 passes)

Refinements to Phase 0 modules, not new architecture. Low risk — log metrics before/after each, but no
formal ablation gate required (see `08_ABLATION_MATRIX.md` for what *does* need a gate).

### 1.1 — Verify RRF fully replaces any leftover weighted-sum logic
Audit `retrieval.py` — confirm no raw-score averaging slipped in anywhere during Phase 0's speed run.

### 1.2 — Explicit Shannon-entropy framing pass
Confirm `overgenerality.py`'s pool-reduction computation is exactly the entropy formula from
`04_SYSTEM_DESIGN.md` (not an approximation) — matters for the writeup's rigor, not just correctness.

### 1.3 — Threshold calibration pass
Systematically sweep `base_threshold`/`decay_rate` (turn policy) and `low`/`high` (entropy gate)
against the 200 dev sessions; record the sweep results (not just the winning values) in
`wiki/08_evaluation_log.md` for the writeup's ablation narrative.

### 1.4 — Adaptive orchestrator polish (FR-8 completion)
Add the remaining named adaptive branch points from `research/07`'s recommendation: skip-rerank on
high-confidence margin (partially done in 0.10 — confirm it's wired end to end), retrieval blend
weighting by buying-intent specificity. Log every routing decision + triggering signal
(`orchestrator.py`) — this is what makes "Adaptive Orchestration" demonstrable in the demo video.

**Phase 1 exit criteria**: no metric regressions vs. Phase 0's exit numbers on any of the three core
metrics; calibrated thresholds logged with their sweep evidence.

---

## Phase 2 — Real payoff, real cost, ablation-gated (attempt only with time left after Phase 1)

Every item here is gated by `08_ABLATION_MATRIX.md` — build behind a feature flag, measure, keep only
if it wins. **Do not** assume any of these help; the literature documents real cases where the
equivalent technique hurt.

### 2.1 — Multi-interest hypothesis vectors (K > 1)
Build `phase2/multi_interest.py` behind a flag; ablate K=1/2/3/4 per `08_ABLATION_MATRIX.md` Ablation 1.

### 2.2 — Contextual bandit action policy
Build `phase2/action_policy.py`; ablate static vs. adaptive per Ablation 2. Warm-start from Phase 3's
offline tuning pass if that's built first, rather than learning cold within each 10-turn session.

### 2.3 — Value-of-information question selection (upgrade from pure entropy)
Only build if a genuinely live-computable proxy is defined (retrieval-confidence spread, BM25/dense
disagreement — see Phase 2.5 step 1). **Never** compute this against the ground-truth target rank,
which the live agent never has access to (`06_DECISION_LOG.md` D6/D7).

---

## Phase 2.5 — Cheap refinements to Phase 2 (bundle into 2.1-2.3's work, not separate builds)

- **Retriever-disagreement as a live VoI proxy** (extends 2.3): rank-correlation/overlap between BM25
  and dense candidate lists as an additional signal, computable with zero ground truth.
- **Intent volatility**: track how much inferred interests have shifted turn-over-turn; slow the
  dynamic-K collapse rate (2.1) under high volatility rather than always monotonically shrinking.
- **Product-belief distribution framing**: maintain ranked candidates as a normalized probability-like
  distribution updated incrementally, rather than fully recomputed each turn — an implementation
  cleanliness upgrade, not new capability.

---

## Phase 3 — Offline self-evolution + comparative feedback (final stretch, only if core is solid)

### 3.1 — SkillOpt-style offline strategy tuning
Rollout → score → edit → validate loop against a **training split** of the 200 dev sessions (see
`10_PRE_REGISTRATION.md` for the exact split), producing a tuned strategy document (thresholds, facet
priorities, fusion weights) rather than hand-guessed values. Validate against the held-out split, not
the training split (that comparison is meaningless — see `08_ABLATION_MATRIX.md` Ablation 3).

### 3.2 — Comparative feedback (text-routed — CONFIRMED no click/selection channel exists)
Parse comparative language ("closer to the second one, but less flashy") through the same NLU/state
path as any other turn. Apply a Rocchio-style update, **bounded and positive-heavy** per the negative
literature on query drift (`research/06` cross-ref; `/My Ideas/` D9): high weight on original signal,
small positive-feedback weight, near-zero/heavily-damped negative term, cap feedback at k≤5.

---

## Phase 3.5 — Moderate new additions (after Phase 3's core works)

- **Portfolio/slate hedging**: reserve top few recommendation slots for highest-confidence matches,
  hedge remaining slots across plausible alternative interpretations (esp. if 2.1's multi-interest is
  kept). Ablate against pure top-10-by-score on HitRate@10.
- **Uncertainty calibration**: check whether stated confidence scores actually correlate with real
  hit-rate outcomes on held-out dev sessions; recalibrate if not.
- **Counterfactual/synthetic rollout augmentation** (extends 3.1): only if the evaluator is confirmed
  genuinely replayable with counterfactual actions — verify against the actual evaluator source before
  investing time (we have this source locally now — check before building, not after).

---

## Phase 4 — World-model-lite cluster (highest risk; attempt only with substantial time left)

Explicit non-goals, carried forward: no trained neural world model, no heavy RL, no full MCTS, no
retrained MIND/ComiRec, no LoRA/hypernetwork layer (independently cut — `06_DECISION_LOG.md` D8).
Everything here stays inside a 1-2 step hand-built heuristic lookahead.

1. A minimal transition-function "world model" — reuses `expected_pool_reduction`/entropy-reduction
   from 0.9 as its 1-step core; only adds value if extended to 2 steps.
2. Counterfactual action simulation, depth ≤2, over a handful of plausible next actions.
3. Metric-aware planning **using only live-computable proxies** — never secretly requiring ground
   truth (the exact bug already caught and fixed in D6/D7; do not reintroduce it here).
4. Planning fallback: if depth-2 estimates look unreliable, fall back to the Phase 0/2 one-step
   selector automatically — this is the default failure mode, built alongside step 2, not after.

**Mandatory gate**: ablate the full system with vs. without Phase 4, bar set higher than earlier gates
(diminishing returns are likely by construction over an already-good 1-step heuristic).

---

## Phase 5 — Submission packaging (new phase, not in `/My Ideas/` — closes the loop on deliverables)

### 5.1 — Final regression run + report numbers
Run the evaluator one final time against all 200 dev sessions with the final shipped configuration;
this is the headline number set for the written report.

### 5.2 — Package `submission/` per `docs/submission_rules.md`
Copy `src/copilot/` into `submission/src/`, write the top-level `submission/agent.py` re-export,
`requirements.txt`, and confirm the recommended layout matches exactly.

### 5.3 — README + reproducibility check
Project overview, setup/install steps, exact run command, disclosed model choice/cost/latency/offline-
fallback, limitations & what you'd improve with more time, contribution breakdown. Actually re-run the
documented steps from a clean checkout to confirm reproducibility (submission rules: failing this "may
be treated as invalid").

### 5.4 — Demo video
Walkthrough of inference/API usage across at least one full multi-turn session (no UI required — the
spec explicitly accepts an API-usage walkthrough for backend/NLP tracks). Upload to YouTube, public,
linked from Devpost.

### 5.5 — Devpost written submission
Approach, tools, APIs, libraries, datasets — cross-reference `02_TECHNICAL_PRD.md`'s deliverable
checklist so nothing is missed.

---

## If time runs out at any phase boundary

Stop at the end of whatever phase/step you're in, confirm everything already integrated still passes
the evaluator cleanly, and move straight to Phase 5 packaging around whatever is actually shipped. A
team that ships Phase 0-1 cleanly with a clear "we tried X, ablated it, cut it because Y" narrative for
anything attempted in Phase 2+ scores better on Feasibility and Presentation than one that ships a
half-working Phase 2/3 feature. This is not a fallback to be ashamed of — see `01_PROBLEM_FRAMING.md`'s
floor-vs-ceiling framing.
