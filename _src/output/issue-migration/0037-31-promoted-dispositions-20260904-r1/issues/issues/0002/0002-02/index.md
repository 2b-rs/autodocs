---
schema_version: "1.0"
id: "0002-02"
level: "task"
parent: "0002"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:93"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

decide whether the process description should be a single static `nolang` page or a localized page family, and document the rationale — DECIDED 2026-08-14: the process description **shall be i18n'ed** (a localized page family, wired into the same i18n extraction/translation/merge pipeline as the rest of the site), not a single static `nolang` page. TODO (design impact for 0002-04 onward): the page model must go through `_src/sources/pages/`, participate in `i18n_translate.py extract/merge`, and be generated per-language by `generate.py` like other localized pages, including fallback-to-German behavior for untranslated segments.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
