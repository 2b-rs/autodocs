# Wartungsanleitung — ara::* API-Referenz (R25-11)

- Alle Prozesse zum manuellen und automatischen Umgang mit Projektdaten sind
  verbindlich beschrieben in: docs/pipeline.

Der HTML-Tree (`index.html`, `classes/`, `namespaces/`, `modules/`, `services/`)
ist ein **Build-Artefakt**. Maßgebliche Quellen liegen unter `_src/`. Inhalte
werden **nicht** im generierten HTML geändert, sondern in den Quellen — danach
wird der Tree neu generiert. Das gilt auch für die neun übersetzten Sprachbäume
(`en/`, `es/`, `pt/`, `fr/`, `ru/`, `ar/`, `hi/`, `ko/`, `zh/` — s. Kapitel
„Mehrsprachige Bäume (i18n)“).

Neugenerierung via:
```bash
python3 _src/generate.py && python3 _src/validate.py
```

Das Schichtenmodell der Pipeline (Spezifikations-DB → KI-Kuratierung →
Komposition → i18n → HTML) und die Rezepte zum Erweitern des Umfangs (neue
Module, Funktionscluster, ganze Projekte) stehen in `ARCHITEKTUR.md`.

## Verzeichnislayout

```
ara-api-doku/
├── index.html, classes/, namespaces/, modules/, services/   ← GENERIERT
├── style.css                    ← Quelle: zentrales Stylesheet (direkt editierbar)
├── fold.js                      ← Quelle: Verhalten der klappbaren Abschnitte
│                                (Deep-Link-Aufklappen, Drucken; direkt editierbar)
├── en/, es/, pt/, fr/, ru/, ar/, hi/, ko/, zh/   ← GENERIERTE Sprachbäume
│                                (gleiche Struktur wie der deutsche Tree)
└── _src/
    ├── WARTUNG.md               ← diese Anleitung
    ├── ARCHITEKTUR.md           ← Schichtenmodell, Erweiterungsrezepte
    ├── KONVENTIONEN.md          ← inhaltliche & gestalterische Konventionen
    ├── site.json                ← Projektmanifest: Titel, Bereiche, Sprachen
    ├── generate.py              ← Quellen → HTML-Tree
    ├── validate.py              ← Qualitätsprüfungen (Links, Anker, Aktualität)
    ├── build_indexes.py         ← erzeugt die CSV-Indizes unter data/
    ├── extract.py               ← HTML-Tree → Quellen (nur für Resync!;
    │                              erhält Diagrammquellen .dot/.seq.json)
    ├── i18n_extract.py           ← deutsche Quellen → Segment-/Label-Register
    ├── i18n_translate.py         ← Batch-Verwaltung: status / split / merge
    ├── i18n_diagrams.py          ← übersetzte Diagramm-SVGs je Sprache
    ├── lib_i18n.py               ← Extraktions-/Übersetzungsregeln (s. u.)
    ├── i18n/                     ← Register, Batches, ui.json, ANWEISUNG.md
    │                              (Details im i18n-Kapitel unten)
    ├── render_diagrams.py       ← Diagrammquellen → SVGs (Datei + Inline)
    ├── seqgen.py                ← Generator für Sequenzdiagramme (.seq.json → SVG)
    ├── lib_svgdiag.py           ← Graphviz-Nachbearbeitung, Modell- und
    │                              Äquivalenzprüfung der Diagramme
    ├── ai_workflow.py           ← KI-Kuratierung: status/auftrag/merge/invalidiere
    ├── lib_docmodel.py          ← gemeinsames Datenmodell / Renderer / Loader
    ├── templates/
    │   ├── page.html.tmpl       ← Seiten-Chrome (head, header, nav, main, footer)
    │   └── footers.json         ← die vier Footer-Textvarianten
    ├── sources/pages/**.json    ← ein Seitenmodell pro HTML-Seite (Komposition)
    ├── spec/records/**.json     ← Spezifikations-DB: ein Record je Datei,
    │                              adressierbar über die ID (s. Kapitel unten)
    ├── spec/pdf-cache/<REL>/    ← Cache der normativen AUTOSAR-Standard-PDFs
    │                              (Quelle der Validierung; manifest.sha256
    │                               dokumentiert den Stand; nur über run.sh
    │                               befüllt, s. Kapitel „Spec-PDF-Cache“)
    ├── content/ai/**.html       ← alle KI-generierten Blöcke als Einzelfragmente
    │                              (+ Quellen der Inline-Diagramme:
    │                               <fragment>.<diag-id>.dot|.seq.json)
    ├── ai/                      ← KI-Kuratierung: RICHTLINIEN.md, policy.json,
    │                              quellen.json (Quellenregister),
    │                              traces/** (Herkunftsakten je Fragment),
    │                              work/ (Regenerierungsaufträge)
    ├── diagrams/**.svg          ← alle Datei-Diagramme; GENERIERT aus der
    │                              danebenliegenden Quelle svg_NN.dot|.seq.json
    ├── tools/                   ← QA-Scans + Einmalwerkzeuge (s. tools/README.md)
    └── data/*.csv               ← GENERIERTE Indizes (Lesesichten, s. u.)
```

## Voraussetzungen

- Python 3 mit `lxml` (basiert auf libxml2) — einzige harte Abhängigkeit
- `graphviz` (`dot`, Bestand wurde mit 14.x gerendert) für Diagramm-Rendering
- optional: `playwright`/Chromium für Screenshot-QA

## Standard-Workflow: Ändern → Generieren → Validieren

