---
schema_version: "1.0"
id: "0038-09"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0037-41"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1705"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-09:0037-41 Build a portable environment/capability doctor and reusable prepared-environment fingerprint. REF: `b9fc9167a`. **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-09-Commit)`). Abgenommene Baseline `b9fc9167a`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). 23/23 Tests am eigenen REF (unittest test_environment_doctor).

## Scope

- **Completion evidence (2026-08-17):** Portable doctor, prepared-environment schema, 26 hermetic fixture cases, adversarial cache tests, cross-bound protocol checks, bounded local probes, and operator documentation delivered in `b9fc9167a`; focused suite `python3 -m unittest _src.tests.test_environment_doctor` passed 23/23; `python3 -m py_compile _src/tools/environment_doctor.py _src/tests/test_environment_doctor.py` passed; `python3 _src/tools/automation_safety.py --root . --path _src/tools/environment_doctor.py --json` returned `verdict: PASS` with zero unresolved critical/policy findings.

## Acceptance criteria

- **AC-001** Check writable project-local caches, Python/Node modules, browser launch/navigation, Graphviz/fonts, locale/timezone, platform-safe watchdog support, Git identity/operation state, disk/resource bounds, and approved network/credential handles without exposing secrets. Cache the validated dependency fingerprint
- **AC-002** unchanged missing prerequisites fail immediately instead of retrying install/test phases

## Definition of Done

Fixtures reproduce root-owned npm-cache `EPERM`, missing macOS `timeout`, browser navigation/selector failures, unknown phase heartbeats, and dependency drift; one concise result identifies the first actionable gate and safe remediation.
