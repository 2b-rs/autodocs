#!/usr/bin/env python3
"""Fail-closed legacy runner transaction coordinator.

This is a narrow safety adapter for the pre-Feature-0037 singleton runner.  It
turns the repeated generate/validate/commit/bookkeeping sequence into one
versioned, testable transaction.  It is deliberately *not* a generic command
runner: manifests select fixed action IDs, never shell strings or executables.

The permanent typed request queue remains owned by Feature 0037.  This helper
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
ALLOWED_AUTHORITY_KEYS = ("authority_epoch", "authority_profile", "write_phase", "runner_protocol")
TASK_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,127}$")
OWNER_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{7,255}$")
SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./-]*$")
PROFILE = "close-task-v1"
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


# Fixed action IDs are intentional.  Extending this registry requires a code
# review and tests; a manifest cannot smuggle in an executable or shell text.
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
    }


ACTION_REGISTRY = _registered_actions()


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _open_directory_nofollow(path: Path) -> int:
    """Open an absolute directory one component at a time without symlinks."""

    absolute = path.absolute()
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(os.sep, flags)
    try:
        for part in absolute.parts[1:]:
            next_descriptor = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


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
            f"symlink paths are not supported: {path}",
            "preflight",
            EXIT_PREFLIGHT,
        )
    if not path.is_file():
        raise TransactionError(
            "RTX-PATH-NOT-FILE",
            f"v1 requires exact file paths, not directories or special files: {path}",
            "preflight",
            EXIT_PREFLIGHT,
        )
    payload = path.read_bytes()
    metadata = path.stat()
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
        "mode": stat.S_IMODE(state.mode) if state.mode is not None else None,
        "size": state.size,
        "device": state.device,
        "inode": state.inode,
    }


def _normalize_path(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise TransactionError("RTX-MANIFEST-PATH", f"{field} must contain non-empty strings", "manifest", EXIT_MANIFEST)
    if not SAFE_PATH_RE.fullmatch(raw) or raw.startswith(("-", ":")):
        raise TransactionError("RTX-MANIFEST-PATH", f"unsafe path in {field}: {raw!r}", "manifest", EXIT_MANIFEST)
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts or candidate == Path("."):
        raise TransactionError("RTX-MANIFEST-PATH", f"path must be repository-relative: {raw!r}", "manifest", EXIT_MANIFEST)
    normalized = candidate.as_posix()
    if normalized != raw or normalized.casefold() == ".git" or normalized.casefold().startswith(".git/"):
        raise TransactionError("RTX-MANIFEST-PATH", f"path is not canonical or addresses Git metadata: {raw!r}", "manifest", EXIT_MANIFEST)
    return normalized


def _exact_keys(value: Mapping[str, Any], required: Set[str], optional: Set[str], field: str) -> None:
    keys = set(value)
    missing = required - keys
    unknown = keys - required - optional
    if missing:
        raise TransactionError("RTX-MANIFEST-MISSING", f"{field} is missing keys: {sorted(missing)}", "manifest", EXIT_MANIFEST)
    if unknown:
        raise TransactionError("RTX-MANIFEST-UNKNOWN", f"{field} has unknown keys: {sorted(unknown)}", "manifest", EXIT_MANIFEST)


def _string_list(value: Any, field: str, allow_empty: bool = False) -> List[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise TransactionError("RTX-MANIFEST-LIST", f"{field} must be a {'possibly empty' if allow_empty else 'non-empty'} list", "manifest", EXIT_MANIFEST)
    normalized = [_normalize_path(item, field) for item in value]
    if len(normalized) != len(set(normalized)):
        raise TransactionError("RTX-MANIFEST-DUPLICATE", f"{field} contains duplicate paths", "manifest", EXIT_MANIFEST)
    return normalized


def load_manifest(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TransactionError("RTX-MANIFEST-JSON", f"cannot read manifest {path}: {exc}", "manifest", EXIT_MANIFEST) from exc
    if not isinstance(data, dict):
        raise TransactionError("RTX-MANIFEST-TYPE", "manifest root must be an object", "manifest", EXIT_MANIFEST)
    _exact_keys(
        data,
        required={"schema", "profile", "identity", "authority", "scope", "actions", "commit", "bookkeeping"},
        optional=set(),
        field="manifest",
    )
    if data["schema"] != MANIFEST_SCHEMA:
        raise TransactionError("RTX-MANIFEST-SCHEMA", f"unsupported schema: {data['schema']!r}", "manifest", EXIT_MANIFEST)
    if data["profile"] != PROFILE:
        raise TransactionError("RTX-MANIFEST-PROFILE", f"unsupported transaction profile: {data['profile']!r}", "manifest", EXIT_MANIFEST)

    identity = data["identity"]
    if not isinstance(identity, dict):
        raise TransactionError("RTX-MANIFEST-TYPE", "identity must be an object", "manifest", EXIT_MANIFEST)
    _exact_keys(
        identity,
        {"task_id", "request_id", "owner_token", "claim_path", "manifest_path", "expected_base"},
        set(),
        "identity",
    )
    if not TASK_ID_RE.fullmatch(str(identity["task_id"])):
        raise TransactionError("RTX-IDENTITY-TASK", "identity.task_id is not a Task ID", "manifest", EXIT_MANIFEST)
    if not REQUEST_ID_RE.fullmatch(str(identity["request_id"])):
        raise TransactionError("RTX-IDENTITY-REQUEST", "identity.request_id is invalid", "manifest", EXIT_MANIFEST)
    if not OWNER_TOKEN_RE.fullmatch(str(identity["owner_token"])):
        raise TransactionError("RTX-IDENTITY-OWNER", "identity.owner_token is invalid", "manifest", EXIT_MANIFEST)
    if not FULL_COMMIT_RE.fullmatch(str(identity["expected_base"])):
        raise TransactionError("RTX-IDENTITY-BASE", "identity.expected_base must be a full lowercase commit ID", "manifest", EXIT_MANIFEST)
    identity["claim_path"] = _normalize_path(identity["claim_path"], "identity.claim_path")
    identity["manifest_path"] = _normalize_path(identity["manifest_path"], "identity.manifest_path")

    authority = data["authority"]
    if not isinstance(authority, dict):
        raise TransactionError("RTX-MANIFEST-TYPE", "authority must be an object", "manifest", EXIT_MANIFEST)
    _exact_keys(authority, {"selector_path", *ALLOWED_AUTHORITY_KEYS}, set(), "authority")
    authority["selector_path"] = _normalize_path(authority["selector_path"], "authority.selector_path")
    for key in ALLOWED_AUTHORITY_KEYS:
        if not isinstance(authority[key], str) or not authority[key]:
            raise TransactionError("RTX-AUTHORITY-VALUE", f"authority.{key} must be a non-empty string", "manifest", EXIT_MANIFEST)

    scope = data["scope"]
    if not isinstance(scope, dict):
        raise TransactionError("RTX-MANIFEST-TYPE", "scope must be an object", "manifest", EXIT_MANIFEST)
    _exact_keys(scope, {"read_paths", "input_paths", "output_paths", "substantive_paths"}, set(), "scope")
    for key in ("read_paths", "input_paths", "output_paths", "substantive_paths"):
        scope[key] = _string_list(scope[key], f"scope.{key}", allow_empty=(key in {"read_paths", "output_paths"}))
    inputs = set(scope["input_paths"])
    outputs = set(scope["output_paths"])
    substantive = set(scope["substantive_paths"])
    if not outputs:
        raise TransactionError("RTX-SCOPE-OUTPUT", "close-task-v1 requires at least one generated output path", "manifest", EXIT_MANIFEST)
    if inputs & outputs:
        raise TransactionError("RTX-SCOPE-OVERLAP", "input_paths and output_paths must be disjoint", "manifest", EXIT_MANIFEST)
    if substantive != inputs | outputs:
        raise TransactionError(
            "RTX-SCOPE-SUBSTANTIVE",
            "substantive_paths must equal the exact union of input_paths and output_paths",
            "manifest",
            EXIT_MANIFEST,
        )
    if identity["claim_path"] in substantive:
        raise TransactionError("RTX-SCOPE-CLAIM", "the active claim cannot be a substantive path", "manifest", EXIT_MANIFEST)
    claim_name = Path(identity["claim_path"])
    if (
        claim_name.parent != Path(".")
        or not claim_name.name.startswith("TODO-")
        or not claim_name.name.endswith(".md")
        or identity["task_id"] not in claim_name.name
        or identity["request_id"] not in claim_name.name
    ):
        raise TransactionError(
            "RTX-CLAIM-PATH",
            "claim_path must be a top-level TODO-*.md name containing the exact Task and request IDs",
            "manifest",
            EXIT_MANIFEST,
        )

    actions = data["actions"]
    if not isinstance(actions, list) or not actions:
        raise TransactionError("RTX-ACTION-LIST", "actions must be a non-empty list", "manifest", EXIT_MANIFEST)
    prior_order = -1
    saw_generate = False
    saw_validate = False
    normalized_actions: List[Dict[str, Any]] = []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise TransactionError("RTX-ACTION-TYPE", f"actions[{index}] must be an object", "manifest", EXIT_MANIFEST)
        _exact_keys(action, {"id"}, {"timeout_seconds", "reports"}, f"actions[{index}]")
        action_id = action["id"]
        if action_id not in ACTION_REGISTRY:
            raise TransactionError("RTX-ACTION-UNKNOWN", f"unknown action ID: {action_id!r}", "manifest", EXIT_MANIFEST)
        registered = ACTION_REGISTRY[action_id]
        order = PHASE_ORDER[registered.phase]
        if order < prior_order:
            raise TransactionError("RTX-ACTION-ORDER", "generate actions cannot follow validation actions", "manifest", EXIT_MANIFEST)
        prior_order = order
        saw_generate = saw_generate or registered.phase == "generate"
        saw_validate = saw_validate or registered.phase == "validate"
        timeout = action.get("timeout_seconds", 900)
        if not isinstance(timeout, int) or timeout < 1 or timeout > 7200:
            raise TransactionError("RTX-ACTION-TIMEOUT", f"invalid timeout for action {action_id}", "manifest", EXIT_MANIFEST)
        reports = _string_list(action.get("reports", []), f"actions[{index}].reports", allow_empty=True)
        normalized_actions.append({"id": action_id, "timeout_seconds": timeout, "reports": reports})
    if not saw_generate or not saw_validate:
        raise TransactionError("RTX-ACTION-PROFILE", "close-task-v1 requires generation followed by validation", "manifest", EXIT_MANIFEST)
    data["actions"] = normalized_actions

    commit = data["commit"]
    if not isinstance(commit, dict):
        raise TransactionError("RTX-MANIFEST-TYPE", "commit must be an object", "manifest", EXIT_MANIFEST)
    _exact_keys(commit, {"substantive_message"}, set(), "commit")
    message = commit["substantive_message"]
    provenance_marker = "User-Prompt-Provenance:"
    if (
        not isinstance(message, str)
        or provenance_marker not in message
        or not message.split(provenance_marker, 1)[1].strip()
    ):
        raise TransactionError(
            "RTX-COMMIT-PROVENANCE",
            "commit.substantive_message must include a non-empty User-Prompt-Provenance section",
            "manifest",
            EXIT_MANIFEST,
        )

    bookkeeping = data["bookkeeping"]
    if not isinstance(bookkeeping, dict):
        raise TransactionError("RTX-MANIFEST-TYPE", "bookkeeping must be an object", "manifest", EXIT_MANIFEST)
    _exact_keys(bookkeeping, {"todo_path", "closure_text", "commit_message"}, set(), "bookkeeping")
    bookkeeping["todo_path"] = _normalize_path(bookkeeping["todo_path"], "bookkeeping.todo_path")
    for key in ("closure_text", "commit_message"):
        if not isinstance(bookkeeping[key], str) or not bookkeeping[key].strip() or "\n" in bookkeeping[key]:
            raise TransactionError("RTX-BOOKKEEPING-VALUE", f"bookkeeping.{key} must be a non-empty single line", "manifest", EXIT_MANIFEST)
    role_paths = {
        bookkeeping["todo_path"],
        identity["claim_path"],
        identity["manifest_path"],
        authority["selector_path"],
    }
    if len(role_paths) != 4 or role_paths & substantive:
        raise TransactionError(
            "RTX-SCOPE-ROLE-ALIAS",
            "TODO, claim, manifest, selector, and substantive paths must be pairwise disjoint",
            "manifest",
            EXIT_MANIFEST,
        )
    data["_loaded_path"] = str(path.resolve())
    data["_loaded_sha256"] = _sha256_bytes(raw.encode("utf-8"))
    return data


def contract_digest(manifest: Mapping[str, Any]) -> str:
    """Digest the complete normalized execution contract for claim binding."""

    payload = {
        "schema": manifest["schema"],
        "profile": manifest["profile"],
        "identity": manifest["identity"],
        "authority": manifest["authority"],
        "scope": manifest["scope"],
        "actions": manifest["actions"],
        "commit": manifest["commit"],
        "bookkeeping": manifest["bookkeeping"],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(canonical)


def claim_contract_fields(manifest: Mapping[str, Any]) -> Dict[str, str]:
    read_paths = sorted(
        set(manifest["scope"]["read_paths"])
        | set(manifest["scope"]["input_paths"])
        | {manifest["authority"]["selector_path"], manifest["identity"]["manifest_path"]}
    )
    write_paths = sorted(
        set(manifest["scope"]["substantive_paths"])
        | {manifest["bookkeeping"]["todo_path"], manifest["identity"]["claim_path"]}
    )
    compact = lambda value: json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "transaction_manifest": manifest["identity"]["manifest_path"],
        "transaction_actions_json": compact(manifest["actions"]),
        "transaction_authority_json": compact(manifest["authority"]),
        "transaction_commit_message_json": compact(manifest["commit"]["substantive_message"]),
        "transaction_bookkeeping_json": compact(manifest["bookkeeping"]),
        "transaction_read_paths_json": compact(read_paths),
        "transaction_write_paths_json": compact(write_paths),
    }


def _assert_safe_repo_path(root: Path, relative: str, phase: str = "preflight") -> None:
    """Reject symlink ancestors and ensure a lexical path stays below root."""

    root = root.resolve()
    current = root
    parts = Path(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            raise TransactionError("RTX-PATH-SYMLINK", f"symlink component is forbidden: {relative}", phase, EXIT_PREFLIGHT)
        if current.exists() and index < len(parts) - 1 and not current.is_dir():
            raise TransactionError("RTX-PATH-ANCESTOR", f"non-directory path ancestor: {relative}", phase, EXIT_PREFLIGHT)
    parent = current.parent.resolve()
    try:
        parent.relative_to(root)
    except ValueError as exc:
        raise TransactionError("RTX-PATH-ESCAPE", f"path escapes repository root: {relative}", phase, EXIT_PREFLIGHT) from exc


def _run_process(
    argv: Sequence[str],
    cwd: Path,
    *,
    env: Optional[Mapping[str, str]] = None,
    timeout: Optional[int] = None,
    stdout: Any = subprocess.PIPE,
    stderr: Any = subprocess.PIPE,
    check: bool = False,
    input_data: Optional[bytes] = None,
    replace_env: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    process_env = dict(env or {}) if replace_env else os.environ.copy()
    if env and not replace_env:
        process_env.update(env)
    try:
        completed = subprocess.run(
            list(argv),
            cwd=str(cwd),
            env=process_env,
            timeout=timeout,
            input=input_data,
            stdin=None if input_data is not None else subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TransactionError("RTX-PROCESS-TIMEOUT", f"process timed out: {argv[0]}", "action", EXIT_ACTION) from exc
    if check and completed.returncode != 0:
        stderr_value = completed.stderr.decode("utf-8", "replace") if isinstance(completed.stderr, bytes) else str(completed.stderr or "")
        excerpt = "\n".join(stderr_value.splitlines()[-10:])[:4096]
        raise TransactionError(
            "RTX-PROCESS-NONZERO",
            f"process failed ({completed.returncode}): {' '.join(argv)}\n{excerpt}",
            "process",
            EXIT_ACTION,
        )
    return completed


def _git(
    root: Path,
    args: Sequence[str],
    *,
    env: Optional[Mapping[str, str]] = None,
    check: bool = True,
    input_data: Optional[bytes] = None,
) -> subprocess.CompletedProcess[bytes]:
    process_env = {key: value for key, value in os.environ.items() if key not in FORBIDDEN_GIT_ENV}
    process_env.update(
        {
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
        }
    )
    if env:
        process_env.update(env)
    return _run_process(
        ["git", "--no-pager", *args],
        root,
        env=process_env,
        timeout=120,
        check=check,
        input_data=input_data,
        replace_env=True,
    )


def _git_text(root: Path, args: Sequence[str], *, env: Optional[Mapping[str, str]] = None) -> str:
    completed = _git(root, args, env=env)
    return completed.stdout.decode("utf-8", "replace").strip()


def _git_paths(root: Path, args: Sequence[str], *, env: Optional[Mapping[str, str]] = None) -> Set[str]:
    completed = _git(root, args, env=env)
    return {part.decode("utf-8", "surrogateescape") for part in completed.stdout.split(b"\0") if part}


def _changed_paths(root: Path, *, env: Optional[Mapping[str, str]] = None) -> Set[str]:
    tracked = _git_paths(root, ["diff", "--name-only", "-z", "HEAD", "--"], env=env)
    staged = _git_paths(root, ["diff", "--cached", "--name-only", "-z", "HEAD", "--"], env=env)
    untracked = _git_paths(root, ["ls-files", "--others", "--exclude-standard", "-z"], env=env)
    return tracked | staged | untracked


def _index_entries(root: Path) -> Dict[str, str]:
    completed = _git(root, ["ls-files", "--stage", "-z"])
    result: Dict[str, str] = {}
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        prefix, separator, path = raw.partition(b"\t")
        if not separator:
            raise TransactionError("RTX-INDEX-FORMAT", "unexpected git ls-files output", "preflight", EXIT_PREFLIGHT)
        result[path.decode("utf-8", "surrogateescape")] = prefix.decode("ascii", "strict")
    return result


def _outside_index(entries: Mapping[str, str], mutable_paths: Set[str]) -> Dict[str, str]:
    return {path: value for path, value in entries.items() if path not in mutable_paths}


def _parse_plain_fields(text: str) -> Dict[str, List[str]]:
    fields: Dict[str, List[str]] = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([a-z][a-z0-9_]*):\s*(.+)", line)
        if match:
            fields.setdefault(match.group(1), []).append(match.group(2))
    return fields


def _validate_structured_report(path: Path) -> bytes:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TransactionError("RTX-REPORT-INVALID", f"structured report is missing or invalid: {path}: {exc}", "validate", EXIT_ACTION) from exc

    failures: List[str] = []
    if not isinstance(value, dict):
        failures.append("$ must be an object")
    else:
        if value.get("success") is not True:
            failures.append("$.success must be true")
        exit_code = value.get("exit_code")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool) or exit_code != 0:
            failures.append("$.exit_code must be integer zero")
        if not isinstance(value.get("findings"), list):
            failures.append("$.findings must be an array")

    def walk(node: Any, location: str) -> None:
        if isinstance(node, dict):
            severity = node.get("severity")
            if isinstance(severity, str) and severity.lower() == "error":
                failures.append(f"{location}.severity=error")
            for key in ("status", "result", "verdict"):
                status_value = node.get(key)
                if isinstance(status_value, str) and status_value.lower() in FAIL_STATUSES:
                    failures.append(f"{location}.{key}={status_value}")
            if node.get("success") is False:
                failures.append(f"{location}.success=false")
            exit_code = node.get("exit_code")
            if isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code != 0:
                failures.append(f"{location}.exit_code={exit_code}")
            for key, child in node.items():
                walk(child, f"{location}.{key}")
        elif isinstance(node, list):
            for index, child in enumerate(node):
                walk(child, f"{location}[{index}]")

    walk(value, "$")
    if failures:
        raise TransactionError(
            "RTX-REPORT-ERROR",
            f"structured report contains failure findings: {path}: {', '.join(failures[:8])}",
            "validate",
            EXIT_ACTION,
        )
    return raw


def render_task_closure(
    todo_text: str,
    task_id: str,
    substantive_commit: str,
    request_id: str,
    closure_text: str,
) -> str:
    """Render one exact legacy Task closure without free-form document regexes."""

    header_re = re.compile(rf"^- \[p\] \*\*{re.escape(task_id)}\*\*(?P<tail>[^\n]*)$", re.MULTILINE)
    matches = list(header_re.finditer(todo_text))
    if len(matches) != 1:
        raise TransactionError(
            "RTX-BOOKKEEPING-TASK",
            f"expected exactly one [p] header for {task_id}, found {len(matches)}",
            "bookkeeping",
            EXIT_BOOKKEEPING,
        )
    match = matches[0]
    next_task = re.search(r"^(?:- \[[^\]]+\] \*\*[0-9]{4}-[0-9]{2}|## )", todo_text[match.end() :], re.MULTILINE)
    block_end = match.end() + (next_task.start() if next_task else len(todo_text[match.end() :]))
    block = todo_text[match.start() : block_end]
    if re.search(r"\bREF:\s*[0-9a-f]{7,40}\b", match.group(0)):
        raise TransactionError("RTX-BOOKKEEPING-REF", f"active Task {task_id} already has a REF", "bookkeeping", EXIT_BOOKKEEPING)
    dod_matches = list(re.finditer(r"^  - \*\*Definition of Done:\*\*[^\n]*$", block, re.MULTILINE))
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
        self.lock_path: Optional[Path] = None
        self.lock_payload = f"{self.identity['request_id']}\n{self.identity['owner_token']}\n"

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
            raise TransactionError("RTX-CONCURRENT-DRIFT", f"paths changed after preflight: {changed}", phase, EXIT_SCOPE)

    def preflight(self) -> None:
        self.current_phase = "preflight"
        if not (self.root / ".git").exists():
            # Worktrees use a .git file, while ordinary fixture repositories use a directory.
            if not (self.root / ".git").is_file():
                raise TransactionError("RTX-ROOT-GIT", f"not a Git worktree: {self.root}", "preflight", EXIT_PREFLIGHT)
        self._assert_head(self.identity["expected_base"], "preflight")
        branch = _git_text(self.root, ["symbolic-ref", "--quiet", "HEAD"])
        if not branch.startswith("refs/heads/"):
            raise TransactionError("RTX-HEAD-DETACHED", "transaction requires a named local branch", "preflight", EXIT_PREFLIGHT)
        self.branch_ref = branch
        git_dir_text = _git_text(self.root, ["rev-parse", "--git-dir"])
        git_dir = Path(git_dir_text)
        if not git_dir.is_absolute():
            git_dir = self.root / git_dir
        for relative in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply", "sequencer"):
            if (git_dir / relative).exists():
                raise TransactionError("RTX-GIT-OPERATION", f"repository operation is in progress: {relative}", "preflight", EXIT_PREFLIGHT)
        if _git(self.root, ["ls-files", "-u", "-z"]).stdout:
            raise TransactionError("RTX-GIT-UNMERGED", "index contains unmerged entries", "preflight", EXIT_PREFLIGHT)

        selector_path = self.root / self.authority["selector_path"]
        try:
            selector = json.loads(selector_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise TransactionError("RTX-AUTHORITY-SELECTOR", f"cannot read authority selector: {exc}", "preflight", EXIT_PREFLIGHT) from exc
        for key in ALLOWED_AUTHORITY_KEYS:
            if selector.get(key) != self.authority[key]:
                raise TransactionError(
                    "RTX-AUTHORITY-DRIFT",
                    f"authority {key} expected {self.authority[key]!r}, observed {selector.get(key)!r}",
                    "preflight",
                    EXIT_PREFLIGHT,
                )

        try:
            claim_text = self.claim_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise TransactionError("RTX-CLAIM-MISSING", f"cannot read exact claim: {exc}", "preflight", EXIT_PREFLIGHT) from exc
        fields = _parse_plain_fields(claim_text)
        expected_claim_fields = {
            "task_id": self.identity["task_id"],
            "request_id": self.identity["request_id"],
            "owner_token": self.identity["owner_token"],
            "base_commit": self.identity["expected_base"],
            "transaction_profile": PROFILE,
            **claim_contract_fields(self.manifest),
            "state": "[p]",
        }
        for key, expected in expected_claim_fields.items():
            if fields.get(key) != [expected]:
                raise TransactionError(
                    "RTX-CLAIM-IDENTITY",
                    f"claim field {key} must occur exactly once with value {expected!r}",
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
        current_manifest_sha256 = _sha256_bytes(expected_manifest.read_bytes())
        if current_manifest_sha256 != self.manifest["_loaded_sha256"]:
            raise TransactionError(
                "RTX-MANIFEST-DRIFT",
                "manifest bytes changed after they were parsed",
                "preflight",
                EXIT_PREFLIGHT,
            )
        report_paths = {
            report for action in self.manifest["actions"] for report in action["reports"]
        }
        all_declared_paths = (
            set(self.scope["read_paths"])
            | set(self.scope["input_paths"])
            | set(self.scope["output_paths"])
            | report_paths
            | {
                self.identity["claim_path"],
                self.identity["manifest_path"],
                self.authority["selector_path"],
                self.manifest["bookkeeping"]["todo_path"],
            }
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

        bookkeeping = self.manifest["bookkeeping"]
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
            holder = "unreadable"
            with contextlib.suppress(OSError, UnicodeError):
                holder = lock.read_text(encoding="utf-8").strip().replace("\n", " ")
            raise TransactionError("RTX-LOCK-HELD", f"transaction lock is held: {holder}", "preflight", EXIT_PREFLIGHT) from exc
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(self.lock_payload)
            handle.flush()
            os.fsync(handle.fileno())
        self.lock_path = lock

    def release_lock(self) -> None:
        if self.lock_path is None:
            return
        try:
            if self.lock_path.read_text(encoding="utf-8") == self.lock_payload:
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
        self.current_phase = "actions"
        self.log_dir.mkdir(parents=True, exist_ok=False)
        candidate_inputs = {
            relative: _read_state(candidate / relative) for relative in self.scope["input_paths"]
        }
        for index, action in enumerate(self.manifest["actions"], start=1):
            registered = ACTION_REGISTRY[action["id"]]
            self.current_phase = registered.phase
            protected_before = {
                relative: _read_state(candidate / relative)
                for relative in (
                    self.scope["input_paths"]
                    if registered.phase == "generate"
                    else self.scope["substantive_paths"]
                )
            }
            report_before = {
                report: _read_state(candidate / report) for report in action["reports"]
            }
            stdout_path = self.log_dir / f"{index:02d}-{registered.action_id}.stdout.log"
            stderr_path = self.log_dir / f"{index:02d}-{registered.action_id}.stderr.log"
            started = time.monotonic()
            with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
                completed = _run_process(
                    registered.argv,
                    candidate,
                    timeout=action["timeout_seconds"],
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                )
            duration_ms = int((time.monotonic() - started) * 1000)
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
                    f"{registered.action_id} exited {completed.returncode}; logs: {result.stdout_path}, {result.stderr_path}",
                    registered.phase,
                    EXIT_ACTION,
                )
            protected_after = {
                relative: _read_state(candidate / relative) for relative in protected_before
            }
            mutated_protected = [
                relative for relative in protected_before if protected_before[relative] != protected_after[relative]
            ]
            if mutated_protected:
                rule = "RTX-GENERATE-MUTATED-INPUT" if registered.phase == "generate" else "RTX-VALIDATE-MUTATED-TREE"
                raise TransactionError(rule, f"{registered.action_id} mutated protected paths: {mutated_protected}", registered.phase, EXIT_SCOPE)
            for report in action["reports"]:
                report_path = candidate / report
                report_after = _read_state(report_path)
                if not report_after.exists or report_after == report_before[report]:
                    raise TransactionError("RTX-REPORT-STALE", f"action did not create a fresh report: {report}", registered.phase, EXIT_ACTION)
                report_bytes = _validate_structured_report(report_path)
                retained = self.log_dir / f"{index:02d}-{registered.action_id}-{Path(report).name}"
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
        if not changed:
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
        self.emit(f"PHASE promote: PASS outputs={len(self.scope['output_paths'])}")

    def _write_promotion_journal(self, status: str) -> None:
        journal_path = self.log_dir / "promotion-journal.json"
        value = {
            "schema": "legacy-runner-promotion-journal@v1",
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
                raise TransactionError(
                    "RTX-ROLLBACK-DRIFT",
                    f"refusing to overwrite a newer edit while rolling back {record.path}; backups retained",
                    "rollback",
                    EXIT_PROMOTION,
                )
            if record.previous.exists and record.backup is not None:
                backup_bytes, _ = _read_file_nofollow(record.backup)
                _atomic_write(destination, backup_bytes, record.previous.mode)
            else:
                _unlink_nofollow(destination, current)
        self._write_promotion_journal("rolled-back")
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
    ) -> str:
        """Create and verify a commit object without moving any reference."""

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
            if not changed:
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
        if _git_text(self.root, ["rev-parse", f"{commit}^{{tree}}"] ) != tree:
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
        observed_outputs = {relative: _read_state(self.root / relative) for relative in self.scope["output_paths"]}
        if observed_outputs != self.promoted_states:
            raise TransactionError("RTX-PROMOTED-DRIFT", "promoted outputs changed before commit preparation", self.current_phase, EXIT_SCOPE)
        sources = {relative: self.root / relative for relative in self.scope["substantive_paths"]}
        self.substantive_commit = self._prepare_commit(
            expected,
            self.scope["substantive_paths"],
            sources,
            self.manifest["commit"]["substantive_message"],
            "prepare-substantive",
        )
        self._inject("after-substantive-commit")
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
                    stdout=stdout_handle,
                    stderr=stderr_handle,
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
        self.emit("PHASE validate-bookkeeping: PASS")

    def promote_bookkeeping_todo(self) -> None:
        if self.bookkeeping_todo_bytes is None or self.promotion_backup_root is None:
            raise TransactionError("RTX-BOOKKEEPING-PREPARED", "bookkeeping bytes or promotion journal are unavailable", "publish", EXIT_BOOKKEEPING)
        todo_relative = self.manifest["bookkeeping"]["todo_path"]
        self._assert_paths_unchanged({todo_relative}, "publish")
        destination = self.root / todo_relative
        previous = _read_state(destination)
        backup = self.promotion_backup_root / "bookkeeping-todo.backup"
        _backup_file_nofollow(destination, backup, previous)
        record = PromotionRecord(todo_relative, previous, backup)
        self.promotion_journal.append(record)
        self._write_promotion_journal("promoting-bookkeeping")
        _atomic_write(destination, self.bookkeeping_todo_bytes, destination.stat().st_mode)
        record.promoted = _read_state(destination)
        self.promoted_todo_state = record.promoted
        self._write_promotion_journal("prepared-for-publish")

    def _assert_publish_context(self) -> None:
        self._assert_head(self.identity["expected_base"], "publish")
        if _git_text(self.root, ["symbolic-ref", "--quiet", "HEAD"]) != self.branch_ref:
            raise TransactionError("RTX-BRANCH-DRIFT", "checked-out branch changed after preflight", "publish", EXIT_COMMIT)
        self._assert_paths_unchanged(
            set(self.scope["input_paths"])
            | {
                self.identity["claim_path"],
                self.identity["manifest_path"],
                self.authority["selector_path"],
                self.manifest["bookkeeping"]["todo_path"],
            },
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
        todo_path = self.root / self.manifest["bookkeeping"]["todo_path"]
        if self.promoted_todo_state is None or _read_state(todo_path) != self.promoted_todo_state:
            raise TransactionError("RTX-BOOKKEEPING-DRIFT", "prepared TODO.md changed before CAS", "publish", EXIT_SCOPE)
        self._assert_worktree_matches_commit(self.substantive_commit, self.scope["substantive_paths"], "publish")
        if _outside_index(_index_entries(self.root), self.mutable_paths) != _outside_index(self.initial_index, self.mutable_paths):
            raise TransactionError("RTX-INDEX-DRIFT", "ambient Git index changed before CAS", "publish", EXIT_COMMIT)

    def publish(self) -> None:
        if not self.substantive_commit or not self.bookkeeping_commit or not self.branch_ref or self.bookkeeping_todo_bytes is None:
            raise TransactionError("RTX-PUBLISH-PREPARED", "commit objects are not fully prepared", "publish", EXIT_COMMIT)
        self.current_phase = "publish"
        self._assert_publish_context()
        self.promote_bookkeeping_todo()
        self._assert_pre_cas_context()
        prepared_path = self.log_dir / "prepared-result.json"
        self.write_result(self.result("prepared"), path=prepared_path)
        self._assert_pre_cas_context()
        self._inject("before-cas")
        completed = _git(
            self.root,
            [
                "update-ref",
                "-m",
                f"runner transaction {self.identity['task_id']} {self.identity['request_id']}",
                self.branch_ref,
                self.bookkeeping_commit,
                self.identity["expected_base"],
            ],
            check=False,
        )
        if completed.returncode != 0:
            raise TransactionError("RTX-PUBLISH-CAS", "branch compare-and-swap publication failed", "publish", EXIT_COMMIT)
        self.published = True
        self.discard_promotion_backups()
        self._inject("after-publish")
        if self._head() != self.bookkeeping_commit:
            raise TransactionError("RTX-PUBLISH-HEAD", "published branch is not checked out at the bookkeeping commit", "publish", EXIT_COMMIT)

        outside_before = _outside_index(self.initial_index, self.mutable_paths)
        exact_paths = sorted(self.mutable_paths)
        _git(self.root, ["reset", "--quiet", self.bookkeeping_commit, "--", *exact_paths])
        if _outside_index(_index_entries(self.root), self.mutable_paths) != outside_before:
            raise TransactionError("RTX-INDEX-CORRUPTION", "publication altered unrelated index entries", "publish", EXIT_COMMIT)
        self._assert_paths_unchanged(
            {self.identity["claim_path"], self.identity["manifest_path"], self.authority["selector_path"]},
            "publish",
        )
        self.emit(f"PHASE publish: PASS branch={self.branch_ref} commit={self.bookkeeping_commit}")

    def verify_published(self) -> None:
        self.current_phase = "verify"
        if not self.published or not self.substantive_commit or not self.bookkeeping_commit:
            raise TransactionError("RTX-FINAL-PUBLISH", "transaction was not published", "verify", EXIT_COMMIT)
        self._assert_head(self.bookkeeping_commit, "verify")
        if _git_text(self.root, ["rev-parse", f"{self.bookkeeping_commit}^"]) != self.substantive_commit:
            raise TransactionError("RTX-FINAL-PARENT", "bookkeeping parent is not the substantive commit", "verify", EXIT_BOOKKEEPING)
        for commit in (self.substantive_commit, self.bookkeeping_commit):
            _git(self.root, ["cat-file", "-e", f"{commit}^{{commit}}"])
        self._assert_worktree_matches_commit(self.substantive_commit, self.scope["substantive_paths"], "verify")
        todo_path = self.root / self.manifest["bookkeeping"]["todo_path"]
        if todo_path.read_bytes() != self.bookkeeping_todo_bytes or self.substantive_commit not in todo_path.read_text(encoding="utf-8"):
            raise TransactionError("RTX-FINAL-REF", "working TODO.md does not match the verified bookkeeping tree", "verify", EXIT_BOOKKEEPING)
        if not self.claim_path.exists():
            raise TransactionError("RTX-FINAL-CLAIM-EARLY", "claim disappeared before durable finalization", "verify", EXIT_BOOKKEEPING)
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
        # Persist a non-success recovery state before moving the exact claim.
        self.write_result(self.result("published-pending-finalization"))
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
            # PASS is the final durable operation; no fallible mutation follows it.
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
            if isinstance(exc, TransactionError):
                detail = f"{exc.rule}: {exc.message}"
            else:
                detail = f"{type(exc).__name__}: {exc}"
            raise TransactionError(
                "RTX-CLAIM-FINALIZE-FAILED",
                f"claim finalization failed: {detail}; retained locations: {recovery_locations}",
                "finalize-claim",
                EXIT_BOOKKEEPING,
            ) from exc
        self.emit("PHASE finalize-claim: PASS")

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
        except Exception as exc:  # Defensive boundary: never print PASS after an unknown failure.
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

    lint_parser = subparsers.add_parser("lint-envelope", help="reject ad hoc or destructive legacy run.sh content")
    lint_parser.add_argument("path", type=Path)

    render_parser = subparsers.add_parser("render-envelope", help="print the only accepted legacy envelope form")
    render_parser.add_argument("--manifest", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
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
