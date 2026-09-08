---
schema_version: "1.0"
id: "0037-50.02"
level: "subtask"
parent: "0037-50"
state: "closed"
visibility: "internal"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2182"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

Extract and prove the singleton retirement guard before automatic rollback is wired. REF: `f3522aaaa80d851f3ba28744b08956a52eb63275`.

## Scope

- **DEC-0037-002 disposition:** Superseded. William released the implementation claim at `3b584a9c95876e54d04966c152e80db9142e1ccf`; preserved evidence tip `c640adc58b861280f584f97b3c01a632a6ef762b`.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** Architect `data`, proposal `164890ec3c`: behavior-preserving extraction and collision hardening remain dormant until `.04`; the complete live boundary is reviewed at `.05`.

## Acceptance criteria

- **AC-001** Add `runner-host/lib/retirement_guard.sh`, source it script-relative from `runner-host/run-loop.sh`, update `runner-host/MANIFEST.json`, and add `_src/tests/test_run_loop_retirement_guard.py`. Prove healthy-queue rejection, sentinel exemption, restored-legacy pass-through, malformed-selector failover handling, and two same-second rejections without overwrite
- **AC-002** do not activate or deploy rollback in this package

## Definition of Done

`bash -n` passes for both shell files; the focused test passes with all five cases; manifest digests and before/after behavior are retained; automation-safety and `git diff --check` pass; no host, governance, acceptance, integration, push, or external mutation occurs.
