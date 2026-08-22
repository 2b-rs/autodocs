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
| `build_report.py` | Aggregiert Subreports zu kanonischem Gesamtbericht, erzeugt statisches HTML-Seitenmodell `build-reports.html` und trägt den Lauf ins getrackte Build-Ledger ein | `python3 _src/tools/build_report.py combine` / `publish` / `mint-ref` / `--no-ledger` |
| `build_ledger.py` | Getracktes, append-only Build-Ledger `docs/evidence/build-ledger.jsonl` (ein Eintrag je Veröffentlichungslauf; `DEC-0043-001`); prüft Schema, Duplikate und — gegen eine Git-Baseline — die Append-only-Eigenschaft byte-genau (siehe `build-ledger.md`) | `python3 _src/tools/build_ledger.py verify [--baseline=HEAD]` / `list` / `backfill-historic` |
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

## Prozessdokumentations-Prüfung

| Werkzeug | Zweck |
|---|---|
| `process_doc_doctor.py` | Read-only-Konsistenzprüfung des Prozessdokumentations-Korpus: `DOC001` tote relative Links, `DOC002` Index-Abdeckung, `DOC003` zitiertes Prozessdokument ohne Rückanker, `DOC004` unverlinkte Dokumente (aggregiert, informativ), `DOC005` unzitierte Entscheidungsdatensätze, `DOC006` unerreichbares Task-gebundenes Kontraktdokument |

Aufruf: `python3 _src/tools/process_doc_doctor.py [--json] [--strict]`

Es prüft **Struktur, nicht Wahrheit**: ob die Dokumente, die einen Prozess
definieren, zusammenhängen und erreichbar sind — nicht, ob der Prozess auch
gelebt wird. Letzteres bleibt Aufgabe einer QA-Rolle
([`process-roles.md`](process-roles.md)).

Unverlinkt zu sein ist bei **Nachschlagewerken kein Mangel** — niemand navigiert
zu einem Schema, man schlägt es nach. `DOC004` fasst diese Fälle deshalb zu
einem informativen Befund zusammen. Aussagekräftig ist allein `DOC006`: ein
Dokument, das sich selbst über eine `Status:`-Zeile als Kontrakt oder
Spezifikation eines Backlog-Items ausweist und trotzdem von nirgends erreichbar
ist. Es bindet entweder noch und niemand findet es, oder es bindet nicht mehr
und sagt das nirgends.

Es repariert nichts, schreibt nichts und ist **standardmäßig beratend**: ohne
`--strict` ist der Exit-Code immer `0`. Es in ein blockierendes Tor zu hängen,
ist eine Entscheidung mit Reichweite über die eigene Arbeitseinheit hinaus und
verlangt deshalb einen Entscheidungsdatensatz nach `TK-2`. Genau diese Kopplung
ohne Datensatz war der Fehler von Task `0038-03`, den Feature `0040` beseitigen
soll.

## Integrations-Hygieneprüfung

| Werkzeug | Zweck |
|---|---|
| `check_integration_hygiene.py` | Read-only-Vorprüfung vor jeder Integration (`DEC-0044-010`, `DEC-0044-015`, Tasks `0044-14`/`0044-15`): prüft **alle** registrierten Worktrees des gemeinsamen Repositories auf `INDEX_NOT_HEAD` (eigener Index ≠ `HEAD`), `FOREIGN_STAGED_TREE` (fremder Worktree hält einen gestagten Baum), `MAIN_WORKTREE_DIRTY` (getrackte Dateien im `main`-Worktree ≠ Index), `STALE_AFTER_REF_MOVE` (Branch-Ref vorgerückt, Index und Dateien stehen noch auf dem vorigen Reflog-Tip) und `WORKTREE_UNAVAILABLE` |

Aufruf: `python3 _src/tools/check_integration_hygiene.py --repo <integrations-worktree> [--json]`

Exit-Codes: `0` sauber, `1` Befunde, `2` die Prüfung selbst konnte nicht laufen —
eine `2` ist ein **Fehlschlag, kein Bestehen**. `--json` liefert
`integration-hygiene-report@v1`.