```bash
# 1. Quelle ändern (siehe Tabelle unten)
# 2. Tree neu generieren (alle Seiten oder gezielt einzelne):
python3 _src/generate.py
python3 _src/generate.py classes/cl_ara_core_Future_420ba8.html
python3 _src/generate.py --lang=alle   # zusätzlich alle 9 Sprachbäume
# 3. Prüfen:
python3 _src/validate.py        # Aktualität, tote Links/Anker, Waisen-Fragmente
python3 _src/build_indexes.py   # CSV-Indizes auffrischen
```

### Extraktions-Berichte: Bauen vs. Publizieren

Der Extraktions-Bericht hat **zwei getrennte Schritte**:

1. `python3 _src/tools/extraction_report.py build` erzeugt bzw. aktualisiert die
   Berichtsdaten: `_src/sources/pages/extraction-report.json`,
   `extraction-reports-data.js` und die versionierten Seitenmodelle unter
   `_src/sources/pages/reports/extraction-report-v%04d.json`.
2. `python3 _src/generate.py` rendert diese Seitenmodelle erst in die
   browsebaren HTML-Seiten am Web-Wurzelverzeichnis, also u. a.
   `extraction-reports.html` sowie `extraction-report-v%04d.html`.

Wichtig: `build` **publiziert noch nichts sichtbar im HTML-Tree**. Wer nur
`extraction_report.py build` ausführt, bekommt neue Versions-Metadaten, aber
keine neuen `extraction-report-v%04d.html`-Dateien. Für sichtbare Änderungen im
Web muss danach immer `generate.py` laufen.

Seit 2026-08-12 ist `record_version()` versionsneutral für reine
Publikationsläufe: Wenn Kennzahlen, Residual-Status und relevante
Extraktionsskript-Stände unverändert sind, wird keine neue Berichtsversion
angelegt; ein nachträgliches `generate.py` rendert dann lediglich bestehende
Versionen nach HTML aus, statt Dubletten wie v0012/v0013 zu erzeugen.

**Bewahrung veröffentlichter Berichte (`DEC-0043-002`):** Vorhandene
versionierte Seitenmodelle und gerenderte `extraction-report-v%04d.html`-Seiten
werden standardmäßig bewahrt. Ein neuer Lauf legt nur das fehlende Modell seiner
neuen Version an. Verlust oder ein schwerer Erzeugerfehler erlauben eine
auditierbare Ersetzung; eine forensische Rekonstruktion bleibt immer ein
getrennter Kandidat. Das aktuelle Arbeitsmodell
`_src/sources/pages/extraction-report.json`, das Berichtsverzeichnis und der
Startseitenindex sind dagegen Live-Sichten und werden auf die neueste Version
aktualisiert. Die vollständigen Ausnahmen und Nachweispflichten stehen in
`docs/pipeline/reports.md` und `DEC-0043-002`.

Für lokale Agent-/Sandbox-Läufe gilt zusätzlich AGENTS.md: wegen CPU-/I/O-Last
immer über `run.sh` ausführen und darin **beide** Schritte kombinieren
(`extraction_report.py build && python3 _src/generate.py`).

Nach inhaltlichen Änderungen an deutschen Quellen gilt zusätzlich der
i18n-Workflow (neue/geänderte Segmente übersetzen, s. u.) — sonst fallen die
betroffenen Stellen in den Sprachbäumen auf Deutsch zurück und `generate.py`
meldet fehlende Übersetzungen.

`generate.py` ist idempotent und byte-stabil: gleiche Quellen ⇒ identische Dateien.

## Diagramme: Quellen und Rendern

Alle 447 Diagramme sind aus Quelldateien generiert; die SVGs sind Build-Artefakte.

| Diagrammtyp | Quelle | Ablage |
|---|---|---|
| Graphviz (UML-Klassen-, Kontext-, Strukturdiagramme) | `.dot` | Datei-Diagramme: `_src/diagrams/<seite>/svg_NN.dot`; Inline-Diagramme: `_src/content/ai/<seite>/<fragment>.<diag-id>.dot` |
| Sequenzdiagramme | `.seq.json` | analog: `svg_NN.seq.json` bzw. `<fragment>.<diag-id>.seq.json` |

```bash
# Quelle ändern, dann:
python3 _src/render_diagrams.py                # alles neu rendern
python3 _src/render_diagrams.py classes/cl_x   # nur passende Quellen
python3 _src/render_diagrams.py --pruefe-alt   # zusätzlich prüfen, dass neue
                                               # SVGs informationsgleich zu den
                                               # bisherigen sind (Migrationen)
python3 _src/generate.py && python3 _src/validate.py
```

- `render_diagrams.py` schreibt Datei-SVGs neu und patcht Inline-SVGs direkt in
  den KI-Fragmenten (per lxml, niemals per Regex).
- Graphviz-Ausgaben werden durch `lib_svgdiag.postprocess_dot_svg()` in den
  Hausstil überführt (responsive Wurzelattribute, `vis-…`-Klassen am `<a>`).
- Das `.seq.json`-Format (Teilnehmer, Nachrichten, Selbstaufrufe, Notizen,
  `alt`/`opt`-Rahmen mit Guards und Trennern) ist im Kopf von `seqgen.py`
  dokumentiert; Raster und Farben sind dort bewusst fest verdrahtet.
- Neues Diagramm: Quelle am passenden Ort ablegen (Namensschema oben), auf der
  Seite bzw. im Fragment einen Wrapper mit eindeutiger `id="diag-…"` anlegen,
  dann rendern und generieren.
- `tools/svg2dot.py`/`tools/svg2seq.py` waren Einmalwerkzeuge zur Rückgewinnung
  der Quellen aus den Bestands-SVGs (mit Roundtrip-Verifikation); für die
  laufende Pflege werden sie nicht benötigt (s. `tools/README.md`).

