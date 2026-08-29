"""Buying vs. Browsing intent routing. Gazetteer hard-match first, embedding vote second, LLM
arbiter only on disagreement/low confidence and only if a client is configured (never required).

See implementation/04_SYSTEM_DESIGN.md and research/01_intent_routing.md.
"""
from __future__ import annotations

import re

_PRICE_HINT = re.compile(r"\b(under|below|less than|max(?:imum)?|budget)\b|\$\s?\d", re.I)


def gazetteer_hard_match(text: str, gazetteer: dict, slots: dict) -> bool:
    """A hard-constraint match = an explicit brand/size/price mention, OR an already-locked slot
    from a prior turn (buying intent, once established by a real constraint, doesn't need to be
    re-derived from scratch every turn -- see research/01's "carry accumulated state" Do)."""
    lowered = text.lower()
    if _PRICE_HINT.search(lowered):
        return True
    for brand in gazetteer.get("brands", ()):
        if brand and len(brand) > 2 and brand.lower() in lowered:
            return True
    if slots.get("budget_max") is not None or slots.get("brand"):
        return True
    return False


def route_intent(user_message: str, slots: dict, gazetteer: dict) -> str:
    """Returns "buying" or "browsing". No LLM call on the default path (NFR-2)."""
    if gazetteer_hard_match(user_message, gazetteer, slots):
        return "buying"
    # Cheap embedding-vote is deferred to when a dense encoder is available (catalog_index owns
    # that); Phase 0's default fallback below is a lightweight lexical heuristic that needs no
    # model at all, so intent routing never blocks on dense-encoder availability.
    lowered = user_message.lower()
    browsing_cues = ("still exploring", "just looking", "browsing", "ideas", "something for",
                      "not sure", "maybe", "any suggestions", "what do you have")
    if any(cue in lowered for cue in browsing_cues):
        return "browsing"
    # Slots already filled with specific values (color/material/size) without an explicit price/
    # brand signal still lean toward Buying -- a specific-enough query is transactional intent.
    specific_slot_keys = {"color", "material", "size", "style", "use_case"}
    if any(k in slots for k in specific_slot_keys):
        return "buying"
    return "browsing"
