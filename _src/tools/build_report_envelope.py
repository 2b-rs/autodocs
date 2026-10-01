#!/usr/bin/env python3
"""Build-report envelope v2 and explicit 1.0 migration (Task 0037-26.06).

build-report schema ``1.0`` is never treated as current. Callers must run
``migrate_build_report_v1`` with the missing identity fields supplied; combine
never infers a cohort from latest mtime.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

UUIDV7_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
LEGACY_SCHEMA_VERSION = "1.0"
SCHEMA_VERSION = "2.0"
SCHEMA_NAME = "build-report@v2"
REQUIRED_STAGES = ("i18n_merge", "i18n_diagrams", "html_generate", "validate")
ALLOWED_FINDING_SEVERITIES = frozenset(("info", "warning", "error"))
TRIGGER_KINDS = frozenset(("issue", "criterion", "campaign"))
REPORT_OUTPUT_PREFIXES = ("output/build-reports/",)
CLASSIFICATIONS = frozenset({"public", "internal", "restricted"})
ENVIRONMENTS = frozenset({"synthetic", "development-test", "production", "assessment"})


class EnvelopeError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def member_digest_for_path(path: str, content: bytes, source_commit: str, media_type: str) -> dict:
    return {
        "path": path,
        "digest": sha256_bytes(content),
        "size_bytes": len(content),
        "media_type": media_type,
        "source_commit": source_commit,
        "classification": "internal",
    }


def artifact_set_from_members(members: Sequence[Mapping[str, Any]]) -> dict:
    normalized = []
    for member in members:
        item = dict(member)
        for key in ("path", "digest", "size_bytes", "media_type", "source_commit"):
            if key not in item:
                raise EnvelopeError("BR-ARTIFACT", f"artifact member missing {key}")
        if not SHA256_RE.match(str(item["digest"])):
            raise EnvelopeError("BR-ARTIFACT", "digest must be sha256:<64 hex>")
        if not COMMIT_RE.match(str(item["source_commit"])):
            raise EnvelopeError("BR-ARTIFACT", "source_commit must be 40 hex chars")
        if not isinstance(item["size_bytes"], int) or isinstance(item["size_bytes"], bool):
            raise EnvelopeError("BR-ARTIFACT", "size_bytes must be an integer")
        if item["size_bytes"] < 0:
            raise EnvelopeError("BR-ARTIFACT", "size_bytes must be >= 0")
        normalized.append(item)
    ordered = sorted(normalized, key=lambda m: m["path"])
    lines = [f"{m['path']}:{m['digest']}:{m['size_bytes']}" for m in ordered]
    return {
        "schema_version": "1.0",
        "members": ordered,
        "set_digest": sha256_bytes("\n".join(lines).encode("utf-8")),
    }


def _validate_trigger(trigger: Any) -> Optional[str]:
    if not isinstance(trigger, dict):
        return "trigger must be an object"
    kind = trigger.get("kind")
    ident = trigger.get("id")
    if kind not in TRIGGER_KINDS:
        return "trigger.kind must be issue, criterion, or campaign"
    if not isinstance(ident, str) or not ident.strip():
        return "trigger.id must be a non-empty string"
    return None


def _validate_commits(data: Mapping[str, Any], errors: List[str]) -> None:
    for field in ("source_commit", "tool_commit", "config_commit"):
        value = data.get(field)
        if not isinstance(value, str) or not COMMIT_RE.match(value):
            errors.append(f"{field} must be a 40-character lowercase hex Git commit")


def _validate_artifact_set(data: Mapping[str, Any], field: str, errors: List[str]) -> None:
    aset = data.get(field)
    if not isinstance(aset, dict):
        errors.append(f"{field} must be an artifact-set object")
        return
    members = aset.get("members")
    if not isinstance(members, list) or not members:
        errors.append(f"{field}.members must be a non-empty array")
        return
    try:
        rebuilt = artifact_set_from_members(members)
    except EnvelopeError as exc:
        errors.append(f"{field}: {exc.message}")
        return
    digest = aset.get("set_digest")
    if digest != rebuilt["set_digest"]:
        errors.append(f"{field}.set_digest does not match canonical member digest")


def _validate_findings(findings: Any, errors: List[str]) -> bool:
    has_error = False
    if not isinstance(findings, list):
        errors.append("findings must be an array")
        return False
    for index, finding in enumerate(findings):
        prefix = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{prefix} must be an object")
            continue
        fid = finding.get("finding_id")
        if not isinstance(fid, str) or not UUIDV7_RE.match(fid):
            errors.append(f"{prefix}.finding_id must be a UUIDv7 (unstable finding rejected)")
        category = finding.get("category")
        severity = finding.get("severity")
        message = finding.get("message")
        if not isinstance(category, str) or not category.strip():
            errors.append(f"{prefix}.category must be a non-empty string")
        if not isinstance(severity, str) or severity not in ALLOWED_FINDING_SEVERITIES:
            errors.append(f"{prefix}.severity must be one of {tuple(sorted(ALLOWED_FINDING_SEVERITIES))!r}")
        if not isinstance(message, str) or not message.strip():
            errors.append(f"{prefix}.message must be a non-empty string")
        if severity == "error" and isinstance(message, str) and message.strip():
            has_error = True
    return has_error


def _path_is_report_artifact(path: Any) -> bool:
    if not isinstance(path, str):
        return False
    normalized = path.replace("\\", "/").lstrip("./")
    return any(normalized.startswith(prefix) or f"/{prefix}" in f"/{normalized}"
               for prefix in REPORT_OUTPUT_PREFIXES)


def _self_injection_error(data: Mapping[str, Any]) -> Optional[str]:
    inputs = data.get("inputs")
    output_members = ((data.get("output_artifact_set") or {}).get("members") or [])
    output_paths = {m.get("path") for m in output_members if isinstance(m, dict)}
    if not isinstance(inputs, list):
        return None
    for item in inputs:
        if _path_is_report_artifact(item):
            return "self-validating report injection: inputs must not include build-report artifacts"
        if item in output_paths:
            return "self-validating report injection: an output path is also listed as an input"
    for member in output_members:
        if isinstance(member, dict) and _path_is_report_artifact(member.get("path")):
            if data.get("report_kind") == "validate":
                return "self-validating report injection: validate outputs must not be the report under validation"
    return None


def validate_v2_subreport(data: Mapping[str, Any], selected_run_id: Optional[str] = None) -> List[str]:
    errors: List[str] = []
    if data.get("schema_version") == LEGACY_SCHEMA_VERSION:
        errors.append(
            "schema_version 1.0 is retired; migrate explicitly with migrate_build_report_v1"
        )
        return errors
    if data.get("schema_version") != SCHEMA_VERSION or data.get("schema") != SCHEMA_NAME:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r} and schema {SCHEMA_NAME!r}")

    kind = data.get("report_kind")
    if kind not in REQUIRED_STAGES and kind != "combined":
        errors.append(f"report_kind must be one of {REQUIRED_STAGES!r} or 'combined'")

    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not UUIDV7_RE.match(run_id):
        errors.append("run_id must be a UUIDv7")
    elif selected_run_id is not None and run_id != selected_run_id:
        errors.append(f"run_id must exactly match the selected cohort {selected_run_id!r}")

    archive = data.get("run_archive_ref")
    if not isinstance(archive, str) or not archive.strip():
        errors.append("run_archive_ref must be a non-empty string")

    for field in ("tool", "command"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    if not isinstance(data.get("inputs"), list) or not all(isinstance(x, str) for x in data.get("inputs") or []):
        errors.append("inputs must be an array of strings")
    if not isinstance(data.get("changed_artifacts"), list) or not all(
        isinstance(x, str) for x in data.get("changed_artifacts") or []
    ):
        errors.append("changed_artifacts must be an array of strings")

    _validate_commits(data, errors)
    trigger_err = _validate_trigger(data.get("trigger"))
    if trigger_err:
        errors.append(trigger_err)
    _validate_artifact_set(data, "input_artifact_set", errors)
    _validate_artifact_set(data, "output_artifact_set", errors)

    success = data.get("success")
    if not isinstance(success, bool):
        errors.append("success must be a boolean")

    if not isinstance(data.get("counts"), dict):
        errors.append("counts must be an object")

    has_error = _validate_findings(data.get("findings"), errors)
    exit_code = data.get("exit_code")
    valid_exit = isinstance(exit_code, int) and not isinstance(exit_code, bool) and 0 <= exit_code <= 255
    if not valid_exit:
        errors.append("exit_code must be an integer from 0 through 255")
    elif exit_code != 0 and not has_error:
        errors.append("nonzero exit_code requires at least one error finding with a message")
    if valid_exit and isinstance(success, bool) and success != (exit_code == 0):
        errors.append("success must be true iff exit_code is 0")

    injection = _self_injection_error(data)
    if injection:
        errors.append(injection)
    return errors


def migrate_build_report_v1(
    data: Mapping[str, Any],
    *,
    run_id: str,
    source_commit: str,
    tool_commit: str,
    config_commit: str,
    trigger: Mapping[str, Any],
    input_artifact_set: Mapping[str, Any],
    output_artifact_set: Mapping[str, Any],
    findings: Optional[Sequence[Mapping[str, Any]]] = None,
) -> dict:
    """Explicit 1.0 → 2.0 migration. Missing identity is never invented."""
    if not isinstance(data, dict):
        raise EnvelopeError("BR-MIGRATE", "legacy report must be an object")
    if data.get("schema_version") != LEGACY_SCHEMA_VERSION:
        raise EnvelopeError("BR-MIGRATE", "migrate_build_report_v1 accepts only schema_version 1.0")
    if not UUIDV7_RE.match(run_id):
        raise EnvelopeError("BR-MIGRATE", "run_id must be a UUIDv7")
    migrated = dict(data)
    migrated["schema_version"] = SCHEMA_VERSION
    migrated["schema"] = SCHEMA_NAME
    migrated["run_id"] = run_id
    migrated["source_commit"] = source_commit
    migrated["tool_commit"] = tool_commit
    migrated["config_commit"] = config_commit
    migrated["trigger"] = dict(trigger)
    migrated["input_artifact_set"] = dict(input_artifact_set)
    migrated["output_artifact_set"] = dict(output_artifact_set)
    if findings is not None:
        migrated["findings"] = [dict(item) for item in findings]
    exit_code = migrated.get("exit_code")
    migrated["success"] = exit_code == 0 if isinstance(exit_code, int) and not isinstance(exit_code, bool) else False
    migrated["legacy_disposition"] = {
        "from_schema": "build-report@1.0",
        "status": "migrated",
        "adapter": "migrate_build_report_v1",
    }
    errors = validate_v2_subreport(migrated)
    if errors:
        raise EnvelopeError("BR-MIGRATE", "; ".join(errors))
    return migrated


def select_cohort_files(
    paths: Sequence[str],
    payloads: Sequence[Mapping[str, Any]],
    *,
    requested_run_id: Optional[str] = None,
    requested_archive_ref: Optional[str] = None,
) -> Tuple[str, Dict[str, dict], List[dict]]:
    """Select one run_id cohort. Files are associated by identity, never mtime order."""
    findings: List[dict] = []
    indexed = list(zip(paths, payloads))
    indexed.sort(key=lambda pair: os.path.basename(pair[0]))

    run_ids = []
    for path, data in indexed:
        if not isinstance(data, dict):
            findings.append(_finding("malformed-build-report", f"{os.path.basename(path)} is not an object", path))
            continue
        if os.path.basename(path).startswith("combined-"):
            continue
        version = data.get("schema_version")
        if version == LEGACY_SCHEMA_VERSION:
            findings.append(
                _finding(
                    "legacy-build-report-unmigrated",
                    f"{os.path.basename(path)} is build-report 1.0 and was not migrated explicitly",
                    path,
                )
            )
            continue
        rid = data.get("run_id")
        if isinstance(rid, str) and UUIDV7_RE.match(rid):
            run_ids.append(rid)

    unique_ids = sorted(set(run_ids))
    selected = requested_run_id
    if selected is None and requested_archive_ref:
        matches = [
            data.get("run_id")
            for _path, data in indexed
            if isinstance(data, dict)
            and data.get("run_archive_ref") == requested_archive_ref
            and isinstance(data.get("run_id"), str)
            and UUIDV7_RE.match(data["run_id"])
        ]
        match_set = sorted(set(matches))
        if len(match_set) == 1:
            selected = match_set[0]
        elif len(match_set) > 1:
            findings.append(
                _finding(
                    "mixed-run-cohort",
                    "run_archive_ref maps to multiple run_id values; refusing mtime or latest-file disambiguation",
                    requested_archive_ref,
                )
            )
            return "", {}, findings
        else:
            findings.append(
                _finding(
                    "malformed-build-report",
                    f"no v2 reports share run_archive_ref {requested_archive_ref!r}; refusing to substitute another run",
                    requested_archive_ref,
                )
            )
            return "", {}, findings
    if selected is None:
        if len(unique_ids) == 1:
            selected = unique_ids[0]
        elif len(unique_ids) > 1:
            findings.append(
                _finding(
                    "mixed-run-cohort",
                    "directory contains multiple run_id values; combine requires an explicit shared run_id, never latest mtime",
                    ",".join(unique_ids),
                )
            )
            return "", {}, findings
        else:
            findings.append(
                _finding(
                    "malformed-build-report",
                    "no v2 producer report with a UUIDv7 run_id is present",
                    "run_id",
                )
            )
            return "", {}, findings

    by_kind: Dict[str, dict] = {}
    for path, data in indexed:
        if not isinstance(data, dict) or os.path.basename(path).startswith("combined-"):
            continue
        if data.get("schema_version") == LEGACY_SCHEMA_VERSION:
            continue
        if data.get("run_id") != selected:
            continue
        errors = validate_v2_subreport(data, selected)
        if errors:
            findings.append(
                _finding(
                    "malformed-build-report",
                    f"{os.path.basename(path)} violates build-report@v2: " + "; ".join(errors),
                    path,
                )
            )
            continue
        kind = data["report_kind"]
        if kind in by_kind:
            findings.append(
                _finding(
                    "malformed-build-report",
                    f"duplicate stage {kind!r} for run_id {selected!r}; refusing mtime winner",
                    path,
                )
            )
            continue
        by_kind[kind] = data
    return selected, by_kind, findings


def _finding(category: str, message: str, ref: str, finding_id: Optional[str] = None) -> dict:
    item = {
        "category": category,
        "severity": "error",
        "message": message,
        "ref": ref,
    }
    if finding_id:
        item["finding_id"] = finding_id
    return item


def lineage_matches(subreports: Mapping[str, Mapping[str, Any]]) -> Optional[str]:
    if not subreports:
        return None
    keys = []
    for report in subreports.values():
        trigger = report.get("trigger") or {}
        keys.append(
            (
                report.get("run_id"),
                report.get("source_commit"),
                report.get("tool_commit"),
                report.get("config_commit"),
                trigger.get("kind"),
                trigger.get("id"),
            )
        )
    if len(set(keys)) != 1:
        return "stage reports do not share run/commit/trigger lineage"
    return None


def typed_ref(kind: str, ident: str, classification: str = "internal", environment: str = "development-test") -> dict:
    uri = ident if ident.startswith(kind + ":") else f"{kind}:{ident}"
    return {
        "schema_version": "1.0",
        "kind": kind,
        "uri": uri,
        "classification": classification,
        "environment": environment,
    }


def persist_combined_provenance(
    store,
    *,
    run_id: str,
    started_at: str,
    ended_at: str,
    success: bool,
    trigger: Mapping[str, Any],
    input_set: Mapping[str, Any],
    output_set: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
    set_id_input: str,
    set_id_output: str,
    event_ids: Mapping[str, str],
    producer_tool: str = "build_report.py",
) -> dict:
    """Write run, artifact-sets, findings, and reverse-traceable events."""
    in_members = list(input_set["members"])
    out_members = list(output_set["members"])
    in_record = {
        "schema_version": "1.0",
        "set_id": set_id_input,
        "created_at": started_at,
        "classification": "internal",
        "environment": "development-test",
        "members": in_members,
        "producer": typed_ref("run", run_id),
    }
    out_record = {
        "schema_version": "1.0",
        "set_id": set_id_output,
        "created_at": ended_at,
        "classification": "internal",
        "environment": "development-test",
        "members": out_members,
        "producer": typed_ref("run", run_id),
    }
    stored_in = store.create_artifact_set(in_record)
    stored_out = store.create_artifact_set(out_record)
    in_digest = stored_in["record"]["set_digest"]
    out_digest = stored_out["record"]["set_digest"]
    trigger_kind = trigger["kind"]
    trigger_id = trigger["id"]
    source_commit = in_members[0]["source_commit"]
    store.create_run(
        {
            "schema_version": "1.0",
            "run_id": run_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "environment": "development-test",
            "classification": "internal",
            "status": "succeeded" if success else "failed",
            "producer": typed_ref("artifact", producer_tool),
            "inputs": [
                typed_ref(trigger_kind, trigger_id),
                typed_ref("commit", source_commit),
                typed_ref("artifact-set", in_digest),
            ],
            "outputs": [typed_ref("artifact-set", out_digest)],
        }
    )
    store.create_event(
        {
            "schema_version": "1.0",
            "event_id": event_ids["triggered"],
            "occurred_at": started_at,
            "relation": "triggered",
            "source": typed_ref(trigger_kind, trigger_id),
            "target": typed_ref("run", run_id),
            "classification": "internal",
            "environment": "development-test",
        }
    )
    store.create_event(
        {
            "schema_version": "1.0",
            "event_id": event_ids["produced"],
            "occurred_at": ended_at,
            "relation": "produced-by",
            "source": typed_ref("artifact-set", out_digest),
            "target": typed_ref("run", run_id),
            "classification": "internal",
            "environment": "development-test",
        }
    )
    store.create_event(
        {
            "schema_version": "1.0",
            "event_id": event_ids["derived"],
            "occurred_at": ended_at,
            "relation": "derived-from",
            "source": typed_ref("artifact-set", out_digest),
            "target": typed_ref("artifact-set", in_digest),
            "run": typed_ref("run", run_id),
            "classification": "internal",
            "environment": "development-test",
        }
    )
    for finding in findings:
        fid = finding.get("finding_id")
        if not isinstance(fid, str) or not UUIDV7_RE.match(fid):
            continue
        store.create_finding(
            {
                "schema_version": "1.0",
                "finding_id": fid,
                "detected_at": ended_at,
                "state": "open",
                "classification": "internal",
                "environment": "development-test",
                "subject": typed_ref("run", run_id),
                "detected_during": typed_ref("run", run_id),
            }
        )
    return {"input_set": stored_in, "output_set": stored_out}


def current_commits(root: str) -> Tuple[str, str, str]:
    """Best-effort HEAD pin; tests inject via BUILD_REPORT_*_COMMIT."""
    env_source = os.environ.get("BUILD_REPORT_SOURCE_COMMIT")
    env_tool = os.environ.get("BUILD_REPORT_TOOL_COMMIT")
    env_config = os.environ.get("BUILD_REPORT_CONFIG_COMMIT")
    if env_source and env_tool and env_config:
        return env_source, env_tool, env_config
    import subprocess

    try:
        head = subprocess.check_output(
            ["git", "-C", root, "rev-parse", "HEAD"], text=True, timeout=30
        ).strip()
    except (OSError, subprocess.SubprocessError):
        head = "0" * 40
    return (
        env_source or head,
        env_tool or head,
        env_config or head,
    )


def trigger_from_env() -> dict:
    kind = os.environ.get("BUILD_REPORT_TRIGGER_KIND", "issue")
    ident = os.environ.get("BUILD_REPORT_TRIGGER_ID", "0037-26.06")
    return {"kind": kind, "id": ident}


def run_id_from_env() -> Optional[str]:
    value = os.environ.get("BUILD_REPORT_RUN_ID") or os.environ.get("RUN_ID")
    if value and UUIDV7_RE.match(value):
        return value
    return None


def members_for_paths(paths: Sequence[str], source_commit: str, media_type: str = "application/octet-stream") -> list:
    members = []
    for raw in paths:
        path = str(raw).replace("\\", "/").lstrip("./")
        if not path or path.startswith("/") or ".." in path.split("/"):
            path = "declared/" + hashlib.sha256(str(raw).encode()).hexdigest()[:16]
        content = str(raw).encode("utf-8")
        if os.path.isfile(raw):
            with open(raw, "rb") as handle:
                content = handle.read()
        members.append(member_digest_for_path(path, content, source_commit, media_type))
    if not members:
        members.append(member_digest_for_path("declared-empty", b"", source_commit, media_type))
    return members


def write_stage_report_file(reports_dir: str, report: Mapping[str, Any]) -> str:
    os.makedirs(reports_dir, exist_ok=True)
    kind = report.get("report_kind") or "stage"
    rid = report.get("run_id") or "unidentified"
    path = os.path.join(reports_dir, f"{kind}-{rid}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1)
    return path


def emit_stage_report(
    *,
    report_kind: str,
    tool: str,
    command: str,
    inputs: Sequence[str],
    started_at: str,
    finished_at: str,
    duration_s: float,
    exit_code: int,
    changed_artifacts: Sequence[str],
    counts: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
    run_archive_ref: Optional[str],
    root: str,
    input_members: Sequence[Mapping[str, Any]],
    output_members: Sequence[Mapping[str, Any]],
    run_id: Optional[str] = None,
) -> dict:
    """Assemble a v2 stage report. Does not invent a run_id when env is empty."""
    rid = run_id or run_id_from_env()
    source_commit, tool_commit, config_commit = current_commits(root)
    archive = run_archive_ref if isinstance(run_archive_ref, str) and run_archive_ref.strip() else os.environ.get("RUN_ARCHIVE_REF")
    report = {
        "schema_version": SCHEMA_VERSION,
        "schema": SCHEMA_NAME,
        "report_kind": report_kind,
        "tool": tool,
        "command": command,
        "inputs": list(inputs),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_s": duration_s,
        "exit_code": exit_code,
        "changed_artifacts": list(changed_artifacts),
        "counts": dict(counts),
        "findings": [dict(item) for item in findings],
        "run_archive_ref": archive,
        "run_id": rid,
        "source_commit": source_commit,
        "tool_commit": tool_commit,
        "config_commit": config_commit,
        "trigger": trigger_from_env(),
        "input_artifact_set": artifact_set_from_members(input_members),
        "output_artifact_set": artifact_set_from_members(output_members),
        "success": exit_code == 0,
    }
    return report


def emit_and_write_stage(
    reports_dir: str,
    root: str,
    *,
    report_kind: str,
    tool: str,
    command: str,
    inputs: Sequence[str],
    started_at: float,
    exit_code: int,
    changed_artifacts: Sequence[str],
    counts: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
) -> dict:
    tools = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    if tools not in sys.path:
        sys.path.insert(0, tools)
    from version_id import uuid7

    finished = time.time()
    started_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_at))
    finished_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(finished))
    source_commit, _tool, _config = current_commits(root)
    stabilized = []
    for item in findings:
        row = dict(item)
        if not row.get("finding_id"):
            row["finding_id"] = uuid7()
        stabilized.append(row)
    report = emit_stage_report(
        report_kind=report_kind,
        tool=tool,
        command=command,
        inputs=list(inputs),
        started_at=started_iso,
        finished_at=finished_iso,
        duration_s=round(finished - started_at, 3),
        exit_code=exit_code,
        changed_artifacts=list(changed_artifacts),
        counts=counts,
        findings=stabilized,
        run_archive_ref=os.environ.get("RUN_ARCHIVE_REF"),
        root=root,
        input_members=members_for_paths(inputs, source_commit),
        output_members=members_for_paths(changed_artifacts or ("declared-empty",), source_commit),
    )
    write_stage_report_file(reports_dir, report)
    return report
