"""Catalog loading, gazetteer construction, and the CatalogIndex used by retrieval.py.

Ground truth this is built against: wiki/09_simulator_mechanics.md. In particular:
- `details` has zero keys common across items even within one leaf category (verified by direct
  sampling) -- the gazetteer scans values generically, never assumes a fixed schema.
- Some `categories` entries are actually store/brand names that leaked into the taxonomy (e.g.
  "Westlake") -- the category-frequency-based filtering in build_gazetteer() is the defense.
- Category strings are comma-split before use, exactly mirroring the evaluator's own
  coarse_category() (see _normalized_category_parts()) -- getting this wrong desyncs our category
  index from what's actually disclosed to the customer (a real bug caught by codex review).
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

MATERIAL_WORDS = {
    "cotton", "polyester", "nylon", "leather", "wool", "spandex", "silk", "rayon",
    "fabric", "denim", "linen", "suede", "canvas", "velvet", "cashmere", "fleece",
}
COLOR_WORDS = {
    "black", "white", "blue", "red", "pink", "green", "brown", "gray", "grey",
    "purple", "yellow", "orange", "navy", "beige", "gold", "silver", "tan",
    "maroon", "teal", "ivory", "burgundy", "khaki", "coral", "lavender",
}
STYLE_WORDS = {
    "casual", "formal", "crew", "v-neck", "slim", "regular", "relaxed", "fitted",
    "oversized", "sleeveless", "long-sleeve", "short-sleeve", "collared",
}
USE_CASE_WORDS = {
    "hiking", "running", "gym", "winter", "outdoor", "work", "travel", "yoga",
    "training", "workout", "athletic", "formal wear", "everyday",
}
PRICE_BUCKETS = [(15, "under $15"), (25, "$15-25"), (40, "$25-40"), (60, "$40-60"),
                 (100, "$60-100"), (float("inf"), "$100+")]
PRICE_RE = re.compile(r"\$?\s?(\d+(?:\.\d+)?)")
_MATERIAL_RE = re.compile(r"\b(" + "|".join(sorted(MATERIAL_WORDS)) + r")\b")
_COLOR_RE = re.compile(r"\b(" + "|".join(sorted(COLOR_WORDS)) + r")\b")
_STYLE_RE = re.compile(r"\b(" + "|".join(sorted(STYLE_WORDS)) + r")\b")
_USE_CASE_RE = re.compile(r"\b(" + "|".join(sorted(USE_CASE_WORDS)) + r")\b")


def price_bucket(price: float) -> str:
    """Buckets price into a small, fixed number of bands -- see the codex-review fix on
    _attributes_for() below for why (raw per-item price has near-100% cardinality, which unfairly
    dominates unnormalized entropy comparisons against low-cardinality facets like color)."""
    for ceiling, label in PRICE_BUCKETS:
        if price < ceiling:
            return label
    return PRICE_BUCKETS[-1][1]
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "i", "in", "is", "it", "me", "my", "of", "on", "or", "please", "some",
    "that", "the", "this", "to", "want", "with", "would", "you", "looking",
}


def load_catalog(path: str | Path) -> dict[str, dict]:
    products: dict[str, dict] = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            p = json.loads(line)
            products[str(p["parent_asin"])] = p
    return products


def _flatten(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [f"{k} {v}" for k, v in value.items() if v not in (None, "", [])]
    if isinstance(value, list):
        return [str(v) for v in value if v not in (None, "")]
    if value in (None, ""):
        return []
    return [str(value)]


def searchable_text(p: dict) -> str:
    parts: list[str] = []
    for field in ("title", "features", "description", "categories", "store", "details"):
        parts.extend(_flatten(p.get(field)))
    return " ".join(parts)


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if len(t) > 1 and t not in STOPWORDS]


_EXCLUDED_CATEGORY_LOWER = {"clothing", "clothing shoes & jewelry", "clothing, shoes & jewelry"}


def _normalized_category_parts(categories: list[str]) -> list[str]:
    """Mirrors the evaluator's own coarse_category() EXACTLY (verified against
    evaluator/local_evaluator.py) -- each category STRING is itself split on commas before
    filtering, not treated as one atomic label (e.g. "Tops, Tees & Blouses" splits into "Tops"
    and "Tees & Blouses" as two separate parts). CORRECTED per codex review: the original version
    of this module treated each `categories` entry as atomic (no comma-splitting), which silently
    desynced our category index from what the evaluator actually discloses to the customer --
    products could be indexed under a raw multi-word label containing a comma while the disclosed
    text never contains one, causing the true target to be excluded from Buying-track hard filters
    while an unrelated product with a coincidentally-matching shorter label got included."""
    cleaned: list[str] = []
    for value in categories or []:
        for part in str(value).split(","):
            part = part.strip()
            if part and part.lower() not in _EXCLUDED_CATEGORY_LOWER:
                cleaned.append(part)
    return cleaned


def coarse_category(categories: list[str]) -> str:
    """Mirrors the evaluator's own coarse_category(): last two non-generic category parts,
    space-joined. See _normalized_category_parts() for the comma-splitting this depends on."""
    parts = _normalized_category_parts(categories)
    return " ".join(parts[-2:]) if parts else "clothing item"


def build_gazetteer(products: dict[str, dict]) -> dict[str, set]:
    """Scan the full catalog once to build vocabularies. Categories are frequency-filtered (not just
    excluded by a hardcoded blocklist) since store/brand names occasionally leak into the taxonomy."""
    brands: set[str] = set()
    sizes: set[str] = set()
    materials: set[str] = set()
    colors: set[str] = set()
    category_counts: Counter[str] = Counter()

    for p in products.values():
        details = p.get("details") if isinstance(p.get("details"), dict) else {}
        for key, val in details.items():
            lk = key.lower()
            if "brand" in lk and val:
                brands.add(str(val).strip())
            if "size" in lk and val:
                sizes.add(str(val).strip()[:24])
        store = p.get("store")
        if store:
            brands.add(str(store).strip())
        text = searchable_text(p).lower()
        materials.update(_MATERIAL_RE.findall(text))
        colors.update(_COLOR_RE.findall(text))
        for part in _normalized_category_parts(p.get("categories") or []):
            category_counts[part] += 1

    # A "category" that appears on only 1-2 products in a 50k catalog is far more likely to be a
    # mislabeled store/brand name than a genuine taxonomy node -- drop the long tail.
    categories = {c for c, n in category_counts.items() if n >= 5}
    brands = {b for b in brands if len(b) <= 40}
    # "materials"/"colors" are deliberately tuples, not sets: nlu.py's _gazetteer_fallback_extract
    # and rejection_memory.py's detect_rejection_signal both iterate them with "first regex match
    # wins, then stop" semantics. A plain set's iteration order is hash-randomized per Python
    # process (PYTHONHASHSEED) -- self-caught during Phase 3.1's tuning sweep, where two runs of the
    # *identical* baseline config against the *identical* training split produced different
    # TechnicalScores, traced to this: a message mentioning two gazetteer colors/materials (e.g. "no
    # gold or silver") would silently extract a different one depending on which Python process
    # happened to iterate the set which way, cascading into different retrieval/ranking/turn
    # decisions for the rest of that session. Sorted alphabetically -- both vocabularies are flat,
    # equally-specific single words (see MATERIAL_WORDS/COLOR_WORDS above), so there's no length- or
    # specificity-based ordering to prefer; the only requirement is that it's fixed.
    return {"brands": brands, "sizes": sizes, "materials": tuple(sorted(materials)),
            "colors": tuple(sorted(colors)), "categories": categories}


class CatalogIndex:
    """Bundles BM25, metadata inverted indexes, and (lazily) dense embeddings over the frozen catalog."""

    def __init__(self, products: dict[str, dict], gazetteer: dict[str, set]):
        self.products = products
        self.ids: list[str] = list(products.keys())
        self.gazetteer = gazetteer

        self._doc_len: dict[str, int] = {}
        self._inverted: dict[str, dict[str, int]] = defaultdict(dict)  # term -> {pid: term_freq}
        self._by_category: dict[str, set[str]] = defaultdict(set)
        self._by_brand: dict[str, set[str]] = defaultdict(set)
        self._price: dict[str, Optional[float]] = {}
        self._build_bm25_and_metadata()

        self._embed_model = None
        self._embeddings: Optional["np.ndarray"] = None  # type: ignore[name-defined]
        self._id_to_idx: dict[str, int] = {}
        self._dense_failed = False

    # ---------- BM25 (plain, dependency-free — see D-BM25 in wiki/03_design_log.md) ----------
    def _build_bm25_and_metadata(self) -> None:
        for pid, p in self.products.items():
            tokens = tokenize(searchable_text(p))
            self._doc_len[pid] = len(tokens)
            tf: Counter[str] = Counter(tokens)
            for t, count in tf.items():
                self._inverted[t][pid] = count
            for part in _normalized_category_parts(p.get("categories") or []):
                if part in self.gazetteer["categories"]:
                    self._by_category[part].add(pid)
            details = p.get("details") if isinstance(p.get("details"), dict) else {}
            for key, val in details.items():
                if "brand" in key.lower() and val:
                    self._by_brand[str(val).strip().lower()].add(pid)
            store = p.get("store")
            if store:
                self._by_brand[str(store).strip().lower()].add(pid)
            price = p.get("price")
            self._price[pid] = float(price) if isinstance(price, (int, float)) else None

        n_docs = len(self.products)
        self._avg_doc_len = (sum(self._doc_len.values()) / n_docs) if n_docs else 0.0
        self._n_docs = n_docs

    def bm25_search(self, query_text: str, top_n: int = 150) -> list[str]:
        """O(query_terms * matching_docs) via the inverted index, not O(query_terms * all_docs) --
        the original draft scanned every one of 50k docs per query term, which would have made a
        full 200-session evaluator run impractically slow (self-caught before implementation, not
        by codex review)."""
        import math
        # Sorted, not a bare set iteration: self-caught during Phase 3.1's tuning sweep (two runs of
        # the identical config against the identical training split produced different
        # TechnicalScores). A plain set's iteration order is hash-randomized per Python process --
        # iterating query terms in a random order changes both the floating-point summation order
        # feeding `scores[pid]` (non-associative rounding) AND which pid gets inserted into `scores`
        # first, which is exactly what decides tie-breaking in the stable sort below. Sorting fixes
        # both, deterministically, regardless of the process's hash seed.
        q_tokens = sorted(set(tokenize(query_text)))
        if not q_tokens:
            return []
        k1, b = 1.5, 0.75
        scores: dict[str, float] = {}
        for t in q_tokens:
            postings = self._inverted.get(t)
            if not postings:
                continue
            df = len(postings)
            idf = max(0.0, math.log((self._n_docs - df + 0.5) / (df + 0.5) + 1))
            for pid, tf in postings.items():
                denom = tf + k1 * (1 - b + b * self._doc_len[pid] / (self._avg_doc_len or 1))
                scores[pid] = scores.get(pid, 0.0) + idf * (tf * (k1 + 1)) / (denom or 1)
        return [pid for pid, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:top_n]]

    # ---------- metadata rank (CORRECTED per codex review: a real fusion leg, not Buying-only) ----------
    def metadata_rank(self, slots: dict, top_n: int = 150) -> list[str]:
        if not slots:
            return []
        # `sorted(ids)`/`sorted(...)` below, not bare set iteration: same class of bug as
        # bm25_search's q_tokens (Phase 3.1 self-caught finding) -- each increment here is a fixed
        # constant so the summed *values* are order-independent, but a plain set's hash-randomized
        # iteration order still decides which pid is inserted into `scores` first, which decides
        # `most_common()`'s stable-sort tie-break among equal-score pids downstream.
        scores: Counter[str] = Counter()
        category = slots.get("category")
        if category:
            for cat_name, ids in self._by_category.items():
                if category.lower() in cat_name.lower() or cat_name.lower() in category.lower():
                    for pid in sorted(ids):
                        scores[pid] += 2.0
        brand = slots.get("brand")
        if brand and brand.lower() in self._by_brand:
            for pid in sorted(self._by_brand[brand.lower()]):
                scores[pid] += 2.0
        budget_max = slots.get("budget_max")
        if isinstance(budget_max, (int, float)):
            for pid, price in self._price.items():
                if price is not None and price <= budget_max:
                    scores[pid] += 1.0
        if not scores:
            return []
        return [pid for pid, _ in scores.most_common(top_n)]

    def apply_hard_filters(self, slots: dict) -> Optional[set[str]]:
        ids: Optional[set[str]] = None
        category = slots.get("category")
        if category:
            matched: set[str] = set()
            for cat_name, cat_ids in self._by_category.items():
                if category.lower() in cat_name.lower() or cat_name.lower() in category.lower():
                    matched |= cat_ids
            if matched:
                ids = matched
        brand = slots.get("brand")
        if brand and brand.lower() in self._by_brand:
            brand_ids = self._by_brand[brand.lower()]
            ids = brand_ids if ids is None else (ids & brand_ids)
        budget_max = slots.get("budget_max")
        if isinstance(budget_max, (int, float)):
            price_ids = {pid for pid, price in self._price.items() if price is not None and price <= budget_max}
            ids = price_ids if ids is None else (ids & price_ids)
        return ids

    def hydrate(self, ids: list[str]) -> list[dict]:
        out = []
        for pid in ids:
            p = self.products.get(pid)
            if p is None:
                continue
            out.append({
                "parent_asin": pid,
                "_score": 0.0,
                "attributes": self._attributes_for(p),
                "product": p,
            })
        return out

    def _attributes_for(self, p: dict) -> dict:
        """CORRECTED per codex review (two related findings): this used to populate only
        color/material/category/budget, so `_facet_value_entropy` always returned 0 for
        feature/style/size/use_case and `select_best_question` could never ask about them --
        despite almost every intent card having a feature-classified constraint. Also, raw price
        (near-100% cardinality) was unfairly dominating unnormalized entropy comparisons against
        low-cardinality facets like color, making "budget" the default first question even though
        wiki/09's own finding is that budget rarely survives the intent card's candidate slicing.
        Now: every enum-relevant facet gets a populated (if best-effort) value, and price is
        bucketed into a handful of bands so its cardinality is comparable to the others."""
        text = searchable_text(p).lower()
        attrs: dict[str, Any] = {}
        color_match = _COLOR_RE.search(text)
        if color_match:
            attrs["color"] = color_match.group(1)
        material_match = _MATERIAL_RE.search(text)
        if material_match:
            attrs["material"] = material_match.group(1)
        style_match = _STYLE_RE.search(text)
        if style_match:
            attrs["style"] = style_match.group(1)
        use_case_match = _USE_CASE_RE.search(text)
        if use_case_match:
            attrs["use_case"] = use_case_match.group(1)

        details = p.get("details") if isinstance(p.get("details"), dict) else {}
        for key, val in details.items():
            if "size" in key.lower() and val:
                attrs["size"] = str(val).strip()[:24]
                break

        attrs["category"] = coarse_category(p.get("categories") or [])

        price = p.get("price")
        if isinstance(price, (int, float)):
            attrs["budget"] = price_bucket(price)

        features = p.get("features")
        if isinstance(features, list) and features:
            # Best-effort proxy: the simulator's own "feature" bucket is a catch-all for whatever
            # doesn't classify as budget/material/color/size/style/use_case, so there's no single
            # canonical value to predict exactly -- the first feature bullet at least gives the
            # entropy calculation real per-product variation to work with, rather than always 0.
            attrs["feature"] = str(features[0]).strip()[:60]
        return attrs

    @staticmethod
    def _embedding_text(p: dict) -> str:
        """Short, targeted text for the dense leg -- title + top 2 features + coarse category.
        BM25 already indexes the full searchable_text() exhaustively; the dense leg's job is
        semantic placement, not exhaustive term coverage, so it doesn't need the same input size."""
        title = str(p.get("title") or "")
        features = p.get("features") or []
        feat_text = " ".join(str(f) for f in features[:2]) if isinstance(features, list) else ""
        category = coarse_category(p.get("categories") or [])
        return f"{title}. {feat_text}. {category}".strip()[:220]

    # ---------- dense retrieval (lazy model load; degrades gracefully if unavailable — NFR-2) ----------
    def _ensure_dense_ready(self) -> bool:
        """CORRECTED per codex review, two bugs fixed together:
        1. A cache *write* failure (e.g. read-only directory) used to discard the already-computed
           in-memory embeddings matrix too, via one broad try/except around both compute and save --
           the very next call (this is invoked once per candidate per turn via embedding_for(), plus
           once via encode_text()) would then recompute the ENTIRE 50K-item catalog from scratch
           every single time, effectively hanging evaluation. Saving to disk is now best-effort and
           isolated from the in-memory result.
        2. A genuine failure (import error, encode() itself raising) is now memoized in
           `self._dense_failed` so it's not retried on every call for the rest of the session --
           NFR-2's "degrade gracefully" must mean degrade ONCE, not degrade-and-retry-expensively
           forever.
        """
        if self._embeddings is not None:
            return True
        if self._dense_failed:
            return False
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
        except Exception:
            self._dense_failed = True
            return False
        try:
            from .model_paths import resolve as _resolve_model_path
            from .model_paths import resolve_data_asset as _resolve_data_asset
            # CORRECTED per codex review (2026-08-30): a bare cwd-relative path silently missed the
            # bundled submission cache whenever the importing process's cwd wasn't the package root
            # -- see model_paths.resolve_data_asset's docstring for the full reasoning.
            cache_path = _resolve_data_asset(Path("data/_catalog_embeddings.npz"))  # .npz: bundles ids alongside embeddings
            self._embed_model = SentenceTransformer(_resolve_model_path("bge-small-en-v1.5", "BAAI/bge-small-en-v1.5"))
            # Self-caught performance bug before shipping this: the first version encoded up to
            # 1000 chars/item (title+features+description+categories+store+details) across all
            # 50K items -- attention cost scales with sequence length, and this took far longer
            # than expected on CPU. Embedding text only needs enough signal to place an item
            # correctly in semantic space (title + a couple of features + category), not the full
            # searchable-text blob BM25 already covers exhaustively -- cut sequence length by
            # ~5-8x and cap the model's own max_seq_length so long outliers can't dominate cost.
            self._embed_model.max_seq_length = 64
            # CORRECTED (self-caught while preparing Phase 5's submission bundle): this used to
            # validate the cache by ROW COUNT alone (`cached.shape[0] == len(self.ids)`). If the
            # organizer's copy of the catalog ever has the same 50K products in a DIFFERENT row
            # order (same count, different sequence), row i's cached embedding would silently
            # belong to a different product than row i of `self.ids` -- every dense-search result
            # corrupted with no error, no fallback engaging (the cache looks "valid" by count).
            # Now stores and validates the exact id sequence alongside the embeddings.
            if cache_path.exists():
                with np.load(cache_path, allow_pickle=False) as cached:
                    if list(cached["ids"]) == self.ids:
                        self._embeddings = cached["embeddings"]
                        self._id_to_idx = {pid: i for i, pid in enumerate(self.ids)}
                        return True
            texts = [self._embedding_text(self.products[pid]) for pid in self.ids]
            emb = self._embed_model.encode(
                texts, batch_size=256, show_progress_bar=True, normalize_embeddings=True)
        except Exception:
            self._dense_failed = True
            return False

        # Compute succeeded -- commit the in-memory result unconditionally. Persisting the cache
        # to disk is a pure optimization for future runs; its failure must never undo this.
        self._embeddings = np.asarray(emb, dtype="float32")
        self._id_to_idx = {pid: i for i, pid in enumerate(self.ids)}
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache_path, embeddings=self._embeddings, ids=np.array(self.ids))
        except OSError:
            pass  # best-effort; this run still has working embeddings in memory regardless
        return True

    def dense_search(self, query_text: str, top_n: int = 150, query_embedding_hook=None) -> list[str]:
        """`query_embedding_hook(embedding) -> embedding`, if given, runs after text encoding and
        before the similarity search -- lets a caller nudge the search vector (e.g.
        phase2/query_nudge.py) without catalog.py importing phase2/ (same decoupling pattern as
        overgenerality.py's utility_fn and retrieval.py's disagreement signal)."""
        if not self._ensure_dense_ready():
            return []
        import numpy as np
        q_emb = self._embed_model.encode([query_text], normalize_embeddings=True)[0]
        if query_embedding_hook is not None:
            q_emb = query_embedding_hook(q_emb)
        sims = self._embeddings @ q_emb
        top_idx = np.argpartition(-sims, min(top_n, len(sims) - 1))[:top_n]
        top_idx = top_idx[np.argsort(-sims[top_idx])]
        return [self.ids[i] for i in top_idx]

    def embedding_for(self, pid: str) -> Optional["np.ndarray"]:
        """Self-caught before this ran: `self.ids.index(pid)` is an O(n) linear scan over 50K
        ids, called once per candidate per turn (up to ~50 candidates) -- a dict lookup, built
        once, is the obvious fix and costs nothing extra since _ensure_dense_ready() already
        iterates self.ids once to build the embedding matrix in the same order."""
        if not self._ensure_dense_ready():
            return None
        idx = self._id_to_idx.get(pid)
        if idx is None:
            return None
        return self._embeddings[idx]

    def encode_text(self, text: str) -> Optional["np.ndarray"]:
        if not self._ensure_dense_ready():
            return None
        return self._embed_model.encode([text], normalize_embeddings=True)[0]
