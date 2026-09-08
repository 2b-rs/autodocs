---
schema_version: "1.0"
id: "0008-06"
level: "task"
parent: "0008"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:274"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

document the requirement in `_src/WARTUNG.md` / `docs/pipeline/actions.md` that any new page-chrome text (banners, notices, badges) must go through `ui.json`/segment registers, not literal German strings in Python -- DONE 2026-08-13: added a dedicated subsection to `_src/WARTUNG.md` (`### Regel: Seiten-Chrome-Texte gehoeren in die i18n-Register, nicht in Python-Strings`) documenting the requirement and referencing the 0008-01 incident and the 0008-03/0008-04 regression checks as enforcement. REF: 82b25ae6

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
