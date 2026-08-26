# Prior Art & Starter Kit Research — TechJam 2026 Track 4 (Shopping Copilot)

Compiled 2026-08-26. All Part A findings come from `WebFetch` on GitHub web pages, `raw.githubusercontent.com`, and the GitHub REST API (`api.github.com`) — no `git clone`/`git pull` was performed, per instructions. Repo: `https://github.com/TechJam2026/techjam-conversational-search` (default branch assumed `main` — this was not separately confirmed, see Gaps below).

---

## Part A: Participant kit / starter repo findings

### Repo structure (verified via GitHub Trees API, `git/trees/main?recursive=1`)

```
.gitignore
DATA_ATTRIBUTION.md
README.md
data/README.md
data/public_set.jsonl
docs/agent_api_contract.json
docs/baseline_results.json
docs/competition_specification.md
docs/evaluation_config.json
docs/submission_rules.md
evaluator/__init__.py
evaluator/local_evaluator.py
starter/__init__.py
starter/agent.py
tests/__init__.py
tests/test_evaluator.py
```
Note: `data/catalog.jsonl` is **not** in the repo tree — the catalog is distributed only via the GitHub Release (see below), consistent with `data/README.md`'s "requires manual download" note.

### Agent interface (verified, from `docs/agent_api_contract.json` + `docs/competition_specification.md`, cross-checked against `starter/agent.py` and `evaluator/local_evaluator.py`)

```python
class Agent:
    def reset(self, session_id: str, user_profile: dict) -> None: ...
    def respond(self, session_id: str, user_message: str, turn: int, top_k: int) -> dict:
        return {
            "message": "Do you have a material preference?",
            "ask_attribute": "material",   # one of the allowed enum values, or null
            "recommendations": [{"parent_asin": "B000...", "score": 0.0}],  # score optional, ignored
            "usage": {"prompt_tokens": 120, "completion_tokens": 30},  # optional if no model used
        }
```
- `ask_attribute` enum (exact, from the JSON Schema): `category, material, color, size, style, brand, budget, feature, use_case, other, null`. This is a **closed vocabulary** — the evaluator's simulated customer keys off this exact field to decide what to reveal, not off the free-text `message`. Sending an out-of-vocabulary or malformed value in `message` alone gets nothing extra revealed.
- `turn_request.top_k` is schema-locked to the constant `10`.
- `recommendations` may return up to 100 items but only the **first 10 valid, unique, catalog-present `parent_asin` values** are scored (`normalize_recommendations`, `TOP_K = 10`); invalid/duplicate/out-of-catalog IDs are silently dropped, not penalized beyond being skipped.
- Exceptions or malformed responses inside `respond()` are caught by the harness and treated as an empty response for that turn (`{"message": "", "ask_attribute": None, "recommendations": []}`) — this is **not necessarily a full-session miss**, just a wasted turn; a later turn can still hit.
- `reset()` must be called before `respond()` per session (starter agent enforces this with a `RuntimeError`, but this is starter-agent behavior, not a contract requirement per se).

### Starter BM25 agent (verified, full source read from `starter/agent.py`)

- Purely lexical, no LLM, no embeddings. Builds an **in-memory SQLite FTS5** virtual table (`sqlite3.connect(":memory:")`) over concatenated text from `title, categories, features, details, store, description` at construction time, batching inserts 1000 rows at a time.
- Text normalization: `_text()` flattens dicts as `"key value"` pairs and lists via `str(item)` join; `_terms()` tokenizes with `[a-z0-9]+` (case-insensitive), drops tokens of length ≤1, and drops a small hardcoded stopword list (`STOPWORDS` — 27 words including generic connectors and shopping filler like "want", "looking", "please").
- Query construction: takes up to the first 40 unique terms from the user message, joins them with `OR` into an FTS5 MATCH expression (quoted per term), ranks with `bm25(products, 0.0, 6.0, 4.0, 2.5, 2.5, 1.5, 1.0)` — i.e., column weights favor `title` (6.0) and `categories`/`features` (4.0, 2.5) over `details`/`store` (2.5, 1.5) and `description` (1.0); note the first weight `0.0` corresponds to the UNINDEXED `parent_asin` column.
- **Never asks a clarification question** — `ask_attribute` is always `None`; it treats every turn as a fresh independent search over the raw user message (no state accumulation, no query rewriting/expansion across turns). This is why it scores so low (see baseline below) — with OR-only matching plus no multi-turn memory, it wastes turns re-running near-identical noisy queries.
- Reported baseline (from `docs/baseline_results.json`, run on the 200 public dev sessions): `hit_rate_at_10 = 0.125`, `mrr = 0.068034`, `mttc = 9.81` turns, `efficiency = 0.119`, `technical_score = 0.10671`.

