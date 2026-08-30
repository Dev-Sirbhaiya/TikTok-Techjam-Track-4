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
# Transient, gitignored -- NOT the pre-registered train/validation split (that's SPLIT_PATH above).
# Records the most recent --split training run's exact candidate set, so --split validation can
# verify it's evaluating one of THOSE already-decided candidates, not a fresh one chosen after
# seeing a prior validation result -- see main()'s CORRECTED comment below.
LAST_TRAINING_RUN_PATH = REPO_ROOT / "tools" / "_last_training_run.json"

ENV_VAR_BY_KEY = {
    "CLARIFY_BASE_LOW": "COPILOT_CLARIFY_BASE_LOW",
    "CLARIFY_MIN_POOL_TO_BOTHER": "COPILOT_CLARIFY_MIN_POOL_TO_BOTHER",
    "CLARIFY_NO_ASK_AFTER_TURN": "COPILOT_CLARIFY_NO_ASK_AFTER_TURN",
    "VOI_DISAGREEMENT_WEIGHT": "COPILOT_VOI_DISAGREEMENT_WEIGHT",
    "NEG_BOOST_WEIGHT": "COPILOT_NEG_BOOST_WEIGHT",
    "METADATA_RRF_WEIGHT": "COPILOT_METADATA_RRF_WEIGHT",
    "EXTENDED_HARD_FILTER_ATTRS": "COPILOT_EXTENDED_HARD_FILTER_ATTRS",
    "ENABLE_PROFILE_SEEDING": "COPILOT_ENABLE_PROFILE_SEEDING",
    "ENABLE_QUALITY_BOOST": "COPILOT_ENABLE_QUALITY_BOOST",
    "QUALITY_BOOST_WEIGHT": "COPILOT_QUALITY_BOOST_WEIGHT",
    "ENABLE_CROSS_ENCODER_ENSEMBLE": "COPILOT_ENABLE_CROSS_ENCODER_ENSEMBLE",
    "ENABLE_BM25F": "COPILOT_ENABLE_BM25F",
    "BM25_RRF_WEIGHT": "COPILOT_BM25_RRF_WEIGHT",
    "DENSE_RRF_WEIGHT": "COPILOT_DENSE_RRF_WEIGHT",
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
    # CORRECTED (self-caught, 2026-08-30): agent.py's _build_llm_client() calls load_dotenv(),
    # which reads .env from disk regardless of this subprocess's own environment -- every ablation
    # here was silently exercising the optional LLM booster whenever a real ANTHROPIC_API_KEY
    # happened to be present in .env (which it has been for most of this session). This tool's
    # entire purpose is measuring the GUARANTEED path that ablation decisions get shipped on
    # (D-LLM-TIER: the organizer provides no hosted credentials) -- an ablation contaminated by the
    # optional booster is not measuring what it claims to. load_dotenv()'s default override=False
    # means setting this to an empty string here is enough to block .env's value.
    env["ANTHROPIC_API_KEY"] = ""

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
    # CORRECTED per codex review (2026-08-30): this used to let --split validation evaluate and
    # rank an arbitrary number of candidates together, which lets validation results influence
    # which candidate looks best -- exactly the "peeking" 10_PRE_REGISTRATION.md's train/validation
    # split exists to prevent (training proposes changes; validation only accepts/rejects the
    # single already-decided winner). A multi-candidate validation run was actually exercised
    # several times this session; see wiki/03_design_log.md's 2026-08-30 audit entry for the
    # honest accounting of which conclusions were and weren't affected. Now hard-enforced: at
    # most one candidate may be evaluated per --split validation invocation.
    if args.split == "validation" and len(candidates) > 1:
        raise SystemExit(
            f"Refusing to evaluate {len(candidates)} candidates against the validation split in "
            "one run -- this lets validation results influence which candidate looks best, "
            "violating 10_PRE_REGISTRATION.md's train/validation discipline. Validate exactly one "
            "already-decided candidate at a time (plus, if needed, a separate single baseline run "
            "to compare against)."
        )
    # CORRECTED per codex review (2026-08-30, second round): the one-candidate-per-run guard above
    # only prevents peeking WITHIN a single validation invocation -- nothing stopped running
    # validation on candidate A, then in a SEPARATE invocation running validation on candidate B,
    # and keeping whichever validation score happened to be better. That's the same peeking the
    # guard exists to prevent, just spread across two runs instead of one. Now enforced: a
    # validation run must name a candidate that actually appeared in the most recent training run
    # (persisted to LAST_TRAINING_RUN_PATH, gitignored/transient) -- the training step proposes,
    # this step only accepts or rejects the training-selected candidate, never a fresh choice made
    # after seeing how a prior candidate scored on validation.
    if args.split == "validation":
        if not LAST_TRAINING_RUN_PATH.exists():
            raise SystemExit(
                "No recorded --split training run found (tools/_last_training_run.json missing). "
                "Run --split training first so this candidate is on record as training-proposed, "
                "then validate it -- never validate a candidate that wasn't proposed by a training run."
            )
        last_training = json.loads(LAST_TRAINING_RUN_PATH.read_text(encoding="utf-8"))
        (name, overrides), = candidates.items()
        if last_training.get("candidates", {}).get(name) != overrides:
            raise SystemExit(
                f"Refusing to validate {name!r}: it does not match any candidate from the most "
                "recent --split training run (tools/_last_training_run.json). Re-run --split "
                "training with this exact candidate first -- validation may only confirm or reject "
                "a candidate the training step already proposed, never a fresh choice."
            )

    results = [run_one(args.split, name, overrides) for name, overrides in candidates.items()]
    results.sort(key=lambda r: r["technical_score"], reverse=True)

    if args.split == "training":
        LAST_TRAINING_RUN_PATH.write_text(json.dumps({"candidates": candidates}, indent=2), encoding="utf-8")

    print(f"\n=== Phase 3.1 tuning results ({args.split} split) ===")
    for r in results:
        print(f"{r['name']:>24s}  TechnicalScore={r['technical_score']:.6f}  "
              f"HitRate@10={r['hit_rate_at_10']:.4f}  MRR={r['mrr']:.6f}  MTTC={r['mttc']:.4f}  "
              f"overrides={r['overrides']}")


if __name__ == "__main__":
    main()
