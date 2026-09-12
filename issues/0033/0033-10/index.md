---
schema_version: "1.0"
id: "0033-10"
level: "task"
parent: "0033"
state: "closed"
visibility: "internal"
prerequisites:
  - "0033-03"
  - "0033-04"
  - "0033-04.01"
  - "0033-05"
  - "0033-09"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:893"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
  - id: "AC-005"
    status: "active"
  - id: "AC-006"
    status: "active"
---

## Goal

PREREQ: 0033-10:0033-03, 0033-10:0033-04, 0033-10:0033-04.01, 0033-10:0033-05, 0033-10:0033-09 Implement a browser package builder that exactly matches the strict schema and reuses the confirmed request for export, submission, and retry.

## Scope

Claim: `DONE-quark-0033-10-20260901.md`; owner_token:
  `agent:quark:0033-10:1788266728784-07f50cb1`.
  - **Acceptance:** ✓
    - **Disposition:** `completed`
    - **Accepted by:** `obrien` (Miles O'Brien, Integrator for Team DeepSpace9)
    - **Authority reference:** `agent-inbox:jadzia→obrien:1788267007390-fcdade04` (Offer `1788267007390-fcdade04` awarded by coordinator `jadzia` per `docs/pipeline/task-acceptance.md`)
    - **Accepted at:** `2026-09-01T12:51:00Z`
  - **Baseline findings:** `RRB-IDENT-001`, `RRB-META-001`, `RRB-BROWSER-001`.
  - **Previous implementation flaws:** The browser emitted numeric client version `1`, generated UUID-looking random bits rather than timestamped UUIDv7, minted a new ID at confirmation/export/submission/every retry, used evidence kinds outside the schema, silently discarded partial evidence, and let a GitHub-connected user export a `github_authenticated` claim that ingestion rejected.

## Acceptance criteria

- **AC-001** Build one immutable package after local validation and identity selection
- **AC-002** display that exact package's target, version/hash/status/source, category/rationale/evidence, actor claim, event/idempotency identities, and selected transport at confirmation
- **AC-003** submit/export the same object and preserve it for ambiguous retry, while an intentional edit follows the approved identity rule. Implement the approved reuse of the existing `review.js` localStorage collection with an explicit request/decision discriminator and lossless request fields
- **AC-004** locally staged requests appear in the existing collection UI as `local-only`, survive reload without becoming submitted/queued, use the same package builder/bytes for collected and direct submission, and are revalidated against authoritative current state when finally ingested. Use a standards-correct UUIDv7 implementation with shared pinned vectors and a semver string client version
- **AC-005** calculate the deterministic key exactly as the schema specifies. Present evidence as a clearly optional validated link plus optional free-text line, derive schema kinds internally, and reject invalid/partial input visibly instead of exposing or silently dropping raw kind/value/note rows. JSON export never asserts authoritative GitHub trust even when a verified GitHub name is available
- **AC-006** GitHub submission carries only a client claim and obtains authority from the later envelope. The downloaded bytes pass strict validation and contain no token or sensitive transport state

## Definition of Done

Unit and browser tests parse the actual downloaded/submitted JSON—not the server render payload—and compare every field/canonical byte/digest to the confirmed package; retry retains IDs/bytes, edit behavior is explicit, authenticated JSON downgrade passes ingestion, invalid local input blocks transport with field-level errors, and no browser action mutates record/status/history.
