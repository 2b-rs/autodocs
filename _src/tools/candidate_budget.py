#!/usr/bin/env python3
"""Isolate generated candidates and enforce output/diff/realism budgets (Task `0038-13`).

Composes three sibling contracts rather than reinventing them:

* **Run-specific roots** — `candidate_root()` places every generated candidate
  under ``output/logs/<task_id>/<request_id>/.candidates/``, the same
  request-scoped-directory pattern `_src/tools/artifact_retention.py`
  (Task `0038-11`) uses for its ``.partial`` quarantine root. A candidate is
  never generated in place over a shared/fixed path.
* **Sole-writer declaration** — a `candidate-budget@v1` document names the one
  producer (``sole_writer``) allowed to promote into a given destination,
  mirroring the sole-writer hazard class `_src/tools/legacy_scope_planner.py`
  (Task `0038-06`) already detects for write-scope collisions.
* **Structured PASS/FAIL, never bare exit codes** — `evaluate()` returns a
  `candidate-budget-report@v1` with the same PASS/FAIL/INCONCLUSIVE discipline
  `_src/tools/task_validation.py` (Task `0038-08`) established, so a required
  budget check failing (or missing) blocks promotion even if an upstream
  generator process happened to exit zero.

Three checks exist specifically because of this Feature's evidence baseline
(see the "Evidence baseline (2026-08-16)" paragraph in `TODO.md`'s Feature
`0038` section): Feature `0021` had green focused/generation checks but was
later archived, not accepted, because its checks were synthetic-only; current
build artifacts show fixed-path exports and mutable `run-current` evidence
that silently absorb a bad regeneration. `evaluate()` therefore requires
production-realistic byte floors (``realism``), rejects candidates that look
like synthesized in-memory stand-ins (``max_duplicate_digest_ratio``), and
requires at least one negative/error-case path when a budget declares
``require_negative_path`` — not only the happy path.

Promotion (`promote()`) is atomic and recoverable through a single small
pointer file (``current.json`` under the destination root), the same
atomic-mutable-pointer shape Task `0038-10` uses for attempt results: each
promotion stages its full tree under ``<destination>/<request_id>/`` and only
the final pointer write (temp file + ``rename``) decides what is "current".
A retry after a crash either completes idempotently (staged tree already
matches the evaluated manifest) or fails closed on a genuine collision; it
never blindly overwrites a differently-owned destination in place.

Stdlib only, no network access.
"""
from __future__ import annotations

import argparse
import datetime
import fnmatch
import hashlib
import json
import shutil
import stat as stat_module
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

BUDGET_SCHEMA = "candidate-budget@v1"
MANIFEST_SCHEMA = "candidate-manifest@v1"
REPORT_SCHEMA = "candidate-budget-report@v1"
POINTER_SCHEMA = "candidate-promotion-pointer@v1"
PROMOTION_RESULT_SCHEMA = "candidate-promotion-result@v1"


class BudgetError(ValueError):
    """A fail-closed candidate-budget contract or promotion rule was violated."""

    def __init__(self, rule: str, message: str) -> None:
        super().__init__(f"{rule}: {message}")
        self.rule = rule
        self.message = message


# ---------------------------------------------------------------------------
# small generic helpers
# ---------------------------------------------------------------------------


def _now_iso(now: Optional[float] = None) -> str:
    dt = datetime.datetime.fromtimestamp(now, tz=datetime.timezone.utc) if now is not None else datetime.datetime.now(datetime.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return "sha256:" + hasher.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _atomic_write_json(destination: Path, value: Mapping[str, Any]) -> bytes:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".part")
    tmp.write_bytes(payload)
    tmp.chmod(0o600)
    tmp.replace(destination)
    return payload


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


def _object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BudgetError("CB-SHAPE", f"{label}: object required")
    return value


def _closed(value: Any, label: str, required: Sequence[str], allowed: Sequence[str]) -> Mapping[str, Any]:
    obj = _object(value, label)
    missing = [key for key in required if key not in obj]
    unknown = sorted(set(obj) - set(allowed))
    if missing:
        raise BudgetError("CB-SHAPE", f"{label}: missing {','.join(missing)}")
    if unknown:
        raise BudgetError("CB-SHAPE", f"{label}: unknown member {unknown[0]}")
    return obj


