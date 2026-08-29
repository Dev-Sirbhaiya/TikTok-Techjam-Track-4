# 03 — Decision Log

Every entry: what was decided, what alternatives were considered, why, and current status. Status
values: **KEPT** (in the architecture, Phase 0/1), **KEPT — GATED** (Phase 2/3, must win an ablation),
**CUT** (explicitly rejected, do not build), **OPEN** (not yet resolved).

---

## Retrieval

### D1 — Hybrid retrieval combined via Reciprocal Rank Fusion (RRF), not a weighted sum
**Status: KEPT (Phase 0).**
A hand-tuned weighted sum of BM25 score + dense cosine similarity requires calibrating two different
score scales against each other, which is fragile and dataset-sensitive. RRF combines by rank position
only (`score = Σ 1/(k + rank)`, typically `k=60`), sidestepping calibration entirely. Validated in
multiple 2024–2026 studies as a consistent improvement over single-method retrieval, because BM25 and
dense methods capture orthogonal aspects of relevance.
**Caveat found in research:** RRF can occasionally *hurt* an already-strong dense retriever (observed
~2–3 nDCG@10 point drops in one 2026 study) — if the dense embedding model in use is clearly
outperforming BM25 alone, verify fusion is actually helping via ablation rather than assuming it.

### D2 — PageIndex-style structural pre-filter over the category tree
**Status: KEPT — GATED (Phase 2, optional).**
Idea: reason over the category hierarchy (Clothing → Shoes → sub-type → attributes) as a coarse filter
before hitting the retrieval index, rather than always searching the full 50k catalog. Inspired by
PageIndex (VectifyAI, Sept 2025), a real, open-source, vectorless reasoning-based retrieval method.
**Caveat:** PageIndex's published results (98.7% on FinanceBench) are for long professional documents,
not product catalogs — the numbers do not transfer, this is an analogous use, not the intended one.
Costs LLM latency/token budget per navigation step. Only build if Phase 0/1 retrieval quality plateaus
and there's time to spare; not a Phase 0 item.

---

## Dialog state, memory, and multi-vector representation

### D3 — Multi-interest hypothesis vectors (MIND/ComiRec-inspired), K vectors instead of one
**Status: KEPT — GATED (Phase 2). Highest-scrutiny item in this document.**
Originally pitched by analogy to MIND (Li et al., CIKM 2019, Alibaba) and ComiRec (Cen et al., KDD 2020),
both of which demonstrated multi-vector user representations beat a single averaged embedding for
heterogeneous intent, at real production scale (Tmall) and validated on Amazon/Taobao data.
**Correction made during design (important — do not lose this framing in the writeup):** the accurate
claim is *"MIND/ComiRec demonstrate multi-vector representations preserve heterogeneous intent better
than a single averaged one, in a recommendation setting built on behavioral click/purchase sequences —
this design adapts that principle to conversational turns and tests empirically whether it transfers."*
NOT "ComiRec works on Amazon, therefore ours will work" — that does not follow, because the input
modality (behavioral sequences vs. a single text conversation) is fundamentally different, and no
benchmark exists for the conversational-turn adaptation.
**Further correction — MIND/ComiRec are NOT pretrained/downloadable models.** They are architectures
Alibaba trained end-to-end on their own data, with item embeddings tied to Taobao/Tmall's specific
catalog. There is no public checkpoint to reuse, the item-embedding space wouldn't transfer to Amazon's
catalog even if there were, and the input type (behavioral sequences, not text) is wrong regardless.
What actually gets built here is an **untrained, hand-built reimplementation of the routing pattern**
(K vectors, attention-based soft routing, probabilistic fusion) using off-the-shelf embedding tools —
not a trained, benchmark-validated system. The literature's wins belong to the trained version; this
system inherits the *idea*, not the *evidence*.
**Documented failure mode from research:** multi-interest decomposition can *underperform* a single
representation when interests aren't genuinely multi-faceted (TiMiRec authors found joint multi-interest
training "leads to much worse results" on some datasets), and K is dataset-sensitive with no universal
right value.
**Mandatory gate:** ablate K=1 vs K=2 vs K=3 vs K=4 against the dev-session evaluator (see
`06_ABLATIONS_AND_METRICS.md`). If K=1 ties or wins, do not ship K>1.
**Mechanics if kept:** context-conditioned encoding (`v_k = Enc(shared_context + interest_k_context +
current_turn)`, not just `Enc("minimalist")` alone, so no branch loses track of hard constraints like
budget); probabilistic fusion (`Score(product) = Σ_k p_k · Sim(v_k, product)`) instead of hard
delete/spawn of vectors; dynamic effective K that shrinks as confidence rises (interest probabilities
concentrate rather than staying uniform).

