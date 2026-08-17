# Privileged Task Acceptance and Feature Closure

**Status:** Normative legacy-authority process introduced by reserved Task `0039-04`. Until Feature `0037` completes its authorized cutover, `TODO.md`, `DONE.md`, and active coordination records remain authoritative. The future issue-store contracts must implement equivalent semantics before approval and cutover.

## Purpose and boundary

Implementation completion and independent acceptance are different decisions. A Task may have a committed deliverable, successful validation, and a real `REF` while still resting on incomplete evidence, unrealistic tests, an unreviewed prerequisite, a hidden authority assumption, or a result that does not satisfy the intended outcome. This process introduces a separate Task-acceptance state, rendered as `✓`, and an independent Feature aggregate-acceptance gate.

Task acceptance means that the exact reviewed work-product baseline satisfies the Task contract under the recorded review scope. It does **not** grant or imply product approval, architecture approval, release authorization, safety acceptance, cybersecurity/privacy residual-risk acceptance, external-service authorization, process-baseline approval, or an Automotive SPICE capability rating. The reviewer verifies that any separately required decision exists and is correctly bound; the reviewer does not manufacture that authority.

The word `accepted` in this document is namespaced to **Task/Feature work-product acceptance**. It is distinct from curation-item decisions, review-request acceptance, publication, or external approval processes elsewhere in `docs/pipeline/`.

## State and rendering model

Acceptance is orthogonal to the legacy checkbox marker so that the executed disposition remains visible and current parsers are not silently broken.

| Representation | Meaning | Ordinary implementation start gate | Feature closure |
|---|---|---|---|
| `[ ]`, `[?]`, `[p]`, `[u]` | Existing open, investigatory, active, or genuinely human-blocked state | Unsatisfied | Unsatisfied |
| `[x]` | Implementation complete, committed, implementer validation complete, awaiting acceptance | Satisfied unless the consumer explicitly requires prior acceptance | Unsatisfied |
| `[w]` | Non-implementation disposition complete, reason/evidence committed, awaiting acceptance | Satisfied unless the consumer explicitly requires prior acceptance | Unsatisfied |
| `**Acceptance:** ✓` | The exact `[x]`/`[w]` baseline has a current accepted disposition | Satisfied | Required, but not sufficient by itself |

An accepted Task retains `[x]` or `[w]` on its header and adds a structured acceptance record. This preserves the distinction between a delivered result and a correctly accepted `wontfix`, `superseded`, `duplicate`, or `cancelled` disposition. `[✓]` is not introduced as a Markdown checkbox because it is not a standard checkbox token and would erase the underlying disposition.

The minimum legacy rendering is:

```markdown
  - **Acceptance:** ✓
    - **Disposition:** `completed|wontfix|superseded|duplicate|cancelled`
    - **Accepted by:** `<authorized-reviewer-identity>`
    - **Authority reference:** `<immutable assignment/authority reference>`
    - **Accepted at:** `<ISO-8601 timestamp with timezone>`
    - **Contract SHA-256:** `<64 lowercase hexadecimal>`
    - **Work-product manifest SHA-256:** `<64 lowercase hexadecimal>`
    - **Prerequisite-acceptance SHA-256:** `<64 lowercase hexadecimal>`
    - **Review REF:** `<full reachable 40-hex commit>`
```

A historical `ARCHIVED — NOT ACCEPTED` record never receives acceptance credit. Existing Features already in `DONE.md` retain the semantics and evidence status recorded when they were moved; they are not retroactively relabeled or represented as accepted under this process.

## Authority and separation of duties

Sandboxed/grunt agents may implement, investigate, validate, commit, prepare acceptance packages, and move their own claimed Tasks to `[x]` or `[w]`. They are prohibited from:

- creating, modifying, invalidating, or removing a current `Acceptance: ✓` record;
- representing themselves as the acceptance reviewer;
- asking a generic runner action to perform acceptance promotion;
- moving a Feature to `DONE.md`;
- treating privilege, a green command, or a Task `REF` as acceptance.

Only a session that is both currently privileged **and explicitly assigned by the current user or registered acceptance authority to the exact review scope** may decide Task or Feature acceptance. Privilege alone is not acceptance authority. A model name, Git author, claim filename, terminal access, or role self-assertion is not proof.

The reviewer is independent by default: the reviewer must not be the Task claim owner, principal implementer, author of the decisive technical disposition, or sole producer of the validation evidence. Prior consultation does not automatically destroy independence, but material design authorship, implementation, or self-generated approval evidence must be disclosed and normally disqualifies the reviewer. A self-acceptance exception requires an explicit current-user or registered-authority waiver naming scope, reason, duration, conflict, and compensating controls. Urgency or reviewer scarcity is not a waiver.

Specialist competence is part of assignment. One reviewer need not possess every specialist authority, but the review plan must identify required architecture, security, privacy, safety, release, legal, operational, or domain decisions and verify their authentic records.

