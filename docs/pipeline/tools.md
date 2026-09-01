# Werkzeuge — Katalog

Jedes Skript unter `_src/tools/*.py` und den relevanten `_src/*.py`, mit
Zweck und typischem Aufruf. Quelle: jeweiliger Modul-Docstring.

## Kern-Pipeline (`_src/`)

| Werkzeug | Zweck | Aufruf |
|---|---|---|
| `generate.py` | Erzeugt kompletten HTML-Tree aus Quellen unter `_src/` | `python3 _src/generate.py` / `--check` / `<seite>.html` |
| `extract.py` | Zerlegt generierten HTML-Tree zurück in editierbare Quelldateien (Resync nach Hand-Edits) | selten nötig, siehe `WARTUNG.md` |
| `validate.py` | Qualitätsprüfungen für HTML-Tree und Quellen | `python3 _src/validate.py` |
| `ai_workflow.py` | Kuratierungs-Workflow für KI-generierte Erklärungen (Zyklus Invalidieren→Auftrag→Merge) | `status`, `zeige`, `invalidiere`, `auftrag`, `merge` |
| `build_indexes.py` | Erzeugt kondensierte CSV-Sichten unter `_src/data/` (Lesesichten, nie zurückgeschrieben) | — |
| `build_component_graph.py` | Baut abstrakten API-Abhängigkeitsgraphen aus Seitenmodellen + Spec-Records | — |
| `render_diagrams.py` | Rendert alle Diagramme (Graphviz `.dot`, Sequenz `.seq.json`) neu | — |
| `seqgen.py` | Generator für Sequenzdiagramme im Hausstil, Quelle: `.seq.json` | — |
| `i18n_extract.py` | Baut deutsches Quellregister der Mehrsprachigkeit (`segments.de.json`) | — |
| `i18n_translate.py` | Erzeugt/mergt Übersetzungs-Arbeitspakete | `split <lang> [--kb=40]` |
| `i18n_diagrams.py` | Materialisiert übersetzte Diagramme (rendert neu bei Abweichung von Label-Register) | — |
| `lib_docmodel.py` | Bibliothek: Dokumentmodell-Grundfunktionen (importiert von `ai_workflow.py` u. a.) | Bibliothek, kein CLI |
| `lib_i18n.py` | Bibliothek: i18n-Grundfunktionen | Bibliothek, kein CLI |
| `lib_svgdiag.py` | Bibliothek: SVG-Diagramm-Grundfunktionen | Bibliothek, kein CLI |

## Spec-DB-Werkzeuge (`_src/tools/`)

