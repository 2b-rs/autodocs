# Architect scope review — Feature 0020 closure floor

## Verdict and authority

- **Verdict:** `scope-ok-with-conditions`
- **Reviewed at:** `2026-08-29T18:56:00Z`
- **Reviewer:** `agent:data:0020-feature-closure-architecture:1788029226494-1b18733c`
- **Role:** management-instantiated Architect, Team Enterprise
- **Capability class:** `privileged`
- **Assignment:** atomic award `1788029226494-1b18733c`
- **Pinned current main:** `874e6209e936df2c1eebf5e8444972d9a226a625`
- **Pinned Feature input:** `0020@032fcb6ccc`
- **Candidate after baseline reconciliation:** `8adf508aecf1ce9272ac1210ea1ade3a2f3485d9`
- **Companion decision:** `DEC-0020-003`

This is the pre-mutation supporting Architect scope review required for a
cross-item closure gate. It is not implementation, Task Acceptance, an
integration verdict, checkpoint crossing, Feature closure, risk acceptance, or
permission to advance `main`.

## Finding and population proof

Current `main` and `0020@032fcb6ccc` each contain exactly the nine declared
Feature Tasks `0020-01` through `0020-09`, all marked `[x]`. Each has a real
implementation REF and explicitly withholds Feature closure; none is designated
as the Feature's terminal integrating Task and the Feature block contains zero
`Integration review: mandatory` attributes. `DEC-0020-003` and `0020-10` were
absent from current `main` immediately before allocation.

The missing floor has actual cross-item reach. Feature-level prerequisites name
`0020` for Features `0027`, `0022`–`0026`, and `0028`–`0032`. Closing `0020`
without a package integration result could admit inconsistent scope,
responsibility, applicability, evidence-origin, catalogue, or selected-profile
state into their start, validation, release, assessment, or closure paths.

## Minimum sufficient correction

One new Task, `0020-10`, is necessary and sufficient. It consumes every existing
Feature Task through explicit edges and owns only:

1. exact source/REF and work-product manifesting for `0020-01` through `0020-09`;
2. cross-product consistency of ECU boundary, responsibility, applicability,
   evidence origins, assessment input, catalogue, and selected-profile register;
3. deterministic validation results, contrary evidence, and complete finding
   disposition, with child corrections returned to separate owners;
4. recovery instructions and a prerequisite-closed review/Acceptance handoff;
5. the Feature's single mandatory integration checkpoint.

No extra Task, child rewrite, new selected-profile edge, default shared
validator, assessment result, or release gate is required by this correction.

## Executable Task contract

The sources are `TODO.md` Feature `0020` and its nine terminal child records at
`main@874e6209e936df2c1eebf5e8444972d9a226a625` (authoritative backlog and
repository evidence), `0020@032fcb6ccc` (evidentiary integrated Feature input),
`DEC-0020-001` and `DEC-0020-002` (binding boundary decisions), and
`DEC-0020-003` (binding integration-floor decision). No ECU execution evidence,
Acceptance, rating, release approval, or specialist safety/cybersecurity
approval is assumed.

```yaml
task_id: "0020-10"
feature_id: "0020"
role: implementer
architecture_decisions:
  - decision: "Assemble an immutable source manifest and deterministic cross-product consistency package; return child defects instead of editing child products."
    derives_from:
      requirements: ["TODO.md#feature-0020-goal", "TODO.md#feature-0020-acceptance-envelope"]
      decision_records: ["DEC-0020-001", "DEC-0020-002", "DEC-0020-003"]
      existing_architecture: ["0020-01 through 0020-09 committed dossiers and contracts"]
      repository_evidence: ["TODO.md@874e6209e936df2c1eebf5e8444972d9a226a625", "0020@032fcb6ccc"]
    authority_or_assumption: authority
prerequisites:
  - task_id: "0020-01"
    derives_from: "approved assessed-unit and supplied-product boundary"
  - task_id: "0020-02"
    derives_from: "canonical evidence origins and refuse-at-use contract"
  - task_id: "0020-03"
    derives_from: "responsibility and authority matrix"
  - task_id: "0020-04"
    derives_from: "32-process applicability matrix and selected 14-process profile"
  - task_id: "0020-05"
    derives_from: "conditional-process dispositions and external interfaces"
  - task_id: "0020-06"
    derives_from: "cybersecurity and functional-safety applicability boundary"
  - task_id: "0020-07"
    derives_from: "Level-1 assessment-input and official-outcome worksheet contract"
  - task_id: "0020-08"
    derives_from: "controlled work-product and evidence catalogue"
  - task_id: "0020-09"
    derives_from: "selected-profile execution register and consumer edges"
planned_order:
  position: 10
  order: ["0020-01", "0020-02", "0020-03", "0020-04", "0020-05", "0020-06", "0020-07", "0020-08", "0020-09", "0020-10"]
  order_matters_because: "0020-10 must bind the complete terminal child population and is the Feature's only integrating node."
test_scope:
  derives_from: ["cross-product consistency risk", "evidence-origin refusal contract", "Feature closure and checkpoint criteria"]
  kind: integration
  evidence: "manifest schema/semantic checker; wrong-origin, missing, stale, unsupported-claim, and child-conflict fixtures; legacy_task_doctor.py; process_doc_doctor.py; git diff --check"
capability_profile:
  capability_class: unprivileged
  rights: ["read repository and Git history", "write the declared Task paths"]
  data: ["committed 0020-01 through 0020-09 products, claims, REFs, and review records"]
  tools: ["Git", "stdlib Python", "repository validation tools"]
  execution_needs: direct
  cognitive_demand: high
  independence: "Implementer distinct from this Architect; privileged Integrator distinct from both; no self-Acceptance."
branch:
  parent: "Feature 0020 integration baseline containing this governance candidate and every done prerequisite tip"
  name: "0020-10"
  create: "Project Lead pre-provisions from the current parent; merge every done-but-unintegrated 0020-01 through 0020-09 tip before first mutation."
```

