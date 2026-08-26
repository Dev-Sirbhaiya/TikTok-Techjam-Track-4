# Evaluation & Benchmarks: How Conversational Recommendation Systems Are Scored, and How to Optimize Jointly for Recall, Ranking, and Efficiency

## Overview

TechJam Track 4 scores agents on three axes anchored to the session's final purchased `parent_asin`: **Coverage** (Hit Rate@K), **Precision** (MRR / Top-K Hit Rate), and **Efficiency** (MTTC, capped at 10 turns). This is an unusual combination for IR evaluation — standard recommender-system benchmarks (Hit Rate@K, MRR, NDCG) only ever measure the first two axes over a *static* candidate list; they say nothing about the *cost* of getting there. Adding a hard-capped turn-efficiency term makes this closer to task-oriented dialogue evaluation (e.g., MultiWOZ's Inform/Success/BLEU) or RL-based dialogue policy learning, where "turns to success" is treated as an explicit cost term traded off against task success rate.

The central design tension for this challenge is real and well-documented in the conversational search/CRS literature: **asking a clarifying question reliably improves precision-type metrics (MRR, NDCG@1, P@1) but costs a turn**, and turns are capped at 10 with a hard zero-score cliff if exceeded. This document surveys (1) how Hit Rate@K and MRR are defined and what "good" looks like in product-search literature, (2) how conversational/dialogue systems have historically formalized efficiency and combined it with task success, (3) what the literature says about the precision-vs-turns trade-off specifically, (4) how the organizer's `TechnicalScore` appears to be built (verified against the participant repo, with residual caveats), and (5) where to spend limited build time for best ROI.

Everything below is tagged inline as **[Established]** (directly supported by literature/sources found) or **[Inference]** (my reasoning applied to this specific competition, to be verified once the local evaluator code is actually run).

---

## Metric definitions and typical benchmarks from literature

### Hit Rate@K (HR@K)

**[Established]** HR@K (a.k.a. Recall@K / HitRatio@K in top-N recommendation literature) is a binary, rank-agnostic hit indicator: it equals 1 if the ground-truth item appears anywhere in the top-K list, 0 otherwise, averaged over all sessions. It measures *coverage* — whether the correct answer survived the retrieval/candidate-generation stage at all — independent of where within the top K it lands (Towards Data Science, "How to Assess Recommender Systems"; Shaped.ai, "Evaluation Metrics for Search and Recommendation Systems").

- **Typical K values** in the recommender-systems literature are K = 5, 10, 20, sometimes evaluated at multiple cutoffs simultaneously to show how quickly recall saturates (arXiv:2408.14851, survey of GNN/sequential session-based recommendation).
- **Typical value ranges**: on session-based recommendation benchmarks (Yoochoose, Diginetica), reported HR@20 / Recall@20 (often written P@20 in these papers) ranges roughly from the high-40s to low-70s (percent) depending on dataset difficulty and model sophistication — e.g., one comparison reports Yoochoose P@20 ≈ 60–72% and Diginetica P@20 ≈ 44–53% across baseline-to-SOTA model families (arXiv:2309.12218, SR-PredictAO and related session-rec papers). Weak non-neural baselines (POP, S-POP) land far lower (Diginetica R@20 ≈ 0.9%–21%).
- On the Amazon ESCI product-search benchmark (query→product ranking rather than session recall, so not directly comparable), fine-tuned cross-encoder baselines report nDCG ≈ 0.85, and the KDD Cup 2022 winning submission reached nDCG ≈ 0.90 (arXiv:2405.15190; Amazon Science KDD Cup summary) — illustrating that with strong supervised ranking, near-ceiling ranking quality is achievable on curated relevance-labeled data, but ESCI is a *labeled-relevance* task, not a session/next-item task, so it over-states what's achievable for a cold, single-purchase-anchored session task like this one.
- **Pitfall — sensitivity to K [Established]**: HR@K is monotonically non-decreasing in K by construction, so raising K trivially inflates the score; comparisons across systems or papers are only meaningful at matched K. This challenge fixes K = 10 (`HitRate@10`, confirmed from the participant repo — see below), which removes this particular ambiguity for the competition itself, but it means retrieval-stage effort should be tuned specifically for "is the item in the top 10 candidates," not top-50 or top-100 recall, which is a materially different (and easier) target than typical academic Recall@50/100 recall-stage numbers.
- **Pitfall — coverage vs usefulness [Established]**: HR@K says nothing about *where* in the top K the item sits, so a system can max out HR@10 while still burying the correct item at rank 10 every time — useless to a user who only reads the first result. This is precisely why HR@K is always reported alongside a rank-sensitive metric like MRR or NDCG (Towards Data Science; recometrics R vignette).