## Implementation completion and review handoff

The implementation owner completes the existing claim at `[x]` or `[w]`, commits the substantive result and bookkeeping, finalizes the implementation claim, and returns to ordinary queue work. Waiting for acceptance must not hold the implementation write scope or become `[u]`.

The acceptance package must identify:

1. Task and Feature identity, exact normative Task text, acceptance criteria, Definition of Done, and contract digest;
2. exact substantive and bookkeeping commits, candidate tree, expected parent/base, and authority epoch;
3. a complete authoritative work-product manifest with paths, roles, source/generated classification, media types, and digests;
4. declared and observed direct, derived, external, and evidence scopes, including proof that unrelated work was excluded;
5. a criterion matrix mapping every normative condition to implementation, validation, evidence, findings, and disposition;
6. the direct and transitive prerequisite graph plus existing acceptance records and invalidation state;
7. validation profiles, commands or typed actions, environment/input/output identities, coverage, canaries, negative cases, durations, resource bounds, and immutable results;
8. material findings, severity, affected criterion/artifact, owner, corrective action or authorized disposition, and verification status;
9. security, privacy, safety, external-effect, migration, compatibility, recovery, rollback, and residual-risk interfaces;
10. user-prompt/process provenance and immutable evidence references without secrets or restricted personal data;
11. prior rejected, inconclusive, superseded, or invalidated review attempts.

Missing, stale, mixed, inaccessible, malformed, or internally inconsistent package information yields `inconclusive`, never an assumed pass.

## Privileged review procedure

### 1. Assignment and preflight

The reviewer verifies current privilege, exact user/authority assignment, independence, competence, review scope, policy/authority epoch, and absence of a competing review assignment. The reviewer pins the exact Task contract and candidate baseline before substantive inspection. Any drift requires a new review baseline.

### 2. Expand the prerequisite closure

The reviewer parses the exact prerequisite graph, rejects missing endpoints, self-edges, duplicate/reversed edges, cycles, ambiguous alternatives, and required prose-only dependencies, then computes the transitive prerequisite closure. A valid, reachable, non-invalidated acceptance record forms a review boundary. Every prerequisite without such a boundary enters the same review batch.

The batch is topologically ordered from leaves to the target. Acceptance is prerequisite-closed: a Task cannot be accepted while a required predecessor remains unaccepted, rejected, inconclusive, stale, or invalidated. Several items may be reviewed in one batch, but each receives its own decision and is promoted bottom-up.

Ordinary implementation may consume `[x]`/`[w]` to avoid serializing all work behind privileged reviews. A Task with an irreversible migration, canonical interface/schema, credential/security boundary, public release, architecture selection, or comparable high-risk dependency may state a stricter acceptance-before-start gate; until machine-enforced profile edges exist, this gate must be explicit in the Task contract and checked manually.

### 3. Inspect contract, work products, and scope

The reviewer reads the actual changed source, configuration, policy, process, test, and generated-output contracts—not only summaries or logs. Every criterion, changed authoritative path, authority-sensitive path, manifest/digest, structured finding, negative test requirement, and recovery/rollback boundary receives complete inspection.

For a large homogeneous generated population, deterministic whole-population checks remain preferred. Sampling is permitted only when the population is enumerated and digest-bound, a complete validator is infeasible or complementary inspection is useful, and the method records strata, seed, size, exclusions, boundary/high-risk selections, and rationale. Authority boundaries are never sampled. A material sample defect, population heterogeneity, missing canary, or unexplained mismatch expands the sample or triggers complete inspection.

The reviewer confirms that declared scope agrees with observed changes; no ambient staged, unstaged, untracked, generated, or external effect was silently included or omitted. Generated artifacts must map to their canonical producer and source manifest.

### 4. Evaluate and rerun validation

Existing immutable runs support review but do not replace independent freshness checks. Against an isolated exact candidate where feasible, the reviewer reruns:

- package/schema/digest/reachability and prerequisite checks;
- focused tests for changed behavior;
- required security/privacy/authority policy checks;
- representative negative, canary, failure, cancellation, retry, and recovery cases;
- broader regression, generation, or end-to-end validation required by the Task risk and contract.

A full expensive rerun may be omitted only when the validation profile permits reuse, all inputs/environment/tool versions and immutable results match exactly, canaries prove coverage, and the reviewer records why reproduction adds no material assurance. Child exit zero, output existence, timestamps, synthetic-only data, or a baseline-only run are not sufficient by themselves.

### 5. Review findings and authority boundaries

Findings use stable identities and at least critical, major, minor, and observation/improvement classes. Critical and major findings block acceptance. A minor finding may remain only when it does not contradict a criterion, the Task contract permits deferral, and it has an owner, due condition, traceable downstream item, and any required authority disposition.

