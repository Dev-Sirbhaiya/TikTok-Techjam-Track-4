"""Natural-language message generation. `message` is not scored directly (only `ask_attribute` and
`recommendations` are), but must be a non-empty string per the contract -- keep it simple and honest.
"""
from __future__ import annotations

from .overgenerality import top_facet_values

_ATTRIBUTE_PROMPTS = {
    "category": "What category are you looking for?",
    "material": "Do you have a material preference?",
    "color": "Any color preference?",
    "size": "What size do you need?",
    "style": "Any particular style in mind?",
    "budget": "What's your budget?",
    "use_case": "What will you be using this for?",
    "feature": "Is there a specific feature that matters most to you?",
}


def phrase_question(attribute: str | None, candidates: list[dict]) -> str:
    if not attribute:
        return "Could you tell me a bit more about what you're looking for?"
    base = _ATTRIBUTE_PROMPTS.get(attribute, f"Do you have a preference for {attribute}?")
    values = top_facet_values(candidates, attribute, limit=3)
    if values:
        options = ", ".join(str(v) for v in values)
        return f"{base} I'm seeing options like {options}."
    return base


def phrase_recommendation(top_items: list[dict]) -> str:
    if not top_items:
        return "I couldn't find a strong match yet -- could you share a bit more detail?"
    n = len(top_items)
    return f"Here are {n} option{'s' if n != 1 else ''} I think you'll like, ranked by best match."
