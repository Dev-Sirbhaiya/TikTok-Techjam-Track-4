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
