#!/usr/bin/env python3
"""Portable, read-only environment doctor and prepared-environment fingerprint.

The doctor performs no network or live credential operation.  All potentially
stateful capability probes are supplied through an ObservationAdapter; the
built-in adapter is limited to local metadata and bounded subprocesses.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import locale
import os
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

SCHEMA = "prepared-environment@v1"
CACHE_SCHEMA = "prepared-environment-cache@v1"
REQUIREMENTS_SCHEMA = "environment-doctor-requirements@v1"
PROFILE_SCHEMA = "environment-doctor-profile@v1"
OBSERVATIONS_SCHEMA = "environment-doctor-observations@v1"
STATUSES = ("READY", "MISSING", "UNSUPPORTED", "UNAVAILABLE", "STALE", "FORBIDDEN", "ERROR", "NOT_REQUIRED")
BLOCKING = {"MISSING", "UNSUPPORTED", "UNAVAILABLE", "STALE", "FORBIDDEN"}
ERROR_STATUSES = {"ERROR"}
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 256
MAX_STRING = 1024
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SECRET_KEY_RE = re.compile(r"(?:password|passwd|secret|private.?key|access.?key|api.?key|auth.?token|bearer|cookie|session)", re.I)
PEM_RE = re.compile(r"-----BEGIN [A-Z ]*(?:PRIVATE KEY|CERTIFICATE)-----")
BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I)
URL_USERINFO_RE = re.compile(r"^[a-z][a-z0-9+.-]*://[^/@\s]+@", re.I)
TOKEN_VALUE_RE = re.compile(r"^(?:gh[opusr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|[A-Za-z0-9+/]{48,}={0,2})$")
ALLOWED_OBSERVATION_KEYS = {
    "schema", "platform", "tools", "python", "node", "playwright", "webkit",
    "browser", "graphviz", "fonts", "locale", "timezone", "network",
    "credential", "sandbox", "runner", "repository", "writable_roots",
    "watchdog", "process_group", "resources",
}
TOOL_PROBES = {
    "git": ("git", ("--version",)),
    "node": ("node", ("--version",)),
    "python": (sys.executable, ("--version",)),
    "dot": ("dot", ("-V",)),
}
OBSERVATION_FIELDS = {
    "platform": {"system", "machine", "release", "path_entries"},
    "python": {"status", "path", "version", "modules"},
    "node": {"status", "path", "version", "identity"},
    "playwright": {"status", "path", "version", "identity"},
    "webkit": {"status", "path", "version", "identity"},
    "browser": {"identity", "launch", "navigation", "selector"},
    "graphviz": {"status", "path", "version", "identity"},
    "locale": {"status", "value"}, "timezone": {"status", "value"},
    "network": {"status", "mode", "state"},
    "credential": {"status", "state", "handle_id", "age_seconds"},
    "sandbox": {"status", "mode", "capability"},
    "runner": {"status", "protocol", "authority_epoch"},
    "repository": {"status", "protocol"},
    "watchdog": {"status", "mechanism"}, "process_group": {"status", "mechanism"},
    "resources": {"status", "cpu", "memory_mb", "disk_free_mb", "free_bytes", "pid", "duration", "duration_ms", "timestamp", "observed_at"},
}
IDENTITY_ITEM_FIELDS = {"name", "status", "path", "version", "identity"}
ROOT_FIELDS = {"status", "path", "class"}
GATE_ORDER = (
    "inputs", "bootstrap", "repository", "runner_protocol", "authority_epoch",
    "capability", "sandbox", "resources", "temporary_root", "cache_root",
    "python", "python_modules", "tools", "node", "playwright", "webkit",
    "graphviz", "fonts", "locale", "timezone", "watchdog", "process_group",
    "network", "credential", "browser_launch", "browser_navigation", "browser_selector",
)


class ContractError(ValueError):
    """A closed input or privacy contract was violated."""


class DuplicateKeyError(ContractError):
    pass


@dataclass(frozen=True)
class InputBlob:
    label: str
    path: str
    raw: bytes
    digest: str


class ObservationAdapter:
    """Interface for hermetic observations."""

    def collect(self, requirements: Mapping[str, Any], profile: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError


class InjectedObservationAdapter(ObservationAdapter):
    def __init__(self, observations: Mapping[str, Any]) -> None:
        self._observations = observations

    def collect(self, requirements: Mapping[str, Any], profile: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._observations


class LocalObservationAdapter(ObservationAdapter):
    """Bounded local metadata adapter; never performs network/credential access."""

    def _tool(self, name: str) -> Dict[str, Any]:
        probe = TOOL_PROBES.get(name)
        if probe is None:
            return {"name": name, "status": "UNAVAILABLE"}
        executable, argv = probe
        resolved = sys.executable if name == "python" else shutil.which(executable)
        if not resolved:
            return {"name": name, "status": "MISSING"}
        try:
            proc = subprocess.run(
                [resolved, *argv],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=2,
                check=False,
                start_new_session=True,
                env={"PATH": os.environ.get("PATH", "")},
            )
        except (OSError, subprocess.TimeoutExpired):
            return {"name": name, "path": resolved, "status": "UNAVAILABLE", "version": "unknown"}
        version = (proc.stdout.splitlines() or ["unknown"])[0][:160]
        return {"name": name, "path": resolved, "status": "READY" if proc.returncode == 0 else "UNAVAILABLE", "version": version}

    def collect(self, requirements: Mapping[str, Any], profile: Mapping[str, Any]) -> Mapping[str, Any]:
        tools = [self._tool(str(name)) for name in requirements.get("tools", [])]
        modules = []
        for name in requirements.get("python_modules", []):
            modules.append({"name": name, "status": "READY" if importlib.util.find_spec(name) else "MISSING"})
        has_alarm = hasattr(signal, "SIGALRM") and hasattr(signal, "setitimer")
        browser_required = bool(requirements.get("browser", False))
        network_required = bool(profile.get("network_required", False))
        credential_required = bool(profile.get("credential_required", False))
        return {
            "schema": OBSERVATIONS_SCHEMA,
            "platform": {"system": platform.system(), "machine": platform.machine(), "release": platform.release(), "path_entries": os.environ.get("PATH", "").split(os.pathsep)},
            "tools": tools,
            "python": {"status": "READY", "path": sys.executable, "version": platform.python_version(), "modules": modules},
            "node": {"status": "UNAVAILABLE" if requirements.get("node", False) else "NOT_REQUIRED"},
            "playwright": {"status": "UNAVAILABLE" if requirements.get("playwright", False) else "NOT_REQUIRED"},
            "webkit": {"status": "UNAVAILABLE" if requirements.get("webkit", False) else "NOT_REQUIRED"},
            "browser": {"launch": "UNAVAILABLE" if browser_required else "NOT_REQUIRED", "navigation": "UNAVAILABLE" if browser_required else "NOT_REQUIRED", "selector": "UNAVAILABLE" if browser_required else "NOT_REQUIRED", "identity": "none"},
            "graphviz": {"status": self._tool("dot")["status"] if requirements.get("graphviz", False) else "NOT_REQUIRED"},
            "fonts": [],
            "locale": {"status": "READY", "value": locale.setlocale(locale.LC_ALL, None)},
            "timezone": {"status": "READY", "value": os.environ.get("TZ", "system")},
            "network": {"status": "UNAVAILABLE" if network_required else "FORBIDDEN", "mode": "metadata-only", "state": "not-probed"},
            "credential": {"status": "UNAVAILABLE" if credential_required else "FORBIDDEN", "state": "not-inspected"},
            "sandbox": {"status": "UNAVAILABLE", "mode": "observed-local", "capability": "unknown"},
            "runner": {"status": "UNAVAILABLE", "protocol": "unknown", "authority_epoch": "unknown"},
            "repository": {"status": "UNAVAILABLE", "protocol": "unknown"},
            "writable_roots": {"temporary": {"status": "READY", "path": tempfile.gettempdir()}, "cache": {"status": "NOT_REQUIRED"}},
            "watchdog": {"status": "READY" if has_alarm else "UNSUPPORTED", "mechanism": "python-sigalrm" if has_alarm else "none"},
            "process_group": {"status": "READY" if hasattr(os, "setsid") else "UNSUPPORTED"},
            "resources": {"status": "READY", "cpu": os.cpu_count() or 1, "memory_mb": None, "disk_free_mb": None},
        }


def _pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_bytes(raw: bytes, label: str) -> Any:
    if len(raw) > MAX_JSON_BYTES:
        raise ContractError(f"{label}: input exceeds {MAX_JSON_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(f"{label}: invalid UTF-8") from exc
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=lambda value: (_ for _ in ()).throw(ContractError(f"{label}: non-finite number {value}")))
    except (json.JSONDecodeError, DuplicateKeyError, ContractError) as exc:
        raise ContractError(f"{label}: invalid JSON: {exc}") from exc
    _bounded(value, label)
    return value


def _bounded(value: Any, label: str, depth: int = 0) -> None:
    if depth > 12:
        raise ContractError(f"{label}: nesting too deep")
    if isinstance(value, str):
        if len(value) > MAX_STRING:
            raise ContractError(f"{label}: string too long")
    elif isinstance(value, list):
        if len(value) > MAX_ITEMS:
            raise ContractError(f"{label}: too many items")
        for item in value:
            _bounded(item, label, depth + 1)
    elif isinstance(value, dict):
        if len(value) > MAX_ITEMS:
            raise ContractError(f"{label}: too many members")
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractError(f"{label}: non-string key")
            _bounded(item, label, depth + 1)
    elif value is not None and not isinstance(value, (bool, int, float)):
        raise ContractError(f"{label}: unsupported value")


def _privacy_check(value: Any, label: str = "input", key: str = "") -> None:
    if key and SECRET_KEY_RE.search(key):
        raise ContractError(f"{label}: secret-shaped field rejected: {key}")
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            _privacy_check(child, label, str(child_key))
    elif isinstance(value, list):
        for child in value:
            _privacy_check(child, label, key)
    elif isinstance(value, str):
        if PEM_RE.search(value) or BEARER_RE.search(value) or URL_USERINFO_RE.search(value) or TOKEN_VALUE_RE.fullmatch(value):
            raise ContractError(f"{label}: secret-shaped value rejected")


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_json(value: Any) -> str:
    return _canonical_bytes(value).decode("utf-8")


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _safe_read(path: Path, label: str, json_input: bool = False) -> InputBlob:
    try:
        before = path.lstat()
    except OSError as exc:
        raise ContractError(f"{label}: missing or inaccessible") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ContractError(f"{label}: exact input must be a regular non-symlink file")
    limit = MAX_JSON_BYTES if json_input else MAX_TEXT_BYTES
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise ContractError(f"{label}: input changed during open")
            raw = handle.read(limit + 1)
            after = os.fstat(handle.fileno())
    except OSError as exc:
        raise ContractError(f"{label}: read failed") from exc
    if len(raw) > limit:
        raise ContractError(f"{label}: input exceeds {limit} bytes")
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ContractError(f"{label}: input changed during scan")
    return InputBlob(label, path.name, raw, _digest(raw))


def _closed_object(value: Any, label: str, required: Iterable[str], allowed: Iterable[str]) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label}: expected object")
    required_set, allowed_set = set(required), set(allowed)
    missing = sorted(required_set - set(value))
    unknown = sorted(set(value) - allowed_set)
    if missing:
        raise ContractError(f"{label}: missing fields: {', '.join(missing)}")
    if unknown:
        raise ContractError(f"{label}: unknown fields: {', '.join(unknown)}")
    return value


def _validate_inputs(bootstrap: Any, requirements: Any, profile: Any, observations: Any) -> None:
    _closed_object(bootstrap, "bootstrap", {"schema", "workflow_version", "authority_epoch", "authority_profile", "write_phase", "required_capability", "runner_protocol", "selector_digest", "instruction_bundle"}, {"schema", "workflow_version", "authority_epoch", "authority_profile", "write_phase", "required_capability", "runner_protocol", "selector_digest", "instruction_bundle"})
    if bootstrap["schema"] != "agent-workflow-bootstrap@v1" or not DIGEST_RE.fullmatch(str(bootstrap["selector_digest"])):
        raise ContractError("bootstrap: unsupported schema or digest")
    bundle = bootstrap["instruction_bundle"]
    if not isinstance(bundle, str) or not re.fullmatch(r"docs/pipeline/agent-instructions/(?:legacy|current|future)/index\.md", bundle):
        raise ContractError("bootstrap: invalid instruction_bundle")
    _closed_object(requirements, "requirements", {"schema"}, {"schema", "tools", "python_modules", "node", "playwright", "webkit", "graphviz", "fonts", "browser"})
    if requirements["schema"] != REQUIREMENTS_SCHEMA:
        raise ContractError("requirements: unsupported schema")
    for field in ("tools", "python_modules", "fonts"):
        if field in requirements and (not isinstance(requirements[field], list) or not all(isinstance(item, str) for item in requirements[field])):
            raise ContractError(f"requirements: {field} must be a string array")
    _closed_object(profile, "profile", {"schema"}, {"schema", "capability", "sandbox", "runner_protocol", "authority_epoch", "repository_protocol", "write_phase", "locale", "timezone", "network_required", "credential_required", "credential_max_age_seconds", "minimum_cpu", "minimum_memory_mb", "minimum_disk_free_mb", "cache_max_age_seconds"})
    if profile["schema"] != PROFILE_SCHEMA:
        raise ContractError("profile: unsupported schema")
    _closed_object(observations, "observations", {"schema"}, ALLOWED_OBSERVATION_KEYS)
    if observations["schema"] != OBSERVATIONS_SCHEMA:
        raise ContractError("observations: unsupported schema")
    for field, allowed_fields in OBSERVATION_FIELDS.items():
        if field in observations:
            _closed_object(observations[field], f"observations.{field}", set(), allowed_fields)
    for field in ("tools", "fonts"):
        items = observations.get(field, [])
        if not isinstance(items, list):
            raise ContractError(f"observations.{field}: expected array")
        for index, item in enumerate(items):
            _closed_object(item, f"observations.{field}[{index}]", {"name", "status"}, IDENTITY_ITEM_FIELDS)
    modules = observations.get("python", {}).get("modules", [])
    if not isinstance(modules, list):
        raise ContractError("observations.python.modules: expected array")
    for index, item in enumerate(modules):
        _closed_object(item, f"observations.python.modules[{index}]", {"name", "status"}, IDENTITY_ITEM_FIELDS)
    roots = observations.get("writable_roots", {})
    _closed_object(roots, "observations.writable_roots", set(), {"temporary", "cache"})
    for name, item in roots.items():
        _closed_object(item, f"observations.writable_roots.{name}", {"status"}, ROOT_FIELDS)
    _privacy_check(bootstrap, "bootstrap")
    _privacy_check(requirements, "requirements")
    _privacy_check(profile, "profile")
    _privacy_check(observations, "observations")


def _status(value: Any, default: str = "MISSING") -> str:
    status_value = value.get("status", default) if isinstance(value, Mapping) else value
    status_value = str(status_value)
    if status_value not in STATUSES:
        return "ERROR"
    return status_value


def _alias_path(value: Any, root: Path) -> Optional[Dict[str, str]]:
    if not value:
        return None
    raw = str(value)
    path = Path(raw)
    name = path.name or "root"
    try:
        resolved = path.resolve(strict=False)
        repo = root.resolve(strict=False)
        temp = Path(tempfile.gettempdir()).resolve(strict=False)
        if resolved == repo or repo in resolved.parents:
            alias = "repository"
        elif resolved == temp or temp in resolved.parents:
            alias = "temporary"
        elif raw.startswith(("/usr/", "/bin/", "/opt/", "/System/", "C:\\Windows\\")):
            alias = "system"
        else:
            alias = "private"
    except OSError:
        alias = "unresolved"
    return {"class": alias, "name": name if alias != "private" else "private", "identity": _digest(raw.encode("utf-8"))}


def _normal(value: Any, root: Path, key: str = "") -> Any:
    if isinstance(value, Mapping):
        result = {}
        for child_key in sorted(value):
            child = value[child_key]
            if child_key == "path":
                result["path"] = _alias_path(child, root)
            elif child_key in {"free_bytes", "disk_free_mb", "duration", "duration_ms", "pid", "timestamp", "observed_at"}:
                continue
            else:
                result[child_key] = _normal(child, root, child_key)
        return result
    if isinstance(value, list):
        normalized = [_normal(item, root, key) for item in value]
        if key in {"tools", "modules", "fonts", "path_entries"}:
            normalized.sort(key=lambda item: canonical_json(item) if isinstance(item, (dict, list)) else str(item))
        return normalized
    if key == "path_entries":
        return _alias_path(value, root)
    return value


def _gate(gates: Dict[str, Dict[str, Any]], gate_id: str, status_value: str, required: bool, message: str) -> None:
    status_value = status_value if status_value in STATUSES else "ERROR"
    if required and status_value == "NOT_REQUIRED":
        status_value = "MISSING"
    gates[gate_id] = {"id": gate_id, "status": status_value, "required": bool(required), "message": message[:240].replace("\n", " ")}


def _component_status(observations: Mapping[str, Any], name: str, required: bool) -> str:
    if name not in observations:
        return "MISSING" if required else "NOT_REQUIRED"
    status_value = _status(observations[name])
    if not required and status_value == "MISSING":
        return "NOT_REQUIRED"
    return status_value


def _build_gates(bootstrap: Mapping[str, Any], requirements: Mapping[str, Any], profile: Mapping[str, Any], observations: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    gates: Dict[str, Dict[str, Any]] = {}
    _gate(gates, "inputs", "READY", True, "all exact inputs validated")
    bootstrap_status = "READY"
    bootstrap_pairs = (
        ("authority_epoch", "authority_epoch"),
        ("authority_profile", "repository_protocol"),
        ("required_capability", "capability"),
        ("runner_protocol", "runner_protocol"),
        ("write_phase", "write_phase"),
    )
    for bootstrap_key, profile_key in bootstrap_pairs:
        if bootstrap.get(bootstrap_key) != profile.get(profile_key):
            bootstrap_status = "STALE"
            break
    _gate(gates, "bootstrap", bootstrap_status, True, "bootstrap contract must cross-bind profile and authority")
    repository = observations.get("repository", {})
    expected_repo = profile.get("repository_protocol", bootstrap.get("authority_profile"))
    repo_status = _status(repository)
    if repo_status == "READY" and repository.get("protocol") != expected_repo:
        repo_status = "STALE"
    _gate(gates, "repository", repo_status, True, "repository protocol must match profile")
    runner = observations.get("runner", {})
    runner_status = _status(runner)
    if runner_status == "READY" and runner.get("protocol") != profile.get("runner_protocol", bootstrap.get("runner_protocol")):
        runner_status = "UNSUPPORTED"
    _gate(gates, "runner_protocol", runner_status, True, "runner protocol must match bootstrap/profile")
    epoch_status = _status(runner)
    if epoch_status == "READY" and runner.get("authority_epoch") != profile.get("authority_epoch", bootstrap.get("authority_epoch")):
        epoch_status = "STALE"
    _gate(gates, "authority_epoch", epoch_status, True, "authority epoch must match bootstrap/profile")
    sandbox = observations.get("sandbox", {})
    capability_status = _status(sandbox)
    if capability_status == "READY" and sandbox.get("capability") != profile.get("capability", bootstrap.get("required_capability")):
        capability_status = "FORBIDDEN"
    _gate(gates, "capability", capability_status, True, "capability class must match")
    sandbox_status = _status(sandbox)
    if sandbox_status == "READY" and profile.get("sandbox") is not None and sandbox.get("mode") != profile.get("sandbox"):
        sandbox_status = "FORBIDDEN"
    _gate(gates, "sandbox", sandbox_status, True, "sandbox mode must match")
    resources = observations.get("resources", {})
    resource_status = _status(resources)
    for observed, minimum in ((resources.get("cpu"), profile.get("minimum_cpu")), (resources.get("memory_mb"), profile.get("minimum_memory_mb")), (resources.get("disk_free_mb"), profile.get("minimum_disk_free_mb"))):
        if minimum is not None and (observed is None or observed < minimum):
            resource_status = "UNAVAILABLE"
    _gate(gates, "resources", resource_status, True, "declared resource minima must be available")
    roots = observations.get("writable_roots", {})
    _gate(gates, "temporary_root", _status(roots.get("temporary", {})), True, "temporary root must be writable")
    _gate(gates, "cache_root", _status(roots.get("cache", {"status": "NOT_REQUIRED"})), _status(roots.get("cache", {"status": "NOT_REQUIRED"})) != "NOT_REQUIRED", "cache root is optional and never repaired")
    _gate(gates, "python", _component_status(observations, "python", True), True, "Python runtime required")
    modules = observations.get("python", {}).get("modules", []) if isinstance(observations.get("python"), Mapping) else []
    module_status = "READY"
    required_modules = set(requirements.get("python_modules", []))
    observed_modules = {item.get("name"): _status(item) for item in modules if isinstance(item, Mapping)}
    for name in required_modules:
        if observed_modules.get(name, "MISSING") != "READY":
            module_status = observed_modules.get(name, "MISSING")
            break
    _gate(gates, "python_modules", module_status, bool(required_modules), "required Python modules")
    tools = observations.get("tools", [])
    observed_tools = {item.get("name"): _status(item) for item in tools if isinstance(item, Mapping)}
    tool_status = "READY"
    for name in requirements.get("tools", []):
        if observed_tools.get(name, "MISSING") != "READY":
            tool_status = observed_tools.get(name, "MISSING")
            break
    _gate(gates, "tools", tool_status, bool(requirements.get("tools")), "required command-line tools")
    for name in ("node", "playwright", "webkit", "graphviz"):
        required = bool(requirements.get(name, False))
        _gate(gates, name, _component_status(observations, name, required), required, f"{name} capability")
    required_fonts = set(requirements.get("fonts", []))
    observed_fonts = {item.get("name"): _status(item) for item in observations.get("fonts", []) if isinstance(item, Mapping)}
    font_status = "READY"
    for name in required_fonts:
        if observed_fonts.get(name, "MISSING") != "READY":
            font_status = observed_fonts.get(name, "MISSING")
            break
    _gate(gates, "fonts", font_status, bool(required_fonts), "required font identities")
    for name in ("locale", "timezone"):
        item = observations.get(name, {})
        expected = profile.get(name)
        item_status = _status(item)
        if item_status == "READY" and expected is not None and item.get("value") != expected:
            item_status = "STALE"
        _gate(gates, name, item_status, expected is not None, f"{name} must match profile")
    _gate(gates, "watchdog", _component_status(observations, "watchdog", True), True, "portable watchdog required; external timeout is not required")
    _gate(gates, "process_group", _component_status(observations, "process_group", True), True, "process-group termination support required")
    network_required = bool(profile.get("network_required", False))
    credential_required = bool(profile.get("credential_required", False))
    _gate(gates, "network", _component_status(observations, "network", network_required), network_required, "metadata-only network state; no live probe")
    credential_status = _component_status(observations, "credential", credential_required)
    credential = observations.get("credential", {})
    if credential_status == "READY" and profile.get("credential_max_age_seconds") is not None and credential.get("age_seconds", 0) > profile["credential_max_age_seconds"]:
        credential_status = "STALE"
    _gate(gates, "credential", credential_status, credential_required, "credential-handle metadata only; no secret access")
    browser_required = bool(requirements.get("browser", False))
    browser = observations.get("browser", {})
    for suffix in ("launch", "navigation", "selector"):
        _gate(gates, "browser_" + suffix, _status(browser.get(suffix, "MISSING" if browser_required else "NOT_REQUIRED")), browser_required, f"browser {suffix} probe")
    return gates


def _fingerprint_payload(tool_blob: InputBlob, bootstrap_blob: InputBlob, instruction_blob: InputBlob, requirements_blob: InputBlob, profile_blob: InputBlob, bootstrap: Mapping[str, Any], requirements: Mapping[str, Any], profile: Mapping[str, Any], observations: Mapping[str, Any], gates: Mapping[str, Mapping[str, Any]], root: Path) -> Dict[str, Any]:
    normalized_observations = _normal(observations, root)
    return {
        "contract": SCHEMA,
        "doctor": tool_blob.digest,
        "inputs": {
            "bootstrap": {"digest": bootstrap_blob.digest, "normalized": bootstrap},
            "instruction_bundle": instruction_blob.digest,
            "requirements": {"digest": requirements_blob.digest, "normalized": requirements},
            "profile": {"digest": profile_blob.digest, "normalized": profile},
        },
        "environment": normalized_observations,
        "derived_states": {name: gates[name]["status"] for name in GATE_ORDER},
    }


def _cache_member(cache_root: Path, fingerprint: str) -> Path:
    return cache_root / (fingerprint.removeprefix("sha256:") + ".json")


def _cache_root_safe(cache_root: Path, root: Path) -> bool:
    try:
        info = cache_root.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            return False
        fd = os.open(cache_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            opened = os.fstat(fd)
        finally:
            os.close(fd)
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            return False
        resolved = cache_root.resolve(strict=False)
        temp = Path(tempfile.gettempdir()).resolve(strict=True)
        repo = root.resolve(strict=True)
    except OSError:
        return False
    return resolved == temp or temp in resolved.parents or resolved == repo or repo in resolved.parents


def _report_digest(report: Mapping[str, Any]) -> str:
    candidate = dict(report)
    candidate.pop("content_digest", None)
    candidate.pop("cache", None)
    candidate.pop("summary", None)
    return _digest(_canonical_bytes(candidate))


def _read_cache(cache_root: Optional[Path], root: Path, fingerprint: str, freshness: Mapping[str, str], now: int, max_age: Optional[int]) -> Tuple[str, Optional[Dict[str, Any]]]:
    if cache_root is None:
        return "NOT_REQUIRED", None
    if not _cache_root_safe(cache_root, root):
        return "FORBIDDEN", None
    member = _cache_member(cache_root, fingerprint)
    if not member.exists():
        return "MISSING", None
    try:
        blob = _safe_read(member, "cache member", json_input=True)
        envelope = strict_json_bytes(blob.raw, "cache member")
        _closed_object(envelope, "cache member", {"schema", "fingerprint", "created_at", "freshness", "report", "report_digest"}, {"schema", "fingerprint", "created_at", "freshness", "report", "report_digest"})
        if envelope["schema"] != CACHE_SCHEMA or envelope["fingerprint"] != fingerprint:
            return "STALE", None
        if envelope["freshness"] != freshness:
            return "STALE", None
        if not isinstance(envelope["created_at"], int) or (max_age is not None and now - envelope["created_at"] > max_age):
            return "STALE", None
        report = envelope["report"]
        if not isinstance(report, dict) or report.get("schema") != SCHEMA or report.get("environment_id") != fingerprint:
            return "ERROR", None
        if envelope["report_digest"] != _report_digest(report) or report.get("content_digest") != _report_digest(report):
            return "ERROR", None
        return "READY", report
    except (ContractError, OSError, TypeError, ValueError):
        return "ERROR", None


def _write_cache(cache_root: Path, fingerprint: str, freshness: Mapping[str, str], report: Mapping[str, Any], now: int, root: Path) -> str:
    if not _cache_root_safe(cache_root, root):
        return "FORBIDDEN"
    member = _cache_member(cache_root, fingerprint)
    envelope = {"schema": CACHE_SCHEMA, "fingerprint": fingerprint, "created_at": int(now), "freshness": dict(freshness), "report": report, "report_digest": _report_digest(report)}
    payload = _canonical_bytes(envelope)
    dir_fd: Optional[int] = None
    temp_name: Optional[str] = None
    try:
        dir_fd = os.open(cache_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
        before = os.fstat(dir_fd)
        root_info = cache_root.lstat()
        if (before.st_dev, before.st_ino) != (root_info.st_dev, root_info.st_ino):
            return "UNAVAILABLE"
        temp_name = f".environment-doctor-{os.getpid()}-{int(now)}.partial"
        temp_fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=dir_fd)
        try:
            with os.fdopen(temp_fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, member.name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
        finally:
            if temp_name is not None:
                try:
                    os.unlink(temp_name, dir_fd=dir_fd)
                except OSError:
                    pass
                temp_name = None
        return "READY"
    except OSError:
        return "UNAVAILABLE"
    finally:
        if dir_fd is not None:
            try:
                os.close(dir_fd)
            except OSError:
                pass


def _summary(report: Mapping[str, Any]) -> Tuple[str, ...]:
    first = report["first_actionable"]
    lines = [f"environment-doctor {report['aggregate']}: {report['environment_id']}"]
    if first is None:
        lines.append("first-actionable: none")
    else:
        lines.append(f"first-actionable: {first['id']} [{first['status']}] {first['message']}")
    lines.append(f"gates: ready={report['counts']['READY']} blocked={report['counts']['blocking']} error={report['counts']['ERROR']}")
    lines.append(f"cache: {report['cache']['status']} ({'reused' if report['cache']['reused'] else 'cold'})")
    return tuple(lines[:10])


def scan_environment(root: Path, requirements_path: Path, profile_path: Path, *, bootstrap_path: Optional[Path] = None, instruction_path: Optional[Path] = None, adapter: Optional[ObservationAdapter] = None, observations: Optional[Mapping[str, Any]] = None, cache_root: Optional[Path] = None, write_cache: bool = False, now: Optional[int] = None, verify_hook: Optional[Any] = None) -> Dict[str, Any]:
    """Scan exact inputs and return canonical prepared-environment@v1 data."""
    root = Path(root)
    bootstrap_path = bootstrap_path or root / "agent-workflow.json"
    now_value = int(time.time() if now is None else now)
    bootstrap_blob = _safe_read(bootstrap_path, "bootstrap", json_input=True)
    bootstrap = strict_json_bytes(bootstrap_blob.raw, "bootstrap")
    if instruction_path is None:
        if not isinstance(bootstrap, Mapping) or not isinstance(bootstrap.get("instruction_bundle"), str):
            raise ContractError("bootstrap: instruction_bundle missing")
        instruction_path = root / str(bootstrap["instruction_bundle"])
    resolved_instruction_path = Path(instruction_path)
    instruction_blob = _safe_read(resolved_instruction_path, "instruction bundle")
    requirements_blob = _safe_read(requirements_path, "requirements", json_input=True)
    profile_blob = _safe_read(profile_path, "profile", json_input=True)
    tool_blob = _safe_read(Path(__file__), "doctor tool")
    requirements = strict_json_bytes(requirements_blob.raw, "requirements")
    profile = strict_json_bytes(profile_blob.raw, "profile")
    if observations is not None and adapter is not None:
        raise ContractError("provide observations or adapter, not both")
    selected_adapter = adapter or (InjectedObservationAdapter(observations) if observations is not None else LocalObservationAdapter())
    observed = dict(selected_adapter.collect(requirements, profile))
    _validate_inputs(bootstrap, requirements, profile, observed)
    if verify_hook is not None:
        verify_hook()
    for blob, path in ((bootstrap_blob, bootstrap_path), (instruction_blob, resolved_instruction_path), (requirements_blob, requirements_path), (profile_blob, profile_path), (tool_blob, Path(__file__))):
        current = _safe_read(path, blob.label, json_input=blob.label in {"bootstrap", "requirements", "profile"})
        if current.digest != blob.digest:
            raise ContractError(f"{blob.label}: input changed during scan")
    gates_map = _build_gates(bootstrap, requirements, profile, observed)
    payload = _fingerprint_payload(tool_blob, bootstrap_blob, instruction_blob, requirements_blob, profile_blob, bootstrap, requirements, profile, observed, gates_map, root)
    fingerprint = _digest(_canonical_bytes(payload))
    freshness = {"bootstrap": bootstrap_blob.digest, "instructions": instruction_blob.digest, "requirements": requirements_blob.digest, "profile": profile_blob.digest, "doctor": tool_blob.digest}
    gates = [gates_map[name] for name in GATE_ORDER]
    first = next((gate for gate in gates if gate["required"] and gate["status"] not in {"READY", "NOT_REQUIRED"}), None)
    required_statuses = {gate["status"] for gate in gates if gate["required"]}
    aggregate = "INCOMPLETE" if required_statuses & ERROR_STATUSES else ("BLOCKED" if required_statuses & BLOCKING else "PREPARED")
    counts = {status_value: sum(1 for gate in gates if gate["status"] == status_value) for status_value in STATUSES}
    counts["blocking"] = sum(1 for gate in gates if gate["required"] and gate["status"] in BLOCKING)
    member_name = fingerprint.removeprefix("sha256:") + ".json"
    report: Dict[str, Any] = {
        "schema": SCHEMA,
        "environment_id": fingerprint,
        "aggregate": aggregate,
        "exit_code": 0 if aggregate == "PREPARED" else (1 if aggregate == "BLOCKED" else 2),
        "first_actionable": first,
        "counts": counts,
        "inputs": {"bootstrap": bootstrap_blob.digest, "instruction_bundle": instruction_blob.digest, "requirements": requirements_blob.digest, "profile": profile_blob.digest, "doctor": tool_blob.digest},
        "bootstrap": {key: bootstrap[key] for key in sorted(bootstrap)},
        "observations": _normal(observed, root),
        "gates": gates,
        "cache": {"status": "NOT_REQUIRED" if cache_root is None else "MISSING", "reused": False, "member": member_name if cache_root is not None else None},
        "summary": [],
        "content_digest": "sha256:" + "0" * 64,
    }
    report["summary"] = list(_summary(report))
    report["content_digest"] = _report_digest(report)
    if cache_root is not None:
        cache_status, cached = _read_cache(cache_root, root, fingerprint, freshness, now_value, profile.get("cache_max_age_seconds"))
        if cached is not None:
            if _report_digest(cached) == _report_digest(report):
                report["cache"] = {"status": "READY", "reused": True, "member": member_name}
            else:
                # A cache member is an optimization, never an authority. A
                # self-consistent but forged report must not be presented as a
                # benign miss: surface the disagreement for fail-closed callers.
                report["cache"] = {"status": "ERROR", "reused": False, "member": member_name}
        else:
            report["cache"] = {"status": cache_status, "reused": False, "member": member_name}
        if write_cache:
            write_status = _write_cache(cache_root, fingerprint, freshness, report, now_value, root)
            if write_status == "READY":
                report["cache"] = {"status": "READY", "reused": report["cache"]["reused"], "member": member_name}
            else:
                report["cache"] = {"status": write_status, "reused": report["cache"]["reused"], "member": member_name}
                if report["aggregate"] == "PREPARED" and write_status in {"FORBIDDEN", "UNAVAILABLE"}:
                    cache_gate = {"id": "cache_write", "status": write_status, "required": True, "message": "cache write failed; cache root is unavailable or forbidden"}
                    report["gates"].append(cache_gate)
                    report["counts"][write_status] += 1
                    report["counts"]["blocking"] += 1
                    report["first_actionable"] = cache_gate
                    report["aggregate"] = "INCOMPLETE"
                    report["exit_code"] = 2
    report["summary"] = list(_summary(report))
    report["content_digest"] = _report_digest(report)
    return report


def render_summary(report: Mapping[str, Any]) -> Tuple[str, ...]:
    return _summary(report)


def _error_report(message: str) -> Dict[str, Any]:
    safe = message[:240].replace("\n", " ")
    report: Dict[str, Any] = {"schema": SCHEMA, "environment_id": "sha256:" + "0" * 64, "aggregate": "INCOMPLETE", "exit_code": 2, "first_actionable": {"id": "inputs", "status": "ERROR", "required": True, "message": safe}, "counts": {**{status_value: (1 if status_value == "ERROR" else 0) for status_value in STATUSES}, "blocking": 1}, "inputs": {}, "bootstrap": {}, "observations": {}, "gates": [{"id": "inputs", "status": "ERROR", "required": True, "message": safe}], "cache": {"status": "NOT_REQUIRED", "reused": False, "member": None}, "summary": [], "content_digest": "sha256:" + "0" * 64}
    report["summary"] = list(_summary(report))
    report["content_digest"] = _report_digest(report)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument("--write-cache", action="store_true")
    parser.add_argument("--summary", action="store_true", help="emit the at-most-ten-line summary to stderr")
    args = parser.parse_args(argv)
    try:
        injected = None
        if args.observations:
            injected = strict_json_bytes(_safe_read(args.observations, "observations", json_input=True).raw, "observations")
        report = scan_environment(args.root, args.requirements, args.profile, observations=injected, cache_root=args.cache_root, write_cache=args.write_cache)
    except (ContractError, OSError, ValueError, TypeError) as exc:
        report = _error_report(str(exc))
    sys.stdout.write(canonical_json(report))
    if args.summary:
        sys.stderr.write("\n".join(render_summary(report)) + "\n")
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
