# Proactive Clarification Question Generation for Turn-Budgeted Shopping Copilots

Research scope: how conversational search/recommendation systems decide **when** to ask a
clarifying question vs. return results, how they choose **what** to ask, and how a **hard
turn budget** (max 10 turns, MTTC-penalized) should shape that policy — for a frozen,
in-memory, text-only, no-fine-tuning Amazon `Clothing_Shoes_and_Jewelry` shopping copilot
(TikTok TechJam 2026 Track 4).

## Overview

Two academic lineages converge on this problem and both point the same direction:

1. **Conversational search / clarifying-question generation** (SIGIR/IR community: Qulac,
   ClariQ, Sekulic et al.) — treats "ask vs. answer" as a query-ambiguity classification
   problem and clarification-question generation as a retrieval-conditioned NLG problem.
2. **Multi-turn Conversational Recommender Systems (MCR)** (RecSys/AI community: EAR, SCPR,
   UNICORN/CRIF, decision-tree CRS, and 2024–2026 LLM-CRS follow-ups) — treats "ask vs.
   recommend" as a *sequential decision policy* over a shrinking candidate set, explicitly
   optimized against turn-count metrics (**Success Rate@T**, **Average Turns**) that are the
   direct ancestors of this competition's **MTTC**.

The unifying mechanism across both lineages, and the one most directly transferable to our
constraints, is: **maintain a live candidate pool; measure its ambiguity via entropy /
score-distribution spread; ask only when that ambiguity is high enough that a question is
expected to net-save turns; and when you do ask, ask about the single facet that splits the
pool the most (maximum expected information gain), phrased as a small closed set of concrete
options rather than an open-ended question.** This is exactly the "Over-Generality → cutoff →
structured proactive clarification" capability the track requires, and it needs no model
training — it is computable from catalog statistics and retrieval scores alone.

## Key approaches found (with inline citations/links)

### 1. Deciding WHEN to ask — ambiguity/uncertainty signals

