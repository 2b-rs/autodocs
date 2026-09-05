---
schema_version: "1.0"
id: "0036-05"
level: "task"
parent: "0036"
state: "open"
visibility: "internal"
prerequisites:
  - "0036-04"
labels:
  - "legacy-terminal-unverified"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:405"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Verlinkung der Prozessdoku aus den betroffenen Dialogen (`review_request.js`, `review.js`). PREREQ: 0036-05:0036-04 <!-- REF: 31479053a49e434854dcf0a5ececa806f0cd3f39 -->

## Scope

- **Akzeptanzkriterien:** Jeder Dialog erhaelt einen kontextbezogenen Link (z. B. "Wie funktioniert das?") zur passenden Seite bzw. zum passenden Einsprungpunkt/Anker aus 0036-04; Link ist barrierefrei erreichbar (Tastatur, Screenreader-Label) analog zu den Anforderungen aus 0021-05; Link funktioniert in allen Sprachtree-Varianten (zeigt auf die sprachlokale Doku-Seite, nicht hart auf Deutsch/Englisch verdrahtet).

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

UI-Aenderung committed mit `REF`; stichprobenhafte Pruefung in mind. zwei Sprachtrees.
