---
schema_version: "1.0"
id: "0036-03"
level: "task"
parent: "0036"
state: "open"
visibility: "internal"
prerequisites:
  - "0036-01"
  - "0036-02"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:396"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Normative Dokumentation des **Seitenerzeugungsprozesses** fuer illustrierte Prozessseiten in `docs/pipeline/` anlegen. PREREQ: 0036-03:0036-01, 0036-03:0036-02. REF: 9d3511eadd839ced304e9b3877738109173d4333 in `docs/pipeline/` anlegen. PREREQ: 0036-03:0036-01, 0036-03:0036-02

## Scope

- **Akzeptanzkriterien:** Beschreibt die Artefaktkette von normativer Prozessdoku → Quellen unter `_src/`/`_src/sources/pages/` → optionalem KI-Agenten-Schritt fuer nutzerfreundliche Erklaertexte/Illustrationen/Diagrammtexte → i18n extract/merge → `generate.py` → validiertes HTML; definiert, ob/wo eine Instruktionsdatei im Stil `ANWEISUNGEN.md` liegt, wofuer sie normativ ist und wie sie versioniert/invalidiert wird; definiert feste Einsprungpunkte/Anker (z. B. pro Prozess und pro Abschnitt), auf die Dialoge spaeter tief verlinken duerfen; referenziert `published-process-page.md`, statt dessen Architektur zu duplizieren oder zu widersprechen.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Neues Dokument in `docs/pipeline/` committed mit `REF`; enthaelt mindestens einen expliziten Abschnitt zu Deep-Link-Stabilitaet/Ankerpolitik und einen zu KI-Agenten-Instruktionen als Pipeline-Artefakt.
