# Auftrag: Multi-Release Supersession & Delta Evolution Reporting Tool

## Ziel
Entwickle das Werkzeug `_src/tools/multi_release_report.py` und die zugehörige Test-Suite `_src/tests/test_multi_release_report.py`, um den Versions-Verlauf und Revisions-Deltas zwischen zwei beliebigen AUTOSAR-Releases (z. B. R20-11 und R25-11) zusammenzufassen.

## Umfang
1. Implementierung von `_src/tools/multi_release_report.py`:
   - Funktion `generate_release_report(from_release: str, to_release: str, platform: str = None) -> dict`:
     - Ermittelt alle Anforderungen, die im Ausgangs-Release vorhanden waren.
     - Ermittelt alle Anforderungen, die im Ziel-Release vorhanden sind.
     - Kategorisiert in `added` (neu hinzugekommen), `modified` (Inhalt/Syntax geändert), `unchanged` (identischer Hash), `deprecated_or_removed`.
   - CLI-Schnittstelle:
     `python3 _src/tools/multi_release_report.py --from <REL> --to <REL> [--platform AP|CP] [--json]`
     Gibt formatierte Text-Zusammenfassung oder strukturiertes JSON aus.
2. Implementierung von `_src/tests/test_multi_release_report.py`:
   - Mindestens 3 Testmethoden zur Verifikation der Delta-Erkennung, Kategorisierung und CLI-Ausgabe.

## Nicht im Umfang
- Keine Änderungen an `serve.py` oder HTML-Templates.

## Erlaubte Dateien
- Neu anlegen: `_src/tools/multi_release_report.py`, `_src/tests/test_multi_release_report.py`
- Ändern erlaubt: keine

## Abnahme (Orakel)
- `python3 -m unittest _src/tests/test_multi_release_report.py` läuft vollständig grün mit mindestens 3 Testmethoden (Exit-Code 0).
- `python3 _src/tools/multi_release_report.py --from R20-11 --to R25-11 --platform CP` erzeugt einen validen Bericht mit Exit-Code 0.

## Projektregeln
- Alle Befehle mit `rtk` prefixen.
- Python 3.14 kompatibler Code.
- Saubere Commits mit aussagekräftiger Message.
