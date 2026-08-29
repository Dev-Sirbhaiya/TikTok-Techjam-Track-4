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
VALIDATION_FRACTION = 0.2  # 40 of 200


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

    validation = sorted(sid for sid in sample_ids if split_key(sid) < VALIDATION_FRACTION)
    training = sorted(sid for sid in sample_ids if sid not in set(validation))

    OUT_PATH.write_text(json.dumps({
        "training": training,
        "validation": validation,
        "n_training": len(training),
        "n_validation": len(validation),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"training={len(training)} validation={len(validation)} -> {OUT_PATH}")


if __name__ == "__main__":
    main()