## Was wird wo geändert?

| Änderung | Ort |
|---|---|
| KI-Text (Guides, Nutzungshinweise, Fehlerpfad-Abschnitte) — manuell | `_src/content/ai/<seite>/<fragment>.html` (Herkunftsakte `_src/ai/traces/…` mitpflegen) |
| KI-Text neu erzeugen / regenerieren lassen | `ai_workflow.py auftrag` → `merge` (s. Kapitel „KI-Kuratierung“) |
| Inhalt eines Spezifikations-Records (Text, Attribute, Tabellen im Record) | `_src/spec/records/<GRUPPE>/<ID>.json` |
| Normative Quell-PDFs fuer die Validierung (Dokumentregister, Cache) | `_src/tools/spec_scrape.py` (`DOCS`) + `_src/spec/pdf-cache/<RELEASE>/` (nur ueber `run.sh`) |
| Referenzinhalt einer Seite (Blockfolge, Tabellen, Listen, Überschriften) | `_src/sources/pages/<seite>.json` |
| Projekttitel, Bereiche (Rubriken), Sprachenliste, Flaggen | `_src/site.json` |
| Leitplanken/Parameter der KI-Generierung (Modell, Budgets, Diagrammkriterien) | `_src/ai/policy.json` + `_src/ai/RICHTLINIEN.md` |
| Diagramm | Quelle ändern (`.dot` bzw. `.seq.json`, liegt neben dem SVG bzw. neben dem KI-Fragment), dann `python3 _src/render_diagrams.py` — niemals SVGs direkt editieren (s. o.) |
| Farben, Typografie, Badges, Abstände (global) | `style.css` (direkt, wird nicht generiert) |
| Klappverhalten der Guide-Abschnitte | `fold.js` (direkt, wird nicht generiert); Abschnitt ein-/ausklappbar machen: Blocktyp `fold` im Seiten-JSON |
| Seiten-Chrome: `<head>`, Kopfzeile, Breadcrumb-Rahmen, Footer | `_src/templates/page.html.tmpl`, `footers.json` |
| Navigationszeile einer Seite (Badge, Crumbs) | Feld `nav_html` im Seiten-JSON |
| Neue Seite | JSON einer ähnlichen Seite kopieren, `file`/`title`/Blöcke anpassen; Verweise auf die neue Seite in Namespace-/Modul-Listen ergänzen |
| Übersetzungen (alle 9 Sprachen) | Register/Batches unter `_src/i18n/` — niemals im generierten Sprachbaum; Workflow s. Kapitel „Mehrsprachige Bäume (i18n)“ |
| UI-Texte der Sprachbäume (Chrome, Rubriken, docref-Bausteine) | `_src/i18n/ui.json` |

## Das Seitenmodell (JSON)

Jede Seite ist eine Liste von Blöcken unter `"main"`. Blocktypen:

- `html` — beliebiges Element verbatim (`"html"`-Feld). Für Überschriften,
  Meta-Zeile, Syntaxblöcke, Beschreibungen, Listen.
- `props` / `params` — Eigenschafts- bzw. Parameter-Tabellen als strukturierte
  Zeilen (`rows`); Zelleninhalt ist HTML-Text. Bevorzugt hier ändern statt in
  Roh-HTML.
- `rec` — ein Spezifikations-Record (`<article class="rec">`) mit `id`, `attrs`
  und rekursiver Blockliste. In den Seiten-JSONs steht seit der Auslagerung in
  die Spezifikations-DB nur noch ein **Verweis** (`rec-ref`, s. Kapitel
  „Spezifikations-DB“); `lib_docmodel.load_page()`/`iter_pages()` lösen ihn
  beim Laden transparent zu einem vollen `rec`-Block auf.
- `ai` — Verweis auf ein KI-Fragment (`src` relativ zu `_src/`).
- `svg` — Diagramm-Wrapper; `src` zeigt auf die SVG-Datei, `wrap_attrs` trägt
  die Wrapper-Klasse (`umlwrap` bzw. `diagram`).
- `fold` — klappbarer Abschnitt (`<details class="fold">`): `summary` enthält die
  `<h2 class="sect">`-Überschrift verbatim, `blocks` die Abschnittsblöcke
  (rekursiv). Alle KI-Guide-Abschnitte (Plattformüberblick, User Guides,
  „Verwendung“/„Technische Einordnung“) sind so gewickelt und initial
  eingeklappt. Klappverhalten: `fold.js` (Wurzel), Optik: `style.css`
  (Abschnitt „Klappbare KI-Guide-Abschnitte“). Deep Links auf Anker im
  Abschnitt (z. B. `#diag-…`, `#guide-…`) öffnen ihn automatisch per JS.

Jeder Block hat ein `tail`-Feld (Whitespace nach dem Element) — unverändert lassen.
Die vollständige Felddoku steht im Kopf von `lib_docmodel.py`.

## Spec-PDF-Cache (`_src/spec/pdf-cache/<RELEASE>/`)

Die Spezifikations-DB unter `_src/spec/records/` wird gegen die **normativen
AUTOSAR-Standard-PDFs** validiert. Diese PDFs liegen versionsweise im Cache,
jetzt hierarchisch nach Hersteller/Familie/Plattform gegliedert:

```
_src/spec/pdf-cache/R25-11/
├── AUTOSAR/
│   ├── AP/
│   │   ├── AUTOSAR_AP_SWS_Core.pdf
│   │   ├── AUTOSAR_AP_RS_General.pdf
│   │   └── …
│   ├── CLASSIC/
│   ├── FOUNDATION/
│   │   ├── AUTOSAR_FO_RS_Diagnostics.pdf
│   │   ├── AUTOSAR_FO_PRS_E2EProtocol.pdf
│   │   ├── AUTOSAR_FO_RS_Safety.pdf
│   │   └── …
│   └── …
├── ECLIPSE/
└── manifest.sha256                 ← Inhaltsverzeichnis (SHA-256 je PDF, relativer Pfad)
```

