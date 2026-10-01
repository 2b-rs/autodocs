# Qualifizierung des Extraction-Benchmarks (0014-05)

## Dokumentsteuerung

| Feld | Wert |
|---|---|
| Feature / Task | `0014` / `0014-05` |
| Gegenstand | Selektionswerkzeug und Fixture des Extraction-Benchmarks |
| Gemessen an | `3170be4607490cbdac3661a0dbd4eba781489d5c` |
| Fixture-Status | `draft-needs-manual-review` |
| Qualifikationsurteil | Charakterisiert. Nicht als eingefrorenes Regressionsorakel freigegeben. |

Diese Qualifizierung bindet den Benchmark an die Verifikationsstrategie aus
[SWE.4/SWE.5/SWE.6](./swe-verification-strategies.md) und an die
Konfigurationsdisziplin aus
[swe-verification-execution-evidence.md](./swe-verification-execution-evidence.md).
Sie ändert keine ECU-Produkt-Testfälle.

Maßgebliche Artefakte:

- [`_src/tools/spec_extraction_benchmark.py`](../../_src/tools/spec_extraction_benchmark.py)
- [`_src/tests/test_spec_extraction_benchmark.py`](../../_src/tests/test_spec_extraction_benchmark.py)
- [`_src/tests/fixtures/spec_extraction/benchmark-draft.json`](../../_src/tests/fixtures/spec_extraction/benchmark-draft.json)
- [`_src/tests/fixtures/spec_extraction/README.md`](../../_src/tests/fixtures/spec_extraction/README.md)
- [`_src/tests/fixtures/spec_extraction/negative-history.json`](../../_src/tests/fixtures/spec_extraction/negative-history.json)
- Katalogeintrag in [`tools.md`](./tools.md) und [`reports.md`](./reports.md)
- Aufgabenstand in [`TODO.md`](../../TODO.md): `0007-01` in Arbeit, `0007-03` offen, `0007-04` offen
- Evidenzregister [`docs/ASPICE/05-evidence-register.md`](../ASPICE/05-evidence-register.md)

## Anwendbarkeit

Der Geltungsbereich ist die Absicherung des Extraktionswerkzeugs für
Anforderungskennungen der Form `RS_<Modul>_<Ziffern>` und `SWS_<Modul>_<Ziffern>`.
Das Selektionswerkzeug erkennt beide Präfixe
(`(?:RS|SWS)_[A-Za-z0-9_]+_\d{3,}`) und übernimmt aus einer Kampagne nur
Kandidaten mit Definitionsanker. Bevorzugt wird der `pypdf`-Record, ersatzweise
ein verankerter `builtin`-Record.

Die gemessene Fixture deckt diesen Geltungsbereich nur für RS-Records ab:

| Eigenschaft | Gemessen in `benchmark-draft.json` |
|---|---|
| Schema | `1` |
| Status | `draft-needs-manual-review` |
| Kampagne | `2026-08-11-headingfix` |
| `selection_policy.target_size` | `199` |
| Records | `199`, alle Schlüssel eindeutig, alle `RS_` |
| `SWS_`-Records | `0` |
| Dokumente | `18` AUTOSAR-RS-Dokumente (Adaptive Platform und Foundation) |
| Backends je Record | immer `builtin` und `pypdf` |
| `skipped` | Schlüssel fehlt. Die Fixture bewahrt die Ausschlussliste nicht. |

SWS-Records existieren außerhalb dieser Fixture, zum Beispiel
`_src/spec/records/SWS_UCM/SWS_UCM_00351.json`. Diese Qualifizierung überträgt
keine Aussage auf die SWS-Extraktion.

Der Aufgabenwortlaut nennt einen unabhängig geprüften und eingefrorenen
200-Record-Benchmark. Der gemessene Bestand ist das nicht.
[`TODO.md`](../../TODO.md) hält `0007-03` (unabhängige Prüfung) und `0007-04`
(Einfrieren und Erzwingen als Regressionsorakel) offen. Das
[ASPICE-Evidenzregister](../ASPICE/05-evidence-register.md) führt dieselbe
Fixture als nicht eingefroren und nicht freigegeben. Commit `0ca23e0896595d38aa4926fa7d4038b791ab22cf`
hat `target_size` von 200 auf 199 gesetzt und `RS_SAF_21101` entfernt.

## Abdeckung und Grenzen der Dokumenten- und Record-Shapes

