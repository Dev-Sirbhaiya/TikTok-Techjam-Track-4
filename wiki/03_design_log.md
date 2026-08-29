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
`tools/tune_strategy.py`, a reusable rollout→score tool for Phase 3.1's actual sweep (still pending
as of this entry — this reproducibility detour came first).

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
