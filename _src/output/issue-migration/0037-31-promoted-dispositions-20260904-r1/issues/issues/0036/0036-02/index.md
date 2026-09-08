---
schema_version: "1.0"
id: "0036-02"
level: "task"
parent: "0036"
state: "open"
visibility: "internal"
prerequisites:
  - "0035"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:392"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Normative Prozessbeschreibung fuer den Flag-for-review-Antragsprozess (`review-request-package@v1`) in `docs/pipeline/` um die 0035-Erkenntnisse (Storage-Abgrenzung zu `review.js`, Root Cause des Submit-Defekts) ergaenzen bzw. konsolidieren. REF: 8c3c155a10639d665c9892b6803fb5e55e3d5be5 (`review-request-package@v1`) in `docs/pipeline/` um die 0035-Erkenntnisse (Storage-Abgrenzung zu `review.js`, Root Cause des Submit-Defekts) ergaenzen bzw. konsolidieren.

## Scope

- **Akzeptanzkriterien:** Grenzzieht klar zu 0036-01 ab (Entscheidung vs. Antrag, siehe Feature-0035-Diskussion); dokumentiert nach Abschluss von Feature 0035, welchen Speicher- und Absendeweg der Flag-for-review-Request tatsaechlich nutzt.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Dokument committed mit `REF`; PREREQ: 0036-02:0035 (Feature 0035 muss die tatsaechliche Ziel-Architektur festgelegt haben, sonst wuerde diese Aufgabe eine noch nicht getroffene Implementierungsentscheidung vorwegnehmen).
