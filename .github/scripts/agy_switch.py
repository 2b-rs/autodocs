#!/usr/bin/env python3
"""agy mit Profilwechsel: nimmt das erste nicht gesperrte Profil und wechselt bei erschöpftem Kontingent
oder fehlender Anmeldung zum nächsten.

    agy_switch.py [--state DATEI] -- <agy-Argumente>

Profile: AUTODOCS_AGY_PROFILES (kommagetrennte HOME-Pfade aus setup-agy, Verzeichnisname agy-profile-<name>).
Zustand: JSON {name: {"cooldown_until": epoch, "needs_login": bool, "updated": epoch}}, standardmäßig
$AGY_STATE oder $RUNNER_TEMP/agy-state.json; der aufrufende Workflow trägt die Datei von Lauf zu Lauf weiter.
Mehrere gleichzeitige Aufrufe (live_distribute.py mit mehreren Arbeitsplätzen) teilen die Datei: Jede Änderung
liest den Zustand unter einer Dateisperre neu, ändert nur den Eintrag des eigenen Profils und ersetzt die Datei
atomar.

Ausgabe von agy auf stdout, eine Statuszeile "agy-switch: {...}" auf stderr (nie Token- oder Antworttext).
Exit: 0 Erfolg, 75 alle Profile erschöpft, 77 kein Profil angemeldet, sonst der Exitcode von agy.
"""
import json
import os
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:            # nur POSIX; ohne fcntl gilt die Datei wie bisher als nicht geteilt
    fcntl = None

RESET = re.compile(r"Resets in ((?:\d+h)?(?:\d+m)?(?:\d+s)?)")
EXHAUSTED = re.compile(r"RESOURCE_EXHAUSTED|quota reached|code 429", re.I)
NO_LOGIN = re.compile(r"not logged in|authentication required|please (?:log|sign) ?in|invalid_grant", re.I)


def seconds(span: str) -> int:
    total = 0
    for n, unit in re.findall(r"(\d+)([hms])", span or ""):
        total += int(n) * {"h": 3600, "m": 60, "s": 1}[unit]
    return total


def name_of(home: str) -> str:
    base = os.path.basename(home.rstrip("/"))
    return base[len("agy-profile-"):] if base.startswith("agy-profile-") else base


@contextmanager
def _locked(state_path: Path):
    lock = state_path.with_name(state_path.name + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    with open(lock, "a+") as fh:
        if fcntl:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def load_state(state_path: Path) -> dict:
    try:
        data = json.loads(state_path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def update_state(state_path: Path, name: str, entry: dict) -> dict:
    """Eintrag eines Profils setzen (unter Sperre neu lesen, atomar ersetzen); Rückgabe: aktueller Gesamtzustand."""
    with _locked(state_path):
        state = load_state(state_path)
        if entry is not None:
            state[name] = entry
        tmp = state_path.with_name(".%s.%d.tmp" % (state_path.name, os.getpid()))
        tmp.write_text(json.dumps(state, indent=1))
        os.replace(tmp, state_path)
        return state


def classify(text: str):
    """("ok"|"exhausted"|"login"|"error", Sperrdauer in s)."""
    if EXHAUSTED.search(text):
        m = RESET.search(text)
        return "exhausted", seconds(m.group(1)) if m else 3600
    if NO_LOGIN.search(text):
        return "login", 0
    return "error", 0


def main(argv):
    state_path = Path(os.environ.get("AGY_STATE") or Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "agy-state.json")
    if argv[:1] == ["--state"]:
        state_path, argv = Path(argv[1]), argv[2:]
    if argv[:1] == ["--"]:
        argv = argv[1:]
    homes = [h for h in os.environ.get("AUTODOCS_AGY_PROFILES", "").split(",") if h]
    if not homes:
        print("agy-switch: " + json.dumps({"result": "no_profiles"}), file=sys.stderr)
        return 77
    state = load_state(state_path)
    now = time.time()
    ready = [h for h in homes
             if not state.get(name_of(h), {}).get("needs_login") and state.get(name_of(h), {}).get("cooldown_until", 0) <= now]
    tried = []
    rc = 1
    for home in ready:
        name = name_of(home)
        r = subprocess.run(["agy", *argv], capture_output=True, text=True, env=dict(os.environ, HOME=home))
        rc = r.returncode
        if rc == 0:
            state = update_state(state_path, name, {"cooldown_until": 0, "needs_login": False, "updated": time.time()})
            sys.stdout.write(r.stdout)
            print("agy-switch: " + json.dumps({"profile": name, "result": "ok", "tried": tried}), file=sys.stderr)
            return 0
        kind, wait = classify(r.stdout + "\n" + r.stderr)
        tried.append({"profile": name, "result": kind, "wait_s": wait})
        if kind == "exhausted":
            state = update_state(state_path, name, {"cooldown_until": time.time() + wait, "needs_login": False,
                                                    "updated": time.time()})
        elif kind == "login":
            state = update_state(state_path, name, {"cooldown_until": 0, "needs_login": True, "updated": time.time()})
        else:                                     # anderer Fehler: nicht wechseln, Aufrufer entscheidet
            update_state(state_path, name, None)
            sys.stdout.write(r.stdout)
            print("agy-switch: " + json.dumps({"profile": name, "result": "error", "rc": rc, "tried": tried}), file=sys.stderr)
            return rc
    state = update_state(state_path, "", None)
    login = [n for n, s in state.items() if s.get("needs_login")]
    waits = {n: max(0, int(s.get("cooldown_until", 0) - time.time())) for n, s in state.items() if s.get("cooldown_until", 0) > time.time()}
    all_login = all(state.get(name_of(h), {}).get("needs_login") for h in homes)
    print("agy-switch: " + json.dumps({"result": "needs_login" if all_login else "exhausted", "tried": tried,
                                        "needs_login": login, "cooldown_s": waits}), file=sys.stderr)
    return 77 if all_login else 75


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
