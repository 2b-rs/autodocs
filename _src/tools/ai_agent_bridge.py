"""AI Agent Bridge for Autodocs Backend.

Provides access to Gemini (via Google Antigravity CLI 'agy') and Cursor
(via Cursor Agent CLI 'agent') subscriptions for commentary generation and
segment translation, honoring the project's AI policy.

Features:
- Startup Model Discovery: Discovers installed CLIs, queries available models,
  and automatically selects the highest versioned flash model (Gemini) and composer (Cursor).
- Live Health Monitoring: Performs periodic availability tests via mini-prompt
  pings in a background daemon thread, measuring roundtrip latency and detecting outages.
- Failover: Automatically switches active model between primary (Gemini Flash)
  and fallback (Cursor Composer) based on health status.
- UI Reporting: Provides real-time status payloads for UI badges and diagnostics.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_LOGGER = logging.getLogger("autodocs.ai_agent_bridge")

TOOLS_DIR = Path(__file__).resolve().parent
SRC_DIR = TOOLS_DIR.parent
POLICY_PATH = SRC_DIR / "ai" / "policy.json"


def load_policy() -> dict:
    if POLICY_PATH.is_file():
        try:
            with open(POLICY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            _LOGGER.warning("Could not read policy from %s: %s", POLICY_PATH, exc)
    return {}


def get_agent_config() -> dict:
    policy = load_policy()
    model_sec = policy.get("modell") or {}
    primary = model_sec.get("primaer") or {
        "provider": "agy",
        "cli": "agy",
        "modell": "gemini-3.8-flash-high",
        "display_name": "Gemini 3.8 Flash (High)",
        "thinking_effort": "high",
        "subscription": "gemini",
    }
    fallback = model_sec.get("fallback") or {
        "provider": "cursor",
        "cli": "agent",
        "modell": "composer-2.5",
        "display_name": "Cursor Composer 2.5",
        "thinking_effort": "none",
        "subscription": "cursor",
    }
    return {
        "primary": primary,
        "fallback": fallback,
        "canonical_lang": policy.get("sprache_kanonisch", "de"),
    }


def check_subscriptions() -> Dict[str, Any]:
    """Check availability of gemini and cursor subscriptions and CLIs."""
    home = Path.home()
    gemini_dir = home / ".gemini"
    cursor_dir = home / ".cursor"

    agy_bin = shutil.which("agy") or "/usr/local/bin/agy"
    cursor_bin = shutil.which("agent") or str(home / ".local" / "bin" / "agent")

    gemini_auth = gemini_dir.is_dir()
    cursor_auth = cursor_dir.is_dir()

    return {
        "gemini": {
            "subscription_active": gemini_auth,
            "config_dir": str(gemini_dir) if gemini_auth else None,
            "cli_path": agy_bin if os.path.exists(agy_bin) else None,
            "available": bool(gemini_auth and os.path.exists(agy_bin)),
        },
        "cursor": {
            "subscription_active": cursor_auth,
            "config_dir": str(cursor_dir) if cursor_auth else None,
            "cli_path": cursor_bin if os.path.exists(cursor_bin) else None,
            "available": bool(cursor_auth and os.path.exists(cursor_bin)),
        },
    }


_DISCOVERY_CACHE: Optional[Dict[str, Any]] = None


def discover_models(refresh: bool = False) -> Dict[str, Any]:
    """Inspect installed CLIs, extract versions, and select best available models."""
    global _DISCOVERY_CACHE
    if not refresh and _DISCOVERY_CACHE is not None:
        return _DISCOVERY_CACHE

    subs = check_subscriptions()

    discovered: Dict[str, Any] = {
        "agy": {
            "available": subs["gemini"]["available"],
            "cli_path": subs["gemini"]["cli_path"],
            "cli_version": None,
            "selected_model": "gemini-3.8-flash-high",
            "display_name": "Gemini 3.8 Flash (High)",
            "thinking_effort": "high",
            "available_models": [],
        },
        "cursor": {
            "available": subs["cursor"]["available"],
            "cli_path": subs["cursor"]["cli_path"],
            "cli_version": None,
            "selected_model": "composer-2.5",
            "display_name": "Cursor Composer 2.5",
            "thinking_effort": "none",
            "available_models": [],
        },
    }

    # Discover Gemini via agy CLI
    agy_cli = subs["gemini"]["cli_path"]
    if agy_cli and os.path.exists(agy_cli):
        try:
            ver_res = subprocess.run([agy_cli, "--version"], capture_output=True, text=True, timeout=5)
            if ver_res.returncode == 0:
                discovered["agy"]["cli_version"] = ver_res.stdout.strip()
        except Exception as exc:
            _LOGGER.debug("agy --version failed: %s", exc)

        try:
            models_res = subprocess.run([agy_cli, "models"], capture_output=True, text=True, timeout=10)
            if models_res.returncode == 0:
                models_list = []
                for line in models_res.stdout.splitlines():
                    if "\t" in line:
                        mid, mname = line.split("\t", 1)
                        models_list.append({"id": mid.strip(), "name": mname.strip()})
                discovered["agy"]["available_models"] = models_list

                # Select best Flash model with High effort
                flash_high = [
                    m for m in models_list
                    if re.match(r"^gemini-[\d\.]+-flash-high$", m["id"])
                ]
                if flash_high:
                    def flash_ver_key(item: dict) -> tuple:
                        mat = re.search(r"gemini-([\d\.]+)-flash-high", item["id"])
                        if mat:
                            return tuple(int(x) for x in mat.group(1).split("."))
                        return ()
                    flash_high.sort(key=flash_ver_key, reverse=True)
                    discovered["agy"]["selected_model"] = flash_high[0]["id"]
                    discovered["agy"]["display_name"] = flash_high[0]["name"]
        except Exception as exc:
            _LOGGER.debug("agy models discovery failed: %s", exc)

    # Discover Cursor Agent CLI
    cursor_cli = subs["cursor"]["cli_path"]
    if cursor_cli and os.path.exists(cursor_cli):
        try:
            ver_res = subprocess.run([cursor_cli, "--version"], capture_output=True, text=True, timeout=5)
            if ver_res.returncode == 0:
                discovered["cursor"]["cli_version"] = ver_res.stdout.strip()
        except Exception as exc:
            _LOGGER.debug("cursor agent --version failed: %s", exc)

        try:
            models_res = subprocess.run([cursor_cli, "models"], capture_output=True, text=True, timeout=10)
            if models_res.returncode == 0:
                models_list = []
                for line in models_res.stdout.splitlines():
                    if " - " in line:
                        mid, mname = line.split(" - ", 1)
                        models_list.append({"id": mid.strip(), "name": mname.strip()})
                discovered["cursor"]["available_models"] = models_list

                # Select best Composer model
                composers = [m for m in models_list if "composer" in m["id"]]
                if composers:
                    def composer_ver_key(item: dict) -> tuple:
                        mat = re.search(r"composer-([\d\.]+)", item["id"])
                        if mat:
                            return tuple(int(x) for x in mat.group(1).split("."))
                        return ()
                    composers.sort(key=composer_ver_key, reverse=True)
                    discovered["cursor"]["selected_model"] = composers[0]["id"]
                    discovered["cursor"]["display_name"] = composers[0]["name"]
        except Exception as exc:
            _LOGGER.debug("cursor agent models discovery failed: %s", exc)

    _DISCOVERY_CACHE = discovered
    return discovered



def ping_agy(
    cli_path: str,
    model: str,
    effort: str = "high",
    timeout: int = 25,
) -> Tuple[bool, int, Optional[str]]:
    """Test availability of agy with mini-prompt. Returns (ok, latency_ms, error)."""
    t0 = time.monotonic()
    cmd = [
        cli_path,
        "--model", model,
        "--effort", effort,
        "--dangerously-skip-permissions",
        "--print=Respond with PONG",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        latency_ms = int((time.monotonic() - t0) * 1000)
        if res.returncode == 0 and "PONG" in res.stdout:
            return True, latency_ms, None
        err = (res.stderr or res.stdout or f"exit code {res.returncode}").strip()
        return False, latency_ms, err
    except subprocess.TimeoutExpired:
        latency_ms = int((time.monotonic() - t0) * 1000)
        return False, latency_ms, f"Timed out after {timeout}s"
    except Exception as exc:
        latency_ms = int((time.monotonic() - t0) * 1000)
        return False, latency_ms, str(exc)


def ping_cursor(
    cli_path: str,
    model: str = "composer-2.5",
    timeout: int = 30,
) -> Tuple[bool, int, Optional[str]]:
    """Test availability of cursor agent with mini-prompt. Returns (ok, latency_ms, error)."""
    t0 = time.monotonic()
    cmd = [
        cli_path,
        "--print",
        "--trust",
        "--mode", "ask",
        "--model", model,
        "Respond with PONG",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        latency_ms = int((time.monotonic() - t0) * 1000)
        if res.returncode == 0 and "PONG" in res.stdout:
            return True, latency_ms, None
        err = (res.stderr or res.stdout or f"exit code {res.returncode}").strip()
        return False, latency_ms, err
    except subprocess.TimeoutExpired:
        latency_ms = int((time.monotonic() - t0) * 1000)
        return False, latency_ms, f"Timed out after {timeout}s"
    except Exception as exc:
        latency_ms = int((time.monotonic() - t0) * 1000)
        return False, latency_ms, str(exc)


class AIHealthMonitor:
    """Thread-safe background health monitor for Gemini and Cursor models."""

    def __init__(self, interval_seconds: int = 120):
        self._interval = interval_seconds
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._check_event = threading.Event()
        self._is_checking = False

        self._discovery: Dict[str, Any] = {}
        self._providers: Dict[str, Any] = {
            "agy": {
                "name": "Gemini (AGY CLI)",
                "role": "primary",
                "model": "gemini-3.8-flash-high",
                "display_name": "Gemini 3.8 Flash (High)",
                "cli_version": None,
                "available": False,
                "status": "untested",
                "latency_ms": None,
                "last_check": None,
                "error": None,
            },
            "cursor": {
                "name": "Cursor Agent",
                "role": "fallback",
                "model": "composer-2.5",
                "display_name": "Cursor Composer 2.5",
                "cli_version": None,
                "available": False,
                "status": "untested",
                "latency_ms": None,
                "last_check": None,
                "error": None,
            },
        }
        self._active_provider: Optional[str] = None
        self._last_updated: Optional[str] = None

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, name="AIHealthMonitorWorker", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._check_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def trigger_check_async(self) -> None:
        self._check_event.set()

    def run_check_cycle(self) -> Dict[str, Any]:
        """Perform discovery and availability tests synchronously."""
        self._is_checking = True
        try:
            disc = discover_models(refresh=True)
            now_iso = datetime.now(timezone.utc).isoformat()

            # 1. Primary: agy
            agy_conf = disc.get("agy", {})
            agy_avail = agy_conf.get("available", False)
            agy_cli = agy_conf.get("cli_path")
            agy_model = agy_conf.get("selected_model", "gemini-3.8-flash-high")
            agy_disp = agy_conf.get("display_name", "Gemini 3.8 Flash (High)")
            agy_ver = agy_conf.get("cli_version")
            agy_effort = agy_conf.get("thinking_effort", "high")

            agy_ok = False
            agy_latency = None
            agy_err = None

            if agy_avail and agy_cli:
                agy_ok, agy_latency, agy_err = ping_agy(agy_cli, agy_model, effort=agy_effort)
            else:
                agy_err = "CLI not installed or subscription not configured (~/.gemini missing)"

            # 2. Fallback: cursor
            cur_conf = disc.get("cursor", {})
            cur_avail = cur_conf.get("available", False)
            cur_cli = cur_conf.get("cli_path")
            cur_model = cur_conf.get("selected_model", "composer-2.5")
            cur_disp = cur_conf.get("display_name", "Cursor Composer 2.5")
            cur_ver = cur_conf.get("cli_version")

            cur_ok = False
            cur_latency = None
            cur_err = None

            if cur_avail and cur_cli:
                cur_ok, cur_latency, cur_err = ping_cursor(cur_cli, cur_model)
            else:
                cur_err = "CLI not installed or subscription not configured (~/.cursor missing)"

            with self._lock:
                self._discovery = disc
                self._providers["agy"].update({
                    "available": agy_avail,
                    "model": agy_model,
                    "display_name": agdisp(agy_disp),
                    "cli_version": agy_ver,
                    "status": "healthy" if agy_ok else ("unreachable" if not agy_avail else "error"),
                    "latency_ms": agy_latency,
                    "last_check": now_iso,
                    "error": agy_err,
                })
                self._providers["cursor"].update({
                    "available": cur_avail,
                    "model": cur_model,
                    "display_name": cur_disp,
                    "cli_version": cur_ver,
                    "status": "healthy" if cur_ok else ("unreachable" if not cur_avail else "error"),
                    "latency_ms": cur_latency,
                    "last_check": now_iso,
                    "error": cur_err,
                })

                # Determine active model (Gemini Flash High preferred, Cursor Composer fallback)
                if agy_ok:
                    self._active_provider = "agy"
                elif cur_ok:
                    self._active_provider = "cursor"
                elif agy_avail:
                    self._active_provider = "agy"
                elif cur_avail:
                    self._active_provider = "cursor"
                else:
                    self._active_provider = None

                self._last_updated = now_iso
                return self._get_status_locked()
        finally:
            self._is_checking = False

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return self._get_status_locked()

    def _get_status_locked(self) -> Dict[str, Any]:
        active_key = self._active_provider
        active_info = None
        if active_key and active_key in self._providers:
            p = self._providers[active_key]
            active_info = {
                "provider": active_key,
                "role": p["role"],
                "model": p["model"],
                "display_name": p["display_name"],
                "cli_version": p["cli_version"],
                "status": p["status"],
                "latency_ms": p["latency_ms"],
                "last_check": p["last_check"],
            }

        return {
            "ok": True,
            "active_provider": active_key,
            "active_model": active_info,
            "providers": {k: dict(v) for k, v in self._providers.items()},
            "is_checking": self._is_checking,
            "last_updated": self._last_updated,
        }

    def _run_loop(self) -> None:
        # Run first check immediately on start
        self.run_check_cycle()

        while not self._stop_event.is_set():
            # Wait for interval or explicit trigger
            triggered = self._check_event.wait(timeout=float(self._interval))
            if self._stop_event.is_set():
                break
            if triggered:
                self._check_event.clear()
            self.run_check_cycle()


def agdisp(name: str) -> str:
    """Helper to clean display names."""
    return re.sub(r"\s+", " ", name).strip()


_MONITOR: Optional[AIHealthMonitor] = None
_MONITOR_LOCK = threading.Lock()


def get_monitor(interval_seconds: int = 120) -> AIHealthMonitor:
    global _MONITOR
    with _MONITOR_LOCK:
        if _MONITOR is None:
            _MONITOR = AIHealthMonitor(interval_seconds=interval_seconds)
        return _MONITOR


def start_health_monitor(interval_seconds: int = 120) -> None:
    mon = get_monitor(interval_seconds=interval_seconds)
    mon.start()


def get_health_status() -> Dict[str, Any]:
    mon = get_monitor()
    return mon.get_status()


def check_health_now() -> Dict[str, Any]:
    mon = get_monitor()
    return mon.run_check_cycle()


def trigger_health_check_async() -> None:
    mon = get_monitor()
    mon.trigger_check_async()


def _run_cli_prompt(cmd: List[str], prompt: str = "", timeout: int = 60) -> Tuple[bool, str]:
    """Execute a prompt via CLI command and return (success, output)."""
    try:
        proc = subprocess.run(
            cmd,
            input=prompt if prompt else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if proc.returncode == 0:
            return True, proc.stdout.strip()
        err_msg = (proc.stderr or proc.stdout or "").strip()
        return False, f"CLI exited with {proc.returncode}: {err_msg}"
    except subprocess.TimeoutExpired:
        return False, f"CLI timed out after {timeout}s"
    except Exception as exc:
        return False, f"CLI execution error: {exc}"


def synthesize_commentary(prompt: str, context: Optional[dict] = None) -> Tuple[Optional[str], dict]:
    """Generate commentary using active model from health monitor with automatic fallback.

    Returns (html_content, metadata).
    """
    status = get_health_status()
    subs = check_subscriptions()
    now_iso = datetime.now(timezone.utc).isoformat()

    active_provider = status.get("active_provider") or "agy"
    agy_prov = status["providers"].get("agy", {})
    cur_prov = status["providers"].get("cursor", {})

    meta: Dict[str, Any] = {
        "timestamp": now_iso,
        "primary_attempted": False,
        "fallback_attempted": False,
        "selected_provider": None,
        "selected_model": None,
        "success": False,
    }

    # Order of providers to try: active first, then other
    providers_order = ["agy", "cursor"] if active_provider == "agy" else ["cursor", "agy"]

    for prov in providers_order:
        if prov == "agy" and subs["gemini"]["available"]:
            meta["primary_attempted"] = True
            cli = subs["gemini"]["cli_path"] or "agy"
            model = agy_prov.get("model", "gemini-3.8-flash-high")
            cmd = [
                cli,
                "--model", model,
                "--effort", "high",
                "--dangerously-skip-permissions",
                f"--print={prompt}",
            ]
            ok, res = _run_cli_prompt(cmd, timeout=60)
            if ok and res:
                meta["selected_provider"] = "agy"
                meta["selected_model"] = model
                meta["success"] = True
                return res, meta
            meta["primary_error"] = res

        elif prov == "cursor" and subs["cursor"]["available"]:
            meta["fallback_attempted"] = True
            cli = subs["cursor"]["cli_path"] or "agent"
            model = cur_prov.get("model", "composer-2.5")
            cmd = [
                cli,
                "--print",
                "--trust",
                "--mode", "ask",
                "--model", model,
                prompt,
            ]
            ok, res = _run_cli_prompt(cmd, timeout=60)
            if ok and res:
                meta["selected_provider"] = "cursor"
                meta["selected_model"] = model
                meta["success"] = True
                return res, meta
            meta["fallback_error"] = res

    return None, meta


def translate_segment(text: str, target_lang: str, context: str = "ai") -> Tuple[Optional[str], dict]:
    """Translate a single masked segment preserving placeholders ⟦k⟧, SWS IDs, and tags."""
    prompt = (
        f"Translate the following technical documentation segment into {target_lang}.\n"
        f"STRICT RULES:\n"
        f"1. Preserve ALL placeholders like ⟦0⟧, ⟦1⟧ exactly as they are.\n"
        f"2. Keep AUTOSAR specification IDs like [SWS_...], [RS_...], and document names unmodified.\n"
        f"3. Keep HTML tags like <code>, <em>, <strong> unmodified.\n"
        f"4. Keep English technical terms that remain English in standard AUTOSAR texts.\n"
        f"5. Return ONLY the translated string without any markdown backticks or explanation.\n\n"
        f"Source text (German):\n{text}\n"
    )
    res, meta = synthesize_commentary(prompt, context={"target_lang": target_lang, "context": context})
    return res, meta
