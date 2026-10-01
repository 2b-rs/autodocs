# Acceptance-Review 0043-07 und Abschluss Feature 0043

- **Prüferin:** `belanna` (Integratorin)
- **Unabhängigkeit:** unabhängig vom Implementierer `agent:tom-adeyemi-20260824t133000z:0043-07:20260824T133000Z` (Dispatcher `tom`, unprivilegiert). Diese Session hat den Publikationslauf nicht implementiert und nicht erneut ausgeführt.
- **Datum:** 2026-09-29
- **Auftrag:** `20260929-215515-grok-0043-07-rev`
- **Geprüfter Baum:** Branch `task-0043-07-review`, Baseline vor diesem Bericht `3170be4607490cbdac3661a0dbd4eba781489d5c`
- **Substanzieller Kandidat:** `5bfe836f65cc410374a63bf2f8c435a67d35b55e` (Vorfahr dieses Branch)
- **Kohorte:** `manual-20260824T072259Z-d6eece5d`
- **Projektleitung in der Feature-Zeile:** `jadzia`, wie im Abschlussauftrag benannt

## Entscheidung

**Acceptance: ✓**

Task `0043-07` ist abgenommen. Feature `0043` (Publication Pipeline and Build History; Repository-Identität *Reporting: Continuous Build Evidence and Current Reports*) ist auf dieser Basis geschlossen. Die Buchung in `TODO.md` folgt in einem eigenen Commit und verweist auf den Commit dieses Berichts. Dieser Bericht enthält keinen selbstbezüglichen Hash.

Verdikt: `accepted`. Die Abnahme ist die Abnahme des Arbeitsprodukts nach `docs/pipeline/task-acceptance.md`. Sie ist keine Produktfreigabe, keine Architekturgenehmigung, keine Release-Freigabe und kein Automotive-SPICE-Capability-Level.

## Auftrag und Grenze

Geprüft wurden die vorhandene Evidenz unter `docs/campaign-evidence/0043-07-publication-run/`, der Ledger-Eintrag in `docs/evidence/build-ledger.jsonl`, die Seitenbindung von `build-reports.html` / `_src/sources/pages/build-reports.json`, die Auflage `F-TOM-BAXTER-003` aus der Abnahme von `0043-04`, die Dispositionen `RQ-BR-01` bis `RQ-BR-07` und die bereits gebuchten Acceptance-Zeilen von `0043-01` bis `0043-06`.

Der Publikationslauf wurde nicht erneut ausgeführt. `DONE.md`, der Issue-Store und fremde Claims wurden nicht geändert.

## Kriterien

| Kriterium | Ergebnis | Beleg auf diesem Baum |
|---|---|---|
| AC-001 Ein realer Lauf end-to-end: korrelierte Subreports, erfolgreiches `combine`, Ledger-Eintrag, Historie, `validate.py` grün einschließlich Staleness | erfüllt | Stufen 11–20 derselben Kohorte; Ledger-Zeile 2; Seitenbindung identisch; `check_report_freshness()` heute ohne Befund |
| AC-002 Jede `RQ-BR-*`-Anforderung hat eine Disposition | erfüllt | `21-rq-br-dispositions.md`: `RQ-BR-01` bis `RQ-BR-07` |
| AC-003 Lauf-Evidenz bleibt erhalten | erfüllt | Stufen `00`–`21` liegen unter `docs/campaign-evidence/0043-07-publication-run/` |
| DoD: committet; keine Berichtsseite älter als der Lauf, den sie ausweist | erfüllt für die bindende Prüfung | Provenienz bindet `recorded_at=2026-08-24T11:29:43Z`; Stufe 20 und der heutige Freshness-Aufruf sind befundfrei |
| Auflage `F-TOM-BAXTER-003` (Feuerbedingung (b) live) | erledigt | Stufe 15, Exit 1, Kategorie `unrecorded-publication-run` für genau diese Kohorte |

Voraussetzungen `0043-01` bis `0043-06` tragen in `TODO.md` bereits `[x]` und `Acceptance: ✓`. Die von `0043-07` induzierte prerequisite-closed Kette ist damit geschlossen. Die Vorgänger bleiben in ihrer historischen Formulierung `(task, open)`; das war nicht Teil dieses Auftrags.

