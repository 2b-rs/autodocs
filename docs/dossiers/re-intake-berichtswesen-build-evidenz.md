# Requirements-Analyse: Berichtswesen und durchgängige Build-Evidenz

**Status:** RE-Arbeitsprodukt. Informativ bis zur Umsetzung durch Feature `0043`.
**Erhoben:** 2026-08-19 (Meldung) / 2026-08-20 (Beauftragung), Requirements-Engineer-Funktion nach `docs/pipeline/process-roles.md`.
**Anlass:** Die publizierten Berichtsseiten unter `process.html` §8 sind veraltet, unvollständig und für das bevorstehende ASPICE-Assessment nicht belastbar.

## 1. Anforderung im Originalwortlaut (`RQ-SRC-03`)

Meldung des Kunden (aktueller Benutzer), 2026-08-19:

> Hallo Troy, ich bin noch ein wenig unglücklich mit unseren Prozessen. Jetzt wurde im Zuge von Feature 0019 die Website neu gebaut, aber die Berichte unter 8. von /process.html sind nicht auf einem aktuellen Stand, inbesondere nicht build-reports.html, wo ich eine Liste aller Website-Builds erwartet hätte. Die anderen Berichtsformate sind ebenso unvollständig, erklärungsbedürftig und nicht schön anzusehen. Können wir da was machen? Ich glaube, wir kriegen auch Probleme mit unserem bevorstehenden ASPICE-Assessment, wenn wir uns darum nicht kümmern.

Beauftragung und Entscheidung des Kunden, 2026-08-20 (Satz 1–2 einer längeren
Nachricht; der vollständige Wortlaut ist als `RQ-SRC-04` in
[`re-intake-prozessverbesserung-integration-und-capabilities.md`](re-intake-prozessverbesserung-integration-und-capabilities.md)
archiviert):

> Ledger einchecken passt. Mach daraus gerne ein TODO-Feature.

## 2. Befunde (technische Analyse, 2026-08-20)

- **B1 — `build-reports.html` ist ein eingefrorener Schnappschuss.** Die Seite
  wird nicht beim Build erzeugt; `_src/tools/build_report.py publish` schreibt
  fertiges HTML in das Seitenmodell `_src/sources/pages/build-reports.json`.
  Letzter erfolgreicher Lauf: 13./14.08.2026. Seitdem rendert jeder Build
  denselben Stand mit festen Zahlen und „Runner-Referenz: N/A".
- **B2 — Die Korrelationskette ist gerissen.** Alle vier Produzenten
  (`generate.py`, `validate.py`, `i18n_translate.py`, `i18n_diagrams.py`)
  schreiben Subreports nach `output/build-reports/` und übernehmen
  `run_archive_ref` aus der Umgebungsvariablen `RUN_ARCHIVE_REF` — die **nirgends
  gesetzt wird** (weder Runner-Lifecycle noch `run-loop.sh` noch `WARTUNG.md`).
  Befund am Bestand: 128 von 129 Reports tragen `run_archive_ref: null`, einer
  ist defekt. `build_report.py combine` wurde nachträglich fail-closed gehärtet
  und verweigert ohne gültige Referenz-Kohorte die Aggregation; gegen den realen
  Bestand kann es daher **nie** erfolgreich laufen. Der einzige existierende
  Combined-Report stammt aus der Zeit vor der Härtung.
- **B3 — Eine Build-Liste war nie vorgesehen.** `publish` rendert ausschließlich
  den jeweils letzten Lauf; die vom Kunden erwartete Historie ist konzeptionell
  nicht vorhanden.
- **B4 — Die Historiendaten existieren, aber unversioniert.** 737 Skript/Log-Paare
  unter `output/run-archive/` und 129 Subreports liegen vor, sämtlich unter dem
  git-ignorierten `output/` — nicht konfigurationsverwaltet, nicht
  baseline-fähig, pro Maschine verschieden. Als Assessment-Evidenz (SUP.8) so
  nicht zitierfähig.
- **B5 — Die übrigen Berichte tragen keinen sichtbaren Stand.** Kurations-,
  Traceability- und Open-Reviews-Bericht nennen keinerlei Erzeugungszeitpunkt;
  jüngster Extraktions-Stand ist der 12.08.2026. Die S-Core-Kampagne (Feature
  `0019`) taucht in keinem Bericht auf, obwohl `0019-06` eigene Kampagnen-Evidenz
  fordert.
