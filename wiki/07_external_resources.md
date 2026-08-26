# 07 — External Resources & Datasets

Exactly what was imported, from where, at what version, and where it lives locally. This page must
stay accurate enough that a fresh clone of this repo plus this page is sufficient to reproduce the
environment — no upstream URL hunting needed later.

## Organizer-provided (authoritative — this is what the eval actually runs against)

| Resource | Source | Local path | Version/commit/checksum | Status |
|---|---|---|---|---|
| Participant repo (starter agent, evaluator, API contract, docs, submission rules) | https://github.com/TechJam2026/techjam-conversational-search | `external/techjam-conversational-search/` | _(fill in commit SHA once cloned)_ | pending |
| Participant kit release (frozen 50k-product catalog, 200 public dev sessions, checksum file) | https://github.com/TechJam2026/techjam-conversational-search/releases/tag/participant-kit | `data/participant-kit/` | _(fill in release asset names + SHA256 verification result)_ | pending |

## Background reference (not required for the eval — for understanding the data shape only)

| Resource | Source | Local path | Notes |
|---|---|---|---|
| Amazon Reviews 2023 loader code | https://github.com/hyp1231/AmazonReviews2023 | `external/AmazonReviews2023/` | reference only; problem statement explicitly says we do **not** need the full upstream dataset |
| Amazon Reviews 2023 dataset (full, HF) | https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023 | not downloaded | out of scope — organizer's frozen kit is authoritative; only pull specific files here if the participant kit is missing something documented in its own schema |

## Python environment

- Venv location: `.venv/` (project root)
- Dependency source: `external/techjam-conversational-search/requirements.txt` (or equivalent,
  once inspected) plus anything this project adds — track additions in a project-level
  `requirements.txt` at repo root, don't hand-install untracked packages into the venv.
- Setup log / issues: see [03_design_log.md](03_design_log.md) entry for 2026-08-26.

## Verification checklist (mark off once the import agent finishes)

- [ ] Participant repo cloned, commit SHA recorded above
- [ ] Participant kit release downloaded and extracted
- [ ] Catalog SHA256 checksum verified against the organizer's checksum file
- [ ] Starter BM25 agent runs locally against the local evaluator without modification (sanity check)
- [ ] Python venv created, all starter-kit dependencies installed cleanly
- [ ] `requirements.txt` at repo root reflects the actual installed environment
