# 07 — External Resources & Datasets

Exactly what was imported, from where, at what version, and where it lives locally. This page must
stay accurate enough that a fresh clone of this repo plus this page is sufficient to reproduce the
environment — no upstream URL hunting needed later.

## Organizer-provided (authoritative — this is what the eval actually runs against)

| Resource | Source | Local path | Version/commit/checksum | Status |
|---|---|---|---|---|
| Participant repo (starter agent, evaluator, API contract, docs, submission rules) | https://github.com/TechJam2026/techjam-conversational-search | `external/techjam-conversational-search/` | commit `9a35be51780ff1caf89eceaabca34259e946f40f` (branch `main`) | done |
| Participant kit release (frozen 50k-product catalog, 200 public dev sessions, checksum file) | https://github.com/TechJam2026/techjam-conversational-search/releases/tag/participant-kit | `data/participant-kit/` | Assets: `catalog.jsonl.gz` (19,235,996 bytes), `SHA256SUMS`, `techjam-participant-kit.zip` (19,234,914 bytes). SHA256 verification: **PASS** — both `catalog.jsonl.gz` and `techjam-participant-kit.zip` match the hashes published in `SHA256SUMS` exactly (`07fd1426…a0a8f8` and `b3d7e283…e5b38ae` respectively). Extracted `catalog.jsonl` (50,000 lines) into `data/participant-kit/catalog.jsonl` and also copied it into `external/techjam-conversational-search/data/catalog.jsonl` per the participant repo's own README instructions (that path is gitignored inside the participant repo). `techjam-participant-kit.zip` extracted to `data/participant-kit/techjam-participant-kit/` — it is a superset mirror of the git repo plus `data/catalog.jsonl` and `data/public_set.jsonl` (200 dev sessions), consistent with the repo clone. | done |

## Background reference (not required for the eval — for understanding the data shape only)

| Resource | Source | Local path | Notes |
|---|---|---|---|
| Amazon Reviews 2023 loader code | https://github.com/hyp1231/AmazonReviews2023 | `external/AmazonReviews2023/` | reference only; problem statement explicitly says we do **not** need the full upstream dataset |
| Amazon Reviews 2023 dataset (full, HF) | https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023 | not downloaded | out of scope — organizer's frozen kit is authoritative; only pull specific files here if the participant kit is missing something documented in its own schema |

## Python environment

- Venv location: `.venv/` (project root), created with `python -m venv .venv` using Python 3.13.7.
- Dependency source: the participant repo (`external/techjam-conversational-search/`) has **no**
  `requirements.txt` / `pyproject.toml` / `setup.py`. Inspected `starter/agent.py` and
  `evaluator/local_evaluator.py` directly — both import only Python standard library modules
  (`json`, `re`, `sqlite3`, `argparse`, `random`, `statistics`, `uuid`, `collections`, `pathlib`),
  matching the README's claim that "the starter uses only the Python standard library." No
  third-party packages were installed.
- `requirements.txt` at repo root: present, intentionally empty of pins, with a comment explaining
  the above (stdlib-only) and instructions to add packages here if a custom agent needs an LLM SDK.
- `requirements-freeze.txt` at repo root: generated via `pip freeze` in the activated venv — empty,
  confirming zero third-party packages installed.
- Setup log / issues: see [03_design_log.md](03_design_log.md) entry for 2026-08-26.

## Verification checklist (mark off once the import agent finishes)

- [x] Participant repo cloned, commit SHA recorded above
- [x] Participant kit release downloaded and extracted
- [x] Catalog SHA256 checksum verified against the organizer's checksum file
- [x] Starter BM25 agent runs locally against the local evaluator without modification (sanity check)
- [x] Python venv created, all starter-kit dependencies installed cleanly (none required — stdlib only)
- [x] `requirements.txt` at repo root reflects the actual installed environment
