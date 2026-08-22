# Berichtstypen und Inhalte

## Scrape-Berichte (`spec_scrape.py`)

Alle unten stehenden Berichte werden über die Phase-Positionalargumente von
`spec_scrape.py` erzeugt: `{ids,props,reqs,trace,trace-check,siblings,
compare,all,crosscheck,urls,upstream,observations}`.

| Phase | Inhalt | Ausgabeformat | Schreibt in DB? |
|---|---|---|---|
| `ids` | Pro Dokument: Seitenzahl, gefundene IDs | Text oder `--json` | Nein |
| `props` | Pro Record: Dokument, Seite, Titel, Upstream, Namespace, Eigenschaften | Text oder `--json` | Nein |
| `reqs` | Prosa-Requirement-Text je ID, mit Reparatur-Nachweis (`_repair_requirements`) | Text oder `--json`; optional `--write-reqs` schreibt additiv | Nur mit `--write-reqs` |
| `trace` | Chapter-6-Traceability-Tabellen je Dokument, gemergt über alle Quelldokumente pro RS-ID (via `merge_trace_parts.py`) | Kanonische Records unter `_src/spec/traceability/` | Ja — eigene Tabelle, nicht `records/` |
| `trace-check` | Konsistenzprüfung Record-Upstream ↔ Traceability-Tabellen, beidseitig: `upstream_not_traced`, `traced_not_upstream` | `--json` | Nein (nur Review-Liste) |
| `siblings` | Für eine RS-ID: alle Records, die von ihr abhängen ("satisfiers"), mit Quelldokumenten | Text oder `--json` | Nein |
| `compare` | (nicht näher im Docstring beschrieben; Name deutet auf reinen Feld-Vergleich zweier Quellen) | — | Nein |
| `all` | Alle Phasen-Ergebnisse zusammen | — | je nach `--rebuild`/`--write-reqs` |
| `crosscheck` | Backend-A-vs-Backend-B-Abweichungen + DB-Abweichungen (Phase-1-Input für Kampagnen) | `--json`, archiviert unter `output/spec-validation/<release>/crosscheck-<campaign>.json` | Nein |
| `urls` | Download-Zeilen für `run.sh`, wenn PDF-Verzeichnis fehlt (Sandbox hat keinen Netzzugriff) | Text | Nein |
| `upstream` | Vergleich (Standard) oder Rebuild (`--rebuild`) der `upstream`-Metadaten je Record gegen den `UpstreamIndex` | `--json`: `{unchanged, updated, missing, ambiguous, none, source_records, mode}` | Nur mit `--rebuild` |
| `observations` | Rohbeobachtungen der pypdf-Backend-Geometrie je Seite (nur `--backend pypdf`) | `--json`, sortierte Keys | Nein |

## Traceability-Bericht (`traceability_report.py`)

- **Input**: Ergebnis eines `spec_scrape.py crosscheck --json`-Laufs plus
  zugehöriges Lauf-Log.
- **Output**: Seitenmodell `_src/sources/pages/traceability.html`. Gefundene
  Record-IDs werden, soweit im deutschen HTML-Baum vorhanden, auf ihre
  Dokumentationsseite verlinkt.
- **Sprache**: Bewusst nur Deutsch (Seitenmodell-Flag `nolang`) — wird nicht
  übersetzt.
- **Datum**: Trägt das Datum des zugrunde liegenden Scraping-Laufs.

## Extraktionsbericht (`extraction_report.py`)

- **Inhalt**: Volle Abweichungsliste, gruppiert nach vier am 2026-08-11
  behobenen Extraktions-Fehlerklassen (`CATEGORIES`):
  - `history_continuation` — mehrseitige "Document Change History"-Fortsetzung (Commit `bae18b1c`)
  - `traceability` — "Requirements Tracing"-Tabellen fälschlich als lokale Definitionen gezaehlt (Commits `c2334c43`/`ffa42b17`)
  - `number_heading` — mehrseitige Anhangs-Tabellen "Number Heading" (Commit `e554a1a8`)
  - `heading_label` — Überschrift fälschlich als Label-Zeile verworfen (Commit `751013a2`)
  - Jede Kategorie trägt: Titel, verweisenden Commit, Problem-Text, Fix-Text.
- **Kurationsanfragen**: Am Berichtsanfang gelistet — Fälle, die die
  Extraktion nicht automatisch entscheiden konnte, mit Screenshot,
  aktuellem Extraktionsergebnis, Klartext-Erklärung. Konsumiert von
  `curation_ingest.py`.
- **Kennzahlen** (`kennzahl(...)`): u. a. "Behobene Fehlerklassen" (=
  `len(CATEGORIES)`), Issues-Count, Curation-Open-Count.