The implementation product write scope is exactly
`docs/dossiers/0020-terminal-integration-package.md`,
`docs/dossiers/0020-terminal-integration-manifest.json`, and the `0020-10`
block of `TODO.md` for marker/claim/REF bookkeeping. The worker's canonical
claim path is added by the atomic award from its immutable owner token before
mutation; it does not widen the product scope. The JSON manifest must record
the candidate commit, one entry per child with Task ID, implementation REF,
claim/review inputs, product paths and SHA-256 digests, a consistency-result
entry for every named boundary, every executed validation with exit status,
and every finding with disposition, owner, and immutable evidence reference.
The Markdown package explains the same evidence, contrary evidence, recovery,
and the exact unchanged candidate handed to the separate Integrator.

The `cognitive-demand-rubric@v1` vector is
`scope=high/reasoning=high/context=high/ambiguity=medium/verification=high`, so
the aggregate is `high`: nine heterogeneous contracts must agree; the binding
decisions resolve the architecture choice but not the transitive evidence or
recovery work. Advisory budgets are 16k–32k implementation tokens, 4k–8k
test-design tokens, CPU under 20 minutes, memory under 1 GiB, and no network or
external-system time. An unresolved child contradiction is a returned finding,
not license to guess or widen scope.

## Conditions

- **C-01 — Separation:** the `0020-10` Implementer is distinct from this
  Architect; the checkpoint Integrator is distinct from both. No self-Acceptance.
- **C-02 — Child preservation:** `0020-10` does not edit `0020-01` through
  `0020-09` products. A material inconsistency becomes a bounded returned finding.
- **C-03 — Evidence boundary:** documentation, tools, templates, and controlled
  scenarios remain non-ECU execution and cannot satisfy an ECU outcome claim.
- **C-04 — Profile stability:** the 14-process selected profile, shared/external
  responsibility dispositions, and conditional SYS/VAL boundaries are inputs,
  not choices reopened by the integrating Task.
- **C-05 — Closure:** green aggregation is neither Acceptance nor Feature
  closure. The mandatory checkpoint and prerequisite-closed Acceptance remain
  separately authorized actions.
- **C-06 — Downstream reach:** existing Feature-level `:0020` prerequisites are
  unchanged. No downstream child Task receives a new direct prerequisite.
- **C-07 — Recovery:** before integration, abandon the candidate without
  touching completed products; after integration, supersede through an
  append-only decision and reviewed backlog correction.
- **C-08 — Resource bounds:** implementation is documentation/evidence assembly,
  direct Git plus stdlib validation, no network or credentials, CPU under 20
  minutes, memory under 1 GiB, advisory 16k–32k tokens, cognitive demand `high`.

## A1 and checkpoint rationale

```yaml
target_policy_check:
  field: A1-target-policy-integrability
  verdict: fits
  checked_target: main
  basis: "main@874e6209e9 contains all nine terminal implementation nodes and the normative exactly-one terminal integration-floor rule; the correction adds the missing node without changing child products or selected-profile semantics"
  checked_at: "2026-08-29T18:56:00Z"
  recorded_by: "Architect agent:data:0020-feature-closure-architecture:1788029226494-1b18733c"
```

`0020-10` is `Integration review: mandatory` because it is the Feature's sole
terminal integrating Task and its verdict controls whether a shared ECU scope
and evidence boundary can be consumed by eleven downstream Features. A false
pass could propagate substituted evidence or an inconsistent responsibility
boundary into release and assessment gates.
