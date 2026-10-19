#!/usr/bin/env python3
"""agy mit Profilwechsel: nimmt das erste nicht gesperrte Profil und wechselt bei erschöpftem Kontingent
oder fehlender Anmeldung zum nächsten.

    agy_switch.py [--state DATEI] -- <agy-Argumente>

Profile: AUTODOCS_AGY_PROFILES (kommagetrennte HOME-Pfade aus setup-agy, Verzeichnisname agy-profile-<name>).
Zustand: JSON {name: {"cooldown_until": epoch, "needs_login": bool, "updated": epoch,
"in_flight": {"call_id", "started", "lease_until"} | null,
"last_call": {"call_id", "result", "ended"} | null}}, standardmäßig
$AGY_STATE oder $RUNNER_TEMP/agy-state.json; der aufrufende Workflow trägt die Datei von Lauf zu Lauf weiter.
Mehrere gleichzeitige Aufrufe (live_distribute.py mit mehreren Arbeitsplätzen) teilen die Datei: Jede Änderung
liest den Zustand unter einer Dateisperre neu, ändert nur den Eintrag des eigenen Profils und ersetzt die Datei
atomar. Vor dem Providerstart wird ein eindeutiger Aufruf (AGY_CALL_ID oder neu) zusammen mit dem gewählten
Profil als in-flight-Lease geschrieben. Ein äußerer Timeout markiert genau diesen Aufruf als timeout und setzt
eine endliche Abkühlung; abgelaufene Leases nach einem Elternabsturz werden ebenfalls endlich abgekühlt und
nicht sofort wiederverwendet. Es gibt keinen Timeout-Retry und keine zweite Provider-Invocation.

Ausgabe von agy auf stdout, eine Statuszeile "agy-switch: {...}" auf stderr (nie Token- oder Antworttext).
Exit: 0 Erfolg, 75 alle nutzbaren Profile nachweislich quotenerschöpft, 76 Profile nur vorübergehend belegt
oder in endlicher Timeout-Abkühlung, 77 kein Profil angemeldet, sonst der Exitcode von agy.
"""
import json
import os
import re
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:            # nur POSIX; ohne fcntl gilt die Datei wie bisher als nicht geteilt
    fcntl = None

RESET = re.compile(r"Resets in ((?:\d+h)?(?:\d+m)?(?:\d+s)?)")
EXHAUSTED = re.compile(r"RESOURCE_EXHAUSTED|quota reached|code 429", re.I)
NO_LOGIN = re.compile(r"not logged in|authentication required|please (?:log|sign) ?in|invalid_grant", re.I)
CALL_ID_RE = re.compile(r"^[0-9a-f]{8,64}$")
# Endliche Abkühlung nach Timeout bzw. verwaistem Lease; kein Retry und keine Provider-Timeout-Änderung.
TIMEOUT_COOLDOWN_S = 300
# Standard-Lease deckt den äußeren Wait (call_timeout + 60) des Live-Jobs.
DEFAULT_LEASE_S = 360
# Ein belegtes Profil kann vor Ablauf seines Leases frei werden. In diesem Fall
# kurz pollen; reine Timeout-Abkühlungen haben dagegen einen bekannten Termin.
BUSY_POLL_S = 1.0
STATUS_KEYS = ("profile", "call_id", "result", "tried", "wait_s", "rc", "needs_login", "cooldown_s",
               "cooldown_until")


def seconds(span: str) -> int:
    total = 0
    for n, unit in re.findall(r"(\d+)([hms])", span or ""):
        total += int(n) * {"h": 3600, "m": 60, "s": 1}[unit]
    return total


def name_of(home: str) -> str:
    base = os.path.basename(home.rstrip("/"))
    return base[len("agy-profile-"):] if base.startswith("agy-profile-") else base


def new_call_id() -> str:
    return uuid.uuid4().hex


def valid_call_id(value) -> str:
    text = str(value or "")
    return text if CALL_ID_RE.fullmatch(text) else ""


def _now() -> float:
    return time.time()


def _cooldown_s(value=None) -> float:
    if value is not None:
        return max(0.0, float(value))
    raw = os.environ.get("AGY_TIMEOUT_COOLDOWN_S")
    try:
        return max(0.0, float(raw)) if raw else float(TIMEOUT_COOLDOWN_S)
    except (TypeError, ValueError):
        return float(TIMEOUT_COOLDOWN_S)