| Werkzeug | Zweck | Aufruf/Phasen |
|---|---|---|
| `spec_scrape.py` | Haupt-Extraktionswerkzeug: gewinnt Spezifikations-Records aus AUTOSAR-PDFs | Phasen: `ids props reqs trace trace-check siblings compare all crosscheck urls upstream observations` |
| `spec_upstream.py` | Löst kanonische AUTOSAR-RS-Referenzen auf, aktualisiert Record-Metadaten sicher; bewusst unabhängig von PDF-Extraktion | Bibliothek (`UpstreamIndex`, `rebuild_record_files`, `rebuild_upstream`), importiert von `spec_scrape.py` |
| `merge_trace_parts.py` | Mergt parallel erzeugte Trace-JSON-Teilergebnisse sequenziell, um Schreibkonflikte zu vermeiden | — |
| `summarize_trace_all.py` | Fasst Trace-Ergebnisse zusammen (kein eigener Docstring gefunden) | — |
| `summarize_trace_check.py` | Fasst `trace-check`-Ergebnisse zusammen, liest von stdin | `python3 _src/tools/summarize_trace_check.py < input.json` |
| `review_ingest.py` | Review-Pakete aus dem HTML-Workflow (`review.js`) in Records schreiben; einziger schreibender Weg für Requirement-Text-Reviews | `--check`/`--apply paket.json`, `-g <issue-nr>...`, `--repo <org>/<repo>`, `--require-authenticated` |
| `review_flags.py` | Flag-Dateien für KI-Review-Jobs, kollisionsfrei via `os.rename` (atomar) | Bibliothek: `write_review_flag`, `complete_flag`, `build_instruction` |
| `curation_ingest.py` | Kurationsentscheidungen aus dem Extraktionsbericht übernehmen | `--check`/`--apply paket.json`, `--issue-body issue-42.md` |
| `curation_flags.py` | Warteschlange für KI-gestützte Kurations-Anfragen, kollisionsfrei | Bibliothek: `write_curation_flag`, `complete_flag` |
| `review_request_ingest.py` | Nimmt website-initiierte Re-Review-Anfragen (`review-request-package@v1`) entgegen, prüft Schema/Version/Hash/Duplikate und schreibt bei Erfolg ein `open`-Curation-Queue-Item vom `item_kind: "review-request"` (0021-03) | Bibliothek: `ingest(pkg, apply=..., current_content_hash=..., current_version_id=..., authoritative_actor=...)` |
| `curation_item.py` | Normalisiert Items aus `curation-queue/` und `review-queue/` in das gemeinsame `curation-item@v1`-Schema, inkl. Lifecycle-Status-Mapping für `review-request`-Items (`open`/`claimed`/`accepted`/`rejected`, nie mit `proposed` verwechselt) | Bibliothek, importiert von `curation_report.py` |
| `curation_report.py` | Baut den vereinheitlichten Kurationsbericht (0006-09/0006-10, erweitert 0021-06) inkl. Requester-Trust/Transport/Zielversion für `review-request`-Items; zeigt alle Terminalstatus, nicht nur `open` | `python3 _src/tools/curation_report.py build` (siehe `reports.md`) |
| `open_reviews_report.py` | Baut die reine "offene Reviews"-Sicht als eigenes Seitenmodell | `python3 _src/tools/open_reviews_report.py build` |
| `check_review_request_ui.cjs` | Playwright/WebKit-Kopfloser Smoke-Test des "Flag for review"-Dialogs auf einer gerenderten Record-Seite (Kategorie wählen, Begründung eingeben, Bestätigungstext prüfen) | `node _src/tools/check_review_request_ui.cjs <html-datei>` |
| `extraction_report.py` | Extraktionsbericht mit vollständiger Abweichungsliste (vier Fehlerklassen), zeigt Kurationsanfragen | Subkommandos u. a. `category`, `output`, `document`, `page` |
| `spec_extraction_campaign.py` | Reproduzierbare Side-by-Side-Extraktionskampagnenberichte; führt selbst keine Extraktion aus | `create`, `report` |
| `spec_extraction_benchmark.py` | Baut deterministischen, review-first 200-Record-Benchmark-Entwurf | — |
| `build_report.py` | Aggregiert Subreports zu kanonischem Gesamtbericht und erzeugt statisches HTML-Seitenmodell `build-reports.html` | `python3 _src/tools/build_report.py combine` / `publish` |
| `traceability_report.py` | Baut Traceability-Seitenmodell aus `crosscheck --json` + Log | `--json <crosscheck.json> --log <crosscheck.log>` |
| `upstream_evidence.py` | Persistiert rohe Backend-Beobachtungen je Dokument/ID/Backend ("Preserve raw evidence") | schreibt `_src/spec/upstream/evidence/<doc>/<id>/<backend>.json` |
| `text_repair.py` | Repariert PDF-Extraktionsartefakte mit belegter Herkunft; jede Änderung ist eine versionierte, protokollierte Regel; unbeweisbare Fälle werden als `suspects` gemeldet, nicht geraten | Bibliothek |
| `namespace_migrate.py` | Schreibt Namensraum-Zugehörigkeit explizit in jeden Spec-Record (statt implizit aus Modul) | Einmalwerkzeug |
| `migriere_ns_enclosing.py` | Trennt `ns`-Block der Spec-DB in zwei Fakten (altes Schema trug teils den umschließenden Typ vermischt) | Einmalwerkzeug |
| `migriere_schema_language.py` | Vereinheitlicht maschinenlesbare Schema-Sprache (Records trugen teils deutsche Schlüsselnamen im Legacy-`ns`-Objekt) | Einmalwerkzeug |
| `migriere_spec_db.py` | **Einmalwerkzeug (August 2026)**: Migration der Spec-Records aus Seitenmodellen in eigenständige Spec-DB (`_src/spec/records/`) | Einmalwerkzeug, historisch |
| `backfill_traces.py` | **Einmalwerkzeug (August 2026)**: rückwirkendes Anlegen der Trace-Dateien (`_src/ai/traces/**`) und Quellenregister (`_src/ai/quellen.json`) für den KI-Bestand | Einmalwerkzeug, historisch |
| `fix_dopplungen.py` | Einmaliges Bereinigungsskript: Dopplungen in Modul-/Namespace-Guides | Einmalwerkzeug |
| `namespace_migrate.py`, o.ä. Migrationsskripte | — siehe oben | — |

