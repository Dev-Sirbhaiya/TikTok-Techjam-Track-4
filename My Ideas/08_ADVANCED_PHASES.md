# 08 — Advanced Extension Phases: "World-Model-Lite" Stack

This document turns a 32-item proposed stack (external source, pasted in full below the mapping table)
into a step-by-step phased plan. **This extends `02_BUILD_PLAN.md` — it does not replace it.** Phase 0
and Phase 1 there remain the non-negotiable floor. Nothing in this document starts before that floor is
complete and evaluated.

## Read this first: most of this list is already decided — here's the mapping

Before adding anything new, here's where each of the 32 proposed items already lives in the existing
docs. Most of it is convergent validation (the same conclusions, reached independently) rather than new
work — that's a good sign, not a reason to re-litigate it.

| # | Proposed item | Where it already lives |
|---|---|---|
| 1 | Context distillation | `03_DECISION_LOG.md` D4 — already IN ARCHITECTURE |
| 2 | Global latent shopping state | Same as `DialogState`/C_t — no new work needed |
| 3 | Multi-interest latent hypotheses | D3 — already GATED (Phase 2) |
| 4 | Dynamic number of hypotheses | D3's dynamic-K mechanic — already covered |
| 5 | Context-conditioned vectors | D3's `v_k = Enc(shared + specific + turn)` — already covered |
| 6 | Bayesian belief weights | D3's probabilistic fusion `p_k` — already covered |
| 8 | Hybrid retrieval | Phase 0 floor, `02_BUILD_PLAN.md` step 7 |
| 9 | Multi-route retrieval | Same mechanism as D3 — already covered |
| 10 | Adaptive retrieval routing | The intent-specificity dial — already covered |
| 11 | Shopper regime detection | Already flagged SPECULATIVE / Phase 2 A-B candidate in `07_IDEAS_AND_REFERENCES.md` |
| 17 | Value-of-information questioning | D6 — already GATED, already corrected to need a live-computable proxy |
| 20 | Recommend while asking | D14 — already IN ARCHITECTURE, pending Q1 |
| 23 | Comparative preference learning | D9 — already IN ARCHITECTURE (reframed) |
| 24 | Tinder-style probe, demo-only | D9 — already scoped exactly this way independently |
| 25 | OLIVIA-style policy adaptation | D11 — already GATED |
| 26 | Global prior + session adaptation | Already the stated relationship between D13 (SkillOpt) and D11 (bandit warm-start) |
| 27 | SkillOpt-style offline self-evolution | D13 — already GATED |
| 32 | Strict ablations | The governing rule of `06_ABLATIONS_AND_METRICS.md` |

**Genuinely new items** (not previously in the doc set) are items 7, 12, 13, 14–16, 18, 19, 21–22, 28–31.
These are what the rest of this document actually plans for.

## Explicit non-goals (carried forward verbatim — this is a good discipline to keep)

This stack is **not** planning to build: a trained Dreamer-style neural world model, heavy RL, full MCTS,
a retrained MIND/ComiRec, or a complex LoRA/hypernetwork layer (that last one is also independently CUT
per Decision D8). Every "planning" or "world model" item below must stay inside 1–2 step lookahead using
cheap, hand-built heuristics — the moment any of this starts requiring a trained model or a real
simulation environment, it has scope-crept past what this competition's constraints and timeline support.

---

## Phase 2.5 — cheap, new, folds into existing Phase 2 items

These are small enough to bundle into the Phase 2 work already planned for D3/D6/D11 — not separate
build efforts.

**Step 1 — Retriever-disagreement as a live VoI proxy signal (extends Decision D6).**
BM25 and dense retrieval disagreeing sharply on a query is itself informative and, critically, it's
**computable live with no ground truth required** — unlike ΔHitRate/ΔMRR, which the live agent can never
access mid-session (this is the exact bug already caught in D7 — do not reintroduce it here). Add
retriever disagreement (e.g., rank-correlation or overlap between the BM25 and dense candidate lists) as
one more input to the live value-of-information proxy already being built for D6.

