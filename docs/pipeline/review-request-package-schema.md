# Website Review-Request Package Schema (`review-request-package@v1`) — 0021-02

Status: drafted for **0021-02**. PREREQ: 0021-01 (`website-review-flag.md`).
Consumed by `0021-03` (ingestion boundary) and `0021-04`/`0021-05`
(record-page UX/implementation).

## Design decision carried over from 0021-01's open questions

`item_kind` gets a new enum value **`review-request`**, distinct from
`record`/`ai-amendment`/`ai-hypothesis`/`scrape-observation`/`report-entry`
(`curation-item-schema.md`). Rationale: a review-request has no
`proposed_state` at submission time — unlike an `ai-amendment`, the
requester is not proposing a replacement value, only asking that the
existing `current_state` be re-examined against external evidence. Reusing
`item_kind="record"` would conflate "here is a concrete fix" with "please
look at this again," which is exactly the ambiguity `0021-01`'s non-bypass
rule 3 forbids.

## Two distinct identities (0021-01 role split)

Per `0021-01`, a submitted package has **two separate identity concepts**
that must never be merged into one field:

1. **Actor claim** (`actor_claim`) — what the requester *says* about
   themselves. Always present, always `self_declared` in isolation.
2. **Authoritative trust context** (`trust`) — derived exclusively by the
   *transport*, never by the browser package itself: a GitHub Issue
   transport lets the ingestion tool read the actual authenticated Issue
   author from the GitHub API/webhook payload; a JSON-download/export
   transport has no authoritative identity and MUST be treated as
   `self_declared` regardless of what `actor_claim` says. This mirrors the
   existing `review.js` distinction between `github_authenticated` and
   `self_declared` (`review.js`, `VALID_IDENTITY` in `curation_ingest.py`)
   and closes the spoofing gap: the package itself can never assert its own
   authentication level.

## Deterministic request identity

```
request_id = "review-request:" + uuid7()
```

Uses the existing `uuid7()` generator (`version_id.py`) for time-sortable,
collision-safe IDs consistent with `curation:<uuid7>` / `evidence:<uuid7>`.
The request ID is client-generated (at submission time in the browser) so
resubmission after a transport failure is detectable: same `request_id`
submitted twice is a **retry**, not a duplicate concern (see De-duplication).

## Schema fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema` | string | yes | Always `"review-request-package@v1"`. |
| `client_schema_version` | string | yes | Semver of the client code that produced the package (e.g. `"1.0.0"`); lets `0021-03` reject packages from a known-broken client build. |
| `request_id` | string | yes | `review-request:<uuid7>`, client-generated. |
| `target_canonical_id` | string | yes | `project/kind/id` per `canonical_id.py`, e.g. `AUTOSAR/AP/record/SWS_TSYNC_00123`. |
| `target_version_id` | string \| null | yes (null only if pre-0006-17 record has no minted version) | `<canonical-id>@rel:<release>#<hash8>` per `version_id.requirement_version_id()`. |
| `target_content_hash` | string | yes | `hash8` (first 8 hex of SHA-256) of the exact rendered content the requester saw, per `version_id.content_hash8()`. Independent of `target_version_id` so staleness can be detected even for un-versioned legacy records (see Staleness). |
| `target_status_snapshot` | string | yes | The record's `status.state` at submission time (`status-model.md` enum), e.g. `"valid/ai-decided"`. Never re-derived later — frozen at submission. |
| `source_url` | string (URL) | yes | Deep link to the published page/section the requester was viewing. |
| `category` | enum | yes | `"factual-accuracy"` \| `"outdated-source"` \| `"missing-context"` \| `"ai-hallucination-suspected"` \| `"other"`. |
| `rationale` | string | yes | Free-text requester explanation; non-empty. |
| `evidence_refs` | list of object | no | Each: `{"kind": "url"\|"citation"\|"field-ref", "value": string, "note": string\|null}`. External evidence (e.g. an AUTOSAR errata link) lives here — never inline-merged into `rationale`. |
| `actor_claim` | object | yes | `{"display_name": string, "identity_kind": "github_authenticated"\|"self_declared"}`. This is the requester's *assertion*; see Two distinct identities. |
| `created_at` | string (ISO 8601 UTC) | yes | Client-side submission timestamp. |
| `transport` | enum | yes | `"github_issue"` \| `"json_export"`. Set by the client depending which submission path was used; does not itself grant trust (see Two distinct identities). |

## Fields the ingestion tool adds (never present in the client package)