Die Kategorien stehen so in den Records. Seitenzahlen wurden gegen
`expected.pages` nachgerechnet. Feldzahlen wurden gegen `expected.fields`
nachgerechnet. `lists`, `typography`, `mixed_case_id`, `multiple_per_page` und
`empty_or_dash` wurden in dieser Qualifizierung nicht neu aus PDF-Text
abgeleitet.

| Shape | Records mit dieser Kategorie | Grenze |
|---|---:|---|
| `multi_page` | 25 | Entspricht 25 Records mit mindestens zwei verschiedenen Seiten. Spannen in der Stichprobe sind zweiseitig. |
| `single_page` | 174 | Entspricht den übrigen 174 Records. Kein Record trägt beide Seitenklassen. |
| `dense_fields` | 50 | Konstruktionsregel des Werkzeugs: mindestens fünf Felder. 14 Records haben heute mindestens fünf Felder und tragen die Kategorie nicht. |
| `lists` | 25 | Untere Auswahlgrenze des Werkzeugs. Keine Neuberechnung aus dem aktuellen Feldtext. |
| `mixed_case_id` | 25 | Untere Auswahlgrenze. Keine Neuberechnung. |
| `typography` | 115 | Über der Untergrenze. Keine Neuberechnung. |
| `empty_or_dash` | 165 | 184 Feldwerte sind leer oder einer der Striche `-`, `–`, `—`. |
| `multiple_per_page` | 192 | Fast die ganze Population. Als Trennkriterium für eine Teilauswahl unbrauchbar. |

Dokumentverteilung, gezählt aus `records[].document`:

| Dokument | Records |
|---|---:|
| `AUTOSAR_AP_RS_CommunicationManagement` | 57 |
| `AUTOSAR_AP_RS_Cryptography` | 42 |
| `AUTOSAR_AP_RS_General` | 22 |
| `AUTOSAR_FO_RS_Diagnostics` | 22 |
| `AUTOSAR_AP_RS_ExecutionManagement` | 15 |
| `AUTOSAR_FO_RS_LogAndTrace` | 12 |
| `AUTOSAR_FO_RS_E2E` | 7 |
| `AUTOSAR_AP_RS_PlatformHealthManagement` | 4 |
| `AUTOSAR_AP_RS_SafeHardwareAcceleration` | 4 |
| `AUTOSAR_AP_RS_OperatingSystemInterface` | 3 |
| `AUTOSAR_AP_RS_Persistency` | 3 |
| `AUTOSAR_FO_RS_NetworkManagement` | 2 |
| `AUTOSAR_AP_RS_StateManagement` | 1 |
| `AUTOSAR_AP_RS_UpdateAndConfigurationManagement` | 1 |
| `AUTOSAR_AP_RS_VehicleUpdateAndConfigurationManagement` | 1 |
| `AUTOSAR_FO_RS_HealthMonitoring` | 1 |
| `AUTOSAR_FO_RS_IntrusionDetectionSystem` | 1 |
| `AUTOSAR_FO_RS_TimeSync` | 1 |

Jedes der 18 Dokumente ist vertreten. Sechs Dokumente tragen genau einen
Record. Das ist Anwesenheit, keine proportionale und keine vollständige
Dokumentabdeckung.

Weitere gemessene Grenzen:

- Review: 20 Records `reviewed` durch `agent-0007-01`, 179 Records `needs_review`.
- Die 20 geprüften Records haben `expected.complete_start = true`. Die 179 ungeprüften haben `complete_start = null`. Alle 199 haben `complete_end = true`.
- Überschriften: 194 gesetzte Strings, 5 `null`.
- Feldkarten sind nie leer. Histogramm der Feldanzahl: 2 Felder bei 2 Records, 3 bei 2, 4 bei 131, 5 bei 54, 6 bei 9, 7 bei 1.
- Die 14 Records mit mindestens fünf Feldern ohne Kategorie `dense_fields` sind `RS_CM_00001`, `RS_CRYPTO_02001`, `RS_EM_00002`, `RS_AP_00111`, `RS_OSI_00100`, `RS_PHM_00101`, `RS_SHWA_00001`, `RS_SM_00001`, `RS_EM_00111`, `RS_AP_00120`, `RS_AP_00144`, `RS_OSI_00209`, `RS_DIAG_04005` und `RS_AP_00130`. Alle 14 gehören zu den 20 geprüften Records. Die Kategorien wurden nach der manuellen Feldkorrektur nicht neu geschrieben.
- Zwölf `RS_LT_*`-Records bleiben `needs_review` und tragen Notizen zur nummerierten Unterabschnittsüberschrift (Commit `fdba7e28` laut Notiz). Die Form ist im [Dossier 0007-02](../dossiers/0007-02-dense-definition-list-shape-resolution.md) als eigene Extraktionsform beschrieben. Dieses Dossier ist keine unabhängige Freigabe des Benchmarks.
- `RS_PHM_00001`, `RS_PHM_00002` und `RS_PHM_00003` sind nicht in den 199 Records. Dieselbe Negativliste liegt neben der Fixture in `negative-history.json` und gehört nicht zur 199-Population.
- `RS_SAF_21101` fehlt. Vor `0ca23e0896595d38aa4926fa7d4038b791ab22cf` lag der Record unter dem Dokumentnamen `AUTOSAR_AP_RS_PlatformHealthManagement`, mit leeren Feldern, ohne Seiten und mit den Kategorien `citation_only` und `no_definition_present`. Der Test `test_fixture_no_longer_contains_known_citation_only_entry` bindet Abwesenheit und die Länge 199.

