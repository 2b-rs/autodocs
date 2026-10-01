#!/usr/bin/env python3
"""Claim-aware artifact quarantine, retention, and garbage collection (Task `0038-11`).

Two related jobs live here:

1. **Quarantine** (`quarantine_artifact`) — the sanctioned way for a partial,
   failed, or interrupted translation/export/generated-tree/report/scratch
   attempt to become GC-eligible at all. It moves the artifact into a
   run-specific ``.partial`` root under ``output/logs/<task-id>/<request-id>/``
   and writes a structured ``artifact-quarantine@v1`` side-car recording
   state, error, source/output digests, and retry eligibility. A raw,
   un-quarantined artifact is never a GC candidate — see the "fixed-path
   export" fixture in the test module for why: this is what stops a shared,
   overwrite-in-place export path from ever being blindly deleted.
2. **Garbage collection** (`plan_gc` / `gc`) — a dry-run-first sweep of
   ``output/logs/<task-id>/**`` that classifies every attempt directory and
   quarantine entry into a retention tier (``successful-log``, `failed-trace``,
   ``cache``, ``scratch``, ``permanent-manifest``) and only proposes deleting
   **terminal, unowned** artifacts whose tier TTL has elapsed. It refuses:

   * a **live claim** — any ``TODO-*.md`` claim file naming the Task, or a
     ``[p]`` marker for it in ``TODO.md``;
   * an **unfinalized journal** — `_src/tools/runner_transaction.py` (Task
     `0038-10`) writes ``transaction-journal.json`` before it writes the
     immutable ``result.json``; without a ``result.json`` the attempt is not
     terminal, no matter what the journal's last recorded state says;
   * **unknown state** — any stray, non-empty file this tool does not
     recognize (e.g. a reused free-text ``run-current.log``) is never
     interpreted as pending/completed/safe-to-delete;
   * the **current pointer target** — whatever ``current.json`` (Task
     `0038-10`) currently points at is never deleted by this tool, even if
     its own TTL has otherwise elapsed;
   * a **permanent-manifest** reference — any path named by an ``items[].path``
     entry of a ``task-evidence-pack@v1`` manifest (Task `0038-12`) found
     under the scanned roots is retained with an explicit disposition rather
     than silently deleted out from under the manifest.

   It additionally prunes **safe empty tombstones** (attempt directories that
   are completely empty, or contain only zero-byte files) once they clear a
   small minimum age, and guards against **clock skew**: a recorded timestamp
   that lies in the future relative to ``now`` is never treated as "old" (no
   ``abs()`` on the age), so a clock jump cannot make a fresh artifact look
   eligible.

Dry-run is the default for both the planner and the CLI; real deletion
requires an explicit ``--apply``. Stdlib only, no network access.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

QUARANTINE_SCHEMA = "artifact-quarantine@v1"
GC_REPORT_SCHEMA = "artifact-gc-report@v1"
EVIDENCE_PACK_SCHEMA = "task-evidence-pack@v1"
RESULT_SCHEMA_PREFIX = "legacy-runner-transaction-result"

QUARANTINE_STATES = {"partial", "failed", "interrupted", "superseded"}

# Default retention TTLs in seconds. "permanent-manifest" has no TTL: it is
# never auto-deleted by this tool.
DEFAULT_TTL_SECONDS: Dict[str, int] = {
    "successful-log": 7 * 86400,
    "failed-trace": 30 * 86400,
    "cache": 3 * 86400,
    "scratch": 1 * 86400,
}

# Quarantine-descriptor state -> retention tier.
QUARANTINE_TIER_BY_STATE: Dict[str, str] = {
    "failed": "failed-trace",
    "partial": "scratch",
    "interrupted": "scratch",
    "superseded": "scratch",
}

MIN_TOMBSTONE_AGE_SECONDS_DEFAULT = 60
RESERVED_TASK_DIR_ENTRIES = {"evidence-blobs", "current.json"}
SENTINEL_NAME_RE = re.compile(r"(?i)(^failed$|\.failed$|sentinel)")


class RetentionError(ValueError):
    """A fail-closed retention/quarantine rule was violated."""

    def __init__(self, rule: str, message: str) -> None:
        super().__init__(f"{rule}: {message}")
        self.rule = rule
        self.message = message


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------


def _now_iso(now: Optional[float] = None) -> str:
    dt = datetime.datetime.fromtimestamp(now, tz=datetime.timezone.utc) if now is not None else datetime.datetime.now(datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: str) -> float:
    try:
        dt = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except ValueError as exc:
        raise RetentionError("RET-BAD-TIMESTAMP", f"not an ISO-8601 UTC timestamp: {value!r}") from exc
    return dt.timestamp()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _digest_dir(path: Path) -> str:
    """Order-independent digest of every regular file's relative path + content hash."""
    lines: List[str] = []
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file():
            lines.append(f"{file_path.relative_to(path).as_posix()}:{_sha256_path(file_path)}")
    return _sha256_bytes("\n".join(lines).encode("utf-8"))


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _atomic_write_json(destination: Path, value: Mapping[str, Any]) -> bytes:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".part")
    tmp.write_bytes(payload)
    tmp.chmod(0o600)
    tmp.replace(destination)
    return payload


