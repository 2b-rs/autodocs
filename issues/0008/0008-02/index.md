---
schema_version: "1.0"
id: "0008-02"
level: "task"
parent: "0008"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:266"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

fix the header logo/home link (`lib_docmodel.py::render_page`, key `"home": prefix + "index.html"`): it reuses the site-root-relative `prefix` (correct for shared assets like `style.css` that exist once at the tree root) instead of the language-root-relative depth used by `nav_html`'s breadcrumb "Start" link, so on every non-German page the logo link jumps one level too far up into the German root `index.html` instead of staying in `<lang>/index.html` (found 2026-08-13 via nl screenshot, `ara::log` namespace page) -- DONE 2026-08-13: added a separate `lang_prefix` (page-file-depth `../` levels, without the +1 language-subdir offset used by the shared-asset `prefix`) and used it only for the `home` template key; German canonical output unaffected since both prefixes coincide when lang==KANONISCH. Verified on sample nl pages that the home link now has one fewer `../` than the style.css link and resolves within the nl/ tree. All language trees rebuilt via `generate.py --lang=alle`. REF: 38459c13

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
