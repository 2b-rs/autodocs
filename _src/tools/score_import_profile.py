#!/usr/bin/env python3
"""Validate and evaluate the release-pinned Eclipse S-Core import profile.

This module deliberately produces profile decisions and curation drafts only. It
never reads a moving ref, writes a queue item, creates a record, or promotes a
status. Those operations belong to the later Feature 0019 tasks.
"""
from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

PROFILE_SCHEMA = "score-import-profile@v1"
PROJECT = "ECLIPSE/S-CORE"
SUPPORTED_KINDS = {"module", "component", "design-doc", "process-doc"}
MOVING_REFS = {"main", "master", "head", "latest", "develop", "development"}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NEED_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
EXPECTED_CONDITIONS = {
    "REJECT-UNSUPPORTED-SOURCE-CLASS": "reject",
    "REJECT-MOVING-REF": "reject",
    "REJECT-SOURCE-PIN": "reject",
    "REJECT-INVALID-LOCATOR": "reject",
    "REJECT-SELECTOR-MISS": "reject",
    "QUEUE-MISSING-MANDATORY-FIELD": "queue",
    "REVIEW-MALFORMED-NEED-ID": "review",
    "REVIEW-DUPLICATE-CANONICAL": "review",
    "REVIEW-CONFLICTING-CANONICAL": "review",
    "QUEUE-INITIAL-CURATION": "queue",
}


class ProfileError(ValueError):
    """Raised when an evaluator is asked to use an invalid profile."""


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ProfileError(f"{path} must contain a JSON object")
    return payload


