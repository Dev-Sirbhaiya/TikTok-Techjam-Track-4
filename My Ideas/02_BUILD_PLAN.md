# 02 — Build Plan

## Governing rule for every phase past Phase 0

> A technique being real, published, and well-cited is never sufficient justification for keeping it in
> this system. If a component doesn't measurably improve held-out results on our own dev sessions, it
> gets removed or demoted — never kept because a paper exists for it.

Re-run the evaluator after every single addition and log HitRate@10 / MRR / MTTC. If a feature doesn't
move the needle, don't rip it out last-minute — just stop investing further time in it and move on.

---

## Phase 0 — The floor (non-negotiable, nothing else starts until this is done and evaluated)

**Goal: a complete, submittable system, even if plain.** This is insurance, not a fallback to be
ashamed of — a working plain system beats an ambitious broken one at deadline, every time.

1. **Setup + baseline.** Load catalog and dev sessions. Implement basic BM25 retrieval → top 50
   candidates. Naive ranker (BM25 score only, no memory, no smart questions). Hardcoded fixed question
   order (category → price → color → size). Run the evaluator. **Log this number — it is the control
   group for every single feature added afterward.**
2. **Dialog state + partial updates.** Build the `DialogState` object (see `01_ARCHITECTURE.md`).
   Implement `diff_and_update(state, new_message)`: parse the new message for slot values, compare
   against existing state, overwrite only fields that actually changed. Test explicitly against an
   Intent Override scenario (user changes their mind mid-session) and a contradiction scenario.
