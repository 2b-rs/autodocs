# Prozess: Aufbau und Pflege der Spezifikations-Datenbank

Dieser Prozess beschreibt, wie die Records unter `spec/records/` nach einer
Werkzeugverbesserung neu aufgebaut, bewertet, entschieden und um Evidenz aus
informellen Dokumenten angereichert werden. Er setzt die Anforderungen aus
`SPEC_TRACEABILITY.md` operativ um und respektiert die Invarianten aus
`ARCHITEKTUR.md` (ein Fakt, ein Ort; generierte Artefakte sind wegwerfbar).

Grundhaltung: **Extraktion schlaegt Darstellung, Evidenz schlaegt Meinung,
Entscheidung schlaegt Stillschweigen.** Kein Wert wird still korrigiert, kein
Zweifel wird still aufgeloest.

## Rollen

- **Werkzeug** — `spec_scrape.py` und Backends (`pypdf`, `builtin`, optional `mupdf`).
- **Kurator** — Mensch, entscheidet Freigaben und Grenzfaelle.
- **KI-Entscheider** — schlaegt Werte fuer strittige Faelle vor, mit Rationale.
- **KI-Extraktor** — liest informelle Dokumente und liefert Evidenz je Record.
- **Validator** — prueft Statusfelder, Traceability und Konsistenz.

## Statusmodell

Jeder Record traegt genau einen `status.state` und einen `status.reason`.

| state | Bedeutung | Darf generiert werden |
|---|---|---|
| `invalid/obsolete` | vor dem Import entwertet, noch nicht neu bewertet | nein |
| `valid/auto-approved` | beide Backends und DB identisch | ja |
| `valid/corrected` | beide Backends einig, DB wich ab, DB korrigiert | ja |
| `invalid/to-be-confirmed` | Backends uneinig, Entscheidung offen | nein |
| `valid/ai-decided` | strittiger Fall durch KI entschieden, Rationale vorhanden | ja |
| `valid/curator-decided` | strittiger Fall durch Kurator entschieden | ja |
| `invalid/hypothesized` | neu vorgeschlagenes Element aus informeller Evidenz | nein |

Regeln:

1. Nur `valid/*` fliesst in Seiten, Indizes und Diagramme.
2. Jeder Statuswechsel erzeugt einen Eintrag in `history[]`.
3. Jeder `valid/*`-Wert braucht Traceability nach `SPEC_TRACEABILITY.md`.
4. `hypothesized/unconfirmed` ist sichtbar in Reports, nie in der Publikation.

## Phase 0 — Kampagne eroeffnen

Jeder Neuaufbau ist eine benannte **Kampagne** mit eigener ID, damit History
und Reports zuordenbar bleiben.

```
campaign: 2026-08-spec-update-after-tool-improvement
trigger:  spec update after tool improvement
release:  R25-11
scope:    alle Records unter spec/records/
```

Schritte:

1. Kampagnen-Manifest anlegen (`spec/campaigns/<id>.json`): Ausloeser, Release,
   Werkzeugstand (Git-Commit von `spec_scrape.py`), Backend-Liste,
   PDF-Cache-Hash aus `manifest.sha256`.
2. Alle Records auf `invalid/obsolete` setzen, Reason
   `"spec update after tool improvement"`.
3. Den alten Wert je verglichenem Feld als `legacy` sichern — er ist die dritte
   Stimme im spaeteren Vergleich und stammt aus dem re-engineerten HTML.
4. Commit: `spec: open campaign <id>, invalidate all records`.

Wichtig: Entwertung loescht nichts. Werte bleiben erhalten, nur ihre
Geltung ist ausgesetzt.

## Phase 1 — Extraktion

`spec_scrape.py crosscheck` mit mindestens zwei Backends gegen den
versionierten PDF-Cache. Ergebnis ist der Kampagnen-Input; er wird unveraendert
archiviert (`output/spec-validation/<release>/crosscheck-<campaign>.json`).

Kein Schreibzugriff auf die DB in dieser Phase.

## Phase 2 — Triage je Feld

Verglichen werden die Felder aus `COMPARED` (Kind, Header file, Scope, Symbol,
Underlying type) sowie die abgeleitete Namespace-Sicht.

