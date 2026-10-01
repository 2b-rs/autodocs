# `DEC-0037-032` — Separate lifecycle for noncanonical coordination claims

This pre-mutation record captures the Management-selected schema for terminal
noncanonical coordination claims. It defines a future implementation contract;
it does not modify a claim, Task marker, validator, scheduling frontier, lease,
Acceptance record, integration state, or repository ref.

### `DEC-0037-032` — Separate noncanonical claim lifecycle from Task markers

- **Record format:** `decision-record@v1`
- **Recorded at:** `2026-09-04T08:31:21Z`
- **Deciding identity:** `authority:management:decision-1788508678045-f8f7c94e`
- **Role:** `Management`
- **Authority reference:** `decision-1788508678045-f8f7c94e`; selected option `separate_claim_lifecycle`; preparation assignment `1788508448831-d06899cd`; supporting Architect scope review `docs/dossiers/restart-claim-closure-terminal-lease-schema-scope-review-20260904.md@77c0ecc58dd5fb7286ab688dffa6aff274ada1b1`
- **Subject:** Machine-readable lifecycle and lease schema for noncanonical root coordination claims consumed by `legacy_task_doctor.py` and `frontier_query.py`, distinct from authoritative exact-Task claim markers.
- **Decision:** Adopt an additive three-field envelope for every root noncanonical coordination claim: `claim_kind: noncanonical-coordination`, `claim_state: active|terminal`, and `lease_active: true|false`. `active` requires `lease_active: true`; `terminal` requires `lease_active: false`. The three fields form one invariant and MUST be parsed from supported plain, code-formatted, or bold Markdown identity-preamble fields without changing their values. `state` remains governed exclusively by the existing authoritative Task-marker contract; this decision adds, removes, or reinterprets no Task marker. `state: terminal` is invalid and MUST NOT classify a claim as released. A claim is noncanonical only when the explicit `claim_kind` value is present and its canonical `task_id` or `item_id` does not identify an exact numeric Task claim participating in Task bookkeeping. An exact numeric Task claim cannot evade Task-state, marker, Acceptance, or exact-set validation by adding the noncanonical discriminator; conflicting or ambiguous classification fails closed. Future implementation MUST make `legacy_task_doctor.py` and `frontier_query.py` consume the same normalized envelope and reject missing, duplicate, malformed, contradictory, or unsupported lifecycle fields. A terminal noncanonical claim is excluded from the ready-frontier active-lease set but remains provenance and creates no Task completion or Acceptance inference. Candidate `8081c9a5099faed07d46dcee6174862af41ab3ba` is rejected because it writes `state: terminal`, overloading the Task-marker field and producing divergent doctor/frontier interpretations. No existing claim is rewritten by this record. A later, separately awarded implementation may reissue the nine-claim candidate only after a distinct Management-instantiated Architect reviews the cross-item gate scope, and only with synchronized consumer changes and tests.
- **Technical justification:** The operative lifecycle rule requires terminal noncanonical coordination claims to release their leases without manufacturing Task state or Acceptance. Current `legacy_task_doctor.py` parses `state` as a Task marker and rejects `terminal`, while `frontier_query.py` textually treats `state: terminal` as inactive and ignores `lease_active`; the reproduced R6 result therefore regressed doctor findings from 1886 to 1889 even though frontier tests passed. A dedicated discriminator and lifecycle field prevents the coordination state from entering the Task-marker domain, while the explicit lease boolean makes release independently auditable. Requiring both consumers to share one normalized invariant prevents one gate from scheduling work that the other still classifies as leased. Exact-Task exclusion blocks a noncanonical label from bypassing Task marker, claim-set, or Acceptance controls.
- **Triggers:**
  - `cross-item-blast-radius`
  - `material-architecture-or-repository-behavior`
  - `material-risk-decision`
- **Considered alternatives:**
  - **ALT-01:** Introduce `claim_kind`, `claim_state`, and `lease_active` as a separate noncanonical lifecycle envelope and update both consumers together after scope review.
    - **Disposition:** `selected`
    - **Reason:** It preserves the authoritative Task-marker vocabulary, represents lease release explicitly, and gives both scheduling and validation gates one falsifiable schema.
  - **ALT-02:** Extend the existing `state` marker model with `terminal` for claims classified heuristically as noncanonical.
    - **Disposition:** `rejected`
    - **Reason:** It overloads Task state, depends on classification before validation, and reproduces the R6 disagreement between doctor and frontier behavior.
