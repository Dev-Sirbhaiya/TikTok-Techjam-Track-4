# TikTok TechJam 2026 — Track 4: Shopping Copilot

A conversational shopping agent over a frozen 50,000-item Amazon `Clothing_Shoes_and_Jewelry`
catalog: hybrid BM25 + dense + metadata retrieval, cross-encoder reranking, a dialog state machine
with calibrated clarification, and an optional LLM reranking pass — all within a hard 10-turn
session cap. Built for TikTok TechJam 2026, Track 4 (E-Commerce AI Conversational Search &
Recommendations).

## Start here

**If you're new to this repo, read in this order:**

1. **[`status.md`](status.md)** — current phase, latest score, what's done, what's next. The single
   source of truth for "where are things right now."
2. **[`wiki/INDEX.md`](wiki/INDEX.md)** — the living wiki: architecture, every design decision (and
   why), a full chronological narrative of what was tried/kept/cut, and the evaluation log with
   every measured result. This is the project's memory — nothing important lives only in chat
   history or commit messages.
3. **[`docs/SUBMISSION_README.md`](docs/SUBMISSION_README.md)** — setup, run instructions, model/
   cost/latency disclosure, and current known limitations. This is also what ships inside
   `submission/` (the packaged deliverable — gitignored, regenerate with `tools/build_submission.py`).

## Repo layout

| Path | What's in it |
|---|---|
| `src/copilot/` | The actual agent implementation |
| `tools/` | Evaluator wiring, offline tuning/ablation scripts, diagnostics, submission packaging |
| `tests/` | Fast unit tests (no model downloads required) — `pytest tests/` |
| `wiki/` | Living project memory — architecture, decisions, design log, evaluation history |
| `implementation/` | The authoritative pre-build architecture/build-plan corpus |
| `docs/` | Submission-facing docs (README, demo video script, Devpost draft) |
| `My Ideas/` | Historical brainstorming input — superseded by `implementation/`, kept for reference |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r submission/requirements.txt   # after running tools/build_submission.py once
pytest tests/                                 # fast unit tests, no model downloads
python tools/run_eval.py                      # full evaluator run against the real agent
```

See `docs/SUBMISSION_README.md` for the exact `Agent` API usage.

## Current status

Score progression, exact numbers, and everything tried (including what was tried and honestly
declined) are tracked in `wiki/08_evaluation_log.md` and summarized in `status.md` — check those
directly rather than trusting a number written here, since this file isn't kept in sync with every
result the way those pages are.
