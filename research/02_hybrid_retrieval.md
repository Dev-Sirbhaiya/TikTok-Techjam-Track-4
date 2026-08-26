# Hybrid Retrieval Architectures for In-Memory, No-Infra Shopping Copilots

Research scope: in-process/in-memory hybrid (keyword + dense + structured-filter) retrieval
suitable for a frozen 50,000-item text-only Amazon `Clothing_Shoes_and_Jewelry` catalog,
under TikTok TechJam Track 4 constraints (max 10 turns/session, no external vector DB
service, no fine-tuning, no images, no UI). Evaluated on Hit Rate@K, MRR, MTTC.

## Overview

At 50,000 items with text-only metadata, this is a **small-data problem**, not a big-data
one. Nearly every technique that exists to make vector search scale to millions/billions of
vectors (IVF, PQ, sharded ANN clusters, hosted vector DBs) is unnecessary overhead here — the
literature and benchmarks consistently show that **exact brute-force search is still fast
enough** at this scale, and even approximate libraries are only reached for at 100K+ to
millions of vectors. The dominant industry pattern for this class of problem — confirmed
across e-commerce hybrid-search writeups, RAG engineering blogs, and academic conversational
shopping papers — is a **multi-route retrieval → fusion → LLM rerank** cascade:

1. **Sparse/lexical retrieval** (BM25 or similar) over titles/descriptions/features for
   exact term matching (brand names, model numbers, sizes).
2. **Structured/metadata filtering** (inverted index or dict/dataframe filter) for hard
   constraints (category, price range, brand, size).
3. **Dense/semantic retrieval** (small sentence-embedding model + brute-force or lightweight
   ANN cosine similarity) for paraphrase/intent matching and cross-category "browsing."
4. **Fusion** of the above ranked lists, typically via Reciprocal Rank Fusion (RRF) or a
   weighted linear combination, into one candidate set (tens of items).
5. **LLM semantic reranking** over the small fused candidate set (the only stage that is
   actually expensive), which is exactly the second half of the mandated pipeline.

This matches the required "Multi-Route Retrieval → LLM Semantic Ranking" pipeline shape
almost exactly, and every component of the retrieval half can run in pure Python/NumPy/SciPy
in-process, with no server, no external service, and no training.

## Key approaches found (with citations)

### 1. In-memory dense vector search — no external service needed

