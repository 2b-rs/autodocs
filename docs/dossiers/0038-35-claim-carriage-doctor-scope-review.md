# Architect scope review — claim carriage and legacy-doctor lifecycle

**Position:** `supports-with-conditions`
**Review kind:** pre-mutation cross-item gate-scope review
**Reviewer:** `agent:data:0038-35:claim-carriage-20260825T211241Z-c86a50d2`, management-instantiated Architect
**Decision:** [`DEC-0038-006`](dec-0038-006-claim-carriage-doctor-lifecycle.md)
**Baseline:** `main@8a364e000fed6e826a1e7d49c4b1c014c849eece`
**Implementation status:** prohibited until this decision and review are reachable from `main`; no tool/test mutation is part of this packet

This review supports the exact boundary below. It is not Task Acceptance, an
integration review, an integration verdict, an implementation assignment, or
permission to close Feature `0038`. The future Implementer must be a distinct
identity. The Feature terminal Integrator and any Acceptance reviewer remain
separately assigned and independent under the existing `0038-35` contract.

## Normative precedence and reproduced contradiction

The doctor implementation and its rule table entered at
`cc99c1f27a0be1c53357b6aaef829aab8ae36770` on 2026-08-17 08:15 +02. The
later branch-carriage governance at `4f5a563569f` explicitly changed the older
delete-at-terminal behavior. Current authority is consistent:

- `AGENTS.md:24` delegates branch carriage to the normative branch workflow;
- `AGENTS.md:69` requires claims to travel upward and not be deleted at
  `[x]`/`[w]`;
- `AGENTS.md:210` says terminality ends ownership/write scope while the
  persisted file becomes provenance until Feature integration;
- `docs/pipeline/branch-workflow.md:229-247` defines that carriage and the
  Feature-integration removal point; and
- `docs/pipeline/task-acceptance.md:183` requires the privileged integrator to
  reconcile and remove carried predecessor claims during Feature integration.

The unconditional code at `_src/tools/legacy_task_doctor.py:1311-1317` and
documentation at `docs/pipeline/legacy-task-doctor.md:175` therefore lag the
current authority. A read-only run on exact `main` reported 776 findings,
including 60 `LTD-CLAIM-TERMINAL-RETAINED`; 56 map to Tasks in Features still
in `TODO.md`, and four map to completed Features in `DONE.md`. Exact candidate
`84ed0fab0ea8a2e3a3cae2bb9abd6e62f82af3d4` reported 780 findings: three more
open-Feature terminal-retention findings plus one identity mismatch for its
three restored Paul root records. The focused existing suite passed 57/57;
its `claim-drift` fixture freezes the old unconditional behavior and contains
no valid open-Feature terminal-carriage control.

The identity issue is separate. The original record at
`5b08608b0dada88e061ab8985c8f11e08cde21e9:TODO-paul-review-0038-33-34-20260825T195800Z.md`
minted `agent:paul:review-0038-33-34:20260825T195800Z`. Candidate `84ed0fab0`
rewrites that root path to `agent:paul:0038-33:20260825T195800Z`, which also
appears in the canonical `TODO-paul-0038-33-20260825T195800Z.md`. Preserving a
Git ancestor does not make a current immutable-token rewrite conforming.

## Supported classification interface

The Implementer may change the legacy doctor only to implement this complete
classification:

| Record condition | Classification | Required result |
|---|---|---|
| Canonical Task claim, claim and Task both `[p]` | active lease | Existing active-claim scope, resume, collision, and identity checks apply. |
| Canonical Task claim, claim state equals Task `[x]`/`[w]`, Feature is in `TODO.md` | ordinary carried provenance | Not `LTD-CLAIM-TERMINAL-RETAINED`; not active ownership; keep all identity/base/scope safety findings that independently apply. |
| Any claim state differs from the authoritative Task marker | divergent | Existing error remains; terminality must not suppress it. |
| A `[p]` claim points to an `[x]`/`[w]` Task | stale active lease | Error remains, including state divergence and an actionable stale-active classification. |
| Claim belongs to a Feature in `DONE.md` and remains at root | post-integration unreconciled | Error remains and blocks a final closure candidate. |
| Explicit `historical-carriage@v1` record with complete verified provenance | historical carried provenance | Inactive; excluded from active-claim counts; original token/path are preserved; no filename-derived Task-claim identity. |
| Historical kind missing or with invalid source/token/digest/related Tasks | malformed historical record | Error; fail closed without falling back to a filename exception. |
| Multiple records assert the same active lease | duplicate active ownership | Existing error remains. Multiple inactive provenance records never create ownership, but each must independently validate. |

`historical-carriage@v1` is a narrow adapter, not a general suppression. Its
machine-readable identity region must contain at least:

- `record_kind: historical-carriage@v1`;
- the exact current root `path`;
- the full reachable `source_ref` and identical `source_path` at which the
  record first minted its identity;
- `original_owner_token`, compared byte-for-byte with the source blob;
- a nonempty, unique, sorted `related_task_ids` set whose members exist;
- `lifecycle: carried-provenance` and `lease_active: false`; and
- a SHA-256 binding to the original source blob or a specified canonical
  provenance projection.

The Paul combined record uses source REF
`5b08608b0dada88e061ab8985c8f11e08cde21e9`, its unchanged root path, and the
original `agent:paul:review-0038-33-34:20260825T195800Z` token. The canonical
per-Task `0038-33` and `0038-34` records remain ordinary inactive Task-carriage
records. No path, agent, token prefix, or Feature-specific allowlist is allowed.

## Affected reach and gates