The reviewer verifies required architecture, security, privacy, safety, release, external mutation, signing, or residual-risk decisions, but does not make them without the corresponding registered authority. An absent required decision blocks or makes the review inconclusive according to the evidence.

### 6. Decide and record

The review has exactly one outcome for the reviewed baseline:

- `accepted`: all criteria and prerequisite acceptance gates are satisfied; material findings are closed or validly dispositioned;
- `rejected`: evidence demonstrates a material nonconformity;
- `inconclusive`: identity, evidence, environment, scope, or authority is insufficient to determine conformity.

Rejected and inconclusive attempts remain append-only evidence. Rejection normally returns the Task to `[p]` when corrective implementation work is actionable. Inconclusive normally leaves `[x]`/`[w]` awaiting corrected review evidence; it becomes `[p]` only when substantive rework is required. `[u]` remains reserved for a genuine human decision as the sole next action.

The review evidence is committed first. A separate path-isolated bookkeeping commit adds `Acceptance: ✓` and references the real review commit. The acceptance commit must preserve unrelated work and use compare-and-swap or equivalent expected-base protection. The reviewer never fabricates a self-referential hash.

## Invalidation and reacceptance

Acceptance binds the Task-contract digest, substantive commit/tree, work-product manifest, validation profile/results, prerequisite acceptance set, authority epoch, accepted disposition, reviewer identity/assignment, and review timestamp. It is invalidated—not deleted—when relevant content or authority changes, including:

- normative Task, criterion, or Definition-of-Done change;
- accepted work-product bytes or semantic interface change;
- prerequisite acceptance invalidation or incompatible prerequisite change;
- changed required validation profile, environment, source input, or generated-output contract;
- a newly discovered material finding;
- relevant policy/authority epoch, supersession, rollback, or migration change.

An unrelated repository `HEAD` advance does not invalidate acceptance. Impact is determined from bound scopes, manifests, and semantics. Invalidation is append-only, names the triggering evidence, removes current acceptance credit, and propagates to affected dependent Tasks and Feature aggregate acceptance. Historical acceptance remains visible but is not current.

## Feature aggregate acceptance and `DONE.md`

All current Task and Subtask acceptance records are necessary but not sufficient. A separately assigned independent privileged reviewer performs Feature aggregate review after every in-scope child has a current accepted disposition. The reviewer verifies:

1. complete, acyclic, current Task/Subtask and Feature-prerequisite closure;
2. satisfaction of the Feature goal and Feature Definition of Done;
3. consistency and integration of Task outputs and accepted baselines;
4. Feature-level end-to-end, negative, recovery, migration, and operational checks;
5. cross-Task findings, residual risks, exclusions, cancellations, and successors;
6. current required product/specialist approvals from their proper authorities;
7. one digest-bound aggregate manifest of Task acceptance records and work products;
8. one immutable Feature-acceptance review record.

Only after aggregate acceptance may a privileged reviewer authorize the path-isolated move to `DONE.md`. A grunt, checkbox counter, parent aggregation tool, or old closure-eligibility advisory cannot perform or imply this move.

## Interim legacy enforcement and required migration

The human/agent authority rules in this document apply immediately. Existing legacy tools still encode `[x]`/`[w]` as terminal and therefore cannot be trusted to decide Feature closure or acceptance eligibility. Until machine enforcement is implemented:

- no automated or grunt-authored path may add, alter, invalidate, or remove acceptance records;
- no tool output stating that a Feature is closure-eligible is sufficient;
- privileged acceptance uses an exact reviewed candidate, separate evidence and bookkeeping commits, and manual verification of the rules above;
- any tool that cannot preserve acceptance records must fail closed rather than rewrite the Task block;
- future Feature `0037` approval/cutover must reconcile this process into lifecycle, schema, migration, queue, authority, and validation contracts.

Reserved follow-up Task `0039-05` owns the coordinated machine-enforcement and migration plan. It must extend the existing legacy editor/transaction semantics rather than create a competing writer, and must not appropriate active Tasks `0038-02` or `0038-05`.

## Measures and improvement

Track acceptance queue age, implementation-to-acceptance lead time, first-review acceptance rate, rejection/inconclusive causes, package-completeness defects, findings by severity/category, validation-rerun mismatches, escaped findings, invalidations, prerequisite-closure size, sampling escalation, independence waivers, Feature aggregate rejections/reopens, and reviewer load. Measures require definitions, denominators, population boundaries, data-quality checks, privacy controls, and decision use. Acceptance volume or a high pass rate is not an assurance objective.

## Automotive SPICE relationship boundary

This process can contribute evidence to quality assurance, verification, configuration management, problem/change management, project/risk/measurement management, work-product management, and process improvement. It is not an assessment and establishes no process capability level. A privileged agent is not automatically an organizationally independent QA function or competent assessor. Capability claims require the selected Automotive SPICE model/edition, named process and organizational scope, representative process instances, competent assessment, and evidence that practices are deployed and effective—not merely documented in this repository.
