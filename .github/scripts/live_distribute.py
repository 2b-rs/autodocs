#!/usr/bin/env python3
"""Online-Job der Live-Verteilung (CONCEPT-0060 §6.7, CONCEPT-0061): Snippets, Schaubild-Reihen und Elemente
(Fragmente) inkrementell zuordnen und jede Entscheidung als Kettenglied in ``autodocs-live`` festhalten.

Läuft im Workflow ``live-distribution.yml`` des öffentlichen Website-Repos (Kopie aus ``_src/tools`` des
Quell-Repos, siehe ``live_bundle.py vendor``) und lokal in den Tests.

    live_distribute.py pending --bundle-url URL --bundle-sha256 SHA --live-repo DIR
    live_distribute.py run --bundle-url URL --bundle-sha256 SHA --live-repo DIR [Budget]
    live_distribute.py finalize --live-repo DIR [--commit]
    live_distribute.py verify --live-repo DIR [--bundle-file F]
    live_distribute.py status --live-repo DIR

Ablauf von ``run``: Bündel laden und prüfen (SHA-256, Manifest, Code-Hashes), Kette prüfen, offene Einheiten des
Plans bestimmen (Schlüssel nicht im Protokoll), volle Batches je Art bilden und fair im Rundlauf einplanen (Größe
und Prompt-Bytes begrenzt), je Batch agy über ``agy_switch.py`` aufrufen (gesperrt: eigenes HOME je Arbeitsplatz,
settings.json erlaubt nur Lesen im leeren Aufrufverzeichnis, jeder Befehl verboten, nie
``--dangerously-skip-permissions``), Antworten prüfen, Entscheidungen anhängen, danach die Prüfregeln (Patrouille
Stufe 1) über die neuen Entscheidungen, Laufglied, Zeiger, Statusdatei, lokaler Commit. Gepusht wird in einem
eigenen Workflow-Schritt mit dem Deploy-Key; dieser Prozess sieht keinen Schlüssel.

Das Log nennt nur Zahlen, Kosten zu API-Listenpreisen und die Profilnamen (leo, neo); nie Prompts oder Antworten.

Exit: 0 fertig oder Budget erreicht oder nichts zu tun, 75 alle Profile erschöpft, 77 kein Profil angemeldet,
65 Kette oder Bündel ungültig, 78 Konfiguration (Code-Stand, fehlende Eingaben), 1 sonstige Fehler.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import live_core as core  # noqa: E402
import live_method as M  # noqa: E402

EXIT_OK, EXIT_ERROR, EXIT_DATA = 0, 1, 65
EXIT_EXHAUSTED, EXIT_TEMPORARY, EXIT_LOGIN, EXIT_CONFIG = 75, 76, 77, 78
# Was in einem agy-HOME bleiben darf (wie abo_relay.mjs); Verläufe, Transkripte und Logs werden nach jedem Aufruf gelöscht.
KEEP_HOME = (".gemini",)
KEEP_GEMINI = ("antigravity-cli",)
KEEP_CLI = ("antigravity-oauth-token", "installation_id", "settings.json", "bin", "builtin", "updater",
            "last_check.timestamp")
# Einheiten je Aufruf (K des vermessenen Laufs); die Byte-Grenze teilt größere Batches. agy bringt je Aufruf rund
# 16.000 Tokens Grundlast mit (Fit über die Aufrufe des Laufs vom 9. Oktober), volle Batches sind deshalb billiger.
BATCH = {"snippet": 20, "figure": 20, "element": 12}
# Linux begrenzt ein einzelnes Argument auf 128 KiB (agy -p); bis 100.000 Bytes bleibt ein Aufruf auch unter der
# Schwelle von ~47.000 Tokens, ab der agy in Agentenschleifen fiel.
MAX_PROMPT_BYTES = 100_000
PERFORMANCE_STABLE_SAMPLES = 3
SCHEDULE_CADENCE_SECONDS = 3600
SCHEDULED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
LIVE_WORKER_SCHEMA = "dashboard-live-worker-update@1"
LIVE_WORKER_PATH = "/dashboard/live-worker.json"
LIVE_WORKER_URL = "https://autodocs-nexos.autodocs-2b-rs.workers.dev/dashboard/live-worker.json"
DASHBOARD_TOKEN_ENV = "DASHBOARD_WRITE_TOKEN"
TELEMETRY_ATTEMPTS = 3
TELEMETRY_TIMEOUT_S = 15.0
HEARTBEAT_INTERVAL_S = 10.0  # coordinator cadence while futures are pending; keep within 10–15s
TELEMETRY_WARN_MAX = 180
TERMINAL_STOPS = {"errors", "exhausted", "needs-login"}
SUCCESSFUL_STOPS = {"done", "budget-time", "budget-calls", "budget-usd"}
_TELEMETRY_LOCK = threading.Lock()


def log(msg: str) -> None:
    print("live: " + msg, flush=True)


def _dashboard_token() -> str:
    value = os.environ.get(DASHBOARD_TOKEN_ENV)
    return value if isinstance(value, str) else ""


def _redact(text: str, token: Optional[str] = None) -> str:
    token = token if token is not None else _dashboard_token()
    if not isinstance(text, str):
        text = str(text)
    if token:
        text = text.replace(token, "[redacted]")
    return text


def _scrubbed_env(src: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Copy an environment mapping without the dashboard write token (name or value)."""
    env = dict(src if src is not None else os.environ)
    token = env.get(DASHBOARD_TOKEN_ENV, "") if isinstance(env.get(DASHBOARD_TOKEN_ENV), str) else ""
    env.pop(DASHBOARD_TOKEN_ENV, None)
    if token:
        for key, value in list(env.items()):
            if value == token:
                env.pop(key, None)
    return env


def _git_env() -> Dict[str, str]:
    env = _scrubbed_env(os.environ)
    env.update(GIT_AUTHOR_NAME="autodocs-live-worker", GIT_COMMITTER_NAME="autodocs-live-worker",
               GIT_AUTHOR_EMAIL="autodocs-live-worker@users.noreply.github.com",
               GIT_COMMITTER_EMAIL="autodocs-live-worker@users.noreply.github.com")
    env.pop(DASHBOARD_TOKEN_ENV, None)
    return env


def _telemetry_warn(msg: str) -> None:
    text = _redact(msg)[:TELEMETRY_WARN_MAX]
    log("telemetry warning: " + text)
    print("::warning::dashboard telemetry " + text, flush=True)


def _worker_state_path() -> Path:
    raw = os.environ.get("AUTODOCS_LIVE_WORKER_STATE", "").strip()
    if raw:
        return Path(raw)
    tmp = os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()
    run = os.environ.get("GITHUB_RUN_ID") or "local"
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT") or "0"
    return Path(tmp) / f"live-worker-state-{run}-{attempt}.json"


