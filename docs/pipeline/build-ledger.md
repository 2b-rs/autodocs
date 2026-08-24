# Build-Ledger — getrackte, append-only Bauhistorie

Status: verbindliche Schemadefinition (Task `0043-02`, umgesetzte Entscheidung
`DEC-0043-001`). Ergänzt [`build-report-schema.md`](build-report-schema.md):
dort steht das Format **eines** Laufberichts, hier das Format der **Historie**
über alle Läufe.

- **Datei:** `docs/evidence/build-ledger.jsonl` (getrackt, im Repository)
- **Format:** JSON Lines — UTF-8, eine JSON-Zeile je Veröffentlichungslauf,
  jede Zeile mit `\n` abgeschlossen, keine Leerzeilen
- **Werkzeug:** [`_src/tools/build_ledger.py`](../../_src/tools/build_ledger.py)
- **Schreiber:** `_src/tools/build_report.py` bei `combine` und `publish`
- **Leser:** `build_ledger.read_entries()` / `verify()` (für `0043-03`
  Rendering und `0043-04` Staleness-Prüfung)

## Warum getrackt (`DEC-0043-001`)

Nur konfigurationsverwaltete Evidenz ist baseline-fähig und in einem
ASPICE-Assessment (SUP.8) zitierfähig. Die Grenze der Entscheidung ist scharf:

- **Getrackt:** Kennzahlen, Referenzen und Ergebnisse je Lauf — also genau
  dieses Ledger.
- **Weiterhin git-ignoriert:** die Rohdaten, d. h. `output/build-reports/*.json`
  und die Skript/Log-Paare unter `output/run-archive/`. Das Ledger *verweist*
  auf sie (`combined_report_ref`) und *fixiert* sie kryptographisch
  (`combined_report_digest`), kopiert sie aber nicht ins Repository.

## Append-only — was das konkret heißt

1. Ein Lauf erzeugt **genau einen** Eintrag. `combine` schreibt ihn; das
   nachfolgende `publish` desselben Laufs erkennt ihn an `run_archive_ref`
   wieder und schreibt **nicht** erneut (idempotent je Lauf).
2. Geschrieben wird ausschließlich mit `O_APPEND` — bestehende Bytes werden
   nie überschrieben, auch nicht bei parallelen Schreibern.
3. Ein Eintrag wird **nie** korrigiert. Ist eine Aussage falsch, wird ein neuer
   Eintrag angehängt; die Historie bleibt vollständig.
4. `recorded_at` ist monoton: ein Eintrag, der älter als der letzte im Ledger
   ist, wird abgewiesen.
5. Die Append-only-Eigenschaft ist **maschinell prüfbar**:
   `build_ledger.py verify --baseline=HEAD` verlangt, dass der eingecheckte
   Stand ein **byte-genaues Präfix** der Arbeitskopie ist. Jede Änderung,
   Umsortierung oder Löschung eines bestehenden Eintrags verletzt diese
   Präfix-Relation und wird als `rewritten-build-ledger` (severity `error`)
   gemeldet — auch dann, wenn der manipulierte Eintrag für sich genommen
   schemakonform ist.

## Eintragsschema (`schema_version: "1.0"`)

| Feld | Typ | Beschreibung |
|---|---|---|
| `schema_version` | string | `"1.0"`. Bei brechenden Änderungen erhöhen. |
| `entry_kind` | string | Immer `"publication-run"`. |
| `recorded_at` | string | UTC-Zeitstempel `YYYY-MM-DDTHH:MM:SSZ` des Anhängens. Monoton steigend. |
| `run_started_at` | string | Beginn des Laufs (frühestes `started_at` der Kohorte). |
| `run_finished_at` | string | Ende des Laufs. |
| `run_archive_ref` | string \| null | Kohorten-ID des Laufs (`run-archive/run-<ts>-n<seq>` oder `manual-<ts>-<8 hex>`, siehe [`build-report-schema.md`](build-report-schema.md)). `null` ist **ausschließlich** in einem `backfilled`-Eintrag zulässig. |
| `repo_commit` | string \| null | 40-stelliger HEAD-Commit des Repositories zum Zeitpunkt des Laufs; `null`, wenn nicht ermittelbar. Wird nie geraten. |
| `exit_code` | integer | 0–255, Gesamtergebnis des Laufs (aus dem kombinierten Report). |
| `overall_success` | boolean | Muss mit `exit_code == 0` übereinstimmen. |
| `counts_by_stage` | object | Zähler je Stufe; enthält immer alle vier Schlüssel `i18n_merge`, `i18n_diagrams`, `html_generate`, `validate` (leeres Objekt, wenn die Stufe nicht lief). |
| `findings_count` | integer | Anzahl der Befunde des kombinierten Reports. |
| `findings_by_severity` | object | `{"info": n, "warning": n, "error": n}`. Die Summe darf `findings_count` nicht überschreiten. |
| `combined_report_digest` | string | `sha256:<64 hex>` über die exakten Bytes des kombinierten Reports. |
| `combined_report_ref` | string | Repo-relativer Pfad des kombinierten Reports (liegt unter `output/`, also git-ignoriert). |
| `backfilled` | boolean | `true`, wenn der Eintrag nachträglich aus historischer Evidenz erzeugt wurde, statt vom Lauf selbst geschrieben zu sein. |
| `note` | string | *(optional)* Erläuterung, insbesondere für `backfilled`-Einträge. |