### MRR (Mean Reciprocal Rank)

**[Established]** MRR = mean over sessions of 1/rank(target item) if the target is found within the considered list, else 0. Unlike HR@K, MRR is *rank-sensitive*: a hit at rank 1 contributes 1.0, at rank 2 contributes 0.5, at rank 10 contributes 0.1 — an order of magnitude difference in reward for two outcomes that would score identically under HR@10 (recometrics documentation; Shaped.ai).

- **Typical value ranges**: on session-based rec benchmarks, MRR@20 commonly falls in the high-teens to low-30s (percent) — e.g., ≈18–37% MRR@20 across the Yoochoose/Diginetica literature depending on model (arXiv:2309.12218 and related). Because MRR divides by rank, it is numerically much smaller than HR@K at the same K for any system that doesn't consistently rank the target near #1.
- **Pitfall — dominated by rank-1 misses [Established/Inference]**: Because reciprocal rank falls off sharply (1, 0.5, 0.33, 0.25, 0.2, …), MRR is disproportionately driven by whether the system nails rank 1 or rank 2; the marginal value of moving a correct answer from rank 9 to rank 5 is tiny (0.11→0.20) compared to moving it from rank 2 to rank 1 (0.5→1.0). This has a direct implication for this competition: a re-ranking/LLM-scoring stage that reliably promotes the true item to rank-1-or-2 (even if it occasionally drops out of top 10 entirely) will move MRR far more than a retrieval stage that pads the top 10 with more plausible-but-not-first candidates. Practically, ranking-stage precision work has outsized MRR leverage relative to broadening recall.
- **Pitfall — undefined/zero on miss [Established]**: sessions where the target never appears in the considered list contribute exactly 0 to MRR (not a small penalty) — so MRR is jointly bounded above by HR@K (you cannot have non-trivial MRR without non-trivial HR@K first). This is the formal reason "coverage" logically gates "precision": a ranking model has nothing to rank correctly if retrieval never surfaces the item.
- **Top-K Hit Rate as MRR proxy [Established]**: the problem statement's "Precision (MRR / Top-K Hit Rate)" pairing reflects a common practice in industry recsys reporting where MRR and a tighter Hit-Rate-at-small-K (e.g., HR@1 or HR@3) are reported together as complementary precision signals, since MRR alone can be hard for practitioners to interpret intuitively while HR@1 ("did we get it exactly right") is not.

### Conversational recommender system (CRS) efficiency framing

**[Established]** The CRS evaluation literature (survey: "Evaluating Conversational Recommender Systems: A Landscape of Research," arXiv:2208.12061; "Evaluating User Experience in Conversational Recommender Systems," arXiv:2508.02096; ACM TORS "CRS-Que") consistently identifies **efficiency of task support** as a first-class evaluation dimension alongside effectiveness, conversational quality, and subtask quality. Concretely:
- Efficiency is operationalized as *number of interaction cycles / dialogue turns before an acceptable recommendation is reached*, or *task completion time* in user studies — the general assumption in this literature is explicitly "shorter is better," mirroring MTTC's design in this challenge.
- Evaluation in this space blends objective/computational metrics (turns, acceptance rate, task completion) with subjective/perception metrics (satisfaction, trust, novelty via Likert surveys) — but for an automated hackathon evaluator, only the objective/behavioral side (turns, hit/rank) is measurable, which is exactly what TechJam's evaluator implements.