def _lease_s(value=None) -> float:
    if value is not None:
        return max(1.0, float(value))
    raw = os.environ.get("AGY_LEASE_S")
    try:
        return max(1.0, float(raw)) if raw else float(DEFAULT_LEASE_S)
    except (TypeError, ValueError):
        return float(DEFAULT_LEASE_S)


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


def _write_state(state_path: Path, state: dict) -> None:
    tmp = state_path.with_name(".%s.%d.tmp" % (state_path.name, os.getpid()))
    tmp.write_text(json.dumps(state, indent=1))
    os.replace(tmp, state_path)


def mutate_state(state_path: Path, fn):
    """Zustand unter Sperre lesen, ändern, atomar ersetzen. fn(state) -> extra; Rückgabe (state, extra)."""
    with _locked(state_path):
        state = load_state(state_path)
        extra = fn(state)
        _write_state(state_path, state)
        return load_state(state_path), extra


def update_state(state_path: Path, name: str, entry: dict) -> dict:
    """Eintrag eines Profils setzen (unter Sperre neu lesen, atomar ersetzen); Rückgabe: aktueller Gesamtzustand."""
    def fn(state):
        if name and entry is not None:
            state[name] = entry
        return None
    state, _ = mutate_state(state_path, fn)
    return state


def classify(text: str):
    """("ok"|"exhausted"|"login"|"error", Sperrdauer in s)."""
    if EXHAUSTED.search(text):
        m = RESET.search(text)
        return "exhausted", seconds(m.group(1)) if m else 3600
    if NO_LOGIN.search(text):
        return "login", 0
    return "error", 0


def _entry(state: dict, name: str) -> dict:
    cur = state.get(name)
    return dict(cur) if isinstance(cur, dict) else {}


def recover_stale_in_state(state: dict, now: float, cooldown_s: float) -> list:
    """Abgelaufene in-flight-Leases endliche Abkühlung geben; kein sofortiges Wiederverwenden, kein Dauerbusy."""
    recovered = []
    for name, cur in list(state.items()):
        if not isinstance(cur, dict):
            continue
        inflight = cur.get("in_flight") or None
        if not isinstance(inflight, dict):
            continue
        try:
            lease_until = float(inflight.get("lease_until") or 0)
        except (TypeError, ValueError):
            lease_until = 0.0
        if lease_until > now:
            continue
        call_id = valid_call_id(inflight.get("call_id"))
        entry = dict(cur)
        entry["in_flight"] = None
        entry["cooldown_until"] = now + cooldown_s
        entry["needs_login"] = bool(entry.get("needs_login"))
        entry["updated"] = now
        last = {"call_id": call_id, "result": "timeout", "ended": now}
        if call_id:
            last["recovered"] = True
        entry["last_call"] = last
        state[name] = entry
        recovered.append(name)
    return recovered


def recover_stale(state_path: Path, now: float = None, cooldown_s: float = None) -> dict:
    now = _now() if now is None else now
    cooldown_s = _cooldown_s(cooldown_s)
    state, recovered = mutate_state(state_path, lambda st: recover_stale_in_state(st, now, cooldown_s))
    return {"recovered": recovered, "state": state}


def _ready(entry: dict, now: float) -> bool:
    if entry.get("needs_login"):
        return False
    try:
        cool = float(entry.get("cooldown_until") or 0)
    except (TypeError, ValueError):
        cool = 0.0
    if cool > now:
        return False
    inflight = entry.get("in_flight") or None
    if isinstance(inflight, dict):
        try:
            lease_until = float(inflight.get("lease_until") or 0)
        except (TypeError, ValueError):
            lease_until = 0.0
        if lease_until > now:
            return False
    return True