Die Fixture-README widerspricht der JSON-Datei. Sie sagt `Selected: 200 / 200`,
`multi_page: 28`, `multiple_per_page: 194`, `typography: 111`,
`empty_or_dash: 163`, `single_page: 172` und fünf Records für
PlatformHealthManagement. Dieselben Kategoriezahlen weichen schon von der
JSON-Datei mit 200 Records vor dem Entfernen von `RS_SAF_21101` ab. Die
README ist damit weder der 200er- noch der 199er-Stand. Zählquelle dieser
Qualifizierung ist nur `benchmark-draft.json`.

Datenverlustrisiken, die diese Qualifizierung festhält:

1. Ein erneuter Lauf des Selektors über eine Kampagne schreibt
   `benchmark-draft.json` und die README neu. Dabei gehen die 20 Prüfnotizen,
   die zwölf `RS_LT`-Notizen und die manuell korrigierten Felder verloren, wenn
   die bestehende Datei ersetzt wird.
2. Die README als Zählquelle würde die entfernte Zitation `RS_SAF_21101` wieder
   in die Population rechnen und die Shape-Zahlen der JSON-Datei verfehlen.
3. `skipped` fehlt. Außer dem vom Test benannten `RS_SAF_21101` ist die Menge
   ausgeschlossener Kennungen in der Fixture nicht nachvollziehbar.
4. Die gespeicherten Kategorien `dense_fields` beschreiben nicht die aktuellen
   Feldkarten. Eine Regression, die nur die Kategorie auswertet, sieht 50 dichte
   Records. Eine Regression, die die Felder zählt, sieht 64 Records mit
   mindestens fünf Feldern.
5. 179 erwartete Feldkarten sind weiterhin `needs_review`. Sie als Wahrheit
   einzufrieren würde ungeprüfte Extraktionswerte festschreiben.
6. Der Ankerfilter verwirft Zitationen. Dieselbe Regel verwirft eine echte
   Definition, wenn kein Backend einen Anker setzt. Die Gegenrichtung hält
   einen älteren Record mit Überschrift und Feldern auch ohne Grenzflags für
   verankert (`test_legacy_populated_record_without_boundary_flags_remains_eligible`).

## Regression Selection Policy

Die Policy regelt, wann dieser Benchmark als Regressionsnachweis gewählt wird
und wann ein Lauf an diese Fixture gebunden ist.

1. **Identität vor Teilmenge.** Ein Lauf nach dieser Policy nennt den
   SHA-256 der Bytes von `benchmark-draft.json` und des Selektionswerkzeugs aus
   dem Abschnitt Benchmark-Version. Ein Lauf ohne diese beiden Hashes ist kein
   Nachweis nach dieser Qualifizierung.
2. **Population.** Die Population ist die gesamte Fixture mit 199 Records.
   `minimum_per_difficult_shape = 25` ist die Konstruktionsuntergrenze des
   Selektors für jede Kategorie außer `single_page`. Sie ist keine Erlaubnis,
   in der Regression nur 25 Records je Shape auszuführen. `multiple_per_page`
   erfüllt die Untergrenze, trennt die Population aber nicht.
3. **Auswahl des Laufs.** Änderungen an
   `_src/tools/spec_extraction_benchmark.py`,
   `_src/tests/test_spec_extraction_benchmark.py` oder
   `_src/tests/fixtures/spec_extraction/benchmark-draft.json` wählen die fünf
   Tests in `BenchmarkSelectionTests`. Änderungen außerhalb dieser Pfade
   erhalten aus diesem Benchmark keinen Regressionsnachweis.
