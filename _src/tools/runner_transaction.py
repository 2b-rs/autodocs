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

try:  # pragma: no cover - exercised implicitly by both import modes
    from _src.tools import legacy_task_editor as lte
except ImportError:  # pragma: no cover - direct script execution from _src/tools
    import legacy_task_editor as lte  # type: ignore[no-redef]


MANIFEST_SCHEMA = "legacy-runner-transaction@v1"
RESULT_SCHEMA = "legacy-runner-transaction-result@v1"
PROMOTION_JOURNAL_SCHEMA = "legacy-runner-promotion-journal@v1"
TRANSACTION_JOURNAL_SCHEMA = "legacy-runner-transaction-journal@v1"
CURRENT_POINTER_SCHEMA = "legacy-runner-current-pointer@v1"
LOCK_SCHEMA = "legacy-runner-lock@v1"
TERMINAL_RESULT_VERDICTS = {"passed", "failed"}

ALLOWED_AUTHORITY_KEYS = ("authority_epoch", "authority_profile", "write_phase", "runner_protocol")
TASK_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,127}$")
OWNER_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{7,255}$")
SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./-]*$")
CANDIDATE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PROFILE = "close-task-v1"
VERIFY_AND_COMMIT_PROFILE = "verify-and-commit-v1"
EDITOR_PROFILE = "legacy-editor-candidate-v1"
BRANCH_MERGE_PROFILE = "branch-merge-v1"
PROFILES = (PROFILE, VERIFY_AND_COMMIT_PROFILE, EDITOR_PROFILE, BRANCH_MERGE_PROFILE)

# Typed branch/merge sub-protocol (docs/pipeline/branch-merge-actions.md, Task 0038-19).
TYPED_ACTION_BASE_BRANCH = "base-branch"
TYPED_ACTION_MERGE_PREREQS = "merge-prereqs"
TYPED_ACTION_INTEGRATE_CHECKPOINT = "integrate-checkpoint"
CONTRACT_TYPED_ACTIONS = (
    TYPED_ACTION_BASE_BRANCH,
    TYPED_ACTION_MERGE_PREREQS,
    TYPED_ACTION_INTEGRATE_CHECKPOINT,
)
# The legacy bridge implements exactly the two non-checkpoint-crossing actions.
IMPLEMENTED_TYPED_ACTIONS = (TYPED_ACTION_BASE_BRANCH, TYPED_ACTION_MERGE_PREREQS)
CAPABILITY_CLASSES = ("sandboxed-grunt", "unprivileged", "privileged")
NON_PRIVILEGED_CLASSES = ("sandboxed-grunt", "unprivileged")
ITEM_ID_RE = re.compile(r"^[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?$")
FEATURE_ID_RE = re.compile(r"^[0-9]{4}$")
BRANCH_NAME_RE = re.compile(r"^(?:main|[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?)$")
# Feature closure bookkeeping never routes through this bridge.
FORBIDDEN_BRANCH_WRITE_PATHS = frozenset({"DONE.md"})
CLAIM_FILENAME_RE = re.compile(r"(?:^|/)TODO-[^/]+\.md$")
CLAIM_OWNER_TOKEN_LINE_RE = re.compile(r"^owner_token:[ \t]*(\S.*)$", re.MULTILINE)
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
EXIT_BRANCH = 80
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
    status: str
    exit_code: Optional[int]
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
    """Open an existing directory without resolving or traversing symlinks."""
    absolute = path.absolute()
    if not absolute.is_absolute():
        raise OSError(f"directory path is not absolute: {path}")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open("/", flags)
    try:
        for component in absolute.parts[1:]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _atomic_create(path: Path, data: bytes, mode: Optional[int] = None) -> None:
    """Atomically create one immutable file, failing rather than replacing it."""
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
        try:
            os.link(temporary_name, path.name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        except FileExistsError as exc:
            raise TransactionError(
                "RTX-RESULT-IMMUTABLE",
                f"immutable file already exists at {path}",
                "result",
                EXIT_INTERNAL,
            ) from exc
        os.fsync(directory_fd)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary_name, dir_fd=directory_fd)
        os.close(directory_fd)


def _ensure_directory_nofollow(root: Path, directory: Path) -> None:
    """Create a repository-relative directory chain without traversing symlinks."""
    relative = directory.absolute().relative_to(root.absolute())
    descriptor = _open_directory_nofollow(root)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        for component in relative.parts:
            try:
                os.mkdir(component, 0o700, dir_fd=descriptor)
            except FileExistsError:
                pass
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
    finally:
        os.close(descriptor)


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


def _branch_error(rule: str, message: str) -> TransactionError:
    return TransactionError(rule, message, "manifest", EXIT_MANIFEST)


