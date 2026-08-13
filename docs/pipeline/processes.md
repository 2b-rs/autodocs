# Prozesse

Quelle: `_src/SPEC_BUILD_PROCESS.md`. Dies ist der einzige Ort im Repo, der
den vollen Lebenszyklus einer Kampagne end-to-end beschreibt.

## Grundhaltung

> Extraktion schlägt Darstellung, Evidenz schlägt Meinung, Entscheidung
> schlägt Stillschweigen.

Ein Fakt hat genau einen Ort (`ein Fakt, ein Ort`, aus `ARCHITEKTUR.md`);
generierte Artefakte sind wegwerfbar.

## Phase 0 — Kampagne öffnen

- Kampagnen-Manifest anlegen: `spec/campaigns/<id>.json` mit Auslöser,
  Release, Werkzeugstand (Git-Commit von `spec_scrape.py`), Backend-Liste,
  PDF-Cache-Hash (`manifest.sha256`).
- Alle Records auf `invalid/obsolete` setzen (Reason: z. B. "spec update
  after tool improvement").
- Alten Feldwert als `legacy` sichern (dritte Stimme später).
- Commit: `spec: open campaign <id>, invalidate all records`.
- **Wichtig**: Entwertung löscht nichts — nur die Geltung wird ausgesetzt.

**Implementierungsstatus**: Konzept vollständig beschrieben. Das konkrete
Beispiel im echten Repo (`SWS_LOG`, Kampagne
`2026-08-sws-log-pilot-after-tool-improvement`) zeigt exakt dieses Muster in
geschriebenen Records (`status.state`, `legacy`, `history`) — also praktisch
bereits einmal durchlaufen, mindestens pilothaft.

## Phase 1 — Extraktion

- `spec_scrape.py crosscheck` mit mindestens zwei Backends gegen versionierten
  PDF-Cache.
- Ergebnis = Kampagnen-Input, unverändert archiviert unter
  `output/spec-validation/<release>/crosscheck-<campaign>.json`.
- **Kein Schreibzugriff auf die DB** in dieser Phase.

**Implementierungsstatus**: `crosscheck`-Phase existiert als CLI-Kommando in
`spec_scrape.py` (`phase_crosscheck`).

## Phase 2 — Triage je Feld

- Verglichene Felder: Kind, Header file, Scope, Symbol, Underlying type,
  abgeleitete Namespace-Sicht.
- Drei Stimmen je Feld: `backend_a`, `backend_b`, `legacy`.

| Konstellation | Ergebnis | Reason |
|---|---|---|
| A = B = legacy | `valid/auto-approved` | `unchanged` |
| A = B ≠ legacy | `valid/corrected` | `database error, detected after new import` |
| A ≠ B | `invalid/to-be-confirmed` | `uncertain scraping result` |

- Fehlende Backend-Stimme zählt als Uneinigkeit, nicht Zustimmung.
- Bekannte Modellierungsabsichten (z. B. `std`-Spezialisierungen,
  `ns.abweichung = "std-spezialisierung"`) werden vor der Triage per
  Normalisierungsregel neutralisiert.
- Triage ist feldweise: Record-Status = Minimum der Feldstatus (strittig
  schlägt korrigiert schlägt unverändert).
- Alle drei Stimmen werden im Record persistiert (`fields.<Name>.votes`).
- Commit: `spec: triage campaign <id> (auto-approved N, corrected M, disputed K)`.

**Implementierungsstatus**: Das `fields`-Objekt mit `state`/`reason`/`votes`
ist exakt in den bereits geschriebenen `SWS_LOG`-Pilot-Records zu finden —
konkret gelebt, nicht nur beschrieben.

## Phase 3 — KI-Entscheidung strittiger Felder

- Nur Felder mit `invalid/to-be-confirmed`.
- Vorlage je Fall: `id, field, votes{backend_a, backend_b, legacy}, kontext,
  frage`.
- Antwortpflichten: `decision.value`, `decision.rationale`,
  `decision.confidence` (`high`|`medium`|`low`), optional
  `decision.suspected_backend_bug`; bei Unentscheidbarkeit `value = null` +
  Eskalation an Kurator.
- Speicherung: Status `valid/ai-decided`, Trace-Eintrag `mode: "ai_decision"`.
- Grenze: KI entscheidet nur über Extraktionswahrheit, nie über Normtext.
- Commit: `spec: ai decisions for campaign <id> (K cases)`.

**Implementierungsstatus**: Nur als Schema/Prozess beschrieben; kein
eigenständiges Skript im Repo automatisiert diese Phase (die KI-Entscheidung
selbst ist ein externer, nicht versionierter Schritt).

## Phase 4 — Backend-Korrektur

1. Fehlermuster clustern (größte Cluster zuerst): Seitenumbruch, Ligatur,
   Trennstrich, Tabellenspalte, Ziffernrauschen, Überschrift im
   Beschreibungstext.
2. Fix eng begrenzt im Backend implementieren.
3. Regressionsfall aus dem entschiedenen Beispiel ableiten.
4. `crosscheck` erneut, nur betroffene IDs.
5. Nachweis: entschiedene Fälle reproduziert, keine neuen Abweichungen.
- Commit-Muster: `spec_scrape: <Ursache> -> <Wirkung> (campaign <id>, N Fälle)`.
- Abbruchkriterium: keine offenen Cluster mehr.

**Implementierungsstatus**: Tatsächlich gelebt — die Commit-History zeigt
genau dieses Muster (`bae18b1c`, `e554a1a8`, `751013a2`, `c2334c43` usw.), wie
in `extraction_report.py`'s `CATEGORIES` dokumentiert (siehe `reports.md`).

## Phase 5 — Evidenz aus informellen Dokumenten

- Ziel: aus Spezifikationsprosa/Doku/Beispielen/Code Belege sammeln, die
  Eigenschaften stützen oder neue Elemente nahelegen.
- Harte Regeln:
  - Evidenz wörtlich übernehmen, nie paraphrasieren.
  - Jede Evidenz trägt Quelle, Locator, Evidenzstärke
    (`strong`|`medium`|`weak`).
  - Evidenz ändert nie direkt einen Faktwert; erzeugt höchstens einen Claim.
  - Gegenbelege ebenso gespeichert (`counter_evidence[]`).
  - Neue Elemente nur als Hypothese (`hypothesized/unconfirmed`), nie als
    publizierter Fakt.
- Optimierungsstrategie (Gruppierung/Laufzahl):
  1. Kandidatenfilter zuerst (billiger Textindex je Dokument).
  2. Gruppieren nach Kohärenz (Klasse/Owner, Header, Cluster), nicht Alphabet.
  3. Gruppengröße an Kontextfenster koppeln.
  4. Dokument nach Kapitel/Unterkapitel schneiden, nie an Byte-Grenzen.
  5. Zwei Läufe je Abschnitt-Gruppe-Paar: Lauf 1 = Evidenz für bekannte
     Records, Lauf 2 = ausschließlich Hinweise auf fehlende Elemente.
  6. Abbruch nach Sättigung (keine neue Evidenz mehr).
  7. Stichprobenkontrolle eines festen Prozentsatzes gegen das Dokument.
- Messwerte je Lauf: neue Evidenz, Dubletten, falsche Zitate, neue
  Hypothesen, Kosten.
- Commit: `spec: evidence harvest <document> (campaign <id>, E Belege, H
  Hypothesen)`.

**Implementierungsstatus**: Nur als Prozess beschrieben. `upstream_evidence.py`
implementiert einen *verwandten, aber anderen* Mechanismus (rohe
Backend-Textausschnitte je ID/Dokument sichern, "Preserve raw evidence at
every stage") — nicht dasselbe wie das hier beschriebene Sammeln von
Prosa-Evidenz aus informellen Dokumenten.

## Phase 6 — Freigabe und Publikation

1. Validator läuft: kein `valid/*` ohne Traceability, keine widerspürliche
   Lücken, keine Hypothese in der Publikation.
2. Kurator sichtet `valid/ai-decided` mit `confidence: low` und alle
   Hypothesen.
3. Erst danach Generierung der Bäume und Diagramme.
4. Kampagne schließen: Kennzahlen ins Manifest, Report ablegen.
- Commit: `spec: close campaign <id> (valid V, disputed D, hypotheses H)`.

**Implementierungsstatus**: `trace-check` (Konsistenzvalidierung) und
`generate.py` (Generierung des HTML-Baums) existieren als separate, bereits
lauffähige Tools — aber nicht als ein einziger orchestrierter
"Phase-6-Runner".

## Kennzahlen einer Kampagne (aus `SPEC_BUILD_PROCESS.md`)

- Records gesamt, je Status
- Felder je Triage-Klasse
- KI-Entscheidungen je Confidence
- Backend-Fehlerquote vor/nach Fix
- Evidenzsätze je Dokument
- Hypothesen: vorgeschlagen, bestätigt, verworfen

## Reihenfolge in Kurzform

1. Kampagne öffnen, alles entwerten, Legacy sichern.
2. Crosscheck fahren, Ergebnis archivieren.
3. Feldweise triagieren, drei Stimmen speichern.
4. Strittiges der KI vorlegen, Entscheidung plus Rationale speichern.
5. Backend reparieren, je Fix ein Commit, Regression nachweisen.
6. Informelle Dokumente ernten, Evidenz und Hypothesen anlegen.
7. Validieren, freigeben, generieren, Kampagne schließen.

## Einordnung: vereinheitlichtes Kurations-/Review-Modell (0006-14)

Die oben beschriebenen Prozessschritte, die auf eine menschliche oder
KI-Entscheidung warten (Review, Kuration), durchlaufen seit **0006-06**
konzeptionell denselben Lebenszyklus, unabhängig davon, über welchen
Einstiegspunkt (Warteschlange, Browser-Widget, oder — neu seit **0006-05** —
den warteschlangenlosen Hypothesen-Speicher) sie entstanden sind:
`discovered → queued → claimed → proposed → accepted/rejected → applied →
published → superseded`. Details und die vollständige Zuordnung jeder
bestehenden Aktion zu diesem Lebenszyklus stehen in
[`workflow-lifecycle.md`](workflow-lifecycle.md); das zugrundeliegende
Datenschema in [`data-model.md`](data-model.md) und
[`curation-item-schema.md`](curation-item-schema.md).