### Local evaluator (verified, full source read from `evaluator/local_evaluator.py` and `tests/test_evaluator.py`)

This is the single most important file for our design — it fully determines scoring and simulated-customer behavior. Key mechanics:

**Simulated customer / hidden intent construction** (`intent_card()`, `behavior_for()`):
- For each sample, if the public JSONL doesn't already carry `intent_card`/`behavior` (the shipped `public_set.jsonl` does NOT — confirmed by reading actual records, see below), the evaluator derives them on the fly from the **target product's own catalog row** looked up by `ground_truth.parent_asin`: title (cleaned/truncated to 180 chars) becomes `target_category`; a regex over the product's searchable text pulls a material (`MATERIAL_RE`: cotton/polyester/nylon/leather/wool/spandex/silk/rayon/fabric) and a color (`COLOR_RE`: black/white/blue/red/pink/green/brown/gray/grey/purple/yellow/orange); price becomes a "budget around $X" candidate. These, plus flattened `features`/`details` values, become `hard_constraints` (first 2) and `soft_preferences` (next 2, or first 1 if fewer than 2 remain).
- `behavior_for()` for `intent_override` scenarios picks (deterministically seeded via `random.Random(sample_id + scenario_type)`) an override turn of 3 or 4, and constructs an explicit override message: `"Actually, ignore my earlier preference. What I need is: {new_value}."` where `new_value` is the first hard constraint.
- **This means the target product's attributes are effectively leaked into the conversation over time** via disclosed constraints — the simulator is deterministic and rule-based, not an LLM. There is no paraphrasing variance; the same sample always yields the same intent card given the same catalog snapshot.