- **Brute-force NumPy/SciPy cosine similarity.** Exact brute-force vector search is
  reported to work well up to a few million vectors, with the ANN world only becoming
  necessary past roughly the 5M mark; at 50K vectors with modest dimensionality (e.g.
  384-dim from a small sentence-transformer), a single matrix–vector dot product
  (`embeddings @ query_vec`) plus `np.argpartition` for top-k is a single BLAS call over a
  50,000×384 float32 matrix (~75MB) — this is comfortably sub-10ms per query on commodity
  CPU hardware. ([Research ways to speed up brute force cosine similarity](https://github.com/simonw/llm/issues/246), [Vector Search with FAISS: ANN Explained](https://pyimagesearch.com/2026/02/16/vector-search-with-faiss-approximate-nearest-neighbor-ann-explained/))
- **FAISS in local/CPU mode.** FAISS is **a library, not a hosted database or cluster** — it
  runs fully in-process with no server component, and even the official FAISS paper
  describes it as an embedded toolkit of indexing primitives, not a database system (storage/
  metadata/scaling are explicitly left to other tools). This means FAISS's `IndexFlatIP`
  (exact brute force, GPU-optional) or `IndexHNSWFlat` (approximate) **does not violate**
  the "no external vector DB clusters" constraint — it is functionally equivalent to using
  NumPy, just with a faster/more optimized kernel and a convenient ID-filtering API. Using
  FAISS locally is safe; standing up a managed/hosted FAISS-backed service (e.g. via
  Zilliz/Pinecone, which reuse FAISS internally) would not be. ([The Faiss library, arXiv:2401.08281](https://arxiv.org/abs/2401.08281), [facebookresearch/faiss](https://github.com/facebookresearch/faiss), [Is FAISS a Vector Database?](https://www.upgrad.com/blog/is-faiss-vector-database/))
- **hnswlib / usearch.** Both are lightweight, dependency-light, embedded ANN libraries
  (header-only C++ with Python bindings) built specifically for in-memory HNSW search with
  no server process. On datasets in the tens-of-thousands range (e.g. AG News, ~45K
  vectors), usearch and hnswlib post near-identical throughput (~2,200–2,400 QPS) at
  >98% recall@10 — i.e., at this scale ANN's approximate-vs-exact trade-off barely matters,
  and the main value of these libraries over brute force is faster incremental
  insertion/build and lower per-query CPU, not scale headroom you actually need. USearch
  additionally reports large speedups over FAISS specifically on **insertion/update-heavy**
  workloads at huge scale (100M+ vectors), which is irrelevant for a frozen 50K catalog.
  ([Faiss vs HNSWlib on Vector Search — Zilliz](https://zilliz.com/blog/faiss-vs-hnswlib-choosing-the-right-tool-for-vector-search), [USearch Benchmarks](https://github.com/unum-cloud/usearch/blob/main/BENCHMARKS.md), [ANN-Benchmarks](https://ann-benchmarks.com/))
- **sqlite-vec.** A dependency-free SQLite extension for embedded vector KNN with SIMD
  acceleration; explicitly positioned as a lighter, actively-maintained replacement for the
  older FAISS-based `sqlite-vss`. Reported to feel "quite snappy" up to 10K–100K documents,
  with plain zero-dependency approaches holding up to ~200K–500K documents before an upgrade
  to FAISS/hnswlib is warranted — i.e. it's comfortably inside its sweet spot for a 50K
  catalog, and is attractive if you want vectors and structured metadata filter predicates
  co-located in one embedded store (SQL `WHERE` + KNN in one query) instead of maintaining
  a separate NumPy array and a separate filter index. ([sqlite-vec v0.1.0 release notes](https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html), [Local-First RAG: Vector Search in SQLite](https://www.sitepoint.com/local-first-rag-vector-search-in-sqlite-with-hamming-distance/))
- **Takeaway:** at 50K items, the choice of ANN library is essentially irrelevant to recall
  or latency — all of them (including plain NumPy) return sub-20ms exact or near-exact
  results. The choice should instead be driven by **integration convenience**: does the
  library make it easy to do combined "hard filter + vector search" queries (FAISS ID
  selectors, sqlite-vec SQL predicates) without hand-rolling that logic.

### 2. Lightweight open embedding models for CPU inference

- **all-MiniLM-L6-v2** (sentence-transformers): 384-dim, ~22M params, the most
  cost-efficient/fastest option, well suited to limited infra/edge/CPU deployment; widely
  used as the default "fast" sentence encoder. ([Best Open-Source Embedding Models, Ranked](https://supermemory.ai/blog/best-open-source-embedding-models-benchmarked-and-ranked/))
- **BAAI/bge-small-en-v1.5**: 384-dim, ~33M params, ~0.24GB memory footprint, reported
  throughput ~467 embeddings/sec on CPU-class hardware; shows a modest but consistent
  quality edge over MiniLM (+2–4 nDCG@10 points in comparative writeups) at similar
  latency/memory cost — a good default "slightly better than MiniLM, still cheap" choice.
  ([BAAI/bge-small-en](https://huggingface.co/BAAI/bge-small-en), [Best Open-Source Embedding Models](https://supermemory.ai/blog/best-open-source-embedding-models-benchmarked-and-ranked/))
- **intfloat/e5-small-v2**: 384-dim, 33.4M params; requires the `query:` / `passage:`
  prefix convention at encode time (asymmetric encoding), which is a genuinely useful
  property for a shopping copilot (query text and product-listing text have very different
  lengths/styles) but is an implementation detail to get right. ([e5-small-v2-gguf](https://huggingface.co/ChristianAzinn/e5-small-v2-gguf), [Choosing the Best Embedding Models — Beam](https://www.beam.cloud/blog/best-embedding-models))
- **thenlper/gte-small**: 384-dim, ~34M params, comparable speed/quality tier to the above;
  frequently cited alongside MiniLM/BGE/E5-small as one of the standard "small, general
  purpose, CPU-friendly" MTEB-competitive encoders.
- **General finding on model choice:** generic off-the-shelf small embedders
  (MiniLM/BGE-small/E5-small/GTE-small) all "leave measurable relevance on the table" for
  real shopper queries — short, noisy, 2–5 word queries with typos/abbreviations — because
  none were trained specifically on the query↔product-title asymmetry; they were trained on
  general STS/retrieval mixtures. Since **fine-tuning foundation models is disallowed** here,
  this gap must be closed by (a) light prompt/query preprocessing (e.g., query expansion,
  synonym normalization) and (b) leaning more heavily on BM25 for exact-token matches and
  on the LLM reranker for final quality — not by trying to train a better encoder.
  ([README — ecommerce-product-search-embeddings](https://huggingface.co/albertobarnabo/ecommerce-product-search-embeddings/blob/main/README.md), [Best Open-Source Embedding Models, Ranked](https://supermemory.ai/blog/best-open-source-embedding-models-benchmarked-and-ranked/))
- **Latency budget implication:** encoding a query with any of these 384-dim, ~20–35M
  param models on CPU is single-digit milliseconds; encoding all 50K catalog items is a
  one-time offline cost (minutes, done once since the catalog is frozen/read-only), not a
  per-turn cost. Per-turn cost is: encode 1 query + one matmul against a cached 50K×384
  matrix — trivially inside a 10-turn interactive budget.

### 3. Keyword (BM25) retrieval and fusion techniques

- **rank_bm25** — the ubiquitous pure-Python BM25 implementation; simple API, but computes
  scores at query time with plain Python loops, which is measurably slow at scale.
- **bm25s** — a NumPy/SciPy/Numba-accelerated BM25 implementation that **precomputes and
  caches BM25 term scores into sparse matrices at indexing time**, reported to be up to
  ~500x faster than rank_bm25 and faster than even Elasticsearch in its own benchmarks, while
  remaining a pure local Python library (no server, no JVM). At 50K documents this is
  effectively instantaneous querying (sub-millisecond), and it removes any concern about
  keyword search being a bottleneck. This is the clear default choice for the sparse leg of
  retrieval. ([xhluca/bm25s](https://github.com/xhluca/bm25s), [BM25S paper, arXiv:2407.03618](https://arxiv.org/pdf/2407.03618), [BM25 for Python — HF blog](https://huggingface.co/blog/xhluca/bm25s))
- **Rank fusion — Reciprocal Rank Fusion (RRF).** The standard, near-universal solution for
  combining a sparse ranked list and a dense ranked list: `score(d) = Σ 1/(k + rank(d))`
  across each list the document appears in (k≈60 is the conventional constant). RRF is
  preferred over naively blending raw scores because BM25 scores are unbounded/corpus-scale
  dependent while cosine similarity is bounded in [-1,1] — the two are not on comparable
  scales, so a weighted linear combination of *raw scores* requires careful normalization
  (e.g. min-max or z-score per query) to avoid one signal dominating, whereas RRF sidesteps
  this entirely by fusing on rank position rather than score magnitude. Weighted linear
  combination (after normalization) is a reasonable alternative when you want to tune the
  balance between lexical and semantic signal per-track (e.g., weight BM25 higher for
  "Buying" intent, weight dense higher for "Browsing" intent) — this tunable weighting is
  exactly the kind of "light scoring tuning" the constraints permit. ([Reciprocal Rank Fusion explained](https://blog.serghei.pl/posts/reciprocal-rank-fusion-explained/), [Hybrid Search for RAG — Denser](https://denser.ai/blog/hybrid-search-for-rag/))
- **Cascade / two-stage retrieval.** The broader pattern both fields (search and
  recommendation) converge on: a cheap, high-recall **candidate generation** stage (BM25 +
  dense retrieval + metadata filter, each individually fast and each producing e.g. top-100–
  500 candidates) followed by a precise, more expensive **reranking** stage over the much
  smaller fused/deduplicated candidate set. This directly matches the mandated pipeline:
  multi-route retrieval is the candidate-generation stage; the LLM semantic ranker is the
  reranking stage. ([Two-Stage Retrieval Architecture](https://www.emergentmind.com/topics/two-stage-retrieval-architecture), [On Ranking Consistency of Pre-ranking Stage, arXiv:2205.01289](https://arxiv.org/pdf/2205.01289))

### 4. Hard-constraint locking (Buying track) over structured metadata

- The consistent pattern for this at small-to-medium catalog scale is **not** a database
  index at all but simple **in-memory columnar/dict structures**:
  - A **dict-based inverted index** per categorical field (brand → set of product IDs,
    category → set of product IDs, size → set of product IDs) gives O(1) lookup and O(min
    set size) intersection for AND-combined filters (brand=X AND category=Y AND
    price∈[a,b]) — trivial to build once at load time for 50K items and trivial to
    intersect per turn.
  - **Pandas or Polars** boolean-mask filtering (`df[(df.brand==X) & (df.price<=Y)]`) is the
    simpler-to-write equivalent; Polars' columnar layout and multi-core vectorized
    filtering give it a speed/memory edge over pandas at any scale, though at 50K rows both
    are fast enough that the choice is really about code ergonomics rather than
    performance. ([Coming from Pandas — Polars docs](https://docs.pola.rs/user-guide/migration/pandas/), [Python Pandas to Polars: Data Filtering](https://towardsdatascience.com/python-pandas-to-polars-data-filtering-a67ccb70a8b3/))
  - A concrete precedent: an arXiv-documented e-commerce semantic search system uses a
    fine-tuned small seq2seq model (Flan-T5-small) to parse the natural-language query into
    a structured JSON filter (price range, rating, subcategory), then applies that filter
    via **FAISS's ID-selector mechanism** to restrict the vector search to only the
    constraint-compliant subset before similarity scoring — i.e., filter-then-search rather
    than search-then-filter, which guarantees hard constraints are never violated by the
    ranking stage. (Note: this pattern used a fine-tuned parser; in our no-fine-tuning
    setting the equivalent role is filled by LLM-based slot/filter extraction via prompting.)
    ([LLM-Based Semantic Search for Conversational Queries in E-commerce, arXiv:2601.16492](https://arxiv.org/html/2601.16492v1))
  - The general principle across all of these: hard constraints should be applied as a
    **pre-filter** (shrinking the candidate universe before any similarity/ranking math),
    not as a post-hoc filter on top-k results — the latter risks returning fewer than K
    results or silently dropping constraint compliance if top-k is computed before
    filtering.

### 5. Diverse cross-category matching (Browsing track)

- **Maximal Marginal Relevance (MMR)** is the standard, well-established technique
  (Carbonell & Goldstein, 1998) for diversifying a ranked list: iteratively select the item
  maximizing `λ·relevance(d) − (1−λ)·max_similarity(d, already_selected)`, trading off
  between staying relevant to the query and avoiding redundancy with items already chosen.
  This is a pure post-processing step over an already-computed dense similarity space (no
  extra retrieval cost) and is directly implementable in NumPy over the same embedding
  matrix used for dense retrieval. ([Balancing Relevance and Diversity with MMR — Qdrant](https://qdrant.tech/blog/mmr-diversity-aware-reranking/), [MMR — Mixpeek docs](https://mixpeek.com/docs/retrieval/stages/mmr))
- **Sampled MMR (SMMR)**, a 2025 SIGIR paper, notes that greedy deterministic MMR can be
  rigid and introduces randomized sampling into the selection step for better
  relevance/diversity trade-offs with a logarithmic speedup at scale — likely overkill for
  a 50-item candidate list at 50K catalog scale, but worth knowing as the "next step up"
  if plain MMR under-diversifies. ([SMMR, SIGIR 2025](https://dl.acm.org/doi/10.1145/3726302.3730250))
- **Category-balanced sampling** — a simpler, cheaper alternative/complement to MMR: bucket
  the top-N dense-retrieval candidates by category/subcategory metadata and round-robin
  or proportionally sample across buckets before handing the set to the LLM reranker. This
  is nearly free to compute (just a groupby over metadata already indexed for the filter
  track) and guarantees category diversity in a way that embedding-space MMR only
  approximates.
- Practically, the Browsing track = dense retrieval with a **relaxed/absent** structured
  filter, top-N pulled generously (e.g. 100–200) from the vector index, then MMR or
  category-balanced resampling down to the candidate set size handed to the LLM reranker.

### 6. Prior art: hybrid keyword+vector e-commerce/conversational search repos

- **xhluca/bm25s** — reference implementation for fast local BM25, frequently paired with
  dense retrieval in hybrid setups. ([GitHub](https://github.com/xhluca/bm25s))
- **querix-semantic-search** — multi-tenant hybrid search stack combining pgvector, BM25,
  LLM query planning, and RRF fusion, explicitly following the "planner prompt → hybrid
  retrieval → RRF → intent shaping" shape that maps closely onto this project's pipeline
  (though it uses Postgres/pgvector rather than pure in-memory structures — the RRF/planner
  pattern is the transferable part, not the storage layer). ([GitHub](https://github.com/Vijayaadhithan/querix-semantic-search))
- **Contextual-RAG-System-with-Hybrid-Search-and-Reranking** — demonstrates the
  "vector + BM25 ensemble retriever → cross-encoder rerank" cascade pattern generically
  (not e-commerce-specific, but architecturally identical to what's needed here).
  ([GitHub](https://github.com/chatterjeesaurabh/Contextual-RAG-System-with-Hybrid-Search-and-Reranking))
- **LLM-Based Semantic Search for Conversational Queries in E-commerce** (arXiv:2601.16492) —
  closest academic analogue found: fine-tuned MiniLM dense embeddings + FAISS IVF-Flat index
  + LLM/T5-parsed structured filters applied via FAISS ID-selector pre-filtering, evaluated
  on a ~22K-item Amazon-like subset. Notably this paper **does not use BM25/hybrid fusion or
  an LLM reranking stage** — it stops at filtered dense retrieval — so our mandated
  pipeline (which adds sparse retrieval, RRF fusion, and LLM reranking) should meaningfully
  outperform it on both precision and coverage. ([arXiv:2601.16492](https://arxiv.org/html/2601.16492v1))
- **PSCon: Product Search Through Conversations** (arXiv:2502.13881) and **Shopping
  Reasoning Bench** (arXiv:2606.12608) confirm the field is actively building multi-turn
  conversational shopping benchmarks that explicitly separate exploratory/browsing turns
  from constraint-heavy goal-directed turns — validating the Buying/Browsing track split
  mandated for this project as a recognized, real distinction in the literature rather than
  an arbitrary product decision. ([PSCon](https://arxiv.org/pdf/2502.13881), [Shopping Reasoning Bench](https://arxiv.org/html/2606.12608))

### 7. LLM reranking cost/latency within a 10-turn budget

- **Listwise LLM reranking is materially expensive relative to retrieval.** Benchmarks
  report listwise LLM reranking adding roughly 4-6 seconds of latency versus a cross-encoder
  reranker, and up to ~35x the latency / ~9x the cost of lighter rerankers for modest
  (~0.04) NDCG gains — meaning the LLM rerank stage, not the retrieval stage, is the
  binding latency/cost constraint on MTTC, and the retrieval stage's job is to hand the LLM
  as small and as high-recall a candidate set as possible. ([Should You Use an LLM as a Reranker? — ZeroEntropy](https://zeroentropy.dev/articles/llm-as-reranker-guide/))
- **Candidate set sizing.** Industry guidance converges on keeping the LLM-facing candidate
  list to roughly 10–75 items: cost/latency scale roughly linearly with list size k, with
  diminishing relevance returns past ~100 candidates, and a commonly cited practical sweet
  spot of 50–75 documents for a cross-encoder pre-filter feeding an LLM listwise pass over
  only the top ~10. This directly informs pipeline sizing: retrieve generously (top ~100-300
  per route, cheap), fuse/dedupe down to ~30-75, then let the LLM do final semantic ranking
  over that set, not the full candidate pool. ([Ultimate Guide to Choosing a Reranking Model — ZeroEntropy](https://zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025/), [Listwise reranking — ZeroEntropy](https://zeroentropy.dev/concepts/listwise-reranking/))

## Relevance to our constraints

| Constraint | Implication |
|---|---|
| **50,000 items, in-memory only, no external vector DB clusters** | Well inside the "brute-force/embedded-library-is-fine" regime documented above. Any of NumPy/SciPy, FAISS-local, hnswlib, usearch, or sqlite-vec will return exact or near-exact top-k in single-digit-to-low-double-digit milliseconds. There is no scale-driven reason to need a hosted/clustered vector DB, and using one would violate the constraint anyway. FAISS run locally is explicitly *not* an "external vector DB cluster" per its own documentation/paper — it's an embedded library — so it is a safe choice if its API conveniences (ID-filtering, index save/load) are wanted. |
| **No training/fine-tuning of foundation models** | Rules out fine-tuning an embedder on the catalog (as the closest prior-art paper did) or fine-tuning a query→filter parser. The gap this leaves (generic embedders underperforming on short/noisy shopper queries) must be compensated by: (a) BM25 catching exact lexical matches embeddings miss, (b) prompt-level query rewriting/normalization before embedding, (c) leaning on the LLM reranker — all "light prompt/scoring tuning," which is explicitly permitted. |
| **Text-only, no images** | All retrieval routes above (BM25, small sentence-transformer embeddings, metadata filters) are text/structured-field native; no multimodal considerations needed. |
| **Max 10 turns/session, MTTC scored** | The expensive part of the pipeline is the LLM reranker, not retrieval. Budget: keep per-route candidate generation cheap and generous (BM25 + dense, each <20ms at 50K scale), fuse via RRF/weighted combination (near-free), then cap the LLM-facing candidate set at roughly 30-75 items to bound LLM cost/latency per turn — this is the dominant lever for hitting a good MTTC, not the choice of ANN library. |
| **Buying vs. Browsing track split** | Directly supported: Buying = pre-filter (dict/inverted-index or pandas/polars mask over brand/size/price/category) intersected with BM25+dense hybrid retrieval restricted to the filtered subset, weighted toward lexical/BM25 signal for exactness. Browsing = dense retrieval with relaxed/no hard filter, generous top-N, then MMR or category-balanced resampling for cross-category diversity before LLM reranking. |

## Recommended approach(es), ranked

1. **Recommended default stack** (simplest to build, fully sufficient at 50K scale, zero
   external services):
   - **Sparse leg:** `bm25s` over concatenated title+description+features text. Chosen over
     `rank_bm25` purely for its precomputed-scoring speed (irrelevant for correctness at 50K,
     but removes any doubt about per-turn latency, and its API is a near drop-in).
   - **Dense leg:** one small `sentence-transformers` encoder — **BAAI/bge-small-en-v1.5**
     as the primary pick (best quality/latency trade-off among the small models found;
     384-dim, ~33M params, sub-ms-scale CPU encode per query) with **all-MiniLM-L6-v2** as a
     fallback/ablation if inference budget is tighter than expected. Encode the full 50K
     catalog once offline into a cached float32 NumPy matrix (~75MB at 384-dim); per-turn
     cost is one query encode + one matrix-vector dot product + `np.argpartition` top-k —
     no ANN library is *required* to hit latency targets, though FAISS `IndexFlatIP` or
     `hnswlib` can be dropped in later for convenience (ID-filtering, persistence) without
     changing the architecture.
   - **Structured filter leg:** build per-field dict-based inverted indexes (brand, category,
     size, price-bucket) at load time from the frozen catalog; combine via set intersection
     for the Buying track's hard-constraint pre-filter. Use this same filter to restrict
     the row-index range considered in the dense/sparse legs (filter-then-search, not
     search-then-filter).
   - **Fusion:** Reciprocal Rank Fusion (RRF, k=60) as the default combiner between BM25 and
     dense rankings; expose the BM25/dense mixing behavior as a simple weighting knob (e.g.
     boost BM25 weight for Buying-track queries, boost dense weight for Browsing-track
     queries) as the permitted "light scoring tuning."
   - **Diversification (Browsing track only):** MMR over the same cached embedding matrix,
     or the cheaper category-balanced round-robin resampling, applied to the top ~100-200
     dense candidates before capping the set handed downstream.
   - **Candidate cap into the LLM reranker:** ~30–75 fused/deduplicated candidates, informed
     by reranking-cost-vs-quality literature, to keep per-turn LLM latency/cost bounded
     across up to 10 turns.

2. **If ID-filtered vector search API convenience is wanted (optional upgrade):**
   swap the plain-NumPy dense leg for **FAISS `IndexFlatIP`** (exact, in-process, GPU-
   optional) using its native ID-selector to combine hard filtering with similarity search
   in one call. This is a drop-in replacement, not an architecture change, and remains
   fully compliant with the "no external vector DB clusters" constraint since FAISS is a
   local library, not a hosted service.

3. **If co-locating structured filters and vectors in one queryable store is preferred:**
   **sqlite-vec** as an alternative to hand-rolled dict indexes + NumPy arrays — lets hard
   constraints and KNN search be expressed as a single SQL query. Reasonable choice for
   code simplicity; not needed for performance at this scale.

4. **Not recommended:** hnswlib/usearch HNSW indexes, IVF/PQ-quantized FAISS indexes, or any
   ANN library chosen specifically "for scale" — at 50K items these solve a problem (recall
   loss / latency at millions-of-vectors scale) that doesn't exist here, and add index-build
   complexity (tuning `ef_construction`/`M`, approximate-recall validation) for no measurable
   benefit over exact brute force.

## Dos

- Do treat the dense retrieval leg as "encode 50K items once, cache the matrix, matmul per
  turn" — this is fast enough on its own; don't reach for ANN infrastructure by default.
- Do use `bm25s` (or equivalent precomputed-scoring BM25) rather than naive `rank_bm25` if
  BM25 will be called many times across a session/evaluation run — it removes any latency
  risk for free.
- Do apply hard constraints (Buying track) as a **pre-filter** that shrinks the candidate
  universe before similarity scoring, using dict/inverted-index or pandas/Polars boolean
  masks — never as a post-filter on an already-computed top-k list.
- Do use Reciprocal Rank Fusion as the default way to combine BM25 and dense rankings; only
  move to normalized weighted-score combination if RRF's rank-based blending proves too
  coarse and score-scale normalization (min-max/z-score per query) can be validated.
- Do cap the number of candidates passed into the LLM reranker (roughly 30-75) — this is the
  single biggest lever on MTTC and cost, far more than any retrieval-side optimization.
- Do use MMR or category-balanced resampling for the Browsing track's diversity requirement;
  both are cheap post-processing steps over signal you've already computed.
- Do consider FAISS's local `IndexFlatIP` + ID-selector, or `sqlite-vec`, purely for API
  convenience (combined filter+search, persistence) if hand-rolled NumPy/dict indexing gets
  unwieldy — both remain in-process and constraint-compliant.
- Do compensate for generic (non-fine-tuned) embedding models' weakness on short/noisy
  shopper queries with query-side prompt normalization/expansion and by weighting BM25 more
  heavily for exact-match-sensitive (Buying) queries.

## Don'ts

- Don't reach for a hosted/managed vector database (Pinecone, Milvus, Weaviate Cloud,
  Zilliz Cloud, etc.) — explicitly disallowed, and unnecessary at 50K items regardless.
- Don't assume FAISS itself is disallowed — it's a library, not a "vector DB cluster"; using
  it locally in-process is fine, only a hosted/clustered deployment would violate the
  constraint.
- Don't fine-tune the embedding model on the catalog, even though prior art (e.g.
  arXiv:2601.16492) does exactly this and gets good results from it — that path is closed
  off by the no-training constraint; compensate via hybrid retrieval and prompting instead.
- Don't build/tune an HNSW or IVF/PQ index "just in case it's needed for scale" — at 50K
  items this adds complexity (approximate recall validation, parameter tuning) without a
  latency or memory problem to solve.
- Don't combine raw BM25 scores and raw cosine-similarity scores via naive averaging without
  normalization — their scales are incompatible and one signal will dominate arbitrarily;
  use RRF or explicitly normalize first.
- Don't apply hard constraints (Buying track) after computing similarity top-k — you risk
  returning fewer than K compliant results or silently leaking non-compliant items; filter
  first, then rank within the filtered set.
- Don't send large candidate sets (hundreds of items) into the LLM reranker — cost and
  latency scale roughly linearly with list size for comparatively little relevance gain
  past ~100 items, and this is the part of the pipeline most likely to blow the 10-turn
  MTTC budget.

## References

- [The Faiss library (arXiv:2401.08281)](https://arxiv.org/abs/2401.08281)
- [facebookresearch/faiss (GitHub)](https://github.com/facebookresearch/faiss)
- [Is FAISS Vector Database? Meaning and Use Explained](https://www.upgrad.com/blog/is-faiss-vector-database/)
- [Faiss vs HNSWlib on Vector Search — Zilliz blog](https://zilliz.com/blog/faiss-vs-hnswlib-choosing-the-right-tool-for-vector-search)
- [USearch Benchmarks (unum-cloud/usearch)](https://github.com/unum-cloud/usearch/blob/main/BENCHMARKS.md)
- [ANN-Benchmarks](https://ann-benchmarks.com/)
- [Introducing sqlite-vec v0.1.0](https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html)
- [Local-First RAG: Vector Search in SQLite with Hamming Distance](https://www.sitepoint.com/local-first-rag-vector-search-in-sqlite-with-hamming-distance/)
- [Research ways to speed up brute force cosine similarity (simonw/llm#246)](https://github.com/simonw/llm/issues/246)
- [Vector Search with FAISS: ANN Explained — PyImageSearch](https://pyimagesearch.com/2026/02/16/vector-search-with-faiss-approximate-nearest-neighbor-ann-explained/)
- [xhluca/bm25s (GitHub)](https://github.com/xhluca/bm25s)
- [BM25S: Orders of magnitude faster lexical search (arXiv:2407.03618)](https://arxiv.org/pdf/2407.03618)
- [BM25 for Python — Hugging Face blog](https://huggingface.co/blog/xhluca/bm25s)
- [Reciprocal Rank Fusion: the one-line algorithm behind hybrid search](https://blog.serghei.pl/posts/reciprocal-rank-fusion-explained/)
- [Hybrid Search for RAG: Combining BM25 and Dense Vector Search — Denser](https://denser.ai/blog/hybrid-search-for-rag/)
- [Two-Stage Retrieval Architecture — Emergent Mind](https://www.emergentmind.com/topics/two-stage-retrieval-architecture)
- [On Ranking Consistency of Pre-ranking Stage (arXiv:2205.01289)](https://arxiv.org/pdf/2205.01289)
- [Best Open-Source Embedding Models, Ranked — Supermemory](https://supermemory.ai/blog/best-open-source-embedding-models-benchmarked-and-ranked/)
- [BAAI/bge-small-en (Hugging Face)](https://huggingface.co/BAAI/bge-small-en)
- [BAAI/bge-small-en-v1.5 (Hugging Face)](https://huggingface.co/BAAI/bge-small-en-v1.5)
- [Choosing the Best Embedding Models for RAG — Beam](https://www.beam.cloud/blog/best-embedding-models)
- [ChristianAzinn/e5-small-v2-gguf (Hugging Face)](https://huggingface.co/ChristianAzinn/e5-small-v2-gguf)
- [README — ecommerce-product-search-embeddings (Hugging Face)](https://huggingface.co/albertobarnabo/ecommerce-product-search-embeddings/blob/main/README.md)
- [Balancing Relevance and Diversity with MMR — Qdrant](https://qdrant.tech/blog/mmr-diversity-aware-reranking/)
- [MMR (Maximal Marginal Relevance) — Mixpeek docs](https://mixpeek.com/docs/retrieval/stages/mmr)
- [SMMR: Sampling-Based MMR Reranking (SIGIR 2025)](https://dl.acm.org/doi/10.1145/3726302.3730250)
- [Coming from Pandas — Polars user guide](https://docs.pola.rs/user-guide/migration/pandas/)
- [Python Pandas to Polars: Data Filtering — Towards Data Science](https://towardsdatascience.com/python-pandas-to-polars-data-filtering-a67ccb70a8b3/)
- [querix-semantic-search (GitHub)](https://github.com/Vijayaadhithan/querix-semantic-search)
- [Contextual-RAG-System-with-Hybrid-Search-and-Reranking (GitHub)](https://github.com/chatterjeesaurabh/Contextual-RAG-System-with-Hybrid-Search-and-Reranking)
- [LLM-Based Semantic Search for Conversational Queries in E-commerce (arXiv:2601.16492)](https://arxiv.org/html/2601.16492v1)
- [PSCon: Product Search Through Conversations (arXiv:2502.13881)](https://arxiv.org/pdf/2502.13881)
- [Shopping Reasoning Bench (arXiv:2606.12608)](https://arxiv.org/html/2606.12608)
- [Should You Use an LLM as a Reranker? — ZeroEntropy](https://zeroentropy.dev/articles/llm-as-reranker-guide/)
- [Ultimate Guide to Choosing the Best Reranking Model in 2026 — ZeroEntropy](https://zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025/)
- [Listwise reranking — ZeroEntropy concepts](https://zeroentropy.dev/concepts/listwise-reranking/)
