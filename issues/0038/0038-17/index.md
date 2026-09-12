---
schema_version: "1.0"
id: "0038-17"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1617"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
  - id: "AC-005"
    status: "active"
---

## Goal

Add sandbox execution-authority safeguards and runner-only enforcement. REF: `cdfc9e3bd3a58d4a29e3911b6e7228798a65abb8`. Claim: `TODO-terra-1-0038-17-20260819T000000Z.md`; owner_token: `agent:terra-1:0038-17:20260819T000000Z`.

## Scope

- **Released (2026-08-17):** Previously claimed by sandboxed agent `perplexity` via `TODO-perplexity-0038-17-20260817-1049.md`; released at explicit user request to assign a different agent. No mutating runner request was published under that claim; no committed evidence exists. The claim file is retained for history and is no longer active.

## Acceptance criteria

- **AC-001** Put a conspicuous default-sandboxed execution gate at the top of `SANDBOX.md`
- **AC-002** require claims to record capability class, execution authority, and startup review
- **AC-003** state explicitly that sandboxed agents may directly edit files under `/tmp` but must use the runner for scripts, shell, Git, tests, generators, browsers, package managers, network clients, and other execution-capable actions
- **AC-004** add a runner-only commit assertion to `AGENTS.md`
- **AC-005** and add deterministic repository-side validation with positive and negative fixtures for missing/contradictory authority fields and direct-execution claims. Document runtime tool-policy denial as an external platform requirement without claiming repository enforcement can configure the host

## Definition of Done

Updated contracts are mutually consistent, the validator names exact path/field/rule failures, clean fixtures pass, violating fixtures fail, focused and project validation pass through a claim-bound runner request, and path-limited implementation plus separate REF bookkeeping commits are retained.
