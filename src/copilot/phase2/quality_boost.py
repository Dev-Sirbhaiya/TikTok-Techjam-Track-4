"""Phase 5.8: rank-time quality boost from the catalog's own average_rating/rating_number fields --
gated behind ENABLE_QUALITY_BOOST, UNTESTED pending ablation.

Found while answering a user question ("is quality modeled anywhere?" -- it wasn't): the catalog
carries `average_rating` and `rating_number` per product, and neither retrieval, fusion, nor ranking
ever touched them. A raw average_rating is unreliable for low `rating_number` items (a single 5-star
review looks identical to a well-established bestseller), so this uses a standard Bayesian/IMDB-style
shrinkage toward the catalog-wide mean rather than the raw average.
"""
from __future__ import annotations

_SHRINKAGE_C = 10.0  # pseudo-count: how many "average" ratings a product's own rating must outweigh


def bayesian_quality_score(product: dict, global_mean_rating: float) -> float:
    """Returns a value centered at 0 (mean-quality product), roughly in [-0.5, 0.5] for a 1-5 rating
    scale -- additive, same shape as preference.py's pos/neg boosts, not a replacement for them."""
    rating = product.get("average_rating")
    count = product.get("rating_number")
    if not isinstance(rating, (int, float)) or not isinstance(count, (int, float)) or count < 0:
        return 0.0
    shrunk = (count * rating + _SHRINKAGE_C * global_mean_rating) / (count + _SHRINKAGE_C)
    return (shrunk - global_mean_rating) / 5.0
