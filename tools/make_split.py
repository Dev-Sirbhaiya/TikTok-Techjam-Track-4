"""Creates the deterministic 160/40 train/validation split over the 200 public dev sessions, per
implementation/10_PRE_REGISTRATION.md. Split by sample_id hash (stable across runs, not random),
written once and committed so it never silently changes.

Usage: python tools/make_split.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SESSIONS_PATH = REPO_ROOT / "external" / "techjam-conversational-search" / "data" / "public_set.jsonl"
OUT_PATH = REPO_ROOT / "tools" / "session_split.json"
N_VALIDATION = 40  # exactly 40 of 200, per implementation/10_PRE_REGISTRATION.md


def split_key(sample_id: str) -> float:
    digest = hashlib.sha256(sample_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def main() -> None:
    sample_ids = []
    with SESSIONS_PATH.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                sample_ids.append(json.loads(line)["sample_id"])

    # CORRECTED per codex review: thresholding the hash (< 0.2) only produces ~40 sessions in
    # expectation, not exactly 40 -- it produced 35/165 for the actual committed IDs, contradicting
    # the pre-registered 160/40 partition. Sort by the deterministic hash and take exactly the
    # first N_VALIDATION instead -- still fully deterministic, now exact.
    ranked = sorted(sample_ids, key=split_key)
    validation = sorted(ranked[:N_VALIDATION])
    training = sorted(ranked[N_VALIDATION:])

    OUT_PATH.write_text(json.dumps({
        "training": training,
        "validation": validation,
        "n_training": len(training),
        "n_validation": len(validation),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"training={len(training)} validation={len(validation)} -> {OUT_PATH}")


if __name__ == "__main__":
    main()
