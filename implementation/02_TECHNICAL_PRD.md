# 02 — Technical PRD

## Interface contract (verified against `external/techjam-conversational-search` source — not docs alone)

```python
class Agent:
    def reset(self, session_id: str, user_profile: dict) -> None: ...
    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        return {
            "message": str,                                  # required
            "ask_attribute": str | None,                      # optional; one of the 11 values below
            "recommendations": [{"parent_asin": str}, ...],   # optional; up to 10 scored
            "usage": {"prompt_tokens": int, "completion_tokens": int},  # optional, feasibility-only
        }
```

- `ask_attribute` closed vocabulary (11 values, CONFIRMED): `category, material, color, size, style,
  brand, budget, feature, use_case, other, null`. **Caveat (new finding, not in `/My Ideas/`)**: the
  simulator's `classify_constraint()` has no branch for `brand` — asking `brand` can never match a
  constraint via that function and will always fall through to the generic "I don't have an additional
  preference for brand" reply. Don't rely on `brand` as a productive clarification target; use the
  catalog's own `store`/`details.Brand` fields directly instead.
- **Combined ask+recommend in one turn: CONFIRMED SUPPORTED.** `evaluator/local_evaluator.py`
  processes `recommendations` for the hit-check independently of `ask_attribute`, and uses
  `ask_attribute` to drive the next customer reply independently of whether a hit occurred. Resolves
  `/My Ideas/04_OPEN_QUESTIONS.md` Q1 conclusively: **yes**. Design rule: always attach the current
  best top-10 when one exists, even on a turn that's also asking — a hit can land on any turn.
- Local dev harness hardcodes `from starter.agent import Agent` with no override flag — real
  implementation must live at/be re-exported from `starter/agent.py`. Final submission format is a
  separate standalone layout (`agent.py` + `requirements.txt` + `README.md` + `src/`). See
  `04_SYSTEM_DESIGN.md` §Packaging for how one implementation serves both.
- Only the first 10 valid, unique, catalog-present `parent_asin` values are scored; malformed
  responses/exceptions count as an empty turn (not a session-ending error).

## Functional requirements (by pillar)

| ID | Requirement | Pillar |
|---|---|---|
| FR-1 | Detect Buying vs. Browsing intent per turn from accumulated dialogue, not just the latest utterance | I |
| FR-2 | Multi-route candidate retrieval (keyword + dense + metadata/structured filter) fused into one ranked pool | I |
| FR-3 | Semantic reranking of a bounded shortlist to push the true item toward rank 1 | I |
| FR-4 | Maintain structured dialogue state across turns: accumulated slots, rejected values (tiered confidence), turn count | II |
| FR-5 | Detect and correctly handle intent override (topic/constraint pivot) distinctly from incremental refinement | II |
| FR-6 | Trigger clarification only on genuine over-generality (measured, not assumed), phrased as a closed catalog-grounded choice | II |
| FR-7 | Maintain a lightweight within-session preference signal that improves ranking turn-over-turn | III |
| FR-8 | Adapt retrieval/ranking/clarification strategy per turn from cheap, already-computed signals (not a fixed pipeline every turn) | III |
| FR-9 | Integrate cleanly with the organizer's local evaluator without modifying it | IV |
| FR-10 | Log per-turn rationale sufficient to debug a failing session and support the demo video | (cross-cutting) |

## Non-functional requirements

| ID | Requirement | Rationale |
|---|---|---|
| NFR-1 | Every code path must make exceeding 10 turns structurally impossible, not "usually avoided" | Hard fail = zero score |
| NFR-2 | Must run correctly with **zero external LLM API access** (organizer guarantees none) | `research/03`, D-LLM-TIER |
| NFR-3 | Fully in-process/in-memory — no external service of any kind beyond an optional LLM API call | Competition constraint |
| NFR-4 | Per-turn latency should stay low enough that 10 turns complete quickly in local eval (no hard number published — see `06_DECISION_LOG.md` D-LATENCY) | Submission rules: undisclosed CPU/timeout limits at final judging |
| NFR-5 | No training or fine-tuning of any foundation model; only hand-built scoring/heuristic logic and off-the-shelf pretrained components | Competition constraint |
| NFR-6 | Reproducible from a documented single command + pinned dependency list | Submission rules |
| NFR-7 | Never mutate `catalog.jsonl` or reference identifiers outside it | Competition constraint |

## Out of scope (explicit, per competition spec + this corpus's own scoping)

UI/UX of any kind (headless evaluation only); full/partial foundation-model training or fine-tuning;
hosted/clustered vector databases; multi-modal (image/audio/video) processing; cross-session persistent
user identity or profile storage (see D8 — sessions are isolated single-user); trained neural
components requiring gradient-descent training on labeled data (e.g., a literal trained MIND/ComiRec,
a trained bandit policy, a trained DST classifier) — hand-built/heuristic/off-the-shelf-pretrained
equivalents are in scope, trained-from-scratch equivalents are not.

## Deliverable requirements (from the competition spec, tracked here so nothing is forgotten)

1. Devpost written description: approach, tools, APIs, libraries, datasets.
2. Public GitHub repo: structured/commented code, README (overview, setup, repro steps, limitations &
   future improvements, contribution breakdown).
3. Demo video (YouTube, public): end-to-end walkthrough; API/inference-example walkthrough is
   acceptable since there's no UI, per the spec's own note for backend/NLP tracks.
4. Model/cost/latency/offline-fallback disclosure (submission rules — build this in from Phase 0, not
   bolted on later, per `05_BUILD_PLAN.md` step 0.10).
