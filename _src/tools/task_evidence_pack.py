#!/usr/bin/env python3
"""Compact, content-addressed Task evidence packs (Task `0038-12`).

An evidence pack is one JSON manifest (`task-evidence-pack@v1`) that records,
for a single Task attempt: the exact argv/action, base/tool/environment
identity, exit status, counts, a criterion mapping, and one entry per piece
of retained evidence. Every entry is either:

* ``blob`` — content copied once into a content-addressed store keyed by its
  SHA-256 digest (repeated bytes across many timestamped log directories are
  stored exactly once), or
* ``tracked-ref`` — a pointer to a tracked source/script file by exact Git
  commit and path, so a probe script committed at some historical commit is
  never duplicated byte-for-byte into every timestamped log directory that
  used it.

The builder fails closed before writing anything if it detects a likely
secret, a caller-supplied glob instead of an exact path list, evidence whose
path names a Task ID other than the pack's own declared Task (unless
explicitly allow-listed as a related Task), or a pack whose only proof is an
unreferenced, git-ignored scratch log with no captured item.

No network access, no repository mutation outside the declared blob-root and
manifest output path, and no interpretation of shell strings: every input is
an explicit path.  Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

SCHEMA = "task-evidence-pack@v1"

SOURCE_EXTENSIONS = {".py", ".cjs", ".js", ".mjs", ".sh", ".ts", ".applescript", ".as"}
GLOB_CHARS = set("*?[]")
TASK_ID_RE = re.compile(r"(?<![0-9])(\d{4}-\d{2}(?:\.\d{2})?)(?![0-9])")
ALLOWED_PRIVACY_CLASSES = {"public", "internal", "restricted"}
EXCERPT_MAX_LINES = 20
EXCERPT_MAX_BYTES = 8192
MAX_BLOB_BYTES = 8 * 1024 * 1024

# Same shape of check as the project's other secret scanners (see
# environment_doctor.py's PEM_RE/TOKEN_VALUE_RE/SECRET_KEY_RE); kept as an
# independent, stdlib-only copy so this tool has no import-time coupling to
# another Task's module.
SECRET_PATTERNS: Tuple[Tuple[str, "re.Pattern[bytes]"], ...] = (
    ("EVP-SECRET-PEM", re.compile(rb"-----BEGIN [A-Z ]*(?:RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----")),
    ("EVP-SECRET-AWS-KEY", re.compile(rb"AKIA[0-9A-Z]{16}")),
    ("EVP-SECRET-GH-TOKEN", re.compile(rb"gh[opusr]_[A-Za-z0-9]{20,}")),
    ("EVP-SECRET-SLACK-TOKEN", re.compile(rb"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("EVP-SECRET-BEARER", re.compile(rb"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}")),
    ("EVP-SECRET-GENERIC-KEYVAL", re.compile(rb"(?i)(?:api[_-]?key|secret|password|passwd|access[_-]?key|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9/+=_.-]{12,}")),
)


class EvidencePackError(ValueError):
    """A closed evidence-pack contract was violated; fail closed."""

    def __init__(self, rule: str, message: str) -> None:
        super().__init__(f"{rule}: {message}")
        self.rule = rule
        self.message = message


def _digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _reject_globs(paths: Sequence[str]) -> None:
    for path in paths:
        if any(ch in GLOB_CHARS for ch in path):
            raise EvidencePackError("EVP-BROAD-GLOB", f"declared path is a glob/wildcard, not an exact path: {path!r}")


def _reject_secrets(data: bytes, logical_path: str) -> None:
    for rule, pattern in SECRET_PATTERNS:
        if pattern.search(data):
            raise EvidencePackError(rule, f"likely secret material detected in evidence candidate: {logical_path}")


def _check_related(logical_path: str, task_id: str, related_task_ids: Sequence[str]) -> None:
    allowed = {task_id, *related_task_ids}
    for match in TASK_ID_RE.findall(logical_path):
        if match not in allowed:
            raise EvidencePackError(
                "EVP-UNRELATED-RUN",
                f"evidence path names Task {match!r}, not declared task {task_id!r} "
                f"or an explicit related_task_ids entry: {logical_path}",
            )


def _run_git(root: Path, args: Sequence[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(root),
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise EvidencePackError("EVP-GIT", f"git {' '.join(args)} failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout.decode("utf-8", "replace")


def _git_show_bytes(root: Path, commit: str, path: str) -> Optional[bytes]:
    proc = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=str(root),
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def _git_is_tracked_at(root: Path, commit: str, path: str) -> bool:
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{path}"],
        cwd=str(root),
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def _git_is_ignored(root: Path, path: str) -> bool:
    proc = subprocess.run(
        ["git", "check-ignore", "-q", "--", path],
        cwd=str(root),
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def _read_bytes(root: Path, path: str, *, at_commit: Optional[str]) -> bytes:
    if at_commit:
        data = _git_show_bytes(root, at_commit, path)
        if data is None:
            raise EvidencePackError("EVP-MISSING-INPUT", f"path not found at commit {at_commit}: {path}")
        return data
    full = root / path
    try:
        return full.read_bytes()
    except OSError as exc:
        raise EvidencePackError("EVP-MISSING-INPUT", f"cannot read {path}: {exc}") from exc


def _line_count(data: bytes) -> int:
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def _bounded_excerpt(data: bytes) -> Optional[str]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    lines = text.splitlines()
    excerpt_lines = lines[:EXCERPT_MAX_LINES]
    excerpt = "\n".join(excerpt_lines)
    encoded = excerpt.encode("utf-8")
    if len(encoded) > EXCERPT_MAX_BYTES:
        encoded = encoded[:EXCERPT_MAX_BYTES]
        excerpt = encoded.decode("utf-8", "ignore")
    truncated = len(excerpt_lines) < len(lines) or len(encoded) < len(text.encode("utf-8"))
    if truncated:
        excerpt += "\n... [excerpt truncated]"
    return excerpt


def _blob_path(blob_root: Path, digest: str) -> Path:
    hex_digest = digest.removeprefix("sha256:")
    return blob_root / "sha256" / hex_digest[:2] / hex_digest


def _write_blob(blob_root: Path, digest: str, data: bytes, *, dry_run: bool) -> bool:
    """Write ``data`` under its content address if absent. Returns True if newly written."""
    destination = _blob_path(blob_root, digest)
    if destination.exists():
        return False
    if dry_run:
        return True
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".part")
    tmp.write_bytes(data)
    tmp.chmod(0o600)
    tmp.replace(destination)
    return True


def _classify_and_build_item(
    root: Path,
    blob_root: Path,
    spec: Mapping[str, Any],
    *,
    task_id: str,
    related_task_ids: Sequence[str],
    dry_run: bool,
) -> Dict[str, Any]:
    logical_path = spec["path"]
    if not isinstance(logical_path, str) or not logical_path:
        raise EvidencePackError("EVP-BAD-ITEM", "item spec requires a non-empty string 'path'")
    _reject_globs([logical_path])
    _check_related(logical_path, task_id, related_task_ids)

    privacy_class = spec.get("privacy_class", "internal")
    if privacy_class not in ALLOWED_PRIVACY_CLASSES:
        raise EvidencePackError("EVP-PRIVACY-CLASS", f"unsupported privacy_class {privacy_class!r} for {logical_path}")

    at_commit = spec.get("commit")
    data = _read_bytes(root, logical_path, at_commit=at_commit)
    _reject_secrets(data, logical_path)

    extension = Path(logical_path).suffix.lower()
    source_commit = at_commit
    is_source = extension in SOURCE_EXTENSIONS
    tracked = False
    if source_commit and _git_is_tracked_at(root, source_commit, logical_path):
        tracked = True
    elif not source_commit:
        # Try HEAD when no explicit historical commit was declared. An empty
        # repository (no commits yet) has no HEAD; that is "not tracked", not
        # a hard failure.
        try:
            head = _run_git(root, ["rev-parse", "HEAD"]).strip()
        except EvidencePackError:
            head = None
        if head and _git_is_tracked_at(root, head, logical_path):
            tracked_bytes = _git_show_bytes(root, head, logical_path)
            if tracked_bytes == data:
                source_commit = head
                tracked = True

    digest = _digest_bytes(data)
    item: Dict[str, Any] = {
        "path": logical_path,
        "size_bytes": len(data),
        "line_count": _line_count(data),
        "digest": digest,
        "privacy_class": privacy_class,
        "criteria": list(spec.get("criteria", [])),
    }

    if is_source and tracked:
        item["kind"] = "tracked-ref"
        item["source_commit"] = source_commit
        item["source_path"] = logical_path
        item["excerpt"] = None
    else:
        if len(data) > MAX_BLOB_BYTES:
            raise EvidencePackError("EVP-BLOB-TOO-LARGE", f"{logical_path} exceeds the {MAX_BLOB_BYTES}-byte blob bound; reduce or split")
        newly_written = _write_blob(blob_root, digest, data, dry_run=dry_run)
        item["kind"] = "blob"
        item["blob_path"] = str(_blob_path(blob_root, digest).relative_to(blob_root))
        item["newly_written"] = newly_written
        item["excerpt"] = _bounded_excerpt(data)

    return item


def _build_full_log_entry(root: Path, spec: Mapping[str, Any]) -> Dict[str, Any]:
    path = spec["path"]
    if not isinstance(path, str) or not path:
        raise EvidencePackError("EVP-BAD-FULL-LOG", "full_log spec requires a non-empty string 'path'")
    _reject_globs([path])
    at_commit = spec.get("commit")
    digest = spec.get("digest")
    if digest is None:
        data = _read_bytes(root, path, at_commit=at_commit)
        digest = _digest_bytes(data)
    ignored = False if at_commit else _git_is_ignored(root, path)
    return {"path": path, "digest": digest, "commit": at_commit, "ignored": ignored}


def build_pack(
    root: Path,
    blob_root: Path,
    *,
    task_id: str,
    argv: Sequence[str],
    action: str,
    base_commit: str,
    tool_name: str,
    tool_version: str,
    environment_id: Optional[str],
    exit_status: int,
    item_specs: Sequence[Mapping[str, Any]],
    criteria: Sequence[Mapping[str, Any]],
    counts: Mapping[str, Any],
    full_log_specs: Sequence[Mapping[str, Any]] = (),
    commits: Optional[Mapping[str, Optional[str]]] = None,
    related_task_ids: Sequence[str] = (),
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    if not TASK_ID_RE.fullmatch(task_id):
        raise EvidencePackError("EVP-BAD-TASK-ID", f"task_id must look like an item ID (e.g. 0038-12): {task_id!r}")
    _reject_globs([spec["path"] for spec in item_specs if isinstance(spec, Mapping) and "path" in spec])
    _reject_globs([spec["path"] for spec in full_log_specs if isinstance(spec, Mapping) and "path" in spec])

    items = [
        _classify_and_build_item(root, blob_root, spec, task_id=task_id, related_task_ids=related_task_ids, dry_run=dry_run)
        for spec in item_specs
    ]
    full_logs = [_build_full_log_entry(root, spec) for spec in full_log_specs]

    if not items and any(entry["ignored"] for entry in full_logs):
        raise EvidencePackError(
            "EVP-SCRATCH-SOLE-PROOF",
            "pack has no captured blob/tracked-ref item; an ignored/scratch log path alone is not closure proof",
        )

    declared_item_paths = {item["path"] for item in items}
    for criterion in criteria:
        cid = criterion.get("id")
        if not cid:
            raise EvidencePackError("EVP-BAD-CRITERION", "criterion entries require an 'id'")
        for satisfied_path in criterion.get("satisfied_by", []):
            if satisfied_path not in declared_item_paths:
                raise EvidencePackError(
                    "EVP-CRITERION-UNKNOWN-ITEM",
                    f"criterion {cid!r} maps to undeclared item path: {satisfied_path}",
                )

    blob_items = [item for item in items if item["kind"] == "blob"]
    tracked_items = [item for item in items if item["kind"] == "tracked-ref"]
    unique_blob_digests = {item["digest"] for item in blob_items}
    evidence_counts = {
        "declared_items": len(items),
        "blob_items": len(blob_items),
        "unique_blobs": len(unique_blob_digests),
        "deduplicated_items": len(blob_items) - len(unique_blob_digests),
        "tracked_ref_items": len(tracked_items),
        "full_logs": len(full_logs),
    }

    manifest: Dict[str, Any] = {
        "schema": SCHEMA,
        "task_id": task_id,
        "created_at": _now_iso(),
        "run": {
            "argv": list(argv),
            "action": action,
            "base_commit": base_commit,
            "tool": {"name": tool_name, "version": tool_version},
            "environment_id": environment_id,
            "exit_status": int(exit_status),
            "started_at": started_at,
            "finished_at": finished_at,
        },
        "counts": {"evidence": evidence_counts, "custom": dict(counts)},
        "items": items,
        "full_logs": full_logs,
        "criteria": [dict(criterion) for criterion in criteria],
        "commits": {"substantive": None, "bookkeeping": None, **(dict(commits) if commits else {})},
        "related_task_ids": list(related_task_ids),
        "blob_root": str(blob_root.relative_to(root)) if _is_relative_to(blob_root, root) else str(blob_root),
    }
    manifest["content_digest"] = _digest_bytes(_canonical_bytes(manifest))
    return manifest


def _is_relative_to(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def write_manifest(manifest: Mapping[str, Any], destination: Path, *, dry_run: bool = False) -> bytes:
    payload = json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    if dry_run:
        return payload
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".part")
    tmp.write_bytes(payload)
    tmp.chmod(0o600)
    tmp.replace(destination)
    return payload


def load_manifest(path: Path) -> Dict[str, Any]:
    with path.open("rb") as handle:
        raw = handle.read()
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise EvidencePackError("EVP-BAD-MANIFEST", f"not a {SCHEMA} manifest: {path}")
    return value


def verify_pack(root: Path, blob_root: Path, manifest: Mapping[str, Any]) -> List[str]:
    """Return a list of finding strings; empty means the pack verifies clean."""
    findings: List[str] = []
    recomputed = dict(manifest)
    stored_digest = recomputed.pop("content_digest", None)
    if stored_digest != _digest_bytes(_canonical_bytes(recomputed)):
        findings.append("EVP-VERIFY-MANIFEST-DIGEST: manifest content_digest does not match its own body")

    for item in manifest.get("items", []):
        path = item.get("path", "<unknown>")
        if item.get("kind") == "blob":
            blob_file = _blob_path(blob_root, item["digest"])
            if not blob_file.is_file():
                findings.append(f"EVP-VERIFY-BLOB-MISSING: {path} -> {blob_file}")
                continue
            actual = _digest_bytes(blob_file.read_bytes())
            if actual != item["digest"]:
                findings.append(f"EVP-VERIFY-BLOB-DIGEST: {path} stored digest mismatch")
        elif item.get("kind") == "tracked-ref":
            commit = item.get("source_commit")
            source_path = item.get("source_path", path)
            if not commit or not _git_is_tracked_at(root, commit, source_path):
                findings.append(f"EVP-VERIFY-TRACKED-MISSING: {path} not resolvable at {commit}:{source_path}")
                continue
            data = _git_show_bytes(root, commit, source_path)
            if data is None or _digest_bytes(data) != item["digest"]:
                findings.append(f"EVP-VERIFY-TRACKED-DIGEST: {path} content at {commit} no longer matches recorded digest")
        else:
            findings.append(f"EVP-VERIFY-BAD-KIND: {path} has unknown kind {item.get('kind')!r}")
    return findings


def _load_json_arg(raw: Optional[str]) -> Any:
    if raw is None:
        return None
    return json.loads(raw)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="build a task-evidence-pack@v1 manifest and populate the blob store")
    build.add_argument("--root", required=True, type=Path)
    build.add_argument("--blob-root", required=True, type=Path)
    build.add_argument("--out-manifest", required=True, type=Path)
    build.add_argument("--task-id", required=True)
    build.add_argument("--action", required=True)
    build.add_argument("--base-commit", required=True)
    build.add_argument("--tool-name", required=True)
    build.add_argument("--tool-version", default="unknown")
    build.add_argument("--environment-id", default=None)
    build.add_argument("--exit-status", required=True, type=int)
    build.add_argument("--argv-json", default="[]", help="JSON list of the original argv")
    build.add_argument("--items-json", required=True, help="JSON list of {path, commit?, privacy_class?, criteria?}")
    build.add_argument("--criteria-json", default="[]", help="JSON list of {id, satisfied_by: [path,...]}")
    build.add_argument("--counts-json", default="{}", help="JSON object of caller-supplied counts")
    build.add_argument("--full-logs-json", default="[]", help="JSON list of {path, commit?, digest?}")
    build.add_argument("--commits-json", default="{}", help="JSON object {substantive?, bookkeeping?}")
    build.add_argument("--related-task-ids", default="", help="comma-separated Task IDs allowed inside evidence paths")
    build.add_argument("--dry-run", action="store_true")
    build.add_argument("--json", action="store_true")

    verify = sub.add_parser("verify", help="verify a manifest against its blob store / tracked commits")
    verify.add_argument("--root", required=True, type=Path)
    verify.add_argument("--blob-root", required=True, type=Path)
    verify.add_argument("--manifest", required=True, type=Path)
    verify.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "build":
        try:
            manifest = build_pack(
                args.root.resolve(),
                args.blob_root.resolve(),
                task_id=args.task_id,
                argv=_load_json_arg(args.argv_json) or [],
                action=args.action,
                base_commit=args.base_commit,
                tool_name=args.tool_name,
                tool_version=args.tool_version,
                environment_id=args.environment_id,
                exit_status=args.exit_status,
                item_specs=_load_json_arg(args.items_json),
                criteria=_load_json_arg(args.criteria_json),
                counts=_load_json_arg(args.counts_json),
                full_log_specs=_load_json_arg(args.full_logs_json),
                commits=_load_json_arg(args.commits_json),
                related_task_ids=[value for value in args.related_task_ids.split(",") if value],
                dry_run=args.dry_run,
            )
        except EvidencePackError as exc:
            if args.json:
                print(json.dumps({"verdict": "FAIL", "rule": exc.rule, "message": exc.message}))
            else:
                print(f"FAIL {exc.rule}: {exc.message}", file=sys.stderr)
            return 1
        write_manifest(manifest, args.out_manifest, dry_run=args.dry_run)
        if args.json:
            print(json.dumps({"verdict": "PASS", "manifest": str(args.out_manifest), "counts": manifest["counts"]}))
        else:
            evidence = manifest["counts"]["evidence"]
            print(
                f"PASS items={evidence['declared_items']} unique_blobs={evidence['unique_blobs']} "
                f"deduplicated={evidence['deduplicated_items']} tracked_refs={evidence['tracked_ref_items']} "
                f"manifest={args.out_manifest}"
            )
        return 0

    if args.command == "verify":
        manifest = load_manifest(args.manifest)
        findings = verify_pack(args.root.resolve(), args.blob_root.resolve(), manifest)
        verdict = "PASS" if not findings else "FAIL"
        if args.json:
            print(json.dumps({"verdict": verdict, "findings": findings}))
        else:
            print(f"{verdict} findings={len(findings)}")
            for finding in findings[:20]:
                print(f"  {finding}")
        return 0 if not findings else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