**Step 2 — Intent volatility (refines D3's dynamic-K collapse).**
Track how much the inferred interest hypotheses have shifted turn-over-turn. If intent is volatile
(rapid movement between interpretations), avoid collapsing K down to 1 prematurely — the existing
dynamic-K mechanic should slow its collapse rate under high volatility rather than always shrinking
monotonically with rising confidence. Cheap: this is a small modifier on an existing formula, not a new
module.

**Step 3 — Explicit change-point/override detection, distinct from gradual decay (refines D2/D10).**
The existing `_handle_override` function already exists in `05_COMPONENT_SPECS.md`, but currently
depends on the NLU step's `override_detected` flag without a specific detection method behind it. Make
this explicit: a genuine pivot (e.g., "actually, forget the dress, show me shoes instead") should
**immediately invalidate** the relevant slots/hypotheses, not merely let them decay over several turns.
This is a real distinction worth engineering deliberately — decay handles "this constraint is becoming
less relevant," override handling needs to handle "this constraint is now wrong," and conflating the two
risks a stale hypothesis lingering for several turns after the user has clearly moved on.

**Step 4 — Product-level belief distribution (reframes the ranker, does not replace it).**
Rather than the ranker just producing an ordered list with opaque scores, maintain the ranked candidates
as an explicit probability-like distribution (normalized scores) that gets updated incrementally each
turn from the same evidence already flowing into `DialogState`, instead of being fully recomputed from
scratch every time. This is more of an implementation-cleanliness upgrade than new capability — worth
doing if it makes the ranker easier to reason about and debug, not worth a separate large engineering
push.

**Ablation for this phase:** compare Phase 2 (D3/D6/D11 alone) against Phase 2.5 (same, with these four
refinements) on the dev sessions. These are small enough that a combined ablation is fine — no need to
test each in isolation unless one specifically looks like it's hurting a metric.

---

## Phase 3.5 — moderate new additions, after Phase 3's core (SkillOpt + comparative feedback) is working

**Step 1 — Portfolio/slate Top-10 hedging.**
Instead of always filling all 10 recommendation slots with the single highest-ranked candidates, reserve
the top few slots for the highest-confidence matches and use some of the remaining slots to hedge across
plausible-but-less-certain interpretations (especially relevant if D3's multi-interest hypotheses are
kept — one or two slots per live hypothesis, weighted by its probability). This is a slate-construction
step that runs *after* ranking, not a change to the ranker itself.
**Ablation:** pure top-10-by-score vs. hedged slate, on HitRate@10 specifically — hedging should help
recall without meaningfully hurting MRR if implemented correctly (since it only affects lower-confidence
slots, not the top of the list). If it hurts MRR meaningfully, the hedge allocation needs tuning or
should be dropped.

**Step 2 — Uncertainty calibration.**
Before the turn-budget policy (Decision-adjacent to D6/`turn_policy.py`) can be trusted to decide
"commit now" based on a confidence score, that confidence score needs to actually correlate with real
outcomes. Using a held-out slice of the dev sessions, check whether "top-candidate confidence = 0.8"
actually corresponds to roughly 80% real hit-rate at that confidence level, and recalibrate if not (a
simple approach: bucket historical confidence scores and compare against actual hit/miss outcomes,
adjust the raw score with a correction curve if bucket accuracy diverges meaningfully from the stated
confidence).
**Ablation:** raw uncalibrated confidence vs. calibrated confidence, feeding the same turn-budget policy
— compare TechnicalScore. Skip if time is short; this is a refinement of an already-working policy, not
a prerequisite for one.

**Step 3 — Counterfactual/synthetic rollout augmentation for the offline tuning loop (extends D13).**
The SkillOpt-style offline loop (D13) is limited to 200 labeled dev sessions. Since the catalog and
evaluator are both deterministic, additional synthetic state/action transitions can be generated by
replaying dev sessions with different hypothetical agent choices at each turn (e.g., "what if we'd asked
about material instead of color at turn 2?") and scoring the counterfactual outcome using the same
deterministic evaluator logic, without needing new real conversations. This meaningfully increases the
offline tuning loop's effective training signal.
**Caution:** only valid where the evaluator's scoring is genuinely replayable/deterministic given a
different action sequence — confirm this is actually possible against the real evaluator harness before
investing time here (this connects to Q6/Q9 in `04_OPEN_QUESTIONS.md` — read the actual evaluator source
first). If the evaluator can't be replayed with counterfactual actions, skip this step entirely rather
than trying to approximate it.

---

## Phase 4 — the "world-model-lite" cluster (highest risk, attempt only with substantial time left)

This is the heaviest, most novel part of the proposed stack, and the part most likely to become scope
creep if not tightly bounded. Everything in this phase must stay inside the explicit non-goals above —
1–2 step lookahead using cheap heuristics, never a trained model or real simulator.

**Step 1 — A minimal "structured shopping world model" (a transition function, not a trained model).**
This does not mean building a neural network that predicts future states. It means writing a small,
hand-built function that estimates, cheaply, how the candidate pool and confidence would change after a
hypothetical action — e.g., "if we ask about `use_case`, the pool likely shrinks by roughly X% based on
how discriminating that attribute has been in similar states so far." This can literally reuse the
Phase 0 `expected_pool_reduction` function (`05_COMPONENT_SPECS.md`) as its core mechanism — **the
existing question selector already IS a shallow, 1-step version of this "world model."** Phase 4 only
adds value if it extends this to 2 steps ahead, not 1.

**Step 2 — Counterfactual action simulation, 1–2 steps ahead.**
Before choosing which facet to ask about, simulate two steps: "if I ask about X and get answer Y, what
would I ask about next, and how much would the pool shrink by then?" — using the same cheap transition
function from Step 1, not a trained rollout policy. This is a small tree search over a handful of
plausible next actions, bounded strictly to depth 2, not open-ended planning.

**Step 3 — Metric-aware planning, with the live/offline correction preserved.**
The proposed framing ("value actions by expected HitRate@10 + MRR + turn efficiency") **must not**
secretly require the ground-truth target to compute live — this is the exact bug already caught and
fixed in Decision D7 (`03_DECISION_LOG.md`), and it would be a real regression to reintroduce it here
under a new name. If this is built, "expected HitRate@10 improvement" must mean an estimated proxy
(e.g., using the pool-reduction/confidence signals already available), not the literal metric, which the
live agent never has access to during a real session. Target-aware terms using real ground truth remain
legitimate only in the offline tuning loop (D13/Phase 3.5 Step 3), never in the live planning path.

**Step 4 — Planning fallback.**
If the depth-2 simulation from Step 2 produces unreliable-looking estimates (e.g., wildly different
predictions from small input changes, a sign the cheap transition function is being pushed past where
it's trustworthy), fall back automatically to the simple, already-working Phase 0/2 one-step
information-gain question selector rather than trusting a bad simulation. This fallback should be the
default failure mode, not an edge case handled late — build it alongside Step 2, not after.

**Mandatory gate for the entire Phase 4 cluster:** ablate the full Phase 0–3.5 system against the same
system with Phase 4's 2-step planning added, on the dev sessions. Given the real risk of added latency,
added complexity, and a small absolute ceiling for improvement (a 2-step lookahead over an already-good
1-step heuristic has diminishing returns almost by construction), **the bar to justify keeping this
phase should be higher than for earlier gated items** — a marginal or noisy improvement is not enough
to justify the added complexity and failure surface this introduces this late in a build.

---

## Explicit engineering decision to make, not silently assume: "fully local scoring path"

The proposed stack's item 31 argues for a fully local scoring path with no external LLM/API dependency
anywhere in the core loop. This is a stronger commitment than what's currently documented — Phase 0 step
7 (`02_BUILD_PLAN.md`) keeps an *optional* LLM call for re-ranking a short list. These are a genuine
tradeoff, not a strict upgrade either direction:
- **Fully local**: faster, cheaper, zero dependency risk, easier to reason about latency — but likely
  gives up whatever quality an LLM re-rank of the top ~20–30 candidates would have added.
- **LLM-assisted re-rank (current default)**: potentially better ranking quality on ambiguous cases, at
  the cost of latency/cost and an external dependency.
**Recommendation:** keep Phase 0's default (LLM re-rank optional, gated behind `len(shortlist) > 3` per
Decision D12) unless a fully-local run is shown via ablation to perform comparably — don't silently
switch to fully-local without checking whether it costs ranking quality. If time allows, ablate both.

---

## Summary: where each new phase sits relative to the existing plan

```
Phase 0  (02_BUILD_PLAN.md) ── non-negotiable floor
Phase 1  (02_BUILD_PLAN.md) ── cheap safe wins
Phase 2  (02_BUILD_PLAN.md) ── multi-interest / bandit, ablation-gated
Phase 2.5 (this document)   ── cheap refinements to Phase 2 (volatility, override detection,
                                 retriever disagreement, product-belief framing)
Phase 3  (02_BUILD_PLAN.md) ── SkillOpt offline tuning + comparative feedback
Phase 3.5 (this document)   ── portfolio slate, uncertainty calibration, synthetic rollouts
Phase 4  (this document)    ── world-model-lite planning cluster, highest risk, highest bar to keep
```

Same rule as everywhere else in this doc set: nothing in Phase 2.5 through 4 gets kept because the idea
is good on paper. It gets kept because it won its ablation against held-out dev sessions. See
`06_ABLATIONS_AND_METRICS.md` for the exact procedure this document's ablations should follow.
