# TODO-claude-re-intake-20260818T003223Z-845170c0e4da.md — Koordinationssatz

## Art dieses Satzes

**Temporärer Koordinationssatz für eine benutzergeführte Tätigkeit**, zulässig
nach `AGENTS.md`:

> „A user-directed activity that is not an existing Task may use
> `TODO-<agent-id>.md` as a temporary coordination record, but must not falsely
> mark an unrelated Task `[p]`."

Dieser Satz markiert daher **keinen** Task-Marker in `TODO.md`. Insbesondere
bleibt `0039-01` unverändert `[u]`, solange die Reservierungssperre von Feature
`0039` nicht durch den Benutzer ausdrücklich aufgehoben ist.

## Claim identity

Kanonische Schreibweise (`key: value`, ohne Aufzählungszeichen und Backticks),
wie sie `_src/tools/legacy_task_doctor.py` erwartet:

owner_token: agent:claude:re-intake:20260818T003223Z-845170c0e4da
request_id: 20260818T003223Z-845170c0e4da
base_commit: 3e8be817ace3387cf35abd355c7da302cd807cd8
capability_class: privileged
state: [p]

Ergänzende, nicht-kanonische Angaben:

- `process_role`: Requirements Engineer, danach Architekt, danach QA-Manager
  (vom Benutzer ausdrücklich zugewiesen)
- `authority`: vollprivilegierte Eignersession laut `DEC-0040-001`
  (Benutzerentscheidung 2026-08-18, begrenzter Autoritätsverzicht mit
  kompensierender Maßnahme — siehe Arbeitsprodukt Abschnitt 6a)
- `opened`: 2026-08-18T00:32:23Z
- **Kein `task_id`:** Dieser Satz koordiniert eine benutzergeführte Tätigkeit,
  nicht eine einzelne bestehende Task. Er beansprucht keine fremde Task.

## Auftrag

Benutzerauftrag im Originalwortlaut: siehe Abschnitt 1 von
`docs/dossiers/re-intake-evidence-traceability-and-roles.md` (`RQ-SRC-01`).

Zugewiesene Rollen laut Auftrag: zuerst Requirements Engineer (dokumentieren,
analysieren, im Review hinterfragen, Ergebnis dokumentieren, Rückverfolgbarkeit
sicherstellen), anschließend QA-Manager (gelebten Prozess als allgemeine Regel
festhalten).

## Intended write scope

- `docs/dossiers/re-intake-evidence-traceability-and-roles.md`
- `TODO-claude-re-intake-20260818T003223Z-845170c0e4da.md`
- `TODO.md` (ausschließlich der neue Abschnitt Feature `0040`)

## Ausserhalb des Schreibbereichs

Bewusst **nicht** angefasst, weil dafür die Umsetzung der Tasks von Feature
`0040` zuständig ist: die Autoritätsdokumente `AGENTS.md`, `SANDBOX.md` und
`PRIVILEGED.md` sowie sämtliche Prozessdokumente unterhalb des Verzeichnisses
`docs/pipeline`.

## Fremde Arbeit im Baum (unberührt zu erhalten)

- gestagter Rename `docs/studies/` → `docs/dossiers/`
- `tools/discover_runner_transaction_recovery.py` (Discovery-Nutzlast zu `0038-02`)
- `docs/brainstorming/*` (unversioniert)
- alle fremden Claims, insbesondere die beiden `0038-02`-Claims

## Ergebnis der RE-Phase

Arbeitsprodukt: `docs/dossiers/re-intake-evidence-traceability-and-roles.md`

- Anforderung verbatim aufgenommen (`RQ-SRC-01`)
- Auslösender Befund mit acht belegten Beobachtungen (T1–T8)
- 17 zerlegte, einzeln prüfbare Anforderungen mit stabilen IDs
  (`RQ-TRACE-*`, `RQ-DEC-*`, `RQ-PROC-*`, `RQ-ROLE-*`, `RQ-STD-*`, `RQ-EFF-01`)
- Sechs Analysebefunde (A–F), darunter zwei, die den Auftragszuschnitt ändern:
  - **Befund E:** Task `0039-01` deckt den Auftrag bereits weitgehend ab; neu
    sind nur `RQ-TRACE-03`, `RQ-DEC-01/02/03/05`, `RQ-ROLE-03`, `RQ-EFF-01`.
  - **Befund F:** Feature `0039` trägt eine Reservierungssperre, die eine
    Agentensession nicht selbst aufheben darf.
- Vorläufige ASPICE-Zuordnung als Prozessunterstützung, ausdrücklich **ohne**
  Capability-Behauptung
- Fünf offene Fragen (`OQ-1` … `OQ-5`) an den Kunden

## Blocker

`OQ-1` und `OQ-2` blockieren die Umsetzungsphase:

- `OQ-1` ist eine Autoritätsfrage (Reservierungssperre Feature `0039`). Ohne
  ausdrückliche Benennung dieser Session als privilegierte Eignersession darf
  kein `0039`-Marker bewegt werden.
- `OQ-2` bestimmt, ob eine bestehende Task geändert oder ein neues Feature
  angelegt wird. Ein Fehlgriff hier erzeugt genau die Art von Backlog-Defekt,
  die der Auftrag beseitigen soll.

`OQ-3`, `OQ-4` und `OQ-5` sind fachliche Zuschnittsfragen; sie blockieren
nicht die Bookkeeping-Entscheidung, wohl aber den Entwurf des Rollenmodells
und des Traceability-Formats.

## Bekannte Abweichung: `owner_token` ohne Task-ID

`legacy_task_doctor.py` meldet `LTD-CLAIM-IDENTITY-MISMATCH`, weil
`owner_token` an der Task-Position `re-intake` statt einer Task-ID trägt.

Die Abweichung wird **bewusst nicht korrigiert**: `AGENTS.md` erklärt den
einmal geprägten Token für unveränderlich („that token remains this session's
ownership proof"). Ihn nachträglich umzuschreiben wäre ein schwererer
Regelverstoß als der Befund selbst. Zum Zeitpunkt der Prägung existierte
Feature `0040` noch nicht, und es gibt bis heute keine Task, die das Anlegen
dieses Features abdeckt.

Der eigentliche Mangel liegt im Werkzeug: Der Doctor kennt nur Task-Claims,
während `AGENTS.md` den temporären Koordinationssatz für benutzergeführte
Tätigkeiten ausdrücklich erlaubt. Dieses Format ist im Schema nicht abgebildet.
Der Befund ist als Arbeitsposten in Feature `0040` vermerkt (siehe dortige
Anmerkung zu `0040-03`) und nicht stillschweigend unterdrückt.

## Next step

Umsetzung von Feature `0040` beginnen. Reihenfolge nach Vorbedingungen:
`0040-01` (Rollenmodell) und `0040-03` (Entscheidungsdatensatz) sind ohne
Vorbedingung startbar und bilden die Grundlage für alles Weitere. `0040-05`
(Prozesserweiterung, Integrationsprüfung verpflichtend) folgt auf beide.

Vor jeder Abnahme an eigener Arbeit ist die kompensierende Maßnahme aus
`DEC-0040-001` anzuwenden: Kennzeichnung als Selbstabnahme mit Nennung von
`DEC-0040-001` als Autoritätsreferenz.
