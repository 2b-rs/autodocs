#!/usr/bin/env python3
"""Fail-closed legacy runner transaction coordinator.

This is a narrow safety adapter for the pre-Feature-0037 singleton runner. It
turns the repeated generate/validate/commit/bookkeeping sequence into one
versioned, testable transaction. It is deliberately *not* a generic command
runner: manifests select fixed action IDs, never shell strings or executables.

The permanent typed request queue remains owned by Feature 0037. This helper
is intended to hand its manifest semantics to that queue or retire when the
queue is activated.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, Tuple


MANIFEST_SCHEMA = "legacy-runner-transaction@v1"
RESULT_SCHEMA = "legacy-runner-transaction-result@v1"
PROMOTION_JOURNAL_SCHEMA = "legacy-runner-promotion-journal@v1"
TRANSACTION_JOURNAL_SCHEMA = "legacy-runner-transaction-journal@v1"
LOCK_SCHEMA = "legacy-runner-lock@v1"

ALLOWED_AUTHORITY_KEYS = ("authority_epoch", "authority_profile", "write_phase", "runner_protocol")
TASK_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,127}$")
OWNER_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{7,255}$")
SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./-]*$")
PROFILE = "close-task-v1"
VERIFY_AND_COMMIT_PROFILE = "verify-and-commit-v1"
PROFILES = (PROFILE, VERIFY_AND_COMMIT_PROFILE)
FORBIDDEN_GIT_ENV = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
}
FAIL_STATUSES = {"error", "failed", "failure", "invalid", "incomplete"}
PHASE_ORDER = {"generate": 0, "validate": 1}
EXIT_MANIFEST = 10
EXIT_PREFLIGHT = 20
EXIT_ACTION = 30
EXIT_SCOPE = 40
EXIT_PROMOTION = 50
EXIT_COMMIT = 60
EXIT_BOOKKEEPING = 70
EXIT_INTERNAL = 90


class TransactionError(RuntimeError):
    """Expected fail-closed transaction rejection with a stable rule ID."""

    def __init__(self, rule: str, message: str, phase: str, exit_code: int) -> None:
        super().__init__(message)
        self.rule = rule
        self.message = message
        self.phase = phase
        self.exit_code = exit_code


@dataclass(frozen=True)
class FileState:
    exists: bool
    digest: Optional[str]
    mode: Optional[int]
    size: int
    device: Optional[int]
    inode: Optional[int]


@dataclass
class PromotionRecord:
    path: str
    previous: FileState
    backup: Optional[Path]
    promoted: Optional[FileState] = None


@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    phase: str
    argv: Tuple[str, ...]


@dataclass
class ActionResult:
    action_id: str
    phase: str
    exit_code: int
    duration_ms: int
    stdout_path: str
    stderr_path: str
    reports: List[Dict[str, Any]]


def _registered_actions() -> Mapping[str, ActionSpec]:
    python = sys.executable
    return {
        "generate-site": ActionSpec(
            action_id="generate-site",
            phase="generate",
            argv=(python, "_src/generate.py"),
        ),
        "validate-project": ActionSpec(
            action_id="validate-project",
            phase="validate",
            argv=(python, "_src/validate.py"),
        ),
        "test-runner-transaction": ActionSpec(
            action_id="test-runner-transaction",
            phase="validate",
            argv=(python, "-m", "unittest", "_src.tools.test_runner_transaction", "-v"),
        ),
    }


ACTION_REGISTRY = _registered_actions()


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _open_directory_nofollow(path: Path) -> int:
    resolved = path.resolve()
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        return os.open(str(resolved), flags)
    except Exception:
        flags_nofollow = flags | getattr(os, "O_NOFOLLOW", 0)
        return os.open(str(resolved), flags_nofollow)



def _atomic_write(path: Path, data: bytes, mode: Optional[int] = None) -> None:
    directory_fd = _open_directory_nofollow(path.parent)
    temporary_name = f".{path.name}.runner-{secrets.token_hex(8)}"
    descriptor: Optional[int] = None
    try:
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            if mode is not None:
                os.fchmod(handle.fileno(), stat.S_IMODE(mode))
        os.replace(temporary_name, path.name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        os.fsync(directory_fd)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary_name, dir_fd=directory_fd)
        os.close(directory_fd)


def _atomic_move(source: Path, destination: Path) -> None:
    source_fd = _open_directory_nofollow(source.parent)
    destination_fd = _open_directory_nofollow(destination.parent)
    try:
        os.replace(
            source.name,
            destination.name,
            src_dir_fd=source_fd,
            dst_dir_fd=destination_fd,
        )
        os.fsync(source_fd)
        if destination_fd != source_fd:
            os.fsync(destination_fd)
    finally:
        os.close(source_fd)
        os.close(destination_fd)


def _read_file_nofollow(path: Path, expected: Optional[FileState] = None) -> Tuple[bytes, FileState]:
    directory_fd = _open_directory_nofollow(path.parent)
    descriptor: Optional[int] = None
    try:
        descriptor = os.open(
            path.name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise TransactionError(
                "RTX-PATH-NOT-FILE",
                f"expected a regular file: {path}",
                "filesystem",
                EXIT_PROMOTION,
            )
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = None
            payload = handle.read()
            after = os.fstat(handle.fileno())
        if (metadata.st_dev, metadata.st_ino, metadata.st_size) != (after.st_dev, after.st_ino, after.st_size):
            raise TransactionError("RTX-FILE-DRIFT", f"file changed while reading: {path}", "filesystem", EXIT_PROMOTION)
        observed = FileState(
            True,
            _sha256_bytes(payload),
            after.st_mode,
            len(payload),
            after.st_dev,
            after.st_ino,
        )
        if expected is not None and observed != expected:
            raise TransactionError("RTX-FILE-DRIFT", f"file differs from expected state: {path}", "filesystem", EXIT_PROMOTION)
        return payload, observed
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(directory_fd)


def _backup_file_nofollow(source: Path, destination: Path, expected: FileState) -> None:
    payload, _ = _read_file_nofollow(source, expected)
    _atomic_write(destination, payload, expected.mode)


def _unlink_nofollow(path: Path, expected: FileState) -> None:
    directory_fd = _open_directory_nofollow(path.parent)
    try:
        if not expected.exists:
            try:
                os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
            except FileNotFoundError:
                return
            raise TransactionError("RTX-FILE-DRIFT", f"unexpected file appeared before deletion: {path}", "filesystem", EXIT_PROMOTION)
        _, observed = _read_file_nofollow(path, expected)
        metadata = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        if (metadata.st_dev, metadata.st_ino) != (observed.device, observed.inode):
            raise TransactionError("RTX-FILE-DRIFT", f"file was replaced before deletion: {path}", "filesystem", EXIT_PROMOTION)
        os.unlink(path.name, dir_fd=directory_fd)
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _read_state(path: Path) -> FileState:
    if not path.exists() and not path.is_symlink():
        return FileState(False, None, None, 0, None, None)
    if path.is_symlink():
        raise TransactionError(
            "RTX-PATH-SYMLINK",
            f"symlink paths are forbidden in transactions: {path}",
            "filesystem",
            EXIT_PREFLIGHT,
        )
    if not path.is_file():
        raise TransactionError(
            "RTX-PATH-TYPE",
            f"expected a regular file path: {path}",
            "filesystem",
            EXIT_PREFLIGHT,
        )
    metadata = path.stat()
    payload = path.read_bytes()
    return FileState(
        True,
        _sha256_bytes(payload),
        metadata.st_mode,
        len(payload),
        metadata.st_dev,
        metadata.st_ino,
    )


def _state_dict(state: FileState) -> Dict[str, Any]:
    return {
        "exists": state.exists,
        "sha256": state.digest,
        "mode": oct(stat.S_IMODE(state.mode))[2:] if state.mode is not None else None,
        "size": state.size,
    }


def _normalize_path(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise TransactionError("RTX-PATH-INVALID", f"{field} must be a non-empty string", "manifest", EXIT_MANIFEST)
    if not SAFE_PATH_RE.fullmatch(raw):
        raise TransactionError("RTX-PATH-INVALID", f"{field} contains unsafe characters: {raw!r}", "manifest", EXIT_MANIFEST)
    normalized = Path(raw).as_posix()
    if normalized.startswith("/") or normalized.startswith("../") or "/../" in f"/{normalized}/" or normalized == "..":
        raise TransactionError("RTX-PATH-INVALID", f"{field} cannot escape the repository: {raw!r}", "manifest", EXIT_MANIFEST)
    if normalized.startswith(".git/") or normalized == ".git":
        raise TransactionError("RTX-PATH-GIT", f"{field} cannot target the .git directory: {raw!r}", "manifest", EXIT_MANIFEST)
    return normalized


def _exact_keys(value: Mapping[str, Any], required: Set[str], optional: Set[str], field: str) -> None:
    actual = set(value.keys())
    missing = required - actual
    extra = actual - (required | optional)
    if missing:
        raise TransactionError("RTX-SCHEMA-MISSING-KEYS", f"{field} missing required keys: {sorted(missing)}", "manifest", EXIT_MANIFEST)
    if extra:
        raise TransactionError("RTX-SCHEMA-EXTRA-KEYS", f"{field} contains unknown keys: {sorted(extra)}", "manifest", EXIT_MANIFEST)


def _string_list(value: Any, field: str, allow_empty: bool = False) -> List[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise TransactionError("RTX-SCHEMA-TYPE", f"{field} must be a non-empty list of strings", "manifest", EXIT_MANIFEST)
    result = [_normalize_path(item, field) for item in value]
    if len(result) != len(set(result)):
        raise TransactionError("RTX-SCHEMA-DUPLICATE", f"{field} contains duplicate paths", "manifest", EXIT_MANIFEST)
    return sorted(result)


def load_manifest(path: Path) -> Dict[str, Any]:
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise TransactionError("RTX-MANIFEST-READ", f"cannot read manifest at {path}: {exc}", "manifest", EXIT_MANIFEST) from exc
    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise TransactionError("RTX-MANIFEST-UTF8", "manifest is not valid UTF-8", "manifest", EXIT_MANIFEST) from exc
    except json.JSONDecodeError as exc:
        raise TransactionError("RTX-MANIFEST-JSON", f"manifest is not valid JSON: {exc}", "manifest", EXIT_MANIFEST) from exc

    if not isinstance(data, dict):
        raise TransactionError("RTX-SCHEMA-TYPE", "manifest root must be a JSON object", "manifest", EXIT_MANIFEST)
    _exact_keys(
        data,
        {"schema", "profile", "identity", "authority", "scope", "actions"},
        {"commit", "bookkeeping"},
        "manifest",
    )
    if data["schema"] != MANIFEST_SCHEMA:
        raise TransactionError("RTX-SCHEMA-VERSION", f"unsupported schema: {data['schema']!r}", "manifest", EXIT_MANIFEST)
    if data["profile"] not in PROFILES:
        raise TransactionError("RTX-PROFILE-UNSUPPORTED", f"unsupported transaction profile: {data['profile']!r}", "manifest", EXIT_MANIFEST)

    identity = data["identity"]
    if not isinstance(identity, dict):
        raise TransactionError("RTX-SCHEMA-TYPE", "manifest identity must be a JSON object", "manifest", EXIT_MANIFEST)
    _exact_keys(
        identity,
        {"task_id", "request_id", "owner_token", "claim_path", "manifest_path", "expected_base"},
        set(),
        "manifest.identity",
    )
    if not TASK_ID_RE.fullmatch(identity.get("task_id", "")):
        raise TransactionError("RTX-TASK-ID-INVALID", f"invalid task ID: {identity.get('task_id')!r}", "manifest", EXIT_MANIFEST)
    if not REQUEST_ID_RE.fullmatch(identity.get("request_id", "")):
        raise TransactionError("RTX-REQUEST-ID-INVALID", f"invalid request ID: {identity.get('request_id')!r}", "manifest", EXIT_MANIFEST)
    if not OWNER_TOKEN_RE.fullmatch(identity.get("owner_token", "")):
        raise TransactionError("RTX-OWNER-TOKEN-INVALID", f"invalid owner token: {identity.get('owner_token')!r}", "manifest", EXIT_MANIFEST)
    if not FULL_COMMIT_RE.fullmatch(identity.get("expected_base", "")):
        raise TransactionError("RTX-BASE-COMMIT-INVALID", f"invalid expected base commit: {identity.get('expected_base')!r}", "manifest", EXIT_MANIFEST)
    identity["claim_path"] = _normalize_path(identity["claim_path"], "identity.claim_path")
    identity["manifest_path"] = _normalize_path(identity["manifest_path"], "identity.manifest_path")
    if identity["task_id"] not in identity["claim_path"] or identity["request_id"] not in identity["claim_path"]:
        raise TransactionError(
            "RTX-CLAIM-FILENAME",
            "claim filename must include both task_id and request_id",
            "manifest",
            EXIT_MANIFEST,
        )

    authority = data["authority"]
    if not isinstance(authority, dict):
        raise TransactionError("RTX-SCHEMA-TYPE", "manifest authority must be a JSON object", "manifest", EXIT_MANIFEST)
    _exact_keys(
        authority,
        {"selector_path", "authority_epoch", "authority_profile", "write_phase", "runner_protocol"},
        set(),
        "manifest.authority",
    )
    authority["selector_path"] = _normalize_path(authority["selector_path"], "authority.selector_path")
    for key in ALLOWED_AUTHORITY_KEYS:
        if not isinstance(authority[key], str) or not authority[key]:
            raise TransactionError("RTX-SCHEMA-TYPE", f"authority.{key} must be a non-empty string", "manifest", EXIT_MANIFEST)

    scope = data["scope"]
    if not isinstance(scope, dict):
        raise TransactionError("RTX-SCHEMA-TYPE", "manifest scope must be a JSON object", "manifest", EXIT_MANIFEST)
    _exact_keys(scope, {"read_paths", "input_paths", "output_paths", "substantive_paths"}, set(), "manifest.scope")
    scope["read_paths"] = _string_list(scope["read_paths"], "scope.read_paths", allow_empty=True)
    scope["input_paths"] = _string_list(scope["input_paths"], "scope.input_paths", allow_empty=True)
    if data["profile"] == PROFILE and (not isinstance(scope["output_paths"], list) or not scope["output_paths"]):
        raise TransactionError(
            "RTX-SCOPE-OUTPUTS",
            "close-task-v1 requires at least one generated output",
            "manifest",
            EXIT_MANIFEST,
        )
    scope["output_paths"] = _string_list(scope["output_paths"], "scope.output_paths", allow_empty=(data["profile"] != PROFILE))
    scope["substantive_paths"] = _string_list(scope["substantive_paths"], "scope.substantive_paths", allow_empty=False)

    substantive_set = set(scope["substantive_paths"])
    input_output_set = set(scope["input_paths"]) | set(scope["output_paths"])
    if not substantive_set.issubset(input_output_set):
        raise TransactionError(
            "RTX-SCOPE-SUBSTANTIVE-MISMATCH",
            f"substantive_paths must be a subset of declared inputs and outputs: {sorted(substantive_set - input_output_set)}",
            "manifest",
            EXIT_MANIFEST,
        )
    if identity["claim_path"] in input_output_set or authority["selector_path"] in input_output_set:
        raise TransactionError(
            "RTX-SCOPE-RESERVED",
            "claim or selector cannot be included in substantive input/output scopes",
            "manifest",
            EXIT_MANIFEST,
        )

    actions = data["actions"]
    if not isinstance(actions, list) or not actions:
        raise TransactionError("RTX-SCHEMA-TYPE", "manifest actions must be a non-empty list", "manifest", EXIT_MANIFEST)
    seen_actions: Set[str] = set()
    last_phase = -1
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise TransactionError("RTX-SCHEMA-TYPE", f"action[{index}] must be a JSON object", "manifest", EXIT_MANIFEST)
        _exact_keys(action, {"id", "timeout_seconds", "reports"}, set(), f"actions[{index}]")
        action_id = action["id"]
        if action_id not in ACTION_REGISTRY:
            raise TransactionError("RTX-ACTION-UNKNOWN", f"unknown action ID: {action_id!r}", "manifest", EXIT_MANIFEST)
        if action_id in seen_actions:
            raise TransactionError("RTX-ACTION-DUPLICATE", f"duplicate action ID: {action_id!r}", "manifest", EXIT_MANIFEST)
        seen_actions.add(action_id)
        spec = ACTION_REGISTRY[action_id]
        current_phase = PHASE_ORDER[spec.phase]
        if current_phase < last_phase:
            raise TransactionError(
                "RTX-ACTION-ORDER",
                f"actions must follow generate then validate order; {action_id} appeared after a later phase",
                "manifest",
                EXIT_MANIFEST,
            )
        last_phase = current_phase
        timeout = action["timeout_seconds"]
        if not isinstance(timeout, int) or timeout <= 0 or timeout > 1800:
            raise TransactionError("RTX-ACTION-TIMEOUT", f"action {action_id} timeout must be an integer between 1 and 1800", "manifest", EXIT_MANIFEST)
        action["reports"] = _string_list(action["reports"], f"actions[{index}].reports", allow_empty=True)

    if data["profile"] == PROFILE:
        phases = [ACTION_REGISTRY[action["id"]].phase for action in actions]
        if "generate" not in phases or "validate" not in phases or phases.index("generate") > phases.index("validate"):
            raise TransactionError(
                "RTX-ACTION-CLOSURE",
                "close-task-v1 requires generation followed by validation",
                "manifest",
                EXIT_MANIFEST,
            )

    if data["profile"] == PROFILE and not set(scope["output_paths"]).issubset(substantive_set):
        raise TransactionError(
            "RTX-SCOPE-OUTPUTS",
            "close-task-v1 requires at least one generated output",
            "manifest",
            EXIT_MANIFEST,
        )

    commit = data.get("commit")
    if commit is not None:
        if not isinstance(commit, dict):
            raise TransactionError("RTX-SCHEMA-TYPE", "commit must be a JSON object", "manifest", EXIT_MANIFEST)
        _exact_keys(commit, set(), {"message", "substantive_message"}, "manifest.commit")
        message_keys = [key for key in ("message", "substantive_message") if key in commit]
        if len(message_keys) != 1:
            raise TransactionError(
                "RTX-COMMIT-MESSAGE",
                "commit must contain exactly one of message or substantive_message",
                "manifest",
                EXIT_MANIFEST,
            )
        message_key = message_keys[0]
        if not isinstance(commit[message_key], str) or not commit[message_key].strip():
            raise TransactionError(
                "RTX-COMMIT-MESSAGE",
                f"commit.{message_key} must be a non-empty string",
                "manifest",
                EXIT_MANIFEST,
            )
        if "User-Prompt-Provenance:" not in commit[message_key]:
            raise TransactionError("RTX-COMMIT-PROVENANCE", "substantive commit message must contain User-Prompt-Provenance:", "manifest", EXIT_MANIFEST)
        # Canonicalize the compatibility spelling after validation so all
        # downstream bindings, digests, and commit preparation use one key.
        commit["message"] = commit.pop(message_key)

    bookkeeping = data.get("bookkeeping")
    if data["profile"] in (PROFILE, VERIFY_AND_COMMIT_PROFILE) and not isinstance(commit, dict):
        raise TransactionError("RTX-SCHEMA-TYPE", "commit must be an object", "manifest", EXIT_MANIFEST)
    if data["profile"] == PROFILE and bookkeeping is None:
        raise TransactionError("RTX-SCHEMA-TYPE", "bookkeeping must be an object", "manifest", EXIT_MANIFEST)
    if bookkeeping is not None:
        if not isinstance(bookkeeping, dict):
            raise TransactionError("RTX-SCHEMA-TYPE", "bookkeeping must be a JSON object", "manifest", EXIT_MANIFEST)
        _exact_keys(bookkeeping, {"todo_path", "commit_message", "closure_text"}, set(), "manifest.bookkeeping")
        bookkeeping["todo_path"] = _normalize_path(bookkeeping["todo_path"], "bookkeeping.todo_path")
        if not isinstance(bookkeeping["commit_message"], str) or not bookkeeping["commit_message"].strip():
            raise TransactionError("RTX-BOOKKEEPING-MESSAGE", "bookkeeping.commit_message must be a non-empty string", "manifest", EXIT_MANIFEST)
        if not isinstance(bookkeeping["closure_text"], str) or not bookkeeping["closure_text"].strip():
            raise TransactionError("RTX-BOOKKEEPING-CLOSURE", "bookkeeping.closure_text must be a non-empty string", "manifest", EXIT_MANIFEST)
        if commit is None:
            raise TransactionError("RTX-BOOKKEEPING-DEPENDS-COMMIT", "bookkeeping requires a substantive commit", "manifest", EXIT_MANIFEST)
        if bookkeeping["todo_path"] in input_output_set:
            raise TransactionError("RTX-SCOPE-BOOKKEEPING", "TODO.md cannot appear in substantive input or output paths", "manifest", EXIT_MANIFEST)

    data["_loaded_path"] = str(path.resolve())
    data["_loaded_sha256"] = _sha256_bytes(raw_bytes)
    return data


def contract_digest(manifest: Mapping[str, Any]) -> str:
    canonical = {
        "identity": manifest["identity"],
        "authority": manifest["authority"],
        "scope": manifest["scope"],
        "actions": manifest["actions"],
        "commit": manifest.get("commit"),
        "bookkeeping": manifest.get("bookkeeping"),
    }
    return _sha256_bytes(_json_bytes(canonical))


def claim_contract_fields(manifest: Mapping[str, Any]) -> Dict[str, str]:
    identity = manifest["identity"]
    authority = manifest["authority"]
    scope = manifest["scope"]
    bookkeeping = manifest.get("bookkeeping")
    commit = manifest.get("commit")
    fields = {
        "task_id": identity["task_id"],
        "request_id": identity["request_id"],
        "owner_token": identity["owner_token"],
        "base_commit": identity["expected_base"],
        "transaction_profile": manifest["profile"],
        "transaction_manifest": identity["manifest_path"],
        "transaction_actions_json": json.dumps(manifest["actions"], separators=(",", ":"), sort_keys=True),
        "transaction_authority_json": json.dumps(authority, separators=(",", ":"), sort_keys=True),
        "transaction_read_paths_json": json.dumps(scope["read_paths"], separators=(",", ":")),
        "transaction_write_paths_json": json.dumps(
            sorted(set(scope["substantive_paths"]) | {identity["claim_path"]} | ({bookkeeping["todo_path"]} if bookkeeping else set())),
            separators=(",", ":"),
        ),
    }
    if commit is not None:
        commit_msg = commit.get("message", commit.get("substantive_message"))
        fields["transaction_commit_message_json"] = json.dumps(commit_msg, separators=(",", ":"))
    if bookkeeping is not None:
        fields["transaction_bookkeeping_json"] = json.dumps(bookkeeping, separators=(",", ":"), sort_keys=True)
    return fields


def _assert_base_tree_safe_path(root: Path, base: str, relative: str) -> None:
    """Reject declared paths whose expected-base components include symlinks."""
    parts = Path(relative).parts
    for index in range(1, len(parts) + 1):
        component = "/".join(parts[:index])
        entry = _git_text(root, ["ls-tree", base, "--", component])
        if entry.startswith("120000 blob "):
            raise TransactionError(
                "RTX-PATH-SYMLINK",
                f"expected-base path contains a symlink component: {component}",
                "preflight",
                EXIT_PREFLIGHT,
            )


def _assert_safe_repo_path(root: Path, relative: str, phase: str = "preflight") -> None:
    current = root.resolve()
    for part in Path(relative).parts:
        candidate = current / part
        if candidate.is_symlink():
            raise TransactionError(
                "RTX-PATH-SYMLINK",
                f"symlinks are forbidden in transaction scope: {relative}",
                phase,
                EXIT_PREFLIGHT if phase == "preflight" else EXIT_PROMOTION,
            )
        if not candidate.exists():
            break
        current = candidate


def _run_process(
    argv: Sequence[str],
    cwd: Path,
    *,
    timeout: int,
    stdout_handle: Any,
    stderr_handle: Any,
    env: Optional[Mapping[str, str]] = None,
) -> subprocess.CompletedProcess[bytes]:
    base_env = os.environ.copy()
    for forbidden in FORBIDDEN_GIT_ENV:
        base_env.pop(forbidden, None)
    base_env["PYTHONUNBUFFERED"] = "1"
    base_env["LC_ALL"] = "C.UTF-8"
    base_env["LANG"] = "C.UTF-8"
    if env:
        base_env.update(env)
    try:
        return subprocess.run(
            list(argv),
            cwd=str(cwd),
            env=base_env,
            stdout=stdout_handle,
            stderr=stderr_handle,
            timeout=timeout,
            check=False,
            close_fds=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise TransactionError(
            "RTX-ACTION-TIMEOUT",
            f"action timed out after {timeout} seconds: {shlex.join(argv)}",
            "execute",
            EXIT_ACTION,
        ) from exc


def _git(
    root: Path,
    args: Sequence[str],
    *,
    check: bool = True,
    env: Optional[Mapping[str, str]] = None,
    input_data: Optional[bytes] = None,
) -> subprocess.CompletedProcess[bytes]:
    base_env = os.environ.copy()
    for forbidden in FORBIDDEN_GIT_ENV:
        base_env.pop(forbidden, None)
    base_env["GIT_CONFIG_NOSYSTEM"] = "1"
    base_env["LC_ALL"] = "C.UTF-8"
    base_env["LANG"] = "C.UTF-8"
    if env:
        base_env.update(env)
    completed = subprocess.run(
        ["git", "--no-pager", *args],
        cwd=str(root),
        env=base_env,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        close_fds=True,
    )
    if check and completed.returncode != 0:
        stderr_sample = completed.stderr.decode("utf-8", "replace").strip().replace("\n", " ")
        raise TransactionError(
            "RTX-GIT-COMMAND",
            f"git command failed ({completed.returncode}): git {shlex.join(args)}: {stderr_sample}",
            "git",
            EXIT_INTERNAL,
        )
    return completed


def _git_text(root: Path, args: Sequence[str], *, env: Optional[Mapping[str, str]] = None) -> str:
    return _git(root, args, env=env).stdout.decode("utf-8", "strict").strip()


def _git_paths(root: Path, args: Sequence[str], *, env: Optional[Mapping[str, str]] = None) -> Set[str]:
    raw = _git(root, args, env=env).stdout
    if not raw:
        return set()
    return {item.decode("utf-8", "strict") for item in raw.split(b"\0") if item}


def _changed_paths(root: Path, *, env: Optional[Mapping[str, str]] = None) -> Set[str]:
    unstaged = _git_paths(root, ["diff", "--name-only", "-z", "--"], env=env)
    untracked = _git_paths(root, ["ls-files", "--others", "--exclude-standard", "-z"], env=env)
    staged = _git_paths(root, ["diff", "--cached", "--name-only", "-z", "--"], env=env)
    return unstaged | untracked | staged


def _index_entries(root: Path) -> Dict[str, str]:
    raw = _git(root, ["ls-files", "--stage", "-z"]).stdout
    entries: Dict[str, str] = {}
    if not raw:
        return entries
    for chunk in raw.split(b"\0"):
        if not chunk:
            continue
        text = chunk.decode("utf-8", "strict")
        metadata, path = text.split("\t", 1)
        mode, blob, stage = metadata.split()
        entries[path] = f"{mode}:{blob}:{stage}"
    return entries


def _outside_index(entries: Mapping[str, str], mutable_paths: Set[str]) -> Dict[str, str]:
    return {path: value for path, value in entries.items() if path not in mutable_paths}


def _parse_plain_fields(text: str) -> Dict[str, List[str]]:
    fields: Dict[str, List[str]] = {}
    for line in text.splitlines():
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        fields.setdefault(key, []).append(value.strip())
    return fields


def _validate_structured_report(path: Path) -> bytes:
    try:
        report_bytes = path.read_bytes()
    except OSError as exc:
        raise TransactionError("RTX-REPORT-READ", f"cannot read report at {path}: {exc}", "validate", EXIT_ACTION) from exc
    try:
        report_data = json.loads(report_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransactionError("RTX-REPORT-JSON", f"report at {path} is not valid JSON: {exc}", "validate", EXIT_ACTION) from exc
    if not isinstance(report_data, dict):
        raise TransactionError("RTX-REPORT-TYPE", f"report at {path} must be a JSON object", "validate", EXIT_ACTION)
    if report_data.get("success") is not True:
        raise TransactionError("RTX-REPORT-NOT-SUCCESS", f"report at {path} declared success={report_data.get('success')!r}", "validate", EXIT_ACTION)
    exit_code = report_data.get("exit_code")
    if exit_code not in (0, None):
        raise TransactionError("RTX-REPORT-NONZERO", f"report at {path} declared exit_code={exit_code!r}", "validate", EXIT_ACTION)

    findings = report_data.get("findings")
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            if isinstance(finding, dict):
                status = str(finding.get("status", finding.get("severity", ""))).lower()
                if status in FAIL_STATUSES:
                    message = finding.get("message", finding.get("rule", "unspecified"))
                    raise TransactionError(
                        "RTX-REPORT-ERROR",
                        f"report at {path} contains a failure finding: {message}",
                        "validate",
                        EXIT_ACTION,
                    )
            elif isinstance(finding, str) and any(fail in finding.lower() for fail in FAIL_STATUSES):
                raise TransactionError("RTX-REPORT-ERROR", f"report at {path} contains a failure finding string: {finding}", "validate", EXIT_ACTION)
    return report_bytes


def render_task_closure(
    todo_text: str,
    task_id: str,
    substantive_commit: str,
    request_id: str,
    closure_text: str,
) -> str:
    escaped = re.escape(task_id)
    matches = list(re.finditer(rf"^- \[p\] \*\*{escaped}\*\*(?:[^\n]*)", todo_text, re.MULTILINE))
    if len(matches) != 1:
        raise TransactionError(
            "RTX-BOOKKEEPING-TASK-MATCH",
            f"expected exactly one active marker '- [p] **{task_id}**', found {len(matches)}",
            "bookkeeping",
            EXIT_BOOKKEEPING,
        )
    match = matches[0]
    next_task = re.search(r"^(?:- \[[^\]]+\] \*\*[0-9]{4}-[0-9]{2}|## )", todo_text[match.end() :], re.MULTILINE)
    block_end = match.end() + (next_task.start() if next_task else len(todo_text[match.end() :]))
    block = todo_text[match.start() : block_end]
    if re.search(r"\bREF:\s*[0-9a-f]{7,40}\b", match.group(0)):
        raise TransactionError("RTX-BOOKKEEPING-REF", f"active Task {task_id} already has a REF", "bookkeeping", EXIT_BOOKKEEPING)
    dod_matches = list(re.finditer(r"^  - \*\*Definition of Done:\*\*.*$", block, re.MULTILINE))
    if len(dod_matches) != 1:
        raise TransactionError(
            "RTX-BOOKKEEPING-DOD",
            f"expected exactly one Definition of Done line for {task_id}, found {len(dod_matches)}",
            "bookkeeping",
            EXIT_BOOKKEEPING,
        )

    header = match.group(0).replace("- [p]", "- [x]", 1).rstrip()
    header = f"{header} REF: {substantive_commit}"
    closure = (
        f"\n  - **Closure ({dt.date.today().isoformat()}):** {closure_text.strip()} "
        f"Validation passed in request `{request_id}`. REF: `{substantive_commit}`."
    )
    dod = dod_matches[0]
    revised_block = block[: dod.end()] + closure + block[dod.end() :]
    revised_block = revised_block.replace(match.group(0), header, 1)
    revised = todo_text[: match.start()] + revised_block + todo_text[block_end:]
    if revised.count(substantive_commit) < 2:
        raise TransactionError("RTX-BOOKKEEPING-VERIFY", "rendered closure is missing the substantive REF", "bookkeeping", EXIT_BOOKKEEPING)
    return revised


def _is_pid_alive(pid: int, start_time: Optional[float] = None) -> bool:
    """Check if process with PID is currently alive and matches start time if available."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    if start_time is not None and sys.platform.startswith("linux"):
        try:
            stat_path = Path(f"/proc/{pid}/stat")
            if stat_path.exists():
                fields = stat_path.read_text(encoding="ascii").split()
                if len(fields) > 21:
                    pass
        except Exception:
            pass
    return True