- **Output-Format**: HTML-Seitenmodell (verlinkt von der Startseite).
- **Bewahrung veröffentlichter Berichte (`DEC-0043-002`)**: Vorhandene
  versionierte Extraktionsberichte werden **bewahrt**. Ein neuer Lauf erzeugt nur
  das noch fehlende Modell seiner eigenen neuen Version und aktualisiert das
  Berichtsverzeichnis als Verweis darauf; bestehende Berichtseiten werden dabei
  nicht neu erzeugt oder überschrieben. Normale Site-Neuerzeugungen rendern das
  historische Archiv nicht neu — es wächst mit der Zeit, und ein routinemäßiges
  Neurendern würde die Regenerierung dauerhaft verlangsamen.
  Bewahrung ist die **Voreinstellung, kein Verbot**. Eine Ersetzung ist zulässig
  bei Verlust der gerenderten Seiten oder bei schweren Fehlern früherer
  Erzeugungslogik, die auch in den erzeugten Seiten behoben werden müssen — dann
  auditierbar, mit Grund, Digests und Verknüpfung. Forensische Rekonstruktion und
  Vergleich erzeugen einen **getrennten Kandidaten** und überschreiben niemals den
  beobachteten Bericht. Das Verhalten für den aktuellen Bericht und den Index ist
  gesondert zu klassifizieren und fällt nicht stillschweigend unter die
  Archivregel. Maßgeblich ist `DEC-0043-002` in
  [`docs/dossiers/re-intake-berichtswesen-build-evidenz.md`](../dossiers/re-intake-berichtswesen-build-evidenz.md).
- **Bauen vs. Publizieren (wichtig, seit Vorfall 2026-08-12)**: `extraction_report.py
  build` erzeugt/aktualisiert nur die Seitenmodell-JSONs (u. a.
  `_src/sources/pages/extraction-report.json`, `extraction-reports-data.js`,
  versionierte Stubs unter `_src/sources/pages/reports/`). Es schreibt **kein**
  sichtbares HTML. Erst ein anschließender Lauf von `python3 _src/generate.py`
  rendert diese Modelle in die browsebaren Seiten (`extraction-reports.html`,
  `extraction-report-v%04d.html`). Beide Schritte gehören für Agenten/Sandbox-
  Läufe zusammen in **ein** `run.sh` (`extraction_report.py build && python3
  _src/generate.py`) — siehe `_src/WARTUNG.md`, Abschnitt „Extraktions-Berichte:
  Bauen vs. Publizieren“.
- **Versionsneutrale Re-Publikation**: `record_version()` legt seit 2026-08-12
  keine neue Version an, wenn Kennzahlen, Residual-Status und Skript-Stände
  gegenüber der letzten Version unverändert sind — ein reiner Publikationslauf
  (nur `generate.py` nötig) erzeugt dadurch keine Versions-Dubletten mehr.
- **Unveränderliche Historie (0043-05)**: Vorhandene versionierte
  Extraktionsberichte bleiben byte-identische Evidenz. Ein neuer Lauf erstellt nur
  das noch fehlende Modell seiner neuen Version und aktualisiert das
  Berichtsverzeichnis/den Index als Verweis darauf; bestehende Berichtseiten werden
  nicht neu erzeugt oder überschrieben.

## Extraktions-Kampagnenbericht (`spec_extraction_campaign.py`)

- **Subkommandos**: `create`, `report`.
- **Beschreibung**: Reproduzierbare Side-by-Side-PDF-Extraktionskampagnen-
  berichte. Der Campaign-Runner **führt selbst keine PDF-Extraktion aus** —
  er orchestriert/vergleicht nur.
- **Status**: Implementiert als CLI mit zwei Kommandos; genauer Inhalt von
  `report` nicht vollständig dokumentiert im Docstring.

## Extraktions-Benchmark (`spec_extraction_benchmark.py`)

- **Zweck**: Baut einen deterministischen, review-first Benchmark-Entwurf
  über 200 Records.
- **Kategorien** (Stratifizierung): `multi_page`, `dense_fields`, `lists`,
  `multiple_per_page`, `mixed_case_id`, `typography`, `empty_or_dash`,
  `single_page`.
- **Status**: Implementiert.

## Rebuild-DB-Bericht (`upstream --rebuild` JSON-Ausgabe)

- **Felder**: `unchanged`, `updated`, `missing`, `ambiguous`, `none`,
  `source_records` (Anzahl RS-Quell-Records im Index),
  `mode` (`"rebuild"` oder `"compare"`).
- **Verwendung**: Direkt als Nachweis in `run.sh`-Archivläufen protokolliert
  (siehe `output/run-archive/run-2026-08-11_17-34-37-n0217.sh`).

## Changeset-ähnliche Berichte

Kein Werkzeug im Repo heißt explizit "changeset", aber folgende Mechanismen
erfüllen diese Funktion:

- **`run.sh`-Archiv** (`output/run-archive/run-<timestamp>-n<seq>.sh` +
  `.log`): Jede ausgeführte Task wird als Skript+Log-Paar archiviert — der
  nächstliegende Ersatz für ein Changeset-Protokoll in diesem Repo.
- **Kampagnen-Commit-Muster** (`SPEC_BUILD_PROCESS.md`): jede Phase
  schreibt einen eigenen, nach Muster benannten Commit (`spec: open
  campaign <id>...`, `spec: triage campaign <id>...`, `spec_scrape:
  <Ursache> -> <Wirkung> (campaign <id>, N Fälle)`, `spec: close campaign
  <id>...`) — zusammen ergeben sie ein vollständiges Changelog einer
  Kampagne über `git log`.