`cross-item-blast-radius` applies directly. The doctor's error verdict is
consumed by validation and integration work outside `0038-04`; changing it can
unblock or block `0038-35`, Feature `0038` closure, and Feature `0037` migration
and closure. The same change establishes repository-wide claim-lifecycle and
migration behavior, so `material-architecture-or-repository-behavior` also
applies.

Immediate work units are `0038-04`, `0038-21`, `0038-23`, `0038-33`,
`0038-34`, `0038-35`, Feature `0038`, Feature `0037`, and the repository's
legacy claim population. Gates are doctor claim validation,
`0038-35` backlog/claim-structure validation, `integration:0038-35`,
`feature-closure:0038`, Feature `0037` claim migration, and
`feature-closure:0037`.

## Implementation contract and exact exclusions

After the governance packet reaches `main`, a separately assigned Implementer
may own only the smallest necessary code/test/documentation correction. The
expected technical paths are `_src/tools/legacy_task_doctor.py`,
`_src/tests/test_legacy_task_doctor.py`,
`_src/tests/fixtures/legacy_task_doctor/cases.json`, and the registered doctor
documentation. Any Paul-record representation correction must be separately
scoped, preserve all three root paths, and retain the immutable source token.

This review does **not** authorize:

- deletion, relocation, hiding, or filename/path allowlisting of a root claim;
- mutation of an original token or synthesis of authority from a derived file;
- a blanket downgrade/removal of terminal, identity, divergence, duplicate,
  scope, base, or malformed-record findings;
- treating inactive carriage as an active lease or Acceptance record;
- changing Task markers, Acceptance, integration checkpoints, `TODO.md`,
  `DONE.md`, Feature closure, or `main` as part of the tool implementation;
- retroactive claims that old doctor outputs were clean; or
- implementation by Architect Data or silent repair by the terminal Integrator.

## Required falsification and property evidence

The implementation must add named fixtures and assertions for at least:

1. open Feature + canonical matching `[x]` claim: ordinary carriage, no
   terminal-retained error;
2. open Feature + canonical matching `[w]` claim: same result;
3. `DONE.md` Feature + the same terminal claim: unreconciled error;
4. terminal Task + `[p]` claim: state-divergence/stale-active errors;
5. nonterminal Task + terminal claim: divergence error;
6. exact Paul historical record with its original token and valid
   `historical-carriage@v1`: inactive valid provenance;
7. historical kind with wrong source ref, path, token, digest, duplicate or
   unknown related Task: fail closed;
8. two records asserting one active lease: duplicate error;
9. multiple inactive provenance records: no active duplication, with every
   record still independently validated; and
10. final Feature closure tree that retains any predecessor claim: blocked.

Because the change claims a classification invariant over a finite state
space, AE-5 applies. Exhaustively enumerate at least:

`Feature location {TODO,DONE}` × `Task marker {[ ],[p],[x],[w],[u]}` ×
`record state {[p],[x],[w]}` ×
`kind {task-claim,historical-carriage@v1,malformed-historical}`.

The oracle is the classification table above. Record the exact case count,
matrix boundary, and any structurally impossible combinations. AE-3 additionally
requires a baseline/candidate falsification: the valid open-Feature carriage
case is red under `cc99c1f27` behavior and green after correction, while the
`DONE.md` and stale-active controls remain red. Deterministic JSON, bounded
summary, input-resampling, and existing 57-test behavior outside the corrected
expectations must remain stable.

## Acceptance, migration, activation, and recovery

This governance-only packet changes no accepted work product and invalidates no
Acceptance by itself. The future code/semantic change is material to accepted
Task `0038-04`; its Implementer must prepare an additive invalidation and impact
analysis before promotion. Reviewers then determine propagation through
`0038-21`, `0038-23`, the `0038-33`/`0038-34` current records, and the complete
`0038-35` prerequisite-closed batch. A green doctor run cannot self-accept this
change or prove the scope decision.

Feature `0037` migration must use classification rather than top-level file
presence: only active leases become active `claim.json`; terminal Task carriage
and historical carriage become immutable provenance/closure events with source
identity and digest. The migration report must prove one active owner per item,
zero provenance loss, zero active duplication, and exact reconciliation of all
legacy root files. No implicit grandfathering applies after activation.

Governance activation requires this decision and review on `main`. Tool behavior
activates only through a separate implementation, validation, independent
Acceptance impact resolution, and authorized integration. Rollback reverts that
later behavior/schema/documentation delta together, re-runs the old doctor, and
records the restored findings. Root claims, decision/review history, prior
outputs, and Acceptance history remain untouched and recoverable.

## Advisory delivery profile

- **Capability:** future Implementer `unprivileged` or `privileged` with direct
  local execution; no network, credentials, external service, publication, or
  destructive operation.
- **Cognitive demand:** `high`; exact lifecycle and migration semantics matter
  more than code volume.
- **Estimate:** 4-7 changed implementation/test/documentation paths, 8-16 focused
  test additions, 2-6 CPU minutes focused and under 20 minutes broader local
  validation, memory below 1 GiB.
- **Uncertainty:** medium (legacy coordination-record shapes are heterogeneous).
- **Risk:** high error-direction risk: over-broad suppression hides genuine
  reconciliation failures; under-broad classification continues blocking
  conforming carriage.

## Architect verdict

**Supports with the conditions above.** The scope is sufficiently bounded for a
distinct Implementer after the governance packet reaches `main`. Any proposal
to weaken an additional finding, infer history from filenames, omit migration
classification, or remove a root record exceeds this review and requires a new
decision/review before mutation.