## Unabhängig nachgemessen

Python `3.14.7`. Das echte Ledger und das Seitenmodell blieben bei allen Läufen byte-identisch.

1. Ledger `docs/evidence/build-ledger.jsonl`: 2 Zeilen, SHA-256 `254862eee8af423835154607533af18e21c0e5d8a98efb47322fb6a930d8625e`. Das ist der in den Stufen 16, 17, 18 und 20 festgehaltene Hash.
2. Zeile 1, SHA-256 der Zeile inklusive Zeilenumbruch: `eb43c604ebc2b968a8e9872c3760c6107799b4075e56da718a9d3c6087a44be7`. Das ist der in Stufe 16 als Zustand *vor* dem Append genannte Datei-Hash. `backfilled: true`, `run_archive_ref: null`.
3. Zeile 2: `backfilled: false`, `run_archive_ref: manual-20260824T072259Z-d6eece5d`, `repo_commit: 7a0cce8d2ac60a5b1b19e529a571cd740de10039` (Objekt im Repository vorhanden), `recorded_at: 2026-08-24T11:29:43Z`, `combined_report_digest: sha256:7add61d98f88a5d8e00ea4e5aa11e9507d18e577d4649a926899e3ad4edf3d6d`, `exit_code: 1`, `overall_success: false`. Die eingebettete Validate-Zählung nennt einen Befund `unrecorded-publication-run`. Das ist der Stand zum Zeitpunkt von `combine`, nicht der spätere Endzustand.
4. Seitenmodell `_src/sources/pages/build-reports.json`, Schlüssel `publication_provenance`, `schema_version` `1.0`: `ledger_entry.recorded_at`, `run_archive_ref` und `combined_report_digest` sind gleich dem jüngsten Ledger-Eintrag. `rendered_run_archive_ref` ist dieselbe Kohorte.
5. `build-reports.html` enthält die Kohorte dreimal und `2026-08-24T11:29:43Z` vor `2026-08-21T12:58:43Z`. `href="output/build-reports` kommt nullmal vor.
6. `validate.check_report_freshness()` auf diesem Baum: 0 neue Befunde. `output/build-reports/` existiert hier nicht; die Prüfung bleibt dafür grün, wie der Vertrag es für einen Checkout ohne Rohberichte vorsieht. Ledger danach unverändert.
7. Hermetische Suiten, alle gegen Temp-Verzeichnisse, Ledger danach unverändert:
   - `_src/tests/test_build_ledger.py`: `Ran 26 tests` / `OK` / Exit 0
   - `_src/tools/test_build_report.py`: `Ran 12 tests` / `OK` / Exit 0
   - `_src/tools/test_report_page_header.py`: `Ran 2 tests` / `OK` / Exit 0
   - `_src/tests/test_build_report_provenance.py`: `Ran 9 tests` / `OK` / Exit 0
   - `_src/tests/test_report_freshness.py`: 19/19 bestanden, darunter `test_malformed_ledger_is_reported`, `test_complete_cohort_without_ledger_entry_fires`, `test_frozen_page_without_provenance_fires`, `test_incomplete_cohort_does_not_fire`, `test_fresh_clone_with_empty_output_passes` und `test_real_repository_page_model_is_bound_and_current`. `pytest` ist in diesem Interpreter nicht installiert; die Testdatei wurde mit einem lokalen `pytest`-Stub geladen und jede `test_*`-Funktion ausgeführt. Exit der Sammelausführung 0, `FRESHNESS_TESTS passed=19 failed=0`.

## Dreiweg-Nachweis des Staleness-Gates

Die drei Zustände stehen in den aufbewahrten Stufen und schließen einander aus. Heute wurde der räumende Zustand auf diesem Baum erneut ausgeführt.

