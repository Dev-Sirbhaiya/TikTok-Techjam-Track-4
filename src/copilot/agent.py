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
from .overgenerality import score_entropy, select_best_question
from .phrasing import phrase_question, phrase_recommendation
from .preference import preference_boost, update_preference_vectors
from .ranker import rerank
from .rejection_memory import apply_rejection, apply_rejection_filter, detect_rejection_signal
from .retrieval import retrieve_candidates
from .state import DialogState
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

        rejection_signal = detect_rejection_signal(user_message, self.gazetteer)
        if rejection_signal:
            apply_rejection(state, rejection_signal)

        track = route_intent(user_message, state.slots, self.gazetteer)
        state.buying_intent_score = 0.8 if track == "buying" else 0.3

        query_text = " ".join(state.accumulated_terms) or user_message
        candidates = retrieve_candidates(query_text, state.slots, state.buying_intent_score, self.catalog_index)
        candidates = apply_rejection_filter(candidates, state)

        turn_embedding = self.catalog_index.encode_text(query_text)
        signal = "negative" if rejection_signal else ("positive" if extraction.get("slot_updates") else None)
        if signal:
            update_preference_vectors(state, turn_embedding, signal)
        for c in candidates:
            emb = self.catalog_index.embedding_for(c["parent_asin"])
            c["_score"] += preference_boost(emb, state) - c.get("_rejection_penalty", 0.0) * 0.05

        entropy = score_entropy([c["_score"] for c in candidates[:10]]) if candidates else 0.0
        state.pool_entropy = entropy

        ranked = rerank(candidates[:50], state, state.accumulated_terms)
        state.candidate_pool = [c["parent_asin"] for c in ranked]

        action = decide_turn_action(state, entropy, len(ranked))

        response: dict = {"message": "", "ask_attribute": None, "recommendations": []}
        if ranked:
            response["recommendations"] = [{"parent_asin": c["parent_asin"]} for c in ranked[:top_k]]

        excluded = set(state.slots.keys()) | state.exhausted_attributes
        if action in ("ask", "both"):
            attr = select_best_question(ranked, excluded, ATTRIBUTE_ENUM)
            if attr:
                response["ask_attribute"] = attr
                response["message"] = phrase_question(attr, ranked)
                state.last_asked_attribute = attr
            else:
                action = "commit"  # nothing productive left to ask -- fall through to commit phrasing

        if action == "commit" or not response["message"]:
            response["message"] = phrase_recommendation(ranked[:top_k])

        log_turn_rationale(session_id, turn, state, action, ranked[:3])
        state.turn_count = turn
        return response
