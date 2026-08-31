# ShopMind frontend

A deliberately cinematic, judge-facing frontend for the Track 4 Shopping Copilot. It is static and dependency-free so it can be demoed immediately from `frontend/index.html` and later wired to the real `Agent` API.

## Design intent

- Lead with the verified TechnicalScore rather than generic marketing.
- Make the dual-track / hybrid retrieval architecture visible without overwhelming a judge.
- Show the core product behavior: disclose → clarify → distill context → rerank → commit.
- Make the evaluation story legible in seconds: HitRate@10, MRR, MTTC and the clean 0.441 headline.
- Keep the interface polished enough for a live demo while preserving a credible engineering-console feel.

## Wiring to the real agent

The current UI is a deterministic presentation layer. Replace the demo response handler in `index.html` with a thin HTTP bridge or local Python wrapper around the repository's `Agent` implementation. The visual pipeline should remain unchanged: the frontend is meant to expose the system's reasoning and state, not become another source of scoring behavior.
