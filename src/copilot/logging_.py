"""Per-turn rationale logging. Cheap, high debugging value, feeds the Embedding Explorer's export
pipeline later (implementation/13_FRONTEND_VISUALIZATION.md). Not required by the competition spec.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_LOG_PATH = Path(os.environ.get("COPILOT_TURN_LOG", "turn_log.jsonl"))
_ENABLED = os.environ.get("COPILOT_DISABLE_LOGGING", "") == ""


def log_turn_rationale(session_id: str, turn: int, state, action: str, top_candidates: list[dict],
                        trace=None) -> None:
    if not _ENABLED:
        return
    entry = {
        "session_id": session_id,
        "turn": turn,
        "action": action,
        "buying_intent_score": round(state.buying_intent_score, 3),
        "pool_entropy": round(state.pool_entropy, 3),
        "slots": dict(state.slots),
        "rejected_hard": dict(state.rejected_hard),
        "top_candidates": [
            {"parent_asin": c.get("parent_asin"), "score": round(c.get("_score", 0.0), 5)}
            for c in top_candidates
        ],
        # Phase 1.4 (FR-8): named adaptive-orchestration decisions, so "Adaptive Orchestration" is
        # demonstrable from the log, not just implemented in code no one can point to.
        "orchestration_decisions": trace.decisions if trace is not None else [],
    }
    try:
        with _LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # logging must never break a turn
