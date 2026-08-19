# Retrospective Pilot — Feature 0041

**Assessment type:** Candidate-process retrospective; no `0041` marker, claim, branch, implementation, or acceptance state was changed.

**Why materially different:** `0041` changes worker clone/push and check-in behavior. It has direct repository/worktree effects, migration compatibility, and host-side operational boundaries rather than `0040`'s governance scope.

## Candidate-process coverage

| Candidate control | Observed evidence | Assessment |
|---|---|---|
| Intake and outcome | `TODO.md` Feature 0041 trigger: shared `.git` symlink caused shared refs/index | A concrete failure and desired isolation outcome are recorded. |
| Direct/derived/external scope | `0041-01` clone provisioner; `0041-04` push path; `0041-05` end-to-end integration | Direct clone/ref effects, derived canonical-tree proof, and host boundary are distinguishable. |
| Decomposition by outcome | Tasks `0041-01` through `0041-05` | Provisioning, check-in semantics, publication guard, and integrated verification have different evidence and recovery needs. |
| Prerequisite semantics | `0041-02:0041-01`; `0041-04:0041-01,0041-02`; `0041-05` consumes all producers | Producer-consumer ordering is explicit and acyclic. |
| Capability/executability | Feature trigger records host-side branch/clone limitation; `0041-01` has committed clone implementation evidence | The assessment exposes a required execution profile rather than assuming sandboxed Git capability. |
| Risk/recovery/closure | refusal of unsafe target paths, no force-push, canonical-tree before/after evidence, `0041-05` integration | Operational effects and recovery boundaries are identified before aggregate closure. |

## Findings

- `P0041-01` (observation): The Feature contract should express canonical-tree immutability as a stable outcome criterion with a retained before/after evidence class, not only Task prose.
- `P0041-02` (pass): Separating provisioning, semantic check-in change, push guard, and end-to-end integration follows the candidate split rules.

## Verdict

The candidate process would add criterion-level coverage and explicit authority interfaces while preserving the existing implementation sequencing. It does not authorize deployment, push, release, or Feature acceptance.