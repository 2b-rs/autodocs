---
schema_version: "1.0"
id: "0035-03"
level: "task"
parent: "0035"
state: "open"
visibility: "internal"
prerequisites:
  - "0033-10"
  - "0033-12"
  - "0033-13"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:2578"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Verifizieren und schliessen, dass "Evidence references" nutzerverstaendlich als getrenntes Link-Feld und optionale Freitextzeile statt als Kind/Value/Note-Rohschema erscheinen. PREREQ: 0035-03:0033-10, 0035-03:0033-12, 0035-03:0033-13

## Scope

- **Befund (2026-08-15, Nutzer):** Die aktuelle Darstellung mit `Kind` (Platzhalter `quote|url|note`), `Value` und `Note (optional)` ist aus Nutzersicht komplett unverstaendlich. Zusaetzlich werden drei leere Referenzzeilen gleichzeitig angeboten, was den Eindruck einer Pflichteingabe verstaerkt.
  - **Akzeptanzkriterien:** Der Nutzer bekommt ein klar beschriftetes Eingabefeld fuer einen Link sowie eine Eingabezeile fuer Freitext; die interne Repraesentation bleibt zum Evidence-Schema aus 0021-02 kompatibel (der `kind` wird abgeleitet statt vom Nutzer getippt); der optionale Charakter ist sichtbar; Link-Eingaben werden validiert und eine ungueltige Eingabe blockiert das Absenden nicht stumm; Barrierefreiheit aus 0021-05 (Labels, Fokus, Fehlermeldungen, Tastaturbedienung) bleibt erfuellt.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

UI-Aenderung und Tests committed mit `REF`; ein Beispielpaket mit Link- und Freitext-Evidence validiert gegen das Schema.