3. **Rejection memory.** Extend state with `rejected_hard` / `rejected_soft`, using the three-tier
   confidence system (explicit → strong/hard; comparative or vague → medium/soft; implicit → weak/soft,
   and **do not auto-infer a specific attribute cause from a bare "show me more"** — that's an
   over-inference risk, log it as a weak generic negative on the last-shown item only). Apply as a
   filter step: strip hard-rejected attributes entirely, penalize (don't remove) soft-rejected ones.
4. **Information-gain question selector.** For each candidate facet not yet filled, compute expected
   resulting pool size if asked about (grouped by attribute value, weighted by how common each value is
   in the current pool). Pick the facet with the lowest expected remaining pool. This can be framed as
   Shannon entropy reduction in the writeup — same computation, stronger framing.
5. **Turn budget policy.** Track `turns_remaining`. Confidence threshold for committing gets more
   lenient as turns run out, so the system is forced toward a decision rather than drifting to turn 10
   with nothing:
   ```
   threshold = base_threshold - (decay_rate * (10 - turns_left))
   if top_candidate_score >= threshold or turns_left <= 1:
       commit
   else:
       ask
   ```
   Tune `base_threshold` and `decay_rate` empirically against the 200 dev sessions.
6. **Intent detector.** Lightweight buying-intent score (0.0–1.0) — even a rule-based score counting
   filled slots + language specificity is fine to start. Use it to set initial retrieval breadth (narrow
   filter vs. wide diverse search) and the initial confidence threshold from step 5.
7. **Ranker upgrade.** Add dense embedding similarity as a second retrieval signal alongside BM25.
   Combine via **Reciprocal Rank Fusion (RRF)**, not a hand-tuned weighted sum — RRF combines by rank
   position rather than raw score, avoiding the need to calibrate two different score scales against
   each other. Adjust fusion weighting based on rejection patterns if time allows (e.g., repeated price
   rejections → increase price-match weight). Optionally, LLM re-rank only the top ~20–30 candidates for
   semantic quality — keeps cost/latency reasonable and stays within the no-fine-tuning constraint.
8. **Combined recommend+ask, if the API allows it (verify first — see Q1).** Do not build "ask OR
   commit" as a hard either/or if the real contract permits returning `ask_attribute` and
   `recommendations` together. Always attach your current best Top-10 when you have one, even on a turn
   where you're also asking — a hit can land on any turn, and MTTC rewards early hits.
9. **Integration + full-loop testing.** Wire every module into `agent.py`. Run against all 200 dev
   sessions. Check for regressions between steps — a feature that helps MRR but hurts MTTC needs a
   tuning pass, not a rewrite.
10. **Debug logging.** One-line rationale per top-ranked candidate ("matched category, avoided rejected
    color, within budget percentile"). Not required by the spec, but the fastest way to debug a failing
    session, and good demo material.

**Phase 0 exit criteria:** full run against all 200 dev sessions, no crashes, metrics logged, clearly
beating the BM25-only baseline (HitRate@10 0.125 / MRR 0.068 / MTTC 9.81) on at least HitRate@10 and
MTTC.

---

## Phase 1 — Cheap, high-confidence additions (do immediately after Phase 0 passes)

These are refinements to Phase 0 modules, not new architecture — low risk, don't need a separate
ablation gate, but still log metrics before/after.

- **RRF fusion**, if not already done in Phase 0 step 7 — replaces any weighted-sum ranker.
- **Explicit Shannon-entropy framing** of the question selector (already computing the equivalent —
  this is a naming/writeup upgrade, cheap to make precise).
- **Verify the real Agent API contract** against the cloned repo (see `04_OPEN_QUESTIONS.md`, Q1–Q3) —
  confirm combined-turn support, the exact `ask_attribute` enum, and whether any comparative-feedback
  channel exists. This gates decisions in Phase 2 and 3, do it early.
- **Rejection-memory confidence tiers**, if not already fully built in Phase 0 step 3.

---

## Phase 2 — Real payoff, real cost, ablation-gated (attempt only with time left after Phase 1)

Every item here **must** be tested K/on vs. off against the dev-session evaluator before being kept.
See `06_ABLATIONS_AND_METRICS.md` for the exact procedure. Do not assume any of these help — several
have documented cases in the literature where the equivalent technique *hurt* performance.

- **Multi-interest hypothesis vectors** (K > 1 instead of a single dialog state). Ablate K=1 vs K=2 vs
  K=3 vs K=4. If K=1 wins or ties, do not ship K>1 — see Decision D3 and D10 for why this is a real risk,
  not a formality.
- **Contextual-bandit action policy** (`Q(action | state)`, adapting within-session which facet type is
  paying off, e.g. color vs. use-case). Ablate static Phase-0 policy vs. adaptive. Be aware of cold-start
  risk: a session offers only ~3–6 real clarification decisions before the turn cap, which is very little
  data for a bandit to learn from — warm-start its prior from the offline tuning pass (Phase 3) rather
  than learning from scratch.
- **Value-of-information framing for ask-vs-commit**, replacing pure pool-shrinkage. Only worth building
  if a genuinely *live-computable* proxy is defined first (e.g., retrieval-confidence spread, BM25/dense
  ranking disagreement) — do NOT build a version that secretly requires the ground-truth target rank to
  compute, since the live agent never has that. See Decision D6.
- **Regime states** (Browsing → Exploring → Narrowing → Buying → Override) instead of the single 0–1
  buying-intent dial. A/B against the simple dial — more expressive isn't automatically better; discrete
  states are easier to log/debug, a continuous dial is easier to compute and blend.

---

## Phase 3 — Offline self-evolution and comparative feedback (final stretch, only if core is solid)

- **SkillOpt-style offline strategy tuning.** Use the 200 dev sessions + the provided deterministic
  evaluator as a rollout → score → edit → validate loop to tune thresholds, facet priorities, and fusion
  weights as an explicit text strategy document, rather than by hand. **Hold out a validation split of
  the 200** so thresholds aren't fit to the exact set you're iterating against — the 800 private sessions
  are what's actually judged. This is lower-risk than it sounds: it's mostly a formalization of "tune
  empirically against dev sessions," which Phase 0 already does informally.
- **Comparative feedback ("Tinder-style"), text-routed version.** Per Decision D9: build this as
  comparative *language* parsing, not a new API surface. When multiple interest hypotheses or candidates
  are shown, a reply like "closer to the second one, but less flashy" gets parsed by the same NLU/state
  update path as any other turn, and nudges the ranking/state the same way an explicit rejection would.
  If Q1/Q3 confirm the real API has zero support even for showing multiple representative examples in one
  message, scope this down further to whatever the confirmed contract allows.
  - **Optional, presentation-only:** an actual swipeable demo UI outside the scored path, feeding the
    same underlying update function, purely for the demo video. Zero risk to the graded system since it
    never touches the scored code path. Do not spend more than a token amount of time on this — the spec
    does not evaluate UI/UX.

---

## What to do if time runs out at any phase boundary

Stop at the end of whatever phase you're in, make sure Phase 0 + everything already integrated still
passes the evaluator cleanly, and prepare the writeup/demo around what's actually shipped. A team that
ships Phase 0 + Phase 1 cleanly, with a clear "we tried X, ablated it, and cut it because Y" narrative
for anything attempted in Phase 2/3, scores better on Feasibility and Presentation than a team that
shipped a half-working Phase 2/3 feature.
