# 06 — Future / Risky Ideas (Ideation Backlog)

Dump ground for anything speculative: risky architecture bets, "what if we tried", stretch goals,
ideas that could blow up the timeline if pursued too early. Nothing here is approved. Promote an
idea into `01_architecture.md` (with a matching `02_design_decisions.md` entry) only once it's
actually been decided — don't let half-approved ideas leak into the live design.

Format per entry:
```
### <idea>
- Logged: YYYY-MM-DD
- Risk: <what could go wrong / why it's not in the main line yet>
- Upside: <why it's worth keeping around>
- Status: idea | evaluating | promoted (→ DD-NNN) | rejected (why)
```

---

### Use the evaluator-provided `user_profile` field
- Logged: 2026-08-30
- Risk: `preference_tags`/`rating_style`/`purchase_frequency` are synthetic/heuristic, not verified
  ground truth about the actual target item — could bias toward a wrong prior if over-weighted.
- Upside: free, per-session, in-domain signal available from turn 0 (before any dialog), completely
  unused since Phase 0 (`agent.py`'s `reset()` explicitly deferred it as "Phase 1+ personalization"
  and no later phase revisited it). Could seed the preference vector or bias facet-question order
  before any real signal has accumulated.
- Status: idea — found while answering a user question, not yet ablated. Awaiting decision on
  whether to pursue.

### BM25F (field-weighted BM25: title/brand/category weighted above description/bullets)
- Logged: 2026-08-30 (external research, prompted by a user question about SOTA techniques)
- Risk: low — training-free, a formula change to the existing hand-rolled BM25 leg.
- Upside: commonly cited as one of the single highest-value, lowest-effort levers in e-commerce
  search; the research agent ranked it #1 by effort-to-impact of everything surveyed.
- Status: idea — not yet ablated. Awaiting decision on whether to pursue.

### RRF per-source weight tuning (beyond the existing METADATA_RRF_WEIGHT knob)
- Logged: 2026-08-30 (external research)
- Risk: low — same overfitting risk any threshold sweep has; already-established split discipline
  covers it.
- Upside: cheap, free lever; research agent ranked it #2 by effort-to-impact.
- Status: idea — `METADATA_RRF_WEIGHT` itself was already ablated and declined (contradicted on
  validation); a more general per-source (not just metadata) weight search hasn't been tried.

### Cross-encoder ensembling (2 pretrained rerankers, averaged scores)
- Logged: 2026-08-30 (external research) — directly relevant given the post-fix diagnostic showing
  buying's remaining gap is now a ranking problem (30.0% in-pool-but-not-top10), not recall.
- Risk: low — no training involved, roughly doubles rerank-stage latency for the candidate set.
- Upside: well-established variance reduction; research agent ranked it #3, and the post-fix
  diagnostic makes ranking-side improvements the more relevant lever than further retrieval work.
- Status: idea — not yet ablated. Awaiting decision on whether to pursue.

### Offline doc2query-T5 document expansion (index-time only, fits the frozen catalog)
- Logged: 2026-08-30 (external research)
- Risk: medium — one-time inference pass over 50k items plus a BM25 reindex; `castorini/doct5query`
  is a pretrained, off-the-shelf checkpoint (no training by us).
- Upside: research agent's highest-value medium-effort item — directly attacks BM25's known
  vocabulary-mismatch weakness (customers word things differently than catalog copy), and a frozen
  catalog is exactly the case this technique suits best (one-time cost, no per-query overhead).
- Status: idea — not yet ablated. Awaiting decision on whether to pursue.

### ColBERT-style late-interaction retrieval (`colbert-ir/colbertv2.0`, pretrained)
- Logged: 2026-08-30 (external research, prompted by a user question about MIND/ComiRec-style
  multi-vector approaches — this is a different idea: multi-vector *retrieval*, not multi-*interest*
  user modeling, which was already tried via `phase2/multi_interest.py` and cut, see
  `wiki/03_design_log.md`'s 2026-08-30 entries).
- Risk: high integration cost — new per-token embedding pipeline, materially more memory (32-128
  tokens/doc × 128 dims vs. one 384-dim vector today), a new fusion signal to tune.
- Upside: genuine, well-cited retrieval technique; a real pretrained checkpoint is available and
  would be rules-compliant (no training required).
- Status: **deliberately deferred, not declined** — the research agent's own read is that its main
  advantage (fine-grained token matching) substantially overlaps with what the existing cross-
  encoder rerank stage already provides via full cross-attention, for the highest integration cost
  of anything surveyed. Worth revisiting only if cross-encoder-side improvements (ensembling, etc.)
  hit their own ceiling first.

### SPLADE-style learned sparse retrieval (`naver/splade-v3`, pretrained)
- Logged: 2026-08-30 (external research)
- Risk: medium-high — needs its own sparse-vector inverted-index structure (different from the
  existing term-frequency BM25), trained by Naver on MS MARCO (not our domain) so generalization to
  apparel/jewelry queries is unproven; becomes a 4th fusion signal on top of an already-strong
  3-signal pipeline.
- Upside: legitimately pretrained/off-the-shelf, competitive with BM25/dense on zero-shot benchmarks
  in the literature.
- Status: idea, lower priority than the above — research agent's own read is that marginal value
  over the existing BM25+dense+metadata combination is the weakest part of the case for it.

### ANN indexing (HNSW-style) for dense retrieval
- Logged: 2026-08-30 (external research, direct user question — answered, not adopted)
- Status: **declined for now, not a live idea.** Research confirmed the brute-force/ANN crossover is
  commonly cited around 100K-1M vectors; the catalog is 50K, 2-20x below that. Would add
  approximate-recall risk for no measurable latency benefit at this scale. Revisit only if the
  catalog size assumption ever changes.