def _acked_seq(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def _load_worker_state(path: Path) -> Dict[str, Any]:
    fallback = {"seq": 0, "terminal_sent": False, "started": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(fallback)
    if not isinstance(data, dict):
        return dict(fallback)
    data["seq"] = _acked_seq(data.get("seq"))
    data["terminal_sent"] = data.get("terminal_sent") is True
    if "started" not in data:
        data["started"] = None
    return data


def _save_worker_state(path: Path, state: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {k: v for k, v in state.items() if k != DASHBOARD_TOKEN_ENV}
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False) + "\n"
    token = _dashboard_token()
    if token and token in text:
        raise ValueError("refusing to persist dashboard token")
    core.write_atomic(path, text.encode("utf-8"))


def _persist_worker_state(path: Path, state: Dict[str, Any]) -> bool:
    try:
        _save_worker_state(path, state)
        return True
    except (OSError, TypeError, ValueError) as exc:
        _telemetry_warn(f"state-write:{type(exc).__name__}")
        return False


def _pending_record(worker_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    pending = worker_state.get("pending")
    if pending is None:
        return None
    if not isinstance(pending, dict):
        return {"malformed": True}
    body = pending.get("body")
    if not isinstance(body, str) or not body:
        return {"malformed": True}
    return pending


def _ack_pending(worker_state: Dict[str, Any], pending: Dict[str, Any]) -> None:
    seq = pending.get("seq")
    event = pending.get("event")
    if not (isinstance(seq, int) and not isinstance(seq, bool) and seq > 0) or not isinstance(event, str):
        try:
            fragment = json.loads(pending.get("body") or "")
        except (TypeError, ValueError):
            fragment = {}
        if isinstance(fragment, dict):
            if not (isinstance(seq, int) and not isinstance(seq, bool) and seq > 0):
                seq = fragment.get("seq")
            if not isinstance(event, str):
                event = fragment.get("event")
    if isinstance(seq, int) and not isinstance(seq, bool) and seq > 0:
        worker_state["seq"] = seq
    if event == "terminal":
        worker_state["terminal_sent"] = True
        if "outcome" in pending:
            worker_state["last_outcome"] = pending.get("outcome")
        if "reason" in pending:
            worker_state["last_reason"] = pending.get("reason")
    worker_state.pop("pending", None)


def _put_live_worker_attempts(url: str, token: str, body: bytes, event: str, seq: int) -> Tuple[int, str, bool]:
    last_status, last_detail = 0, "unsent"
    for attempt in range(1, TELEMETRY_ATTEMPTS + 1):
        status, detail = _put_live_worker(url, token, body)
        last_status, last_detail = status, detail
        if status == 200:
            log(f"telemetry: {event} seq={seq} http=200")
            return status, detail, True
        if attempt < TELEMETRY_ATTEMPTS:
            time.sleep(0.2 * attempt)
    return last_status, last_detail, False


def _flush_pending_event(url: str, token: str, path: Path, worker_state: Dict[str, Any]) -> bool:
    """Retry a persisted un-acked body. False means a later event must not be built."""
    pending = _pending_record(worker_state)
    if pending is None:
        return True
    if pending.get("malformed"):
        _telemetry_warn("pending:malformed")
        return False
    body = pending["body"].encode("utf-8")
    seq = pending.get("seq") if isinstance(pending.get("seq"), int) and not isinstance(pending.get("seq"), bool) else 0
    event = pending.get("event") if isinstance(pending.get("event"), str) else "pending"
    last_status, last_detail, ok = _put_live_worker_attempts(url, token, body, event, seq)
    if not ok:
        _telemetry_warn(f"{event} seq={seq} http={last_status} {_redact(last_detail, token)}")
        return False
    _ack_pending(worker_state, pending)
    _persist_worker_state(path, worker_state)
    return True


def _github_ids() -> Dict[str, Any]:
    run_id = os.environ.get("GITHUB_RUN_ID") or ""
    attempt_raw = os.environ.get("GITHUB_RUN_ATTEMPT") or ""
    unknown: List[str] = []
    if not run_id:
        unknown.append("run_id")
        run_id_out: Optional[str] = None
    else:
        run_id_out = run_id
    attempt: Optional[int]
    try:
        attempt = int(attempt_raw) if attempt_raw else None
    except ValueError:
        attempt = None
    if attempt is None or isinstance(attempt, bool) or attempt < 1:
        unknown.append("run_attempt")
        attempt = None
    return {"run_id": run_id_out, "run_attempt": attempt, "unknown": unknown}


def _progress_obj(done: Optional[int], total: Optional[int],
                  by_kind: Optional[Dict[str, Dict[str, int]]] = None) -> Dict[str, Any]:
    unknown: List[str] = []
    done_out: Optional[int] = done
    total_out: Optional[int] = total
    if done_out is None or isinstance(done_out, bool) or not isinstance(done_out, int) or done_out < 0:
        if done_out is not None:
            unknown.append("done")
        else:
            unknown.append("done")
        done_out = None
    if total_out is None or isinstance(total_out, bool) or not isinstance(total_out, int) or total_out < 0:
        unknown.append("total")
        total_out = None
    out: Dict[str, Any] = {"done": done_out, "total": total_out, "unknown": unknown}
    if by_kind is not None:
        clean: Dict[str, Dict[str, int]] = {}
        for kind in core.UNIT_KINDS:
            item = by_kind.get(kind) if isinstance(by_kind, dict) else None
            if not isinstance(item, dict):
                raise ValueError(f"missing progress for {kind}")
            values = {name: item.get(name) for name in ("done", "total", "remaining")}
            if any(isinstance(value, bool) or not isinstance(value, int) or value < 0
                   for value in values.values()):
                raise ValueError(f"invalid progress for {kind}")
            if values["done"] > values["total"] or values["remaining"] != values["total"] - values["done"]:
                raise ValueError(f"inconsistent progress for {kind}")
            clean[kind] = values
        out["by_kind"] = clean
    return out


def absolute_progress_by_kind(plan: List[Dict[str, Any]], todo: List[Dict[str, Any]],
                              completed_by_kind: Optional[Dict[str, int]] = None) -> Dict[str, Dict[str, int]]:
    """Absolute per-kind progress for a run, never a snapshot-relative delta."""
    completed_by_kind = completed_by_kind or {}
    planned = {kind: 0 for kind in core.UNIT_KINDS}
    open_at_start = {kind: 0 for kind in core.UNIT_KINDS}
    for unit in plan:
        if unit.get("kind") in planned:
            planned[unit["kind"]] += 1
    for unit in todo:
        if unit.get("kind") in open_at_start:
            open_at_start[unit["kind"]] += 1
    out: Dict[str, Dict[str, int]] = {}
    for kind in core.UNIT_KINDS:
        delta = completed_by_kind.get(kind, 0)
        if isinstance(delta, bool) or not isinstance(delta, int) or delta < 0:
            raise ValueError(f"invalid completed delta for {kind}")
        done = planned[kind] - open_at_start[kind] + delta
        if done > planned[kind]:
            raise ValueError(f"completed delta exceeds plan for {kind}")
        out[kind] = {"done": done, "total": planned[kind], "remaining": planned[kind] - done}
    return out


def _live_worker_target() -> Optional[str]:
    raw = (os.environ.get("DASHBOARD_LIVE_WORKER_URL") or LIVE_WORKER_URL).strip()
    try:
        parsed = urllib.parse.urlparse(raw)
    except ValueError:
        _telemetry_warn("refused: unusable URL")
        return None
    if parsed.path.rstrip("/") != LIVE_WORKER_PATH.rstrip("/"):
        _telemetry_warn("refused: path is not /dashboard/live-worker.json")
        return None
    if parsed.username or parsed.password:
        _telemetry_warn("refused: credentials in URL")
        return None
    if parsed.scheme == "https":
        return raw
    host = (parsed.hostname or "").lower()
    if parsed.scheme == "http" and host in {"127.0.0.1", "localhost", "::1"}:
        return raw
    _telemetry_warn("refused: URL scheme")
    return None


def _put_live_worker(url: str, token: str, body: bytes) -> Tuple[int, str]:
    request = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": "autodocs-live-worker/1.0"},
        method="PUT")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=TELEMETRY_TIMEOUT_S) as resp:
            payload = resp.read()
            return int(resp.getcode() or 0), payload.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        try:
            payload = exc.read().decode("utf-8", errors="replace")
        except Exception:
            payload = ""
        try:
            exc.close()
        except Exception:
            pass
        return int(exc.code or 0), payload
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return 0, type(exc).__name__


_ABORTED_REASONS = {
    "errors": "error-threshold",
    "exhausted": "provider-capacity-exhausted",
    "needs-login": "login-required",
}


def _aborted_stop(stop: Any) -> bool:
    return stop in _ABORTED_REASONS


def _last_error_view(run: Dict[str, Any]) -> Dict[str, Any]:
    stop = run.get("stop")
    return {
        "run": run.get("run"),
        "started": run.get("started"),
        "ended": run.get("ended"),
        "elapsed_seconds": run.get("elapsed_seconds"),
        "stop": stop,
        "reason": _ABORTED_REASONS.get(stop, "failed-batches"),
        "failed_batches": int(run.get("failed_batches") or 0),
        "codes": sorted((run.get("error_diagnostics") or {}).keys()),
    }


def distribution_worker_counters(*, calls: int, completed: int, failed_batches: int, remaining: int,
                                 elapsed_seconds: float, completed_by_kind: Dict[str, int],
                                 started_calls: int = 0, in_flight_calls: int = 0) -> Dict[str, Any]:
    """Counters the live-worker allowlist accepts. Findings stay on the run record."""
    return {
        "calls": calls,
        "started_calls": started_calls,
        "in_flight_calls": in_flight_calls,
        "completed": completed,
        "failed_batches": failed_batches,
        "remaining": remaining,
        "elapsed_seconds": elapsed_seconds,
        "completed_by_kind": dict(completed_by_kind),
    }


def _parse_utc_iso(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        return datetime.fromisoformat(value[:-1]).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _monotonic_utc_now(prev_ts: Any) -> str:
    now_str = core.utc_now()
    now_dt = _parse_utc_iso(now_str)
    prev_dt = _parse_utc_iso(prev_ts)
    if now_dt is not None and prev_dt is not None and now_dt <= prev_dt:
        return (prev_dt + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return now_str


def _confidence(sample_count: int, *, remaining: int, eta_ok: bool) -> Optional[str]:
    if remaining == 0:
        return "stable"
    if not eta_ok:
        return None
    if sample_count >= PERFORMANCE_STABLE_SAMPLES:
        return "stable"
    if sample_count >= 1:
        return "provisional"
    return None


def _nonneg_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _nonneg_finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return math.isfinite(number) and number >= 0


def _usable_performance_run(run: Any, config_key: Optional[str]) -> bool:
    if not isinstance(run, dict) or not config_key or run.get("config_key") != config_key:
        return False
    failed_batches = run.get("failed_batches")
    if failed_batches is None:
        failed_batches = 0
    if not _nonneg_int(failed_batches):
        return False
    completed = run.get("completed_by_kind")
    if completed is None:
        completed = {}
    if not isinstance(completed, dict):
        return False
    for value in completed.values():
        if not _nonneg_int(value):
            return False
    stop = run.get("stop")
    if stop not in SUCCESSFUL_STOPS:
        # A capacity stop censors the tail of an otherwise useful observation:
        # retain measured positive work, but never turn a zero-yield abort into
        # evidence of throughput. Login and true processing errors stay out.
        if stop != "exhausted" or not any(value > 0 for value in completed.values()):
            return False
    elapsed = run.get("elapsed_seconds_by_kind")
    if elapsed is None:
        elapsed = {}
    if not isinstance(elapsed, dict):
        return False
    for value in elapsed.values():
        # A scheduled invocation may legitimately spend no productive time on
        # one kind while completing another.  Keep that invocation as a zero-
        # yield calendar sample; only a present elapsed value must be finite.
        if value is not None and not _nonneg_finite_number(value):
            return False
    return True


def publish_live_worker(*, event: str, phase: str, state: str,
                        done: Optional[int] = None, total: Optional[int] = None,
                        progress_by_kind: Optional[Dict[str, Dict[str, int]]] = None,
                        counters: Optional[Dict[str, Any]] = None,
                        outcome: Optional[str] = None, reason: Optional[str] = None,
                        performance: Optional[Dict[str, Any]] = None,
                        ended: bool = False) -> bool:
    """PUT one live-worker fragment. Failure-open: never raises, never changes distribution rc."""
    try:
        return _publish_live_worker(event=event, phase=phase, state=state, done=done, total=total,
                                    progress_by_kind=progress_by_kind,
                                    counters=counters, outcome=outcome, reason=reason,
                                    performance=performance, ended=ended)
    except Exception as exc:
        _telemetry_warn(f"publish:{type(exc).__name__}")
        return False


def _publish_live_worker(*, event: str, phase: str, state: str,
                         done: Optional[int] = None, total: Optional[int] = None,
                         progress_by_kind: Optional[Dict[str, Dict[str, int]]] = None,
                         counters: Optional[Dict[str, Any]] = None,
                         outcome: Optional[str] = None, reason: Optional[str] = None,
                         performance: Optional[Dict[str, Any]] = None,
                         ended: bool = False) -> bool:
    token = _dashboard_token()
    if not token:
        log("telemetry: skipped (DASHBOARD_WRITE_TOKEN unset)")
        return False
    url = _live_worker_target()
    if not url:
        return False
    with _TELEMETRY_LOCK:
        path = _worker_state_path()
        worker_state = _load_worker_state(path)
        if not _flush_pending_event(url, token, path, worker_state):
            return False
        if worker_state.get("terminal_sent") is True:
            return True
        if event == "start" and worker_state.get("started") and _acked_seq(worker_state.get("seq")) > 0:
            return True
        now = _monotonic_utc_now(worker_state.get("last_timestamp"))
        started = worker_state.get("started") or now
        seq = _acked_seq(worker_state.get("seq")) + 1
        last_prog = worker_state.get("last_progress") if isinstance(worker_state.get("last_progress"), dict) else {}
        if event == "terminal" and done is None and total is None:
            done = last_prog.get("done")
            total = last_prog.get("total")
        if event == "terminal" and progress_by_kind is None and isinstance(last_prog.get("by_kind"), dict):
            progress_by_kind = last_prog["by_kind"]
        if isinstance(counters, dict) and counters:
            resolved_counters: Dict[str, Any] = dict(counters)
        elif event == "terminal" and isinstance(worker_state.get("last_counters"), dict):
            resolved_counters = dict(worker_state["last_counters"])
        else:
            resolved_counters = {}
        if event == "terminal" and "in_flight_calls" in resolved_counters:
            resolved_counters["in_flight_calls"] = 0
        fragment: Dict[str, Any] = {
            "schema": LIVE_WORKER_SCHEMA,
            "github": _github_ids(),
            "seq": seq,
            "event": event,
            "phase": phase,
            "state": state,
            "interval": {"started": started, "ended": now if ended or event == "terminal" else None},
            "progress": _progress_obj(done, total, progress_by_kind),
            "counters": resolved_counters,
            "timestamp": now,
            "outcome": outcome,
            "reason": reason,
        }
        if performance is not None:
            fragment["performance"] = performance
        try:
            body = json.dumps(fragment, sort_keys=True, separators=(",", ":"),
                              ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            _telemetry_warn(f"encode:{type(exc).__name__}")
            return False
        worker_state["started"] = started
        worker_state["last_timestamp"] = now
        if done is not None or total is not None or "last_progress" not in worker_state:
            worker_state["last_progress"] = fragment["progress"]
        if resolved_counters or "last_counters" not in worker_state:
            worker_state["last_counters"] = dict(resolved_counters)
        worker_state["pending"] = {
            "body": body.decode("utf-8"),
            "event": event,
            "seq": seq,
            "outcome": outcome,
            "reason": reason,
        }
        if not _persist_worker_state(path, worker_state):
            return False
        last_status, last_detail, ok = _put_live_worker_attempts(url, token, body, event, seq)
        if ok:
            _ack_pending(worker_state, worker_state["pending"])
            _persist_worker_state(path, worker_state)
            return True
        _telemetry_warn(f"{event} seq={seq} http={last_status} {_redact(last_detail, token)}")
        return False


def _workflow_terminal_fields() -> Tuple[str, str, str]:
    if os.environ.get("CFG_SKIP") == "true":
        return "skipped", "config-skip", "skipped"
    if os.environ.get("CFG_OUTCOME") == "failure":
        return "error", "config", "error"
    pending = os.environ.get("PENDING", "")
    rc_raw = os.environ.get("RC", "")
    if pending == "0" and rc_raw in ("", "0"):
        return "ok", "nothing-to-do", "idle"
    try:
        rc = int(rc_raw) if rc_raw not in ("",) else 1
    except ValueError:
        rc = 1
    mapping = {0: ("ok", "completed", "idle"), 75: ("exhausted", "exhausted", "error"),
               77: ("needs-login", "needs-login", "error"), 65: ("error", "data", "error"),
               78: ("error", "config", "error")}
    return mapping.get(rc, ("error", f"rc-{rc}"[:40], "error"))


def _run_terminal_fields(stop: str) -> Tuple[str, str, str]:
    if stop in SUCCESSFUL_STOPS:
        return "ok", stop, "idle"
    if stop == "exhausted":
        return "exhausted", stop, "error"
    if stop == "needs-login":
        return "needs-login", stop, "error"
    if stop == "errors":
        return "error", stop, "error"
    return "error", (stop or "unknown")[:40], "error"


def cmd_dashboard(a: argparse.Namespace) -> int:
    """Workflow helper: start/terminal fragment. Always returns 0 (failure-open)."""
    try:
        if a.event == "start":
            publish_live_worker(event="start", phase="start", state="active")
        elif a.event == "progress":
            publish_live_worker(event="progress", phase=a.phase or "progress", state=a.state or "active",
                                done=a.done, total=a.total, outcome=a.outcome or None, reason=a.reason or None)
        else:
            path = _worker_state_path()
            worker_state = _load_worker_state(path)
            last = worker_state.get("last_progress") if isinstance(worker_state.get("last_progress"), dict) else {}
            last_counters = (dict(worker_state["last_counters"])
                             if isinstance(worker_state.get("last_counters"), dict) else {})
            if "in_flight_calls" in last_counters:
                last_counters["in_flight_calls"] = 0
            outcome, reason, state = _workflow_terminal_fields()
            if worker_state.get("terminal_sent"):
                return EXIT_OK
            publish_live_worker(event="terminal", phase="terminal", state=state,
                                done=last.get("done"), total=last.get("total"),
                                progress_by_kind=(last.get("by_kind")
                                                  if isinstance(last.get("by_kind"), dict) else None),
                                counters=last_counters,
                                outcome=outcome, reason=reason, ended=True)
    except Exception as exc:
        _telemetry_warn(f"dashboard:{type(exc).__name__}")
    return EXIT_OK


# ==============================================================================
# Daten des Bündels
# ==============================================================================

class Data:
    """Korpus, Einheiten und Universum aus einem geöffneten Bündel."""

    def __init__(self, bundle: core.Bundle):
        self.bundle = bundle
        self.records: Dict[str, M.Record] = {}
        for r in bundle.rows("corpus.jsonl"):
            rec = M.Record.from_row(r)
            self.records[rec.id] = rec
        self.snippets: Dict[str, M.Item] = {}
        for r in bundle.rows("snippets.jsonl"):
            it = M.Item.from_snippet_row(r)
            self.snippets[it.id] = it
        self.figure_rows: Dict[str, Dict[str, Any]] = {r["figure_id"]: r for r in bundle.rows("figure_texts.jsonl")}
        self.elements = {r["id"]: r for r in bundle.rows("elements.jsonl")}
        self.module_index = M.module_index(self.records.values())
        self._figures: Dict[str, M.Item] = {}
        self._mod_idx: Dict[str, M.LexicalIndex] = {}
        self._lock = threading.Lock()

    def item(self, ref: str, platform: Optional[str] = None) -> Optional[M.Item]:
        if ref in self.snippets:
            return self.snippets[ref]
        with self._lock:
            if ref not in self._figures and ref in self.figure_rows:
                self._figures[ref] = M.item_from_figure(self.figure_rows[ref], platform)
            return self._figures.get(ref)

    def module_candidates(self, modules: List[str], text: str, exclude: Set[str], k: int) -> List[str]:
        out: List[str] = []
        for m in modules:
            with self._lock:
                idx = self._mod_idx.get(m)
                if idx is None:
                    idx = self._mod_idx[m] = M.record_index([r for r in self.records.values() if r.module == m])
            added = 0
            for rid, _ in idx.search(text, k + len(exclude)):
                if added >= k:
                    break
                if rid not in exclude and rid not in out:
                    out.append(rid)
                    added += 1
        return out

    def universe(self, matrix_strong: Dict[Tuple[str, str], str]) -> core.Universe:
        items = {sid: {"mask": it.mask, "mod": it.module} for sid, it in self.snippets.items()}
        for fid, row in self.figure_rows.items():
            rels = row.get("releases") or []
            items[fid] = {"mask": M.release_mask(rels) if rels else M.ALL_MASK, "mod": "figure"}
        els = {eid: {"m": e.get("m"), "k": e.get("k"), "mask": int(e.get("mask", "0x0"), 16)} for eid, e in self.elements.items()}
        return core.Universe(els, items, M.ALL_MASK, matrix_strong)


def strong_matrix_rows(bundle: core.Bundle, snippet_ids: Set[str]) -> Dict[Tuple[str, str], str]:
    out: Dict[Tuple[str, str], str] = {}
    for r in bundle.rows("assignment_matrix.jsonl"):
        sid = r.get("snippet_id")
        if sid in snippet_ids and float(r.get("confidence") or 0) >= 0.95 and r.get("target_element"):
            out[(r["target_element"], sid)] = str(r.get("relation_type") or r.get("role") or "constitutive")
    return out


# ==============================================================================
# agy über agy_switch.py, Arbeitsplätze mit eigener Sperre
# ==============================================================================

def _prune(d: Path, keep: Tuple[str, ...]) -> None:
    if not d.is_dir():
        return
    for p in d.iterdir():
        if p.name in keep:
            continue
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p, ignore_errors=True)
        else:
            try:
                p.unlink()
            except OSError:
                pass


def lockdown_settings(call_dir: Path) -> str:
    return json.dumps({"permissions": {"allow": [f"read_file({os.path.realpath(call_dir)}/*)"],
                                       "deny": ["command(*)", "command(regex:.*)"]}})


class Slot:
    """Arbeitsplatz eines Threads: je Profil eine Kopie des HOME (nur Token, Installations-ID, Programmteile) mit
    eigener settings.json, die nur das Lesen im leeren Aufrufverzeichnis erlaubt. Der Verzeichnisname bleibt
    ``agy-profile-<name>``, damit agy_switch.py den Sperrzustand unter leo/neo führt."""

    def __init__(self, idx: int, base_profiles: List[str], root: Path):
        self.idx = idx
        self.dir = root / f"w{idx}"
        self.call_dir = self.dir / "call"
        self.call_dir.mkdir(parents=True, exist_ok=True)
        self.call_dir = Path(os.path.realpath(self.call_dir))
        self.homes: List[Path] = []
        old = os.umask(0o077)
        try:
            # Reihenfolge je Arbeitsplatz rotiert: agy_switch.py nimmt das erste verfügbare Profil, ohne Rotation liefen
            # alle Plätze auf dem ersten Konto, bis es erschöpft ist (Übersetzungslauf 2026-10-15: 1940 von 1940 Aufrufen
            # auf einem Konto).
            k = idx % len(base_profiles) if base_profiles else 0
            for base in base_profiles[k:] + base_profiles[:k]:
                src = Path(base) / ".gemini" / "antigravity-cli"
                home = self.dir / Path(base.rstrip("/")).name
                cli = home / ".gemini" / "antigravity-cli"
                cli.mkdir(parents=True, exist_ok=True)
                for f in ("antigravity-oauth-token", "installation_id"):
                    if (src / f).is_file():
                        shutil.copyfile(src / f, cli / f)
                (cli / "settings.json").write_text(lockdown_settings(self.call_dir), encoding="utf-8")
                self.homes.append(home)
        finally:
            os.umask(old)

    @property
    def profiles(self) -> str:
        return ",".join(str(h) for h in self.homes)

    def scrub(self) -> None:
        for home in self.homes:
            _prune(home, KEEP_HOME)
            _prune(home / ".gemini", KEEP_GEMINI)
            _prune(home / ".gemini" / "antigravity-cli", KEEP_CLI)
        _prune(self.call_dir, ())

    def lock(self) -> bool:
        """Sperre vor jedem Aufruf neu schreiben (agy könnte die Datei selbst ändern) und das Aufrufverzeichnis
        leeren. False, wenn das nicht gelingt: dann kein Aufruf."""
        expect = lockdown_settings(self.call_dir)
        try:
            _prune(self.call_dir, ())
            for home in self.homes:
                p = home / ".gemini" / "antigravity-cli" / "settings.json"
                core.write_atomic(p, expect.encode("utf-8"))
                os.chmod(p, 0o600)
                if p.read_text(encoding="utf-8") != expect:
                    return False
        except OSError:
            return False
        return not any(self.call_dir.iterdir())


@dataclass
class CallResult:
    outcome: str                       # ok | exhausted | unavailable | login | error | contaminated | empty | timeout
    structured: Optional[Dict[str, Any]] = None
    tokens: Dict[str, int] = field(default_factory=lambda: {"input": 0, "cached": 0, "output": 0, "thinking": 0})
    profile: str = ""
    rc: int = 0
    wall_s: float = 0.0
    steps: int = 0
    diagnostic: str = ""
    provider_invoked: bool = True
    wait_s: float = 0.0


_GROUPS: Set[int] = set()


def _terminate(signum, _frame) -> None:
    """Abbruch des Laufs (Workflow-Abbruch, Strg-C): laufende agy-Gruppen mit beenden."""
    for pg in list(_GROUPS):
        try:
            os.killpg(pg, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    os._exit(128 + signum)


def _switch_runtime(switch: Path):
    """Load the paired agy_switch.py next to this job (public copy) or the canonical source path."""
    path = Path(switch)
    spec = importlib.util.spec_from_file_location("_agy_switch_runtime", path)
    if spec is None or spec.loader is None:
        raise ImportError("agy_switch unreadable")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _attribute_timeout(switch: Path, state: Path, call_id: str) -> Dict[str, Any]:
    """Mark the recorded in-flight call timed out and read the attribution back. Never invent tokens."""
    try:
        runtime = _switch_runtime(switch)
        attr = getattr(runtime, "attribute_timeout", None)
        if not callable(attr):
            return {}
        found = attr(state, call_id) or {}
        return found if isinstance(found, dict) else {}
    except (OSError, ImportError, ValueError, AttributeError, TypeError):
        return {}


def _run_group(cmd: List[str], timeout: float, env: Dict[str, str], cwd: str) -> Tuple[int, str, str, bool]:
    """Prozess in eigener Gruppe; bei Zeitüberschreitung wird die ganze Gruppe (auch agy) beendet."""
    env = _scrubbed_env(env)
    env.pop(DASHBOARD_TOKEN_ENV, None)
    with tempfile.TemporaryFile("w+", encoding="utf-8") as out, tempfile.TemporaryFile("w+", encoding="utf-8") as err:
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=err, env=env, cwd=cwd,
                                start_new_session=True, text=True)
        _GROUPS.add(proc.pid)
        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            _GROUPS.discard(proc.pid)
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            if proc.poll() is None:
                proc.wait(timeout=10)
        out.seek(0)
        err.seek(0)
        return proc.returncode if not timed_out else 124, out.read(), err.read(), timed_out


class Agy:
    def __init__(self, switch: Path, state: Path, model: str, effort: str, timeout_s: int, python: str):
        self.switch, self.state, self.model, self.effort = switch, state, model, effort
        self.timeout_s, self.python = timeout_s, python

    def env(self, slot: Slot) -> Dict[str, str]:
        src = _scrubbed_env(os.environ)
        env = {"PATH": src.get("PATH", "/usr/bin:/bin"), "LANG": src.get("LANG", "C.UTF-8"),
               "AUTODOCS_AGY_PROFILES": slot.profiles, "AGY_STATE": str(self.state)}
        for k in ("RUNNER_TEMP", "TMPDIR", "TZ"):
            if src.get(k):
                env[k] = src[k]
        env.pop(DASHBOARD_TOKEN_ENV, None)
        return env

    def call(self, slot: Slot, prompt: str, schema: Dict[str, Any]) -> CallResult:
        if not slot.lock():
            return CallResult("error", rc=EXIT_CONFIG)
        call_id = uuid.uuid4().hex
        env = self.env(slot)
        env["AGY_CALL_ID"] = call_id
        env["AGY_LEASE_S"] = str(max(1, int(self.timeout_s) + 60))
        cmd = [self.python, str(self.switch), "--state", str(self.state), "--",
               "-p", prompt, "--model", self.model, "--effort", self.effort, "--output-format", "stream-json",
               "--json-schema", json.dumps(schema, separators=(",", ":")), "--disable-slash-commands",
               "--print-timeout", f"{self.timeout_s}s"]
        t0 = time.monotonic()
        try:
            rc, out, err, timed_out = _run_group(cmd, self.timeout_s + 60, env, str(slot.call_dir))
        except (OSError, ValueError) as exc:    # z. B. E2BIG oder ein für argv unzulässiger Wert
            return CallResult("error", rc=EXIT_ERROR, wall_s=time.monotonic() - t0,
                              diagnostic=f"agy-start:{type(exc).__name__}")
        finally:
            slot.scrub()
        wall = time.monotonic() - t0
        sw: Dict[str, Any] = {}
        for line in err.splitlines():
            if line.startswith("agy-switch: "):
                try:
                    sw = json.loads(line[len("agy-switch: "):])
                except ValueError:
                    sw = {}
        profile = str(sw.get("profile") or "")
        tried = sw.get("tried") if isinstance(sw.get("tried"), list) else []
        provider_invoked = bool(profile or tried)
        if timed_out:
            attributed = _attribute_timeout(self.switch, self.state, call_id)
            profile = str(attributed.get("profile") or profile)
            return CallResult("timeout", profile=profile, rc=rc, wall_s=wall, provider_invoked=True)
        if rc == EXIT_EXHAUSTED:
            return CallResult("exhausted", profile=profile, rc=rc, wall_s=wall,
                              provider_invoked=provider_invoked)
        if rc == EXIT_TEMPORARY:
            try:
                wait_s = float(sw.get("wait_s") or 0.05)
            except (TypeError, ValueError, OverflowError):
                wait_s = 0.05
            if not math.isfinite(wait_s) or wait_s <= 0:
                wait_s = 0.05
            return CallResult("unavailable", profile=profile, rc=rc, wall_s=wall,
                              diagnostic="profile-temporarily-unavailable",
                              provider_invoked=provider_invoked, wait_s=wait_s)
        if rc == EXIT_LOGIN:
            return CallResult("login", profile=profile, rc=rc, wall_s=wall,
                              provider_invoked=provider_invoked)
        try:
            result, steps, bad = M.parse_agy_stream(out)
            tokens = M.usage_tokens((result or {}).get("usage") or {})
            n_steps = sum(steps.values())
        except Exception as exc:
            # Never expose raw CLI output or exception text: either can contain
            # prompt material. The phase and exception class are sufficient.
            return CallResult("error", profile=profile, rc=EXIT_ERROR, wall_s=wall,
                              diagnostic=f"agy-output:{type(exc).__name__}")
        if bad:
            return CallResult("contaminated", None, tokens, profile, rc, wall, n_steps)
        if rc != 0:
            return CallResult("error", None, tokens, profile, rc, wall, n_steps)
        structured = (result or {}).get("structured_output")
        if not isinstance(structured, dict) or (result or {}).get("status", "SUCCESS") != "SUCCESS":
            return CallResult("empty", None, tokens, profile, rc, wall, n_steps)
        return CallResult("ok", structured, tokens, profile, rc, wall, n_steps)


# ==============================================================================
# Budget
# ==============================================================================

class Budget:
    def __init__(self, max_calls: int, max_minutes: float, max_usd: float):
        self.max_calls, self.max_s, self.max_usd = max_calls, max_minutes * 60.0, max_usd
        self.t0 = time.monotonic()
        self.calls = 0
        self.usd = 0.0
        self.stop: Optional[str] = None
        self._lock = threading.Lock()

    def reason(self) -> Optional[str]:
        if self.stop:
            return self.stop
        if self.max_calls and self.calls >= self.max_calls:
            return "budget-calls"
        if self.max_s and time.monotonic() - self.t0 >= self.max_s:
            return "budget-time"
        if self.max_usd and self.usd >= self.max_usd:
            return "budget-usd"
        return None

    def take(self) -> bool:
        """Einen Aufruf reservieren (False: Budget erschöpft oder Lauf angehalten)."""
        with self._lock:
            if self.reason():
                return False
            self.calls += 1
            return True

    def spend(self, usd: float) -> None:
        with self._lock:
            self.usd += usd

    def refund_call(self) -> None:
        """Undo a reservation when profile acquisition proved that no provider was invoked."""
        with self._lock:
            self.calls = max(0, self.calls - 1)

    def wait_for_availability(self, requested_s: float) -> bool:
        """Wait no longer than the remaining wall-clock budget; False means the run must stop."""
        if self.reason():
            return False
        delay = max(0.05, float(requested_s or 0.0))
        if self.max_s:
            remaining = self.max_s - (time.monotonic() - self.t0)
            if remaining <= 0:
                return False
            delay = min(delay, remaining)
        time.sleep(delay)
        return self.reason() is None

    _RANK = {"needs-login": 3, "exhausted": 2, "errors": 1}

    def halt(self, why: str) -> None:
        """Lauf anhalten; ein schwererer Grund (Anmeldung > Kontingent > Fehler) ersetzt einen leichteren."""
        with self._lock:
            if self.stop is None or self._RANK.get(why, 0) > self._RANK.get(self.stop, 0):
                self.stop = why


# ==============================================================================
# Batches und Entscheidungen
# ==============================================================================

@dataclass
class Batch:
    kind: str
    units: List[Dict[str, Any]]
    prompt: str


@dataclass
class BatchResult:
    batch: Batch
    bodies: List[Dict[str, Any]] = field(default_factory=list)
    calls: int = 0
    retries: int = 0
    stage2_calls: int = 0
    usd: float = 0.0
    tokens: Dict[str, int] = field(default_factory=lambda: {"input": 0, "cached": 0, "output": 0, "thinking": 0})
    profiles: Dict[str, int] = field(default_factory=dict)
    outcome: str = "ok"
    unanswered: int = 0
    incomplete: int = 0
    diagnostics: Dict[str, int] = field(default_factory=dict)


class Job:
    def __init__(self, a: argparse.Namespace, bundle: core.Bundle, data: Data, live: core.LiveLog, agy: Optional[Agy],
                 budget: Budget, run_id: str):
        self.a, self.bundle, self.data, self.live, self.agy, self.budget, self.run_id = a, bundle, data, live, agy, budget, run_id
        self.assets = {"bundle": bundle.sha256, "manifest": bundle.manifest_hash}
        self.call_no = 0
        self.started_calls = 0
        self.in_flight_calls = 0
        self._lock = threading.Lock()
        self.sizes = {"snippet": a.batch_snippets, "figure": a.batch_figures, "element": a.batch_elements}
        self.skipped = {"missing": 0, "oversize": 0}

    def _enter_call(self) -> Tuple[int, int]:
        with self._lock:
            self.started_calls += 1
            self.in_flight_calls += 1
            return self.started_calls, self.in_flight_calls

    def _exit_call(self) -> Tuple[int, int]:
        with self._lock:
            self.in_flight_calls = max(0, self.in_flight_calls - 1)
            return self.started_calls, self.in_flight_calls

    def _discard_unstarted_call(self) -> Tuple[int, int]:
        """Remove an acquisition-only probe from provider-call telemetry."""
        with self._lock:
            self.started_calls = max(0, self.started_calls - 1)
            return self.started_calls, self.in_flight_calls

    def call_counts(self) -> Tuple[int, int]:
        with self._lock:
            return self.started_calls, self.in_flight_calls

    # --- Prompts ---------------------------------------------------------------------------------------
    def items_for(self, units: List[Dict[str, Any]]) -> List[M.Item]:
        return [self.data.item(u["ref"], u.get("p")) for u in units]

    def build_prompt(self, kind: str, units: List[Dict[str, Any]]) -> str:
        if kind == "element":
            recs = [self.data.records[u["ref"]] for u in units]
            pool_ids = list(dict.fromkeys(c for u in units for c in u["cand"]))
            pool = [it for it in (self.data.item(c) for c in pool_ids) if it is not None]
            return M.reverse_prompt(recs, pool)
        return M.forward_prompt(self.data.records, self.items_for(units), {u["ref"]: u["cand"] for u in units})

    def fit(self, u: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Einheit, deren Prompt schon allein die Grenze überschreitet (z. B. ein Element, das hunderte Snippets
        zitieren): gezeigte Kandidaten von hinten kürzen (zitierte und Seiten-Nachbarn stehen vorn). Zitatkanten ordnet
        der Job für alle Kandidaten deterministisch zu; ``trimmed`` hält fest, wie viele das Modell nicht sah."""
        cap = self.a.max_prompt_bytes
        if len(self.build_prompt(u["kind"], [u]).encode("utf-8")) <= cap:
            return u
        cand = list(u["cand"])
        lo, hi = 0, len(cand)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if len(self.build_prompt(u["kind"], [dict(u, cand=cand[:mid])]).encode("utf-8")) <= cap:
                lo = mid
            else:
                hi = mid - 1
        if lo == 0:
            return None
        return dict(u, cand=cand[:lo], cand_all=cand, trimmed=len(cand) - lo)

    def _ordered_batches(self, todo: List[Dict[str, Any]]) -> Iterator[Batch]:
        """Build full batches for one kind while preserving the plan order."""
        cur: List[Dict[str, Any]] = []
        prompt = ""
        for u in todo:
            if u["kind"] == "element" and u["ref"] not in self.data.records:
                self.skipped["missing"] += 1
                continue
            if u["kind"] != "element" and self.data.item(u["ref"], u.get("p")) is None:
                self.skipped["missing"] += 1
                continue
            u = self.fit(u)
            if u is None:
                self.skipped["oversize"] += 1
                log("Einheit zu groß für einen Aufruf, übersprungen")
                continue
            if cur and (u["kind"] != cur[0]["kind"] or len(cur) >= self.sizes[cur[0]["kind"]]):
                yield Batch(cur[0]["kind"], cur, prompt)
                cur, prompt = [], ""
            trial = self.build_prompt(u["kind"], cur + [u])
            if cur and len(trial.encode("utf-8")) > self.a.max_prompt_bytes:
                yield Batch(cur[0]["kind"], cur, prompt)
                cur, trial = [u], self.build_prompt(u["kind"], [u])
            else:
                cur = cur + [u]
            prompt = trial
        if cur:
            yield Batch(cur[0]["kind"], cur, prompt)

    def batches(self, todo: List[Dict[str, Any]]) -> Iterator[Batch]:
        """Yield one full batch per open kind in a stable round-robin.

        The plan is intentionally grouped by kind. Consuming it directly made
        every time-bounded invocation spend its whole budget on snippets, so
        figures and elements could remain untouched forever. Per-kind batch
        builders preserve batching efficiency; only their dispatch order is
        interleaved.
        """
        queues = {
            kind: iter(self._ordered_batches([unit for unit in todo if unit.get("kind") == kind]))
            for kind in core.UNIT_KINDS
            if any(unit.get("kind") == kind for unit in todo)
        }
        while queues:
            for kind in list(core.UNIT_KINDS):
                queue = queues.get(kind)
                if queue is None:
                    continue
                batch = next(queue, None)
                if batch is None:
                    del queues[kind]
                else:
                    yield batch

    # --- Aufruf mit Wiederholung ------------------------------------------------------------------------
    def _call(self, slot: Slot, prompt: str, schema: Dict[str, Any], res: BatchResult) -> Optional[Dict[str, Any]]:
        attempts = [prompt]
        strict = M.STRICT_RETRY_RULE + prompt + M.STRICT_RETRY_RULE
        if len(strict.encode("utf-8")) <= self.a.max_prompt_bytes + 2000:
            attempts.append(strict)
        for n, text in enumerate(attempts):
            while True:
                if not self.budget.take():
                    res.outcome = res.outcome if res.outcome != "ok" else "budget"
                    return None
                # Reserve before entering provider/decoder code so exceptions are
                # counted.  A pure acquisition miss is explicitly refunded below.
                res.calls += 1
                self._enter_call()
                try:
                    r = self.agy.call(slot, text, schema)
                finally:
                    self._exit_call()
                if r.diagnostic:
                    res.diagnostics[r.diagnostic] = res.diagnostics.get(r.diagnostic, 0) + 1
                if not r.provider_invoked:
                    self.budget.refund_call()
                    res.calls = max(0, res.calls - 1)
                    self._discard_unstarted_call()
                else:
                    res.retries += 1 if n else 0
                    usd = M.list_price(self.agy.model, r.tokens)
                    self.budget.spend(usd)
                    res.usd += usd
                    for key in res.tokens:
                        res.tokens[key] += r.tokens.get(key, 0)
                    if r.profile:
                        res.profiles[r.profile] = res.profiles.get(r.profile, 0) + 1
                if r.outcome == "unavailable":
                    res.outcome = "unavailable"
                    if not self.budget.wait_for_availability(r.wait_s):
                        res.outcome = "budget"
                        return None
                    continue
                if r.outcome == "ok":
                    res.outcome = "ok"
                    res.last_profile = r.profile      # type: ignore[attr-defined]
                    res.attempt = n + 1               # type: ignore[attr-defined]
                    return r.structured
                res.outcome = r.outcome
                if r.outcome == "exhausted":
                    self.budget.halt("exhausted")
                    return None
                if r.outcome == "login":
                    self.budget.halt("needs-login")
                    return None
                if r.outcome not in ("contaminated", "empty", "error"):
                    return None                      # Zeitüberschreitung: nicht wiederholen
                break
        return None

    # --- Verarbeitung eines Batches ------------------------------------------------------------------
    def process(self, batch: Batch, slot: Slot) -> BatchResult:
        res = BatchResult(batch)
        res.last_profile = ""              # type: ignore[attr-defined]
        res.attempt = 1                    # type: ignore[attr-defined]
        try:
            if batch.kind == "element":
                self._process_reverse(batch, slot, res)
            else:
                self._process_forward(batch, slot, res)
        except Exception as exc:          # der Koordinator zählt und begrenzt fehlerhafte Batches
            res.bodies = []
            res.outcome = f"exception:{type(exc).__name__}"
            key = f"batch:{type(exc).__name__}"
            res.diagnostics[key] = res.diagnostics.get(key, 0) + 1
        return res

    def _decision_body(self, u: Dict[str, Any], decision: Dict[str, Any], prompt: str, profile: str, share_usd: float,
                       extra_inputs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        best = sorted(decision["assignments"], key=lambda a: (-a["confidence"], core.RELATION_TYPES.index(a["relation_type"])
                      if a["relation_type"] in core.RELATION_TYPES else 99, a["target_element"], a["snippet_id"]))
        with self._lock:
            self.call_no += 1
            call_no = self.call_no
        mask = int(u.get("mask") or "0x0", 16)
        return {
            "kind": "decision",
            "id": core.identity(u["kind"], u["ref"], M.newest_release(mask)),
            "unit": u["unit"], "unit_key": u["key"], "unit_kind": u["kind"],
            "inputs": list(u["inputs"]) + list(extra_inputs or []),
            "assets": self.assets, "basis": u.get("basis"), "parent": u.get("prior"),
            "reason": {"kind": "never-decided" if u.get("status") == "new" else "input-changed", "ref": u.get("prior")},
            "decisions": [],
            "decision": decision,
            "relation_type": best[0]["relation_type"] if best else core.NO_RELATION,
            "confidence": round(best[0]["confidence"], 4) if best else 0.0,
            "rationale": decision.get("effect_rationale", ""),
            "model": self.agy.model, "effort": self.agy.effort, "backend": "agy", "profile": profile or "unbekannt",
            "prompt_hash": core.sha256_hex(prompt.encode("utf-8")), "call": f"{self.run_id}/{call_no}",
            "list_price_usd": round(share_usd, 6), "author": "worker", "run": self.run_id, "at": core.utc_now(),
        }

    def _assign(self, answer: Dict[str, Any], it: M.Item, cand: List[str], source: str,
                have: Dict[str, Dict[str, Any]], rejected: List[Dict[str, Any]]) -> None:
        best: Dict[str, Dict[str, Any]] = {}
        for m in answer.get("matches") or []:
            if m["id"] not in best or m["confidence"] > best[m["id"]]["confidence"]:
                best[m["id"]] = m
        for rid, m in best.items():
            why = M.gate(self.data.records.get(rid), it.mask)
            if why:
                rejected.append({"target": rid, "reason": why, "confidence": round(m["confidence"], 4)})
                continue
            row = {"target_element": rid, "snippet_id": it.id, "relation_type": m["relation_type"],
                   "confidence": round(m["confidence"], 4), "rationale": m["rationale"], "source": source}
            if rid not in have or row["confidence"] > have[rid]["confidence"]:
                have[rid] = row

    def _process_forward(self, batch: Batch, slot: Slot, res: BatchResult) -> None:
        items = self.items_for(batch.units)
        structured = self._call(slot, batch.prompt, M.FORWARD_SCHEMA, res)
        if structured is None:
            return
        parsed, _problems = M.parse_answer(structured, [it.id for it in items], "snippet_id", "record_id")
        res.unanswered = len(items) - len(parsed)
        profile = res.last_profile                      # type: ignore[attr-defined]
        states: List[Tuple[Dict[str, Any], M.Item, Dict[str, Any]]] = []
        need2: Dict[str, List[str]] = {}
        for u, it in zip(batch.units, items):
            ans = parsed.get(it.id)
            if ans is None:
                continue
            have: Dict[str, Dict[str, Any]] = {}
            rejected: List[Dict[str, Any]] = []
            self._assign(ans, it, u["cand"], "model", have, rejected)
            for c in it.cited:                       # deterministische Zitatkanten (--auto-cited)
                if c in self.data.records and c not in have:
                    have[c] = {"target_element": c, "snippet_id": it.id, "relation_type": "EXPLICIT_REFERENCE",
                               "confidence": 0.95, "rationale": "EXPLICIT_REFERENCE (deterministic citation)",
                               "source": "deterministic"}
            mods, unknown = M.resolve_modules(ans["modules"], self.data.module_index)
            covered = {self.data.records[c].module for c in u["cand"] if c in self.data.records}
            need = [m for m in mods if m not in covered][:core.METHOD["stage2_max_modules"]] if ans["external_effect"] else []
            decision = {"external_effect": ans["external_effect"], "modules": mods, "modules_unresolved": unknown,
                        "effect_rationale": ans["effect_rationale"], "candidates": list(u["cand"]),
                        "stage2": {"status": "none"}, "_have": have, "rejected": rejected}
            if u.get("trimmed"):
                decision["trimmed"] = u["trimmed"]
            if need:
                need2[it.id] = need
            states.append((u, it, decision))
        stage2_inputs: Dict[str, List[Dict[str, Any]]] = {}
        stage2_cost = 0.0
        if need2:
            sub = [(u, it, d) for u, it, d in states if it.id in need2]
            cands2 = {it.id: self.data.module_candidates(need2[it.id], it.text, set(u["cand"]), core.METHOD["stage2_k"])
                      for u, it, _ in sub}
            sub = [(u, it, d) for u, it, d in sub if cands2[it.id]]
            for u, it, d in states:
                if it.id in need2 and not cands2.get(it.id):
                    d["stage2"] = {"status": "no-candidates", "modules": need2[it.id]}
            if sub:
                prompt2 = M.forward_prompt(self.data.records, [it for _, it, _ in sub], cands2, stage2=True)
                usd_before = res.usd
                calls_before = res.calls
                structured2 = None
                if len(prompt2.encode("utf-8")) <= self.a.max_prompt_bytes:
                    structured2 = self._call(slot, prompt2, M.FORWARD_SCHEMA, res)
                res.stage2_calls += res.calls - calls_before
                stage2_cost = res.usd - usd_before
                parsed2 = M.parse_answer(structured2, [it.id for _, it, _ in sub], "snippet_id", "record_id")[0] if structured2 else {}
                for u, it, d in sub:
                    cand2 = cands2[it.id]
                    if structured2 is None:
                        d["stage2"] = {"status": "deferred" if res.outcome in ("budget",) or self.budget.reason() else "failed",
                                       "modules": need2[it.id], "candidates": cand2}
                        continue
                    ans2 = parsed2.get(it.id) or {"matches": []}
                    ans2 = {"matches": [m for m in ans2.get("matches") or [] if m["id"] in set(cand2)]}
                    self._assign(ans2, it, cand2, "stage2", d["_have"], d["rejected"])
                    d["stage2"] = {"status": "done", "modules": need2[it.id], "candidates": cand2,
                                   "prompt_hash": core.sha256_hex(prompt2.encode("utf-8"))}
                    stage2_inputs[it.id] = [{"kind": "candidates-stage2", "ref": "+".join(need2[it.id]),
                                             "hash": core.obj_hash(cand2)}]
        stage1_cost = res.usd - stage2_cost
        n1 = max(1, len(states))
        n2 = max(1, sum(1 for _, it, _ in states if it.id in stage2_inputs))
        for u, it, d in states:
            have = d.pop("_have")
            d["assignments"] = sorted(have.values(), key=lambda a: a["target_element"])
            d["rejected"] = d["rejected"][:20]
            if d["stage2"].get("status") in ("failed", "deferred"):
                res.incomplete += 1
            share = stage1_cost / n1 + (stage2_cost / n2 if it.id in stage2_inputs else 0.0)
            d["attempt"] = res.attempt                  # type: ignore[attr-defined]
            res.bodies.append(self._decision_body(u, d, batch.prompt, profile, share, stage2_inputs.get(it.id)))

    def _process_reverse(self, batch: Batch, slot: Slot, res: BatchResult) -> None:
        recs = [self.data.records[u["ref"]] for u in batch.units]
        structured = self._call(slot, batch.prompt, M.REVERSE_SCHEMA, res)
        if structured is None:
            return
        parsed, _problems = M.parse_answer(structured, [r.id for r in recs], "record_id", "snippet_id")
        res.unanswered = len(recs) - len(parsed)
        profile = res.last_profile                      # type: ignore[attr-defined]
        n = max(1, len(parsed))
        pool = {c for u in batch.units for c in u["cand"]}      # wie der Runner: alle Snippets des Batch-Pools
        for u, rec in zip(batch.units, recs):
            ans = parsed.get(rec.id)
            if ans is None:
                continue
            have: Dict[str, Dict[str, Any]] = {}
            rejected: List[Dict[str, Any]] = []
            best: Dict[str, Dict[str, Any]] = {}
            for m in ans["matches"]:
                if m["id"] not in best or m["confidence"] > best[m["id"]]["confidence"]:
                    best[m["id"]] = m
            for sid, m in best.items():
                it = self.data.item(sid)
                if sid not in pool or it is None:
                    rejected.append({"target": sid, "reason": "not_in_pool", "confidence": round(m["confidence"], 4)})
                    continue
                why = M.gate(rec, it.mask)
                if why:
                    rejected.append({"target": sid, "reason": why, "confidence": round(m["confidence"], 4)})
                    continue
                have[sid] = {"target_element": rec.id, "snippet_id": sid, "relation_type": m["relation_type"],
                             "confidence": round(m["confidence"], 4), "rationale": m["rationale"], "source": "model"}
            for sid in u.get("cand_all") or u["cand"]:
                it = self.data.item(sid)
                if it is not None and sid not in have and rec.id in it.cited:
                    have[sid] = {"target_element": rec.id, "snippet_id": sid, "relation_type": "EXPLICIT_REFERENCE",
                                 "confidence": 0.95, "rationale": "EXPLICIT_REFERENCE (deterministic citation)",
                                 "source": "deterministic"}
            mods, unknown = M.resolve_modules(ans["modules"], self.data.module_index)
            d = {"external_effect": ans["external_effect"], "modules": mods, "modules_unresolved": unknown,
                 "effect_rationale": ans["effect_rationale"], "candidates": list(u["cand"]),
                 "stage2": {"status": "none"}, "rejected": rejected[:20],
                 "assignments": sorted(have.values(), key=lambda a: a["snippet_id"]),
                 "attempt": res.attempt}                    # type: ignore[attr-defined]
            if u.get("trimmed"):
                d["trimmed"] = u["trimmed"]
            res.bodies.append(self._decision_body(u, d, batch.prompt, profile, res.usd / n))


# ==============================================================================
# Bündel beschaffen, Code-Stand prüfen
# ==============================================================================

def obtain_bundle(a: argparse.Namespace, work: Path) -> core.Bundle:
    sha = (a.bundle_sha256 or "").strip().lower()
    if a.bundle_file:
        archive = Path(a.bundle_file)
    else:
        if not a.bundle_url:
            raise core.BundleError("weder --bundle-file noch --bundle-url angegeben")
        if not re.match(r"^[0-9a-f]{64}$", sha):
            raise core.BundleError("--bundle-sha256 (64 Hex-Zeichen) ist Pflicht beim Herunterladen")
        if not a.bundle_url.startswith("https://"):
            raise core.BundleError("--bundle-url muss https:// sein")
        cache = Path(a.bundle_cache) if a.bundle_cache else work
        cache.mkdir(parents=True, exist_ok=True)
        archive = cache / f"live-bundle-{sha}.tar.gz"
        if not archive.exists() or core.file_sha256(archive) != sha:
            tmp = archive.with_suffix(".part")
            req = urllib.request.Request(a.bundle_url, headers={"User-Agent": "autodocs-live-distribution"})
            with urllib.request.urlopen(req, timeout=300) as resp, open(tmp, "wb") as fh:
                shutil.copyfileobj(resp, fh, 1 << 20)
            os.replace(tmp, archive)
            log(f"Bündel geladen: {archive.stat().st_size / 1e6:.1f} MB")
    return core.open_bundle(archive, work / "bundle", sha or None)


def check_code(bundle: core.Bundle) -> List[str]:
    want = bundle.manifest.get("code") or {}
    have = core.code_hashes(HERE)
    return [f"{n}: Bündel {want.get(n, '-')[:12]} / Job {have.get(n, '-')[:12]}" for n in core.CODE_FILES
            if want.get(n) != have.get(n)]


# ==============================================================================
# Status, Commit
# ==============================================================================

def profile_state(path: Optional[Path]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    try:
        st = json.loads(Path(path).read_text(encoding="utf-8")) if path else {}
    except (OSError, ValueError):
        st = {}
    now = time.time()
    for name, s in sorted(st.items()):
        if not re.match(r"^[a-z0-9-]{1,20}$", str(name)):
            continue
        until = float(s.get("cooldown_until") or 0)
        out[name] = {"needs_login": bool(s.get("needs_login")),
                     "cooldown_until": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(until)) if until > now else None}
    return out


def _median(values: List[float]) -> float:
    values = sorted(values)
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2.0


def _finite_projection(value: Any) -> Optional[float]:
    """Return a non-negative finite public metric, otherwise no estimate."""
    try:
        projected = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return projected if math.isfinite(projected) and projected >= 0 else None


def _finite_sum(values: List[float]) -> Optional[float]:
    try:
        return _finite_projection(math.fsum(values))
    except OverflowError:
        return None


def _valid_scheduled_at(value: Any) -> bool:
    if not isinstance(value, str) or not SCHEDULED_AT_RE.fullmatch(value):
        return False
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.tzinfo == timezone.utc


def _scheduled_sample(trigger: Any) -> bool:
    return (isinstance(trigger, dict) and trigger.get("kind") == "scheduled"
            and trigger.get("provenance") == "dispatcher-declared"
            and _valid_scheduled_at(trigger.get("scheduled_at")))


def _trigger() -> Dict[str, Any]:
    event = os.environ.get("GITHUB_EVENT_NAME", "").strip()
    if event == "schedule":
        return {"kind": "scheduled", "cadence_seconds": SCHEDULE_CADENCE_SECONDS,
                "provenance": "github-event", "scheduled_at": None}
    if event == "workflow_dispatch":
        # workflow_dispatch is used both by humans and by the Cloudflare cron.
        # The marker is dispatcher-declared provenance, not a cryptographic
        # attestation; only the exact pair emitted by live-cron.mjs is counted
        # as a scheduled performance sample.
        kind = os.environ.get("AUTODOCS_TRIGGER_KIND", "").strip()
        scheduled_at = os.environ.get("AUTODOCS_SCHEDULED_AT", "").strip()
        if kind == "cloudflare-schedule" and _valid_scheduled_at(scheduled_at):
            return {"kind": "scheduled", "cadence_seconds": SCHEDULE_CADENCE_SECONDS,
                    "provenance": "dispatcher-declared", "scheduled_at": scheduled_at}
        return {"kind": "requested", "cadence_seconds": None,
                "provenance": "github-event", "scheduled_at": None}
    return {"kind": "local" if not event else "other", "cadence_seconds": None,
            "provenance": "local" if not event else "github-event", "scheduled_at": None}


def _performance_config(a: argparse.Namespace, concurrency: int, profiles: List[str]) -> Dict[str, Any]:
    profile_ids = sorted(Path(profile.rstrip("/")).name.removeprefix("agy-profile-") for profile in profiles)
    config = {
        "model": a.model,
        "effort": a.effort,
        # This is external-call concurrency.  It deliberately does not claim
        # CPU/vCPU assignment, which is owned by the build runtime.
        "external_call_concurrency": concurrency,
        "kinds": sorted(k for k in (a.kinds or "").split(",") if k) or list(core.UNIT_KINDS),
        "batch": {"snippet": a.batch_snippets, "figure": a.batch_figures, "element": a.batch_elements},
        "max_prompt_bytes": a.max_prompt_bytes,
        "call_timeout_seconds": a.call_timeout,
        "budget": {"max_calls": a.max_calls, "max_minutes": a.max_minutes, "max_usd": a.max_usd},
        "profiles": profile_ids,
    }
    raw = json.dumps(config, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**config, "key": hashlib.sha256(raw).hexdigest()[:16]}


def _performance(runs: List[Dict[str, Any]], plan_by_kind: Dict[str, Dict[str, int]],
                 config: Dict[str, Any]) -> Dict[str, Any]:
    """Robust, conservative ETA from usable same-config run samples.

    Active throughput measures productive worker time.  Scheduled yield is a
    separate wall-clock quantity: units per hourly scheduled invocation.
    Budget-time runs that still completed units after failed or timeout batches
    contribute realized yield and elapsed productive time.  Terminal errors,
    Productive capacity-stopped runs contribute censored positive observations;
    their zero-yield kinds do not.  Login failure, true errors, wholly
    unproductive exhaustion, malformed samples, and mismatched config stay
    excluded.  n=1 and n=2 emit provisional (low-confidence) estimates; the
    stable/high-confidence label is reserved for n>=3.  Overall ETA stays null
    while any still-open kind lacks supporting samples.
    """
    by_kind: Dict[str, Dict[str, Any]] = {}
    active_etas: List[float] = []
    active_lows: List[float] = []
    active_highs: List[float] = []
    scheduled_etas: List[float] = []
    scheduled_lows: List[float] = []
    scheduled_highs: List[float] = []
    active_counts: List[int] = []
    scheduled_counts: List[int] = []
    all_active_valid = True
    all_scheduled_valid = True
    all_scheduled_ranges_valid = True
    config_key = config.get("key") if isinstance(config.get("key"), str) and config.get("key") else None
    configured_kinds = config.get("kinds")
    selected_kinds = ({kind for kind in configured_kinds if kind in core.UNIT_KINDS}
                      if isinstance(configured_kinds, list) else set(core.UNIT_KINDS))
    for kind in core.UNIT_KINDS:
        active_rates: List[float] = []
        scheduled_yields: List[float] = []
        for run in runs:
            if not _usable_performance_run(run, config_key):
                continue
            censored = run.get("stop") == "exhausted"
            completed = (run.get("completed_by_kind") or {}).get(kind) if isinstance(run.get("completed_by_kind"), dict) else None
            elapsed = (run.get("elapsed_seconds_by_kind") or {}).get(kind) if isinstance(run.get("elapsed_seconds_by_kind"), dict) else None
            if (kind in selected_kinds and _scheduled_sample(run.get("trigger"))
                    and isinstance(completed, int) and not isinstance(completed, bool) and completed >= 0
                    and (not censored or completed > 0)):
                scheduled_yields.append(float(completed))
            if (isinstance(completed, int) and not isinstance(completed, bool) and completed > 0
                    and isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool)
                    and math.isfinite(float(elapsed)) and elapsed > 0):
                try:
                    rate, completed_float = completed / float(elapsed), float(completed)
                except (OverflowError, ZeroDivisionError):
                    continue
                if not math.isfinite(rate) or not math.isfinite(completed_float) or rate <= 0:
                    continue
                active_rates.append(rate)
        remaining = max(0, int((plan_by_kind.get(kind) or {}).get("planned", 0))
                        - int((plan_by_kind.get(kind) or {}).get("done", 0)))
        n_active, n_scheduled = len(active_rates), len(scheduled_yields)
        scheduled_center = _median(scheduled_yields) if n_scheduled else 0.0
        active_ok = n_active >= 1
        scheduled_ok = n_scheduled >= 1 and math.isfinite(scheduled_center) and scheduled_center > 0
        active_eta = scheduled_eta = None
        active_range = scheduled_range = None
        if remaining == 0:
            active_eta = scheduled_eta = 0.0
            active_range = scheduled_range = [0.0, 0.0]
        else:
            if active_ok:
                median_rate = _median(active_rates)
                active_eta = _finite_projection(remaining / median_rate)
                active_range = [_finite_projection(remaining / max(active_rates)),
                                _finite_projection(remaining / min(active_rates))]
                throughput = _finite_projection(median_rate * 60.0)
                if active_eta is not None and None not in active_range and throughput is not None:
                    active_range = [float(active_range[0]), float(active_range[1])]
                    active_etas.append(active_eta)
                    active_lows.append(active_range[0])
                    active_highs.append(active_range[1])
                    active_counts.append(n_active)
                else:
                    active_ok = False
            if not active_ok:
                active_eta = active_range = None
                all_active_valid = False
            if scheduled_ok:
                scheduled_eta = _finite_projection(remaining / scheduled_center * SCHEDULE_CADENCE_SECONDS)
                scheduled_range = None
                if min(scheduled_yields) > 0:
                    projected_range = [
                        _finite_projection(remaining / max(scheduled_yields) * SCHEDULE_CADENCE_SECONDS),
                        _finite_projection(remaining / min(scheduled_yields) * SCHEDULE_CADENCE_SECONDS),
                    ]
                    if None not in projected_range:
                        scheduled_range = [float(projected_range[0]), float(projected_range[1])]
                scheduled_yield = _finite_projection(scheduled_center)
                if scheduled_eta is not None and scheduled_yield is not None:
                    scheduled_etas.append(scheduled_eta)
                    if scheduled_range is not None:
                        scheduled_lows.append(scheduled_range[0])
                        scheduled_highs.append(scheduled_range[1])
                    else:
                        all_scheduled_ranges_valid = False
                    scheduled_counts.append(n_scheduled)
                else:
                    scheduled_ok = False
            if not scheduled_ok:
                scheduled_eta = scheduled_range = None
                all_scheduled_valid = False
        by_kind[kind] = {
            "remaining": remaining,
            "active": {
                "eta_seconds": round(active_eta, 1) if active_eta is not None else None,
                "range_seconds": [round(v, 1) for v in active_range] if active_range else None,
                "sample_count": n_active,
                "throughput_per_minute": round(_median(active_rates) * 60.0, 3) if active_ok else None,
                "confidence": _confidence(n_active, remaining=remaining, eta_ok=active_ok and active_eta is not None),
            },
            "scheduled": {
                "eta_seconds": round(scheduled_eta, 1) if scheduled_eta is not None else None,
                "range_seconds": [round(v, 1) for v in scheduled_range] if scheduled_range else None,
                "sample_count": n_scheduled,
                "yield_per_hour": round(scheduled_center, 3) if scheduled_ok else None,
                "confidence": _confidence(n_scheduled, remaining=remaining,
                                          eta_ok=scheduled_ok and scheduled_eta is not None),
            },
        }
    remaining_total = sum(item["remaining"] for item in by_kind.values())
    active_total = _finite_sum(active_etas)
    active_low_total = _finite_sum(active_lows)
    active_high_total = _finite_sum(active_highs)
    # Each kind's yield already includes zero progress in scheduled
    # invocations that worked on another selected kind.  The estimates are
    # therefore calendar rates; shared invocations finish when the slowest
    # remaining kind finishes, rather than being summed once per kind.
    scheduled_total = max(scheduled_etas, default=0.0)
    scheduled_low_total = max(scheduled_lows, default=0.0)
    scheduled_high_total = max(scheduled_highs, default=0.0)
    if remaining_total and (active_total is None or active_low_total is None or active_high_total is None):
        all_active_valid = False
    active_n = min(active_counts) if active_counts else 0
    scheduled_n = min(scheduled_counts) if scheduled_counts else 0
    return {
        "basis": ("active median and scheduled calendar median of successful same-config runs; "
                  "low-confidence/provisional at 1–2 samples per remaining kind, "
                  "stable/high-confidence at 3+"),
        "minimum_samples_per_kind": 1,
        "stable_samples_per_kind": PERFORMANCE_STABLE_SAMPLES,
        "active": {
            "eta_seconds": (0.0 if not remaining_total else round(active_total, 1)) if all_active_valid else None,
            "range_seconds": ([0.0, 0.0] if not remaining_total else
                              [round(active_low_total, 1), round(active_high_total, 1)]) if all_active_valid else None,
            "sample_count": active_n,
            "confidence": _confidence(active_n, remaining=remaining_total, eta_ok=all_active_valid),
        },
        "scheduled": {
            "eta_seconds": (0.0 if not remaining_total else round(scheduled_total, 1)) if all_scheduled_valid else None,
            "range_seconds": ([0.0, 0.0] if not remaining_total else
                              [round(scheduled_low_total, 1), round(scheduled_high_total, 1)])
                              if all_scheduled_valid and all_scheduled_ranges_valid else None,
            "sample_count": scheduled_n,
            "cadence_seconds": SCHEDULE_CADENCE_SECONDS,
            "confidence": _confidence(scheduled_n, remaining=remaining_total,
                                      eta_ok=all_scheduled_valid and (not remaining_total or scheduled_etas)),
        },
        "by_kind": by_kind,
    }


def build_status(live: core.LiveLog, plan: List[Dict[str, Any]], bundle: core.Bundle, state: Optional[Path],
                 config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    decided = live.decided_keys()
    by_kind: Dict[str, Dict[str, int]] = {}
    for u in plan:
        b = by_kind.setdefault(u["kind"], {"planned": 0, "done": 0})
        b["planned"] += 1
        b["done"] += 1 if u["key"] in decided else 0
    total = sum(b["planned"] for b in by_kind.values())
    done = sum(b["done"] for b in by_kind.values())
    runs = [e for e in live.entries if e.get("kind") == "run"]
    config = config or ((runs[-1].get("config") or {}) if runs else {})
    findings: Dict[str, int] = {}
    for e in live.entries:
        if e.get("kind") == "finding":
            c = e["finding"].get("class", "other")
            findings[c] = findings.get(c, 0) + 1
    head = live.head
    last_error_run = next((run for run in reversed(runs) if _aborted_stop(run.get("stop"))), None)
    return {
        "schema": "live-status@v1",
        "updated": core.utc_now(),
        "chain": {"seq": head["seq"] if head else 0, "hash12": head["hash"][:12] if head else None,
                  "decisions": len(live.decisions())},
        "bundle": {"sha12": bundle.sha256[:12], "created": bundle.manifest.get("created"),
                   "source_commit": (bundle.manifest.get("source_commit") or "")[:12]},
        "plan": {"total": total, "done": done, "remaining": total - done,
                 "progress": round(done / total, 4) if total else 1.0, "by_kind": by_kind},
        "cost": {"list_price_usd_total": round(sum(float(r.get("list_price_usd") or 0) for r in runs), 4),
                 "runs": len(runs), "currency": "USD, API-Listenpreise"},
        "last_runs": [{k: r.get(k) for k in ("run", "started", "ended", "stop", "calls", "decided", "findings", "list_price_usd",
                                              "profiles", "remaining", "elapsed_seconds", "completed_per_minute",
                                              "eta_seconds", "failed_batches", "skipped_units",
                                              "error_diagnostics", "trigger", "config_key", "completed_by_kind",
                                              "elapsed_seconds_by_kind")} for r in runs[-10:]],
        "findings": findings,
        "profiles": profile_state(state),
        "worker": {
            "state": "idle",
            "trigger": (runs[-1].get("trigger") if runs else None) or _trigger(),
            "config": config,
            "last_error": (_last_error_view(last_error_run) if last_error_run else None),
        },
        "performance": _performance(runs, by_kind, config),
    }


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=_git_env(), check=check)


def is_git(repo: Path) -> bool:
    return (repo / ".git").exists() and shutil.which("git") is not None


def commit(repo: Path, message: str) -> bool:
    if not is_git(repo):
        return False
    paths = [p for p in (core.CHAIN_DIR, "status") if (repo / p).exists()]
    if not paths:
        return False
    git(repo, "add", "-A", "--", *paths)
    if not git(repo, "diff", "--cached", "--quiet", check=False).returncode:
        return False
    git(repo, "commit", "-q", "-m", message)
    return True


def uncommitted_segments(repo: Path) -> List[Path]:
    seg = segment_dir(repo)
    if not seg.is_dir():
        return []
    if not is_git(repo):
        return []
    out = git(repo, "status", "--porcelain", "--untracked-files=all", "--", core.LOG_DIR, check=False).stdout
    return [repo / line[3:].strip() for line in out.splitlines() if line[3:].strip().endswith(".jsonl")]


def segment_dir(repo: Path) -> Path:
    return Path(repo) / core.LOG_DIR


# ==============================================================================
# Befehle
# ==============================================================================

def prepare(a: argparse.Namespace, work: Path, repo: Path):
    """Bündel, Code-Stand, Kette und offene Einheiten. Rückgabe (rc, bundle, live, plan, todo)."""
    try:
        bundle = obtain_bundle(a, work)
    except (core.BundleError, OSError, ValueError) as exc:
        log(f"Bündel unbrauchbar: {exc}")
        return (EXIT_DATA if isinstance(exc, core.BundleError) else EXIT_CONFIG), None, None, None, None
    drift = check_code(bundle)
    if drift:
        log("Code-Stand des Jobs passt nicht zum Bündel (live_bundle.py vendor ausführen): " + "; ".join(drift))
        return EXIT_CONFIG, None, None, None, None
    try:
        live = core.LiveLog(repo)
    except core.ChainError as exc:
        log(f"Kette in autodocs-live ungültig: {exc}")
        return EXIT_DATA, None, None, None, None
    head = bundle.live_head()
    if head and not core.contains(live.state, head):
        log(f"Kette enthält den Kopf des Bündels nicht (seq {head.get('seq')}, {str(head.get('hash'))[:12]}): Historie umgeschrieben?")
        return EXIT_DATA, None, None, None, None
    plan = list(bundle.rows("plan.jsonl"))
    decided = live.decided_keys()
    kinds = set(k for k in (a.kinds or "").split(",") if k) or set(core.UNIT_KINDS)
    todo = [u for u in plan if u["key"] not in decided and u["kind"] in kinds]
    counts = {k: sum(1 for u in todo if u["kind"] == k) for k in core.UNIT_KINDS}
    log(f"Bündel {bundle.sha256[:12]} (Quelle {(bundle.manifest.get('source_commit') or '?')[:10]}), Kette {len(live.entries)} "
        f"Glieder, Plan {len(plan)} Einheiten, offen {len(todo)} " + " ".join(f"{k}={v}" for k, v in counts.items()))
    return EXIT_OK, bundle, live, plan, todo


def cmd_pending(a: argparse.Namespace) -> int:
    """Nur zählen (vor der Einrichtung von agy): ``pending=<n>`` nach $GITHUB_OUTPUT bzw. --github-output."""
    rc, _bundle, _live, plan, todo = prepare(a, Path(a.work or tempfile.mkdtemp(prefix="live-work-")), Path(a.live_repo))
    n = len(todo) if todo is not None else 0
    out = a.github_output or os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"pending={n if rc == EXIT_OK else 'error'}\nrc={rc}\n")
    if rc == EXIT_OK and plan is not None and todo is not None:
        publish_live_worker(event="progress", phase="pending", state="idle" if not n else "active",
                            done=len(plan) - n, total=len(plan),
                            progress_by_kind=absolute_progress_by_kind(plan, todo),
                            counters={"remaining": n, "planned": len(plan)})
    if rc == EXIT_OK and not n:
        log("nichts zu tun")
    return rc


def cmd_run(a: argparse.Namespace) -> int:
    run_id = a.run_id or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    work = Path(a.work or tempfile.mkdtemp(prefix="live-work-"))
    repo = Path(a.live_repo)
    rc, bundle, live, plan, todo = prepare(a, work, repo)
    if rc != EXIT_OK:
        return rc
    base_done = len(plan) - len(todo)
    plan_total = len(plan)
    initial_progress_by_kind = absolute_progress_by_kind(plan, todo)
    publish_live_worker(event="progress", phase="distribute", state="active" if todo else "idle",
                        done=base_done, total=plan_total,
                        progress_by_kind=initial_progress_by_kind,
                        counters={"remaining": len(todo), "completed": 0, "calls": 0,
                                  "started_calls": 0, "in_flight_calls": 0, "failed_batches": 0,
                                  "elapsed_seconds": 0.0})
    if not todo:
        log("nichts zu tun")
        return EXIT_OK
    data = Data(bundle)
    budget = Budget(a.max_calls, a.max_minutes, a.max_usd)
    if a.dry_run:
        job = Job(a, bundle, data, live, None, budget, run_id)
        sizes = []
        for b in job.batches(todo):
            sizes.append(len(b.prompt.encode("utf-8")))
            if len(sizes) >= max(1, a.max_calls or 20):
                break
        log(f"Trockenlauf: erste {len(sizes)} Batches, Prompt-Bytes Median {sorted(sizes)[len(sizes) // 2] if sizes else 0}, "
            f"Maximum {max(sizes) if sizes else 0}; kein Modellaufruf")
        publish_live_worker(event="terminal", phase="terminal", state="idle", done=base_done, total=plan_total,
                            progress_by_kind=initial_progress_by_kind,
                            counters={"remaining": len(todo), "completed": 0, "calls": 0,
                                      "started_calls": 0, "in_flight_calls": 0, "failed_batches": 0,
                                      "elapsed_seconds": 0.0},
                            outcome="ok", reason="dry-run", ended=True)
        return EXIT_OK
    base_profiles = [p for p in os.environ.get("AUTODOCS_AGY_PROFILES", "").split(",") if p]
    if not base_profiles:
        log("keine agy-Profile (setup-agy, AUTODOCS_AGY_PROFILES)")
        publish_live_worker(event="terminal", phase="terminal", state="error", done=base_done, total=plan_total,
                            progress_by_kind=initial_progress_by_kind,
                            counters={"remaining": len(todo), "completed": 0, "calls": 0,
                                      "started_calls": 0, "in_flight_calls": 0, "failed_batches": 0,
                                      "elapsed_seconds": 0.0},
                            outcome="needs-login", reason="needs-login",
                            ended=True)
        return EXIT_LOGIN
    state = Path(a.state or os.environ.get("AGY_STATE") or (work / "agy-state.json"))
    agy = Agy(Path(a.switch), state, a.model, a.effort, a.call_timeout, a.python)
    slots_root = Path(a.slots or (work / "agy-workers"))
    slots = [Slot(i, base_profiles, slots_root) for i in range(max(1, a.concurrency))]
    performance_config = _performance_config(a, len(slots), base_profiles)
    trigger = _trigger()
    free: List[Slot] = list(slots)
    job = Job(a, bundle, data, live, agy, budget, run_id)
    new_decisions: List[Dict[str, Any]] = []
    tot = {"calls": 0, "retries": 0, "stage2_calls": 0, "usd": 0.0, "failed_batches": 0, "unanswered": 0,
           "incomplete": 0, "tokens": {"input": 0, "cached": 0, "output": 0, "thinking": 0}, "profiles": {},
           "by_kind": {k: 0 for k in core.UNIT_KINDS},
           "completed_by_kind": {k: 0 for k in core.UNIT_KINDS},
           "completed": 0, "diagnostics": {}}
    consecutive_fail = 0
    progress_sent = False
    started = core.utc_now()
    gen = job.batches(todo)
    in_flight: Dict[Any, Tuple[Slot, str]] = {}
    pending: Optional[Batch] = None
    exhausted_gen = False
    kind_active_since: Dict[str, float] = {}
    kind_active_count = {kind: 0 for kind in core.UNIT_KINDS}
    kind_elapsed = {kind: 0.0 for kind in core.UNIT_KINDS}
    last_telemetry_at = time.monotonic()
    with ThreadPoolExecutor(max_workers=len(slots)) as ex:
        while True:
            while free and not exhausted_gen and not budget.reason():
                if pending is None:
                    pending = next(gen, None)
                    if pending is None:
                        exhausted_gen = True
                        break
                slot = free.pop()
                dispatch_at = time.monotonic()
                if kind_active_count[pending.kind] == 0:
                    kind_active_since[pending.kind] = dispatch_at
                kind_active_count[pending.kind] += 1
                in_flight[ex.submit(job.process, pending, slot)] = (slot, pending.kind)
                pending = None
            if not in_flight:
                break
            hb_interval = float(HEARTBEAT_INTERVAL_S)
            wait_timeout = max(0.0, (last_telemetry_at + hb_interval) - time.monotonic())
            done, _ = wait(list(in_flight), timeout=wait_timeout, return_when=FIRST_COMPLETED)
            if not done:
                started_calls, in_flight_calls = job.call_counts()
                elapsed = max(0.001, time.monotonic() - budget.t0)
                remain_now = max(0, len(todo) - tot["completed"])
                publish_live_worker(
                    event="progress", phase="distribute", state="active",
                    done=base_done + tot["completed"], total=plan_total,
                    progress_by_kind=absolute_progress_by_kind(plan, todo, tot["completed_by_kind"]),
                    counters=distribution_worker_counters(
                        calls=tot["calls"], started_calls=started_calls,
                        in_flight_calls=in_flight_calls, completed=tot["completed"],
                        failed_batches=tot["failed_batches"], remaining=remain_now,
                        elapsed_seconds=round(elapsed, 3),
                        completed_by_kind=tot["completed_by_kind"]))
                last_telemetry_at = time.monotonic()
                continue
            emitted_in_batch = False
            for f in done:
                slot, batch_kind = in_flight.pop(f)
                finished_at = time.monotonic()
                kind_active_count[batch_kind] = max(0, kind_active_count[batch_kind] - 1)
                if kind_active_count[batch_kind] == 0:
                    kind_elapsed[batch_kind] += max(0.0, finished_at - kind_active_since.pop(batch_kind, finished_at))
                free.append(slot)
                try:
                    r: BatchResult = f.result()
                except Exception as exc:
                    # Job.process already contains the normal exception boundary. Keep
                    # the coordinator fail-closed as a final guard in case construction
                    # or future wrapper code fails outside that boundary.
                    key = f"coordinator:{type(exc).__name__}"
                    tot["diagnostics"][key] = tot["diagnostics"].get(key, 0) + 1
                    tot["failed_batches"] += 1
                    consecutive_fail += 1
                    log(f"Worker ohne Ergebnis ({batch_kind}): {type(exc).__name__}")
                    if consecutive_fail >= a.max_failures:
                        budget.halt("errors")
                    continue
                for body in r.bodies:
                    e = live.append(body)
                    new_decisions.append(e)
                    tot["by_kind"][e["unit_kind"]] += 1
                    if core.decision_complete(e):
                        tot["completed"] += 1
                        tot["completed_by_kind"][e["unit_kind"]] += 1
                tot["calls"] += r.calls
                tot["retries"] += r.retries
                tot["stage2_calls"] += r.stage2_calls
                tot["usd"] += r.usd
                tot["unanswered"] += r.unanswered
                tot["incomplete"] += r.incomplete
                for k in tot["tokens"]:
                    tot["tokens"][k] += r.tokens.get(k, 0)
                for p, n in r.profiles.items():
                    tot["profiles"][p] = tot["profiles"].get(p, 0) + n
                for d, n in r.diagnostics.items():
                    tot["diagnostics"][d] = tot["diagnostics"].get(d, 0) + n
                if r.bodies:
                    consecutive_fail = 0
                    elapsed = max(0.001, time.monotonic() - budget.t0)
                    remain_now = max(0, len(todo) - tot["completed"])
                    crossed = bool(len(new_decisions) and len(new_decisions) % 50 < len(r.bodies))
                    if crossed:
                        per_minute = tot["completed"] * 60.0 / elapsed
                        eta = remain_now * 60.0 / per_minute if per_minute else None
                        eta_text = f"{eta / 60.0:.1f} min" if eta is not None else "unbekannt"
                        log(f"Fortschritt: {len(new_decisions)} Entscheidungen, {tot['calls']} Aufrufe, "
                            f"{tot['usd']:.3f} $ Listenpreis, {per_minute:.1f}/min, "
                            f"offen {remain_now}, ETA {eta_text}")
                    if not progress_sent or crossed or (time.monotonic() - last_telemetry_at >= hb_interval):
                        progress_sent = True
                        emitted_in_batch = True
                        started_calls, in_flight_calls = job.call_counts()
                        publish_live_worker(
                            event="progress", phase="distribute", state="active",
                            done=base_done + tot["completed"], total=plan_total,
                            progress_by_kind=absolute_progress_by_kind(plan, todo, tot["completed_by_kind"]),
                            counters=distribution_worker_counters(
                                calls=tot["calls"], started_calls=started_calls,
                                in_flight_calls=in_flight_calls, completed=tot["completed"],
                                failed_batches=tot["failed_batches"], remaining=remain_now,
                                elapsed_seconds=round(elapsed, 3),
                                completed_by_kind=tot["completed_by_kind"]))
                        last_telemetry_at = time.monotonic()
                elif r.outcome not in ("budget", "exhausted", "login"):
                    tot["failed_batches"] += 1
                    consecutive_fail += 1
                    detail = ",".join(sorted(r.diagnostics)) or "ohne Diagnose"
                    log(f"Batch ohne Ergebnis ({r.batch.kind}, {len(r.batch.units)} Einheiten): {r.outcome} [{detail}]")
                    if consecutive_fail >= a.max_failures:
                        budget.halt("errors")
            if not emitted_in_batch and (time.monotonic() - last_telemetry_at >= hb_interval):
                started_calls, in_flight_calls = job.call_counts()
                elapsed = max(0.001, time.monotonic() - budget.t0)
                remain_now = max(0, len(todo) - tot["completed"])
                publish_live_worker(
                    event="progress", phase="distribute", state="active",
                    done=base_done + tot["completed"], total=plan_total,
                    progress_by_kind=absolute_progress_by_kind(plan, todo, tot["completed_by_kind"]),
                    counters=distribution_worker_counters(
                        calls=tot["calls"], started_calls=started_calls,
                        in_flight_calls=in_flight_calls, completed=tot["completed"],
                        failed_batches=tot["failed_batches"], remaining=remain_now,
                        elapsed_seconds=round(elapsed, 3),
                        completed_by_kind=tot["completed_by_kind"]))
                last_telemetry_at = time.monotonic()
    # Patrouille Stufe 1: Prüfregeln über die neuen Entscheidungen
    findings_new = run_validators(bundle, data, live, new_decisions, run_id)
    known = live.finding_ids()
    n_findings = 0
    for f in findings_new:
        if f["id"] in known:
            continue
        live.append({"kind": "finding", "finding": f, "unit": f["subject"]["id"], "run": run_id, "at": core.utc_now()})
        known.add(f["id"])
        n_findings += 1
    completed_now = tot["completed"]
    remaining = len(todo) - completed_now
    # Erschöpfter Generator bei offener Arbeit ist niemals ``done``. Das deckt
    # auch Exceptions vor dem ersten Modellaufruf und übersprungene Einheiten ab.
    # Ein erschöpftes Ein-Aufruf-Budget darf einen vollständig unproduktiven
    # Fehlerlauf nicht als erfolgreichen Budget-Stopp maskieren (Canary-Fall).
    stop = ("errors" if tot["failed_batches"] and not new_decisions
            else budget.reason() or ("errors" if remaining else "done"))
    elapsed_s = max(0.0, time.monotonic() - budget.t0)
    elapsed_by_kind = {kind: round(seconds, 3) if seconds > 0 else None
                       for kind, seconds in kind_elapsed.items()}
    per_minute = completed_now * 60.0 / elapsed_s if elapsed_s > 0 else 0.0
    eta_s = (remaining * elapsed_s / completed_now
             if completed_now and stop not in ("errors", "exhausted", "needs-login") else None)
    run_entry = {"kind": "run", "run": run_id, "at": core.utc_now(), "started": started, "ended": core.utc_now(),
                 "stop": stop, "assets": dict(job.assets, source_commit=bundle.manifest.get("source_commit"),
                                              created=bundle.manifest.get("created")),
                 "code": core.code_hashes(HERE),
                 "model": a.model, "effort": a.effort, "concurrency": len(slots),
                 "trigger": trigger, "config": performance_config, "config_key": performance_config["key"],
                 "budget": {"max_calls": a.max_calls, "max_minutes": a.max_minutes, "max_usd": a.max_usd},
                 "calls": tot["calls"], "retries": tot["retries"], "stage2_calls": tot["stage2_calls"],
                 "failed_batches": tot["failed_batches"], "unanswered_units": tot["unanswered"],
                 "incomplete": tot["incomplete"], "decided": len(new_decisions), "decided_by_kind": tot["by_kind"],
                 "completed_by_kind": tot["completed_by_kind"],
                 "findings": n_findings, "tokens": tot["tokens"], "list_price_usd": round(tot["usd"], 6),
                 "profiles": tot["profiles"], "remaining": remaining,
                 "error_diagnostics": tot["diagnostics"],
                 "skipped_units": job.skipped, "elapsed_seconds": round(elapsed_s, 3),
                 "elapsed_seconds_by_kind": elapsed_by_kind,
                 "completed_per_minute": round(per_minute, 3),
                 "eta_seconds": round(eta_s, 1) if eta_s is not None else None}
    # Auch ein Null-Aufruf-Fehler ist ein Lauf: Er muss in Status und Historie
    # erscheinen, damit unverändert offene Arbeit nicht wie Erfolg aussieht.
    if tot["calls"] or new_decisions or tot["failed_batches"] or remaining:
        live.append(run_entry)
        live.write_pointer(run_id, bundle.sha256[:12])
        core.write_atomic(repo / core.STATUS_FILE, (json.dumps(build_status(live, plan, bundle, state,
                                                               performance_config), indent=1,
                                                               sort_keys=True, ensure_ascii=False,
                                                               allow_nan=False) + "\n").encode())
        check = core.verify_chain(repo)
        chain_ok = check.ok
        if not chain_ok:
            log("Kette nach dem Schreiben ungültig: " + "; ".join(check.errors[:3]))
        elif a.commit:
            commit(repo, f"live-distribution {run_id}: {len(new_decisions)} Entscheidungen, {n_findings} Befunde, "
                         f"{tot['calls']} Aufrufe, {tot['usd']:.2f} $ Listenpreis")
    else:
        chain_ok = True
    outcome, reason, worker_state_name = _run_terminal_fields(stop)
    if not chain_ok:
        outcome, reason, worker_state_name = "error", "chain", "error"
    try:
        perf = build_status(live, plan, bundle, state, performance_config).get("performance")
    except Exception:
        perf = None
    started_calls, _ = job.call_counts()
    publish_live_worker(event="terminal", phase="terminal", state=worker_state_name,
                        done=base_done + completed_now, total=plan_total,
                        progress_by_kind=absolute_progress_by_kind(plan, todo, tot["completed_by_kind"]),
                        counters=distribution_worker_counters(
                            calls=tot["calls"], started_calls=started_calls,
                            in_flight_calls=0, completed=tot["completed"],
                            failed_batches=tot["failed_batches"], remaining=remaining,
                            elapsed_seconds=round(elapsed_s, 3),
                            completed_by_kind=tot["completed_by_kind"]),
                        outcome=outcome, reason=reason, performance=perf, ended=True)
    if not chain_ok:
        return EXIT_DATA
    prof = ", ".join(f"{p} {n}" for p, n in sorted(tot["profiles"].items())) or "-"
    log(f"Ende ({stop}): {len(new_decisions)} Entscheidungen " + " ".join(f"{k}={v}" for k, v in tot["by_kind"].items())
        + f", {n_findings} Befunde, {tot['calls']} Aufrufe (Wiederholungen {tot['retries']}, Stufe 2 {tot['stage2_calls']}), "
        f"Tokens ein {tot['tokens']['input']} aus {tot['tokens']['output']}, {tot['usd']:.4f} $ Listenpreis, "
        f"Profile {prof}, offen {remaining}")
    if stop == "exhausted":
        return EXIT_EXHAUSTED
    if stop == "needs-login":
        return EXIT_LOGIN
    if stop == "errors":
        return EXIT_ERROR
    return EXIT_OK


def run_validators(bundle: core.Bundle, data: Data, live: core.LiveLog, new: List[Dict[str, Any]], run_id: str) -> List[Dict[str, Any]]:
    if not new:
        return []
    refs = {core.split_unit(e["unit"])[1] for e in new}
    refs |= {a["snippet_id"] for e in new for a in (e.get("decision") or {}).get("assignments") or []}
    uni = data.universe(strong_matrix_rows(bundle, refs))
    out = core.validate_decisions(new, live.latest_decisions(), uni, run_id, all_decisions=live.decisions())
    for e in new:
        kind, ref = core.split_unit(e["unit"])
        if kind == "figure" and ref in data.figure_rows:
            row = data.figure_rows[ref]
            subject = ((row.get("description_source") or {}).get("figure_id")) or ref
            out += core.figure_text_findings(subject, row.get("description") or "", run_id)
    return core.fnd.merge(out)


def cmd_finalize(a: argparse.Namespace) -> int:
    repo = Path(a.live_repo)
    for seg in uncommitted_segments(repo):
        cut = core.repair_tail(repo, seg)
        if cut:
            log(f"unvollständige letzte Zeile in {seg.name} entfernt ({cut} Bytes)")
    state = core.verify_chain(repo, check_pointer=False)
    if not state.ok:
        log("Kette ungültig: " + "; ".join(state.errors[:5]))
        return EXIT_DATA
    if state.head:
        ptr = state.pointer or {}
        if ptr.get("hash") != state.head["hash"]:
            live = core.LiveLog(repo, allow_invalid=True)
            runs = [e for e in live.entries if e.get("kind") == "run"]
            live.write_pointer(runs[-1]["run"] if runs else "finalize", ptr.get("basis"))
            log("Zeiger auf den Kopf der Kette gesetzt")
    final = core.verify_chain(repo)
    if not final.ok:
        log("Kette ungültig: " + "; ".join(final.errors[:5]))
        return EXIT_DATA
    if a.commit and commit(repo, f"live-distribution: Abschluss bei Glied {final.head['seq'] if final.head else 0}"):
        log("Abschluss-Commit erstellt")
    log(f"Kette gültig: {len(final.entries)} Glieder, Kopf {final.head['hash'][:12] if final.head else '-'}")
    return EXIT_OK


def cmd_verify(a: argparse.Namespace) -> int:
    state = core.verify_chain(Path(a.live_repo))
    if not state.ok:
        for err in state.errors[:20]:
            log("Fehler: " + err)
        return EXIT_DATA
    if a.bundle_file:
        b = core.open_bundle(Path(a.bundle_file), Path(tempfile.mkdtemp(prefix="live-verify-")), a.bundle_sha256 or None)
        if not core.contains(state, b.live_head()):
            log("Kette enthält den Kopf des Bündels nicht")
            return EXIT_DATA
    log(f"Kette gültig: {len(state.entries)} Glieder in {len(state.segments)} Segmenten")
    return EXIT_OK


def cmd_status(a: argparse.Namespace) -> int:
    p = Path(a.live_repo) / core.STATUS_FILE
    if not p.exists():
        log("noch kein Status")
        return EXIT_OK
    st = json.loads(p.read_text(encoding="utf-8"))
    pl = st.get("plan", {})
    log(f"Fortschritt {pl.get('done')}/{pl.get('total')} ({100 * float(pl.get('progress') or 0):.1f} %), "
        f"Kosten gesamt {st.get('cost', {}).get('list_price_usd_total')} $ Listenpreis, Läufe {st.get('cost', {}).get('runs')}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def bundle_args(x: argparse.ArgumentParser) -> None:
        x.add_argument("--bundle-url", default=os.environ.get("LIVE_BUNDLE_URL", ""))
        x.add_argument("--bundle-sha256", default=os.environ.get("LIVE_BUNDLE_SHA256", ""))
        x.add_argument("--bundle-file", default=None)
        x.add_argument("--bundle-cache", default=None, help="Verzeichnis für heruntergeladene Bündel (Schlüssel: SHA-256)")
        x.add_argument("--live-repo", required=True, help="Arbeitsbaum von autodocs-live")
        x.add_argument("--work", default=None)
        x.add_argument("--kinds", default="", help="nur diese Arten (snippet,figure,element)")

    pe = sub.add_parser("pending", help="offene Einheiten zählen (ohne agy)")
    bundle_args(pe)
    pe.add_argument("--github-output", default=None)
    r = sub.add_parser("run", help="Plan abarbeiten")
    bundle_args(r)
    r.add_argument("--slots", default=None, help="Verzeichnis der Arbeitsplätze (Standard <work>/agy-workers)")
    r.add_argument("--switch", default=str(HERE / "agy_switch.py"))
    r.add_argument("--python", default=sys.executable)
    r.add_argument("--state", default=None, help="Sperrzustand der Profile (Standard $AGY_STATE)")
    r.add_argument("--model", default=core.DEFAULT_MODEL)
    r.add_argument("--effort", default=core.DEFAULT_EFFORT)
    r.add_argument("--max-calls", type=int, default=300)
    r.add_argument("--max-minutes", type=float, default=40.0)
    r.add_argument("--max-usd", type=float, default=0.0, help="Obergrenze in $ Listenpreis (0 = keine)")
    r.add_argument("--max-failures", type=int, default=5, help="aufeinanderfolgende Batches ohne Ergebnis bis zum Abbruch")
    r.add_argument("--concurrency", type=int, default=4)
    r.add_argument("--call-timeout", type=int, default=300)
    r.add_argument("--batch-snippets", type=int, default=BATCH["snippet"])
    r.add_argument("--batch-figures", type=int, default=BATCH["figure"])
    r.add_argument("--batch-elements", type=int, default=BATCH["element"])
    r.add_argument("--max-prompt-bytes", type=int, default=MAX_PROMPT_BYTES)
    r.add_argument("--run-id", default=None)
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--no-commit", dest="commit", action="store_false", default=True)
    f = sub.add_parser("finalize", help="Segmentende reparieren, Zeiger setzen, prüfen, committen")
    f.add_argument("--live-repo", required=True)
    f.add_argument("--commit", action="store_true")
    v = sub.add_parser("verify", help="Kette prüfen")
    v.add_argument("--live-repo", required=True)
    v.add_argument("--bundle-file", default=None)
    v.add_argument("--bundle-sha256", default=None)
    s = sub.add_parser("status", help="Fortschritt anzeigen")
    s.add_argument("--live-repo", required=True)
    d = sub.add_parser("dashboard", help="Live-Worker-Fragment senden (Start/Fortschritt/Ende, fehlertolerant)")
    d.add_argument("--event", choices=("start", "progress", "terminal"), required=True)
    d.add_argument("--phase", default="")
    d.add_argument("--state", default="")
    d.add_argument("--outcome", default="")
    d.add_argument("--reason", default="")
    d.add_argument("--done", type=int, default=None)
    d.add_argument("--total", type=int, default=None)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    a = build_parser().parse_args(argv)
    fn = {"run": cmd_run, "pending": cmd_pending, "finalize": cmd_finalize, "verify": cmd_verify,
          "status": cmd_status, "dashboard": cmd_dashboard}[a.cmd]
    if os.environ.get("LIVE_DEBUG") == "1":
        return fn(a)
    try:
        return fn(a)
    except Exception as exc:       # öffentliches Log: nur Art und Stelle, keine Meldung (sie könnte Daten enthalten)
        tb = exc.__traceback__
        while tb is not None and tb.tb_next is not None:
            tb = tb.tb_next
        where = f"{Path(tb.tb_frame.f_code.co_filename).name}:{tb.tb_lineno}" if tb else "?"
        log(f"unerwarteter Fehler {type(exc).__name__} in {where} (Details lokal mit LIVE_DEBUG=1)")
        return EXIT_ERROR


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _terminate)
    signal.signal(signal.SIGINT, _terminate)
    sys.exit(main())
