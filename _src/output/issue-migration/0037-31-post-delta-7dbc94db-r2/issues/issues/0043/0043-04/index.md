---
schema_version: "1.0"
id: "0043-04"
level: "task"
parent: "0043"
state: "closed"
visibility: "internal"
prerequisites:
  - "0043-01"
  - "0043-02"
  - "0043-03"
  - "2026"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:DONE.md:716"
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

PREREQ: 0043-04:0043-01, 0043-04:0043-02, 0043-04:0043-03 Make report staleness mechanically impossible to miss. **Claim freigegeben (2026-08-22):** vormaliger Owner `Data-Aria-20260821T093000Z` ist beim Neustart von `Data` verlorengegangen. Vorarbeit auf Branch `0043-04`, Tip `b9bef3f42` (Claim und Architect-Authorization-Hold). `[u]` bleibt bestehen: der Blocker ist die noch ausstehende eigene Gate-Scope-Pruefung, nicht der weggefallene Claim. **`[u]` aufgehoben (2026-08-23, Projektleiter `kathryn`):** Die Gate-Scope-Pruefung liegt vollstaendig vor — `DEC-0043-003` (`docs/dossiers/dec-0043-report-staleness-gate.md`) und Scope-Review `docs/dossiers/0043-04-report-staleness-scope-review.md` sind auf `main` integriert; zusaetzlich bestaetigendes unabhaengiges Zweitreview `scope-supported-with-bounds` (B-01..B-07) durch Architektin `seven`, Branch `review-0043-04-scope-seven-20260823T143143Z`, Tip `e729182d3`, Record `docs/campaign-evidence/review-0043-04-scope-20260823T143143Z/scope-review.md`. Implementierung darf starten, gebunden an die Auflagen aus `DEC-0043-003` (einschl. der dort korrigierten Prerequisites `0043-04:0043-02`, `0043-04:0043-03`); Uebernehmer setzt auf Branch `0043-04` @ `b9bef3f42` auf, beginnt NICHT neu. **Claim (2026-08-23):** `Tom-Baxter-20260823T203000Z` (Dispatcher `tom`, unprivilegiert), `TODO-Tom-Baxter-0043-04-20260823T203000Z.md`, owner_token `agent:tom-baxter-20260823t203000z:0043-04:20260823T203000Z`. Branch `0043-04` ab `b9bef3f42` (nicht neu begonnen); Base-and-Merge: `0043-03`@`c67b6b0c7` (enthaelt `0043-02`@`946e5e4ab` und `0043-05`), danach `main`-Catch-up `a11b72507` und `46597fd28` in eigenen Commits. TODO-Konflikte ausschliesslich zeilenweise uebernommen. **Implementierung abgeschlossen (2026-08-23):** `Tom-Baxter-20260823T203000Z` (Dispatcher `tom`, unprivilegiert). REF `32a127c83` (substanziell), Branch-Tip siehe Buchhaltungscommit. Startfolge enthalten: `0043-03`@`c67b6b0c7` (traegt `0043-02`@`946e5e4ab` und `0043-05`), `main`-Catch-ups `a11b72507` (`1217eccfb`) und `46597fd28` (`080a91db0`); TODO-Konflikte ausschliesslich zeilenweise. Ergebnis: eine fokussierte Pruefung `check_report_freshness()` in `_src/validate.py` (Schranke B-01) mit **genau zwei** Ausloesebedingungen (B-02): `stale-build-report` (Provenienzbindung des Seitenmodells fehlt, ist fehlerhaft oder weicht vom juengsten schemakonformen Ledger-Eintrag ab) und `unrecorded-publication-run` (vollstaendige, nicht-diagnostische Publikationskohorte ohne Ledger-Eintrag); Ledger-Befunde werden mit den Kategorien des `0043-02`-Konsumentenvertrags durchgereicht. Neues Top-Level-Objekt `publication_provenance` im Seitenmodell (B-04, erzeugt, nie handgeschrieben; neues idempotentes Kommando `build_report.py provenance`), Diagnose-Markierung `diagnostic_no_ledger` fuer `--no-ledger`-Laeufe; `docs/pipeline/build-report-schema.md` erweitert (nicht gebrochen); `_src/WARTUNG.md` dokumentiert die kanonische Folge einschliesslich `combine`+`publish`. Fehlalarmschutz (B-03): unvollstaendige/laufende Kohorten, identitaetslose Reports, Diagnosekohorten und der eigene Validator-Subreport loesen nie aus; ein frischer Klon mit leerem `output/` ist gruen. Pruefung ist rein beobachtend, ohne Netz, ohne Schreibzugriff (B-07); Exit-Status-Semantik fuer bestehende taskfremde Befunde unveraendert. **Validierung:** `test_report_freshness` 19/19 (hermetisch, echtes Ledger unberuehrt), zusammen mit `test_build_report`, `test_build_ledger` und `test_report_page_header` 55/55; `generate.py` 428 Seiten; `build-reports.html` byte-identisch (kein HTML von Hand geaendert). **DoD nachgewiesen:** Pruefung feuert auf dem Vor-Feature-Stand (eingefrorene Seite ohne Bindung -> ein `severity=error`-Befund, der den Exit-Status treibt) und ist auf dem Nach-Feature-Stand befundfrei. Voll-`validate.py` meldet genau zwei **taskfremde** Baseline-Deadlinks, bewusst **nicht** mitrepariert: `process.html` -> `TODO-perplexity-0037-37-...md` (bekannt aus `0043-05`) und `build-reports.html` -> `output/build-reports/combined-1786722004.json` — letzterer stammt aus dem von B-05 vorgeschriebenen `0043-03`-Merge (git-ignoriertes `output/` je `DEC-0043-001`), gehoert zu `0043-03`/`0043-07` und ist im Claim als F-TOM-BAXTER-002 samt Empfehlung verzeichnet. Kein Integrationscheckpoint gekreuzt (der verpflichtende `0043-04`-Checkpoint liegt bei `belanna`), keine Acceptance erzeugt, `refs/heads/main` nicht bewegt, `DONE.md` unberuehrt. Abnahme steht aus. **Acceptance: ✓** (2026-08-24, Integratorin `belanna`, unabhängig von Implementierer `Tom-Baxter-20260823T203000Z`). Mandatory Integrationscheckpoint **bestanden**. Abgenommene Baseline: Kandidat `32a127c83`, integrierter Stand `2aa718a3b`; Review-REFs `5199bd60c` (B-01…B-07, null Regressionen, DoD nachgewiesen) und `f944f2710` (Delta-Re-Review nach Nachzug bestanden). Prerequisite-closed Batch `{0043-01, 0043-02, 0043-03, 0043-05}` vollständig abgenommen. Dritte Feuerbedingung `malformed-build-ledger` nach B-02 in das Review eingetreten und ausdrücklich angenommen. **Auflagen an `0043-07`:** Live-Nachweis für Feuerbedingung (b) (`F-TOM-BAXTER-003`) und der verbleibende taskfremde `process.html`-Deadlink.

