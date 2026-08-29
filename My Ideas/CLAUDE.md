# CLAUDE.md — Project Context for Claude Code

> **Read this file first.** This is the entry point for a hackathon submission to **TikTok TechJam 2026,
> Track 4: "Shopping Copilot — AI Conversational Search and Recommendations."** Everything in `/docs`
> was produced during an extensive design/research phase (ideation, external critique, and a formal
> research pass) *before any code was written*. No implementation exists yet. Your job, when asked to
> build, is to follow `docs/02_BUILD_PLAN.md` in order — Phase 0 first, nothing else, until it's a
> complete, evaluator-passing submission.

## What this project is

A conversational agent that, given a shopper's message, must return (per turn): a natural-language
`message`, optionally one `ask_attribute` (a clarifying question about a specific facet), and up to 10
ranked `parent_asin` product IDs — across at most 10 turns — trying to get the true target product into
its Top-10 as early and as accurately as possible.

Scored on: `TechnicalScore = 0.50·HitRate@10 + 0.30·MRR + 0.20·Efficiency`, where
`Efficiency = clip((11 − MTTC)/10, 0, 1)`. The provided weak BM25 starter agent scores
**HitRate@10 = 0.125, MRR = 0.068, MTTC = 9.81** — that is the number to beat, not zero.

## Non-negotiable constraints (violating any of these can zero the submission)

- **No training or full-parameter fine-tuning of any base LLM.** Small, hand-built scoring/heuristic
  functions are fine. Nothing that requires a gradient-descent training loop during the competition.
- **In-memory only.** No external vector DB clusters, no persistent database. 50k products must be held
  and searched as an in-memory structure (numpy arrays, `faiss-cpu` in in-memory mode, etc.).
- **Text/structured-metadata only.** No image, audio, or video processing.
- **Hard 10-turn cap per session, zero score if exceeded.** A turn-budget policy that forces a commit
  before turn 10 is mandatory, not optional.
- **Catalog is read-only.** Never mutate the provided catalog data.
- **Sessions are isolated, single-user.** No cross-session memory, no persistent user profile across
  sessions — design accordingly (see `docs/03_DECISION_LOG.md`, Decision D8).
- **A paid LLM API is not required.** BM25 + embeddings + a hand-built scorer can score respectably on
  their own; reserve any LLM calls for the highest-value step (semantic re-ranking of a short list).

## Critical open item — verify before trusting downstream assumptions

**We have not yet independently read the actual competition repository's API contract.** Several
important design decisions in this documentation set (whether a single turn can return both an
`ask_attribute` AND `recommendations` together; the exact fixed list of valid `ask_attribute` values;
whether any comparative/click feedback channel exists at all) are based on a research pass's best
inference, not a confirmed read of the real files. **The first task in any coding session should be
reading `agent_api_contract.json` (or equivalent) and `competition_specification.md` directly from
the cloned repo, then updating `docs/04_OPEN_QUESTIONS.md` with confirmed answers before Phase 1
begins.** Repo links are in `docs/01_ARCHITECTURE.md` under "Data & Repository Sources."

## Where everything lives

| File | What's in it |
|---|---|
| `docs/01_ARCHITECTURE.md` | Full system design, architecture diagrams, data flow, module responsibilities |
| `docs/02_BUILD_PLAN.md` | Phased implementation plan — bare-minimum floor first, then gated expansions |
| `docs/03_DECISION_LOG.md` | Every design decision made, the alternatives considered, and why |
| `docs/04_OPEN_QUESTIONS.md` | Every unresolved/unverified question, ranked by how much depends on it |
| `docs/05_COMPONENT_SPECS.md` | Per-module interfaces, data structures, and pseudocode, ready to implement from |
| `docs/06_ABLATIONS_AND_METRICS.md` | The mandatory ablation plan and the metric-tracking discipline |

## The one rule that governs every phase past the floor

> A technique being real, published, and well-cited is never sufficient justification for keeping it in
> this system. If a component doesn't measurably improve held-out results on our own dev sessions, it
> gets removed or demoted — never kept because a paper exists for it.

This applies to every "Phase 2+" item in the build plan. See `docs/06_ABLATIONS_AND_METRICS.md` for the
exact gating procedure.
