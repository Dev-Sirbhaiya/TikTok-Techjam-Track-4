# Codex Review — Architecture Synthesis (2026-08-29)

Reviewed commit: `0a0dd8fba5f767cd5610dd2562f05c1b48f339fd` ("architecture: merge user ideas +
research into implementation/ corpus"). Full raw output: `architecture-synthesis-2026-08-29.raw.txt`
(gitignored). Curated findings + resolutions logged in full at
`implementation/06_DECISION_LOG.md`'s "Codex review findings" section — summary here:

**7 findings, all fixed, none declined:**
- 5× P1 (evaluator-shim packaging bug, missing recommendations on ask turns, wrong response object
  shape, non-softmax entropy normalization, unaddressed offline-model packaging risk)
- 2× P2 (Phase 1.3 threshold sweep missing a validation split, metadata not contributing to Browsing
  turns' retrieval fusion)

All were caught at the design-doc stage, before any implementation code existed — exactly the value
the phase-level review tier is meant to provide. Files touched by fixes: `implementation/04_SYSTEM_DESIGN.md`,
`implementation/05_BUILD_PLAN.md`, `implementation/10_PRE_REGISTRATION.md`,
`implementation/06_DECISION_LOG.md`.
