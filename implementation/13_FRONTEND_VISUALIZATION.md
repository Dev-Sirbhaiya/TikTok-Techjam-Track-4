# 13 — Frontend Visualization ("Embedding Explorer")

**Status: design complete, prototype published.** Live interactive concept (synthetic data, proves the
interaction design, not the real embeddings):
**https://claude.ai/code/artifact/31def4f4-8acc-4bc0-adcd-f31c0abce200** — drag to orbit the 3D space,
toggle auto-rotate and the ground-truth overlay, scroll to zoom. Private by default; share it from the
artifact's own share menu if it needs to go beyond this session. Everything in it is also described in
full below so this spec survives independent of the link.

## What this is, and is not

This is a **debug and demo visualization tool**, not part of the scored `Agent` path. The competition
spec explicitly places "UI/UX Development" out of scope — evaluation is "purely via automated backend
APIs and headless pipelines" (`wiki/00_problem_statement.md`). Building this is legitimate and valuable
anyway, for three reasons that don't conflict with that constraint:

1. **Phase 5.4 needs a demo video**, and "a walkthrough showing API usage, inference results, or result
   analysis" is explicitly accepted for backend/NLP tracks with no UI. A good visualization *is* that
   walkthrough's visual spine.
2. **Debugging a failing session is hard from JSON logs alone.** Seeing the candidate pool in embedding
   space, the dialog state, and the retrieval funnel side by side is a genuinely faster way to find why
   a session missed, especially for Intent Override and Boundary scenarios (`wiki/09` flags these as
   the most bug-prone).
3. **Judging criteria reward "well-structured, thoughtful architecture" and clear problem insight**
   (Technical Execution 35%, Innovation & Problem Insight 20%) — a tool that visibly demonstrates how
   the four pillars work together is strong supporting material, as long as it never becomes the thing
   being judged in place of the actual metrics.

**Guardrail, stated plainly so it can't drift**: this tool consumes a JSON export produced *after* an
evaluator run. It never sits on the scored request path, never adds latency to `Agent.respond()`, and
its "ground truth" overlay (see below) only exists because dev-session labels are available for
debugging — the live agent never has access to them, exactly as documented in
`implementation/06_DECISION_LOG.md` D6/D7. Do not let Phase 0-3 build time bleed into this — see
`05_BUILD_PLAN.md`'s placement (a new, explicitly optional step, not inserted into the numbered
critical path).

## What it visualizes

| Panel | Shows | Data source |
|---|---|---|
| 3D embedding space | Product catalog subsample projected to 3D, colored by category; the current turn's query point; thread lines to the top candidates; an optional ground-truth overlay (dev sessions only) | `preference.py`/`retrieval.py`'s cached embedding matrix, reduced offline |
| Turn timeline | 10-slot stepper; each turn marked by action taken (ask/commit/both) and whether it was the hit turn | Per-turn `agent.py` output log |
| Over-generality gate | A radial gauge of the current pool entropy against the calibrated ask/commit thresholds | `overgenerality.py`'s `score_entropy()` output |
| Dialog state | Filled slots (pills), hard-rejected values (struck through), soft-rejected values (dimmed, confidence shown), and any override event | `DialogState` snapshot per turn |
| Preference vectors | Small sparklines of turn-over-turn **stability** (cosine similarity between consecutive turns' vectors) — rising toward 1.0 as preferences converge | `preference.py`'s EMA vectors; **not** their norm (see correction below) |

**CORRECTED per codex review round 2**: the original design plotted "affinity magnitude" as the
sparkline value, but `preference.py`'s `_ema()` re-normalizes the stored vector to unit length on
every update — so its norm is always ≈1 regardless of turn, and a "magnitude" sparkline would be a
flat, meaningless line. Fixed to plot **cosine similarity between the current turn's preference vector
and the previous turn's** instead — this actually changes over the session (low early, while
preferences are still forming; converging toward 1.0 as the signal stabilizes) and is a genuinely
informative turn-over-turn quantity.
| Retrieval funnel | Candidate counts shrinking through BM25 → dense → RRF fusion → rejection filter → reranked top-10 | Per-turn candidate-count log at each pipeline stage |

## Why 3D, and why PCA (not UMAP/t-SNE) for the live view

