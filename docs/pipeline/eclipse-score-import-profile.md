# Eclipse S-Core v0.6.0 import profile

**Profile:** `_src/spec/import-profiles/eclipse-score-v0.6.0.json` (`score-import-profile@v1`, profile version `1.0.0`)
**Validator/evaluator:** `_src/tools/score_import_profile.py`
**Scope:** Task `0019-03`; this is an import contract, not an extraction run, a source snapshot, a queue writer, or a curator decision.

## Purpose and authority boundary

This profile defines the only source shapes which a later S-Core importer may
turn into candidates for the release-pinned v0.6.0 campaign. It is deliberately
strict: a candidate which is structurally usable still starts as
`invalid/to-be-confirmed`, with source-locator traceability and a curation draft.
It is never silently made factual or published.

The profile binds exactly the complete `score-source-bom@v1` in
`_src/spec/campaigns/eclipse-score-v0.6.0.json`:

| Repository | Accepted tag | Resolved commit | Content root |
| --- | --- | --- | --- |
| `score` | `v0.6.0` | `db1f5bb87ad7f41b40b6aca4b96a889d8798735e` | `docs` |
| `process_description` | `v1.6.0` | `04e9cd30bc657033a764dbb75f07e03e4ccbbc12` | `process` |

Both are tags. `main`, `HEAD`, a branch, a short SHA, a source URL/ref/commit
that differs from this table, and a fallback after a source failure are rejected.
The validator compares the bindings to the BOM when called with `--bom`.

### Identity-metadata boundary

The identity convention requires `MODULE.bazel` and Bazel package markers for
`module` and `component`, while the BOM's imported documentation roots are
`docs` and `process`. Therefore the `score` selectors may read only
`MODULE.bazel` and **non-root** `BUILD`/`BUILD.bazel` files as identity metadata.
They do not widen the imported documentation content root, authorize a general
code scan, or alter the BOM. The pinned archive hash already covers the complete
repository; Task `0019-02` remains solely responsible for controlled snapshot
retention and inventory linkage of these locators.

## Supported source classes and field mapping

Each raw candidate supplies the common pinned-source fields: `repository`,
`repository_url`, `release_ref`, `ref_kind`, `resolved_commit`, a bounded
`locator` (`path`, `line_start`, `line_end`, `anchor`), and a 64-hex
`source_content_sha256`. The digest is source evidence; minting the normalized
record content hash and version ID remains Task `0019-05` work.

| Source class and selector | Target `kind` | Required source fields | Canonical ID mapping |
| --- | --- | --- | --- |
| `score-module-manifest`: exact `score/MODULE.bazel` | `module` | `module_name`, `title` | `ECLIPSE/S-CORE/module/<module_name>` |
| `score-bazel-package`: non-root `score/**/BUILD` or `BUILD.bazel` | `component` | `module_name`, `package_path`, `title` | `ECLIPSE/S-CORE/component/<module_name>.<package_path with / → .>` |
| `score-design-need`: a Sphinx-needs item in `score/docs/**/*.rst` or `.md` | `design-doc` | `need_id`, `need_type`, `title` | `ECLIPSE/S-CORE/design-doc/<need_id>` |
| `process-sphinx-need`: a Sphinx-needs item in `process_description/process/**/*.rst` or `.md` | `process-doc` | `need_id`, `need_type`, `title` | `ECLIPSE/S-CORE/process-doc/<need_id>` |

