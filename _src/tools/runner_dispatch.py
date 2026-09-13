#!/usr/bin/env python3
"""runner_dispatch.py — Task 0037-46.01 typed-action queue/dispatcher.

Implements, WITHOUT ACTIVATING, the approved conflict-safe runner queue:

  * a draft-then-atomic-rename publication model
    (``.runner/drafts/<agent>/<request-id>/`` -> ``.runner/requests/<request-id>/``);
  * a dispatcher that only ever lists ``requests/`` (drafts are structurally
    invisible), validates every request against the frozen
    ``runner-request@v1``/``runner-result@v1`` contract
    (``issues/_schema/*.schema.json``) plus this package's own
    ``_src/runner/actions-v1.json`` typed-action registry;
  * atomic claiming (``O_CREAT|O_EXCL`` lease files), scope-collision
    rejection, stale base/epoch/ref rejection, dependency/credential/network
    preflight, timeouts, cooperative cancellation, isolated temporary
    execution roots, immutable/append-only results and logs, tamper-evident
    result digests, and idempotence-key-based retry/duplicate rejection.

This module is a **library and CLI test harness only**. Nothing here wires
into the live legacy ``run.sh`` singleton runner (that activation step is
Task ``0037-46.02``), and no repository authority changes as a result of
importing or running it. ``.runner/`` is a git-ignored runtime root that
tests exercise inside temporary directories or this worktree's own
``.runner/`` — it is never tracked, never committed as source.

Design note on carrying typed-action arguments inside the frozen envelope:
``issues/_schema/runner-request-v1.schema.json`` is frozen and
``additionalProperties: false`` with a fixed field set — there is no generic
"action arguments" property. Exactly as
``docs/pipeline/branch-merge-actions.md`` already does for
``base-branch``/``merge-prereqs``/``integrate-checkpoint``, this dispatcher
carries typed-action arguments as additional, machine-parseable
``preflight`` entries of the form ``arg:<name>=<value>`` alongside the
structural entries that document already specifies (``target-branch:...``,
``expected-parent-tip:...``, etc.). This is strictly additive convention on
top of a schema-valid instance, never a schema relaxation, and is documented
in ``docs/pipeline/runner-dispatch.md``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

THIS_FILE = Path(__file__).resolve()
REPO_ROOT_DEFAULT = THIS_FILE.parents[2]
RUNNER_PKG_DIR = REPO_ROOT_DEFAULT / "_src" / "runner"
FROZEN_SCHEMA_DIR = REPO_ROOT_DEFAULT / "issues" / "_schema"

GOVERNANCE_PREFIXES = (
    "AGENTS.md",
    "SANDBOX.md",
    "PRIVILEGED.md",
    "CLAUDE.md",
    "docs/pipeline/",
)

DATE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def now_iso(now: Optional[datetime] = None) -> str:
    dt = now or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond:06d}Z"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


# ---------------------------------------------------------------------------
# Minimal JSON-Schema (draft/2020-12 subset) validator — stdlib only.
# Supports exactly the keywords the frozen and _src/runner schemas use:
# type, const, enum, pattern, minLength, minItems, maxItems, uniqueItems,
# properties, required, additionalProperties, items, allOf, if/then, format
# (date-time only, loosely checked).
# ---------------------------------------------------------------------------

def validate_schema(instance: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    errors: List[str] = []
    _validate_node(instance, schema, path, errors)
    return errors


def _validate_node(inst: Any, schema: Dict[str, Any], path: str, errors: List[str]) -> None:
    if "const" in schema and inst != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {inst!r}")
        return
    if "enum" in schema and inst not in schema["enum"]:
        errors.append(f"{path}: {inst!r} not in enum {schema['enum']!r}")
        return
    if "type" in schema:
        if not _type_ok(inst, schema["type"]):
            errors.append(f"{path}: expected type {schema['type']!r}, got {type(inst).__name__}")
            return
    if isinstance(inst, str):
        if "pattern" in schema and not re.match(schema["pattern"], inst):
            errors.append(f"{path}: {inst!r} does not match pattern {schema['pattern']!r}")
        if "minLength" in schema and len(inst) < schema["minLength"]:
            errors.append(f"{path}: length below minLength {schema['minLength']}")
        if schema.get("format") == "date-time" and not DATE_RE.match(inst):
            errors.append(f"{path}: {inst!r} is not a valid date-time")
    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(inst) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems {schema['maxItems']}")
        if schema.get("uniqueItems") and len(inst) != len({canonical_json(x) for x in inst}):
            errors.append(f"{path}: items are not unique")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(inst):
                _validate_node(item, item_schema, f"{path}[{i}]", errors)
    if isinstance(inst, dict):
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for req in required:
            if req not in inst:
                errors.append(f"{path}: missing required property {req!r}")
        addl = schema.get("additionalProperties", True)
        if addl is False:
            for key in inst:
                if key not in props:
                    errors.append(f"{path}: additional property {key!r} not allowed")
        for key, val in inst.items():
            if key in props:
                _validate_node(val, props[key], f"{path}.{key}", errors)
    for sub in schema.get("allOf", []):
        if "if" in sub and "then" in sub:
            if not _validate_node_bool(inst, sub["if"]):
                continue
            _validate_node(inst, sub["then"], path, errors)
        else:
            _validate_node(inst, sub, path, errors)


def _validate_node_bool(inst: Any, schema: Dict[str, Any]) -> bool:
    return not _validate_node_collect(inst, schema)


def _validate_node_collect(inst: Any, schema: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    _validate_node(inst, schema, "$", errs)
    return errs


def _type_ok(inst: Any, expected: Any) -> bool:
    types = expected if isinstance(expected, list) else [expected]
    for t in types:
        if t == "object" and isinstance(inst, dict):
            return True
        if t == "array" and isinstance(inst, list):
            return True
        if t == "string" and isinstance(inst, str):
            return True
        if t == "integer" and isinstance(inst, int) and not isinstance(inst, bool):
            return True
        if t == "number" and isinstance(inst, (int, float)) and not isinstance(inst, bool):
            return True
        if t == "boolean" and isinstance(inst, bool):
            return True
        if t == "null" and inst is None:
            return True
    return False


def load_schema(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


_REQUEST_SCHEMA = None
_RESULT_SCHEMA = None


def request_schema() -> Dict[str, Any]:
    global _REQUEST_SCHEMA
    if _REQUEST_SCHEMA is None:
        _REQUEST_SCHEMA = load_schema(FROZEN_SCHEMA_DIR / "runner-request-v1.schema.json")
    return _REQUEST_SCHEMA


def result_schema() -> Dict[str, Any]:
    global _RESULT_SCHEMA
    if _RESULT_SCHEMA is None:
        _RESULT_SCHEMA = load_schema(FROZEN_SCHEMA_DIR / "runner-result-v1.schema.json")
    return _RESULT_SCHEMA


# ---------------------------------------------------------------------------
# Action registry
# ---------------------------------------------------------------------------

class ActionRegistry:
    def __init__(self, path: Path = RUNNER_PKG_DIR / "actions-v1.json"):
        self.path = path
        data = json.loads(path.read_text(encoding="utf-8"))
        self.raw = data
        self.actions: Dict[str, Dict[str, Any]] = {a["id"]: a for a in data["actions"]}
        self.forbidden_patterns = [re.compile(f["pattern"]) for f in data.get("forbidden", [])]

    def is_forbidden(self, action_id: str) -> bool:
        return any(p.match(action_id) for p in self.forbidden_patterns)

    def get(self, action_id: str) -> Optional[Dict[str, Any]]:
        return self.actions.get(action_id)

    def is_registered(self, action_id: str) -> bool:
        return action_id in self.actions


# ---------------------------------------------------------------------------
# Findings (structured rejection/failure codes)
# ---------------------------------------------------------------------------

class RunnerDispatchError(Exception):
    """Raised for programming-usage errors (not business-rule rejections)."""


FINDING = {
    "UNKNOWN_ACTION": "RD-UNKNOWN-ACTION",
    "GENERIC_FORBIDDEN": "RD-GENERIC-ACTION-FORBIDDEN",
    "SCHEMA_INVALID": "RD-SCHEMA-INVALID",
    "STALE_BASE": "RD-STALE-BASE",
    "STALE_EPOCH": "RD-STALE-EPOCH",
    "STALE_REF": "RD-STALE-REF",
    "BAD_SCOPE": "RD-BAD-SCOPE",
    "SCOPE_COLLISION": "RD-SCOPE-COLLISION",
    "GOVERNANCE_SCOPE": "RD-GOVERNANCE-SCOPE",
    "UNAVAILABLE_DEPENDENCY": "RD-UNAVAILABLE-DEPENDENCY",
    "UNAVAILABLE_CREDENTIAL": "RD-UNAVAILABLE-CREDENTIAL",
    "CREDENTIAL_NOT_ALLOWED": "RD-CREDENTIAL-NOT-ALLOWED",
    "NETWORK_DENIED": "RD-NETWORK-DENIED",
    "AUTHORITY_VIOLATION": "RD-AUTHORITY-VIOLATION",
    "MISSING_ARG": "RD-MISSING-ARG",
    "DUPLICATE_IDEMPOTENCE": "RD-DUPLICATE-IDEMPOTENCE",
    "TIMEOUT": "RD-TIMEOUT",
    "CANCELLED": "RD-CANCELLED",
    "MERGE_CONFLICT": "RD-MERGE-CONFLICT",
    "CLAIM_FOREIGN_TOKEN": "RD-CLAIM-FOREIGN-TOKEN",
    "TAMPERED_RESULT": "RD-TAMPERED-RESULT",
    "SECRET_LEAK": "RD-SECRET-VALUE-REJECTED",
}


# ---------------------------------------------------------------------------
# Preflight context supplied by the caller (repo/authority/credential state)
# ---------------------------------------------------------------------------

@dataclass
class PreflightContext:
    base_commit: str
    authority_epoch: str = "legacy-writable"
    capability_class: str = "sandboxed-grunt"
    ref_state: Dict[str, str] = field(default_factory=dict)  # "refs/heads/x" -> tip
    available_dependencies: Set[str] = field(default_factory=set)
    credential_store: Set[str] = field(default_factory=set)
    network_allowed_hosts: Set[str] = field(default_factory=set)
    governance_write_ok: bool = False


SECRET_LIKE_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}"
)


def _parse_preflight_args(preflight: Sequence[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for entry in preflight:
        m = re.match(r"^arg:([A-Za-z0-9_]+)=(.*)$", entry, re.DOTALL)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def preflight(
    request: Dict[str, Any],
    registry: ActionRegistry,
    ctx: PreflightContext,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Return (accepted, findings, parsed_args). Fail-closed: any finding => rejected."""

    findings: List[str] = []

    schema_errors = validate_schema(request, request_schema())
    if schema_errors:
        findings.append(FINDING["SCHEMA_INVALID"])
        return False, findings, {}

    for blob in canonical_json(request), request.get("idempotence_key", ""):
        text = blob if isinstance(blob, str) else blob.decode("utf-8", "ignore")
        if SECRET_LIKE_RE.search(text):
            findings.append(FINDING["SECRET_LEAK"])
            return False, findings, {}

    typed_action = _typed_action_of(request)
    if typed_action is None or registry.is_forbidden(typed_action):
        findings.append(FINDING["GENERIC_FORBIDDEN"])
        return False, findings, {}
    action = registry.get(typed_action)
    if action is None:
        findings.append(FINDING["UNKNOWN_ACTION"])
        return False, findings, {}

    if request["expected_base"] != ctx.base_commit:
        findings.append(FINDING["STALE_BASE"])
    if request["authority_epoch"] != ctx.authority_epoch:
        findings.append(FINDING["STALE_EPOCH"])

    for scope_list in (request["read_scopes"], request.get("write_scopes", [])):
        for entry in scope_list:
            m = re.match(r"^ref:(refs/heads/[^@]+)@([0-9a-f]{40})$", entry)
            if m:
                ref, pinned_tip = m.group(1), m.group(2)
                observed = ctx.ref_state.get(ref)
                if observed is not None and observed != pinned_tip:
                    findings.append(FINDING["STALE_REF"])
            elif entry.startswith("ref:"):
                pass
            else:
                if entry.startswith("/") or ".." in entry.split("/") or "*" in entry:
                    findings.append(FINDING["BAD_SCOPE"])

    for dep in request.get("dependencies", []):
        if dep not in ctx.available_dependencies:
            findings.append(FINDING["UNAVAILABLE_DEPENDENCY"])

    creds = request.get("credential_handles", [])
    if creds and not action["authority"]["credentials"]:
        findings.append(FINDING["CREDENTIAL_NOT_ALLOWED"])
    for handle in creds:
        if handle not in ctx.credential_store:
            findings.append(FINDING["UNAVAILABLE_CREDENTIAL"])

    hosts = request.get("network_hosts", [])
    if hosts and not action["authority"]["network"]:
        findings.append(FINDING["NETWORK_DENIED"])
    for host in hosts:
        if host not in ctx.network_allowed_hosts:
            findings.append(FINDING["NETWORK_DENIED"])

    if action["authority"]["capability_class"] == "privileged" and ctx.capability_class != "privileged":
        findings.append(FINDING["AUTHORITY_VIOLATION"])

    write_scopes = request.get("write_scopes", [])
    touches_governance = any(
        any(s.split("@")[0].split(":", 1)[-1].startswith(pfx) for pfx in GOVERNANCE_PREFIXES)
        for s in write_scopes
    )
    if touches_governance and not ctx.governance_write_ok:
        findings.append(FINDING["GOVERNANCE_SCOPE"])

    args = _parse_preflight_args(request.get("preflight", []))
    for req_arg in action["args"]["required"]:
        if req_arg not in args and req_arg not in request:
            findings.append(FINDING["MISSING_ARG"])

    accepted = len(findings) == 0
    return accepted, findings, args