## QA-Scans (aus `WARTUNG.md`, Abschnitt "QA der Sprachbäume")

| Werkzeug | Zweck |
|---|---|
| `scan_bezeichner.py` | Punkt 3: Bezeichner-Scan — findet Label-Einträge, deren Schlüssel wie ein API-Identifier aussieht (CamelCase, etc.) |
| `scan_lazycopy.py` | Punkt 1: Lazy-Copy-Scan — findet Übersetzungseinträge, identisch zum deutschen Original |
| `scan_restdeutsch.py` | Punkt 2: Rest-Deutsch-Scan — sucht verbliebenes Deutsch in Übersetzungsregistern (`i18n/<lang>/segments.json`, `labels.json`) |

## PDF-/Geometrie-Diagnose-Werkzeuge

| Werkzeug | Zweck |
|---|---|
| `font_inventory.py` | Inventarisiert eingebettete Fonts und Glyph-Mapping-Fehler je Dokument (ob `/ToUnicode`-Map vorhanden) |
| `geometry_audit.py` | Prüft dokument-unabhängige Geometrie-Invarianten über den ganzen PDF-Korpus, meldet Counts je Dokument |
| `geometry_schema.py` | Strukturelles Schema für pypdf-Geometrie-Beobachtungsartefakte; validiert Form ohne externe Abhängigkeiten |

## Diagramm-Rückgewinnungs-Werkzeuge (einmalig)

| Werkzeug | Zweck |
|---|---|
| `svg2dot.py` | Einmalige Rückgewinnung der Diagrammquellen aus SVGs (zurück in `.dot`) |
| `svg2seq.py` | Einmalige Rückgewinnung der Sequenzdiagramm-Spezifikation aus SVGs (zurück in `.seq.json`) |

## Externe Abhängigkeiten (nicht im Repo, aber im Workflow verwendet)

| Werkzeug | Zweck | Installationsweg |
|---|---|---|
| `jq` | Strukturelles JSON-Filtern/Diffen über CLI | bereits installiert (`/usr/bin/jq`) |
| `git` / `git diff` / `git difftool` | Versionskontrolle, Standard-Diff | bereits installiert |
| `jd` (josephburnett/jd) | Semantisches JSON-Diffing (Set-Modus, unified-ähnliches Format) | nicht installiert; via `brew install jd`, dann `git config diff.jd.command 'jd --git-diff-driver -set'` + `.gitattributes`-Eintrag |

## Skript-Ausführungs-Infrastruktur

