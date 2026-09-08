---
schema_version: "1.0"
id: "0037-50.05"
level: "subtask"
parent: "0037-50"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2200"
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

Integrate the corrective packages, perform hermetic and operator-assisted live qualification, retain evidence, and pin the fresh `0037-46.02` candidate. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded; there is no live queue/singleton cutover candidate to integrate or deploy.
  - **Integration review: mandatory.** **Rationale (architect):** Architect `data`, proposal `164890ec3c`: this is the sole package that integrates both admission gates, changes the external runner-host service, and claims atomic failover. A defect can stop all sandboxed work or permit concurrent mutation protocols; Geordi or another freshly authorized independent privileged Integrator must pin and review the exact terminal candidate before the parent checkpoint can pass.

## Acceptance criteria

- **AC-001** Merge exact `.02`--`.04` tips without source authoring here
- **AC-002** retain `retirement-guard-results.json`, `live-failover-results.json`, `evidence-summary.md`, and `SHA256SUMS.txt`
- **AC-003** advance only `/tmp/runner-0037-46.02` to the pinned candidate
- **AC-004** use only synthetic non-secret requests to prove healthy singleton rejection, unattended rollback before the same safe singleton request executes, rollback-failure parking with queue blockage, active-claim drain, and selector-flip rejection with zero mutation. Append the corrective activation event to `docs/pipeline/legacy-handoff-manifest.md` on `main` only after evidence is immutable

## Definition of Done

All focused suites, shell syntax, evidence checksums, legacy manifest/task doctors, automation-safety, changed-path, clean-worktree, and residual-finding comparisons are retained with exact commands/results; before/after selector/service and host HEAD digests, request/result/event/marker digests, recovery steps, governance addendum REF, and fresh candidate tip are immutable; Data does not implement or accept, and a fresh independent Geordi assignment is requested only after this package is complete.
