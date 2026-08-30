# 03 — Design Log (Chronological Narrative)

Free-form, dated, append-only. This is where "we tried X, it broke because Y, switched to Z" lives
— the texture that a table of decisions loses. Codex review findings and how they were resolved
also get logged here (with a link to the full report under `reviews/`).

---

## 2026-08-26 — Project scaffolding

- Read and digested the four source docs (`Tiktok_Problem.md`, `Amazon_Dataset_Description.md`,
  `Important_Links.md`, `Tiktok_Mail.md`). Confirmed this is TechJam 2026 Track 4 (Shopping
  Copilot / conversational search), 72-hour build window 2026-08-29 → 2026-09-01.
- Initialized git repo at project root (was not a repo before).
- Verified local tooling: `git 2.49.0`, `python 3.13.7`, `codex-cli 0.147.0` all present.
- Built the living wiki (this directory) and the CLAUDE.md / status.md enforcement rules that keep
  it authoritative across sessions. See DD-001.
- Kicked off import of external resources (participant repo + release kit) and Python venv setup —
  see [07_external_resources.md](07_external_resources.md) for outcome.
- No solution architecture decisions made yet — Pillars I–III design starts once the participant
  kit (starter agent, evaluator, API contract) has been inspected.

## 2026-08-26 — External resource import completed

- Cloned `techjam-conversational-search` into `external/techjam-conversational-search/` at commit
  `9a35be51780ff1caf89eceaabca34259e946f40f` (main).
- `gh` CLI is not installed in this environment, so release assets were listed via the GitHub REST
  API (`curl -s https://api.github.com/repos/TechJam2026/techjam-conversational-search/releases/tags/participant-kit`)
  and downloaded individually with `curl -L`. Three assets on the `participant-kit` tag:
  `catalog.jsonl.gz` (~18.3 MB), `SHA256SUMS`, `techjam-participant-kit.zip` (~18.3 MB). All
  downloaded successfully into `data/participant-kit/`.
- Verified checksums with `sha256sum` against the published `SHA256SUMS` file: **both files match
  exactly** (`catalog.jsonl.gz` → `07fd1426…a0a8f8`, `techjam-participant-kit.zip` →
  `b3d7e283…e5b38ae`). No integrity issues.
- Extracted `catalog.jsonl.gz` (50,000-line catalog) and the participant-kit zip into
  `data/participant-kit/`. Also copied `catalog.jsonl` into
  `external/techjam-conversational-search/data/catalog.jsonl` per the participant repo's own README
  (`data/catalog.jsonl` is gitignored inside that repo, confirming this is the intended local
  placement). The repo clone already shipped `data/public_set.jsonl` (200 labeled dev sessions)
  directly in git.
- Cloned the reference-only `AmazonReviews2023` loader repo into `external/AmazonReviews2023/` at
  commit `b18fdf54bd46013d60799684f7a4eb80d8501d1a`. Not used for the eval itself — kept for
  understanding the upstream data shape only, per the problem statement.
- Set up `.venv/` at project root with `python -m venv .venv` (Python 3.13.7). Checked the
  participant repo for `requirements.txt` / `pyproject.toml` / `setup.py` — none exist. Confirmed by
  reading `starter/agent.py` and `evaluator/local_evaluator.py` that both import only the Python
  standard library, matching the README's explicit claim. No packages needed installing.
  `requirements.txt` at project root documents this (empty of pins, with explanation).
  `requirements-freeze.txt` generated via `pip freeze` — empty, as expected.
- Sanity check: ran `python -m evaluator.local_evaluator` from
  `external/techjam-conversational-search/` inside the venv. It executed cleanly on the first try —
  no errors, no missing docs. Output matched the repo's documented baseline
  (`docs/baseline_results.json`) exactly: Hit Rate@10 `0.125`, MRR `0.068034`, MTTC `9.81`,
  Efficiency `0.119`, TechnicalScore `0.10671`, over the 200 public sessions (scenario breakdown:
  boundary/browsing/buying/intent_override all present in `results.json`). This confirms the whole
  pipeline (catalog + sessions + starter agent + evaluator) is wired correctly end to end.
- No blockers encountered. Everything in this step completed without issue — nothing to add to
  `status.md`'s Blockers section from this pass.
- Current state: `external/`, `data/participant-kit/`, `.venv/`, `requirements.txt`, and
  `requirements-freeze.txt` are all in place and untracked (per `.gitignore`) except the two
  requirements files at repo root, ready for the coordinating session to review/commit. Solution
  architecture work can now start from an inspected, verified, runnable baseline.

## 2026-08-26 — Deep research phase: 9 parallel agents + ground-truth verification

- User asked for deep parallel research across the problem statement's technical dimensions before
  any ideation/implementation, plus thorough codebase/dataset understanding. Launched 9 parallel
  research agents (general-purpose, web/arXiv/GitHub access) into `research/01-09_*.md`, each
  ending in topic-scoped Dos/Don'ts: intent routing, hybrid in-memory retrieval, LLM reranking,
  dialogue state tracking, clarification generation, context distillation/personalization, adaptive
  orchestration, evaluation-metric literature, and prior art + starter-kit online inspection.
  All 9 completed successfully with no blockers; full citation trails in each file.
