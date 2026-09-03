# 0037-29 disposition-policy implementation evidence

Task `0037-29` implements the Q1–Q5 mapping selected by `DEC-0037-008` without
activating the issue store or mutating legacy authority files.

- Candidate baseline: branch `0037-29`, current `main` merged at `e17a47d98e18067bf06cf58e0439343216b6b404`.
- Exact evidence baseline: `51be4db07c26bf48aa1eb00ff8cdbcea8fc81b45`.
- Q1/Q2/Q3 remain provenance-only and grant neither lease nor evidence credit.
- Q4 exact signed coverage changes affected legacy terminals to OPEN with
  `legacy-terminal-unverified` and removes any candidate `closure.json`.
- Q5 malformed syntax remains archive-only; `[~]` is retained as an OPEN item
  labeled `investigation-required` after exact signed coverage.
- The generator binds finding id, rule, locator, item, source commit, exact
  source/field digest, disposition, reason, authority, time, and evidence into
  the existing canonical payload digest. The separate authority-record helper
  emits the exact payload binding consumed by git-SSH verification.

Validation:

- `python3 -m unittest _src.tests.test_issue_import_legacy.DispositionContractTests`
  — 14 tests passed (including Q4/Q5 red/green and generator binding).
- `python3 -m unittest _src.tests.test_issue_import_legacy`
  — 36 tests passed before the exhaustive watermark test was added.
- AE-5 invariant: every `(id, rule, locator, item)` tuple is unique within each
  pinned watermark and every rule belongs to an authorized disposition family.
  Domain: the complete 910- and 911-finding JSON arrays stored at the exact
  evidence commit. Method: exhaustive, seed not applicable, replay pin
  `51be4db07c26bf48aa1eb00ff8cdbcea8fc81b45`, actual case count `1821`.

No Acceptance, closure credit, production migration, activation, `main`
advance, TODO/DONE mutation, or release authority is asserted here.
