---
schema_version: "1.0"
id: "0036-01"
level: "task"
parent: "0036"
state: "open"
visibility: "internal"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:388"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Normative Prozessbeschreibung fuer das Curator-Entscheidungsprotokoll (`review-package@v1`, `review.js`) in `docs/pipeline/` verfassen. REF: f3c266708c85156bd4c7791b36ab84a6fa078c11 (`review-package@v1`, `review.js`) in `docs/pipeline/` verfassen.

## Scope

- **Akzeptanzkriterien:** Beschreibt Item-Schema (`outcome`, `decided_by`, `identity`, `rationale`, `decision_basis`), Speicherort (`ara-review-package-v1`), Sammel-Submit als GitHub-Issue, Verhaeltnis zu `ara-review-github-token-v1`, und den fehlenden formalen Lifecycle-Zustand (kein Queue-Eintrag, da bereits Entscheidung); Konsistenz mit bestehenden `docs/pipeline/`-Dokumenten (`workflow-lifecycle.md`, `roles.md`) wird explizit hergestellt oder Abweichung begruendet.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Dokument committed mit `REF`; Review durch Abgleich mit dem tatsaechlichen Code (`review.js`) ohne Widerspruch.
