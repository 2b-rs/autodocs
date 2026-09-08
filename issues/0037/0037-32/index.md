---
schema_version: "1.0"
id: "0037-32"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-34.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2508"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0037-32:0037-34.01 Conduct an independent signed pre-cutover audit of the exact frozen candidate and prepared final authority tree.

## Scope

- **Rescoping pending (`0037-49`, `DEC-0044-014`):** This Task's role/signer requirements below still name distributed roles. When this Task is next worked, rescope them to the single repository-owner authority per `0037-49`'s single-authority model before implementing against them.

## Acceptance criteria

- **AC-001** A sandboxed audit agent submits the exact pre-cutover runner profile from `issues/_policy/audit-profiles.json`: all mandatory checks/high-risk items (including Feature `0021` and placeholders), all authority/privacy boundaries, and deterministic seeded samples meeting each state/type minimum. A registered quality signer who did not author the candidate independently reviews the retained results, verifies the deterministic control-closure delta, absence of evidence/acceptance/authority inflation, exact agent-instruction bundle/authority epoch/stale-client guards, policy-semantic continuity for owned-work resumption, parent closure, autonomous backlog repair, `[u]` boundaries, collaboration/tooling suggestions, and one-use non-escalation runner semantics, graph/public-projection/i18n/HTML parity, and the hermetic causal chain in both candidate and exact prepared authority tree, and records stable findings against exact artifact digests. Any candidate/profile/policy change invalidates the audit. Evidence is written to the transaction/approval refs while this Task remains `[p]`
- **AC-002** the required post-cutover reference commit materializes its closure

## Definition of Done

SSH-signed audit recommendation, command/result manifest, sample inventory, and closed finding log meet every profile threshold, pass bootstrap/role verification, and identify the unchanged candidate, or explicitly block cutover.
