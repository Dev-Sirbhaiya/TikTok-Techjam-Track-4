# 01 — Architecture

## Data & Repository Sources

- Amazon Reviews 2023 dataset (HuggingFace): https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
- Dataset paper (Hou et al., "Bridging Language and Items for Retrieval and Recommendation," arXiv 2403.03952): https://arxiv.org/abs/2403.03952
- Dataset GitHub: https://github.com/hyp1231/AmazonReviews2023
- Dataset documentation site: https://amazon-reviews-2023.github.io/
- **Competition participant repository**: https://github.com/TechJam2026/techjam-conversational-search
- **Competition participant kit release**: https://github.com/TechJam2026/techjam-conversational-search/releases/tag/participant-kit

Catalog for this track: a frozen 50,000-product subset of `Clothing_Shoes_and_Jewelry`. 200 labeled
public dev sessions; 800 held-out private sessions used for final judging (4x the public set — do not
overfit thresholds to the 200).

Item metadata fields (per the dataset paper): `main_category`, `title`, `average_rating`, `rating_number`,
`features`, `description`, `price`, `images`, `videos`, `store`, `categories`, `details` (a **free-form,
heterogeneous dict that varies by product type** — this is why dialog state cannot assume a fixed slot
schema across all products), `parent_asin` (the join/scoring key — variants like size/color share a
parent, and scoring is on `parent_asin` equality only, so child-ASIN disambiguation is never required),
`bought_together`.

## System overview — one turn, end to end

```
                                   USER MESSAGE
                                        │
                                        ▼
                          ┌─────────────────────────┐
                          │      NLU / INTENT        │   parses message → slot deltas,
                          │        DETECTOR          │   rejection signals, buying-intent
                          └─────────────────────────┘   score, comparative-feedback text
                                        │
                                        ▼
                          ┌─────────────────────────┐
                          │    DIALOG STATE UPDATE   │   diffs against memory, updates
                          │  (context distillation)  │   slots, applies decay/override,
                          └─────────────────────────┘   logs rejections
                                        │
                                        ▼
                          ┌─────────────────────────┐
                          │     RETRIEVAL LAYER      │   BM25 + dense embeddings,
                          │   (hybrid, RRF fusion)   │   combined by Reciprocal Rank Fusion
                          └─────────────────────────┘
                                        │
                                        ▼
                          ┌─────────────────────────┐
                          │      FILTER LAYER        │   strip hard-rejected attributes,
                          │   (rejection memory)      │   penalize soft-rejected attributes
                          └─────────────────────────┘
                                        │
                                        ▼
                          ┌─────────────────────────┐
                          │         RANKER           │   weighted scoring function;
                          │                          │   optional LLM re-rank of top ~20-30
                          └─────────────────────────┘
                                        │
                                        ▼
                          ┌─────────────────────────┐
                          │    DECISION POLICY       │   given confidence + turns remaining:
                          │    (turn budget)          │   ask, recommend, or both
                          └─────────────────────────┘
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                  ┌───────────────────┐  ┌───────────────────┐
                  │ QUESTION SELECTOR │  │  TOP-10 OUTPUT     │
                  │  (info gain / EIG) │  │  (always attached  │
                  │  → ask_attribute   │  │  when available)   │
                  └───────────────────┘  └───────────────────┘
                              │                   │
                              └─────────┬─────────┘
                                        ▼
                              RESPONSE TO USER
                    (message [+ ask_attribute] [+ recommendations])
```

**Design rule confirmed by the scoring formula**: always attach a Top-10 when you have one, even on a
turn where you're also asking a question — a hit can occur on any turn, and MTTC rewards early hits.
Never spend a turn asking without also returning your current best guess, *unless* the actual API
contract turns out to forbid combining them (see `docs/04_OPEN_QUESTIONS.md`, Q1).

## The dialog state object ("context distillation")

Everything downstream of NLU reads from one structured object rather than raw chat history. This is
what "context distillation" means in this design — a compressed, decision-relevant state, not a bigger
prompt.

