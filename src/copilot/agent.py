"""The Agent class -- the actual scored interface. See docs/agent_api_contract.json and
implementation/02_TECHNICAL_PRD.md for the exact contract this implements.

Both codex-review rounds' fixes are applied here:
- recommendations are populated whenever a ranked pool exists, regardless of action (round 1 #2)
- recommendations are emitted as {"parent_asin": ...} objects, not bare strings (round 1 #3)
"""
from __future__ import annotations

from pathlib import Path

from .catalog import CatalogIndex, build_gazetteer, load_catalog
from .intent_router import route_intent
from .logging_ import log_turn_rationale
from .nlu import apply_extraction, extract_slot_updates
from .orchestrator import OrchestrationTrace, decide_rerank_depth, record_action, route_retrieval_breadth
from .overgenerality import score_entropy, select_best_question
from .phase2.action_policy import record_outcome, utility_multiplier
from .phase2.voi import adjusted_clarify_threshold
from .phrasing import phrase_question, phrase_recommendation
from .preference import update_preference_vectors
from .ranker import rerank
from .rejection_memory import apply_rejection, apply_rejection_filter, detect_rejection_signal
from .retrieval import retrieve_candidates
from .state import DialogState
from .strategy_config import CLARIFY_BASE_LOW, NEG_BOOST_WEIGHT
from .turn_policy import decide_turn_action

ATTRIBUTE_ENUM = [
    "category", "material", "color", "size", "style", "brand",
    "budget", "feature", "use_case", "other",
]

DEFAULT_CATALOG_PATH = "data/catalog.jsonl"


