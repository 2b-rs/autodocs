---
schema_version: "1.0"
id: "0037-43"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-09"
  - "0037-42"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2321"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-43:0037-09, 0037-43:0037-42 Provision and prove a non-bypassable integration-policy gate before migration freeze. **REF:** `0ca70a810b6fc7977bad7b2c5bc0a7f4cbcc697d`.

## Scope

- **Rescoping pending (`0037-49`, `DEC-0044-014`):** This Task's role/signer requirements below still name distributed roles. When this Task is next worked, rescope them to the single repository-owner authority per `0037-49`'s single-authority model before implementing against them.
  - **Implementation completion (frozen closure delta):** The substantive product `0ca70a810b6fc7977bad7b2c5bc0a7f4cbcc697d` and canonical integration receipt `867d12f6ac95301a6fa1aaf53649f778feb7c353` are ancestors of the assignment-bound base. Transaction `0037-43-44-closure-delta-1788512992649-36e30730` records implementation completion only; no Acceptance or checkpoint crossing is inferred.

## Acceptance criteria

- **AC-001** Commit `.github/workflows/issue-policy.yml` and its pinned validation entry point
- **AC-002** use the approved external-policy runner action—never a privileged agent—to configure the integration branch to require that exact check for pull requests and direct pushes, disallow force-push/deletion, require up-to-date heads, and disable administrator/role bypass for prohibited issue/instruction/generated-view changes. The check reads `agent-workflow.json` from the candidate tree and enforces its epoch/phase, instruction-bundle consistency, claims, authority, and generated-view rules. Record authenticated branch-rule/repository identity and workflow digest evidence. If the hosting/integration endpoint cannot provide and prove equivalent non-bypassable enforcement, final migration remains blocked rather than relying on local hooks or agent compliance

## Definition of Done

A retained integration test proves a conforming legacy change can merge before cutover and that direct push, skipped hook, stale epoch, hand-edited generated TODO/DONE, legacy claim file, partial instruction switch, force-push, and privileged bypass attempts cannot land; the same fixture proves approved issue-store operations pass after the profile switch.