4. **Was ein grüner Lauf zeigt.** Der ausgeführte Testlauf zeigt die
   Ankerregel, das Fehlen von `RS_SAF_21101` und die Länge 199. Er liest die
   AUTOSAR-PDFs nicht erneut und vergleicht die 199 erwarteten Feldkarten nicht
   mit den Quellen. Solange `status` den Wert `draft-needs-manual-review` hat
   und `0007-03` sowie `0007-04` offen sind, ist ein grüner Lauf kein
   freigegebenes Extraktionsorakel.
5. **Keine stillen Ersetzungen.** Eine Regenerierung, die die Fixture
   überschreibt, ist eine neue Benchmark-Version. Sie braucht einen neuen
   SHA-256, eine neue Zählung und eine eigene Qualifizierung. Die vorherige
   Version bleibt über den Git-Blob erreichbar.
6. **Ausschluss bleibt gebunden.** `RS_SAF_21101` bleibt außerhalb der
   Population. `negative-history.json` bleibt eine eigene Negativfixture und
   wird nicht in die 199 hineingezählt.
7. **Keine Produktauswahl.** Diese Policy wählt keine SWE.6-Qualifikation,
   keine VAL.1-Validierung und keinen ECU-Release-Lauf. Dafür gelten
   [swe-verification-strategies.md](./swe-verification-strategies.md),
   [swe6-qualification-execution.md](./swe6-qualification-execution.md) und
   [val1-validation-strategy.md](./val1-validation-strategy.md).

Der Selektor selbst baut eine Kandidatenliste in stabiler Dokument- und
ID-Reihenfolge: mindestens ein Record je Dokument, danach bis zu 25 je
schwieriger Shape, danach nur einseitig vorhandene Backends, danach Auffüllen
bis zur Zielgröße, danach Schnitt auf die Zielgröße. Der Prozess endet mit
Status 0, wenn die Zielgröße erreicht ist und jedes Eingabedokument mindestens
einen gewählten Record hat, sonst mit Status 2. Die abgelegte Fixture enthält
keinen nur einseitigen Backend-Record.

## Kontrollierte Ausführungsumgebung

Die automatische Prüfung dieser Qualifizierung ist ein lokaler Lauf der
Standardbibliothek. Werkzeug und Test importieren keine Drittmodule.

| Bestandteil | Gemessener Wert |
|---|---|
| Betriebssystem | Darwin 22.6.0, x86_64 |
| Interpreter | Python 3.14.7, Executable `/usr/local/opt/python@3.14/bin/python3.14`, aufgerufen als `/usr/local/bin/python3` |
| Arbeitsbaum | dieser Task-Worktree, HEAD `3170be4607490cbdac3661a0dbd4eba781489d5c` |
| Befehl | `python3 -m unittest _src.tests.test_spec_extraction_benchmark -v` |
| Ergebnis | `Ran 5 tests in 0.174s`, `OK` |
| pytest | `python3 -m pytest --version` endet mit `No module named pytest` |

Der historische Befehl im
[Dossier 0007-02](../dossiers/0007-02-dense-definition-list-shape-resolution.md)
(`pytest` über Kampagnen- und Benchmark-Tests, 16 bestanden) wurde hier nicht
erneut ausgeführt. pytest ist in diesem Interpreter nicht vorhanden.

Die fünf Tests legen eine hermetische Zwei-Record-Kampagne in einem temporären
Verzeichnis an und lesen die Fixture nur für Länge und Abwesenheit von
`RS_SAF_21101`. Sie starten kein Netz, kein PDF-Werkzeug und keine
Abhängigkeitssperre. [`toolchain-dependency-pinning.md`](./toolchain-dependency-pinning.md)
beschreibt die allgemeine Pin-Pflicht für Verifikationsumgebungen. Dieser Lauf
hat keine `requirements.txt`- oder Lock-Datei als Eingabe verwendet. Die
Umgebung ist damit für den Ankertest kontrolliert und für eine
PDF-Neuextraktion nicht ausreichend.

Der Testprozess schreibt zusätzlich die JSON-Zusammenfassung des Selektors für
die hermetische Kampagne auf die Standardausgabe (`selected: 2`). Das gehört
zum Werkzeug und ist kein zweites Testergebnis.

## Benchmark-Version und SHA-256

Version im Fixture-Objekt:

