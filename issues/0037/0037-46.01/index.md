---
schema_version: "1.0"
id: "0037-46.01"
level: "subtask"
parent: "0037-46"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2130"
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
  - id: "AC-007"
    status: "active"
  - id: "AC-008"
    status: "active"
  - id: "AC-009"
    status: "active"
  - id: "AC-010"
    status: "active"
  - id: "AC-011"
    status: "active"
  - id: "AC-012"
    status: "active"
  - id: "AC-013"
    status: "active"
  - id: "AC-014"
    status: "active"
  - id: "AC-015"
    status: "active"
  - id: "AC-016"
    status: "active"
---

## Goal

Implement and test the approved conflict-safe runner queue, dispatcher, complete action registry, and structured result protocol without activating it. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded as future transport infrastructure; preserve the implementation as historical evidence and a possible source of reusable safety invariants.
  - **Successor recheck (2026-08-22, Seven-Icheb, per `AGENTS.md` "Completing implementation work" step 5):** `0037-07` closed `[x]` this pass. Of this Task's two prerequisites, `0037-07` is now terminal but `0038-16.01` is still `[ ]` (open, with its own nine unresolved prerequisites). `0037-46.01` is therefore **not yet globally eligible** — recheck again once `0038-16.01` closes. **[ÜBERHOLT, 2026-08-22, kathryn — diese Notiz war beim Schreiben bereits falsch.]** Sie entstand gegen ein regrediertes `main`: Commit `4b95d99db` hatte `0038-16.01` versehentlich von `[x]` auf `[ ]` zurückgesetzt und seine Lieferergebnisse gelöscht. Die Reparatur `27930dc9c` hat beides wiederhergestellt; `0038-16.01` steht auf `main` wieder auf `[x]`. **Beide Prerequisites von `0037-46.01` sind terminal, der Task ist eligibel.** Unabhängig hergeleitet von `Seven` und `kathryn` am 2026-08-22. Die Notiz bleibt append-only stehen, weil sie zeigt, wie ein Datenverlust sich in abgeleitete Falschschlüsse fortpflanzt, die die Reparatur des Inhalts überleben.

## Acceptance criteria

- **AC-001** Implement `_src/tools/runner_dispatch.py`, `_src/runner/actions-v1.json`, schemas, and a rigorously ignored `.runner/` runtime root. Sandboxed agents build complete requests under `.runner/drafts/<agent>/<request-id>/` and publish only by same-filesystem atomic rename to `.runner/requests/...`
- **AC-002** the dispatcher ignores drafts/incomplete entries, validates manifest/member digests, and atomically claims ready requests. Results/logs/cancellation/leases are immutable or append-only under `.runner/`, never tracked or treated as source, and clean-tree/commit guards exclude only declared runtime paths. Enforce typed actions/arguments, base/epoch/ref/dependency/resource/network/credential/read/write preflight, timeout/worker limits, isolated temporary roots, mutation guards, progress/results, cleanup, retry identity, and no secret persistence. The reviewed registry must cover every action identified by `0037-37`: discovery
- **AC-003** fetch/recheck
- **AC-004** protected integration/push/PR
- **AC-005** validators/tests/probes/generators/builds/browsers
- **AC-006** package/tool provisioning
- **AC-007** external policy setup
- **AC-008** signature creation through approved handles and verification
- **AC-009** path-limited commits
- **AC-010** two-commit REF closure
- **AC-011** claim `git update-ref` CAS
- **AC-012** approval/cutover ref creation and append CAS
- **AC-013** detached worktrees/temporary refs
- **AC-014** exact-tree cutover
- **AC-015** rollback/ref cleanup
- **AC-016** and recovery. Generic shell action is forbidden

## Definition of Done

Source/fixture tests run through the qualified legacy runner and cover draft visibility, concurrent publication/claiming, stale base/epoch/ref, scope collision, unknown/generic action, unavailable dependency/credential, network denial, timeout/cancel, partial mutation, crash/restart, tampered result, retry, every Git/ref action's rollback, and claim retention; the implementation commit does not change the live runner protocol.