- In parallel, personally read the actual cloned participant repo's evaluator source
  (`evaluator/local_evaluator.py`), starter agent (`starter/agent.py`), competition spec,
  submission rules, and evaluation config — this is ground truth, not inference, and is now
  captured in `wiki/09_simulator_mechanics.md` (new page). Key findings: category is disclosed in
  100% of session openers regardless of scenario; the simulated customer only reveals constraints
  when `ask_attribute` matches its exact `classify_constraint()` keyword taxonomy; a hit before an
  Intent Override's scripted turn never counts; budget/brand are structurally weak clarification
  channels (rarely survive the intent-card's candidate-slicing); local dev evaluation hardcodes
  `from starter.agent import Agent` with no override flag, while the final submission format is a
  different standalone layout — both need to stay in sync via a shared implementation module.
  Independently, research agent 9's own WebFetch-based inspection of the same repo converged on
  the same facts (good cross-validation of the research methodology).
- Directly confirmed the TechnicalScore formula against source (`evaluator/local_evaluator.py`
  lines 279-280), not just the README, resolving research agent 8's flagged uncertainty:
  `TechnicalScore = 0.50×HitRate@10 + 0.30×MRR + 0.20×Efficiency`,
  `Efficiency = clip((11-MTTC)/10, 0, 1)`. HitRate@10 has the largest weight and gates MRR
  mathematically (MRR ≤ HitRate@10), making retrieval coverage the highest-ROI first investment.
  Logged onto `wiki/00_problem_statement.md`.
- Synthesized all 9 research files plus the ground-truth mechanics into
  `research/DOS_AND_DONTS.md` — a single master Dos/Don'ts organized by pillar, deduplicated,
  distinguishing `[GROUND TRUTH]` (verified against actual code) from `[RESEARCH]` (literature-
  derived judgment). No architecture decisions made yet — per the user's explicit instruction,
  this phase was research-only; next step is ideation with the user before anything gets written
  into `wiki/01_architecture.md`.
- Note: `codex exec review` remains blocked (auth token revoked, see `status.md` Blockers) — this
  research phase's commit has not been through a codex review; will be included in the backlog
  once `codex login` is run.

## 2026-08-29 — Architecture decided: `implementation/` corpus built, all open questions resolved

- Challenge window opened (2026-08-29 12:00). `codex login` was run by the user — `codex exec review`
  is now authenticated and working (v0.150.1), unblocking the review backlog noted above.
- User added `/My Ideas/` — a 10-file independent design + research pass (MYIDEA.md brainstorm plus a
  structured `01_ARCHITECTURE.md` through `08_ADVANCED_PHASES.md`, and two CLAUDE.md drafts), explicitly
  flagged by the user as "not ground truth." Read and cross-checked in full: it independently converged
  on much of our own research (RRF over weighted-sum, three-tier rejection memory, cutting cross-session
  personalization, ablation-gated ambitious ideas) — strong signal these calls are right, not an
  artifact of one research pass. It also left 10 explicit open questions (Q1-Q10) about the real API
  contract, unverified against the actual repo.
- Directly sampled 30,000+ `catalog.jsonl` records (grouped by leaf category) to resolve Q7: confirmed
  `details` has **zero keys common to all items even within one narrow leaf category** — genuinely
  unstructured, no reliable per-category schema. Bonus finding: some catalog "leaf categories" are
  actually store/brand names (e.g. "Westlake") that leaked into the taxonomy — a data-quality quirk
  worth defensive handling.
- Resolved all 10 of `/My Ideas/04_OPEN_QUESTIONS.md`'s questions directly against
  `evaluator/local_evaluator.py` and the competition spec (not inference) — most importantly: combined
  ask_attribute+recommendations in one turn IS supported (Q1), the enum is exactly as inferred but
  `brand` has no matching reveal-logic branch (Q2), the API is strictly free-text with zero click/
  comparative channel (Q3), and both public/private splits share the same scenario mix (Q8).
- Built `implementation/` (12 documents: problem framing, PRD, system architecture with a mermaid
  diagram, system design with pseudocode, a phased build plan numbered 0.1-5.5, a decision log
  resolving every open question, risk register, ablation matrix, supervisor questions, pre-registration,
  future work, and a one-page build memo) — the new authoritative architecture/build reference,
  superseding `/My Ideas/` (kept untouched as historical input) and filling one real gap it had (no
  explicit within-session preference-vector ranking boost for Pillar III's "long-term profile" language
  — added as `D-PROFILE`).
- Updated `CLAUDE.md` (§1a) so "run Phase 0" / "run step N.M" unambiguously maps to
  `implementation/05_BUILD_PLAN.md` and inherits the commit/codex-review/wiki-update loop automatically.
  Updated `wiki/01_architecture.md` to point to the decided design instead of a placeholder.
- No implementation code written yet — this was architecture/planning synthesis only, per the explicit
  build-order discipline both idea sources and our own research converge on (floor first, ambitious
  ideas ablation-gated).

## 2026-08-29 (cont.) — Phase 0 implementation: `src/copilot/` written, 21 tests passing, one real environment issue found

- User invoked `/goal` to start Phase 0 implementation. Wrote the full `src/copilot/` package per
  `implementation/04_SYSTEM_DESIGN.md`: `state.py`, `catalog.py`, `nlu.py`, `intent_router.py`,
  `retrieval.py`, `rejection_memory.py`, `preference.py`, `overgenerality.py`, `ranker.py`,
  `turn_policy.py`, `phrasing.py`, `logging_.py`, `agent.py`, plus `tools/install_shim.py` and
  `tools/run_eval.py`. 21 fast unit tests (`tests/test_smoke.py`) all passing.
- Caught and fixed 6 real bugs during implementation, before any codex review touched this code
  (logged in full in the commit message and `implementation/06_DECISION_LOG.md`): a BM25 full-scan
  instead of an inverted index, an O(n) embedding lookup instead of a dict, retrieval losing
  accumulated context on "no new info" turns, multiple revealed values overwriting each other in one
  slot key, a turn-policy scale-mismatch risk, and slow catalog dense-embedding text.
- **Real environment issue found and documented (D-EMBED-CACHE)**: encoding the full 50K-item
  catalog through `bge-small-en-v1.5` showed wildly inconsistent throughput in this dev sandbox — a
  500-text synthetic benchmark ran at 318 texts/sec, but real diverse catalog text stabilized at a
  much lower ~42-50 texts/sec (confirmed via a controlled 200/1000/3000/6000-sample test, not
  degrading further at scale — so a bounded, finite rate, not runaway throttling as first suspected
  from two premature kills at 25 min and 60 min). Full 50K catalog ≈ 18-20 min one-time cost.
  Decision: since the catalog is frozen for the whole competition, precompute this once and **ship
  the cached embeddings matrix as a submission asset** rather than relying on it being fast (or even
  completing within a time limit) on the official judge's machine — added to `05_BUILD_PLAN.md`
  Phase 0.2 and Phase 5.2.
- Committed (`90d6501`); phase-level codex review and the real 200-session evaluator run were both
  kicked off in parallel — results in the next log entry.

## 2026-08-29 (cont.) — Phase 0 CLOSED OUT: review triaged, fixes applied, honest benchmark comparison

- Codex review of the full Phase 0 implementation (`wiki/reviews/phase0-implementation-2026-08-29.md`)
  returned 7 real findings (4 P1, 3 P2), all fixed (`aa41ca2`), none declined: clarification declines
  were being misread as rejections (corrupting ranking after every unproductive question); `feature`/
  `style`/`size`/`use_case` facets were never populated so they could never be asked about; raw
  per-item price unfairly dominated unnormalized entropy comparisons (fixed via bucketing AND a
  general distinct-value-count cap, since the newly-populated `feature` facet would have reintroduced
  the same problem with near-unique text); a cache-write failure discarded already-computed
  embeddings, risking a full 50K-item recompute on every candidate lookup; forced overrides didn't
  reset preference vectors; category indexing didn't comma-split the way the evaluator's own
  `coarse_category()` does; and a word-boundary bug misclassified text like "Water Resistant" as
  color=tan. 5 new regression tests added (26 total, all passing).
- **Honest before/after benchmark, not just "reviewed, fixed, done"**: the pre-fix run scored
  TechnicalScore 0.353; the post-fix run scored 0.328 — a real, measured *drop*, driven mainly by the
  buying scenario (0.3625→0.3125 HitRate@10) while intent_override *improved* as expected (0.367→0.4,
  matching the preference-vector-reset fix). Kept the fixes anyway: all 7 are genuine correctness bugs
  verified independently of their score effect, and shipping known-wrong behavior because it happened
  to score higher on this one 200-sample dev set would be reward-hacking this specific sample, not
  building a system that generalizes to the private 800-session set's different products. Flagged the
  buying-track regression explicitly as a Phase 1.3 calibration target (`wiki/08_evaluation_log.md`)
  rather than either hiding it or reverting correct fixes to chase a number.
- **Phase 0 exit criteria met**: TechnicalScore 0.328 clears both the pre-registered floor (beat
  baseline's 0.107) and stretch target (≥0.25) from `implementation/10_PRE_REGISTRATION.md`, on all
  200 public dev sessions, no crashes. Treating the single comprehensive review already run (which
  covered the entire Phase 0 diff from scratch) as satisfying the phase-level review requirement,
  given it was run against the accumulated implementation, not an individual step — no separate
  redundant third review before moving on, per the user's explicit direction to keep iterating.
- User set a broader `/goal`: continue directly through Phase 1, 2, 3 (each with its own codex
  review + benchmark), not stopping to ask between phases. Proceeding to Phase 1 next.

## 2026-08-29 (cont.) — Phase 1 CLOSED OUT: calibration recovers the buying regression, +24.5%

- Steps 1.1/1.2 (audit RRF purity, entropy formula) needed no changes — already correct from
  Phase 0's own review fixes. Step 1.3: created the pre-registered train/validation split
  (`tools/make_split.py`) and a split-aware eval runner (`tools/run_eval_split.py`). Step 1.4:
  added `orchestrator.py` — named, logged adaptive decision points (`retrieval_breadth`,
  `rerank_depth`, `turn_action`), moving the hard-filter strategy decision out of `retrieval.py`
  (now a pure mechanism) per FR-8.
- Codex review (`wiki/reviews/phase1-1.1-1.4-2026-08-29.raw.txt`) found 4 real issues, all fixed:
  the facet distinct-value cap fix from Phase 0 didn't scale down (a near-unique facet in a
  *small* reranked pool could still slip under the absolute cap) — added a distinct-value/pool-size
  ratio gate (≤0.5) that catches it at any pool size; the split's hash-threshold produced 35/165
  instead of the pre-registered 40/160 — fixed to sort-and-take-exactly-N; the orchestration trace
  recorded the pre-fallback action, disagreeing with what was actually sent — moved after fallback
  resolution; and the architecture wiki was stale relative to the actual Phase 1.4 state.
- **Discovered mid-fix**: background evaluator runs were being killed externally three times in a
  row for unclear reasons (not by this session), while the earlier Phase 0 full-200 runs had
  completed fine as background tasks — switched to running the evaluator in the **foreground**
  instead (accepting the tool's ~10-minute cap, with the harness auto-backgrounding runs that
  exceed it), which completed reliably. Worth remembering if evaluator runs mysteriously stall again.
- **Full Phase 1 exit result (200 sessions, locked config): TechnicalScore 0.4087** — up from Phase
  0's 0.328379 (+24.5%). Every scenario improved with zero regressions, and critically, **the
  buying-track regression flagged at Phase 0 exit fully recovered** (0.3625, matching Phase 0's
  original pre-bug-fix number, but now with the underlying bugs actually fixed, not just working
  around them). Validated on the held-out 40-session split first (0.382, consistent with training's
  0.402 — no overfitting to the sweep) before locking the configuration in.
- Phase 1 exit criteria (`05_BUILD_PLAN.md`): no regressions vs. Phase 0 — met and substantially
  exceeded. Proceeding directly to Phase 2 per the user's standing `/goal`.

## 2026-08-30 — Phase 2 CLOSED OUT: one kept, two honestly cut, +0.6% net

- Implemented and ablated all three Phase 2 items on the 40-session validation split (fast
  iteration; full-200 confirmatory run reserved for the final locked configuration):
  - **2.3/2.5 retriever-disagreement VoI signal** (`phase2/voi.py`, using
    `retrieval.retriever_disagreement` — a live-computable BM25/dense overlap measure, never the
    ground-truth target rank per D6/D7): modest, consistent win (TechnicalScore/MRR/MTTC all favor
    it, HitRate@10 tied). **KEPT.**
  - **2.1 multi-interest hypothesis vectors** (`phase2/multi_interest.py`, K=2 vs K=1): K=1 won on
    every single metric. **CUT**, exactly matching D3's a priori risk assessment that multi-interest
    can hurt when sessions aren't genuinely multi-faceted (true here — each session has one hidden
    target, not multiple competing interests to disambiguate).
  - **2.2 contextual bandit action policy** (`phase2/action_policy.py`, warm-started from a
    ground-truth-derived prior, not cold): OFF won on every single metric. **CUT**, matching D11's
    a priori cold-start-risk assessment (only ~3-6 real clarification decisions per session — not
    enough signal for within-session adaptation to help, and the warm-start prior alone wasn't
    enough to compensate).
  - Both cut modules are kept in the tree, disabled by their own flags, as a genuine "tried,
    measured, cut" record — explicitly sanctioned as valuable Technical Execution material by
    `implementation/08_ABLATION_MATRIX.md`, not something to hide.
