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

## Process-version pin and re-check — added 2026-08-26

**This pilot originally pinned no process version.** It assessed "the candidate process"
without naming which text, so a reader could not tell afterwards what was piloted. That is a
violation of `feature-definition-and-breakdown.md` §7a.2, committed by this package before that
rule existed. The pin is added retrospectively rather than the pilot being rewritten.

| | |
|---|---|
| Process text assessed | `docs/pipeline/feature-definition-and-breakdown.md` and siblings, as of branch `0039-01` @ `316bce655` |
| Governance baseline | `main` @ `9ccd99b25`; `feature-breakdown.md` from Task `0044-04` (`[x]`, **Task Acceptance `✓`**), its §8 from `0044-06` (`[x]`, integration-reviewed, **no Task Acceptance**) |
| Assessed Feature | unchanged — no marker, claim, scope, or acceptance state of the assessed Feature was touched, then or now |

**Re-check against the reworked process.** Every control row above was re-read against the
current text. **All rows still map**, and none depended on removed material:

- The removed templates §C (the competing eight-field decision-record format) is **cited by
  neither pilot** — both reference real `DEC-` records instead — so its removal disturbs no row.
- §4's move from restating breakdown mechanics to citing `feature-breakdown.md` does not change
  what the rows assess; it changes where the rule is written.
- `feature-breakdown.md` §8 adds cognitive-demand fields to the **task record**, which these
  retrospective assessments do not produce; no row is invalidated, and no row now covers it.

**What this re-check does not claim.** It does not upgrade these pilots into evidence for the
*expanded* contract. They demonstrate that the process can be applied retrospectively to two
materially different Features; they do not address the 20-Task effectiveness measurement added
to the contract later, which is carried by
`docs/dossiers/0039-01-effectiveness-measurement.md` instead. Nor does a re-check substitute
for the independent review that the exit criteria require.