Das Werkzeug schreibt **nichts**: keine Dateien, Refs, Indizes oder Objekte. Es
findet Zustand, den die Git-Historie grundsätzlich nicht zeigen kann — genau die
Schadensklasse, die den Root-Checkout mit einem gestagten Baum aus der Zeit vor
dem Abschluss von Feature `0040` zurückließ.

Zwei Eigenschaften müssen mitgelesen werden, sonst wird der Prüfung mehr
zugetraut, als sie leistet:

- `FOREIGN_STAGED_TREE` ist **kein Vorwurf**. Dass ein anderer Agent in seinem
  eigenen Worktree etwas staged, ist der Normalfall. Der Befund sagt nur, dass
  Zustand existiert, den die Historie nicht zeigt, und dass eine Integration
  nicht darüber hinweggehen darf. Aufgelöst wird er vom Eigentümer (committen
  oder stashen) — **niemals** durch ein Zurücksetzen eines fremden Worktrees.
- `MAIN_WORKTREE_DIRTY` meldet die bekannte Restabweichung getrackter Dateien
  bei sauberem Index nun blockierend, aber ausschließlich für den Worktree, der
  `main` auscheckt. Derselbe ungestagte Zustand in einem lebenden
  Vorgangs-Worktree ist normale unfertige Arbeit und erzeugt bewusst keinen
  Befund. Untracked Dateien bleiben ebenfalls außerhalb der Prüfung. Deshalb
  verlangt `DEC-0044-015` weiterhin zusätzlich den harten Preflight im Root
  (`git diff --quiet`, `git diff --cached --quiet`, `HEAD` ist
  `refs/heads/main`). Werkzeug und Preflight ergänzen einander; keines ersetzt
  das andere.

Einbindung in die Integrationsprozedur, der bestätigte Mechanismus hinter
`STALE_AFTER_REF_MOVE` und die `preserved/*`-Momentaufnahmen:
[`branch-workflow.md`](branch-workflow.md).