## Scope

- **Requirements covered:** `RQ-BR-04`.
  - **Context (finding B6):** No check notices a frozen report page today; the canonical build sequence does not include `publish`.
  - **Integration review:** **mandatory.** **Rationale (architect):** this adds a gate to the canonical validation every future build runs through; an error is either a silent no-op (staleness returns) or a false-positive build blocker.
  - **Authority hold (2026-08-21):** Discovery at `59a546c03` established that the proposed `validate.py` finding has cross-item blast radius and depends on the unintegrated terminal ledger contract from `0043-02` (`56560fa2c`). Before any gate-scope mutation, Management must instantiate an Architect independent of the Implementer; a conforming `decision-record@v1` on `main` and the Architect’s supporting scope review must name the completed-cohort/ledger boundary, affected work units/gates, severity/absence behavior, prerequisite disposition, and allowed paths. This Task remains `[u]` because that authorization is now the sole next action.

## Acceptance criteria

- **AC-001** The canonical build sequence includes `combine`+`publish`
- **AC-002** `validate.py` emits a finding when the published page model is older than the newest subreport cohort or when a run produced no ledger entry
- **AC-003** the check has focused tests including the frozen-page case that motivated this Feature

## Definition of Done

Committed; the check demonstrably fires on the pre-Feature state and passes on the post-Feature state; `WARTUNG.md` documents the extended sequence.
