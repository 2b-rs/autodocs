# Pre-mutation Architect scope review — Task `0038-34`

## Verdict

**`supports`**, for exact decision candidate `DEC-0038-004` in this commit
lineage and only within the binding scope below.

- **Recorded at:** `2026-08-25T09:22:12Z`
- **Reviewer identity:** `agent:data:architect:0038-34:20260825T092500Z`
- **Role / capability:** management-instantiated `Architekt`, `privileged`
- **Implementer identity:** `agent:tom-sisko-20260825t091500z:0038-34:20260825T091500Z`
- **Independence:** the Architect is distinct from the Implementer, did not author the implementation or proposed operative text, and holds no implementation, Acceptance, checkpoint-crossing, integration, `main`, or Feature-closure scope in this assignment.
- **Authority boundary:** the Task contract and Architect process role authorize the architectural decision; Kathryn's agent-inbox packet `1787649633229-37b9dcc0` coordinates exact execution scope but is not itself Management authority.
- **Pinned baseline:** `main@bd768cb3ce571491d332e9ea26029f8f0e4aedf9`; Task branch `0038-34@30aedae0d4`.

## Source findings and corrected diagnosis

The four named source records were inspected directly. The Task's useful
observation survives, but its role-based diagnosis and two historical claims do
not. `0038-31` was rejected because a multiplicity collision could hide a real
finding; code inspection exposed the missing neighbor and a later 10,000-case
property run closed the correction. The property test did not originally find
the defect. `0044-16` was rejected because optional persistent-only fields
serialized as `null` on every neighboring finding shape, directly supporting
presence/absence neighbor evidence. `0038-33` had four negative controls named
in `DEC-0038-002` and was technically sound, but its first overall checkpoint
verdict was `inconclusive` for an authority-package question before a later
clarification supported a superseding technical acceptance. `0044-04` concerns
stale pilot baseline and incorrect role attribution; it does not support an
executable adversarial-test mandate.

The transferable mechanism is therefore a named falsification question tied to
a changed claim, not an assumption that implementers confirm while reviewers
refute. The decision correctly adopts that third answer and excludes the
non-test-shaped defects instead of forcing them into either proposed branch.

## Binding implementation boundary

The qualifying mutation may proceed only if both operative locations express
the same rules without broadening them:

1. Applicability is semantic: a substantive change alters counting/cardinality,
   identity matching, serialization shape or field presence, blocking/gate
   classification, or asserts a set/sequence invariant. Merely touching a file
   associated with those topics is insufficient; disguising such a behavior
   change as documentation or test-only work is also insufficient.
2. Red-first means evidence against the exact pre-change baseline and candidate,
   not necessarily wall-clock test authorship before coding. It binds the real
   command and bounded output or an immutable output artifact. A test that was
   always green, a mocked assertion that bypasses the changed path, or a prose
   claim is not conforming.
3. At least one falsification case is derived from the changed contract. At
   least two distinct adjacent cases name the neighboring dimension, expected
   result, observed result, and why it is adjacent. The falsification case may
   also be one of the two adjacent cases only when it actually tests a distinct
   neighbor rather than restating the happy path.
4. A claimed set or sequence invariant requires a generative or exhaustive
   property test. Evidence names the invariant/oracle, input domain or finite
   enumeration boundary, reproducible seed or replay input when applicable,
   and actual executed case count. Do not impose an arbitrary universal count;
   reviewers judge whether the domain meaningfully exercises the claim.
5. The new requirement is additive. It does not replace relevant unit,
   integration, safety, regression, checkpoint, Acceptance, provenance,
   independence, or authority evidence and cannot turn those questions into
   test-only questions.
6. Explicit exclusions include prose-only/documentation-only changes,
   bookkeeping and marker/claim maintenance, unrelated generated-output
   refreshes, and authority/baseline/independence questions. An excluded change
   remains subject to every pre-existing requirement.

The worked example should use `0038-33` only for its four independently red
technical controls and must preserve the initial `inconclusive` plus later
superseding history. It may use `0038-31` to show a property boundary, but must
state that code reading found the defect and property testing closed it.

## Verification and activation

Before implementation completion, verify the full Task contract against both
operative diffs, compare their normative propositions one-for-one, and run at
least one positive fixture and negative fixtures for: out-of-scope bookkeeping,
missing red baseline, always-green negative, fewer than two neighbors, missing
neighbor result, set claim without property evidence, missing oracle/domain,
and inconsistent partial projection. The exact commands and outputs become
Task evidence; green validation does not self-authorize the scope.

Activation occurs only after `DEC-0038-004`, this review, both consistent
operative projections, analysis, worked example, and exclusions are committed
and integrated through the mandatory `0038-34` checkpoint. Until then the old
completion contract remains authoritative. Rollback is symmetric across both
operative locations. No existing Acceptance or checkpoint record is rewritten.

## Baseline discrepancy and residual risk

At review start, the implementer branch contained only its opening claim. Three
analysis files were untracked in the foreign implementer worktree, while the
advertised DEC draft and exclusion file were absent. Those mutable bytes were
not consumed. This review derives its findings from the pinned Task and exact
source-review commits instead. The primary residual risk is ritual compliance
through weak generators or mislabeled neighbors; explicit domain/oracle/replay
evidence and independent checkpoint inspection bound that risk. This review
accepts no residual product, authority, or integration risk.

This record is a pre-mutation scope review only. It is not Task Acceptance, an
integration review/verdict, implementation validation, or permission to advance
`main`.