### Task-oriented dialogue: the MultiWOZ precedent for combined scoring

**[Established]** The closest existing precedent for combining a "did we get the answer right" metric with dialogue-level scoring is MultiWOZ's standard trio: **Inform rate** (did the system surface all correct entities), **Success rate** (did it fully satisfy the informational/booking goal), and **BLEU** (response fluency), combined into a single **Combined Score = (Inform + Success) × 0.5 + BLEU** (Budzianowski et al. 2018; discussed critically in "Shades of BLEU, Flavours of Success," arXiv:2106.05555). Two lessons transfer directly:
1. **Weighted linear combination of heterogeneous metrics into one leaderboard number is standard practice** — not a bespoke or unusual choice by the TechJam organizers.
2. **This style of scoring is known to be gameable and inconsistently reproducible** across papers/implementations due to preprocessing and edge-case differences (arXiv:2106.05555 documents exactly this for MultiWOZ) — a caution to carry into how we interpret our own local-evaluator numbers: match the evaluator's exact tie-breaking / edge-case behavior (e.g., what happens on a session with zero turns, or duplicate parent_asins) rather than re-deriving metrics independently, since subtle definitional mismatches are the single most common source of score discrepancies in this literature.

Note MultiWOZ has no direct *turn-count* efficiency term in its combined score (BLEU stands in for "response quality," not efficiency) — so it is not a perfect analogy for MTTC. The turn-cost-explicit analogy is stronger in RL dialogue-policy literature (below).

---

## The precision-vs-efficiency tension and how prior work handles it

This is the crux of the challenge design, and it is a well-studied tension across two adjacent literatures.

### 1. Clarifying questions measurably improve precision-type metrics

**[Established]** Multiple conversational-search papers quantify large, front-loaded precision gains from asking even a single clarifying question:
- Asking one well-chosen clarifying question was reported to improve document retrieval precision by **~170%** relative, with especially large gains at the top of the ranking — **nDCG@1 improved ~173%, P@1 ~158%** in one conversational-search study (found via clarifying-question generation literature; consistent with Aliannejadi et al.-style "Asking Clarifying Questions in Open-Domain Information-Seeking Conversations," arXiv:1907.06554, and follow-on work).
- "ProductAgent: Benchmarking Conversational Product Search Agent with Asking Clarification Questions" (arXiv:2407.00942) — directly on conversational **product** search, closely analogous to this challenge — reports that retrieval performance improves with increasing dialogue turns because "user demands become gradually more explicit and detailed" as clarification proceeds, evaluated via an LLM-based user simulator and their PROCLARE benchmark.
- Multi-turn clarification work studying turn-by-turn retrieval scores (found in the "Multi-Turn Multi-Modal Question Clarification" line of research) reports **diminishing returns**: the score jump from turn 1→2 is larger than turn 2→3, i.e., a Pareto-like curve — most of the achievable precision gain from clarification is realized in the *first one or two* clarifying turns, with rapidly shrinking marginal benefit afterward, and explicit warnings in this literature that asking "too many" clarifying questions stops helping and starts hurting the user experience.

### 2. Clarifying questions cost turns, and turn-count is explicitly penalized in dialogue-policy literature

**[Established]** In the task-oriented dialogue RL literature (PyDial-style user-simulator training, e.g. "An Asynchronous Updating Reinforcement Learning Framework for Task-oriented Dialog Systems," arXiv:2305.02718; "Reward estimation for dialogue policy optimisation"), the canonical reward function is:

> reward = (large positive terminal reward if task succeeds) + (large negative terminal penalty if it fails) + (small negative constant "turn penalty" applied at *every* turn, to bias the policy toward shorter dialogues)

This is functionally isomorphic to what MTTC is doing at the *evaluation* level (rather than the *training* level) in this challenge: it converts "turns taken" into a monotonic efficiency penalty, and — importantly — the RL literature treats the per-turn penalty as a *small constant*, not something that should dominate the reward, because over-weighting the turn penalty teaches the policy to blurt out a low-confidence answer immediately rather than clarify when genuinely ambiguous. This is the formal version of the failure mode this challenge is guarding against on both sides (a system that always asks → runs out the 10-turn clock and scores zero; a system that never asks → answers fast but with low HR@10/MRR because it retrieved/ranked based on an underspecified query).

