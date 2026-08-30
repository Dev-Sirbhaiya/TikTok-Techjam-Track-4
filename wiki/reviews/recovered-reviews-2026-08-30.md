# Recovered Codex Reviews — 2026-08-30

**How these were found**: 6 `codex exec review` invocations across this session produced short,
seemingly-incomplete `.raw.txt` files (banner + one exec command, nothing else) and were logged as
failed/blocked at the time. While debugging one more such case, the actual review verdict was found
sitting in the session's rollout transcript (`~/.codex/sessions/**/*<session-id>*.jsonl`, under
`"type":"ExitedReviewMode"` → `review_output`) — the review had fully completed; the final verdict
simply never reached the redirected stdout file. All 6 were recovered with `tools/extract_review.py`
and are triaged below. Full narrative: `wiki/03_design_log.md`'s "recovered reviews" entry.
Process fix: `CLAUDE.md`'s work-phase protocol now documents this pitfall directly.

## 1. `tools/tune_strategy.py` — multi-candidate validation contamination

**[P1, confidence 0.98]** `--split validation` let a candidates file with more than one entry be
evaluated and ranked together, letting validation results influence which candidate looks best —
exactly what `10_PRE_REGISTRATION.md`'s train/validation split exists to prevent.

**Audit**: exercised several times this session (round-3 threshold extremes, metadata-RRF-weight
confirmatory check). In every instance the actual decision reached was "no candidate beats the
default" or "decline the change" — never a cherry-picked "ship this one." No shipped KEEP decision
was reached this way.

**Fixed**: the tool now refuses (`SystemExit`) to evaluate more than one candidate against
`--split validation` in a single invocation.

## 2. Anthropic client — no bounded timeout

**[P1, confidence 0.97]** The SDK's default timeout/retry policy could block an ambiguous turn for
minutes on a slow/unreachable/rate-limited endpoint before the except-and-fallback ever triggered.

**Fixed**: `anthropic.Anthropic(api_key=..., timeout=8.0, max_retries=0)`.

## 3. LLM listwise rerank — no determinism control (and the fix that broke it worse)

**[P1, confidence 0.94]** No explicit sampling control on the `messages.create()` call risked
non-reproducible permutations.

**First fix attempt (`temperature=0`) was itself broken**: the installed `anthropic` SDK (1.2.0)
doesn't accept a `temperature` parameter in this API version at all — confirmed via
`inspect.signature`. It crashed every call with `TypeError`, silently caught by the existing
except-and-fallback, **completely disabling the booster with no visible error**. The immediate
"re-verification" run after that fix produced byte-identical ON/OFF results, which should have been
an instant red flag and initially wasn't.

**Actually fixed**: removed the unsupported kwarg. Empirically, repeated identical calls returned
byte-identical permutations with no temperature control at all — an observation, not a guarantee;
documented as a real, unresolved SDK limitation. Re-ablated with the working fix: validation (n=40)
ON 0.388104 vs OFF 0.3605; training (n=160) ON 0.442434 vs OFF 0.417911 — confirms the original
conclusion (KEEP ENABLED) once the code actually works.

## 4. Weighted RRF fusion — zero-weight legs still contributed candidates

**[P2, confidence 0.99]** `weight=0.0`, documented as "drop this leg entirely," still inserted every
one of that leg's ids into the fused-score dict with a zero contribution, making `fused` look
non-empty from spurious entries alone.

**Fixed**: legs with `weight == 0.0` are now skipped entirely. Affects only the already-declined
`METADATA_RRF_WEIGHT=0.0` exploration — the shipped default (`1.0`) never triggers this path.

## 5. Slate hedging shipped despite a validation-split wash — REVERSED

**[P2, confidence 0.96]** The validation-split check showed HitRate@10 identical between ON and OFF
(0.45 both) — a wash, not a win — while the training split showed a real improvement. The shipped
decision reasoned the validation sample was "probably just underpowered" and shipped anyway. This
is precisely the reasoning `10_PRE_REGISTRATION.md`'s own rule exists to rule out.

**Reversed**: `ENABLE_SLATE_HEDGING` set back to `False`. This also retracts the earlier
"guaranteed-path score raised to 0.415731" claim — corrected figure is 0.406428. Module kept,
disabled, for the "tried, looked promising, held-out check didn't confirm it, correctly declined on
review" record.

## 6. `tools/calibration_check.py` — conflated "both" with "commit"

**[P2, confidence 0.97]** "both" actions still ask a clarifying question and are deliberately not
hedged by `agent.py` (hedging gates to `action == "commit"` only), so counting them as forced
commits skewed the diagnostic that motivated building slate hedging.

**Fixed**: now tracks only genuine `"commit"` actions.

## 7. Embedding cache path resolved against process cwd, not the package

**[P1, confidence 0.98]** `catalog.py`'s cache path was cwd-relative. If the official harness
imports `submission/agent.py` without first `cd`-ing into `submission/` (the likely case), the
bundled cache is silently missed and the ~14.5-minute full-catalog recompute triggers anyway — the
entire point of bundling it, defeated. The original "verified end-to-end" offline test happened to
`cd` into `submission/` first, which masked this by coincidence rather than testing the real fix.

**Fixed**: added `model_paths.resolve_data_asset()` (cwd-relative first for dev convenience,
package-relative second for the real submission scenario). **Re-verified properly**: ran the
isolated offline test again, deliberately staying at the temp directory's root and importing via
`sys.path.insert(0, "submission")` — `Agent` constructed in 13s, a genuine cache hit.

## 8. `build_submission.py` — missing cache only warned, didn't fail the build

**[P1, confidence 0.96]** A submission built without the evaluator ever having generated the
embedding cache would ship silently incomplete while still printing "submission built."

**Fixed**: missing cache is now a hard `SystemExit`, not a warning.

## 9. Phase 4 lookahead — probability mis-normalization for sparse facets

**[P2, confidence 0.95]** `expected_entropy_reduction()` normalized each value's probability over
the POPULATED subset while `base_entropy` covered the full pool, letting a sparsely-populated facet
look artificially maximally informative. Affects only already-disabled code (Phase 4 was declined
regardless of this bug).

**Fixed anyway**: now weights every branch, including an explicit "missing" branch, against the
full pool size.

## Net effect

2 genuine submission-breaking P1 bugs caught and fixed before they could silently degrade or
invalidate official scoring. 1 previously-reported "shipped win" (slate hedging) correctly reversed.
1 LLM-booster fix-attempt bug caught before it could ship a completely inert "working" feature. All
findings triaged with either a fix or an explicit, audited decline — no finding silently dropped.