def _normalize_branch_name(raw: Any, field: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise _branch_error("BMA-BRANCH-NAME-INVALID", f"{field} must be a non-empty string")
    if not BRANCH_NAME_RE.fullmatch(raw):
        raise _branch_error(
            "BMA-BRANCH-NAME-INVALID",
            f"{field} must be 'main' or an item-ID branch name, not {raw!r}",
        )
    return raw


def _expected_parent_branch(item_id: str) -> str:
    """Derive the parent branch from the topology in docs/pipeline/branch-workflow.md."""
    if "." in item_id:
        return item_id.split(".", 1)[0]
    if "-" in item_id:
        return item_id.split("-", 1)[0]
    return "main"


def _is_checkpoint_target(target_branch: str, item_id: str) -> bool:
    """A target that is not the item's own branch advances an integration boundary."""
    return target_branch == "main" or bool(FEATURE_ID_RE.fullmatch(target_branch)) or target_branch != item_id


def load_branch_block(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the typed branch/merge sub-protocol block, fail-closed.

    Implements the request-shape rules of ``docs/pipeline/branch-merge-actions.md``
    (Task ``0038-19``) that are checkable without touching the repository. Repository
    facts (parent tip, source tips, claim owner token) are checked in preflight.
    """
    identity = data["identity"]
    scope = data["scope"]
    branch = data["branch"]
    if not isinstance(branch, dict):
        raise _branch_error("RTX-SCHEMA-TYPE", "manifest branch must be a JSON object")
    _exact_keys(
        branch,
        {"typed_action", "item_id", "target_branch", "capability_class", "idempotence_key"},
        {"parent_branch", "sources"},
        "manifest.branch",
    )

    typed_action = branch["typed_action"]
    if typed_action not in CONTRACT_TYPED_ACTIONS:
        raise _branch_error(
            "BMA-ACTION-UNKNOWN",
            f"unknown typed action: {typed_action!r}; expected one of {list(CONTRACT_TYPED_ACTIONS)}",
        )
    capability_class = branch["capability_class"]
    if capability_class not in CAPABILITY_CLASSES:
        raise _branch_error(
            "BMA-CAPABILITY-UNKNOWN",
            f"unknown capability class: {capability_class!r}; expected one of {list(CAPABILITY_CLASSES)}",
        )
    item_id = branch["item_id"]
    if not isinstance(item_id, str) or not ITEM_ID_RE.fullmatch(item_id):
        raise _branch_error("BMA-ITEM-ID-INVALID", f"invalid branch.item_id: {item_id!r}")
    if item_id != identity["task_id"]:
        raise _branch_error(
            "BMA-ITEM-IDENTITY",
            f"branch.item_id {item_id!r} must equal identity.task_id {identity['task_id']!r}",
        )
    target_branch = _normalize_branch_name(branch["target_branch"], "branch.target_branch")

    # Authority split (contract §6): a request may only advance the item's own
    # branch. Advancing a Feature branch or `main` is `integrate-checkpoint`,
    # which is privileged-only and is not implemented by this legacy bridge.
    crosses_checkpoint = (
        typed_action == TYPED_ACTION_INTEGRATE_CHECKPOINT
        or _is_checkpoint_target(target_branch, item_id)
    )
    if crosses_checkpoint:
        if capability_class in NON_PRIVILEGED_CLASSES:
            raise _branch_error(
                "BMA-AUTHORITY-VIOLATION",
                f"capability class {capability_class!r} may not advance integration target "
                f"{target_branch!r} for item {item_id!r}; Task->Feature, Feature->main, acceptance "
                "records and Feature [u] verdicts are privileged-integrator actions",
            )
        raise _branch_error(
            "BMA-ACTION-UNSUPPORTED",
            "integrate-checkpoint is not implemented by the legacy branch-merge bridge; "
            "the privileged integrator performs it per docs/pipeline/branch-workflow.md",
        )
    if typed_action not in IMPLEMENTED_TYPED_ACTIONS:  # pragma: no cover - defensive
        raise _branch_error("BMA-ACTION-UNSUPPORTED", f"typed action {typed_action!r} is not implemented")

    idempotence_key = branch["idempotence_key"]
    prefix = f"{typed_action}:{item_id}:"
    if not isinstance(idempotence_key, str) or not idempotence_key.startswith(prefix) or len(idempotence_key) <= len(prefix):
        raise _branch_error(
            "BMA-IDEMPOTENCE-KEY",
            f"branch.idempotence_key must start with {prefix!r} and carry a disambiguator",
        )

    expected_parent = _expected_parent_branch(item_id)
    if typed_action == TYPED_ACTION_BASE_BRANCH:
        if "parent_branch" not in branch:
            raise _branch_error("BMA-PARENT-BRANCH-MISSING", "base-branch requires branch.parent_branch")
        parent_branch = _normalize_branch_name(branch["parent_branch"], "branch.parent_branch")
        if parent_branch != expected_parent:
            raise _branch_error(
                "BMA-PARENT-BRANCH-INVALID",
                f"branch.parent_branch {parent_branch!r} is not the topology parent {expected_parent!r} of {item_id!r}",
            )
        if branch.get("sources"):
            raise _branch_error("BMA-SOURCES-FORBIDDEN", "base-branch declares no merge sources")
        branch["sources"] = []
        if scope["substantive_paths"]:
            raise _branch_error(
                "BMA-SCOPE-VIOLATION",
                "base-branch produces an identical tree and must declare no substantive paths",
            )
    else:
        if "parent_branch" in branch:
            raise _branch_error("BMA-PARENT-BRANCH-FORBIDDEN", "merge-prereqs does not declare a parent branch")
        branch["parent_branch"] = None
        sources = branch.get("sources")
        if not isinstance(sources, list) or not sources:
            raise _branch_error("BMA-SOURCES-MISSING", "merge-prereqs requires at least one declared source branch")
        seen: Set[str] = set()
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                raise _branch_error("RTX-SCHEMA-TYPE", f"branch.sources[{index}] must be a JSON object")
            _exact_keys(source, {"dependency", "branch", "tip"}, set(), f"branch.sources[{index}]")
            dependency = source["dependency"]
            if not isinstance(dependency, str) or not ITEM_ID_RE.fullmatch(dependency):
                raise _branch_error("BMA-ITEM-ID-INVALID", f"invalid branch.sources[{index}].dependency: {dependency!r}")
            source_branch = _normalize_branch_name(source["branch"], f"branch.sources[{index}].branch")
            if source_branch != dependency:
                raise _branch_error(
                    "BMA-UNDECLARED-SOURCE",
                    f"branch.sources[{index}] dependency {dependency!r} has no matching pinned branch "
                    f"reference (declared {source_branch!r})",
                )
            if source_branch == target_branch:
                raise _branch_error("BMA-UNDECLARED-SOURCE", "a merge source may not be the target branch")
            if source_branch in seen:
                raise _branch_error("BMA-SOURCES-DUPLICATE", f"duplicate merge source: {source_branch!r}")
            seen.add(source_branch)
            if not isinstance(source["tip"], str) or not FULL_COMMIT_RE.fullmatch(source["tip"]):
                raise _branch_error("BMA-STALE-SOURCE-TIP", f"branch.sources[{index}].tip must be a full 40-hex commit")
        if not scope["substantive_paths"]:
            raise _branch_error(
                "BMA-SCOPE-VIOLATION",
                "merge-prereqs must declare the exact tracked paths the merge changes",
            )

    forbidden = FORBIDDEN_BRANCH_WRITE_PATHS & set(scope["substantive_paths"])
    if forbidden:
        raise _branch_error(
            "BMA-ACCEPTANCE-RECORD-FORBIDDEN",
            f"branch/merge actions never author Feature closure bookkeeping: {sorted(forbidden)}",
        )
    reserved = {identity["claim_path"], data["authority"]["selector_path"]} & set(scope["substantive_paths"])
    if reserved:
        raise _branch_error(
            "BMA-SCOPE-RESERVED",
            f"the item's own claim and the authority selector are never merge outputs: {sorted(reserved)}",
        )
    return branch


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
        {"commit", "bookkeeping", "editor", "branch"},
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
    is_branch_profile = data["profile"] == BRANCH_MERGE_PROFILE
    _exact_keys(scope, {"read_paths", "input_paths", "output_paths", "substantive_paths"}, set(), "manifest.scope")
    scope["read_paths"] = _string_list(scope["read_paths"], "scope.read_paths", allow_empty=True)
    scope["input_paths"] = _string_list(scope["input_paths"], "scope.input_paths", allow_empty=True)
    if data["profile"] in (PROFILE, EDITOR_PROFILE) and (not isinstance(scope["output_paths"], list) or not scope["output_paths"]):
        raise TransactionError(
            "RTX-SCOPE-OUTPUTS",
            f"{data['profile']} requires at least one output path",
            "manifest",
            EXIT_MANIFEST,
        )
    scope["output_paths"] = _string_list(
        scope["output_paths"],
        "scope.output_paths",
        allow_empty=(data["profile"] not in (PROFILE, EDITOR_PROFILE)),
    )
    scope["substantive_paths"] = _string_list(
        scope["substantive_paths"], "scope.substantive_paths", allow_empty=is_branch_profile
    )

    substantive_set = set(scope["substantive_paths"])
    input_output_set = set(scope["input_paths"]) | set(scope["output_paths"])
    if is_branch_profile and (scope["input_paths"] or scope["output_paths"]):
        raise TransactionError(
            "BMA-SCOPE-VIOLATION",
            "branch-merge-v1 runs no generator: input_paths and output_paths must be empty",
            "manifest",
            EXIT_MANIFEST,
        )
    # A merge's substantive paths come from the merged source trees, not from a
    # declared generator input/output pair, so the close-profile subset rule
    # does not apply to branch-merge-v1.
    if not is_branch_profile and not substantive_set.issubset(input_output_set):
        raise TransactionError(
            "RTX-SCOPE-SUBSTANTIVE-MISMATCH",
            f"substantive_paths must be a subset of declared inputs and outputs: {sorted(substantive_set - input_output_set)}",
            "manifest",
            EXIT_MANIFEST,
        )
    if data["profile"] == EDITOR_PROFILE and substantive_set != set(scope["output_paths"]):
        raise TransactionError(
            "RTX-SCOPE-SUBSTANTIVE-MISMATCH",
            "legacy-editor-candidate-v1 requires substantive_paths to equal output_paths exactly",
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
    if not isinstance(actions, list):
        raise TransactionError("RTX-SCHEMA-TYPE", "manifest actions must be a list", "manifest", EXIT_MANIFEST)
    if data["profile"] == EDITOR_PROFILE:
        if actions:
            raise TransactionError(
                "RTX-EDITOR-ACTIONS",
                "legacy-editor-candidate-v1 does not run generate/validate actions; actions must be empty",
                "manifest",
                EXIT_MANIFEST,
            )
    elif is_branch_profile:
        if actions != []:
            raise TransactionError(
                "BMA-ACTIONS-FORBIDDEN",
                "branch-merge-v1 runs no registry actions; actions must be an empty list",
                "manifest",
                EXIT_MANIFEST,
            )
    elif not actions:
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

    if is_branch_profile:
        if "branch" not in data:
            raise TransactionError(
                "RTX-SCHEMA-MISSING-KEYS", "branch-merge-v1 requires a branch block", "manifest", EXIT_MANIFEST
            )
        # Acceptance records, `[u]` integration verdicts and the `DONE.md` move are
        # bookkeeping_commit shapes (contract §6). Making them structurally
        # unexpressible here is how this bridge rejects them.
        if data.get("bookkeeping") is not None:
            raise TransactionError(
                "BMA-ACCEPTANCE-RECORD-FORBIDDEN",
                "branch-merge-v1 never carries a bookkeeping commit; acceptance records, "
                "Feature [u] verdicts and DONE.md moves are privileged-integrator actions",
                "manifest",
                EXIT_MANIFEST,
            )
        if data.get("commit") is not None:
            raise TransactionError(
                "BMA-COMMIT-FORBIDDEN",
                "branch-merge-v1 derives its merge commit messages deterministically; "
                "no free-form commit message is accepted",
                "manifest",
                EXIT_MANIFEST,
            )
        data["branch"] = load_branch_block(data)
        data["_loaded_path"] = str(path.resolve())
        data["_loaded_sha256"] = _sha256_bytes(raw_bytes)
        return data
    if "branch" in data:
        raise TransactionError(
            "BMA-BRANCH-BLOCK-FORBIDDEN",
            f"profile {data['profile']!r} does not accept a branch block",
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
    if data["profile"] in (PROFILE, VERIFY_AND_COMMIT_PROFILE, EDITOR_PROFILE) and not isinstance(commit, dict):
        raise TransactionError("RTX-SCHEMA-TYPE", "commit must be an object", "manifest", EXIT_MANIFEST)
    if data["profile"] == EDITOR_PROFILE and bookkeeping is not None:
        raise TransactionError(
            "RTX-EDITOR-BOOKKEEPING",
            "legacy-editor-candidate-v1 has no separate bookkeeping commit; the candidate carries its own TODO.md change",
            "manifest",
            EXIT_MANIFEST,
        )
    if data["profile"] != EDITOR_PROFILE and data.get("editor") is not None:
        raise TransactionError("RTX-EDITOR-UNEXPECTED", "editor is only valid for legacy-editor-candidate-v1", "manifest", EXIT_MANIFEST)
    if data["profile"] in (PROFILE, VERIFY_AND_COMMIT_PROFILE) and bookkeeping is None:
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

    editor = data.get("editor")
    if data["profile"] == EDITOR_PROFILE:
        if not isinstance(editor, dict):
            raise TransactionError("RTX-SCHEMA-TYPE", "editor must be a JSON object for legacy-editor-candidate-v1", "manifest", EXIT_MANIFEST)
        _exact_keys(
            editor,
            {"operation_path", "candidate_dir", "candidate_manifest_path", "expected_candidate_sha256"},
            set(),
            "manifest.editor",
        )
        editor["operation_path"] = _normalize_path(editor["operation_path"], "editor.operation_path")
        editor["candidate_dir"] = _normalize_path(editor["candidate_dir"], "editor.candidate_dir")
        editor["candidate_manifest_path"] = _normalize_path(editor["candidate_manifest_path"], "editor.candidate_manifest_path")
        if editor["candidate_manifest_path"] != f"{editor['candidate_dir']}/candidate.json":
            raise TransactionError(
                "RTX-EDITOR-CANDIDATE-LAYOUT",
                "editor.candidate_manifest_path must be editor.candidate_dir/candidate.json",
                "manifest",
                EXIT_MANIFEST,
            )
        digest = editor["expected_candidate_sha256"]
        if not isinstance(digest, str) or not CANDIDATE_SHA256_RE.fullmatch(digest):
            raise TransactionError(
                "RTX-EDITOR-CANDIDATE-DIGEST",
                "editor.expected_candidate_sha256 must be 64 lowercase hex characters",
                "manifest",
                EXIT_MANIFEST,
            )

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
        "branch": manifest.get("branch"),
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
    branch = manifest.get("branch")
    if branch is not None:
        fields["transaction_branch_json"] = json.dumps(branch, separators=(",", ":"), sort_keys=True)
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
    """Render a close-task-v1 bookkeeping closure.

    This is a thin adapter over the ``legacy_task_editor`` (Task 0038-05.01)
    digest-bound structural backlog parser: it locates the exact Task block,
    its ``Definition of Done`` line, and header REF-absence using the same
    ``parse_backlog`` primitive the editor uses for pickup/progress/closure
    operations, instead of maintaining a second, independent regex-based
    Task-boundary detector. It intentionally does not require a
    ``**Claim (...):**`` pointer/base-commit cross-check the way the editor's
    own ``closure`` operation kind does: this profile's own coordination
    claim (see ``claim_contract_fields``) binds its ``base_commit`` field to
    the *current* transaction's ``expected_base`` rather than the Task's
    original pickup base, so the two are not generally the same value and
    the editor's stricter ``_assert_pointer`` invariant does not apply here
    without changing that unrelated, already-accepted convention.
    """
    try:
        document = lte.parse_backlog("<close-task-v1 bookkeeping>", todo_text.encode("utf-8"))
    except lte.EditorError as exc:
        raise TransactionError(f"RTX-BOOKKEEPING-{exc.rule}", exc.message, "bookkeeping", EXIT_BOOKKEEPING) from exc
    matches = [task for task in document.tasks if task.id == task_id]
    if len(matches) != 1 or matches[0].marker != "p":
        active = len(matches) == 1 and matches[0].marker == "p"
        raise TransactionError(
            "RTX-BOOKKEEPING-TASK-MATCH",
            f"expected exactly one active marker '- [p] **{task_id}**', found {len(matches)} match(es) (active={active})",
            "bookkeeping",
            EXIT_BOOKKEEPING,
        )
    task = matches[0]
    header = document.text[task.header.start : task.header.end]
    if lte.AUTHORITATIVE_REF_RE.search(header):
        raise TransactionError("RTX-BOOKKEEPING-REF", f"active Task {task_id} already has a REF", "bookkeeping", EXIT_BOOKKEEPING)
    dod_spans = task.sections.get("Definition of Done", ())
    if len(dod_spans) != 1:
        raise TransactionError(
            "RTX-BOOKKEEPING-DOD",
            f"expected exactly one Definition of Done line for {task_id}, found {len(dod_spans)}",
            "bookkeeping",
            EXIT_BOOKKEEPING,
        )

    block = document.text[task.span.start : task.span.end]
    header_relative_end = task.header.end - task.span.start
    new_header = header.replace("- [p]", "- [x]", 1).rstrip() + f" REF: {substantive_commit}"
    closure = (
        f"\n  - **Closure ({dt.date.today().isoformat()}):** {closure_text.strip()} "
        f"Validation passed in request `{request_id}`. REF: `{substantive_commit}`."
    )
    dod = dod_spans[0]
    insert = dod.end - task.span.start
    new_block = block[:insert] + closure + block[insert:]
    new_block = new_header + new_block[header_relative_end:]
    after_text = document.text[: task.span.start] + new_block + document.text[task.span.end :]
    if not after_text.startswith(document.text[: task.span.start]) or not after_text.endswith(document.text[task.span.end :]):
        raise TransactionError("RTX-BOOKKEEPING-UNRELATED-BYTES", "closure rendering changed bytes outside the Task span", "bookkeeping", EXIT_BOOKKEEPING)
    if after_text.count(substantive_commit) < 2:
        raise TransactionError("RTX-BOOKKEEPING-VERIFY", "rendered closure is missing the substantive REF", "bookkeeping", EXIT_BOOKKEEPING)
    return after_text


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
        self._phase_started_at = time.monotonic()
        self.phase_results: List[Dict[str, Any]] = []
        self.observed_base: Optional[str] = None
        self.observed_authority: Optional[Dict[str, str]] = None
        self.action_results: List[ActionResult] = []
        self.substantive_commit: Optional[str] = None
        self.bookkeeping_commit: Optional[str] = None
        self.branch_ref: Optional[str] = None
        self.published = False
        self.bookkeeping_todo_bytes: Optional[bytes] = None
        self.claim_finalized = False
        self.editor_candidate: Optional[Mapping[str, Any]] = None
        self.preflight_states: Dict[str, FileState] = {}
        self.initial_index: Dict[str, str] = {}
        self.promotion_journal: List[PromotionRecord] = []
        self.promotion_backup_root: Optional[Path] = None
        self.promoted_states: Dict[str, FileState] = {}
        self.promoted_todo_state: Optional[FileState] = None
        self.claim_archive: Optional[Path] = None
        self.log_dir = self.root / "output" / "logs" / self.identity["task_id"] / self.identity["request_id"]
        self.task_log_dir = self.log_dir.parent
        self.result_path = self.log_dir / "result.json"
        self.current_pointer_path = self.task_log_dir / "current.json"
        self.journal_path = self.log_dir / "transaction-journal.json"
        self.terminal_result_persisted = False
        self.attempt_evidence_preexisted = False
        self.current_pointer_persisted = False
        self.preflight_current_pointer_state: Optional[FileState] = None
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

    def _begin_phase(self, phase: str) -> None:
        self.current_phase = phase
        self._phase_started_at = time.monotonic()

    def _finish_phase(
        self,
        status: str,
        exit_code: int = 0,
        *,
        detail: Optional[str] = None,
    ) -> None:
        duration_ms = int((time.monotonic() - self._phase_started_at) * 1000)
        record: Dict[str, Any] = {
            "name": self.current_phase,
            "status": status,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
        }
        if detail:
            record["detail"] = detail
        self.phase_results.append(record)

    def _finish_failure_phase(self, error: TransactionError) -> None:
        if (
            not self.phase_results
            or self.phase_results[-1]["name"] != self.current_phase
            or self.phase_results[-1]["status"] != "failed"
        ):
            self._finish_phase("failed", error.exit_code, detail=error.rule)

    def _ensure_log_dir(self) -> None:
        _ensure_directory_nofollow(self.root, self.log_dir)

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
            "claim_path": self.identity["claim_path"],
            "branch_ref": self.branch_ref,
            "manifest_sha256": self.manifest.get("_loaded_sha256"),
            "contract_sha256": contract_digest(self.manifest),
            "claim_preimage_sha256": self.preflight_states.get(self.identity["claim_path"], FileState(False, None, None, 0, None, None)).digest,
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
            self._ensure_log_dir()
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
            self._finish_failure_phase(err)
            self.write_transaction_journal(f"killed-by-signal-{signame}", {"error": err.rule})
            try:
                self.persist_terminal_result(self.result("failed", err))
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
        self._begin_phase("preflight")
        if self.result_path.exists() or self.result_path.is_symlink() or self.journal_path.exists() or self.journal_path.is_symlink():
            self.attempt_evidence_preexisted = True
            raise TransactionError(
                "RTX-ATTEMPT-EXISTS",
                "request ID already has retained result or journal evidence; retries require a fresh request ID",
                "preflight",
                EXIT_PREFLIGHT,
            )
        pointer = _current_pointer_status(self.root, self.identity["task_id"])
        if pointer["status"] == "invalid":
            raise TransactionError(
                "RTX-CURRENT-POINTER-INVALID",
                "Task current pointer is malformed or does not match immutable result bytes; preserve it for reconciliation",
                "preflight",
                EXIT_PREFLIGHT,
            )
        self.preflight_current_pointer_state = _read_state(self.current_pointer_path)
        self._assert_head(self.identity["expected_base"], "preflight")
        self.observed_base = self._head()
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
        self.observed_authority = {key: current_authority[key] for key in ALLOWED_AUTHORITY_KEYS}

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
            if parent.exists() and not parent.is_dir():
                raise TransactionError(
                    "RTX-OUTPUT-PARENT",
                    f"v1 requires an existing output parent directory: {relative}",
                    "preflight",
                    EXIT_PREFLIGHT,
                )
            if not parent.exists() and self.manifest["profile"] != EDITOR_PROFILE:
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

        if self.manifest["profile"] == EDITOR_PROFILE:
            self.editor_candidate = self._verify_editor_candidate()

        self.initial_index = _index_entries(self.root)
        self._snapshot_paths()
        self.write_transaction_journal("preflight-passed")
        self._finish_phase("passed")
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

    def _verify_editor_candidate(self) -> Mapping[str, Any]:
        """Recheck every legacy_task_editor (0038-05.01) candidate preimage.

        This binds the manifest's declared ``editor`` contract to the exact
        candidate/operation/read-set/member digests and rechecks them against
        the live repository, exactly as ``legacy_task_editor.py promote``
        would, without performing any write. It is called once at preflight
        and again immediately before promotion in ``materialize_editor_candidate``
        so drift between planning and publication is rejected fail-closed.
        """
        editor = self.manifest["editor"]
        candidate_manifest_path = self.root / editor["candidate_manifest_path"]
        _assert_safe_repo_path(self.root, editor["operation_path"])
        _assert_safe_repo_path(self.root, editor["candidate_dir"])
        _assert_safe_repo_path(self.root, editor["candidate_manifest_path"])
        if candidate_manifest_path.is_symlink() or not candidate_manifest_path.is_file():
            raise TransactionError(
                "RTX-EDITOR-CANDIDATE-MISSING",
                f"candidate manifest is missing or not a regular file: {editor['candidate_manifest_path']}",
                "preflight",
                EXIT_PREFLIGHT,
            )
        try:
            candidate = lte.verify_candidate_for_promotion(
                self.root,
                candidate_manifest_path,
                editor["expected_candidate_sha256"],
            )
        except lte.EditorError as exc:
            raise TransactionError(f"RTX-EDITOR-{exc.rule}", exc.message, "preflight", EXIT_PREFLIGHT) from exc
        changes = candidate["changes"]
        assert isinstance(changes, list)
        derived_paths = sorted({str(change["path"]) for change in changes})
        if derived_paths != list(self.scope["output_paths"]):
            raise TransactionError(
                "RTX-EDITOR-SCOPE-MISMATCH",
                f"declared output_paths {self.scope['output_paths']} differ from verified candidate paths {derived_paths}",
                "preflight",
                EXIT_PREFLIGHT,
            )
        operation_entry = candidate["operation"]
        assert isinstance(operation_entry, dict)
        subject = operation_entry["subject"]
        assert isinstance(subject, dict)
        if str(subject.get("task_id")) != self.identity["task_id"]:
            raise TransactionError(
                "RTX-EDITOR-SUBJECT-MISMATCH",
                f"candidate subject {subject.get('task_id')!r} does not match transaction task_id {self.identity['task_id']!r}",
                "preflight",
                EXIT_PREFLIGHT,
            )
        return candidate

    def materialize_editor_candidate(self, candidate: Path) -> None:
        """Recheck preimages immediately before publication, then write the
        verified legacy_task_editor changes into the candidate worktree so
        the existing promote/rollback/journal machinery promotes them
        atomically, exactly like any other declared output path.
        """
        self._begin_phase("execute")
        # Resolve the candidate worktree path once: it lives under the
        # platform temp root, which on macOS contains a symlink component
        # (/var -> /private/var) that the nofollow atomic-write helpers
        # correctly refuse to traverse. This mirrors Transaction.__init__'s
        # own `self.root = root.resolve()` for the real repository root.
        candidate = candidate.resolve()
        self.write_transaction_journal("materializing-editor-candidate")
        self.editor_candidate = self._verify_editor_candidate()
        self._inject("before-editor-materialize")
        editor = self.manifest["editor"]
        candidate_source_dir = self.root / editor["candidate_dir"]
        for change in self.editor_candidate["changes"]:
            assert isinstance(change, dict)
            relative = str(change["path"])
            destination = candidate / relative
            if change["action"] == "delete":
                if destination.exists() or destination.is_symlink():
                    if destination.is_symlink() or not destination.is_file():
                        raise TransactionError(
                            "RTX-EDITOR-CANDIDATE-TYPE",
                            f"editor delete target is not a regular file: {relative}",
                            "execute",
                            EXIT_ACTION,
                        )
                    destination.unlink()
                continue
            after_blob = change.get("after_blob")
            if not after_blob:
                raise TransactionError(
                    "RTX-EDITOR-CANDIDATE-SHAPE",
                    f"editor change for {relative} is missing an after blob",
                    "execute",
                    EXIT_ACTION,
                )
            blob_path = candidate_source_dir / str(after_blob)
            if blob_path.is_symlink() or not blob_path.is_file():
                raise TransactionError(
                    "RTX-EDITOR-CANDIDATE-TYPE",
                    f"editor candidate blob is not a regular file: {after_blob}",
                    "execute",
                    EXIT_ACTION,
                )
            payload = blob_path.read_bytes()
            if _sha256_bytes(payload) != change["after_sha256"] or len(payload) != change["bytes_after"]:
                raise TransactionError(
                    "RTX-EDITOR-CANDIDATE-DIGEST",
                    f"editor candidate blob digest/size differs for {relative}",
                    "execute",
                    EXIT_ACTION,
                )
            destination.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write(destination, payload)
        self._inject("after-editor-materialize")

        self._begin_phase("candidate-scope")
        allowed = set(self.scope["input_paths"]) | set(self.scope["output_paths"])
        changed = _changed_paths(candidate)
        unexpected = changed - allowed
        if unexpected:
            raise TransactionError("RTX-CANDIDATE-SCOPE", f"candidate changed undeclared paths: {sorted(unexpected)}", "validate", EXIT_SCOPE)
        if not changed:
            raise TransactionError("RTX-CANDIDATE-NOOP", "candidate has no substantive changes", "validate", EXIT_SCOPE)
        self._finish_phase("passed")
        self.emit(f"PHASE candidate-scope: PASS changed={len(changed)}")

    def run_actions(self, candidate: Path) -> None:
        self._begin_phase("execute")
        self.write_transaction_journal("running-actions")
        candidate_inputs = {relative: _read_state(candidate / relative) for relative in self.scope["input_paths"]}
        for action in self.manifest["actions"]:
            registered = ACTION_REGISTRY[action["id"]]
            self._begin_phase(registered.phase)
            stdout_path = self.log_dir / f"{registered.phase}-{registered.action_id}.stdout.log"
            stderr_path = self.log_dir / f"{registered.phase}-{registered.action_id}.stderr.log"
            self._ensure_log_dir()
            protected_paths = (
                self.scope["input_paths"]
                if registered.phase == "generate"
                else self.scope["substantive_paths"]
            )
            protected_before = {
                relative: _read_state(candidate / relative) for relative in protected_paths
            }
            start_ms = time.monotonic()
            try:
                with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
                    completed = _run_process(
                        registered.argv,
                        candidate,
                        timeout=action["timeout_seconds"],
                        stdout_handle=stdout_handle,
                        stderr_handle=stderr_handle,
                    )
            except TransactionError as exc:
                duration_ms = int((time.monotonic() - start_ms) * 1000)
                status = "timed_out" if exc.rule == "RTX-ACTION-TIMEOUT" else "failed"
                self.action_results.append(
                    ActionResult(
                        action_id=registered.action_id,
                        phase=registered.phase,
                        status=status,
                        exit_code=None,
                        duration_ms=duration_ms,
                        stdout_path=stdout_path.relative_to(self.root).as_posix(),
                        stderr_path=stderr_path.relative_to(self.root).as_posix(),
                        reports=[],
                    )
                )
                self._finish_phase(status, exc.exit_code, detail=exc.rule)
                raise
            duration_ms = int((time.monotonic() - start_ms) * 1000)
            result = ActionResult(
                action_id=registered.action_id,
                phase=registered.phase,
                status="passed" if completed.returncode == 0 else "failed",
                exit_code=completed.returncode,
                duration_ms=duration_ms,
                stdout_path=stdout_path.relative_to(self.root).as_posix(),
                stderr_path=stderr_path.relative_to(self.root).as_posix(),
                reports=[],
            )
            self.action_results.append(result)
            if completed.returncode != 0:
                self._finish_phase("failed", completed.returncode, detail="RTX-ACTION-NONZERO")
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
            self._finish_phase("passed")
            self.emit(f"PHASE {registered.phase}:{registered.action_id}: PASS exit=0")
            self._inject(f"after-action:{registered.action_id}")

        self._begin_phase("candidate-scope")
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
        self._finish_phase("passed")
        self.emit(f"PHASE candidate-scope: PASS changed={len(changed)}")

    def promote_outputs(self, candidate: Path) -> None:
        self._begin_phase("promote")
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
                    if self.manifest["profile"] == EDITOR_PROFILE and not destination.parent.exists():
                        _ensure_directory_nofollow(self.root, destination.parent)
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
        self._finish_phase("passed")
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

            # --no-renames: a delete plus a byte-identical create (e.g. an
            # editor-candidate claim finalization archiving a claim file
            # verbatim) is otherwise collapsed by git's rename heuristic
            # into a single R100 entry, silently dropping one declared path
            # from `changed` and triggering a spurious scope mismatch below.
            changed = _git_paths(self.root, ["diff", "--cached", "--no-renames", "--name-only", "-z", parent, "--"], env=env)
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
        self._begin_phase("prepare-substantive")
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
        self._finish_phase("passed")
        self.emit(f"PHASE prepare-substantive: PASS commit={self.substantive_commit}")

    def prepare_bookkeeping(self) -> None:
        if not self.substantive_commit:
            raise TransactionError("RTX-BOOKKEEPING-REF", "substantive commit is unavailable", "bookkeeping", EXIT_BOOKKEEPING)
        self._begin_phase("prepare-bookkeeping")
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
        self._finish_phase("passed")
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
        self._begin_phase("validate-bookkeeping")
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
        self._finish_phase("passed")
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
        self._begin_phase("publish")
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
        self._finish_phase("passed")
        self.emit(f"PHASE publish: PASS branch={self.branch_ref} commit={final_commit}")

    def verify_published(self) -> None:
        self._begin_phase("verify")
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
        self._finish_phase("passed")
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
        self._begin_phase("finalize-claim")
        self._assert_paths_unchanged({self.identity["claim_path"]}, self.current_phase)
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
            self.write_transaction_journal("claim-finalized")
            self._finish_phase("passed")
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
        if verdict not in TERMINAL_RESULT_VERDICTS and verdict != "prepared":
            raise TransactionError("RTX-RESULT-VERDICT", f"unsupported result verdict: {verdict}", "result", EXIT_INTERNAL)
        findings: List[Dict[str, Any]] = []
        if error:
            findings.append({"rule": error.rule, "message": error.message, "exit_code": error.exit_code})
        value: Dict[str, Any] = {
            "schema": RESULT_SCHEMA,
            "task_id": self.identity["task_id"],
            "request_id": self.identity["request_id"],
            "owner_token": self.identity["owner_token"],
            "expected_base": self.identity["expected_base"],
            "base_observed": self.observed_base,
            "authority_observed": self.observed_authority,
            "manifest_path": self.identity["manifest_path"],
            "manifest_sha256": self.manifest.get("_loaded_sha256"),
            "contract_sha256": contract_digest(self.manifest),
            "started_at": self.started_at,
            "finished_at": _utc_now(),
            "verdict": verdict,
            "lifecycle_state": "complete" if verdict == "passed" else ("failed" if verdict == "failed" else "prepared"),
            "phase": self.current_phase,
            "phases": list(self.phase_results),
            "actions": [
                {
                    "id": item.action_id,
                    "phase": item.phase,
                    "status": item.status,
                    "exit_code": item.exit_code,
                    "duration_ms": item.duration_ms,
                    "stdout": item.stdout_path,
                    "stderr": item.stderr_path,
                    "reports": item.reports,
                }
                for item in self.action_results
            ],
            "findings": findings,
            "substantive_commit": self.substantive_commit,
            "bookkeeping_commit": self.bookkeeping_commit,
            "published": self.published,
            "claim_finalized": self.claim_finalized,
            "paths": {
                "counts": {
                    "read": len(self.scope["read_paths"]),
                    "input": len(self.scope["input_paths"]),
                    "output": len(self.scope["output_paths"]),
                    "substantive": len(self.scope["substantive_paths"]),
                },
                "preflight": {relative: _state_dict(state) for relative, state in sorted(self.preflight_states.items())},
                "promoted": {relative: _state_dict(state) for relative, state in sorted(self.promoted_states.items())},
            },
            "commits": {
                "substantive": self.substantive_commit,
                "bookkeeping": self.bookkeeping_commit,
                "final": self.final_commit,
            },
            "cleanup": {
                "claim_finalized": self.claim_finalized,
                "promotion_backups_retained": bool(self.promotion_journal),
                "journal_state": "complete" if verdict == "passed" else "failed",
            },
            "evidence": {
                "journal": self.journal_path.relative_to(self.root).as_posix(),
                "prepared_result": (self.log_dir / "prepared-result.json").relative_to(self.root).as_posix(),
                "promotion_journal": (self.log_dir / "promotion-journal.json").relative_to(self.root).as_posix(),
            },
            "changed_path_count": len(self.scope["substantive_paths"]),
            "promotion_backups_retained": bool(self.promotion_journal),
        }
        if error:
            value["error"] = findings[0]
            value["recovery"] = (
                "Claim retained unless the journal says claim_finalized. Inspect the digest-bound current pointer, "
                "journal, and exact phase logs; use a fresh request ID for a retry."
            )
        else:
            value["error"] = None
            value["recovery"] = "none"
        return value

    def write_result(self, value: Dict[str, Any], *, path: Optional[Path] = None) -> bytes:
        if self.dry_run:
            return b""
        destination = path or self.result_path
        relative_destination = destination.relative_to(self.root).as_posix()
        _assert_safe_repo_path(self.root, relative_destination, "result")
        if destination == self.result_path and (destination.exists() or destination.is_symlink()):
            raise TransactionError(
                "RTX-RESULT-IMMUTABLE",
                f"immutable attempt result already exists at {relative_destination}",
                "result",
                EXIT_INTERNAL,
            )
        payload = _json_bytes(value)
        try:
            self._ensure_log_dir()
            if destination == self.result_path:
                _atomic_create(destination, payload, 0o600)
            else:
                _atomic_write(destination, payload, 0o600)
        except OSError as exc:
            raise TransactionError(
                "RTX-RESULT-WRITE",
                f"cannot persist structured result at {destination}: {exc}",
                "result",
                EXIT_INTERNAL,
            ) from exc
        if destination == self.result_path:
            self.terminal_result_persisted = True
        return payload

    def write_current_pointer(self, result_payload: bytes, value: Dict[str, Any]) -> None:
        result_relative = self.result_path.relative_to(self.root).as_posix()
        pointer_relative = self.current_pointer_path.relative_to(self.root).as_posix()
        _assert_safe_repo_path(self.root, pointer_relative, "current-pointer")
        if self.current_pointer_path.exists() and not self.current_pointer_path.is_file():
            raise TransactionError(
                "RTX-CURRENT-POINTER-TYPE",
                f"current pointer is not a regular file: {pointer_relative}",
                "current-pointer",
                EXIT_INTERNAL,
            )
        pointer = {
            "schema": CURRENT_POINTER_SCHEMA,
            "task_id": self.identity["task_id"],
            "request_id": self.identity["request_id"],
            "result_path": result_relative,
            "result_sha256": _sha256_bytes(result_payload),
            "verdict": value["verdict"],
            "lifecycle_state": value["lifecycle_state"],
            "updated_at": _utc_now(),
        }
        if self.preflight_current_pointer_state is not None:
            current_state = _read_state(self.current_pointer_path)
            if current_state != self.preflight_current_pointer_state:
                raise TransactionError(
                    "RTX-CURRENT-POINTER-DRIFT",
                    "current pointer changed after preflight; refusing to overwrite it",
                    "current-pointer",
                    EXIT_INTERNAL,
                )
        try:
            self._ensure_log_dir()
            _atomic_write(self.current_pointer_path, _json_bytes(pointer), 0o600)
        except OSError as exc:
            raise TransactionError(
                "RTX-CURRENT-POINTER-WRITE",
                f"cannot atomically update current pointer at {pointer_relative}: {exc}",
                "current-pointer",
                EXIT_INTERNAL,
            ) from exc
        self.current_pointer_persisted = True

    def persist_terminal_result(self, value: Dict[str, Any]) -> None:
        if value["verdict"] not in TERMINAL_RESULT_VERDICTS:
            raise TransactionError("RTX-RESULT-VERDICT", "only terminal results can become current", "result", EXIT_INTERNAL)
        self.write_transaction_journal("writing-terminal-result")
        payload = self.write_result(value)
        result_relative = self.result_path.relative_to(self.root).as_posix()
        pointer_relative = self.current_pointer_path.relative_to(self.root).as_posix()
        self.write_transaction_journal(
            "result-persisted",
            {"result_path": result_relative, "result_sha256": _sha256_bytes(payload), "current_pointer_path": pointer_relative},
        )
        self._inject("after-result-write")
        self._inject("before-current-pointer")
        self.write_current_pointer(payload, value)
        self._inject("after-current-pointer")
        self.write_transaction_journal(
            "complete",
            {"result_path": result_relative, "result_sha256": _sha256_bytes(payload), "current_pointer_path": pointer_relative},
        )

    def _may_persist_terminal_result(self) -> bool:
        """Only write attempt evidence while this transaction owns an unused request ID."""
        return self.lock_path is not None and not self.attempt_evidence_preexisted

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
                if self.manifest["profile"] == EDITOR_PROFILE:
                    self.materialize_editor_candidate(candidate)
                else:
                    self.run_actions(candidate)
                self.promote_outputs(candidate)
            self.prepare_substantive()
            if self.manifest.get("bookkeeping"):
                self.prepare_bookkeeping()
                self.validate_prepared_bookkeeping()
            self.publish()
            self.verify_published()
            self.finalize_claim()
            self._begin_phase("complete")
            self._finish_phase("passed")
            self.persist_terminal_result(self.result("passed"))
            self.emit(
                "FINAL: PASS exit=0 "
                f"substantive={self.substantive_commit or 'none'} "
                f"bookkeeping={self.bookkeeping_commit or 'none'} result={self.result_path.relative_to(self.root)}"
            )
            return 0
        except TransactionError as exc:
            exc = self._rollback_or_compound(exc)
            if self.claim_finalized and not self.terminal_result_persisted:
                archive = self.log_dir / "finalized-claim.md"
                expected_claim = self.preflight_states.get(self.identity["claim_path"])
                try:
                    if expected_claim is None:
                        raise TransactionError("RTX-CLAIM-STATE", "claim preimage is unavailable", "finalize-claim", EXIT_BOOKKEEPING)
                    self._recover_claim_move(archive, expected_claim)
                    self.claim_finalized = False
                    self.claim_archive = None
                    self.write_transaction_journal("claim-restored-after-result-write-failure", {"error": exc.rule})
                except Exception as recovery_error:
                    message = recovery_error.message if isinstance(recovery_error, TransactionError) else f"{type(recovery_error).__name__}: {recovery_error}"
                    exc = TransactionError(
                        "RTX-RESULT-WRITE-CLAIM-RECOVERY",
                        f"terminal result persistence failed ({exc.rule}); claim recovery failed: {message}",
                        "finalize-claim",
                        EXIT_BOOKKEEPING,
                    )
                else:
                    exc = TransactionError(
                        "RTX-RESULT-WRITE-CLAIM-RESTORED",
                        f"terminal result persistence failed ({exc.rule}); claim restored for deterministic recovery",
                        "finalize-claim",
                        EXIT_BOOKKEEPING,
                    )
            self.current_phase = exc.phase
            self._finish_failure_phase(exc)
            if self._may_persist_terminal_result() and not self.terminal_result_persisted:
                try:
                    self.persist_terminal_result(self.result("failed", exc))
                except TransactionError as result_exc:
                    print(f"RESULT-WRITE-ERROR: {result_exc.message}", file=sys.stderr)
            elif self._may_persist_terminal_result():
                state = "complete" if self.current_pointer_persisted else "result-persisted-pointer-pending"
                try:
                    self.write_transaction_journal(state, {"error": exc.rule})
                except TransactionError as journal_exc:
                    print(f"RESULT-JOURNAL-ERROR: {journal_exc.message}", file=sys.stderr)
            self.emit(f"FINAL: FAIL exit={exc.exit_code} rule={exc.rule} phase={exc.phase} result={self.result_path.relative_to(self.root)}")
            return exc.exit_code
        except Exception as exc:
            wrapped = TransactionError("RTX-INTERNAL", f"unexpected error: {type(exc).__name__}: {exc}", self.current_phase, EXIT_INTERNAL)
            wrapped = self._rollback_or_compound(wrapped)
            self._finish_failure_phase(wrapped)
            if self._may_persist_terminal_result() and not self.terminal_result_persisted:
                try:
                    self.persist_terminal_result(self.result("failed", wrapped))
                except TransactionError as result_exc:
                    print(f"RESULT-WRITE-ERROR: {result_exc.message}", file=sys.stderr)
            elif self._may_persist_terminal_result():
                state = "complete" if self.current_pointer_persisted else "result-persisted-pointer-pending"
                try:
                    self.write_transaction_journal(state, {"error": wrapped.rule})
                except TransactionError as journal_exc:
                    print(f"RESULT-JOURNAL-ERROR: {journal_exc.message}", file=sys.stderr)
            self.emit(f"FINAL: FAIL exit={EXIT_INTERNAL} rule=RTX-INTERNAL phase={self.current_phase} result={self.result_path.relative_to(self.root)}")
            return EXIT_INTERNAL
        finally:
            if self.promotion_backup_root is not None and not self.promotion_journal:
                shutil.rmtree(self.promotion_backup_root, ignore_errors=True)
                self.promotion_backup_root = None
            self.release_lock()


class BranchMergeTransaction(Transaction):
    """Typed `base-branch` / `merge-prereqs` actions for the legacy runner bridge.

    Implements ``docs/pipeline/branch-merge-actions.md`` (Task ``0038-19``) on top of
    the ``0038-02`` lock/journal/signal/resume guarantees and the ``0038-18``
    validation/commit profile machinery. It performs only merges whose destination
    is the item's own branch, so it never crosses an integration checkpoint.
    """

    def __init__(
        self,
        root: Path,
        manifest: Dict[str, Any],
        *,
        dry_run: bool = False,
        inject_failure: Optional[str] = None,
    ) -> None:
        super().__init__(root, manifest, dry_run=dry_run, inject_failure=inject_failure)
        self.branch = manifest["branch"]
        self.typed_action: str = self.branch["typed_action"]
        self.item_id: str = self.branch["item_id"]
        self.target_ref = f"refs/heads/{self.branch['target_branch']}"
        self.preflight_entries: List[str] = []
        self.merge_steps: List[Dict[str, str]] = []
        self.claim_unions: List[str] = []
        self.branch_outputs: List[str] = []
        self.final_branch_tip: Optional[str] = None
        self.branch_ref_created = False
        self.worktree_synchronized = False
        self.claim_record_appended = False
        self._git_identity: Tuple[str, str] = ("", "")

    # ------------------------------------------------------------------ scope

    @property
    def mutable_paths(self) -> Set[str]:
        return set(self.scope["substantive_paths"]) | {self.identity["claim_path"]}

    def _snapshot_paths(self) -> None:
        super()._snapshot_paths()
        for relative in sorted(set(self.scope["substantive_paths"])):
            if relative not in self.preflight_states:
                self.preflight_states[relative] = _read_state(self.root / relative)

    def write_transaction_journal(self, state: str, extra: Optional[Dict[str, Any]] = None) -> None:
        payload: Dict[str, Any] = {
            "typed_action": self.typed_action,
            "item_id": self.item_id,
            "target_ref": self.target_ref,
            "idempotence_key": self.branch["idempotence_key"],
            "capability_class": self.branch["capability_class"],
            "declared_sources": [
                f"refs/heads/{source['branch']}@{source['tip']}" for source in self.branch["sources"]
            ],
            "merged_tips": list(self.branch_outputs),
            "final_branch_tip": self.final_branch_tip,
            "claim_unions": list(self.claim_unions),
            "worktree_synchronized": self.worktree_synchronized,
        }
        if extra:
            payload.update(extra)
        super().write_transaction_journal(state, payload)

    # -------------------------------------------------------------- preflight

    def preflight(self) -> None:
        super().preflight()
        self._branch_preflight()

    def _resolve_ref(self, ref: str) -> Optional[str]:
        completed = _git(self.root, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], check=False)
        if completed.returncode != 0:
            return None
        return completed.stdout.decode("ascii", "strict").strip() or None

    def _branch_preflight(self) -> None:
        self._begin_phase("branch-preflight")
        entries = [
            f"target-branch:{self.target_ref}",
            f"owner-token-matches-claim:{self.identity['owner_token']}",
            f"idempotence-key:{self.branch['idempotence_key']}",
            f"capability-class:{self.branch['capability_class']}",
        ]
        user_name = _git_text(self.root, ["config", "--get", "user.name"])
        user_email = _git_text(self.root, ["config", "--get", "user.email"])
        self._git_identity = (user_name, user_email)

        if self.typed_action == TYPED_ACTION_BASE_BRANCH:
            parent_branch = self.branch["parent_branch"]
            parent_ref = f"refs/heads/{parent_branch}"
            parent_tip = self._resolve_ref(parent_ref)
            if parent_tip is None:
                raise TransactionError(
                    "BMA-PARENT-BRANCH-MISSING",
                    f"parent branch does not exist: {parent_ref}",
                    "branch-preflight",
                    EXIT_BRANCH,
                )
            if parent_tip != self.identity["expected_base"]:
                raise TransactionError(
                    "BMA-STALE-BASE",
                    f"expected parent tip {self.identity['expected_base']} at {parent_ref}, observed {parent_tip}",
                    "branch-preflight",
                    EXIT_BRANCH,
                )
            existing = self._resolve_ref(self.target_ref)
            if existing is not None and existing != self.identity["expected_base"]:
                raise TransactionError(
                    "BMA-BRANCH-EXISTS",
                    f"{self.target_ref} already exists at {existing} and is not the declared base "
                    f"{self.identity['expected_base']}; never fast-forward another writer's branch",
                    "branch-preflight",
                    EXIT_BRANCH,
                )
            entries.extend(
                [
                    f"parent-branch-exists:{parent_branch}",
                    f"expected-parent-tip:{parent_ref}@{self.identity['expected_base']}",
                    f"item-branch-absent-or-fast-forwardable:{self.target_ref}",
                ]
            )
        else:
            if not user_name or not user_email:
                raise TransactionError(
                    "RTX-GIT-IDENTITY",
                    "Git user.name and user.email are required to author merge commits",
                    "branch-preflight",
                    EXIT_BRANCH,
                )
            checked_out = _git_text(self.root, ["symbolic-ref", "--quiet", "HEAD"])
            if checked_out != self.target_ref:
                raise TransactionError(
                    "BMA-TARGET-NOT-CHECKED-OUT",
                    f"merge-prereqs advances the checked-out item branch; HEAD is {checked_out!r}, "
                    f"declared target is {self.target_ref!r}",
                    "branch-preflight",
                    EXIT_BRANCH,
                )
            for source in self.branch["sources"]:
                source_ref = f"refs/heads/{source['branch']}"
                observed = self._resolve_ref(source_ref)
                if observed is None:
                    raise TransactionError(
                        "BMA-UNDECLARED-SOURCE",
                        f"declared prerequisite branch does not exist: {source_ref}",
                        "branch-preflight",
                        EXIT_BRANCH,
                    )
                if observed != source["tip"]:
                    raise TransactionError(
                        "BMA-STALE-SOURCE-TIP",
                        f"expected {source_ref}@{source['tip']}, observed {observed}",
                        "branch-preflight",
                        EXIT_BRANCH,
                    )
                entries.append(f"expected-source-tip:{source_ref}@{source['tip']}")
            entries.append("claim-union-no-foreign-rewrite")
            dirty = _changed_paths(self.root) & set(self.scope["substantive_paths"])
            if dirty:
                raise TransactionError(
                    "BMA-WORKTREE-DIRTY",
                    f"declared merge paths carry uncommitted work: {sorted(dirty)}",
                    "branch-preflight",
                    EXIT_BRANCH,
                )

        self.preflight_entries = entries
        self.write_transaction_journal("branch-preflight-passed", {"preflight_entries": entries})
        self._finish_phase("passed")
        self.emit(f"PHASE branch-preflight: PASS action={self.typed_action} target={self.target_ref}")

    # ----------------------------------------------------------- base-branch

    def run_base_branch(self) -> None:
        self._begin_phase("base-branch")
        expected = self.identity["expected_base"]
        existing = self._resolve_ref(self.target_ref)
        if existing == expected:
            # Idempotent replay of an already-created identical ref.
            self.emit(f"NOTICE: {self.target_ref} already points at the declared base; no ref change required.")
        else:
            self.write_transaction_journal("branch-creating")
            self._inject("before-branch-cas")
            completed = _git(
                self.root,
                ["update-ref", "--create-reflog", self.target_ref, expected, ""],
                check=False,
            )
            if completed.returncode != 0:
                raise TransactionError(
                    "BMA-BRANCH-CAS-LOST",
                    f"{self.target_ref} was created concurrently; refusing to overwrite it",
                    "base-branch",
                    EXIT_BRANCH,
                )
            self.branch_ref_created = True
        observed = self._resolve_ref(self.target_ref)
        if observed != expected:
            raise TransactionError(
                "BMA-BRANCH-VERIFY",
                f"{self.target_ref} is {observed!r} after creation, expected {expected}",
                "base-branch",
                EXIT_BRANCH,
            )
        if _git_text(self.root, ["rev-parse", f"{self.target_ref}^{{tree}}"]) != _git_text(
            self.root, ["rev-parse", f"{expected}^{{tree}}"]
        ):
            raise TransactionError(
                "BMA-BRANCH-VERIFY",
                "base-branch must produce a tree identical to its parent tip",
                "base-branch",
                EXIT_BRANCH,
            )
        self.final_branch_tip = expected
        self.published = True
        self.branch_outputs = [f"ref:{self.target_ref}@{expected}"]
        self.write_transaction_journal("branch-published")
        self._inject("after-branch-publish")
        self._finish_phase("passed")
        self.emit(f"PHASE base-branch: PASS ref={self.target_ref} tip={expected}")

    # --------------------------------------------------------- merge-prereqs

    @contextlib.contextmanager
    def _merge_worktree(self) -> Iterator[Path]:
        temporary = Path(tempfile.mkdtemp(prefix=f"autodocs-merge-{self.identity['request_id']}-"))
        added = False
        try:
            _git(self.root, ["worktree", "add", "--detach", str(temporary), self.identity["expected_base"]])
            added = True
            yield temporary
        finally:
            if added:
                _git(self.root, ["worktree", "remove", "--force", str(temporary)], check=False)
            shutil.rmtree(temporary, ignore_errors=True)

    def _merge_message(self, source: Mapping[str, str]) -> str:
        return (
            f"merge({self.item_id}): integrate prerequisite {source['dependency']}\n"
            "\n"
            f"Typed-Action: {TYPED_ACTION_MERGE_PREREQS}\n"
            f"Idempotence-Key: {self.branch['idempotence_key']}\n"
            f"Owner-Token: {self.identity['owner_token']}\n"
            f"Merged-Branch-Tip: refs/heads/{source['branch']}@{source['tip']}\n"
            "Contract: docs/pipeline/branch-merge-actions.md\n"
        )

    def _merge_git(self, work: Path, args: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        name, email = self._git_identity
        prefix = [
            "-c",
            "commit.gpgsign=false",
            "-c",
            "merge.autoStash=false",
            "-c",
            f"user.name={name}",
            "-c",
            f"user.email={email}",
        ]
        return _git(work, [*prefix, *args], check=check)

    @staticmethod
    def _owner_token(text: str) -> Optional[str]:
        match = CLAIM_OWNER_TOKEN_LINE_RE.search(text)
        return match.group(1).strip() if match else None

    @staticmethod
    def _append_only_union(destination: str, source: str) -> str:
        """Append every source line absent from the destination, order preserved."""
        destination_lines = destination.splitlines()
        present = set(destination_lines)
        appended = [line for line in source.splitlines() if line not in present]
        if not appended:
            return destination
        merged = list(destination_lines)
        if merged and merged[-1].strip():
            merged.append("")
        merged.extend(appended)
        return "\n".join(merged) + "\n"

    def _stage_blob(self, work: Path, stage: int, relative: str) -> Optional[bytes]:
        completed = _git(work, ["show", f":{stage}:{relative}"], check=False)
        if completed.returncode != 0:
            return None
        return completed.stdout

    def _resolve_claim_conflicts(self, work: Path, conflicts: Sequence[str]) -> None:
        """Append-only auto-union of same-token claim records (contract §5)."""
        for relative in sorted(conflicts):
            ours = self._stage_blob(work, 2, relative)
            theirs = self._stage_blob(work, 3, relative)
            if ours is None or theirs is None:
                raise TransactionError(
                    "BMA-MERGE-CONFLICT",
                    f"claim conflict at {relative} is not a same-path append conflict; resolve it manually",
                    "merge-prereqs",
                    EXIT_BRANCH,
                )
            try:
                ours_text = ours.decode("utf-8")
                theirs_text = theirs.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise TransactionError(
                    "BMA-CLAIM-UTF8",
                    f"claim record is not valid UTF-8 and cannot be unioned: {relative}",
                    "merge-prereqs",
                    EXIT_BRANCH,
                ) from exc
            ours_token = self._owner_token(ours_text)
            theirs_token = self._owner_token(theirs_text)
            if ours_token is None or theirs_token is None or ours_token != theirs_token:
                raise TransactionError(
                    "BMA-CLAIM-FOREIGN-TOKEN",
                    f"claim {relative} carries different owner tokens ({ours_token!r} vs {theirs_token!r}); "
                    "never rewrite, rename, or discard another session's claim",
                    "merge-prereqs",
                    EXIT_BRANCH,
                )
            unioned = self._append_only_union(ours_text, theirs_text)
            if self._owner_token(unioned) != ours_token:  # pragma: no cover - defensive
                raise TransactionError(
                    "BMA-CLAIM-FOREIGN-TOKEN",
                    f"auto-union altered the owner_token of {relative}",
                    "merge-prereqs",
                    EXIT_BRANCH,
                )
            (work / relative).write_text(unioned, encoding="utf-8")
            _git(work, ["add", "--", relative])
            self.claim_unions.append(f"claim-union:{relative}")

    def _merge_one(self, work: Path, current_tip: str, source: Mapping[str, str]) -> str:
        self._merge_git(work, ["checkout", "--detach", "--force", current_tip])
        self._merge_git(work, ["clean", "-fdq"], check=False)
        message = self._merge_message(source)
        completed = self._merge_git(
            work,
            ["merge", "--no-ff", "--no-edit", "-m", message, source["tip"]],
            check=False,
        )
        if completed.returncode != 0:
            conflicts = sorted(_git_paths(work, ["diff", "--name-only", "--diff-filter=U", "-z"]))
            claim_conflicts = [item for item in conflicts if CLAIM_FILENAME_RE.search(item)]
            if not conflicts or len(claim_conflicts) != len(conflicts):
                self._merge_git(work, ["merge", "--abort"], check=False)
                detail = sorted(conflicts) if conflicts else "unknown"
                raise TransactionError(
                    "BMA-MERGE-CONFLICT",
                    f"merging refs/heads/{source['branch']} conflicts on {detail}; resolve manually "
                    "under a fresh request; no partial merge is published",
                    "merge-prereqs",
                    EXIT_BRANCH,
                )
            try:
                self._resolve_claim_conflicts(work, claim_conflicts)
            except TransactionError:
                self._merge_git(work, ["merge", "--abort"], check=False)
                raise
            self._merge_git(work, ["commit", "--no-edit", "-m", message])

        tip = _git_text(work, ["rev-parse", "HEAD"])
        parents = _git_text(work, ["rev-list", "--parents", "-n", "1", tip]).split()
        if len(parents) != 3:
            raise TransactionError(
                "BMA-MERGE-PARENTS",
                f"merge step produced {len(parents) - 1} parents; only sequential 2-parent merges are allowed",
                "merge-prereqs",
                EXIT_BRANCH,
            )
        if parents[1] != current_tip or parents[2] != source["tip"]:
            raise TransactionError(
                "BMA-MERGE-PARENTS",
                f"merge step parents {parents[1:]} do not match ({current_tip}, {source['tip']})",
                "merge-prereqs",
                EXIT_BRANCH,
            )
        self.merge_steps.append(
            {
                "dependency": source["dependency"],
                "source_ref": f"refs/heads/{source['branch']}",
                "source_tip": source["tip"],
                "merge_commit": tip,
                "first_parent": current_tip,
            }
        )
        self.branch_outputs.extend(
            [f"merged-branch-tip:refs/heads/{source['branch']}@{source['tip']}", f"merge-commit:{tip}"]
        )
        self.emit(f"PHASE merge-step: PASS source=refs/heads/{source['branch']} commit={tip}")
        return tip

    def run_merge_prereqs(self) -> None:
        self._begin_phase("merge-prereqs")
        self.write_transaction_journal("merging-prereqs")
        expected = self.identity["expected_base"]
        declared = set(self.scope["substantive_paths"])
        with self._merge_worktree() as work:
            current = expected
            for source in self.branch["sources"]:
                current = self._merge_one(work, current, source)
            final_tip = current
        if final_tip == expected:  # pragma: no cover - defensive
            raise TransactionError("BMA-MERGE-NOOP", "merge produced no new commit", "merge-prereqs", EXIT_BRANCH)
        changed = _git_paths(self.root, ["diff", "--name-only", "-z", expected, final_tip, "--"])
        if changed != declared:
            raise TransactionError(
                "BMA-SCOPE-VIOLATION",
                f"merge changed {sorted(changed)} but the request declared {sorted(declared)}",
                "merge-prereqs",
                EXIT_BRANCH,
            )
        self.final_branch_tip = final_tip
        self.substantive_commit = final_tip
        self.write_transaction_journal(
            "merge-prepared", {"merge_steps": list(self.merge_steps), "final_branch_tip": final_tip}
        )
        self._inject("before-branch-cas")
        self.write_transaction_journal("attempting-branch-cas")
        completed = _git(self.root, ["update-ref", self.target_ref, final_tip, expected], check=False)
        if completed.returncode != 0:
            raise TransactionError(
                "BMA-CAS-LOST",
                f"{self.target_ref} advanced past {expected} while merging; no merge was published",
                "merge-prereqs",
                EXIT_BRANCH,
            )
        self.published = True
        self.write_transaction_journal("branch-published")
        self._inject("after-branch-publish")
        self._synchronize_worktree(final_tip, sorted(declared))
        self._finish_phase("passed")
        self.emit(
            f"PHASE merge-prereqs: PASS ref={self.target_ref} tip={final_tip} "
            f"sources={len(self.merge_steps)} unions={len(self.claim_unions)}"
        )

    def _synchronize_worktree(self, commit: str, paths: Sequence[str]) -> None:
        """Materialize exactly the declared merged paths, preserving unrelated bytes."""
        for relative in paths:
            entry = _git_text(self.root, ["ls-tree", commit, "--", relative])
            destination = self.root / relative
            match = re.fullmatch(r"([0-9]{6}) blob ([0-9a-f]{40})\t(.+)", entry)
            if not match:
                with contextlib.suppress(FileNotFoundError):
                    destination.unlink()
                continue
            _ensure_directory_nofollow(self.root, destination.parent)
            blob = _git(self.root, ["cat-file", "blob", match.group(2)]).stdout
            mode = 0o755 if match.group(1) == "100755" else 0o644
            _atomic_write(destination, blob, mode)
        self._restore_mutable_index_entries()
        self.worktree_synchronized = True
        self.write_transaction_journal("worktree-synchronized")

    # ------------------------------------------------------ claim + evidence

    def record_merged_tips_in_claim(self) -> None:
        """Append-only merged-tip evidence in the item's own active claim."""
        if self.typed_action != TYPED_ACTION_MERGE_PREREQS or not self.merge_steps:
            return
        self._begin_phase("claim-record")
        claim = self.claim_path
        if not claim.exists():
            raise TransactionError(
                "BMA-CLAIM-MISSING",
                f"active claim disappeared before merged-tip recording: {claim}",
                "claim-record",
                EXIT_BRANCH,
            )
        existing = claim.read_text(encoding="utf-8")
        lines = [
            "",
            f"### Merged prerequisite branches ({self.branch['idempotence_key']})",
            "",
            f"- target: {self.target_ref}@{self.final_branch_tip}",
        ]
        for step in self.merge_steps:
            lines.append(
                f"- merged: {step['source_ref']}@{step['source_tip']} -> merge-commit {step['merge_commit']}"
            )
        for union in self.claim_unions:
            lines.append(f"- {union}")
        lines.append("")
        addition = "\n".join(lines)
        payload = (existing if existing.endswith("\n") else existing + "\n") + addition
        _atomic_write(claim, payload.encode("utf-8"), stat.S_IMODE(claim.stat().st_mode))
        self.claim_record_appended = True
        self.write_transaction_journal("claim-record-appended")
        self._finish_phase("passed")
        self.emit(f"PHASE claim-record: PASS entries={len(self.merge_steps)}")

    def result(self, verdict: str, error: Optional[TransactionError] = None) -> Dict[str, Any]:
        value = super().result(verdict, error)
        findings = [union for union in self.claim_unions]
        if error:
            findings.append(error.rule)
        value["branch"] = {
            "typed_action": self.typed_action,
            "item_id": self.item_id,
            "target_ref": self.target_ref,
            "capability_class": self.branch["capability_class"],
            "idempotence_key": self.branch["idempotence_key"],
            "preflight": list(self.preflight_entries),
            "declared_sources": [
                f"refs/heads/{source['branch']}@{source['tip']}" for source in self.branch["sources"]
            ],
            "outputs": list(self.branch_outputs),
            "findings": findings,
            "merge_steps": list(self.merge_steps),
            "final_branch_tip": self.final_branch_tip,
            "branch_ref_created": self.branch_ref_created,
            "worktree_synchronized": self.worktree_synchronized,
            "claim_record_appended": self.claim_record_appended,
        }
        for union in self.claim_unions:
            value["findings"].append({"rule": "BMA-CLAIM-UNION", "message": union, "exit_code": 0})
        value["changed_path_count"] = len(self.scope["substantive_paths"])
        return value

    # ----------------------------------------------------------------- driver

    def execute(self) -> int:
        if self.dry_run:
            self.preflight()
            self.emit(
                f"FINAL: PASS dry-run=true mutation=none action={self.typed_action} "
                f"target={self.target_ref} sources={len(self.branch['sources'])}"
            )
            return 0
        try:
            self.acquire_lock()
            self.preflight()
            if self.typed_action == TYPED_ACTION_BASE_BRANCH:
                self.run_base_branch()
            else:
                self.run_merge_prereqs()
            self.record_merged_tips_in_claim()
            self._begin_phase("complete")
            self._finish_phase("passed")
            self.persist_terminal_result(self.result("passed"))
            self.emit(
                f"FINAL: PASS exit=0 action={self.typed_action} ref={self.target_ref} "
                f"tip={self.final_branch_tip or 'none'} result={self.result_path.relative_to(self.root)}"
            )
            return 0
        except TransactionError as exc:
            self.current_phase = exc.phase
            self._finish_failure_phase(exc)
            if self._may_persist_terminal_result() and not self.terminal_result_persisted:
                try:
                    self.persist_terminal_result(self.result("failed", exc))
                except TransactionError as result_exc:
                    print(f"RESULT-WRITE-ERROR: {result_exc.message}", file=sys.stderr)
            self.emit(
                f"FINAL: FAIL exit={exc.exit_code} rule={exc.rule} phase={exc.phase} "
                f"result={self.result_path.relative_to(self.root)}"
            )
            return exc.exit_code
        except Exception as exc:
            wrapped = TransactionError(
                "RTX-INTERNAL", f"unexpected error: {type(exc).__name__}: {exc}", self.current_phase, EXIT_INTERNAL
            )
            self._finish_failure_phase(wrapped)
            if self._may_persist_terminal_result() and not self.terminal_result_persisted:
                try:
                    self.persist_terminal_result(self.result("failed", wrapped))
                except TransactionError as result_exc:
                    print(f"RESULT-WRITE-ERROR: {result_exc.message}", file=sys.stderr)
            self.emit(
                f"FINAL: FAIL exit={EXIT_INTERNAL} rule=RTX-INTERNAL phase={self.current_phase} "
                f"result={self.result_path.relative_to(self.root)}"
            )
            return EXIT_INTERNAL
        finally:
            self.release_lock()


def build_transaction(
    root: Path,
    manifest: Dict[str, Any],
    *,
    dry_run: bool = False,
    inject_failure: Optional[str] = None,
) -> Transaction:
    """Select the transaction implementation declared by the manifest profile."""
    if manifest["profile"] == BRANCH_MERGE_PROFILE:
        return BranchMergeTransaction(root, manifest, dry_run=dry_run, inject_failure=inject_failure)
    return Transaction(root, manifest, dry_run=dry_run, inject_failure=inject_failure)


def _current_pointer_status(root: Path, task_id: str) -> Dict[str, Any]:
    """Validate one mutable current pointer against its immutable result bytes."""
    pointer_path = root / "output" / "logs" / task_id / "current.json"
    relative_pointer = pointer_path.relative_to(root).as_posix()
    if not pointer_path.exists() and not pointer_path.is_symlink():
        return {"path": relative_pointer, "status": "missing"}
    try:
        pointer_bytes, _ = _read_file_nofollow(pointer_path)
        pointer = json.loads(pointer_bytes.decode("utf-8"))
        if not isinstance(pointer, dict):
            raise ValueError("pointer must be a JSON object")
        expected_keys = {
            "schema", "task_id", "request_id", "result_path", "result_sha256", "verdict", "lifecycle_state", "updated_at"
        }
        if set(pointer) != expected_keys:
            raise ValueError("pointer keys do not match the current-pointer contract")
        if pointer["schema"] != CURRENT_POINTER_SCHEMA or pointer["task_id"] != task_id:
            raise ValueError("pointer schema or task identity does not match its directory")
        request_id = pointer["request_id"]
        if not isinstance(request_id, str) or not REQUEST_ID_RE.fullmatch(request_id):
            raise ValueError("pointer request ID is invalid")
        result_relative = _normalize_path(pointer["result_path"], "current result_path")
        expected_result = f"output/logs/{task_id}/{request_id}/result.json"
        if result_relative != expected_result:
            raise ValueError("pointer result path does not match task/request identity")
        result_path = root / result_relative
        result_bytes, _ = _read_file_nofollow(result_path)
        if pointer["result_sha256"] != _sha256_bytes(result_bytes):
            raise ValueError("pointer result digest does not match immutable result bytes")
        result = json.loads(result_bytes.decode("utf-8"))
        if not isinstance(result, dict):
            raise ValueError("result must be a JSON object")
        _validate_result_shape(result)
        if result.get("schema") != RESULT_SCHEMA:
            raise ValueError("result schema is not the legacy transaction result schema")
        if result.get("task_id") != task_id or result.get("request_id") != request_id:
            raise ValueError("result identity does not match pointer identity")
        if result.get("verdict") != pointer["verdict"] or result.get("lifecycle_state") != pointer["lifecycle_state"]:
            raise ValueError("result verdict/lifecycle does not match pointer")
        if result.get("verdict") not in TERMINAL_RESULT_VERDICTS:
            raise ValueError("pointer may reference only a terminal result")
        commits = result.get("commits")
        required_result = ("expected_base", "manifest_path", "contract_sha256", "published", "claim_finalized")
        if not all(key in result for key in required_result) or not isinstance(commits, dict):
            raise ValueError("result lacks journal-binding fields")
        final_commit = commits.get("final")
        if result.get("published") not in (True, False) or result.get("claim_finalized") not in (True, False):
            raise ValueError("result publication or claim-finalization state is invalid")
        if result["verdict"] == "passed" and result["published"] is not True:
            raise ValueError("passed pointer result does not prove publication")
        if result["published"] is True:
            if not isinstance(final_commit, str) or not FULL_COMMIT_RE.fullmatch(final_commit):
                raise ValueError("published result final commit is invalid")
        elif final_commit is not None and (not isinstance(final_commit, str) or not FULL_COMMIT_RE.fullmatch(final_commit)):
            raise ValueError("unpublished result final commit is invalid")
        if not isinstance(result["expected_base"], str) or not FULL_COMMIT_RE.fullmatch(result["expected_base"]):
            raise ValueError("result expected base is invalid")
        if not isinstance(result["manifest_path"], str) or not isinstance(result["contract_sha256"], str):
            raise ValueError("result manifest or contract binding is invalid")
        return {
            "path": relative_pointer,
            "status": "valid",
            "request_id": request_id,
            "result_path": result_relative,
            "verdict": pointer["verdict"],
            "expected_base": result["expected_base"],
            "manifest_path": result["manifest_path"],
            "contract_sha256": result["contract_sha256"],
            "final_commit": commits["final"],
            "claim_finalized": result["claim_finalized"],
        }
    except (OSError, UnicodeError, json.JSONDecodeError, TransactionError, ValueError) as exc:
        return {"path": relative_pointer, "status": "invalid", "error": str(exc)}


def _pointer_matches_journal(pointer: Mapping[str, Any], journal: Mapping[str, Any], request_id: str) -> bool:
    """Require a passed pointer to bind to the exact journal being recovered."""
    final_commit = journal.get("bookkeeping_commit") or journal.get("substantive_commit")
    return (
        pointer.get("status") == "valid"
        and pointer.get("request_id") == request_id
        and pointer.get("expected_base") == journal.get("expected_base")
        and pointer.get("manifest_path") == journal.get("manifest_path")
        and pointer.get("contract_sha256") == journal.get("contract_sha256")
        and pointer.get("final_commit") == final_commit
    )


def _write_current_pointer_for_result(
    root: Path,
    *,
    task_id: str,
    request_id: str,
    result_path: Path,
    result_payload: bytes,
    result: Mapping[str, Any],
    expected_pointer_state: FileState,
) -> None:
    pointer_path = root / "output" / "logs" / task_id / "current.json"
    if _read_state(pointer_path) != expected_pointer_state:
        raise TransactionError(
            "RTX-CURRENT-POINTER-DRIFT",
            "current pointer changed during recovery; refusing to overwrite it",
            "recover",
            EXIT_INTERNAL,
        )
    _ensure_directory_nofollow(root, result_path.parent)
    pointer = {
        "schema": CURRENT_POINTER_SCHEMA,
        "task_id": task_id,
        "request_id": request_id,
        "result_path": result_path.relative_to(root).as_posix(),
        "result_sha256": _sha256_bytes(result_payload),
        "verdict": result["verdict"],
        "lifecycle_state": result["lifecycle_state"],
        "updated_at": _utc_now(),
    }
    _atomic_write(pointer_path, _json_bytes(pointer), 0o600)


def _validate_result_shape(result: Mapping[str, Any]) -> None:
    required = {
        "schema", "task_id", "request_id", "owner_token", "expected_base", "base_observed", "authority_observed",
        "manifest_path", "manifest_sha256", "contract_sha256", "started_at", "finished_at", "verdict", "lifecycle_state",
        "phase", "phases", "actions", "findings", "substantive_commit", "bookkeeping_commit", "published", "claim_finalized",
        "paths", "commits", "cleanup", "evidence", "changed_path_count", "promotion_backups_retained", "error", "recovery",
    }
    missing = required - set(result)
    if missing:
        raise TransactionError("RTX-RECOVER-RESULT", f"result is missing required fields: {sorted(missing)}", "recover", EXIT_INTERNAL)
    if result.get("schema") != RESULT_SCHEMA:
        raise TransactionError("RTX-RECOVER-RESULT", "result schema is invalid", "recover", EXIT_INTERNAL)
    if not isinstance(result["phases"], list) or not isinstance(result["actions"], list) or not isinstance(result["findings"], list):
        raise TransactionError("RTX-RECOVER-RESULT", "result phase/action/finding fields are invalid", "recover", EXIT_INTERNAL)
    if not isinstance(result["authority_observed"], dict) or not isinstance(result["paths"], dict):
        raise TransactionError("RTX-RECOVER-RESULT", "result authority/path fields are invalid", "recover", EXIT_INTERNAL)
    if not isinstance(result["commits"], dict) or not isinstance(result["cleanup"], dict) or not isinstance(result["evidence"], dict):
        raise TransactionError("RTX-RECOVER-RESULT", "result commit/cleanup/evidence fields are invalid", "recover", EXIT_INTERNAL)


def _validate_result_journal_binding(
    result: Mapping[str, Any],
    journal: Mapping[str, Any],
    *,
    expected_verdict: str,
    expected_claim_finalized: bool,
    expected_published: bool,
) -> None:
    _validate_result_shape(result)
    final_commit = journal.get("bookkeeping_commit") or journal.get("substantive_commit")
    expected = {
        "task_id": journal.get("task_id"),
        "request_id": journal.get("request_id"),
        "owner_token": journal.get("owner_token"),
        "expected_base": journal.get("expected_base"),
        "manifest_path": journal.get("manifest_path"),
        "manifest_sha256": journal.get("manifest_sha256"),
        "contract_sha256": journal.get("contract_sha256"),
    }
    for key, value in expected.items():
        if not isinstance(value, str) or result.get(key) != value:
            raise TransactionError("RTX-RECOVER-RESULT-BINDING", f"result {key} does not match journal", "recover", EXIT_INTERNAL)
    commits = result["commits"]
    if result.get("substantive_commit") != journal.get("substantive_commit") or result.get("bookkeeping_commit") != journal.get("bookkeeping_commit"):
        raise TransactionError("RTX-RECOVER-RESULT-BINDING", "result commit fields do not match journal", "recover", EXIT_INTERNAL)
    if commits.get("final") != final_commit:
        raise TransactionError("RTX-RECOVER-RESULT-BINDING", "result final commit does not match journal", "recover", EXIT_INTERNAL)
    if (
        result.get("verdict") != expected_verdict
        or result.get("claim_finalized") is not expected_claim_finalized
        or result.get("published") is not expected_published
    ):
        raise TransactionError("RTX-RECOVER-RESULT-BINDING", "result verdict, publication, or claim-finalization state is invalid", "recover", EXIT_INTERNAL)


def _validate_claim_payload(payload: bytes, journal: Mapping[str, Any], task_id: str, request_id: str) -> None:
    expected_digest = journal.get("claim_preimage_sha256")
    if not isinstance(expected_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        raise TransactionError("RTX-FINALIZE-CLAIM", "journal lacks a valid claim preimage digest", "finalize-claim", EXIT_INTERNAL)
    if _sha256_bytes(payload) != expected_digest:
        raise TransactionError("RTX-FINALIZE-CLAIM", "claim bytes do not match the journaled preimage digest", "finalize-claim", EXIT_INTERNAL)
    try:
        claim_text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise TransactionError("RTX-FINALIZE-CLAIM", "claim is not UTF-8", "finalize-claim", EXIT_INTERNAL) from exc
    for field, value in (("task_id", task_id), ("request_id", request_id), ("owner_token", journal.get("owner_token"))):
        if not isinstance(value, str) or value not in claim_text:
            raise TransactionError("RTX-FINALIZE-CLAIM", f"claim does not contain journal-bound {field}", "finalize-claim", EXIT_INTERNAL)


def _recovery_result_candidate(root: Path, journal_path: Path, journal: Dict[str, Any]) -> Tuple[Path, bytes, Dict[str, Any], bool]:
    """Validate a complete result candidate before any recovery mutation occurs."""
    result_path = journal_path.parent / "result.json"
    if result_path.exists() or result_path.is_symlink():
        payload, _ = _read_file_nofollow(result_path)
        try:
            result = json.loads(payload.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise TransactionError("RTX-RECOVER-RESULT", f"cannot parse retained result: {exc}", "recover", EXIT_INTERNAL) from exc
        if not isinstance(result, dict):
            raise TransactionError("RTX-RECOVER-RESULT", "retained result is not a JSON object", "recover", EXIT_INTERNAL)
        _validate_result_journal_binding(result, journal, expected_verdict="passed", expected_claim_finalized=True, expected_published=True)
        return result_path, payload, result, False

    prepared_path = journal_path.parent / "prepared-result.json"
    try:
        prepared_bytes, _ = _read_file_nofollow(prepared_path)
        result = json.loads(prepared_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, TransactionError) as exc:
        raise TransactionError(
            "RTX-RECOVER-PREPARED-RESULT",
            f"cannot reconstruct terminal result from {prepared_path.relative_to(root)}: {exc}",
            "recover",
            EXIT_INTERNAL,
        ) from exc
    if not isinstance(result, dict):
        raise TransactionError("RTX-RECOVER-PREPARED-RESULT", "prepared result is not a JSON object", "recover", EXIT_INTERNAL)
    _validate_result_journal_binding(result, journal, expected_verdict="prepared", expected_claim_finalized=False, expected_published=False)
    final_commit = journal.get("bookkeeping_commit") or journal.get("substantive_commit")
    result.update(
        {
            "finished_at": _utc_now(),
            "verdict": "passed",
            "lifecycle_state": "complete",
            "phase": "complete",
            "published": True,
            "claim_finalized": True,
            "error": None,
            "recovery": "recovered from prepared-result.json after verified publication",
        }
    )
    result["commits"]["substantive"] = journal.get("substantive_commit")
    result["commits"]["bookkeeping"] = journal.get("bookkeeping_commit")
    result["commits"]["final"] = final_commit
    result["cleanup"]["claim_finalized"] = True
    result["cleanup"]["journal_state"] = "complete"
    result["phases"].append({"name": "recovery-finalize", "status": "passed", "exit_code": 0, "duration_ms": 0})
    _validate_result_journal_binding(result, journal, expected_verdict="passed", expected_claim_finalized=True, expected_published=True)
    payload = _json_bytes(result)
    return result_path, payload, result, True


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
    current_pointers: List[Dict[str, Any]] = []
    logs_dir = root / "output" / "logs"
    if logs_dir.exists():
        for task_dir in sorted(path for path in logs_dir.iterdir() if path.is_dir()):
            current_pointers.append(_current_pointer_status(root, task_dir.name))
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
        "current_pointers": current_pointers,
        "interrupted_transactions": interrupted_requests,
    }


def _transaction_journal(root: Path, request_id: str) -> Tuple[Path, Dict[str, Any]]:
    """Load exactly one journal for a request; ambiguity is never guessed away."""
    logs_dir = root / "output" / "logs"
    matched = sorted(logs_dir.glob(f"*/{request_id}/transaction-journal.json"))
    if not matched:
        raise TransactionError(
            "RTX-RECOVER-NOT-FOUND",
            f"no transaction journal found for request ID {request_id}",
            "recover",
            EXIT_INTERNAL,
        )
    if len(matched) != 1:
        paths = [path.relative_to(root).as_posix() for path in matched]
        raise TransactionError(
            "RTX-RECOVER-AMBIGUOUS",
            f"multiple transaction journals match request ID {request_id}: {paths}",
            "recover",
            EXIT_INTERNAL,
        )
    path = matched[0]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TransactionError(
            "RTX-RECOVER-JOURNAL",
            f"cannot read transaction journal {path.relative_to(root)}: {exc}",
            "recover",
            EXIT_INTERNAL,
        ) from exc
    if data.get("schema") != TRANSACTION_JOURNAL_SCHEMA or data.get("request_id") != request_id:
        raise TransactionError(
            "RTX-RECOVER-JOURNAL",
            f"journal identity/schema mismatch at {path.relative_to(root)}",
            "recover",
            EXIT_INTERNAL,
        )
    return path, data


def _journal_claim_path(root: Path, journal: Dict[str, Any]) -> str:
    """Resolve the exact claim bound by a journal, including older journals."""
    value = journal.get("claim_path")
    if isinstance(value, str) and value:
        return _normalize_path(value, "journal claim_path")
    manifest_value = journal.get("manifest_path")
    if not isinstance(manifest_value, str) or not manifest_value:
        raise TransactionError(
            "RTX-RECOVER-CLAIM",
            "journal has neither claim_path nor a usable manifest_path",
            "recover",
            EXIT_INTERNAL,
        )
    manifest_path = root / _normalize_path(manifest_value, "journal manifest_path")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        claim_path = manifest["identity"]["claim_path"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise TransactionError(
            "RTX-RECOVER-CLAIM",
            f"cannot recover exact claim identity from {manifest_value}: {exc}",
            "recover",
            EXIT_INTERNAL,
        ) from exc
    return _normalize_path(claim_path, "manifest identity.claim_path")


def recover_transaction(root: Path, request_id: str) -> Dict[str, Any]:
    """Return a deterministic, read-only recovery plan for one exact request."""
    root = root.resolve()
    journal_path, journal = _transaction_journal(root, request_id)
    task_id = journal.get("task_id")
    claim_path = _journal_claim_path(root, journal)
    pointer = _current_pointer_status(root, str(task_id)) if isinstance(task_id, str) else {"status": "invalid", "error": "missing Task ID"}
    pointer_matches = _pointer_matches_journal(pointer, journal, request_id)
    report: Dict[str, Any] = {
        "status": "action-required",
        "request_id": request_id,
        "task_id": task_id,
        "prior_state": journal.get("state"),
        "journal_path": journal_path.relative_to(root).as_posix(),
        "claim_path": claim_path,
        "published": bool(journal.get("published")),
        "claim_finalized": bool(journal.get("claim_finalized")),
        "current_pointer": pointer,
        "pointer_matches_journal": pointer_matches,
    }
    typed_action = journal.get("typed_action")
    if typed_action in IMPLEMENTED_TYPED_ACTIONS:
        report["typed_action"] = typed_action
        report["target_ref"] = journal.get("target_ref")
        report["merged_tips"] = journal.get("merged_tips") or []
        report["final_branch_tip"] = journal.get("final_branch_tip")
        report["worktree_synchronized"] = bool(journal.get("worktree_synchronized"))
    lock = doctor(root)["lock"]
    if lock.get("exists"):
        report["status"] = "blocked-by-lock"
        report["recommendation"] = "Inspect the reported lock holder; recover never deletes a live or stale lock."
    elif typed_action in IMPLEMENTED_TYPED_ACTIONS:
        # Branch/merge actions never archive the claim: it travels on the branch
        # (docs/pipeline/branch-workflow.md), so `finalize-claim` never applies.
        if pointer["status"] == "invalid":
            report["status"] = "pointer-invalid"
            report["recommendation"] = (
                "Preserve the immutable result and repair the digest-bound pointer explicitly; "
                "never infer branch publication from logs."
            )
        elif journal.get("published"):
            report["status"] = "branch-published"
            report["recommendation"] = (
                f"The ref {journal.get('target_ref')} was advanced to {journal.get('final_branch_tip')}. "
                "Verify the ref and the declared merged paths in the working tree, record the merged tips "
                "in the claim if the journal shows that step did not complete, then continue under a fresh "
                "request ID. Never re-run this request ID."
            )
        else:
            report["status"] = "branch-unpublished"
            report["recommendation"] = (
                "No ref was advanced; the merge was performed only in a discarded temporary worktree. "
                "Retain the claim, journal and result, then submit a fresh request ID against the current tips."
            )
    elif pointer["status"] == "invalid":
        report["status"] = "pointer-invalid"
        report["recommendation"] = "Do not infer completion from logs or journals; preserve the immutable result and repair the digest-bound pointer explicitly."
    elif pointer["status"] == "valid" and not pointer_matches:
        report["status"] = "pointer-journal-mismatch"
        report["recommendation"] = "Current pointer belongs to a different request or commit contract; retain both records and do not finalize this claim."
    elif pointer["status"] == "valid" and pointer.get("verdict") != "passed":
        report["status"] = "terminal-failure-recorded"
        report["recommendation"] = "The current pointer records a terminal failure; retain the claim and immutable result, then reconcile the failure rather than finalizing or rerunning this request ID."
    elif journal.get("published") and journal.get("claim_finalized") and pointer_matches and pointer.get("claim_finalized") is True:
        report["status"] = "complete"
        report["recommendation"] = "No recovery action required."
    elif journal.get("published"):
        report["recommendation"] = (
            "python3 _src/tools/runner_transaction.py finalize-claim "
            f"--task-id {task_id} --request-id {request_id}"
        )
    else:
        report["status"] = "retry-required"
        report["recommendation"] = (
            "Preserve the exact claim, journal, result, and promotion backups; resolve any "
            "rollback-blocked-by-drift finding, then submit a fresh request ID against the current base."
        )
    return report


@contextlib.contextmanager
def _recovery_lease(root: Path, journal: Mapping[str, Any]) -> Iterator[None]:
    """Serialize standalone recovery; no caller may bypass another lock holder."""
    git_dir_text = _git_text(root, ["rev-parse", "--git-dir"])
    git_dir = Path(git_dir_text)
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    lock_path = git_dir.resolve() / "autodocs-runner-transaction.lock"
    payload = _json_bytes(
        {
            "schema": LOCK_SCHEMA,
            "pid": os.getpid(),
            "start_time": time.time(),
            "recovery": True,
            "task_id": journal.get("task_id"),
            "request_id": journal.get("request_id"),
            "owner_token": journal.get("owner_token"),
        }
    )
    try:
        descriptor = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise TransactionError(
            "RTX-FINALIZE-LOCK",
            "transaction lock exists; finalize-claim never deletes or bypasses a live or stale lock",
            "finalize-claim",
            EXIT_INTERNAL,
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        yield
    finally:
        try:
            if lock_path.read_bytes() == payload:
                lock_path.unlink()
        except FileNotFoundError:
            pass


def finalize_claim_standalone(root: Path, task_id: str, request_id: str) -> bool:
    """Idempotently complete exact post-CAS recovery without trusting mutable logs."""
    root = root.resolve()
    journal_path, journal = _transaction_journal(root, request_id)
    with _recovery_lease(root, journal):
        return _finalize_claim_locked(root, task_id, request_id, journal_path, journal)


def _finalize_claim_locked(
    root: Path,
    task_id: str,
    request_id: str,
    journal_path: Path,
    journal: Dict[str, Any],
) -> bool:
    if journal.get("task_id") != task_id:
        raise TransactionError(
            "RTX-FINALIZE-TASK",
            f"journal Task {journal.get('task_id')!r} does not match requested Task {task_id!r}",
            "finalize-claim",
            EXIT_INTERNAL,
        )
    if not journal.get("published"):
        raise TransactionError(
            "RTX-FINALIZE-UNPUBLISHED",
            "journal does not prove successful branch publication",
            "finalize-claim",
            EXIT_INTERNAL,
        )
    final_commit = journal.get("bookkeeping_commit") or journal.get("substantive_commit")
    if not isinstance(final_commit, str) or not FULL_COMMIT_RE.fullmatch(final_commit):
        raise TransactionError(
            "RTX-FINALIZE-COMMIT",
            "journal has no valid published commit identity",
            "finalize-claim",
            EXIT_INTERNAL,
        )
    _git(root, ["cat-file", "-e", f"{final_commit}^{{commit}}"])
    branch_ref = journal.get("branch_ref")
    if isinstance(branch_ref, str) and branch_ref:
        if _git_text(root, ["rev-parse", branch_ref]) != final_commit:
            raise TransactionError(
                "RTX-FINALIZE-BRANCH",
                f"branch {branch_ref} does not point to journal commit {final_commit}",
                "finalize-claim",
                EXIT_INTERNAL,
            )

    pointer_before = _current_pointer_status(root, task_id)
    if pointer_before["status"] == "invalid":
        raise TransactionError(
            "RTX-FINALIZE-RESULT",
            "finalize-claim refuses a malformed or tampered current pointer",
            "finalize-claim",
            EXIT_INTERNAL,
        )
    if pointer_before["status"] == "valid":
        if not _pointer_matches_journal(pointer_before, journal, request_id) or pointer_before.get("verdict") != "passed":
            raise TransactionError(
                "RTX-FINALIZE-RESULT",
                "finalize-claim requires a passed pointer bound to this exact journal",
                "finalize-claim",
                EXIT_INTERNAL,
            )
        if pointer_before.get("claim_finalized") is not True:
            raise TransactionError(
                "RTX-FINALIZE-RESULT",
                "existing immutable result does not prove claim finalization",
                "finalize-claim",
                EXIT_INTERNAL,
            )
    pointer_state = _read_state(root / "output" / "logs" / task_id / "current.json")
    recovery_candidate: Optional[Tuple[Path, bytes, Dict[str, Any], bool]] = None
    if pointer_before["status"] == "missing":
        recovery_candidate = _recovery_result_candidate(root, journal_path, journal)

    claim_relative = _journal_claim_path(root, journal)
    claim_path = root / claim_relative
    archive = journal_path.parent / "finalized-claim.md"
    changed = False
    if claim_path.exists() or claim_path.is_symlink():
        claim_payload, _ = _read_file_nofollow(claim_path)
        _validate_claim_payload(claim_payload, journal, task_id, request_id)
        if archive.exists() or archive.is_symlink():
            raise TransactionError(
                "RTX-FINALIZE-ARCHIVE",
                f"claim archive already exists at {archive.relative_to(root)}",
                "finalize-claim",
                EXIT_INTERNAL,
            )
        _atomic_move(claim_path, archive)
        archive_payload, _ = _read_file_nofollow(archive)
        _validate_claim_payload(archive_payload, journal, task_id, request_id)
        changed = True
    elif archive.exists() and not archive.is_symlink():
        archive_payload, _ = _read_file_nofollow(archive)
        _validate_claim_payload(archive_payload, journal, task_id, request_id)
    else:
        return False

    journal["claim_finalized"] = True
    journal["state"] = "claim-finalized"
    journal["updated_at"] = _utc_now()
    _atomic_write(journal_path, _json_bytes(journal), 0o600)

    if recovery_candidate is not None:
        result_path, result_payload, result, create_result = recovery_candidate
        if create_result:
            _atomic_create(result_path, result_payload, 0o600)
        _write_current_pointer_for_result(
            root,
            task_id=task_id,
            request_id=request_id,
            result_path=result_path,
            result_payload=result_payload,
            result=result,
            expected_pointer_state=pointer_state,
        )

    pointer_after = _current_pointer_status(root, task_id)
    if (
        not _pointer_matches_journal(pointer_after, journal, request_id)
        or pointer_after.get("verdict") != "passed"
        or pointer_after.get("claim_finalized") is not True
    ):
        raise TransactionError(
            "RTX-FINALIZE-RESULT",
            "claim archival completed but no exact passed immutable result/current pointer is available",
            "finalize-claim",
            EXIT_INTERNAL,
        )
    journal["state"] = "complete"
    journal["updated_at"] = _utc_now()
    _atomic_write(journal_path, _json_bytes(journal), 0o600)
    return changed


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
        transaction = build_transaction(
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
