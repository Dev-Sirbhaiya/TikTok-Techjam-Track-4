"""Fast unit tests -- no dense-encoder dependency, run in well under a second. See
implementation/08_ABLATION_MATRIX.md for the fuller evaluator-based validation these complement.
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from copilot.catalog import _normalized_category_parts, coarse_category, price_bucket
from copilot.nlu import extract_slot_updates, classify_value_attribute, apply_extraction
from copilot.overgenerality import score_entropy, should_clarify, select_best_question, _facet_value_entropy
from copilot.rejection_memory import detect_rejection_signal, apply_rejection, apply_rejection_filter
from copilot.retrieval import reciprocal_rank_fusion
from copilot.state import DialogState

GAZETTEER = {
    "colors": {"black", "red", "blue", "green"},
    "materials": {"cotton", "leather", "polyester"},
    "brands": {"nike", "adidas"},
    "categories": {"dresses", "shoes"},
    "sizes": set(),
}


def test_rrf_basic_ordering():
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "c", "a"]])
    assert fused["b"] > fused["a"] or fused["b"] > fused["c"]
    assert set(fused) == {"a", "b", "c"}


def test_rrf_restrict_to():
    fused = reciprocal_rank_fusion([["a", "b"], ["b", "c"]], restrict_to={"b"})
    assert set(fused) == {"b"}


def test_score_entropy_confident_vs_ambiguous():
    confident = score_entropy([10.0, 0.1, 0.1, 0.1], temperature=1.0)
    ambiguous = score_entropy([1.0, 1.0, 1.0, 1.0], temperature=1.0)
    assert confident < 0.3
    assert ambiguous > 0.9


def test_score_entropy_handles_negative_scores_no_crash():
    # Preference-boost subtraction can make scores negative -- must not raise (round-1 fix).
    h = score_entropy([-0.5, 0.3, -0.1, 0.2])
    assert 0.0 <= h <= 1.0


def test_score_entropy_empty():
    assert score_entropy([]) == 0.0


def test_should_clarify_turn_ceiling():
    # turns_remaining=2 means turn 8 of 10; no_ask_after_turn=7 -> ceiling at turns_remaining<=3
    assert should_clarify(entropy=0.9, pool_size=20, turns_remaining=2, no_ask_after_turn=7) is False
    assert should_clarify(entropy=0.9, pool_size=20, turns_remaining=5, no_ask_after_turn=7) is True


def test_should_clarify_pool_floor():
    assert should_clarify(entropy=0.9, pool_size=2, turns_remaining=5, min_pool_to_bother=4) is False


def test_facet_value_entropy_prefers_split_attribute():
    # _facet_value_entropy returns RAW (unnormalized) Shannon entropy in nats -- used only for
    # relative comparison between facets in select_best_question(), so max-for-2-values is ln(2),
    # not 1.0 (that normalization is score_entropy()'s job, a different function for a different
    # purpose). Original test assertion (`> 0.9`) reflected a wrong expectation, not a code bug.
    split_candidates = [
        {"attributes": {"color": "black"}},
        {"attributes": {"color": "red"}},
        {"attributes": {"color": "black"}},
        {"attributes": {"color": "red"}},
    ]
    skewed_candidates = [{"attributes": {"color": "black"}}] * 3 + [{"attributes": {"color": "red"}}]
    split_h = _facet_value_entropy(split_candidates, "color")
    skewed_h = _facet_value_entropy(skewed_candidates, "color")
    assert split_h == pytest.approx(math.log(2), rel=1e-6)
    assert split_h > skewed_h  # an even split is more informative to ask about than a skewed one


def test_classify_value_attribute():
    assert classify_value_attribute("cotton", GAZETTEER) == "material"
    assert classify_value_attribute("red", GAZETTEER) == "color"
    assert classify_value_attribute("budget around $45", GAZETTEER) == "budget"
    assert classify_value_attribute("some random feature text", GAZETTEER) == "feature"


def test_extract_buying_opener():
    result = extract_slot_updates(
        "I'm looking for dresses. A key requirement is: cotton.", DialogState(), GAZETTEER, turn=1)
    assert result["slot_updates"]["category"] == "dresses"
    assert result["slot_updates"].get("material") == "cotton"


def test_extract_browsing_opener():
    result = extract_slot_updates(
        "I'm looking for shoes, but I'm still exploring.", DialogState(), GAZETTEER, turn=1)
    assert result["slot_updates"]["category"] == "shoes"
    assert "material" not in result["slot_updates"]


def test_extract_forced_override():
    state = DialogState()
    state.slots["color"] = "black"
    result = extract_slot_updates(
        "Actually, ignore my earlier preference. What I need is: red.", state, GAZETTEER, turn=4)
    assert result["override"] is not None
    assert result["override"]["cleared_category_dependent"] is True


def test_apply_extraction_clears_category_dependent_slots_on_override():
    state = DialogState()
    state.slots.update({"color": "black", "size": "M", "budget_max": 50.0})
    extraction = {
        "slot_updates": {},
        "override": {"cleared_category_dependent": True, "new_value": "red", "attribute": "color"},
        "exhausted_attribute": None,
    }
    apply_extraction(state, extraction, turn=4)
    assert "color" not in state.slots
    assert "size" not in state.slots
    assert state.slots["budget_max"] == 50.0  # category-independent slot survives
    assert len(state.override_history) == 1


def test_extract_reveal_classifies_each_value_independently():
    # Self-caught bug (round 0, before any review): originally forced ALL revealed values onto
    # last_asked_attribute's single slot key, so a second value silently overwrote the first even
    # when it was a clearly different attribute type. Each value is now classified independently.
    state = DialogState()
    state.last_asked_attribute = "material"
    result = extract_slot_updates(
        "For that, what matters is: cotton; under $80.", state, GAZETTEER, turn=2)
    assert result["slot_updates"].get("material") == "cotton"
    assert result["slot_updates"].get("budget") == "under $80"
    assert result["slot_updates"].get("budget_max") == 80.0


def test_extract_reveal_same_attribute_falls_back_to_last_asked():
    # Two genuinely ambiguous/generic values for the same asked attribute: both fall back to
    # last_asked_attribute since neither classifies as anything more specific than "feature".
    state = DialogState()
    state.last_asked_attribute = "feature"
    result = extract_slot_updates(
        "For that, what matters is: durable stitching; reinforced sole.", state, GAZETTEER, turn=2)
    assert result["slot_updates"].get("feature") in ("durable stitching", "reinforced sole")


def test_extract_no_additional_marks_exhausted():
    result = extract_slot_updates(
        "I don't have an additional preference for budget.", DialogState(), GAZETTEER, turn=3)
    assert result["exhausted_attribute"] == "budget"
    assert result["no_new_info"] is True


def test_rejection_hard_vs_soft():
    hard = detect_rejection_signal("I don't want black, it's too plain", GAZETTEER)
    assert hard["type"] == "explicit"
    assert hard["attribute"] == "color"

    implicit = detect_rejection_signal("no thanks", GAZETTEER)
    assert implicit["type"] == "implicit"
    assert implicit["attribute"] is None  # never invent an attribute from a vague signal


def test_rejection_filter_drops_hard_keeps_soft():
    state = DialogState()
    apply_rejection(state, {"type": "explicit", "attribute": "color", "value": "black"})
    apply_rejection(state, {"type": "comparative", "attribute": "material", "value": "leather"})
    candidates = [
        {"parent_asin": "A", "attributes": {"color": "black"}, "_score": 1.0},
        {"parent_asin": "B", "attributes": {"color": "red", "material": "leather"}, "_score": 1.0},
        {"parent_asin": "C", "attributes": {"color": "red"}, "_score": 1.0},
    ]
    filtered = apply_rejection_filter(candidates, state)
    ids = {c["parent_asin"] for c in filtered}
    assert "A" not in ids  # hard-rejected color dropped entirely
    assert ids == {"B", "C"}
    b = next(c for c in filtered if c["parent_asin"] == "B")
    assert b["_rejection_penalty"] > 0  # soft-rejected material penalized, not dropped


def test_retriever_disagreement_full_overlap_is_zero():
    from copilot.retrieval import retriever_disagreement
    same = ["a", "b", "c", "d"]
    assert retriever_disagreement(same, same) == 0.0


def test_retriever_disagreement_no_overlap_is_one():
    from copilot.retrieval import retriever_disagreement
    assert retriever_disagreement(["a", "b"], ["c", "d"]) == 1.0


def test_adjusted_clarify_threshold_lowers_bar_on_disagreement():
    from copilot.phase2.voi import adjusted_clarify_threshold
    assert adjusted_clarify_threshold(0.3, disagreement=1.0) < 0.3
    assert adjusted_clarify_threshold(0.3, disagreement=0.0) == 0.3


def test_multi_interest_k1_fallback_matches_single_ema():
    import copilot.phase2.multi_interest as mi
    import numpy as np
    mi.ENABLE_MULTI_INTEREST = False
    try:
        state = mi.MultiInterestState()
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        state.update(v1)
        state.update(v2)
        assert len(state.vectors) == 1  # K=1 disabled -> never spawns a second hypothesis
    finally:
        mi.ENABLE_MULTI_INTEREST = True


def test_multi_interest_spawns_second_hypothesis_on_divergence():
    import copilot.phase2.multi_interest as mi
    import numpy as np
    state = mi.MultiInterestState()
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])  # orthogonal -- similarity 0, well below SPAWN_THRESHOLD
    state.update(v1)
    state.update(v2)
    assert len(state.vectors) == 2


def test_action_policy_warm_start_prior_not_cold():
    from copilot.phase2.action_policy import initial_utility
    # Warm-started, per D11's cold-start-risk mitigation -- material/color should start above a
    # neutral 1.0, budget below, matching wiki/09's verified ground truth about reveal channels.
    assert initial_utility("material") > 1.0
    assert initial_utility("budget") < 1.0


def test_action_policy_record_outcome_updates_utility():
    import copilot.phase2.action_policy as ap
    # Disabled by default post-ablation (see the module's own comment) -- force-enable to test the
    # underlying mechanism itself in isolation from the ablation's on/off decision.
    original = ap.ENABLE_ACTION_POLICY
    ap.ENABLE_ACTION_POLICY = True
    try:
        state = DialogState()
        prior = ap.initial_utility("color")
        ap.record_outcome(state, "color", pool_before=20, pool_after=5)  # a big, productive reduction
        assert state.facet_utility_history["color"] > prior  # good outcome should raise the estimate
    finally:
        ap.ENABLE_ACTION_POLICY = original


def test_turns_remaining():
    state = DialogState(turn_count=7)
    assert state.turns_remaining == 3


def test_accumulated_terms_survive_a_no_new_info_turn():
    # Self-caught bug: retrieval used to rebuild its query from ONLY the current turn's terms, so
    # a "no new info" reply (e.g. the simulator's generic non-answer) would wipe out everything
    # learned in earlier turns. accumulated_terms must carry forward across such a turn.
    state = DialogState()
    apply_extraction(state, extract_slot_updates(
        "I'm looking for dresses. A key requirement is: cotton.", state, GAZETTEER, turn=1), turn=1)
    assert "dresses" in state.accumulated_terms and "cotton" in state.accumulated_terms

    apply_extraction(state, extract_slot_updates(
        "I don't have an additional preference for budget.", state, GAZETTEER, turn=2), turn=2)
    assert "dresses" in state.accumulated_terms and "cotton" in state.accumulated_terms


def test_word_boundary_prevents_substring_misclassification():
    # Regression for codex review finding: "Water Resistant" contains "tan" as a substring and
    # was being classified as color=tan before word-boundary matching was added.
    assert classify_value_attribute("Water Resistant", GAZETTEER) != "color"
    assert classify_value_attribute("black leather strap", GAZETTEER) == "material"  # leather wins (checked first)
    assert classify_value_attribute("black", GAZETTEER) == "color"


def test_category_normalization_matches_evaluator_comma_splitting():
    # Regression for codex review finding: categories must be comma-split before use, exactly
    # like the evaluator's own coarse_category(), or our index desyncs from what's disclosed.
    categories = ["Clothing, Shoes & Jewelry", "Women", "Clothing", "Tops, Tees & Blouses"]
    parts = _normalized_category_parts(categories)
    assert "Tops" in parts and "Tees & Blouses" in parts
    assert "Clothing" not in parts  # excluded exactly, not just as a whole unsplit string
    assert coarse_category(categories) == "Tops Tees & Blouses"


def test_price_bucket_reduces_cardinality():
    assert price_bucket(10) == "under $15"
    assert price_bucket(150) == "$100+"
    # A handful of fixed bands, not one bucket per distinct price -- this is what prevents budget
    # from dominating unnormalized entropy comparisons against low-cardinality facets like color.
    assert len({price_bucket(p) for p in range(0, 200, 5)}) <= 6


def test_select_best_question_skips_near_unique_facets():
    # Regression for codex review finding: a facet where almost every candidate has a distinct
    # value (e.g. raw per-product feature text) must not be selectable as a closed-choice question
    # just because its raw entropy is high -- it's not presentable as 2-4 options. Pool size (30)
    # chosen to exceed overgenerality._MAX_DISTINCT_VALUES (calibrated to 15 in Phase 1.3) with
    # near-unique feature text, while color still only ever takes 2 values regardless of pool size.
    candidates = [{"attributes": {"feature": f"unique feature text {i}", "color": "black" if i % 2 else "red"}}
                  for i in range(30)]
    attr = select_best_question(candidates, filled_slots=set(), attribute_enum=["feature", "color", "other", "brand"])
    assert attr == "color"  # color has 2 presentable values; feature has 30 near-unique ones


def test_select_best_question_ratio_gate_catches_small_near_unique_pools():
    # Regression for codex review round 2: an absolute distinct-value cap alone doesn't scale down
    # -- once reranking narrows the pool to e.g. 10 candidates, a near-unique facet's distinct
    # count (10) can slip under the absolute cap (15) even though it's just as "near-unique"
    # relative to this smaller pool. The ratio gate (n_distinct/pool_size) catches this regardless
    # of absolute pool size.
    small_pool = [{"attributes": {"feature": f"unique {i}", "color": "black" if i % 2 else "red"}}
                  for i in range(10)]
    attr = select_best_question(small_pool, filled_slots=set(), attribute_enum=["feature", "color", "other", "brand"])
    assert attr == "color"


def test_no_new_info_turn_does_not_trigger_rejection():
    # Regression for codex review finding: the simulator's own decline templates contain "don't"
    # and were being misread as an implicit rejection by rejection_memory's negation check --
    # agent.py now skips rejection detection entirely when nlu.py already tagged a turn as
    # "no new info" (i.e. it matched one of those exact templates).
    result = extract_slot_updates(
        "I don't have an additional preference for budget.", DialogState(), GAZETTEER, turn=3)
    assert result["no_new_info"] is True
    # (the actual skip lives in agent.py's respond() -- this test documents the signal it checks)


def test_override_resets_accumulated_terms_to_new_intent():
    state = DialogState()
    state.slots["category"] = "dresses"
    state.accumulated_terms = ["dresses", "cotton", "black"]
    extraction = {
        "slot_updates": {},
        "query_terms": [],
        "override": {"cleared_category_dependent": True, "new_value": "leather shoes", "attribute": "feature"},
        "exhausted_attribute": None,
    }
    apply_extraction(state, extraction, turn=4)
    assert "black" not in state.accumulated_terms
    assert "leather shoes" in state.accumulated_terms