Drei Stimmen je Feld: `backend_a`, `backend_b`, `legacy`.

| Konstellation | Ergebnis | Reason |
|---|---|---|
| A = B = legacy | `valid/auto-approved` | `unchanged` |
| A = B != legacy | `valid/corrected` | `database error, detected after new import` |
| A != B | `invalid/to-be-confirmed` | `uncertain scraping result` |

Zusatzregeln:

- Fehlt eine Backend-Stimme (leere Extraktion), zaehlt das als Uneinigkeit,
  nicht als Zustimmung.
- Bekannte Modellierungsabsichten sind **keine** Abweichung. Beispiel:
  `std`-Spezialisierungen tragen `ns.abweichung = "std-spezialisierung"`;
  Namespace `std` gegen Typ `std::hash` ist ein Vergleichsfehler, kein DB-Fehler.
  Solche Faelle werden vor der Triage per Normalisierungsregel neutralisiert.
- Triage ist feldweise, nicht recordweise. Ein Record kann korrigierte und
  strittige Felder gleichzeitig haben; der Record-Status ist das Minimum der
  Feldstatus (strittig schlaegt korrigiert schlaegt unveraendert).

In jedem Fall werden alle drei Stimmen im Record persistiert:

```json
"fields": {
  "Scope": {
    "value": "class ara::crypto::x509::Certificate",
    "state": "valid/corrected",
    "reason": "database error, detected after new import",
    "votes": {
      "pypdf":   "class ara::crypto::x509::Certificate",
      "builtin": "class ara::crypto::x509::Certificate",
      "legacy":  "class ara::crypto::x"
    },
    "trace": [ { "mode": "direct_id", "sources": [ ... ] } ]
  }
}
```

Commit: `spec: triage campaign <id> (auto-approved N, corrected M, disputed K)`.

## Phase 3 — KI-Entscheidung strittiger Felder

Nur Felder mit `invalid/to-be-confirmed` gehen in diese Phase.

Vorlage je Fall (maschinenlesbar, ein Fall pro Objekt):

```
id, field, votes{backend_a, backend_b, legacy},
kontext: syntax, header, benachbarte Felder, Dokument, Seite,
frage: welcher Wert ist der plausibel wahre Wert?
```

Anforderungen an die Antwort:

- genau ein `decision.value`,
- `decision.rationale` (kurz, sachlich, nachvollziehbar),
- `decision.confidence` (`high` | `medium` | `low`),
- optional `decision.suspected_backend_bug` mit Kurzdiagnose,
- kein Rateergebnis ohne Begruendung; bei echter Unentscheidbarkeit
  `decision.value = null` und Eskalation an den Kurator.

Speicherung im Record: Status `valid/ai-decided`, Rationale als Trace-Eintrag
mit `mode: "ai_decision"`, Regelbezeichner und Kampagnen-ID.

Grenze: KI entscheidet ueber **Extraktionswahrheit**, nicht ueber Normtext. Wo
der Standard schweigt, bleibt der Fall offen.

Commit: `spec: ai decisions for campaign <id> (K cases)`.

## Phase 4 — Backend-Korrektur

Aus den Entscheidungen entsteht eine Fehlerliste je Backend: welches Backend
lag wie oft falsch, mit welchem Muster (Seitenumbruch, Ligatur, Trennstrich,
Tabellenspalte, Ziffernrauschen, Ueberschrift im Beschreibungstext).

Vorgehen:

1. Muster clustern, groesste Cluster zuerst.
2. Fix im Backend implementieren, eng begrenzt.
3. Regressionsfall aus dem entschiedenen Beispiel ableiten.
4. `crosscheck` erneut laufen lassen, nur betroffene IDs.
5. Nachweis: die entschiedenen Faelle werden nun reproduziert, ohne neue
   Abweichungen an anderer Stelle.

Jede Skriptaenderung wird einzeln committet, mit erklaerender Nachricht nach
Muster: `spec_scrape: <Ursache> -> <Wirkung> (campaign <id>, N Faelle)`.
Beispiel: `spec_scrape: trailing page digits only as standalone token -> keeps
x509 in Scope (campaign 2026-08, 27 Faelle)`.

Abbruchkriterium: keine offenen Cluster mehr oder verbleibende Faelle sind als
Einzelfaelle dokumentiert.

