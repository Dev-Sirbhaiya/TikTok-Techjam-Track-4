# 06 — Decision Log

Every entry: what was decided, alternatives considered, why, current status. Status values: **KEPT**
(Phase 0/1), **KEPT — GATED** (Phase 2/3+, must win an ablation), **CUT** (rejected, do not build),
**RESOLVED** (was an open question, now answered from ground truth). Numbering (D1, D2...) is carried
over from `/My Ideas/03_DECISION_LOG.md` where the decision is unchanged, so cross-referencing the
original stays easy; new decisions get descriptive IDs (`D-PROFILE`, `D-PACKAGING`, etc.).

---

## Resolved from `/My Ideas/04_OPEN_QUESTIONS.md` — read this section first

Every Tier A/B/C open question from the ideas folder, answered directly from the actual evaluator/
starter-agent source code (not web-fetched docs, not inference) — see `wiki/09_simulator_mechanics.md`
for the full mechanics these answers are drawn from.

**Q1 — Can a turn return both `ask_attribute` AND `recommendations`? → RESOLVED: YES.**
`evaluator/local_evaluator.py`'s `evaluate()` normalizes and scores `recommendations` independently of
`ask_attribute`, and independently uses `ask_attribute` to drive the next customer reply. Decision D14
(combined recommend+ask) is CONFIRMED CORRECT as designed — no fallback to strict either/or needed.

**Q2 — Exact `ask_attribute` enum? → RESOLVED.** `category, material, color, size, style, brand,
budget, feature, use_case, other, null` — exactly the inferred list, confirmed against
`docs/agent_api_contract.json` and the simulator's own `ALLOWED_ATTRIBUTES` set. **New finding not in
the original inference**: `classify_constraint()` has no matching branch for `brand` — asking `brand`
can never surface a constraint via the simulator's reveal logic; it always falls through to the generic
non-answer. Treat `brand` as a structurally weak clarification target (use the catalog's own
`store`/`details` fields directly instead) — see `04_SYSTEM_DESIGN.md`'s question-selector code.

**Q3 — Does the API expose any comparative/click signal? → RESOLVED: NO.** Strictly free-text turns
in both directions; the response schema has no selection/click field at all. Decision D9's text-routed
comparative-feedback design is not just the safer choice, it's the *only* choice — the "if some
structured mechanism exists" branch in the original doc can be deleted.

**Q4 — What do the four scenarios test / how are they weighted? → RESOLVED.** Fixed mix, both public
and private splits (see Q8): 40% Buying (hard constraint disclosed turn 1), 40% Browsing (vague
opener), 15% Intent Override (forced pivot at turn 3 or 4, hit before the pivot never counts), 5%
Boundary (first clarification of any kind gets a one-time non-answer). Per-scenario metrics are
reported separately (`scenario_metrics` in `results.json`) but the **overall `TechnicalScore` is
computed across all sessions combined, not scenario-weighted differently** — confirmed from
`metric_summary()`'s implementation (it's called once on the full session list for the top-level
metrics, and separately per scenario group purely for the breakdown report).

**Q5 — Does the simulated user volunteer unsolicited constraints? → RESOLVED: NO, strictly reactive.**
`customer_reply()` only reveals a constraint when `ask_attribute` matches its keyword classification;
it never volunteers anything beyond the scripted turn-1 disclosure (Buying) and the scripted override
message (Intent Override). This is good news for the design: the "CoSearcher" cooperative-simulator
concern does not apply here — asking well has real, undiminished value.

**Q6 — Is there a per-turn/session token/cost budget enforced by the local evaluator? → RESOLVED: NO.**
`local_evaluator.py` only accumulates and reports `usage` tokens; it does not cap or penalize them in
the scoring formula. Final judging may impose infra restrictions per `docs/submission_rules.md`, but no
numeric limits are published anywhere (see D-LATENCY below) — don't assume the local number reflects a
final-judging guarantee either way.

