# Claim: Subtask 0037-26.06

owner_token: agent:worf-0037-26-06:0037-26.06:20260827T124500Z-worf2606
agent: worf-0037-26-06
persona: unprivileged Programmer (≠ gabriel dispatcher)
capability_class: unprivileged
execution_authority: direct git/test in own worktree; no runner; no Acceptance; no main; no DONE; no push
task: 0037-26.06
feature: 0037
branch: 0037-26.06
worktree: /Users/tobias.anton/devel/autodocs/.worktrees/0037-26.06
base_commit: 2064704457f98c66fb6f77ad3c263415864fe2ff
base_status: R2 candidate base (dispatcher-named). 0037-19 remesured [x] on branch 0037-19 at this tip (TODO.md line with REF c2f198e19). 0037-17 is an ancestor of 0037-19 (merge-base --is-ancestor yes). Parent Task branch 0037-26 does not exist; Feature 0037 is e495e0534 and is an ancestor of this tip.
merged_prerequisite_tips:
  - 0037-19: 2064704457f98c66fb6f77ad3c263415864fe2ff (this checkout)
  - 0037-17: contained in 0037-19
startup_review: claim-first after remesure; no sibling 26/27 writes; 0037-16 STOP not touched
state: [p]

## Task text (verbatim)

- [ ] **0037-26.06** PREREQ: 0037-26.06:0037-17, 0037-26.06:0037-19 Extend validation and build reports with stable findings, common run identity, and artifact manifests.
  - **Acceptance criteria:** Migrate build-report `1.0` explicitly; require shared run ID, source/tool/config commits, exact stage inputs/outputs, stable finding IDs, issue/criterion/campaign trigger, and success/failure; combining reports requires the same run/artifact lineage and all required stages, never latest mtime.
  - **Definition of Done:** Integration tests reject mixed runs, missing/malformed stages, unstable findings, incomplete artifact sets, and self-validating report injection and support reverse trace from final report to trigger/input.

## Write scope

- `_src/tools/build_report_envelope.py` (new)
- `_src/tools/build_report.py`
- `_src/validate.py` (validate-stage report emission only)
- `_src/i18n_translate.py`, `_src/i18n_diagrams.py`, `_src/generate.py` (stage report emission)
- `_src/tools/test_build_report.py`
- `_src/tests/test_build_report_provenance.py` (new DoD integration tests)
- `_src/tests/test_report_freshness.py`, `_src/tests/test_automation_safety.py` (fixture schema updates only as required)
- this claim
- `TODO.md` 0037-26.06 marker/bookkeeping on this branch only

## Must not

Acceptance; main; DONE.md; 0037-16 STOP lift; sibling 26/27; 16/19/20/38/42 product scope; shared root; memory_append; push; docs/pipeline/ governance edits.

## Next step

Implement explicit 1.0→2.0 migration, v2 envelope, combine-by-run-id (path-sorted, never mtime), producer emit, integration tests, then path-limited commits.
