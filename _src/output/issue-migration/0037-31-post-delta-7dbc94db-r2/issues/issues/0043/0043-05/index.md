---
schema_version: "1.0"
id: "0043-05"
level: "task"
parent: "0043"
state: "closed"
visibility: "internal"
prerequisites:
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:724"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
  - id: "AC-004"
    status: "active"
---

## Goal

Overhaul the five report pages: uniform explanatory header, visible freshness, S-Core campaign included. **Claim freigegeben (2026-08-22):** vormaliger Owner `Data-Julia-20260821T090700Z` ist beim Neustart von `Data` verlorengegangen. ACHTUNG, substanzielle Vorarbeit vorhanden: Branch `0043-05`, Tip `afcba7663`, 10 Commits, 17 Dateien, 271 Einfuegungen (Header-Generatoren, Tests, Report-Regenerierung). Dort aufsetzen, NICHT neu beginnen. **Uebernommen (2026-08-22, Projektleiter `kathryn`):** `Harry-Neelix-20260822T164100Z`, Claim `TODO-Harry-Neelix-0043-05-20260822T164100Z.md`, owner_token `agent:harry-neelix-20260822t164100z:0043-05:20260822T164100Z`, Dispatcher `harry`, unprivilegiert, Branch/Worktree `0043-05` ab `afcba7663`. Der Marker wird hier auf `main` gesetzt, weil der Uebernehmende `main` selbst nicht bewegen darf. **Implementierung abgeschlossen (2026-08-22):** `Harry-Neelix-20260822T164100Z` (Dispatcher `harry`, unprivilegiert). REF `0e194c1f44bf1826735fd54f6e7d4fc46778cc65` (substanziell), Branch-Tip/Buchhaltung `c897899c4c1fa5fd18230dca2aaccc929d79103c`, Abgleich-Merge `cfcf49844`, Claim `TODO-Harry-Neelix-0043-05-20260822T164100Z.md`. Validierung: 16/16 fokussierte Tests gruen; `generate.py --check` fuer 5 Seiten 0 Abweichungen, nach der Buchhaltung wiederholt; Hygiene vor dem Commit PASS. Voll-`validate` meldet genau einen **taskfremden** Baseline-Deadlink (`process.html` -> `TODO-perplexity-0037-37-20260816-1443.md`); `process.html` ist byte-identisch zu `main`, der Link wurde korrekt **nicht** mitrepariert. Offene Reviewhinweise: `0019-06` ist sichtbar, aber mangels same-tree-HTML-Ziel nicht verlinkt; alle fuenf Seiten sind absichtlich `nolang`. Abnahme steht aus. **Acceptance: ✓** (2026-08-24, Integratorin `belanna`, unabhängig von Implementierer `Harry-Neelix-20260822T164100Z`). Abgenommene Baseline `c897899c4`; Review-REF `d8834121b`.

## Scope

- **Requirements covered:** `RQ-BR-05`, `RQ-BR-06`.
  - **Context (finding B5):** Curation, traceability, and open-reviews pages carry no visible generation timestamp; the newest extraction state is 2026-08-12; the S-Core campaign appears nowhere.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** presentation and explanatory text through existing generators; no authority or data semantics change. Re-examined at `0043-07`.

## Acceptance criteria

- **AC-001** `build-reports.html`, `curation-report.html`, `extraction-reports.html`, `traceability.html`, and `open-reviews.html` each carry a uniform header naming generation timestamp, generating tool, data source, and a short "what this report shows and how to read it" paragraph
- **AC-002** the S-Core campaign evidence (`0019-06`) is reachable from the report landscape
- **AC-003** visual presentation is aligned across the five pages per `KONVENTIONEN.md`
- **AC-004** all changes go through the page-model generators (`curation_report.py`, `extraction_report.py`, `open_reviews_report.py`, …), never hand-edited HTML

## Definition of Done

Committed; regeneration reproduces the headers; i18n segments for new user-visible text are extracted; validation passes.
