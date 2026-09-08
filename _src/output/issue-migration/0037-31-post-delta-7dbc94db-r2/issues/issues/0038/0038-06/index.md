---
schema_version: "1.0"
id: "0038-06"
level: "task"
parent: "0038"
state: "closed"
visibility: "internal"
prerequisites:
  - "0037-05"
  - "0038-04"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1686"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

PREREQ: 0038-06:0038-04, 0038-06:0037-05 Implement explicit plus derived write-scope collision planning. REF: 67031b6df38e502125121851fa7f59a4801b216b **Acceptance: ✓** (2026-08-25, Integratorin `belanna`, unabhängig von Implementierer `tobias.anton (0038-06-Commit)`). Abgenommene Baseline `67031b6df38e502125121851fa7f59a4801b216b`; Teil der durch Checkpoint `0038-33` induzierten prerequisite-closed Batch (Review-REFs `97475b1e9`/`b221fcd60`/`890353886`/`4fddf329e`/`645790841`/`c54c2f5e5`). 24+42=66 Tests am eigenen REF (Planner + Doctor-Regression).

## Scope

- **Closed (2026-08-17):** Committed the stdlib-only read-only planner over normalized active claims, the authoritative `issue-regeneration-dag@v1`, and identity-bound Git/runner/action snapshots. It detects exact, ancestor, read/write, source-derived, sole-writer, promotion-group, dirty-tree, runner, symlink/type, and incomplete-scope hazards; automatically projects matching file/directory foreign claims through producer chains; blocks all 20 aggregate overlap cases including the `0036-05`/`0036-06` incident; and permits the genuinely disjoint page/locale case. Validation passed 24 planner tests, 42 doctor regressions, JSON/diff checks, and an explicit two-file safety scan with zero findings/policy errors. Independent review `0633e0d2-d8d4-4d14-baba-b9a993cc7015` returned `ACCEPT`. Isolated full validation reproduced the unrelated 12-link/six-file baseline and passed after candidate-only empty shims. Provenance receipt SHA-256 `258dceb80db06e4730cc3265354fa64e747b8a06608d64a5f8975117c8d91a37`.

## Acceptance criteria

- **AC-001** Expand source paths through known generator/report/i18n/publication output ownership, compare them with active claims and runner/Git snapshots, identify exact/direct versus derived collisions, and calculate a safe serialization or disjoint execution plan. Include `0036-05`/`0036-06`-style source-disjoint but language-tree-overlapping fixtures

## Definition of Done

The planner blocks every known overlap fixture before mutation, permits two genuinely disjoint agents, explains the conflicting producer/output edge, and feeds the future queue scope model rather than maintaining a second DAG.
