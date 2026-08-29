"""Phase 3.5: uncertainty calibration check -- does the entropy signal actually correlate with
real hit-rate outcomes? Cheap, no new agent code: runs the evaluator once with per-turn logging
enabled, then joins the turn log against the evaluator's own results by ORDER (both iterate the
same `samples` list sequentially and single-threaded -- see local_evaluator.py's `evaluate()` --
so the Nth distinct session_id in the turn log corresponds to the Nth session in results["sessions"];
there is no shared ID, since the evaluator generates a fresh random session_id per run and never
exposes sample_id to the Agent).

Usage: python tools/calibration_check.py [--dataset data/public_set.jsonl]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTICIPANT_REPO = REPO_ROOT / "external" / "techjam-conversational-search"


def main() -> None:
    dataset = sys.argv[sys.argv.index("--dataset") + 1] if "--dataset" in sys.argv else "data/public_set.jsonl"
    log_path = PARTICIPANT_REPO / "_calibration_turn_log.jsonl"
    results_path = PARTICIPANT_REPO / "_calibration_results.json"
    if log_path.exists():
        log_path.unlink()

    env = dict(os.environ)
    env["COPILOT_TURN_LOG"] = str(log_path)

    subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "install_shim.py")], check=True,
                    cwd=REPO_ROOT, env=env)
    result = subprocess.run(
        [sys.executable, "-m", "evaluator.local_evaluator", "--dataset", dataset,
         "--output", str(results_path.name)],
        cwd=PARTICIPANT_REPO, capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    sessions = json.loads(results_path.read_text(encoding="utf-8"))["sessions"]

    # Last COMMIT-action turn per session_id, in first-appearance order.
    last_commit_entropy: "OrderedDict[str, float]" = OrderedDict()
    with log_path.open(encoding="utf-8") as fh:
        for line in fh:
            entry = json.loads(line)
            sid = entry["session_id"]
            if sid not in last_commit_entropy:
                last_commit_entropy[sid] = None
            if entry["action"] in ("commit", "both"):
                last_commit_entropy[sid] = entry["pool_entropy"]

    session_ids = list(last_commit_entropy.keys())
    if len(session_ids) != len(sessions):
        print(f"WARNING: turn log has {len(session_ids)} sessions, results has {len(sessions)} -- "
              "order-based join is unsafe, aborting.", file=sys.stderr)
        raise SystemExit(1)

    buckets = {"low (0.0-0.4)": [], "mid (0.4-0.7)": [], "high (0.7-1.0)": []}
    for sid, outcome in zip(session_ids, sessions):
        entropy = last_commit_entropy[sid]
        if entropy is None:
            continue
        key = "low (0.0-0.4)" if entropy < 0.4 else "mid (0.4-0.7)" if entropy < 0.7 else "high (0.7-1.0)"
        buckets[key].append(outcome["hit"])

    print(f"\n=== Uncertainty calibration check ({len(session_ids)} sessions, dataset={dataset}) ===")
    print("(well-calibrated = hit rate should DECREASE as commit-time entropy increases)")
    for key, hits in buckets.items():
        n = len(hits)
        rate = sum(hits) / n if n else float("nan")
        print(f"  {key}: n={n:3d}  hit_rate={rate:.4f}")


if __name__ == "__main__":
    main()