## Phase 5 — Evidenz aus informellen Dokumenten

Ziel: aus Spezifikationsprosa, Dokumentation, Beispielen und Code Belege
sammeln, die Eigenschaften stuetzen oder neue Elemente nahelegen.

Auftragsform je Lauf:

> Lies dieses Dokument mit genau dieser Record-Gruppe im Blick. Wenn ein
> vollstaendiger Satz Evidenz zu einem Record liefert, uebertrage den Satz
> woertlich in den Evidenzspeicher dieses Records, mit Fundstelle. Wenn du
> Evidenz zu einem fehlenden Element findest, schlage ein neues Element vor,
> lege es als `hypothesized/unconfirmed` an und begruende es.

Harte Regeln:

- Evidenz wird **woertlich** uebernommen, nie paraphrasiert.
- Jede Evidenz traegt Quelle, Locator und Evidenzstaerke
  (`strong` | `medium` | `weak`).
- Evidenz aendert **nie** direkt einen Faktwert; sie erzeugt hoechstens einen
  Claim.
- Gegenbelege werden ebenso gespeichert (`counter_evidence[]`).
- Neue Elemente entstehen nur als Hypothese, nie als publizierter Fakt.

### Gruppierung und Laufzahl

Das Optimierungsproblem lautet: moeglichst wenige Dokument-Durchlaeufe bei
moeglichst hoher Trefferquote je Record.

Empfohlene Strategie:

1. **Kandidatenfilter zuerst.** Fuer jedes Dokument nur die Records
   vorauswaehlen, deren ID, Symbol, Klasse, Header oder Namespace im Dokument
   ueberhaupt vorkommt (billiger Textindex). Das schrumpft die Gruppen massiv.
2. **Gruppieren nach Kohaerenz, nicht nach Alphabet.** Bevorzugt nach
   Klasse/Owner, dann Header, dann Cluster — weil informelle Texte typischerweise
   ueber eine Klasse als Ganzes sprechen.
3. **Gruppengroesse an Kontextfenster koppeln.** Richtwert: so viele Records,
   dass Record-Steckbriefe zusammen deutlich unter der Haelfte des Fensters
   bleiben; der Rest gehoert dem Dokumentabschnitt.
4. **Dokument in Abschnitte schneiden** (Kapitel/Unterkapitel), nicht in feste
   Byte-Bloecke; Evidenzsaetze sollen nie ueber eine Schnittkante zerfallen.
5. **Zwei Laeufe je Abschnitt-Gruppe-Paar.** Lauf 1 sammelt Evidenz fuer
   bekannte Records, Lauf 2 sucht ausschliesslich nach Hinweisen auf fehlende
   Elemente. Getrennte Auftraege liefern messbar sauberere Ergebnisse als ein
   Mischauftrag.
6. **Abbruch nach Saettigung.** Wenn ein weiterer Lauf ueber denselben Abschnitt
   keine neue Evidenz mehr liefert, gilt der Abschnitt als ausgeschoepft.
7. **Stichprobenkontrolle.** Ein fester Prozentsatz der Evidenzsaetze wird gegen
   das Dokument rueckgeprueft (Zitat vorhanden, Locator korrekt).

Messwerte je Lauf, damit die Optimierung datenbasiert wird: neue Evidenz,
Dubletten, falsche Zitate, neue Hypothesen, Kosten. Die Gruppengroesse wird
nach diesen Zahlen nachgezogen, nicht nach Gefuehl.

Commit: `spec: evidence harvest <document> (campaign <id>, E Belege, H Hypothesen)`.

## Phase 6 — Freigabe und Publikation

1. Validator laeuft: kein `valid/*` ohne Traceability, keine widerspruchsfreien
   Luecken, keine Hypothese in der Publikation.
2. Kurator sichtet `valid/ai-decided` mit `confidence: low` und alle
   Hypothesen.
3. Erst danach Generierung der Baeume und Diagramme.
4. Kampagne schliessen: Kennzahlen ins Manifest, Report ablegen.

Commit: `spec: close campaign <id> (valid V, disputed D, hypotheses H)`.

## History je Record

