# AUTOSAR-Spec-Pipeline — Übersicht

Dieser Ordner dokumentiert **alle Rollen, Prozesse, Kampagnentypen, Aktionen,
Berichte und Werkzeuge**, die in diesem Repository zur Pflege der
Spezifikations-Datenbank (`_src/spec/records/`) und des generierten
HTML-Baums verwendet werden — unabhängig davon, ob sie vollständig
implementiert, teilweise implementiert, oder nur in Dokumentation/Docstrings
beschrieben sind. Jede Aussage ist mit ihrer Quelle im Code oder in einer
`.md`-Datei belegt.

## Inhalt

- [`roles.md`](./roles.md) — alle Rollen (Mensch, KI, Werkzeug/Validator)
- [`processes.md`](./processes.md) — die Kampagnen-Prozessphasen (0–6)
- [`campaigns.md`](./campaigns.md) — Kampagnentypen, die im Repo tatsächlich vorkommen
- [`actions.md`](./actions.md) — alle Einzelaktionen (ingest review, ingest
  feedback, add evidence, infer evidence, make decision, rebuild html,
  rebuild i18n, …)
- [`reports.md`](./reports.md) — Berichtstypen und ihr Inhalt
- [`tools.md`](./tools.md) — jedes Werkzeug/Skript, Zweck, Aufruf
- [`status-model.md`](./status-model.md) — Statuswerte, Übergänge, Regeln
- [`data-model.md`](./data-model.md) — Record-Felder, Queues, Verzeichnisse

## Kernquellen

| Dokument | Rolle |
|---|---|
| `_src/SPEC_BUILD_PROCESS.md` | Maßgebliches Prozessdokument: Kampagnen-Phasen 0–6, Statusmodell, Rollen |
| `SPEC_QUALITY_ROADMAP.md` | Offene Punkte, Ebenen-Fortschritt, Working-Tree-Triage |
| `NEXTSTEPS.md` (jetzt in `SPEC_QUALITY_ROADMAP.md` umbenannt) | Ursprungsanalyse der Traceability-Arbeit |
| `AGENTS.md` | Betriebsregeln für Agenten/Werkzeuge in diesem Repo |
| Docstrings in `_src/tools/*.py` und `_src/*.py` | Zweck und Aufruf jedes einzelnen Werkzeugs |

## Wichtigster Grundsatz (aus `SPEC_BUILD_PROCESS.md`)

> Extraktion schlägt Darstellung, Evidenz schlägt Meinung, Entscheidung
> schlägt Stillschweigen. Kein Wert wird still korrigiert, kein Zweifel wird
> still aufgelöst.

Dieser Satz begründet praktisch jede Design-Entscheidung unten: warum es
getrennte Rollen für Werkzeug/KI/Kurator gibt, warum jeder Statuswechsel
protokolliert wird, und warum Evidenz nie direkt einen Faktwert überschreibt.
