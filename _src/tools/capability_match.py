#!/usr/bin/env python3
"""Deterministic capability matcher (Task 0044-05.02). Evidence only; not assignment."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MATCHER_VERSION = "capability-match@v1"
NON_AUTHORITY_NOTICE = (
    "This result is capability evidence only. It grants no assignment, "
    "ownership, independence, Acceptance, waiver, specialist approval, "
    "release authority, or permission to exceed the Task write scope."
)
PRIVILEGED_RIGHTS = frozenset({
    "acceptance.review", "integration.checkpoint", "feature.close",
})
BUDGET_RANK = {"small": 0, "medium": 1, "large": 2, "very-large": 3}
COGNITIVE_ORDER = ("low", "medium", "high", "critical")
REASON_ORDER = (
    "CAPACITY_UNAVAILABLE",
    "CAPACITY_UNKNOWN",
    "PROCESS_ROLE_MISSING",
    "CAPABILITY_CLASS_INCOMPATIBLE",
    "EXECUTION_ROUTE_MISSING",
    "RIGHT_MISSING",
    "DATA_HANDLE_MISSING",
    "TOOL_MISSING",
    "TOKEN_BUDGET_INSUFFICIENT",
    "CONTEXT_BUDGET_INSUFFICIENT",
    "COGNITIVE_CLASS_UNSERVED",
    "ASSURANCE_MISSING",
    "AUTHORITY_CONSTRAINT_FAILED",
)
KNOWN_ROLES = frozenset({
    "Architect", "Implementer", "Integrator",
    "Requirements Engineer", "QA Manager",
})
PROFILE_KEYS = (
    "schema", "profile_id", "task_id", "process_role", "capability_class",
    "execution_needs", "required_rights", "required_data_handles",
    "required_tools", "token_budget_class", "context_budget_class",
    "cognitive_demand", "required_assurances", "sources", "test_scope",
    "resource_bounds",
)
DESCRIPTOR_KEYS = (
    "schema", "descriptor_id", "agent_id", "process_roles", "capability_class",
    "execution_routes", "rights", "data_handles", "tools", "token_budget_class",
    "context_budget_class", "cognitive_classes_served", "assurances",
    "capacity_status", "snapshot_reference",
)
SOURCE_KEYS = ("kind", "reference", "derivation")
TEST_SCOPE_KEYS = ("kind", "derived_from", "command", "expected_evidence")
RESOURCE_KEYS = ("max_cpu_seconds", "max_wall_seconds", "max_memory_mib", "expected_token_range")


class InputError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code)
        self.code = code
        self.detail = detail


def _sha256_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def _load_strict(path):
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise InputError("INPUT_BOM")
    text = raw.decode("utf-8")
    if text.startswith("\ufeff"):
        raise InputError("INPUT_BOM")

    def pairs(items):
        seen = set()
        out = {}
        for key, val in items:
            if key in seen:
                raise InputError("INPUT_DUPLICATE_KEY", key)
            seen.add(key)
            out[key] = val
        return out

    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(InputError("INPUT_NONFINITE")))
    except InputError:
        raise
    except json.JSONDecodeError as exc:
        raise InputError("INPUT_JSON", str(exc)) from exc
    if not isinstance(value, dict):
        raise InputError("INPUT_ROOT_TYPE")
    return value, raw


def _require_canonical_list(name, value, allowed=None):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise InputError("SCHEMA_TYPE", name)
    if allowed is not None:
        for item in value:
            if item not in allowed:
                raise InputError("SCHEMA_ENUM", name)
    if len(value) != len(set(value)):
        raise InputError("SCHEMA_UNIQUE", name)
    if value != sorted(value):
        raise InputError("INPUT_NONCANONICAL_ORDER", name)
    return value


def _str_field(obj, key):
    val = obj.get(key)
    if not isinstance(val, str) or not val:
        raise InputError("SCHEMA_TYPE", key)
    return val


def _closed(obj, keys, label):
    extra = set(obj) - set(keys)
    if extra:
        raise InputError("SCHEMA_UNKNOWN_FIELD", ",".join(sorted(extra)))
    missing = [key for key in keys if key not in obj]
    if missing:
        raise InputError("SCHEMA_MISSING_FIELD", ",".join(missing))


def validate_profile(obj):
    _closed(obj, PROFILE_KEYS, "profile")
    if obj["schema"] != "task-requirement-profile@v1":
        raise InputError("SCHEMA_VERSION", obj.get("schema"))
    _str_field(obj, "profile_id")
    task_id = _str_field(obj, "task_id")
    if not __import__("re").fullmatch(r"[0-9]{4}-[0-9]{2}(\.[0-9]{2})?", task_id):
        raise InputError("SCHEMA_TASK_ID", task_id)
    role = _str_field(obj, "process_role")
    cap = obj["capability_class"]
    if cap not in {"sandboxed-grunt", "unprivileged", "privileged"}:
        raise InputError("SCHEMA_ENUM", "capability_class")
    needs = obj["execution_needs"]
    if needs not in {"none", "runner", "direct"}:
        raise InputError("SCHEMA_ENUM", "execution_needs")
    if cap == "sandboxed-grunt" and needs == "direct":
        raise InputError("SCHEMA_CROSS_FIELD", "sandboxed-direct")
    if cap in {"unprivileged", "privileged"} and needs == "runner":
        raise InputError("SCHEMA_CROSS_FIELD", "class-runner")
    rights = _require_canonical_list("required_rights", obj["required_rights"])
    if role == "Integrator":
        if cap != "privileged":
            raise InputError("SCHEMA_CROSS_FIELD", "integrator-class")
        if "acceptance.review" not in rights or "integration.checkpoint" not in rights:
            raise InputError("SCHEMA_CROSS_FIELD", "integrator-rights")
    if PRIVILEGED_RIGHTS.intersection(rights) and cap != "privileged":
        raise InputError("SCHEMA_CROSS_FIELD", "privileged-rights")
    _require_canonical_list("required_data_handles", obj["required_data_handles"])
    _require_canonical_list("required_tools", obj["required_tools"])
    if obj["token_budget_class"] not in BUDGET_RANK:
        raise InputError("SCHEMA_ENUM", "token_budget_class")
    if obj["context_budget_class"] not in BUDGET_RANK:
        raise InputError("SCHEMA_ENUM", "context_budget_class")
    if obj["cognitive_demand"] not in COGNITIVE_ORDER:
        raise InputError("SCHEMA_ENUM", "cognitive_demand")
    _require_canonical_list("required_assurances", obj["required_assurances"])
    sources = obj["sources"]
    if not isinstance(sources, list) or not sources:
        raise InputError("SCHEMA_TYPE", "sources")
    for source in sources:
        if not isinstance(source, dict):
            raise InputError("SCHEMA_TYPE", "source")
        _closed(source, SOURCE_KEYS, "source")
        if source["kind"] not in {"requirement", "decision", "architecture", "evidence", "assumption"}:
            raise InputError("SCHEMA_ENUM", "source.kind")
        _str_field(source, "reference")
        _str_field(source, "derivation")
    test_scope = obj["test_scope"]
    if not isinstance(test_scope, dict):
        raise InputError("SCHEMA_TYPE", "test_scope")
    _closed(test_scope, TEST_SCOPE_KEYS, "test_scope")
    _str_field(test_scope, "kind")
    _require_canonical_list("derived_from", test_scope["derived_from"])
    _str_field(test_scope, "command")
    _str_field(test_scope, "expected_evidence")
    bounds = obj["resource_bounds"]
    if not isinstance(bounds, dict):
        raise InputError("SCHEMA_TYPE", "resource_bounds")
    _closed(bounds, RESOURCE_KEYS, "resource_bounds")
    for key in ("max_cpu_seconds", "max_wall_seconds", "max_memory_mib"):
        if not isinstance(bounds[key], int) or isinstance(bounds[key], bool) or bounds[key] < 0:
            raise InputError("SCHEMA_TYPE", key)
    rng = bounds["expected_token_range"]
    if not isinstance(rng, list) or len(rng) != 2 or any(not isinstance(n, int) or isinstance(n, bool) for n in rng):
        raise InputError("SCHEMA_TYPE", "expected_token_range")
    return obj


def validate_descriptor(obj):
    if obj.get("schema") == "agent-capability@v1":
        raise InputError("SCHEMA_UNSUPPORTED_LEGACY")
    _closed(obj, DESCRIPTOR_KEYS, "descriptor")
    if obj["schema"] != "agent-capability-descriptor@v1":
        raise InputError("SCHEMA_VERSION", obj.get("schema"))
    _str_field(obj, "descriptor_id")
    _str_field(obj, "agent_id")
    _require_canonical_list("process_roles", obj["process_roles"])
    cap = obj["capability_class"]
    if cap not in {"sandboxed-grunt", "unprivileged", "privileged"}:
        raise InputError("SCHEMA_ENUM", "capability_class")
    routes = _require_canonical_list(
        "execution_routes", obj["execution_routes"], allowed={"none", "runner", "direct"},
    )
    if cap == "sandboxed-grunt":
        if "direct" in routes or "none" not in routes:
            raise InputError("SCHEMA_CROSS_FIELD", "grunt-routes")
        if set(routes) - {"none", "runner"}:
            raise InputError("SCHEMA_CROSS_FIELD", "grunt-routes")
    else:
        if "runner" in routes or set(routes) != {"direct", "none"}:
            raise InputError("SCHEMA_CROSS_FIELD", "direct-routes")
    _require_canonical_list("rights", obj["rights"])
    _require_canonical_list("data_handles", obj["data_handles"])
    _require_canonical_list("tools", obj["tools"])
    if obj["token_budget_class"] not in BUDGET_RANK:
        raise InputError("SCHEMA_ENUM", "token_budget_class")
    if obj["context_budget_class"] not in BUDGET_RANK:
        raise InputError("SCHEMA_ENUM", "context_budget_class")
    served = obj["cognitive_classes_served"]
    if not isinstance(served, list):
        raise InputError("SCHEMA_TYPE", "cognitive_classes_served")
    if served != list(COGNITIVE_ORDER[:len(served)]) or not served:
        raise InputError("SCHEMA_COGNITIVE_PREFIX")
    _require_canonical_list("assurances", obj["assurances"])
    if obj["capacity_status"] not in {"available", "unavailable", "unknown"}:
        raise InputError("SCHEMA_ENUM", "capacity_status")
    _str_field(obj, "snapshot_reference")
    return obj


def _class_ok(required_class, required_route, actual_class, actual_routes):
    if required_class == "privileged":
        return actual_class == "privileged"
    if required_class == "unprivileged":
        return actual_class in {"unprivileged", "privileged"}
    if required_class == "sandboxed-grunt":
        if required_route == "runner":
            return actual_class == "sandboxed-grunt" and "runner" in actual_routes
        return "none" in actual_routes
    return False


def _authority_failed(profile, descriptor):
    if profile["process_role"] == "Integrator" and descriptor["capability_class"] != "privileged":
        return True
    if PRIVILEGED_RIGHTS.intersection(profile["required_rights"]) and descriptor["capability_class"] != "privileged":
        return True
    return False


def reject_reasons(profile, descriptor):
    reasons = []
    if descriptor["capacity_status"] == "unavailable":
        reasons.append(("CAPACITY_UNAVAILABLE", ""))
    if descriptor["capacity_status"] == "unknown":
        reasons.append(("CAPACITY_UNKNOWN", ""))
    if profile["process_role"] not in descriptor["process_roles"]:
        reasons.append(("PROCESS_ROLE_MISSING", profile["process_role"]))
    if not _class_ok(
        profile["capability_class"], profile["execution_needs"],
        descriptor["capability_class"], descriptor["execution_routes"],
    ):
        reasons.append(("CAPABILITY_CLASS_INCOMPATIBLE", descriptor["capability_class"]))
    if profile["execution_needs"] not in descriptor["execution_routes"]:
        reasons.append(("EXECUTION_ROUTE_MISSING", profile["execution_needs"]))
    for right in profile["required_rights"]:
        if right not in descriptor["rights"]:
            reasons.append(("RIGHT_MISSING", right))
    for handle in profile["required_data_handles"]:
        if handle not in descriptor["data_handles"]:
            reasons.append(("DATA_HANDLE_MISSING", handle))
    for tool in profile["required_tools"]:
        if tool not in descriptor["tools"]:
            reasons.append(("TOOL_MISSING", tool))
    if BUDGET_RANK[descriptor["token_budget_class"]] < BUDGET_RANK[profile["token_budget_class"]]:
        reasons.append(("TOKEN_BUDGET_INSUFFICIENT", descriptor["token_budget_class"]))
    if BUDGET_RANK[descriptor["context_budget_class"]] < BUDGET_RANK[profile["context_budget_class"]]:
        reasons.append(("CONTEXT_BUDGET_INSUFFICIENT", descriptor["context_budget_class"]))
    if profile["cognitive_demand"] not in descriptor["cognitive_classes_served"]:
        reasons.append(("COGNITIVE_CLASS_UNSERVED", profile["cognitive_demand"]))
    for handle in profile["required_assurances"]:
        if handle not in descriptor["assurances"]:
            reasons.append(("ASSURANCE_MISSING", handle))
    if _authority_failed(profile, descriptor):
        reasons.append(("AUTHORITY_CONSTRAINT_FAILED", ""))
    rank = {code: index for index, code in enumerate(REASON_ORDER)}
    reasons.sort(key=lambda item: (rank[item[0]], item[1]))
    return [code if not value else f"{code}:{value}" for code, value in reasons]


def match(profile, descriptors):
    eligible = []
    rejections = []
    for descriptor in descriptors:
        reasons = reject_reasons(profile, descriptor)
        if reasons:
            rejections.append({
                "agent_id": descriptor["agent_id"],
                "descriptor_id": descriptor["descriptor_id"],
                "reasons": reasons,
            })
        else:
            eligible.append(descriptor["agent_id"])
    eligible = sorted(set(eligible))
    rejections.sort(key=lambda item: (item["agent_id"], item["descriptor_id"]))
    if len(eligible) == 0:
        status = "none-eligible"
    elif len(eligible) == 1:
        status = "single-eligible"
    else:
        status = "multiple-eligible"
    return eligible, rejections, status


def build_result(profile, profile_raw, descriptors, descriptor_raws, eligible, rejections, status):
    bindings = []
    for descriptor, raw in zip(descriptors, descriptor_raws):
        bindings.append({
            "agent_id": descriptor["agent_id"],
            "descriptor_id": descriptor["descriptor_id"],
            "sha256": _sha256_bytes(raw),
        })
    bindings.sort(key=lambda item: (item["agent_id"], item["descriptor_id"]))
    return {
        "schema": "capability-match-result@v1",
        "matcher_version": MATCHER_VERSION,
        "profile_id": profile["profile_id"],
        "profile_sha256": _sha256_bytes(profile_raw),
        "descriptor_sha256": bindings,
        "status": status,
        "eligible_agent_ids": eligible,
        "rejections": rejections,
        "non_authority_notice": NON_AUTHORITY_NOTICE,
    }


def run(profile_path, descriptor_paths, agent_id=None):
    profile, profile_raw = _load_strict(profile_path)
    if profile.get("schema") == "agent-capability@v1":
        raise InputError("SCHEMA_UNSUPPORTED_LEGACY")
    profile = validate_profile(profile)
    descriptors = []
    raws = []
    seen_desc = set()
    seen_agent = set()
    for path in descriptor_paths:
        obj, raw = _load_strict(path)
        if obj.get("schema") == "agent-capability@v1":
            raise InputError("SCHEMA_UNSUPPORTED_LEGACY")
        obj = validate_descriptor(obj)
        if obj["descriptor_id"] in seen_desc or obj["agent_id"] in seen_agent:
            raise InputError("INPUT_DUPLICATE_IDENTITY")
        seen_desc.add(obj["descriptor_id"])
        seen_agent.add(obj["agent_id"])
        descriptors.append(obj)
        raws.append(raw)
    eligible, rejections, status = match(profile, descriptors)
    result = build_result(profile, profile_raw, descriptors, raws, eligible, rejections, status)
    encoded = _canonical_json(result)
    if agent_id is not None:
        ids = {item["agent_id"] for item in descriptors}
        if agent_id not in ids:
            raise InputError("INPUT_AGENT_ABSENT", agent_id)
        if agent_id in eligible:
            return encoded, 0, result
        return encoded, 1, result
    if status == "none-eligible":
        return encoded, 1, result
    return encoded, 0, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--descriptor", action="append", required=True)
    parser.add_argument("--agent-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        encoded, exit_code, result = run(args.profile, args.descriptor, args.agent_id)
    except InputError as exc:
        payload = {
            "schema": "capability-match-result@v1",
            "matcher_version": MATCHER_VERSION,
            "profile_id": "",
            "profile_sha256": "sha256:" + ("0" * 64),
            "descriptor_sha256": [],
            "status": "invalid-input",
            "eligible_agent_ids": [],
            "rejections": [],
            "non_authority_notice": NON_AUTHORITY_NOTICE,
            "error": exc.code,
        }
        sys.stdout.write(_canonical_json(payload) if args.json else f"invalid-input {exc.code}\n")
        return 2
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.json:
        sys.stdout.write(encoded)
    else:
        lines = [
            f"status {result['status']}",
            f"eligible {','.join(result['eligible_agent_ids']) or '-'}",
            f"rejections {len(result['rejections'])}",
            "non-authority: result grants no assignment or Acceptance",
        ]
        sys.stdout.write("\n".join(lines[:10]) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
