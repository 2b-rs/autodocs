# Wartungsanleitung — ara::* API-Referenz (R25-11)

Der HTML-Tree (`index.html`, `classes/`, `namespaces/`, `modules/`, `services/`)
ist ein **Build-Artefakt**. Maßgebliche Quellen liegen unter `_src/`. Inhalte
werden **nicht** im generierten HTML geändert, sondern in den Quellen — danach
wird der Tree neu generiert. Das gilt auch für die neun übersetzten Sprachbäume
(`en/`, `es/`, `pt/`, `fr/`, `ru/`, `ar/`, `hi/`, `ko/`, `zh/` — s. Kapitel
„Mehrsprachige Bäume (i18n)“).

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
AUTOSAR-Standard-PDFs** validiert. Diese PDFs liegen versionsweise im Cache:

```
_src/spec/pdf-cache/R25-11/
├── AUTOSAR_AP_SWS_Core.pdf
├── AUTOSAR_AP_SWS_LogAndTrace.pdf
├── …
└── manifest.sha256          ← Inhaltsverzeichnis (SHA-256 je PDF)
```

- **Dateinamen sind nicht frei waehlbar.** Sie entsprechen exakt den auf der
  Startseite verlinkten Standarddokumenten (`_src/sources/pages/index.json`,
  Abschnitt „Quellen“). Das Dokumentregister `DOCS` in
  `_src/tools/spec_scrape.py` haelt Modul, Zweig, PDF-Basisnamen und
  Record-Praefix zusammen; es muss mit dieser Liste deckungsgleich bleiben.
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
