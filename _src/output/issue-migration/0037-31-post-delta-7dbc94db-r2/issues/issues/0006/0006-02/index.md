---
schema_version: "1.0"
id: "0006-02"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:128"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

introduce a project-aware canonical identity scheme for every curatable item — REF: 3a2bc7be — `project`/`kind` design resolved 2026-08-13; `projects.json` registry (0006-02.01, REF: 9daffda4) and propagation into record queues (`review_flags.py`/`curation_flags.py`), ingest (`review_ingest.py`/`curation_ingest.py`), campaign manifests (`spec_extraction_campaign.py`), and HTML anchors (`lib_docmodel.py`) implemented additively via new `_src/tools/canonical_id.py`, backward-compatible default `AUTOSAR/AP`/`record` for all pre-existing bare-id call sites; 72 existing tests pass unchanged, plus new roundtrip/registry/smoke/backward-compat checks. Eclipse S-Core's concrete `kind`/ID-minting convention is OUT OF SCOPE here — uncoupled 2026-08-13 into Feature 0009 ("Eclipse S-Core Corpus Scraping").

## Scope

- Current gap (2026-08-12): records and queues are implicitly single-project (`_src/spec/records/<MODULE>/<ID>.json`, queue filenames = `<ID>.json`), and the docs contain no evidence of multi-project support for future AUTOSAR Classic / FOUNDATION / Eclipse S-Core expansion.
  - RESOLVED design (2026-08-13, supersedes the release-inclusive draft below): canonical identity is **release-free** — `project/kind/id`, e.g. `AUTOSAR/AP/record/SWS_UCM_00348`, `AUTOSAR/FOUNDATION/record/RS_SAF_00001`, `ECLIPSE/S-CORE/module/<id>`. Release only ever appears inside the separate version ID from **0006-15** (`<canonical-id>@rel:<release>#<content-hash8>`), never in the canonical key itself — otherwise the same requirement in two releases would be two unrelated identities and supersession tracking breaks.
  - `project` values are namespaced two-level strings registered in one place (see **0006-02.01**), not left implicit in code: `AUTOSAR/AP`, `AUTOSAR/CP`, `AUTOSAR/FOUNDATION`, `ECLIPSE/S-CORE`.
  - `kind` is an open, documented enum, not fixed to `record`: AP/CP/Foundation use `record` (document-extracted requirement); Eclipse S-Core is a live codebase, not a PDF spec, so its curatable units (module, component-interface, design-doc, ...) need their own `kind` values and their own ID-minting convention (e.g. derived from repo path/component name) since there is no upstream "SWS_xxx"-style source ID to inherit.
  - Superseded original wording (kept for history): canonical key was originally drafted as `project/release/kind/id` (example dimensions: `AUTOSAR/AP/R25-11/record/SWS_UCM_00348`, `AUTOSAR/FOUNDATION/R25-11/record/RS_SAF_00001`, `ECLIPSE/S-CORE/<release>/record/<id>`); superseded 2026-08-13 for the release-free scheme above.
  - Ensure the raw record `id` can remain human-familiar while the canonical identity becomes the cross-project stable key for queues, history, links, and reports.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