| Mechanismus | Zweck |
|---|---|
| `run.sh` | Einmalige, parameterlose Runner-Hülle; bei Task-Abschluss nur noch als dünner Aufruf des Transaktionswerkzeugs zulässig |
| `_src/run-loop.sh` | Legacy-Watch-/One-Shot-Runner mit Sandbox, Umgebungs-Selbsttest und expliziter Erstinitialisierung über `--init`; normale Selbsttests installieren oder aktualisieren keine Abhängigkeiten |
| `_src/tools/runner_transaction.py` | Fail-closed Legacy-Transaktion für `generate → validate → promote → einen atomaren Implementierungs-Check-in`; feste Action-IDs, Kandidaten-Worktree, temporärer Git-Index, CAS-Publikation, trailer- und tree-gebundene `[x]`/`[w]`-Transition mit behaltenem finalisiertem Claim, Recovery-Journal und strukturierte Ergebnisse; siehe [`runner-transaction.md`](runner-transaction.md) |
| `_src/tools/environment_doctor.py` | Rein lesende, portable Diagnose der Ausführungsumgebung; erzeugt ein digest-gebundenes `prepared-environment@v1` mit Capability-/Protokoll-Gates und optional verifiziertem Cache; Aufruf: `python3 _src/tools/environment_doctor.py --root <root> --requirements <requirements.json> --profile <profile.json> [--observations <observations.json>] [--cache-root <dir>] [--write-cache]`; siehe [`environment-doctor.md`](environment-doctor.md) |
| `_src/tools/task_validation.py` | Wertet einen unveränderlichen Validierungslauf gegen ein `task-validation-profile@v1` aus; erzwingt Freshness, Stage-/Input-/Output-Verträge, Coverage-Canaries und strukturierte Fehler statt blindem Vertrauen in Exit 0; Aufruf: `python3 _src/tools/task_validation.py --profile <profile.json> --run <result.json>`; siehe [`task-validation.md`](task-validation.md) | 
| `_src/tools/legacy_task_doctor.py` | Rein lesende, deterministische Diagnose für Legacy-`TODO.md`/`DONE.md`, Claims, REFs, Prerequisites und Agent-Bootstrap; Aufruf: `python3 _src/tools/legacy_task_doctor.py [--json]`; gibt höchstens zehn Zusammenfassungszeilen oder `legacy-task-doctor-report@v1`-JSON aus und repariert/übernimmt/löscht nichts; siehe [`legacy-task-doctor.md`](legacy-task-doctor.md) |
| `_src/tools/legacy_scope_planner.py` | Rein lesender, fail-closed Kollisionsplaner für direkte und abgeleitete Schreibbereiche; kombiniert normalisierte aktive Claims, den autoritativen `issue-regeneration-dag@v1` und exakt gebundene Git-/Runner-/Generator-/i18n-/Publikations-Snapshots, erklärt Producer-Ketten und liefert `PARALLEL`, `SERIALIZE`, `BLOCK` oder `INCOMPLETE`; siehe [`legacy-scope-planner.md`](legacy-scope-planner.md) |
| `_src/tools/legacy_task_editor.py` | Digest-gebundener struktureller Planer für Pickup, Fortschritt, Closure/Wontfix, Parent-Aggregation, REF-Korrektur und Claim-Handoff/-Finalisierung; erzeugt immer content-addressed Candidate+Diff, verifiziert Promotion-Preimages erneut und liefert bis `0038-05.02` ausschließlich `verified-coordinator-required` ohne autoritative Mutation; siehe [`legacy-task-editor.md`](legacy-task-editor.md) |
| `_src/tools/task_bookkeeping_closure.py` | **Stillgelegt:** frühere freie TODO-/Claim-Direktschreiboberfläche; APIs/CLI schlagen ohne Dateizugriff fehl und verweisen auf `legacy_task_editor.py`. |
| `_src/tools/test_runner_transaction.py` | Hermetische Git-/Fehler-Injektions-Tests für atomare Check-ins, Trailer/Marker-/Claim-Bindung, Abbruch, Rollback, Index-Isolation, CAS-Rennen, Symlink-/Pfadschutz und Ergebnis-Persistenz |
| `output/logs/<task-id>/<request-id>/` | Ignorierte, request-spezifische Voll-Logs, strukturierte Ergebnisse, validierte Report-Kopien und Recovery-Journale des Transaktionswerkzeugs |
| `output/run-archive/run-<timestamp>-n<seq>.sh` + `.log` | Vollständiges Archiv jedes `run.sh`-Aufrufs — Skript + Ausgabe, sequenziell durchnummeriert |
| `output/run-current.log` | Veränderlicher Zeiger/Log des jeweils letzten (oder laufenden) Legacy-Aufrufs; nie als alleiniger Abschlussnachweis verwenden |

