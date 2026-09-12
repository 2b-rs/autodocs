---
schema_version: "1.0"
id: "0036-06"
level: "task"
parent: "0036"
state: "closed"
visibility: "internal"
prerequisites:
  - "0036-01"
  - "0036-02"
  - "0036-03"
  - "0036-04"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:409"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
---

## Goal

Vollstaendige Uebersetzung der normativen und nutzerfreundlichen Prozessdokumentation sowie aller Diagramm-Texte/Beschriftungen ueber die bestehende i18n-Pipeline. PREREQ: 0036-06:0036-01, 0036-06:0036-02, 0036-06:0036-03, 0036-06:0036-04 <!-- REF: c8788f6865feeef9cfbbece41c1d802d9cee9b8c -->

## Scope

- **Closure evidence (2026-08-16):** Substantive REF `c8788f6865feeef9cfbbece41c1d802d9cee9b8c`. Stable-ID extraction and rendering cover page metadata, authored headings, ARIA labels, and inline-SVG text; all ten locale registers report `4648/4648` translated and zero open. The focused gate reports 71 hits, zero fallbacks/findings, six stable anchors, two ARIA labels, and 18 inline-SVG labels per locale; the all-locale process check has zero deviations and `_src/validate.py` passes. Evidence: `logs/i18n-process-0036-06/20260816-9c4e7b2a/completeness.json` (SHA-256 `9d51daa07c1da65ee86347453b5190419c0ca6cd3da57895b1cde5011ac090cf`). Public German documentation alone was sent through read-only `translate.googleapis.com` requests; no credentials or external mutation were used. Fail-closed retries exceeded the original 900-request estimate; the reconstructed upper bound is below 1,200 and is retained in the evidence.
  - **Akzeptanzkriterien:** Alle neuen uebersetzbaren Strings durchlaufen die JSONL-Pipeline mit stabilen IDs; Platzhaltertoken und `[SWS_…]`/`[RS_…]`-Marker bleiben in jeder Zielsprache unveraendert; alle unterstuetzten Sprachtrees (siehe Startseite, u. a. en/es/pt/fr/ru/ar/hi/ko/zh/nl) enthalten die neuen Seiten vollstaendig, keine fehlenden/englisch durchgerutschten Segmente; Deep-Link-Anker bleiben sprachstabil oder werden ueber eine dokumentierte sprachlokale Mapping-Regel aufloesbar gehalten.

## Acceptance criteria

- **AC-001** Preserve imported acceptance text from the legacy source.

## Definition of Done

Uebersetzungslauf durchgefuehrt, Vollstaendigkeitspruefung dokumentiert und committed mit `REF`.
