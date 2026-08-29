"""Dialog state: the "context distillation" object every downstream module reads from.

See implementation/04_SYSTEM_DESIGN.md for the design rationale.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np


@dataclass
class DialogState:
    slots: dict[str, Any] = field(default_factory=dict)
    rejected_hard: dict[str, list[Any]] = field(default_factory=dict)
    rejected_soft: dict[str, list[Any]] = field(default_factory=dict)
    rejected_soft_confidence: dict[str, float] = field(default_factory=dict)

    pref_vector_pos: Optional[np.ndarray] = None
    pref_vector_neg: Optional[np.ndarray] = None

    buying_intent_score: float = 0.5
    turn_count: int = 0

    candidate_pool: list[str] = field(default_factory=list)
    pool_entropy: float = 1.0
    accumulated_terms: list[str] = field(default_factory=list)  # every turn's query terms, never reset

    override_history: list[dict] = field(default_factory=list)
    last_asked_attribute: Optional[str] = None
    exhausted_attributes: set[str] = field(default_factory=set)
    facet_utility_history: dict[str, float] = field(default_factory=dict)

    # Slot confidence tiers ("confirmed" never decays within a session; "inferred" decays after
    # SLOT_TTL_TURNS without reinforcement). See D-slot-decay in implementation/04_SYSTEM_DESIGN.md.
    slot_confidence: dict[str, str] = field(default_factory=dict)  # {"category": "confirmed"}
    slot_last_seen_turn: dict[str, int] = field(default_factory=dict)

    @property
    def turns_remaining(self) -> int:
        return 10 - self.turn_count

    def top_level_category(self) -> Optional[str]:
        return self.slots.get("category")
