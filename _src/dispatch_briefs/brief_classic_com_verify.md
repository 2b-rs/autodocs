# Auftrag: Classic COM Multi-Release Verification & Test Suite

## Ziel
Erstelle eine umfassende Test-Suite `_src/tests/test_classic_multi_release.py`, die die Multi-Release-Versionierung von AUTOSAR Classic COM Spezifikationselementen (z. B. SWS_Com_00001 bis SWS_Com_00015) über alle Releases (R19-11, R20-11, R21-11, R22-11, R25-11) im unveränderlichen Versions-Store (_src/spec/versions/AUTOSAR/CP/record/) verifiziert.

## Umfang
1. Test der Existenz und Struktur der generierten JSONL-Dateien unter `_src/spec/versions/AUTOSAR/CP/record/SWS_Com_*.jsonl`.
2. Test von `asof_view.as_of_release` für mehrere historische Releases (z. B. R20-11 vs. R25-11) für `AUTOSAR/CP/record/SWS_Com_00001`: Verifikation, dass unterschiedliche Releases den jeweils korrekten historischen Text und die korrekte Version-ID liefern.
3. Test von `delta_view.delta_view` mit Baseline R20-11: Verifikation, dass veränderte Classic-Requirements korrekt in `changed_requirements` aufgeführt werden.
4. Test der kanonischen Namensraum- und ID-Konventionen (`AUTOSAR/CP/record/...`).

## Nicht im Umfang
- Keine Änderungen an der Dokumenten-Generierung (`generate.py`) oder HTML-Templates.
- Keine Änderungen am Preview-Server (`serve.py`).

## Erlaubte Dateien
- Neu anlegen: `_src/tests/test_classic_multi_release.py`
- Ändern erlaubt: keine

## Abnahme (Orakel)
- `python3 -m unittest _src/tests/test_classic_multi_release.py` läuft vollständig grün mit mindestens 4 Testmethoden (Exit-Code 0).

## Projektregeln
- Alle Befehle mit `rtk` prefixen.
- Python 3.14 kompatibler Code.
- Saubere Commits mit aussagekräftiger Message.
