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
    package-relative path FIRST (the verified, bundled asset -- trustworthy regardless of the
    importing process's cwd) and the cwd-relative path SECOND (dev convenience only). Returns the
    cwd-relative path unchanged if NEITHER location has the file yet (first-ever compute, which
    then saves to the cwd-relative path as before).

    CORRECTED per codex review, 2026-08-30 (second round): the original order checked cwd-relative
    FIRST -- if the official harness's cwd happened to already contain *any* file at that relative
    path (stale, or from an unrelated prior run), it would be silently preferred over the verified
    bundled asset, up to and including a same-shaped-but-wrong cache silently corrupting retrieval
    with no error at all. The bundled, package-relative asset is the one this project actually
    verified end-to-end (see the offline-reproducibility entries in wiki/08_evaluation_log.md); it
    should always win when present, not lose to whatever happens to already exist in an unknown
    harness cwd."""
    package_relative = _PACKAGE_ROOT / cwd_relative
    if package_relative.exists():
        return package_relative
    if cwd_relative.exists():
        return cwd_relative
    return cwd_relative
