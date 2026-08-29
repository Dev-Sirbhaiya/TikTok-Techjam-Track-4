"""Runs the evaluator against just the training or validation split (tools/session_split.json),
per implementation/10_PRE_REGISTRATION.md. Writes a filtered dataset file and reuses the
evaluator's own --dataset flag -- never modifies the evaluator itself.

Usage: python tools/run_eval_split.py --split training|validation [--variant "label"]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTICIPANT_REPO = REPO_ROOT / "external" / "techjam-conversational-search"
SESSIONS_PATH = PARTICIPANT_REPO / "data" / "public_set.jsonl"
SPLIT_PATH = REPO_ROOT / "tools" / "session_split.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["training", "validation"], required=True)
    parser.add_argument("--variant", default=None)
    args = parser.parse_args()
    variant = args.variant or f"{args.split} split"

    split = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    keep_ids = set(split[args.split])

    filtered_path = PARTICIPANT_REPO / "data" / f"_split_{args.split}.jsonl"
    with SESSIONS_PATH.open(encoding="utf-8") as src, filtered_path.open("w", encoding="utf-8") as dst:
        for line in src:
            line = line.strip()
            if line and json.loads(line)["sample_id"] in keep_ids:
                dst.write(line + "\n")

    subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "install_shim.py")], check=True, cwd=REPO_ROOT)
    result = subprocess.run(
        [sys.executable, "-m", "evaluator.local_evaluator", "--dataset", f"data/_split_{args.split}.jsonl",
         "--output", f"results_{args.split}.json"],
        cwd=PARTICIPANT_REPO, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    data = json.loads((PARTICIPANT_REPO / f"results_{args.split}.json").read_text(encoding="utf-8"))
    print(f"\n=== {variant} (n={data['sample_count']}) ===")
    print(f"HitRate@10 = {data['hit_rate_at_10']}")
    print(f"MRR = {data['mrr']}")
    print(f"MTTC = {data['mttc']}")
    print(f"Efficiency = {data['efficiency']}")
    print(f"TechnicalScore = {data['recommended_technical_score']}")
    for scenario, metrics in data["scenario_metrics"].items():
        print(f"  {scenario}: {metrics}")


if __name__ == "__main__":
    main()
