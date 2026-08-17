#!/usr/bin/env python3
"""Evaluate a versioned Task validation profile against one immutable run report.

This tool is deliberately an evaluator, not a runner: it never executes a stage,
changes files, or interprets a zero process exit as proof that validation ran.
Coverage canaries, freshness identity, declared inputs/outputs, and structured
findings are part of the result contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

PROFILE_SCHEMA = "task-validation-profile@v1"
RUN_SCHEMA = "task-validation-run@v1"
REPORT_SCHEMA = "task-validation-report@v1"
STATUSES = ("PASS", "FAIL", "SKIP", "INCONCLUSIVE")
MAX_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 512
MAX_STRING = 2048


class ContractError(ValueError):
    pass


class DuplicateKeyError(ContractError):
    pass


def _pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _bounded(value: Any, label: str, depth: int = 0) -> None:
    if depth > 12:
        raise ContractError(f"{label}: nesting too deep")
    if isinstance(value, str):
        if len(value) > MAX_STRING:
            raise ContractError(f"{label}: string too long")
    elif isinstance(value, list):
        if len(value) > MAX_ITEMS:
            raise ContractError(f"{label}: too many items")
        for item in value:
            _bounded(item, label, depth + 1)
    elif isinstance(value, dict):
        if len(value) > MAX_ITEMS:
            raise ContractError(f"{label}: too many members")
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractError(f"{label}: non-string key")
            _bounded(item, label, depth + 1)
    elif value is not None and not isinstance(value, (bool, int, float)):
        raise ContractError(f"{label}: unsupported value")


def load_json(path: Path, label: str) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ContractError(f"{label}: inaccessible") from exc
    if len(raw) > MAX_BYTES:
        raise ContractError(f"{label}: input exceeds {MAX_BYTES} bytes")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda value: (_ for _ in ()).throw(ContractError(f"{label}: non-finite {value}")))
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, ContractError) as exc:
        raise ContractError(f"{label}: invalid JSON: {exc}") from exc
    _bounded(value, label)
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{label}: object required")
    return value


def _closed(value: Any, label: str, required: Sequence[str], allowed: Sequence[str]) -> Mapping[str, Any]:
    obj = _object(value, label)
    missing = [key for key in required if key not in obj]
    unknown = sorted(set(obj) - set(allowed))
    if missing:
        raise ContractError(f"{label}: missing {','.join(missing)}")
    if unknown:
        raise ContractError(f"{label}: unknown member {unknown[0]}")
    return obj


def _strings(value: Any, label: str) -> List[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ContractError(f"{label}: non-empty string array required")
    return list(value)


def _validate_profile(profile: Any) -> Mapping[str, Any]:
    obj = _closed(profile, "profile", ("schema", "profile_id", "required_stages", "freshness", "canaries", "limits"),
                  ("schema", "profile_id", "required_stages", "freshness", "canaries", "limits", "baseline_allowed", "allowed_mutations", "expected"))
    if obj["schema"] != PROFILE_SCHEMA or not isinstance(obj["profile_id"], str):
        raise ContractError("profile: unsupported schema or profile_id")
    stages = obj["required_stages"]
    if not isinstance(stages, list) or not stages:
        raise ContractError("profile.required_stages: non-empty array required")
    seen = set()
    for index, stage in enumerate(stages):
        item = _closed(stage, f"profile.required_stages[{index}]", ("id", "inputs", "outputs"),
                       ("id", "inputs", "outputs", "required", "canary_id", "expected_counts", "expected_invariants"))
        if not isinstance(item["id"], str) or item["id"] in seen:
            raise ContractError("profile.required_stages: duplicate or invalid id")
        seen.add(item["id"])
        _strings(item["inputs"], f"profile.required_stages[{index}].inputs")
        _strings(item["outputs"], f"profile.required_stages[{index}].outputs")
    freshness = _closed(obj["freshness"], "profile.freshness", ("fields",), ("fields", "max_age_seconds", "expected"))
    _strings(freshness["fields"], "profile.freshness.fields")
    canaries = obj["canaries"]
    if not isinstance(canaries, list):
        raise ContractError("profile.canaries: array required")
    for index, canary in enumerate(canaries):
        item = _closed(canary, f"profile.canaries[{index}]", ("id", "stage"), ("id", "stage", "expected"))
        if not isinstance(item["id"], str) or not isinstance(item["stage"], str):
            raise ContractError(f"profile.canaries[{index}]: id/stage required")
    _closed(obj["limits"], "profile.limits", ("max_duration_ms",), ("max_duration_ms", "max_memory_mb"))
    if not isinstance(obj["limits"]["max_duration_ms"], int) or obj["limits"]["max_duration_ms"] < 0:
        raise ContractError("profile.limits.max_duration_ms: non-negative integer required")
    return obj


def _validate_run(run: Any) -> Mapping[str, Any]:
    obj = _closed(run, "run", ("schema", "run_id", "freshness", "stages", "baseline_only"),
                  ("schema", "run_id", "freshness", "stages", "baseline_only", "deterministic", "mutations", "metadata", "mixed_inputs", "stale"))
    if obj["schema"] != RUN_SCHEMA or not isinstance(obj["run_id"], str):
        raise ContractError("run: unsupported schema or run_id")
    if not isinstance(obj["freshness"], Mapping):
        raise ContractError("run.freshness: object required")
    if not isinstance(obj["stages"], list):
        raise ContractError("run.stages: array required")
    seen = set()
    for index, stage in enumerate(obj["stages"]):
        item = _closed(stage, f"run.stages[{index}]", ("id", "status", "exit_code", "inputs", "outputs", "findings", "coverage", "duration_ms"),
                       ("id", "status", "exit_code", "inputs", "outputs", "findings", "coverage", "duration_ms", "error"))
        if item["id"] in seen:
            raise ContractError("run.stages: duplicate id")
        seen.add(item["id"])
        if item["status"] not in STATUSES:
            raise ContractError(f"run.stages[{index}].status: invalid")
        if not isinstance(item["exit_code"], int) or not isinstance(item["duration_ms"], int):
            raise ContractError(f"run.stages[{index}]: exit_code/duration_ms must be integers")
        _strings(item["inputs"], f"run.stages[{index}].inputs")
        _strings(item["outputs"], f"run.stages[{index}].outputs")
        if not isinstance(item["findings"], list) or not isinstance(item["coverage"], Mapping):
            raise ContractError(f"run.stages[{index}]: findings/coverage shape invalid")
    if not isinstance(obj["baseline_only"], bool) or not isinstance(obj["mixed_inputs"], bool) or not isinstance(obj["stale"], bool):
        raise ContractError("run.baseline_only/mixed_inputs/stale: booleans required")
    return obj


def _finding(stage: str, code: str, message: str, severity: str = "error") -> Dict[str, str]:
    return {"stage": stage, "code": code, "severity": severity, "message": message[:240]}


def evaluate(profile: Mapping[str, Any], run: Mapping[str, Any]) -> Dict[str, Any]:
    stages = {item["id"]: item for item in run["stages"]}
    findings: List[Dict[str, str]] = []
    stage_reports: List[Dict[str, Any]] = []
    profile_freshness = profile["freshness"]["fields"]
    run_freshness = run["freshness"]
    for field in profile_freshness:
        if field not in run_freshness:
            findings.append(_finding("run", "missing-freshness", f"freshness field missing: {field}"))
        elif not isinstance(run_freshness[field], str) or not run_freshness[field]:
            findings.append(_finding("run", "invalid-freshness", f"freshness field invalid: {field}"))
    if findings:
        overall = "INCONCLUSIVE"
    else:
        overall = "PASS"
    expected_freshness = profile["freshness"].get("expected", {})
    for field, expected in expected_freshness.items():
        if run_freshness.get(field) != expected:
            findings.append(_finding("run", "freshness-mismatch", f"freshness mismatch: {field}"))
    if run.get("mixed_inputs"):
        findings.append(_finding("run", "mixed-run", "run combines inputs from different freshness identities"))
    if run.get("stale"):
        findings.append(_finding("run", "stale-run", "run freshness is outside the profile window"))
    if run.get("baseline_only") and not profile.get("baseline_allowed", False):
        findings.append(_finding("run", "baseline-only", "baseline-only run is not allowed by this profile"))
    if run.get("baseline_only") and profile.get("baseline_allowed", False) and run.get("deterministic") is not True:
        findings.append(_finding("run", "nondeterministic-baseline", "baseline-only run lacks deterministic evidence"))
    declared = {item["id"]: item for item in profile["required_stages"]}
    for stage_id, spec in declared.items():
        stage = stages.get(stage_id)
        if stage is None:
            findings.append(_finding(stage_id, "missing-stage", "required stage is absent"))
            stage_reports.append({"id": stage_id, "status": "INCONCLUSIVE"})
            continue
        status = stage["status"]
        if status != "PASS":
            findings.append(_finding(stage_id, "stage-not-pass", f"required stage status is {status}"))
        if stage["exit_code"] != 0:
            findings.append(_finding(stage_id, "stage-exit", "stage exited nonzero"))
        if not set(spec["inputs"]).issubset(set(stage["inputs"])):
            findings.append(_finding(stage_id, "input-contract", "stage did not report all declared inputs"))
        if not set(spec["outputs"]).issubset(set(stage["outputs"])):
            findings.append(_finding(stage_id, "output-contract", "stage did not report all declared outputs"))
        coverage = stage["coverage"]
        if coverage.get("checks_run", 0) == 0:
            findings.append(_finding(stage_id, "zero-coverage", "stage reported zero detector coverage"))
        if coverage.get("baseline_only") is True:
            findings.append(_finding(stage_id, "baseline-only-stage", "stage coverage is baseline-only"))
        for item in stage["findings"]:
            if isinstance(item, Mapping) and item.get("severity") in {"error", "critical"}:
                findings.append(_finding(stage_id, "stage-finding", str(item.get("message", "structured error finding"))))
        if stage["duration_ms"] > profile["limits"]["max_duration_ms"]:
            findings.append(_finding(stage_id, "duration-limit", "stage exceeded profile duration limit"))
        stage_reports.append({"id": stage_id, "status": status, "checks_run": coverage.get("checks_run", 0), "findings": len(stage["findings"])})
    canary_hits = set()
    for stage_id, stage in stages.items():
        for canary in stage.get("coverage", {}).get("canaries", []):
            if isinstance(canary, str):
                canary_hits.add(canary)
    for canary in profile["canaries"]:
        if canary["id"] not in canary_hits:
            findings.append(_finding(canary["stage"], "missing-canary", f"coverage canary not observed: {canary['id']}"))
    if findings and overall == "PASS":
        overall = "FAIL"
    counts = {status: sum(1 for item in stage_reports if item["status"] == status) for status in STATUSES}
    report: Dict[str, Any] = {"schema": REPORT_SCHEMA, "profile_id": profile["profile_id"], "run_id": run["run_id"], "aggregate": overall,
                              "exit_code": 0 if overall == "PASS" else (1 if overall == "FAIL" else 2), "stages": stage_reports,
                              "findings": findings, "counts": counts, "freshness": dict(run_freshness), "report_digest": ""}
    report["report_digest"] = digest(report)
    return report


def _error_report(message: str) -> Dict[str, Any]:
    report: Dict[str, Any] = {"schema": REPORT_SCHEMA, "profile_id": "unknown", "run_id": "unknown", "aggregate": "INCONCLUSIVE", "exit_code": 2,
                              "stages": [], "findings": [_finding("inputs", "contract", message)], "counts": {status: 0 for status in STATUSES}, "freshness": {}, "report_digest": ""}
    report["report_digest"] = digest(report)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = evaluate(_validate_profile(load_json(args.profile, "profile")), _validate_run(load_json(args.run, "run")))
    except (ContractError, TypeError, ValueError) as exc:
        report = _error_report(str(exc))
    print(canonical_json(report), end="")
    return int(report["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
