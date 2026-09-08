---
schema_version: "1.0"
id: "0008-04"
level: "task"
parent: "0008"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:270"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

add a regression check (scan or test) that flags any hardcoded German UI string in generated non-German HTML output, so future chrome/banner text additions can't silently bypass the i18n pipeline again -- DONE 2026-08-13: added `check_home_links()`/`check_no_hardcoded_german()` to `validate.py`, wired into `main()`; both pass cleanly (0 problems) in isolation against the current tree after 0008-01/0008-02. NOTE: the full `validate.py` run still exits 1 due to an unrelated, pre-existing `check_namespaces()` failure (see new backlog note below) -- not caused by this change. REF: 9c7da54a

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