**Q7 — Does `details` have a consistent per-category sub-schema? → RESOLVED: NO, confirmed by direct
sampling.** Sampled 30,000+ `catalog.jsonl` records grouped by leaf category (e.g. "T-Shirts" n=2807,
"Shoes" n=1299): **zero keys are common to all items even within the same narrow leaf category.**
`details` must be treated as fully generic/unstructured per item — confirms the open-vocabulary
internal slot design (D10) was the right call, not a hedge that turned out unnecessary. **Bonus
finding**: some catalog "leaf categories" are actually store/brand names (e.g. "Westlake") that leaked
into the category taxonomy — a real data-quality quirk worth a defensive note in `retrieval.py`'s
category handling (don't assume every `categories` entry is a genuine taxonomy node).

**Q8 — Are the public 200 and private 800 sessions the same scenario-type distribution? → RESOLVED:
YES.** `docs/competition_specification.md`, verbatim: "Both splits use the same fixed scenario mix" —
directly answers this; dev-session ablation results are a trustworthy predictor of scenario-type
behavior on the private set (the *specific products* differ, the *mechanics and mix* don't).

**Q9 — Is `TechnicalScore = 0.50·HitRate@10 + 0.30·MRR + 0.20·Efficiency` exactly correct? → RESOLVED:
YES, verified against source, not just the README.** `evaluator/local_evaluator.py` lines 279-280:
`efficiency = clip((11-mttc)/10, 0, 1)`, `technical_score = 0.50*hit_rate_at_10 + 0.30*mrr +
0.20*efficiency`. Exact, not approximate.

**Q10 — Does the reported baseline (0.125/0.068/9.81) reflect the public or private set? → RESOLVED:
public set.** We ran `python -m evaluator.local_evaluator` ourselves against `data/public_set.jsonl`
(the default) and reproduced the documented baseline exactly — this is our own regression floor, not
just a claimed number (`wiki/08_evaluation_log.md`).

---

## Retrieval

### D1 — Hybrid retrieval combined via Reciprocal Rank Fusion (RRF), not a weighted sum
**Status: KEPT (Phase 0).** Unchanged from `/My Ideas/` — independently validated by `research/02`'s
survey (RRF sidesteps score-scale calibration between BM25 and cosine similarity entirely). **Caveat
preserved**: verify via ablation if the dense leg is clearly outperforming BM25 alone, since RRF has
documented cases of hurting an already-strong dense retriever by 2-3 nDCG@10 points in one 2026 study.

### D2 — PageIndex-style structural pre-filter over the category tree
**Status: KEPT — GATED (Phase 2, optional), unchanged.** Not a Phase 0 item; the dict-based inverted
index (D1's companion) already gives a cheap structural pre-filter without LLM-navigation latency.

---

## Dialog state, memory, and personalization

### D3 — Multi-interest hypothesis vectors (K > 1)
**Status: KEPT — GATED (Phase 2). Highest-scrutiny item, unchanged.** The correction already present
in `/My Ideas/` (MIND/ComiRec are trained architectures with no reusable checkpoint; this system
inherits the *idea* — K vectors, attention routing, probabilistic fusion — not the *evidence*) stands
and is echoed independently by `research/06`'s session-based-recommendation survey (simple
recency-weighted aggregation baselines are strong and cheap; heavier sequence models show diminishing
marginal accuracy at much higher engineering cost). Mandatory K-sweep ablation unchanged — see
`08_ABLATION_MATRIX.md`.

### D4 — Context distillation as an explicit structured object (`DialogState`)
**Status: KEPT (Phase 0), unchanged in spirit, extended by D-PROFILE below.** This is directly what
the competition's Pillar III language ("Personalized Context Distillation") should mean per both idea
sources independently converging on it.

### D5 — Rejection memory with three-tier confidence
**Status: KEPT (Phase 0), unchanged.** Good design, adopted as-is into `04_SYSTEM_DESIGN.md`. The
"don't auto-infer a specific attribute from implicit signal" correction is preserved and is consistent
with `research/04`'s DST literature on avoiding over-interpretation of weak signals.

### D6 — Question/action selection: information gain (Phase 0) → value-of-information (Phase 2)
**Status: Information gain KEPT (Phase 0), exact formula now specified (`04_SYSTEM_DESIGN.md`'s
`score_entropy`/`_facet_value_entropy`, sourced from arXiv:2509.06185 and the CIKM'13 Probabilistic
Entropy method — `research/05`). Value-of-information KEPT — GATED (Phase 2), correction preserved.**
The critical correction from `/My Ideas/` (never compute against the live-unavailable ground-truth
target rank) is independently reinforced by `research/05`'s entire "live-computable proxy" framing —
this was not a hypothetical bug, it's the exact failure mode the literature also warns against.

### D7 — Two-phase reward: live-observable signal vs. offline target-aware tuning
**Status: KEPT, unchanged.** The split (live = entropy/pool-size only; offline = target-aware terms,
Phase 3's tuning loop) is correct and directly enforced by the fact that the live `Agent.respond()`
genuinely never receives `ground_truth` — verified structurally from `evaluator/local_evaluator.py`
(the target is held in the evaluator's closure, never passed to the agent).

### D10 — Slot representation: open-vocabulary internally, projected onto the fixed enum externally
**Status: KEPT (Phase 0), constraint now fully confirmed (resolved Q2, Q7 above).** No longer
"pending final repo verification" — both the enum and the free-form `details` schema are verified.

### D-PROFILE (new) — "Long-term user profile" = within-session, slower-decaying layer, not cross-session storage
**Status: KEPT (Phase 0/1).** Directly resolves the ambiguity `research/06` flagged in Pillar III's
language, applied to this specific build: implement `preference.py`'s EMA positive/negative affinity
vectors as the "long-term" (slower-decaying) component alongside `DialogState.slots`'s "short-term"
(per-turn) component, both scoped to the single session, both purely in-memory. **Why not literal
cross-session storage**: sessions are isolated single-user interactions with no cross-session
identifier (confirmed independently by `/My Ideas/` D8's reasoning and our own research) — a literal
cross-session profile store would never be exercised or rewarded by the evaluator, and would
additionally require persistence infrastructure the "in-memory only" constraint argues against. This
was a genuine gap in `/My Ideas/`'s docs (heavy on rejection memory and multi-interest, but no explicit
ranking-time preference boost) — added as FR-7 / Phase 0 step 0.8.

---

## Self-evolution / adaptation layers

### D8 — Cross-session hypernetwork/LoRA personalization
**Status: CUT ENTIRELY, unchanged.** Independently confirmed cut by both idea sources' reasoning and
our own research — a rare case of three independent passes (user's original idea, external teammate's
critique, our research) all converging on the same rejection. Strong material for the writeup's
"considered and rejected, here's why" section.

### D9 — Comparative critiquing ("Tinder-style" feedback)
**Status: CUT at implementation time (Phase 3.2, 2026-08-30) — confirmed structurally impossible
against the actual evaluator, not merely deprioritized.** Q3 above already ruled out a *structured*
click/swipe signal; at Phase 3.2 implementation time, direct inspection of the organizer's actual
`evaluator/local_evaluator.py` ruled out the *free-text* fallback too. The complete, exhaustive
space of simulator-generated turns is: `initial_message()` (3 fixed templates: buying hard-constraint,
intent_override pivot, browsing "still exploring") and `customer_reply()` (4 fixed templates: boundary
non-answer, generic nudge on no-attribute-asked, attribute reveal, attribute-exhausted). Critically,
`customer_reply()`'s signature (`sample, ask_attribute, disclosed, boundary_used`) **never receives
the agent's recommendation list at all** — the simulator has no way to reference "the second one" or
critique a specific shown item, comparatively or otherwise, even in principle. There are only 4
scenario types (`boundary`/`browsing`/`buying`/`intent_override`, confirmed via `behavior_for()`), none
of which route through any comparative-language generation path. Building a comparative-feedback
parser would be dead code that can never fire against this evaluator — exactly the class of
unearned complexity `CLAUDE.md` rule 5 prohibits ("don't add abstractions... for scenarios the
competition rules make impossible"), here extended to scenarios *this specific simulator's actual
code* makes impossible. The Rocchio-update engineering caution (bounded, positive-heavy, k≤5) and the
underlying research citation remain correct and worth preserving for the writeup's "considered and
rejected, here's exactly why" section, but nothing is built. If a future session ever revisits this
(e.g. against a different/updated evaluator), re-verify this finding against that evaluator's actual
source before assuming it still holds — this conclusion is evaluator-specific, not a general claim
about the problem domain.

### D11 — Within-session adaptive action policy (contextual bandit)
**Status: KEPT — GATED (Phase 2), unchanged.** The cold-start risk (only ~3-6 real clarification
decisions per session) and warm-start mitigation are preserved; `research/07`'s adaptive-orchestration
survey independently reinforces preferring a small explicit state machine over a free-form learned
policy for exactly this reason — a bandit needs the state machine's signal inputs (candidate count,
score margin) regardless of whether it ships.

### D12 — Decision-path compression and workflow re-orchestration
**Status: KEPT (Phase 0/1), unchanged, now explicitly the mechanism for FR-8.** Confidence-gated
rerank-skip and buying-intent-specificity-driven retrieval breadth are exactly the "adaptive
orchestration" pattern `research/07` recommends: a handful of named, signal-gated branch points inside
an otherwise fixed pipeline, not a free-form controller.

### D13 — Offline SkillOpt-style strategy optimization
**Status: KEPT — GATED (Phase 3), unchanged.** Lower-risk than D3/D11 as originally assessed — it
formalizes what Phase 1's threshold calibration (step 1.3) already does informally.

### D14 — Combined recommend+ask in a single turn
**Status: KEPT (Phase 0), no longer "pending confirmation" — RESOLVED YES (Q1 above).** The turn
policy's `"both"` action is confirmed valid and should be used whenever pool size and confidence allow.

### D-LLM-TIER (new) — Cross-encoder is the guaranteed reranking stage; LLM is an optional booster, never a hard dependency
**Status: KEPT (Phase 0); the optional booster ITSELF implemented and ablated (2026-08-30, Phase
3.5, user-provided key).** The organizer provides no hosted model access or API credits and states a
paid LLM is not required. `/My Ideas/`'s tech-stack table already listed "optional LLM API" for
reranking, but didn't make explicit that Phase 0 must fully function and beat baseline with **zero**
external LLM calls. `research/03`'s benchmark evidence (calibrated cross-encoders matching or beating
general LLM rerankers on this exact task class) means this is not a fallback-quality compromise — it's
the right default even if an API key *is* available. Any LLM usage (slot-extraction arbiter, listwise
rerank booster) must degrade gracefully to the non-LLM path on any failure (timeout, missing key,
exception) — see `04_SYSTEM_DESIGN.md`'s `nlu.py`/`ranker.py` try/except patterns.

**Ablation 4 result (2026-08-30)**: implemented `ranker._llm_listwise_rerank()` for real — Claude
Haiku 4.5, single-pass listwise, only invoked when the cross-encoder's own margin-skip gate doesn't
already fire (i.e., only on genuinely ambiguous shortlists, minimizing calls). Ablated on both
splits: validation (n=40) ON 0.403042 vs OFF 0.375938; training (n=160) ON 0.442173 vs OFF 0.417604
— a consistent win on every metric on both splits, MRR gaining the most (+14.4% on training) exactly
as expected for a reranking mechanism, with zero regressions on any scenario at the larger sample
size. **Enabled by default** (`ranker.ENABLE_LLM_BOOSTER = True`) per Ablation 4's own decision rule.

**Critical caveat, not a formality**: the organizer provides no hosted model credentials for the
official grading run, and `agent.py` only constructs an `llm_client` when `ANTHROPIC_API_KEY` is
present in the environment (this session's own local `.env`, gitignored, never shipped in the
submission). **The official private-set score will almost certainly be measured WITHOUT this key
present**, meaning this entire mechanism is inert during real judging and the guaranteed
cross-encoder-only number (Phase 2 corrected exit, full 200 sessions: TechnicalScore 0.40927) is the
realistic expected submission score, not the boosted number. The boosted result is genuine,
validated, and worth reporting as bonus/stretch capability in the writeup and demo — but must never
be presented as "the" score. See `wiki/08_evaluation_log.md`'s Ablation 4 rows for the full numbers
including a same-configuration full-200-session confirmatory run.

### D-PACKAGING (new) — One implementation, two thin re-export shims
**Status: KEPT (Phase 0).** Resolves a real gotcha neither idea source addressed: local dev evaluation
hardcodes `from starter.agent import Agent` with no override flag (verified —
`wiki/09_simulator_mechanics.md`), while the final submission format is a different standalone layout
(`docs/submission_rules.md`). Real logic lives in `src/copilot/`; `starter/agent.py` and the eventual
`submission/agent.py` are both two-line re-exports. See `04_SYSTEM_DESIGN.md`'s repository layout.

### D-LATENCY (new) — Build defensively against unpublished resource limits
**Status: KEPT (Phase 0/1).** `docs/submission_rules.md` states the organizer "reserves the right to
run your submission under CPU, memory, timeout, and network restrictions" with **no numbers published
anywhere** (confirmed by direct reading, resolving `/My Ideas/`'s Q6-adjacent concern about numeric
limits generally). Design implication: bound candidate-set sizes at every stage (retrieval top-N,
reranker shortlist size), avoid unbounded loops, and keep the no-LLM path (D-LLM-TIER) as the tested
default in case network access is disabled at final judging, per the submission rules' explicit
disclosure requirement.

---

## Process / meta decisions

### D15 — Bare-minimum-first, tiered expansion strategy
**Status: KEPT — governs the whole build plan, unchanged.** Reinforced by the user's own explicit
instruction that Phase 0 must include the full hybrid stack (RRF/retrieval/metadata), not a literal
bare-minimum BM25-only floor — `05_BUILD_PLAN.md` Phase 0 reflects this directly (steps 0.2, 0.7 are
non-negotiable Phase 0 items, not later refinements).

### D16 — Deep-research validation pass before finalizing architecture
**Status: COMPLETED (original pass), EXTENDED by a second, independent 9-agent research pass.** The
independent convergence between the user's/teammate's research pass and this session's separate
9-file research pass (`research/01-09`) on RRF, hybrid retrieval, cross-encoder reranking, entropy-
gated clarification, category-conflict override detection, and cutting cross-session personalization,
is strong signal these are the right calls, not an artifact of one research pass's blind spots.

### D17 (new) — This document supersedes `/My Ideas/` as the ground-truth architecture reference
**Status: KEPT.** `/My Ideas/` is preserved untouched as historical input (excellent input — most of it
survived this merge unchanged). Going forward, `implementation/` is what `CLAUDE.md` and `status.md`
point to for build execution; `/My Ideas/` is not read for day-to-day decisions once this exists.

---

## Codex review findings — architecture synthesis pass (2026-08-29)

First `codex exec review` run against the full `implementation/` corpus (commit `0a0dd8f`), full
report: `wiki/reviews/architecture-synthesis-2026-08-29.raw.txt`. Every finding named here, per the
two-tier review protocol (`05_BUILD_PLAN.md` intro) — none silently fixed without a record.

| # | Severity | Finding | Fixed in | Resolution |
|---|---|---|---|---|
| 1 | P1 | Evaluator shim (`starter/agent.py`) lives inside the entirely-gitignored `external/` vendor clone and is never actually committed; even if it existed, `src/copilot` isn't on `sys.path` when run from there | `04_SYSTEM_DESIGN.md` repo layout | **Fixed**: `tools/install_shim.py` (git-tracked) generates a self-sufficient shim that manipulates `sys.path` itself, run as an explicit setup + `run_eval.py` step — no reliance on a hand-committed file inside gitignored vendor code |
| 2 | P1 | Orchestrator pseudocode only populated `recommendations` for `"commit"`/`"both"`, so every `"ask"` turn was a guaranteed miss (contradicts this corpus's own combined-ask+recommend design rule) | `04_SYSTEM_DESIGN.md` `agent.py` | **Fixed**: recommendations now populated whenever `ranked` is non-empty, independent of action |
| 3 | P1 | Response pseudocode emitted bare `parent_asin` strings; the real contract requires `[{"parent_asin": "..."}]` objects (the local evaluator's permissive normalizer would have hidden this until official scoring) | `04_SYSTEM_DESIGN.md` `agent.py` | **Fixed**: emits proper objects |
| 4 | P1 | `score_entropy()` normalized by plain sum, not an actual softmax — breaks (negative "probabilities", possible log-domain error) once `preference_boost` introduces negative/mixed-sign scores | `04_SYSTEM_DESIGN.md` `overgenerality.py` | **Fixed**: numerically-stable softmax (subtract max before `exp`) |
| 5 | P1 | Phase 5.2 packaging only mentioned source + `requirements.txt`; the guaranteed cross-encoder/dense-encoder models would attempt a download and fail if network access is disabled at final judging (`docs/submission_rules.md` explicitly warns of this) | `05_BUILD_PLAN.md` Phase 5.2/5.3 | **Fixed**: bundle model weights or a tested, network-disabled-verified prefetch step; added an explicit "run once with network disabled" reproducibility check |
| 6 | P2 | Phase 1.3's threshold sweep used all 200 sessions with no held-out split, even though `10_PRE_REGISTRATION.md` already names this exact failure mode (selection and reporting on the same data) — just scoped its split to start at Phase 3.1 instead of Phase 1.3 | `05_BUILD_PLAN.md` step 1.3, `10_PRE_REGISTRATION.md` | **Fixed**: split scope extended to cover any systematic threshold search from Phase 1.3 onward, not just Phase 3.1+ |
| 7 | P2 | `retrieve_candidates()` only used the metadata hard-filter as a `restrict_to` gate active exclusively when `buying_intent_score > 0.6` — so Browsing turns (40% of sessions) got zero metadata contribution, contradicting FR-2/Phase 0's own acceptance criterion | `04_SYSTEM_DESIGN.md` `retrieval.py` | **Fixed**: added `catalog_index.metadata_rank()` as a genuine third RRF fusion leg, always active; the hard-filter gate remains a separate, additional mechanism for high-confidence Buying turns |

**All 7 findings fixed, none declined.** This is exactly the kind of integration bug the phase-level
review tier (added the same day, per user request) is meant to catch before code exists to make them
expensive — all 7 were caught at the design-doc stage, not after implementation.

## Codex review findings — round 2, reviewing the round-1 fixes (2026-08-29)

Second review, against the commit that applied round 1's fixes (`e5c9eab`). Full report:
`wiki/reviews/two-tier-and-viz-2026-08-29.raw.txt`. Second-order issues in the fixes themselves — a
healthy sign the review loop keeps working on its own output, not just first drafts.

| # | Severity | Finding | Fixed in | Resolution |
|---|---|---|---|---|
| 8 | P1 | Round 1's softmax fix used unit temperature over raw RRF scores, which differ only in the thousandths — entropy saturates near 1.0 regardless of actual confidence, defeating the 0.3/0.8 thresholds | `04_SYSTEM_DESIGN.md` `score_entropy()` | **Fixed**: added a `temperature` parameter (scores divided by it before softmax), to be calibrated alongside `low`/`high` in Phase 1.3 |
| 9 | P1 | Round 1's offline-model fix treated "bundle weights" and "prefetch into local cache" as equally valid options — prefetch can't populate a clean scorer's cache if network is disabled before setup runs at all | `05_BUILD_PLAN.md` Phase 5.2/5.3 | **Fixed**: bundling is now required, not optional; prefetch demoted to a dev-only convenience; reproducibility check now tests the submitted bundle itself from a location with no pre-existing cache |
| 10 | P1 | `tools/install_shim.py` was described in `04_SYSTEM_DESIGN.md`'s prose but not required by step 0.1's actual checklist — an executor could reach 0.3 without ever running it | `05_BUILD_PLAN.md` step 0.1 | **Fixed**: shim creation + invocation + an import/evaluator acceptance check added directly to 0.1's checklist |
| 11 | P2 | Phase 1.3's validation-split fix reports the winning config's score only on the 40-session split, making it incomparable to Phase 0's full-200-session exit number | `05_BUILD_PLAN.md` step 1.3 | **Fixed**: added a confirmatory full-200 run of the locked configuration as the actual number compared against Phase 0's exit criteria |
| 12 | P2 | Phase-closeout sequence starts immediately upon reaching a phase's last step, with no check that every step's asynchronously-launched review has actually returned | `05_BUILD_PLAN.md` closeout sequence | **Fixed**: added an explicit barrier step (0) confirming all step-level reviews in the phase are triaged before the phase-level review runs |
| 13 | P2 | Phase 2.5's own text says its work is bundled into Phase 2's commits (no separate builds), but it had its own "Phase 2.5 exit review" diffed against Phase 2's closeout commit — necessarily an empty diff | `05_BUILD_PLAN.md` Phase 2.5 + Phase 3's review base | **Fixed**: Phase 2.5 has no separate phase-closeout; its changes are covered by Phase 2's own review; Phase 3's review base corrected to point at Phase 2's closeout commit |
| 14 | P3 | Frontend viz spec's preference-vector sparkline was described as plotting affinity "magnitude" — but `preference.py`'s EMA re-normalizes to unit length every update, so magnitude is always ≈1 and conveys nothing | `13_FRONTEND_VISUALIZATION.md` | **Fixed**: sparkline now plots turn-over-turn cosine similarity (vector stability) instead — an actually-informative quantity |

**All 7 round-2 findings fixed, none declined.**

## D-EMBED-CACHE (new, self-caught during implementation, 2026-08-29) — Ship precomputed catalog embeddings as a submission asset, not a runtime cost

**Status: KEPT (Phase 0).** While implementing `catalog.py`'s dense-retrieval leg, encoding all
50,000 catalog items through `bge-small-en-v1.5` showed wildly inconsistent throughput in this dev
sandbox: a 500-text synthetic micro-benchmark ran at ~318 texts/sec (implying ~2.6 min for the full
catalog), but the real 50K-item run was still going after 25+ minutes before being killed, and a
second, more carefully instrumented attempt showed the same pattern (fast for the first ~130s of
compute, then degrading well below the benchmarked rate). Text length/diversity differences between
the synthetic benchmark and real catalog text don't plausibly account for a 10x gap on their own —
the most likely explanation is CPU throttling under sustained load in this sandboxed/virtualized
environment (a fast initial burst, then throttling once some credit is exhausted), not a bug in the
encoding code itself.

**Decision**: since the catalog is frozen and read-only for the entire competition (never changes),
its embeddings never need to be computed more than once, ever. Precompute the full
`_catalog_embeddings.npy` matrix once during our own development, and **ship it as a bundled
submission asset** (alongside the bundled model weights already required by D-LATENCY's offline-
packaging fix) rather than relying on `CatalogIndex._ensure_dense_ready()`'s cache-or-compute logic
to work fast (or at all, under a possible time limit) on the official judge's machine. The runtime
code path is unchanged — `_ensure_dense_ready()` still checks for a cache file first — but the
submission now guarantees that cache file is already present, so official scoring only ever hits the
fast `np.load()` branch, never the slow encode branch.

**Action**: add an explicit Phase 0.2 acceptance item (build and commit the embeddings cache once)
and a Phase 5.2 packaging item (the cache file ships with `submission/`, alongside the bundled model
weights). See `05_BUILD_PLAN.md`.

**This does not change any of Phase 0's scored behavior** — it's a deployment/packaging decision
about *when* a one-time, input-independent computation happens, not what the agent does per turn.
