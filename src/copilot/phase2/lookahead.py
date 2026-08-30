"""Phase 4: world-model-lite 1-step lookahead question selection, gated behind
ENABLE_LOOKAHEAD_QUESTION_SELECTION.

Explicit non-goals carried forward from implementation/05_BUILD_PLAN.md's Phase 4 section: no
trained neural world model, no RL, no MCTS, no retrained MIND/ComiRec. This is a hand-built 1-step
heuristic, matching the build plan's "1-2 step hand-built heuristic lookahead" scope, not an attempt
at the full 2-step version (no evidence yet that 1-step clears the bar; extending depth before that
is premature).

Critical constraint (D6/D7, already caught and fixed once in Phase 2 -- do not reintroduce it): the
live Agent never receives the simulator's `intent_card`/hidden target, only conversational text and
its own retrieved candidate pool. Genuinely simulating "what would the simulator actually say if I
asked X" is therefore impossible by design, however tempting a name like "world model" makes it
sound -- this instead reasons about the AGENT'S OWN candidate pool: for each candidate facet,
compute the EXPECTED reduction in the pool's SCORE-distribution entropy after hypothetically
conditioning on each of the facet's observed values, weighted by how many current candidates hold
that value (a live-computable proxy for likelihood, never ground truth).

This is a genuine upgrade over `overgenerality.select_best_question()`'s existing heuristic (entropy
of the facet's OWN value distribution): that measures how evenly-spread a facet's values are, which
is only a proxy for how much asking about it would actually resolve RANKING uncertainty -- a facet
with evenly-distributed values doesn't necessarily correlate with score-distribution structure. This
directly measures the thing turn_policy's ask/commit decision and the final ranking both care about.
"""
from __future__ import annotations

from collections import Counter

from .. import overgenerality

ENABLE_LOOKAHEAD_QUESTION_SELECTION = False  # Ablated 2026-08-30 (Phase 4's mandatory gate: "bar set
# higher than earlier gates, diminishing returns are likely by construction over an already-good
# 1-step heuristic" -- exactly what happened). Guaranteed path, both splits: validation (n=40) ON
# 0.45/0.269792/7.9/**0.367938** vs OFF 0.45/0.270238/7.5/**0.376071** (worse -- more turns needed,
# MTTC 7.9 vs 7.5); training (n=160, confirmatory) ON 0.51875/0.287636/6.975/**0.426166** vs OFF
# 0.5125/0.281734/6.7562/**0.425645** (essentially flat, +0.1%, MTTC still slightly worse). Per
# Phase 4's own explicitly-higher bar, a wash-to-slightly-negative result across two splits does not
# clear it. DECLINED -- the existing entropy-based heuristic in overgenerality.py was already good
# enough that a more theoretically-principled expected-entropy-reduction lookahead doesn't earn a
# measurable improvement, matching the build plan's own risk prediction for this phase. Module kept
# for the writeup's "attempted the highest-risk phase, found diminishing returns as predicted,
# declined" record.


def expected_entropy_reduction(candidates: list[dict], attribute: str) -> float:
    """Base score-distribution entropy minus the expected entropy after hypothetically
    conditioning on `attribute`'s observed values, weighted by their live-observed frequency in
    the current pool (never the target's true value, which the agent has no access to)."""
    # Reach into overgenerality's "private" helper directly rather than duplicating it -- phase2/
    # modules importing core (never the reverse) is the same one-way layering already used
    # throughout (e.g. phase2/query_nudge.py -> catalog.py's dense_search hook).
    values = overgenerality._facet_values(candidates, attribute)
    if not values:
        return 0.0
    # CORRECTED per codex review (2026-08-30): this used to normalize each value's probability
    # over `len(values)` (the POPULATED subset only) while `base_entropy` covers the FULL pool --
    # candidates missing this facet (which `_facet_values` silently drops) then contributed no
    # posterior entropy at all, letting a sparsely-populated facet look artificially maximally
    # informative. Now weights every branch (including a "missing" branch, if any candidates lack
    # the facet) against the full pool size, so a sparse facet can no longer look better than it is.
    total = len(candidates)
    counts = Counter(values)
    base_entropy = overgenerality.score_entropy([c.get("_score", 0.0) for c in candidates])
    expected_conditional = 0.0
    covered = 0
    for value, count in counts.items():
        p_value = count / total
        covered += count
        subset_scores = [c.get("_score", 0.0) for c in candidates
                          if c.get("attributes", {}).get(attribute) == value]
        subset_entropy = overgenerality.score_entropy(subset_scores) if subset_scores else 0.0
        expected_conditional += p_value * subset_entropy
    missing = total - covered
    if missing > 0:
        p_missing = missing / total
        missing_scores = [c.get("_score", 0.0) for c in candidates
                           if not c.get("attributes", {}).get(attribute)]
        expected_conditional += p_missing * overgenerality.score_entropy(missing_scores)
    return max(0.0, base_entropy - expected_conditional)


def _select_best_question_lookahead(candidates, filled_slots, attribute_enum, utility_fn=None):
    """Drop-in alternative to overgenerality.select_best_question() using expected
    score-entropy reduction instead of raw facet-value entropy. Applies the SAME candidacy gates
    (distinct-value cap/ratio, unproductive-attribute exclusion) so it only changes WHICH facet
    wins among already-legitimate candidates, not which facets are eligible at all."""
    pool_size = len(candidates)
    best_attr, best_gain = None, -1.0
    for attr in attribute_enum:
        if attr in filled_slots or attr in overgenerality._UNPRODUCTIVE_ATTRIBUTES:
            continue
        values = overgenerality._facet_values(candidates, attr)
        n_distinct = len(set(values))
        if not (overgenerality._MIN_DISTINCT_VALUES <= n_distinct <= overgenerality._MAX_DISTINCT_VALUES):
            continue
        if pool_size and (n_distinct / pool_size) > overgenerality._MAX_DISTINCT_RATIO:
            continue
        gain = expected_entropy_reduction(candidates, attr) * (utility_fn(attr) if utility_fn else 1.0)
        if gain > best_gain:
            best_attr, best_gain = attr, gain
    return best_attr if best_gain > 0 else None


def select_best_question(candidates, filled_slots, attribute_enum, utility_fn=None):
    """Public entry point agent.py calls in place of overgenerality.select_best_question directly
    -- routes to the lookahead selector when enabled, else passes straight through unchanged.
    Phase 4's mandatory fallback ("if depth-2 estimates look unreliable, fall back to the Phase 0/2
    one-step selector automatically", built alongside the mechanism, not after): any exception, or
    the lookahead finding no facet with positive expected gain, falls back to the already-shipped
    heuristic rather than returning nothing."""
    if not ENABLE_LOOKAHEAD_QUESTION_SELECTION:
        return overgenerality.select_best_question(candidates, filled_slots, attribute_enum, utility_fn)
    try:
        result = _select_best_question_lookahead(candidates, filled_slots, attribute_enum, utility_fn)
        if result is not None:
            return result
    except Exception:
        pass
    return overgenerality.select_best_question(candidates, filled_slots, attribute_enum, utility_fn)
