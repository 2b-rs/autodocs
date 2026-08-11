# Arbeitsregeln für Automatisierung und KI-Agenten

Diese Datei richtet sich an automatisierte Werkzeuge und KI-Agenten, die im
Projekt arbeiten. Sie ist keine Anleitung für die Nutzung oder Veröffentlichung
der API-Referenz.

## Script execution / MCP
- DO NOT EXECUTION SCRIPTS VIA MCP.

  Instead, put the necessary commands into a command script called "run.sh" in the project's root directory and YIELD. run.sh will be executed manually and get back to you. You will find its stdout+stderr in output/run-current.log.

- NEVER attempt to install software, download anything, write to the user's home directory, or run a headless browser through MCP. Internet access, writing outside /tmp, and anything that causes high CPU usage will be blocked by the sandbox. Therefore, all of these operations MUST be performed through the run.sh mechanism explained above.

- if any other MCP operation fails, report this verbatim and YIELD.

- Combine as much work as possible in each single call to run.sh. You can e.g. grep into multiple output streams under /tmp/output/, run multiple screenshot-tools in parallel etc. You may spawn up to 12 jobs in parallel.

- At the beginning of run.sh, DESCRIBE THE PURPOSE. Echo to stdout:
  1. A one-line title containing the Purpose, e.g. CPU OFFLOADING, DOWNLOAD, or SW INSTALLATION.
  2. A short summary of run.sh's structure,
  3. A detailed explanation of your goal hierarchy
  4. An estimate of how much data traffic, cpu load, number of workers, or wall clock time will be needed for completion.
- Have run.sh output progress information on a regular basis, at least once every 5s.

## Way of collaboration
- ALWAYS KEEP GOING as long as possible, i.e. until the goal is reached or it has clearly become unreachable.
- If the user's intention is not 100% clear, DON'T ASK BACK. Make a best-guess of his preferences and document your decisions.
- Be THOROUGH, FACTUAL, PRECISE, CONCISE, and HONEST.
- Whenever you complete a piece of work:
  1. check the box in TODO.md.
  2. check it into the local git. Use the user's email adress as the author.
  2. pick up the next piece of work from TODO.md and KEEP GOING.

## MCP-Sandbox: Schreibzugriffe

Beschreibbar sind `/tmp` und das Projektverzeichnis (inkl. `_src/`). Blockiert
sind das Home-Verzeichnis, Netzzugriff und Schreibvorgänge ausserhalb dieser
Bereiche. Die Sandbox prüft das **gesamte** Kommando vorab: Ein einziger
unzulässiger Pfad bricht den kompletten Aufruf ab, auch wenn der restliche Teil
zulässig wäre.

Zwei Stolperfallen, die dabei regelmässig unbemerkt zuschlagen:

- `TMPDIR` zeigt standardmässig auf `/var/folders/…`, also nach draussen. Jede
  Nutzung von `tempfile` scheitert damit.
- `python3 -m py_compile` schreibt `__pycache__` neben die Quelldatei.

Deshalb jedem Kommando voranstellen:

```bash
export TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1
```

Für Syntaxprüfungen `ast.parse()` verwenden oder das Ziel explizit setzen:
`py_compile.compile(src, cfile="/tmp/x.pyc", doraise=True)`.

## Generierte Inhalte

Der HTML-Tree ist ein Build-Artefakt. Inhaltliche Änderungen gehören nach
`_src/`; danach neu generieren und validieren:

```bash
python3 _src/generate.py && python3 _src/validate.py
```

Weiterführende Projektinformationen stehen in [`README.md`](README.md) sowie
in [`_src/WARTUNG.md`](_src/WARTUNG.md).
