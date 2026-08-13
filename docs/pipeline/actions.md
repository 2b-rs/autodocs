# Aktionen

Jede Zeile ist eine konkrete, aufrufbare (oder zumindest benannte) Aktion.
"Implementiert" heißt: ein CLI-Kommando oder eine Funktion existiert im Repo
und führt genau diese Aktion aus.

## Ingest-Aktionen

### Ingest Review (Requirement-Text-Review übernehmen)

- **Werkzeug**: `review_ingest.py`
- **Aufruf**: `python3 _src/tools/review_ingest.py --check paket.json` /
  `--apply paket.json` / `-g 1 2` (GitHub-Issues) / `--apply -g 1 2 --repo
  2b-rs/autodocs`
- **Beschreibung**: Liest ein Review-Paket (Requirement-Text-Entscheidung),
  entweder lokal als JSON oder direkt aus einem GitHub-Issue. Prüft
  `text_hash` gegen den aktuellen Record, um veralteten Text zu erkennen
  (Konflikt statt stiller Übernahme). Einziger schreibender Weg für diese
  Paketart zurück in die Spec-DB.
- **Status**: Implementiert. `--check` ist ein reiner Dry-Run (kein Schreiben
  auf Platte, `apply=False`); `--apply` schreibt atomar.

### Ingest Feedback (Kurationsentscheidung übernehmen)

- **Werkzeug**: `curation_ingest.py`
- **Aufruf**: `python3 _src/tools/curation_ingest.py --check paket.json` /
  `--apply paket.json` / `--apply --issue-body issue-42.md`
- **Beschreibung**: Liest eine Kurationsentscheidung (Freigabe/Ablehnung +
  Begründung zu einem Fäll, den die Extraktion nicht automatisch entscheiden
  konnte) und legt dafür ein Flag in `spec/curation-queue/open/` an. Schreibt
  NICHT direkt in die Records — das übernimmt später ein KI-Agent + Kurator.
- **Status**: Implementiert (`curation_flags.write_curation_flag`).

## Evidenz-Aktionen

### Add Evidence (rohe Evidenz hinzufügen)

- **Werkzeug**: `upstream_evidence.py`
- **Beschreibung**: Schreibt für jede lokal definierte ID pro Dokument und
  Backend eine unveränderliche Datei unter
  `_src/spec/upstream/evidence/<document>/<id>/<backend>.json` mit dem rohen
  Textausschnitt, unverändert, VOR jeder Normalisierung/Reparatur.
  Umsetzung des Prinzips "Preserve raw evidence at every stage" aus
  `NEXTSTEPS.md` (jetzt `SPEC_QUALITY_ROADMAP.md`).
- **Status**: Implementiert, aber begrenzter Scope als "Evidenz aus
  informellen Dokumenten" (Phase 5 in `SPEC_BUILD_PROCESS.md`) — dies sind
  Backend-Rohbeobachtungen, keine Prosa-Belege aus Sekundärdokumenten.

### Infer Evidence (Evidenz aus informellen Dokumenten ableiten)

- **Beschreibung**: Phase-5-Prozess: KI-Extraktor liest informelle
  Dokumente/Code/Beispiele mit Blick auf eine Record-Gruppe, überträgt
  wörtliche Belegsätze mit Fundstelle und Evidenzstärke
  (`strong`|`medium`|`weak`) in den Evidenzspeicher des Records, oder
  schlägt ein neues Element als `hypothesized/unconfirmed` vor.
- **Status**: **Nur als Prozess/Vorlage beschrieben** (`SPEC_BUILD_PROCESS.md`
  Phase 5). Kein Skript im Repo automatisiert diesen Schritt — der
  eigentliche Lese-/Inferenzschritt ist ein externer KI-Aufruf.

## Entscheidungs-Aktionen

### Make Decision (strittigen Fall entscheiden)

- **Beschreibung**: Zwei Varianten je nach Rolle:
  - **KI-Entscheidung** (Phase 3): `decision.value` + `decision.rationale` +
    `decision.confidence` für Felder mit `invalid/to-be-confirmed`; Ergebnis
    landet als `valid/ai-decided` mit Trace `mode: "ai_decision"`.
  - **Kurator-Entscheidung**: letzte Instanz bei Kurationsanfragen und
    KI-Entscheidungen mit niedriger Confidence; `complete_flag()` schließt
    das offene Flag.
