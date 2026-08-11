# Arbeitsregeln für Automatisierung und KI-Agenten

Diese Datei richtet sich an automatisierte Werkzeuge und KI-Agenten, die im
Projekt arbeiten. Sie ist keine Anleitung für die Nutzung oder Veröffentlichung
der API-Referenz.

## Script execution
- NEVER attempt to install software, download anything, write to the user's home directory, or run a headless browser directly through MCP. Every operation that requires internet access, needs to write anywhere outside the project directory, or is expected to consume significant CPU must be performed as follows: Put the necessary commands into a command script called "run.sh" into the directory where this file resides and YIELD IMMEDIATELY. The script will be executed by me and I will inform you about the result. I will redirect the script's output into output/run-current.log.
- Try to offload as much work as possible this way. Use script-level parallelism where possible. You have 10 CPUs. Don't run any process using 'nice'.
- At the beginning of the script, DESCRIBE THE JOB COMPREHENSIVELY. Echo to stdout:
  1. A one-line title containing the Purpose, e.g. CPU OFFLOADING, DOWNLOAD, or SW INSTALLATION.
  2. A short summary of the script's structure,
  3. A detailed explanation of your goal hierarchy
  4. An estimate of how much data traffic, cpu load, number of workers, or wall clock time will be needed for completion.
- The script shall continuously inform about its progress, at least once every 5s.

## Way of collaboration
- ALWAYS WORK TOWARDS THE GOAL as possible. KEEP GOING unless the goal has clearly become unreachable.
- If the user's intention is not 100% clear, DON'T ASK BACK, but make a best-guess of his preferences. Document your decisions and what you have achieved after completion.
- Be THOROUGH, FACTUAL, PRECISE, CONCISE, and HONEST.
- Find an open task list in NEXTSTEPS.md. Keep track of your goals there. After you've completed a task, mark it as done in NEXTSTEPS.md or delete it. Don't remove unfinished items.
- Once you have completed a piece of work and are confident of the results, check it in.

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
