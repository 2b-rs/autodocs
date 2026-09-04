---
schema_version: "1.0"
id: "0007-01"
level: "task"
parent: "0007"
state: "in_progress"
visibility: "internal"
prerequisites:
  - "0006"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:3053"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

OWNED BY THIS AGENT. PREREQ: 0007-01:0006 Complete source-backed truthing of the 200-record benchmark and produce a reviewable freeze candidate. (in progress by agent-0007-01, see `TODO-agent-0007-01.md`)

## Scope

- **History (2026-08-12):** Manually truthed the two previously called-out empty-field cases: `RS_SAF_21101` is an inline citation rather than a formal block, while mixed-case source ID `RS_DIAG_04005` is a real formal block with recovered heading/fields and `complete_start = true`.
  - **Progress (2026-08-15)**: Started incremental manual truthing of the remaining 186 `needs_review` entries in `_src/tests/fixtures/spec_extraction/benchmark-draft.json` (status was `draft-needs-manual-review`, all 200 entries `needs_review`, all `complete_start = null`). Verified 9 entries directly against source PDFs and flipped them to `status: reviewed` with reviewer identity, page citation, and full field transcription: `RS_CM_00001` (p.11, CommunicationManagement), `RS_CRYPTO_02001` (p.8, Cryptography), `RS_EM_00002` (p.11, ExecutionManagement, extra `Upstream requirements` field), `RS_AP_00111` (p.10, General), `RS_OSI_00100` (p.10, OperatingSystemInterface), `RS_PER_00001` (p.11, Persistency, no Dependencies/Use Case/Supporting Material fields in this doc style), `RS_PHM_00101` (p.10, PlatformHealthManagement), `RS_SHWA_00001` (p.7, SafeHardwareAcceleration), `RS_SM_00001` (p.8, StateManagement). Several draft entries had a recurring extraction bug — the "Supporting Material" field label bled into the preceding "Use Case" field value instead of being split out — corrected in each case with source citation. Root-caused on 2026-08-15 to wrapped-label handling in `spec_scrape.py` and filed as **0034-01**; it affects 146 of the 191 records still awaiting review here. Truthing those 146 by hand would bake extractor output into the fixture, so prefer landing `0034-01` first and regenerating, then hand-verifying the residue.
  - **Fixture staleness (2026-08-15, important):** `RS_EM_00111` in the draft was bound to the wrong source region entirely — pages 7-11 with a sentence-fragment heading and Description/Dependencies scraped from the glossary and Table 3.1 — while the real block is a clean single-page record on p.15. Corrected by hand. Crucially, re-running today's `spec_scrape.parse_record()` on that document returns the CORRECT heading and fields for `RS_EM_00111`, so this particular defect has already been fixed in the scraper since the draft was generated. Conclusion: **the draft fixture is partly stale relative to current extractor behaviour**, and its page spans/headings must not be trusted as review starting points. 39 unreviewed records show misattribution symptoms (>=4-page spans, glossary text in fields, fragment headings), an upper bound needing case-by-case checks. This strengthens the case for regenerating rather than hand-patching: regenerate after `0034-01` lands, then truth the result. Current state: 9 reviewed / 191 needs_review. `test_spec_extraction_campaign.py` still passes (5 passed) after all edits. This is real incremental progress, not full completion — 191 entries remain to be individually source-verified before this task can close; do not mark `0007-01` `[x]` until every entry is reviewed and no unexplained nulls remain.
  - **History (2026-08-12, pre-fix):** A recount found 12 headingless-but-populated `AUTOSAR_FO_RS_LogAndTrace` entries (`RS_LT_00001`, `00002`, `00003`, `00004`, `00008`, `00028`, `00030`, `00031`, `00032`, `00033`, `00035`, `00037`).
  - **History (2026-08-12, current):** Commit `fdba7e28` added the numbered-subsection heading fallback and updated the expected values; the same recount then found zero headingless-but-populated entries. The remaining candidate blockers are unresolved review/completeness metadata, not those 12 headings.

### Campaign B — Shape precision

## Acceptance criteria

- **AC-001** Exactly 200 unique entries cover all 18 source documents and the selection policy's difficult shapes
- **AC-002** every entry records source pages/locator, expected heading/fields/pages, explicit completeness disposition, reviewer identity/status/notes, and any exclusion/non-record rationale. No entry remains `needs_review`, and no unexplained `complete_start = null` is accepted as a freeze result

## Definition of Done

The candidate schema/version, inventory, coverage report, and validation command are committed; automated checks reject duplicate/missing entries, unresolved review state, missing provenance, and invalid completeness dispositions.
