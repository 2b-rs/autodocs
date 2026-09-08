---
schema_version: "1.0"
id: "0037-33"
level: "task"
parent: "0037"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-31"
  - "0037-32"
  - "0037-34.01"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2522"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0037-33:0037-31, 0037-33:0037-32, 0037-33:0037-34.01 Obtain the signed process/security/release cutover decision for the exact candidate and prepared patch.

## Scope

- **Rescoping pending (`0037-49`, `DEC-0044-014`):** This Task's role/signer requirements below still name distributed roles. When this Task is next worked, rescope them to the single repository-owner authority per `0037-49`'s single-authority model before implementing against them.

## Acceptance criteria

- **AC-001** Registered process, security/privacy, and release signers review source/candidate/control-base commits, patch/artifact digests, migration/validation/audit reports, generated diff, residual limitations, exact public projection, complete `SANDBOX.md`/`AGENTS.md`/`PRIVILEGED.md`/`agent-workflow.json` capability/runner/phase/epoch switch, zero-privileged-agent execution profile, grunt first-attempt qualification and stale-client results, non-bypassable integration-gate evidence, zero active sessions/claims, write freeze, signed point-of-no-return implications, post-activation forward recovery, support, and frozen-window rollback/event replay. Approval commits branch from the recorded control base onto dedicated immutable refs and do not advance integration HEAD
- **AC-002** each record names package/policy revision, exact digests, validity/revocation, and conditions. Rejection/change keeps legacy authority and opens bounded remediation
- **AC-003** no candidate/patch author self-approves. Because the legacy source is frozen, waiting/approval state is recorded on the transaction ref while this Task remains `[p]`, not by changing `TODO.md` to `[u]`

## Definition of Done

Bootstrap-verified SSH-signed approval refs authorize one unchanged patch and control base; the post-cutover reference commit later materializes this Task's closure.