- `schema`: `1`
- `status`: `draft-needs-manual-review`
- `campaign`: `2026-08-11-headingfix`
- `selection_policy.target_size`: `199`
- `selection_policy.minimum_per_difficult_shape`: `25`
- `selection_policy.requires_definition_anchor`: `true`
- Git-Revision der Messung: `3170be4607490cbdac3661a0dbd4eba781489d5c`
- Letzte inhaltsändernde Revision der JSON-Fixture in dieser Historie: `0ca23e0896595d38aa4926fa7d4038b791ab22cf`

SHA-256 der Dateibytes, hexadezimal, ohne Präfix. Neu berechnet in dieser
Qualifizierung mit `hashlib.sha256` über die gelesenen Bytes:

| Pfad | Bytes | SHA-256 |
|---|---:|---|
| `_src/tests/fixtures/spec_extraction/benchmark-draft.json` | 261603 | `5144b0af0c374b73fd7ee4fa5abb7b25c9fd061f9f4dc4e4aedc01c5e8604de8` |
| `_src/tests/fixtures/spec_extraction/README.md` | 1018 | `6d0641682349b4d658524f8b58f8b3ebf2f3332e08002540f420a489204dc6fd` |
| `_src/tests/fixtures/spec_extraction/negative-history.json` | 19883 | `156485f1ad90bd576f8ed84102f29dd5b00548cac42e50034efcc55eed7e3a1d` |
| `_src/tools/spec_extraction_benchmark.py` | 7911 | `6a3ff48c089f3ddc2b6a4cdf957cc495c161fff209f66d8394d5fbfb584813fb` |
| `_src/tests/test_spec_extraction_benchmark.py` | 3338 | `20c24a38569b7a09cb20eeb26e55324d06d71a064c450ca4f9354c66db8638c9` |

Git-Blob-IDs derselben Pfade an der gemessenen Revision, verschieden vom
SHA-256 der Dateibytes, weil Git den Blob-Header mit hasht:

| Pfad | Git-Blob |
|---|---|
| `_src/tests/fixtures/spec_extraction/benchmark-draft.json` | `b29a62054f94e2425485bc3473306041dd48081b` |
| `_src/tests/fixtures/spec_extraction/README.md` | `49433560aff01d4660556246db38233d385d85a9` |
| `_src/tools/spec_extraction_benchmark.py` | `32d83bf60ff3cfdb62e6a2240dd3ba7681e1e420` |
| `_src/tests/test_spec_extraction_benchmark.py` | `cb475aae8dd5d8ea5097dc09272e96decf33065f` |

Ein späterer Commit, der nur diese Qualifizierung ergänzt, ändert die fünf
Hashes nicht. Ändert sich ein Byte der Fixture oder des Werkzeugs, gilt der
alte Hash nicht mehr für den neuen Lauf.

## Abgrenzung zur ECU-Produktverifikation

Der Benchmark dient der Werkzeug- und Extraktionsabsicherung und ist keine ECU-Produktverifikation.

Ein grüner Ankertest und eine charakterisierte 199-Record-Fixture belegen
nicht, dass eine ECU-Software ihre Software-Anforderungen erfüllt, nicht, dass
SWE.6-Qualifikation oder VAL.1 ausgeführt wurde, und nicht, dass ein
Release-Nachweis nach
[vvr-verification-validation-qa-summary.md](./vvr-verification-validation-qa-summary.md)
vorliegt. ECU-Produktprüfungen bleiben in den dort genannten Strategien und
Ausführungsnachweisen. Diese Datei nimmt keinen dieser Nachweise auf und ändert
keine ECU-Produkt-Testfälle.

## Ergebnis und verbleibende Lücken

Die Qualifizierung definiert Anwendbarkeit, gemessene Shape- und
Dokumentgrenzen, die Regressionsauswahl, die tatsächlich benutzte
Ausführungsumgebung und die Version mit SHA-256. Das Urteil lautet:
charakterisierter Entwurf, nicht freigegebenes Orakel.

Offen bleibt, was diese Aufgabe nicht herstellen kann, ohne `0007-03` und
`0007-04` zu ersetzen:

- unabhängige Prüfung der 179 noch nicht geprüften Records
- Einfrieren und Erzwingen der Fixture als Extraktionsorakel
- Angleichen der Fixture-README an die 199 JSON-Records
- Nachziehen der Kategorie `dense_fields` an die aktuellen Feldkarten
- Aufnehmen einer SWS-Population, falls SWS-Extraktion mit demselben Maß
  abgesichert werden soll
- erneutes Lesen der Quell-PDFs in dieser Umgebung
- privilegierte Abnahme von Task `0014-05` und aggregierter Abschluss von
  Feature `0014` nach [`task-acceptance.md`](./task-acceptance.md)