### D4 — Context distillation as an explicit structured object (`DialogState` / "C_t")
**Status: KEPT (Phase 0).**
Rather than feeding downstream logic raw chat history or an implicit mix of a slot dict and turn
history, maintain one explicit structured state: hard constraints, soft preferences, negative
preferences (with confidence tiers, see D5), interest hypotheses (if D3 is kept), pool uncertainty,
facet-utility history, and turns remaining. This is what "context distillation" should mean per the
competition's own framing — a compressed, decision-relevant state, not a bigger prompt.
**Refinement considered:** splitting into two derived views (`C_t^retrieval` vs `C_t^policy`) so
retrieval and the question-selection/turn-policy logic each only see what's relevant to their own
decision. Reasonable but optional polish — a single well-organized `DialogState` object is sufficient
for Phase 0; only split it out if the object grows unwieldy in practice.

### D5 — Rejection memory with three-tier confidence, not binary hard/soft
**Status: KEPT (Phase 0).**
Adopted and refined from an external teammate's proposal.
```
explicit reason given ("too expensive")     → hard filter, strong confidence
comparative negative ("less flashy than #2") → soft down-weight, medium confidence
vague/no reason ("not really my style")      → soft down-weight, medium confidence
implicit ("what else do you have?")          → soft down-weight, WEAK confidence
```
**Important correction made during design:** do not auto-infer a *specific attribute* as the rejection
cause from an implicit/vague signal (e.g., don't assume "what else do you have?" means "dislikes
leather"). That over-interprets weak behavioral signal as a strong attribute-level dislike. For weak/
implicit signals, log only a generic negative on the last-shown item, not an inferred attribute cause.

### D6 — Question/action selection: information gain (Phase 0) → optionally value-of-information (Phase 2)
**Status: Information gain KEPT (Phase 0). Value-of-information KEPT — GATED (Phase 2), with a
correction.**
Phase 0 baseline: pick the facet whose expected pool-size reduction is largest (equivalent to Shannon
entropy reduction; can be framed either way in the writeup — entropy framing is more rigorous-sounding,
expected-pool-reduction is simpler to explain and implement).
**Proposed Phase 2 upgrade:** rather than pool-size reduction alone, weight by expected ΔHitRate@10 and
ΔMRR, since the smallest resulting pool isn't necessarily the one with the best target rank.
**Critical correction:** ΔHitRate@10 and ΔMRR both require knowing the true target product, which the
live agent never has access to mid-session — only the offline evaluator knows it. A value-of-information
formula that silently assumes this is unbuildable as a live policy. If pursued, it must be defined
against a genuinely live-computable proxy instead (e.g., retrieval-confidence spread between top
candidates, or disagreement between BM25 and dense rankings) — never against the ground-truth target
rank directly. See D7 for where target-aware terms *do* legitimately belong (offline tuning).

### D7 — Two-phase reward: live-observable signal only, vs. offline target-aware tuning
**Status: KEPT (Phase 0 conceptually; Phase 3 for the offline half).**
A single reward formula mixing live-observable entropy reduction with target-aware terms (ΔTop10
probability, MRR proxy) is invalid as written, because the live agent doesn't have ground truth during
a session. Split explicitly:
- **Live, within a session:** only entropy/pool-size reduction and other directly observable signals
  (candidate count, retriever disagreement) can drive any within-session adaptation (D6, D11-adjacent
  bandit logic).
- **Offline, against the 200 labeled dev sessions:** target-aware terms (actual HitRate@10, MRR, MTTC
  impact) legitimately belong here, feeding either the offline strategy-tuning pass (D13) or a manual
  threshold search.
Do not conflate these into one formula — it will look correct on paper and fail at implementation time.

### D10 — Slot representation: internally open-vocabulary, externally projected onto a fixed enum
**Status: KEPT (Phase 0), constraint confirmed by research (pending final repo verification — see
Q2 in `04_OPEN_QUESTIONS.md`).**
Motivation for open-vocabulary internal slots: the Amazon catalog's `details` metadata field is a
free-form dict that varies by product type (a ring has no meaningful "size" in the shoe sense) — a
rigid, fixed internal slot schema would break on many products. Originally framed via slot-independent
dialogue state tracking (Rastogi, Hakkani-Tür, Heck, Google Research 2017).
**Constraint discovered during research:** the scored Agent API most likely only accepts one
`ask_attribute` value per turn from a **fixed enum** (roughly: category, material, color, size, style,
brand, budget, feature, use_case, other/null — confirm exact list against the real repo). So: track
whatever arbitrary constraints the conversation actually surfaces internally, but when actually asking
a clarifying question externally, project onto the nearest enum value (use `feature`/`other` as escape
hatches for anything that doesn't map cleanly).

---

## Self-evolution / adaptation layers

### D8 — Cross-session hypernetwork/LoRA personalization
**Status: CUT ENTIRELY. Do not build any version of this.**
Considered: a hypernetwork mapping a compressed user profile to LoRA weights in one forward pass
(inspired by Text-to-LoRA, Sakana AI 2025, and Profile-to-PEFT, Oct 2025), for cross-session
personalization.
**Reasons for cutting, confirmed rather than merely suspected by research:**
1. Sessions are isolated single-user interactions with no cross-session identifier — this layer would
   never be exercised by the evaluator at all.
2. Published hypernetwork checkpoints were trained/validated on benchmark tasks (math, code), not
   shopping conversations — unproven zero-shot domain transfer.
3. Injecting LoRA weights requires direct model-parameter access, ruling out a hosted API model and
   forcing local model infrastructure for no corresponding certainty of payoff.
4. The competition bans training/fine-tuning base LLMs and requires in-memory-only operation, which
   further conflicts with a per-user weight-delta approach regardless of the above.
Keep this as an explicit "considered and rejected, here's why" line in the writeup — demonstrates
scoping judgment to judges.

### D6b / D9 — Comparative critiquing ("Tinder-style" feedback)
**Status: KEPT — REFRAMED, pending API confirmation (Q1/Q3).**
Original idea: show representative example products from competing interest hypotheses, let the user
react comparatively ("B is closest, but less flashy"), update the relevant interest vector via a
Rocchio-style relevance-feedback rule (`v_new = Normalize(v_old + η₁·Enc(chosen) + η₂·Enc(refinement) −
η₃·Enc(rejected))`).
**Constraint suspected from research (needs final confirmation against the actual repo):** the scored
Agent API most likely has no click/swipe/selection event — only text turns.
**Resolution:** two layers.
- **Scored path:** comparative language arrives as ordinary message text and is parsed by the same
  NLU/state-update step as any other turn — no new API surface required. The underlying update rule
  (Rocchio-style, or a simpler constraint-based update) still applies.
- **Demo-only, optional:** an actual swipeable UI outside the scored path, purely for the demo video,
  feeding the same update function. Cosmetic only, since UI/UX is not evaluated — don't over-invest time.
**Real negative literature on the Rocchio update rule itself, worth engineering around:** dense-retrieval
pseudo-relevance-feedback research (Li, Mourad, Zhuang, Koopman & Zuccon, ACM TOIS 2023) found that
adding PRF signal "will cause query drift and lead to worse performance" on harder/noisier queries, and
recommends dropping the negative term entirely, keeping the original query at higher weight than
feedback, and using a shallow feedback set (k=3–5 items). A SIGIR 2026 user study found only ~21% of
queries benefit from PRF while ~26% degrade — the dominant lever is *suppressing* harmful updates, not
maximizing beneficial ones.
**Mitigation if built:** keep the update bounded and positive-heavy (high weight on original query, small
weight on positive feedback, near-zero or heavily damped negative term), cap feedback at k≤5, and gate
every update behind a validation check (don't apply an update that would visibly hurt candidate quality).
Prefer representing reactions as constraints in `DialogState` and re-ranking, over literally moving an
embedding, where feasible — safer and more compatible with a text-only API regardless.

### D11 — Within-session adaptive action policy (contextual bandit)
**Status: KEPT — GATED (Phase 2).**
Idea: rather than a fixed heuristic for which facet to ask about, maintain `Q(action | state)` that
adapts within a session based on observed entropy reduction per action type (color vs. use-case, etc.),
inspired by/comparable to OLIVIA (arXiv 2605.11169, 2026 — online learning via inference-time action
adaptation for LLM agents, no fine-tuning) and PURPLE (arXiv 2601.12078, ACL 2026 — contextual bandits
for retrieval-augmented LLM personalization).
**Correction made during design:** the value estimate must be conditioned on state/product category
(`Q(a | state)`, a genuine contextual bandit), not a single global score per action — material questions
are highly informative for jewelry, nearly useless for sneakers, and the reverse is true of use-case
questions. The system is not learning "color questions are bad," it's learning "given this state, color
currently has low expected information value."
**Real risk, not hypothetical:** a 10-turn session offers only ~3–6 real clarification decisions before
the cap — very little data for a bandit to converge from scratch. Mitigate by warm-starting the bandit's
prior from the offline tuning pass (D13) rather than learning cold within each session, and be honest in
any writeup that this is "lightweight inference-time adaptation," not "the agent deeply learns the
user" — that stronger claim is not defensible under 10-turn constraints and invites easy pushback from
judges.
**Mandatory gate:** ablate static Phase-0 policy vs. this adaptive version; keep only if it measurably
improves MTTC/HitRate on held-out dev sessions.

### D13 — Offline SkillOpt-style strategy optimization
**Status: KEPT — GATED (Phase 3, lower risk than D3/D11).**
Idea: rather than hand-tuning thresholds (base_threshold, decay_rate, fusion weights, facet priorities)
by intuition, run an explicit rollout → score → edit → validate loop against the 200 labeled dev
sessions and the provided deterministic evaluator, treating the strategy as a text document that gets
bounded edits, each accepted only if it strictly improves a held-out validation score. Inspired by
SkillOpt (Microsoft Research, arXiv 2605.23904, 2026; MIT-licensed code at github.com/microsoft/SkillOpt).
No model weights touched at any point — text-space optimization only, cleanly compliant with the
no-fine-tuning constraint.
**Why lower-risk than the other Phase 2/3 items:** it's mostly a formalization of something Phase 0
already does informally ("tune base_threshold and decay_rate empirically against dev sessions") — the
upgrade is rigor and reproducibility, not new capability.
**Mandatory discipline:** hold out a validation split of the 200 public sessions rather than tuning
against all of them — the 800 private sessions are what's actually judged, and overfitting to the public
set is an explicitly named common failure mode (see `06_ABLATIONS_AND_METRICS.md`).

### D12 — Decision-path compression and workflow re-orchestration
**Status: KEPT (Phase 0/1).**
Two cheap, high-value mechanisms: (a) skip the optional LLM re-ranking call when the candidate pool is
already small/unambiguous (e.g., ≤3 candidates after filtering) — direct latency/cost saving with no
quality loss; (b) let the pipeline's shape itself respond to buying-intent specificity — when intent is
very specific (tight constraints, high buying-intent score), skip the wide/diverse retrieval pass and
go straight to precise filtering, rather than always running the full pipeline uniformly. Both are cheap
to implement relative to their payoff and directly serve the MTTC / "light execution" goals.

### D14 — Combined recommend+ask in a single turn
**Status: KEPT (Phase 0), pending final confirmation (Q1).**
An early draft plan (from an external teammate) modeled turns as strictly "ask OR recommend." If the
real Agent API allows returning `ask_attribute` and `recommendations` together in one response (research
suggests likely yes, not yet independently confirmed against the actual repo), this should be corrected:
always attach the current best Top-10 when available, even on a turn that's also asking a clarifying
question, since a hit can occur on any turn and MTTC rewards early hits. **If Q1 comes back negative
(API truly forces a strict either/or), revert to the simpler either/or turn policy** — don't build
against an assumption the repo doesn't support.

---

## Process / meta decisions

### D15 — Bare-minimum-first, tiered expansion strategy
**Status: KEPT — governs the whole build plan.**
Rather than attempting the full ambitious architecture from the start, build Phase 0 (a complete, safe,
evaluator-passing system) fully before attempting anything else, and gate every subsequent addition
behind a measured ablation rather than intuition or citation strength. Directly informed by an external
teammate's build plan (see `02_BUILD_PLAN.md` for full attribution) and reinforced independently by a
formal research pass that found genuine failure-mode literature for several of the more ambitious ideas
(D3, D9 in particular) — the caution this strategy encodes was not hypothetical.

### D16 — Deep-research validation pass before finalizing architecture
**Status: COMPLETED, findings folded into this log.**
Before committing to the architecture, a formal research pass validated every major cited paper (OLIVIA,
PURPLE, SkillOpt, Tool Attention, Sekulić/ClariQ, Rastogi/DST all confirmed real with correct
dates/venues), surfaced negative/failure-mode literature not previously known (Rocchio query drift,
multi-interest K-sensitivity, RRF's occasional harm to strong dense retrievers), and extracted the actual
scoring formula and baseline numbers from the participant kit. See the original research dossier for the
full write-up (industrial-system comparisons, investment/market landscape, cross-domain technique
survey) — condensed into the relevant decisions above.
