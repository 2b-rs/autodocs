# Arbeitsregeln für Automatisierung und KI-Agenten

Diese Datei richtet sich an automatisierte Werkzeuge und KI-Agenten, die im
Projekt arbeiten. Sie ist keine Anleitung für die Nutzung oder Veröffentlichung
der API-Referenz.

## Way of Working
- Never attempt to install software, download anything, or run a headless browser directly through MCP. Every operation that requires internet access, needs to write anywhere outside the project directory, or is expected to consume significant CPU must be performed as follows: Put the necessary commands into a command script called "run.sh" into the directory where this file resides. It will be executed automatically, so then keep checking the existence of the file until it disappears. Keep trying for at least as long as the expected runtime of the script is. After that, inspect the output of the command in output/run-current.log.
- Keep the contents and runtime of commands executed via run.sh as small as possible. Local commands and simple file read operations can generally performed directly via MCP.
- If a run.sh is needed, describe the task comprehensively. Let the script echo to stdout: 1. A one-line title, containing CPU LOAD, INTERNET ACCESS, SW INSTALLATION or whatever was the reason. 2. A short summary what the script is supposed to do, 3. A detailed explanation of the hierarchy of goals in which it was created. 4. Expected "volume" - an estimate of how much internet data will be downloaded, the number of files and packages to be installed, the amount of CPU runtime and tne number of worker processes that is expected.
- Include continuous output of progress information for run.sh. Console output is required at least once every 5s, so that the person running the script can see that it isn't stuck.
- Always keep working towards the task's goal as long as possible. DON'T STOP WORKING just because a minor issue came into the way. DON'T ASK BACK TO THE USER unless reaching the goal has clearly become impossible.
- Be THOROUGH, FACTUAL, PRECISE, and CONCISE in your reports.
- Be HONEST. Report if something is unclear or you simply don't know.

## Generierte Inhalte

Der HTML-Tree ist ein Build-Artefakt. Inhaltliche Änderungen gehören nach
`_src/`; danach neu generieren und validieren:

```bash
python3 _src/generate.py && python3 _src/validate.py
```

Weiterführende Projektinformationen stehen in [`README.md`](README.md) sowie
in [`_src/WARTUNG.md`](_src/WARTUNG.md).
