# _src/tools/ — Hilfswerkzeuge

Werkzeuge, die nicht zum regulären Generierungszyklus gehören (der lebt in
`_src/*.py`, siehe WARTUNG.md), aber bei Pflege und QA gebraucht wurden bzw.
werden. Konvention: Auch ad hoc entstandene Skripte (Einmal-Migrationen,
Prüf-Scans) werden hier abgelegt und im Kopfkommentar erklärt — nicht in
/tmp entsorgt. Alle Skripte sind vom Repo-Wurzelverzeichnis aus aufrufbar
(`python3 _src/tools/<name>.py`) und pfad-relativ, nichts ist fest verdrahtet.

## QA-Scans (wiederkehrend)

Die drei Scans aus WARTUNG.md, Abschnitt „QA der Sprachbäume“ — nach jedem
größeren Übersetzungslauf ausführen; Exit-Code 1 bei Funden:

| Skript | Zweck |
|---|---|
| `scan_lazycopy.py` | Übersetzungseinträge, die identisch zum Deutschen durchgereicht wurden (Whitelists: `i18n/whitelist*.json`) |
| `scan_restdeutsch.py` | deutsche Überbleibsel in Übersetzungen, inkl. umlautfreier Stoppwörter („zeigt“, „zur“, „wird“ …) |
| `scan_bezeichner.py` | Label-Schlüssel, die wie API-Bezeichner aussehen, müssen in jeder Sprache unverändert bleiben |

## Einmalwerkzeuge (erledigt, als Dokumentation aufbewahrt)

| Skript | Zweck |
|---|---|
| `svg2dot.py` | Rückgewinnung der `.dot`-Quellen aus den ausgelieferten Graphviz-SVGs (Oktober-Bestand) |
| `svg2seq.py` | Rückgewinnung der `.seq.json`-Quellen aus den Sequenzdiagramm-SVGs |
| `fix_dopplungen.py` | Bereinigung von Text-/Diagramm-Dopplungen in Modul-/Namespace-Guides (lxml, keine Textersetzung) |
| `migriere_spec_db.py` | Migration der Spezifikations-Records aus den Seitenmodellen in die Spezifikations-DB `_src/spec/records/` (August 2026) |
| `backfill_traces.py` | Rückwirkendes Anlegen der KI-Herkunftsakten `_src/ai/traces/**` und des Quellenregisters `_src/ai/quellen.json` für den Altbestand (August 2026); wiederholbar für neue Fragmente ohne Trace |

Einmalwerkzeuge werden nicht gelöscht: Sie dokumentieren, wie der heutige
Quellenstand entstanden ist, und dienen als Vorlage für ähnliche Migrationen
(z. B. beim Aufsetzen eines neuen Projekts nach diesem Muster).
