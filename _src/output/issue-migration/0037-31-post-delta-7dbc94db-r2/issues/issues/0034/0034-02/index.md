---
schema_version: "1.0"
id: "0034-02"
level: "task"
parent: "0034"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2605"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

(wontfix — AGENT PERPLEXITY, see `TODO-perplexity.md`) Fix `_record_slice()` definition-anchor detection in `spec_scrape.py` so requirement blocks whose opening `⌈` marker is emitted *before* the `[ID]` line are anchored to the real definition instead of falling back to an unrelated first mention. REF: e51f161480e493c35511e3f3b0959407bd776dc4

## Scope

- **Reason (2026-08-15, AGENT PERPLEXITY):** Reproduced the task against the real cached AUTOSAR corpus before editing. The named motivating example `RS_OSI_00209` in `AUTOSAR_AP_RS_OperatingSystemInterface.pdf` already parses correctly on the current code path: its real definition occurrence has the opening marker `⌈` 99 characters *after* the `[ID]`, inside the existing 240-character lookahead, and `parse_record()` returns the expected heading plus `Description`, `Rationale`, `Dependencies`, and `Use Case`. A corpus-wide probe for records with a preceding `⌈` but no following `⌈` found five apparent candidates, all in `AUTOSAR_AP_RS_General.pdf`, but every one is a citation-only mention of an external `SWS_CORE_*` ID inside some other requirement's prose, not a local definition missing its anchor. There is therefore no reproducible `_record_slice()` definition-anchor bug of the form described by this task on the current repository state. The real underlying risk is citation-only ID handling, which is already owned by **0034-04**; that sibling task remains open and absorbs the relevant concern. Evidence: `logs/source-reconnaissance/20260815-215209/` and `logs/source-reconnaissance/20260815-215652/`.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
