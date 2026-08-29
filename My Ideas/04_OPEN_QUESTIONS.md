# 04 — Open Questions

Ranked by how much downstream design depends on the answer. **Q1–Q3 should be resolved before Phase 1
starts** — everything else in this list can be resolved opportunistically or is genuinely fine to leave
as an assumption if time is short.

## Tier A — resolve before Phase 1 (high blast radius, currently unverified)

**Q1. Can a single turn response include both `ask_attribute` AND `recommendations`, or is it strictly
one or the other?**
Why it matters: Decision D14 (combined recommend+ask) assumes yes. If the real contract is strictly
either/or, the Phase 0 turn policy needs the simpler either/or branching, and MTTC expectations should
be recalibrated (fewer "free" turns where progress happens on an ask-only turn).
Where to check: `agent_api_contract.json` or equivalent in the participant repo/kit
(https://github.com/TechJam2026/techjam-conversational-search).

**Q2. What is the exact, complete list of valid `ask_attribute` enum values?**
Why it matters: the question selector (Phase 0 step 4) and the internal-to-external slot projection
(Decision D10) both need the real list, not the inferred approximation currently in this documentation
(category, material, color, size, style, brand, budget, feature, use_case, other/null). If the real
enum is different or larger/smaller, the projection logic and the fixed-order fallback question
sequence both need updating.
Where to check: same contract file as Q1.

**Q3. Does the scored API expose any comparative, click, or selection signal at all — even implicitly —
or is it strictly free-text turns in both directions?**
Why it matters: directly determines the shape Decision D9 (comparative critiquing) must take. If there
is truly zero comparative channel, the text-routed version is the only option; if there's some structured
mechanism this research pass missed, the feature could be built more directly and possibly more
reliably.
Where to check: same contract file, plus any example/sample session transcripts in the repo.

## Tier B — worth checking, moderate blast radius

**Q4. What exactly do the four scenario types (Buying, Browsing, Intent Override, Boundary) test, and
how are they graded/weighted?**
Why it matters: if scenario-specific behavior is separately scored or weighted, the turn policy and
question selector may benefit from scenario-aware tuning (e.g., a detected Intent Override might warrant
immediately clearing stale hypotheses rather than gradually decaying them). Currently designed generically
without scenario-specific logic.
Where to check: `competition_specification.md` or equivalent in the repo.

**Q5. Does the simulated user ever volunteer unsolicited constraints, or does it strictly answer only
what's asked?**
Why it matters: affects how aggressively the question selector should ask vs. wait — a cooperative
simulator that volunteers information reduces the value of asking; a strict one increases it. Research
flagged this as a documented risk area (the "CoSearcher" caveat — user simulators can be unrealistically
cooperative, inflating apparent clarification value).
Where to check: sample dev session transcripts in the participant kit.

**Q6. Is there a per-turn or per-session token/cost budget enforced by the evaluator, beyond the
disclosure requirement?**
Why it matters: affects how aggressively an LLM re-ranking step (Phase 0 step 7) or a PageIndex-style
structural filter (Decision D2) can be used. Currently assumed to be "disclose but not hard-capped" —
confirm this is actually correct before relying on generous LLM usage.
Where to check: evaluator code / rules in the participant kit.

**Q7. Does `catalog.jsonl.gz`'s `details` field have any consistent sub-schema per top-level category
(e.g., do all "Shoes" items share a `size` field even if `Jewelry` doesn't), or is it fully
unstructured per item?**
Why it matters: determines how much of the internal slot representation (Decision D10) can rely on a
semi-structured per-category schema vs. needing to be fully generic. Affects retrieval indexing strategy
too (whether structured filters can be built per top-level category).
Where to check: direct inspection of a sample of `catalog.jsonl.gz` records.

## Tier C — lower priority, fine to proceed on current assumptions

**Q8. Are the 200 public dev sessions representative of the same scenario-type distribution as the 800
private sessions, or could the private set be skewed differently?**
Why it matters: affects how much to trust dev-session ablation results (see `06_ABLATIONS_AND_METRICS.md`)
as a predictor of private-set performance. No specific reason to suspect skew, but worth a sanity check
if time allows (e.g., compare scenario-type proportions in the 200 against whatever the spec document
says about the full generation process, if disclosed).

**Q9. Exact numeric weighting confirmation: is `TechnicalScore = 0.50·HitRate@10 + 0.30·MRR +
0.20·Efficiency` and `Efficiency = clip((11 − MTTC)/10, 0, 1)` precisely correct, or approximate?**
Why it matters: the whole Phase 2 value-of-information framing (Decision D6) and the Phase 0 baseline
comparison depend on these weights being right. Currently sourced from a research pass, not directly
read from evaluator source code.
Where to check: `local_evaluator.py` or equivalent in the participant kit — read the actual scoring
function, don't trust the summarized formula blindly.

**Q10. Does the BM25 starter agent's reported baseline (HitRate@10 0.125, MRR 0.068, MTTC 9.81) reflect
the public dev set, the private set, or both?**
Why it matters: minor — affects exactly what "beating the baseline" means as a Phase 0 exit criterion.
Assume public set unless the repo says otherwise; re-run the starter agent locally against the dev set
to get a first-hand number regardless, rather than relying solely on the reported figure.

## How to close these out

When starting a coding session, the first concrete task should be: clone the repo, locate and read
`agent_api_contract.json` (or equivalent) and `competition_specification.md` (or equivalent), answer
Q1–Q3 directly from the source, and update this file (change status from "unverified" to "confirmed: ...
[quote or paraphrase the actual contract]") before writing any code that depends on them. Q4–Q10 can be
resolved opportunistically during Phase 0 implementation as the relevant files get touched.
