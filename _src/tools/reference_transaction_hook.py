#!/usr/bin/env python3
"""Fail-open early warning for foreign-origin fast-forward absorption.

The versioned script has two operator commands::

    python3 _src/tools/reference_transaction_hook.py install --repo .
    python3 _src/tools/reference_transaction_hook.py check --repo .

``install`` atomically creates (and never overwrites) the active
``reference-transaction`` hook. ``check`` verifies its digest, executable bit,
and active hook path. When Git invokes the installed copy with ``prepared``,
``committed``, or ``aborted``, hook mode is selected automatically.

The hook is deliberately a *net*, not a gate. Hook mode catches every internal
error and returns zero. A missing, stale, bypassed, or failed hook never counts
as the binding integration check required by ``DEC-0044-009``.

Stdlib-only. The hook runs only read-only Git plumbing commands. Its sole
mutation is private evidence under the common Git directory:
``autodocs/reference-transactions.jsonl`` and short-lived pending records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, TextIO


SCHEMA = "reference-transaction-log@v1"
HOOK_STATES = frozenset({"prepared", "committed", "aborted"})
HOOK_NAME = "reference-transaction"
ZERO_OIDS = frozenset({"0" * 40, "0" * 64})
CANONICAL_ITEM = re.compile(r"^[0-9]{4}(?:-[0-9]+(?:\.[0-9]+)?)?$")
TASK_ID = re.compile(r"\*\*([0-9]{4}(?:-[0-9]+(?:\.[0-9]+)?)?)\*\*")
FEATURE_ID = re.compile(r"^## Feature: ([0-9]{4})\b", re.MULTILINE)
PREREQ_EDGE = re.compile(
    r"\b([0-9]{4}(?:-[0-9]+(?:\.[0-9]+)?)?):"
    r"([0-9]{4}(?:-[0-9]+(?:\.[0-9]+)?)?)\b"
)
OID = re.compile(r"^[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?$")
GIT_TIMEOUT_SECONDS = 5.0
ANALYSIS_BUDGET_SECONDS = 8.0
MAX_INCOMING_COMMITS = 256
MAX_MATCHING_REFS = 256
MAX_PENDING_BYTES = 2 * 1024 * 1024


class HookError(RuntimeError):
    """An operator-facing install/check or internal analysis error."""


@dataclass(frozen=True)
class RefUpdate:
    old_oid: str
    new_oid: str
    refname: str

    def canonical_line(self) -> str:
        return f"{self.old_oid} {self.new_oid} {self.refname}"


@dataclass(frozen=True)
class GitContext:
    common_dir: Path
    git_prefix: tuple[str, ...]

    @property
    def evidence_dir(self) -> Path:
        return self.common_dir / "autodocs"

    @property
    def pending_dir(self) -> Path:
        return self.evidence_dir / "reference-transaction-pending"

    @property
    def log_path(self) -> Path:
        return self.evidence_dir / "reference-transactions.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_git(prefix: Sequence[str], args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Return a checked-by-caller Git result; never invoke a shell."""
    try:
        return subprocess.run(
            [*prefix, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise HookError(f"git {' '.join(args)} exceeded {GIT_TIMEOUT_SECONDS:.1f}s") from exc


def _require_git(prefix: Sequence[str], args: Sequence[str]) -> str:
    proc = _run_git(prefix, args)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "no diagnostic"
        raise HookError(f"git {' '.join(args)} failed ({proc.returncode}): {detail}")
    return proc.stdout


def _discover_context(repo: Path | None = None) -> GitContext:
    prefix = ("git", "-C", str(repo.resolve())) if repo is not None else ("git",)
    common = _require_git(prefix, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
    common_dir = Path(common.strip()).resolve()
    if not common_dir.is_dir():
        raise HookError(f"Git common directory is unavailable: {common_dir}")
    return GitContext(common_dir=common_dir, git_prefix=("git", "--git-dir", str(common_dir)))


def _active_hooks_dir(repo: Path) -> tuple[GitContext, Path]:
    context = _discover_context(repo)
    config = _run_git(
        ("git", "-C", str(repo.resolve())),
        ["config", "--path", "--get", "core.hooksPath"],
    )
    if config.returncode == 1:
        return context, context.common_dir / "hooks"
    if config.returncode != 0:
        detail = config.stderr.strip() or "no diagnostic"
        raise HookError(f"could not read core.hooksPath ({config.returncode}): {detail}")
    configured = Path(config.stdout.strip())
    if not configured.is_absolute():
        raise HookError(
            "relative core.hooksPath is worktree-context-dependent; use an absolute "
            "shared path or unset it before installing the common hook"
        )
    return context, configured.resolve()


def _source_bytes() -> bytes:
    return Path(__file__).read_bytes()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def install(repo: Path) -> dict[str, object]:
    """Create the active hook without overwriting any existing hook."""
    context, hooks_dir = _active_hooks_dir(repo)
    if hooks_dir.is_symlink():
        raise HookError(f"refusing symlinked hooks directory: {hooks_dir}")
    hooks_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
    if hooks_dir.is_symlink() or not hooks_dir.is_dir():
        raise HookError(f"active hooks path is not a real directory: {hooks_dir}")
    target = hooks_dir / HOOK_NAME
    source = _source_bytes()
    expected = _sha256(source)

    if target.exists():
        if target.is_symlink() or not target.is_file():
            raise HookError(f"refusing non-regular existing hook: {target}")
        if target.stat().st_size != len(source):
            raise HookError(
                f"refusing to overwrite different existing hook {target} "
                f"({target.stat().st_size} bytes)"
            )
        actual = target.read_bytes()
        if actual != source:
            raise HookError(
                f"refusing to overwrite existing hook {target}; preserve or remove it explicitly"
            )
        target.chmod(target.stat().st_mode | stat.S_IXUSR)
        return {
            "status": "already-installed",
            "hook_path": str(target),
            "sha256": expected,
            "common_git_dir": str(context.common_dir),
        }

    fd, temporary_name = tempfile.mkstemp(prefix=f".{HOOK_NAME}.", dir=str(hooks_dir))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(source)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), 0o755)
        try:
            os.link(temporary, target)
        except FileExistsError:
            if target.is_symlink() or not target.is_file() or target.read_bytes() != source:
                raise HookError(f"hook appeared concurrently with different bytes: {target}")
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass

    return {
        "status": "installed",
        "hook_path": str(target),
        "sha256": expected,
        "common_git_dir": str(context.common_dir),
    }


def presence(repo: Path) -> dict[str, object]:
    """Return exact active-hook presence and version evidence."""
    context, hooks_dir = _active_hooks_dir(repo)
    target = hooks_dir / HOOK_NAME
    expected = _sha256(_source_bytes())
    safe_path = not hooks_dir.is_symlink() and not target.is_symlink()
    exists = safe_path and target.is_file()
    executable = exists and os.access(target, os.X_OK)
    same_size = exists and target.stat().st_size == len(_source_bytes())
    actual = _sha256(target.read_bytes()) if same_size else None
    matches = actual == expected
    pending_records = 0
    if context.pending_dir.is_dir() and not context.pending_dir.is_symlink():
        pending_records = sum(
            1
            for candidate in context.pending_dir.glob("*.json")
            if candidate.is_file()
        )
    return {
        "present": bool(exists and executable and matches),
        "exists": exists,
        "executable": executable,
        "matches_versioned_source": matches,
        "safe_regular_path": safe_path,
        "hook_path": str(target),
        "expected_sha256": expected,
        "actual_sha256": actual,
        "common_git_dir": str(context.common_dir),
        "log_path": str(context.log_path),
        "pending_records": pending_records,
        "authority": "early-warning-only; not an integration verdict",
    }


def _parse_updates(stream: TextIO) -> tuple[RefUpdate, ...]:
    updates: list[RefUpdate] = []
    for number, raw in enumerate(stream, start=1):
        line = raw.rstrip("\n")
        fields = line.split(" ", 2)
        if len(fields) != 3:
            raise HookError(f"malformed reference-transaction input at line {number}")
        old_oid, new_oid, refname = fields
        if not OID.fullmatch(old_oid) or not OID.fullmatch(new_oid):
            raise HookError(f"invalid object id at line {number}")
        if not refname.startswith("refs/") or any(ch in refname for ch in "\r\n\x00"):
            raise HookError(f"invalid refname at line {number}")
        updates.append(RefUpdate(old_oid.lower(), new_oid.lower(), refname))
    if not updates:
        raise HookError("reference-transaction input was empty")
    return tuple(updates)


def _transaction_id(updates: Sequence[RefUpdate]) -> str:
    material = "\n".join(sorted(update.canonical_line() for update in updates)).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _task_contract(context: GitContext, old_oid: str) -> str:
    proc = _run_git(context.git_prefix, ["show", f"{old_oid}:TODO.md"])
    return proc.stdout if proc.returncode == 0 else ""


def _parent_item(item: str) -> str | None:
    if "." in item:
        return item.rsplit(".", 1)[0]
    if "-" in item:
        return item.split("-", 1)[0]
    return "main" if re.fullmatch(r"[0-9]{4}", item) else None


def _allowed_carriers(target_ref: str, contract: str) -> set[str]:
    """Refs representing the documented direct item chain for ``target_ref``."""
    if not target_ref.startswith("refs/heads/"):
        return set()
    target = target_ref.removeprefix("refs/heads/")
    task_ids = set(TASK_ID.findall(contract))
    feature_ids = set(FEATURE_ID.findall(contract))
    allowed: set[str] = {target}

    if target == "main":
        allowed.update(feature_ids)
    elif CANONICAL_ITEM.fullmatch(target):
        parent = _parent_item(target)
        if parent:
            allowed.add(parent)
        for consumer, producer in PREREQ_EDGE.findall(contract):
            if consumer == target:
                allowed.add(producer)
            if producer == target:
                allowed.add(consumer)
        if re.fullmatch(r"[0-9]{4}", target):
            allowed.update(item for item in task_ids if item.startswith(f"{target}-"))
        else:
            allowed.update(item for item in task_ids if _parent_item(item) == target)

    return {f"refs/heads/{name}" for name in allowed}


def _is_fast_forward(context: GitContext, old_oid: str, new_oid: str) -> bool:
    proc = _run_git(context.git_prefix, ["merge-base", "--is-ancestor", old_oid, new_oid])
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    detail = proc.stderr.strip() or "no diagnostic"
    raise HookError(f"merge-base failed ({proc.returncode}): {detail}")


def _ref_lines(context: GitContext, args: Sequence[str]) -> set[str]:
    output = _require_git(
        context.git_prefix,
        [
            "for-each-ref",
            *args,
            f"--count={MAX_MATCHING_REFS + 1}",
            "--format=%(refname)",
            "refs/heads",
        ],
    )
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if len(lines) > MAX_MATCHING_REFS:
        raise HookError(f"more than {MAX_MATCHING_REFS} matching branch refs")
    return set(lines)


def _incoming_commits(
    context: GitContext, old_oid: str, new_oid: str
) -> tuple[list[str], bool]:
    output = _require_git(
        context.git_prefix,
        [
            "rev-list",
            "--reverse",
            f"--max-count={MAX_INCOMING_COMMITS + 1}",
            f"{old_oid}..{new_oid}",
        ],
    )
    commits = [line.strip() for line in output.splitlines() if line.strip()]
    truncated = len(commits) > MAX_INCOMING_COMMITS
    return commits[:MAX_INCOMING_COMMITS], truncated


def _analyze(context: GitContext, updates: Sequence[RefUpdate]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    deadline = time.monotonic() + ANALYSIS_BUDGET_SECONDS
    for update in updates:
        if time.monotonic() > deadline:
            raise HookError(f"analysis exceeded {ANALYSIS_BUDGET_SECONDS:.1f}s budget")
        if (
            not update.refname.startswith("refs/heads/")
            or update.old_oid in ZERO_OIDS
            or update.new_oid in ZERO_OIDS
            or not _is_fast_forward(context, update.old_oid, update.new_oid)
        ):
            continue

        contract = _task_contract(context, update.old_oid)
        allowed = _allowed_carriers(update.refname, contract)
        new_tip_refs = _ref_lines(context, [f"--points-at={update.new_oid}"])
        if allowed.intersection(new_tip_refs):
            continue

        commit_findings: list[dict[str, object]] = []
        incoming, truncated = _incoming_commits(context, update.old_oid, update.new_oid)
        for commit in incoming:
            if time.monotonic() > deadline:
                raise HookError(f"analysis exceeded {ANALYSIS_BUDGET_SECONDS:.1f}s budget")
            containing = _ref_lines(context, [f"--contains={commit}"])
            foreign = sorted(containing.difference(allowed).difference({update.refname}))
            if foreign:
                commit_findings.append({"commit": commit, "also_on": foreign})
        if commit_findings:
            findings.append(
                {
                    "target_ref": update.refname,
                    "old_oid": update.old_oid,
                    "new_oid": update.new_oid,
                    "allowed_carrier_refs": sorted(allowed),
                    "analysis_truncated": truncated,
                    "foreign_origin": commit_findings,
                }
            )
    return findings


def _ensure_private_dir(path: Path, common_dir: Path) -> None:
    try:
        path.relative_to(common_dir)
    except ValueError as exc:
        raise HookError(f"evidence path escapes the common Git directory: {path}") from exc
    cursor = path
    while cursor != common_dir:
        if cursor.is_symlink():
            raise HookError(f"refusing symlinked evidence path: {cursor}")
        cursor = cursor.parent
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise HookError(f"evidence path is not a directory: {path}")


def _write_pending(context: GitContext, transaction_id: str, event: dict[str, object]) -> None:
    _ensure_private_dir(context.pending_dir, context.common_dir)
    target = context.pending_dir / f"{transaction_id}.json"
    payload = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_PENDING_BYTES:
        raise HookError(f"pending evidence exceeds {MAX_PENDING_BYTES} bytes")
    fd, temporary_name = tempfile.mkstemp(prefix=f".{transaction_id}.", dir=str(context.pending_dir))
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), 0o600)
        os.replace(temporary, target)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _commit_pending(context: GitContext, transaction_id: str) -> None:
    pending = context.pending_dir / f"{transaction_id}.json"
    if pending.is_symlink():
        raise HookError(f"refusing symlinked pending record: {pending}")
    if not pending.is_file():
        return
    if pending.stat().st_size > MAX_PENDING_BYTES:
        raise HookError(f"pending evidence exceeds {MAX_PENDING_BYTES} bytes")
    event = json.loads(pending.read_text(encoding="utf-8"))
    if event.get("transaction_id") != transaction_id:
        raise HookError("pending transaction identity mismatch")
    event["outcome"] = "committed"
    event["committed_at"] = _utc_now()
    line = (json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    _ensure_private_dir(context.evidence_dir, context.common_dir)
    if context.log_path.is_symlink():
        raise HookError(f"refusing symlinked evidence log: {context.log_path}")
    if context.log_path.exists() and not context.log_path.is_file():
        raise HookError(f"refusing non-regular evidence log: {context.log_path}")
    flags = (
        os.O_APPEND
        | os.O_CREAT
        | os.O_WRONLY
        | os.O_NONBLOCK
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(
        context.log_path,
        flags,
        0o600,
    )
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise HookError(f"evidence log is not a regular file: {context.log_path}")
        written = os.write(descriptor, line)
        if written != len(line):
            raise HookError(
                f"short evidence-log append: wrote {written} of {len(line)} bytes"
            )
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    pending.unlink()


def _abort_pending(context: GitContext, transaction_id: str) -> None:
    pending = context.pending_dir / f"{transaction_id}.json"
    try:
        pending.unlink()
    except FileNotFoundError:
        pass


def _hook(state: str, stream: TextIO) -> int:
    """Run hook state handling. This function itself may raise; entry never does."""
    context = _discover_context()
    updates = _parse_updates(stream)
    transaction_id = _transaction_id(updates)
    if state == "prepared":
        findings = _analyze(context, updates)
        if findings:
            _write_pending(
                context,
                transaction_id,
                {
                    "schema": SCHEMA,
                    "transaction_id": transaction_id,
                    "observed_at": _utc_now(),
                    "outcome": "prepared",
                    "findings": findings,
                },
            )
    elif state == "committed":
        _commit_pending(context, transaction_id)
    elif state == "aborted":
        _abort_pending(context, transaction_id)
    return 0


def hook_entry(state: str, stream: TextIO) -> int:
    """Fail open under every hook-path exception, including malformed input."""
    try:
        return _hook(state, stream)
    except BaseException as exc:  # Git safety boundary: the warning layer never becomes a gate.
        try:
            sys.stderr.write(f"autodocs reference-transaction warning unavailable: {exc}\n")
        except BaseException:
            pass
        return 0


def _operator_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "check"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--repo", type=Path, default=Path("."))
    return parser


def operator_main(argv: Sequence[str]) -> int:
    args = _operator_parser().parse_args(argv)
    try:
        if args.command == "install":
            result = install(args.repo)
            print(json.dumps(result, sort_keys=True))
            return 0
        result = presence(args.repo)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["present"] else 1
    except (HookError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc), "present": False}, sort_keys=True))
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) == 1 and arguments[0] in HOOK_STATES:
        return hook_entry(arguments[0], sys.stdin)
    return operator_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
