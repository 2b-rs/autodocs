# Architect governance coordination — 0038-35 claim carriage and doctor lifecycle

record_kind: governance-coordination
task_id: 0038-35
request_id: claim-carriage-20260825T211241Z-c86a50d2
owner_token: agent:data:0038-35:claim-carriage-20260825T211241Z-c86a50d2
base_commit: 8a364e000fed6e826a1e7d49c4b1c014c849eece
capability_class: privileged
execution_authority: direct
startup_review: SANDBOX.md, AGENTS.md, PRIVILEGED.md, docs/pipeline/roles/architect.md, docs/pipeline/core-rules.md, docs/pipeline/feature-breakdown.md, and docs/pipeline/task-acceptance.md reviewed
state: [ ]
coordination_state: complete
architect_work_product_status: [x]
write_scope: ["docs/dossiers/dec-0038-006-claim-carriage-doctor-lifecycle.md", "docs/dossiers/0038-35-claim-carriage-doctor-scope-review.md", "TODO-data-0038-35-claim-carriage-20260825T211241Z-c86a50d2.md"]

## Assignment and authority boundary

Project Lead `jean-luc` assigned a governance-only Architect packet under the
existing Management-instantiated Feature-0038 Architect role and the recorded
`0038-35` role separation. Stable coordination reference:
`agent-inbox:1787692280926-ca5124de`.

This record does not claim implementation ownership of Task `0038-35` and does
not change its authoritative `[ ]` marker. Data authors the decision and
supporting pre-mutation scope review only. Data must not implement the doctor
correction, edit tests or Paul records, decide Acceptance, integrate the
governance candidate, move Feature `0038`, or advance `main`.

## Baseline and allocation evidence

- Exact branch base and current `main` at worktree creation:
  `8a364e000fed6e826a1e7d49c4b1c014c849eece`.
- Branch: `gov-0038-35-claim-carriage-data-20260825`.
- Worktree:
  `/Users/tobias.anton/devel/autodocs/.worktrees/0038-35-claim-carriage-governance-data-20260825`.
- Before allocation, `DEC-0038-006` had zero occurrences on exact `main` and
  zero committed-history hits; `DEC-0038-005` was the highest allocated
  Feature-0038 decision on `main`.
- Evidence baselines preserved: candidate
  `84ed0fab0ea8a2e3a3cae2bb9abd6e62f82af3d4`, original combined record
  `5b08608b0dada88e061ab8985c8f11e08cde21e9`, and doctor implementation
  `cc99c1f27a0be1c53357b6aaef829aab8ae36770`.

## Intended write scope

- `docs/dossiers/dec-0038-006-claim-carriage-doctor-lifecycle.md`
- `docs/dossiers/0038-35-claim-carriage-doctor-scope-review.md`
- `TODO-data-0038-35-claim-carriage-20260825T211241Z-c86a50d2.md`

No authoritative backlog list, Task marker, Acceptance, doctor
implementation/test, Paul claim, governance authority file, or external system
is in scope.

## Delivered work product

`DEC-0038-006` records the already-determined precedence and lifecycle rule,
affected work units/gates, staged activation, no implicit grandfathering,
migration, Acceptance impact, and rollback. The supporting Architect review
defines the validated historical-carriage interface, classification table,
exact exclusions, falsification fixtures, exhaustive property matrix, resource
profile, and separation conditions for a future Implementer.

Substantive governance REF:
`9e63b0c8a852273ea6e622b4caa273e0f011310b`.

## Validation before check-in

- Decision-record shape: PASS; all 15 ordered fields present, four alternatives
  with exactly one selected, eight consequences, conforming identity/timestamp,
  affected units/gates, participation, and `Waiver: none`.
- `process_doc_doctor.py --root . --json`: exit 0; 32 existing findings, the
  exact same rule/severity multiset as `main@8a364e000`; zero findings
  attributable to this packet.
- `legacy_task_doctor.py --root . --json`: expected repository-wide exit 1;
  776 existing findings, the exact same rule/severity multiset as the main
  baseline; zero findings attributable to this coordination record or packet.
- `DEC-0038-006` uniqueness: zero occurrences on exact main and zero earlier
  committed-history hits before allocation.
- Every cited full commit (`8a364e000`, `84ed0fab0`, `5b08608b0`,
  `cc99c1f27`, `4f5a56356`) is locally reachable and the packet changes only
  the three declared paths.

## Next step

Hand the exact candidate tip containing the substantive REF and this final
bookkeeping record to separately assigned Integrator Geordi. Do not advance
`main` or begin tool implementation.