- **Status**: Kuratoren-Seite implementiert (`review_flags.complete_flag`,
  `curation_flags.complete_flag`); KI-Entscheidungslogik selbst nur als
  Schema/Vorlage beschrieben, kein Automatismus im Repo.

## Rebuild-Aktionen

### Rebuild DB (Records neu aufbauen/anreichern)

- **Werkzeug**: `spec_scrape.py` (`upstream --rebuild`, `props`, `ids`,
  `reqs --write-reqs`), `spec_upstream.py` (`rebuild_record_files`),
  `review_ingest.py --apply`, `curation_ingest.py --apply`,
  `migriere_spec_db.py`, `namespace_migrate.py`,
  `migriere_ns_enclosing.py`, `migriere_schema_language.py`.
- **Beschreibung**: Sammelbegriff für jeden schreibenden Vorgang auf
  `_src/spec/records/*.json`. Konkret dokumentiert im aktuellen Working Tree:
  `spec_scrape.py upstream --rebuild` hat 2.996 Records angereichert (siehe
  Provenienz-Analyse in dieser Konversation).
- **Status**: Implementiert und tatsächlich ausgeführt (siehe
  `output/run-archive/run-2026-08-11_17-34-37-n0217.*`).

### Rebuild HTML (kompletten HTML-Baum neu erzeugen)

- **Werkzeug**: `_src/generate.py`
- **Aufruf**: `python3 _src/generate.py` (schreibt alle deutschen Seiten
  nach `../`) / `--check` (nur Vergleich, kein Schreiben, DOM-Diff) /
  `python3 _src/generate.py classes/cl_ara_core_Future_420ba8.html` (einzelne
  Seite)
- **Beschreibung**: Erzeugt den kompletten HTML-Tree aus den Quellen unter
  `_src/`. Gegenstück: `extract.py` (Resync von Hand editiertem HTML zurück
  in Quellen — laut Docstring "im Normalfall NICHT nötig").
- **Status**: Implementiert, voll funktionsfähig CLI.

### Rebuild i18n'ed Files (übersetzte Register und Diagramme aktualisieren)

- **Werkzeuge** (mehrstufige Pipeline):
  1. `i18n_extract.py` — baut deutsches Quellregister
     (`_src/i18n/segments.de.json`, Labels).
  2. `i18n_translate.py split <lang> [--kb=40]` — erzeugt Übersetzungs-
     Arbeitspakete (JSONL) unter `i18n/work/<lang>/batch_NN.jsonl`.
  3. `i18n_translate.py` (merge-Kommando, aus Docstring impliziert) — führt
     übersetzte Batches zurück in die Sprachregister.
  4. `i18n_diagrams.py` — materialisiert übersetzte Diagramme: prüft je
     Sprache/Diagrammquelle das Label-Register, rendert neu bei Abweichung.
- **Status**: Implementiert als mehrteilige CLI-Kette; kein einzelner
  "rebuild all i18n" Befehl gefunden — die Schritte werden nacheinander
  aufgerufen.

### Rebuild Diagrams (Diagrammquellen neu rendern)

- **Werkzeug**: `render_diagrams.py`
- **Beschreibung**: Rendert alle Diagramme aus ihren Quellen (Graphviz
  `.dot`, Sequenzdiagramme `.seq.json` via `seqgen.py`) neu.
- **Status**: Implementiert.

### Rebuild Indexes (Analyse-CSVs neu erzeugen)

- **Werkzeug**: `build_indexes.py`
- **Beschreibung**: Erzeugt kondensierte CSV-Sichten unter `_src/data/` aus
  `_src/sources/pages/**.json` und Fragmenten — Lesesichten für Analyse, QA
  und als kompakter Kontext für KI-Werkzeuge. Änderungen daran fließen NICHT
  in den generierten HTML-Baum zurück (reine Ableitung).
- **Status**: Implementiert.

### Rebuild Component Graph (Abhängigkeitsgraph ableiten)

- **Werkzeug**: `build_component_graph.py`
- **Beschreibung**: Baut den abstrakten API-Abhängigkeitsgraphen aus
  Seitenmodellen und Spec-Records ab — nie handgepflegt. Ownership kommt aus
  `rec-ref`-Blöcken in Seitenmodellen, Abhängigkeiten aus internen Links im
  jeweiligen Record.
- **Status**: Implementiert.

## AI-Content-Aktionen (`ai_workflow.py`)

