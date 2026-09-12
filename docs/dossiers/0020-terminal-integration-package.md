# Feature 0020 terminal integration package

## Status and boundary

This report is the implementation product of Task `0020-10`. It aggregates
the nine completed child contracts without editing them. It is not Task
Acceptance, an integration verdict, Feature closure, ECU process execution, a
`PA 1.1` or capability rating, ISO/SAE 21434 or ISO 26262 performance, release
approval, or residual-risk acceptance.

The machine-readable source of the exact REFs, product digests, validation
cases, findings, and handoff is
`docs/dossiers/0020-terminal-integration-manifest.json`.

## Reconciled contract

The assessed increment is system and application software above the kernel for
`product_id=virtualized-automotive-ecu` and
`project_id=autodocs-ecu-software`. The kernel, hardware, manufacturing, and
complete-ECU lifecycle are outside this increment. The responsibility matrix
and applicability matrix agree: the selected profile is exactly `SWE.1`–
`SWE.6`, `SPL.2`, `SUP.1`, `SUP.8`, `SUP.9`, `SUP.10`, `MAN.3`, `MAN.5`, and
`MAN.6`, all with internal execution responsibility. The shared set is empty.
`SYS.1`–`SYS.5`, `VAL.1`, the conditional processes, and owned cybersecurity
or functional-safety lifecycles are not selected and receive no internal
rating.

The evidence contract is also consistent across the worksheets, catalogue,
and execution register. An ECU outcome requires `ecu-execution` with matching
product, project, process, process-instance, and baseline identity.
`process-definition`, `implemented-mechanism`, `documentation-execution`,
`controlled-scenario`, cross-product evidence, and external interface evidence
cannot substitute for the assessed unit's own performance. The worksheets and
catalogue cover the same 14 processes, assign no ratings, and retain the honest
gap that no valid ECU-execution baseline exists. The register identifies
executable downstream paths but does not claim those paths are complete.

## Deterministic consistency matrix

| Boundary | Compared sources | Result | Observable reason |
|---|---|---|---|
| ECU and supplied product | `0020-01`, `0020-03`–`06` | pass | All exclude kernel, hardware, manufacturing, and complete-ECU ownership. |
| Responsibility and applicability | `0020-03`–`05`, `0020-09` | pass | Exactly 14 internal processes, zero shared processes, and no internal SYS/VAL or conditional-process rating. |
| Evidence origin and refusal | `0020-02`, `0020-07`–`09` | pass | All require matching-identity `ecu-execution` for an ECU outcome and refuse substitution. |
| Assessment input | `0020-04`, `0020-07` | pass | Same process population; CL1 requires per-process `PA 1.1 = L/F`; ratings remain blank. |
| Catalogue and register | `0020-08`, `0020-09` | pass | Same 14-process population and same explicit no-ECU-execution gap. |
| Unsupported claims | all inputs | pass | No rating, safety/cybersecurity performance, release approval, Acceptance, or closure is asserted. |

## Contrary evidence and findings

The principal contrary evidence is deliberate and retained: the catalogue says
there is no `ecu-execution` baseline, while the register shows execution paths
whose completion Tasks remain future work. This prevents a false readiness,
freeze, rating, release, or closure inference. It is finding
`F-0020-10-002`, open and owned by future ECU execution and assessment work;
it is not a defect in the nine definition products.

No child inconsistency was found in the named boundaries. That closed result is
`F-0020-10-001`. Any later discovered child conflict must be returned through a
separately owned correction and must not be repaired in this package.

## Validation contract

The local manifest checker verifies schema shape, the exact nine-child
population, Git-object reachability, product existence and SHA-256, the
14-process population, empty shared set, consistency-result coverage, findings
dispositions, and checkpoint/Acceptance withholding. In-memory negative cases
must reject missing and stale product evidence, wrong-origin and cross-product
evidence, unsupported claims, and a divergent child process population. The
package also records JSON parsing and `git diff --check`.

No checker is registered as a repository-wide default gate.

The package-specific semantic suite passed the current manifest and rejected
each required missing-product, stale-digest, wrong-origin, cross-product,
unsupported-claim, and child-conflict mutation. JSON parsing and
`git diff --check` also passed.

## Recovery and handoff

Before integration, recovery is to abandon the `0020-10` candidate without
touching any completed child product. After integration, change requires an
append-only decision and independently reviewed backlog correction; neither the
decision history nor child evidence is rewritten.

The handoff consists of the exact committed candidate and this worker claim.
A distinct privileged Integrator must review the unchanged candidate at the
mandatory checkpoint. Prerequisite-closed Task Acceptance is a separate,
explicitly assigned action. A green package check performs neither action and
does not authorize a Feature merge, `main` advance, or `DONE.md` move.
