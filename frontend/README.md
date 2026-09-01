# ShopMind real-agent frontend

A judge-facing console for the Track 4 Shopping Copilot. This frontend is **not a mock conversation**: the browser sends each turn to the repository's real `src/copilot/agent.py::Agent.respond()` through `tools/run_frontend.py` and renders the returned response plus the live `DialogState` and real catalog records.

## Run it

From the repository root:

```bash
pip install -r requirements.txt
python tools/run_frontend.py
```

Open **http://127.0.0.1:8765**.

The first startup may take time because the real Agent loads the catalog and initializes its pretrained retrieval/reranking components. That is the same expensive setup the evaluator intentionally performs once per Agent instance.

## What is real

- `Agent.reset(session_id, user_profile)` creates the real isolated dialog session.
- Every message is passed to `Agent.respond(session_id, user_message, turn, top_k)`.
- The UI displays the Agent's actual `message`, `ask_attribute`, and up-to-10 recommendation IDs.
- Recommendation cards are hydrated directly from `data/catalog.jsonl`; no product copy is invented by the UI.
- Slot state, confidence tiers, hard/soft rejection memory, accumulated query terms, candidate pool, entropy, turn budget, and override history are read from the Agent's live session state.
- The current strategy configuration is read from `src/copilot/strategy_config.py`.
- The raw response panel shows the exact JSON returned by `Agent.respond()`.
- The local bridge enforces the same 10-turn ceiling and top-k maximum as the competition contract.

## Architecture exposed by the UI

The console is deliberately organized around the actual project pillars: NLU/slot extraction, Buying vs Browsing routing, BM25 + dense + metadata retrieval with RRF, within-session preference/rejection memory, bounded cross-encoder reranking, and the entropy/VOI ask-vs-commit policy. These labels describe the implemented backend; session values are only shown when the backend exposes them.

## Important boundary

The frontend is a **demo/debug surface**, not part of the competition scoring path. It does not replace, modify, or proxy the organizer evaluator. The scored interface remains the existing `Agent` contract documented in `implementation/02_TECHNICAL_PRD.md`.

This distinction is intentional: the competition explicitly evaluates the backend headlessly, while the UI makes that backend understandable and demonstrable to a human judge.