### 3. Risk-aware / cost-sensitive stopping as the resolution mechanism

**[Established]** "Controlling the Risk of Conversational Search via Reinforcement Learning" (arXiv:2101.06327, on real MSDialog data) frames this exactly as a **risk-reward decision at every turn**: at each point the agent compares the expected retrieval-quality gain from asking one more clarifying question against the cost/risk of that additional turn (user frustration, abandonment), and only clarifies when the expected gain outweighs the cost — trained via RL directly on real conversation logs without extra annotation, and shown to outperform "always clarify" and "never clarify" baselines. Related survey work ("How to Approach Ambiguous Queries in Conversational Search," ACM CSUR, doi:10.1145/3534965) frames the general design space as **budgeted turns, cost-sensitive stopping rules, or single-turn clarification** as the three standard mitigations against unbounded clarification cost — i.e., the field's consensus resolution is *not* "always ask" or "never ask" but a **learned or heuristic stopping condition** gated on expected information gain vs. turns remaining.
- A directly relevant finding: "in conversational search sessions of similar total length, taking a feedback/clarification turn comes at the expense of an alternative action (e.g., issuing another query)" — clarification and search are turn-competitive actions drawn from the same fixed budget, exactly mirroring this challenge's 10-turn hard cap.

### 4. Entropy/ambiguity-gated dialogue policy — closest analog to this challenge's own architecture

**[Established]** "Modeling shopper interest broadness with entropy-driven dialogue policy in the context of arbitrarily large product catalogs" (arXiv:2509.06185) is functionally almost a direct precedent for the "Dual-Track Routing" and "Proactive Guidance on Over-Generality" requirements in this challenge's own problem statement: it routes **low-entropy (specific) queries → direct recommendation**, and **high-entropy (ambiguous) queries → exploratory clarifying question**, using the entropy of the retrieval score distribution as the routing signal, explicitly to stay efficient over a large catalog without always paying the clarification-turn cost. This validates "candidate-pool-overload-triggered clarification" (mentioned in the problem statement's Section II) as a technique with direct literature support, not just an ad hoc heuristic — and offers a concrete, cheap signal (entropy or score-gap of the retrieval-stage candidate distribution) to decide *when* asking is worth the turn.

### Net synthesis of the trade-off literature [Inference building on the above]

No paper found gives a universal "N clarifying questions is optimal" answer — the optimum is dataset- and ambiguity-distribution-dependent. But the consistent qualitative shape across all sources above is:
- Gains from clarification are **front-loaded and convex-decreasing** (first question worth much more than the fifth).
- The decision to clarify should be **conditional on measured ambiguity** (retrieval score entropy / top-1-vs-top-k score gap / candidate pool size), not a fixed dialogue-turn schedule.
- A **hard budget with graceful degradation** (stop clarifying and commit to best-guess ranking as turns run low) beats both extremes. Given this challenge's binary catastrophic cliff at turn 10 (hard cap, zero score if exceeded — confirmed below, treated even more harshly than MTTC's own linear decay), the policy should treat "turns remaining" as a hard constraint that forces a final commit well before turn 10, not just a soft efficiency cost.

---

## How TechnicalScore is actually computed, and where the leverage is

**[Established — verified directly, not inferred]** The participant repository (`github.com/TechJam2026/techjam-conversational-search`) README was fetched directly (two independent fetches of the GitHub page and the raw README both agree) and states the scoring formula explicitly:

```
TechnicalScore = 0.50 × HitRate@10 + 0.30 × MRR + 0.20 × Efficiency
Efficiency = clip((11 - MTTC) / 10, 0, 1)
```