```json
"history": [
  {
    "campaign": "2026-08-spec-update-after-tool-improvement",
    "date": "2026-08-10",
    "from": "valid/auto-approved",
    "to": "invalid/obsolete",
    "reason": "spec update after tool improvement",
    "actor": "tool"
  }
]
```

Pflicht: `campaign`, `date`, `from`, `to`, `reason`, `actor`
(`tool` | `ai` | `curator`). History wird nur angehaengt, nie umgeschrieben.

## Kennzahlen einer Kampagne

- Records gesamt, je Status
- Felder je Triage-Klasse
- KI-Entscheidungen je Confidence
- Backend-Fehlerquote vor/nach Fix
- Evidenzsaetze je Dokument
- Hypothesen: vorgeschlagen, bestaetigt, verworfen

Diese Zahlen gehoeren in den Kampagnenreport und in die Traceability-Seite.

## Reihenfolge in Kurzform

1. Kampagne oeffnen, alles entwerten, Legacy sichern.
2. Crosscheck fahren, Ergebnis archivieren.
3. Feldweise triagieren, drei Stimmen speichern.
4. Strittiges der KI vorlegen, Entscheidung plus Rationale speichern.
5. Backend reparieren, je Fix ein Commit, Regression nachweisen.
6. Informelle Dokumente ernten, Evidenz und Hypothesen anlegen.
7. Validieren, freigeben, generieren, Kampagne schliessen.

## Vereinheitlichtes Kurations-/Review-Modell (0006-14, Nachtrag 2026-08-13)

Die in diesem Dokument beschriebenen Phasen 3 (KI-Entscheidung bei
Extraktions-Unsicherheit) und 5 (informelle Evidenz/Kuration) laufen seit
**0006-03**/**0006-06** über ein gemeinsames Datenschema und einen
gemeinsamen Lebenszyklus, nicht mehr über zwei separate, nur implizit
verwandte Mechanismen. Dieser Abschnitt macht das explizit, weil dieses
Dokument laut Vorgabe von **0006-14** die "Source of Truth" für den
Gesamtprozess bleiben soll, nicht nur emergenter Warteschlangen-Code:

- **Datenschema**: `curation-item@v1` (`_src/tools/curation_item.py`,
  `docs/pipeline/curation-item-schema.md`). Jedes Review- oder
  Kurationsflag lässt sich verlustfrei hierauf abbilden.
- **Lebenszyklus**: `discovered → queued → claimed → proposed →
  accepted/rejected → applied → published → superseded`
  (`_src/tools/workflow_lifecycle.py`,
  `docs/pipeline/workflow-lifecycle.md`). Jede bestehende Schreibfunktion
  (`review_flags.py`, `curation_flags.py`, `review_ingest.py`,
  `curation_ingest.py`, `hypothesis_store.py`) ist genau einem gültigen
  Von-/Nach-Zustandspaar zugeordnet.
- **Validierung**: `validate.py::check_workflow_lifecycle()` (**0006-13**)
  prüft laufend, dass Schema und Lebenszyklus-Vokabular nicht auseinander-
  laufen.

### Zuständigkeitsgrenzen (verbindlich)

- **Nur Mensch**: finale Entscheidung (`accepted`/`rejected`), tatsächliches
  Anwenden auf einen Record (`applied`), Betrieb der Extraktionsskripte.
- **KI darf vorschlagen, nie selbst final entscheiden**: `proposed`-Zustand
  erzeugen (konkrete Änderung oder neues hypothetisches Element, siehe
  **0006-05**). Die Ausnahme `review_flags.complete_flag(): proposed →
  applied` überspringt keinen menschlichen Schritt — sie überspringt nur
  einen separaten *Buchhaltungs*-Zustand ("accepted"), weil in diesem Pfad
  das Einreichen der Entscheidung durch einen Menschen (im Browser-Widget)
  bereits die Freigabe IST.
- **Werkzeug darf automatisch**: rein mechanische Übergänge ohne
  inhaltliche Bewertung (`discovered → queued`, `queued ⇄ claimed`,
  `applied → published`). Nie `accepted`/`rejected`.

Siehe `docs/pipeline/roles.md` Abschnitt "Zuständigkeitsgrenzen im
vereinheitlichten Modell" für die tabellarische Fassung.
