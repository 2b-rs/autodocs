---
schema_version: "1.0"
id: "0006-03"
level: "task"
parent: "0006"
state: "closed"
visibility: "internal"
prerequisites:
  - "0006-02"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:140"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0006-03:0006-02 — define one unified "curation item" schema that subsumes `review-flag@v1` and `curation-flag@v1` — REF: 1ac5f141 — implemented as read-side adapters in `_src/tools/curation_item.py` (`from_review_flag()`/`from_curation_flag()`) plus `docs/pipeline/curation-item-schema.md`; existing writers unchanged, unblocks 0006-15.

## Scope

- Current gap: `review_flags.py` and `curation_flags.py` are near-duplicate but divergent queues with different payload shapes, different directory trees, and different semantics.
  - Design a single schema with at least: `schema`, `canonical_id`, `project`, `release`, `item_kind` (record-field / record / ai-amendment / ai-hypothesis / scrape-observation / report-entry), `origin` (tool / ai / browser / curator), `status` (open / claimed / proposed / accepted / rejected / superseded / applied), `subject`, `current_state`, `proposed_state`, `evidence`, `counter_evidence`, `decision_basis`, `campaign`, `created`, `claimed_by`, `decided_by`, `completed_at`, and `history`.
  - Make the schema expressive enough to represent: (a) scrape ambiguities, (b) DB-value corrections, (c) AI-generated amendments to existing records, (d) AI-proposed new spec elements / requirements currently only described as `hypothesized/unconfirmed` in the process docs.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.
