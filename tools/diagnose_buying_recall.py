"""Diagnostic (not scored-path code): for every session, measures whether the hidden target
`parent_asin` ever reaches the fused/filtered candidate pool (`retrieve_candidates`'s output,
before the rerank-depth cap) versus whether it ever reaches the final top-10 recommendations.

Why this exists: every prior attempt at closing the Buying-track gap (query nudge, weighted RRF,
rerank-depth widening, slate hedging, lookahead question selection -- see wiki/08_evaluation_log.md)
started from a hypothesized *fix* and ablated it. None of them first measured whether the gap is a
retrieval-recall problem (target never in the pool at all -- no amount of reranking can fix that)
or a ranking problem (target reaches the pool but never gets reranked into the top 10). This
monkeypatches `retrieve_candidates` at the point `agent.py` calls it (no scored file is edited) to
record pool membership per turn, then replays the real simulator loop.

This is pure measurement, not a tuned/selected change -- safe to run against the full 200-session
set (no train/validation split concern; nothing here is being optimized against the result).

Usage: python tools/diagnose_buying_recall.py [--scenario buying]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import uuid
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTICIPANT_REPO = REPO_ROOT / "external" / "techjam-conversational-search"
MAX_TURNS = 10
TOP_K = 10


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default=None,
                         choices=["buying", "browsing", "intent_override", "boundary"])
    parser.add_argument("--no-hard-filter", action="store_true",
                         help="Force route_retrieval_breadth() to always return False, isolating "
                              "whether the hard filter itself (vs. underlying BM25/dense/metadata "
                              "recall) is responsible for targets never reaching the pool.")
    args = parser.parse_args()

    subprocess.run([sys.executable, str(REPO_ROOT / "tools" / "install_shim.py")], check=True, cwd=REPO_ROOT)
    os.chdir(PARTICIPANT_REPO)  # see tools/trace_session.py's comment: this is where the embedding cache lives
    sys.path.insert(0, str(PARTICIPANT_REPO))

    from evaluator.local_evaluator import (  # noqa: E402
        catalog_index, coarse_category, customer_reply, initial_message,
        load_jsonl, materialize_hidden_fields, normalize_recommendations,
    )
    from copilot import agent as agent_module  # noqa: E402
    from starter.agent import Agent  # noqa: E402

    real_retrieve = agent_module.retrieve_candidates
    pool_ids_this_turn: list[str] = []

    def spy(*call_args, **call_kwargs):
        candidates, disagreement = real_retrieve(*call_args, **call_kwargs)
        pool_ids_this_turn[:] = [c["parent_asin"] for c in candidates]
        return candidates, disagreement

    agent_module.retrieve_candidates = spy
    if args.no_hard_filter:
        agent_module.route_retrieval_breadth = lambda buying_intent_score, trace: False

    catalog_ids, categories, products = catalog_index(PARTICIPANT_REPO / "data" / "catalog.jsonl")
    samples = load_jsonl(PARTICIPANT_REPO / "data" / "public_set.jsonl")
    if args.scenario:
        samples = [s for s in samples if s["scenario_type"] == args.scenario]

    agent = Agent(str(PARTICIPANT_REPO / "data" / "catalog.jsonl"))
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {
        "total": 0, "hit_top10": 0, "in_pool_never_top10": 0, "never_in_pool": 0,
    })

    for sample in samples:
        scenario = sample["scenario_type"]
        session_id = f"diag_{uuid.uuid4().hex}"
        agent.reset(session_id, sample["user_profile"])
        target = str(sample["ground_truth"]["parent_asin"])
        card, behavior = materialize_hidden_fields(sample, products)
        effective_sample = {**sample, "intent_card": card, "behavior": behavior}
        disclosed: set[str] = set()
        boundary_used = False
        override_applied = scenario != "intent_override"
        user_message = initial_message(effective_sample, coarse_category(categories.get(target, [])), disclosed)

        ever_in_pool = False
        hit = False
        for turn in range(1, MAX_TURNS + 1):
            pool_ids_this_turn.clear()
            response = agent.respond(session_id, user_message, turn, TOP_K)
            if target in pool_ids_this_turn:
                ever_in_pool = True
            ranked = normalize_recommendations(response.get("recommendations"), catalog_ids)
            if override_applied and target in ranked:
                hit = True
                break
            if turn == MAX_TURNS:
                break
            override = effective_sample.get("behavior", {}).get("override") or {}
            if not override_applied and turn + 1 == int(override.get("turn", 3)):
                override_applied = True
                new_value = str(override.get("new_value", ""))
                if new_value:
                    disclosed.add(new_value)
                user_message = str(override.get("message", "Actually, please ignore my earlier preference."))
            else:
                user_message, boundary_used = customer_reply(
                    effective_sample, response.get("ask_attribute"), disclosed, boundary_used
                )

        c = counts[scenario]
        c["total"] += 1
        if hit:
            c["hit_top10"] += 1
        elif ever_in_pool:
            c["in_pool_never_top10"] += 1
        else:
            c["never_in_pool"] += 1

    print(f"{'scenario':<16} {'n':>4} {'hit@10':>8} {'in_pool_but_not_top10':>22} {'never_in_pool':>14}")
    for scenario in sorted(counts):
        c = counts[scenario]
        n = c["total"]
        print(f"{scenario:<16} {n:>4} "
              f"{c['hit_top10']:>4} ({100*c['hit_top10']/n:4.1f}%) "
              f"{c['in_pool_never_top10']:>10} ({100*c['in_pool_never_top10']/n:4.1f}%) "
              f"{c['never_in_pool']:>6} ({100*c['never_in_pool']/n:4.1f}%)")


if __name__ == "__main__":
    main()