def _assert_safe_repo_path(root: Path, relative: str, rule: str) -> Path:
    candidate = root / relative
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise RetentionError(rule, f"path escapes repository root: {relative}") from exc
    return candidate


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        value = json.loads(raw)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


# ---------------------------------------------------------------------------
# Quarantine
# ---------------------------------------------------------------------------


def quarantine_artifact(
    root: Path,
    *,
    task_id: str,
    request_id: str,
    source_path: str,
    kind: str,
    state: str,
    error: Optional[Tuple[str, str]] = None,
    retry_eligible: bool = False,
    quarantine_root: str = "output/logs",
    now: Optional[float] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Move a partial/failed/interrupted artifact into a run-specific quarantine root.

    ``source_path`` must be an exact, existing path (file or directory) under
    ``root`` — never a glob. The artifact is moved (not copied) into
    ``<quarantine_root>/<task_id>/<request_id>/.partial/<name>`` and a
    structured ``artifact-quarantine@v1`` side-car is written next to it,
    recording ``state``, an optional ``error``, ``source_digest``/
    ``output_digest``, and ``retry_eligible``. This is the only way an
    artifact outside the ``output/logs/<task>/<request>`` attempt structure
    (e.g. a fixed-path export) can ever become a GC candidate.
    """
    if state not in QUARANTINE_STATES:
        raise RetentionError("RET-BAD-STATE", f"unsupported quarantine state: {state!r} (expected one of {sorted(QUARANTINE_STATES)})")
    if any(ch in source_path for ch in "*?[]"):
        raise RetentionError("RET-BROAD-GLOB", f"source_path must be an exact path, not a glob: {source_path!r}")

    source_abs = _assert_safe_repo_path(root, source_path, "RET-SOURCE-SCOPE")
    if not source_abs.exists():
        raise RetentionError("RET-SOURCE-MISSING", f"quarantine source does not exist: {source_path}")

    source_digest = _digest_dir(source_abs) if source_abs.is_dir() else _sha256_path(source_abs)

    quarantine_dir_rel = f"{quarantine_root}/{task_id}/{request_id}/.partial"
    quarantine_dir = _assert_safe_repo_path(root, quarantine_dir_rel, "RET-QUARANTINE-SCOPE")
    destination = quarantine_dir / source_abs.name
    if destination.exists():
        raise RetentionError("RET-QUARANTINE-COLLISION", f"quarantine destination already exists: {destination.relative_to(root)}")

    descriptor_path = quarantine_dir / f"{source_abs.name}.quarantine.json"
    quarantined_at = _now_iso(now)
    descriptor: Dict[str, Any] = {
        "schema": QUARANTINE_SCHEMA,
        "task_id": task_id,
        "request_id": request_id,
        "kind": kind,
        "state": state,
        "original_path": source_path,
        "artifact_path": None,
        "source_digest": source_digest,
        "output_digest": None,
        "error": None,
        "retry_eligible": bool(retry_eligible),
        "quarantined_at": quarantined_at,
    }
    if error:
        descriptor["error"] = {"rule": error[0], "message": error[1]}

    if dry_run:
        descriptor["artifact_path"] = str((destination.relative_to(root)))
        descriptor["output_digest"] = source_digest
        return descriptor

    quarantine_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_abs), str(destination))
    output_digest = _digest_dir(destination) if destination.is_dir() else _sha256_path(destination)
    descriptor["artifact_path"] = str(destination.relative_to(root))
    descriptor["output_digest"] = output_digest
    _atomic_write_json(descriptor_path, descriptor)
    return descriptor


# ---------------------------------------------------------------------------
# Live-claim and permanent-manifest guards
# ---------------------------------------------------------------------------


def has_live_claim(root: Path, task_id: str) -> bool:
    """Conservative claim-awareness: any claim filename or ``[p]`` marker naming
    ``task_id`` blocks GC for the whole task, regardless of which attempt."""
    todo_path = root / "TODO.md"
    if todo_path.exists():
        try:
            text = todo_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        if re.search(rf"^- \[p\] \*\*{re.escape(task_id)}\*\*", text, re.MULTILINE):
            return True
    for candidate in root.glob("TODO-*.md"):
        if task_id in candidate.name:
            return True
    return False


def collect_permanent_manifest_paths(root: Path, search_roots: Sequence[Path]) -> set:
    """Collect every ``items[].path`` referenced by a `task-evidence-pack@v1`
    manifest under the given search roots, as repo-relative POSIX strings."""
    referenced: set = set()
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for candidate in search_root.rglob("*.json"):
            value = _read_json(candidate)
            if not value or value.get("schema") != EVIDENCE_PACK_SCHEMA:
                continue
            for item in value.get("items", []) or []:
                path = item.get("path") if isinstance(item, dict) else None
                if isinstance(path, str):
                    referenced.add(path)
    return referenced


def _current_pointer_request_id(task_dir: Path) -> Optional[str]:
    pointer = _read_json(task_dir / "current.json")
    if pointer and isinstance(pointer.get("request_id"), str):
        return pointer["request_id"]
    return None


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


class Candidate:
    def __init__(
        self,
        *,
        path: str,
        kind: str,
        tier: Optional[str],
        state: str,
        timestamp: Optional[float],
        reason: str,
        task_id: str,
        request_id: Optional[str] = None,
        note: str = "",
    ) -> None:
        self.path = path
        self.kind = kind
        self.tier = tier
        self.state = state
        self.timestamp = timestamp
        self.reason = reason
        self.task_id = task_id
        self.request_id = request_id
        self.note = note
        self.deleted = False

    def to_dict(self, now: float) -> Dict[str, Any]:
        age = None if self.timestamp is None else round(now - self.timestamp, 3)
        return {
            "path": self.path,
            "kind": self.kind,
            "tier": self.tier,
            "state": self.state,
            "task_id": self.task_id,
            "request_id": self.request_id,
            "timestamp": None if self.timestamp is None else _now_iso(self.timestamp),
            "age_seconds": age,
            "reason": self.reason,
            "note": self.note,
            "eligible": self.reason == "eligible",
            "deleted": self.deleted,
        }


def _is_all_empty(path: Path) -> bool:
    """True if `path` (file or dir) contains no bytes anywhere: an empty file,
    an empty directory, or a directory whose files are all zero-byte."""
    if path.is_file():
        return path.stat().st_size == 0
    saw_any = False
    for entry in path.rglob("*"):
        if entry.is_file():
            saw_any = True
            if entry.stat().st_size > 0:
                return False
    return True  # empty dir or all-zero-byte files


def classify_request_dir(request_dir: Path, *, now: float) -> Tuple[str, str, Optional[float], str]:
    """Return (tier_or_None, state, timestamp_or_None, reason) for one attempt
    directory, BEFORE live-claim / current-pointer / permanent-manifest guards."""
    result_path = request_dir / "result.json"
    journal_path = request_dir / "transaction-journal.json"

    if result_path.exists():
        result = _read_json(result_path)
        if not result or not str(result.get("schema", "")).startswith(RESULT_SCHEMA_PREFIX):
            return None, "unknown-state", None, "retained:unknown-state"
        verdict = result.get("verdict")
        finished_at = result.get("finished_at")
        if verdict not in {"passed", "failed"} or not isinstance(finished_at, str):
            return None, "unknown-state", None, "retained:unknown-state"
        try:
            ts = _parse_iso(finished_at)
        except RetentionError:
            return None, "unknown-state", None, "retained:unknown-state"
        tier = "successful-log" if verdict == "passed" else "failed-trace"
        return tier, "terminal-result", ts, "pending-ttl"

    if journal_path.exists():
        # A journal without an immutable result.json means the transaction
        # never reached persist_terminal_result() — it is not terminal no
        # matter what its own "state" field claims (0038-10 contract).
        return None, "unfinalized-journal", None, "retained:unfinalized-journal"

    # No result.json, no journal: either debris from a sentinel-style legacy
    # attempt, safe empty tombstone, or genuinely unknown stray content.
    top_level_files = [entry for entry in request_dir.iterdir() if entry.is_file()]
    non_empty_files = [entry for entry in top_level_files if entry.stat().st_size > 0]
    sentinel_files = [entry for entry in non_empty_files if SENTINEL_NAME_RE.search(entry.name)]

    if non_empty_files and sentinel_files and len(sentinel_files) == len(non_empty_files):
        # every non-empty file is a recognized failure sentinel
        newest = max(sentinel_files, key=lambda entry: entry.stat().st_mtime)
        return "failed-trace", "legacy-sentinel", newest.stat().st_mtime, "pending-ttl"

    if _is_all_empty(request_dir):
        return None, "empty-tombstone", request_dir.stat().st_mtime, "pending-tombstone"

    return None, "unknown-state", None, "retained:unknown-state"


def _quarantine_candidates(request_dir: Path, *, task_id: str, request_id: str) -> List[Candidate]:
    candidates: List[Candidate] = []
    partial_dir = request_dir / ".partial"
    if not partial_dir.is_dir():
        return candidates
    for descriptor_path in sorted(partial_dir.glob("*.quarantine.json")):
        descriptor = _read_json(descriptor_path)
        if not descriptor or descriptor.get("schema") != QUARANTINE_SCHEMA:
            candidates.append(
                Candidate(
                    path=str(descriptor_path),
                    kind="quarantine",
                    tier=None,
                    state="unknown-state",
                    timestamp=None,
                    reason="retained:unknown-state",
                    task_id=task_id,
                    request_id=request_id,
                )
            )
            continue
        state = descriptor.get("state")
        tier = QUARANTINE_TIER_BY_STATE.get(state)
        if descriptor.get("retry_eligible") and tier == "scratch":
            tier = "failed-trace"  # give retry-eligible artifacts more runway
        try:
            ts = _parse_iso(descriptor.get("quarantined_at", ""))
        except RetentionError:
            ts = None
        artifact_path = descriptor.get("artifact_path")
        group_paths = [str(descriptor_path)]
        if artifact_path:
            group_paths.insert(0, artifact_path)
        candidates.append(
            Candidate(
                path="|".join(group_paths),
                kind="quarantine",
                tier=tier,
                state=f"quarantine:{state}",
                timestamp=ts,
                reason="pending-ttl" if tier else "retained:unknown-state",
                task_id=task_id,
                request_id=request_id,
            )
        )
    return candidates


# ---------------------------------------------------------------------------
# Planning / GC
# ---------------------------------------------------------------------------


def plan_gc(
    root: Path,
    *,
    logs_root: str = "output/logs",
    now: Optional[float] = None,
    ttl_by_tier: Optional[Mapping[str, int]] = None,
    min_tombstone_age_seconds: int = MIN_TOMBSTONE_AGE_SECONDS_DEFAULT,
    task_ids: Optional[Sequence[str]] = None,
    cache_roots: Sequence[str] = (),
    manifest_search_roots: Optional[Sequence[Path]] = None,
) -> List[Candidate]:
    """Build the full candidate list with dispositions, performing no deletion."""
    now_ts = now if now is not None else datetime.datetime.now(datetime.timezone.utc).timestamp()
    ttl = dict(DEFAULT_TTL_SECONDS)
    if ttl_by_tier:
        ttl.update(ttl_by_tier)

    logs_dir = root / logs_root
    candidates: List[Candidate] = []

    manifest_roots = list(manifest_search_roots) if manifest_search_roots is not None else [logs_dir]
    protected_paths = collect_permanent_manifest_paths(root, manifest_roots)

    def _is_manifest_protected(candidate_path: str) -> bool:
        parts = candidate_path.split("|")
        for protected in protected_paths:
            for part in parts:
                if protected == part or protected.startswith(part + "/") or part.startswith(protected + "/"):
                    return True
        return False

    def _finalize(candidate: Candidate) -> Candidate:
        if candidate.reason not in {"pending-ttl", "pending-tombstone"}:
            return candidate
        if _is_manifest_protected(candidate.path):
            candidate.reason = "retained:permanent-manifest"
            return candidate
        if has_live_claim(root, candidate.task_id):
            candidate.reason = "retained:live-claim"
            return candidate
        if candidate.reason == "pending-tombstone":
            age = now_ts - (candidate.timestamp or now_ts)
            candidate.reason = "eligible" if age >= min_tombstone_age_seconds else "retained:ttl-not-elapsed"
            return candidate
        # pending-ttl: apply clock-skew guard, then TTL.
        age = now_ts - (candidate.timestamp or now_ts)
        if age < 0:
            candidate.reason = "retained:future-timestamp"
            return candidate
        tier_ttl = ttl.get(candidate.tier or "", None)
        if tier_ttl is None:
            candidate.reason = "retained:permanent-manifest" if candidate.tier == "permanent-manifest" else "retained:unknown-state"
            return candidate
        candidate.reason = "eligible" if age >= tier_ttl else "retained:ttl-not-elapsed"
        return candidate

    if logs_dir.is_dir():
        for task_dir in sorted(logs_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            task_id = task_dir.name
            if task_ids and task_id not in task_ids:
                continue
            current_request_id = _current_pointer_request_id(task_dir)

            for entry in sorted(task_dir.iterdir()):
                if entry.name in RESERVED_TASK_DIR_ENTRIES:
                    continue
                if entry.is_file():
                    # A stray top-level file outside any request directory
                    # (e.g. a legacy reused run-current.log). Never trusted.
                    candidates.append(
                        Candidate(
                            path=str(entry.relative_to(root)),
                            kind="stray-file",
                            tier=None,
                            state="unknown-state",
                            timestamp=None,
                            reason="retained:unknown-state",
                            task_id=task_id,
                        )
                    )
                    continue
                request_id = entry.name
                tier, state, ts, reason = classify_request_dir(entry, now=now_ts)
                candidate = Candidate(
                    path=str(entry.relative_to(root)),
                    kind="attempt",
                    tier=tier,
                    state=state,
                    timestamp=ts,
                    reason=reason,
                    task_id=task_id,
                    request_id=request_id,
                )
                if reason in {"pending-ttl", "pending-tombstone"} and current_request_id == request_id:
                    candidate.reason = "retained:current-pointer"
                else:
                    candidate = _finalize(candidate)
                candidates.append(candidate)

                for qcandidate in _quarantine_candidates(entry, task_id=task_id, request_id=request_id):
                    if qcandidate.reason == "pending-ttl":
                        qcandidate = _finalize(qcandidate)
                    candidates.append(qcandidate)

    for cache_root in cache_roots:
        cache_dir = root / cache_root
        if not cache_dir.is_dir():
            continue
        for entry in sorted(cache_dir.iterdir()):
            mtime = entry.stat().st_mtime
            candidate = Candidate(
                path=str(entry.relative_to(root)),
                kind="cache",
                tier="cache",
                state="cache-entry",
                timestamp=mtime,
                reason="pending-ttl",
                task_id="(cache)",
            )
            age = now_ts - mtime
            if age < 0:
                candidate.reason = "retained:future-timestamp"
            elif age >= ttl.get("cache", DEFAULT_TTL_SECONDS["cache"]):
                candidate.reason = "eligible"
            else:
                candidate.reason = "retained:ttl-not-elapsed"
            candidates.append(candidate)

    return candidates


def apply_gc(root: Path, candidates: Sequence[Candidate]) -> None:
    """Delete every candidate whose reason is 'eligible'. Called only with apply=True."""
    for candidate in candidates:
        if candidate.reason != "eligible":
            continue
        if candidate.kind == "attempt":
            target = root / candidate.path
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            candidate.deleted = True
        elif candidate.kind == "quarantine":
            for part in candidate.path.split("|"):
                target = root / part
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                elif target.exists():
                    target.unlink()
            candidate.deleted = True
        elif candidate.kind == "cache":
            target = root / candidate.path
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
            elif target.exists():
                target.unlink()
            candidate.deleted = True


def gc(
    root: Path,
    *,
    apply: bool = False,
    **plan_kwargs: Any,
) -> Dict[str, Any]:
    now_ts = plan_kwargs.get("now") or datetime.datetime.now(datetime.timezone.utc).timestamp()
    plan_kwargs["now"] = now_ts
    candidates = plan_gc(root, **plan_kwargs)
    if apply:
        apply_gc(root, candidates)
    counts: Dict[str, int] = {}
    for candidate in candidates:
        counts[candidate.reason] = counts.get(candidate.reason, 0) + 1
    report = {
        "schema": GC_REPORT_SCHEMA,
        "generated_at": _now_iso(now_ts),
        "dry_run": not apply,
        "root": str(root),
        "counts": counts,
        "candidates": [candidate.to_dict(now_ts) for candidate in candidates],
    }
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_summary(report: Mapping[str, Any]) -> None:
    mode = "DRY-RUN" if report["dry_run"] else "APPLIED"
    print(f"VERDICT {mode} candidates={len(report['candidates'])} counts={report['counts']}")
    for entry in report["candidates"]:
        if entry["reason"] == "eligible" or entry["deleted"]:
            print(f"  {entry['reason']:>28} {entry['kind']:>10} {entry['path']}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    quarantine = sub.add_parser("quarantine", help="Move a partial/failed/interrupted artifact into a run-specific quarantine root")
    quarantine.add_argument("--root", required=True, type=Path)
    quarantine.add_argument("--task-id", required=True)
    quarantine.add_argument("--request-id", required=True)
    quarantine.add_argument("--source", required=True, help="exact repo-relative path (no globs)")
    quarantine.add_argument("--kind", required=True, help="e.g. translation, export, generated-tree, report, scratch")
    quarantine.add_argument("--state", required=True, choices=sorted(QUARANTINE_STATES))
    quarantine.add_argument("--error-rule", default=None)
    quarantine.add_argument("--error-message", default=None)
    quarantine.add_argument("--retry-eligible", action="store_true")
    quarantine.add_argument("--quarantine-root", default="output/logs")
    quarantine.add_argument("--dry-run", action="store_true")
    quarantine.add_argument("--json", action="store_true")

    for name in ("plan", "gc"):
        cmd = sub.add_parser(name, help="Classify GC candidates" if name == "plan" else "Plan and optionally apply GC")
        cmd.add_argument("--root", required=True, type=Path)
        cmd.add_argument("--logs-root", default="output/logs")
        cmd.add_argument("--now", default=None, help="ISO-8601 UTC override for testing")
        cmd.add_argument("--task-id", action="append", default=None, dest="task_ids")
        cmd.add_argument("--cache-root", action="append", default=[], dest="cache_roots")
        cmd.add_argument("--ttl-successful-log", type=int, default=None)
        cmd.add_argument("--ttl-failed-trace", type=int, default=None)
        cmd.add_argument("--ttl-cache", type=int, default=None)
        cmd.add_argument("--ttl-scratch", type=int, default=None)
        cmd.add_argument("--min-tombstone-age-seconds", type=int, default=MIN_TOMBSTONE_AGE_SECONDS_DEFAULT)
        cmd.add_argument("--out-report", type=Path, default=None)
        cmd.add_argument("--json", action="store_true")
        if name == "gc":
            cmd.add_argument("--apply", action="store_true", help="perform real deletion; default is dry-run")

    args = parser.parse_args(argv)

    if args.command == "quarantine":
        error = (args.error_rule, args.error_message) if args.error_rule and args.error_message else None
        try:
            descriptor = quarantine_artifact(
                args.root.resolve(),
                task_id=args.task_id,
                request_id=args.request_id,
                source_path=args.source,
                kind=args.kind,
                state=args.state,
                error=error,
                retry_eligible=args.retry_eligible,
                quarantine_root=args.quarantine_root,
                dry_run=args.dry_run,
            )
        except RetentionError as exc:
            print(f"VERDICT FAIL {exc.rule}: {exc.message}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(descriptor, sort_keys=True, indent=2))
        else:
            print(f"VERDICT PASS quarantined={descriptor['artifact_path']} state={descriptor['state']}")
        return 0

    if args.command in {"plan", "gc"}:
        ttl_overrides = {
            "successful-log": args.ttl_successful_log,
            "failed-trace": args.ttl_failed_trace,
            "cache": args.ttl_cache,
            "scratch": args.ttl_scratch,
        }
        ttl_by_tier = {tier: value for tier, value in ttl_overrides.items() if value is not None}
        now_ts = _parse_iso(args.now) if args.now else None
        apply = bool(getattr(args, "apply", False))
        report = gc(
            args.root.resolve(),
            apply=apply,
            logs_root=args.logs_root,
            now=now_ts,
            ttl_by_tier=ttl_by_tier or None,
            min_tombstone_age_seconds=args.min_tombstone_age_seconds,
            task_ids=args.task_ids,
            cache_roots=args.cache_roots,
        )
        if args.out_report:
            _atomic_write_json(args.out_report, report)
        if args.json:
            print(json.dumps(report, sort_keys=True, indent=2))
        else:
            _print_summary(report)
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