| Stufe | Befehl laut Evidenzdatei | Exit | Zustand |
|---|---|---|---|
| 15 `15-validate-unrecorded-run.txt` | `python3 _src/validate.py` | 1 | Feuerbedingung (b) `unrecorded-publication-run` für `manual-20260824T072259Z-d6eece5d`. Das ist `F-TOM-BAXTER-003`. |
| 17 `17-validate-after-combine.txt` | `python3 _src/validate.py` | 1 | Feuerbedingung (a) `stale-build-report`: Seite noch `2026-08-21T12:58:43Z` / `run_archive_ref=None`, Ledger bereits `2026-08-24T11:29:43Z` / diese Kohorte. |
| 20 `20-validate-final.txt` | `python3 _src/validate.py` | 0 | `OK — Tree aktuell …`, `STAGE-COMPLETE`. Ledger-Hash in der Datei gleich dem heutigen Datei-Hash. |
| heute | `validate.check_report_freshness()` | keine Befunde | Bindung und Ledger stimmen überein; kein lokales `output/` erzeugt keinen Fehlalarm. |

`malformed-build-ledger` wurde in diesem Lauf nicht live ausgelöst und hier auch nicht am echten Ledger erzeugt. Die hermetische Abdeckung ist `test_malformed_ledger_is_reported` (bestanden). Das bleibt eine benannte Grenze, kein Abnahmehindernis: die Auflage verlangte den Live-Nachweis der Bedingung (b), nicht einen absichtlich beschädigten Ledger.

## Auflage aus 0043-04 und combine

`F-TOM-BAXTER-003` ist durch Stufe 15 erledigt. Bedingung (a) ist in Stufe 17 zusätzlich live belegt.

Die zweite, taskfremde Auflage zum toten Link `process.html` → `TODO-perplexity-0037-37-20260816-1443.md` ist auf diesem Baum erledigt, indem die Seite den Namen nicht mehr enthält (0 Treffer). Die Zieldatei wurde nicht wiederhergestellt. Ein grünes `validate` bedeutet nicht, dass die Datei zurückgekehrt ist.

`combine` hat den Eintrag angehängt (Stufe 16: 1 → 2 Zeilen, derselbe End-Hash). Die Zeile `shell exit_code: 0` in `16-combine.txt` ist eine falsch gemessene Shell-Variable. `16a-combine-exit-correction.txt` lässt die bereits committete Datei stehen und korrigiert den Wert auf `1`. `_src/tools/build_report.py` gibt den Exit des aggregierten Laufs zurück, nicht den Erfolg der Aggregation. `overall_success: false` und Exit 1 stammen aus 107 taskfremden `i18n_merge`-Ablehnungen (`F-TOM-ADEYEMI-001`) plus dem zum Combine-Zeitpunkt noch unrecorded Validate-Befund. Die Aggregation selbst hat alle vier Stufen unter einem nicht-leeren `run_archive_ref` zusammengeführt, den Digest gesetzt und genau einen Eintrag geschrieben. Ein erneutes `combine` (Stufe 16a) und `publish` (Stufe 18) ließen denselben Hash stehen: ein Eintrag je Lauf. Das erfüllt „erfolgreiches combine“. Einen befundfreien Gesamtbuild nachträglich zu fordern, würde das Kriterium verschärfen.

## Feature-Abschluss

`0043-07` ist der verpflichtende Integrationsknoten des Features. Der Feature-Knoten selbst trägt in `issues/0043/index.md` kein zusätzliches `Integration review: mandatory`; der Floor ist dieser Task. `0043-01` bis `0043-06` sind akzeptiert. Damit ist die Schließung in `TODO.md` zulässig.

Die Feature-Zeile verwendet den im Auftrag vorgegebenen Titel `Publication Pipeline and Build History`. Die hinterlegte Identität bleibt `Reporting: Continuous Build Evidence and Current Reports` (`DONE.md`, `issues/0043/index.md`). `DONE.md` führt `0043` bereits als `(feature, closed)` ohne diese Acceptance-Zeile und ist als generierte Sicht markiert; es wurde nicht von Hand geändert.

`docs/pipeline/aspice-report-evidence-map.md` ist aus `docs/pipeline/README.md` verlinkt und sagt in Zeile 7 und Zeile 43 ausdrücklich, dass es kein Assessment ist und kein Capability-Level vergibt.

## Datenverlust und Grenzen

