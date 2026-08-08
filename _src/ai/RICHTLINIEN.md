# Richtlinien für KI-generierte Erklärungen

Diese Datei ist Teil des Kuratierungsprozesses: Sie enthält die inhaltlichen
Leitplanken für alle KI-generierten Texte und Diagramme. Die maschinenlesbaren
Parameter dazu stehen in `ai/policy.json`; beide werden von
`ai_workflow.py auftrag` wörtlich in jeden Regenerierungsauftrag eingebettet.
Änderungen an Policy oder Richtlinien ⇒ `version` in `policy.json` erhöhen;
`ai_workflow.py status` zeigt dann, welche Fragmente noch mit einer älteren
Version erzeugt wurden.

## Geltungsbereich und Sprache

- Kanonische Sprache ist Deutsch (`site.json → sprachen.kanonisch`). KI-Inhalte
  werden ausschließlich deutsch erzeugt; die Übersetzung ist ein nachgelagerter
  Schritt (i18n_*.py) und niemals Teil der Generierung.
- API-Bezeichner, Typnamen, Enum-Werte, Code und `[SWS_…]`-Kennungen bleiben
  in jeder Sprache unverändert.

## Strukturelle Invarianten

- Jedes Fragment ist genau ein `<div class="ai …">` (Varianten: `ai` für
  Abschnitte, `ai usage` für Verwendungshinweise an Records, `ai module-guide`
  für Modul-Leitfäden) mit Badge und abschließender `<p class="ai-note">`
  (KI-Hinweis). Bestehende Fragmente sind die Referenz.
- Fragmente liegen unter `content/ai/<seiten-verzeichnis>/` und heißen
  `rec_<ELEMENT-ID>_<NN>.html` (an ein Spezifikationselement gebunden) oder
  `main_<NN>.html` (seitenbezogen).

## Belegpflicht und Quellen

- Jede fachliche Aussage ist mit `[SWS_…]`/`[RS_…]`-Zitat zu belegen
  (`policy.zitierpflicht`); Zitate verlinken auf das Quelldokument (PDF mit
  `#nameddest`), Richtwert `policy.relevanz.min_zitate_je_absatz`.
- Es dürfen nur Dokumente aus dem Quellenregister `ai/quellen.json` verwendet
  werden. Neue Quellen werden zuerst dort registriert (id, titel, typ, url).
- Aus Quellen extrahierte Einzelaussagen, auf die sich ein Text stützt, werden
  in der Trace unter `wissen[]` festgehalten: `{"aussage": …, "quelle": <id>,
  "fundstelle": …}`.

## Annahmen (Wissenslücken)

- Wo die Spezifikation schweigt, darf die KI Lücken mit Annahmen schließen —
  höchstens `policy.annahmen.budget_je_text` pro Text bzw.
  `budget_je_diagramm` pro Diagramm.
- Jede Annahme wird (a) im Text als Interpretation erkennbar formuliert und
  (b) in der Trace unter `annahmen[]` protokolliert:
  `{"annahme": …, "begruendung": …}`.
- Reicht das Budget nicht, wird der Aspekt weggelassen — niemals unmarkiert
  spekuliert.

## Diagramm-Entscheidung

Ein Diagramm wird nur eingefügt, wenn es gegenüber dem Text Mehrwert bietet
(`policy.diagramme`):

- Sequenzdiagramm (`.seq.json`): Abläufe mit ≥ `sequenz_ab_schritten`
  Schritten oder nicht offensichtlicher Reihenfolge/Asynchronität.
- Kontext-/Strukturdiagramm (`.dot`): ≥ `kontext_ab_beteiligten` beteiligte
  Komponenten oder nicht-triviale Vererbungs-/Abhängigkeitscluster.
- Zustandsdiagramm (`.dot`): Lebenszyklen und Zustandsmaschinen.
- Keine Trivialdiagramme (einzelne Aufrufe, Getter/Setter, Zweierbeziehungen).

Die Entscheidung („warum dieses Diagramm, warum diese Form“), etwaige
Annahmen und das Denk-Transkript zur Quellenerstellung gehören in die Trace
unter `diagramme["<quellpfad>"]` — nicht ins HTML. Diagrammquellen liegen als
`<fragment-stem>.<diag-id>.dot|.seq.json` neben dem Fragment (inline) bzw.
unter `diagrams/` (seitenweite Diagramme); gerendert wird mit
`render_diagrams.py`. Beschriftungen deutsch, Bezeichner unverändert.

## Trace-Dateien

Jedes Fragment hat eine Trace unter `ai/traces/<pfad>/<stem>.json` — die
vollständige Herkunftsakte:

| Feld | Inhalt |
|---|---|
| `fragment`, `seite`, `art` | Artefakt, zugehörige Seite, Gattung (usage/guide/abschnitt) |
| `elemente` | assoziierte Spezifikationselemente (IDs in `spec/records/`) |
| `zitate` | alle im Text zitierten Kennungen |
| `quellen` | verwendete Dokumente (ids aus `quellen.json`) |
| `wissen` | extrahierte Einzelaussagen mit Fundstelle |
| `annahmen` | eingeführte Annahmen mit Begründung |
| `prompt` | der Auftragstext, aus dem das Fragment erzeugt wurde |
| `modell`, `policy_version` | Erzeugungsparameter |
| `laeufe` | Historie: `{datum, modell, policy_version, transkript}` je Lauf |
| `diagramme` | je Diagrammquelle: Entscheidung, Annahmen, Transkript |
| `status` | `legacy` (vor Einführung der Traces), `aktuell`, `veraltet` |
| `elemente_stand` | SHA1 der Record-Dateien zum Erzeugungszeitpunkt (Veraltet-Erkennung) |

Der Altbestand (August 2026) trägt `status: "legacy"`: Elemente, Zitate,
Quellen und Diagrammquellen wurden automatisch rekonstruiert; Prompt, Modell,
Wissen, Annahmen und Transkripte der ursprünglichen Generierung sind nicht
mehr rekonstruierbar und bleiben bewusst leer statt erfunden. Sie füllen sich
bei der ersten Regenerierung.

## Regenerierung

Neues Wissen, geänderte Records, neue Quellen oder Policy-Änderungen ⇒

1. `ai_workflow.py status` — zeigt veraltete/legacy Fragmente
   (Record-Hash-Abgleich, Policy-Versionen, fehlende Traces).
2. `ai_workflow.py invalidiere --quelle=<id> | --element=<ID> | <fragment>` —
   markiert Betroffene gezielt als `veraltet`.
3. `ai_workflow.py auftrag <fragment|seite.html|ELEMENT-ID>` — erzeugt
   in `ai/work/` einen in sich vollständigen Auftrag (Policy + diese
   Richtlinien + aufgelöste Records + bisheriges Fragment + Trace).
4. Auftrag von einem Modell bearbeiten lassen; Ergebnis als
   `…auftrag_NN.out.json` daneben legen.
5. `ai_workflow.py merge` — prüft (Struktur, ai-note, Platzhalter,
   Annahmen-Budget), schreibt Fragment + Diagrammquellen, aktualisiert die
   Trace. Danach wie immer: `render_diagrams.py` (falls Diagramme),
   `generate.py`, `validate.py`, `i18n_extract.py` → Übersetzungsrunde.
