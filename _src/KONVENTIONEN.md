# Konventionen — ara::* API-Referenz (R25-11)

Verbindliche inhaltliche und gestalterische Regeln. Bei Änderungen und neuen
Inhalten einhalten; Abweichungen zuerst hier dokumentieren. Für das ERZEUGEN
und Regenerieren von KI-Inhalten (Leitplanken, Annahmen-Budgets,
Diagramm-Entscheidung, Herkunftsakten) gilt zusätzlich `ai/RICHTLINIEN.md`
mit den Parametern aus `ai/policy.json`.

## Grundsätze

- Quelle der Wahrheit sind die offiziellen AUTOSAR-R25-11-PDFs (SWS/RS/EXP/TR).
  Die Referenz ist **keine offizielle AUTOSAR-Publikation** — das sagt der Footer
  auf jeder Seite.
- UI-Sprache des Hauptbaums Deutsch; Original-Beschreibungstexte der
  Spezifikation bleiben Englisch — in allen Sprachbäumen.
- Neun generierte Sprachbäume (en, es, pt, fr, ru, ar, hi, ko, zh); Regeln
  s. Abschnitt „Mehrsprachigkeit (i18n)“.
- Jede fachliche Aussage in KI-Texten ist belegt: mit `[SWS_…]`/`[RS_…]`-Verweis
  oder Kapitel-Link ins PDF.

## Dateinamen und Seitentypen

- `classes/cl_<pfad>_<hash>.html`, `namespaces/ns_<modul>_<pfad>_<hash>.html`,
  `modules/<modul>.html`, `services/sv_<modul>_<name>_<hash>.html`.
  Hash-Suffixe niemals ändern (stabile Linkziele).
- Seitenaufbau: Kopfzeile → Breadcrumb-Navigation mit Interface-Badge →
  `<main>` mit H1 (`span.kind`-Chip + Name), Meta-Zeile (SWS-ID + Upstream),
  Syntax, Beschreibung, Eigenschaften, UML-Diagramm, KI-Guide, Übersichten,
  Record-Dokumentation → Footer. **Kein Inhalt außerhalb von `<main>`.**

## Interface-Sichtbarkeit (Farbsystem)

Kategorie eines Elements = Hintergrund-/Textfarbe seines Namens:

| Kategorie | Bedeutung | Farbe | CSS |
|---|---|---|---|
| APPLICATION | von Adaptive Applications nutzbar | Blau `rgb(25,92,189)` | `vis-app` |
| PRIVILEGED | nur autorisierte Anwendungen | Rot `rgb(198,40,40)` | `vis-priv` |
| INTERNAL | nur andere Functional Cluster / Plattform-Integration | Dunkelgrau `rgb(55,65,76)` | `vis-internal` |

- Zentral änderbar über `--vis-*-rgb`, Blassheit über `--vis-bg-alpha` (0.09)
  und `--vis-bg-alpha-hover` (0.24) in `style.css`.
- Navigationszeile: Badge in Pillenform (`span.vis-tag vis-…`) mit Suffix
  **INTERFACE**, z. B. `PRIVILEGED INTERFACE (Users: SM-Control-Application, …;
  Except INTERNAL UpdateRequest, …)`. Genannte Nutzer stets mit Präfix `Users:`;
  Ausnahmen als `Except`-Klausel in Klammern.
- Gemischte Aggregate (Namespace-/Modulseiten) tragen die Mehrheitsfarbe
  (`body class="vis-…"`).
- Startseiten-Modulkarten: `mini-badge` je enthaltenem Interface-Typ; gemischte
  Module zusätzlich `vis-mixed` = Mehrheitsfarbe mit Neutralgrau gemischt
  (45 % Farbanteil, `color-mix` in `style.css`).
- In SVG-Diagrammen färbt CSS verlinkte Knoten über `svg a.vis-… rect|polygon|…`;
  der Knoten des Seiten-Elements selbst bekommt `g.node.vis-…`. Externe,
  nicht klassifizierte Knoten: `dbox ext`-Grau.

## KI-Kennzeichnung