- **`source-map.json`** (`_src/spec/pdf-cache/<RELEASE>/source-map.json`) haelt
  je Cache-Eintrag den relativen lokalen Pfad, den Plattformzweig, das Release
  und die kanonische Download-URL unter `autosar.org/fileadmin/standards/`
  fest, inklusive noch fehlender, aber bereits bekannter Dokumente (z. B.
  `AUTOSAR_FO_EXP_SafetyOverview.pdf`, `cached: false`). Wird von Hand
  gepflegt, sobald ein Dokument neu registriert oder umbenannt wird; nicht
  automatisch generiert.

- **Dateinamen sind nicht frei waehlbar.** Sie entsprechen exakt den auf der
  Startseite verlinkten Standarddokumenten (`_src/sources/pages/index.json`,
  Abschnitt „Quellen“). Das Dokumentregister `DOCS` in
  `_src/tools/spec_scrape.py` haelt Modul, Zweig, PDF-Basisnamen und
  Record-Praefix zusammen; es muss mit dieser Liste deckungsgleich bleiben.
- **Die Cache-Hierarchie ist semantisch, nicht namensbildend.** Die Werkzeuge
  suchen PDFs rekursiv unterhalb des Release-Verzeichnisses; massgeblich fuer
  die Identitaet bleibt der PDF-Basisname, nicht sein Unterordner.
- **Befuellt wird ausschliesslich ueber `run.sh`** (die MCP-Sandbox hat keinen
  Netzzugriff, siehe `AGENTS.md`). Der Cache ist der Standardwert von
  `--pdf-dir`; ohne Option arbeiten alle Unterbefehle auf diesem Verzeichnis.
- **Ein gueltiger Cache-Eintrag wird nie ueberschrieben.** Heruntergeladen wird
  in eine `.part`-Nebendatei, die erst nach Pruefung der PDF-Signatur
  umbenannt wird.

```bash
python3 _src/tools/spec_scrape.py ids                       # nutzt den Cache
python3 _src/tools/spec_scrape.py crosscheck --json         # beide Backends
python3 _src/tools/spec_scrape.py all --check               # DB gegen PDFs
```

## Spezifikations-DB (`_src/spec/records/`)

Jedes Spezifikationselement (Record, `<article class="rec">` mit ID wie
`SWS_CORE_00512`) liegt als eigene Datei `spec/records/<GRUPPE>/<ID>.json`
(GRUPPE = die ersten beiden Unterstrich-Token der ID, z. B. `SWS_CORE`).
Dateiformat: `{"id", "attrs", "lead", "blocks"}` — identisch zum `rec`-Block
des Seitenmodells, nur ohne Einbettungskontext.

Im Seiten-JSON steht an der Einbaustelle ein Verweis:

```json
{"t": "rec-ref", "src": "spec/records/SWS_CORE/SWS_CORE_00512.json", "tail": "\n"}
```

`load_page()`/`iter_pages()` (lib_docmodel) lösen Verweise beim Laden zu vollen
`rec`-Blöcken auf; alle Pipeline-Skripte arbeiten darüber. Damit ist ein
Record **unabhängig von seiner Seite adressierbar**: Inhaltliche Änderungen an
einem Element passieren genau in seiner Record-Datei; wo es eingebaut ist,
sagt `data/records.csv` (Spalten `datei`/`quelle`). Nach Änderungen den
üblichen Zyklus fahren (generate → validate → i18n); `ai_workflow.py status`
meldet anschließend KI-Texte, deren zugehörige Records sich geändert haben
(Hash-Abgleich).

Ein Record an eine andere Stelle einbauen = denselben `rec-ref` in ein anderes
Seiten-JSON setzen. `validate.py` meldet Record-Dateien, die nirgends
referenziert sind, und `extract.py` (Resync) lagert Records automatisch wieder
in die DB aus.

### Review-Fallback: JSON manuell nach GitHub uebernehmen

Der Browser-Workflow in `review.js` kennt zwei Versandwege:

- **Authentifiziert**: `submitPackage()` postet direkt ein neues GitHub-Issue an
  `https://api.github.com/repos/<repo>/issues`. Der Issue-Body besteht nur aus
  einem ```json-Block mit einem `review-package@v1`, `identity` ist dabei
  `github_authenticated`.
- **Fallback ohne Token**: `exportPackage()` laedt stattdessen eine Datei
  `ara-review-<timestamp>.json` herunter. Das JSON hat ebenfalls
  `schema: "review-package@v1"`, aber `identity: "self_declared"` und einen
  Warnhinweis zur geringeren Vertrauensstufe.

Manuelle Uebernahme des Fallback-Pakets in GitHub:

1. Die exportierte `ara-review-*.json` lokal oeffnen und den kompletten Inhalt
   unveraendert kopieren.
2. Im Ziel-Repository ein neues Issue anlegen (derselbe Repo-Wert wie im
   `<meta name="review-github-repo">` der HTML-Seite; aktuell
   `2b-rs/autodocs`).
3. Als Titel z. B. `Requirement review package (manual fallback)` verwenden.
4. Den kopierten JSON-Inhalt als einzigen Issue-Body in einen fenced Block
   einsetzen:

   ```json
   { ... exportierter Paketinhalt ... }
   ```

5. Issue absenden. Danach kann der Import lokal mit
   `python3 _src/tools/review_ingest.py -g <ISSUE_NR>` geprueft oder mit
   `python3 _src/tools/review_ingest.py --apply -g <ISSUE_NR>` uebernommen
   werden.
6. Fuer strengere Uebernahme `--require-authenticated` **nicht** setzen: ein
   Fallback-Paket traegt absichtlich `identity: self_declared` und wird damit
   sonst schon vor der Einzelpruefung abgelehnt.

Wichtig: Das JSON nicht umformatieren, nicht mit zusaetzlichem Freitext
mischen und nicht auf mehrere Kommentare verteilen. `review_ingest.py`
erwartet im Issue-Body genau ein gueltiges Paket-JSON (optional in einem
äusseren ```json-Block), das `_strip_code_fence()` / `json.loads()` direkt
parsen koennen.