def _strings(value: Any, label: str) -> List[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise BudgetError("CB-SHAPE", f"{label}: array of non-empty strings required")
    return list(value)


def _finding(path: str, code: str, message: str, severity: str = "error") -> Dict[str, str]:
    return {"path": path, "code": code, "severity": severity, "message": message[:240]}


# ---------------------------------------------------------------------------
# run-specific candidate root
# ---------------------------------------------------------------------------


def candidate_root(root: Path, *, task_id: str, request_id: str, logs_root: str = "output/logs") -> Path:
    """The sole sanctioned generation target: a run-specific, non-fixed path.

    Mirrors `_src/tools/artifact_retention.py`'s ``.partial`` quarantine root:
    a raw candidate is never generated over a shared/fixed export path.
    """
    for label, value in (("task_id", task_id), ("request_id", request_id)):
        if not value or any(ch in value for ch in "/\\") or value in (".", ".."):
            raise BudgetError("CB-BAD-ID", f"{label} must be a single safe path segment: {value!r}")
    return root / logs_root / task_id / request_id / ".candidates"


# ---------------------------------------------------------------------------
# candidate manifest
# ---------------------------------------------------------------------------


def build_manifest(candidate_dir: Path, *, now: Optional[float] = None) -> Dict[str, Any]:
    """Deterministic file/byte/digest inventory of a candidate root.

    ``manifest_digest`` is computed only from the sorted (path, bytes, digest)
    triples — never from ``generated_at`` — so two independent generations of
    identical content (a "clean-checkout reproduction") produce the same
    digest regardless of when or where they ran.
    """
    files: List[Dict[str, Any]] = []
    if candidate_dir.is_dir():
        for path in sorted(candidate_dir.rglob("*")):
            stat = path.stat()
            if not stat_module.S_ISREG(stat.st_mode):
                continue
            rel = path.relative_to(candidate_dir).as_posix()
            files.append({"path": rel, "bytes": stat.st_size, "digest": _sha256_path(path)})
    total_bytes = sum(item["bytes"] for item in files)
    manifest: Dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "generated_at": _now_iso(now),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "files": files,
        "manifest_digest": "",
    }
    manifest["manifest_digest"] = digest({"files": files})
    return manifest


# ---------------------------------------------------------------------------
# budget contract
# ---------------------------------------------------------------------------