Where, per the repo:
- **HitRate@10**: proportion of sessions where the target `parent_asin` appears in the top 10 recommendations within 10 turns.
- **MRR**: mean reciprocal rank of the target's first appearance; failed sessions contribute 0.
- **MTTC**: mean turn number at which the target first appears; failed/unsuccessful sessions are counted as turn 11 (i.e., MTTC is capped/penalized rather than left undefined — this also means Efficiency for a totally failed session is exactly 0, since clip((11-11)/10,0,1)=0).
- The weak BM25 starter baseline achieves **HitRate@10 ≈ 0.125, MRR ≈ 0.068, MTTC ≈ 9.81** on the 200 public sessions — i.e., Efficiency ≈ clip((11-9.81)/10,0,1) ≈ 0.119, giving a baseline TechnicalScore ≈ 0.50×0.125 + 0.30×0.068 + 0.20×0.119 ≈ **0.106**. This confirms the starter is intentionally weak across all three axes simultaneously (low coverage, near-zero ranking precision, and near-worst-case efficiency, since it almost never finds the item until the session is nearly exhausted).

**Marginal-value implications of this exact formula [Established arithmetic, given the formula above]:**
- **HitRate@10 carries the largest weight (0.50) and the largest realistic headroom.** The baseline's HR@10 of 0.125 means ~87.5% of sessions never even get the target into the top 10 at all — this is the single biggest lever available, and every point of HR@10 improvement is worth more (0.50 per unit) than the same-sized improvement in MRR (0.30 per unit) or Efficiency (0.20 per unit). Moreover, per the earlier point that **MRR is mechanically bounded above by HR@K**, fixing retrieval recall is a prerequisite for MRR gains too — a session where the item never appears in the top 10 contributes 0 to both HR@10 and MRR simultaneously. This makes retrieval/recall-stage improvement (better query understanding, hybrid keyword+category+vector retrieval as the problem statement specifies) the highest-leverage, lowest-risk first investment.
- **MRR (0.30) is the reranking/LLM-semantic-ranking payoff.** Once HR@10 is reasonably high, the marginal path to more TechnicalScore is pushing the already-retrieved item from rank ~5–10 up toward rank 1, which is squarely the "LLM Semantic Ranking" stage the problem statement calls for. Given MRR's convex reward shape (established above), a ranker need not be perfect — reliably getting hits into the top 2–3 captures most of the achievable MRR gain.
- **Efficiency (0.20) is the smallest weight, has a floor of 0, and only pays off once HitRate/MRR are already non-trivial** — a session that fails to find the item at all gets Efficiency = 0 regardless of how few turns were spent trying (since a "failed" session is scored as if it took all 11 turns). This has a strong practical corollary: **efficiency is not free-standing** — there is no reward for "asking zero questions" in isolation; it only pays off *conditional on* actually finding the right item. A system that answers instantly but wrongly loses on all three terms simultaneously (HR@10, MRR, and Efficiency all collapse to/near 0 for that session), while a system that takes 4–5 turns but finds the item scores non-trivially on all three. This is the formal reason the "ask only when it measurably improves the odds of hitting top-10/top-1" policy (entropy-gated clarification, above) dominates a fixed-turns-then-answer policy or a never-ask policy.

**[Inference — flagged explicitly for verification]** This formula was recovered via two independent WebFetch summarizations of the README, not by directly reading `evaluator/local_evaluator.py` source (which lives under `external/` and was explicitly out of scope for this research task). Both fetches agreed on the formula and on specific baseline numbers (0.068034 MRR, 9.81 MTTC), which is reassuring, but the following should still be confirmed once the actual evaluator code is inspected:
1. Exact rounding/precision behavior of the `clip()` and averaging operations.
2. Whether "Top-K Hit Rate" mentioned separately in the official problem statement (`Precision (MRR / Top-K Hit Rate)`) is a distinct reported metric from HitRate@10, or the same quantity described two ways.
3. Whether ties (target tied in score with other items at the cutoff rank) are broken in a specific documented order.
4. Whether the 200 public dev sessions and 800 private eval sessions are scored with the *identical* formula/weights, or whether the private set could reweight axes — the problem statement doesn't say, so treat the public formula as the working assumption but don't over-fit exclusively to it in ways that would look bad under a different plausible weighting (e.g., don't sacrifice HR@10 entirely to chase Efficiency, since Efficiency's own ceiling is only 0.20 of the total and it is zero for any failed session anyway).
5. Whether the harsh "turn 11 / zero-Efficiency" treatment of a failed session is exactly what happens on session timeout in-practice, versus some sessions being excluded from MTTC's denominator entirely — this materially changes whether "give up and guess" late in a session is better than silently timing out.