def _typed_action_of(request: Dict[str, Any]) -> Optional[str]:
    key = request.get("idempotence_key", "")
    if ":" not in key:
        return None
    prefix = key.split(":", 1)[0]
    return prefix


# ---------------------------------------------------------------------------
# .runner/ runtime root layout
# ---------------------------------------------------------------------------

class RunnerRoot:
    """Manages the git-ignored ``.runner/`` runtime root layout."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.drafts = self.root / "drafts"
        self.requests = self.root / "requests"
        self.claims = self.root / "claims"
        self.claims_expired = self.claims / "_expired"
        self.results = self.root / "results"
        self.logs = self.root / "logs"
        self.cancel = self.root / "cancel"
        self.idempotence = self.root / "idempotence"
        self.quarantine = self.root / "quarantine"

    def ensure_layout(self) -> None:
        for d in (
            self.root, self.drafts, self.requests, self.claims,
            self.claims_expired, self.results, self.logs, self.cancel,
            self.idempotence, self.quarantine,
        ):
            d.mkdir(parents=True, exist_ok=True)

    # -- drafts / publication --------------------------------------------

    def draft_dir(self, agent: str, request_id: str) -> Path:
        return self.drafts / agent / request_id

    def write_draft(self, agent: str, request_id: str, request_obj: Dict[str, Any]) -> Path:
        d = self.draft_dir(agent, request_id)
        d.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema": "draft-manifest@v1",
            "agent": agent,
            "request_id": request_id,
            "created_at": now_iso(),
            "request": request_obj,
        }
        (d / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        # request.json is a partial/incomplete marker until fully written;
        # write it last so a reader can distinguish "still writing" drafts.
        (d / "request.json").write_text(json.dumps(request_obj, indent=2, sort_keys=True), encoding="utf-8")
        return d

    def publish_draft(self, agent: str, request_id: str) -> Path:
        """Atomically publish a complete draft via same-filesystem rename."""
        d = self.draft_dir(agent, request_id)
        req_path = d / "request.json"
        manifest_path = d / "manifest.json"
        if not req_path.is_file() or not manifest_path.is_file():
            raise RunnerDispatchError(f"draft incomplete: {d}")
        request_obj = json.loads(req_path.read_text(encoding="utf-8"))
        errs = validate_schema(request_obj, request_schema())
        if errs:
            raise RunnerDispatchError(f"draft request fails schema: {errs}")
        dest = self.requests / request_id
        if dest.exists():
            raise RunnerDispatchError(f"request already published: {request_id}")
        os.rename(d, dest)  # atomic, same filesystem under .runner/
        # clean up now-empty agent draft directory (best effort, non-fatal)
        try:
            d.parent.rmdir()
        except OSError:
            pass
        return dest

    def list_ready_requests(self) -> List[str]:
        """Only ever scans requests/; drafts/ is never visible here."""
        if not self.requests.is_dir():
            return []
        out = []
        for entry in sorted(self.requests.iterdir()):
            if not entry.is_dir():
                continue
            req_path = entry / "request.json"
            if not req_path.is_file():
                continue
            try:
                obj = json.loads(req_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if validate_schema(obj, request_schema()):
                continue
            out.append(entry.name)
        return out

    def read_request(self, request_id: str) -> Dict[str, Any]:
        return json.loads((self.requests / request_id / "request.json").read_text(encoding="utf-8"))

    # -- claims / leases ----------------------------------------------------

    def lease_path(self, request_id: str) -> Path:
        return self.claims / f"{request_id}.lease.json"

    def claim(self, request_id: str, worker_id: str, lease_seconds: int = 600,
              retry_of: Optional[str] = None, now: Optional[datetime] = None) -> Path:
        self.reclaim_stale_leases(now=now)
        path = self.lease_path(request_id)
        now_dt = now or datetime.now(timezone.utc)
        lease = {
            "schema": "runner-lease@v1",
            "request_id": request_id,
            "worker_id": worker_id,
            "claimed_at": now_iso(now_dt),
            "lease_expires_at": now_iso(now_dt + timedelta(seconds=lease_seconds)),
            "retry_of": retry_of,
        }
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            raise RunnerDispatchError(f"already claimed: {request_id}")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(lease, indent=2, sort_keys=True))
        return path

    def read_lease(self, request_id: str) -> Optional[Dict[str, Any]]:
        path = self.lease_path(request_id)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def release_claim(self, request_id: str) -> None:
        path = self.lease_path(request_id)
        if path.is_file():
            path.unlink()

    def reclaim_stale_leases(self, now: Optional[datetime] = None) -> List[str]:
        """Move an expired lease with no result to _expired/ so it can be reclaimed."""
        now_dt = now or datetime.now(timezone.utc)
        reclaimed = []
        if not self.claims.is_dir():
            return reclaimed
        for path in list(self.claims.glob("*.lease.json")):
            try:
                lease = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            request_id = lease["request_id"]
            if self.result_path(request_id).is_file():
                continue
            expires = datetime.strptime(lease["lease_expires_at"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            if now_dt > expires:
                dest = self.claims_expired / path.name
                shutil.move(str(path), str(dest))
                reclaimed.append(request_id)
        return reclaimed

    def currently_claimed_write_scopes(self, exclude_request_id: Optional[str] = None) -> List[Set[str]]:
        out = []
        if not self.claims.is_dir():
            return out
        for path in self.claims.glob("*.lease.json"):
            try:
                lease = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            rid = lease["request_id"]
            if rid == exclude_request_id:
                continue
            if self.result_path(rid).is_file():
                continue  # already resolved, no longer "in flight"
            try:
                req = self.read_request(rid)
            except (OSError, json.JSONDecodeError):
                continue
            out.append(set(req.get("write_scopes", [])))
        return out

    # -- cancellation ---------------------------------------------------

    def cancel_path(self, request_id: str) -> Path:
        return self.cancel / f"{request_id}.cancel"

    def request_cancel(self, request_id: str) -> None:
        self.cancel_path(request_id).write_text(now_iso(), encoding="utf-8")

    def is_cancel_requested(self, request_id: str) -> bool:
        return self.cancel_path(request_id).is_file()

    # -- results (immutable / append-only) -------------------------------

    def result_path(self, request_id: str) -> Path:
        return self.results / f"{request_id}.result.json"

    def write_result(self, request_id: str, result_obj: Dict[str, Any]) -> Path:
        path = self.result_path(request_id)
        digestable = {k: v for k, v in result_obj.items() if k != "result_digest"}
        digest = "sha256:" + sha256_hex(canonical_json(digestable))
        result_obj = dict(result_obj)
        result_obj["result_digest"] = digest
        errs = validate_schema(result_obj, result_schema())
        if errs:
            raise RunnerDispatchError(f"result fails schema: {errs}")
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            raise RunnerDispatchError(f"result already recorded (immutable): {request_id}")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(result_obj, indent=2, sort_keys=True))
        self._update_idempotence_index(request_id, result_obj)
        return path

    def read_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        path = self.result_path(request_id)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def verify_result_untampered(self, request_id: str) -> bool:
        obj = self.read_result(request_id)
        if obj is None:
            return False
        stored = obj.get("result_digest")
        digestable = {k: v for k, v in obj.items() if k != "result_digest"}
        recomputed = "sha256:" + sha256_hex(canonical_json(digestable))
        return stored == recomputed

    # -- idempotence index -------------------------------------------------

    def _idempotence_index_path(self, idempotence_key: str) -> Path:
        return self.idempotence / f"{sha256_hex(idempotence_key.encode('utf-8'))}.json"

    def _update_idempotence_index(self, request_id: str, result_obj: Dict[str, Any]) -> None:
        try:
            req = self.read_request(request_id)
        except (OSError, json.JSONDecodeError):
            return
        key = req.get("idempotence_key")
        if not key:
            return
        path = self._idempotence_index_path(key)
        path.write_text(json.dumps({
            "idempotence_key": key,
            "request_id": request_id,
            "status": result_obj["status"],
        }, sort_keys=True), encoding="utf-8")

    def idempotence_lookup(self, idempotence_key: str) -> Optional[Dict[str, Any]]:
        path = self._idempotence_index_path(idempotence_key)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    # -- logs (append-only) -----------------------------------------------

    def log_path(self, request_id: str) -> Path:
        return self.logs / f"{request_id}.log"

    def append_log(self, request_id: str, line: str) -> None:
        with open(self.log_path(request_id), "a", encoding="utf-8") as fh:
            fh.write(line.rstrip("\n") + "\n")

    # -- quarantine (recovery.quarantine@v1 support) -----------------------

    def quarantine_artifact(self, path: Path, reason: str) -> Path:
        dest = self.quarantine / f"{path.name}.{uuid.uuid4().hex[:8]}"
        shutil.move(str(path), str(dest))
        (self.quarantine / f"{dest.name}.reason.txt").write_text(reason, encoding="utf-8")
        return dest


# ---------------------------------------------------------------------------
# Execution: handlers + dispatcher
# ---------------------------------------------------------------------------

@dataclass
class ExecOutcome:
    status: str  # succeeded | failed | rejected | cancelled | partial_mutation_recovered
    outputs: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)


@dataclass
class ExecContext:
    request: Dict[str, Any]
    args: Dict[str, Any]
    runner_root: "RunnerRoot"
    request_id: str
    repo_root: Optional[Path] = None
    temp_root: Optional[Path] = None
    cancel_event: threading.Event = field(default_factory=threading.Event)

    def is_cancelled(self) -> bool:
        return self.cancel_event.is_set() or self.runner_root.is_cancel_requested(self.request_id)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=check,
    )


def _git_text(repo: Path, *args: str) -> str:
    return _git(repo, *args).stdout.strip()


# -- typed git handlers, implemented against a real Git repo -----------------

def handle_git_base_branch(ctx: ExecContext) -> ExecOutcome:
    repo = ctx.repo_root
    item_id = ctx.args["item_id"]
    parent_branch = ctx.args["parent_branch"]
    expected_tip = ctx.args["expected_parent_tip"]
    observed = _git_text(repo, "rev-parse", f"refs/heads/{parent_branch}")
    if observed != expected_tip:
        return ExecOutcome("rejected", findings=[FINDING["STALE_BASE"]])
    existing = _git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{item_id}", check=False)
    if existing.returncode == 0:
        return ExecOutcome("rejected", findings=["RD-BRANCH-ALREADY-EXISTS"])
    _git(repo, "branch", item_id, expected_tip)
    return ExecOutcome("succeeded", outputs=[f"ref:refs/heads/{item_id}@{expected_tip}"])


def handle_git_merge_prereqs(ctx: ExecContext) -> ExecOutcome:
    repo = ctx.repo_root
    item_id = ctx.args["item_id"]
    expected_base = ctx.args["expected_base"]
    sources = ctx.args.get("sources") or []
    if isinstance(sources, str):
        sources = json.loads(sources)
    observed = _git_text(repo, "rev-parse", f"refs/heads/{item_id}")
    if observed != expected_base:
        return ExecOutcome("rejected", findings=[FINDING["STALE_BASE"]])
    tmp = Path(tempfile.mkdtemp(prefix="rd-merge-"))
    outputs: List[str] = []
    try:
        _git(repo, "worktree", "add", "--detach", "-f", str(tmp), expected_base)
        cur = expected_base
        for src in sources:
            branch, tip = src["branch"], src["tip"]
            observed_src = _git_text(repo, "rev-parse", f"refs/heads/{branch}")
            if observed_src != tip:
                _git(tmp, "merge", "--abort", check=False)
                return ExecOutcome("rejected", findings=["RD-STALE-SOURCE-TIP"])
            res = _git(tmp, "merge", "--no-ff", "-m", f"merge({item_id}): {branch}", tip, check=False)
            if res.returncode != 0:
                _git(tmp, "merge", "--abort", check=False)
                return ExecOutcome("failed", findings=[FINDING["MERGE_CONFLICT"]])
            cur = _git_text(tmp, "rev-parse", "HEAD")
            outputs.append(f"merged-branch-tip:refs/heads/{branch}@{tip}")
            outputs.append(f"merge-commit:{cur}")
        cas = _git(repo, "update-ref", f"refs/heads/{item_id}", cur, expected_base, check=False)
        if cas.returncode != 0:
            return ExecOutcome("failed", findings=["RD-CAS-LOST-RACE"])
        return ExecOutcome("succeeded", outputs=outputs)
    finally:
        _git(repo, "worktree", "remove", "--force", str(tmp), check=False)
        shutil.rmtree(tmp, ignore_errors=True)


def handle_git_integrate_checkpoint(ctx: ExecContext) -> ExecOutcome:
    repo = ctx.repo_root
    target_kind = ctx.args["target_kind"]
    expected_base = ctx.args["expected_base"]
    source_branch = ctx.args["source_branch"]
    target_ref = "main" if target_kind == "main" else ctx.args["item_id"]
    observed = _git_text(repo, "rev-parse", f"refs/heads/{target_ref}")
    if observed != expected_base:
        return ExecOutcome("rejected", findings=[FINDING["STALE_BASE"]])
    tmp = Path(tempfile.mkdtemp(prefix="rd-integ-"))
    try:
        _git(repo, "worktree", "add", "--detach", "-f", str(tmp), expected_base)
        src_tip = _git_text(repo, "rev-parse", f"refs/heads/{source_branch}")
        res = _git(tmp, "merge", "--no-ff", "-m", f"integrate: {source_branch} -> {target_ref}", src_tip, check=False)
        if res.returncode != 0:
            _git(tmp, "merge", "--abort", check=False)
            return ExecOutcome("failed", findings=[FINDING["MERGE_CONFLICT"]])
        new_tip = _git_text(tmp, "rev-parse", "HEAD")
        cas = _git(repo, "update-ref", f"refs/heads/{target_ref}", new_tip, expected_base, check=False)
        if cas.returncode != 0:
            return ExecOutcome("failed", findings=["RD-CAS-LOST-RACE"])
        return ExecOutcome("succeeded", outputs=[f"merge-commit:{new_tip}"])
    finally:
        _git(repo, "worktree", "remove", "--force", str(tmp), check=False)
        shutil.rmtree(tmp, ignore_errors=True)


def handle_git_rollback_ref_cleanup(ctx: ExecContext) -> ExecOutcome:
    repo = ctx.repo_root
    ref, expected_current, restore_to = ctx.args["ref"], ctx.args["expected_current"], ctx.args["restore_to"]
    cas = _git(repo, "update-ref", ref, restore_to, expected_current, check=False)
    if cas.returncode != 0:
        return ExecOutcome("failed", findings=["RD-ROLLBACK-CAS-FAILED"])
    temp_refs = ctx.args.get("temporary_refs") or []
    if isinstance(temp_refs, str):
        temp_refs = json.loads(temp_refs)
    for tref in temp_refs:
        _git(repo, "update-ref", "-d", tref, check=False)
    return ExecOutcome("succeeded", outputs=[f"ref:{ref}@{restore_to}"])


def handle_approval_ref_create_append_cas(ctx: ExecContext) -> ExecOutcome:
    repo = ctx.repo_root
    ref = ctx.args["ref"]
    expected_current = ctx.args["expected_current"] or None
    new_value = ctx.args["new_value"]
    existing = _git(repo, "rev-parse", "--verify", "--quiet", ref, check=False)
    observed = existing.stdout.strip() if existing.returncode == 0 else ""
    if (expected_current or "") != observed:
        return ExecOutcome("rejected", findings=["RD-CAS-STALE-REF"])
    cas = _git(repo, "update-ref", ref, new_value, observed, check=False)
    if cas.returncode != 0:
        return ExecOutcome("failed", findings=["RD-CAS-LOST-RACE"])
    return ExecOutcome("succeeded", outputs=[f"ref:{ref}@{new_value}"])


def handle_claim_finalize(ctx: ExecContext) -> ExecOutcome:
    claim_path = Path(ctx.args["claim_path"])
    owner_token = ctx.args["owner_token"]
    if not claim_path.is_file():
        return ExecOutcome("rejected", findings=["RD-CLAIM-NOT-FOUND"])
    text = claim_path.read_text(encoding="utf-8")
    m = re.search(r"^owner_token:\s*(.+)$", text, re.MULTILINE)
    existing_token = m.group(1).strip() if m else None
    if existing_token is not None and existing_token != owner_token:
        return ExecOutcome("rejected", findings=[FINDING["CLAIM_FOREIGN_TOKEN"]])
    return ExecOutcome("succeeded", outputs=[f"claim-finalized:{claim_path}"])


def _generic_simulated_handler(ctx: ExecContext) -> ExecOutcome:
    """Non-mutating/non-git actions: record a bounded simulated success.

    These wrap external scripts (bootstrap, provisioning, publish, approval
    readiness, evidence, recovery planning, validation runners) that this
    Task explicitly does not activate. The handler still runs through full
    preflight (capability/network/credential/scope checks) so the DoD's
    failure-category coverage exercises the real gate, not a stub gate.
    """
    return ExecOutcome("succeeded", outputs=[f"simulated:{_typed_action_of(ctx.request)}"])


DEFAULT_HANDLERS: Dict[str, Callable[[ExecContext], ExecOutcome]] = {
    "git.base-branch@v1": handle_git_base_branch,
    "git.merge-prereqs@v1": handle_git_merge_prereqs,
    "git.integrate-checkpoint@v1": handle_git_integrate_checkpoint,
    "git.rollback-ref-cleanup@v1": handle_git_rollback_ref_cleanup,
    "approval.ref-create-append-cas@v1": handle_approval_ref_create_append_cas,
    "claim.finalize@v1": handle_claim_finalize,
}


class Dispatcher:
    """Ties RunnerRoot + ActionRegistry + preflight + handlers together."""

    def __init__(
        self,
        runner_root: RunnerRoot,
        registry: Optional[ActionRegistry] = None,
        repo_root: Optional[Path] = None,
        handlers: Optional[Dict[str, Callable[[ExecContext], ExecOutcome]]] = None,
        max_workers: int = 1,
    ):
        self.runner_root = runner_root
        self.registry = registry or ActionRegistry()
        self.repo_root = repo_root
        self.handlers = dict(DEFAULT_HANDLERS)
        if handlers:
            self.handlers.update(handlers)
        self.max_workers = max_workers

    def _handler_for(self, action_id: str) -> Callable[[ExecContext], ExecOutcome]:
        return self.handlers.get(action_id, _generic_simulated_handler)

    def claim_and_execute(
        self,
        request_id: str,
        worker_id: str,
        pf_ctx: PreflightContext,
        lease_seconds: int = 600,
    ) -> Dict[str, Any]:
        """Claim a ready request and run it to completion, writing a result."""
        active = len([
            p for p in self.runner_root.claims.glob("*.lease.json")
            if not self.runner_root.result_path(json.loads(p.read_text(encoding="utf-8"))["request_id"]).is_file()
        ]) if self.runner_root.claims.is_dir() else 0
        if active >= self.max_workers:
            raise RunnerDispatchError("worker limit reached")

        request = self.runner_root.read_request(request_id)
        idem = request.get("idempotence_key")
        retry_of = None
        if idem:
            prior = self.runner_root.idempotence_lookup(idem)
            if prior and prior["status"] == "succeeded" and prior["request_id"] != request_id:
                return self._finalize_result(request_id, "rejected", [], [FINDING["DUPLICATE_IDEMPOTENCE"]], pf_ctx)
            if prior and prior["status"] in ("failed", "rejected", "cancelled") and prior["request_id"] != request_id:
                retry_of = prior["request_id"]

        collisions = self.runner_root.currently_claimed_write_scopes(exclude_request_id=request_id)
        my_scopes = set(request.get("write_scopes", []))
        if my_scopes and any(my_scopes & other for other in collisions):
            return self._finalize_result(request_id, "rejected", [], [FINDING["SCOPE_COLLISION"]], pf_ctx)

        self.runner_root.claim(request_id, worker_id, lease_seconds=lease_seconds, retry_of=retry_of)

        accepted, findings, args = preflight(request, self.registry, pf_ctx)
        if not accepted:
            return self._finalize_result(request_id, "rejected", [], findings, pf_ctx, retry_of=retry_of)

        action_id = _typed_action_of(request)
        action = self.registry.get(action_id)
        handler = self._handler_for(action_id)

        exec_ctx = ExecContext(
            request=request, args=args, runner_root=self.runner_root,
            request_id=request_id, repo_root=self.repo_root,
        )
        timeout = request["limits"]["timeout_seconds"]

        outcome_box: Dict[str, ExecOutcome] = {}
        error_box: Dict[str, BaseException] = {}

        def _run():
            try:
                outcome_box["outcome"] = handler(exec_ctx)
            except BaseException as exc:  # noqa: BLE001 - captured across thread boundary
                error_box["error"] = exc

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            self.runner_root.request_cancel(request_id)
            return self._finalize_result(request_id, "failed", [], [FINDING["TIMEOUT"]], pf_ctx, retry_of=retry_of)

        if exec_ctx.is_cancelled():
            return self._finalize_result(request_id, "cancelled", [], [FINDING["CANCELLED"]], pf_ctx, retry_of=retry_of)

        if "error" in error_box:
            self.runner_root.append_log(request_id, f"handler-exception: {error_box['error']!r}")
            return self._finalize_result(request_id, "failed", [], ["RD-HANDLER-EXCEPTION"], pf_ctx, retry_of=retry_of)

        outcome = outcome_box["outcome"]
        return self._finalize_result(
            request_id, outcome.status, outcome.outputs, outcome.findings, pf_ctx, retry_of=retry_of,
        )

    def _finalize_result(
        self, request_id: str, status: str, outputs: List[str], findings: List[str],
        pf_ctx: PreflightContext, retry_of: Optional[str] = None,
    ) -> Dict[str, Any]:
        started = now_iso()
        result_obj: Dict[str, Any] = {
            "schema": "runner-result@v1",
            "request_id": request_id,
            "status": status,
            "started_at": started,
            "finished_at": now_iso(),
            "base_observed": pf_ctx.base_commit,
            "authority_epoch_observed": pf_ctx.authority_epoch,
            "outputs": outputs,
            "findings": findings,
        }
        if retry_of:
            result_obj["retry_of"] = retry_of
        path = self.runner_root.write_result(request_id, result_obj)
        self.runner_root.append_log(request_id, f"result: {status} findings={findings}")
        return json.loads(path.read_text(encoding="utf-8"))

    def cancel(self, request_id: str) -> None:
        self.runner_root.request_cancel(request_id)


__all__ = [
    "ActionRegistry",
    "Dispatcher",
    "ExecContext",
    "ExecOutcome",
    "FINDING",
    "PreflightContext",
    "RunnerDispatchError",
    "RunnerRoot",
    "preflight",
    "validate_schema",
    "request_schema",
    "result_schema",
]
