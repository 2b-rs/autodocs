# Architektur der Generierungspipeline

Zielbild: Der komplette HTML-Baum (und jeder Teil davon) ist jederzeit allein
aus Klartext-Quellen reproduzierbar — Spezifikations-Datenbank, KI-Erklärungen
als Klartextfragmente mit Herkunftsakten, Diagrammquellen und i18n-fähige
Templates. Handgriffe im generierten HTML sind die dokumentierte Ausnahme
(WARTUNG.md, „Direkteingriff“). Tagesgeschäft: WARTUNG.md; inhaltliche Regeln:
KONVENTIONEN.md; KI-Leitplanken: ai/RICHTLINIEN.md.

## Schichtenmodell

Fünf Schichten, jede mit eigener Klartext-Quelle und eigenem Änderungszyklus.
Abhängigkeiten zeigen nur nach unten:

```
┌────────────────────────────────────────────────────────────────────┐
│ 5  HTML-Bäume        de (kanonisch) + Sprachbäume       GENERIERT  │
├────────────────────────────────────────────────────────────────────┤
│ 4  i18n              i18n/: Register (sid→Text), Labels, ui.json,  │
│                      übersetzte Diagramm-SVGs — NACHGELAGERT:      │
│                      übersetzt wird das Kompositionsergebnis       │
├────────────────────────────────────────────────────────────────────┤
│ 3  Komposition       sources/pages/*.json (Blockfolge je Seite),   │
│                      templates/ (Chrome, i18n-fähig), site.json    │
│                      (Manifest: Titel, Bereiche, Sprachen)         │
├────────────────────────────────────────────────────────────────────┤
│ 2  KI-Kuratierung    content/ai/ (Fragmente, deutsch, HTML) +      │
│                      Inline-Diagrammquellen; ai/: policy.json,     │
│                      RICHTLINIEN.md, quellen.json, traces/**       │
│                      (Herkunftsakten), work/ (Aufträge)            │
├────────────────────────────────────────────────────────────────────┤
│ 1  Spezifikations-DB spec/records/<GRUPPE>/<ID>.json — ein         │
│                      Element je Datei, über die ID adressierbar   │
└────────────────────────────────────────────────────────────────────┘
```

Werkzeuge je Schicht: (1)+(3) `generate.py`/`extract.py`/`validate.py`,
(2) `ai_workflow.py` + `render_diagrams.py`, (4) `i18n_*.py`,
Querschnitt `build_indexes.py` (Lesesichten), `tools/` (QA-Scans).

Warum KI-Texte als HTML-Fragmente in der „Datenbank“ liegen (und nicht als
Markdown o. ä.): Die i18n-Segment-IDs sind Hashes des maskierten innerHTML.
Jede Formatkonversion würde das komplette Übersetzungsregister (≈ 34 000
akzeptierte Segmente über 9 Sprachen) invalidieren. Die Fragmente SIND die
Klartext-Repräsentation der KI-Erklärungen; ihre Herkunft (Prompt, Wissen,
Annahmen, Transkripte) liegt daneben in `ai/traces/`.

## Invarianten

1. **Reproduzierbarkeit**: `generate.py` ist idempotent und byte-stabil;
   `generate.py --check` gegen einen frischen Checkout meldet 0 Abweichungen.
2. **Ein Fakt, ein Ort**: Spezifikationselemente nur in `spec/records/`,
   KI-Prosa nur in `content/ai/`, Übersetzungen nur in `i18n/`, Chrome nur in
   `templates/`, Projektstammdaten nur in `site.json`.
3. **Deutsch ist kanonisch** (`site.json → sprachen.kanonisch`); i18n ist
   nachgelagert und inkrementell (nur neue/geänderte Segmente werden fällig).
4. **KI-Inhalte tragen Herkunft**: kein Fragment ohne Trace
   (`ai_workflow.py status` prüft das).
5. **Generierte Artefakte sind wegwerfbar**: HTML-Bäume, `data/*.csv`,
   gerenderte SVGs, `i18n/<lg>/diagrams|inline` lassen sich jederzeit aus den
   Schichten darunter neu erzeugen.

## Erweiterungsrezepte

### Neues Spezifikationselement / neue Seite

Record-Datei unter `spec/records/` anlegen, `rec-ref` in das Seiten-JSON
setzen (bzw. JSON einer ähnlichen Seite kopieren und anpassen), generate →
validate → i18n. Details: WARTUNG.md.

### Neues Modul / ganzer Funktionscluster (z. B. Timing Extensions, Service-Schnittstellen, kundenspezifische Komponenten)

Rein additiv, keine Pipeline-Änderung:

1. Records des Clusters als neue Gruppe(n) unter `spec/records/` ablegen
   (Gruppierung ergibt sich aus den IDs, z. B. `SWS_TEX/…`).
2. Seiten-JSONs unter `sources/pages/<bereich>/…` anlegen; Modulseite unter
   `modules/`, Querverweise in Namespace-/Indexseiten ergänzen.
3. KI-Erklärungen über den Kuratierungszyklus erzeugen
   (`ai_workflow.py auftrag` — neue Quelldokumente vorher in
   `ai/quellen.json` registrieren).
4. generate → validate → i18n-Runde für die neuen Segmente.

Braucht der Cluster eine eigene Rubrik (eigenes Unterverzeichnis neben
`classes/`, `modules/`, …): einen Eintrag in `site.json → bereiche`
ergänzen — extract, build_indexes und die Loader lesen die Bereichsliste von
dort. Keine Skriptänderung nötig.

### Neues Projekt (z. B. AUTOSAR Classic, ADTF, Eclipse S-Core)

Die Pipeline ist projektneutral: Alle Skripte arbeiten pfad-relativ und
beziehen Projektstammdaten aus `site.json`. Rezept:

1. Neues Repo/Verzeichnis, `_src/`-Gerüst kopieren: die `*.py`-Skripte,
   `tools/`, leere `spec/`, `sources/`, `content/ai/`, `ai/` (policy.json und
   RICHTLINIEN.md als Ausgangspunkt übernehmen und anpassen), `i18n/` mit
   leeren Registern (`ui.json` und `ANWEISUNG.md` anpassen).
2. `site.json` schreiben: Titel, Beschreibung, `bereiche` (Rubriken des neuen
   Projekts), Sprachen.
3. `templates/page.html.tmpl` + `footers.json` fürs neue Projekt gestalten
   (das Chrome ist bewusst NICHT in den Skripten verdrahtet), `style.css`/
   `fold.js` übernehmen oder ersetzen.
4. Quellen befüllen: Records + Seiten-JSONs (bei Bestands-HTML kann
   `extract.py` als Vorlage für einen Importer dienen), dann KI-Kuratierung
   und i18n wie hier.

### Layout-/Strukturänderungen

- Seiten-Chrome (head/header/nav/footer): nur `templates/` anfassen.
- Schachtelungsstruktur der Spezifikationselemente auf den Seiten: Blockbaum
  im Seiten-JSON (`fold`/`rec-ref`-Anordnung) — die Records selbst bleiben
  unberührt.
- Neue Blocktypen: in `lib_docmodel.py` (render + extract + Felddoku im
  Docstring) ergänzen; `i18n_extract.py`/`validate.py`/`build_indexes.py`
  erweitern, falls der Typ übersetzbaren Text, Links oder Referenzen trägt.
  Danach: Roundtrip-Nachweis (`extract.py` + `generate.py --check`).
