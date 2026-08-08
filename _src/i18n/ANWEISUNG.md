# Übersetzungsanweisung — ara::* API-Referenz (AUTOSAR Adaptive Platform R25-11)

Du übersetzt deutsche Segmente einer technischen API-Dokumentation
(AUTOSAR Adaptive Platform, C++-Schnittstellen) in eine Zielsprache.

## Ein-/Ausgabeformat

Eingabe: JSONL-Datei, eine Zeile je Segment: `{"id": "…", "de": "…"}`
Ausgabe: JSONL-Datei gleicher Länge, eine Zeile je Segment: `{"id": "…", "t": "…"}`
- `id` unverändert übernehmen (auch die mit Präfix `L:`).
- Reihenfolge beibehalten. Keine Zeile auslassen, keine hinzufügen.
- Gültiges JSON je Zeile, `ensure_ascii` nicht nötig (UTF-8 erlaubt).

## Harte Invarianten (werden maschinell geprüft; Verstoß = Zeile wird verworfen)

1. Platzhalter `⟦0⟧ ⟦1⟧ …` exakt erhalten: gleiche Ziffern, gleiche Anzahl.
   Position im Satz darf (und soll) der Zielgrammatik folgen.
   Platzhalter stehen für geschützte Inhalte (Links, `code`, Bilder) — nie
   erfinden, nie weglassen, Ziffern nie ändern.
2. Kennungen wie `[SWS_CM_00701]`, `AUTOSAR_AP_SWS_…`, `EXP_…`, `FO_…`
   unverändert lassen.
3. HTML-Tags `<em>…</em>`, `<strong>…</strong>` u. ä. bleiben als Markup
   erhalten (gleiche Anzahl); den Text darin übersetzen.

## Was NICHT übersetzt wird (wörtlich stehen lassen)

- Namen von Spezifikationselementen und Bezeichner: Klassen-, Methoden-,
  Namespace-, Typ-, Parameternamen (`ara::core::Future`, `GetNewSamples`,
  `maxNumberOfSamples`, `kNetworkDown` …).
- Englische Originalzitate aus der Referenzdokumentation, falls sie in einem
  Segment eingebettet sind (z. B. Klammerzitate wie
  "(Maximum number of received data samples …)"): wörtlich erhalten.
- Etablierte AUTOSAR-Fachbegriffe: Adaptive Platform, Functional Cluster,
  Service Discovery, Manifest, Deployment, Update and Configuration
  Management, Platform Health Management usw. — in lateinischer Schrift
  belassen, sofern die Zielsprache keine fest etablierte Übersetzung hat.
- Dokumenttitel der AUTOSAR-Spezifikationen (z. B. "Specification of
  Communication Management") bleiben englisch.

## Stil

- Fachregister, präzise, konsistent; formelle Anrede vermeiden (Doku-Stil,
  keine direkte Leseransprache außer wo die Quelle es tut).
- Deutsche Komposita sauber auflösen; keine wörtlichen Kalques.
- Typografie der Zielsprache verwenden (Anführungszeichen, Spatien bei
  französischen Doppelzeichen, arabische/chinesische Interpunktion), aber:
  in Platzhaltern/Kennungen nichts verändern.
- Labels (`id` beginnt mit `L:`) sind kurze Diagramm-/Tabellenbeschriftungen:
  knapp übersetzen, Zeilenumbruch-Escapes `\n` an sinnvoller Stelle erhalten
  (gleiche Anzahl Teilzeilen, ähnliche Zeilenlängen — die Beschriftung muss
  in eine Diagrammbox passen). Pfeile `→`, Punkte `·` und Trennzeichen
  erhalten.
- RTL-Sprachen (Arabisch): normale arabische Prosa; lateinische Bezeichner
  bleiben lateinisch, keine Richtungszeichen einfügen.

## Kontext

Die Segmente stammen aus KI-generierten Erläuterungen (User Guides,
Verwendungshinweise, Interpretationen) einer API-Referenz zu AUTOSAR R25-11.
"**Interpretation:**"-Präfixe (als <strong>Interpretation:</strong> im Markup
oder als Platzhalter) leiten vorsichtige Deutungen ein; entsprechend
vorsichtige Modalität in der Zielsprache wählen. Wörter wie "Annahme",
"vermutlich" markieren Unsicherheit — Ton erhalten.
