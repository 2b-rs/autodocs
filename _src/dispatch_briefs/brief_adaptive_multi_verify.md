# Auftrag: Adaptive Platform Multi-Release Version Integrity & Schema Audit

## Ziel
Erstelle eine umfassende Test-Suite `_src/tests/test_adaptive_multi_release.py`, die die Multi-Release-Versionierung und Datenintegrität der AUTOSAR Adaptive Platform Spezifikationselemente im Versions-Store (`_src/spec/versions/AUTOSAR/AP/record/`) sowie das Zusammenspiel mit dem Dokumentenmodell (`lib_docmodel.py`) validiert.

## Umfang
1. Test der JSONL-Integrität in `_src/spec/versions/AUTOSAR/AP/record/`: Jede Zeile muss ein valides JSON-Objekt sein mit den Pflichtfeldern `version_id`, `canonical_id`, `release`, `content`, `recorded_at`.
2. Test der Idempotenz: Mehrfaches Aufzeichnen identischer Versionen darf keine Duplikate im Store erzeugen.
3. Test des Renderings in `lib_docmodel._render_rec_history_html`: Verifikation, dass für Records mit Versionen im Store die Revisions-Timeline (`.rec-version-timeline`) und die Versions-Badge (`.rec-version-badge`) korrekt mit den echten Version-IDs erzeugt werden.
4. Test von `asof_view.as_of_release` und `asof_view.as_of_date` für Adaptive-Elemente (z. B. SWS_CORE_00017 oder SWS_AIDSM_10706).

## Nicht im Umfang
- Keine Änderungen an `lib_docmodel.py` oder HTML-Templates.
- Keine Änderungen an `_src/serve.py`.

## Erlaubte Dateien
- Neu anlegen: `_src/tests/test_adaptive_multi_release.py`
- Ändern erlaubt: keine

## Abnahme (Orakel)
- `python3 -m unittest _src/tests/test_adaptive_multi_release.py` läuft vollständig grün mit mindestens 4 Testmethoden (Exit-Code 0).

## Projektregeln
- Alle Befehle mit `rtk` prefixen.
- Python 3.14 kompatibler Code.
- Saubere Commits mit aussagekräftiger Message.
