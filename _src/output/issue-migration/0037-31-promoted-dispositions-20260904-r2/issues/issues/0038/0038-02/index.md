---
schema_version: "1.0"
id: "0038-02"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-01"
  - "0038-18"
  - "2026"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1627"
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
---

## Goal

PREREQ: 0038-02:0038-01, 0038-02:0038-18 Add durable hard-kill, stale-lock, rollback-conflict, and transaction-resume recovery. REF: `9d8e45bbbeede9a2fd5c6c9471820d76686b743b`.

## Scope

- **Acceptance:** ✓ (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `zed (0038-02-Commit)`). Abgenommene Baseline `9d8e45bbbeede9a2fd5c6c9471820d76686b743b`; Teil der durch Checkpoint `0038-30` induzierten prerequisite-closed Batch. Review-REF `a995f9047`. 35/35 eigene Tests am eigenen REF.
  - **Historical claim (2026-08-17):** Sandboxed agent `perplexity` via `TODO-perplexity-0038-02-20260817-0531.md`, `owner_token: agent:perplexity:0038-02:0038-02-impl-20260817-0540`, request ID `0038-02-impl-20260817-0540`, `base_commit: 5b306e23706a3455d995eb8dd99edf16ce43f372`. The current user declared that session abandoned on 2026-08-18; its immutable identity is retained as provenance, not an active lease.
  - **Takeover claim (2026-08-18):** Explicitly assigned by the current user to privileged Implementer `TODO-zed-0038-02-20260818T133931Z-ba3432d6d0cb.md`; owner_token `agent:zed:0038-02:20260818T133931Z-ba3432d6d0cb`; canonical branch `0038-02`.
  - **Progress (2026-08-17):** Recovery implementation and 31 focused hermetic tests were complete; focused tests and `git diff --check` passed. Broader `_src/validate.py` was blocked by the sandbox macOS Python multiprocessing semaphore restriction, and the then-current runner lacked the focused closure profile, so the Task correctly remained `[p]` with its claim retained.
  - **Implementation completion (2026-08-18):** After prerequisite `0038-18` became terminal, the current user explicitly authorized privileged takeover of both abandoned claims. Independent validation passed: 35 focused runner-transaction tests in 78.237 seconds, Python compilation, and scoped `git diff --check`. Recovery documentation was corrected to match implemented stale-lock, signal, doctor, recover, and finalization behavior. A material takeover finding was fixed: standalone finalization no longer glob-selects an arbitrary Task claim; journal identity now binds the exact claim and branch, recovery rejects ambiguous request journals, and finalization fails closed on locks, unpublished/unreachable commits, identity or branch mismatch, and an existing archive while preserving competing claims. No project-wide validation pass is claimed. This node has no `Integration review: mandatory` attribute, so no `Acceptance: ✓` record is required or created.

## Acceptance criteria

- **AC-001** Journal every mutation/ref/finalization boundary with PID/process start identity, request/owner/base, preimage/promoted digests, backup paths, and commit objects
- **AC-002** add signal/process-group handling
- **AC-003** retain backups on incomplete rollback
- **AC-004** provide a read-only doctor plus explicit recover/finalize operations that never delete a live lock or overwrite newer edits. Inject termination before/after each file, commit-object, CAS, TODO, result, and claim boundary

## Definition of Done

Crash/restart tests prove each state is either unchanged, automatically reconciled, or accompanied by one deterministic safe recovery command and retained claim/evidence; no stale lock requires guessing or blind deletion.
