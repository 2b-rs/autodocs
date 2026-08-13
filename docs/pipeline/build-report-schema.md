# Build-Report Schema (i18n + HTML Publication Runs)

Status: canonical schema definition (TASK 0001-01). Producers (i18n_translate.py,
i18n_diagrams.py, generate.py, validate.py) are extended to emit conforming
reports in follow-up tasks 0001-03..0001-06. This document defines the schema
only; it does not by itself change any producer's behavior.

## Envelope (common to every producer)

Every build-report JSON document has this top-level envelope:

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Schema version, e.g. `"1.0"`. Bump on breaking changes. |
| `report_kind` | string | One of `i18n_merge`, `i18n_diagrams`, `html_generate`, `validate`, `combined`. |
| `tool` | string | Script/module name that produced the report, e.g. `i18n_translate.py`. |
| `command` | string | Full invoked command line (argv, joined), for reproducibility. |
| `inputs` | array[string] | Paths/identifiers of inputs consumed (e.g. batch files, source PDFs, language code). |
| `started_at` | string | ISO-8601 UTC timestamp, run start. |
| `finished_at` | string | ISO-8601 UTC timestamp, run end. |
| `duration_s` | number | Wall-clock duration in seconds (finished_at - started_at). |
| `exit_code` | integer | Process exit code of the producing run. |
| `changed_artifacts` | array[string] | Paths of files created/modified/deleted by this run. |
| `counts` | object | Producer-specific counters (see below); always present, may be `{}`. |
| `findings` | array[object] | Structured findings/issues, each `{category: string, severity: "info"|"warning"|"error", message: string, ref?: string}`. Empty array if none. |
| `run_archive_ref` | string\|null | Path to the `run.sh` + `.log` pair that produced this report, if run via the local runner (links to 0001-09's traceability). |

## Producer-specific `counts` fields

| `report_kind` | `counts` fields |
|---|---|
| `i18n_merge` | `batches_consumed`, `accepted`, `rejected`, `register_changes` |
| `i18n_diagrams` | `sources_considered`, `translated_written`, `unchanged_skipped`, `stale_deleted` |
| `html_generate` | `pages_generated_per_lang` (object: lang -> int), `fallback_to_german` (object: lang -> int), `changed_targets` |
| `validate` | `checks_performed`, `findings_by_category` (object: category -> int), `success` (bool) |
| `combined` | union of the above under `by_stage` (object: report_kind -> counts object), plus `overall_success` (bool) |

## Conventions

- All reports are UTF-8 JSON, one document per run (no NDJSON).
- `findings` categories are free-form strings but SHOULD be stable, kebab-case identifiers (e.g. `missing-namespace`, `stale-svg`) so 0001-06's category grouping and future automation can group on them reliably.
- A report with `exit_code != 0` MUST have at least one `findings` entry with `severity: "error"` explaining the failure.
- Where a run's output is intended to be published into the HTML tree (0001-08), the report MUST additionally set `run_archive_ref`.
- This schema is deliberately producer-agnostic at the envelope level so 0001-07's combined report can merge N producer reports without bespoke per-tool glue.