- **Consequences:**
  - **CON-01:** Future noncanonical coordination claims have exactly one explicit kind, lifecycle state, and lease state; `active/true` and `terminal/false` are the only valid pairs.
  - **CON-02:** Exact numeric Task claims retain their existing marker, atomic-finalization, Acceptance, and claim-set rules; the new discriminator grants no escape from them.
  - **CON-03:** `legacy_task_doctor.py` and `frontier_query.py` must share normalized parsing and classification semantics before any claim migration or scheduling-gate activation.
  - **CON-04:** Required positive tests cover supported Markdown field styles and both valid lifecycle pairs. Required negative tests cover absent/duplicate/unknown fields, invalid booleans or states, contradictory pairs, `state: terminal`, ambiguous identity, and an exact Task claim carrying `claim_kind: noncanonical-coordination`.
  - **CON-05:** Cross-consumer regression tests must prove that the same terminal noncanonical fixture is lease-free and frontier-inactive in both tools, while the same active fixture remains visible in both.
  - **CON-06:** The nine noncanonical claims from rejected R6 may be reissued with the new envelope; `TODO-jean-luc-0037-51-20260824T072000Z.md` remains an unchanged exact Task claim and is an explicit exclusion fixture.
  - **CON-07:** Candidate `8081c9a5099faed07d46dcee6174862af41ab3ba` remains rejected evidence and is not merged, amended in place, or treated as an implementation input.
  - **CON-08:** This record is non-operative. A distinct Management-instantiated Architect scope review, fresh exact implementation award, synchronized tool/document/test changes, independent integration review, and canonical receipt remain required.
  - **CON-09:** Before publication, rollback is deletion of the unintegrated decision candidate branch. After publication, the append-only decision can only be superseded by a new record; later implementation can be reverted without erasing this history.
- **Affected work units:**
  - `repository:autodocs`
  - `feature:0037`
  - `path:docs/pipeline/terminal-claim-lifecycle.md`
  - `path:_src/tools/legacy_task_doctor.py`
  - `path:_src/tools/frontier_query.py`
  - `path:_src/tests/test_legacy_task_doctor.py`
  - `path:_src/tools/test_frontier_query.py`
  - `path:TODO-jean-luc-0037-08-integration-20260825.md`
  - `path:TODO-jean-luc-0037-09.01-parent-integration-20260825.md`
  - `path:TODO-jean-luc-0037-39-contract-repair-20260824T162000Z.md`
  - `path:TODO-jean-luc-0037-39-integration-20260825.md`
  - `path:TODO-jean-luc-0037-46.02-governance-20260823T134915Z.md`
  - `path:TODO-jean-luc-0038-management-decision-20260825T211222Z.md`
  - `path:TODO-jean-luc-0044-02-integration-20260824T232213Z.md`
  - `path:TODO-jean-luc-0044-07-marker-repair-20260829T002500Z.md`
  - `path:TODO-jean-luc-0044-13-containment-20260828T194500Z-01a049e4.md`
  - `path:TODO-jean-luc-0037-51-20260824T072000Z.md`
- **Affected gates:**
  - `validation:_src/tools/legacy_task_doctor.py`
  - `validation:_src/tools/frontier_query.py`
  - `task-start:0037-43`
  - `integration:0037-08`
  - `integration:0037-09.01`
  - `integration:0037-39`
  - `integration:0037-46.02`
  - `integration:0038`
  - `integration:0044-02`
  - `integration:0044-07`
  - `integration:0044-13`
  - `integration:0037-43`
  - `feature-closure:0037`
  - `feature-closure:0038`
  - `feature-closure:0044`
- **Review participation:**
  - **PART-01:**
    - **Identity:** `agent:data:0037-cutover-decisions-scope-review:1788510735023-4e984d7d`
    - **Role:** `Architekt`
    - **Participation:** `consulted`
    - **Position:** `supports`
    - **Note:** Signed scope-review candidate `77c0ecc58dd5fb7286ab688dffa6aff274ada1b1` supports the selected separate lifecycle only with explicit structural discrimination, conjunctive terminal release, exact-Task exclusion, synchronized consumer semantics, the complete negative matrix, and no operative mutation before both records are main-reachable.
- **Waiver:** `none`
