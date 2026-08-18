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

## Identität

- `owner_token`: agent:claude:re-intake:20260818T003223Z-845170c0e4da
- `request_id`: 20260818T003223Z-845170c0e4da
- `capability_class`: lokal, nicht privilegiert (keine Abnahmebefugnis,
  keine `Acceptance: ✓`-Promotion, kein `DONE.md`-Verschieben)
- `process_role`: Requirements Engineer (vom Benutzer ausdrücklich zugewiesen)
- `base_commit`: 3e8be817a
- `opened`: 2026-08-18T00:32:23Z
- `state`: [p] — Requirements-Aufnahme abgeschlossen, Review offen

## Auftrag

Benutzerauftrag im Originalwortlaut: siehe Abschnitt 1 von
`docs/dossiers/re-intake-evidence-traceability-and-roles.md` (`RQ-SRC-01`).

Zugewiesene Rollen laut Auftrag: zuerst Requirements Engineer (dokumentieren,
analysieren, im Review hinterfragen, Ergebnis dokumentieren, Rückverfolgbarkeit
sicherstellen), anschließend QA-Manager (gelebten Prozess als allgemeine Regel
festhalten).

## Schreibbereich

- `docs/dossiers/re-intake-evidence-traceability-and-roles.md` (angelegt)
- dieser Koordinationssatz

Bewusst **nicht** angefasst, weil Autorität bzw. Kundenentscheidung fehlt:
`TODO.md`, `AGENTS.md`, `SANDBOX.md`, `PRIVILEGED.md`, `docs/pipeline/*`.

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

## Nächster Schritt

Review mit dem Kunden zu `OQ-1` … `OQ-5`; danach Bookkeeping gemäß `OQ-2`
anlegen und die in Abschnitt 7 des Arbeitsprodukts genannten Schritte
abarbeiten.