```
DialogState
├── slots: dict                  # {"category": "dress", "price_max": 80, ...}
│                                  # open-vocabulary internally; projected onto the
│                                  # real ask_attribute enum only when asking (see Q2)
├── rejected_hard: dict           # {"color": ["green"], "price_max": 100}
│                                  # from explicit rejections — strong confidence
├── rejected_soft: dict           # {"style": ["floral"]}
│                                  # from comparative/inferred rejections — weak/medium
│                                  # confidence, down-weighted not banned (see D5)
├── interest_hypotheses: list     # OPTIONAL / Phase 2+, see D3 —
│   [{vector, label, probability}]  only if multi-vector ablation wins
├── buying_intent_score: float    # 0.0-1.0, drives retrieval breadth + confidence threshold
├── turn_count: int
├── turns_remaining: int
├── candidate_pool: list          # current ranked candidate set
├── pool_entropy: float           # uncertainty over candidate_pool, used by question selector
└── facet_utility_history: dict   # {"color": low, "use_case": high, ...} — Phase 2+ bandit input
```

Rejection confidence tiers (see Decision D5 for rationale):

```
explicit reason given ("too expensive")        → rejected_hard   (strong)
comparative negative ("less flashy than #2")    → rejected_soft   (medium)
vague/no reason ("not really my style")         → rejected_soft   (medium)
implicit ("what else do you have?")             → rejected_soft   (weak — do NOT
                                                    auto-infer a specific attribute cause)
```

## Module responsibilities

| Module | File | Responsibility |
|---|---|---|
| Intent Detector | `agent/intent_detector.py` | Buying-intent score (0.0–1.0); sets initial retrieval breadth and confidence threshold |
| Dialog State | `agent/state.py` | `DialogState` class, diffing/update logic, decay, override handling |
| Retrieval | `agent/retrieval.py` | BM25 + dense embedding candidate generation, RRF fusion |
| Rejection Memory | `agent/rejection_memory.py` | Hard/soft negative constraint tracking and confidence tiers |
| Ranker | `agent/ranker.py` | Weighted scoring function; optional LLM re-rank of shortlist |
| Question Selector | `agent/question_selector.py` | Information-gain / expected-pool-reduction facet selection |
| Turn Policy | `agent/turn_policy.py` | Confidence-vs-turns-remaining decision: ask, recommend, or both |
| Orchestrator | `agent/agent.py` | Wires the full turn loop together |

Phase 2+ optional modules (build only if their ablation wins — see `docs/06_ABLATIONS_AND_METRICS.md`):

| Module | File | Responsibility |
|---|---|---|
| Multi-Interest Layer | `agent/multi_interest.py` | K-hypothesis vector routing + probabilistic fusion |
| Action Policy (bandit) | `agent/action_policy.py` | Contextual-bandit facet-value estimation, `Q(a \| state)` |
| Comparative Feedback | `agent/comparative.py` | Parses comparative language ("closer to #2, less flashy") into state updates |
| Offline Strategy Tuner | `tools/offline_tune.py` | SkillOpt-style rollout → score → edit → validate loop against dev sessions |

## Why modules are this decoupled

Each module is a separate file with a narrow interface so a team can build in parallel without blocking
each other, and so each feature can be demoed/ablated in isolation. This also directly serves the
"well-structured, commented code covering all components" deliverable requirement.

## What is explicitly NOT in this architecture

- **No hypernetwork/LoRA personalization layer.** Sessions are isolated single-user interactions with no
  cross-session identifier — a cross-session personalization layer would never be exercised by the
  evaluator, and it would also require local model weight access the rest of this design doesn't need.
  See Decision D8.
- **No literal swipe/click UI feeding the scored path.** If the real API is text-turns-only (unconfirmed,
  see Q1/Q3), any comparative "Tinder-style" signal must arrive as ordinary message text, parsed through
  the same NLU step as any other turn. See Decision D9.
- **No externally-hosted vector database.** In-memory only, per the competition's own constraint.
