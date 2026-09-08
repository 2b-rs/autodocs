---
schema_version: "1.0"
id: "0036-04"
level: "task"
parent: "0036"
state: "closed"
visibility: "internal"
prerequisites:
  - "0036-03"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:400"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Nutzerverstaendliche, illustrierte Fassung beider Prozesse als generierte HTML-Seite(n) erstellen, inkl. mindestens eines Ablaufdiagramms pro Prozess. PREREQ: 0036-04:0036-03. REF: 51482d09533d2f83a7b14daf5870abb1f576399c, inkl. mindestens eines Ablaufdiagramms pro Prozess. PREREQ: 0036-04:0036-03

## Scope

- **Zu klaeren vor Umsetzung:** Ob die vorhandene Cytoscape-Graph-Infrastruktur fuer Ablaufdiagramme (Zustand/Uebergang statt Modul-Abhaengigkeit) geeignet ist, oder ob ein einfacheres statisches Diagramm-Format (z. B. serverseitig aus `_src/` gerendertes SVG) angemessener ist.
  - **Akzeptanzkriterien:** Seite(n) sind Build-Artefakt gemaess dem in 0036-03 dokumentierten Seitenerzeugungsprozess (generiert aus `_src/`, nicht manuell im HTML-Baum editiert); Sprache ist einfach und an Website-Nutzer gerichtet, ohne die normativen Dokumente aus 0036-01/0036-02 zu widersprechen; jedes Diagramm ist mit den tatsaechlichen Zustaenden/Uebergaengen aus dem Code konsistent; die Seite enthaelt die in 0036-03 definierten stabilen Einsprungpunkte/Anker fuer Dialog-Deep-Links.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Seiten generiert, `validate.py` meldet keine defekten Links/Anker; Diagramme committed als Teil der `_src/`-Quellen mit `REF`.
