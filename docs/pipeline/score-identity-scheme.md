# Eclipse S-Core `kind`/ID-Minting Convention (0009-01)

Status: DECIDED 2026-08-14. Layered on the canonical identity scheme from
**0006-02** (`project/kind/id`), which 0009-01 could not directly inherit
because S-Core is a live codebase, not a PDF spec, with no upstream
`SWS_xxx`-style source ID to anchor on.

## Motivating problem

Unlike AUTOSAR AP records, Eclipse S-Core units have no existing
`kind`/ID convention to inherit. This document fixes the enumerated `kind`
values, the deterministic derivation rule from repo/component to `id`, and
stability rules across renames/refactors, so **0009-02/03/05/06** can
proceed.

## Research basis

S-Core already exposes three overlapping identity mechanisms in its own
tooling and docs, which are reused here instead of inventing a new scheme:

- **GitHub repo name** — S-Core is organized as ~37+ separate repos under
  `eclipse-score/` (e.g. `communication`, `feo`, `tooling`), one per
  architectural unit.
- **Bazel module name** — every repo declares `module(name = "...")` in
  `MODULE.bazel`; this is S-Core's own build-time canonical identity,
  globally unique via the `bazel_registry`, and referenced by every
  downstream `bazel_dep`.
- **Sphinx-needs IDs** — the `process_description` and module docs use
  `sphinx-needs` with typed, prefixed, regex-validated IDs
  (`needs_id_regex`, optional `id_prefix`) for requirements, architecture
  elements, and work products.

## Pinned design decisions

### `kind` taxonomy

| `kind` | Definition | ID derivation |
|---|---|---|
| `module` | Top-level architectural building block = one GitHub repo | `MODULE.bazel` `name` field; fallback to GitHub repo slug if absent |
| `component` | Sub-unit inside a module, mapped to a Bazel package | Repo-relative Bazel package path, `/` normalized to `.` (e.g. `communication.mw.com`) |
| `design-doc` | Sphinx-needs work product (requirement, architecture spec, safety case, ...) | The existing sphinx-needs ID verbatim — not re-minted |
| `process-doc` | Content from the `process_description` repo (workflows, roles, glossary) | Its sphinx-needs ID, or repo-relative doc path if untagged |

Canonical identity format follows **0006-02** unchanged:
`ECLIPSE/S-CORE/<kind>/<id>`, e.g.:

- `ECLIPSE/S-CORE/module/communication`
- `ECLIPSE/S-CORE/component/communication.mw.com`
- `ECLIPSE/S-CORE/design-doc/<sphinx-needs-id>`

### Why Bazel module name over GitHub repo name for `module`

Bazel module names are S-Core's own dependency-resolution identity
(used in every `bazel_dep`), so they are treated as globally unique and
change far less often than repo names or file paths — renaming one would
break every downstream dependency declaration. This gives near-AUTOSAR-
grade stability without a custom persistence layer.

### Stability across renames/refactors

- `module`: anchor on Bazel module name (rename-resistant by construction,
  see above).
- `component`: anchor on Bazel package path, matching the same unit
  developers already target via `bazel build //<pkg>/...`. As a fallback
  for components without their own Bazel target, record the repo's
  GitHub `node_id` (immutable, rename-proof) as a secondary stable
  anchor.
- `design-doc` / `process-doc`: no re-derivation — ingest the sphinx-needs
  ID as-is, since S-Core already enforces uniqueness/regex validation on
  these IDs. Store the sphinx-needs `type` as a sub-field on the record.

## Non-goals of this task

- Does not define how content changes are tracked over time for S-Core
  (commit hash / tag / release branch) — that is **0009-04**, still open.
- Does not implement the scraper, registry entries, curation mapping, or
  validation checks — those are **0009-02/03/05/06**, now unblocked.