- **B6 — Strukturmuster.** Ein Gate wurde gehärtet (`combine` fail-closed), die
  Produzenten wurden nicht nachgezogen, und kein Prüfschritt bemerkt die Lücke.
  Dasselbe Muster hat bereits das Automation-Safety-Gate stillgelegt. Ohne
  mechanischen Frischecheck wird jede Berichtsseite wieder einfrieren.

## 3. Abgeleitete Anforderungen

- **RQ-BR-01** `build-reports.html` zeigt die vollständige Liste aller
  Publikationsläufe (nicht nur den letzten), mit Ergebnis, Zeitpunkt, Referenz.
- **RQ-BR-02** Jeder Publikationslauf trägt eine durchgängige Laufkorrelation:
  die Produzenten-Subreports eines Laufs teilen eine gültige `run_archive_ref`;
  `combine` darf an fehlender Korrelation nicht mehr strukturell scheitern.
- **RQ-BR-03** Die Build-Historie ist konfigurationsverwaltet: ein getracktes,
  append-only Ledger (eine Zeile pro Publikationslauf) ist die zitierfähige
  Quelle der Liste aus `RQ-BR-01`.
- **RQ-BR-04** Veralten ist mechanisch ausgeschlossen: die kanonische
  Build-Sequenz enthält `publish`, und `validate.py` meldet einen Befund, wenn
  das publizierte Seitenmodell älter ist als der jüngste Subreport.
- **RQ-BR-05** Alle fünf Berichtsseiten tragen einen einheitlichen Kopf:
  Erzeugungszeitpunkt, erzeugendes Werkzeug, Datenquelle und ein erklärender
  Absatz „was zeigt dieser Bericht, wie lese ich ihn".
- **RQ-BR-06** Die S-Core-Kampagnen-Evidenz (`0019-06`) ist in das Berichtswesen
  einbezogen.
- **RQ-BR-07** Eine dokumentierte Evidenzlandkarte ordnet jedem Bericht das
  ASPICE-Prozessergebnis zu, das er belegt (insb. SUP.8, MAN.3, SWE.6).

## 4. Entscheidungsdatensatz

Format nach `RQ-DEC-01/02/03`; Aufzeichnungspflicht nach `TK-2`
(`docs/pipeline/process-roles.md`).

### `DEC-0043-001` — Das Build-Ledger wird eingecheckt

