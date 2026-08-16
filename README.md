# ara::* API-Referenz — AUTOSAR Adaptive Platform R25-11

Der HTML-Tree in diesem Verzeichnis ist ein **generiertes Build-Artefakt**.
Inhalte bitte nicht direkt im HTML ändern, sondern in den Quellen unter
[`_src/`](_src/) — danach den Tree neu generieren:

```bash
python3 _src/generate.py && python3 _src/validate.py
```

- Anleitung: [`_src/WARTUNG.md`](_src/WARTUNG.md)
- Konventionen: [`_src/KONVENTIONEN.md`](_src/KONVENTIONEN.md)
- Arbeitsregeln für Automatisierung und KI-Agenten: [`AGENTS.md`](AGENTS.md)

Einstieg in die Dokumentation: [`index.html`](index.html)
Issues und offene Punkte: TODO.md

## Veröffentlichung

Die generierte HTML-Dokumentation ist derzeit über GitHub Pages veröffentlicht:

<https://2b-rs.github.io/autodocs/>

Wichtig: Der GitHub-Link `https://github.com/2b-rs/autodocs/blob/main/index.html` zeigt die Datei nur innerhalb der GitHub-Oberfläche. Für die Doku selbst immer die GitHub-Pages-URL oben verwenden.

Das öffentliche Deploy-Repository `2b-rs/autodocs` enthält ausschließlich die gebauten HTML-, CSS- und Asset-Dateien. Die lokalen Quellen und Build-Werkzeuge unter `_src/` werden nicht dorthin übertragen. Ausgeliefertes HTML, CSS und clientseitiges JavaScript bleiben jedoch grundsätzlich im Browser beziehungsweise im öffentlichen Deploy-Artefakt einsehbar.
