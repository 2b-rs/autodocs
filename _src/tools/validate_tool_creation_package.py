#!/usr/bin/env python3
"""Read-only structural validator for tool-creation-evidence@v1."""
import argparse
import hashlib
import json
import re
from pathlib import Path

SCHEMA = "tool-creation-evidence@v1"
RECONCILIATION_SCHEMA = "tool-creation-study-reconciliation@v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^(?:TCP|E|P)-\d{3}$")
DISPOSITIONS = {"selected", "rejected", "deferred", "superseded"}
PILOT_DECISIONS = {"candidate-only", "rejected-pending-independent-review", "revise", "suspend", "retire"}
REQUIRED_CONTROLS = {f"TCP-{number:03d}" for number in range(1, 8)}


def finding(code, detail):
    return {"code": code, "detail": detail}


def safe_path(root, value):
    return isinstance(value, str) and not Path(value).is_absolute() and ".." not in Path(value).parts and (root / value).is_file()


def validate(data, root):
    findings = []
    if not isinstance(data, dict) or set(data) != {"schema", "feature", "reconciliation", "controls", "pilots", "evidence"}:
        return [finding("TCP-001", "manifest has an unexpected top-level shape")]
    if data["schema"] != SCHEMA or data["feature"] != "0039":
        findings.append(finding("TCP-001", "schema or Feature ID is invalid"))
    for collection in ("controls", "pilots", "evidence"):
        if not isinstance(data[collection], list):
            return findings + [finding("TCP-001", f"{collection} must be an array")]
    controls = data["controls"]
    control_ids = [item.get("id") for item in controls if isinstance(item, dict)]
    if (len(control_ids) != len(controls) or set(control_ids) != REQUIRED_CONTROLS
            or any(set(item) != {"id", "artifact"} or not safe_path(root, item.get("artifact")) for item in controls if isinstance(item, dict))):
        findings.append(finding("TCP-003", "mandatory controls or control artifacts are incomplete"))
    evidence_ids = [item.get("id") for item in data["evidence"] if isinstance(item, dict)]
    if (len(evidence_ids) != len(data["evidence"]) or len(set(evidence_ids)) != len(evidence_ids)
            or any(not isinstance(item, dict) or set(item) != {"id", "path"} or not isinstance(item.get("id"), str) or not ID.fullmatch(item["id"]) or not safe_path(root, item.get("path")) for item in data["evidence"])):
        findings.append(finding("TCP-001", "evidence IDs or paths are invalid"))
    reconciliation = data.get("reconciliation")
    if not isinstance(reconciliation, dict) or set(reconciliation) != {"path", "study_path", "study_sha256"}:
        return findings + [finding("TCP-002", "reconciliation locator is invalid")]
    if (not safe_path(root, reconciliation.get("path")) or not safe_path(root, reconciliation.get("study_path"))
            or not isinstance(reconciliation.get("study_sha256"), str) or not SHA256.fullmatch(reconciliation["study_sha256"])):
        return findings + [finding("TCP-002", "study binding is invalid")]
    if hashlib.sha256((root / reconciliation["study_path"]).read_bytes()).hexdigest() != reconciliation["study_sha256"]:
        findings.append(finding("TCP-002", "study digest does not match the reconciled input"))
    try:
        reconciled = json.loads((root / reconciliation["path"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return findings + [finding("TCP-002", f"cannot read reconciliation: {exc}")]
    expected_study = {"path": reconciliation["study_path"], "sha256": reconciliation["study_sha256"]}
    recommendations = reconciled.get("recommendations") if isinstance(reconciled, dict) else None
    if (not isinstance(reconciled, dict) or reconciled.get("schema") != RECONCILIATION_SCHEMA
            or not isinstance(reconciled.get("study"), dict) or not expected_study.items() <= reconciled["study"].items()
            or not isinstance(recommendations, list)):
        findings.append(finding("TCP-002", "reconciliation shape or study binding is invalid"))
    else:
        expected_ids = [f"REC-{number:02d}" for number in range(1, 21)]
        valid = []
        for item in recommendations:
            valid.append(isinstance(item, dict) and isinstance(item.get("id"), str) and isinstance(item.get("recommendation"), str) and item["recommendation"].strip() and item.get("disposition") in DISPOSITIONS and isinstance(item.get("authority"), str) and item["authority"].strip() and isinstance(item.get("post_0037_owner"), str) and item["post_0037_owner"].strip() and isinstance(item.get("artifacts"), list) and item["artifacts"])
        if [item.get("id") if isinstance(item, dict) else None for item in recommendations] != expected_ids or not all(valid):
            findings.append(finding("TCP-002", "reconciliation must contain complete REC-01 through REC-20 in order"))
    pilots = data["pilots"]
    shapes = [item.get("shape") for item in pilots if isinstance(item, dict)]
    if len(pilots) != 2 or set(shapes) != {"new-capability", "extension-or-consolidation"}:
        findings.append(finding("TCP-004", "exactly one pilot of each required shape is required"))
    for item in pilots:
        if (not isinstance(item, dict) or set(item) != {"id", "shape", "evidence", "decision"}
                or not isinstance(item.get("id"), str) or not ID.fullmatch(item["id"])
                or not safe_path(root, item.get("evidence"))):
            findings.append(finding("TCP-004", "pilot identity or evidence is invalid"))
        elif item.get("decision") not in PILOT_DECISIONS:
            findings.append(finding("TCP-005", "pilot decision implies registration or deployment"))
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
        findings = [finding("TCP-001", f"cannot read manifest: {exc}")]
    else:
        findings = validate(data, args.root.resolve())
    report = {"schema": "tool-creation-validation@v1", "verdict": "PASS" if not findings else "FAIL", "findings": findings}
    print(json.dumps(report, sort_keys=True) if args.json else report["verdict"])
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
