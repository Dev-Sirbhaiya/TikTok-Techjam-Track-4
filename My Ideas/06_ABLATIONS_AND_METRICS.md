# 06 — Ablations & Metrics

## The rule (repeated here because it's the one that matters most)

> A technique being real, published, and well-cited is never sufficient justification for keeping it in
> this system. If a component doesn't measurably improve held-out results on our own dev sessions, it
> gets removed or demoted — never kept because a paper exists for it.

## Metric-tracking discipline (applies from Phase 0 step 1 onward)

1. **Log all three metrics after every single change**, not just at the end of a phase:
   `HitRate@10`, `MRR`, `MTTC` — plus the derived `Efficiency` and overall `TechnicalScore` once Q9 is
   confirmed. Keep this as an append-only log (a CSV or a markdown table), not something that gets
   overwritten — you want the full trajectory for the writeup, and to catch regressions.
2. **The Phase 0 step 1 baseline (naive BM25-only, fixed question order) is the permanent control
   group.** Every later number gets compared against it, not just against the immediately-preceding step.
3. **Watch for metric trade-offs, not just improvement.** A feature that helps MRR but hurts MTTC is not
   a clean win — it needs a tuning pass (adjust its weight/threshold) before being called "kept." Log
   per-metric deltas, not just an aggregate score, so trade-offs are visible.
4. **Split-aware evaluation once Phase 3 offline tuning starts.** Hold out a validation subset of the
   200 public dev sessions (e.g., 160 train / 40 validation) so that offline strategy edits (Decision
   D13) or threshold tuning aren't being fit and validated on the exact same data. The 800 private
   sessions — 4x the public set — are what's actually judged; overfitting to the public 200 is an
   explicitly named common failure mode from the original build plan this project started from.

## The three mandatory ablations for Phase 2/3 items

### Ablation 1 — Multi-interest K sweep (gates Decision D3)

**Procedure:** run the full pipeline with the multi-interest layer set to K=1 (equivalent to disabling
it — falls back to a single `DialogState`-only representation), then K=2, K=3, K=4, each against the
full 200 dev sessions (or the training split, if Ablation-3's validation split is already in place).

**Metric to watch primarily:** HitRate@10 and MRR (multi-interest is a ranking-quality mechanism first).
Also watch MTTC — a K>1 system that's more accurate but takes more turns to converge may not be a net
win under the efficiency-weighted scoring formula.

**Decision rule:** if K=1 ties or beats every K>1 setting on the combined `TechnicalScore`, do not ship
K>1 — the added complexity, latency, and failure surface aren't earning their keep. If some K>1 setting
wins, use the *smallest* K that captures most of the gain (diminishing returns are likely, per the
literature's own finding that K is dataset-sensitive with no universal right value).

**What "winning" should look like to be worth the complexity:** a non-trivial improvement, not a
rounding-error one — e.g., meaningfully more than run-to-run noise on the dev set. If the gap between
K=1 and the best K>1 is within noise, treat it as a tie and keep K=1 for simplicity and reliability.

### Ablation 2 — Static vs. adaptive action policy (gates Decision D11)

**Procedure:** run the full Phase 0/1 pipeline with (a) the static, hand-tuned question-selection logic
from Phase 0 step 4, vs. (b) the same logic wrapped with the within-session contextual-bandit adjustment
from Decision D11, both against the same dev sessions.

**Metric to watch primarily:** MTTC (this mechanism's whole purpose is deciding which questions are
worth asking, faster).

**Decision rule:** keep the adaptive version only if it improves MTTC without a corresponding drop in
HitRate@10 (i.e., it shouldn't be converging to bad guesses faster). Given the known cold-start risk
(only ~3-6 real decisions per session before the 10-turn cap), a marginal or inconsistent improvement is
plausible even if the idea is sound — don't be surprised if this ablation is close, and don't feel
obligated to ship it if it isn't a clear win. If it's close, prefer the simpler static version and note
in the writeup that adaptive policy was tried, measured, and found not to clearly outperform under the
turn budget — that is itself a legitimate and interesting technical finding, not a failure.

### Ablation 3 — Before vs. after offline strategy optimization (gates Decision D13)

**Procedure:** establish a hand-tuned strategy (Phase 0/1's thresholds, weights, and facet priorities,
set by reasonable manual iteration) as the "before" baseline. Run the SkillOpt-style rollout → score →
edit → validate loop against a training split of the dev sessions to produce an optimized strategy
document. Evaluate both the "before" and "after" strategies against a held-out validation split they
were never tuned against.

**Metric to watch:** overall `TechnicalScore`, since this is a general strategy-tuning mechanism, not
targeted at one specific metric.

**Decision rule:** keep the offline-optimized strategy only if it beats the hand-tuned baseline on the
held-out validation split specifically — not just on the training split it was optimized against (that
comparison is meaningless, since it would be expected to win by construction). If time is short, this
ablation can be skipped and the hand-tuned Phase 0/1 thresholds shipped as-is — per Decision D13, this
is the lowest-risk Phase 2/3 item, but it is not free, and an untested "optimized" strategy that was
never validated against held-out data should not be trusted over a simpler hand-tuned one.

## What to do with ablation results in the writeup

Every ablation run — whether the feature was kept or cut — is genuinely good material for the required
project writeup: it directly demonstrates "well-structured decision-making" and gives concrete evidence
for claims rather than assertions backed only by citations. A cut feature with a clear "we tested K=2/3/4
against K=1 and found no significant improvement, so we shipped the simpler system" is a legitimate,
even strong, technical-execution story — arguably a better one than uncritically shipping every idea
that had a paper behind it. Include the actual before/after numbers, not just the conclusion.
