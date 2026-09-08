---
schema_version: "1.0"
id: "0033-04"
level: "task"
parent: "0033"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-02"
  - "0033-03"
  - "0033-03.01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:794"
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
  - id: "AC-007"
    status: "active"
  - id: "AC-008"
    status: "active"
  - id: "AC-009"
    status: "active"
---

## Goal

PREREQ: 0033-04:0033-02, 0033-04:0033-03 Prepare a review-ready replacement for the drafted record-page UX document that is implementable and consistent with the process and package/envelope models.

## Scope

- **Baseline findings:** `RRB-UX-001`, `RRB-IDENT-001`, `RRB-NOJS-001`.
  - **Previous implementation flaws:** The prior UX remained explicitly `drafted`; promised controls on unreachable `invalid/*` published pages; allowed GitHub-authenticated claims to be exported as JSON even though ingestion rejected them; treated page age as staleness detection; omitted an implementable post-ingestion feedback channel; and specified a static no-JavaScript URL that could not mint required per-request metadata.
  - **Completion evidence (2026-08-30):** Class R candidate `docs/dossiers/0033-04-ux-scenarios.md`, REF `51fd87270` on branch `chain-0033-chakotay`, claim `TODO-Chakotay-Paris-0033-chain-20260830T113000Z.md`. Built only on this chain's own `0033-02` (REF `99fdc4a2b`) and `0033-03` (REF `f6af48701`) candidates; does not reinstate the historical `0033-04:0033-03.01` edge (architect scope review §3.1). Scenario map to proposed later tests in the candidate §8; requirement-to-artifact matrix in §10. No `docs/pipeline/**` path touched. Chain stops here; `0033-04.01` (approval gate) is explicitly out of this chain's scope.
  - **Acceptance: ✓** (2026-08-30, Integrator `obrien`, award `1788098846986-89dd4738`, review REF `54d3cf1a4` `docs/campaign-evidence/0033-recovery/chain-0033-acceptance-review-obrien-20260830.md`).

## Acceptance criteria

- **AC-001** Define action placement and wording only for eligible page kinds plus separately specified internal/report contexts
- **AC-002** exact required/optional fields and nested evidence validation
- **AC-003** a user-facing evidence UI with one clearly optional validated link field and one optional free-text line whose internal kinds are derived rather than typed by the user
- **AC-004** immutable target/status/source disclosure
- **AC-005** privacy/consent and public-GitHub disclosure
- **AC-006** one confirmation model that displays the exact client-controlled payload later exported/submitted, treats prefilled no-JavaScript target context as an untrusted claim unless protected by an approved tamper-evident token, defines signed-out/login behavior, while clearly disclosing which authoritative envelope fields do not exist until GitHub submission or ingestion and showing those server-derived fields only afterward
- **AC-007** `local-only`, `exported`, `submitted with receipt`, `ingested/queued`, duplicate, stale/rejected, transport-failure, and governed outcome states with their actual feedback channels
- **AC-008** retry/edit identity rules
- **AC-009** and explicit no-record-mutation wording. Decide and document how review-request drafts reuse the existing `review.js` / `ara-review-package-v1` localStorage collection without conflating decision items with request items, including schema/kind discrimination, migration, removal, clear-local-data, multi-tab/concurrent-update behavior, delayed-submit staleness, quota/privacy limits, and whether direct and collected submission share exactly one package builder. Define keyboard activation, unique dialog naming, focus trap/restoration, error and live-region behavior, visible focus, cancellation, named mobile breakpoints/layout, and an implementable no-JavaScript GitHub-intake flow whose trusted ingestion adapter derives server-owned request metadata from the Issue envelope

## Definition of Done

A review-ready UX contract and executable scenarios cover valid-curated, duplicate-before-open, duplicate race, stale-at-ingest, JSON export, GitHub receipt, authenticated-user JSON downgrade, signed-out/no-JS success and failure, retry, cancel, desktop/mobile, keyboard/focus, and post-ingestion traceability; every scenario maps to a proposed later automated test and all open UX decisions are explicit for `0033-04.01`.
