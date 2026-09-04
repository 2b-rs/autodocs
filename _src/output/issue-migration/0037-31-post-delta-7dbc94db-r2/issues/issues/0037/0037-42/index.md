---
schema_version: "1.0"
id: "0037-42"
level: "task"
parent: "0037"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-09"
  - "0037-10"
  - "0037-11"
  - "0037-51"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2316"
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

PREREQ: 0037-42:0037-09, 0037-42:0037-10, 0037-42:0037-11, 0037-42:0037-51 Implement and validate the versioned agent-bootstrap and stale-client compatibility boundary.

## Scope

- **DEC-0037-002 execution model:** Bootstrap assumes direct Shell/Git capability. Programmer, Tester, and Runner are process roles; Runner selection does not define or elevate authority.

## Acceptance criteria

- **AC-001** Implement stdlib-only `_src/tools/agent_bootstrap.py doctor --json` before any issue/YAML import and expose it as the approved `agent-doctor` runner action
- **AC-002** sandboxed agents read the selector with non-execution tools and obtain doctor results only through the runner, while privileged agents may invoke it directly
- **AC-003** validate `agent-workflow.json` schema, contract/tool version, authority epoch/profile, write phase/capabilities/transaction ID, policy-file digests, command availability, and consistency with `SANDBOX.md`, `AGENTS.md`, `PRIVILEGED.md`, lifecycle docs, generated-view headers, and repository state. Install the live pre-cutover `legacy-lists` descriptor and update `SANDBOX.md`/`AGENTS.md` so every new sandboxed agent uses runner-backed doctor before pickup, without changing backlog authority. Implement a machine-selected `legacy-frozen` transaction-operator mode before `0037-30`: it forbids ordinary claims/pickup/item edits, permits only named transaction IDs and typed runner actions for `0037-31`–`0037-40`, accepts signed transaction-ledger evidence as the selected-profile start gate while markers remain `[p]`, and enforces immutable expected refs/epochs. Require every mutating command to accept the session's expected authority epoch, re-read the selector immediately before its final compare-and-swap/write, and reject changed epoch, frozen capability, stale transaction, or unsupported tool. Add protected-integration validation that, under `issue-store`, rejects hand-edited `TODO.md`/`DONE.md`, new or changed `TODO-<agent-id>.md`, legacy marker/REF/Feature moves, direct item-state transitions, stale epoch/tool versions, and partial instruction bundles with stable diagnostics naming the current authority and exact re-bootstrap command. `issuectl agent doctor` and the runner action must delegate to the same implementation after cutover

## Definition of Done

Clean-checkout CLI/integration tests run with no network or non-stdlib bootstrap dependency and cover approved legacy operation, legacy-frozen no-claim transaction operators and rejection of ordinary pickup, fresh post-cutover operation, an agent retaining each old instruction path/command, interrupted/partial switch, corrupt/missing selector, unsupported tool, contradictory policy, protected-branch bypass attempt, and rollback; stale agents make no authoritative write and recover after re-reading the switched bundle. A policy-continuity fixture under both writable authority profiles starts with an owned incomplete item plus an open parent whose children are terminal and whose completion text has a downstream semantic deadlock; it proves resumption, issue-store-native intent-preserving repair, package closure, suggestion recording, and continued pickup without a user question, `[u]`, direct generated-view edit, or runner escalation token.
