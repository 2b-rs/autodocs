---
schema_version: "1.0"
id: "0043-03"
level: "task"
parent: "0043"
state: "closed"
visibility: "internal"
prerequisites:
  - "0043-02"
  - "0043-05"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:709"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
  - id: "AC-003"
    status: "active"
---

## Goal

PREREQ: 0043-03:0043-02, 0043-03:0043-05 Render the full build history on `build-reports.html`. **Claim (2026-08-22):** `Harry-Odo-20260822T153100Z` (Dispatcher `harry`, unprivilegiert), `TODO-Harry-Odo-0043-03-20260822T153100Z.md`. Branch `0043-03` von Feature-Base `0043` (`38a4d43ad`); zuerst `0043-02`@`946e5e4ab`, danach `0043-05`@`c897899c4` einmergen. **Prerequisite-Korrektur (Projektleiter `kathryn`, autonome Backlog-Reparatur):** `0043-03:0043-05` ergaenzt. Begruendung: `0043-05` erweitert `build_report.py` um `report_page_header()` und erzeugt den fertigen einheitlichen Kopf in **genau der Seite**, die `0043-03` rendert (`build-reports.html`). Ohne diese Kante haette `0043-03` entweder unter Verletzung der bindenden Base-and-Merge-Regel eigenmaechtig gemergt oder den fertigen Kopf zurueckgebaut. Intent-erhaltend, zeigt auf ein bereits terminales Item, kein Zyklus, kein Akzeptanzkriterium geschwaecht. Gemeldet von `Harry-Odo-20260822T153100Z`, der korrekt **nicht** eigenmaechtig gemergt hat. **Implementierung abgeschlossen (2026-08-22):** REF `e62939dd1` (substanziell), Branch-Tip `c67b6b0c7`. Startfolge dokumentiert und enthalten: `0043-02`@`946e5e4ab`, danach `0043-05`@`c897899c4`; `main`@`418f09b79` mit TODO-Konflikt **ausschliesslich zeilenweise** uebernommen. Ergebnis: vollstaendige schemakonforme Ledger-Historie neueste-zuerst (Zeit, Badge, Ref, Seiten/Pruefungen/Diagramme/Befunde, JSON-Detail-Link), Ledger-Befunde sichtbar, juengste Run-Details und der `0043-05`-Header erhalten; `publish` schreibt das Ledger vor dem Rendering. Validierung: `test_build_report` 8/8, `test_build_ledger` 26/26, hermetischer Zwei-Eintrag-Regenerationstest, `generate.py` 428 Seiten, Diff-Check sauber, echte Ledger-Historie unveraendert. Kein Checkpoint gekreuzt (Architekten-No-Checkpoint-Begruendung), keine Acceptance, kein `main` bewegt. Abnahme steht aus. **Korrektur nach Acceptance-Review REJECTED (2026-08-24):** REF `2fef3b798` (Fix + Tests), `ef6ca5884` (regenerierte Seite). Claim `TODO-Tom-Kestra-0043-03-20260824T005000Z.md` (`Tom-Kestra-20260824T005000Z`, Dispatcher `tom`, unprivilegiert), Basis `c67b6b0c7`. Befund `F-BELANNA-0043-03-01` (Review-Record `d8834121b`, `belanna`): der JSON-Detail-Link der Historientabelle wurde bedingungslos gerendert, obwohl `combined_report_ref` in das per `DEC-0043-001` dauerhaft git-ignorierte `output/build-reports/` zeigt — pro Ledger-Zeile ein toter Link, den `validate.py` meldet und der `0043-07` unerreichbar macht. Korrektur analog zum `MANUAL_REF_PREFIX`-Muster aus `0043-01`: verlinkt wird nur ein Ref, der einen **getrackten** (veroeffentlichten) Pfad benennt; andernfalls erscheint der Ref-Wert als Klartext `<code>`, ein leerer Ref behaelt den Platzhalter `–`. Die Aufloesung wird aus dem Git-Trackingstand entschieden, nicht aus dem lokalen `output/`-Baum, und faellt geschlossen aus, wenn Git nicht befragt werden kann. Validierung: `_src/tools/test_build_report.py` 12/12 (vier neue Faelle), `_src/tests/test_build_ledger.py` 26/26, `publish` + `generate.py` (428 Seiten) neu erzeugt, `validate.py` meldet nur noch den vorbestehenden, task-fremden Baseline-Befund aus `0043-05` (toter interner Link in `process.html` -> `TODO-perplexity-0037-37-20260816-1443.md`); kein toter `<a href>` nach `output/` mehr in der Historientabelle. Keine Acceptance. **Acceptance: ✓** (2026-08-24, Integratorin `belanna`, unabhängig von Implementierern `Harry-Odo-20260822T153100Z` / `Tom-Kestra-20260824T005000Z`). Abgenommene Baseline `2fef3b798` (Branch-Tip `248bd1c4b`) **nach Korrektur** des zunächst abgelehnten Standes; Review-REF `dc9b4748b` (`review-0043-03-belanna-20260824T010500Z`), vorangehende Ablehnung `d8834121b` (Befund `F-BELANNA-0043-03-01`, behoben und gemessen).

## Scope

- **Requirements covered:** `RQ-BR-01`.
  - **Context (finding B3):** `publish` renders only the latest run; the list the customer expected was never designed.
  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** presentation over an authoritative ledger; errors are visible on the page itself. Re-examined at `0043-07`.

## Acceptance criteria

- **AC-001** `build-reports.html` shows the complete ledger as a build list (newest first: time, result badge, ref, key counters, link to details) plus the latest run's detail section as today
- **AC-002** the page states its data source and generation time
- **AC-003** rendering is driven by the ledger, not by hand-edited HTML in the page model

## Definition of Done

Committed; regenerating after a new run adds the run to the list without manual editing; layout follows `KONVENTIONEN.md`.