## KI-Kuratierung und Traceability (`_src/ai/`)

Vollständig dokumentiert in `ai/RICHTLINIEN.md` (inhaltliche Leitplanken,
Trace-Schema, Regenerierungs-Workflow); maschinenlesbare Parameter in
`ai/policy.json` (Modell, Annahmen-Budgets, Diagramm-Kriterien,
Relevanz-Cutoffs — globale Änderung ⇒ `version` erhöhen). Kurzfassung:

- Jedes KI-Fragment `content/ai/<pfad>/<stem>.html` hat eine Herkunftsakte
  `ai/traces/<pfad>/<stem>.json`: assoziierte Records, Zitate, Quelldokumente
  (Register: `ai/quellen.json`), extrahiertes Wissen, Annahmen, Prompt,
  Modell, Lauf-Historie mit Denk-Transkripten, Diagramm-Entscheidungen und
  Record-Stände (SHA1) zur Veraltet-Erkennung.
- Der Bestand von August 2026 trägt `status: "legacy"` (Prompt/Transkripte der
  Ursprungsgenerierung nicht mehr rekonstruierbar; Rest automatisch belegt).
- Zyklus: `ai_workflow.py status` → `invalidiere` → `auftrag` (Auftrag unter
  `ai/work/`, eingebettet: Policy + Richtlinien + Records + bisheriges
  Fragment + Trace) → Modell bearbeitet Auftrag → `merge` (prüft Struktur,
  ai-note, Platzhalter, Annahmen-Budget; schreibt Fragment, Diagrammquellen
  und Trace). Danach: render_diagrams (falls Diagramme), generate, validate,
  i18n_extract.
- KI-Fragmente doch manuell editiert? Trace mitpflegen (mindestens `laeufe`
  ergänzen bzw. `status` prüfen) — sonst lügt die Herkunftsakte.

## Build- & Publikations-Berichte (`build_report.py`)

Jeder Veröffentlichungslauf der Dokumentations-Pipeline erzeugt maschinenlesbare
Subreports (`i18n_merge`, `i18n_diagrams`, `html_generate`, `validate`) unter
`output/build-reports/` gemäß `docs/pipeline/build-report-schema.md`.

### `RUN_ARCHIVE_REF` (Lauf-Korrelation, 0043-01)

`generate.py`, `validate.py`, `i18n_translate.py` und `i18n_diagrams.py` lesen
alle die Umgebungsvariable `RUN_ARCHIVE_REF` und schreiben ihren Wert in das
`run_archive_ref`-Feld ihres jeweiligen Subreports (Schema siehe
`docs/pipeline/build-report-schema.md`). `build_report.py combine` gruppiert
Subreports zu einem Kohorten-Report ausschließlich über einen **gemeinsamen,
nicht-leeren** `run_archive_ref`; ohne ihn (bzw. bei uneinheitlichem Wert)
schlägt `combine` absichtlich fehl (fail-closed) statt eine falsche Kohorte zu
raten.

- **Runner-Lauf:** `runner-host/run-loop.sh` setzt `RUN_ARCHIVE_REF` automatisch
  vor jeder Ausführung des überwachten Skripts auf
  `run-archive/run-<timestamp>-n<seq>` — denselben Namensstamm, unter dem es
  Log (`.log`) und Skript (`.sh`) danach unter `output/run-archive/` archiviert.
  Jeder Subprozess des Runs erbt die Variable automatisch.
- **Manueller Build (außerhalb des Runners):** Es gibt kein Runner-Archiv, das
  benannt werden könnte. Vor dem manuellen Aufruf der Produzenten muss daher
  ein Fallback-Wert gesetzt werden, den `build_report.py mint-ref` erzeugt.
  Er trägt das Präfix `manual-` (gefolgt von UTC-Zeitstempel und 8 Hex-Zeichen
  Zufall), damit er nie mit einem echten, vom Runner vergebenen Ref verwechselt
  oder kollidieren kann:

```bash
export RUN_ARCHIVE_REF="$(python3 _src/tools/build_report.py mint-ref)"
python3 _src/generate.py && python3 _src/validate.py
python3 _src/i18n_translate.py merge <lg>     # falls Teil des Laufs
python3 _src/i18n_diagrams.py <lg>            # falls Teil des Laufs
```

Alle Produzenten desselben Laufs (ob Runner oder manuell) müssen mit
demselben `RUN_ARCHIVE_REF`-Wert laufen, damit `combine` sie als eine Kohorte
erkennt.

`build_report.py` führt diese Subreports zusammen und erzeugt das publizierte
Seitenmodell `_src/sources/pages/build-reports.json`, welches in `build-reports.html`
gerendert wird:

### Die kanonische Bau- und Publikationsfolge (0043-04)

**`combine` und `publish` gehören zur Folge, nicht dazu.** Genau ihr Fehlen hat
die eingefrorene `build-reports.html` verursacht, die Feature `0043` ausgelöst
hat: die Produzenten liefen, aber nichts hat den Bericht je neu veröffentlicht.
Die vollständige Folge ist:

```bash
# 0. Kohorten-Identität für den ganzen Lauf setzen (Runner setzt sie selbst)
export RUN_ARCHIVE_REF="$(python3 _src/tools/build_report.py mint-ref)"

# 1. Produzenten — alle unter demselben RUN_ARCHIVE_REF
python3 _src/i18n_translate.py merge <lg>     # falls Teil des Laufs
python3 _src/i18n_diagrams.py <lg>            # falls Teil des Laufs
python3 _src/generate.py
python3 _src/validate.py                      # erste Validierung

# 2. Subreports zu einem Lauf aggregieren und den Lauf ins Ledger schreiben
#    (verwendet $RUN_ARCHIVE_REF, falls nicht per --run-archive-ref=<ref>
#    überschrieben)
python3 _src/tools/build_report.py combine

# 3. Bericht veröffentlichen: Seitenmodell samt Publikations-Provenienz erzeugen
python3 _src/tools/build_report.py publish

# 4. Seitenmodell in den HTML-Tree rendern
python3 _src/generate.py build-reports.html

# 5. Abschließende Validierung — prüft u. a. die Aktualität des Berichts
python3 _src/validate.py
```

Schritt 5 läuft unter demselben `RUN_ARCHIVE_REF` und erzeugt daher **keine
neuere Kohorte**; er ist die Endabnahme des Laufs, kein neuer Lauf.

Wird Schritt 2 oder 3 ausgelassen, meldet `validate.py` das ab sofort als
Fehler (`stale-build-report` bzw. `unrecorded-publication-run`, Task `0043-04`,
Entscheidung `DEC-0043-003`) — der Bericht kann nicht mehr unbemerkt einfrieren.
Die Prüfung ist rein beobachtend: sie repariert nichts, sondern nennt den
Befehl, der fehlt. Ist nur die Bindung veraltet, während der Seitenkörper
stimmt (etwa weil der kombinierte Rohreport unter git-ignoriertem `output/`
nicht mehr vorliegt), genügt:

```bash
python3 _src/tools/build_report.py provenance   # idempotent, nur die Bindung
```

Details zum Objekt `publication_provenance` im Seitenmodell:
[`docs/pipeline/build-report-schema.md`](../docs/pipeline/build-report-schema.md).

### Build-Ledger (`docs/evidence/build-ledger.jsonl`, 0043-02)

`combine` und `publish` hängen jeden Veröffentlichungslauf als **eine Zeile** an
das getrackte, append-only Build-Ledger `docs/evidence/build-ledger.jsonl` an
(Entscheidung `DEC-0043-001`, Schema und Konsumentenvertrag:
[`docs/pipeline/build-ledger.md`](../docs/pipeline/build-ledger.md)). Der
Eintrag hält Zeitpunkt, `run_archive_ref`, Repository-Commit, Exit-Status,
Zähler je Stufe, Befundzahl und den SHA-256-Digest des kombinierten Reports
fest. Die **Rohdaten** bleiben git-ignoriert: das Ledger verweist auf
`output/build-reports/combined-*.json` und `output/run-archive/`, kopiert sie
aber nicht ins Repository.

Regeln für den Betrieb:

- Ein Lauf erzeugt genau einen Eintrag; das `publish` nach dem `combine`
  desselben Laufs erkennt ihn an `run_archive_ref` wieder und schreibt nicht
  erneut.
- **Einträge werden nie nachträglich geändert.** Ist etwas falsch, wird ein
  neuer Eintrag angehängt. Prüfen lässt sich das mit:

```bash
python3 _src/tools/build_ledger.py verify --baseline=HEAD
python3 _src/tools/build_ledger.py list --limit=10
```

- Nach einem Lauf gehört die neue Ledger-Zeile **eingecheckt** — sie ist die
  konfigurationsverwaltete Evidenz, nicht ein Nebenprodukt.
- Konnte das Ledger nicht geschrieben werden, endet `combine`/`publish` mit
  einem Exit-Code ≥ 1, auch wenn der Build selbst grün war.
- `--no-ledger` unterdrückt den Eintrag und ist ausschließlich für
  Diagnoseläufe gedacht, die nicht in die Bauhistorie gehören.

Der erste Eintrag ist der nachgetragene (`backfilled`) historische Lauf vom
2026-08-13/14 — der eingefrorene Stand, der Feature `0043` ausgelöst hat.

Das publizierte `build-reports.html` verlinkt direkt auf das zugehörige
Runner-Archiv (`output/run-archive/run-<timestamp>-n<seq>.log`), sofern
`run_archive_ref` einen tatsächlich vorhandenen Runner-Archiv-Pfad benennt; ein
`manual-*`-Fallback wird stattdessen als Klartext-Referenz angezeigt (kein
Archiv-Link, da keines existiert). So bleibt vollständige Traceability vom
HTML-Artefakt bis zum ausführenden Prozess gewährleistet, ohne bei manuellen
Läufen einen nicht existenten Link vorzutäuschen.

## CSV-Indizes unter `_src/data/` (nur lesen!)

Kondensierte Sichten für Analyse, Reviews und als kompakter Kontext für
KI-Werkzeuge. Sie werden von `build_indexes.py` **erzeugt** — Änderungen darin
fließen nicht in den Tree zurück.

- `records.csv` — alle 3533 Spezifikations-Records (Seite, SWS-ID, Quelldatei
  in `spec/records/`, Art, Name, Upstream, Scope, Exception-/Thread-Sicherheit,
  Kurzbeschreibung, KI-Fragmente)
