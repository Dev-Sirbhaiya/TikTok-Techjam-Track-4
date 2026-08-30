"""Runs the organizer's local evaluator against our real agent and logs a
wiki/08_evaluation_log.md-ready row. Always regenerates the evaluator shim first (idempotent) so
this script alone is the "one command to run" the reproducibility docs need.

CORRECTED (self-caught, 2026-08-30): `agent.py`'s `_build_llm_client()` calls `load_dotenv()`,
which reads any local `.env` file from disk regardless of what this script's own environment looks
like -- meaning every run of this tool was silently using the optional LLM booster whenever a real
`ANTHROPIC_API_KEY` happened to be present in `.env` (which it has been for most of this session),
even though this tool's whole purpose is measuring the GUARANTEED path (D-LLM-TIER: the organizer
provides no hosted credentials). `load_dotenv()`'s default `override=False` means explicitly
setting the env var to an empty string here is enough to block the .env file's value from taking
effect. Pass --with-llm-booster to deliberately measure the optional ceiling instead.

Usage: python tools/run_eval.py [--variant "label for this run"] [--with-llm-booster]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTICIPANT_REPO = REPO_ROOT / "external" / "techjam-conversational-search"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="dev run")
    parser.add_argument("--with-llm-booster", action="store_true",
                         help="Deliberately allow .env's ANTHROPIC_API_KEY through, to measure "
                              "the optional ceiling instead of the guaranteed path.")
    args = parser.parse_args()

    subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "install_shim.py")], check=True, cwd=REPO_ROOT)

    env = dict(os.environ)
    if not args.with_llm_booster:
        env["ANTHROPIC_API_KEY"] = ""

    result = subprocess.run(
        [sys.executable, "-m", "evaluator.local_evaluator"],
        cwd=PARTICIPANT_REPO,
        capture_output=True,
        text=True,
        env=env,
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
