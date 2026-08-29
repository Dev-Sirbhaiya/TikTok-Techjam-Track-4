"""Three-tier rejection confidence: explicit -> hard (drop), comparative/vague -> soft (penalize),
implicit -> soft/weak (generic negative, never an inferred attribute cause).

See implementation/04_SYSTEM_DESIGN.md and implementation/06_DECISION_LOG.md D5.
"""
from __future__ import annotations

import re

_NEGATION_RE = re.compile(
    r"\b(don'?t|do not|not|no|never|hate|dislike|avoid|too expensive|too pricey)\b", re.I)
_COMPARATIVE_RE = re.compile(
    r"\b(less|more|instead of|rather than|not as|prefer .* over)\b", re.I)


def detect_rejection_signal(user_message: str, gazetteer: dict) -> dict | None:
    lowered = user_message.lower()
    if not _NEGATION_RE.search(lowered):
        return None

    for color in gazetteer.get("colors", ()):
        if re.search(rf"\b(?:don'?t|not|no|hate|dislike|avoid)\b.{{0,20}}\b{re.escape(color)}\b", lowered):
            sig_type = "comparative" if _COMPARATIVE_RE.search(lowered) else "explicit"
            return {"type": sig_type, "attribute": "color", "value": color}
    for material in gazetteer.get("materials", ()):
        if re.search(rf"\b(?:don'?t|not|no|hate|dislike|avoid)\b.{{0,20}}\b{re.escape(material)}\b", lowered):
            sig_type = "comparative" if _COMPARATIVE_RE.search(lowered) else "explicit"
            return {"type": sig_type, "attribute": "material", "value": material}
    if "too expensive" in lowered or "too pricey" in lowered:
        return {"type": "explicit", "attribute": "budget", "value": "current_price_band"}

    # Negation present but no specific attribute matched -- implicit/vague. Per D5: do NOT invent
    # an attribute cause; log a generic weak negative on the last-shown top candidate only.
    return {"type": "implicit", "attribute": None, "value": None}


def apply_rejection(state, signal: dict) -> None:
    sig_type, attr, value = signal["type"], signal.get("attribute"), signal.get("value")
    if sig_type == "explicit" and attr:
        state.rejected_hard.setdefault(attr, [])
        if value not in state.rejected_hard[attr]:
            state.rejected_hard[attr].append(value)
        state.rejected_soft.pop(attr, None)
    elif sig_type in ("comparative", "vague") and attr:
        state.rejected_soft.setdefault(attr, [])
        if value not in state.rejected_soft[attr]:
            state.rejected_soft[attr].append(value)
        state.rejected_soft_confidence[attr] = 0.5
    elif sig_type == "implicit":
        last_shown = state.candidate_pool[0] if state.candidate_pool else None
        state.rejected_soft.setdefault("_generic", [])
        state.rejected_soft["_generic"].append(last_shown)
        state.rejected_soft_confidence["_generic"] = 0.2


def _matches_hard_rejection(candidate: dict, rejected_hard: dict) -> bool:
    attrs = candidate.get("attributes", {})
    for attr, values in rejected_hard.items():
        if attrs.get(attr) in values:
            return True
    return False


def _soft_rejection_penalty(candidate: dict, rejected_soft: dict, confidence: dict) -> float:
    attrs = candidate.get("attributes", {})
    penalty = 0.0
    for attr, values in rejected_soft.items():
        if attr == "_generic":
            if candidate.get("parent_asin") in values:
                penalty += confidence.get(attr, 0.2)
            continue
        if attrs.get(attr) in values:
            penalty += confidence.get(attr, 0.5)
    return penalty


def apply_rejection_filter(candidates: list[dict], state) -> list[dict]:
    out = []
    for c in candidates:
        if _matches_hard_rejection(c, state.rejected_hard):
            continue
        c["_rejection_penalty"] = _soft_rejection_penalty(c, state.rejected_soft, state.rejected_soft_confidence)
        out.append(c)
    return out