- `pages.csv` — Seiteninventar (Typ, Titel, Interface-Typ, Modul, Zählwerte)
- `links_extern.csv` — jedes Vorkommen eines externen Links (Linktext-QA!)
- `ki_bloecke.csv` — Index aller KI-Fragmente
- `diagramme.csv` — Index aller SVG-Diagramme

## Mehrsprachige Bäume (i18n)

Der deutsche Tree ist die einzige inhaltliche Quelle. Die neun Sprachbäume
(`LANGS` in `lib_docmodel.py`; RTL-Menge `RTL = {"ar"}`) werden vollständig
generiert: `generate.py --lang=<lg>` rendert jede Seite aus den deutschen
Quellen und ersetzt dabei Segmente, Labels, Navigation und Diagramme durch die
übersetzten Fassungen. Der Flaggen-Umschalter oben rechts (RTL: oben links)
verlinkt jede Seite auf ihre Entsprechung in allen Sprachen.

### Dateien unter `_src/i18n/`

- `segments.de.json` — Register aller übersetzbaren Segmente. Schlüssel ist die
  `sid` = `sha1(maskiertes innerHTML)[:12]`; geschützte Kinder (Links, `code`,
  SVG …) sind im maskierten Text durch Platzhalter `⟦0⟧ ⟦1⟧ …` ersetzt.
- `labels.de.json` — Diagramm-/Tabellenbeschriftungen; Schlüssel ist der volle
  Labeltext (in Batches mit Präfix `L:`). Mehrzeilige Labels enthalten
  literale `\n`-Zeichen (in JSON als `\\n`).
- `<lg>/segments.json`, `<lg>/labels.json` — akzeptierte Übersetzungen je Sprache.
- `<lg>/diagrams/`, `<lg>/inline/` — gerenderte übersetzte SVGs (generiert).
- `work/<lg>/batch_NN[.out].jsonl` — Übersetzungs-Batches (Eingabe/Ausgabe).
- `ui.json` — feste UI-Texte je Sprache (Seitenkopf, Rubriken, Footer,
  docref-Bausteine für lokalisierte Kapitelverweise).
- `whitelist.json`, `whitelist_labels.json` — kuratierte Nicht-Übersetzen-Listen;
  `kandidaten*.json` — von `i18n_extract.py` vorgeschlagene Grenzfälle, die in
  die Whitelist oder ins Register wandern.
- `ANWEISUNG.md` — verbindliche Übersetzungsanweisung für die Batch-Übersetzung
  (Invarianten, Nicht-Übersetzen-Regeln, Stil je Zielsprache).

### Workflow

```bash
python3 _src/i18n_extract.py            # 1. Register aus deutschen Quellen auffrischen
python3 _src/i18n_translate.py status   # 2. offene Segmente je Sprache anzeigen
python3 _src/i18n_translate.py split <lg>   # 3. offene Segmente als Batch exportieren
# 4. Batch übersetzen (gemäß i18n/ANWEISUNG.md) → work/<lg>/batch_NN.out.jsonl
python3 _src/i18n_translate.py merge <lg>   # 5. prüfen + übernehmen
python3 _src/i18n_diagrams.py [<lg>]        # 6. übersetzte Diagramm-SVGs rendern
python3 _src/generate.py --lang=alle        # 7. Sprachbäume neu generieren
python3 _src/build_indexes.py && python3 _src/validate.py   # 8. QA
```

### Merge-Mechanik (`i18n_translate.py`)

- `merge` verarbeitet bei jedem Lauf **alle** `batch_*.out.jsonl` einer Sprache
  in sortierter Reihenfolge — spätere Dateien überschreiben frühere. Korrekturen
  daher entweder in der ursprünglichen `.out`-Zeile patchen oder als neue,
  höher nummerierte Batch-Datei anlegen.
- `merge` bricht mit Exit-Code 1 ab, wenn eine Zeile eine unbekannte `sid`
  trägt (z. B. nach Register-Änderungen): veraltete Zeilen aus den
  `.out`-Dateien entfernen.
- `pruefe()` verwirft Zeilen maschinell bei: Platzhalter-Abweichung (`⟦k⟧`-Menge
  muss identisch sein), veränderten Kennungen (`[SWS_…]`, `AUTOSAR_…`, `EXP_…`,
  `FO_…`) und abweichender `em`/`strong`-Anzahl.
- `normalisiere_zitate()` normalisiert beim Übernehmen deutsche Anführungszeichen
  („…“) in die Typografie der Zielsprache (en/hi/ko/zh “…”, es/pt/ru/ar «…»,
  fr «\u202f…\u202f»). Englische Originalzitate bleiben davon unberührt, weil
  sie bereits in der Quelle gerade Anführungszeichen tragen.

### Extraktionsregeln (`lib_i18n.py`)

- Übersetzt werden Prosa-Blöcke (`BLOCKTAGS`: p, li, h3–h6, figcaption, dt, dd,
  caption), Tabellenzellen (`ZELLTAGS`: td, th) mit deutscher Prosa sowie
  bestimmte Spans (`SPAN_UEBERSETZBAR`: `dim`, `chip`, `interp`).
- `PROTECT = {a, code, svg, br, span, img}` wird maskiert (Platzhalter).
- Klassenlose Links mit rein deutschem Text sind übersetzbar
  (`link_uebersetzbar`), auch wenn sie geschützte Kinder wie `<code>` enthalten —
  dann läuft die Ersetzung über `maskiere`/`entmaskiere`.
- `a.docref`-Linktexte werden nicht als Ganzes übersetzt, sondern über die
  docref-Bausteine in `ui.json` lokalisiert: die Verpackung („§“, „Kapitel“,
  „Anhang“, Seitenangaben) folgt der Zielsprache, zitierte Kapiteltitel und
  Dokumentnamen bleiben wörtlich englisch.