- Das getrackte Ledger wurde durch diese Prüfung nicht beschrieben. Hash vorher und nachher identisch.
- `output/build-reports/combined-1787570983.json` ist nicht in Git (`git ls-files` findet ihn nicht). Das ist die Grenze aus `DEC-0043-001`: der Rohbericht ist git-ignoriert, der Digest steht im Ledger. Aus diesem Checkout ist der Rohbericht nicht wiederherstellbar. Das ist die entschiedene Grenze, kein bei dieser Abnahme neu gefundener Defekt.
- `0019-06` bleibt sichtbar und unverlinkt. Das ist die bereits disponierte Grenze von `0043-05` / `RQ-BR-06`.
- Zwei Messfehler der Implementierung bleiben sichtbar: Stufe 16a (Combine-Exit) und die in Stufe 19 protokollierte erste, leere Exit-Erfassung. Sie sind korrigiert dokumentiert, nicht still bereinigt.
- Die älteren Review-Commits `218ca607df4b3628e7d424e6dd5aadb65bda074a` und `2d96dd7513509a8f2093413118bb19583adcf37f` sind als Objekte erreichbar und liegen auf `review-0043-07-belanna-20260824T163500Z`. Sie sind keine Vorfahren dieses Branch, und ihre Berichtsdateien liegen nicht im Arbeitsbaum. Diese Abnahme stützt sich auf die hier nachgemessenen Artefakte, nicht auf jene nicht integrierten Berichte.
- Ein vollständiger `validate.py`-Lauf über den Baum und ein erneuter Publikationslauf wurden nicht ausgeführt. Stufe 20 dauerte historisch etwa drei Minuten; der Auftrag nimmt die erneute Ausführung aus dem Umfang. Der heutige Ersatz für das Staleness-Orakel ist der direkte Aufruf von `check_report_freshness()` plus die 19 hermetischen Fälle.
- Kein Browser stand in diesem Lauf zur Verfügung. Die Historienseite wurde als Datei gelesen, nicht in einem Browser bedient.
- Der Issue-Store führt `0043` und `0043-07` bereits als `closed` und enthält eine Acceptance-Prosa vom 2026-08-25. Er liegt außerhalb der erlaubten Dateien und wurde nicht angeglichen. Maßgeblich für diesen Auftrag ist die bisher fehlende Buchung in `TODO.md`.

## Ausgeführte Befehle

Arbeitsverzeichnis jeweils `/private/tmp/autodocs-worktrees/task-0043-07-review`.

- Ledger-Hash, Zeilenzerlegung, HTML- und Seitenmodellvergleich, Auswertung der Exit-Zeilen in der Evidenz, Erreichbarkeit von `5bfe836f6`, `7a0cce8d2ac60a5b1b19e529a571cd740de10039`, `218ca607d`, `2d96dd751`. Ende: Ledger-Hash gleich dem Stufenclaim, Seitenbindung `match_recorded/ref/digest True`, `218` und `2d96` nicht Vorfahren von `HEAD`.
- `validate.check_report_freshness()` im Prozess, ohne Schreiben. Ende: `freshness_new_findings 0`, `ledger_unchanged True`, `output_dir_exists False`.
- `python3 _src/tests/test_build_ledger.py`. Ende: `Ran 26 tests in 0.828s` / `OK` / `EXIT 0`.
- `python3 _src/tools/test_build_report.py`. Ende: `Ran 12 tests in 0.166s` / `OK` / `EXIT 0`.
- `python3 _src/tools/test_report_page_header.py`. Ende: `Ran 2 tests in 0.000s` / `OK` / `EXIT 0`.
- `python3 _src/tests/test_build_report_provenance.py`. Ende: `Ran 9 tests in 0.069s` / `OK` / `EXIT 0`.
- `python3 -m pytest _src/tests/test_report_freshness.py`. Ende: `No module named pytest` / `EXIT 1`. Danach dieselbe Datei über einen Stub, 19 Funktionen. Ende: `FRESHNESS_TESTS passed=19 failed=0 total=19`, `LEDGER_UNCHANGED True`, `PAGE_UNCHANGED True`.