def load_budget(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BudgetError("CB-BUDGET-READ", f"cannot read budget: {exc}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BudgetError("CB-BUDGET-JSON", f"invalid JSON: {exc}") from exc
    return _validate_budget(value)


def _bounds(obj: Mapping[str, Any], key: str) -> Dict[str, int]:
    bound = _closed(obj[key], f"budget.{key}", ("min", "max"), ("min", "max"))
    lo, hi = bound["min"], bound["max"]
    if not isinstance(lo, int) or not isinstance(hi, int) or isinstance(lo, bool) or isinstance(hi, bool) or lo < 0 or hi < lo:
        raise BudgetError("CB-BOUNDS", f"budget.{key}: integers with 0 <= min <= max required")
    return {"min": lo, "max": hi}


def _validate_budget(value: Any) -> Dict[str, Any]:
    obj = _closed(
        value, "budget",
        ("schema", "budget_id", "task_id", "sole_writer", "allowed_paths", "file_count", "total_bytes"),
        ("schema", "budget_id", "task_id", "sole_writer", "allowed_paths", "file_count", "total_bytes",
         "required_subtrees", "realism", "require_negative_path", "negative_path_patterns",
         "expected_manifest", "diff_tolerance", "explained_diffs", "max_duplicate_digest_ratio"),
    )
    if obj.get("schema") != BUDGET_SCHEMA:
        raise BudgetError("CB-SCHEMA", f"budget.schema must equal {BUDGET_SCHEMA!r}")
    for key in ("budget_id", "task_id", "sole_writer"):
        if not isinstance(obj[key], str) or not obj[key]:
            raise BudgetError("CB-IDENTITY", f"budget.{key}: non-empty string required")

    allowed_paths = _strings(obj["allowed_paths"], "budget.allowed_paths")
    if not allowed_paths:
        raise BudgetError("CB-ALLOWED-PATHS", "budget.allowed_paths: at least one pattern required")

    file_count = _bounds(obj, "file_count")
    total_bytes = _bounds(obj, "total_bytes")

    required_subtrees = _strings(obj.get("required_subtrees", []), "budget.required_subtrees")

    realism_raw = obj.get("realism", [])
    if not isinstance(realism_raw, list):
        raise BudgetError("CB-REALISM", "budget.realism: array required")
    realism: List[Dict[str, Any]] = []
    for index, item in enumerate(realism_raw):
        rule = _closed(item, f"budget.realism[{index}]", ("pattern", "min_bytes", "kind"), ("pattern", "min_bytes", "kind"))
        if not isinstance(rule["pattern"], str) or not rule["pattern"]:
            raise BudgetError("CB-REALISM", f"budget.realism[{index}].pattern: non-empty string required")
        if not isinstance(rule["min_bytes"], int) or isinstance(rule["min_bytes"], bool) or rule["min_bytes"] < 0:
            raise BudgetError("CB-REALISM", f"budget.realism[{index}].min_bytes: non-negative integer required")
        if not isinstance(rule["kind"], str) or not rule["kind"]:
            raise BudgetError("CB-REALISM", f"budget.realism[{index}].kind: non-empty string required")
        realism.append(dict(rule))

    require_negative_path = bool(obj.get("require_negative_path", False))
    negative_path_patterns = _strings(obj.get("negative_path_patterns", []), "budget.negative_path_patterns")
    if require_negative_path and not negative_path_patterns:
        raise BudgetError("CB-NEGATIVE-PATH", "budget.require_negative_path is true but negative_path_patterns is empty")

    expected_manifest_raw = obj.get("expected_manifest")
    expected_manifest: Optional[List[Dict[str, Any]]] = None
    if expected_manifest_raw is not None:
        if not isinstance(expected_manifest_raw, list):
            raise BudgetError("CB-EXPECTED-MANIFEST", "budget.expected_manifest: array required")
        expected_manifest = []
        for index, item in enumerate(expected_manifest_raw):
            entry = _closed(item, f"budget.expected_manifest[{index}]", ("path", "digest"), ("path", "digest", "bytes"))
            if not isinstance(entry["path"], str) or not entry["path"] or not isinstance(entry["digest"], str) or not entry["digest"]:
                raise BudgetError("CB-EXPECTED-MANIFEST", f"budget.expected_manifest[{index}]: path/digest required")
            expected_manifest.append(dict(entry))

    diff_tolerance_raw = obj.get("diff_tolerance", {"max_added": 0, "max_removed": 0, "max_changed": 0})
    diff_tolerance = _closed(diff_tolerance_raw, "budget.diff_tolerance", ("max_added", "max_removed", "max_changed"), ("max_added", "max_removed", "max_changed"))
    for key in ("max_added", "max_removed", "max_changed"):
        if not isinstance(diff_tolerance[key], int) or isinstance(diff_tolerance[key], bool) or diff_tolerance[key] < 0:
            raise BudgetError("CB-DIFF-TOLERANCE", f"budget.diff_tolerance.{key}: non-negative integer required")

    explained_diffs = _strings(obj.get("explained_diffs", []), "budget.explained_diffs")

    max_ratio = obj.get("max_duplicate_digest_ratio")
    if max_ratio is not None and (not isinstance(max_ratio, (int, float)) or isinstance(max_ratio, bool) or not (0 < max_ratio <= 1)):
        raise BudgetError("CB-DUP-RATIO", "budget.max_duplicate_digest_ratio: number in (0, 1] required")

    return {
        "schema": BUDGET_SCHEMA,
        "budget_id": obj["budget_id"],
        "task_id": obj["task_id"],
        "sole_writer": obj["sole_writer"],
        "allowed_paths": allowed_paths,
        "file_count": file_count,
        "total_bytes": total_bytes,
        "required_subtrees": required_subtrees,
        "realism": realism,
        "require_negative_path": require_negative_path,
        "negative_path_patterns": negative_path_patterns,
        "expected_manifest": expected_manifest,
        "diff_tolerance": diff_tolerance,
        "explained_diffs": explained_diffs,
        "max_duplicate_digest_ratio": max_ratio,
    }


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------


def evaluate(budget: Mapping[str, Any], manifest: Mapping[str, Any], *, writer_identity: Optional[str] = None) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    files: List[Dict[str, Any]] = manifest["files"]
    file_count = manifest["file_count"]
    total_bytes = manifest["total_bytes"]
    manifest_paths = {item["path"] for item in files}

    if writer_identity is not None and writer_identity != budget["sole_writer"]:
        findings.append(_finding("root", "CB-SOLE-WRITER", f"writer identity {writer_identity!r} does not match declared sole_writer {budget['sole_writer']!r}"))

    fc = budget["file_count"]
    if not (fc["min"] <= file_count <= fc["max"]):
        findings.append(_finding("root", "CB-FILE-COUNT", f"file_count {file_count} outside budget [{fc['min']},{fc['max']}]"))

    tb = budget["total_bytes"]
    if not (tb["min"] <= total_bytes <= tb["max"]):
        findings.append(_finding("root", "CB-TOTAL-BYTES", f"total_bytes {total_bytes} outside budget [{tb['min']},{tb['max']}]"))

    allowed_patterns = budget["allowed_paths"]
    for item in files:
        if not any(fnmatch.fnmatchcase(item["path"], pattern) for pattern in allowed_patterns):
            findings.append(_finding(item["path"], "CB-UNALLOWED-PATH", "generated path is not covered by any allowed_paths pattern; a different generated family may have been swept in"))

    for prefix in budget["required_subtrees"]:
        norm = prefix if prefix.endswith("/") else prefix + "/"
        if not any(path.startswith(norm) for path in manifest_paths):
            findings.append(_finding(prefix, "CB-INCOMPLETE-SUBTREE", f"required subtree has no generated files: {prefix}"))

    for rule in budget["realism"]:
        matches = [item for item in files if fnmatch.fnmatchcase(item["path"], rule["pattern"])]
        if not matches:
            findings.append(_finding(rule["pattern"], "CB-MISSING-REALISM-TARGET", f"no generated file matches realism pattern: {rule['pattern']}"))
            continue
        for item in matches:
            if item["bytes"] < rule["min_bytes"]:
                findings.append(_finding(item["path"], "CB-UNREALISTIC-PAYLOAD", f"{rule['kind']} file below production-realism floor: {item['bytes']} < {rule['min_bytes']} bytes"))

    if budget["require_negative_path"]:
        patterns = budget["negative_path_patterns"]
        if not any(fnmatch.fnmatchcase(path, pattern) for path in manifest_paths for pattern in patterns):
            findings.append(_finding("root", "CB-MISSING-NEGATIVE-PATH", "no generated path demonstrates a negative/error case; only happy-path output was produced"))

    max_ratio = budget["max_duplicate_digest_ratio"]
    if max_ratio is not None and files:
        counts: Dict[str, int] = {}
        for item in files:
            counts[item["digest"]] = counts.get(item["digest"], 0) + 1
        worst = max(counts.values())
        ratio = worst / len(files)
        if ratio > max_ratio:
            findings.append(_finding("root", "CB-SYNTHETIC-CONTENT", f"{worst}/{len(files)} generated files share identical byte content (ratio {ratio:.2f} > {max_ratio}); output looks synthesized rather than production-realistic"))

    expected_manifest = budget["expected_manifest"]
    if expected_manifest is not None:
        explained = set(budget["explained_diffs"])
        expected_by_path = {item["path"]: item["digest"] for item in expected_manifest}
        actual_by_path = {item["path"]: item["digest"] for item in files}
        added = sorted(set(actual_by_path) - set(expected_by_path) - explained)
        removed = sorted(set(expected_by_path) - set(actual_by_path) - explained)
        changed = sorted(path for path in (set(actual_by_path) & set(expected_by_path)) - explained if actual_by_path[path] != expected_by_path[path])
        tolerance = budget["diff_tolerance"]
        if len(added) > tolerance["max_added"]:
            findings.append(_finding("root", "CB-UNEXPLAINED-DIFF-ADDED", f"{len(added)} unexplained added path(s), e.g. {added[0]}"))
        if len(removed) > tolerance["max_removed"]:
            findings.append(_finding("root", "CB-UNEXPLAINED-DIFF-REMOVED", f"{len(removed)} unexplained removed path(s), e.g. {removed[0]}"))
        if len(changed) > tolerance["max_changed"]:
            findings.append(_finding("root", "CB-UNEXPLAINED-DIFF-CHANGED", f"{len(changed)} unexplained changed path(s), e.g. {changed[0]}"))

    verdict = "PASS" if not findings else "FAIL"
    report: Dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "budget_id": budget["budget_id"],
        "task_id": budget["task_id"],
        "manifest_digest": manifest.get("manifest_digest"),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "verdict": verdict,
        "exit_code": 0 if verdict == "PASS" else 1,
        "findings": findings,
        "report_digest": "",
    }
    report["report_digest"] = digest(report)
    return report


def _error_report(message: str) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "schema": REPORT_SCHEMA, "budget_id": "unknown", "task_id": "unknown", "manifest_digest": None,
        "file_count": 0, "total_bytes": 0, "verdict": "INCONCLUSIVE", "exit_code": 2,
        "findings": [_finding("root", "CB-CONTRACT", message)], "report_digest": "",
    }
    report["report_digest"] = digest(report)
    return report