| Field | Set by | Notes |
|---|---|---|
| `trust.identity_kind` | `0021-03` ingestion tool | `github_authenticated` only if derived from the GitHub API/webhook, else forced to `self_declared` regardless of `actor_claim`. |
| `trust.authoritative_actor` | `0021-03` ingestion tool | The verified GitHub login for `github_issue` transport; `null` for `json_export`. |
| `received_at` | `0021-03` ingestion tool | Server-side ingestion timestamp. |

Keeping these two groups separate in this table is itself a normative
requirement: `0021-03`'s tests must assert the client-supplied fields and
the ingestion-derived fields are never sourced from the same input.

## Canonical serialization (for identity/de-duplication)

De-duplication and stale-hash comparisons operate on a canonical JSON
serialization: keys sorted lexicographically, no insignificant whitespace,
UTF-8, and `evidence_refs` order-preserved (order is meaningful — it is the
requester's own ordering, not a set). `0021-03` de-duplicates on
`(target_canonical_id, target_version_id_or_hash)`, not on `request_id`
(two different `request_id`s can legitimately target the same record).

## Staleness rule

A package is **stale** if `target_content_hash` does not match the
record's current content hash **and** `target_version_id` (if present)
does not match the record's current `decided_on_version`. Both must
mismatch for a hard rejection; a `target_version_id` match with a
`target_content_hash` mismatch is treated as a soft warning (content
rendering changed without a new version being minted), forwarded to the
Kurator rather than rejected outright.

## Duplicate rule

An **open** review-request queue item already exists for the same
`target_canonical_id`: the new submission is rejected as `duplicate`,
pointing the user to the existing (public, non-sensitive) queue-item
reference — consistent with `curation_flags.write_curation_flag`'s existing
"a bereits offene Anfrage bleibt fuehrend" rule (`curation_flags.py`).

## Sensitive fields and retention

- `actor_claim.display_name` for `self_declared` transport is retained
  verbatim but always rendered with the existing lower-confidence warning
  text (mirrors `review.js`'s `warn` string).
- `trust.authoritative_actor` (GitHub login) is retained as long as the
  curation item exists; deleted along with the item on `complete_flag()`
  per the existing queue-file lifecycle (nothing new here — 0021 does not
  change queue retention).
- No IP address, session token, or browser fingerprint is ever included in
  the schema; the GitHub Issue/webhook is the sole authentication artifact
  for `github_issue` transport.

## Transport equivalence

Both `github_issue` and `json_export` carry the **identical** semantic
package above; only `transport` and the resulting `trust.*` derivation
differ. This satisfies 0021-02's Definition of Done requirement that
"the same semantic package supports GitHub-Issue submission and JSON
export/later transfer without conflating their lifecycle states" —
`json_export` packages sit outside any queue until a human manually
re-submits them through the GitHub path; they are never auto-ingested.

## Worked example (valid, github_issue)

```json
{
  "schema": "review-request-package@v1",
  "client_schema_version": "1.0.0",
  "request_id": "review-request:018f2e1a-7b3c-7c21-9a4e-2f6b1d8c9a01",
  "target_canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
  "target_version_id": "AUTOSAR/AP/record/tsync-user-guide@rel:R25-11#3f9a21bc",
  "target_content_hash": "3f9a21bc",
  "target_status_snapshot": "valid/ai-decided",
  "source_url": "https://example.org/en/modules/tsync.html#user-guide",
  "category": "ai-hallucination-suspected",
  "rationale": "The AI guide states 'always monotonic' but the cited SWS section only guarantees monotonicity for OffsetTime, not RawTime.",
  "evidence_refs": [
    {"kind": "citation", "value": "SWS Time Synchronization §7.3.2", "note": "RawTime exception"}
  ],
  "actor_claim": {"display_name": "jdoe", "identity_kind": "github_authenticated"},
  "created_at": "2026-08-15T07:40:00Z",
  "transport": "github_issue"
}
```

## Worked example (invalid — missing rationale, wrong schema tag)

```json
{
  "schema": "curation-request@v1",
  "target_canonical_id": "AUTOSAR/AP/record/tsync-user-guide",
  "rationale": ""
}
```

Rejected for: wrong `schema` value, empty `rationale`, and missing
`request_id`/`target_content_hash`/`target_status_snapshot`/`actor_claim`/
`created_at`/`transport`.

## Deterministic-ID fixture

Given canonical id `AUTOSAR/AP/record/tsync-user-guide`, release `R25-11`,
and content `"Global time as a service for applications..."`, the pinned
`content_hash8()` algorithm (`version_id.py`) must always yield the same
8 hex characters for the same input — this determinism is what `0021-03`'s
stale-hash comparison relies on and must be covered by a fixture test.