---

## Guidance on where to invest effort first, and why

Given a 72-hour build budget, the standard incremental-build pattern in both the CRS literature and general IR-system practice, **combined with the concrete formula above**, points to this ROI ordering:

### 1. Get retrieval coverage (Hit Rate@10) working first — highest weight, largest headroom, and a prerequisite for everything else
**[Established pattern + Inference specific to this formula]** This is both standard IR-system-building practice (get candidates right before ranking them) and mathematically forced here: MRR cannot exceed what HR@10 allows, and Efficiency is zero whenever the session fails outright. A baseline hybrid retrieval (BM25/keyword + category filter + a cheap embedding similarity signal) that reliably gets the true item into the top 10 is worth building and validating against the 200 public dev sessions before touching the ranking or dialogue-policy layers at all. This also happens to match the problem statement's own architecture ("Multi-Route Retrieval → LLM Semantic Ranking" — retrieval is explicitly the base of the pipeline).

### 2. Then invest in ranking precision (MRR) — second-highest weight, and typically cheap relative to its payoff
**[Established + Inference]** Once coverage is reasonable, an LLM-based (or even simple heuristic/feature-based) reranking pass over the top-10 candidates is usually the cheapest way to buy MRR: it doesn't require touching the retrieval stack, and because of MRR's convex shape, even a rough reranker that gets "somewhat better than random" ordering among an already-correct top-10 captures a large share of the available MRR gain (analogous to how a single well-placed clarifying question captured ~170% relative gain in the cited literature — small, targeted precision interventions have outsized effect once coverage is solved).

### 3. Efficiency (turns) last, and via a *gating condition*, not a fixed turn schedule
**[Established from CRS/RL literature + Inference]** Because Efficiency has the smallest weight and pays nothing on a failed session, the highest-ROI efficiency work is not "minimize turns aggressively" but rather "don't waste turns clarifying when the retrieval-stage candidate distribution is already confidently converged, and don't over-commit to an answer when it's still highly ambiguous." Concretely, an **entropy/score-gap-gated clarification policy** (per arXiv:2509.06185, above) — ask a clarifying question only when the top-K retrieval scores are flat/ambiguous or the candidate pool is large, and go straight to ranking+answer when one candidate clearly dominates — is both cheap to implement (a threshold on an existing score distribution, no RL training needed) and directly targets the metric literature's consensus mitigation (budgeted/cost-sensitive stopping) rather than either extreme. Given the hard 10-turn zero-score cliff, also build in a forced "commit to best guess by turn ~7–8" fallback so that a stuck conversation never runs out the clock into a total zero.