# ---------------------------------------------------------------------------
# atomic/recoverable promotion
# ---------------------------------------------------------------------------


def current_pointer(destination_root: Path) -> Optional[Dict[str, Any]]:
    return _read_json(destination_root / "current.json")


def promote(
    root: Path,
    budget: Mapping[str, Any],
    candidate_dir: Path,
    destination_root: Path,
    *,
    manifest: Mapping[str, Any],
    report: Mapping[str, Any],
    request_id: str,
    apply: bool = False,
    now: Optional[float] = None,
) -> Dict[str, Any]:
    """Promote an evaluated ``PASS`` candidate into ``destination_root``.

    Fail-closed: refuses a non-``PASS`` report (large/unexplained diffs block
    before commit), and refuses to overwrite a destination currently pointing
    at a different ``sole_writer`` (a stale fixed export owned by someone
    else). Only promotes files that match ``budget['allowed_paths']`` even if
    the caller's report is stale, so no unrelated generated family is ever
    swept in. Atomic: the destination's ``current.json`` pointer is the only
    thing a reader trusts, and it is updated with a single temp-file rename
    only after the staged tree is verified byte-for-byte against the
    evaluated manifest. Recoverable: re-running after a crash either finds
    the already-staged tree matches (repairs just the pointer) or fails
    closed on a genuine mismatch — it never silently re-derives content.
    """
    if report.get("verdict") != "PASS":
        raise BudgetError("CB-BLOCKED-VERDICT", f"refusing to promote: budget report verdict is {report.get('verdict')!r}, not PASS")

    pointer = current_pointer(destination_root)
    if pointer is not None and pointer.get("sole_writer") not in (None, budget["sole_writer"]):
        raise BudgetError(
            "CB-OWNER-CONFLICT",
            f"destination {destination_root} is currently owned by sole_writer {pointer.get('sole_writer')!r}, "
            f"not {budget['sole_writer']!r}; refusing to overwrite a stale/foreign export in place",
        )

    allowed_patterns = budget["allowed_paths"]
    promotable = [item for item in manifest["files"] if any(fnmatch.fnmatchcase(item["path"], pattern) for pattern in allowed_patterns)]
    promotable_paths = {item["path"] for item in promotable}
    skipped = sorted(item["path"] for item in manifest["files"] if item["path"] not in promotable_paths)

    result: Dict[str, Any] = {
        "schema": PROMOTION_RESULT_SCHEMA,
        "budget_id": budget["budget_id"],
        "task_id": budget["task_id"],
        "request_id": request_id,
        "applied": False,
        "promoted_file_count": len(promotable),
        "skipped_unallowed": skipped,
        "manifest_digest": manifest.get("manifest_digest"),
    }
    if not apply:
        return result

    stage_dir = destination_root.parent / f"{destination_root.name}.stage-{request_id}"
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)
    for item in promotable:
        src = candidate_dir / item["path"]
        dst = stage_dir / item["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    staged_manifest = build_manifest(stage_dir)
    staged_by_path = {item["path"]: item["digest"] for item in staged_manifest["files"]}
    expected_by_path = {item["path"]: item["digest"] for item in promotable}
    if staged_manifest["file_count"] != len(promotable) or staged_by_path != expected_by_path:
        shutil.rmtree(stage_dir, ignore_errors=True)
        raise BudgetError("CB-STAGE-MISMATCH", "staged tree does not match the evaluated manifest; refusing to promote")

    request_dir = destination_root / request_id
    if request_dir.exists():
        existing_manifest = build_manifest(request_dir)
        if existing_manifest["manifest_digest"] != staged_manifest["manifest_digest"]:
            shutil.rmtree(stage_dir, ignore_errors=True)
            raise BudgetError("CB-REQUEST-COLLISION", f"promotion target already used for a different tree: {request_dir}")
        # Recovered from a crash after staging but before the pointer update:
        # the already-promoted tree matches exactly; only the pointer needs repair.
        shutil.rmtree(stage_dir, ignore_errors=True)
    else:
        destination_root.mkdir(parents=True, exist_ok=True)
        stage_dir.replace(request_dir)

    pointer_value = {
        "schema": POINTER_SCHEMA,
        "budget_id": budget["budget_id"],
        "task_id": budget["task_id"],
        "sole_writer": budget["sole_writer"],
        "request_id": request_id,
        "manifest_digest": manifest.get("manifest_digest"),
        "promoted_at": _now_iso(now),
    }
    _atomic_write_json(destination_root / "current.json", pointer_value)

    result["applied"] = True
    result["promoted_path"] = str(request_dir)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    m = sub.add_parser("manifest", help="Build a candidate-manifest@v1 for a run-specific candidate root")
    m.add_argument("--root", required=True, type=Path)
    m.add_argument("--task-id", required=True)
    m.add_argument("--request-id", required=True)
    m.add_argument("--logs-root", default="output/logs")
    m.add_argument("--out", type=Path, default=None)
    m.add_argument("--json", action="store_true")

    e = sub.add_parser("evaluate", help="Evaluate a candidate manifest against a candidate-budget@v1")
    e.add_argument("--root", required=True, type=Path)
    e.add_argument("--budget", required=True, type=Path)
    e.add_argument("--task-id", required=True)
    e.add_argument("--request-id", required=True)
    e.add_argument("--logs-root", default="output/logs")
    e.add_argument("--writer-identity", default=None)
    e.add_argument("--out-report", type=Path, default=None)
    e.add_argument("--json", action="store_true")

    p = sub.add_parser("promote", help="Atomically promote an evaluated PASS candidate into its destination")
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--budget", required=True, type=Path)
    p.add_argument("--task-id", required=True)
    p.add_argument("--request-id", required=True)
    p.add_argument("--logs-root", default="output/logs")
    p.add_argument("--destination", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path, help="candidate-budget-report@v1 produced by 'evaluate'")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.command == "manifest":
        cdir = candidate_root(root, task_id=args.task_id, request_id=args.request_id, logs_root=args.logs_root)
        result = build_manifest(cdir)
        if args.out:
            _atomic_write_json(args.out, result)
        if args.json:
            print(json.dumps(result, sort_keys=True, indent=2))
        else:
            print(f"VERDICT PASS files={result['file_count']} bytes={result['total_bytes']}")
        return 0

    if args.command == "evaluate":
        try:
            budget = load_budget(args.budget)
            cdir = candidate_root(root, task_id=args.task_id, request_id=args.request_id, logs_root=args.logs_root)
            manifest = build_manifest(cdir)
            report = evaluate(budget, manifest, writer_identity=args.writer_identity)
        except BudgetError as exc:
            report = _error_report(str(exc))
        if args.out_report:
            _atomic_write_json(args.out_report, report)
        if args.json:
            print(json.dumps(report, sort_keys=True, indent=2))
        else:
            print(f"VERDICT {report['verdict']} findings={len(report['findings'])}")
        return int(report["exit_code"])

    if args.command == "promote":
        try:
            budget = load_budget(args.budget)
            cdir = candidate_root(root, task_id=args.task_id, request_id=args.request_id, logs_root=args.logs_root)
            manifest = build_manifest(cdir)
            report = _read_json(args.report) or {}
            result = promote(root, budget, cdir, args.destination.resolve(), manifest=manifest, report=report, request_id=args.request_id, apply=args.apply)
        except BudgetError as exc:
            print(f"VERDICT FAIL {exc.rule}: {exc.message}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(result, sort_keys=True, indent=2))
        else:
            print(f"VERDICT {'APPLIED' if result['applied'] else 'DRY-RUN'} files={result['promoted_file_count']}")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
