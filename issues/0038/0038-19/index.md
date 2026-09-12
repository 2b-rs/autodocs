---
schema_version: "1.0"
id: "0038-19"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-45"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1870"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-19:0037-45 Define the typed branch/merge/integration action contract for legacy and post-cutover execution. REF: 18b563144a87ab5fb830c6f663eccd4934c13667

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `seven-mezoti (0038-19-Commit)`). Abgenommene Baseline `18b563144a87ab5fb830c6f663eccd4934c13667`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. eigener Fixture-Validator 10/10 (6 positiv, 4 negativ, alle vier Pflicht-Negativkategorien vorhanden).
  - **Claim (2026-08-20):** Claimed by unprivileged subagent `seven-mezoti` (dispatched by privileged agent "Seven") via `TODO-seven-mezoti-0038-19-20260820T013543Z.md`, `owner_token: agent:seven-mezoti:0038-19:20260820T013543Z`, `base_commit: 41f70cc7247c95b7f39ea91d9b424b7c4c996607`, branch `0038-19` off Feature branch `0038` (no prerequisite branches to merge; `0037-45`'s content is already present on `0038` at this base).
  - **Validation:** `python3 docs/pipeline/fixtures/0038-19/validate_branch_merge_action_fixtures.py` reports `PASS: 10 fixtures (6 positive, 4 negative)`; all ten fixture request/result instances validate against `issues/_schema/runner-request-v1.schema.json`/`runner-result-v1.schema.json`; all four required negative categories (authority violation, undeclared merge source, stale base/tip, claim-union conflict) are covered by a distinct rule ID; sanity-checked by deliberately sabotaging two positive fixtures and confirming the expected violation is raised. No executable/generated-site change; `_src/generate.py`/`_src/validate.py` not touched or run.
  - **Findings deferred to the integrator (out of this Task's write scope):** (1) `branch-workflow.md`'s "Grunt-permitted merges are limited to Subtask→Task" sentence in "Capability-class execution of branch operations" reads stricter than its own checkpoint-based "Merge authority and direction" framing and than Task `0038-20`'s committed acceptance text (which keys authority on the *target* branch, not the source item's level); a single additive clarifying line would resolve the tension without restructuring the document. (2) `issues/_schema/agent-capability-v1.schema.json`'s frozen `class` enum (`sandboxed-grunt`/`privileged`) still lacks the `unprivileged` capability class added by commit `993ceffbc`; separately, `AGENTS.md`'s own citation of `docs/dossiers/dec-capability-classes.md` for that decision does not resolve to an existing file in this worktree — a pre-existing dangling cross-reference, not introduced by this Task.

## Acceptance criteria

- **AC-001** Add `docs/pipeline/branch-merge-actions.md` specifying, against the frozen `0037-45` request/result contract, the fixed typed actions `base-branch` (base an item branch off its parent branch) and `merge-prereqs` (merge declared done-but-unintegrated `[x]`/`[w]` prerequisite branches), plus the Task→Feature integration action. For each: exact inputs, expected parent base and source-branch tips, owner-token/authority binding, the Subtask→Task versus Task→Feature/Feature→`main` authority split, append-only claim-record auto-union (never rewrite a foreign `owner_token`), 2-parent merge-commit and conflict/fail-closed behavior, recorded-merged-tip evidence, and the result schema. No executable change
- **AC-002** map every action to a `0037-46.01` typed action or `0037-46.02` retirement trigger

## Definition of Done

The contract validates against the `0037-45` request/result schema with zero unmapped or multiply-authoritative actions; positive/negative examples cover authority violation, undeclared merge source, stale base/tip, and claim-union conflict; `branch-workflow.md`, `AGENTS.md`, and `SANDBOX.md` cross-references stay consistent; nothing executes.