- **Zeitpunkt:** 2026-08-20
- **Entscheidende Instanz:** aktueller Benutzer (Management/Kunde)
- **Entscheidung:** Die Build-Historie wird als getracktes, append-only Ledger
  Teil des Repositories („Ledger einchecken passt.").
- **Fachliche Rechtfertigung:** Nur konfigurationsverwaltete Evidenz ist
  baseline-fähig und in einem ASPICE-Assessment (SUP.8) zitierfähig. Die
  bisherige Ablage unter git-ignoriertem `output/` ist pro Maschine verschieden
  und nicht reproduzierbar.
- **Bewusst aufgegeben:** Die bisherige Linie „Laufevidenz ist grundsätzlich
  git-ignoriert" wird **für das Ledger** umgekehrt. Begrenzung: getrackt werden
  Kennzahlen, Referenzen und Ergebnisse je Lauf — nicht die Rohlogs; die
  Skript/Log-Paare unter `output/run-archive/` bleiben ignoriert.
- **Umsetzung:** Feature `0043` (insb. `0043-02`).

### `DEC-0043-002` — Berichte werden bewahrt, nicht routinemäßig neu erzeugt

- **Zeitpunkt:** 2026-08-21
- **Entscheidende Instanz:** aktueller Benutzer (Management/Kunde), übermittelt
  durch Koordinator Data.
- **Vorbereitende Prüfung:** Architekt Riker hat eine unabhängige Scope-Prüfung
  durchgeführt (Session `937e1b2b`) und festgestellt, dass eine erzwungene
  Berichtsbewahrung ein **qualifizierendes vorgangsübergreifendes Tor** im Sinne
  der `cross-item-blast-radius`-Prüfung ist. Damit ist dieser Datensatz vor der
  ersten qualifizierenden Mutation verpflichtend (`AGENTS.md`,
  Cross-item gate-scope review exception).
- **Entscheidung:** Bestehende Berichte werden **bewahrt**. Eine Neuerzeugung ist
  nur bei **Notwendigkeit** zulässig, und Notwendigkeit hat genau drei Gestalten:
  1. **Verlust** der gerenderten Seiten;
  2. **schwere Fehler in früheren Fassungen der Erzeugungslogik**, die nicht nur
     im Skript, sondern auch in den erzeugten Seiten behoben werden müssen;
  3. **Vergleich** — wenn an einem alten HTML-Bericht etwas seltsam wirkt und
     rekonstruiert werden soll, ob jemand ihn manipuliert hat, ob die Daten
     beschädigt oder unvollständig waren, oder ob die Erzeugungslogik einen
     Fehler hatte.
- **Zweite, unabhängige Begründung — Skalierbarkeit:** Extraktionsberichte müssen
  von den normalen Site-Neuerzeugungen **ausgenommen** sein, weil sie mit der Zeit
  länger werden und die Website-Regenerierung dadurch immer langsamer würde. Das
  ist auf Dauer nicht tragbar. Diese Begründung steht **neben** der
  Evidenzbewahrung, nicht unter ihr: Selbst wenn die Bewahrung nicht gewollt
  wäre, verböte sich das routinemäßige Neurendern des wachsenden Archivs aus
  Laufzeitgründen.
- **Betriebliche Grenze:** Historische veröffentlichte Berichte werden
  standardmäßig bewahrt. Verlust oder ein materieller Erzeugungsfehler erlauben
  eine **auditierbare Ersetzung** mit Grund, Digests und Verknüpfung. Forensische
  Rekonstruktion und Vergleich erzeugen einen **getrennten Kandidaten** und
  überschreiben **niemals** den beobachteten Bericht. Das Verhalten für den
  aktuellen/lebenden Bericht und den Index ist ausdrücklich zu klassifizieren und
  fällt nicht stillschweigend unter die Archivregel. Normale Site-Neuerzeugungen
  rendern das historische Extraktionsarchiv nicht neu; erzeugt werden nur
  wirklich neue Seiten und die nötige Übersichtsverknüpfung.
- **Bewusst aufgegeben:** Die zuvor vorgeschlagene **universelle
  Unveränderlichkeitsregel**. Der Benutzer hat sie ausdrücklich verworfen
  („scrap that"). Bewahrung ist die Voreinstellung, nicht ein Verbot: Es gibt
  benannte, begründete und auditierbare Wege zur Ersetzung.
- **Reichweite:** `0043-05` und die weitere Berichtserzeugung; die in `0043-05`
  bereits committete Extraktions-Bewahrungsregel (`f7cf0f09b`) ist **Präzedenz,
  nicht Blankovollmacht** — sie wird durch diesen Datensatz getragen, nicht
  umgekehrt.
- **Umsetzung:** Keine Implementierung ist autorisiert, bevor dieser Datensatz
  existiert. Mit seiner Aufzeichnung ist diese Bedingung erfüllt.
- **Offener Punkt — Governance-Pfad `docs/pipeline/reports.md`:** Der
  Implementierungs-Commit `f7cf0f09b` hat diese Datei auf dem Vorgangszweig
  geändert. Nach `DEC-0044-012` ist sie ein Governance-Artefakt und gehört auf
  `main`. Der Anteil ist auf `main` nachzuziehen, sobald sein Inhalt feststeht;
  der Worker hat weitere Policy-Mutationen zu Recht eingestellt. Siehe die
  Klarstellung zum Geltungsbereich unter `DEC-0044-012`.

- **Provenienz — Nutzeranweisungen wortwörtlich:**

  > scrap that. I simply want existing reports to be preseved if possible and only re-generated when necessary. Necessity for re-generation could be: Loss of the rendered pages, or severe errors in past versions of generation logic that needs fixing not only in the scripts, but also in the generated pages, and third, comparison. If we find something strange in an old html report and want to reconstruct whether somenoe has tampered with the report, or the data was corrupt/incomplete, or the generation logic had a bug.

  > Also, there is a very practical reason why extraction reports must be exempt from normal site rebuilds: They will grow longer over time, so website regeneration will become slower over time. We cannot affort this in the long run.

## 5. Abgrenzung

Nicht Gegenstand dieses Features: die Behebung des Automation-Safety-Blockers
(`0040-10`), die Publikation auf das Deploy-Repo (SSH-Autorisierung, Feature
`0019`-Kontext) und inhaltliche Korrekturen an den Berichtsdaten selbst.
