---
schema_version: "1.0"
id: "0034-04"
level: "task"
parent: "0034"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2617"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

Exclude citation-only ID mentions from benchmark record selection in `_src/tools/spec_extraction_benchmark.py`, so an ID that is merely referenced in prose never becomes a benchmark entry. REF: `0ca23e089`.

## Scope

- **Discovery (2026-08-15, found while working 0007-01):** `RS_SAF_21101` was selected as a benchmark record for `AUTOSAR_AP_RS_PlatformHealthManagement`, but that document does not define it. Its sole occurrence (p.9) is an inline citation inside a running sentence: "...as recommended in ISO26262, for instance [RS_SAF_21101][4]." No block-opening marker appears within 120 characters before or 200 characters after the ID, and no formal block exists anywhere in the file.
  - **Cross-reference (2026-08-15):** Task **0034-02** was investigated and closed `[w]` because its named motivating example does not reproduce on the current repository state. The real concern surfaced during that probe — citation-only mentions of external IDs being treated like local definitions — belongs here and is absorbed by this task.
  - **Symptom:** the produced entry had `heading: null`, `fields: {}` and `pages: [9, 10]` - it anchored to the citation and then spilled past the page boundary, which additionally gave it a bogus `multi_page` category.
  - **Distinct from 0034-01/02/03:** those are extractor defects (field splitting, anchor direction, missing label). This one is a record-SELECTION defect in the benchmark builder: the record should never have been created. Note `spec_extraction_benchmark.py` was previously cleared of blame for 0034-01, which remains correct; this is a separate concern in the same file.
  - **Completion evidence (2026-08-17):** Definition-anchor filtering, cross-backend anchor handling, counted skip diagnostics, the 199-record fixture, and five focused benchmark tests were committed in `0ca23e089`; compilation and the focused benchmark plus scraper regression suite passed 55 tests; the automation-safety scan returned `verdict: PASS` with zero findings/policy errors.

## Acceptance criteria

- **AC-001** a candidate ID is promoted to a benchmark record only when a definition block can be anchored to it (marker present in either direction, per the 0034-02 fix)
- **AC-002** citation-only mentions are skipped and counted in a report so silent loss is impossible
- **AC-003** a regression test covers the `RS_SAF_21101` case
- **AC-004** upstream-requirement cross-references such as `RS_SAF_10039` cited inside other records are likewise not promoted

## Definition of Done

fix and tests committed with `REF`; the existing `RS_SAF_21101` entry in `_src/tests/fixtures/spec_extraction/benchmark-draft.json` (currently reviewed and flagged `not_defined_in_document`) is removed as part of the regeneration, reducing the benchmark from 200 to 199 records, and the count is updated wherever it is asserted.
