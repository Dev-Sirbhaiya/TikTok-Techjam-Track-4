# 11 — Future Work

Speculative or high-risk ideas explicitly kept out of the committed Phase 0-3.5 build. Nothing here
gets built without first passing through `08_ABLATION_MATRIX.md`-style gating, and nothing here should
be started before `05_BUILD_PLAN.md`'s Phase 0-1 are solid. Cross-reference: `wiki/06_future_ideas.md`
(the living-wiki version of this list — update both if a stretch idea graduates to a real decision).

## Phase 4 — World-model-lite planning cluster (already scoped in `05_BUILD_PLAN.md` Phase 4)
1-2 step counterfactual action simulation over the existing entropy-reduction heuristic. Highest risk,
highest bar to justify keeping, per `05_BUILD_PLAN.md`. Explicit non-goals carried forward: no trained
neural world model, no RL, no MCTS, no retrained MIND/ComiRec.

## Ideas considered and deliberately not scheduled into any phase (yet)

- **PageIndex-style structural category-tree reasoning** (D2) — plausible upgrade if Phase 0/1
  retrieval quality plateaus with time to spare; not scheduled by default since the dict-based
  inverted-index pre-filter already gives most of the practical benefit without LLM-navigation latency.
- **Uncertainty calibration as a standalone deliverable** (beyond Phase 3.5's scoped version) — a full
  calibration curve / reliability diagram could be genuinely nice writeup material (demonstrates rigor)
  but is explicitly lower priority than shipping the calibration's actual *use* in the turn policy.
- **Cross-session profile persistence** — CUT, not deferred (see D8, D-PROFILE). Listed here only so a
  future reader doesn't mistake "not built" for "not considered" — it was considered carefully and
  rejected for structural reasons (no cross-session identifier exists in the eval harness), not for
  lack of time.
- **A live demo UI for the swipeable/comparative-preference concept** — explicitly out of scope for the
  scored path (D9); could exist purely for the demo video if time allows in Phase 5.4, but should never
  receive meaningful engineering investment since UI/UX is not evaluated per the competition spec.
- **Real-time per-turn latency dashboard / profiling harness** — nice-to-have for debugging during
  build, not a deliverable; if built, keep it outside `src/copilot/` (e.g. in `tools/`) so it never
  risks becoming an accidental dependency of the scored `Agent` class.
- **Extending the gazetteer with fuzzy/typo-tolerant matching** — the competition spec states input is
  pre-cleaned text with no ASR/typo noise to handle (`wiki/00_problem_statement.md`), so this is
  explicitly *not* needed; listed here only to record that it was considered and correctly excluded
  based on the stated assumption, not overlooked.

## Open research questions worth revisiting only if Phase 0-3.5 ship comfortably early

- Does a genuinely 2-step (not 1-step) lookahead meaningfully beat the Phase 0 entropy-based question
  selector on this specific catalog/session distribution, or is the gain purely theoretical at this
  scale? (Phase 4's own mandatory gate should answer this empirically if attempted.)
- Would a slightly larger/different embedding model (e.g. `gte-small` or `e5-small-v2`'s asymmetric
  query/passage encoding) measurably beat `bge-small-en-v1.5` on this specific short, noisy shopper-
  query distribution? `research/02` flags this as plausible but untested for this exact domain.