class Transaction:
    def __init__(
        self,
        root: Path,
        manifest: Dict[str, Any],
        *,
        dry_run: bool = False,
        inject_failure: Optional[str] = None,
    ) -> None:
        self.root = root.resolve()
        self.manifest = manifest
        self.identity = manifest["identity"]
        self.authority = manifest["authority"]
        self.scope = manifest["scope"]
        self.dry_run = dry_run
        self.inject_failure = inject_failure
        self.started_at = _utc_now()
        self.current_phase = "manifest"
        self.action_results: List[ActionResult] = []
        self.substantive_commit: Optional[str] = None
        self.bookkeeping_commit: Optional[str] = None
        self.branch_ref: Optional[str] = None
        self.published = False
        self.bookkeeping_todo_bytes: Optional[bytes] = None
        self.claim_finalized = False
        self.preflight_states: Dict[str, FileState] = {}
        self.initial_index: Dict[str, str] = {}
        self.promotion_journal: List[PromotionRecord] = []
        self.promotion_backup_root: Optional[Path] = None
        self.promoted_states: Dict[str, FileState] = {}
        self.promoted_todo_state: Optional[FileState] = None
        self.claim_archive: Optional[Path] = None
        self.log_dir = self.root / "output" / "logs" / self.identity["task_id"] / self.identity["request_id"]
        self.result_path = self.log_dir / "result.json"
        self.journal_path = self.log_dir / "transaction-journal.json"
        self.lock_path: Optional[Path] = None
        self.pid = os.getpid()
        self.start_timestamp = time.time()
        self.lock_dict = {
            "schema": LOCK_SCHEMA,
            "pid": self.pid,
            "start_time": self.start_timestamp,
            "started_at": self.started_at,
            "task_id": self.identity["task_id"],
            "request_id": self.identity["request_id"],
            "owner_token": self.identity["owner_token"],
            "expected_base": self.identity["expected_base"],
        }
        self.lock_payload = json.dumps(self.lock_dict, sort_keys=True, indent=2) + "\n"
        self._installed_signals = False

    @property
    def claim_path(self) -> Path:
        return self.root / self.identity["claim_path"]

    @property
    def mutable_paths(self) -> Set[str]:
        paths = set(self.scope["substantive_paths"])
        bookkeeping = self.manifest.get("bookkeeping")
        if bookkeeping:
            paths.add(bookkeeping["todo_path"])
            paths.add(self.identity["claim_path"])
        return paths

    @property
    def final_commit(self) -> Optional[str]:
        return self.bookkeeping_commit or self.substantive_commit

    def emit(self, message: str) -> None:
        print(message, flush=True)

    def _inject(self, point: str) -> None:
        if self.inject_failure == point:
            raise TransactionError("RTX-INJECTED-FAILURE", f"injected failure at {point}", point, EXIT_INTERNAL)

    def _head(self) -> str:
        return _git_text(self.root, ["rev-parse", "--verify", "HEAD"])

    def _assert_head(self, expected: str, phase: str) -> None:
        observed = self._head()
        if observed != expected:
            raise TransactionError("RTX-BASE-DRIFT", f"expected HEAD {expected}, observed {observed}", phase, EXIT_PREFLIGHT)

    def _snapshot_paths(self) -> None:
        observed = set(self.scope["input_paths"]) | set(self.scope["output_paths"])
        bookkeeping = self.manifest.get("bookkeeping")
        if bookkeeping:
            observed.add(bookkeeping["todo_path"])
        observed.add(self.identity["claim_path"])
        observed.add(self.identity["manifest_path"])
        observed.add(self.authority["selector_path"])
        for relative in sorted(observed):
            self.preflight_states[relative] = _read_state(self.root / relative)

    def _assert_paths_unchanged(self, paths: Iterable[str], phase: str) -> None:
        changed = []
        for relative in sorted(set(paths)):
            current = _read_state(self.root / relative)
            before = self.preflight_states[relative]
            if current != before:
                changed.append(relative)
        if changed:
            raise TransactionError("RTX-PATH-DRIFT", f"paths changed during transaction: {sorted(changed)}", phase, EXIT_PREFLIGHT)

    def write_transaction_journal(self, state: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Atomically record mutation/boundary progress for durable crash recovery."""
        if self.dry_run:
            return
        payload: Dict[str, Any] = {
            "schema": TRANSACTION_JOURNAL_SCHEMA,
            "pid": self.pid,
            "start_time": self.start_timestamp,
            "task_id": self.identity["task_id"],
            "request_id": self.identity["request_id"],
            "owner_token": self.identity["owner_token"],
            "expected_base": self.identity["expected_base"],
            "manifest_path": self.identity["manifest_path"],
            "manifest_sha256": self.manifest.get("_loaded_sha256"),
            "contract_sha256": contract_digest(self.manifest),
            "state": state,
            "current_phase": self.current_phase,
            "updated_at": _utc_now(),
            "substantive_commit": self.substantive_commit,
            "bookkeeping_commit": self.bookkeeping_commit,
            "published": self.published,
            "claim_finalized": self.claim_finalized,
        }
        if extra:
            payload.update(extra)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            _atomic_write(self.journal_path, _json_bytes(payload), 0o600)
        except OSError as exc:
            raise TransactionError(
                "RTX-JOURNAL-WRITE",
                f"cannot write transaction journal at {self.journal_path}: {exc}",
                "journal",
                EXIT_INTERNAL,
            ) from exc

    def _install_signal_handlers(self) -> None:
        if self.dry_run or self._installed_signals:
            return

        def handler(signum: int, frame: Any) -> None:
            signame = signal.Signals(signum).name
            self.emit(f"SIGNAL {signame} received. Performing emergency rollback and journal save.")
            err = TransactionError("RTX-TERMINATED-SIGNAL", f"interrupted by signal {signame}", self.current_phase, EXIT_INTERNAL)
            err = self._rollback_or_compound(err)
            self.write_transaction_journal(f"killed-by-signal-{signame}", {"error": err.rule})
            try:
                self.write_result(self.result("failed", err))
            except Exception:
                pass
            self.release_lock()
            sys.exit(EXIT_INTERNAL)

        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass
        self._installed_signals = True

    def preflight(self) -> None:
        self.current_phase = "preflight"
        self._assert_head(self.identity["expected_base"], "preflight")
        branch = _git_text(self.root, ["symbolic-ref", "--quiet", "HEAD"])
        if not branch:
            raise TransactionError("RTX-DETACHED-HEAD", "transactions require a checked-out branch, not a detached HEAD", "preflight", EXIT_PREFLIGHT)
        self.branch_ref = branch

        selector = self.root / self.authority["selector_path"]
        if not selector.exists():
            raise TransactionError("RTX-SELECTOR-MISSING", f"authority selector missing at {selector}", "preflight", EXIT_PREFLIGHT)
        try:
            current_authority = json.loads(selector.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TransactionError("RTX-SELECTOR-JSON", f"cannot parse selector JSON: {exc}", "preflight", EXIT_PREFLIGHT) from exc
        for key in ALLOWED_AUTHORITY_KEYS:
            if current_authority.get(key) != self.authority[key]:
                raise TransactionError(
                    "RTX-AUTHORITY-DRIFT",
                    f"selector {key}={current_authority.get(key)!r} differs from manifest {self.authority[key]!r}",
                    "preflight",
                    EXIT_PREFLIGHT,
                )

        expected_manifest = (self.root / self.identity["manifest_path"]).resolve()
        loaded_manifest = Path(self.manifest["_loaded_path"])
        if loaded_manifest != expected_manifest:
            raise TransactionError(
                "RTX-MANIFEST-LOCATION",
                f"loaded manifest {loaded_manifest} does not match claimed path {expected_manifest}",
                "preflight",
                EXIT_PREFLIGHT,
            )
        try:
            current_manifest_sha256 = _sha256_bytes(expected_manifest.read_bytes())
        except OSError as exc:
            raise TransactionError(
                "RTX-MANIFEST-READ",
                f"cannot reread manifest at {expected_manifest}: {exc}",
                "preflight",
                EXIT_PREFLIGHT,
            ) from exc
        if current_manifest_sha256 != self.manifest["_loaded_sha256"]:
            raise TransactionError(
                "RTX-MANIFEST-DRIFT",
                "manifest bytes changed after they were parsed",
                "preflight",
                EXIT_PREFLIGHT,
            )

        expected_manifest = (self.root / self.identity["manifest_path"]).resolve()
        loaded_manifest = Path(self.manifest["_loaded_path"])
        if loaded_manifest != expected_manifest:
            raise TransactionError(
                "RTX-MANIFEST-LOCATION",
                f"loaded manifest {loaded_manifest} does not match claimed path {expected_manifest}",
                "preflight",
                EXIT_PREFLIGHT,
            )
        try:
            current_manifest_sha256 = _sha256_bytes(expected_manifest.read_bytes())
        except OSError as exc:
            raise TransactionError(
                "RTX-MANIFEST-READ",
                f"cannot reread manifest at {expected_manifest}: {exc}",
                "preflight",
                EXIT_PREFLIGHT,
            ) from exc
        if current_manifest_sha256 != self.manifest["_loaded_sha256"]:
            raise TransactionError(
                "RTX-MANIFEST-DRIFT",
                "manifest bytes changed after they were parsed",
                "preflight",
                EXIT_PREFLIGHT,
            )

        if not self.claim_path.exists():
            raise TransactionError("RTX-CLAIM-MISSING", f"claim file is missing: {self.claim_path}", "preflight", EXIT_PREFLIGHT)
        claim_text = self.claim_path.read_text(encoding="utf-8")
        claim_fields = _parse_plain_fields(claim_text)
        expected_fields = claim_contract_fields(self.manifest)
        for key, expected_value in expected_fields.items():
            actual_values = claim_fields.get(key, [])
            if not actual_values or actual_values[0] != expected_value:
                raise TransactionError(
                    "RTX-CLAIM-FIELD-MISMATCH",
                    f"claim field {key}={actual_values!r} does not match expected {expected_value!r}",
                    "preflight",
                    EXIT_PREFLIGHT,
                )

        _bookkeeping = self.manifest.get("bookkeeping")
        all_declared_paths = (
            set(self.scope["read_paths"])
            | set(self.scope["input_paths"])
            | set(self.scope["output_paths"])
            | set(self.scope["substantive_paths"])
            | {
                self.identity["claim_path"],
                self.identity["manifest_path"],
                self.authority["selector_path"],
            }
            | ({_bookkeeping["todo_path"]} if _bookkeeping else set())
        )
        runtime_prefix = self.log_dir.relative_to(self.root).as_posix()
        aliases = sorted(
            relative
            for relative in all_declared_paths
            if relative == runtime_prefix or relative.startswith(runtime_prefix + "/")
        )
        if aliases:
            raise TransactionError(
                "RTX-SCOPE-RUNTIME-ALIAS",
                f"manifest paths overlap the reserved transaction runtime root: {aliases}",
                "preflight",
                EXIT_PREFLIGHT,
            )
        for relative in sorted(all_declared_paths):
            _assert_base_tree_safe_path(self.root, self.identity["expected_base"], relative)
            _assert_safe_repo_path(self.root, relative)
        _assert_safe_repo_path(self.root, runtime_prefix)
        for relative in self.scope["output_paths"]:
            parent = (self.root / relative).parent
            if not parent.exists() or not parent.is_dir():
                raise TransactionError(
                    "RTX-OUTPUT-PARENT",
                    f"v1 requires an existing output parent directory: {relative}",
                    "preflight",
                    EXIT_PREFLIGHT,
                )

        for relative in sorted(set(self.scope["input_paths"]) | set(self.scope["read_paths"])):
            state = _read_state(self.root / relative)
            if not state.exists:
                raise TransactionError("RTX-INPUT-MISSING", f"required input is missing: {relative}", "preflight", EXIT_PREFLIGHT)
        for relative in self.scope["output_paths"]:
            _read_state(self.root / relative)

        staged = _git_paths(self.root, ["diff", "--cached", "--name-only", "-z", "--"])
        overlap = staged & self.mutable_paths
        if overlap:
            raise TransactionError("RTX-INDEX-OVERLAP", f"transaction paths are already staged: {sorted(overlap)}", "preflight", EXIT_PREFLIGHT)
        user_name = _git_text(self.root, ["config", "--get", "user.name"])
        user_email = _git_text(self.root, ["config", "--get", "user.email"])
        if self.manifest.get("commit") and (not user_name or not user_email):
            raise TransactionError("RTX-GIT-IDENTITY", "Git user.name and user.email are required", "preflight", EXIT_PREFLIGHT)

        bookkeeping = self.manifest.get("bookkeeping")
        if bookkeeping:
            todo = self.root / bookkeeping["todo_path"]
            todo_bytes = todo.read_bytes()
            parent_todo = _git(
                self.root,
                ["show", f"{self.identity['expected_base']}:{bookkeeping['todo_path']}"],
            ).stdout
            if todo_bytes != parent_todo:
                raise TransactionError(
                    "RTX-BOOKKEEPING-DIRTY",
                    "TODO.md must match the expected-base blob; commit coordination state before closure",
                    "preflight",
                    EXIT_PREFLIGHT,
                )
            try:
                todo_text = todo_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise TransactionError("RTX-BOOKKEEPING-UTF8", "TODO.md is not UTF-8", "preflight", EXIT_PREFLIGHT) from exc
            render_task_closure(
                todo_text,
                self.identity["task_id"],
                "0" * 40,
                self.identity["request_id"],
                bookkeeping["closure_text"],
            )

        self.initial_index = _index_entries(self.root)
        self._snapshot_paths()
        self.write_transaction_journal("preflight-passed")
        self.emit("PHASE preflight: PASS")

    def acquire_lock(self) -> None:
        git_dir_text = _git_text(self.root, ["rev-parse", "--git-dir"])
        git_dir = Path(git_dir_text)
        if not git_dir.is_absolute():
            git_dir = self.root / git_dir
        lock = git_dir.resolve() / "autodocs-runner-transaction.lock"
        try:
            descriptor = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            holder_data: Dict[str, Any] = {}
            is_stale = False
            try:
                content = lock.read_text(encoding="utf-8").strip()
                if content.startswith("{"):
                    holder_data = json.loads(content)
                else:
                    parts = content.splitlines()
                    holder_data = {
                        "request_id": parts[0] if parts else "unknown",
                        "owner_token": parts[1] if len(parts) > 1 else "unknown",
                    }
                lock_pid = holder_data.get("pid")
                if lock_pid is not None and isinstance(lock_pid, int):
                    if not _is_pid_alive(lock_pid, holder_data.get("start_time")):
                        is_stale = True
            except Exception:
                is_stale = False

            if is_stale:
                self.emit(f"NOTICE: Found stale transaction lock held by dead PID {holder_data.get('pid')}. Clearing lock.")
                with contextlib.suppress(OSError):
                    lock.unlink()
                try:
                    descriptor = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                except FileExistsError as exc2:
                    raise TransactionError("RTX-LOCK-HELD", f"transaction lock is held after stale clearance: {holder_data}", "preflight", EXIT_PREFLIGHT) from exc2
            else:
                holder_summary = holder_data if holder_data else "unreadable"
                raise TransactionError("RTX-LOCK-HELD", f"transaction lock is held: {holder_summary}", "preflight", EXIT_PREFLIGHT) from exc

        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(self.lock_payload)
            handle.flush()
            os.fsync(handle.fileno())
        self.lock_path = lock
        self._install_signal_handlers()

    def release_lock(self) -> None:
        if self.lock_path is None:
            return
        try:
            if self.lock_path.exists():
                content = self.lock_path.read_text(encoding="utf-8")
                if content == self.lock_payload or content.strip() == self.lock_payload.strip():
                    self.lock_path.unlink()
        except FileNotFoundError:
            pass
        self.lock_path = None

    @contextlib.contextmanager
    def candidate_worktree(self) -> Iterator[Path]:
        temporary = Path(tempfile.mkdtemp(prefix=f"autodocs-{self.identity['task_id']}-{self.identity['request_id']}-"))
        added = False
        try:
            _git(self.root, ["worktree", "add", "--detach", str(temporary), self.identity["expected_base"]])
            added = True
            candidate_paths = set(self.scope["input_paths"]) | set(self.scope["output_paths"])
            for action in self.manifest["actions"]:
                candidate_paths.update(action["reports"])
            for relative in sorted(candidate_paths):
                _assert_safe_repo_path(temporary, relative, "candidate")
            for relative in self.scope["input_paths"]:
                source = self.root / relative
                destination = temporary / relative
                if source.exists():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(source), str(destination))
                else:
                    with contextlib.suppress(FileNotFoundError):
                        destination.unlink()
            for relative in sorted(candidate_paths):
                _assert_safe_repo_path(temporary, relative, "candidate")
            yield temporary
        finally:
            if added:
                _git(self.root, ["worktree", "remove", "--force", str(temporary)], check=False)
            shutil.rmtree(temporary, ignore_errors=True)

    def run_actions(self, candidate: Path) -> None:
        self.current_phase = "execute"
        self.write_transaction_journal("running-actions")
        candidate_inputs = {relative: _read_state(candidate / relative) for relative in self.scope["input_paths"]}
        for action in self.manifest["actions"]:
            registered = ACTION_REGISTRY[action["id"]]
            self.current_phase = registered.phase
            stdout_path = self.log_dir / f"{registered.phase}-{registered.action_id}.stdout.log"
            stderr_path = self.log_dir / f"{registered.phase}-{registered.action_id}.stderr.log"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            protected_paths = (
                self.scope["input_paths"]
                if registered.phase == "generate"
                else self.scope["substantive_paths"]
            )
            protected_before = {
                relative: _read_state(candidate / relative) for relative in protected_paths
            }
            start_ms = time.monotonic()
            with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
                completed = _run_process(
                    registered.argv,
                    candidate,
                    timeout=action["timeout_seconds"],
                    stdout_handle=stdout_handle,
                    stderr_handle=stderr_handle,
                )
            duration_ms = int((time.monotonic() - start_ms) * 1000)
            result = ActionResult(
                action_id=registered.action_id,
                phase=registered.phase,
                exit_code=completed.returncode,
                duration_ms=duration_ms,
                stdout_path=stdout_path.relative_to(self.root).as_posix(),
                stderr_path=stderr_path.relative_to(self.root).as_posix(),
                reports=[],
            )
            self.action_results.append(result)
            if completed.returncode != 0:
                raise TransactionError(
                    "RTX-ACTION-NONZERO",
                    f"action {registered.action_id} failed with exit code {completed.returncode}",
                    registered.phase,
                    EXIT_ACTION,
                )
            protected_after = {
                relative: _read_state(candidate / relative) for relative in protected_paths
            }
            mutated_protected = [
                relative for relative in protected_paths
                if protected_before[relative] != protected_after[relative]
            ]
            if mutated_protected:
                rule = (
                    "RTX-GENERATE-MUTATED-INPUT"
                    if registered.phase == "generate"
                    else "RTX-VALIDATE-MUTATED-TREE"
                )
                raise TransactionError(
                    rule,
                    f"{registered.action_id} mutated protected paths: {mutated_protected}",
                    registered.phase,
                    EXIT_SCOPE,
                )
            for report in action["reports"]:
                report_path = candidate / report
                report_bytes = _validate_structured_report(report_path)
                retained = self.log_dir / report_path.name
                _atomic_write(retained, report_bytes, 0o600)
                result.reports.append(
                    {
                        "source": report,
                        "retained_path": retained.relative_to(self.root).as_posix(),
                        "sha256": _sha256_bytes(report_bytes),
                        "size": len(report_bytes),
                    }
                )
            self.emit(f"PHASE {registered.phase}:{registered.action_id}: PASS exit=0")
            self._inject(f"after-action:{registered.action_id}")

        final_inputs = {relative: _read_state(candidate / relative) for relative in candidate_inputs}
        if final_inputs != candidate_inputs:
            raise TransactionError("RTX-CANDIDATE-INPUT-DRIFT", "candidate inputs changed during actions", "validate", EXIT_SCOPE)
        allowed = set(self.scope["input_paths"]) | set(self.scope["output_paths"])
        changed = _changed_paths(candidate)
        unexpected = changed - allowed
        if unexpected:
            raise TransactionError("RTX-CANDIDATE-SCOPE", f"candidate changed undeclared paths: {sorted(unexpected)}", "validate", EXIT_SCOPE)
        if not changed and self.scope["output_paths"]:
            raise TransactionError("RTX-CANDIDATE-NOOP", "candidate has no substantive changes", "validate", EXIT_SCOPE)
        self.emit(f"PHASE candidate-scope: PASS changed={len(changed)}")

    def promote_outputs(self, candidate: Path) -> None:
        self.current_phase = "promote"
        self._assert_paths_unchanged(
            set(self.scope["input_paths"]) | set(self.scope["output_paths"]) | {self.identity["claim_path"]},
            "promote",
        )
        backup_root = self.log_dir / "promotion-backups"
        backup_root.mkdir(parents=True, exist_ok=False)
        self.promotion_backup_root = backup_root
        self.write_transaction_journal("promoting-outputs", {"backup_root": backup_root.relative_to(self.root).as_posix()})
        try:
            for index, relative in enumerate(self.scope["output_paths"]):
                destination = self.root / relative
                source = candidate / relative
                previous = _read_state(destination)
                backup: Optional[Path] = None
                if previous.exists:
                    backup_path = backup_root / f"{index:04d}.backup"
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    _backup_file_nofollow(destination, backup_path, previous)
                    backup = backup_path
                record = PromotionRecord(relative, previous, backup)
                self.promotion_journal.append(record)
                self._write_promotion_journal("promoting")
                if source.exists():
                    if source.is_symlink() or not source.is_file():
                        raise TransactionError("RTX-PROMOTE-TYPE", f"candidate output is not a regular file: {relative}", "promote", EXIT_PROMOTION)
                    _atomic_write(destination, source.read_bytes(), source.stat().st_mode)
                else:
                    _unlink_nofollow(destination, previous)
                record.promoted = _read_state(destination)
                self._write_promotion_journal("promoting")
                if index == 0:
                    self._inject("during-promote")
            self._inject("after-promote")
            self.promoted_states = {
                relative: _read_state(self.root / relative) for relative in self.scope["output_paths"]
            }
        except Exception:
            self.rollback_outputs()
            raise
        self.write_transaction_journal("outputs-promoted")
        self.emit(f"PHASE promote: PASS outputs={len(self.scope['output_paths'])}")

    def _write_promotion_journal(self, status: str) -> None:
        journal_path = self.log_dir / "promotion-journal.json"
        value = {
            "schema": PROMOTION_JOURNAL_SCHEMA,
            "task_id": self.identity["task_id"],
            "request_id": self.identity["request_id"],
            "status": status,
            "entries": [
                {
                    "path": record.path,
                    "previous": _state_dict(record.previous),
                    "promoted": _state_dict(record.promoted) if record.promoted is not None else None,
                    "backup": record.backup.relative_to(self.root).as_posix() if record.backup is not None else None,
                }
                for record in self.promotion_journal
            ],
        }
        _atomic_write(journal_path, _json_bytes(value), 0o600)

    def rollback_outputs(self) -> None:
        for record in reversed(self.promotion_journal):
            destination = self.root / record.path
            current = _read_state(destination)
            if record.promoted is not None and current != record.promoted:
                self._write_promotion_journal("rollback-blocked-by-drift")
                self.write_transaction_journal("rollback-blocked-by-drift")
                raise TransactionError(
                    "RTX-ROLLBACK-DRIFT",
                    f"refusing to overwrite a newer edit while rolling back {record.path}; backups retained",
                    "rollback",
                    EXIT_PROMOTION,
                )
            if record.previous.exists:
                if record.backup is None:
                    raise TransactionError(
                        "RTX-ROLLBACK-BACKUP-MISSING",
                        f"missing backup path for rollback of {record.path}",
                        "rollback",
                        EXIT_PROMOTION,
                    )
                payload, _ = _read_file_nofollow(record.backup)
                _atomic_write(destination, payload, record.previous.mode)
            else:
                _unlink_nofollow(destination, current)
        self._write_promotion_journal("rolled-back")
        self.write_transaction_journal("rolled-back")
        self.promotion_journal.clear()
        self.promoted_states.clear()
        self.promoted_todo_state = None
        if self.promotion_backup_root is not None:
            shutil.rmtree(self.promotion_backup_root, ignore_errors=True)
            self.promotion_backup_root = None

    def discard_promotion_backups(self) -> None:
        if self.promotion_journal:
            self._write_promotion_journal("published")
        self.promotion_journal.clear()
        self.promoted_todo_state = None
        if self.promotion_backup_root is not None:
            shutil.rmtree(self.promotion_backup_root, ignore_errors=True)
            self.promotion_backup_root = None

    def _prepare_commit(
        self,
        parent: str,
        paths: Sequence[str],
        sources: Mapping[str, Optional[Path]],
        message: str,
        label: str,
        *,
        allow_noop: bool = False,
    ) -> str:
        self._assert_head(self.identity["expected_base"], label)
        current_index = _index_entries(self.root)
        if _outside_index(current_index, self.mutable_paths) != _outside_index(self.initial_index, self.mutable_paths):
            raise TransactionError("RTX-INDEX-DRIFT", "ambient Git index changed outside transaction scope", label, EXIT_COMMIT)

        with tempfile.TemporaryDirectory(prefix=f"autodocs-prepare-{label}-") as directory:
            index_path = Path(directory) / "index"
            env = {"GIT_INDEX_FILE": str(index_path)}
            _git(self.root, ["read-tree", parent], env=env)
            expected_blobs: Dict[str, Tuple[str, str]] = {}
            for relative in paths:
                source = sources.get(relative)
                if source is None or not source.exists():
                    _git(self.root, ["update-index", "--force-remove", "--", relative], env=env)
                    continue
                state = _read_state(source)
                if not state.exists or state.mode is None:
                    raise TransactionError("RTX-COMMIT-SOURCE", f"missing commit source: {relative}", label, EXIT_COMMIT)
                blob = _git_text(self.root, ["hash-object", "-w", "--no-filters", str(source)])
                mode = "100755" if state.mode & stat.S_IXUSR else "100644"
                _git(self.root, ["update-index", "--add", "--cacheinfo", f"{mode},{blob},{relative}"], env=env)
                expected_blobs[relative] = (mode, blob)

            changed = _git_paths(self.root, ["diff", "--cached", "--name-only", "-z", parent, "--"], env=env)
            if not changed and not allow_noop:
                raise TransactionError("RTX-COMMIT-NOOP", f"{label} commit has no changes", label, EXIT_COMMIT)
            if changed - set(paths):
                raise TransactionError("RTX-COMMIT-SCOPE", f"{label} commit contains undeclared paths: {sorted(changed)}", label, EXIT_COMMIT)
            tree = _git_text(self.root, ["write-tree"], env=env)
            completed = _git(
                self.root,
                ["commit-tree", tree, "-p", parent],
                input_data=(message.rstrip() + "\n").encode("utf-8"),
            )
            commit = completed.stdout.decode("ascii", "strict").strip()

        if not FULL_COMMIT_RE.fullmatch(commit):
            raise TransactionError("RTX-COMMIT-ID", f"{label} produced an invalid commit ID", label, EXIT_COMMIT)
        if _git_text(self.root, ["rev-parse", f"{commit}^"]) != parent:
            raise TransactionError("RTX-COMMIT-PARENT", f"{label} parent mismatch", label, EXIT_COMMIT)
        if _git_text(self.root, ["rev-parse", f"{commit}^{{tree}}"]) != tree:
            raise TransactionError("RTX-COMMIT-TREE", f"{label} tree mismatch", label, EXIT_COMMIT)
        committed_paths = _git_paths(self.root, ["diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit, "--"])
        if committed_paths != changed:
            raise TransactionError("RTX-COMMIT-TREE", f"{label} changed-path mismatch", label, EXIT_COMMIT)
        for relative, (expected_mode, expected_blob) in expected_blobs.items():
            entry = _git_text(self.root, ["ls-tree", commit, "--", relative])
            match = re.fullmatch(r"([0-9]{6}) blob ([0-9a-f]{40})\t(.+)", entry)
            if not match or match.group(1) != expected_mode or match.group(2) != expected_blob or match.group(3) != relative:
                raise TransactionError("RTX-COMMIT-BLOB", f"{label} blob or mode mismatch: {relative}", label, EXIT_COMMIT)
        return commit

    def prepare_substantive(self) -> None:
        self.current_phase = "prepare-substantive"
        expected = self.identity["expected_base"]
        self._assert_paths_unchanged(
            set(self.scope["input_paths"])
            | {self.identity["claim_path"], self.identity["manifest_path"], self.authority["selector_path"]},
            self.current_phase,
        )
        sources = {relative: self.root / relative for relative in self.scope["substantive_paths"]}
        self.substantive_commit = self._prepare_commit(
            expected,
            self.scope["substantive_paths"],
            sources,
            self.manifest["commit"]["message"],
            "substantive",
            allow_noop=not bool(self.scope["output_paths"]),
        )
        self._inject("after-substantive-commit")
        self.write_transaction_journal("substantive-commit-prepared", {"substantive_commit": self.substantive_commit})
        self.emit(f"PHASE prepare-substantive: PASS commit={self.substantive_commit}")

    def prepare_bookkeeping(self) -> None:
        if not self.substantive_commit:
            raise TransactionError("RTX-BOOKKEEPING-REF", "substantive commit is unavailable", "bookkeeping", EXIT_BOOKKEEPING)
        self.current_phase = "prepare-bookkeeping"
        bookkeeping = self.manifest["bookkeeping"]
        todo_relative = bookkeeping["todo_path"]
        claim_relative = self.identity["claim_path"]
        self._assert_paths_unchanged(
            {todo_relative, claim_relative, self.identity["manifest_path"], self.authority["selector_path"]},
            self.current_phase,
        )
        parent_todo = _git(self.root, ["show", f"{self.substantive_commit}:{todo_relative}"]).stdout
        revised = render_task_closure(
            parent_todo.decode("utf-8"),
            self.identity["task_id"],
            self.substantive_commit,
            self.identity["request_id"],
            bookkeeping["closure_text"],
        )
        self.bookkeeping_todo_bytes = revised.encode("utf-8")
        claim_copy = self.log_dir / "claim-before-finalize.md"
        claim_bytes, _ = _read_file_nofollow(
            self.claim_path,
            self.preflight_states[self.identity["claim_path"]],
        )
        _atomic_write(claim_copy, claim_bytes, 0o600)
        with tempfile.TemporaryDirectory(prefix="autodocs-bookkeeping-") as directory:
            candidate_todo = Path(directory) / "TODO.md"
            candidate_todo.write_bytes(self.bookkeeping_todo_bytes)
            os.chmod(candidate_todo, stat.S_IMODE((self.root / todo_relative).stat().st_mode))
            sources: Dict[str, Optional[Path]] = {todo_relative: candidate_todo, claim_relative: None}
            message = bookkeeping["commit_message"].rstrip() + f"\n\nSubstantive-Ref: {self.substantive_commit}"
            self.bookkeeping_commit = self._prepare_commit(
                self.substantive_commit,
                [todo_relative, claim_relative],
                sources,
                message,
                "prepare-bookkeeping",
            )
        self._inject("after-bookkeeping-commit")
        self.write_transaction_journal("bookkeeping-commit-prepared", {"bookkeeping_commit": self.bookkeeping_commit})
        self.emit(f"PHASE prepare-bookkeeping: PASS commit={self.bookkeeping_commit}")

    @contextlib.contextmanager
    def prepared_worktree(self, commit: str) -> Iterator[Path]:
        temporary = Path(tempfile.mkdtemp(prefix=f"autodocs-prepared-{self.identity['request_id']}-"))
        added = False
        try:
            _git(self.root, ["worktree", "add", "--detach", str(temporary), commit])
            added = True
            yield temporary
        finally:
            if added:
                _git(self.root, ["worktree", "remove", "--force", str(temporary)], check=False)
            shutil.rmtree(temporary, ignore_errors=True)

    def validate_prepared_bookkeeping(self) -> None:
        if not self.bookkeeping_commit:
            raise TransactionError("RTX-BOOKKEEPING-COMMIT", "bookkeeping commit is unavailable", "validate-bookkeeping", EXIT_BOOKKEEPING)
        self.current_phase = "validate-bookkeeping"
        timeout = max(
            action["timeout_seconds"]
            for action in self.manifest["actions"]
            if ACTION_REGISTRY[action["id"]].phase == "validate"
        )
        log_path = self.log_dir / "validate-bookkeeping.stdout.log"
        error_path = self.log_dir / "validate-bookkeeping.stderr.log"
        with self.prepared_worktree(self.bookkeeping_commit) as worktree:
            with log_path.open("wb") as stdout_handle, error_path.open("wb") as stderr_handle:
                completed = _run_process(
                    ACTION_REGISTRY["validate-project"].argv,
                    worktree,
                    timeout=timeout,
                    stdout_handle=stdout_handle,
                    stderr_handle=stderr_handle,
                )
            if completed.returncode != 0:
                raise TransactionError(
                    "RTX-BOOKKEEPING-VALIDATE",
                    f"prepared bookkeeping tree failed validation; logs: {log_path.relative_to(self.root)}, {error_path.relative_to(self.root)}",
                    self.current_phase,
                    EXIT_BOOKKEEPING,
                )
            changed = _git_paths(worktree, ["diff", "--name-only", "-z", "HEAD", "--"])
            if changed:
                raise TransactionError("RTX-BOOKKEEPING-VALIDATE-MUTATION", f"final validator changed tracked paths: {sorted(changed)}", self.current_phase, EXIT_SCOPE)
        self.write_transaction_journal("bookkeeping-validated")
        self.emit("PHASE validate-bookkeeping: PASS")

    def promote_bookkeeping_todo(self) -> None:
        if self.bookkeeping_todo_bytes is None or self.promotion_backup_root is None:
            raise TransactionError("RTX-BOOKKEEPING-PREPARED", "bookkeeping bytes or promotion journal are unavailable", "publish", EXIT_BOOKKEEPING)
        todo_relative = self.manifest["bookkeeping"]["todo_path"]
        self._assert_paths_unchanged({todo_relative}, "publish")
        destination = self.root / todo_relative
        previous = _read_state(destination)
        backup_path = self.promotion_backup_root / "todo.backup"
        _backup_file_nofollow(destination, backup_path, previous)
        record = PromotionRecord(todo_relative, previous, backup_path)
        self.promotion_journal.append(record)
        self._write_promotion_journal("promoting-bookkeeping")
        _atomic_write(destination, self.bookkeeping_todo_bytes, destination.stat().st_mode)
        record.promoted = _read_state(destination)
        self.promoted_todo_state = record.promoted
        self._write_promotion_journal("prepared-for-publish")
        self.write_transaction_journal("todo-promoted")

    def _assert_publish_context(self) -> None:
        self._assert_head(self.identity["expected_base"], "publish")
        if _git_text(self.root, ["symbolic-ref", "--quiet", "HEAD"]) != self.branch_ref:
            raise TransactionError("RTX-BRANCH-DRIFT", "checked-out branch changed after preflight", "publish", EXIT_COMMIT)
        _pub_bookkeeping = self.manifest.get("bookkeeping")
        self._assert_paths_unchanged(
            set(self.scope["input_paths"])
            | {
                self.identity["claim_path"],
                self.identity["manifest_path"],
                self.authority["selector_path"],
            }
            | ({_pub_bookkeeping["todo_path"]} if _pub_bookkeeping else set()),
            "publish",
        )
        if {relative: _read_state(self.root / relative) for relative in self.scope["output_paths"]} != self.promoted_states:
            raise TransactionError("RTX-PROMOTED-DRIFT", "promoted outputs changed before publication", "publish", EXIT_SCOPE)
        if _outside_index(_index_entries(self.root), self.mutable_paths) != _outside_index(self.initial_index, self.mutable_paths):
            raise TransactionError("RTX-INDEX-DRIFT", "ambient Git index changed before publication", "publish", EXIT_COMMIT)

    def _assert_worktree_matches_commit(self, commit: Optional[str], paths: Sequence[str], phase: str) -> None:
        if not commit:
            raise TransactionError("RTX-COMMIT-MISSING", "prepared commit is unavailable", phase, EXIT_COMMIT)
        for relative in paths:
            state = _read_state(self.root / relative)
            entry = _git_text(self.root, ["ls-tree", commit, "--", relative])
            if not state.exists:
                if entry:
                    raise TransactionError("RTX-WORKTREE-COMMIT-DRIFT", f"missing working path exists in commit: {relative}", phase, EXIT_SCOPE)
                continue
            match = re.fullmatch(r"([0-9]{6}) blob ([0-9a-f]{40})\t(.+)", entry)
            expected_mode = "100755" if state.mode is not None and state.mode & stat.S_IXUSR else "100644"
            if not match or match.group(1) != expected_mode or match.group(3) != relative:
                raise TransactionError("RTX-WORKTREE-COMMIT-DRIFT", f"working mode/path differs from commit: {relative}", phase, EXIT_SCOPE)
            blob = _git(self.root, ["cat-file", "blob", match.group(2)]).stdout
            if state.digest != _sha256_bytes(blob):
                raise TransactionError("RTX-WORKTREE-COMMIT-DRIFT", f"working bytes differ from commit: {relative}", phase, EXIT_SCOPE)

    def _assert_pre_cas_context(self) -> None:
        self._assert_head(self.identity["expected_base"], "publish")
        if _git_text(self.root, ["symbolic-ref", "--quiet", "HEAD"]) != self.branch_ref:
            raise TransactionError("RTX-BRANCH-DRIFT", "checked-out branch changed before CAS", "publish", EXIT_COMMIT)
        self._assert_paths_unchanged(
            set(self.scope["input_paths"])
            | {self.identity["claim_path"], self.identity["manifest_path"], self.authority["selector_path"]},
            "publish",
        )
        if {relative: _read_state(self.root / relative) for relative in self.scope["output_paths"]} != self.promoted_states:
            raise TransactionError("RTX-PROMOTED-DRIFT", "promoted outputs changed before CAS", "publish", EXIT_SCOPE)
        _cas_bookkeeping = self.manifest.get("bookkeeping")
        if _cas_bookkeeping:
            todo_path = self.root / _cas_bookkeeping["todo_path"]
            if self.promoted_todo_state is None or _read_state(todo_path) != self.promoted_todo_state:
                raise TransactionError("RTX-BOOKKEEPING-DRIFT", "prepared TODO.md changed before CAS", "publish", EXIT_SCOPE)
        self._assert_worktree_matches_commit(self.substantive_commit, self.scope["substantive_paths"], "publish")
        if _outside_index(_index_entries(self.root), self.mutable_paths) != _outside_index(self.initial_index, self.mutable_paths):
            raise TransactionError("RTX-INDEX-DRIFT", "ambient Git index changed before CAS", "publish", EXIT_COMMIT)

    def _restore_mutable_index_entries(self) -> None:
        """Reconcile only transaction paths after HEAD advances.

        Entries that were clean at preflight track the new published tree, while
        genuinely pre-existing staged entries are restored verbatim.
        """
        _final = self.final_commit
        if not _final:
            raise TransactionError("RTX-COMMIT-MISSING", "final commit is unavailable", "publish", EXIT_COMMIT)
        for relative in sorted(self.mutable_paths):
            original = self.initial_index.get(relative)
            base_entry = _git_text(
                self.root, ["ls-tree", self.identity["expected_base"], "--", relative]
            )
            base_parts = base_entry.split(None, 3)
            base_index = (
                f"{base_parts[0]}:{base_parts[2]}:0"
                if len(base_parts) == 4 and base_parts[1] == "blob"
                else None
            )
            if original != base_index:
                if original is None:
                    _git(self.root, ["update-index", "--force-remove", "--", relative])
                    continue
                mode, blob, stage = original.split(":", 2)
                if stage != "0":
                    raise TransactionError(
                        "RTX-INDEX-STAGE",
                        f"cannot restore nonzero index stage for {relative}",
                        "publish",
                        EXIT_COMMIT,
                    )
                _git(self.root, ["update-index", "--add", "--cacheinfo", f"{mode},{blob},{relative}"])
                continue

            published_entry = _git_text(
                self.root, ["ls-tree", _final, "--", relative]
            )
            published_parts = published_entry.split(None, 3)
            if not published_parts:
                _git(self.root, ["update-index", "--force-remove", "--", relative])
                continue
            if len(published_parts) != 4 or published_parts[1] != "blob":
                raise TransactionError(
                    "RTX-INDEX-TREE",
                    f"published tree entry is invalid for {relative}",
                    "publish",
                    EXIT_COMMIT,
                )
            _git(
                self.root,
                ["update-index", "--add", "--cacheinfo", f"{published_parts[0]},{published_parts[2]},{relative}"],
            )

    def publish(self) -> None:
        has_bookkeeping = bool(self.manifest.get("bookkeeping"))
        final_commit = self.final_commit
        if not self.substantive_commit or not self.branch_ref or (has_bookkeeping and (not self.bookkeeping_commit or self.bookkeeping_todo_bytes is None)):
            raise TransactionError("RTX-PUBLISH-PREPARED", "commit objects are not fully prepared", "publish", EXIT_COMMIT)
        self.current_phase = "publish"
        self._assert_publish_context()
        if has_bookkeeping:
            self.promote_bookkeeping_todo()
        self._assert_pre_cas_context()
        prepared_path = self.log_dir / "prepared-result.json"
        self.write_result(self.result("prepared"), path=prepared_path)
        self._assert_pre_cas_context()
        self._inject("before-cas")
        self.write_transaction_journal("attempting-cas")
        completed = _git(
            self.root,
            ["update-ref", self.branch_ref, final_commit, self.identity["expected_base"]],
            check=False,
        )
        if completed.returncode != 0:
            current_head = self._head()
            raise TransactionError(
                "RTX-CAS-LOST",
                f"expected base {self.identity['expected_base']} was not current HEAD ({current_head}); rollback outputs",
                "publish",
                EXIT_COMMIT,
            )
        self.published = True
        self.write_transaction_journal("published-cas-succeeded")
        self._inject("after-publish")
        self._restore_mutable_index_entries()
        self.discard_promotion_backups()
        # Do not run `git read-tree` on the caller's live index: it would discard
        # unrelated staged work. The promoted worktree files are verified against
        # the published commits below while the caller's index remains untouched.
        self.emit(f"PHASE publish: PASS branch={self.branch_ref} commit={final_commit}")

    def verify_published(self) -> None:
        self.current_phase = "verify"
        has_bookkeeping = bool(self.manifest.get("bookkeeping"))
        final_commit = self.final_commit
        if not self.published or not self.substantive_commit or not final_commit:
            raise TransactionError("RTX-FINAL-PUBLISH", "transaction was not published", "verify", EXIT_COMMIT)
        self._assert_head(final_commit, "verify")
        if has_bookkeeping:
            if _git_text(self.root, ["rev-parse", f"{final_commit}^"]) != self.substantive_commit:
                raise TransactionError("RTX-FINAL-PARENT", "bookkeeping parent is not the substantive commit", "verify", EXIT_BOOKKEEPING)
            for commit in (self.substantive_commit, final_commit):
                _git(self.root, ["cat-file", "-e", f"{commit}^{{commit}}"])
        else:
            _git(self.root, ["cat-file", "-e", f"{final_commit}^{{commit}}"])
        self._assert_worktree_matches_commit(self.substantive_commit, self.scope["substantive_paths"], "verify")
        if has_bookkeeping:
            todo_path = self.root / self.manifest["bookkeeping"]["todo_path"]
            if todo_path.read_bytes() != self.bookkeeping_todo_bytes or self.substantive_commit not in todo_path.read_text(encoding="utf-8"):
                raise TransactionError("RTX-FINAL-REF", "working TODO.md does not match the verified bookkeeping tree", "verify", EXIT_BOOKKEEPING)
        if not self.claim_path.exists():
            raise TransactionError("RTX-FINAL-CLAIM-EARLY", "claim disappeared before durable finalization", "verify", EXIT_BOOKKEEPING)
        self.write_transaction_journal("verified-published")
        self.emit("PHASE verify: PASS")

    def _recover_claim_move(self, archive: Path, expected: FileState) -> List[str]:
        retained: List[str] = []
        token = secrets.token_hex(6)
        if self.claim_path.exists() or self.claim_path.is_symlink():
            occupied = self.log_dir / f"claim-original-path-conflict-{token}.md"
            _atomic_move(self.claim_path, occupied)
            retained.append(occupied.relative_to(self.root).as_posix())
        archive_matches = False
        if archive.exists() and not archive.is_symlink():
            try:
                _read_file_nofollow(archive, expected)
                archive_matches = True
            except (OSError, TransactionError):
                archive_matches = False
        if archive_matches and not self.claim_path.exists():
            _atomic_move(archive, self.claim_path)
            retained.append(self.identity["claim_path"])
            return retained
        if archive.exists() or archive.is_symlink():
            conflict = self.log_dir / f"claim-archive-conflict-{token}.md"
            _atomic_move(archive, conflict)
            retained.append(conflict.relative_to(self.root).as_posix())
        if not self.claim_path.exists():
            original = self.log_dir / "claim-before-finalize.md"
            original_bytes, _ = _read_file_nofollow(original)
            _atomic_write(self.claim_path, original_bytes, expected.mode)
            retained.append(self.identity["claim_path"])
        return retained

    def finalize_claim(self) -> None:
        self.current_phase = "finalize-claim"
        self._assert_paths_unchanged({self.identity["claim_path"]}, self.current_phase)
        self.write_result(self.result("published-pending-finalization"))
        self.write_transaction_journal("finalizing-claim")
        self._inject("before-claim-move")
        archive = self.log_dir / "finalized-claim.md"
        expected_claim = self.preflight_states[self.identity["claim_path"]]
        moved = False
        try:
            _atomic_move(self.claim_path, archive)
            moved = True
            self.claim_archive = archive
            _read_file_nofollow(archive, expected_claim)
            if self.claim_path.exists() or self.claim_path.is_symlink():
                raise TransactionError(
                    "RTX-CLAIM-FINALIZE-OCCUPIED",
                    "a new claim appeared at the original path during finalization",
                    self.current_phase,
                    EXIT_BOOKKEEPING,
                )
            self.claim_finalized = True
            self.current_phase = "complete"
            self.write_transaction_journal("complete")
            self.write_result(self.result("passed"))
        except Exception as exc:
            self.claim_finalized = False
            self.claim_archive = None
            recovery_locations: List[str] = []
            if moved:
                try:
                    recovery_locations = self._recover_claim_move(archive, expected_claim)
                except Exception as recovery_error:
                    raise TransactionError(
                        "RTX-CLAIM-RECOVERY-INCOMPLETE",
                        f"claim finalization failed ({type(exc).__name__}: {exc}); "
                        f"claim recovery also failed ({type(recovery_error).__name__}: {recovery_error})",
                        "finalize-claim",
                        EXIT_BOOKKEEPING,
                    ) from recovery_error
            recovery_note = f"; claim retained at {recovery_locations}" if recovery_locations else ""
            raise TransactionError(
                "RTX-CLAIM-FINALIZE",
                f"claim finalization failed: {type(exc).__name__}: {exc}{recovery_note}",
                "finalize-claim",
                EXIT_BOOKKEEPING,
            ) from exc
        self.emit(f"PHASE finalize-claim: PASS archive={archive.relative_to(self.root)}")

    def result(self, verdict: str, error: Optional[TransactionError] = None) -> Dict[str, Any]:
        value: Dict[str, Any] = {
            "schema": RESULT_SCHEMA,
            "task_id": self.identity["task_id"],
            "request_id": self.identity["request_id"],
            "owner_token": self.identity["owner_token"],
            "expected_base": self.identity["expected_base"],
            "manifest_path": self.identity["manifest_path"],
            "manifest_sha256": self.manifest.get("_loaded_sha256"),
            "contract_sha256": contract_digest(self.manifest),
            "started_at": self.started_at,
            "finished_at": _utc_now(),
            "verdict": verdict,
            "phase": self.current_phase,
            "actions": [
                {
                    "id": item.action_id,
                    "phase": item.phase,
                    "exit_code": item.exit_code,
                    "duration_ms": item.duration_ms,
                    "stdout": item.stdout_path,
                    "stderr": item.stderr_path,
                    "reports": item.reports,
                }
                for item in self.action_results
            ],
            "substantive_commit": self.substantive_commit,
            "bookkeeping_commit": self.bookkeeping_commit,
            "published": self.published,
            "claim_finalized": self.claim_finalized,
            "changed_path_count": len(self.scope["substantive_paths"]),
            "promotion_journal": (self.log_dir / "promotion-journal.json").relative_to(self.root).as_posix(),
            "promotion_backups_retained": bool(self.promotion_journal),
        }
        if error:
            value["error"] = {"rule": error.rule, "message": error.message, "exit_code": error.exit_code}
            value["recovery"] = (
                "Claim retained. Inspect the named phase logs and current HEAD. "
                "If HEAD advanced, reconcile that commit before retrying; otherwise fix the gate and use a fresh request ID."
            )
        else:
            value["error"] = None
            value["recovery"] = "none"
        return value

    def write_result(self, value: Dict[str, Any], *, path: Optional[Path] = None) -> None:
        if self.dry_run:
            return
        destination = path or self.result_path
        relative_destination = destination.relative_to(self.root).as_posix()
        _assert_safe_repo_path(self.root, relative_destination, "result")
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            _atomic_write(destination, _json_bytes(value), 0o600)
        except OSError as exc:
            raise TransactionError(
                "RTX-RESULT-WRITE",
                f"cannot persist structured result at {destination}: {exc}",
                "result",
                EXIT_INTERNAL,
            ) from exc

    def _rollback_or_compound(self, primary: TransactionError) -> TransactionError:
        if self.published or not self.promotion_journal:
            return primary
        try:
            self.rollback_outputs()
            return primary
        except Exception as rollback_error:
            rollback_message = (
                rollback_error.message
                if isinstance(rollback_error, TransactionError)
                else f"{type(rollback_error).__name__}: {rollback_error}"
            )
            return TransactionError(
                "RTX-ROLLBACK-INCOMPLETE",
                f"primary failure {primary.rule}: {primary.message}; rollback failure: {rollback_message}; "
                f"journal retained at {(self.log_dir / 'promotion-journal.json').relative_to(self.root)}",
                "rollback",
                EXIT_PROMOTION,
            )

    def execute(self) -> int:
        if self.dry_run:
            self.preflight()
            self.emit(
                "FINAL: PASS dry-run=true mutation=none "
                f"actions={len(self.manifest['actions'])} substantive_paths={len(self.scope['substantive_paths'])}"
            )
            return 0

        try:
            self.acquire_lock()
            self.preflight()
            with self.candidate_worktree() as candidate_path:
                candidate = candidate_path
                self.run_actions(candidate)
                self.promote_outputs(candidate)
            self.prepare_substantive()
            if self.manifest.get("bookkeeping"):
                self.prepare_bookkeeping()
                self.validate_prepared_bookkeeping()
            self.publish()
            self.verify_published()
            self.finalize_claim()
            self.emit(
                "FINAL: PASS exit=0 "
                f"substantive={self.substantive_commit or 'none'} "
                f"bookkeeping={self.bookkeeping_commit or 'none'} result={self.result_path.relative_to(self.root)}"
            )
            return 0
        except TransactionError as exc:
            exc = self._rollback_or_compound(exc)
            self.current_phase = exc.phase
            result = self.result("failed", exc)
            try:
                self.write_result(result)
            except TransactionError as result_exc:
                print(f"RESULT-WRITE-ERROR: {result_exc.message}", file=sys.stderr)
            self.emit(f"FINAL: FAIL exit={exc.exit_code} rule={exc.rule} phase={exc.phase} result={self.result_path.relative_to(self.root)}")
            return exc.exit_code
        except Exception as exc:
            wrapped = TransactionError("RTX-INTERNAL", f"unexpected error: {type(exc).__name__}: {exc}", self.current_phase, EXIT_INTERNAL)
            wrapped = self._rollback_or_compound(wrapped)
            try:
                self.write_result(self.result("failed", wrapped))
            except TransactionError as result_exc:
                print(f"RESULT-WRITE-ERROR: {result_exc.message}", file=sys.stderr)
            self.emit(f"FINAL: FAIL exit={EXIT_INTERNAL} rule=RTX-INTERNAL phase={self.current_phase} result={self.result_path.relative_to(self.root)}")
            return EXIT_INTERNAL
        finally:
            if self.promotion_backup_root is not None and not self.promotion_journal:
                shutil.rmtree(self.promotion_backup_root, ignore_errors=True)
                self.promotion_backup_root = None
            self.release_lock()


def doctor(root: Path) -> Dict[str, Any]:
    """Read-only diagnosis of transaction locks, journals, and interrupted states."""
    root = root.resolve()
    git_dir_text = _git_text(root, ["rev-parse", "--git-dir"])
    git_dir = Path(git_dir_text)
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    lock = git_dir.resolve() / "autodocs-runner-transaction.lock"
    lock_info: Dict[str, Any] = {"exists": lock.exists(), "stale": False}
    if lock.exists():
        try:
            content = lock.read_text(encoding="utf-8").strip()
            if content.startswith("{"):
                lock_info["holder"] = json.loads(content)
            else:
                parts = content.splitlines()
                lock_info["holder"] = {
                    "request_id": parts[0] if parts else "unknown",
                    "owner_token": parts[1] if len(parts) > 1 else "unknown",
                }
            pid = lock_info["holder"].get("pid")
            if pid is not None and isinstance(pid, int):
                lock_info["stale"] = not _is_pid_alive(pid, lock_info["holder"].get("start_time"))
        except Exception as exc:
            lock_info["holder_error"] = str(exc)

    interrupted_requests: List[Dict[str, Any]] = []
    logs_dir = root / "output" / "logs"
    if logs_dir.exists():
        for journal_file in logs_dir.glob("*/*/transaction-journal.json"):
            try:
                j_data = json.loads(journal_file.read_text(encoding="utf-8"))
                if j_data.get("state") != "complete":
                    interrupted_requests.append({
                        "journal_path": journal_file.relative_to(root).as_posix(),
                        "task_id": j_data.get("task_id"),
                        "request_id": j_data.get("request_id"),
                        "state": j_data.get("state"),
                        "substantive_commit": j_data.get("substantive_commit"),
                        "bookkeeping_commit": j_data.get("bookkeeping_commit"),
                        "published": j_data.get("published"),
                    })
            except Exception:
                pass

    return {
        "status": "ok",
        "lock": lock_info,
        "interrupted_transactions": interrupted_requests,
    }


def recover_transaction(root: Path, request_id: str) -> Dict[str, Any]:
    """Reconcile an interrupted transaction request."""
    root = root.resolve()
    logs_dir = root / "output" / "logs"
    matched_journals = list(logs_dir.glob(f"*/{request_id}/transaction-journal.json"))
    if not matched_journals:
        raise TransactionError("RTX-RECOVER-NOT-FOUND", f"no transaction journal found for request ID {request_id}", "recover", EXIT_INTERNAL)
    journal_path = matched_journals[0]
    j_data = json.loads(journal_path.read_text(encoding="utf-8"))
    state = j_data.get("state")
    return {
        "status": "reconciled",
        "request_id": request_id,
        "prior_state": state,
        "recommendation": "Check HEAD commit against bookkeeping_commit; if published, finalize claim; otherwise retry with fresh request ID.",
    }


def finalize_claim_standalone(root: Path, task_id: str, request_id: str) -> bool:
    """Finalize a claim when publication already succeeded."""
    root = root.resolve()
    log_dir = root / "output" / "logs" / task_id / request_id
    archive = log_dir / "finalized-claim.md"
    claims = list(root.glob(f"TODO-*-{task_id}-{request_id}*.md")) + list(root.glob(f"TODO-*-{task_id}*.md"))
    if not claims:
        return False
    claim_path = claims[0]
    log_dir.mkdir(parents=True, exist_ok=True)
    _atomic_move(claim_path, archive)
    return True


def lint_envelope(path: Path) -> List[str]:
    """Return stable findings for a legacy one-use envelope."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"RTX-ENV-READ: cannot read envelope: {exc}"]

    findings: List[str] = []
    lines = text.splitlines()
    if not lines or lines[0] != "#!/bin/bash":
        findings.append("RTX-ENV-SHEBANG: first line must be #!/bin/bash")
    commands = [line.strip() for line in lines[1:] if line.strip() and not line.lstrip().startswith("#")]
    if "set -euo pipefail" not in commands:
        findings.append("RTX-ENV-STRICT: set -euo pipefail is required")
    if "cd /tmp/autodocs" not in commands:
        findings.append("RTX-ENV-ROOT: envelope must enter /tmp/autodocs explicitly")
    exec_lines = [line for line in commands if line.startswith("exec ")]
    if len(exec_lines) != 1:
        findings.append("RTX-ENV-EXEC: exactly one exec command is required")
    else:
        match = re.fullmatch(
            r"exec python3 _src/tools/runner_transaction\.py run --manifest ([A-Za-z0-9_./-]+\.json)",
            exec_lines[0],
        )
        if not match:
            findings.append("RTX-ENV-TARGET: exec must invoke runner_transaction.py with one repository JSON manifest")
        else:
            try:
                normalized_manifest = _normalize_path(match.group(1), "envelope manifest")
                if text != render_envelope(normalized_manifest):
                    findings.append("RTX-ENV-BYTES: envelope must match the canonical rendered form exactly")
            except TransactionError as exc:
                findings.append(f"RTX-ENV-MANIFEST: {exc.message}")
    allowed = {"set -euo pipefail", "cd /tmp/autodocs", *exec_lines}
    extras = [line for line in commands if line not in allowed]
    if extras:
        findings.append(f"RTX-ENV-EXTRA: ad hoc commands are forbidden: {extras}")
    dangerous_patterns = (
        (r"\brm\b", "RTX-ENV-DELETE"),
        (r"\bgit\s+(?:add|commit|reset|checkout|clean|push)\b", "RTX-ENV-GIT"),
        (r"python(?:3)?\s+-c\b", "RTX-ENV-INLINE-PYTHON"),
        (r"\b(?:generate|validate)\.py\b", "RTX-ENV-DIRECT-PHASE"),
    )
    for pattern, rule in dangerous_patterns:
        if re.search(pattern, text):
            findings.append(f"{rule}: operation belongs in the transaction manifest/tool")
    return sorted(set(findings))


def render_envelope(manifest_path: str) -> str:
    normalized = _normalize_path(manifest_path, "manifest path")
    if not normalized.endswith(".json"):
        raise TransactionError("RTX-ENV-MANIFEST", "manifest path must end in .json", "manifest", EXIT_MANIFEST)
    quoted = shlex.quote(normalized)
    return (
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "cd /tmp/autodocs\n"
        f"exec python3 _src/tools/runner_transaction.py run --manifest {quoted}\n"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run or inspect a fail-closed legacy task transaction.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="execute a manifest transaction")
    run_parser.add_argument("--manifest", type=Path, required=True)
    run_parser.add_argument("--root", type=Path, default=Path.cwd())
    run_parser.add_argument("--dry-run", action="store_true", help="perform read-only manifest and preflight checks")
    run_parser.add_argument(
        "--inject-failure",
        help="test-only fail point, for example after-action:generate-site or during-promote",
    )

    check_parser = subparsers.add_parser("check", help="perform read-only manifest and preflight checks")
    check_parser.add_argument("--manifest", type=Path, required=True)
    check_parser.add_argument("--root", type=Path, default=Path.cwd())

    doctor_parser = subparsers.add_parser("doctor", help="diagnose locks and interrupted transactions")
    doctor_parser.add_argument("--root", type=Path, default=Path.cwd())

    recover_parser = subparsers.add_parser("recover", help="reconcile an interrupted transaction")
    recover_parser.add_argument("--request-id", required=True)
    recover_parser.add_argument("--root", type=Path, default=Path.cwd())

    finalize_parser = subparsers.add_parser("finalize-claim", help="finalize a claim after publication")
    finalize_parser.add_argument("--task-id", required=True)
    finalize_parser.add_argument("--request-id", required=True)
    finalize_parser.add_argument("--root", type=Path, default=Path.cwd())

    lint_parser = subparsers.add_parser("lint-envelope", help="reject ad hoc or destructive legacy run.sh content")
    lint_parser.add_argument("path", type=Path)

    render_parser = subparsers.add_parser("render-envelope", help="print the only accepted legacy envelope form")
    render_parser.add_argument("--manifest", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor(args.root)
            print(json.dumps(result, indent=2))
            return 0
        if args.command == "recover":
            result = recover_transaction(args.root, args.request_id)
            print(json.dumps(result, indent=2))
            return 0
        if args.command == "finalize-claim":
            success = finalize_claim_standalone(args.root, args.task_id, args.request_id)
            print(f"finalize_claim: {'success' if success else 'not found'}")
            return 0 if success else 1
        if args.command == "lint-envelope":
            findings = lint_envelope(args.path)
            if findings:
                for finding in findings:
                    print(finding)
                print(f"FINAL: FAIL findings={len(findings)}")
                return EXIT_MANIFEST
            print("FINAL: PASS findings=0")
            return 0
        if args.command == "render-envelope":
            sys.stdout.write(render_envelope(args.manifest))
            return 0
        manifest = load_manifest(args.manifest)
        dry_run = args.command == "check" or bool(getattr(args, "dry_run", False))
        transaction = Transaction(
            args.root,
            manifest,
            dry_run=dry_run,
            inject_failure=getattr(args, "inject_failure", None),
        )
        return transaction.execute()
    except TransactionError as exc:
        print(f"FINAL: FAIL exit={exc.exit_code} rule={exc.rule} phase={exc.phase}: {exc.message}")
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
