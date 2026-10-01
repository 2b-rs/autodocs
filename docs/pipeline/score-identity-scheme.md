# Eclipse S-Core `kind`/ID-Minting Convention (0009-01) and Version Tracking (0009-04)

Status: DECIDED 2026-08-14 (0009-01), DECIDED 2026-08-14 (0009-04). Layered
on the canonical identity scheme from **0006-02** (`project/kind/id`),
which 0009-01/0009-04 could not directly inherit because S-Core is a live
codebase, not a PDF spec, with no upstream `SWS_xxx`-style source ID or
AUTOSAR-style discrete release to anchor on.

## Motivating problem

Unlike AUTOSAR AP records, Eclipse S-Core units have no existing
`kind`/ID convention to inherit, and no discrete "release" concept
comparable to AUTOSAR SWS releases. This document fixes (a) the
enumerated `kind` values and deterministic derivation rule from
repo/component to `id`, with stability rules across renames/refactors
(0009-01), and (b) how S-Core content changes are tracked over time as
the S-Core equivalent of the AUTOSAR `@rel:<release>#<content-hash8>`
version ID from **0006-15** (0009-04). Together these unblock
**0009-02/03/05/06**.

## Research basis (0009-01)

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

## Pinned design decisions (0009-01)

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

## Pinned design decision (0009-04): version tracking over time

### Why a Git commit hash cannot be the canonical version axis

A raw commit SHA is excellent **provenance evidence** but the wrong
**canonical integration boundary**: rebasing, squashing, mirroring, or
importing an S-Core repository into another repository changes the commit
DAG identity while the logical specification release may be unchanged.
Since this system's amendment/curation/supersession machinery pins
decisions and evidence to a version ID, coupling that ID to a mutable
commit graph would silently invalidate amendments whenever a repository is
relocated, mirrored, or absorbed — unacceptable for a system built around
stable, addressable spec-element identity.

### Decision: release tags first, release branches second, commit hash as provenance only

Use a **release label** as the canonical version axis, with priority:

1. **Annotated release tag** — preferred whenever S-Core publishes one.
2. **Named release/maintenance branch** — used when no qualifying tag
   exists.
3. **No synthetic rolling version** — an untagged development branch is
   scrapeable only when explicitly requested, and must be labeled as a
   non-release snapshot, never treated as a canonical published release.

Canonical S-Core version IDs follow the existing AUTOSAR-compatible
format from **0006-15** unchanged:

```
ECLIPSE/S-CORE/<kind>/<id>@rel:<release-label>#<content-hash8>
```

Examples:

```
ECLIPSE/S-CORE/module/communication@rel:2026.1#a1c9f3e2
ECLIPSE/S-CORE/component/communication.mw.com@rel:release/2026.1#f0e1d2c3
```

This lets existing amendment, curation, evidence, and supersession
machinery treat S-Core exactly like any other release-bearing corpus,
without special-casing.

### Provenance metadata (non-canonical)

Each scraped record additionally carries provenance fields that do **not**
participate in the canonical ID, so relocation/mirroring of the source
repo never breaks stable IDs:

| Field | Meaning |
|---|---|
| `source_repo_origin` | Logical upstream/project source, not merely the current hosting URL |
| `source_ref_kind` | `tag` or `release-branch` |
| `source_ref` | The selected tag or immutable release-branch name |
| `source_commit` | Full resolved Git SHA, for exact reproducibility of the scrape input |
| `source_repo_url` | Current fetch location |
| `source_path` | Path within the repo at the captured release |

### Ref migration rule

If a release branch is later converted to a tag, the original
`@rel:<branch-name>` version is retained as an alias/supersession-
compatible source reference rather than silently rewritten. New ingestion
may prefer the tag only if it resolves to the same content (same
`content_hash8`); otherwise it is a distinct release snapshot.

## Non-goals of this task

- Does not implement the scraper, registry entries, curation mapping, or
  validation checks — those are **0009-02/03/05/06**, now unblocked.
- Does not define what constitutes a qualifying "release" for repos that
  publish neither tags nor named branches; such repos are out of scope for
  canonical versioning until the project adopts a release process, and are
  scraped (if at all) only as explicitly-labeled non-release snapshots per
  rule 3 above.
