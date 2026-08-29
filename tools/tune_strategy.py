"""Phase 3.1: SkillOpt-style offline strategy tuning -- rollout (run a candidate config against the
training split) -> score (read its TechnicalScore) -> edit (propose the next candidate) -> validate
(the single winner, once, against the held-out validation split it never touched).

Each candidate is a named dict of env-var overrides for src/copilot/strategy_config.py's constants
-- see that module for what each knob does. A fresh `python -m evaluator.local_evaluator` subprocess
per candidate means every rollout exercises the real end-to-end agent, not a cached re-score.

Usage: python tools/tune_strategy.py --split training --candidates candidates.json
       python tools/tune_strategy.py --split validation --candidates winner.json
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
SESSIONS_PATH = PARTICIPANT_REPO / "data" / "public_set.jsonl"
SPLIT_PATH = REPO_ROOT / "tools" / "session_split.json"

ENV_VAR_BY_KEY = {
    "CLARIFY_BASE_LOW": "COPILOT_CLARIFY_BASE_LOW",
    "CLARIFY_MIN_POOL_TO_BOTHER": "COPILOT_CLARIFY_MIN_POOL_TO_BOTHER",
    "CLARIFY_NO_ASK_AFTER_TURN": "COPILOT_CLARIFY_NO_ASK_AFTER_TURN",
    "VOI_DISAGREEMENT_WEIGHT": "COPILOT_VOI_DISAGREEMENT_WEIGHT",
    "NEG_BOOST_WEIGHT": "COPILOT_NEG_BOOST_WEIGHT",
}


def run_one(split: str, name: str, overrides: dict) -> dict:
    keep_ids = set(json.loads(SPLIT_PATH.read_text(encoding="utf-8"))[split])
    filtered_path = PARTICIPANT_REPO / "data" / f"_tune_{split}.jsonl"
    with SESSIONS_PATH.open(encoding="utf-8") as src, filtered_path.open("w", encoding="utf-8") as dst:
        for line in src:
            line = line.strip()
            if line and json.loads(line)["sample_id"] in keep_ids:
                dst.write(line + "\n")

    # CORRECTED per codex review: pop every managed var first, not just conditionally overwrite the
    # ones a candidate happens to set -- otherwise a COPILOT_* var already present in the invoking
    # shell (e.g. left over from an earlier manual debugging session) would silently leak into any
    # candidate that omits that key, including `baseline: {}`, and the leaked value wouldn't even
    # appear in the logged `overrides` dict -- an irreproducible winner reported as reproducible.
    env = dict(os.environ)
    for env_var in ENV_VAR_BY_KEY.values():
        env.pop(env_var, None)
    for key, value in overrides.items():
        env[ENV_VAR_BY_KEY[key]] = str(value)

    subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "install_shim.py")], check=True,
                    cwd=REPO_ROOT, env=env)
    result = subprocess.run(
        [sys.executable, "-m", "evaluator.local_evaluator", "--dataset", f"data/_tune_{split}.jsonl",
         "--output", f"results_tune_{split}.json"],
        cwd=PARTICIPANT_REPO, capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)

    data = json.loads((PARTICIPANT_REPO / f"results_tune_{split}.json").read_text(encoding="utf-8"))
    return {
        "name": name, "split": split, "overrides": overrides,
        "hit_rate_at_10": data["hit_rate_at_10"], "mrr": data["mrr"], "mttc": data["mttc"],
        "technical_score": data["recommended_technical_score"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["training", "validation"], required=True)
    parser.add_argument("--candidates", required=True, help="JSON file: {name: {KEY: value, ...}, ...}")
    args = parser.parse_args()

    candidates = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    results = [run_one(args.split, name, overrides) for name, overrides in candidates.items()]
    results.sort(key=lambda r: r["technical_score"], reverse=True)

    print(f"\n=== Phase 3.1 tuning results ({args.split} split) ===")
    for r in results:
        print(f"{r['name']:>24s}  TechnicalScore={r['technical_score']:.6f}  "
              f"HitRate@10={r['hit_rate_at_10']:.4f}  MRR={r['mrr']:.6f}  MTTC={r['mttc']:.4f}  "
              f"overrides={r['overrides']}")


if __name__ == "__main__":
    main()
