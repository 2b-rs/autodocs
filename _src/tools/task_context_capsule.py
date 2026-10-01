#!/usr/bin/env python3
"""Read-only bounded Task context/resume capsule generator.

Composes three existing read-only tools into one small, budget-bounded JSON
"resume capsule" plus a short human summary, so an agent that hits a context
or tool-budget boundary -- or that must verify a predecessor's claim before
continuing -- can pick a Task back up without repeating completed work,
changing owner, or dropping a blocker:

- ``legacy_task_doctor.py`` (Task 0038-04) supplies the normalized Task/
  Feature/claim/prerequisite/authority-selector model and structural
  findings. This module never reparses ``TODO.md``/``DONE.md``/claims itself.
- ``legacy_scope_planner.py`` (Task 0038-06) supplies the authoritative
  ``issue-regeneration-dag@v1`` loader, its validator, and its graph-walking
  helpers (``_source_stages``/``_descendants``/``_producer_chain``,
  ``_infer_claim_scope``). This capsule reuses exactly those graph
  primitives to expand a claim's *explicit* write scope into its *derived*
  (DAG-downstream) scope. It deliberately does not fabricate a full
  collision-planner participant/Git/runner snapshot: this tool answers "what
  would be downstream of my own declared scope", not "do I collide with
  another active claim", which remains ``legacy_scope_planner.plan_request``'s
  job.
- ``runner_transaction.py`` (Task 0038-10) supplies the immutable per-attempt
  ``result.json`` and the atomic ``current.json`` pointer under
  ``output/logs/<task_id>/``. This module only reads those files -- never
  writes, moves, or archives them -- to report the "pending request/result"
  and "completed phases" fields from the exact same evidence the runner
  itself persisted.

This tool never mutates a file, claim, ref, or the runner slot. It performs
no Git or subprocess call and no network access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

import legacy_scope_planner
import legacy_task_doctor

CAPSULE_SCHEMA = "task-context-capsule@v1"
RESULT_SCHEMA = "legacy-runner-transaction-result@v1"
CURRENT_POINTER_SCHEMA = "legacy-runner-current-pointer@v1"

DEFAULT_MAX_CAPSULE_BYTES = 8192
MAX_INPUT_BYTES = 12 * 1024 * 1024
MAX_RESULT_BYTES = 4 * 1024 * 1024
MAX_POINTER_BYTES = 64 * 1024
MAX_NEXT_ACTION_CHARS = 700
MAX_FINDINGS = 15
MAX_DERIVED_SCOPE = 25
MAX_ATTEMPT_PHASES = 40
MAX_ATTEMPT_FINDINGS = 10
MAX_PREREQUISITES = 60

AUTHORITY_INPUT_PATHS = ("AGENTS.md", "SANDBOX.md", "PRIVILEGED.md", "agent-workflow.json")

TASK_ID_RE = legacy_task_doctor.TASK_ID_RE

# Truncation drops the lowest-priority list fields first, in this order, one
# item at a time, until the compact-canonical capsule fits the byte budget.
# The core Task/claim identity and next-action are shrunk only as a last
# resort, and the schema/verdict/task_id/claim identity are never dropped.
_TRUNCATION_ORDER = (
    "material_findings",
    "scope.derived",
    "prerequisites",
    "completed_phases",
    "retained_evidence",
    "authority.input_digests",
)
# Lowest-value-first: agent-workflow.json and PRIVILEGED.md change least often
# and are least likely to matter for an immediate resume decision; AGENTS.md
# is dropped last because its digest is most load-bearing for authority drift.
_AUTHORITY_DIGEST_DROP_ORDER = ("agent-workflow.json", "PRIVILEGED.md", "SANDBOX.md", "AGENTS.md")


class CapsuleInputError(RuntimeError):
    """A required input could not be read safely."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_relative_path(value: str) -> bool:
    if not value or "\\" in value or "\x00" in value:
        return False
    pure = PurePosixPath(value)
    return not pure.is_absolute() and ".." not in pure.parts


def _read_regular_utf8(root: Path, relative: str, limit: int) -> Optional[bytes]:
    """Read a bounded, safe, regular, non-symlink UTF-8-checked file, or None."""
    if not _safe_relative_path(relative):
        return None
    path = root / relative
    try:
        info = path.lstat()
    except OSError:
        return None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        return None
    try:
        raw = path.read_bytes()
        raw.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return raw


