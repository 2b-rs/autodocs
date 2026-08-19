#!/usr/bin/env python3
"""Read-only structural validator for feature-definition-evidence@v2."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "feature-definition-evidence@v2"
RECONCILIATION_SCHEMA = "feature-definition-study-reconciliation@v1"
STUDY_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RECOMMENDATION_RE = re.compile(r"^REC-\d{2}$")
DISPOSITIONS = {"selected", "rejected", "deferred", "superseded"}
TASK_RE = re.compile(r"^\d{4}-\d{2}(?:\.\d{2})?$")
CRITERION_RE = re.compile(r"^FD-\d{4}-AC-\d{3}$")
EVIDENCE_RE = re.compile(r"^E-\d{3}$")
TYPES = {"producer", "decision", "readiness", "integration", "closure"}


def error(code, detail):
    return {"code": code, "detail": detail}


def duplicates(values):
    return {value for value in values if values.count(value) > 1}


def cycle(edges):
    graph = {}
    for consumer, producer in edges:
        graph.setdefault(consumer, []).append(producer)
    active, done = set(), set()

    def visit(node):
        if node in active:
            return node
        if node in done:
            return None
        active.add(node)
        for next_node in graph.get(node, []):
            found = visit(next_node)
            if found:
                return found
        active.remove(node)
        done.add(node)
        return None

    return next((found for node in graph if (found := visit(node))), None)


def validate(data, root):
    findings = []
    if not isinstance(data, dict) or set(data) != {"schema", "feature", "reconciliation", "criteria", "tasks", "prerequisites", "evidence", "integration_task"}:
        return [error("FDB-001", "manifest has an unexpected top-level shape")]
    if data["schema"] != SCHEMA or not re.fullmatch(r"\d{4}", data["feature"]):
        findings.append(error("FDB-001", "schema or Feature ID is invalid"))
    reconciliation = data.get("reconciliation")
    if not isinstance(reconciliation, dict) or set(reconciliation) != {"path", "study_path", "study_sha256"}:
        return findings + [error("FDB-008", "reconciliation locator is invalid")]
    reconciliation_path = reconciliation.get("path")
    study_path = reconciliation.get("study_path")
    expected_digest = reconciliation.get("study_sha256")
    if (not isinstance(reconciliation_path, str) or not isinstance(study_path, str)
            or Path(reconciliation_path).is_absolute() or Path(study_path).is_absolute()
            or ".." in Path(reconciliation_path).parts or ".." in Path(study_path).parts
            or not isinstance(expected_digest, str) or not STUDY_SHA256_RE.fullmatch(expected_digest)):
        return findings + [error("FDB-008", "reconciliation paths or study digest are invalid")]
    try:
        actual_digest = hashlib.sha256((root / study_path).read_bytes()).hexdigest()
        reconciliation_data = json.loads((root / reconciliation_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return findings + [error("FDB-008", f"cannot read reconciliation: {exc}")]
    if actual_digest != expected_digest:
        findings.append(error("FDB-008", "study digest does not match the reconciled input"))
    expected_study = {"path": study_path, "sha256": expected_digest}
    if (not isinstance(reconciliation_data, dict)
            or set(reconciliation_data) != {"schema", "study", "recommendations"}
            or reconciliation_data.get("schema") != RECONCILIATION_SCHEMA
            or not isinstance(reconciliation_data.get("study"), dict)
            or not expected_study.items() <= reconciliation_data["study"].items()
            or not isinstance(reconciliation_data.get("recommendations"), list)):
        findings.append(error("FDB-008", "reconciliation shape, identity, or study binding is invalid"))
    else:
        recommendation_ids = []
        for item in reconciliation_data["recommendations"]:
            if (not isinstance(item, dict) or not isinstance(item.get("id"), str)
                    or not RECOMMENDATION_RE.fullmatch(item["id"])
                    or not isinstance(item.get("recommendation"), str) or not item["recommendation"].strip()
                    or item.get("disposition") not in DISPOSITIONS
                    or not isinstance(item.get("authority"), str) or not item["authority"].strip()
                    or not isinstance(item.get("post_0037_owner"), str) or not item["post_0037_owner"].strip()
                    or not isinstance(item.get("artifacts"), list) or not item["artifacts"]):
                findings.append(error("FDB-008", "recommendation disposition is incomplete"))
                continue
            recommendation_ids.append(item["id"])
            for artifact in item["artifacts"]:
                artifact_path = artifact.split("#", 1)[0] if isinstance(artifact, str) else ""
                if not artifact_path or not (root / artifact_path).is_file():
                    findings.append(error("FDB-008", f"recommendation {item['id']} has an invalid artifact"))
        if recommendation_ids != [f"REC-{number:02d}" for number in range(1, 21)]:
            findings.append(error("FDB-008", "reconciliation must contain REC-01 through REC-20 in order"))

    collections = ("criteria", "tasks", "prerequisites", "evidence")
    if any(not isinstance(data[name], list) for name in collections):
        return findings + [error("FDB-001", "collections must be arrays")]

    task_ids = [item.get("id") for item in data["tasks"] if isinstance(item, dict)]
    evidence_ids = [item.get("id") for item in data["evidence"] if isinstance(item, dict)]
    criterion_ids = [item.get("id") for item in data["criteria"] if isinstance(item, dict)]
    for label, values, pattern in (("Task", task_ids, TASK_RE), ("criterion", criterion_ids, CRITERION_RE), ("evidence", evidence_ids, EVIDENCE_RE)):
        if len(values) != len(data["tasks"] if label == "Task" else data["criteria"] if label == "criterion" else data["evidence"]) or any(not isinstance(value, str) or not pattern.fullmatch(value) for value in values) or duplicates(values):
            findings.append(error("FDB-001", f"{label} IDs are invalid or non-unique"))

    task_set, evidence_set = set(task_ids), set(evidence_ids)
    for item in data["criteria"]:
        if not isinstance(item, dict) or set(item) != {"id", "implemented_by", "verified_by"} or not item.get("implemented_by") or not item.get("verified_by"):
            findings.append(error("FDB-002", "criterion lacks implementation or verification coverage"))
            continue
        if not set(item["implemented_by"]).issubset(task_set) or not set(item["verified_by"]).issubset(evidence_set):
            findings.append(error("FDB-002", f"criterion {item.get('id')} has unresolved coverage"))
    for item in data["tasks"]:
        if not isinstance(item, dict) or set(item) != {"id", "primary_result", "capability", "evidence"} or not isinstance(item.get("primary_result"), str) or not item["primary_result"].strip() or not isinstance(item.get("capability"), str) or not item["capability"].strip() or not item.get("evidence"):
            findings.append(error("FDB-003", "Task lacks a primary result, capability, or evidence"))
        elif not set(item["evidence"]).issubset(evidence_set):
            findings.append(error("FDB-003", f"Task {item.get('id')} has unresolved evidence"))
    for item in data["evidence"]:
        path = item.get("path") if isinstance(item, dict) else None
        if not isinstance(item, dict) or set(item) != {"id", "path"} or not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts or not (root / path).is_file():
            findings.append(error("FDB-003", f"evidence {item.get('id') if isinstance(item, dict) else '?'} has an invalid path"))

    edges, seen = [], set()
    for edge in data["prerequisites"]:
        if not isinstance(edge, dict) or set(edge) != {"consumer", "producer", "type"}:
            findings.append(error("FDB-004", "prerequisite edge shape is invalid")); continue
        pair = (edge.get("consumer"), edge.get("producer"))
        if not all(isinstance(value, str) and TASK_RE.fullmatch(value) for value in pair) or not set(pair).issubset(task_set) or pair[0] == pair[1] or pair in seen:
            findings.append(error("FDB-004", "prerequisite edge is invalid, unresolved, self-referential, or duplicate"))
        seen.add(pair); edges.append(pair)
        if edge.get("type") not in TYPES:
            findings.append(error("FDB-005", "prerequisite type is invalid"))
    if cycle(edges):
        findings.append(error("FDB-004", "prerequisite graph contains a directed cycle"))
    if data.get("integration_task") not in task_set:
        findings.append(error("FDB-006", "integration Task does not resolve to a Task"))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings = [error("FDB-001", f"cannot read manifest: {exc}")]
    else:
        findings = validate(data, args.root.resolve())
    report = {"schema": "feature-definition-validation@v1", "verdict": "PASS" if not findings else "FAIL", "findings": findings}
    print(json.dumps(report, sort_keys=True) if args.json else report["verdict"])
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
