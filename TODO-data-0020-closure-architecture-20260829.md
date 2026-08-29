# Claim — Feature 0020 closure architecture

item_id: 0020-feature-closure-architecture
request_id: 1788029226494-1b18733c
owner_token: agent:data:0020-feature-closure-architecture:1788029226494-1b18733c
base_commit: 20110ed033c4bcd783e4093b1a8d310fad5658fc
capability_class: privileged
execution_authority: direct
startup_review: AGENTS.md; SANDBOX.md; TODO.md; docs/pipeline/roles/architect.md; docs/pipeline/core-rules.md; docs/pipeline/feature-breakdown.md; docs/pipeline/branch-workflow.md; docs/pipeline/decision-record.md
state: [x]
write_scope: ["TODO-data-0020-closure-architecture-20260829.md", "TODO.md", "docs/dossiers/dec-0020-003-feature-integration-floor.md", "docs/dossiers/0020-feature-closure-architecture-review.md"]

- **assignment:** `agent-inbox:1788029226494-1b18733c` (atomic award; execution wake `1788029258073-54e8caad`)
- **identity/role:** `data`, management-instantiated Architect, Team Enterprise
- **status:** `[x]` — committed architecture candidate ready for separate review
- **branch:** `governance-0020-closure-architecture`
- **worktree:** `/Users/tobias.anton/devel/autodocs/.worktrees/governance-0020-closure-architecture`
- **awarded_base:** `20110ed033c4bcd783e4093b1a8d310fad5658fc`
- **current_main_at_start:** `874e6209e936df2c1eebf5e8444972d9a226a625`
- **feature_input:** `0020@032fcb6ccc`
- **due_at:** `2026-08-29T19:17:38Z`

## Exact write scope and result

Record the missing Feature `0020` terminal integration floor and exact closure
contract. Verify the terminal implementation population `0020-01` through
`0020-09`, allocate `DEC-0020-003` only if collision-free on then-current
`main`, create a distinct supporting Architect scope-review artifact, and amend
only Feature `0020` in `TODO.md` with exactly one terminal integrating Task
prerequisite-closed over `0020-01` through `0020-09` and marked
`Integration review: mandatory`.

Declared write paths are exhaustive:

- `TODO-data-0020-closure-architecture-20260829.md`
- `TODO.md` only within Feature `0020`
- `docs/dossiers/dec-0020-003-feature-integration-floor.md`
- `docs/dossiers/0020-feature-closure-architecture-review.md`

## Startup verification and drift handling

The coordinator-created worktree was clean at the exact awarded base. At start,
`main` had advanced to `874e6209e936df2c1eebf5e8444972d9a226a625`;
the awarded base remains its ancestor. After this claim-only commit, reconcile
that exact current `main` before substantive authoring, re-read the affected
Feature block and decision allocation, and stop on conflict, scope widening, or
an occupied `DEC-0020-003` identifier.

## Prohibitions and boundaries

Do not implement the new terminal Task, change `0020-01` through `0020-09`
deliverables or terminal evidence, grant Acceptance, cross the new checkpoint,
move Feature `0020` to `DONE.md`, alter the selected profile/responsibility,
claim ECU execution/capability rating/release, integrate or advance `main`, or
touch any unrelated `TODO.md` section. The final product is a committed
governance candidate returned to the Project Lead for separate integration.

## Result and validation

- **Substantive REF:** `a795e5fea44e0f1b16bb20d8fe3b998d41babbb2`.
- **Latest reconciled main:** `e978f43c4a52a59a127482f7ddd1dccaee316995`;
  merge REF `c11413b09181734bf182ddb5d4a0d1a314e4fa45`.
- **Later disjoint drift observed:** `main@45b5ef3f2eca1b1a8daefa9b422cc237cb5bdb8c`
  changed only `0017-02` coordination paths. It neither allocates
  `DEC-0020-003` nor changes Feature `0020`; the Integrator must nevertheless
  reconcile the exact then-current `main` before integration.
- **Deliverables:** conforming `DEC-0020-003`, distinct
  `scope-ok-with-conditions` Architect review, and one open terminal Task
  `0020-10` prerequisite-closed over `0020-01` through `0020-09` with the
  Feature's only `Integration review: mandatory` attribute.
- **Graph checks:** ten unique Feature Task IDs; nine unique expected incoming
  edges to `0020-10`; exactly one mandatory checkpoint; no `0020-10` finding
  from `legacy_task_doctor.py`.
- **Validation:** `git diff --check` passed;
  `process_doc_doctor.py --root . --json` reported `ok=true`, 192 documents,
  one pre-existing error and 33 findings; `legacy_task_doctor.py` with
  `--root . --json` reported 768 errors, 305 warnings and one info after the
  reconciled baseline, with no `0020-10` finding.
- **Hygiene:** `check_integration_hygiene.py` with `--repo .` and candidate
  `e978f43c4a52a59a127482f7ddd1dccaee316995` passed across 77 registered
  worktrees before the reconciliation merge.
- **Known claim-format finding:** the immutable atomic-award owner token uses
  the non-backlog item component `0020-feature-closure-architecture`, which the
  legacy doctor's numeric Task-ID grammar rejects. The award-prescribed claim
  path and immutable token are preserved; the finding does not affect the new
  backlog Task or decision record.

## Next step

Project Lead assigns the unchanged candidate to a distinct privileged
Integrator. The Integrator reconciles exact current `main`, reruns hygiene and
validation, and either integrates the four awarded paths or returns findings.
This Architect does not implement `0020-10`, accept work, cross the checkpoint,
close Feature `0020`, or advance `main`.
