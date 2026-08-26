# 08 — Evaluation Log

Track every local evaluator run over time so regressions are visible immediately. Anchor metrics
per [00_problem_statement.md](00_problem_statement.md) Pillar IV: Hit Rate@K (coverage), MRR /
Top-K Hit Rate (precision), MTTC (efficiency), and the combined TechnicalScore the organizer's
evaluator reports.

| Date | Commit | Variant / change under test | Hit Rate@10 | MRR | MTTC | TechnicalScore | Notes |
|---|---|---|---|---|---|---|---|
| 2026-08-26 | (pending — recorded pre-commit) | baseline (organizer's weak BM25 starter, unmodified), `python -m evaluator.local_evaluator` over the 200 public dev sessions | 0.125 | 0.068034 | 9.81 | 0.10671 | Efficiency sub-metric: 0.119. Matches the repo's own documented baseline exactly (`docs/baseline_results.json`) — confirms catalog+sessions+starter+evaluator are wired correctly end to end. **This is our regression floor**: every future variant must be compared against these numbers. Per-scenario breakdown (boundary/browsing/buying/intent_override) is in `results.json` (gitignored, regenerate via the evaluator command above). |

Add a row every time the local evaluator is run against a meaningfully different variant (not
every trivial commit). Link back to the relevant `02_design_decisions.md` entry when a metric
change is the direct result of a decision.
