# Architect governance coordination — 0038-35 claim carriage and doctor lifecycle

record_kind: governance-coordination
task_id: 0038-35
request_id: claim-carriage-20260825T211241Z-c86a50d2
owner_token: agent:data:0038-35:claim-carriage-20260825T211241Z-c86a50d2
base_commit: d05ec9f602d5baaf3c043c8f20e8edda3d5d8caa
capability_class: privileged
execution_authority: direct
startup_review: SANDBOX.md, AGENTS.md, PRIVILEGED.md, docs/pipeline/roles/architect.md, docs/pipeline/core-rules.md, docs/pipeline/feature-breakdown.md, and docs/pipeline/task-acceptance.md reviewed
state: [x]
recorded_task_state: [ ]
coordination_state: complete
lease_active: false
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

## Integration rejection and additive correction

Integrator Geordi rejected candidate
`836e9cbff7a5283af3771c5b6ada3b722c7787dc` before candidate hygiene or merge
because substantive commit `9e63b0c8a852273ea6e622b4caa273e0f011310b`
omitted the mandatory `Policy-Origin-Branch: main` trailer. Project Lead
Jean-Luc assigned an additive correction under
`agent-inbox:1787693769934-0972bbb2`: preserve history, remain within these
three paths, and supply the missing origin provenance without amending,
rewriting, or touching `main`. The scope-review origin section and the
correction commit trailer satisfy that bounded follow-up; the rejection remains
durable and the earlier commit is not represented as having carried the
missing trailer.

Additive origin-provenance correction REF:
`bbc4174f27b37e93384e2a1dc2142623b141bacb`.

Integrator Geordi rejected corrected candidate
`add65255e5c6da9ae21616051844582c1dc0053c` before integration because
path-specific history for the decision artifact still resolved to untrailed
introduction commit `9e63b0c8a852273ea6e622b4caa273e0f011310b`. Project Lead
Jean-Luc assigned a second additive correction under
`agent-inbox:1787694349958-8b82e56c`: touch the exact decision document with an
append-only provenance note in a commit carrying the mandatory origin trailer,
preserve both rejected tips as ancestors, and remain within the same three-path
scope.

Decision-path provenance correction REF:
`401e69651bf6a5899ba2488cc7bb53135cea096f`.

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

## Current-main re-pin

Project Lead Jean-Luc requested a current-main re-pin under
`agent-inbox:1787696951035-c1ddcb9f` after `main` advanced solely through the
Culber preserved-row recovery at
`d401aeb069371934ed349f5b59b9cae5051dbfbc`. The re-derived branch
`gov-0038-35-claim-carriage-data-20260825-r2` starts at that exact main commit
and merges prior candidate `3ae32c1d85d315cb1cb45d43a3db8c2ed018537c`
as preserved ancestry. The one intervening main path,
`docs/pipeline/branch-workflow.md`, is disjoint from this packet and is not
changed relative to current main. Decision, review, and coordination semantics
remain unchanged; this re-pin updates only current baseline and immutable
origin provenance within the same three-path scope.

- Current base: `d401aeb069371934ed349f5b59b9cae5051dbfbc`.
- Re-pin worktree:
  `/Users/tobias.anton/devel/autodocs/.worktrees/0038-35-claim-carriage-governance-data-20260825-r2`.
- Prior exact candidate retained as the second parent:
  `3ae32c1d85d315cb1cb45d43a3db8c2ed018537c`.
- Current-baseline validation: `process_doc_doctor.py --root . --json` exits
  `0` with 32 findings, identical to current main; `legacy_task_doctor.py
  --root . --json` returns its expected repository-wide exit `1` with 776
  findings (`563` error, `212` warning, `1` info), identical to current main,
  with zero findings attributable to the canonical coordination path.
- `git diff --check` passes; the exact net diff from current main contains only
  the three declared packet paths; `DEC-0038-006` remains absent from current
  main before integration.

### Execution recovery

The first no-commit merge invocation inherited the root checkout as its shell
working directory after creating the re-pin worktree. It staged only these
three packet additions in a root merge attempt and was immediately aborted
with `git merge --abort` before any edit or commit. The root returned to
`main@d401aeb069371934ed349f5b59b9cae5051dbfbc`, with no staged paths and only
its pre-existing unstaged Memory/untracked state. The merge was then rerun in
the owned re-pin worktree. No root ref, commit, tracked work product, or
unrelated path was changed.

## Second current-main re-pin

Project Lead Jean-Luc requested the next additive re-pin under
`agent-inbox:1787697998878-d45f4178` after `main` advanced solely through the
two-path `0041` visibility hold at
`d05ec9f602d5baaf3c043c8f20e8edda3d5d8caa`. Branch
`gov-0038-35-claim-carriage-data-20260825-r3` starts at that exact main commit
and merges clean held candidate
`16371cddbaf7f61a3928e36b76bda13cf2c1ed7d` as preserved ancestry. The
intervening paths, `TODO.md` and
`TODO-michael-0041-02-hold-repin-20260826T002700Z.md`, are disjoint from this
packet and remain unchanged relative to current main. Decision, review, and
coordination semantics remain unchanged.

- Current base: `d05ec9f602d5baaf3c043c8f20e8edda3d5d8caa`.
- Re-pin worktree:
  `/Users/tobias.anton/devel/autodocs/.worktrees/0038-35-claim-carriage-governance-data-20260825-r3`.
- Prior exact candidate retained as the second parent:
  `16371cddbaf7f61a3928e36b76bda13cf2c1ed7d`.
- Current-baseline validation: `process_doc_doctor.py --root . --json` exits
  `0` with 32 findings, identical to current main; `legacy_task_doctor.py
  --root . --json` returns its expected repository-wide exit `1` with 777
  findings (`564` error, `212` warning, `1` info), identical to current main,
  with zero findings attributable to the canonical coordination path.
- `git diff --check` passes; the exact net diff from current main contains only
  the three declared packet paths; `DEC-0038-006` remains absent from current
  main before integration.

## Next step

Hand the exact candidate tip containing the substantive REF and this final
bookkeeping record to separately assigned Integrator Geordi. Do not advance
`main` or begin tool implementation.