def _read_json_bounded(root: Path, relative: str, limit: int, expected_schema: str) -> Optional[Dict[str, Any]]:
    raw = _read_regular_utf8(root, relative, limit)
    if raw is None:
        return None
    try:
        value = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict) or value.get("schema") != expected_schema:
        return None
    return value


def _canonical_compact_bytes(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


# --------------------------------------------------------------------------
# Doctor-derived Task/Feature/claim/authority extraction
# --------------------------------------------------------------------------


def _find_task(doctor_report: Mapping[str, object], task_id: str) -> Optional[Dict[str, object]]:
    normalized = doctor_report.get("normalized", {})
    tasks = normalized.get("tasks", []) if isinstance(normalized, dict) else []
    matches = [item for item in tasks if isinstance(item, dict) and item.get("id") == task_id]
    if not matches:
        return None
    return sorted(matches, key=lambda item: (item.get("path", ""), item.get("line", 0)))[0]


def _feature_terminal(doctor_report: Mapping[str, object], feature_id: str) -> Optional[bool]:
    normalized = doctor_report.get("normalized", {})
    features = normalized.get("features", []) if isinstance(normalized, dict) else []
    matches = [item for item in features if isinstance(item, dict) and item.get("id") == feature_id]
    if not matches:
        return None
    return any(item.get("path") == "DONE.md" for item in matches)


def _prerequisite_states(doctor_report: Mapping[str, object], task: Mapping[str, object]) -> List[Dict[str, object]]:
    normalized = doctor_report.get("normalized", {})
    tasks_by_id: Dict[str, Dict[str, object]] = {}
    for item in normalized.get("tasks", []) if isinstance(normalized, dict) else []:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            tasks_by_id.setdefault(item["id"], item)
    result: List[Dict[str, object]] = []
    prereqs = task.get("prerequisites", [])
    for prereq_id in list(prereqs)[:MAX_PREREQUISITES]:
        if not isinstance(prereq_id, str):
            continue
        if "-" in prereq_id:
            other = tasks_by_id.get(prereq_id)
            marker = other.get("marker") if other else None
            terminal = marker in ("x", "w") if other else None
            result.append({"id": prereq_id, "kind": "task", "marker": marker, "terminal": terminal})
        else:
            terminal = _feature_terminal(doctor_report, prereq_id)
            result.append({"id": prereq_id, "kind": "feature", "marker": None, "terminal": terminal})
    result.sort(key=lambda item: item["id"])
    return result


def _find_claim(
    doctor_report: Mapping[str, object],
    task_id: str,
    claim_path: Optional[str],
) -> Tuple[Optional[Dict[str, object]], bool]:
    normalized = doctor_report.get("normalized", {})
    claims = normalized.get("claims", []) if isinstance(normalized, dict) else []
    active = [
        item
        for item in claims
        if isinstance(item, dict) and item.get("task_id") == task_id and item.get("state") == "p"
    ]
    if claim_path is not None:
        selected = [item for item in active if item.get("path") == claim_path]
        return (selected[0] if selected else None), False
    if not active:
        return None, False
    ordered = sorted(active, key=lambda item: item.get("path", ""))
    return ordered[0], len(ordered) > 1


def _authority_digests(doctor_report: Mapping[str, object]) -> Dict[str, object]:
    inputs = doctor_report.get("inputs", [])
    selected = {
        item["path"]: {"sha256": item.get("sha256"), "bytes": item.get("bytes")}
        for item in inputs
        if isinstance(item, dict) and item.get("path") in AUTHORITY_INPUT_PATHS
    }
    authority = doctor_report.get("authority", {})
    return {
        "input_digests": selected,
        "selector": authority if isinstance(authority, dict) else {},
    }


def _material_findings(doctor_report: Mapping[str, object], task_id: str, claim_path: Optional[str]) -> List[Dict[str, object]]:
    findings = doctor_report.get("findings", [])
    selected: List[Dict[str, object]] = []
    for item in findings if isinstance(findings, list) else []:
        if not isinstance(item, dict):
            continue
        if item.get("subject") == task_id or (claim_path is not None and item.get("path") == claim_path):
            selected.append(
                {
                    "rule": item.get("rule"),
                    "severity": item.get("severity"),
                    "path": item.get("path"),
                    "line": item.get("line"),
                    "message": item.get("message"),
                }
            )
    return selected[:MAX_FINDINGS]


# --------------------------------------------------------------------------
# Explicit/derived write-scope (legacy_scope_planner DAG composition)
# --------------------------------------------------------------------------


def _derive_scope(root: Path, explicit_scopes: Sequence[str]) -> Tuple[List[Dict[str, object]], bool]:
    dag_relative = legacy_scope_planner.DAG_PATH
    raw = _read_regular_utf8(root, dag_relative, legacy_scope_planner.MAX_DAG_BYTES)
    if raw is None:
        return [], False
    try:
        dag = legacy_scope_planner._validate_dag(json.loads(raw.decode("utf-8")))
    except (json.JSONDecodeError, legacy_scope_planner.ContractError):
        return [], False

    stages = dag["stages"]
    derived: List[Dict[str, object]] = []
    seen: Set[Tuple[str, str]] = set()
    for raw_path in explicit_scopes:
        scope = legacy_scope_planner._infer_claim_scope(root, raw_path)
        if scope is None:
            continue
        initial = legacy_scope_planner._source_stages(stages, scope["path"], scope["kind"])
        if not initial:
            continue
        for stage_id in sorted(legacy_scope_planner._descendants(stages, initial)):
            stage = next(item for item in stages if item["id"] == stage_id)
            chain = legacy_scope_planner._producer_chain(stages, scope["path"], stage_id, scope["kind"])
            for output in stage["outputs"]:
                key = (scope["path"], output)
                if key in seen:
                    continue
                seen.add(key)
                derived.append(
                    {
                        "source": scope["path"],
                        "producer": stage_id,
                        "output": output,
                        "chain": list(chain) + [output],
                    }
                )
    derived.sort(key=lambda item: (item["source"], item["output"], item["producer"]))
    return derived[:MAX_DERIVED_SCOPE], True


# --------------------------------------------------------------------------
# 0038-10 immutable per-attempt result / current pointer
# --------------------------------------------------------------------------


def _pending_attempt(root: Path, task_id: str) -> Dict[str, object]:
    info: Dict[str, object] = {"current_pointer": None, "result": None, "result_consistent": None}
    if not _safe_relative_path(task_id):
        return info
    pointer_relative = f"output/logs/{task_id}/current.json"
    pointer = _read_json_bounded(root, pointer_relative, MAX_POINTER_BYTES, CURRENT_POINTER_SCHEMA)
    if pointer is None:
        return info
    info["current_pointer"] = {
        "task_id": pointer.get("task_id"),
        "request_id": pointer.get("request_id"),
        "verdict": pointer.get("verdict"),
        "lifecycle_state": pointer.get("lifecycle_state"),
        "updated_at": pointer.get("updated_at"),
        "result_path": pointer.get("result_path"),
    }
    result_relative = pointer.get("result_path")
    if not isinstance(result_relative, str) or not _safe_relative_path(result_relative):
        return info
    raw = _read_regular_utf8(root, result_relative, MAX_RESULT_BYTES)
    if raw is None:
        return info
    expected_sha = pointer.get("result_sha256")
    info["result_consistent"] = isinstance(expected_sha, str) and _sha256_bytes(raw) == expected_sha
    try:
        result = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return info
    if not isinstance(result, dict) or result.get("schema") != RESULT_SCHEMA:
        return info
    phases = [
        {"name": item.get("name"), "status": item.get("status"), "exit_code": item.get("exit_code")}
        for item in result.get("phases", [])
        if isinstance(item, dict)
    ][:MAX_ATTEMPT_PHASES]
    findings = [
        {"rule": item.get("rule"), "message": item.get("message")}
        for item in result.get("findings", [])
        if isinstance(item, dict)
    ][:MAX_ATTEMPT_FINDINGS]
    info["result"] = {
        "request_id": result.get("request_id"),
        "verdict": result.get("verdict"),
        "lifecycle_state": result.get("lifecycle_state"),
        "phase": result.get("phase"),
        "phases": phases,
        "findings": findings,
        "commits": result.get("commits"),
        "recovery": result.get("recovery"),
        "evidence": result.get("evidence"),
    }
    return info


def _completed_phases(pending_attempt: Mapping[str, object]) -> List[str]:
    result = pending_attempt.get("result")
    if not isinstance(result, dict):
        return []
    names: List[str] = []
    for phase in result.get("phases", []):
        if isinstance(phase, dict) and phase.get("status") == "passed" and isinstance(phase.get("name"), str):
            if phase["name"] not in names:
                names.append(phase["name"])
    return names


# --------------------------------------------------------------------------
# Claim "## Next step" extraction (raw claim text; doctor exposes presence
# only, not content)
# --------------------------------------------------------------------------

_NEXT_STEP_HEADING_RE = re.compile(r"^##\s+Next step\b", re.IGNORECASE)
_ANY_HEADING_RE = re.compile(r"^#{2,6}\s+")


def _extract_next_step(root: Path, claim_path: str) -> Tuple[Optional[str], bool]:
    raw = _read_regular_utf8(root, claim_path, MAX_INPUT_BYTES)
    if raw is None:
        return None, False
    lines = raw.decode("utf-8").splitlines()
    heading_indexes = [index for index, line in enumerate(lines) if _ANY_HEADING_RE.match(line)]
    starts = [index for index, line in enumerate(lines) if _NEXT_STEP_HEADING_RE.match(line)]
    if not starts:
        return None, False
    start = starts[-1]
    if heading_indexes and heading_indexes[-1] != start:
        return None, False
    body = lines[start + 1 :]
    meaningful: List[str] = []
    for line in body:
        stripped = line.strip()
        if not stripped or stripped.startswith(("<!--", "-->", "```", "~~~")):
            continue
        meaningful.append(re.sub(r"^[-*+]\s+", "", stripped))
    if not meaningful:
        return None, False
    text = " ".join(meaningful)
    truncated = len(text) > MAX_NEXT_ACTION_CHARS
    if truncated:
        text = text[: MAX_NEXT_ACTION_CHARS - 1].rstrip() + "…"
    return text, truncated


# --------------------------------------------------------------------------
# Capsule assembly and budget enforcement
# --------------------------------------------------------------------------


def _empty_capsule(verdict: str, task_id: str, reason: str) -> Dict[str, object]:
    return {
        "schema": CAPSULE_SCHEMA,
        "verdict": verdict,
        "task_id": task_id,
        "reason": reason,
        "task": None,
        "feature": None,
        "prerequisites": [],
        "claim": None,
        "claim_ambiguous": False,
        "authority": {"input_digests": {}, "selector": {}},
        "scope": {"explicit": [], "derived": [], "dag_considered": False},
        "pending_attempt": {"current_pointer": None, "result": None, "result_consistent": None},
        "completed_phases": [],
        "material_findings": [],
        "retained_evidence": [],
        "next_action": None,
        "next_action_truncated": False,
        "budget": {"max_bytes": DEFAULT_MAX_CAPSULE_BYTES, "actual_bytes": 0},
        "truncated": {},
        "summary": [f"task-context-capsule {verdict}: {task_id}: {reason}"],
    }


def build_capsule(
    root: Path,
    task_id: str,
    *,
    claim_path: Optional[str] = None,
    reachable_commits: Optional[Set[str]] = None,
    max_bytes: int = DEFAULT_MAX_CAPSULE_BYTES,
) -> Dict[str, object]:
    """Build one bounded, read-only Task context/resume capsule.

    Never mutates the repository, a claim, a ref, or the runner slot.
    """
    root = root.resolve()
    if not TASK_ID_RE.fullmatch(task_id):
        return _empty_capsule("INCOMPLETE", task_id, "task_id is not a well-formed Task/Subtask identifier")

    doctor_report = legacy_task_doctor.scan_repository(root, reachable_commits=reachable_commits)
    if doctor_report.get("verdict") == "INCOMPLETE":
        return _empty_capsule("INCOMPLETE", task_id, "legacy_task_doctor scan is incomplete; inputs unstable")

    task = _find_task(doctor_report, task_id)
    if task is None:
        return _empty_capsule("TASK-NOT-FOUND", task_id, "no Task with this ID in TODO.md or DONE.md")

    feature_id = task.get("feature_id")
    feature_record = None
    if isinstance(feature_id, str):
        normalized = doctor_report.get("normalized", {})
        for item in normalized.get("features", []) if isinstance(normalized, dict) else []:
            if isinstance(item, dict) and item.get("id") == feature_id:
                feature_record = {"id": item.get("id"), "title": item.get("title"), "path": item.get("path")}
                break

    prerequisites = _prerequisite_states(doctor_report, task)
    claim, ambiguous = _find_claim(doctor_report, task_id, claim_path)
    authority = _authority_digests(doctor_report)

    claim_summary: Optional[Dict[str, object]] = None
    explicit_scope: List[str] = []
    next_action: Optional[str] = None
    next_action_truncated = False
    retained_evidence: List[Dict[str, object]] = []
    if claim is not None:
        claim_summary = {
            "path": claim.get("path"),
            "owner_token": claim.get("owner_token"),
            "request_id": claim.get("request_id"),
            "base_commit": claim.get("base_commit"),
            "capability_class": claim.get("capability_class"),
            "state": claim.get("state"),
            "next_step_present": claim.get("next_step_present"),
        }
        explicit_scope = sorted(str(item) for item in claim.get("scopes", []))
        next_action, next_action_truncated = _extract_next_step(root, str(claim.get("path")))
        retained_evidence.append({"path": claim.get("path"), "sha256": claim.get("sha256")})
    else:
        next_action = f"No active [p] claim resolves to Task {task_id}; open or resume a claim before continuing."

    derived_scope, dag_considered = _derive_scope(root, explicit_scope)
    pending_attempt = _pending_attempt(root, task_id)
    completed_phases = _completed_phases(pending_attempt)
    material_findings = _material_findings(doctor_report, task_id, claim.get("path") if claim else None)

    result_info = pending_attempt.get("result")
    if isinstance(result_info, dict):
        evidence = result_info.get("evidence")
        result_path = None
        current_pointer = pending_attempt.get("current_pointer")
        if isinstance(current_pointer, dict):
            result_path = current_pointer.get("result_path")
        if isinstance(result_path, str):
            raw = _read_regular_utf8(root, result_path, MAX_RESULT_BYTES)
            if raw is not None:
                retained_evidence.append({"path": result_path, "sha256": _sha256_bytes(raw)})
        if isinstance(evidence, dict):
            for key in ("journal", "prepared_result", "promotion_journal"):
                value = evidence.get(key)
                if isinstance(value, str):
                    retained_evidence.append({"path": value, "sha256": None})

    verdict = "OK"
    if task.get("marker") == "p" and claim is None:
        verdict = "OK"  # capsule is still buildable; doctor's own findings surface the gap

    capsule: Dict[str, object] = {
        "schema": CAPSULE_SCHEMA,
        "verdict": verdict,
        "task_id": task_id,
        "reason": None,
        "task": {
            "id": task.get("id"),
            "marker": task.get("marker"),
            "feature_id": feature_id,
            "title": task.get("title"),
            "path": task.get("path"),
            "line": task.get("line"),
        },
        "feature": feature_record,
        "prerequisites": prerequisites,
        "claim": claim_summary,
        "claim_ambiguous": ambiguous,
        "authority": authority,
        "scope": {"explicit": explicit_scope, "derived": derived_scope, "dag_considered": dag_considered},
        "pending_attempt": pending_attempt,
        "completed_phases": completed_phases,
        "material_findings": material_findings,
        "retained_evidence": retained_evidence,
        "next_action": next_action,
        "next_action_truncated": next_action_truncated,
        "budget": {"max_bytes": max_bytes, "actual_bytes": 0},
        "truncated": {},
    }
    capsule["summary"] = _build_summary(capsule)
    _enforce_budget(capsule, max_bytes)
    return capsule


def _build_summary(capsule: Mapping[str, object]) -> List[str]:
    task = capsule.get("task") or {}
    claim = capsule.get("claim")
    prereqs = capsule.get("prerequisites", [])
    terminal = sum(1 for item in prereqs if item.get("terminal"))
    pending = capsule.get("pending_attempt", {})
    attempt_verdict = None
    result = pending.get("result") if isinstance(pending, dict) else None
    if isinstance(result, dict):
        attempt_verdict = result.get("verdict")
    lines = [
        f"task-context-capsule {capsule.get('verdict')}: {capsule.get('task_id')} [{task.get('marker')}]",
        f"prerequisites: {terminal}/{len(prereqs)} terminal",
        f"claim: {claim.get('owner_token')}" if claim else "claim: none active",
        f"pending attempt: {attempt_verdict or 'none'}",
        f"completed phases: {len(capsule.get('completed_phases', []))}",
        f"material findings: {len(capsule.get('material_findings', []))}",
    ]
    next_action = capsule.get("next_action")
    if next_action:
        lines.append(f"next: {next_action[:120]}")
    return lines[:10]


def _drop_last(capsule: Dict[str, object], dotted_field: str) -> bool:
    if dotted_field == "scope.derived":
        container = capsule["scope"]["derived"]
    elif dotted_field == "authority.input_digests":
        digests = capsule["authority"]["input_digests"]
        for name in _AUTHORITY_DIGEST_DROP_ORDER:
            if name in digests:
                del digests[name]
                capsule["truncated"][dotted_field] = capsule["truncated"].get(dotted_field, 0) + 1
                return True
        return False
    else:
        container = capsule[dotted_field]
    if not container:
        return False
    container.pop()
    capsule["truncated"][dotted_field] = capsule["truncated"].get(dotted_field, 0) + 1
    return True


def _shrink_next_action(capsule: Dict[str, object]) -> bool:
    """Last-resort reduction once every truncatable list/mapping is empty.

    Strictly decreases the un-ellipsized core length on every call so this
    can never loop forever; once the core is at or below the floor, the
    field becomes ``None`` and further shrinking is reported as impossible.
    """
    next_action = capsule.get("next_action")
    if not isinstance(next_action, str) or not next_action:
        return False
    floor = 16
    core = next_action[:-1] if next_action.endswith("…") else next_action
    if len(core) <= floor:
        capsule["next_action"] = None
        capsule["next_action_truncated"] = True
        return True
    new_core = core[: max(floor, len(core) // 2)]
    if len(new_core) >= len(core):
        capsule["next_action"] = None
        capsule["next_action_truncated"] = True
        return True
    capsule["next_action"] = new_core.rstrip() + "…"
    capsule["next_action_truncated"] = True
    return True


_MAX_TRUNCATION_STEPS = 10_000


def _enforce_budget(capsule: Dict[str, object], max_bytes: int) -> None:
    capsule["budget"]["max_bytes"] = max_bytes
    capsule["summary"] = _build_summary(capsule)
    size = len(_canonical_compact_bytes(capsule))
    steps = 0
    while size > max_bytes:
        steps += 1
        if steps > _MAX_TRUNCATION_STEPS:
            # Defensive bound only: _drop_last and _shrink_next_action are each
            # individually guaranteed to make monotonic progress or return
            # False, so this should be unreachable.
            break
        progressed = False
        for field in _TRUNCATION_ORDER:
            if _drop_last(capsule, field):
                progressed = True
                capsule["summary"] = _build_summary(capsule)
                size = len(_canonical_compact_bytes(capsule))
                if size <= max_bytes:
                    break
        if size <= max_bytes:
            break
        if not progressed:
            if _shrink_next_action(capsule):
                capsule["summary"] = _build_summary(capsule)
                size = len(_canonical_compact_bytes(capsule))
                continue
            break
    # Recording the achieved size changes the "actual_bytes" field's own
    # serialized width (e.g. 0 -> 4 digits), which perturbs the true byte
    # count it is reporting. Iterate to a fixed point so the stored value is
    # always exactly the real serialized length of the returned capsule.
    for _ in range(4):
        capsule["budget"]["actual_bytes"] = size
        new_size = len(_canonical_compact_bytes(capsule))
        if new_size == size:
            break
        size = new_size
    else:
        capsule["budget"]["actual_bytes"] = size


def render_summary(capsule: Mapping[str, object]) -> Tuple[str, ...]:
    value = capsule.get("summary", ())
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return ("task-context-capsule INCOMPLETE: malformed capsule summary",)
    return tuple(value[:10])


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="repository root")
    parser.add_argument("--task-id", required=True, help="exact Task/Subtask ID, e.g. 0038-07")
    parser.add_argument("--claim-path", default=None, help="disambiguate an exact active claim path")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_CAPSULE_BYTES, help="capsule byte budget")
    parser.add_argument("--json", action="store_true", help="emit compact canonical JSON")
    args = parser.parse_args(argv)

    capsule = build_capsule(args.root, args.task_id, claim_path=args.claim_path, max_bytes=args.max_bytes)
    if args.json:
        sys.stdout.buffer.write(_canonical_compact_bytes(capsule))
    else:
        for line in render_summary(capsule):
            print(line)
    return {"OK": 0, "TASK-NOT-FOUND": 1, "INCOMPLETE": 2}.get(str(capsule.get("verdict")), 2)


if __name__ == "__main__":
    raise SystemExit(main())