Zyklus **Invalidieren → Auftrag → Merge**, für KI-generierte Erklärungen
(Texte + Diagramme) auf Seitenebene, getrennt vom Spec-DB-Kampagnenprozess.

| Kommando | Aktion | Status |
|---|---|---|
| `status` | Überblick: legacy/aktuell/veraltet, Records geändert (Hash-Abgleich), Traces ohne Fragment, Fragmente ohne Trace, Policy-Versionen | Implementiert |
| `zeige <fragment>` | Trace eines Fragments zusammengefasst anzeigen | Implementiert |
| `invalidiere [ziele] [--grund=…]` | Fragmente als "veraltet" markieren (`--quelle=<dok-id>`, `--element=<ID>`, oder Pfad) | Implementiert |
| `auftrag <ziel>…` | Regenerierungsauftrag nach `ai/work/` schreiben (Fragmentpfad, Seitendatei, Element-ID, oder `--veraltet` für alle veralteten) | Implementiert |
| `merge` | `ai/work/auftrag_*.out.json` prüfen und einspielen (Fragmente, Diagrammquellen, Traces) | Implementiert |

Nach `merge` folgt laut Docstring der übliche Nachlauf: `render_diagrams.py`
(falls Diagramme geändert) → `generate.py` → `validate.py` →
`i18n_extract.py`. Inhaltliche Leitplanken: `_src/ai/RICHTLINIEN.md`.

## Sonstige QA-Aktionen

| Aktion | Werkzeug | Beschreibung | Status |
|---|---|---|---|
| Bezeichner-Scan | `scan_bezeichner.py` | Findet Label-Einträge, deren Schlüssel wie ein API-Identifier aussieht | Implementiert |
| Lazy-Copy-Scan | `scan_lazycopy.py` | Findet Übersetzungseinträge, die identisch zum deutschen Original sind | Implementiert |
| Rest-Deutsch-Scan | `scan_restdeutsch.py` | Sucht in Übersetzungsregistern nach verbliebenem Deutsch | Implementiert |
| Font-Inventar | `font_inventory.py` | Inventarisiert eingebettete Fonts und Glyph-Mapping-Fehler je Dokument | Implementiert |
| Geometrie-Audit | `geometry_audit.py` | Prüft dokument-unabhängige Geometrie-Invarianten über den PDF-Korpus | Implementiert |

## Seiten-Chrome-Texte (Banner, Hinweise, Badges)

Neue statische UI-Texte im generierten Seiten-Chrome muessen ueber `_src/i18n/ui.json` lokalisierbar sein, nicht als literale deutsche Strings im Python-Code der Renderer (`lib_docmodel.py`). Details und Hintergrund: siehe `_src/WARTUNG.md`, Abschnitt „Regel: Seiten-Chrome-Texte gehoeren in die i18n-Register, nicht in Python-Strings“ (0008-01/0008-06).

## Bezug zum vereinheitlichten Kurations-/Review-Modell (0006-14)

Die Aktionen "Ingest Review" und "Ingest Feedback" oben schreiben weiterhin
direkt in `review-flag@v1`/`curation-flag@v1`-Formate; sie ändern sich durch
**0006-03**/**0006-06** nicht. Was neu ist: jedes so entstandene Flag lässt
sich verlustfrei in **curation-item@v1** normalisieren
(`curation_item.from_review_flag()`/`from_curation_flag()`,
[`curation-item-schema.md`](curation-item-schema.md)), und jeder erlaubte
Zustandsübergang jeder hier aufgeführten Aktion ist im
gemeinsamen Lebenszyklus (`_src/tools/workflow_lifecycle.py`,
[`workflow-lifecycle.md`](workflow-lifecycle.md)) als `TOOL_TRANSITIONS`-
Eintrag hinterlegt und durch `validate.py::check_workflow_lifecycle()`
(**0006-13**) laufend gegen das Schema geprüft. Neue Ingest-/Kurations-
Aktionen sollen von Anfang an so entworfen werden, dass ihr Ergebnis in
`curation-item@v1` normalisierbar ist, statt ein weiteres Ad-hoc-Format zu
erfinden.


## Version-aware actions

The pipeline's curation actions are now explicitly version-aware: record new
immutable requirement versions, pin decisions/evidence to exact versions,
append graph edges, record confidence/invalidation events, and query either
point-in-time (`asof_view`) or windowed-delta (`delta_view`) views. Actions
that react to new releases/comments/scraper changes should route through the
supersession-trigger layer rather than inventing their own ad-hoc diff logic.

