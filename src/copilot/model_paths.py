"""Resolves model paths: prefer a bundled local copy (required for the actual submission, since
official scoring may run with network access disabled -- docs/submission_rules.md, D-LATENCY),
fall back to the bare Hugging Face model ID for local dev iteration (this machine's HF cache
handles it transparently, no bundling needed while iterating).

The bundled path is resolved relative to THIS file's own location, not the process cwd, so it
works identically whether this package lives at `src/copilot/` (dev) or `submission/src/copilot/`
(the packaged submission) -- both have a sibling `models/` directory two levels up from
`copilot/model_paths.py`'s own parent (`copilot/` -> `src/` -> repo-or-submission root -> `models/`).
"""
from __future__ import annotations

from pathlib import Path

_BUNDLED_MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def resolve(bundled_dirname: str, hf_model_id: str) -> str:
    """Returns the bundled local path if it exists, else the bare HF model ID."""
    bundled = _BUNDLED_MODELS_DIR / bundled_dirname
    return str(bundled) if bundled.is_dir() else hf_model_id
