"""Runs the organizer's local evaluator against our real agent and logs a
wiki/08_evaluation_log.md-ready row. Always regenerates the evaluator shim first (idempotent) so
this script alone is the "one command to run" the reproducibility docs need.

Usage: python tools/run_eval.py [--variant "label for this run"]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTICIPANT_REPO = REPO_ROOT / "external" / "techjam-conversational-search"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="dev run")
    args = parser.parse_args()

    subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "install_shim.py")], check=True, cwd=REPO_ROOT)

    result = subprocess.run(
        [sys.executable, "-m", "evaluator.local_evaluator"],
        cwd=PARTICIPANT_REPO,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    results_path = PARTICIPANT_REPO / "results.json"
    data = json.loads(results_path.read_text(encoding="utf-8"))
    print(f"\n=== {args.variant} ===")
    print(f"HitRate@10 = {data['hit_rate_at_10']}")
    print(f"MRR = {data['mrr']}")
    print(f"MTTC = {data['mttc']}")
    print(f"Efficiency = {data['efficiency']}")
    print(f"TechnicalScore = {data['recommended_technical_score']}")
    print("\nScenario breakdown:")
    for scenario, metrics in data["scenario_metrics"].items():
        print(f"  {scenario}: {metrics}")


if __name__ == "__main__":
    main()