- Inline-Sequenzdiagramme (`*.seq.json` neben KI-Fragmenten) werden mit
  extrahiert; Diagrammtexte laufen über das Label-Register.
- Erkennung deutscher Prosa (`ist_deutsch`) ist heuristisch (Stoppwörter,
  Umlaute). Bekannte False-Positives: englische Registereinträge mit „der/die“
  als Namensbestandteil, spanisch „antigüedad“. Kandidatenlisten kuratieren
  statt Heuristik aufweichen.

### Diagrammübersetzung (`i18n_diagrams.py`)

- Übersetzt `.dot`-/`.seq.json`-Quellen über das Label-Register und rendert die
  SVGs nach `i18n/<lg>/diagrams/` bzw. `i18n/<lg>/inline/`; `generate.py`
  bevorzugt diese, sonst fällt die Seite auf das Original-SVG zurück.
- Ergibt die Übersetzung einer Quelle keinen Unterschied mehr (z. B. nach dem
  Zurücksetzen fälschlich übersetzter API-Namen), wird eine eventuell
  vorhandene veraltete Zieldatei **gelöscht** — nie von Hand in den
  `i18n/<lg>/diagrams/`-Verzeichnissen arbeiten.
- Namen von Spezifikationselementen (Klassen, Methoden wie `Subscribe()`,
  `Serializable` …) werden in Diagrammen niemals übersetzt; Label-Einträge,
  die das doch tun, per Korrektur-Batch auf den Originaltext zurücksetzen.

### QA der Sprachbäume

- `validate.py` prüft alle Bäume (Links, Anker, Aktualität) und erkennt
  korrupte Platzhalter-Reste (`⟦…⟧`) im generierten HTML.
- `generate.py --lang=…` meldet fehlende Übersetzungen (deutscher Fallback) —
  Ziel ist 0.
- Zusätzliche Scans nach jedem größeren Übersetzungslauf — als Skripte unter
  `tools/` (Exit-Code 1 bei Funden, Details in `tools/README.md`):
  1. **Lazy-Copy-Scan** (`tools/scan_lazycopy.py`): Übersetzungseinträge,
     die identisch zum Deutschen sind (Whitelists werden berücksichtigt).
  2. **Rest-Deutsch-Scan** (`tools/scan_restdeutsch.py`): nicht nur
     Umlaute/„…“, sondern auch umlautfreie Stoppwörter
     (`zeigt|zur|zum|nicht|wird|…`) — deutsche Teilsätze überleben sonst
     unbemerkt in Übersetzungen.
  3. **Bezeichner-Scan** (`tools/scan_bezeichner.py`): Label-Einträge, deren
     Schlüssel wie ein Identifier aussieht (CamelCase, `::`, `()`), müssen
     identisch übersetzt sein.
- Visuelle Stichproben je Sprache (Playwright): arabische RTL-Seiten,
  CJK/Devanagari-Rendering, französische Guillemets mit schmalem
  geschütztem Leerzeichen, Flaggen-Umschalter, übersetzte Diagramme.

## Ausnahme: Direkteingriff ins generierte HTML

Nur wenn es gar nicht anders geht — und dann **nie mit Textersetzung/Regex**,
sondern mit XML-Werkzeugen (libxml2: `lxml` oder `xmllint`), damit die
Dokumentstruktur garantiert intakt bleibt:

```python
from lxml import html
doc = html.parse("classes/cl_x.html")
for a in doc.iter("a"):
    ...
doc.write("classes/cl_x.html", method="html", encoding="utf-8")
```

Danach zwingend die Quellen zurücksynchronisieren, sonst überschreibt der
nächste `generate.py`-Lauf die Änderung:

```bash
python3 _src/extract.py            # HTML → Quellen (Resync)
python3 _src/generate.py           # Tree aus den frischen Quellen neu schreiben
python3 _src/generate.py --check   # muss „Abweichungen: 0“ melden
```

## Qualitätssicherung

`validate.py` prüft: Tree aktuell (byte-genau gegen Quellen), alle internen
Links und Anker gültig, keine Platzhalter `href="#"`, keine fehlenden oder
verwaisten Fragmente/SVGs. Exit-Code 0 = grün.

Bei Layoutänderungen zusätzlich Stichproben-Screenshots (Startseite, eine
Klassen-, eine Namespace-, eine Modulseite) auf Textumbruch/Überlauf prüfen —
Konventionen dazu in `KONVENTIONEN.md`.


## Kanonische RS-Upstream-Metadaten

Die RS-Quellen stehen getrennt vom bestehenden SWS-Dokumentregister in
`RS_DOCS` in `_src/tools/spec_scrape.py`. Die zwei in R25-11 referenzierten, aber in den kanonischen Dokumenten nicht definierten IDs `RS_AP_00154` und `RS_DIAG_04005` bleiben als `expected-unresolved` diagnostisch sichtbar; fuer sie werden keine Quellenmetadaten erfunden. Fuer R25-11 sind derzeit die offiziell
verifizierten AP-Dokumente Communication Management, Vehicle Update and
Configuration Management und HWTestManager registriert.

`spec_scrape.py upstream` vergleicht standardmaessig nur und schreibt keine
Dateien. Erst `--rebuild` aktualisiert bestehende Requirement-Records atomar;
dabei darf ausschliesslich das Feld `upstream` geaendert werden. Fehlende oder
mehrdeutige RS-IDs werden explizit berichtet und fuehren zu einem von null
verschiedenen Exit-Status. `--write-reqs` bleibt davon getrennt und schreibt nur
neue Prosa-Requirement-Records additiv.
