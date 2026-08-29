# 12 — Build Memo

*Read this if you only read one file in `implementation/`.*

## What we're building

A shopping copilot for TikTok TechJam 2026 Track 4: given a shopper's message per turn (max 10 turns),
return a natural-language reply, optionally one clarifying question (from a fixed 11-value enum), and
up to 10 ranked product IDs — trying to get the hidden target product into the top-10, as high-ranked
and as early as possible. Scored by a **deterministic, rule-based, non-LLM customer simulator** whose
exact reveal logic we've read directly from source (`wiki/09_simulator_mechanics.md`) — this is closer
to optimizing against a known mechanism than designing for an unpredictable human.

## Where the score actually comes from

`TechnicalScore = 0.50×HitRate@10 + 0.30×MRR + 0.20×Efficiency` (verified against source, not just
docs). Coverage gates precision mathematically (MRR ≤ HitRate@10); a failed session zeroes Efficiency
too. **Build order follows this exactly**: hybrid retrieval first, ranking precision second,
turn-efficiency last and only as a gate, never traded against the first two.

## The shape of the system

Multi-route retrieval (BM25 + dense embeddings + metadata filters, fused via Reciprocal Rank Fusion) →
rejection-memory filter → within-session preference boost → over-generality entropy check → cross-
encoder rerank (LLM optional, never required) → turn policy (ask/commit/both — combined turns are
confirmed supported) → response. A small explicit state machine adapts a handful of named decision
points (rerank-skip, retrieval blend, clarification aggressiveness) from cheap signals already
computed — never a free-form "LLM decides everything" controller. Full detail:
`03_SYSTEM_ARCHITECTURE.md`, `04_SYSTEM_DESIGN.md`.

## What's genuinely new here vs. the earlier `/My Ideas/` draft

That draft (an excellent independent design + research pass) got almost everything structurally right
— RRF over weighted-sum, three-tier rejection memory, ablation-gated ambitious ideas, cutting
cross-session personalization. This corpus:
1. **Resolves every one of its 10 open questions** against the actual evaluator/starter-agent source
   code, not inference — including the load-bearing one (combined ask+recommend IS supported) and a
   genuine data-quality finding neither pass had (`details` has zero schema consistency even within
   one narrow category, and some "categories" are actually mislabeled store names).
2. **Fills a real gap**: adds an explicit within-session preference-vector boost (`D-PROFILE`) as the
   concrete, defensible answer to Pillar III's "long-term user profile" language — the earlier draft
   had rejection memory and (gated) multi-interest vectors, but nothing addressing this directly at the
   Phase 0/1 floor level.
3. **Makes the no-LLM-dependency requirement structural, not incidental** (`D-LLM-TIER`): the organizer
   provides no API credits; Phase 0 is designed and ablated to fully beat the baseline with zero
   external LLM calls, with any LLM usage as a strictly optional, gracefully-degrading booster.
4. **Solves the packaging gotcha** (`D-PACKAGING`): local dev evaluation hardcodes an import path to
   `starter/agent.py` with no override flag, while the final submission format is a different standalone
   layout — one real implementation, two thin re-export shims.
5. **Turns the build plan into granular, phase-numbered steps** (0.1 through 5.5) so "run Phase 0" or
   "run step 0.4" is an unambiguous instruction that maps directly to `CLAUDE.md`'s enforced
   commit → background codex review → wiki update loop, automatically, per step.

## What could still go wrong (see `07_RISK_REGISTER.md` for the full list)

The two biggest: (a) shipping an ambitious Phase 2+ feature that doesn't survive its ablation, at the
cost of Phase 0/1 polish time — mitigated by mandatory gates and a floor-first build order; (b)
building something that quietly depends on an LLM API the organizer never promised — mitigated
structurally by `D-LLM-TIER`.

## Status as of this writing (2026-08-29)

Research and planning complete; zero implementation code written yet. `codex exec review` is
authenticated and working. Next action: begin `05_BUILD_PLAN.md` Phase 0, step 0.1.