Unbekannte Zusatzfelder sind erlaubt und werden von `validate_entry()` nicht
abgewiesen; Konsumenten dürfen sich nicht auf ihre Abwesenheit verlassen.

## Der erste Eintrag ist nachgetragen

Zeile 1 ist der historische Veröffentlichungslauf vom 2026-08-13/14 — genau der
eingefrorene Stand hinter `build-reports.html`, der Feature `0043` ausgelöst hat.
Er ist mit `"backfilled": true` markiert und hat `run_archive_ref: null` und
`repo_commit: null`, weil er der Korrelationsreparatur aus `0043-01` vorausgeht:
eine Kohorten-ID lässt sich nachträglich nicht ehrlich vergeben, und ein
plausibler Commit wäre eine Schlussfolgerung, keine Evidenz. `note` hält beides
samt des naheliegenden (aber nicht belegten) Commit-Kandidaten fest.
`verify` warnt, wenn ein *späterer* Eintrag als `backfilled` markiert ist — dann
liegt der Verdacht nahe, dass ein Live-Append ausgefallen ist.

## Kommandos

```bash
# Historie prüfen (Schema, Duplikate, Reihenfolge)
python3 _src/tools/build_ledger.py verify

# zusätzlich beweisen, dass nur angehängt wurde
python3 _src/tools/build_ledger.py verify --baseline=HEAD --json

# Historie ausgeben, neueste zuerst
python3 _src/tools/build_ledger.py list --limit=10

# einen Lauf schreiben (implizit durch combine/publish)
python3 _src/tools/build_report.py combine
python3 _src/tools/build_report.py combine --no-ledger   # Diagnoselauf, kein Eintrag
```

Exit-Codes von `verify`: `0` sauber, `1` Befunde mit severity `error`,
`2` Aufruffehler.

## Vertrag für Konsumenten (`0043-03`, `0043-04`)

`build_ledger.read_entries(path=None)` liefert `(entries, findings)`:

- `entries` — nur schemakonforme Einträge, in Dateireihenfolge, **ältester
  zuerst**. Für eine Anzeige „neueste zuerst" umkehren.
- `findings` — Befunde im Format der Build-Reports
  (`{category, severity, message, ref}`), Kategorien
  `malformed-build-ledger`, `duplicate-build-ledger-entry`,
  `rewritten-build-ledger`, `build-ledger-baseline-unavailable`.

Damit gilt für Konsumenten verbindlich:

- Ein defektes Ledger darf **nicht** als „kurze Historie" gerendert oder als
  „alles in Ordnung" gewertet werden. `findings` sind sichtbar zu machen
  (`0043-03`: auf der Seite selbst; `0043-04`: als Validierungsbefund).
- Ein fehlgeschlagener Append ist kein grüner Lauf: `build_report.py`
  hebt den Exit-Code auf mindestens `1`, wenn das Ledger nicht geschrieben
  werden konnte.
- Für Staleness (`0043-04`) ist `entries[-1]` der zuletzt verzeichnete Lauf;
  `run_finished_at` bzw. `recorded_at` sind die Vergleichszeitpunkte, und
  `run_archive_ref` verbindet den Eintrag mit der Subreport-Kohorte unter
  `output/build-reports/`.
- Ein Lauf ohne Ledger-Eintrag ist ein Befund, kein Normalfall — deshalb ist
  `--no-ledger` ausdrücklich auf Diagnoseläufe beschränkt.
