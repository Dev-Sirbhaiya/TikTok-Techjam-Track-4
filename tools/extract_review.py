"""Recovers a codex review's actual verdict from its session transcript, for when the redirected
`codex exec review ... > file.raw.txt` output looks incomplete or inconclusive.

Why this exists (self-caught, 2026-08-30 -- see wiki/03_design_log.md's "recovered reviews" entry
and CLAUDE.md's protocol note): `codex exec review`'s final verdict message can render through a
channel that plain stdout redirection doesn't reliably capture, even when the review fully
completed with real findings -- a short .raw.txt (banner + one exec call, nothing else) is NOT
reliable evidence a review found nothing. The actual verdict is always present in the session's
JSONL transcript under CODEX_HOME (~/.codex/sessions/**/*<session-id>*.jsonl, findable from the
"session id:" line in the raw.txt banner) as an `ExitedReviewMode` item's `review_output` field.

Usage: python tools/extract_review.py <path-to-session-rollout.jsonl>
Prints the review_output JSON (findings, overall_correctness, overall_explanation) if found.
"""
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        payload = entry.get("payload", {})
        item = payload.get("item", {})
        if item.get("type") == "ExitedReviewMode":
            out = item["review_output"]
            print(json.dumps(out, indent=2))
