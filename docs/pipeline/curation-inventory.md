# Curation-Surface Inventory and Classification (Feature 0006-12)

Status: implemented 2026-08-13. Tool: `_src/tools/curation_inventory.py`
(read-only; classifies, does not migrate or delete any scanned file).

## Inventory (counts as of implementation day)

| Category | Classification | Count | Rule |
|---|---|---|---|
| `review-queue` (open) | `first_class` | 349 | Live pending decisions; already losslessly normalized read-only by `curation_item.from_review_flag()` (0006-03). |
| `curation-queue` (open) | `first_class` | 34 | Live pending decisions; already losslessly normalized read-only by `curation_item.from_curation_flag()` (0006-03). This category IS the "34 service-method namespace conflict" the 0006-12 task text names -- confirmed by campaign `2026-08-service-method-namespace-deviation-review` on every one of its 34 open items. |
| `extraction_report.RESIDUAL` | `report_only` | 3 | Finished code-level decisions baked into extraction logic itself, not pending items awaiting a lifecycle state. |
| SWS_LOG `requirement_meta.review_*` | `historical_archive` | 47 | Predates the unified model; the pilot campaign (`2026-08-sws-log-pilot-after-tool-improvement`, see 0006-08's backfilled manifest) already completed for this module. |

## Why no data was physically migrated

`review-queue`/`curation-queue` were classified `first_class` precisely
BECAUSE `curation_item.py`'s 0006-03 read adapters already normalize them
losslessly and non-destructively on read -- rewriting the on-disk
`review-flag@v1`/`curation-flag@v1` files into a different physical format
would add risk (383 real files, some campaigns still open) without changing
what any consumer sees. "Migrate into the unified model" is satisfied by the
read-normalization already shipped in 0006-03, not by a file rewrite.

`RESIDUAL` and the SWS_LOG pilot fields were classified out of
`first_class` precisely because they are not live decisions with an open
lifecycle state -- there is nothing to migrate them INTO; they remain
where they are, referenced from this inventory as findings.

## Non-goals of this task

Does not build the 0006-09 curation report itself (that consumes this
classification as an input once its own PREREQs, 0001-08, are met). Does
not alter any RESIDUAL entry, queue file, or SWS_LOG record.