- **`history[]` je Record**: append-only Statuswechsel-Protokoll je
  einzelnem Record (siehe `status-model.md`).

## AI-Analyse-Bericht

Kein dedizierter "AI analysis report" als eigenes Artefakt gefunden. Am
nächsten kommt:

- `ai_workflow.py status` — Überblick über legacy/aktuell/veraltete
  KI-Fragmente, geänderte Records (Hash-Abgleich), Traces ohne Fragment,
  Fragmente ohne Trace, Policy-Versionen.
- **Decision-Rationale je Feld** (Phase 3 in `SPEC_BUILD_PROCESS.md`):
  `decision.rationale`, `decision.confidence`,
  `decision.suspected_backend_bug` — das ist die nächstliegende Form einer
  "KI-Analyse", aber pro Feld/Record, nicht als eigenständiger
  Gesamtbericht.

## Kurationsbericht (`curation_report.py`, implemented 0006-09/0006-10, extended 0021-06)

- **Inhalt**: Vereinheitlichter Überblick über alle Kurations-/Review-Items
  aus beiden Warteschlangen (`curation-queue/` und `review-queue/`),
  normalisiert nach [`curation-item-schema.md`](curation-item-schema.md).
  Enthält offene Items sowie zuletzt entschiedene Items in jedem
  Terminalstatus (`accepted`, `rejected`, `proposed`, `superseded`) — kein
  Status wird aus der Anzeige gefiltert.
- **Website-originated Requests (0021)**: Items mit `item_kind:
  "review-request"` zeigen zusätzlich Requester-Identität und -Trust
  (`github_authenticated` vs. `self_declared`), Transport
  (`decision_basis.transport`: `github_issue` oder `json_export`) und
  Ziel-Version (`decision_basis.target_version_id`). **Wichtig**: Diese
  Felder dokumentieren nur, *wer die Anfrage gestellt hat und wie*, nie eine
  Entscheidung über den Record — ein `self_declared`-Requester erscheint
  explizit mit niedrigerem Vertrauensstatus, ohne dass daraus eine Autorität
  über Record-Inhalt oder -Status abgeleitet wird. Die Kurator-Entscheidung
  bleibt allein maßgeblich (`website-review-flag.md`, Non-bypass rule 2/3).
- **Output**: `_src/tools/curation_report.py build` erzeugt/aktualisiert nur
  das Seitenmodell (`_src/sources/pages/curation-report.json`) und den
  Exportdatensatz (`_src/data/curation-items.json`); es schreibt **kein**
  sichtbares HTML. Ein anschließender `python3 _src/generate.py` rendert
  `curation-report.html`. Beide Schritte gehören in **ein** `run.sh`
  (`curation_report.py build && python3 _src/generate.py`), analog zum
  Extraktionsbericht.
- **Sprache**: Nur Deutsch (`nolang`), analog zum Traceability-Bericht.

## Offene-Reviews-Bericht (`open_reviews_report.py`)

- Ergänzt den Kurationsbericht um eine reine "was ist gerade offen"-Sicht;
  gleiches Bau-vs.-Publizieren-Muster (`build` erzeugt nur das
  Seitenmodell, `generate.py` rendert `open-reviews.html`).


## Build- und Publikations-Bericht (`build_report.py`)

- **Inhalt**: Aggregierter Veröffentlichungs- und Validierungsbericht der gesamten Dokumentations-Pipeline (Schema: `docs/pipeline/build-report-schema.md`). Führt alle Subreports aus `i18n_merge`, `i18n_diagrams`, `html_generate` und `validate` zusammen.
- **Output-Formate**:
  - Maschinenlesbarer JSON-Gesamtbericht unter `output/build-reports/combined-<timestamp>.json`.
  - Statisches Seitenmodell `_src/sources/pages/build-reports.json`, gerendert nach `build-reports.html` im Root-Verzeichnis.
- **Traceability**: Trägt die exakte Runner-Referenz (`run_archive_ref` auf `run-<timestamp>-n<seq>.sh` / `.log`), Start-/Endzeitpunkte, aggregierte Kennzahlen und eine detaillierte Tabelle aller Validierungsbefunde.
- **Befehle**:
  - `python3 _src/tools/build_report.py combine` — Aggregiert neueste Subreports.
  - `python3 _src/tools/build_report.py publish` — Aggregiert Subreports und erzeugt das Seitenmodell `build-reports.json`.
- **Retention & Archivierung**: Jede Veröffentlichung aktualisiert das kanonische `build-reports.html`. Historische Maschinenberichte verbleiben chronologisch in `output/build-reports/combined-*.json` und sind über die zugehörigen Runner-Archive auditierbar.

## Versioned reports

Report-producing tools should align with the versioned model's existing query
surfaces instead of inventing parallel schemas: per-trigger blast-radius
reports from `supersession_trigger`, point-in-time reconstruction via
`asof_view`, and arbitrary-window change summaries via `delta_view`. These
reports are audit/report views over append-only stores, not separate sources of
truth.

