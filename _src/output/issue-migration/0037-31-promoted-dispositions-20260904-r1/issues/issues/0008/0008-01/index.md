---
schema_version: "1.0"
id: "0008-01"
level: "task"
parent: "0008"
state: "open"
visibility: "internal"
prerequisites:
  - "0006-09"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:264"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0008-01:0006-09 (soft — fix independently now, but content/placement likely rebuilt once 0006 lands) — extract the hardcoded German review-notice banner (`lib_docmodel.py`, `_review_page_enhancements()`: "%d API-Element%s mit Review-Bedarf" / "Vor der Freigabe müssen Requirement-Text und Zuordnung geprüft werden.") into the i18n segment/ui.json pipeline so it renders translated in all 9 non-German language trees instead of always German (found 2026-08-13 via nl screenshot, `ara::log` namespace page) -- DONE 2026-08-13: `_review_page_enhancements()`/`render_page()` now accept an optional `notice_ui` dict (singular/plural/body); German canonical output unchanged (falls back to the same hardcoded German strings). Added best-guess `review_notice` translations to `ui.json` for all 10 non-German languages; curator should spot-check wording. All language trees rebuilt via `generate.py --lang=alle`. Also fixed an unrelated regression from 0001-05 (commit d85e0d86): a local `import json, os` in generate.py's main() shadowed the module-level `os` import and json was never imported at module scope either, breaking every non---check run entirely (UnboundLocalError then NameError). REF: a4acfc6c

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
