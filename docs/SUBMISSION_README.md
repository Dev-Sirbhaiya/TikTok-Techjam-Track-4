# TechJam 2026 Track 4 — Conversational Shopping Copilot

A hybrid retrieval + dialog-state conversational agent over a frozen 50,000-product Amazon
`Clothing_Shoes_and_Jewelry` catalog. Built for TikTok TechJam 2026, Track 4.

## Approach, in one paragraph

Every turn: extract slot updates from free text (deterministic templates against the challenge's
own simulator, with a gazetteer fallback), route Buying-vs-Browsing intent, retrieve candidates via
BM25 + dense (`bge-small-en-v1.5`) + metadata search fused with Reciprocal Rank Fusion, rerank the
shortlist with a cross-encoder (`ms-marco-MiniLM-L-6-v2`), then decide ask-vs-commit from a
calibrated entropy gate over the fused/reranked score distribution. No LLM call is ever required —
the entire pipeline above runs on local, open-weight models bundled with this submission.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Requires Python 3.10+ (developed and tested on 3.13.7). No GPU required — both bundled models run
on CPU at the batch sizes this agent uses.

## Run command

```python
import sys
sys.path.insert(0, ".")
from agent import Agent

agent = Agent("path/to/catalog.jsonl")
agent.reset("session_1", user_profile={})
response = agent.respond("session_1", "I'm looking for a blue cotton shirt", turn=1, top_k=10)
```

Or, to run the organizer's own evaluator against this agent directly, point its `Agent` import at
this package (see the organizer's evaluator harness documentation for the exact invocation).

## Models, cost, and offline behavior

| Component | Model | Where it runs | Network required? |
|---|---|---|---|
| Dense retrieval | `BAAI/bge-small-en-v1.5` | local, CPU | **No** — bundled in `models/`, loaded from the local path directly |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` | local, CPU | **No** — bundled in `models/`, loaded from the local path directly |
| Sparse retrieval | hand-rolled BM25 (dependency-free) | local | No |
| Everything else | rule-based / entropy-gated state machine | local | No |

**This submission requires zero network access and zero API keys or credentials to run.** Both
models are bundled in `models/` and loaded from that local path explicitly — never a bare Hugging
Face model-ID string that would try to download on first use. The catalog's dense embeddings are
also precomputed and bundled (`data/_catalog_embeddings.npz`), so a fresh run never re-encodes the
50,000-item catalog from scratch. This was verified end-to-end: the built `submission/` bundle was
copied to an isolated directory with no pre-existing Hugging Face cache and `HF_HUB_OFFLINE=1` set,
and the agent constructed and responded correctly.

**Cost**: $0 — no paid API calls in the required path. **Latency**: dominated by cross-encoder
reranking (CPU, small batches per turn); catalog load + embedding-cache read takes roughly 10-15
seconds one-time at `Agent` construction, not per turn.

**Optional, not required**: if a local `ANTHROPIC_API_KEY` is present (via a `.env` file, never
shipped in this submission), the agent additionally uses a single-pass LLM listwise reranker
(Claude Haiku) on the subset of turns where the cross-encoder itself isn't confident. This measured
a genuine additional accuracy gain in development (see the design log), but is explicitly optional —
the agent is fully functional and was benchmarked without it, since no credentials are provided or
expected for official evaluation.

## Limitations and what I'd improve with more time

- **`buying` and `intent_override` scenarios lag `browsing`/`boundary` in hit rate.** Several
  targeted fixes were tried (widening the reranked candidate pool, reweighting the metadata fusion
  leg, a query-embedding nudge toward accumulated preference) — all were honestly ablated on two
  independent data splits, and all either regressed or failed to replicate on held-out data. The
  gap is real and unresolved; the design log documents exactly what was tried and why each attempt
  didn't hold up, which is itself useful signal for where the actual bottleneck likely lives
  (retrieval precision under hard filtering, not just clarification-turn policy).
- **A 1-step "world-model-lite" lookahead for question selection was built and ablated but declined**
  — it didn't clear a higher bar than the existing entropy heuristic, exactly as predicted before
  building it. A 2-step extension was not attempted given the 1-step result.
- **Portfolio/slate hedging for high-uncertainty commits** was the one clearly validated accuracy
  improvement found late in development — there may be more headroom in this direction (e.g.
  hedging strategies tuned per scenario type) that time didn't allow exploring further.
- With more time: a genuine offline SkillOpt-style optimization loop over a wider hyperparameter
  space (only a targeted sweep was run here), and a deeper investigation into why the retrieval
  pipeline specifically underperforms on hard-filtered (Buying-track) pools.

## Contribution breakdown

Single contributor for this repository's implementation.

## Full development history

Every phase's design decisions, ablation results (including several honestly-declined ideas, not
just what shipped), and the reasoning behind each are tracked in this project's own `wiki/` and
`implementation/` directories, kept as a living record throughout development rather than
reconstructed after the fact.