### Why this order, restated against the literature
- CRS systems are conventionally built up in this same order in practice: a working retrieval/candidate stage is validated first, then a ranking/scoring layer, then a dialogue-management/clarification layer on top — mirroring both the "component-level then holistic" evaluation split described in arXiv:2208.12061 and the problem statement's own four-pillar ordering (Core Architecture → Dialog Strategy → Self-Evolution → Evaluation).
- The RL dialogue-policy literature explicitly warns against over-weighting the turn-penalty term relative to task-success reward, because it teaches premature, low-quality answers — which maps directly to a warning against front-loading engineering effort on Efficiency (0.20 weight, zero-floor on failure) before HitRate@10/MRR (0.80 combined weight, and gating) are solid.
- All three papers on the precision-vs-turns tension (arXiv:2101.06327 risk-aware stopping, arXiv:2509.06185 entropy-gated policy, and the CSUR ambiguous-queries survey's "budgeted turns" framing) converge on the same practical mechanism — a **cheap, threshold-based ambiguity gate on top of an already-working retrieval score distribution** — which is achievable well within a 72-hour budget without any RL training, unlike the academic papers' own more elaborate learned-policy solutions.

---

## Dos

- **Do** validate retrieval-stage Hit Rate@10 against the 200 public dev sessions before investing in reranking or dialogue policy — it is the largest-weighted term and gates the other two mathematically.
- **Do** treat "coverage" and "precision" as sequential, not parallel, investments: an LLM reranker cannot rank an item that retrieval never surfaced.
- **Do** use a cheap, threshold-based signal (retrieval score entropy, score gap between rank-1 and rank-K, or raw candidate-pool size) to decide *whether* to ask a clarifying question at all, rather than a fixed "always ask N questions" schedule — this is the literature's consistent resolution to the precision/efficiency tension.
- **Do** build in a hard "commit by turn ~7–8" fallback given the catastrophic (zero-score) turn-10 cliff — a stuck/looping clarification policy is far worse than a mediocre best-guess answer.
- **Do** front-load clarification value: if asking, prioritize the question(s) most likely to collapse ambiguity fastest (matches the literature's finding that the first 1–2 clarifying turns capture most of the achievable precision gain; turns 3+ show steeply diminishing returns).
- **Do** re-derive and sanity-check the TechnicalScore formula against the actual `evaluator/local_evaluator.py` once available, rather than relying solely on the README text recovered here — treat the 0.50/0.30/0.20 weighting and the `clip((11-MTTC)/10,0,1)` Efficiency transform as strong working assumptions, not confirmed ground truth.
- **Do** report all three raw sub-metrics (not just TechnicalScore) when iterating locally — optimizing a blended scalar without watching its components is how MultiWOZ-style combined scores get inadvertently gamed or misread (arXiv:2106.05555's central critique).

## Don'ts

- **Don't** over-invest early effort in minimizing turns before coverage/precision are solid — Efficiency is the smallest-weighted term and scores exactly 0 on any session where the target is never found, so "answering fast but wrong" helps nothing.
- **Don't** treat Hit Rate@K figures from unrelated benchmarks (session-rec HR@20, ESCI nDCG) as directly predictive of what's achievable here — different K (10 vs 20), different task framing (session next-item vs labeled query-relevance vs single-purchase-anchored conversational retrieval), and a much harder cold-conversation setup make cross-benchmark number comparisons unreliable; use them only as rough sanity ranges, not targets.
- **Don't** ask clarifying questions on a fixed schedule ("always ask exactly 2 questions") — the literature is consistent that the value of a clarifying question is conditional on actual ambiguity in the current candidate set, and asking when already-confident wastes turns for zero precision gain.
- **Don't** assume MRR gains are cheap at every rank — moving a hit from rank 10 to rank 5 is worth far less (in reciprocal-rank terms) than moving it from rank 2 to rank 1; don't over-engineer fine-grained re-ranking across the full top-10 when the bulk of MRR is won or lost in the top 2–3.
- **Don't** let a stuck conversation run to the 10-turn hard cap — because it's a cliff (zero score on the whole session by the problem statement's stated rule, and MTTC treats it as an effectively worst-case turn-11 outcome per the README), an imperfect early guess strictly dominates a "perfect answer that arrives too late."
- **Don't** treat the TechnicalScore weighting recovered here as certain until verified against the actual evaluator code — it was reconstructed from README text via web fetch, not from reading the scoring script directly, and the private 800-session eval set's exact configuration is not guaranteed identical to the public one.

## References

- Towards Data Science — "How to Assess Recommender Systems" (Hit Rate / MRR definitions and worked example): https://towardsdatascience.com/how-to-assess-recommender-systems-10afd6c1fae0/
- Shaped.ai — "Evaluation Metrics for Search and Recommendation Systems": https://www.shaped.ai/blog/evaluation-metrics-for-search-and-recommendation-systems
- recometrics (CRAN vignette) — "Evaluating recommender systems": https://cran.r-project.org/web/packages/recometrics/vignettes/Evaluating_recommender_systems.html
- "A Comprehensive Survey of Evaluation Techniques for Recommendation Systems" — arXiv:2312.16015
- "Graph and Sequential Neural Networks in Session-based Recommendation: A Survey" — arXiv:2408.14851
- "SR-PredictAO: Session-based Recommendation with High-Capability Predictor Add-On" — arXiv:2309.12218
- "Comprehensive Empirical Evaluation of Deep Learning Approaches for Session-based Recommendation in E-Commerce" — arXiv:2010.12540
- "Shopping Queries Dataset: A Large-Scale ESCI Benchmark for Improving Product Search" (Reddy et al.) — https://github.com/amazon-science/esci-data ; Amazon Science KDD Cup 2022 summary: https://www.amazon.science/blog/amazon-product-query-competition-draws-more-than-9-200-submissions
- "Shopping Queries Image Dataset (SQID)" — arXiv:2405.15190
- "Evaluating Conversational Recommender Systems: A Landscape of Research" — arXiv:2208.12061
- "Evaluating User Experience in Conversational Recommender Systems: A Systematic Review Across Classical and LLM-Powered Approaches" — arXiv:2508.02096
- "Understanding and Predicting User Satisfaction with Conversational Recommender Systems" — ACM TOIS, doi:10.1145/3624989
- "CRS-Que: A User-centric Evaluation Framework for Conversational Recommender Systems" — ACM TORS, doi:10.1145/3631534
- "A Survey on Conversational Recommender Systems" — arXiv:2004.00646
- "Conversational Recommendation: Theoretical Model and Complexity Analysis" — arXiv:2111.05578
- Budzianowski et al., MultiWOZ; combined-score formula discussion — "Shades of BLEU, Flavours of Success: The Case of MultiWOZ" — arXiv:2106.05555
- "An Asynchronous Updating Reinforcement Learning Framework for Task-oriented Dialog System" — arXiv:2305.02718 (turn-penalty + success-reward dialogue RL formulation)
- "Deep Reinforcement Learning for On-line Dialogue State Tracking" — arXiv:2009.10321
- "Asking Clarifying Questions in Open-Domain Information-Seeking Conversations" — arXiv:1907.06554
- "Asking Clarifying Questions Based on Negative Feedback in Conversational Search" (MMR-BERT) — arXiv:2107.05760
- "How to Approach Ambiguous Queries in Conversational Search: A Survey of Techniques, Approaches, Tools, and Challenges" — ACM Computing Surveys, doi:10.1145/3534965
- "Controlling the Risk of Conversational Search via Reinforcement Learning" — arXiv:2101.06327
- "Simulating and Modeling the Risk of Conversational Search" — arXiv:2201.00235
- "ProductAgent: Benchmarking Conversational Product Search Agent with Asking Clarification Questions" (PROCLARE benchmark) — arXiv:2407.00942
- "Modeling shopper interest broadness with entropy-driven dialogue policy in the context of arbitrarily large product catalogs" — arXiv:2509.06185
- "ConvApparel: A Benchmark Dataset and Validation Framework for User Simulators in Conversational Recommenders" — arXiv:2602.16938
- "SalesSim: Benchmarking and Aligning Multimodal Language Models as Retail User Simulators" — arXiv:2605.08334
- "Flippi: End To End GenAI Assistant for E-Commerce" — arXiv:2507.05788
- "Multi-Turn Multi-Modal Question Clarification for Enhanced Conversational Understanding" — arXiv:2502.11442
- "Analysing Mixed Initiatives and Search Strategies during Conversational Search" — arXiv:2109.05955
- TechJam 2026 participant repository (Track 4 evaluator/formula, fetched directly): https://github.com/TechJam2026/techjam-conversational-search and raw README at https://raw.githubusercontent.com/TechJam2026/techjam-conversational-search/main/README.md — **note: recovered via web fetch/summarization of the README text, not by reading the evaluator source; re-verify against `evaluator/local_evaluator.py` once locally available.**
- TikTok TechJam 2026 official problem statement (local file, this repo): `C:\External Projects\Tiktok Hackathon\v1\Tiktok_Problem.md`