- Jeder KI-generierte Block ist ein `div.ai` mit lila Badge
  (`span.ai-badge`, #7A39BB): „KI-generiert / AI generated“ und beginnt mit
  einer `p.ai-note` (Pflichttext: automatisch generiert, abgeleitet aus den
  referenzierten R25-11-Spezifikationselementen, kein offizieller AUTOSAR-Text).
- Varianten: seitenweiter Guide (`div.ai module-guide` bzw. Klassen-Guide) und
  kompakter Nutzungshinweis am Record (`div.ai usage`).
- KI-Guide-Abschnitte (Überschrift `h2.sect` mit Badge) sind klappbar
  (Blocktyp `fold`, `<details class="fold">`) und initial eingeklappt;
  Deep Links auf Anker im Abschnitt öffnen ihn automatisch (`fold.js`).
  Neue KI-Guide-Abschnitte ebenfalls als `fold`-Block anlegen.
- **Interpretationen** (Schlussfolgerungen ohne direkte Spezifikationsaussage):
  `p.interp` (gelbe Markierung, #b58900), Text beginnt mit „**Interpretation:**“.
- **Annahmen** (fehlende Information in den Standarddokumenten): im Text mit
  „Annahme:“ markieren; in Diagrammen ockerfarbene, gestrichelte Elemente plus
  automatische Legende. Nur verwenden, wenn unvermeidbar.
- Redundanzverbot: KI-Erläuterungen, die nur Description/Scope/Exception-/
  Thread-Sicherheit nacherzählen, werden entfernt.
- **Keine Dopplung zwischen Guides**: Jede Erklärung und jedes Diagramm lebt
  auf genau einer Seite; andere Seiten verweisen. Kanonische Orte: Diagramme
  im Modul-Guide (dort mit stabiler Anker-ID `id="diag-…"` am
  `div.diagram`/`div.umlwrap`), geteilte Erklärtexte beim übergeordneten
  Namespace (Abschnittsanker `id="guide-…"` am `h4`). Verweistext nach
  Link-Konvention: Zielseite + Abschnitt/Diagrammtitel, z. B.
  `ara::crypto § „Providerzugänge“` oder `ara::com — Communication Management,
  Zustandsdiagramm „Verarbeitungsmodi des Skeleton“`. Gleichlautende generische
  Formulierungen über nicht verwandte Namespaces hinweg werden nicht verlinkt,
  sondern je Namespace fachlich spezialisiert.
- Elemente mit Spezifikationstext „As per corresponding usage in […]“ erhalten
  eine „Technische Einordnung“: std-Gegenstück (cppreference-Link), Abweichungen
  (insb. Violations statt Exceptions), DRAFT-Status, Besonderheiten.

## Link-Konventionen

- **Requirements**: Linktext ist die ID in Klammern, z. B. `[SWS_EM_02283]`
  (`a.swsref`, monospace). Ziel: Anker `#SWS_…` wenn der Record auf derselben
  Seite dokumentiert ist, sonst PDF-Deep-Link
  `…/AUTOSAR_AP_SWS_X.pdf#nameddest=SWS_…` mit `title="Spezifikations-PDF (…)"`.
- **Informelle Dokumente** (EXP/TR): Linktext muss ohne Klick verständlich sein —
  Kurzname + Kapitel + Überschrift, z. B.
  `EXP ARAComAPI §5.3.4 „Finding Services“` (`a.docref`);
  Seitenziele mit `(S. N)`. Nie bloße Nummern wie „paragraph.9.8.1.1.1“.
- **Literaturverweise in Zitaten** (z. B. „[11]“): im Zitat als `a.bibref` auf
  die externe Quelle verlinken (voller Titel als `title`), direkt unter dem
  Zitat Fußnote `p.fnote` „Literaturverzeichnis SWS X: [11] …“ mit übernommenen
  Links.
- Keine Platzhalter `href="#"`. Selbstverweise auf das Seiten-Element zeigen
  auf dessen PDF-Deep-Link.
- Interne Links immer relativ; Hash-Dateinamen nicht umbenennen.

## Diagramme

- Quellen sind kanonisch, SVGs sind generiert: Graphviz-Diagramme aus `.dot`,
  Sequenzdiagramme aus `.seq.json` (Generator `_src/seqgen.py`). Änderungen
  immer an der Quelle vornehmen und mit `_src/render_diagrams.py` neu rendern
  — nie am SVG (Details: WARTUNG.md, „Diagramme: Quellen und Rendern“).
- Stil: Graphviz-Optik der Bestandsdiagramme (Hintergrund `#f9f8f5`,
  Text `#28251d`, Helvetica 12pt, Akzent `#01696f`); Sequenzdiagramme über den
  projekteigenen Generator-Stil (Raster und Farben fest in `seqgen.py`).
- UML-Klassendiagramme in `div.umlwrap` (mit Hinweiszeile `p.dim` zur
  Pfeilsemantik), sonstige Abläufe in `div.diagram` mit `p.diagram-note`.
- Knoten verlinken auf die jeweilige Element-Seite; Namespace-/Farbzuordnung
  gemäß Interface-Typ. Keine abgeschnittenen Namen — lange Bezeichner
  komprimiert setzen (`font-stretch`/kleinere Schrift), nie kürzen.
- Annahme-basierte Diagrammteile: ocker + gestrichelt + Legende (s. o.).

## Mehrsprachigkeit (i18n)

- **Übersetzt wird nur selbst erzeugter Inhalt.** Sämtliche Originalzitate aus
  der Referenzdokumentation (Auszüge, eingebettete englische Zitate,
  Spezifikations-Beschreibungstexte) und Linktexte auf externe Quellen bleiben
  wörtlich erhalten. Diagramminhalte werden übersetzt, aber Namen von
  Spezifikationselementen (Klassen, Methoden, Namespaces, Parameter — auch in
  Knoten wie `Subscribe()` oder `Serializable`) bleiben unverändert.
- **docref-Verweise**: die Verpackung („§“/„Kapitel“/„Anhang“, Seitenangabe)
  wird je Sprache lokalisiert; zitierte Kapiteltitel und Dokumentnamen bleiben
  wörtlich englisch. Der deutsche Baum verwendet „…“-Anführungszeichen,
  die Sprachbäume ihre eigene Typografie (en/hi/ko/zh “…”, es/pt/ru/ar «…»,
  fr « … » mit schmalem geschütztem Leerzeichen).
- **Bewusst englisch in allen Sprachen**: `kind`-Chips (CLASS, FUNCTION …),
  Interface-Badges (`APPLICATION INTERFACE` …), der `title`-Zusatz
  „AI generated“, `vis-*`-Badge-Spans sowie die gedämpften
  „As per corresponding usage …“-Spans der Spezifikation.
- Das KI-Badge trägt je Sprache die Doppelform „Übersetzung / AI generated“
  (z. B. „GÉNÉRÉ PAR IA / AI GENERATED“); das „Interpretation:“-Präfix wird
  übersetzt (en Interpretation: / es Interpretación: / pt Interpretação: /
  fr Interprétation : / ru Интерпретация: / ar تفسير: / hi व्याख्या: /
  ko 해석: / zh 解释：).
- Flaggen-Umschalter oben rechts (RTL oben links) auf jeder Seite; Arabisch
  ist RTL (`dir="rtl"`), lateinische Bezeichner bleiben darin lateinisch.
- Workflow, Register und QA-Scans: WARTUNG.md, Kapitel „Mehrsprachige Bäume
  (i18n)“; Übersetzungsregeln im Detail: `_src/i18n/ANWEISUNG.md`.

## Fehlerpfad-Dokumentation

Module und zentrale Klassen dokumentieren im KI-Guide einen Abschnitt
„Verhalten im Fehlerfall“: Grenzfälle, Timeouts, Fehlertransport, Zustände —
belegt mit SWS-Requirements, wo sinnvoll mit Zustands-/Sequenzdiagramm.

## Qualität (vor jeder Abgabe)

- `python3 _src/validate.py` grün.
- Screenshot-Stichproben ohne Textüberlauf, falsche Umbrüche mitten im Wort
  oder Kontrastprobleme (dunkler Text auf dunklem Grund).
- Keine PDF-Extraktionsartefakte: Silbentrennungs-Leerzeichen in Bezeichnern
  („StartFind Service“), abgeschnittene Namen („variant_size< const“).
