---
schema_version: "1.0"
id: "0007-02"
level: "task"
parent: "0007"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3064"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

REF: local-20260815-0007-02. Resolve the claimed dense-definition-list/inline-heading record shape from concrete source evidence and retain the already verified `RS_LT` numbered-subsection variant as a distinct shape.

## Scope

- **History (2026-08-12):** Commit `fdba7e28` implemented the separate `AUTOSAR_FO_RS_LogAndTrace` pattern—a numbered subsection immediately above a bare `[RS_LT_xxxxx]` marker—and all 12 affected benchmark headings now pass. The originally cited `RS_PHM_00001..00003` example is absent from the benchmark and remains unverified.
  - **Resolution (2026-08-15)**: Verified against `AUTOSAR_AP_RS_PlatformHealthManagement.pdf` (R25-11), page 21. `RS_PHM_00001..00003` are **not** live requirement definitions and do not support the claimed shape: the document's own change history states they were removed in the R24-11 release, and page 21 shows them only inside Appendix "A.3.3 Deleted Requirements in R24-11", a standard `Number Heading` table identical in structure to every other Added/Changed/Deleted appendix table (A.1.1–A.4.3) — i.e. the already-handled `number_heading` extraction category, not a new "dense definition list, inline heading, no marker" shape. The test fixture `_src/tests/fixtures/spec_extraction/negative-history.json` already correctly marks all three IDs `not_definition`/`history_only`, confirming the pipeline's existing behavior is correct. Retired the unsupported claim in `docs/brainstorming/SPEC_QUALITY_ROADMAP-original.md` with full source citation; no code change was needed. Regression confirmed green: `test_spec_extraction_campaign.py` + `test_spec_scrape_upstream.py`, 15 passed.

### Campaign C — Independent approval and enforcement

## Acceptance criteria

- **AC-001** Locate and cite at least one real instance matching the exact claimed inline-heading/no-marker shape and add positive/negative fixtures, or document that the cited `RS_PHM_00001..00003` example does not support that shape and correct/retire the unsupported claim. Do not generalize the `RS_LT` fallback to a materially different layout without source evidence

## Definition of Done

Shape documentation names exact source locators and parser boundaries; focused and benchmark regression tests pass for every retained shape and prove unrelated prose/citations are not promoted to records.
