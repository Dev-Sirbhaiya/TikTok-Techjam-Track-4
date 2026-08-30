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


_PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # .../submission (or repo root in dev)


def resolve_data_asset(cwd_relative: Path) -> Path:
    """Resolves a bundled data asset (e.g. the catalog embedding cache), checking the
    process's cwd-relative path FIRST (dev convenience -- the evaluator's own cwd during local
    iteration) and the package-relative path SECOND (the actual submission scenario, where the
    official harness's cwd is unknown/uncontrolled -- self-caught via codex review, 2026-08-30:
    a bare cwd-relative path silently missed the bundled cache whenever the importing process's
    cwd wasn't the package root, defeating the entire point of bundling it). Returns the
    cwd-relative path unchanged if NEITHER location has the file yet (first-ever compute, which
    then saves to the cwd-relative path as before)."""
    if cwd_relative.exists():
        return cwd_relative
    package_relative = _PACKAGE_ROOT / cwd_relative
    if package_relative.exists():
        return package_relative
    return cwd_relative
