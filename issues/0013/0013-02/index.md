---
schema_version: "1.0"
id: "0013-02"
level: "task"
parent: "0013"
state: "accepted"
visibility: "internal"
prerequisites:
  - "0013-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2869"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0013-02:0013-01 Create and approve a versioned stakeholder-requirements baseline with stable IDs, source, rationale, priority, acceptance criteria, status, change history, and validation method. Claim: `TODO-beverly-0013-02-1787972130857-fe98737a.md`. Candidate REF: `283af866979a504c7e7e02de7f087ee6d32492f9` (`docs/dossiers/req-0013-02-stakeholder-requirements-baseline.md`, version `0.1.0-candidate`). No approval and no `Acceptance: ✓`.

## Scope

- **Candidate evidence (2026-08-29, Beverly):** The exact `0013-01` terminal tip is the branch base. The candidate defines 14 unique atomic requirements; every record contains source, rationale, priority, binary acceptance criteria, status, validation method, affected stakeholders/interfaces, assumptions/exclusions, and change history. It preserves the Management product boundary and explicitly disposes `PD-0013-01-01`..`08`. Committed-tree schema counts, source reachability, exact three-path scope, and `git show --check` pass.
  - **`[u]` authority boundary:** Bounded candidate preparation is complete. Approval is not: the customer/intended-use sources, system allocation, kernel/platform and operating-environment sources, applicable external authorities, and especially the stakeholder-baseline approver/change authority (`PD-0013-01-04`) are not assigned. The sole next action is authorized source/authority decision followed by review and approval of the exact candidate revision. Authorship, mailbox traffic, Task completion, Project Lead routing, or repository access is not approval. No downstream start gate is added or changed.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Imported item is represented under the disposable candidate root.

## Management Decision
Decision `decision-1789246527834-1f27fd4f` (msg `1789814945765-2c2bce2d`) approved the baseline. The `[u]` boundary is resolved.
