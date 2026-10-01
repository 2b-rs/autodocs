# QA-Ausschlusspruefung Feature 0019 — Kathryn-Harry, 2026-08-22

**Auftrag (einzige Frage):** Ist im Exportbaum versehentlich etwas enthalten, das nicht
veroeffentlicht werden darf? Dies ist der DEC-0019-002-Ersatz fuer die volle
Checkpoint-Pruefung. Design, Codequalitaet, Testabdeckung, Architektur, Prozesstreue
sind explizit NICHT Gegenstand dieser Pruefung.

**Pruefgegenstand:**
- Exportbaum: `/tmp/autodocs-0019-10-preview-20260822T003000Z/export/`
- Aenderungsuebersicht: `/tmp/autodocs-0019-10-preview-20260822T003000Z/overview.html`
- Herkunft: Branch `0019-10` bei `de15a703cfc3d7b07865c339ba631aca8932abcf`, integrierter
  Feature-Tip `58b35f1e54cff2b4e718febe2c666cf5e67ae3f5`
- Behaupteter Tree-SHA256 (Worf): `7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283`

## Ergebnis

**SAUBER.**

Keine Publikationssperre verletzt. Der Baum enthaelt 2.239 unvalidierte Kandidaten-Seiten,
das ist per Kuratorentscheidung `CUR-0019-08-20260820` erwartet und zulaessig, solange sie
erkennbar als unvalidierte Review-Ansicht markiert sind — das ist mechanisch geprueft und
durchgehend der Fall.

## Punkt 1 — Marker-Vollstaendigkeit (mechanisch geprueft, nicht angenommen)

- 2.239 Record-Seiten unter `export/records/*.html` (ohne `records/index.html`, die
  Listing-Seite ist keine Kandidaten-Seite).
- `grep -Lr 'data-unvalidated-marker="awaiting-curator-confirmation"' export/records/*.html`
  (Index-Datei ausgeschlossen) liefert **0 Treffer** — jede einzelne der 2.239 Seiten traegt
  den Marker.
- Zusaetzlich: jede der 2.239 Seiten enthaelt exakt den Block
  `<section id="candidate-status" data-validation-state="unvalidated"><h2>Validation
  status</h2><p><strong>UNVALIDATED — AWAITING CURATOR CONFIRMATION</strong>` — mechanisch
  ueber alle Dateien geprueft, keine Abweichung gefunden.
- Einziger im gesamten Baum vorkommender `data-validation-state`-Wert: `unvalidated`
  (kein `valid`, `confirmed` o.ae. als Seitenzustand).

**Zahlen fuer die Meldung:** 2.239 Seiten geprueft, 2.239 mit Marker (100 %).

## Punkt 2 — Statusbehauptungen als Tatsache?

Volltextsuche nach `valid`, `confirmed`, `approved`, `verified` ueber alle generierten
Seiten:

- Treffer fuer `confirmed`/`invalid/to-be-confirmed` stammen ausschliesslich aus dem
  eingebetteten Kuratier-Evidenzblock (`"status": "invalid/to-be-confirmed"`) — das ist die
  korrekte, nicht-bestaetigende Statusangabe.