Tests: `_src/tools/test_check_integration_hygiene.py` (hermetische Git-Fixtures;
Aufruf aus `_src/tools/`: `python3 -m unittest test_check_integration_hygiene -v`).

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
| `runner-host/run-loop.sh` | Legacy-Watch-/One-Shot-Runner mit Sandbox, Umgebungs-Selbsttest und expliziter Erstinitialisierung über `--init`; normale Selbsttests installieren oder aktualisieren keine Abhängigkeiten |
| `_src/tools/runner_transaction.py` | Fail-closed Legacy-Transaktion für `generate → validate → promote → substantive commit → REF bookkeeping → claim finalization` (`close-task-v1`, `verify-and-commit-v1`); feste Action-IDs, Kandidaten-Worktree, temporärer Git-Index, CAS-Publikation, Recovery-Journal und strukturierte Ergebnisse; seit `0038-05.02` zusätzlich das feste `legacy-editor-candidate-v1`-Profil, das einen bereits geplanten `legacy_task_editor.py`-Kandidaten (Pickup/Progress/Closure/Wontfix/Parent-Aggregation/REF-Injection/Claim-Handoff/-Finalisierung) über dieselbe Journal-/Lock-/Promote-/Rollback-Maschinerie autoritativ mehrdateiig promotet, statt einer zweiten Schreiboberfläche; sowie, als `branch-merge-v1` (`0038-20`, implementiert den `0038-19`-Vertrag), die typisierten `base-branch`/`merge-prereqs`-Aktionen: sequentielle Nicht-Oktopus-2-Parent-Merges in einem Wegwerf-Worktree, CAS-Publikation nur auf die eigene, noch nicht integrierte Item-Branch, Append-only-Claim-Union bei identischem `owner_token`, strukturelle Ablehnung jedes Task→Feature-/Feature→`main`-/`integrate-checkpoint`-Versuchs; siehe [`runner-transaction.md`](runner-transaction.md) |
| `_src/tools/environment_doctor.py` | Rein lesende, portable Diagnose der Ausführungsumgebung; erzeugt ein digest-gebundenes `prepared-environment@v1` mit Capability-/Protokoll-Gates und optional verifiziertem Cache; Aufruf: `python3 _src/tools/environment_doctor.py --root <root> --requirements <requirements.json> --profile <profile.json> [--observations <observations.json>] [--cache-root <dir>] [--write-cache]`; siehe [`environment-doctor.md`](environment-doctor.md) |
| `_src/tools/task_evidence_pack.py` | Baut ein kompaktes, content-addressed `task-evidence-pack@v1`-Manifest je Task-Versuch: dedupliziert Blob-Store für Beleg-Bytes, `tracked-ref`-Verweise auf committete Quell-/Probe-Skripte statt Kopien in Zeitstempel-Logs, gebundenes Excerpt, Kriterien-Mapping; weist Geheimnisse, Wildcard-Pfade, fremde Task-Evidenz und ignorierte Scratch-Pfade als alleinigen Abschlussnachweis fail-closed zurück; Aufruf: `python3 _src/tools/task_evidence_pack.py build --root <root> --blob-root <dir> --out-manifest <pack.json> --task-id <id> --action <name> --base-commit <sha> --tool-name <name> --exit-status <n> --items-json <json>` / `verify --manifest <pack.json>`; siehe [`task-evidence-pack.md`](task-evidence-pack.md) |
| `_src/tools/artifact_retention.py` | Claim-bewusste Quarantäne, Aufbewahrung und Dry-run-first Garbage Collection für Task-Artefakte (`0038-11`): `quarantine` verschiebt einen partiellen/fehlgeschlagenen Export/Report/Scratch-Versuch mit strukturiertem Zustand/Fehler/Digest/Retry-Flag unter einen laufversuchseigenen `.partial`-Wurzelpfad; `plan`/`gc` klassifizieren jeden `output/logs/<task-id>/<request-id>`-Versuch in eine Aufbewahrungsstufe (`successful-log`/`failed-trace`/`cache`/`scratch`/`permanent-manifest`) und schlagen Löschungen nur für terminale, unbeanspruchte, TTL-abgelaufene Artefakte vor; verweigert aktive Claims, nicht abgeschlossene Transaktions-Journale (`0038-10`), unbekannte Zustände und den `current.json`-Zeiger, respektiert `task-evidence-pack@v1`-Referenzen (`0038-12`) und schützt vor Uhr-Drift; echte Löschung nur mit explizitem `--apply`; Aufruf: `python3 _src/tools/artifact_retention.py quarantine --root <root> --task-id <id> --request-id <id> --source <pfad> --kind <art> --state {partial,failed,interrupted,superseded}` / `gc --root <root> [--apply] [--json]` |
| `_src/tools/task_validation.py` | Wertet einen unveränderlichen Validierungslauf gegen ein `task-validation-profile@v1` aus; erzwingt Freshness, Stage-/Input-/Output-Verträge, Coverage-Canaries und strukturierte Fehler statt blindem Vertrauen in Exit 0; Aufruf: `python3 _src/tools/task_validation.py --profile <profile.json> --run <result.json>`; siehe [`task-validation.md`](task-validation.md) | 
| `_src/tools/candidate_budget.py` | Isoliert generierte Kandidaten und erzwingt Ausgabe-/Diff-/Realismus-Budgets (`0038-13`): generiert ausschließlich in laufversuchseigene `output/logs/<task-id>/<request-id>/.candidates/`-Wurzeln (wie `0038-11`s `.partial`-Muster); ein `candidate-budget@v1`-Vertrag deklariert `sole_writer`, erlaubte Pfadmuster, Datei-/Byte-Budgets, erforderliche Teilbäume (z. B. Sprachbäume), Realismus-Byte-Untergrenzen je Kategorie (gerendert/heruntergeladen/übermittelt), optionale Negativ-Pfad-Pflicht, ein Duplikat-Digest-Verhältnis gegen synthetisches Platzhalter-Material sowie eine Soll-Manifest-Diff-Toleranz; `evaluate()` liefert PASS/FAIL/INCONCLUSIVE wie `0038-08`; `promote()` blockiert bei Nicht-PASS, verweigert Überschreiben eines fremden `sole_writer` an einem festen Exportpfad, kopiert nie eine nicht deklarierte Dateifamilie und ist über einen atomaren `current.json`-Zeiger (Muster wie `0038-10`) atomar/recoverable; Aufruf: `python3 _src/tools/candidate_budget.py manifest --root <root> --task-id <id> --request-id <id>` / `evaluate --budget <budget.json> --task-id <id> --request-id <id> --out-report <report.json>` / `promote --budget <budget.json> --task-id <id> --request-id <id> --destination <pfad> --report <report.json> [--apply]` |
| `_src/tools/chore_tool_inventory.py` | Lifecycle-Vertrags-Klassifikation der getrackten mutierenden Chore-Werkzeuge (`0038-14`): wiederverwendet `automation_safety.tracked_automation_paths()` als lebende Enumeration statt eigenen Git-Scans; lädt `chore_tool_inventory_data.json` und trennt strikt `classified` (Kategorie, Write-Set, Commit-Points, Idempotenz-Schlüssel, Journal, Cleanup, Failure-Aggregation, Ownership, Retention, Test-Referenz) von `enumerated` (nur Heuristik-Kategorie, ausdrücklich nicht klassifiziert); `--check` validiert Schema plus Abgleich gegen die lebende Skript-Liste (meldet fehlende/veraltete Einträge) und ist exit-0 nur bei null Fehlern; Aufruf: `python3 _src/tools/chore_tool_inventory.py --check [--json] [--list {classified,enumerated,missing,stale}] [--category <kategorie>]` |
| `_src/tools/legacy_task_doctor.py` | Read-only, deterministic diagnosis for legacy `TODO.md`/`DONE.md`, claims, REFs, prerequisites, and agent bootstrap; invoke with `python3 _src/tools/legacy_task_doctor.py [--json]`; emits at most ten summary lines or `legacy-task-doctor-report@v1` JSON and never repairs, takes over, or deletes anything; see [`legacy-task-doctor.md`](legacy-task-doctor.md) |
| `_src/tools/legacy_scope_planner.py` | Rein lesender, fail-closed Kollisionsplaner für direkte und abgeleitete Schreibbereiche; kombiniert normalisierte aktive Claims, den autoritativen `issue-regeneration-dag@v1` und exakt gebundene Git-/Runner-/Generator-/i18n-/Publikations-Snapshots, erklärt Producer-Ketten und liefert `PARALLEL`, `SERIALIZE`, `BLOCK` oder `INCOMPLETE`; siehe [`legacy-scope-planner.md`](legacy-scope-planner.md) |
| `_src/tools/task_context_capsule.py` | Rein lesender, größenbudgetierter Task-Kontext-/Resume-Capsule-Generator; komponiert `legacy_task_doctor.py`, `legacy_scope_planner.py` und die unveränderlichen `runner_transaction.py`-Attempt-Ergebnisse (`0038-10`) zu kompaktem `task-context-capsule@v1`-JSON plus Zehn-Zeilen-Zusammenfassung, damit ein Agent nach Kontext-/Tool-Budget-Grenzen ohne Wiederholung erledigter Arbeit fortsetzen kann; Aufruf: `python3 _src/tools/task_context_capsule.py --root . --task-id <id> [--claim-path <pfad>] [--max-bytes <n>] [--json]`; siehe [`task-context-capsule.md`](task-context-capsule.md) |
| `_src/tools/legacy_task_editor.py` | Digest-gebundener struktureller Planer für Pickup, Fortschritt, Closure/Wontfix, Parent-Aggregation, REF-Korrektur und Claim-Handoff/-Finalisierung; erzeugt immer content-addressed Candidate+Diff, verifiziert Promotion-Preimages erneut und liefert bis `0038-05.02` ausschließlich `verified-coordinator-required` ohne autoritative Mutation; siehe [`legacy-task-editor.md`](legacy-task-editor.md) |
| `_src/tools/task_bookkeeping_closure.py` | **Stillgelegt:** frühere freie TODO-/Claim-Direktschreiboberfläche; APIs/CLI schlagen ohne Dateizugriff fehl und verweisen auf `legacy_task_editor.py`. |
| `_src/tools/test_runner_transaction.py` | Hermetische Git-/Fehler-Injektions-Tests für Abbruch, Rollback, Index-Isolation, Zwei-Commit-Closure, CAS-Rennen, Symlink-/Pfadschutz und Ergebnis-Persistenz; `BranchMergeTransactionTests` (`0038-20`) deckt zusätzlich `base-branch`/`merge-prereqs` ab: Basis-off-Parent, sequentielle Mehrquellen-Merges, Claim-Union bei gleichem `owner_token`, Ablehnung bei fremdem `owner_token`/veraltetem Source-Tip/nicht deklarierter Quelle/Sandboxed-Task→Feature-Versuch, sowie Publish-dann-Crash-Recovery |
| `_src/tools/check_policy_provenance.py` | Rein lesende, stdlib-only Herkunftsprüfung für Integrations-Policy-Commits (`RQ-IP-04`/`DEC-0044-002`, `0044-01`): meldet für einen Merge-Kandidaten (`--source-branch`, `--target-branch`), welche Commits, die den deklarierten Policy-Pfad (`docs/pipeline/branch-workflow.md` per Default, `--policy-path` wiederholbar) berühren und für die Integration einzigartig zum Source-Branch wären, `source-origin`, `target-pull-in-eligible` (erlaubtes Hereinziehen der Ziel-Policy, `DEC-0044-001`) oder `foreign-branch` (Verstoß gegen `DEC-0044-002`, zu prüfen) sind; mutiert nie Refs/Working-Tree, trifft keine Entscheidung selbst; Aufruf: `python3 _src/tools/check_policy_provenance.py --source-branch <b> --target-branch <b> [--policy-path <pfad>...] [--repo <pfad>] [--json]`; Tests: `_src/tools/test_check_policy_provenance.py` |
| `_src/tools/legacy_handoff_manifest.py` | Rein lesende, stdlib-only Prüfung des Pre-Activation-Handoff-Manifests (`0038-16.01`): bindet das exakte `0037-37`-Review-Paket (Datei-Digest, `base_commit`, alle 17 Kontrakt-Digests, gegen den Arbeitsbaum nachgerechnet) und beweist über `docs/pipeline/legacy-handoff-manifest-v1.json`, dass jedes überlebende Legacy-Primitiv (action, schema, result, scope, evidence, recovery, context, validation, approval-readiness) **genau eine** Disposition trägt — entweder eine typisierte `0037-46.01`-Aktion/Kontrakt oder einen expliziten `0037-46.02`-Retirement-Trigger — und dass kein `authority_key` und keine Aktions-ID doppelt beansprucht wird; die Abdeckung wird gegen die lebende Mechanismen-Tabelle dieses Abschnitts geprüft, nicht gegen eine Kopie; aktiviert keine Queue und ändert keine Autorität (prüft im Gegenteil, dass weder `.runner/` noch `_src/runner/` existiert); Aufruf: `python3 _src/tools/legacy_handoff_manifest.py --check [--json] [--root <root>]`; siehe [`legacy-handoff-manifest.md`](legacy-handoff-manifest.md) |
| `output/logs/<task-id>/<request-id>/` | Ignorierte, request-spezifische Voll-Logs, strukturierte Ergebnisse, validierte Report-Kopien und Recovery-Journale des Transaktionswerkzeugs |
| `output/run-archive/run-<timestamp>-n<seq>.sh` + `.log` | Vollständiges Archiv jedes `run.sh`-Aufrufs — Skript + Ausgabe, sequenziell durchnummeriert |
| `output/run-current.log` | Veränderlicher Zeiger/Log des jeweils letzten (oder laufenden) Legacy-Aufrufs; nie als alleiniger Abschlussnachweis verwenden |

### Erstinitialisierung des Legacy-Runners

Auf einer neuen macOS-Installation wird die mutierende Einrichtung ausschließlich
explizit gestartet. Standardmäßig fragt der Runner vor jeder fehlenden Installation
nach Bestätigung:

```sh
runner-host/run-loop.sh --init /tmp/autodocs/run.sh
```

Für unbeaufsichtigte Provisionierung muss zusätzlich `--batch` beziehungsweise `-b`
angegeben werden; `--batch` ohne `--init` wird abgewiesen:

```sh
runner-host/run-loop.sh --init --batch /tmp/autodocs/run.sh
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