The documentation selectors recognize both reStructuredText (`.. <type>::`)
and MyST fenced (` ```{<type>}`) Sphinx-needs forms. `need_id` must be explicit,
match the locator anchor, and match `[A-Za-z][A-Za-z0-9_.-]*`; no synthetic ID
is generated.

The evaluator maps title, optional description, canonical identity, and full
source provenance into a **candidate record**. It deliberately leaves
`version_id` as deferred to `0019-05`. For documentation items it preserves the
upstream `need_type` as `sphinx_need_type`.

## Defaults, traceability, and curation hand-off

The profile’s candidate-record default is:

```json
{
  "status": {
    "state": "invalid/to-be-confirmed",
    "reason": "release-pinned S-Core source requires curation before factual publication",
    "campaign": "eclipse-score-v0.6.0"
  }
}
```

Every candidate has locator traceability to the repository URL, tag, resolved
commit, path, line range, anchor, and source digest. The materializing importer
must add a real append-only history entry (including the import date) from the
profile’s history template; it must not replace historical entries.

A non-rejected evaluation returns a `curation-item@v1` **draft** at lifecycle
state `discovered`. It is not a physical queue file and does not claim that an
item is already `queued`: Task `0019-07` owns the canonical writer and the
`discovered → queued` transition. A draft uses the registered `score-scraper`
origin and names the condition that caused it. This preserves the separation
between source classification and a curator decision.

## Decisions, rejection, review, and queue conditions

The stable condition IDs in the JSON profile are exhaustive and are all tested.

| Condition | Decision | Result |
| --- | --- | --- |
| `REJECT-UNSUPPORTED-SOURCE-CLASS` | reject | No record or work item; the class is outside the four supported shapes. |
| `REJECT-MOVING-REF` | reject | No fallback from a moving or non-tag ref. |
| `REJECT-SOURCE-PIN` | reject | No candidate when repository URL, tag, or commit differs from the BOM binding. |
| `REJECT-INVALID-LOCATOR` | reject | No candidate for absent, absolute, traversal, or unbounded locator data. |
| `REJECT-SELECTOR-MISS` | reject | No candidate for a locator outside the declared class selector. |
| `QUEUE-MISSING-MANDATORY-FIELD` | queue | A `discovered` curation draft records missing required source data or digest. |
| `REVIEW-MALFORMED-NEED-ID` | review | A `discovered` review draft records an absent/malformed/mismatched explicit Sphinx-needs ID. |
| `REVIEW-DUPLICATE-CANONICAL` | review | A `discovered` review draft records an already-observed canonical identity. |
| `REVIEW-CONFLICTING-CANONICAL` | review | A `discovered` review draft records contradictory content/provenance for one canonical identity. |
| `QUEUE-INITIAL-CURATION` | queue | A structurally valid candidate still requires curation before it can obtain a valid status or publication. |

The evaluator never overwrites, deduplicates, accepts, rejects on a curator’s
behalf, writes any queue directory, or marks a `valid/*` status.

## Pinned source examples and fixture coverage

`_src/tests/fixtures/score_import_profile/positive-artifacts.json` retains
compact source-backed examples from the two pinned repositories:

| Target kind | Repository and locator | Pinned source evidence |
| --- | --- | --- |
| `module` | `score/MODULE.bazel` | `module(name = "score_platform")` at `db1f5bb…` |
| `component` | `score/tools/format/BUILD` | non-root Bazel package at `db1f5bb…` |
| `design-doc` | `score/docs/design_decisions/DR-001-infra.md` | MyST `dec_rec__infra__dev_tools` at `db1f5bb…` |
| `process-doc` | `process_description/process/roles/index.rst` | `rl__project_lead` at `04e9cd…` |

The associated source-file SHA-256 values and short excerpts make the fixtures
hermetic. They are profile samples only, not Task `0019-02`’s controlled source
snapshot. `decision-cases.json` exercises every table row, including all reject,
review, and queue outcomes.

## Contract review against shared lifecycle documents

- [`score-identity-scheme.md`](score-identity-scheme.md) supplies the exact four
  kinds, the Bazel module/package identity derivation, verbatim Sphinx-needs
  IDs, release-free canonical IDs, and tag/commit provenance distinction.
- [`data-model.md`](data-model.md) supplies the record/provenance/status/history
  shape and requires the unified `curation-item@v1` model rather than an S-Core
  queue format.
- [`status-model.md`](status-model.md) supplies the non-publishable
  `invalid/to-be-confirmed` default, the `valid/*` publication constraint, and
  append-only history rule.
- [`processes.md`](processes.md) supplies source traceability, the rule that
  missing evidence is not agreement, and the `discovered → queued → claimed →
  proposed → accepted/rejected → applied → published` lifecycle. The profile
  only creates discovered drafts and cannot skip later curation or Phase 6.

## Explicit non-goals

This profile does **not** implement a manifest-driven extractor (`0019-04`), a
controlled snapshot/inventory (`0019-02`), normalized record/version materialization
(`0019-05`), validation/reporting (`0019-06`), physical queue integration
(`0019-07`), curation decisions, publication, an undocumented-API inference,
production certification, or an Automotive SPICE capability claim. It also does
not use the legacy `score_scrape.py` default of `main`; later adapters must pass
only the profile-pinned tag and commit.

## Validation

```sh
python3 _src/tools/score_import_profile.py \
  _src/spec/import-profiles/eclipse-score-v0.6.0.json \
  --bom _src/spec/campaigns/eclipse-score-v0.6.0.json
python3 _src/tests/test_score_import_profile.py
```