- **3D over 2D**: the catalog spans three fairly distinct top-level verticals (Clothing, Shoes,
  Jewelry — see `wiki/09_simulator_mechanics.md`'s catalog sampling), and a third axis gives real
  separation between them without fighting for the same 2D plane a 2D t-SNE plot would need. It's also
  simply a better demo moment — an orbiting, thread-lit point cloud reads immediately as "the agent
  is reasoning over a semantic space," which is exactly the story Pillar I is telling.
- **PCA, not UMAP/t-SNE, for the interactive/live-recomputable view**: PCA is deterministic, needs no
  training/hyperparameter tuning, and is fast enough to recompute if the embedding model changes —
  consistent with this project's no-training ethos. UMAP/t-SNE give visually tighter clusters but are
  stochastic and slower; **optionally precompute one UMAP projection offline purely for the polished
  demo-video recording** (a one-time, non-interactive export), while the interactive debug tool during
  development uses the cheap PCA projection. Don't block Phase 0-3 work on this decision — PCA is the
  default and is sufficient either way.

## How it's built (real implementation — not the artifact's constraints)

The published artifact prototype is a **self-contained, dependency-free** HTML/Canvas mockup (no
external libraries at all, since the artifact sandbox blocks CDN scripts) — it proves the interaction
design and visual language with synthetic data, not real embeddings. The **actual project tool** has
no such constraint and should be built properly:

```
tools/
├── export_viz_data.py     # runs after an evaluator pass; dumps one JSON per session:
│                           #   catalog subsample + 3D coords (sklearn PCA), per-turn state
│                           #   snapshots, funnel counts, entropy, action taken, hit turn
└── viz/
    ├── index.html          # loads Three.js (via npm/local vendor, NOT a CDN — this is a
    │                       # real repo asset, unlike the constrained artifact preview) for a
    │                       # proper WebGL point cloud: real depth, real lighting, smooth orbit
    ├── app.js              # reads the exported JSON, renders all six panels
    └── style.css           # the same token system as the artifact prototype (see below)
```

Recommended stack for the real tool: **Three.js** (vendored locally, `npm install three` and bundle,
or a downloaded local copy — not a CDN reference, so it works offline per the submission rules'
network-access disclosure) for the 3D point cloud specifically (real WebGL gives better depth
cueing/performance than hand-rolled canvas math at catalog scale), plain HTML/CSS/SVG for the other
five panels (they're 2D and don't need a 3D engine). `sklearn.decomposition.PCA` (already a common
dependency, or a 15-line NumPy SVD if avoiding the import) for the projection step in
`export_viz_data.py`.

## Design language (carried from the published prototype — reuse these tokens, don't reinvent)

- **Palette**: near-black warm-plum ground (`#17141B`) and surface (`#211D27`); brass/gold accent
  (`#C9A66B`) used for the query point, thread lines to neighbors, and active UI state — chosen to nod
  at the catalog's Jewelry vertical and read as "premium boutique tag," not generic dashboard neon.
  Category colors: dusty rose (Clothing), slate teal (Shoes), brass (Jewelry) — three warm-adjacent,
  distinguishable hues, not a rainbow. Semantic colors kept separate from the accent: sage green for
  hits/positive signal, muted terracotta for misses/hard-rejections, amber for the override warning.
- **Type**: Fraunces (display serif, headings only) for a boutique-editorial voice against the
  technical subject matter; Work Sans for UI chrome and labels; JetBrains Mono with tabular figures
  for every numeric readout (turn counts, entropy, funnel counts) so columns of digits actually align.
- **Layout**: dominant 3D stage on the left (the hero — this is the one thing worth a "wow" moment in
  the demo video), a fixed-width inspector column on the right stacked as discrete panel cards, a slim
  top bar for session/turn selection. Deliberately dark-only (not a light/dark toggle) — a data-dense
  3D scene doesn't survive a naive light-mode inversion, and the boutique-dark identity is a real
  aesthetic choice for this subject, not a default.

## Build placement (does not compete with Phase 0-3 time)

Not inserted into `05_BUILD_PLAN.md`'s numbered critical path. If time allows after Phase 1 (or during
Phase 5's packaging window), add as an unnumbered "Phase 5.0 — Visualization tool (optional, time-
permitting)" step: build `tools/export_viz_data.py` first (cheap, reuses logging already built in step
0.10), then the `tools/viz/` front-end. If time is short, the six-panel JSON export alone (without the
polished front-end) is still useful for manual debugging and costs almost nothing to keep.
