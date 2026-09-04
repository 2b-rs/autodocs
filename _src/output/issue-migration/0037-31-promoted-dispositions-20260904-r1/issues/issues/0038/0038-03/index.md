---
schema_version: "1.0"
id: "0038-03"
level: "task"
parent: "0038"
state: "open"
visibility: "internal"
prerequisites:
  - "0038-01"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1652"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

PREREQ: 0038-03:0038-01 Add an automation-safety validator and remediate high-risk tracked scripts. REF: ec251f2a69b18e9d90f3cac53bedfa7fa248e338 **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-03-Commit)`). Abgenommene Baseline `ec251f2a69b18e9d90f3cac53bedfa7fa248e338`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). 121 automation tests, Live-Scan 99/54/28/26/0/0, 11+7=18 extraction+build-report Tests — alle exakt am eigenen REF bestätigt.

## Scope

- **Closed (2026-08-17):** Committed the stdlib automation-safety gate, 28 exact blocking dispositions, eight historical fixtures, project-validator integration, operator documentation, and three fail-closed remediations. Independent blocker/high review was clean. Isolated current-HEAD validation passed 121 automation tests, 11 extraction-campaign tests, 7 build-report tests, the 99-file live scan (54 findings, 28 disposed critical, 26 advisories, zero unresolved/policy errors), audit-helper generation/project checks, and full `_src/validate.py`; provenance receipt SHA-256 `e6491efc6de69270718507e668ae28961eaee35eb02f8bc64b97f6e110db115d`.

### Campaign B — Make backlog, claims, collisions, and context mechanical

## Acceptance criteria

- **AC-001** Stable rules detect unchecked mutating subprocesses, unconditional PASS, broad/wildcard staging or deletion, protected-ref force push, hard-coded remote/identity, shell execution, repair mixed into validation, mutation before gates, ignored commit return codes, and missing recovery/result state. Historical patterns from `_src/tools/link_verification_evidence.py`, publish tooling, and old runner envelopes are fixtures
- **AC-002** findings name exact path/line/rule and distinguish deliberate per-item resumability from accidental continuation

## Definition of Done

`_src/validate.py` runs the checker; every critical finding is fixed, narrowly suppressed with rationale/owner/expiry, or represented by a blocking Task; no false-green fixture passes.