**Turn-by-turn protocol** (`evaluate()`):
1. New `session_id = f"public_{uuid4().hex}"` each run (not the `sample_id`), `agent.reset(session_id, sample["user_profile"])`.
2. `coarse_category()` strips generic "Clothing/Clothing Shoes & Jewelry" labels from the target's `categories` and joins the last 2 remaining parts to build a human-readable category phrase used in the opening message.
3. `initial_message()`: for `buying` scenarios, discloses the first hard constraint immediately ("I'm looking for {category}. A key requirement is: {constraint}."); for `intent_override`, opens with the *old* (soon-to-be-replaced) preference; otherwise (`browsing`, `boundary`) opens vague ("...but I'm still exploring.").
4. Each turn: call `agent.respond(...)`, defensively coerce malformed output to empty, accumulate `usage` tokens, normalize recommendations against the real catalog ID set. **Hit check**: only counts if `override_applied` (i.e., for intent_override scenarios, a hit before the override turn does NOT count — this is a hard rule: `if override_applied and target in ranked`). First-hit turn and rank are recorded; loop breaks on hit.
5. If not turn 10 yet: if this is the scheduled override turn for an `intent_override` sample, force-feed the override message (ignoring the agent's `ask_attribute`) and mark the old disclosed value; otherwise call `customer_reply()`.
6. `customer_reply()`: for `boundary` scenarios, the *first* time the agent asks about any attribute, replies "I don't have a preference for {attribute}; please use your judgment." (only once — `boundary_used` flag). If `ask_attribute` is `None`/falsy, replies with a generic nudge: "Those options are not quite right yet. Ask me about one specific attribute." — i.e., **the starter agent, which never sets `ask_attribute`, gets this same non-informative nudge every single turn**, explaining part of its poor score. If an attribute is given, `classify_constraint()` buckets each undisclosed hard/soft constraint by keyword heuristics (budget/material/color/size/style-fit/use_case/else="feature") and reveals up to 2 matching, not-yet-disclosed constraints for the asked attribute; if none match, replies "I don't have an additional preference for {attribute}."
7. Metrics per session: `hit` (bool), `first_hit_turn` (int or None), `best_rank`, `reciprocal_rank` (0 if miss).

**Metric formulas** (verified, matches `docs/competition_specification.md` and `docs/evaluation_config.json` exactly):
```
hit_rate_at_10 = hits / N
mrr            = mean(reciprocal_rank), miss = 0
mttc           = mean(first_hit_turn), miss = 11   (MAX_TURNS+1)
efficiency     = clip((11 - mttc) / 10, 0, 1)
technical_score = 0.50*hit_rate_at_10 + 0.30*mrr + 0.20*efficiency
```
Scenario-level breakdowns (`buying`, `browsing`, `intent_override`, `boundary`) are reported separately via the same `metric_summary()` function, grouped by `scenario_type`.

**Invocation** (`evaluator/local_evaluator.py` `main()`, confirmed by `tests/test_evaluator.py` imports):
```
python -m evaluator.local_evaluator --catalog data/catalog.jsonl --dataset data/public_set.jsonl --output results.json
```
It directly imports and instantiates `from starter.agent import Agent` — i.e., **the evaluator hardcodes the import path `starter.agent.Agent`**, so our custom agent needs to live at (or be importable as) `starter/agent.py`'s `Agent` class, OR we need to check whether the evaluator script is meant to be pointed at a different module (nothing in the visible code parameterizes the agent import — `Agent(args.catalog)` is called directly with only a `--catalog` CLI arg, no `--agent-module` flag). **This is worth double-checking against the actual local clone** — it's possible participants are expected to overwrite `starter/agent.py` in place rather than add a separate module.

### Session/data format (verified by reading actual `data/public_set.jsonl` records + `data/README.md`)

Each of the 200 public dev session records looks like:
```json
{"category_bucket": "clothing", "difficulty_bucket": "easy", "ground_truth": {"parent_asin": "B09PYB7B6Z"}, "sample_id": "public_0001", "scenario_type": "buying", "user_profile": {"average_prior_rating": 5.0, "preference_tags": ["fit", "comfort", "durability"], "purchase_frequency": "3-4 prior purchases", "rating_style": "usually positive", "summary": "Prior purchases emphasize fit, comfort, durability; ratings are usually positive."}}
```
Confirmed fields: `category_bucket`, `difficulty_bucket` (e.g. "easy"/"hard" — not documented further in what we could access), `ground_truth.parent_asin`, `sample_id`, `scenario_type` (`buying`/`browsing`/`intent_override`/`boundary`), `user_profile` (matches the `reset_request` schema exactly: `purchase_frequency`, `average_prior_rating`, `rating_style`, `preference_tags`, `summary`).

Confirmed: `intent_card` and `behavior` are **not present** in the shipped public file — `materialize_hidden_fields()` in the evaluator explicitly checks `if "intent_card" in sample and "behavior" in sample: return ...` else derives them from the catalog, meaning **for the public set, the evaluator always derives them on the fly** (the private 800-session set presumably ships these directly per the spec's "hidden intent cards ... are never sent to the participant Agent," but might be precomputed for the organizer's own scoring — unconfirmed).

`data/README.md` states the 200 public sessions split as 80 Buying / 80 Browsing / 30 Intent Override / 10 Boundary (matches the spec's 40/40/15/5% mix over 200 = 80/80/30/10).

### Competition spec highlights (verified, `docs/competition_specification.md`, quoted in relevant parts above)
- Visible catalog fields: `parent_asin, title, features, description, price, categories, details, average_rating, rating_number, store`. Only `parent_asin` is scored.
- In scope: keyword/dense/hybrid retrieval, buying/browsing routing, query rewriting, semantic reranking, conversation-state management, clarification strategy, safe profile personalization, legally accessible LLM APIs or local models.
- Out of scope: catalog modification, off-catalog IDs, private-label reconstruction, real transactions, mandatory UI, full model training, multimodal systems, infra-heavy vector DBs.
- Deliverables: source + setup/repro instructions, working `Agent`, short report (architecture, models, cost, limitations, contributions), one demonstrated multi-turn session.

### Submission rules highlights (verified, `docs/submission_rules.md`)
- Allowed: Python source, small local configs, lightweight local assets, dependency docs.
- Forbidden: private eval data, organizer-only files, API keys/secrets, undeclared external services required for official scoring.
- Final scoring may run with network access disabled — must disclose whether live credentials are required and document offline fallback.
- Must disclose exact Python version, install steps, env vars, single run command; failing reproducibility "may be treated as invalid."
- Recommendations must be ordered best-to-worst; only first 10 valid unique IDs scored; unspecified CPU/memory/timeout/network restrictions apply at final judging (exact numbers not visible to us — check `docs/submission_rules.md` in the local clone for anything WebFetch's summarizer may have trimmed).

### Release assets (verified via GitHub REST API, `releases/tags/participant-kit`, published 2026-08-24)
| Asset | Size | Notes |
|---|---|---|
| `catalog.jsonl.gz` | 19,235,996 bytes (~18.3 MB) | the 50k-product catalog, gzip-compressed |
| `SHA256SUMS` | 177 bytes | checksums for integrity verification |
| `techjam-participant-kit.zip` | 19,234,914 bytes (~18.3 MB) | bundles the same content as a zip (near-identical size to the `.gz`, suggesting it's mostly the catalog re-packaged, possibly plus the repo files) |

Release description (verbatim): "Frozen 50,000-product catalog, participant starter package, and SHA-256 checksums for the TechJam Conversational Search Challenge."

### Amazon Reviews'23 schema (verified via WebFetch of amazon-reviews-2023.github.io)
- Metadata fields relevant to us: `main_category`, `title`, `average_rating`, `rating_number`, `features` (list), `description`, `price` (float, "at time of crawling" — i.e., may be stale/inconsistent with real-world pricing), `details` (dict — brand/material/dimensions etc., unstructured/inconsistent across products), `parent_asin`.
- Critical documented quirk: **use `parent_asin`, not `asin`**, to join to metadata — "products with different colors, styles, sizes usually belong to the same parent ID." This matches the competition's exclusive use of `parent_asin` as the scored identifier.
- `Clothing_Shoes_and_Jewelry` is one of the largest categories in the full dataset (22.6M users / 7.2M items / 66.0M ratings across the *full* dataset — the competition's frozen catalog is a specific 50,000-product slice of this, not the full category).

### What we could NOT verify / should double check once the local clone finishes
- Whether the evaluator import path (`from starter.agent import Agent`) is truly hardcoded with no override flag, or whether there's a way to point it at a different agent module — check `evaluator/local_evaluator.py` argparse section directly in the clone (we read the full file via WebFetch and saw no such flag, but WebFetch summarization risk exists even on "verbatim" requests, so treat this as high-confidence but not 100%).
- Exact CPU/memory/timeout/network numeric limits for final judging — `docs/submission_rules.md`'s WebFetch summary said these are "unspecified" in the doc itself; confirm by reading the raw file directly once cloned, in case numbers exist that the summarizer dropped.
- The `difficulty_bucket` field's full value set and how it's used (only "easy"/"hard" seen in the 3 sampled records) — not explained in any doc we accessed; may just be metadata, not scored.
- Whether `main` is actually the default branch (we assumed this successfully resolved for every raw.githubusercontent.com fetch, which is decent evidence it's correct, but wasn't explicitly checked against the repo's default-branch API field).
- Full contents of `docs/submission_rules.md` and `data/README.md` beyond what WebFetch's summarizing pass surfaced — both were fetched via the prompt-and-summarize path rather than a forced verbatim code-fence dump (unlike `agent.py`/`local_evaluator.py` which we got fully verbatim); worth a raw read locally to catch any missed clauses (e.g. exact timeout numbers, exact allowed dependency list).
- We did not attempt to download/inspect `catalog.jsonl.gz` contents (correctly out of scope per instructions — the concurrent agent is handling this).

---

## Part B: Prior art

### 1. Open-source conversational shopping agents / e-commerce chatbots
- **retailGPT** (`unicamp-dl/retailGPT`, paper: [Retail-GPT: leveraging RAG for building E-commerce Chat Assistants](https://arxiv.org/abs/2408.08925)) — open-source RAG chatbot for retail; combines a dialogue layer (built on Rasa for chit-chat/entity extraction) with a RAG component for grounding responses in product data, plus real-time availability checks and cart management. Cross-platform, not tied to one commercial LLM vendor. Relevant pattern: separating "conversation management" (intent/entity extraction, chit-chat) from "retrieval grounding" (RAG over product catalog) as distinct layers.
- **tomlin7/ecommerce-chatbot** — agent-based e-commerce platform using vector search (Pinecone) plus recommendation and cart/order management; illustrates a fuller-stack (non-hackathon-constrained) architecture with a vector DB, which is explicitly out-of-scope for us per the spec ("infrastructure-heavy vector databases" disallowed) but confirms hybrid vector+keyword is the common real-world default.
- Rasa-based chatbots (`ShreyasDatta/e-Commerce-chatbot-rasa`, `Zaamine/eCommerce_Chatbot-Rasa_Python`) — classic slot-filling/intent-classification chatbot pattern (NLU pipeline + dialogue policy + action server hitting a DB). Useful as a contrast case: these are structured/rule-driven dialogue managers, closer in spirit to our clarification-attribute state machine than to an LLM-agent loop.
- [LLM Agent Meets Agentic AI: Can LLM Agents Simulate Customers to Evaluate Agentic-AI-based Shopping Assistants?](https://arxiv.org/pdf/2509.21501) — directly relevant to the *evaluation methodology* side: studies using LLM agents as customer simulators for shopping-assistant evaluation, paralleling (but more sophisticated than) this competition's deterministic rule-based `customer_reply()` simulator.

### 2. This specific track / similar past competitions
- No public solutions, write-ups, or discussion of the "techjam-conversational-search" repo, "TechJam 2026 Track 4," or "Shopping Copilot" track were found via general web search — expected, since the event (Devpost page: `tiktoktechjam2026.devpost.com`) is live/ongoing and team repos are presumably private until after judging. TechJam 2025 (prior edition) drew 2,000+ applications / 308 submissions / 12 finalists per TikTok's developer blog, but no archived Track-4-equivalent solutions were surfaced.
- Closest **structurally similar** public competitions found:
  - **Amazon KDD Cup — ESCI Shopping Queries Challenge** ([amazon-science/esci-data](https://github.com/amazon-science/esci-data), workshop site `amazonkddcup.github.io`) — large-scale product-search relevance benchmark (Exact/Substitute/Complement/Irrelevant labels), not conversational/multi-turn but the standard reference for query-to-product relevance modeling at Amazon scale. [Second-place KDD Cup 2022 solution writeup](https://amazonkddcup.github.io/papers/8408.pdf) is publicly available and documents a practical ranking pipeline (feature engineering + gradient-boosted/transformer reranking) that generalizes to any query→product ranking subproblem inside our agent.
  - [EC-Guide (fzp0424/ec-guide-kddup-2024)](https://github.com/fzp0424/ec-guide-kddup-2024) — Amazon KDD Cup 2024 solution (Track 2 top-2, Track 5 top-5) covering instruction-tuning and inference optimization for e-commerce LLM tasks; shows a full pipeline of dataset construction → fine-tuning → quantization → inference optimization, useful as a reference for token/latency-conscious LLM deployment even though our track disallows FM training.
  - **ProductAgent** ([arXiv:2407.00942](https://arxiv.org/pdf/2407.00942), "ProductAgent: Benchmarking Conversational Product Search Agent with Asking Clarification Questions") — the single most directly analogous piece of prior art found. Proposes an agent with explicit "product feature summarization, query generation, and product retrieval" strategies for deciding what to ask, plus a companion benchmark (PROCLARE) that uses an LLM-driven user simulator to evaluate multi-turn improvement. Reports that retrieval performance improves as dialogue turns progress and user demands become more explicit — directly supports designing our agent around an explicit, accumulating constraint/slot state rather than stateless per-turn retrieval (exactly what the starter BM25 agent fails to do).

### 3. RAG-for-e-commerce reference architectures
- Standard modern hybrid pipeline (multiple corroborating sources, e.g. [Denser.ai's hybrid search guide](https://denser.ai/blog/hybrid-search-for-rag/), [tim-ponomarev/hybrid-rag](https://github.com/tim-ponomarev/hybrid-rag)): **BM25 (lexical) + dense embedding retrieval run in parallel → Reciprocal Rank Fusion (RRF) to merge → cross-encoder reranker on the fused top-N (typically 50-200) → final top-k**. Rationale: BM25 wins on exact identifiers/rare terms/brand names/model numbers; dense retrieval wins on paraphrase/semantic queries with no keyword overlap. This is a strong candidate baseline upgrade over the starter's BM25-only approach, constrained to in-memory/no-heavy-infra as our track requires (an in-process FAISS/numpy cosine index over precomputed embeddings, not a hosted vector DB, would satisfy "no infrastructure-heavy vector databases").
- [A Reference Architecture for Agentic Hybrid Retrieval in Dataset Search](https://arxiv.org/html/2604.16394v1) — documents both a single ReAct-style agent (one loop doing plan→retrieve→evaluate→rerank) and a multi-agent decomposed variant (separate planner/retriever/evaluator/reranker roles) for hybrid retrieval; useful architectural menu for how much orchestration complexity to add given our 10-turn budget and per-turn latency/cost constraints — a single-agent loop is almost certainly the right choice given hard turn limits and no infra allowance.
- [Graph-Enhanced Retrieval-Augmented QA for E-Commerce Customer Support](https://arxiv.org/html/2509.14267v1) — knowledge-graph-augmented RAG for grounding; more relevant to support QA than product discovery, but its "parallel retrieval architecture enables sub-second response times" point is relevant to our efficiency scoring term.
- Conversational-recommendation-specific literature: [Advances and challenges in conversational recommender systems: A survey](https://www.sciencedirect.com/science/article/pii/S2666651021000164) and the [ACM Survey on Conversational Recommender Systems](https://dl.acm.org/doi/fullHtml/10.1145/3453154) frame the core exploration/exploitation trade-off explicitly: use retrieval-result entropy (or similar uncertainty signal) to decide whether to ask another clarifying question ("explore") or commit to recommending now ("exploit") — this maps directly onto our efficiency-vs-hit-rate scoring tension (asking too many questions burns MTTC/efficiency; recommending too early risks missing top-10).
- **ClariQ** ([aliannejadi/ClariQ](https://github.com/aliannejadi/ClariQ)) — the standard academic dataset/framing for "when to ask" vs. "which question to ask" in conversational search; directly names the two decisions our agent's clarification policy must make every turn.

---

## Implications for our design

**Reuse from the starter kit:**
- The `Agent` class shape (`reset`/`respond`) and the exact `ask_attribute` enum are contractual — no room to deviate. Build directly to `docs/agent_api_contract.json`.
- The FTS5/BM25 in-memory indexing technique in `starter/agent.py` is a reasonable, zero-dependency substrate for a lexical retrieval component even inside a much smarter agent — SQLite FTS5 is stdlib (`sqlite3`), satisfies "in-memory only," and avoids extra dependencies. Worth keeping as one leg of a hybrid retriever rather than discarding wholesale.
- The evaluator's `customer_reply()` logic is our de facto specification of simulated-customer behavior for local dev/tuning — since it's deterministic and rule-based (not an LLM), we can essentially **reverse-engineer the exact reveal policy** (`classify_constraint` keyword buckets, "reveal up to 2 undisclosed matching constraints per matching `ask_attribute`", boundary-scenario's one-time non-answer, intent-override's forced message at turn 3 or 4) and design our clarification strategy to exploit it efficiently — e.g., asking about `material`/`color`/`budget`/`use_case` early tends to unlock concrete, disambiguating facts fast, whereas an out-of-vocabulary or `null` `ask_attribute` always gets the useless generic nudge.

**Replace / go beyond the starter kit:**
- Add **conversation state**: accumulate disclosed constraints turn-over-turn into a structured slot/filter state (category, material, color, size, budget, use_case, brand) rather than re-querying from only the latest message — the starter agent's biggest weakness is that it never remembers turn 1's revealed constraint by turn 2.
- Add an explicit **ask-vs-recommend policy**: use retrieval-score entropy/margin (top-1 vs top-10 score gap, or count of catalog items still consistent with known constraints) to decide whether to ask a clarifying question this turn or commit to recommendations, per the CRS exploration/exploitation literature above. Given `Efficiency` is 20% of score and rewards early hits, and 40%+40% of sessions are Buying/Browsing (not requiring many turns if we ask well), an adaptive policy should beat a fixed "always ask N times then recommend."
- Add **hybrid retrieval**: BM25 (reuse FTS5 approach) plus a lightweight in-memory dense signal (e.g., precomputed sentence embeddings for the 50k catalog with numpy/cosine or a simple ANN structure held in RAM) fused via RRF or a weighted sum, satisfying "no infra-heavy vector DB."
- Handle the **intent_override scenario explicitly**: since a hit before the override turn never counts, don't over-commit early confidence to the pre-override signal for the 15% of sessions that are intent_override — a pure "ask once, commit hard" strategy will systematically waste a "hit" that the evaluator discards.
- Handle **boundary scenarios**: since the customer will decline to answer the *first* clarification only, don't spend a second clarifying turn probing the exact same unanswerable attribute; move to a different attribute or commit to recommending.
- Disclose token/cost/model usage per `usage` field and the required report — plan to track this from turn 1, not bolt it on later.

---

## Dos
- Do implement exactly the `reset(session_id, user_profile)` / `respond(session_id, user_message, turn, top_k) -> dict` signature and the exact response schema (`message`, `ask_attribute`, `recommendations`, optional `usage`), matching `docs/agent_api_contract.json` field-for-field including `additionalProperties: false` semantics (don't add extra top-level keys).
- Do use only the documented catalog fields (`parent_asin, title, features, description, price, categories, details, average_rating, rating_number, store`) and score only on `parent_asin`.
- Do maintain per-`session_id` conversation state across turns (constraint slots accumulated over the dialogue) since the evaluator's simulated customer reveals information incrementally and expects the agent to remember.
- Do implement an explicit, closed-vocabulary `ask_attribute` selection (never free-text-only) since the simulator's `customer_reply()` reveals matching constraints strictly keyed on this field.
- Do build a policy for the four scenario types (buying/browsing/intent_override/boundary) since they have measurably different optimal strategies (early hard constraint vs. vague opener vs. forced override vs. one-time non-answer).
- Do verify import-path/module-location assumptions (`starter/agent.py`, `from starter.agent import Agent`) against the actual local clone before finalizing project layout.
- Do keep everything in-memory/in-process (stdlib `sqlite3` FTS5, small in-RAM vector arrays) — no external vector DB service, no network calls to infra beyond an optional LLM API, consistent with "in-memory only" and "no infrastructure-heavy vector databases."
- Do disclose model/cost/token/latency/offline-fallback information as required by `docs/submission_rules.md` and the spec's "Model and API Policy" section.
- Do treat the 200 public sessions purely as a dev/tuning set and watch for overfitting to the exact deterministic `customer_reply()` heuristics, since the private 800-session judging set may use different/harder underlying catalog rows even though the reveal mechanics should be the same code.

**Additional context for these guardrails**: see `docs/competition_specification.md` "Scope"/"Model and API Policy" sections and `docs/submission_rules.md` as summarized above.

## Don'ts
- Don't modify the evaluator (`evaluator/local_evaluator.py`) — the spec explicitly says implement your solution in `starter/agent.py` "without modifying the evaluator."
- Don't rely on `ask_attribute` free text or synonyms outside the 10-value enum (`category, material, color, size, style, brand, budget, feature, use_case, other`) plus `null` — anything else is either coerced to "other" bucket matching or gets the generic non-informative nudge.
- Don't assume a hit before an `intent_override` sample's override turn counts — the evaluator explicitly discards it (`override_applied` gate).
- Don't keep asking the same clarifying attribute after a `boundary` scenario has already declined once for that attribute pattern — no new information will come from repeating it, and it burns turns/efficiency.
- Don't return more than what's needed — only first 10 valid/unique/catalog-present `parent_asin`s are scored; don't assume a `score` field or ordering beyond "best to worst" affects scoring beyond ordering itself.
- Don't commit API keys/secrets or require an undeclared external service for official scoring; don't assume network access will be available at final judging — document an offline/fallback path.
- Don't attempt catalog modification, use identifiers outside the frozen 50k catalog, reconstruct private-label/removed fields, do real transactions, build a mandatory UI, train a full model, or introduce heavy vector-DB infrastructure — all explicitly out of scope per `docs/competition_specification.md`.
- Don't over-trust our derived understanding of `docs/submission_rules.md`'s exact numeric CPU/memory/timeout limits — this was retrieved via a summarizing fetch, not a forced verbatim dump; re-verify against the local clone before hard-coding any performance assumptions.

## References

**Starter kit / organizer materials (all fetched via WebFetch, read-only, no git operations):**
- Repo root: https://github.com/TechJam2026/techjam-conversational-search
- Repo tree (API): https://api.github.com/repos/TechJam2026/techjam-conversational-search/git/trees/main?recursive=1
- README: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/README.md
- Data attribution: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/DATA_ATTRIBUTION.md
- Data README: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/data/README.md
- Public sessions: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/data/public_set.jsonl
- Agent API contract: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/docs/agent_api_contract.json
- Baseline results: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/docs/baseline_results.json
- Competition specification: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/docs/competition_specification.md
- Evaluation config: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/docs/evaluation_config.json
- Submission rules: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/docs/submission_rules.md
- Evaluator source: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/evaluator/local_evaluator.py
- Starter agent source: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/starter/agent.py
- Evaluator tests: https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/tests/test_evaluator.py
- Release (participant-kit): https://github.com/TechJam2026/techjam-conversational-search/releases/tag/participant-kit and https://api.github.com/repos/TechJam2026/techjam-conversational-search/releases/tags/participant-kit
- Amazon Reviews 2023 dataset site: https://amazon-reviews-2023.github.io/
- TikTok TechJam 2026 event page: https://tiktoktechjam2026.devpost.com/
- TikTok TechJam 2025 recap: https://developers.tiktok.com/blog/tiktok-techjam-2025-highlights

**Prior art:**
- retailGPT repo: https://github.com/unicamp-dl/retailGPT
- Retail-GPT paper: https://arxiv.org/abs/2408.08925
- ecommerce-chatbot (vector search + agents): https://github.com/tomlin7/ecommerce-chatbot
- Rasa e-commerce chatbot examples: https://github.com/ShreyasDatta/e-Commerce-chatbot-rasa , https://github.com/Zaamine/eCommerce_Chatbot-Rasa_Python
- LLM agents as customer simulators: https://arxiv.org/pdf/2509.21501
- Amazon ESCI Shopping Queries Dataset: https://github.com/amazon-science/esci-data , workshop: https://amazonkddcup.github.io/
- KDD Cup 2022 2nd place solution writeup: https://amazonkddcup.github.io/papers/8408.pdf
- EC-Guide (Amazon KDD Cup 2024 solution): https://github.com/fzp0424/ec-guide-kddup-2024
- ProductAgent (conversational product search + clarification benchmark): https://arxiv.org/pdf/2407.00942
- Reference architecture for agentic hybrid retrieval: https://arxiv.org/html/2604.16394v1
- Hybrid search (BM25 + dense) guide: https://denser.ai/blog/hybrid-search-for-rag/
- hybrid-rag reference implementation: https://github.com/tim-ponomarev/hybrid-rag
- Graph-enhanced RAG for e-commerce support: https://arxiv.org/html/2509.14267v1
- Survey: Advances and challenges in conversational recommender systems: https://www.sciencedirect.com/science/article/pii/S2666651021000164
- Survey: Conversational Recommender Systems (ACM): https://dl.acm.org/doi/fullHtml/10.1145/3453154
- ClariQ (clarifying questions dataset/framing): https://github.com/aliannejadi/ClariQ
