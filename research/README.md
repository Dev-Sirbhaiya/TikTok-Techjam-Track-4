# Research — Index

Pure research, no implementation (per project rules at this stage — see `status.md`). Each file is
one deep-research agent's output on a specific technical dimension of the problem statement
(`wiki/00_problem_statement.md`). Once research is complete, findings get synthesized into
`wiki/01_architecture.md` (design) and `wiki/02_design_decisions.md` (decisions) — this folder
stays as the raw research trail, not the living design itself.

## Status: all 9 research agents complete — 2026-08-26. Synthesis (`DOS_AND_DONTS.md`) next.

| # | Topic | File | Status |
|---|---|---|---|
| 1 | Intent routing & query understanding (Buying vs Browsing) | `01_intent_routing.md` | done |
| 2 | Hybrid in-memory retrieval architectures (keyword+category+vector) | `02_hybrid_retrieval.md` | done |
| 3 | LLM-based semantic reranking for product search | `03_llm_reranking.md` | done |
| 4 | Multi-turn dialogue state tracking & slot management | `04_dialogue_state_tracking.md` | done |
| 5 | Proactive clarification question generation | `05_clarification_generation.md` | done |
| 6 | Personalization & context distillation (session + long-term profile) | `06_context_distillation.md` | done |
| 7 | Adaptive/dynamic agent orchestration at runtime | `07_adaptive_orchestration.md` | done |
| 8 | Evaluation metrics & benchmarks (Hit Rate@K, MRR, MTTC) | `08_evaluation_benchmarks.md` | done |
| 9 | Existing open-source conversational shopping/search agents (prior art + participant repo) | `09_prior_art_and_starter_kit.md` | done |
| — | Master Dos & Don'ts synthesis (compiled from all of the above + hard constraints) | `DOS_AND_DONTS.md` | done |

## Rules for this folder
- Every research file ends with an explicit **Dos** and **Don'ts** section scoped to its topic,
  tied back to the hackathon's hard constraints (`wiki/00_problem_statement.md` §"Hard constraints").
- Cite sources (paper/repo/doc links) inline — an unsourced claim doesn't make it into the design.
- This is exploration, not commitment — nothing here is architecture until it's promoted into the
  wiki via a `02_design_decisions.md` entry.