- 32 Treffer fuer `verified` und 1 Treffer fuer `approved` liegen ausnahmslos innerhalb der
  als `UNVALIDATED — AWAITING CURATOR CONFIRMATION` gerahmten
  `<section id="source-derived-content">`-Bloecke: es ist woertlich zitierter
  Quelltext (z. B. Requirement-Text „The Security Analyses are verified …"), keine
  Aussage ueber den Record selbst. Jede dieser Seiten traegt zusaetzlich den
  Seiten-Marker und den `candidate-status`-Block aus Punkt 1.
- Keine Seite behauptet an einer nicht klar als Quelle/ausstehend gerahmten Stelle,
  ihr Inhalt sei bestaetigt oder gueltig.

## Punkt 3 — Fremdinhalt / interne Artefakte im Baum?

- Dateitypen im gesamten Baum ausschliesslich `.html`, `.json`, `.css`, `.js` (2.248
  Dateien geprueft) — keine Nicht-Standard-Dateien.
- Keine Datei mit `TODO`/`claim` im Namen.
- Keine Treffer fuer `/Users/tobias` (lokale Pfade), keine E-Mail-Adressen, keine
  Treffer fuer Agenten-/Session-Token-Muster (`agent:...:...`, `owner_token`,
  `TODO-<name>-<id>`).
- Zwei Treffer fuer `token`/`password`/`secret`/`api_key`-Wortmuster — beide sind
  Fachtext aus Quelldokumenten (Kryptografie-/AUTOSAR-Domaenenbegriffe: „validate a
  certificate or token", „secret keys from a master key or password"), keine
  tatsaechlichen Zugangsdaten.
- `export/evidence.json` (1,4 MB) strukturell inspiziert: enthaelt Manifest, Digests,
  Zaehlwerte, einen Unresolved-Fall — keine lokalen Pfade, keine E-Mail-Adressen, keine
  Agenten-/Claim-Kennungen.

## Punkt 4 — Aenderungsuebersicht (`overview.html`) vs. Baum

- Alle 6 in `overview.html` verlinkten Pfade (`export/index.html`,
  `export/participate.html`, `export/records/0010c3e297eff1782132c620.html`,
  `export/en/unresolved.html`, `export/evidence.json`, `export/validation.json`)
  existieren und sind aus dem Dateisystem heraus aufloesbar — geprueft.
- Die Zahlenbehauptung „2.239 records … invalid/to-be-confirmed" stimmt mit
  `export/validation.json` (`counts.records: 2239`, `counts.by_status:
  {"invalid/to-be-confirmed": 2239}`) und mit der mechanischen Zaehlung ueberein.
  `validation.json.result` steht auf `PASS`.
  Alle dort gelisteten Checks (`every_candidate_unvalidated`, `individual_marker`,
  `listing_marker`, `source_and_validation_separated`, …) stehen auf `PASS`,
  konsistent mit den eigenen mechanischen Befunden dieser Pruefung.
- Die Uebersicht behauptet nichts, was im Baum nicht zutrifft. Sie ist als
  Entscheidungsgrundlage brauchbar.

## Punkt 5 — Tree-SHA256

**Nicht reproduzierbar mit dieser Pruefung** — ehrlich, statt geraten. Getestete
Standardverfahren ueber `export/` (Dateiliste `sort`, dann):
1. Konkatenation aller Dateiinhalte, sha256 → `3c964ec1...`
2. Konkatenation aus Pfad+Inhalt je Datei, sha256 → `38731d5e...`
3. Manifest aus `pfad:sha256(inhalt)`-Zeilen, sha256 des Manifests → `c3f2e384...`
4. `find . -type f | sort | shasum -a 256 | shasum -a 256` (Hash-der-Hashliste) →
   `bc7ae96e...`

Keines davon ergibt den von Worf genannten Wert
`7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283`. Das konkrete
Hashverfahren (Tool, Flags, ggf. Normalisierung von Zeilenenden/Metadaten) wurde nicht
mitgeliefert und war aus dem Baum selbst nicht ableitbar. Dieser Punkt bleibt offen und
ist **kein** Bestandteil des `sauber`-Urteils — die inhaltliche Pruefung (Punkte 1-4) ist
davon unabhaengig und vollstaendig.

## 2.239 vs. 2.240 — Aufloesung der Randnotiz

Kein Widerspruch. `find export -path '*records*' -name '*.html'` zaehlt 2.240 Dateien,
weil `export/records/index.html` (die Uebersichtsseite „All 2,239 unvalidated S-Core
candidates") mitgezaehlt wird. Ohne diese Listing-Seite sind es exakt 2.239 individuelle
Kandidaten-Record-Seiten — deckungsgleich mit Worfs Zahl, `validation.json` und
`overview.html`. Harmlos, wie vermutet.

## Nebenbeobachtungen (nicht Teil des Auftrags, kein Befund, kein Blocker)

- `export/participate.html` verlinkt `../../../curation-report.html` — von
  `export/participate.html` aus fuehren drei `../`-Stufen ueber die Wurzel des
  Preview-Baums hinaus; innerhalb dieses Preview-Baums ist der Link nicht aufloesbar.
  Vermutlich ein Pfad-Template, das fuer tiefer verschachtelte Produktionsstruktur
  gedacht ist und in der flachen Preview-Struktur nicht passt. Kein Ausschlussproblem
  (kein Leck, keine Falschaussage), sondern ein moeglicher toter Link.
- Alle 2.239 Record-Seiten referenzieren `<script src="../../../../review_request.js"
  defer>`; diese Datei existiert nirgends im Preview-Baum (`find` bestaetigt: keine
  Treffer). Das Partizipations-Skript wuerde im Preview clientseitig nicht laden. Auch
  hier: kein Ausschluss-/Leck-Befund, sondern eine funktionale Beobachtung fuer die
  Feature-Implementierer, nicht fuer diese Pruefung.

## Was nicht geprueft wurde

- Keine Bewertung von Design, Code, Testabdeckung, Architektur oder Prozesstreue
  (explizit ausserhalb des Auftrags).
- Der Tree-SHA256 wurde nicht reproduziert (siehe Punkt 5) — die Integritaet des
  Baums gegenueber dem behaupteten Hash ist damit nicht durch mich bestaetigt,
  nur die inhaltliche Ausschlusspruefung.
- Keine Pruefung des `git`-Zustands von Branch `0019-10` / Feature-Tip selbst (Commits,
  History, wer was wann committet hat) — nur der bereits gebaute Exportbaum wurde
  inspiziert.
- `export/assets/` (CSS/JS, view.css, view.js) wurde nur ueber die generellen Volltext-
  und Dateityp-Scans erfasst, nicht Zeile fuer Zeile gelesen.
