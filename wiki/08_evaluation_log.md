# 08 — Evaluation Log

Track every local evaluator run over time so regressions are visible immediately. Anchor metrics
per [00_problem_statement.md](00_problem_statement.md) Pillar IV: Hit Rate@K (coverage), MRR /
Top-K Hit Rate (precision), MTTC (efficiency), and the combined TechnicalScore the organizer's
evaluator reports.

| Date | Commit | Variant / change under test | Hit Rate@10 | MRR | MTTC | TechnicalScore | Notes |
|---|---|---|---|---|---|---|---|
| — | — | baseline (organizer's weak BM25 starter, unmodified) | _tbd_ | _tbd_ | _tbd_ | _tbd_ | run once the participant kit is verified — this is our regression floor |

Add a row every time the local evaluator is run against a meaningfully different variant (not
every trivial commit). Link back to the relevant `02_design_decisions.md` entry when a metric
change is the direct result of a decision.