### Erstinitialisierung des Legacy-Runners

Auf einer neuen macOS-Installation wird die mutierende Einrichtung ausschließlich
explizit gestartet. Standardmäßig fragt der Runner vor jeder fehlenden Installation
nach Bestätigung:

```sh
_src/run-loop.sh --init /tmp/autodocs/run.sh
```

Für unbeaufsichtigte Provisionierung muss zusätzlich `--batch` beziehungsweise `-b`
angegeben werden; `--batch` ohne `--init` wird abgewiesen:

```sh
_src/run-loop.sh --init --batch /tmp/autodocs/run.sh
```

Die Initialisierung prüft funktionsfähig statt nur nach Pfad-Präsenz: Python 3 mit
`pip`, Git, SSH sowie Node.js 20+ mit npm. Fehlende Systemwerkzeuge werden über
Homebrew eingerichtet beziehungsweise aktualisiert; fehlt Homebrew selbst, wird der
offizielle Installer verwendet. Projektlokal unter `output/` werden `lxml`, der
npm-Cache, Playwright 1.62.1 und temporäre Laufdaten isoliert. Der WebKit-Browser
liegt im Playwright-Cache unter `~/Library/Caches/ms-playwright`. Ein fehlender
Runner-SSH-Schlüssel wird erzeugt; sein öffentlicher Schlüssel muss anschließend
manuell beim benötigten GitHub-Konto oder Repository registriert werden.

`--init` führt nach erfolgreicher Einrichtung den Sandbox-Selbsttest aus und beendet
sich. Ohne `--batch` ist ein interaktives Terminal erforderlich. Normale Aufrufe und
`--self-test-only` führen keine Paket- oder Browserinstallation aus.

## Werkzeuge des vereinheitlichten Kurations-/Review-Modells (0006-14)

Zusätzlich zu den oben gelisteten Werkzeugen gehören zum vereinheitlichten
Modell (**0006-03**/**0006-06**/**0006-13**):

| Werkzeug | Zweck |
|---|---|
| `_src/tools/curation_item.py` | Lesende Normalisierung von `review-flag@v1`/`curation-flag@v1` nach `curation-item@v1`. Schreibt nichts. |
| `_src/tools/workflow_lifecycle.py` | Gemeinsame Zustandsvokabular (`discovered…superseded`) und `TOOL_TRANSITIONS`-Zuordnung jeder bestehenden Schreib-Funktion zu ihrem gültigen Von-/Nach-Zustand; `validate_transition()`-Helfer. |
| `_src/tools/curation_item_lifecycle_check.py` | Prüft, dass `curation_item.VALID_STATUSES` und `workflow_lifecycle.STATES` konsistent bleiben (`validate_vocabularies()`), und ordnet einem konkreten Item seinen Lebenszyklus-Zustand zu (`item_lifecycle_state()`). Eingebunden in `validate.py::check_workflow_lifecycle()`. |

Siehe [`curation-item-schema.md`](curation-item-schema.md),
[`workflow-lifecycle.md`](workflow-lifecycle.md),
[`workflow-validation.md`](workflow-validation.md) für Details.


## Versioned data-model tools

The versioned curation toolchain now spans `version_id.py`, `version_store.py`,
`curation_item.py`, `dependency_graph.py`, `confidence.py`, `typed_claim.py`,
`supersession_trigger.py`, `asof_view.py`, and `delta_view.py`. Together they
cover id minting, immutable storage, version-pinning, graph semantics,
invalidation/confidence, typed synthesized claims, trigger orchestration, and
historical/delta queries.

