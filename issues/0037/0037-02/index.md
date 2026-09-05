---
schema_version: "1.0"
id: "0037-02"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-02.01"
  - "0037-02.02"
  - "0037-02.03"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2001"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-02:0037-02.01, 0037-02:0037-02.02, 0037-02:0037-02.03 Complete the review-ready `issue-item@v1` data-format work package. REF: 91a4b99fb07948cdea4c71d18ada49f4d661ea42 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-02:c3f8a91e6b52`). Abgenommene Baseline `91a4b99fb07948cdea4c71d18ada49f4d661ea42`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). Manifest-Digests (3) unabhängig neu berechnet, 0 Abweichungen.

## Scope

- **Backlog repair (2026-08-16):** The former Definition of Done required entries in the architecture review package produced by downstream Task `0037-37`, while `0037-37` cannot start until `0037-02` closes. This semantic deadlock is resolved by making this parent own a package-local digest manifest that `0037-37` later verifies and incorporates; acceptance is preserved rather than deferred or weakened.
  - **Closure (2026-08-16):** All three Subtasks are `[x]` (`0037-02.01` REF `5b93372971c7eda5455f323f0c9a59d46db2f5a4`, `0037-02.02` REF `55abebbb5a4f251da5dc07c6077082d0c5e03fa3`, `0037-02.03` REF `70bfe4aee2bf4d0a33711c1d42b743a62c4f1ace`). Committed `docs/pipeline/issue-item-v1-package.json` at base commit `8c3e8625ff3018a103f956dffa1ed9896ebd0d4f` lists all three artifacts with SHA-256 digests, fixture sets, the schema-fixture validator, and cross-contract consistency check results (`OK: 3 valid + 14 invalid fixtures behaved as expected`). Per the backlog-repair note above, this manifest is the local intermediate deliverable that `0037-37` verifies and incorporates; it does not itself require `0037-37` to exist first. Claim: `TODO-perplexity-0037-02-c3f8a91e6b52.md`.

## Acceptance criteria

- **AC-001** All three Subtasks pass against the same examples and normalized-object contract
- **AC-002** no parser, importer, or writer implementation may begin from a partial profile. Create `docs/pipeline/issue-item-v1-package.json` listing every normative document, schema, fixture set, and validator with repository path, SHA-256 digest, producing Task and commit REF, plus the cross-contract consistency checks and result

## Definition of Done

`0037-02.01` through `0037-02.03` are complete; their contracts and examples are package-level consistent; and the committed package-local manifest is complete, machine-readable, digest-verified, and ready for independent verification and incorporation by `0037-37`.