- **Qulac / ClariQ (Aliannejadi et al., SIGIR'19; SCAI'20 shared task).** Formalized "asking
  clarifying questions in open-domain information-seeking conversations" as a first-class IR
  task, built on TREC Web Track topics with (topic, facet, question, answer) tuples. Their
  oracle experiment found that **asking just one good clarifying question improved P@1 by
  over 170%**, empirically justifying that clarification is worth a turn *when the query is
  genuinely under-specified/faceted* (multiple valid facets exist for one query). ClariQ
  extended this to multi-turn synthetic conversations and to a **classification sub-task of
  deciding *whether* clarification is needed at all**, not just what to ask. ([Aliannejadi et al. 2019, arXiv:1907.06554](https://arxiv.org/pdf/1907.06554); [ClariQ dataset](https://github.com/aliannejadi/ClariQ))
- **Entropy over the candidate/attribute pool is the dominant "when" signal in conversational
  *recommendation* (as opposed to open-domain search).** EAR (Estimation–Action–Reflection,
  Lei et al., WSDM'20) and SCPR (Lei et al., graph-based path reasoning) both estimate user
  preference over items *and* attributes, then pick the attribute with **maximum entropy**
  among remaining candidates as the next question, and use a learned policy to decide
  ask-vs-recommend based on how much the top-ranked candidates' scores have separated.
  ([EAR, arXiv:2002.09102](https://arxiv.org/abs/2002.09102); [Learning to Ask Appropriate Questions, KBQG, arXiv:2105.04774](https://arxiv.org/abs/2105.04774))
- **Direct catalog-scale precedent: entropy over the *retrieval score distribution*.**
  "Modeling shopper interest broadness with entropy-driven dialogue policy in the context of
  arbitrarily large product catalogs" (arXiv:2509.06185) is the closest prior art to our exact
  situation — a live e-commerce dialogue policy that computes **normalized entropy of the
  top-k reranked retrieval scores** and routes low-entropy (score mass concentrated on one
  item) queries straight to a confident recommendation, while high-entropy (score mass spread
  across many candidates) queries trigger one or two clarifying questions. Their formula:

  ```
  H_k^N(q) = − Σ_{i=1..k} P_i log P_i / log k   ∈ [0, 1]
  where P_i = s(q, p_i) / Σ_j s(q, p_j),  s = calibrated reranker score
  ```

  This is a clean, training-free, in-memory-computable **Over-Generality trigger**: no LLM
  call needed, just a softmax + entropy over whatever ranker scores you already produced.
  Their empirical calibration on organic search logs found **recall@10 plateaus around
  entropy ≈0.3 and ≈0.8**, i.e., three natural regimes (confident / ambiguous / exploratory)
  that map directly onto a threshold-based trigger. They note the caveat that a merchant-style
  aggressiveness knob (their "educational / balanced / pushy" presets) trades off engagement
  vs. conversion, and in their online test the entropy-gated policy increased conversation
  length with only a statistically insignificant conversion lift — a direct warning that
  clarification is not free and must be *targeted*, not reflexive.
  ([arXiv:2509.06185](https://arxiv.org/abs/2509.06185))
- **Score-distribution / confidence-gap framing recurs across the literature** as an
  alternative/complement to entropy: a large gap between rank-1 and rank-2 scores signals
  confidence (answer directly); a flat top-K score curve signals ambiguity (clarify). This is
  the same signal as "candidate pool size too large to confidently rank" named in the track
  brief — entropy and top-1/top-2 score gap are two operationalizations of the same idea, and
  entropy has the advantage of being a single normalized number in [0,1] independent of K.
- **Decision-theoretic / value-of-information framing.** Recent LLM-agent work explicitly
  casts "ask or act" as a **value-of-information (VOI) problem**: pay a turn/latency cost now
  to reduce uncertainty, only when expected uncertainty-reduction benefit exceeds that cost.
  "Act or Clarify? Modeling Sensitivity to Uncertainty and Cost in Communication"
  (arXiv:2602.02843) formalizes this via expected regret — clarify only when expected
  epistemic benefit outweighs interaction cost. "Ask Early, Ask Late, Ask Right"
  (arXiv:2605.07937) studies *when in a session* to clarify for long-horizon agents, finding
  timing matters as much as content. "Ask to Be Sure" (CIKM'26, arXiv:2608.15949) is the
  closest LLM-CRS analogue: it rewards an LLM policy by the **entropy reduction in the
  recommendation distribution per turn**, i.e., turns that don't measurably shrink uncertainty
  are penalized, which is structurally identical to what an MTTC-penalized objective wants.
- **Uncertainty-guided ambiguity classifiers.** "Human and Model Uncertainty Guidance to Ask
  Clarification Questions" (EACL'24) and "Clarifying the Path to User Satisfaction"
  (Rahmani/Aliannejadi et al., Findings of EACL'24, arXiv:2402.01934) study *when clarification
  actually helps* empirically: their feature-based satisfaction predictors found **(a) short,
  more ambiguous queries benefit the most from clarification**, **(b) specific questions beat
  generic ones**, and **(c) question tone/subjectivity matters** — i.e., blindly clarifying
  every under-specified query is not universally good; it helps most exactly when the query
  itself carries little disambiguating signal, which is a useful trigger-side heuristic
  (short/generic query + large pool → clarify; long/specific query + large pool → the pool
  size may just reflect genuine breadth of acceptable answers, so consider a diversified
  top-K instead of clarifying).

### 2. Structured vs. open-ended clarification questions

- **Attribute-based CRS (structured) vs. open-ended CRS.** The MCR literature draws this
  distinction explicitly: attribute-based systems ask about item attributes with a **bounded
  set of concrete values** (multiple-choice/facet questions), aiming to recommend the target
  "within as few rounds as possible"; open-ended systems allow free natural-language dialogue
  with no predefined slot. Attribute-based framing is what turn-budgeted, metric-driven CRS
  research (EAR, SCPR, KBQG, decision-tree CRS) converges on, precisely because it is
  measurable, low-cognitive-load, and fast to answer (a tap/short reply) vs. free text (higher
  cognitive load, more turns to parse/resolve ambiguity in the *answer itself*).
  ([arXiv:2105.04774](https://arxiv.org/abs/2105.04774); [arXiv:2208.14614](https://arxiv.org/pdf/2208.14614))
- **Facet-driven NLG for phrasing.** Sekulic, Aliannejadi & Crestani ("Towards Facet-Driven
  Generation of Clarifying Questions for Conversational Search", ICTIR'21) fine-tuned GPT-2 on
  ClariQ conditioned on a target facet (e.g., query "kiwi" + facet "fruit" → "Are you
  interested in kiwi fruit?"), and found facet-conditioned generated questions were rated more
  natural/useful than template-based ones — but note this required fine-tuning a generator,
  which conflicts with our no-training constraint. The practical takeaway that *doesn't*
  require training: **a good clarification question names the facet explicitly and offers
  concrete instantiated values drawn from the live candidate pool**, which a template
  ("Looking for a specific color? I see options like {red, blue, black} in this style.") can
  achieve without any fine-tuned generator. ([ICTIR'21 paper](https://irlab.science.uva.nl/wp-content/papercite-data/pdf/sekulic-2021-facet.pdf); [code](https://github.com/isekulic/CQ-generation))
- **Evidence favors specific, closed-form phrasing.** The EACL'24 usefulness study above
  found "specific questions are more effective than generic ones" — reinforcing that a
  structured question naming exact catalog values (not an abstract "can you clarify?") both
  converges faster and is preferred.
- **Amazon's ASK system** (Aspects and Retrieval-based hybrid Clarification, Amazon Science)
  is industrial evidence for the same pattern in task-oriented dialogue: combine
  aspect/attribute-based clarification with retrieval-grounded candidate options rather than
  purely generative open questions. ([Amazon Science paper](https://assets.amazon.science/ff/88/16e14b354abba154007197a19460/ask-aspects-and-retrieval-based-hybrid-clarification-in-task-oriented-dialogue-systems.pdf))

### 3. Choosing WHICH facet to ask about — information-gain / entropy-based facet selection

- **Probabilistic Entropy facet selection (Vandic, Frasincar et al., CIKM'13, "Facet Selection
  Algorithms for Web Product Search").** The canonical, training-free algorithm for this exact
  sub-problem: model each candidate facet as a binary variable "does the target product have
  this facet value" with P(yes) = fraction of remaining candidates with that facet value,
  P(no) = the rest, compute Shannon entropy H = −p·log p − (1−p)·log(1−p) per facet-value, and
  **greedily select the facet(s) with highest entropy first** — maximizing expected reduction
  in candidate-set size per question, i.e., maximum expected information gain. Their
  Probabilistic Entropy method significantly outperformed frequency-based and other facet
  ranking baselines at minimizing the number of steps needed to reach the target product.
  ([CIKM'13 paper](https://personal.eur.nl/frasincar/papers/CIKM2013/cikm2013.pdf); companion "Dynamic Facet Ordering for Faceted Product Search Engines")
- **EAR / SCPR entropy-over-attributes.** Both compute entropy of each candidate attribute's
  value distribution across the remaining item pool and greedily pick the max-entropy
  attribute as the next question — the CRS-literature restatement of the same CIKM'13 idea,
  validated again in "Entropy Guided Diversification and Preference Elicitation in Agentic
  Recommendation Systems" (arXiv:2603.11399), which explicitly frames facet choice as
  "maximizing expected information gain" over a dynamically filtered candidate set, and warns
  that when preference signal remains incomplete, the system should fall back to
  **entropy-based diversification of the shown results** rather than forcing another question
  — an explicit stopping/fallback condition relevant to turn budgets.
- **Practical formula for our catalog:** for each candidate attribute *a* (color, size,
  material, style, brand, occasion, price-band) with values {v1..vn} appearing among the
  current candidate pool, compute the Shannon entropy of the value distribution restricted to
  the pool; the attribute with highest entropy splits the pool most evenly and is expected to
  eliminate the most candidates per answer. This is O(pool_size × num_attributes) and fully
  computable in-memory from the catalog's structured metadata with no ranking model needed
  beyond what retrieval already produced.

### 4. Turn-budget-aware policy — deciding it's "worth it" to clarify

- **Metrics ancestral to MTTC.** MCR literature already evaluates almost exactly what this
  track calls MTTC: **Success Rate@T** (fraction of sessions that reach a successful
  recommendation by turn T) and **Average Turns (AT)** (mean turns to success, with failed
  sessions penalized at T_max) are standard joint metrics in EAR, SCPR, KBQG, decision-tree
  CRS, and hypergraph-RL CRS work — "a lower AT means overall higher efficiency," reported
  jointly with SR@T so that a policy can't game AT by giving up early. KBQG explicitly sets
  T_max = (number of attribute types)+1 and reports SR@T curves for T=1..T_max — the
  direct template for a "hard fail at turn 10" evaluation harness.
  ([KBQG, arXiv:2105.04774](https://arxiv.org/abs/2105.04774); [decision-tree CRS, arXiv:2208.14614](https://arxiv.org/pdf/2208.14614))
- **Value-of-information stopping rule.** Casting each potential clarification as a VOI
  decision: expected turns saved = (probability the answer meaningfully shrinks/reorders the
  candidate pool) × (turns that would otherwise be wasted showing/scrolling through a
  low-confidence ranked list or being rejected and re-querying), compared against the fixed
  cost of 1 turn spent asking. Clarify only when expected turns saved > 1. As remaining turn
  budget shrinks, the bar for "worth it" should rise (a clarification late in a 10-turn budget
  is riskier because there's less runway left to use the answer), consistent with "Ask Early,
  Ask Late, Ask Right" (arXiv:2605.07937) finding that clarification timing materially affects
  outcomes for long-horizon agents, and with RO-PnR-style frameworks that weigh "expected gain
  from probing against its interaction cost" per turn (arXiv:2604.25136).
- **Concrete stopping conditions found across the literature, transferable directly:**
  1. **Pool-size floor:** if the candidate pool is already small enough to rank confidently
     (e.g., below some K where top-1 vs top-2 separation is clear, or entropy below the
     "confident" regime boundary — 0.3 in the arXiv:2509.06185 calibration), skip clarification
     and recommend directly — "if the candidate list is short enough, the system should turn
     to recommend to avoid wasting more turns" (paraphrased finding common to EAR/SCPR-family
     work).
  2. **Turn-budget ceiling:** don't clarify after a late turn threshold (e.g., turn 7–8 of 10)
     regardless of entropy — near the hard cap, any turn spent must go toward a committed
     answer, since a failed/ignored clarification with no turns left to act on it is pure
     waste and directly inflates MTTC / risks the hard-fail cutoff.
  3. **Diminishing-returns / no-progress guard:** if a previous clarification did not
     meaningfully reduce entropy or pool size (compare entropy/pool before vs. after the last
     answer), don't ask another facet question of the same kind — fall back to
     ranking/diversifying and returning a top-K list, matching the diversification fallback in
     arXiv:2603.11399.
  4. **One-shot preference for maximum info gain per question**, since each turn is expensive:
     prefer a single well-chosen high-entropy facet question over multiple lower-value ones,
     and where the domain allows, batching 2 facets into one structured multi-slot question
     (e.g., "color and size?") can trade a little cognitive load for a full extra turn saved —
     but the EACL'24 usefulness study's finding that *specific, non-generic* questions work
     best cautions against over-stuffing a single question until it becomes vague.

### 5. Prior art specific to over-generality-triggered clarification in product search

- **arXiv:2509.06185** (entropy-driven dialogue policy for arbitrarily large product
  catalogs) is the most directly on-point prior art: a live e-commerce policy that computes
  entropy over retrieval/reranker scores to decide discovery (clarify) vs. direct
  recommendation, explicitly designed to avoid "expanding the LLM's context window" — i.e.,
  cutoff-then-clarify instead of dumping a huge ranked list, matching the track's required
  behavior almost exactly.
- **CIKM'13 facet selection** (Vandic/Frasincar) is the closest classical, training-free
  algorithmic prior art for the facet-choice half of the problem, purpose-built for "web
  product search."
- **ProductAgent** (arXiv:2407.00942) and its **PROCLARE** benchmark build an LLM-simulated
  user + strategic clarification-question-generation agent specifically for e-commerce
  product search, reporting that retrieval performance improves with additional clarification
  turns — useful as an evaluation-harness reference (LLM user simulator) even though its
  internal ask/no-ask threshold logic wasn't recoverable from the abstract alone.
- **ConvApparel** (arXiv:2602.16938, EACL'26) is a benchmark/user-simulator specifically for
  **apparel** conversational recommendation (directly our catalog vertical), built to close
  the "realism gap" between LLM-simulated and real shoppers using paired "good" vs "bad"
  recommender trajectories with first-person satisfaction annotations — a strong candidate for
  informing how to simulate a realistic evaluation user for this competition, even though
  exact clarification-trigger details weren't extractable from the abstract.
- **EAR / SCPR / KBQG / decision-tree CRS** (arXiv:2002.09102, arXiv:2105.04774,
  arXiv:2208.14614) are the reference implementations (with released code in most cases) for
  attribute-based ask-vs-recommend policies with entropy-driven facet choice; the
  decision-tree variant is notable for explicitly avoiding deep RL/training, using tree-node
  item diversity as the "ask vs. recommend" stopping signal — directly compatible with a
  no-training, in-memory constraint.
- **ClariQ / CQ-generation repos** (github.com/aliannejadi/ClariQ,
  github.com/isekulic/CQ-generation) are open-source references for the dataset/evaluation
  side (when-to-ask classification, facet-conditioned question templates) though they target
  open-domain search rather than product catalogs specifically.

## Relevance to our constraints (10-turn hard cap, MTTC penalty, in-memory/no-training)

- **The hard 10-turn cap makes entropy/pool-size-based triggering strictly better than
  always-clarify or never-clarify policies.** Literature consistently shows both extremes
  lose: always-clarify wastes turns on queries that are already answerable confidently
  (inflates MTTC, risks the hard-fail cutoff on borderline sessions); never-clarify forces
  low-confidence answers on genuinely ambiguous queries, which the MCR literature shows costs
  *more* turns in expectation (failed recommendation → rejection → re-query cycle) than one
  well-placed clarifying question would have.
- **Every technique surveyed above is trainable-free and computable in pure Python/NumPy in
  memory**: Shannon entropy over retrieval scores or over attribute-value distributions in the
  candidate pool, top-1/top-2 score gaps, and pool-size thresholds are all closed-form
  statistics over data the retrieval stage already produces — no fine-tuning, no external
  service, nothing that touches the frozen catalog beyond read-only lookups. This matches the
  project's no-FM-training / in-memory-only constraints exactly.
- **MTTC directly operationalizes what SR@T / AT already measure in the CRS literature** —
  meaning this is a well-trodden metric family, not a novel one, and the "stopping condition"
  playbook (pool-size floor, turn-budget ceiling, diminishing-returns guard) from that
  literature transfers with only cosmetic renaming.
- **Structured (closed-choice) clarification questions are the right choice over open-ended
  ones** for this track specifically because: (a) they are faster for a simulated/real user to
  answer (lower turns-to-answer and lower ambiguity in parsing the answer, which itself avoids
  burning extra turns on re-interpretation), (b) the evidence base (EACL'24 usefulness study,
  attribute-based CRS literature) shows they converge faster and are rated more useful when
  specific, and (c) they can be generated by simple templates over live catalog facet values
  with zero model calls, which is both cheaper and more reliable under a hard turn cap than an
  LLM free-text question whose value is harder to bound.

## Recommended approach(es) with rationale

**Trigger condition design:**
Compute normalized Shannon entropy over the top-K retrieval/rerank scores (formula from
arXiv:2509.06185: `H = −Σ P_i log P_i / log K`, `P_i` = normalized score) as the primary
Over-Generality signal, computed immediately after the retrieval stage on every turn, before
any expensive ranking/generation step — this is the "immediate retrieval cutoff" the track
requires: if entropy is high, don't proceed to rank/present a huge list; branch to
clarification generation instead. Calibrate two thresholds against this catalog similarly to
the paper's empirical breakpoints (e.g., low ~0.3 = confident-enough to answer directly, high
~0.8 = clearly overloaded/exploratory, ask). Cross-check with a secondary, cheap signal —
raw candidate-pool size after hard filters and top-1/top-2 score gap — since entropy alone can
be noisy on tiny K; require agreement (or a simple weighted combination) before triggering, to
avoid false positives that burn a turn needlessly. Layer the turn-budget policy on top of this
statistical trigger, not instead of it (see below).

**Question generation strategy:**
When triggered, select the single facet/attribute with the highest Shannon entropy of its
value distribution *among the current candidate pool* (CIKM'13 Probabilistic Entropy method /
EAR-style attribute entropy) — this maximizes expected pool-size reduction per question.
Generate the clarification as a **structured, closed-choice prompt** built from a template
populated with the 2–4 most frequent concrete values for that facet actually present in the
pool (e.g., "I found several options — are you looking for a specific color? Popular choices
here: black, red, floral print.") rather than an abstract or generic question. This requires
no model training: it's a template + a groupby/value_counts + entropy computation over the
in-memory catalog dataframe. Avoid open-ended free text as the default; reserve it only as a
fallback when no single facet has enough discriminating entropy (a genuinely flat, low-signal
pool), in which case falling back to a diversified top-K presentation (per arXiv:2603.11399)
may beat a low-value question entirely.

**Turn-budget policy:**
Wrap the statistical trigger in three guardrails drawn directly from the MCR literature's
stopping conditions: (1) a pool-size/entropy floor below which the system always answers
directly regardless of other signals; (2) a turn-index ceiling (e.g., no clarification
initiated after turn 7 of 10) so a late-session clarification can never be issued without
enough remaining budget to act on the answer and still convert; (3) a diminishing-returns
guard that refuses to ask a second clarifying question if the previous one didn't meaningfully
shrink entropy/pool size, falling back to ranking + diversified presentation instead of
looping on low-value questions. Treat each clarification as spending exactly 1 of the 10
turns and only trigger it when the *expected* number of turns saved (avoiding a failed/
rejected low-confidence recommendation and its re-query cost) exceeds 1 — a lightweight,
non-learned approximation of the VOI framing in the decision-theoretic literature above,
computable from simple heuristics (pool size before/after a hypothetical answer) rather than
a trained cost model.

## Dos

- **Do** compute the Over-Generality trigger from statistics you already have after retrieval
  (score entropy, pool size, top-1/top-2 gap) — no extra model call needed.
- **Do** pick the clarification facet by entropy/expected-information-gain over the *live*
  candidate pool, not a static/global facet priority list — the CIKM'13 and EAR/SCPR
  consensus.
- **Do** phrase clarifications as closed, concrete, catalog-grounded choices (2–4 real values
  from the pool), matching the EACL'24 finding that specific questions outperform generic
  ones.
- **Do** enforce a turn-index ceiling and a pool-size floor as hard guardrails around the
  statistical trigger, so clarification frequency naturally tapers as the session nears the
  10-turn cap.
- **Do** treat "ask" as a genuine alternative branch with its own expected-turns accounting,
  not a free action — model it as spending a turn against the MTTC budget explicitly.
- **Do** fall back to a diversified/representative top-K list (rather than a forced
  low-signal question) when no facet has enough discriminating entropy, per
  arXiv:2603.11399's diversification fallback.

## Don'ts

- **Don't** ask a clarifying question just because the pool is "large" in absolute terms —
  use entropy/score-distribution shape, since a large pool with one dominant top score is
  still confidently answerable (per arXiv:2509.06185's low-entropy = confident-answer regime).
- **Don't** use open-ended free-text clarification as the default — it costs more turns to
  parse the answer and the literature (attribute-based CRS, EACL'24) favors structured
  choices for turn efficiency.
- **Don't** clarify repeatedly on the same low-information dimension if a prior answer didn't
  shrink the pool — that's exactly the "unnecessary conversational cognitive load" the MTTC
  penalty punishes.
- **Don't** clarify late in the session (near turn 10) without enough remaining turns to act
  on the answer — a clarification with no runway left to convert is a wasted turn by
  construction.
- **Don't** rely on any fine-tuned clarification-generation model (e.g., Sekulic et al.'s
  GPT-2 facet-conditioned generator) — it requires training data/fine-tuning that conflicts
  with the no-FM-training constraint; template-based generation over live facet values is the
  training-free substitute with comparable or better measured specificity.
- **Don't** conflate "many valid answers exist" (genuine category breadth, e.g., a broad
  browsing query) with "the system is uncertain" — the EACL'24 findings suggest clarification
  helps most for short/ambiguous queries specifically, not merely broad ones; for broad-but-
  clear queries, diversified ranking may serve the user better than another question.

## References

- Aliannejadi, Zamani, Crestani, Croft. "Asking Clarifying Questions in Open-Domain
  Information-Seeking Conversations." SIGIR'19. https://arxiv.org/pdf/1907.06554
- ClariQ dataset / SCAI'20 challenge. https://github.com/aliannejadi/ClariQ
- Sekulic, Aliannejadi, Crestani. "Towards Facet-Driven Generation of Clarifying Questions for
  Conversational Search." ICTIR'21.
  https://irlab.science.uva.nl/wp-content/papercite-data/pdf/sekulic-2021-facet.pdf ;
  code: https://github.com/isekulic/CQ-generation
- Vandic, Frasincar, et al. "Facet Selection Algorithms for Web Product Search." CIKM'13.
  https://personal.eur.nl/frasincar/papers/CIKM2013/cikm2013.pdf
- Lei et al. "Estimation–Action–Reflection: Towards Deep Interaction Between Conversational
  and Recommender Systems." WSDM'20. https://arxiv.org/abs/2002.09102
- "Learning to Ask Appropriate Questions in Conversational Recommendation" (KBQG).
  https://arxiv.org/abs/2105.04774
- "Rethinking Conversational Recommendations: Is Decision Tree All You Need?"
  https://arxiv.org/pdf/2208.14614
- "Modeling shopper interest broadness with entropy-driven dialogue policy in the context of
  arbitrarily large product catalogs." https://arxiv.org/abs/2509.06185
- "Entropy Guided Diversification and Preference Elicitation in Agentic Recommendation
  Systems." https://arxiv.org/abs/2603.11399
- "Ask to Be Sure: Informative Interactions for Confident Multi-Turn LLM Recommendation."
  CIKM'26. https://arxiv.org/abs/2608.15949
- "Act or Clarify? Modeling Sensitivity to Uncertainty and Cost in Communication."
  https://arxiv.org/html/2602.02843v3
- "Ask Early, Ask Late, Ask Right: When Does Clarification Timing Matter for Long-Horizon
  Agents?" https://arxiv.org/pdf/2605.07937
- "Frictive Policy Optimization for LLMs: Epistemic Intervention, Risk-Sensitive Control, and
  Reflective Alignment." https://arxiv.org/pdf/2604.25136
- Rahmani, Wang, Aliannejadi, Naghiaei, Yilmaz. "Clarifying the Path to User Satisfaction: An
  Investigation into Clarification Usefulness." Findings of EACL'24.
  https://arxiv.org/abs/2402.01934 / https://aclanthology.org/2024.findings-eacl.84/
- "Human and Model Uncertainty Guidance to Ask Clarification Questions." EACL'24.
  https://aclanthology.org/2024.eacl-long.16.pdf
- ProductAgent / PROCLARE benchmark. "Benchmarking Conversational Product Search Agent with
  Asking Clarification Questions." https://arxiv.org/pdf/2407.00942
- ConvApparel: "A Benchmark Dataset and Validation Framework for User Simulators in
  Conversational Recommenders" (apparel domain, EACL'26). https://arxiv.org/pdf/2602.16938
- ASK: Aspects and Retrieval-based Hybrid Clarification in Task-Oriented Dialogue Systems
  (Amazon Science).
  https://assets.amazon.science/ff/88/16e14b354abba154007197a19460/ask-aspects-and-retrieval-based-hybrid-clarification-in-task-oriented-dialogue-systems.pdf
- Christakopoulou et al., "Towards Question-based Recommender Systems."
  https://arxiv.org/pdf/2005.14255
- "A Survey on Asking Clarification Questions Datasets in Conversational Systems." ACL'23.
  https://aclanthology.org/2023.acl-long.152.pdf
- "Advances and Challenges in Conversational Recommender Systems: A Survey."
  https://arxiv.org/pdf/2101.09459