- **Codex review** (`wiki/reviews/phase2-2.1-2.3-2026-08-30.raw.txt`) — 3 findings, all fixed, none
  declined (commit reviewed: `9a9659e`). Codex's own summary: "the gated bandit path records a
  capped, usually invariant pool size and can replay stale rewards, so its behavior and ablation
  conclusion are unreliable. The new multi-interest tests are also order-dependent and one fails
  when executed alone."
  1. **[P2] Bandit reward measured an already-capped pool** (`agent.py:133`/`:114`, pre-fix):
     `decide_rerank_depth()` caps `ranked` at exactly 50 whenever the pool exceeds 20, and the
     bandit's reward comparison used `len(ranked)` on both sides — so `pool_size_at_ask` and the
     next turn's comparison pool were both saturated at 50 far more often than not, reporting a
     false zero-reduction reward regardless of how much the clarification actually narrowed the
     real candidate set. **Fixed**: both sides now use `len(candidates)`, the pre-rerank-cap,
     post-filter pool computed earlier in the same turn.
  2. **[P2] Stale bandit outcome replayed across turns** (`agent.py:113-114`, pre-fix):
     `pool_size_at_ask` was never cleared after being consumed, so an ask followed by one or more
     non-ask turns kept re-recording the same stale outcome against each subsequent turn's
     unrelated pool until the next ask overwrote it — repeatedly biasing the learned utility
     estimate on every session with a multi-turn gap after a clarification. **Fixed**: `agent.py`
     now sets `state.pool_size_at_ask = None` immediately after `record_outcome()` runs, so each
     ask contributes exactly one reward.
  3. **[P2] Test flag leak made the multi-interest suite order-dependent**
     (`tests/test_smoke.py:214-215`, pre-fix): `test_multi_interest_k1_fallback_matches_single_ema`
     restored `ENABLE_MULTI_INTEREST` to a hardcoded `True` in its `finally` block instead of the
     actual original value (`False`, the real post-ablation production default) — leaking a flipped
     flag into every test that ran after it in file order. Fixing the leak exposed a second, latent
     bug in the very next test (`test_multi_interest_spawns_second_hypothesis_on_divergence`), which
     had been passing only by silently riding on that leak and failed immediately once it was
     removed. **Both fixed**: the first test now saves/restores the real original value; the second
     now explicitly sets `ENABLE_MULTI_INTEREST = True` itself (with its own save/restore) as its
     own precondition, matching the existing correct pattern already used by the action-policy test
     two functions below. Verified order-independent afterward (`pytest -k multi_interest` run
     standalone, and the full 34-test suite, both green).
  - **Re-ablation, not just a fix**: since findings 1-2 meant the Phase 2.2 bandit's reported
    "OFF beats ON" conclusion was reached with a demonstrably broken reward signal, re-ran the
    40-session validation-split ablation with `ENABLE_ACTION_POLICY` forced back to `True` on top of
    the fixed reward tracking, rather than assuming the original verdict still held. Result: ON got
    **worse**, not better, once measured honestly — TechnicalScore 0.359467/HitRate@10 0.425/MRR
    0.261558/MTTC 7.575, vs. the already-cut OFF number of 0.402/0.475/0.297/7.225, and vs. the
    original *buggy*-measurement ON number of 0.3693/0.425/0.291. The cut verdict was not an
    artifact of the measurement bug — it holds, more decisively, once the bug is fixed. Flag
    reverted to `False` (unchanged shipped configuration); since `ENABLE_ACTION_POLICY=False` makes
    `record_outcome()`/`utility_multiplier()` no-ops regardless of what's stored in
    `pool_size_at_ask`, the fix is provably behavior-neutral in the actual shipped config, so no
    full-200-session re-run was needed to confirm no regression there.
- **Full Phase 2 exit result (200 sessions, locked config): TechnicalScore 0.411066** — up from
  Phase 1's 0.408714 (+0.6%, a modest net gain, consistent with the single kept feature itself
  being a modest win). Three of four scenarios improved (boundary, browsing, buying); intent_override
  dropped (0.433→0.367) — flagged honestly, not chased further given n=30's noise floor (±3.3pp per
  session) and the clear net-positive elsewhere; a candidate for a future calibration look, not a
  blocker. Unaffected by the codex-review fixes above (bandit stays disabled in the shipped config).
  **SUPERSEDED — see the 2026-08-30 (cont.) "Phase 3.1: reproducibility bug" entry below**: this
  number was measured before a hash-seed nondeterminism bug was found and fixed; the corrected,
  now-reproducible number is 0.40927, and the VoI signal (this run's one "kept" feature) turned out
  to have zero real effect once the bug was fixed. Kept here for the historical record, not as the
  current truth.
- Proceeding to Phase 3 per the user's standing `/goal`.

## 2026-08-30 (cont.) — Phase 3.1: reproducibility bug found and fixed, all three Phase 2 items re-ablated, one reversed

While starting Phase 3.1 (offline strategy tuning — rollout/score/edit/validate over the
train/validation split), the very first step (timing a clean baseline run, then running it again
inside the round-1 tuning sweep) surfaced a serious bug: **running the identical config against the
identical 160-session training split twice produced different TechnicalScores** (0.405035, then
0.416775 for literally the same defaults). A follow-up on the faster 40-session validation split
confirmed it wasn't a fluke (0.363217 vs 0.382717, still non-reproducible even after the first,
partial fix below). Traced to Python's hash randomization: `set` iteration
order is randomized per process (`PYTHONHASHSEED`) unless fixed, and several places in the retrieval
path relied on a `set`'s iteration order without realizing it:
- `catalog.build_gazetteer()`'s `colors`/`materials` vocabularies were plain sets; `nlu.py`'s
  `_gazetteer_fallback_extract()` and `rejection_memory.py`'s `detect_rejection_signal()` both
  iterate them with "first regex match wins, then stop" semantics — a message matching two gazetteer
  terms (e.g. "no gold or silver") could silently extract a different one depending on process luck.
- `catalog.CatalogIndex.bm25_search()` iterated `q_tokens` (a `set`) directly, so the
  floating-point summation order feeding each candidate's BM25 score — and, more importantly, which
  candidate got inserted into the `scores` dict first — depended on hash order, deciding tie-breaks
  in the final `sorted()` differently across runs.
- `catalog.CatalogIndex.metadata_rank()` iterated per-category/per-brand id `set`s the same way,
  affecting `Counter.most_common()`'s tie-break order among equal-score candidates.
- All three feed `retrieval.reciprocal_rank_fusion()`, which is itself deterministic *given*
  deterministic inputs — so the bug was entirely upstream, in these three call sites.