def acquisition_status(state: dict, homes, now: float = None) -> dict:
    """Explain why no profile can currently be leased without conflating it with quota exhaustion.

    Only an explicit ``last_call.result == exhausted`` is quota evidence.  A live lease, a timeout cooldown,
    and legacy/ambiguous cooldown state are temporary.  The caller can therefore wait and retry acquisition
    without repeating a provider invocation.
    """
    now = _now() if now is None else now
    login = []
    quota = []
    temporary = []
    waits = []
    busy = False
    names = [name_of(home) for home in homes if name_of(home)]
    for name in names:
        entry = _entry(state, name)
        if entry.get("needs_login"):
            login.append(name)
            continue
        inflight = entry.get("in_flight") if isinstance(entry.get("in_flight"), dict) else {}
        try:
            lease_until = float(inflight.get("lease_until") or 0)
        except (TypeError, ValueError):
            lease_until = 0.0
        if lease_until > now:
            temporary.append(name)
            waits.append(lease_until - now)
            busy = True
            continue
        try:
            cooldown_until = float(entry.get("cooldown_until") or 0)
        except (TypeError, ValueError):
            cooldown_until = 0.0
        if cooldown_until > now:
            last = entry.get("last_call") if isinstance(entry.get("last_call"), dict) else {}
            if last.get("result") == "exhausted":
                quota.append(name)
            else:
                temporary.append(name)
                waits.append(cooldown_until - now)

    if names and len(login) == len(names):
        return {"result": "needs_login", "needs_login": login, "wait_s": 0.0}
    if temporary:
        wait_s = min(waits) if waits else BUSY_POLL_S
        if busy:
            wait_s = min(wait_s, BUSY_POLL_S)
        return {"result": "unavailable", "needs_login": login,
                "wait_s": max(0.05, float(wait_s))}
    non_login = [name for name in names if name not in login]
    if non_login and all(name in quota for name in non_login):
        return {"result": "exhausted", "needs_login": login, "wait_s": 0.0}
    # A profile became ready between the failed lease attempt and this snapshot,
    # or the persisted legacy state is incomplete.  Neither is quota evidence.
    return {"result": "unavailable", "needs_login": login, "wait_s": 0.05}


def acquire_lease(state_path: Path, homes, call_id: str, now: float = None, lease_s: float = None,
                  cooldown_s: float = None) -> dict:
    """Erstes bereites Profil atomar belegen. Stale-in-flight wird endlich abgekühlt, nicht sofort genommen."""
    now = _now() if now is None else now
    lease_s = _lease_s(lease_s)
    cooldown_s = _cooldown_s(cooldown_s)
    call_id = valid_call_id(call_id) or new_call_id()

    def fn(state):
        recover_stale_in_state(state, now, cooldown_s)
        for home in homes:
            name = name_of(home)
            if not name:
                continue
            entry = _entry(state, name)
            if not _ready(entry, now):
                continue
            entry["in_flight"] = {"call_id": call_id, "started": now, "lease_until": now + lease_s}
            entry["updated"] = now
            entry.setdefault("cooldown_until", 0)
            entry.setdefault("needs_login", False)
            state[name] = entry
            return {"profile": name, "call_id": call_id, "result": "selected"}
        return None

    state, leased = mutate_state(state_path, fn)
    if not leased:
        return {"result": "none", "state": state, "call_id": call_id}
    leased["state"] = state
    return leased


def complete_call(state_path: Path, name: str, call_id: str, result: str, wait_s: float = 0,
                  now: float = None, cooldown_s: float = None) -> dict:
    """Lease nur schließen, wenn call_id noch in-flight ist — kein Überschreiben einer Timeout-Attribution."""
    now = _now() if now is None else now
    cooldown_s = _cooldown_s(cooldown_s)
    call_id = valid_call_id(call_id)

    def fn(state):
        entry = _entry(state, name)
        inflight = entry.get("in_flight") if isinstance(entry.get("in_flight"), dict) else {}
        if not call_id or inflight.get("call_id") != call_id:
            kept = (entry.get("last_call") or {}) if isinstance(entry.get("last_call"), dict) else {}
            return {"profile": name, "call_id": call_id, "result": "conflict",
                    "kept": kept.get("result")}
        entry["in_flight"] = None
        entry["updated"] = now
        last = {"call_id": call_id, "result": result, "ended": now}
        entry["last_call"] = last
        if result == "exhausted":
            entry["cooldown_until"] = now + max(0.0, float(wait_s or 0))
            entry["needs_login"] = False
        elif result == "login":
            entry["cooldown_until"] = 0
            entry["needs_login"] = True
        elif result == "timeout":
            entry["cooldown_until"] = now + cooldown_s
            entry["needs_login"] = False
        elif result == "ok":
            entry["cooldown_until"] = 0
            entry["needs_login"] = False
        state[name] = entry
        return {"profile": name, "call_id": call_id, "result": result,
                "cooldown_until": entry.get("cooldown_until", 0)}

    state, extra = mutate_state(state_path, fn)
    extra = extra or {}
    extra["state"] = state
    return extra


