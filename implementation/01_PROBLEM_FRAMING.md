# 01 — Problem Framing

## Restated, in our own words

Given a shopper's message on each of up to 10 turns, return a natural-language `message`, optionally
one clarifying `ask_attribute`, and up to 10 ranked `parent_asin` product IDs from a frozen 50,000-item
catalog — such that the session's true (hidden) target product appears as early and as high-ranked as
possible. The system is scored, not judged qualitatively, by a deterministic local evaluator the
organizer also uses (with a private 800-session set) — this is a **retrieval + ranking + dialogue-
policy optimization problem with a hard efficiency constraint**, not a conversational-UX problem.

## Why this framing matters (it changes what "good" looks like)

Because scoring is fully deterministic and mechanical (see `wiki/09_simulator_mechanics.md` — the
simulated customer is rule-based, not an LLM, and its exact reveal logic is now known), **this is
closer to a competitive-programming / applied-IR optimization task against a known, inspectable
opponent than a "build a nice chatbot" task.** The single highest-value activity is not clever
dialogue design in the abstract — it's building an accurate mental (and literal, in code) model of
`evaluator/local_evaluator.py`'s `classify_constraint()`, `customer_reply()`, and scoring formula, and
optimizing against *that specific mechanism*. Every architecture decision in this corpus is filtered
through this lens.

## Success criteria (in priority order, from the actual scoring formula)

`TechnicalScore = 0.50×HitRate@10 + 0.30×MRR + 0.20×Efficiency`, `Efficiency = clip((11−MTTC)/10,0,1)`
(verified against source, `wiki/00_problem_statement.md`). Because MRR ≤ HitRate@10 always, and
Efficiency = 0 on any failed session:

1. **Coverage first.** Get the true item into the top-10 candidate set at all. This is the load-bearing
   metric (50% weight) and a hard prerequisite for the other two.
2. **Precision second.** Push it to rank 1-2 once it's in the pool. MRR's convex shape means this is
   cheap to buy relative to its payoff once coverage is solid.
3. **Efficiency last, as a gate not a goal.** Never trade coverage/precision for fewer turns. A
   confident wrong guess turn 1 scores worse than a correct answer at turn 4.

The competition's own four "pillars" (Intent Routing, Dialog Strategy, Self-Evolution, Evaluation) are
a design-quality rubric layered on top of this — Innovation & Problem Insight (20%) and Technical
Execution (35%) reward *demonstrating* these pillars are addressed thoughtfully, but the TechnicalScore
itself only measures the three metrics above. Build for the metric; narrate the pillars in the writeup
using what was actually built (this corpus is structured so that mapping is direct and honest, not
retrofitted).

## The floor vs. the ceiling — two different failure modes to design against

- **Floor risk**: shipping nothing that beats the weak BM25 baseline (HitRate@10 0.125, MRR 0.068,
  MTTC 9.81, TechnicalScore 0.107) because time ran out mid-ambitious-feature. This is the single
  worst outcome available and is entirely avoidable — see `05_BUILD_PLAN.md` Phase 0's explicit design
  as insurance against it.
- **Ceiling risk**: over-investing in sophisticated-sounding mechanisms (multi-interest vectors,
  contextual bandits, world-model-lite planning) that look impressive but don't move the measured
  metrics, or worse, destabilize a working system days before the 2026-09-01 12:00 deadline. This is
  why every non-floor addition in `05_BUILD_PLAN.md` is ablation-gated per `08_ABLATION_MATRIX.md` —
  "published, well-cited, and doesn't help our dev sessions" is a real, common outcome, not a strawman.

## What makes this problem genuinely hard (not just busywork)

1. **Information is scarce and structured**: the simulated customer reveals only ~2-4 distinct
   constraint strings per session, ever, and only when asked about the exact right facet (per its
   `classify_constraint()` keyword taxonomy). There's a real ceiling on how much can be *learned*
   within a session — most of the achievable score comes from using what's given efficiently, not
   from extracting more than exists.
2. **Two failure modes pull in opposite directions**: asking too much burns the turn budget
   (Efficiency, and risks the 10-turn hard fail); asking too little means retrieving/ranking against
   an underspecified query (hurts HitRate@10/MRR). The whole "Dialog Strategy" pillar is this
   trade-off, and it has real prior-art solutions (entropy-gated clarification — `research/05`).
3. **Intent Override is adversarial to naive confidence**: 15% of sessions script a forced pivot at
   turn 3-4 regardless of agent behavior, and a hit *before* that pivot never counts. A system that
   locks in early confidence without a change-point mechanism silently loses these sessions.
4. **No guaranteed LLM API**: the organizer provides none. A design that only works with a paid LLM in
   the loop is a real, structural risk, not a hypothetical one — Phase 0 must have a fully local,
   zero-API-dependency path that still beats the baseline (see `06_DECISION_LOG.md` D-LLM-TIER).

## Non-goals (explicitly, so scope discipline is visible from day one)

No UI, no full-parameter LLM fine-tuning, no external/hosted vector DB, no multi-modal processing, no
catalog mutation, no cross-session persistent user profiles (sessions are isolated single-user — see
`06_DECISION_LOG.md` D8), no trained neural components requiring a labeled-data training loop of any
kind. Full list and rationale: `02_TECHNICAL_PRD.md` §Out of Scope.
