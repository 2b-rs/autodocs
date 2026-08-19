# AUTOSAR-Spec-Pipeline — Übersicht

Dieser Ordner dokumentiert **alle Rollen, Prozesse, Kampagnentypen, Aktionen,
Berichte und Werkzeuge**, die in diesem Repository zur Pflege der
Spezifikations-Datenbank (`_src/spec/records/`) und des generierten
HTML-Baums verwendet werden — unabhängig davon, ob sie vollständig
implementiert, teilweise implementiert, oder nur in Dokumentation/Docstrings
beschrieben sind. Jede Aussage ist mit ihrer Quelle im Code oder in einer
`.md`-Datei belegt.

## Inhalt

- [`roles.md`](./roles.md) — **Produktdomänen**rollen (Mensch, KI, Werkzeug/Validator) — nicht zu verwechseln mit [`process-roles.md`](./process-roles.md)
- [`processes.md`](./processes.md) — die Kampagnen-Prozessphasen (0–6)
- [`campaigns.md`](./campaigns.md) — Kampagnentypen, die im Repo tatsächlich vorkommen
- [`actions.md`](./actions.md) — alle Einzelaktionen (ingest review, ingest
  feedback, add evidence, infer evidence, make decision, rebuild html,
  rebuild i18n, …)
- [`reports.md`](./reports.md) — Berichtstypen und ihr Inhalt
- [`tools.md`](./tools.md) — jedes Werkzeug/Skript, Zweck, Aufruf
- [`status-model.md`](./status-model.md) — Statuswerte, Übergänge, Regeln
- [`task-acceptance.md`](./task-acceptance.md) — privilegierte Task-Abnahme, Vorgängerprüfung, Invalidierung und Feature-Gesamtabnahme
- [`branch-workflow.md`](./branch-workflow.md) — Branch-Topologie pro Backlog-Item, Basis-und-Merge-Startregel, Merge-Autorität, Feature-Integration und `[u]`-Integrationsverdikt
- [`process-roles.md`](./process-roles.md) — Prozessrollen und Fähigkeitsklassen als zwei Achsen, Rolle-zu-Klasse-Mapping, Trennungen `TK-1`/`TK-2`, Personas
- [`worker-clone-provisioning.md`](./worker-clone-provisioning.md) — klonbasierte Bereitstellung der Worker-Arbeitsbäume, Zuständigkeit und Verweigerungsfälle
- [`data-model.md`](./data-model.md) — Record-Felder, Queues, Verzeichnisse

## Kernquellen

| Dokument | Rolle |
|---|---|
| `docs/pipeline/*.md` | **Maßgebliche** Prozess- und Modell-Dokumentation für dieses Repository. Änderungen an Rollen, Statusmodell, Kampagnenphasen, Queues, Aktionen, Berichten, Identitätsschemata oder Werkzeugzuständigkeiten müssen hier zuerst oder gleichzeitig dokumentiert werden. |
| `_src/SPEC_BUILD_PROCESS.md` | Historisches, informelles Ursprungsdokument und Design-Herkunft für den ursprünglichen Kampagnenablauf; nicht mehr normativ, wenn Aussagen von `docs/pipeline/` präzisiert, erweitert oder ersetzt wurden. |
| `SPEC_QUALITY_ROADMAP.md` | Offene Punkte, Ebenen-Fortschritt, Working-Tree-Triage |
| `NEXTSTEPS.md` (jetzt in `SPEC_QUALITY_ROADMAP.md` umbenannt) | Ursprungsanalyse der Traceability-Arbeit |
| `AGENTS.md` | Betriebsregeln für Agenten/Werkzeuge in diesem Repo |
| Docstrings in `_src/tools/*.py` und `_src/*.py` | Zweck und Aufruf jedes einzelnen Werkzeugs |

## Normative Geltung

`docs/pipeline/` ist die autoritative Dokumentationsschicht für Prozess,
Datenmodell, Statusmodell, Kampagnen, Rollen, Reports, Identity/Versioning und
Workflow-Regeln dieses Repositories. `_src/SPEC_BUILD_PROCESS.md` bleibt als
historisches Überblicksdokument erhalten, dient aber nur noch der Herkunft und
Einordnung des ursprünglichen Modells. Bei Abweichungen, Präzisierungen oder
später hinzugekommenen Regeln gilt **immer** die Fassung unter `docs/pipeline/`.

## Wichtigster Grundsatz (aus `SPEC_BUILD_PROCESS.md`)

> Extraktion schlägt Darstellung, Evidenz schlägt Meinung, Entscheidung
> schlägt Stillschweigen. Kein Wert wird still korrigiert, kein Zweifel wird
> still aufgelöst.

Dieser Satz begründet praktisch jede Design-Entscheidung unten: warum es
getrennte Rollen für Werkzeug/KI/Kurator gibt, warum jeder Statuswechsel
protokolliert wird, und warum Evidenz nie direkt einen Faktwert überschreibt.