def attribute_timeout(state_path: Path, call_id: str, now: float = None, cooldown_s: float = None) -> dict:
    """Genau den in-flight-Aufruf als timeout markieren und die Attribution zurücklesen."""
    now = _now() if now is None else now
    cooldown_s = _cooldown_s(cooldown_s)
    call_id = valid_call_id(call_id)
    if not call_id:
        return {}

    def fn(state):
        for name, cur in list(state.items()):
            if not isinstance(cur, dict):
                continue
            inflight = cur.get("in_flight") if isinstance(cur.get("in_flight"), dict) else {}
            if inflight.get("call_id") != call_id:
                continue
            entry = dict(cur)
            entry["in_flight"] = None
            entry["cooldown_until"] = now + cooldown_s
            entry["needs_login"] = False
            entry["updated"] = now
            entry["last_call"] = {"call_id": call_id, "result": "timeout", "ended": now}
            state[name] = entry
            return name
        return None

    state, name = mutate_state(state_path, fn)
    if not name:
        return {}
    entry = state.get(name) or {}
    last = entry.get("last_call") if isinstance(entry.get("last_call"), dict) else {}
    if last.get("call_id") != call_id or last.get("result") != "timeout":
        return {}
    return {"profile": name, "call_id": call_id, "result": "timeout",
            "cooldown_until": entry.get("cooldown_until")}


def status_line(payload: dict) -> str:
    safe = {k: payload[k] for k in STATUS_KEYS if k in payload}
    return "agy-switch: " + json.dumps(safe)


def emit_status(payload: dict) -> None:
    print(status_line(payload), file=sys.stderr, flush=True)
    sys.stderr.flush()


def main(argv):
    state_path = Path(os.environ.get("AGY_STATE") or Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "agy-state.json")
    if argv[:1] == ["--state"]:
        state_path, argv = Path(argv[1]), argv[2:]
    if argv[:1] == ["--"]:
        argv = argv[1:]
    homes = [h for h in os.environ.get("AUTODOCS_AGY_PROFILES", "").split(",") if h]
    if not homes:
        emit_status({"result": "no_profiles"})
        return 77
    call_id = valid_call_id(os.environ.get("AGY_CALL_ID")) or new_call_id()
    tried = []
    rc = 1
    while True:
        leased = acquire_lease(state_path, homes, call_id)
        if not leased.get("profile"):
            break
        name = leased["profile"]
        home = next(h for h in homes if name_of(h) == name)
        emit_status({"profile": name, "call_id": call_id, "result": "selected", "tried": tried})
        r = subprocess.run(["agy", *argv], capture_output=True, text=True, env=dict(os.environ, HOME=home))
        rc = r.returncode
        if rc == 0:
            complete_call(state_path, name, call_id, "ok")
            sys.stdout.write(r.stdout)
            emit_status({"profile": name, "call_id": call_id, "result": "ok", "tried": tried})
            return 0
        kind, wait = classify(r.stdout + "\n" + r.stderr)
        tried.append({"profile": name, "result": kind, "wait_s": wait})
        if kind == "exhausted":
            complete_call(state_path, name, call_id, "exhausted", wait_s=wait)
            continue
        if kind == "login":
            complete_call(state_path, name, call_id, "login")
            continue
        complete_call(state_path, name, call_id, "error")
        sys.stdout.write(r.stdout)
        emit_status({"profile": name, "call_id": call_id, "result": "error", "rc": rc, "tried": tried})
        return rc
    state, _ = mutate_state(state_path, lambda st: recover_stale_in_state(st, _now(), _cooldown_s()))
    status = acquisition_status(state, homes)
    login = status.get("needs_login") or []
    waits = {n: max(0, int((s.get("cooldown_until") or 0) - time.time()))
             for n, s in state.items() if isinstance(s, dict) and (s.get("cooldown_until") or 0) > time.time()}
    result = status["result"]
    emit_status({"result": result, "tried": tried, "needs_login": login, "cooldown_s": waits,
                 "wait_s": status.get("wait_s", 0.0), "call_id": call_id})
    return {"needs_login": 77, "unavailable": 76}.get(result, 75)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