**This was NOT just a Phase 3.1 tooling problem — it meant the shipped agent's behavior on the
frozen, deterministic customer simulator was itself non-deterministic**, a real risk for however
official judging invokes the evaluator against the private 800-session set. Fixed at the source
(not by setting `PYTHONHASHSEED` in a local test harness, which wouldn't protect the actual
submission under an invocation this project doesn't control): gazetteer colors/materials are now
sorted tuples; `bm25_search` iterates `sorted(q_tokens)`; `metadata_rank` iterates `sorted(ids)`.
Verified fixed by running the identical config twice more — byte-identical results, both times.

**Given the bug's noise magnitude (~2-4pp on the 40-session split) was comparable to or larger than
several of Phase 2's reported ablation margins, honestly re-ran all three Phase 2 ablations with the
fixed, now-deterministic code** rather than assuming the original verdicts still held:
- **VoI retriever-disagreement signal** (previously "KEPT", a reported modest win): re-tested ON vs
  OFF on both the validation split (n=40) AND the training split (n=160) — **byte-identical results
  in both cases, 200 sessions total, zero difference to 6 decimal places**. The original "modest
  win" was entirely a noise artifact of the nondeterminism bug, not a real effect. **Reversed to
  CUT** — a null result doesn't earn a feature its keep.
- **Multi-interest (K=2)** (previously "CUT", K=1 reportedly won every metric): re-tested on the
  validation split — again byte-identical to K=1. Not a bug this time: `MultiInterestState` only
  spawns a second hypothesis when cosine similarity drops below `SPAWN_THRESHOLD=0.35`, and
  apparently no session in this dataset ever produces two positive-signal turns divergent enough to
  cross it — consistent with D3's original a priori read that these sessions have one coherent
  hidden target, not genuinely competing interests. Verdict **unchanged (CUT)**, but for a cleaner
  reason: not "K=2 hurts", but "K=2 never has the opportunity to differ from K=1 on this data."
- **Contextual bandit** (previously re-ablated once already after its own reward-tracking fix,
  reporting ON=0.359 vs OFF=0.402 — a large gap): re-tested once more on the validation split with
  the full determinism fix — ON=0.376509 vs OFF=0.375938, a negligible, mixed-sign difference.
  Verdict **unchanged (CUT)** — no measurement of this mechanism, across three attempts, has ever
  shown a real win, and D11's a priori cold-start-risk case stands on its own regardless of margin.
- Fixed a resulting test bug: `test_adjusted_clarify_threshold_lowers_bar_on_disagreement` assumed
  VoI's old enabled-by-default state; now force-enables the flag with save/restore, matching the
  pattern already used for the other two gated mechanisms' unit tests.

**Corrected Phase 2 exit result (full 200 sessions, all three items now disabled, deterministic
code): TechnicalScore 0.40927, HitRate@10 0.49, MRR 0.278234, MTTC 6.96** — confirmed byte-identical
to a second full run. Effectively unchanged from the original (buggy-measurement) 0.411066 at this
sample size (large-n averaging diluted the bug's impact here, even though it was large enough to
flip conclusions at n=40) — Phase 1→2's net trend holds, but the mechanism (VoI) is no longer part
of the story; Phase 2 is now honestly a "tried three things, all three didn't earn their keep, net
neutral vs. Phase 1" phase, not a "one small win" phase. This is a materially different, more
accurate story for the eventual writeup, and a good example of why the pre-registration's
train/validation discipline (and, now, a determinism check) matters.

Also incidentally found and fixed during the same pass (self-caught, not from this bug):
`overgenerality.should_clarify()` had a `high` parameter (default 0.8) that was never referenced in
the function body — dead since Phase 0, carried unnoticed into `implementation/04_SYSTEM_DESIGN.md`'s
own pseudocode. Removed rather than wired in with invented semantics (no design doc ever specified
what an upper entropy ceiling should do). Also introduced `src/copilot/strategy_config.py`,
centralizing the thresholds Phase 3.1 tunes (previously hardcoded literals scattered across
`overgenerality.py`/`agent.py`/`phase2/voi.py`) behind env-var overrides, and
`tools/tune_strategy.py`, a reusable rollout→score tool.

**Codex review** (`wiki/reviews/phase3.1-determinism-fix-2026-08-30.raw.txt`, reviewing commit
`7be9ba7`) — 1 finding, fixed: `tune_strategy.py`'s subprocess environment wasn't isolated from the
invoking shell (`dict(os.environ)` let an inherited `COPILOT_*` variable silently leak into any
candidate that omits that key, including `baseline: {}`, without appearing in the logged config).
Verified no actual contamination occurred in this session's runs (no such variables were ever set),
but fixed anyway for correctness — the harness now explicitly clears every managed variable before
applying each candidate's overrides.

**Phase 3.1's actual tuning sweep, now run with the fixed harness**: systematically searched
`should_clarify`'s three knobs (`CLARIFY_BASE_LOW`, `CLARIFY_MIN_POOL_TO_BOTHER`,
`CLARIFY_NO_ASK_AFTER_TURN`) against both splits. Result: every candidate in a wide, sensible range
matched the hand-set Phase 0/1.3 defaults byte-for-byte (e.g. `CLARIFY_BASE_LOW` tested at
0.01/0.2/0.3/0.4/0.5/0.7 all identical); only genuinely extreme values degraded performance sharply
(`CLARIFY_BASE_LOW=0.99` → TechnicalScore 0.188 on training; `CLARIFY_NO_ASK_AFTER_TURN=2` → 0.219
on validation). This is a real, systematically-verified finding, not an inconclusive search: the
existing defaults sit in a wide, robust operating region with comfortable margin before any cliff,
and no candidate beat them on held-out data — per Ablation 3's own decision rule, **the defaults are
kept unchanged**. Phase 3.1 is closed out on this basis.

## 2026-08-30 (cont.) — Phase 3.2 (comparative feedback): confirmed structurally impossible, cut

