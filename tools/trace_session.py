"""Runs ONE public-set session through the real agent and prints a readable per-turn trace —
built for the Phase 5.4 demo video (see docs/DEMO_VIDEO_SCRIPT.md), not a scored-path tool.

Reuses the organizer's own simulation functions (initial_message, customer_reply,
materialize_hidden_fields) from evaluator/local_evaluator.py so the simulated customer behaves
identically to a real scored run — only the printing is new. Regenerates the evaluator shim first,
same as tools/run_eval.py, so this is runnable standalone.

Usage:
  python tools/trace_session.py                          # first "buying" scenario in the public set
  python tools/trace_session.py --sample-id <sample_id>   # a specific session
  python tools/trace_session.py --scenario browsing       # first session of a given scenario
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTICIPANT_REPO = REPO_ROOT / "external" / "techjam-conversational-search"

MAX_TURNS = 10
TOP_K = 10


def _pick_sample(samples: list[dict], sample_id: str | None, scenario: str | None) -> dict:
    if sample_id:
        for s in samples:
            if str(s["sample_id"]) == sample_id:
                return s
        raise SystemExit(f"No sample with sample_id={sample_id!r} in the public set.")
    if scenario:
        for s in samples:
            if s["scenario_type"] == scenario:
                return s
        raise SystemExit(f"No sample with scenario_type={scenario!r} in the public set.")
    for s in samples:
        if s["scenario_type"] == "buying":
            return s
    return samples[0]


def _last_turn_rationale(turn_log_path: Path) -> dict | None:
    if not turn_log_path.exists():
        return None
    with turn_log_path.open(encoding="utf-8") as fh:
        lines = [line for line in fh if line.strip()]
    return json.loads(lines[-1]) if lines else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-id", default=None)
    parser.add_argument("--scenario", default=None, choices=["buying", "browsing", "intent_override", "boundary"])
    args = parser.parse_args()

    subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "install_shim.py")], check=True, cwd=REPO_ROOT)

    # CORRECTED per codex review (2026-08-30): the demo script's narration references the logged
    # entropy value and orchestration decisions, but this tool only ever printed message/
    # ask_attribute/recommendations -- those other fields exist only in agent.py's per-turn
    # turn_log.jsonl, invisible to someone watching just this terminal output while recording. Point
    # COPILOT_TURN_LOG at a private temp file (set before importing copilot.agent, which reads this
    # env var at import time) and print each turn's entry inline instead.
    turn_log_path = Path(tempfile.gettempdir()) / f"trace_turn_log_{uuid.uuid4().hex}.jsonl"
    os.environ["COPILOT_TURN_LOG"] = str(turn_log_path)

    # tools/run_eval.py invokes the evaluator with cwd=PARTICIPANT_REPO, so that's where
    # CatalogIndex's embedding cache actually lives on disk (data/_catalog_embeddings.npz,
    # cwd-relative) -- self-caught while first testing this script: constructing Agent from the
    # repo root's cwd instead missed that cache entirely and silently launched a ~14.5-minute
    # from-scratch encode of all 50,000 catalog items. Match the eval convention exactly.
    os.chdir(PARTICIPANT_REPO)
    sys.path.insert(0, str(PARTICIPANT_REPO))
    from evaluator.local_evaluator import (  # noqa: E402
        catalog_index, coarse_category, customer_reply, initial_message,
        load_jsonl, materialize_hidden_fields, normalize_recommendations,
    )
    from starter.agent import Agent  # noqa: E402

    catalog_ids, categories, products = catalog_index(PARTICIPANT_REPO / "data" / "catalog.jsonl")
    samples = load_jsonl(PARTICIPANT_REPO / "data" / "public_set.jsonl")
    sample = _pick_sample(samples, args.sample_id, args.scenario)

    print(f"=== session: sample_id={sample['sample_id']}  scenario={sample['scenario_type']} ===\n")

    agent = Agent(str(PARTICIPANT_REPO / "data" / "catalog.jsonl"))
    session_id = f"trace_{uuid.uuid4().hex}"
    agent.reset(session_id, sample["user_profile"])

    target = str(sample["ground_truth"]["parent_asin"])
    card, behavior = materialize_hidden_fields(sample, products)
    effective_sample = {**sample, "intent_card": card, "behavior": behavior}
    disclosed: set[str] = set()
    boundary_used = False
    override_applied = sample["scenario_type"] != "intent_override"
    user_message = initial_message(effective_sample, coarse_category(categories.get(target, [])), disclosed)

    print(f"(hidden target for this session: {target} -- never seen by the agent)\n")

    for turn in range(1, MAX_TURNS + 1):
        print(f"--- turn {turn} ---")
        print(f"customer: {user_message}")
        response = agent.respond(session_id, user_message, turn, TOP_K)
        ranked = normalize_recommendations(response.get("recommendations"), catalog_ids)
        print(f"agent:    {response.get('message', '')}")
        if response.get("ask_attribute"):
            print(f"          [asking about: {response['ask_attribute']}]")
        print(f"          [top {min(3, len(ranked))} of {len(ranked)} recommendations: {ranked[:3]}]")
        rationale = _last_turn_rationale(turn_log_path)
        if rationale:
            print(f"          [pool entropy: {rationale.get('pool_entropy')}, "
                  f"buying_intent_score: {rationale.get('buying_intent_score')}]")
            for d in rationale.get("orchestration_decisions", []):
                print(f"          [orchestrator: {d.get('point')} -> {d.get('choice')} ({d.get('signal')})]")

        if override_applied and target in ranked:
            rank = ranked.index(target) + 1
            print(f"\n*** HIT on turn {turn}, rank {rank} (reciprocal rank {1.0/rank:.3f}) ***")
            break
        if turn == MAX_TURNS:
            print("\n*** MISS: target not found within 10 turns ***")
            break

        override = effective_sample.get("behavior", {}).get("override") or {}
        if not override_applied and turn + 1 == int(override.get("turn", 3)):
            override_applied = True
            new_value = str(override.get("new_value", ""))
            if new_value:
                disclosed.add(new_value)
            user_message = str(override.get("message", "Actually, please ignore my earlier preference."))
            print("\n          [scripted intent override fires next turn regardless of the agent's ask]")
        else:
            user_message, boundary_used = customer_reply(
                effective_sample, response.get("ask_attribute"), disclosed, boundary_used
            )
        print()


if __name__ == "__main__":
    main()
