---
schema_version: "1.0"
id: "0037-06.03"
level: "subtask"
parent: "0037-06"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-03"
  - "0037-05"
  - "0037-06.02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2076"
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
  - id: "AC-006"
    status: "active"
---

## Goal

PREREQ: 0037-06.03:0037-03, 0037-06.03:0037-05, 0037-06.03:0037-06.02 Define freeze, candidate promotion, atomic authority switch, and rollback without event loss. REF: 4e05155775c86192686153db52e036635dfadba6 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `agent:perplexity:0037-06.03`). Abgenommene Baseline `4e05155775c86192686153db52e036635dfadba6`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). issue-cutover-rollback.md + Schema + 7/1 Fixtures, JSON gültig.

## Scope

- **Claim (2026-08-16):** Claimed by sandboxed agent `perplexity` via `TODO-perplexity-0037-06.03-20260816-1426.md`, `owner_token: agent:perplexity:0037-06.03:0037-06.03-20260816-1426`, request ID `0037-06.03-20260816-1426`, `base_commit: pending-discovery`. Prerequisites `0037-03`, `0037-05`, and `0037-06.02` are terminal.

## Acceptance criteria

- **AC-001** Pin source/candidate/decision/cutover watermarks
- **AC-002** define freeze ownership/enforcement, candidate immutability, prepared patch verification, single-commit switch, generated legacy headers, process/agent entry-point update, and detached-worktree rollback rehearsal. After the final legacy watermark, Tasks `0037-31`, `0037-34.01`, `0037-32`, and `0037-33` remain `[p]`
- **AC-003** their gate evidence—not alternate backlog state—is stored as immutable records on a protected append-only, fast-forward-only, compare-and-swap `refs/autodocs/cutover/0037/<transaction-id>` history and dedicated approval refs. `0037-34.01` prepares the final authority tree containing the candidate plus the deterministic closure delta for `0037-31`/`0037-34.01`
- **AC-004** `0037-32` audits both candidate and exact final authority tree. The required post-cutover reference commit closes `0037-32`, `0037-33`, `0037-34.02`, and aggregate Task `0037-34` against the real audit/approval/cutover refs. Approval refs branch from the recorded control base and do not advance the integration parent. The final quiescence barrier atomically changes the live selector to a new `legacy-frozen` epoch after all pre-freeze work, rejects new/mutating legacy sessions, and is digest-bound to the final source watermark. Issue writes remain frozen from that watermark through signed post-cutover audit and Task `0037-40`
- **AC-005** under this selected cutover profile, the validator satisfies start gates among `0037-31`–`0037-40` from the signed append-only transaction records while item markers remain `[p]`, and only `0037-40` materializes their closures. Rollback during that window restores the matching `legacy-restored` instruction epoch plus legacy authority and provenance-only control/audit events. Successful `0037-40` is an explicitly signed point of no return for routine legacy rollback: afterward, emergency response first bumps the issue-store epoch back to a write-frozen phase and uses the forward-repair/export/restore process from `0037-44`
- **AC-006** returning to legacy authority would require a new separately authorized reverse migration. No interval allows edits to both authorities

## Definition of Done

Review-ready state machine, ref topology, control-ledger schema, command-level rehearsal plan, pre/postconditions, freeze enforcement/abort criteria, and no-issue-write rollback fixtures are committed.
