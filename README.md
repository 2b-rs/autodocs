# autodocs

Öffentliche Website von autodocs, einer mehrsprachigen Architektur- und API-Referenz
für AUTOSAR Adaptive, AUTOSAR Classic und Eclipse S-Core.

Website: <https://2b-rs.github.io/autodocs/>

Dieses Repository enthält nur die fertig erzeugte Website und die Skripte, die
GitHub Actions braucht. Die Seiten werden außerhalb dieses Repositorys erzeugt
und hier unverändert eingecheckt; GitHub Pages liefert den Zweig `main` aus. Änderungen am HTML dieses Repositorys werden
beim nächsten Stand überschrieben.

## Inhalt

- `index.html`, `404.html`, `site.json`, `style.css` und die Skripte im Wurzelverzeichnis
- `de/`, `en/`, `es/`, `fr/`, `pt/`, `ru/`, `ar/`, `hi/`, `ko/`, `zh/`, `nl/`: Seiten je Sprache
- `spec/`: Aufruf einzelner Anforderungen (`spec/record.html?id=…`)
- `versions/`: Versionskatalog und Anforderungsdatensätze für den Provenienz-Browser
- `static/`, `flags/`: gemeinsam genutzte Skripte und Flaggen
- `ai/traces/`: Herkunftsnachweise der KI-Texte (Modell, Effort, Prompt- und Ausgabe-Hash)
- `.github/workflows/agy-smoke.yml`, `.github/actions/setup-agy/`, `.github/scripts/agy_switch.py`:
  Rauchtest der Antigravity-CLI auf dem Runner

## Rückmeldungen

Hinweise zu Inhalten bitte als Issue in diesem Repository oder über die Prüffunktion der Website.