class Agent:
    """Editable real agent. Constructed once by the evaluator harness (see
    evaluator/local_evaluator.py's `Agent(args.catalog)` call) -- expensive setup (catalog load,
    gazetteer, BM25 index) happens once here, not per session/turn."""

    def __init__(self, catalog_path: str | Path = DEFAULT_CATALOG_PATH) -> None:
        products = load_catalog(catalog_path)
        gazetteer = build_gazetteer(products)
        self.catalog_index = CatalogIndex(products, gazetteer)
        self.gazetteer = gazetteer
        self._sessions: dict[str, DialogState] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        self._sessions[session_id] = DialogState()
        # user_profile (preference_tags, rating_style, etc.) is a safe aggregate the org provides;
        # not load-bearing for Phase 0 -- reserved for a Phase 1+ personalization refinement.

    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        state = self._sessions.setdefault(session_id, DialogState())
        state.turn_count = turn - 1  # evaluator passes 1-indexed turn; recompute after processing

        extraction = extract_slot_updates(user_message, state, self.gazetteer, turn)
        apply_extraction(state, extraction, turn)

        # CORRECTED per codex review: the simulator's own non-answer templates ("I don't have an
        # additional preference for X", "I don't have a preference for X; please use your
        # judgment") contain "don't" and were matching rejection_memory's negation regex, so
        # declining to answer a clarification question was being misread as an implicit rejection
        # -- penalizing the top-ranked candidate and corrupting the negative preference vector on
        # every unproductive clarification, not just genuine rejections. Skip rejection detection
        # entirely on turns nlu.py already tagged as "no new info" (it recognized these exact
        # templates); only run it on genuine free-form user turns.
        rejection_signal = None if extraction.get("no_new_info") else detect_rejection_signal(user_message, self.gazetteer)
        if rejection_signal:
            apply_rejection(state, rejection_signal)

        track = route_intent(user_message, state.slots, self.gazetteer)
        state.buying_intent_score = 0.8 if track == "buying" else 0.3

        # Phase 1.4 (FR-8): named, logged adaptive-orchestration decision points, replacing what
        # used to be inline unlabeled branches -- see orchestrator.py.
        trace = OrchestrationTrace()
        apply_hard_filter = route_retrieval_breadth(state.buying_intent_score, trace)

        query_text = " ".join(state.accumulated_terms) or user_message
        candidates, disagreement = retrieve_candidates(query_text, state.slots, apply_hard_filter, self.catalog_index)
        candidates = apply_rejection_filter(candidates, state)

        turn_embedding = self.catalog_index.encode_text(query_text)
        signal = "negative" if rejection_signal else ("positive" if extraction.get("slot_updates") else None)
        if signal == "negative":
            update_preference_vectors(state, turn_embedding, signal)
        elif signal == "positive":
            # Phase 2.1: positive-interest tracking goes through MultiInterestState, which
            # subsumes K=1 (Phase 1's single EMA vector) as its disabled/no-spawn behavior -- see
            # phase2/multi_interest.py. Negative-affinity tracking is unchanged from Phase 1.
            if state.multi_interest is None:
                from .phase2.multi_interest import MultiInterestState
                state.multi_interest = MultiInterestState()
            state.multi_interest.update(turn_embedding)
        for c in candidates:
            emb = self.catalog_index.embedding_for(c["parent_asin"])
            neg_boost = 0.0
            if state.pref_vector_neg is not None and emb is not None:
                neg_boost = -NEG_BOOST_WEIGHT * float((emb * state.pref_vector_neg).sum())
            pos_boost = state.multi_interest.boost(emb) if state.multi_interest is not None else 0.0
            c["_score"] += pos_boost + neg_boost - c.get("_rejection_penalty", 0.0) * 0.05

        entropy = score_entropy([c["_score"] for c in candidates[:10]]) if candidates else 0.0
        state.pool_entropy = entropy

        rerank_depth = decide_rerank_depth(len(candidates), trace)
        ranked = rerank(candidates[:rerank_depth], state, state.accumulated_terms)
        state.candidate_pool = [c["parent_asin"] for c in ranked]

        # Phase 2.2: close the bandit's reward loop from whatever was asked last turn -- the LIVE
        # reward is pool-size reduction only (never the target rank; see D6/D7).
        # CORRECTED per Phase 2 codex review (finding 1): use the pre-rerank-cap pool (`candidates`,
        # post-filter but before `[:rerank_depth]`/`ranked`'s hard cap at 50) on both sides of the
        # comparison. `len(ranked)` saturates at `rerank_depth` (50 whenever the pool exceeds 20 --
        # see orchestrator.decide_rerank_depth), so it was usually pool-size-invariant regardless of
        # how much the clarification actually narrowed the candidate set, producing false-zero
        # rewards and an unreliable ablation signal.
        # CORRECTED per Phase 2 codex review (finding 2): consume the pending ask exactly once by
        # clearing `pool_size_at_ask` immediately after recording -- previously it was never reset,
        # so an ask followed by one or more non-ask turns kept replaying the same stale outcome
        # against each subsequent turn's unrelated pool until the next ask overwrote it.
        if state.last_asked_attribute and state.pool_size_at_ask is not None:
            record_outcome(state, state.last_asked_attribute, state.pool_size_at_ask, len(candidates))
            state.pool_size_at_ask = None

        # Phase 2.3/2.5: retriever-disagreement-adjusted clarify threshold -- gated behind
        # phase2.voi.USE_DISAGREEMENT_SIGNAL, ablated before being trusted by default.
        clarify_low = adjusted_clarify_threshold(CLARIFY_BASE_LOW, disagreement)
        action = decide_turn_action(state, entropy, len(ranked), low=clarify_low)

        response: dict = {"message": "", "ask_attribute": None, "recommendations": []}
        if ranked:
            response["recommendations"] = [{"parent_asin": c["parent_asin"]} for c in ranked[:top_k]]

        excluded = set(state.slots.keys()) | state.exhausted_attributes
        if action in ("ask", "both"):
            attr = select_best_question(ranked, excluded, ATTRIBUTE_ENUM,
                                         utility_fn=lambda a: utility_multiplier(state, a))
            if attr:
                response["ask_attribute"] = attr
                response["message"] = phrase_question(attr, ranked)
                state.last_asked_attribute = attr
                # CORRECTED per Phase 2 codex review (finding 1): snapshot the pre-rerank-cap pool
                # (`candidates`), not `ranked` (capped at rerank_depth, usually 50) -- see the
                # matching comment at the reward-closing site above.
                state.pool_size_at_ask = len(candidates)
            else:
                action = "commit"  # nothing productive left to ask -- fall through to commit phrasing

        if action == "commit" or not response["message"]:
            response["message"] = phrase_recommendation(ranked[:top_k])

        # CORRECTED per codex review: this used to be recorded right after decide_turn_action(),
        # before the "nothing productive to ask" fallback above could downgrade "ask"/"both" to
        # "commit" -- the trace would then disagree with the actual emitted action/response.
        # Recording after fallback resolution means the trace always matches what was really sent.
        record_action(action, entropy, state.turns_remaining, trace)
        log_turn_rationale(session_id, turn, state, action, ranked[:3], trace)
        state.turn_count = turn
        return response