def _finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _source_bindings(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    bindings = profile.get("source_bindings", [])
    if not isinstance(bindings, list):
        return {}
    return {
        str(binding.get("repository")): binding
        for binding in bindings
        if isinstance(binding, dict) and binding.get("repository")
    }


def _artifact_classes(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    classes = profile.get("artifact_classes", [])
    if not isinstance(classes, list):
        return {}
    return {
        str(item.get("source_class")): item
        for item in classes
        if isinstance(item, dict) and item.get("source_class")
    }


def validate_profile(
    profile: dict[str, Any], bom: dict[str, Any] | None = None
) -> list[dict[str, str]]:
    """Return structural and pinning findings without mutating any input."""
    findings: list[dict[str, str]] = []
    for key in ("schema", "profile_id", "profile_version", "project", "release"):
        if not profile.get(key):
            findings.append(_finding("PROFILE-MISSING-KEY", key, "required key is missing"))
    if profile.get("schema") != PROFILE_SCHEMA:
        findings.append(_finding("PROFILE-SCHEMA", "schema", f"must be {PROFILE_SCHEMA}"))
    if profile.get("project") != PROJECT:
        findings.append(_finding("PROFILE-PROJECT", "project", f"must be {PROJECT}"))
    if profile.get("no_moving_ref_fallback") is not True:
        findings.append(_finding("PROFILE-MOVING-REF-POLICY", "no_moving_ref_fallback", "must be true"))
    if str(profile.get("release", "")).lower() in MOVING_REFS:
        findings.append(_finding("PROFILE-MOVING-RELEASE", "release", "must be a release label, not a moving ref"))

    bindings = _source_bindings(profile)
    if set(bindings) != {"score", "process_description"}:
        findings.append(_finding("PROFILE-SOURCES", "source_bindings", "must bind exactly score and process_description"))
    for repository, binding in bindings.items():
        path = f"source_bindings[{repository}]"
        for key in ("repository_url", "release_ref", "ref_kind", "resolved_commit", "content_roots"):
            if not binding.get(key):
                findings.append(_finding("PROFILE-SOURCE-KEY", f"{path}.{key}", "required source binding field is missing"))
        if binding.get("ref_kind") != "tag":
            findings.append(_finding("PROFILE-SOURCE-REF-KIND", f"{path}.ref_kind", "v0.6.0 profile permits tags only"))
        if str(binding.get("release_ref", "")).lower() in MOVING_REFS:
            findings.append(_finding("PROFILE-SOURCE-MOVING-REF", f"{path}.release_ref", "moving refs are forbidden"))
        if not SHA1_RE.fullmatch(str(binding.get("resolved_commit", ""))):
            findings.append(_finding("PROFILE-SOURCE-COMMIT", f"{path}.resolved_commit", "must be a full lowercase SHA-1"))
        roots = binding.get("content_roots")
        if not isinstance(roots, list) or not all(isinstance(root, str) and root and not root.startswith("/") for root in roots):
            findings.append(_finding("PROFILE-SOURCE-ROOTS", f"{path}.content_roots", "must be relative non-empty paths"))

    classes = _artifact_classes(profile)
    if len(classes) != 4:
        findings.append(_finding("PROFILE-CLASS-COUNT", "artifact_classes", "must define four source classes"))
    kinds = {str(item.get("kind")) for item in classes.values()}
    if kinds != SUPPORTED_KINDS:
        findings.append(_finding("PROFILE-KINDS", "artifact_classes", "must map exactly the four supported kinds"))
    for source_class, item in classes.items():
        path = f"artifact_classes[{source_class}]"
        if item.get("repository") not in bindings:
            findings.append(_finding("PROFILE-CLASS-SOURCE", f"{path}.repository", "must name a bound repository"))
        if not isinstance(item.get("mandatory_fields"), list) or not item["mandatory_fields"]:
            findings.append(_finding("PROFILE-CLASS-MANDATORY", f"{path}.mandatory_fields", "must be a non-empty list"))
        if not item.get("id_strategy") or not isinstance(item.get("field_mapping"), dict):
            findings.append(_finding("PROFILE-CLASS-MAPPING", path, "must declare id strategy and field mapping"))
        selector = item.get("selector")
        if not isinstance(selector, dict) or not selector.get("mode"):
            findings.append(_finding("PROFILE-CLASS-SELECTOR", f"{path}.selector", "must declare a selector mode"))

    configured_conditions: dict[str, str] = {}
    conditions = profile.get("conditions")
    if not isinstance(conditions, list):
        findings.append(_finding("PROFILE-CONDITIONS", "conditions", "must be a list"))
    else:
        for condition in conditions:
            if isinstance(condition, dict) and condition.get("id"):
                configured_conditions[str(condition["id"])] = str(condition.get("action"))
        if configured_conditions != EXPECTED_CONDITIONS:
            findings.append(_finding("PROFILE-CONDITIONS", "conditions", "must define the complete stable decision set"))

    defaults = profile.get("defaults")
    if not isinstance(defaults, dict):
        findings.append(_finding("PROFILE-DEFAULTS", "defaults", "must be an object"))
    else:
        status = defaults.get("status")
        if not isinstance(status, dict) or status.get("state") != "invalid/to-be-confirmed":
            findings.append(_finding("PROFILE-STATUS-DEFAULT", "defaults.status", "must default to invalid/to-be-confirmed"))
        traceability = defaults.get("traceability")
        if not isinstance(traceability, dict) or traceability.get("required") is not True:
            findings.append(_finding("PROFILE-TRACEABILITY-DEFAULT", "defaults.traceability", "must require source traceability"))
        draft = defaults.get("curation_draft")
        if not isinstance(draft, dict) or draft.get("schema") != "curation-item@v1" or draft.get("lifecycle_state") != "discovered":
            findings.append(_finding("PROFILE-CURATION-DEFAULT", "defaults.curation_draft", "must create discovered curation drafts"))

    if bom is not None:
        bom_sources = {
            str(source.get("repository")): source
            for source in bom.get("sources", [])
            if isinstance(source, dict) and source.get("repository")
        }
        for repository, binding in bindings.items():
            bom_source = bom_sources.get(repository)
            if bom_source is None:
                findings.append(_finding("PROFILE-BOM-SOURCE", repository, "profile source is absent from BOM"))
                continue
            for profile_key, bom_key in (
                ("repository_url", "repository_url"),
                ("release_ref", "release_ref"),
                ("ref_kind", "ref_kind"),
                ("resolved_commit", "resolved_commit"),
                ("content_roots", "source_paths"),
            ):
                if binding.get(profile_key) != bom_source.get(bom_key):
                    findings.append(_finding("PROFILE-BOM-MISMATCH", f"{repository}.{profile_key}", "must match the release-pinned BOM"))
        if set(bom_sources) != set(bindings):
            findings.append(_finding("PROFILE-BOM-COVERAGE", "source_bindings", "profile and BOM source sets differ"))
    return findings


def _valid_locator(locator: Any) -> bool:
    if not isinstance(locator, dict):
        return False
    path = locator.get("path")
    if not isinstance(path, str) or not path or path.startswith("/"):
        return False
    parts = PurePosixPath(path).parts
    if ".." in parts or path.endswith("/"):
        return False
    if not isinstance(locator.get("line_start"), int) or locator["line_start"] < 1:
        return False
    if not isinstance(locator.get("line_end"), int) or locator["line_end"] < locator["line_start"]:
        return False
    return isinstance(locator.get("anchor"), str) and bool(locator["anchor"])


def _selector_matches(selector: dict[str, Any], path: str) -> bool:
    mode = selector.get("mode")
    if mode == "exact-path":
        return path in selector.get("paths", [])
    if mode == "bazel-package":
        if path in selector.get("exclude_paths", []):
            return False
        return any(fnmatch.fnmatchcase(path, pattern) for pattern in selector.get("paths", []))
    if mode == "sphinx-need-document":
        root = str(selector.get("root", ""))
        extensions = selector.get("extensions", [])
        return path.startswith(f"{root}/") and any(path.endswith(extension) for extension in extensions)
    return False


def _canonical_id(profile: dict[str, Any], artifact_class: dict[str, Any], fields: dict[str, Any]) -> str:
    strategy = artifact_class["id_strategy"]
    if strategy == "module_name":
        raw_id = str(fields["module_name"])
    elif strategy == "module_name.package_path_dots":
        package_path = str(fields["package_path"]).strip("/").replace("/", ".")
        raw_id = f"{fields['module_name']}.{package_path}"
    elif strategy == "need_id":
        raw_id = str(fields["need_id"])
    else:
        raise ProfileError(f"unsupported id strategy {strategy!r}")
    return f"{profile['project']}/{artifact_class['kind']}/{raw_id}"


def _work_item(
    profile: dict[str, Any],
    candidate: dict[str, Any],
    condition_id: str,
    decision: str,
    message: str,
    canonical_id: str | None,
    item_kind: str,
) -> dict[str, Any]:
    return {
        "schema": profile["defaults"]["curation_draft"]["schema"],
        "lifecycle_state": profile["defaults"]["curation_draft"]["lifecycle_state"],
        "physical_queue_writer": profile["defaults"]["curation_draft"]["physical_queue_writer"],
        "item_kind": item_kind,
        "project": profile["project"],
        "canonical_id": canonical_id,
        "release": profile["release"],
        "origin": profile["defaults"]["curation_draft"]["origin"],
        "condition_id": condition_id,
        "decision": decision,
        "subject": message,
        "source_locator": candidate.get("locator"),
        "source_content_sha256": candidate.get("source_content_sha256"),
    }


def _decision(
    profile: dict[str, Any],
    candidate: dict[str, Any],
    decision: str,
    condition_id: str,
    message: str,
    canonical_id: str | None = None,
    item_kind: str = "scrape-observation",
    record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "decision": decision,
        "condition_id": condition_id,
        "message": message,
        "record": record,
    }
    if decision in {"queue", "review"}:
        result["work_item"] = _work_item(profile, candidate, condition_id, decision, message, canonical_id, item_kind)
    return result


def evaluate_candidate(profile: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Classify one already-read source artifact without reading or writing files."""
    findings = validate_profile(profile)
    if findings:
        raise ProfileError(f"profile is invalid: {findings}")

    source_class = str(candidate.get("source_class", ""))
    classes = _artifact_classes(profile)
    artifact_class = classes.get(source_class)
    if artifact_class is None:
        return _decision(profile, candidate, "reject", "REJECT-UNSUPPORTED-SOURCE-CLASS", "source class is not supported")

    if str(candidate.get("release_ref", "")).lower() in MOVING_REFS or candidate.get("ref_kind") != "tag":
        return _decision(profile, candidate, "reject", "REJECT-MOVING-REF", "moving or non-tag source reference is forbidden")

    binding = _source_bindings(profile)[artifact_class["repository"]]
    pin_fields = ("repository", "repository_url", "release_ref", "ref_kind", "resolved_commit")
    if any(candidate.get(key) != binding.get(key) for key in pin_fields):
        return _decision(profile, candidate, "reject", "REJECT-SOURCE-PIN", "candidate does not match the pinned source binding")

    locator = candidate.get("locator")
    if not _valid_locator(locator):
        return _decision(profile, candidate, "reject", "REJECT-INVALID-LOCATOR", "candidate source locator is not bounded and safe")
    assert isinstance(locator, dict)
    path = str(locator["path"])
    if not _selector_matches(artifact_class["selector"], path):
        return _decision(profile, candidate, "reject", "REJECT-SELECTOR-MISS", "locator does not match the declared source selector")

    fields = candidate.get("fields")
    required = ["source_content_sha256", *artifact_class["mandatory_fields"]]
    if not isinstance(fields, dict) or any(not candidate.get(field) if field == "source_content_sha256" else not fields.get(field) for field in required):
        return _decision(profile, candidate, "queue", "QUEUE-MISSING-MANDATORY-FIELD", "selected artifact needs curation because required source-backed data is absent")
    if not SHA256_RE.fullmatch(str(candidate["source_content_sha256"])):
        return _decision(profile, candidate, "queue", "QUEUE-MISSING-MANDATORY-FIELD", "selected artifact needs a valid source content digest")

    if artifact_class["id_strategy"] == "need_id":
        need_id = str(fields["need_id"])
        if not NEED_ID_RE.fullmatch(need_id) or locator["anchor"] != need_id:
            return _decision(profile, candidate, "review", "REVIEW-MALFORMED-NEED-ID", "documentation item requires a valid explicit need ID matching its locator anchor")

    canonical_id = _canonical_id(profile, artifact_class, fields)
    if canonical_id in candidate.get("conflicting_canonical_ids", []):
        return _decision(profile, candidate, "review", "REVIEW-CONFLICTING-CANONICAL", "canonical identity has contradictory source content or provenance", canonical_id)
    if canonical_id in candidate.get("existing_canonical_ids", []):
        return _decision(profile, candidate, "review", "REVIEW-DUPLICATE-CANONICAL", "canonical identity was already observed in this import batch", canonical_id)

    record = {
        "project": profile["project"],
        "kind": artifact_class["kind"],
        "id": canonical_id.rsplit("/", 1)[1],
        "canonical_id": canonical_id,
        "version_id": "deferred to Task 0019-05 after normalized content hashing",
        "title": fields["title"],
        "description": fields.get("description", ""),
        "provenance": {
            "source_repo_origin": candidate["repository"],
            "source_repo_url": candidate["repository_url"],
            "source_ref_kind": candidate["ref_kind"],
            "source_ref": candidate["release_ref"],
            "source_commit": candidate["resolved_commit"],
            "source_path": locator["path"],
            "source_locator": copy.deepcopy(locator),
            "source_content_sha256": candidate["source_content_sha256"],
        },
        "status": copy.deepcopy(profile["defaults"]["status"]),
        "traceability": {
            "mode": profile["defaults"]["traceability"]["mode"],
            "required": True,
            "sources": [{
                "repository": candidate["repository"],
                "release_ref": candidate["release_ref"],
                "resolved_commit": candidate["resolved_commit"],
                "locator": copy.deepcopy(locator),
                "source_content_sha256": candidate["source_content_sha256"],
            }],
        },
        "history_template": copy.deepcopy(profile["defaults"]["history_template"]),
    }
    if artifact_class["id_strategy"] == "need_id":
        record["sphinx_need_type"] = fields["need_type"]
    return _decision(
        profile,
        candidate,
        "queue",
        "QUEUE-INITIAL-CURATION",
        "release-pinned candidate requires curation before a valid status or publication",
        canonical_id,
        artifact_class["kind"],
        record,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate or evaluate the S-Core import profile.")
    parser.add_argument("profile", type=Path, help="Path to score-import-profile@v1 JSON")
    parser.add_argument("--bom", type=Path, help="Optional pinned score-source-bom@v1 JSON to compare")
    parser.add_argument("--candidate", type=Path, help="Optional candidate JSON to evaluate")
    args = parser.parse_args()

    profile = load_json(args.profile)
    bom = load_json(args.bom) if args.bom else None
    findings = validate_profile(profile, bom)
    if findings:
        print(json.dumps({"ok": False, "findings": findings}, indent=2, sort_keys=True))
        return 1
    if args.candidate:
        print(json.dumps(evaluate_candidate(profile, load_json(args.candidate)), indent=2, sort_keys=True))
    else:
        print(json.dumps({"ok": True, "profile_id": profile["profile_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
