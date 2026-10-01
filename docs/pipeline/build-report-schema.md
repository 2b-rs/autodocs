# Build-Report Schema (i18n + HTML Publication Runs)

Status: canonical schema definition (TASK 0001-01). Producers (i18n_translate.py,
i18n_diagrams.py, generate.py, validate.py) are extended to emit conforming
reports in follow-up tasks 0001-03..0001-06. This document defines the schema
only; it does not by itself change any producer's behavior.

## Envelope (common to every producer)

Every build-report JSON document has this top-level envelope:

| Field | Type | Description |
|---|---|---|
| `schema_version` | string | Schema version, e.g. `"1.0"`. Bump on breaking changes. |
| `report_kind` | string | One of `i18n_merge`, `i18n_diagrams`, `html_generate`, `validate`, `combined`. |
| `tool` | string | Script/module name that produced the report, e.g. `i18n_translate.py`. |
| `command` | string | Full invoked command line (argv, joined), for reproducibility. |
| `inputs` | array[string] | Paths/identifiers of inputs consumed (e.g. batch files, source PDFs, language code). |
| `started_at` | string | ISO-8601 UTC timestamp, run start. |
| `finished_at` | string | ISO-8601 UTC timestamp, run end. |
| `duration_s` | number | Wall-clock duration in seconds (finished_at - started_at). |
| `exit_code` | integer | Process exit code of the producing run. |
| `changed_artifacts` | array[string] | Paths of files created/modified/deleted by this run. |
| `counts` | object | Producer-specific counters (see below); always present, may be `{}`. |
| `findings` | array[object] | Structured findings/issues, each `{category: string, severity: "info"|"warning"|"error", message: string, ref?: string}`. Empty array if none. |
| `run_archive_ref` | string\|null | Path to the `run.sh` + `.log` pair that produced this report, if run via the local runner (links to 0001-09's traceability). |

## Producer-specific `counts` fields

| `report_kind` | `counts` fields |
|---|---|
| `i18n_merge` | `batches_consumed`, `accepted`, `rejected`, `register_changes` |
| `i18n_diagrams` | `sources_considered`, `translated_written`, `unchanged_skipped`, `stale_deleted` |
| `html_generate` | `pages_generated_per_lang` (object: lang -> int), `fallback_to_german` (object: lang -> int), `changed_targets` |
| `validate` | `checks_performed`, `findings_by_category` (object: category -> int), `success` (bool) |
| `combined` | union of the above under `by_stage` (object: report_kind -> counts object), plus `overall_success` (bool) |

## Conventions

- All reports are UTF-8 JSON, one document per run (no NDJSON).
- `findings` categories are free-form strings but SHOULD be stable, kebab-case identifiers (e.g. `missing-namespace`, `stale-svg`) so 0001-06's category grouping and future automation can group on them reliably.
- A report with `exit_code != 0` MUST have at least one `findings` entry with `severity: "error"` explaining the failure.
- Where a run's output is intended to be published into the HTML tree (0001-08), the report MUST additionally set `run_archive_ref`.
- This schema is deliberately producer-agnostic at the envelope level so 0001-07's combined report can merge N producer reports without bespoke per-tool glue.

## `run_archive_ref` correlation and the manual-build fallback (0043-01)

Every producer (`i18n_translate.py`, `i18n_diagrams.py`, `generate.py`,
`validate.py`) sets `run_archive_ref` from the `RUN_ARCHIVE_REF` environment
variable. `build_report.py combine` is fail-closed: it only aggregates
subreports that share one non-empty `run_archive_ref` value, and refuses to
guess a cohort when the value is missing or inconsistent.

Two producers of a valid `run_archive_ref` value are recognized, both plain
non-empty strings (no new field, no schema-version bump required):

- **Runner-issued:** `runner-host/run-loop.sh` sets it to
  `run-archive/run-<timestamp>-n<seq>`, the path stem of the archived
  `.log`/`.sh` pair it writes under `output/run-archive/` for that run. A
  reference in this form is expected to resolve to a real file under
  `output/run-archive/` and is rendered as a link where it does.
- **Manual fallback:** for a build executed outside the runner, `python3
  _src/tools/build_report.py mint-ref` mints a value prefixed `manual-`
  (`manual-<UTC timestamp>-<8 hex chars>`). This prefix is reserved: no
  runner-issued ref ever starts with it, so a manual-run cohort is always
  distinguishable from a runner-run cohort. A `manual-*` ref does not resolve
  to an archive file and is rendered as plain text, not a link — see
  `_src/WARTUNG.md` § "Build- & Publikations-Berichte" for the operator
  procedure.

## Build-Ledger (0043-02)

Der kombinierte Report beschreibt **einen** Lauf und liegt git-ignoriert unter
`output/build-reports/`. Die *Historie* über alle Läufe ist davon getrennt und
getrackt: `build_report.py combine`/`publish` projizieren jeden kombinierten
Report auf eine Zeile des append-only Ledgers
`docs/evidence/build-ledger.jsonl`. Schema, Append-only-Garantie und der
Konsumentenvertrag stehen in [`build-ledger.md`](build-ledger.md); die
Entscheidung, das Ledger (und nur das Ledger, nicht die Rohlogs) einzuchecken,
ist `DEC-0043-001`.

## Publikations-Provenienz des Seitenmodells (0043-04)

Das getrackte Seitenmodell `_src/sources/pages/build-reports.json` trägt seit
Task `0043-04` (Entscheidung `DEC-0043-003`) ein zusätzliches **Top-Level-Objekt**
`publication_provenance`. Es bindet die veröffentlichte Seite an **genau einen**
schemakonformen Eintrag des getrackten Ledgers und macht damit maschinell
prüfbar, ob die Seite den zuletzt verzeichneten Publikationslauf zeigt. Die
bisherigen Felder des Seitenmodells (`file`, `title`, `main`, …) bleiben
unverändert; das Objekt wird nicht gerendert und ändert die erzeugte
`build-reports.html` nicht.

| Feld | Typ | Beschreibung |
|---|---|---|
| `schema_version` | string | `"1.0"`. `validate.py` weist eine unbekannte Version zurück, statt sie zu raten. |
| `bound_at` | string | UTC-Zeitstempel `YYYY-MM-DDTHH:MM:SSZ`, zu dem **diese** Bindung entstand. Bleibt unverändert, solange die Bindung unverändert ist, damit ein wiederholtes `publish` desselben Laufs ein byte-identisches Seitenmodell erzeugt. |
| `ledger_ref` | string | Repo-relativer Pfad des Ledgers, aus dem gebunden wurde. |
| `ledger_entry_count` | integer | Anzahl schemakonformer Ledger-Einträge zum Bindungszeitpunkt. |
| `ledger_findings_count` | integer | Anzahl der Ledger-Befunde zum Bindungszeitpunkt. |
| `ledger_entry` | object \| null | Die Bindung selbst; `null` nur, wenn das Ledger keinen schemakonformen Eintrag enthält. |
| `ledger_entry.recorded_at` | string | `recorded_at` des gebundenen Eintrags. |
| `ledger_entry.run_archive_ref` | string \| null | Kohorten-ID des gebundenen Laufs. `null` ist ausschließlich zulässig, wenn der Eintrag `backfilled: true` trägt. |
| `ledger_entry.combined_report_digest` | string | `sha256:<64 hex>` des kombinierten Reports, wie im Ledger verzeichnet. |
| `ledger_entry.backfilled` | boolean | Spiegelt `backfilled` des gebundenen Eintrags. |
| `rendered_run_archive_ref` | string \| null | Kohorte, aus der der Detailabschnitt („jüngster Lauf") der Seite gerendert wurde. `null`, wenn der gerenderte Lauf keine Kohorten-Identität trägt (der historische Nachtrag hat keine). Ist der Wert gesetzt, muss er `ledger_entry.run_archive_ref` entsprechen. |

Die Bindung wird **immer erzeugt, nie von Hand geschrieben**:

```bash
# im normalen Publikationslauf, zusammen mit der Seite:
python3 _src/tools/build_report.py publish

# nur die Bindung neu berechnen (idempotent) — der unterstützte Weg, wenn der
# kombinierte Rohreport des verzeichneten Laufs nicht mehr vorliegt, weil er
# unter git-ignoriertem output/ liegt (DEC-0043-001):
python3 _src/tools/build_report.py provenance
```

### Diagnose-Markierung `diagnostic_no_ledger`

Ein mit `--no-ledger` erzeugter kombinierter Report trägt zusätzlich
`"diagnostic_no_ledger": true`. Damit unterscheidet `validate.py` eine
ausdrücklich diagnostische Kohorte (kein Publikationskandidat) von einem
Publikationslauf, dessen Ledger-Append **fehlgeschlagen** ist — letzterer bleibt
ein Befund.

### Was `validate.py` daraus prüft

`check_report_freshness()` meldet `severity: "error"` in **genau zwei** Fällen
(`DEC-0043-003`, Architekten-Schranke B-02):

1. `publication_provenance` fehlt, ist fehlerhaft, oder stimmt nicht mit dem
   jüngsten schemakonformen Ledger-Eintrag überein — Kategorie
   `stale-build-report`;
2. eine **vollständige**, nicht-diagnostische Publikationskohorte unter
   `output/build-reports/` hat keinen passenden Ledger-Eintrag — Kategorie
   `unrecorded-publication-run`.

Fehlerhafte Ledger-Daten werden mit den Kategorien aus
[`build-ledger.md`](build-ledger.md) durchgereicht. Die Prüfung ist rein
beobachtend: sie kombiniert, veröffentlicht, schreibt und repariert nichts.
Unvollständige (laufende) Kohorten, identitätslose Reports und die Abwesenheit
git-ignorierter Rohreports lösen **nie** einen Befund aus — ein frischer Klon mit
leerem `output/` ist grün.
