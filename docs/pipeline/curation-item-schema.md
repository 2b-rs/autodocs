# Unified Curation-Item Schema (curation-item@v1)

Status: defined 2026-08-13 for **0006-03**. Subsumes `review-flag@v1`
(`_src/tools/review_flags.py`) and `curation-flag@v1`
(`_src/tools/curation_flags.py`), which remain the on-disk writers for now;
`_src/tools/curation_item.py` provides read-side adapters that normalize
both into this shape. A future task may migrate the writers themselves.

## Fields

| Field | Type | Notes |
|---|---|---|
| `schema` | string | Always `"curation-item@v1"`. |
| `canonical_id` | string | `project/kind/id` from **0006-02**, e.g. `AUTOSAR/AP/record/SWS_UCM_00348`. |
| `project` | string | e.g. `AUTOSAR/AP`. Derived from `canonical_id`. |
| `release` | string \| null | AUTOSAR release the item pertains to, if known. Not part of `canonical_id` (0006-02 is release-free). |
| `item_kind` | enum | `record-field` \| `record` \| `ai-amendment` \| `ai-hypothesis` \| `scrape-observation` \| `report-entry`. |
| `origin` | enum | `tool` \| `ai` \| `browser` \| `curator`. |
| `status` | enum | `open` \| `claimed` \| `proposed` \| `accepted` \| `rejected` \| `superseded` \| `applied`. |
| `subject` | string | Human-readable one-line description of what is being curated. |
| `current_state` | any | The value/text as currently recorded. |
| `proposed_state` | any | The value/text being proposed, if any. |
| `evidence` | list | Supporting evidence for the proposal. |
| `counter_evidence` | list | Evidence against the proposal, if any. |
| `decision_basis` | object | Structured rationale/screenshot/deep-link basis for a decision. |
| `campaign` | string | Campaign/batch this item belongs to. |
| `created` | string (ISO 8601) | Creation timestamp. |
| `claimed_by` | string \| null | Agent/operator who claimed the item. |
| `decided_by` | string \| null | Agent/operator/curator who decided. |
| `completed_at` | string (ISO 8601) \| null | Completion timestamp. |
| `history` | list | Append-only list of prior state transitions. |

## Worked examples

### (a) Scrape ambiguity
Adapted from `review-flag@v1`: `item_kind="scrape-observation"`,
`origin="tool"`, `status="open"`, `subject` derived from `reason`
(e.g. `missing_space_suspects`), `evidence` from `finding.suspects`/`finding.repairs`.

### (b) DB-value correction
Adapted from `curation-flag@v1` with `outcome="accepted"`:
`item_kind="record"`, `origin="curator"`, `status="accepted"`,
`decision_basis` copied verbatim, `decided_by` from `decided_by`.

### (c) AI-generated amendment to an existing record
`item_kind="ai-amendment"`, `origin="ai"`, `status="proposed"`;
`current_state`/`proposed_state` hold before/after text; `evidence` cites
the requirement-version pinned per future **0006-17**.

### (d) AI-proposed new spec element (`hypothesized/unconfirmed`)
`item_kind="ai-hypothesis"`, `origin="ai"`, `status="proposed"`;
`current_state=null` (no existing record); `proposed_state` holds the
hypothesized element text.

## Non-goals of this task

Does not migrate `review_flags.py`/`curation_flags.py` writers, does not
change on-disk queue file layout, and does not implement the graph/version
concepts from 0006-15 through 0006-22 — those remain separate follow-on
tasks that build on this schema.