Before implementing 3.2's Rocchio-style comparative-feedback parser, checked its premise directly
against the organizer's actual `evaluator/local_evaluator.py` rather than assuming the build plan's
framing still held. Result: it doesn't. `customer_reply(sample, ask_attribute, disclosed,
boundary_used)` — the complete function that generates every non-opening simulator turn — never
receives the agent's recommendation list as an argument at all, so the simulator has no way to
reference "the second one" or critique a specific shown item, comparatively or otherwise, even in
principle. Read both `initial_message()` and `customer_reply()` in full: the exhaustive set of
possible simulator turns is 3 opening templates (buying hard-constraint, intent_override pivot,
browsing "still exploring") and 4 reply templates (boundary non-answer, generic nudge when no
attribute was asked, attribute reveal, attribute-exhausted) across the 4 confirmed scenario types
(`boundary`/`browsing`/`buying`/`intent_override`, verified via `behavior_for()`). None of these
paths generates comparative language.

Building a parser for input the simulator can never produce would be dead code — exactly the
unearned-complexity class `CLAUDE.md` rule 5 prohibits, extended here from "the competition rules
make it impossible" to "this specific evaluator's actual code makes it impossible." **Cut, not
deferred** — full reasoning in `implementation/06_DECISION_LOG.md`'s revised D9 entry and
`implementation/05_BUILD_PLAN.md`'s step 3.2. The underlying engineering caution (bounded,
positive-heavy Rocchio update, k≤5, from the negative PRF/query-drift literature `/My Ideas/` D9
cited) remains correct and documented for the writeup even though nothing was built against it.

**Phase 3 is closed out on this basis**: 3.1 shipped (defaults confirmed robust, unchanged), 3.2
confirmed impossible and cut. No change to the scored `Agent`'s runtime behavior occurred during
Phase 3.1/3.2's own work (only tooling/`strategy_config.py` comments and doc updates) — the
corrected Phase 2 exit number (`TechnicalScore 0.40927`, commit `7be9ba7`) stands unchanged as
Phase 3's exit number too; re-running the full 200-session evaluator would be redundant, not more
correct, since nothing in the actual code path changed.

**Phase 3's exit codex review (`--base 4aeaaff`) failed 3 consecutive attempts** for
environment/sandbox reasons (Windows `pwsh.exe` `CreateProcessAsUserW` access-denied errors, then a
sandboxed Python `tempfile` failure) — logged as a blocker in `status.md`, not silently skipped. The
phase's one substantive logic commit (`7be9ba7`) already got a full, successful per-commit review.

## 2026-08-30 (cont.) — Phase 3.5: real LLM listwise reranker, Ablation 4, a genuine +6.4% win

User provided a personal `ANTHROPIC_API_KEY` (added to a new, gitignored `.env` at the repo root;
`anthropic`/`python-dotenv` added to `requirements.txt`) and asked explicitly for higher accuracy,
given the stakes of a worldwide competition. This unblocked implementing `ranker.py`'s previously-
stubbed `_llm_listwise_rerank()` for real: a single-pass listwise Claude Haiku 4.5 call (numbered
candidate list + accumulated query, asked for a best-to-worst permutation), invoked only when the
cross-encoder's own margin-skip gate doesn't already fire (i.e., only on genuinely ambiguous
shortlists — minimizing API calls), with the existing `except Exception: pass` fallback to
cross-encoder order on any failure (NFR-2, unchanged). `Agent.__init__` now constructs an
`anthropic.Anthropic` client only when `ANTHROPIC_API_KEY` is present (via `python-dotenv`), else
`None` — never a hard dependency.

**Ran Ablation 4 for real** (previously never measured, since no key was available before now):
validation split (n=40) ON 0.403042 vs OFF 0.375938; training split (n=160, confirmatory) ON
0.442173 vs OFF 0.417604 — a consistent win on every metric on both splits, MRR gaining the most
(+14.4% on training, exactly matching the ablation's own "watch MRR primarily" expectation), with
zero regressions on any scenario at the larger sample size (buying and intent_override, flat at the
smaller validation split, both improved once the training split's larger sample gave the booster
enough ambiguous turns to engage). **Enabled by default** (`ranker.ENABLE_LLM_BOOSTER = True`).
Full 200-session confirmatory run: **TechnicalScore 0.43531, HitRate@10 0.51, MRR 0.321032, MTTC
6.8** — +6.4% over the guaranteed cross-encoder-only baseline, every scenario improved.

**Critical caveat, reported honestly rather than oversold**: the organizer provides no hosted model
credentials for official grading, and this key exists only in this session's local, gitignored
`.env` — never shipped in the submission. **The official private-set score will almost certainly be
measured without this key present**, meaning `llm_client` is `None` and this entire mechanism is
inert during real judging. The guaranteed, always-applicable number remains the cross-encoder-only
baseline (TechnicalScore 0.40927). This is genuine, validated, submittable-as-bonus-capability
material for the writeup and demo — "built and ablated an optional LLM reranking tier, +6.4% when
available" — but must never be presented as the expected competition score. Documented in
`implementation/06_DECISION_LOG.md` D-LLM-TIER and `08_ABLATION_MATRIX.md` Ablation 4.

**User pushed back explicitly**: "beats baseline" isn't good enough for a worldwide competition;
wants genuine accuracy pushed further, on the GUARANTEED (no-API-key) path specifically since that's
what's actually scored. Ran the cheap uncertainty-calibration check from Phase 3.5's own scoping
note (`tools/calibration_check.py` — joins the per-turn log against evaluator results by execution
order, since the evaluator never exposes `sample_id` to the Agent) against the full 200 sessions.
**Finding**: only 101/200 sessions ever reach a genuinely FORCED commit (the rest hit earlier while
still on an "ask" turn, since recommendations are always populated regardless of action); of those
101, **100% sit at high commit-time entropy (0.7-1.0) and hit at a dismal 2.97% rate**. This directly
identifies where the system fails hardest: forced-commit-while-still-ambiguous sessions.

**Ablation 6 — portfolio/slate hedging** (`phase2/slate_hedging.py`), built specifically to target
that finding: on a forced commit above the entropy threshold, reserve the top 60% of slots for pure
best-by-score, fill the remainder by greedily maximizing facet diversity (color/material/style/
category) among the rest of the ranked pool, hedging against the single most-likely interpretation
being wrong. Original build-plan framing ("esp. if 2.1's multi-interest is kept") no longer applies
since multi-interest was cut in Phase 2 — evaluated on its own merits instead. Result: validation
split flat (too few forced-commit sessions at n=40 to show it), training split (n=160) a real win —
TechnicalScore +1.9%, HitRate@10 +2.5%, gains concentrated in `buying` (+7.7% hit rate) exactly
matching the calibration diagnosis, zero regressions. **Enabled by default.** Full 200-session
guaranteed-path confirmatory run: **TechnicalScore 0.415731** (up from 0.40927) — this is on the
guaranteed path, so it's a real improvement to the expected competition score, not just a demo
number.

**Ablation 7 — query-vector nudge** (`phase2/query_nudge.py`), user-suggested: blend the dense
retrieval query embedding itself with the accumulated positive-preference vector (via
`MultiInterestState.dominant_vector()`, a new accessor), rather than only reordering post-hoc —
motivated by the idea that a style/aesthetic preference not well captured in the accumulated query
TEXT might still be recoverable in embedding space, expanding retrieval recall rather than just
reranking. Wired through `catalog.dense_search()`'s new `query_embedding_hook` param (kept decoupled
from `phase2/`, same pattern as `overgenerality.py`'s `utility_fn`). Result: validation split a wash,
training split a **consistent regression on every metric** (TechnicalScore -2.4%, browsing and
buying both down). Plausible cause: nudging only the dense leg away from the literal current-turn
text reduces the BM25/dense complementarity RRF fusion relies on, rather than adding genuinely new
recall. **Cut** — a well-motivated idea, honestly tested, that didn't earn its keep on this data.

**Full 200-session run with everything kept enabled (LLM booster + slate hedging)**: TechnicalScore
**0.438299** — confirms the two surviving mechanisms compose without conflict, a further small lift
over the LLM-booster-alone number. **0.415731 remains the number to report as the expected
competition score**; 0.438299 is the optional ceiling with a key present.

**Investigated `buying`/`intent_override`'s persistently lower hit rate next**: found a concrete
mechanical gap in `orchestrator.decide_rerank_depth()` — `k_pool=60` fetches 60 candidates, but the
rerank cap was hardcoded at 50, so candidates ranked 51-60 were fetched then silently dropped before
ever reaching `rerank()`/`hedge_slate()`, never eligible for recommendation regardless of true
relevance. This looked like a clear, low-risk bugfix (raising the cap to 60 costs nothing since
latency isn't scored) — but measured it anyway rather than shipping on reasoning alone. **It
regressed**: guaranteed-path training split, TechnicalScore 0.425645 → 0.391078, browsing hit rate
0.634921 → 0.52381. Widening the reranked pool apparently dilutes signal for the cross-encoder,
giving it more opportunities to misrank a genuinely weaker candidate above the true target, rather
than recovering the "wasted" recall the reasoning predicted. **Reverted** — cap stays at 50. A
concrete, useful reminder (for this session and any future one) that even mechanical-looking fixes
need empirical verification before shipping; "obviously correct" reasoning was wrong here.

**Tried weighted RRF fusion next** — added a `weights` parameter to `reciprocal_rank_fusion()` and a
new `METADATA_RRF_WEIGHT` knob (`strategy_config.py`), hypothesizing that the metadata leg (an
exact-match signal on category/brand/budget) might deserve more trust in the fusion than BM25/dense's
fuzzy relevance, especially for buying-track sessions. Swept 0.0/0.5/1.0/2.0/3.0 on the guaranteed-
path training split: a clean, monotonic trend favoring LOWER weight, with weight=0.0 (dropping the
leg entirely) BEST (TechnicalScore 0.433666 vs baseline 0.425645) and weights above 1.0 regressing
sharply (3.0 → 0.329179) — plausibly because `metadata_rank()`'s coarse integer scoring (`+=2.0`/
`+=1.0` per matching constraint) produces many exact ties, and up-weighting a low-resolution signal
in RRF drowns out BM25/dense's more nuanced relevance ordering.

This looked like a genuine, clean finding worth shipping — but per this project's own
pre-registration discipline, ran the confirmatory check on the held-out validation split before
committing to it, rather than trusting the training-split trend alone. **The validation split
contradicted it**: weight=0.0 gave TechnicalScore 0.361333 vs baseline 0.376071 — worse, the
opposite direction from training. Per Ablation 3's explicit decision rule ("a win only on the
training split is meaningless by construction"), **declined** — exactly the overfitting-to-training-
split trap the train/validation discipline exists to catch. `METADATA_RRF_WEIGHT` stays at its
default 1.0 (no behavior change), kept as a tunable knob for a future session that wants to
investigate a scenario-specific (rather than single global) weighting instead.

Net effect of this investigation round: two "obviously reasonable" ideas (rerank_depth cap,
metadata RRF weight) both tested and declined, on top of the two real, validated wins already
shipped (slate hedging, LLM booster). All four outcomes are now honestly documented — a genuinely
useful demonstration of the project's ablation discipline actually catching bad ideas before they
ship, not just validating good ones.

**Phase 3.5's last item, resolved without duplicate work**: the build plan's "counterfactual/
synthetic rollout augmentation" item required first confirming the evaluator is genuinely replayable
with counterfactual actions. Direct source reading (already done for the Phase 3.2 investigation)
confirms `customer_reply()` is a pure function of accessible state — so counterfactual replay is
feasible in principle. But it also confirms the live Agent never receives the simulator's
`intent_card`/hidden target, so genuinely simulating "what the simulator would say" is impossible by
design — any counterfactual mechanism can only reason about the agent's own candidate pool, which is
exactly Phase 4's "world-model-lite" scope. Rather than building a shallow version here and a
"proper" one in Phase 4, folded this finding into Phase 4 directly instead of duplicating the work.

## 2026-08-30 (cont.) — Phase 4 (world-model-lite): attempted, declined per its own predicted risk

Built `phase2/lookahead.py`: a 1-step lookahead question selector computing EXPECTED
score-distribution entropy reduction per facet — for each candidate facet, hypothetically condition
on each of its observed values (weighted by live-observed frequency in the pool, never ground truth)
and measure how much the resulting subsets' score entropy actually shrinks, versus the shipped
heuristic's proxy (entropy of the facet's own value distribution, which doesn't necessarily
correlate with ranking-uncertainty reduction — confirmed directly by a unit test where a facet with
evenly-spread VALUES but tied scores within each group scores worse than a facet whose values
happen to separate high/low scorers, exactly the distinction expected-entropy-reduction is meant to
capture that raw value-entropy misses).

Ablated per Phase 4's own mandatory gate ("bar set higher than earlier gates, diminishing returns
are likely by construction over an already-good 1-step heuristic") on both splits: validation
regressed (TechnicalScore 0.376071 → 0.367938, driven by MTTC going from 7.5 to 7.9 — the more
theoretically-principled selector asks questions that take more turns to resolve in practice);
training was essentially flat (+0.1%, MTTC still marginally worse). **Declined** — exactly the
outcome the build plan's own intro predicted before any code was written. This is a clean example of
the project's risk register doing its job: Phase 4 was explicitly flagged "highest risk, attempt
only with substantial time left" and "diminishing returns... likely by construction," and the
ablation confirmed that prediction rather than contradicting it. The 2-step lookahead extension and
the broader counterfactual/synthetic rollout augmentation were not attempted, since there's no
reason to add depth or scope to a mechanism that doesn't clear the bar at its simplest form.

Module kept, disabled by default, for the writeup's "attempted the highest-risk phase, found
diminishing returns exactly as predicted, declined" record — genuinely useful material precisely
because it demonstrates the risk assessment was sound, not just that the team tried something.

**No further scored-path work remains queued.** Full detail:
`implementation/05_BUILD_PLAN.md`'s Phase 4 section, `implementation/06_DECISION_LOG.md` D6,
`wiki/08_evaluation_log.md`. Proceeding to Phase 3.5 + Phase 4's combined closeout (both phases'
substantive work concluded in the same investigation arc) and the standing goal's next step.

## 2026-08-29 (cont.) — Two-tier codex review + Embedding Explorer visualization

- User asked for the codex-review loop to be explicit at the **phase** level (not just per-step) inside
  `implementation/05_BUILD_PLAN.md` itself, with wiki updates that **name every finding** from a
  phase-level review (not a generic "reviewed, no issues"), followed by a dedicated phase-closeout
  commit. Added this as a documented "two-tier" system: per-step review (already existed) + a broader
  phase-exit review over the whole phase's diff, both wired into every phase section (0 through 5) and
  synced into `CLAUDE.md` §1a so the two docs don't drift apart.
- User asked why MIND/ComiRec weren't included — clarified: they ARE in `06_DECISION_LOG.md` D3
  (carried from `/My Ideas/`'s own D3, gated Phase 2 multi-interest vectors), but our own independent
  9-file research pass (`research/06`) didn't surface them on its own — a real gap in our research that
  the user's ideas folder filled, acknowledged honestly rather than overclaimed.
- User asked for a detailed, polished frontend/visualization document — a demo/debug tool to show
  embedding space in 3D plus dialog state, explicitly **not** part of the scored path (competition
  excludes UI/UX from evaluation). Loaded the `artifact-design` skill and built a published, interactive
  prototype ("Embedding Explorer") with synthetic data proving the interaction design: an orbiting 3D
  point-cloud of the catalog's embedding space (category-colored, thread-lines to nearest candidates,
  optional dev-only ground-truth overlay), plus dialog-state pills, a turn timeline, an entropy gauge,
  preference-vector sparklines, and a retrieval funnel. Design language: boutique-dark palette (brass/
  gold accent nodding to the catalog's Jewelry vertical), Fraunces/Work Sans/JetBrains Mono type system.
  Documented in new `implementation/13_FRONTEND_VISUALIZATION.md`, including the real (non-artifact-
  constrained) build plan using Three.js + a PCA export script, explicitly placed outside
  `05_BUILD_PLAN.md`'s numbered critical path (optional, time-permitting, does not compete with Phase
  0-3 build time).
- **Architecture-synthesis codex review landed and was fully triaged**: 7 findings (5 P1, 2 P2), all
  fixed, none declined — see `wiki/reviews/architecture-synthesis-2026-08-29.md` (curated) and
  `implementation/06_DECISION_LOG.md` (full detail). Real bugs caught at the design-doc stage: the
  evaluator shim would have silently reverted to the vendor baseline on a fresh clone (lived inside a
  gitignored directory + no sys.path setup); the orchestrator pseudocode made every clarification turn
  an automatic miss (recommendations only populated for commit/both, not ask) and emitted the wrong
  response object shape; the entropy formula wasn't an actual softmax and would break once preference
  scores go negative; Phase 5's packaging didn't address offline model-weight availability despite the
  organizer's own network-disabled warning; Phase 1.3's threshold sweep had no validation-split
  discipline; and metadata never contributed to Browsing-turn retrieval fusion. All fixed directly in
  the `implementation/` docs before any implementation code exists.

## 2026-08-30 (cont.) — Recovered 6 "failed" codex reviews from session transcripts; real findings triaged

Throughout Phase 3.5/4/5's work, roughly a dozen `codex exec review` attempts appeared to fail —
short `.raw.txt` files (13-15 lines: banner, one exec command, then nothing) with no review
verdict, attributed at the time to an environment/sandbox issue (`CLAUDE.md`'s two-tier protocol
was followed correctly throughout: every attempt was logged in `status.md` as a blocker rather than
silently skipped, and every shipped change was instead verified via manual review + empirical
ablation). While debugging one more "failed" attempt with a custom, minimal-exploration prompt, the
review still looked incomplete in the redirected file -- but this time the exact session id was
findable, and reading `~/.codex/sessions/**/*<id>*.jsonl` directly (bypassing the redirect
entirely) showed the review had genuinely, fully completed, with a real verdict (`"type":
"ExitedReviewMode"`, a populated `review_output`) that simply never reached the redirected stdout
file — the final verdict message renders through a different output channel than tool-call output,
and plain file redirection only reliably captures the latter.

**This meant 6 separate reviews across this session, previously logged as failed, had actually
completed with real findings sitting unread in session transcripts for hours** (some spanning
Phase 3.5's Ablation 4 work, some spanning Phase 4/5). Recovered all 6 via `tools/extract_review.py`
(new) and triaged every finding properly, per the two-tier protocol's own rule that no finding may
be silently dropped:

1. **[P1] `tune_strategy.py` let `--split validation` evaluate multiple candidates together**
   (phase3-exit review) — this lets validation results influence which candidate looks best,
   exactly the "peeking" `10_PRE_REGISTRATION.md`'s train/validation split exists to prevent. This
   was actually exercised several times this session (the round-3 threshold-extremes check, the
   metadata-RRF-weight confirmatory check). **Audited each instance**: in every case, the actual
   *decision* reached was either "no candidate beats the default, keep unchanged" or "decline the
   change" — never "here's a new champion, ship it based on comparing several validation numbers."
   No shipped KEEP decision was reached via cherry-picking among validation-evaluated candidates.
   **Fixed**: the tool now refuses to evaluate more than one candidate against `--split validation`
   in a single run, making the violation structurally impossible going forward, not just discouraged.

2. **[P1] Anthropic client had no bounded timeout** (llm-booster review) — the SDK's long default
   timeout/retry policy meant a slow/unreachable/rate-limited endpoint could block an ambiguous
   turn for minutes before the except-and-fallback ever triggered, defeating the promised graceful
   degradation in practice. **Fixed**: `timeout=8.0, max_retries=0` on client construction.

3. **[P1] LLM listwise rerank call had no explicit determinism control** (llm-booster review) --
   omitting an explicit sampling setting risked non-reproducible permutations passing validation
   without being reproducible. **First fix attempt (`temperature=0`) was itself broken**: the
   installed `anthropic` SDK (1.2.0) does not accept a `temperature` parameter in this API version
   at all (confirmed via `inspect.signature`) -- it crashed every single call with `TypeError`,
   which the existing except-and-fallback silently swallowed, **completely disabling the booster
   without any visible error**. The "re-verified" ablation run immediately after that first fix
   produced byte-identical ON/OFF results -- which should have been an immediate red flag (a
   working booster essentially never produces IDENTICAL output to having it off) but was initially
   misread as "huh, no effect this time" rather than "this is completely broken." Caught by
   deliberately investigating why ON and OFF matched exactly. **Actually fixed**: removed the
   unsupported kwarg; empirically, 3 repeated identical calls with no temperature control returned
   byte-identical permutations, suggesting this endpoint is already low-variance by default -- an
   observation, not a guarantee, documented honestly as a real, unresolved limitation of this SDK
   surface. **Re-ablated with the genuinely working fix**: validation (n=40) ON
   0.45/0.303681/7.4/**0.388104** vs OFF 0.425/0.266667/7.6/**0.3605**; training (n=160,
   confirmatory) ON 0.51875/0.321029/6.6625/**0.442434** vs OFF 0.5/0.280952/6.81875/**0.417911** --
   a genuine, consistent win on both splits, confirming Ablation 4's original conclusion (KEEP
   ENABLED) survives, once the implementation actually works.

4. **[P2] Weighted RRF fusion didn't skip zero-weight legs** (rrf-weight review) — `weight=0.0`,
   documented as "drop this leg entirely," still inserted every one of that leg's ids into the
   fused-score dict with a zero contribution, making the fusion "look" non-empty from spurious
   zero-score entries and potentially letting arbitrary zero-score candidates fill the pool. Affects
   only the already-declined `METADATA_RRF_WEIGHT=0.0` exploration (shipped default is `1.0`, never
   triggers this path) -- **fixed anyway** since the knob remains exposed for future use.

5. **[P2] Slate hedging shipped enabled despite a validation-split wash** (hedging-nudge review) --
   this is the big one. The validation-split check (n=40) showed HitRate@10 IDENTICAL between ON
   and OFF (0.45 both) and only a hairline MRR difference (0.270238 vs 0.269792) — not a regression,
   but not a confirmed win either, genuinely a wash. The shipped decision reasoned "the training
   split's larger sample (+1.9%) suggests the effect is real, just underpowered on validation" and
   shipped anyway. **This is precisely the reasoning `10_PRE_REGISTRATION.md`'s own rule exists to
   rule out** ("a win only on the training split is meaningless by construction" — post-hoc
   rationalizing a failed held-out check by appealing to the training-split number it's supposed to
   be checked against is not a loophole, it's the exact failure mode). **Reversed**:
   `ENABLE_SLATE_HEDGING` set back to `False`. This also reverses the "guaranteed-path score raised
   to 0.415731" claim reported earlier — see the corrected numbers below. Module kept, disabled, for
   the "tried, looked promising, held-out check didn't confirm it, correctly declined on review" record.

6. **[P2] `calibration_check.py` conflated "both" actions with forced commits** (hedging-nudge
   review) — "both" turns still ask a clarifying question and are deliberately not hedged by
   `agent.py` (hedging gates specifically to `action == "commit"`), so counting them as "forced
   commits" mislabeled non-forced, non-hedged turns and skewed the diagnostic that motivated
   building slate hedging in the first place. **Fixed**: now tracks only genuine `"commit"` actions.

7. **[P1] Bundled catalog embedding cache resolved relative to process cwd, not the package**
   (phase5-packaging review) — `catalog.py`'s cache path was `Path("data/_catalog_embeddings.npz")`,
   resolved against whatever directory the importing process happens to be running from. If the
   official harness imports `submission/agent.py` without first `cd`-ing into `submission/` (the
   overwhelmingly likely case — nothing in `docs/submission_rules.md` suggests the harness would
   do that), this silently misses the bundled cache entirely and triggers the ~14.5-minute
   full-catalog recompute the whole bundling effort (D-EMBED-CACHE) exists to prevent. **This
   directly undermines the "verified end-to-end" claim from Phase 5.2's offline reproducibility
   test** — that test happened to `cd` into `submission/` before running, which accidentally made
   the buggy cwd-relative path resolve correctly by coincidence, not because the fix actually
   worked. A real gap in my own verification methodology, not just the code. **Fixed**: added
   `model_paths.resolve_data_asset()` (checks cwd-relative first for dev convenience, package-
   relative second, matching how `model_paths.resolve()` already handles the model weights) and
   **re-verified properly this time** — ran the isolated offline test again, deliberately staying
   at the temp directory's root (not `cd`-ing into `submission/`) and importing via
   `sys.path.insert(0, 'submission')` instead: `Agent` constructed in 13s (a real cache hit) even
   without the accidental cwd coincidence.

8. **[P1] `build_submission.py` only warned, and built successfully, when the embedding cache was
   missing** (phase5-packaging review) — a submission built on a fresh checkout (no external
   evaluator run yet to generate the cache) would ship without the required asset while still
   printing "submission built," with no signal anything was wrong until official scoring hit the
   slow path. **Fixed**: missing cache is now a hard `SystemExit`, not a warning.

9. **[P2] Phase 4 lookahead mis-normalized probabilities for partially-populated facets**
   (phase4-closeout review) — `expected_entropy_reduction()` normalized each value's probability
   over the POPULATED subset (`len(values)`, since `_facet_values()` silently drops candidates
   missing the facet) while `base_entropy` covered the full pool, so candidates missing a sparse
   facet contributed no posterior entropy at all, letting a sparsely-populated facet look
   artificially maximally informative. Affects only already-disabled code (Phase 4 was declined
   regardless) -- **fixed anyway**: now weights every branch, including an explicit "missing"
   branch, against the full pool size.

**Corrected numbers, replacing every "0.415731 guaranteed-path" and "slate hedging shipped" claim
made earlier this session**: guaranteed-path (no API key) full-200 TechnicalScore is **0.406428**
(not 0.415731 -- that number depended on slate hedging, now reversed). With the LLM booster
correctly enabled (key present, now genuinely working): full-200 TechnicalScore **0.429943**. Note
the guaranteed-path number also shows a small (~0.6pp) drift from the earlier-reported 0.40927,
traced to the catalog embedding cache being regenerated from scratch during Phase 5.2's `.npz`
migration -- a fresh dense-encoding pass can differ by tiny floating-point margins from a prior
one due to ordinary multi-threaded BLAS non-associativity (not the hash-seed bug, which is fully
fixed and confirmed stable: both figures are exactly reproducible across repeated runs against a
fixed cache). This is now the accepted, documented, and *stable* guaranteed-path figure going
forward -- treated as the true value, not chased further given its small magnitude.

**Process fix**: `CLAUDE.md`'s work-phase protocol now documents the redirect-truncation pitfall
directly (see that file), so no future session repeats this mistake. `tools/extract_review.py` is
a small, reusable utility for recovering a review's `review_output` from its session transcript
whenever a `.raw.txt` looks incomplete -- check it before ever concluding a review "found nothing."

## 2026-08-30 — Review of the recovery-fix commit (`2fe00dd`): genuinely incomplete this time, not another redirect artifact

Ran `codex exec review --commit 2fe00dd` per protocol (review the commit that fixed all 9 recovered
findings). The resulting `.raw.txt` was short again, so per the new protocol this was checked
against the session transcript (`~/.codex/sessions/2026/08/30/rollout-...-01a05110-....jsonl`)
before assuming anything — this time the distinction actually mattered in the other direction.

Unlike the 6 prior cases, this transcript genuinely has **no** `ExitedReviewMode` event anywhere
(confirmed by grepping the raw JSONL directly, not just running `extract_review.py` — the 4 hits
`grep` found for the literal string were all inside displayed file contents of `CLAUDE.md` and
`tools/extract_review.py` themselves, not an actual event). The transcript and the `.raw.txt`
both end mid-flight, right after a `Get-FileHash` exec call comparing `src/copilot/` against
`submission/src/copilot/`, followed by one more completed `Reasoning` item — then nothing. The
codex process had already exited (confirmed via `ps`) by the time this was checked, so it isn't
still running in the background; it stopped before reaching a verdict. This is a real, different
failure mode from the redirect-capture bug: that bug hid a *completed* review; this one is an
*actually incomplete* review.

**Response**: retried once more in the background (`recovery-fix-retry-2026-08-30.raw.txt`),
consistent with this session's established pattern of retrying rather than assuming permanent
failure on the first miss. **The retry reproduced the same failure mode**: its transcript
(`session id 01a05114-b030-...`) shows `EnteredReviewMode`, 36 completed `CommandExecution` items
and 26 `Reasoning` items — a real, substantial review genuinely in progress, reading every changed
file and diffing tests — then stops cold with no `ExitedReviewMode` and no final message, same as
the first attempt. Two independent invocations of the same review, both doing real work and both
dying before synthesizing a verdict, rules out "unlucky one-off" — this looks like `codex exec
review` hitting some resource/context ceiling specifically on large, multi-file diffs in this
environment (this commit touched 20 files), not the redirect-capture bug from earlier (that bug
hid a *completed* review; this is a review that never completes at all on a diff this size).

**Decision**: not retrying a third time — two identical failures on the same commit is enough
signal that another attempt at the same scope won't land. `2fe00dd` is treated as
manually-reviewed-only: every one of its 9 changes was already independently reasoned through,
tested (re-ablated on both splits where relevant), and cross-checked against
`10_PRE_REGISTRATION.md` and `06_DECISION_LOG.md` before being written — the same bar several
earlier commits in this session shipped under when codex review was unavailable.

**Update, same session, same hour**: the "only fails on wide diffs" theory above is wrong. A
*separate*, much smaller review (Phase 5.4/5.5's commit `77829e1` — 8 files, mostly new docs plus
one small tool script) was launched next and **failed the identical way**: transcript
`01a0511c-1f81-...` shows `EnteredReviewMode`, 11 `CommandExecution` + 15 `Reasoning` items, real
work reading `implementation/02_TECHNICAL_PRD.md` and the diff, then stops cold mid-file-read with
no `ExitedReviewMode`, no error message anywhere in either the transcript or the raw stdout. Three
independent review invocations in the same session now show this exact shape (real work, clean
stop, no verdict, no error) regardless of diff size — this reads as a genuine, current
environment-level reliability issue with `codex exec review`'s synthesis step in this session, not
something caused by anything in this repo's diffs. **Revised process note**: stop treating this as
"retry until it works" — after one retry with no verdict, accept manual review for that commit and
move on; a third attempt bought no new information here and cost real time against the clock.
`CLAUDE.md`'s guidance updated accordingly.

## 2026-08-30 — Diagnosed and fixed the buying-track retrieval-recall gap (Phase 5.6): +15.9% TechnicalScore, the largest win of the project

Every prior attempt at closing the persistent Buying-track gap (query-vector nudge, weighted RRF
fusion, rerank-depth widening, slate hedging, 1-step lookahead question selection) started from a
hypothesized *fix* and ablated it, without first measuring *why* buying specifically underperformed.
Built `tools/diagnose_buying_recall.py` (not scored-path code) to close that gap: it monkeypatches
`retrieve_candidates` at the point `agent.py` calls it (no scored file edited) to record, per turn,
whether the hidden target ever reaches the fused/filtered candidate pool, then replays the real
simulator loop over all 200 public sessions.

**Result**: buying targets never reach the pool at all in 37.5% of sessions (vs. 26.2% for
browsing), and reach the pool but never the top-10 in a further 23.8% (vs. 8.8% for browsing) — a
near-even split between a pure retrieval-recall failure (unfixable by any amount of reranking) and a
ranking failure, both far worse than browsing's numbers. This is the first *direct measurement* of
the gap's shape, not an inference.

**Follow-up isolation test**: re-ran the buying-only diagnostic with `route_retrieval_breadth`
monkeypatched to always return `False` (hard filter forced off). Result was **byte-identical** to
the baseline — 38.8%/23.8%/37.5%, no change at all. This proved the *existing* hard filter
(`catalog.apply_hard_filters`) was already inert for buying's actual problem: reading the code
showed it only ever restricts on `category`, `brand`, and `budget_max` — never on the disclosed
hard-constraint attribute itself (material/color/style). Brand is structurally almost never
disclosed (resolved-Q2: `classify_constraint()` has no branch for it), so for most buying sessions
the "hard filter" reduces to "category filter," which barely narrows a 50,000-item catalog. The
`route_retrieval_breadth` docstring's claim of "Buying-track precision" was aspirational, not real.

**Fix**: `EXTENDED_HARD_FILTER_ATTRS` (new flag, `strategy_config.py`) also restricts the hard-filter
pool on material/color/style when disclosed, via new `_by_material`/`_by_color`/`_by_style` catalog
indices built once at load time using the exact same regex vocabulary `catalog._attributes_for()`
already uses for candidate-side facet values (so a slot's extracted value and a candidate's attribute
value are drawn from a consistent vocabulary, reducing — not eliminating — mismatch risk).

**Known risk, measured rather than assumed away**: material/color/style are single-regex-match,
best-effort values — a genuinely-matching product whose text mentions a different material/color
first would be wrongly excluded, the same fragility resolved-Q7 already found in `details`. This is
exactly the kind of thing that sank weighted RRF (reversed on validation) and slate hedging
(validation wash) earlier this session, so it was ablated with the same rigor, not shipped on
first-glance plausibility.

**Ablation** (per `10_PRE_REGISTRATION.md`): training split (n=160) TechnicalScore 0.476056 vs
baseline 0.441967 (+7.7%); validation split (n=40, held out, single-candidate run per
`tune_strategy.py`'s enforced rule) TechnicalScore 0.445604 vs a fresh same-run baseline of 0.388292
(**+14.8%**, HitRate@10 +16.7%, MRR +5.8%, MTTC improved). A clean win on BOTH splits — unlike every
other buying-track attempt this session. **ENABLED by default.**

**Full 200-session guaranteed-path exit: TechnicalScore 0.471193** (HitRate@10 0.55, MRR 0.347643,
MTTC 6.405) — up from 0.406428, **+15.9%**, the single largest improvement of the entire project.
Buying's own hit rate rose to 0.475 from roughly 0.36-0.39 across every prior measurement this
session, closing most of the gap to browsing (0.6625).

**A repeat run to double-check determinism, and a separate run to re-measure the optional LLM-
booster ceiling on top of this fix, were both genuinely killed mid-flight by an external interrupt**
(confirmed via `kill -0` on the actual process IDs, not just a `ps`-based check that had earlier given
a false "already exited" reading on the same PID — a real lesson: `ps aux`-based grep checks against
long-running Windows/git-bash subprocesses are unreliable for detecting whether a process is still
alive, use `kill -0 <pid>` instead). Neither produced a result and neither was re-attempted given the
interrupt pattern (three background tasks killed within minutes of each other). This doesn't weaken
the headline number — it's backed by two independent, directionally-consistent prior runs (training +
validation) — but the optional-ceiling number is now stale and not re-measured on top of this fix.

**Codex review of this commit (`4d8e52e`)**: two attempts, both failed to produce a verdict (one 15
lines / one exec call, one 6 lines / no exec calls at all before stopping) — no `ExitedReviewMode`
in either transcript. Consistent with today's established pattern (4 genuinely-incomplete reviews
now, across three unrelated commits of varying size). Not retried a third time; `4d8e52e` accepted
as manually-reviewed-only, same basis as `2fe00dd` and `77829e1` earlier today. The change itself
was independently reasoned through (root-caused via direct measurement, not guessed), tested with
two new unit tests, and ablated on both data splits before being written — the review would have
been a second automated pass on top of substantial existing rigor, not the only check.

## 2026-08-30 — Codex review conclusively unavailable this session: 11/11 failed, sequential and parallel, across 6 commits

Per a direct user request, launched codex review for every commit since the last successful one,
**all 6 simultaneously in parallel** rather than one at a time: `2fe00dd`, `77829e1`, `d6ce4ac`,
`4d8e52e`, `8668665`, `abcf9bb` (diff sizes ranging from 1 file to 20). Checked each one's actual
session transcript for `ExitedReviewMode` (not just raw.txt length, per the established protocol) —
**all 6 failed to produce a verdict.** Combined with the 5 earlier sequential failures today (2 on
`2fe00dd`, 1 on `77829e1`, 2 on `4d8e52e`), that's **11 consecutive failures across 6 distinct
commits, in both sequential and parallel invocation, spanning diff sizes from 1 to 20 files** — this
rules out diff size, parallelism, and any single commit's content as the cause. `codex exec
review`'s review-synthesis step is genuinely, conclusively broken in this session's environment
right now, not an occasional flake.

**Decision**: stop attempting codex review for the remainder of this session unless something about
the environment changes (e.g. a fresh session, a codex update). All 6 of today's commits
(`2fe00dd`, `77829e1`, `d6ce4ac`, `4d8e52e`, `8668665`, `abcf9bb`) are accepted as
manually-reviewed-only. This is a real, disclosed gap in review coverage for this stretch of work —
not hidden in the writeup — but every one of these changes was independently reasoned through,
tested (unit tests where applicable, full evaluator runs, and proper train/validation ablation for
the scored-behavior changes), which is a substantive bar on its own.

**Update, same day, user updated codex 0.150.1 → 0.151.0**: retried all 6 commits again — **still
0/6, no change.** `codex --version` confirmed 0.151.0 active. This rules out "known bug fixed in a
patch release" as the explanation. `codex doctor` separately flagged (before this retry) that
Microsoft Defender exclusions for codex's helper executables (`codex.exe`,
`codex-windows-sandbox-setup.exe`, `codex-command-runner.exe`, `codex-code-mode-host.exe`) were
unverified — the failure signature (real work happens, then a silent death right at the verdict-
synthesis transition, no error anywhere) is consistent with a security tool killing a helper
process mid-flight. That remains the most plausible unconfirmed lead; flagged to the user to check/
add those exclusions, since this session has no permission to modify Defender settings. 17
consecutive failures today across 6 commits, 2 codex versions, sequential and parallel invocation.

## 2026-08-30 — Post-fix recall diagnostic: EXTENDED_HARD_FILTER_ATTRS closed most of the recall gap, exposed a ranking gap instead

Re-ran `tools/diagnose_buying_recall.py` (full 200 sessions) after Phase 5.6/5.7 shipped, to see the
diagnostic's own before/after picture, not just the aggregate TechnicalScore:

| Scenario | never-in-pool (before → after) | in-pool-not-top10 (before → after) | hit@10 (before → after) |
|---|---|---|---|
| buying | 37.5% → **22.5%** | 23.8% → 30.0% | 38.8% → **47.5%** |
| intent_override | 20.0% → 10.0% | 40.0% → 46.7% | 40.0% → 43.3% |
| browsing | 26.2% → 23.8% | 8.8% → 10.0% | 65.0% → 66.2% |
| boundary | 30.0% → 30.0% | 10.0% → 10.0% | 60.0% → 60.0% |

The fix worked exactly as diagnosed: retrieval recall improved substantially for buying (never-in-
pool nearly halved) and, as an unplanned side benefit, for intent_override too (its sessions share
the same buying-style turn-1 disclosure before the pivot). But it also cleanly surfaces the *next*
bottleneck: a meaningfully larger share of buying's candidates now reach the pool but still don't
make the final top-10 (23.8% → 30.0%) — this is now a **ranking** problem, not a recall problem, and
points more directly at reranking-side improvements (e.g. cross-encoder ensembling) than further
retrieval-side work, for whichever gets tackled next.

## 2026-08-30 — Deferred idea logged: ColBERT-style late-interaction retrieval

Parallel research (prompted by a user question) confirmed a pretrained, no-training-required
ColBERT checkpoint exists (`colbert-ir/colbertv2.0`) and would be rules-compliant. Deliberately not
promoted to the active plan: its main advantage (fine-grained token-level matching) substantially
overlaps with what the existing cross-encoder rerank stage already provides via full cross-
attention, for a high integration cost (new per-token embedding pipeline, materially more memory,
a new fusion signal to tune). Logged to `wiki/06_future_ideas.md` rather than declined outright,
since it remains a legitimate idea if the cross-encoder stage's own ceiling is ever reached.

## 2026-08-30 — Codex review finally succeeded: root cause was account usage quota, not Defender/parallelism/version. `2fe00dd` review triaged, 3 findings fixed

The real root cause of every codex review failure today, found only after checking raw stdout
directly (not just the JSONL transcript): `ERROR: You've hit your usage limit... try again at 8:51
PM.` The CLI swallows this into a generic "review was interrupted" message inside the transcript,
which is why checking for `ExitedReviewMode` alone never surfaced it — a real gap in the recovery
protocol this session had been following. Microsoft Defender exclusions and the codex version
update were both reasonable leads given the available signals but were not the actual cause; a
`chatgpt.com` browser tab open elsewhere also turned out to be a red herring (closing it changed
nothing) — the quota reset is what actually fixed it. **Lesson for the protocol**: when a review
looks incomplete, check the raw stdout for an explicit `ERROR:` line before investigating anything
else — it's the cheapest, most direct check and would have found this immediately.

Once working, review of `2fe00dd` (the original 9-fix recovered-reviews commit) surfaced 3 real,
previously-missed findings — this commit had been accepted as manually-reviewed-only for hours,
and a working review found genuine issues in it:

1. **[P1, confidence 0.97] `model_paths.resolve_data_asset()` checked cwd-relative before
   package-relative** — if the official harness's cwd happened to already contain any file at that
   relative path (stale, unrelated, or incompatible), it would be silently preferred over the
   verified bundled cache, potentially corrupting retrieval with no error at all. **Fixed**:
   reversed the order (package-relative, the verified bundled asset, checked first).
2. **[P2, confidence 0.92] `tune_strategy.py`'s one-candidate-per-validation-run guard only
   prevented peeking within a single invocation** — nothing stopped validating candidate A, then in
   a separate invocation validating candidate B, and keeping whichever scored better; the same
   peeking the guard exists to prevent, just spread across two runs. **Fixed**: validation now
   requires the candidate to match one already recorded by the most recent `--split training` run
   (`tools/_last_training_run.json`, gitignored/transient) — training proposes, validation only
   accepts or rejects that exact candidate, never a fresh choice made after seeing a score.
3. **[P2, confidence 0.99] `implementation/05_BUILD_PLAN.md` still hardcoded the RETRACTED
   0.415731/0.438299 figures**, never updated when slate hedging was reversed — since `CLAUDE.md`
   designates this page authoritative, a contributor following it verbatim could report a stale,
   wrong number (this has now happened twice: 0.415731 → 0.406428 → 0.471193, and the page never
   caught up either time). **Fixed**: replaced the hardcoded number with an explicit pointer to
   `wiki/08_evaluation_log.md`'s most recent row, so this specific staleness bug cannot recur a
   third time.

All 3 findings fixed, no findings declined. `overall_correctness` was "patch is incorrect" (0.96
confidence) before these fixes.
