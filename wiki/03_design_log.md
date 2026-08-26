# 03 — Design Log (Chronological Narrative)

Free-form, dated, append-only. This is where "we tried X, it broke because Y, switched to Z" lives
— the texture that a table of decisions loses. Codex review findings and how they were resolved
also get logged here (with a link to the full report under `reviews/`).

---

## 2026-08-26 — Project scaffolding

- Read and digested the four source docs (`Tiktok_Problem.md`, `Amazon_Dataset_Description.md`,
  `Important_Links.md`, `Tiktok_Mail.md`). Confirmed this is TechJam 2026 Track 4 (Shopping
  Copilot / conversational search), 72-hour build window 2026-08-29 → 2026-09-01.
- Initialized git repo at project root (was not a repo before).
- Verified local tooling: `git 2.49.0`, `python 3.13.7`, `codex-cli 0.147.0` all present.
- Built the living wiki (this directory) and the CLAUDE.md / status.md enforcement rules that keep
  it authoritative across sessions. See DD-001.
- Kicked off import of external resources (participant repo + release kit) and Python venv setup —
  see [07_external_resources.md](07_external_resources.md) for outcome.
- No solution architecture decisions made yet — Pillars I–III design starts once the participant
  kit (starter agent, evaluator, API contract) has been inspected.

## 2026-08-26 — External resource import completed

- Cloned `techjam-conversational-search` into `external/techjam-conversational-search/` at commit
  `9a35be51780ff1caf89eceaabca34259e946f40f` (main).
- `gh` CLI is not installed in this environment, so release assets were listed via the GitHub REST
  API (`curl -s https://api.github.com/repos/TechJam2026/techjam-conversational-search/releases/tags/participant-kit`)
  and downloaded individually with `curl -L`. Three assets on the `participant-kit` tag:
  `catalog.jsonl.gz` (~18.3 MB), `SHA256SUMS`, `techjam-participant-kit.zip` (~18.3 MB). All
  downloaded successfully into `data/participant-kit/`.
- Verified checksums with `sha256sum` against the published `SHA256SUMS` file: **both files match
  exactly** (`catalog.jsonl.gz` → `07fd1426…a0a8f8`, `techjam-participant-kit.zip` →
  `b3d7e283…e5b38ae`). No integrity issues.
- Extracted `catalog.jsonl.gz` (50,000-line catalog) and the participant-kit zip into
  `data/participant-kit/`. Also copied `catalog.jsonl` into
  `external/techjam-conversational-search/data/catalog.jsonl` per the participant repo's own README
  (`data/catalog.jsonl` is gitignored inside that repo, confirming this is the intended local
  placement). The repo clone already shipped `data/public_set.jsonl` (200 labeled dev sessions)
  directly in git.
- Cloned the reference-only `AmazonReviews2023` loader repo into `external/AmazonReviews2023/` at
  commit `b18fdf54bd46013d60799684f7a4eb80d8501d1a`. Not used for the eval itself — kept for
  understanding the upstream data shape only, per the problem statement.
- Set up `.venv/` at project root with `python -m venv .venv` (Python 3.13.7). Checked the
  participant repo for `requirements.txt` / `pyproject.toml` / `setup.py` — none exist. Confirmed by
  reading `starter/agent.py` and `evaluator/local_evaluator.py` that both import only the Python
  standard library, matching the README's explicit claim. No packages needed installing.
  `requirements.txt` at project root documents this (empty of pins, with explanation).
  `requirements-freeze.txt` generated via `pip freeze` — empty, as expected.
- Sanity check: ran `python -m evaluator.local_evaluator` from
  `external/techjam-conversational-search/` inside the venv. It executed cleanly on the first try —
  no errors, no missing docs. Output matched the repo's documented baseline
  (`docs/baseline_results.json`) exactly: Hit Rate@10 `0.125`, MRR `0.068034`, MTTC `9.81`,
  Efficiency `0.119`, TechnicalScore `0.10671`, over the 200 public sessions (scenario breakdown:
  boundary/browsing/buying/intent_override all present in `results.json`). This confirms the whole
  pipeline (catalog + sessions + starter agent + evaluator) is wired correctly end to end.
- No blockers encountered. Everything in this step completed without issue — nothing to add to
  `status.md`'s Blockers section from this pass.
- Current state: `external/`, `data/participant-kit/`, `.venv/`, `requirements.txt`, and
  `requirements-freeze.txt` are all in place and untracked (per `.gitignore`) except the two
  requirements files at repo root, ready for the coordinating session to review/commit. Solution
  architecture work can now start from an inspected, verified, runnable baseline.
