#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_branch_merge_action_fixtures.py -- Task 0038-19 fixture validator.

Validates ``branch-merge-action-fixtures.json`` in two layers:

1. **Structural** -- every fixture's ``request``/``result`` object is
   validated against the frozen ``0037-45`` JSON Schema files under
   ``issues/_schema/`` (``runner-request-v1``/``runner-result-v1``). This is
   the machine check behind the Task 0038-19 acceptance criterion "the
   contract validates against the 0037-45 request/result schema". A small
   hand-rolled validator is used rather than the ``jsonschema`` package,
   mirroring ``_src/tools/review_request_package.py``'s stated convention
   ("Deliberately mirrors ... rather than pulling in an external jsonschema
   dependency, consistent with this repo's existing hand-rolled schema
   validators."). It supports exactly the JSON Schema constructs the three
   ``0037-45`` schema files actually use: type, required, properties,
   additionalProperties, enum, const, pattern, format (date-time), items,
   uniqueItems, minItems, maxItems, minimum, and allOf/if/then.

2. **Business-rule** -- the typed-action contract this document defines on
   top of that closed, additionalProperties:false envelope (action-specific
   parameters carried as documented string conventions inside the existing
   generic fields; authority binding; source-tip/base staleness; claim-record
   auto-union vs. foreign-token conflict). This layer is intentionally *not*
   part of the frozen schema -- see ``docs/pipeline/branch-merge-actions.md``.

Every fixture case must pass layer 1 regardless of whether it is a positive
or a negative example (a well-formed-but-rejected request is still schema
valid). Positive cases must additionally pass layer 2 with no violation;
negative cases must fail layer 2 with exactly their declared ``expected``
rule ID.

Usage::

    python3 docs/pipeline/fixtures/0038-19/validate_branch_merge_action_fixtures.py

Exits 0 and prints one ``PASS`` line on success; exits 1 with the first
failing case and reason otherwise. No repository mutation; read-only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_DIR = REPO_ROOT / "issues" / "_schema"
FIXTURES_PATH = Path(__file__).resolve().with_name("branch-merge-action-fixtures.json")

REQUEST_SCHEMA_FILE = SCHEMA_DIR / "runner-request-v1.schema.json"
RESULT_SCHEMA_FILE = SCHEMA_DIR / "runner-result-v1.schema.json"
CAPABILITY_SCHEMA_FILE = SCHEMA_DIR / "agent-capability-v1.schema.json"

_DATE_TIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)


# ---------------------------------------------------------------------------
# Layer 1: minimal JSON Schema subset engine
# ---------------------------------------------------------------------------


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    raise ValueError(f"unsupported schema type {expected!r}")


def schema_validate(value: Any, schema: dict, path: str = "$") -> list[str]:
    """Return a list of human-readable violations; empty means valid."""
    errors: list[str] = []

    if "const" in schema:
        if value != schema["const"]:
            errors.append(f"{path}: expected const {schema['const']!r}, got {value!r}")
            return errors

    if "enum" in schema:
        if value not in schema["enum"]:
            errors.append(f"{path}: {value!r} not in enum {schema['enum']!r}")
            return errors

    if "type" in schema:
        if not _type_ok(value, schema["type"]):
            errors.append(f"{path}: expected type {schema['type']!r}, got {type(value).__name__}")
            return errors

    if "pattern" in schema and isinstance(value, str):
        if not re.match(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match pattern {schema['pattern']!r}")

    if schema.get("format") == "date-time" and isinstance(value, str):
        if not _DATE_TIME_RE.match(value):
            errors.append(f"{path}: {value!r} is not a valid date-time")

    if "minLength" in schema and isinstance(value, str):
        if len(value) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength {schema['minLength']}")

    if "minimum" in schema and isinstance(value, (int, float)):
        if value < schema["minimum"]:
            errors.append(f"{path}: {value!r} < minimum {schema['minimum']}")

    if isinstance(value, dict) and schema.get("type") == "object":
        properties = schema.get("properties", {})
        for required_key in schema.get("required", []):
            if required_key not in value:
                errors.append(f"{path}: missing required property {required_key!r}")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: additional property {key!r} not allowed")
        for key, subvalue in value.items():
            if key in properties:
                errors.extend(schema_validate(subvalue, properties[key], f"{path}.{key}"))
        if "additionalProperties" in schema and isinstance(schema["additionalProperties"], dict):
            for key, subvalue in value.items():
                if key not in properties:
                    errors.extend(
                        schema_validate(subvalue, schema["additionalProperties"], f"{path}.{key}")
                    )

    if isinstance(value, list) and schema.get("type") == "array":
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: array shorter than minItems {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: array longer than maxItems {schema['maxItems']}")
        if schema.get("uniqueItems"):
            seen = []
            for item in value:
                if item in seen:
                    errors.append(f"{path}: duplicate item {item!r} violates uniqueItems")
                seen.append(item)
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(schema_validate(item, item_schema, f"{path}[{index}]"))

    for clause in schema.get("allOf", []):
        if "if" in clause:
            if_errors = schema_validate(value, clause["if"], path)
            if not if_errors:
                errors.extend(schema_validate(value, clause.get("then", {}), path))
        else:
            errors.extend(schema_validate(value, clause, path))

    return errors


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Layer 2: docs/pipeline/branch-merge-actions.md business-rule checks
# ---------------------------------------------------------------------------


class ContractViolation(Exception):
    def __init__(self, rule: str, detail: str) -> None:
        super().__init__(f"{rule}: {detail}")
        self.rule = rule
        self.detail = detail


def _action_kind_from_idempotence_key(key: str) -> str:
    for kind in ("base-branch", "merge-prereqs", "integrate-checkpoint"):
        if key.startswith(f"{kind}:"):
            return kind
    raise ContractViolation("BMA-UNKNOWN-ACTION-KIND", f"idempotence_key {key!r} has no recognized prefix")


def _find_target_branch(preflight: list[str]) -> str:
    for entry in preflight:
        if entry.startswith("target-branch:refs/heads/"):
            return entry[len("target-branch:refs/heads/") :]
    raise ContractViolation("BMA-MISSING-TARGET-BRANCH", "no target-branch: preflight entry")


_FEATURE_ONLY_RE = re.compile(r"^\d{4}$")


def _is_checkpoint_target(branch: str) -> bool:
    return branch == "main" or bool(_FEATURE_ONLY_RE.match(branch))


def _parse_ref_scope(entry: str) -> tuple[str, str] | None:
    if not entry.startswith("ref:refs/heads/"):
        return None
    rest = entry[len("ref:refs/heads/") :]
    if "@" not in rest:
        return None
    branch, tip = rest.rsplit("@", 1)
    return branch, tip


def check_business_rules(case: dict) -> None:
    request = case["request"]
    context = case["context"]
    action_kind = _action_kind_from_idempotence_key(request["idempotence_key"])
    if action_kind != context["action_kind"]:
        raise ContractViolation(
            "BMA-ACTION-KIND-MISMATCH",
            f"idempotence_key implies {action_kind!r} but context declares {context['action_kind']!r}",
        )

    target_branch = _find_target_branch(request["preflight"])
    capability_class = context["capability_class"]
    actual_tips: dict[str, str] = context["actual_tips"]

    if action_kind == "base-branch":
        if request["action"] != "generation":
            raise ContractViolation("BMA-WRONG-SCHEMA-ACTION", "base-branch must use action=generation")
        parent = None
        for entry in request["read_scopes"]:
            parsed = _parse_ref_scope(entry)
            if parsed:
                parent, tip = parsed
                if actual_tips.get(parent) != tip:
                    raise ContractViolation(
                        "BMA-STALE-BASE",
                        f"declared parent tip {tip} for {parent} does not match observed {actual_tips.get(parent)}",
                    )
        if parent is None:
            raise ContractViolation("BMA-MISSING-PARENT-REF", "no parent ref: entry in read_scopes")
        if request["expected_base"] != actual_tips.get(parent):
            raise ContractViolation("BMA-STALE-BASE", "expected_base does not match observed parent tip")
        return

    if action_kind == "merge-prereqs":
        if request["action"] != "path_limited_commit":
            raise ContractViolation("BMA-WRONG-SCHEMA-ACTION", "merge-prereqs must use action=path_limited_commit")
        if _is_checkpoint_target(target_branch):
            # merge-prereqs must never itself be the checkpoint-crossing merge;
            # that is exactly what integrate-checkpoint is reserved for.
            raise ContractViolation(
                "BMA-AUTHORITY-VIOLATION",
                f"merge-prereqs must not target checkpointed branch {target_branch!r}",
            )
        declared_sources: dict[str, str] = {}
        for entry in request["read_scopes"]:
            parsed = _parse_ref_scope(entry)
            if parsed:
                branch, tip = parsed
                declared_sources[branch] = tip
        for dependency in request["dependencies"]:
            if dependency not in declared_sources:
                raise ContractViolation(
                    "BMA-UNDECLARED-SOURCE",
                    f"dependency {dependency!r} has no matching ref:refs/heads/{dependency}@... entry in read_scopes",
                )
        for branch, declared_tip in declared_sources.items():
            observed = actual_tips.get(branch)
            if observed != declared_tip:
                raise ContractViolation(
                    "BMA-STALE-SOURCE-TIP",
                    f"declared tip {declared_tip} for refs/heads/{branch} does not match observed tip {observed}",
                )
        expected_base = request["expected_base"]
        own_branch = target_branch
        if own_branch in actual_tips and actual_tips[own_branch] != expected_base:
            raise ContractViolation("BMA-STALE-BASE", "expected_base does not match observed own-branch tip")
        for conflict in context.get("claim_conflicts", []):
            if conflict["resolution"] == "foreign-token":
                raise ContractViolation(
                    "BMA-CLAIM-FOREIGN-TOKEN",
                    f"{conflict['path']} carries owner_token {conflict['destination_owner_token']} on the "
                    f"destination side and {conflict['source_owner_token']} on the source side; auto-union is refused",
                )
        return

    if action_kind == "integrate-checkpoint":
        if request["action"] not in ("path_limited_commit", "bookkeeping_commit"):
            raise ContractViolation(
                "BMA-WRONG-SCHEMA-ACTION",
                "integrate-checkpoint must use action=path_limited_commit or bookkeeping_commit",
            )
        if not _is_checkpoint_target(target_branch):
            raise ContractViolation(
                "BMA-NOT-A-CHECKPOINT-TARGET",
                f"integrate-checkpoint target {target_branch!r} is neither a bare Feature ID nor 'main'",
            )
        if capability_class != "privileged":
            raise ContractViolation(
                "BMA-AUTHORITY-VIOLATION",
                f"claim_owner_token {request['claim_owner_token']} resolves to capability class "
                f"{capability_class!r}; integrate-checkpoint targeting refs/heads/{target_branch} requires 'privileged'",
            )
        if target_branch == "main" and "all-checkpoints-passed" not in request["preflight"]:
            raise ContractViolation(
                "BMA-CHECKPOINTS-INCOMPLETE",
                "Feature-to-main integrate-checkpoint requires the all-checkpoints-passed preflight entry",
            )
        return

    raise ContractViolation("BMA-UNKNOWN-ACTION-KIND", action_kind)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    request_schema = load_schema(REQUEST_SCHEMA_FILE)
    result_schema = load_schema(RESULT_SCHEMA_FILE)
    # Loaded for completeness/documentation parity; capability class values
    # referenced by fixtures ("unprivileged") are validated against the
    # frozen enum separately (see docs/pipeline/branch-merge-actions.md, Note
    # on `agent-capability@v1` -- the frozen enum predates the `unprivileged`
    # class and is not itself mutated here).
    load_schema(CAPABILITY_SCHEMA_FILE)

    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    cases = fixtures["cases"]

    positive_count = 0
    negative_count = 0

    for case in cases:
        case_id = case["id"]

        request_errors = schema_validate(case["request"], request_schema)
        if request_errors:
            print(f"FAIL {case_id}: request schema violations: {request_errors}", file=sys.stderr)
            return 1

        if "result" in case:
            result_errors = schema_validate(case["result"], result_schema)
            if result_errors:
                print(f"FAIL {case_id}: result schema violations: {result_errors}", file=sys.stderr)
                return 1

        expected = case["expected"]
        try:
            check_business_rules(case)
            observed_rule: str | None = None
        except ContractViolation as violation:
            observed_rule = violation.rule

        if expected == "valid":
            if observed_rule is not None:
                print(f"FAIL {case_id}: expected valid, business layer raised {observed_rule}", file=sys.stderr)
                return 1
            if case["category"] != "positive":
                print(f"FAIL {case_id}: expected=valid but category={case['category']!r}", file=sys.stderr)
                return 1
            if "result" in case and case["result"]["status"] != "succeeded":
                print(f"FAIL {case_id}: positive case result.status != succeeded", file=sys.stderr)
                return 1
            positive_count += 1
        else:
            if observed_rule != expected:
                print(
                    f"FAIL {case_id}: expected violation {expected!r}, got {observed_rule!r}",
                    file=sys.stderr,
                )
                return 1
            if case["category"] != "negative":
                print(f"FAIL {case_id}: expected={expected!r} but category={case['category']!r}", file=sys.stderr)
                return 1
            if "result" in case and case["result"]["status"] != "rejected":
                print(f"FAIL {case_id}: negative case result.status != rejected", file=sys.stderr)
                return 1
            if "result" in case and not any(expected in finding for finding in case["result"]["findings"]):
                print(f"FAIL {case_id}: result.findings does not cite {expected!r}", file=sys.stderr)
                return 1
            negative_count += 1

    required_negative_rules = {
        "BMA-AUTHORITY-VIOLATION",
        "BMA-UNDECLARED-SOURCE",
        "BMA-STALE-SOURCE-TIP",
        "BMA-CLAIM-FOREIGN-TOKEN",
    }
    seen_negative_rules = {case["expected"] for case in cases if case["category"] == "negative"}
    missing = required_negative_rules - seen_negative_rules
    if missing:
        print(f"FAIL: missing required negative categories: {sorted(missing)}", file=sys.stderr)
        return 1

    print(
        f"PASS: {len(cases)} fixtures ({positive_count} positive, {negative_count} negative); "
        f"all request/result instances validate against runner-request@v1/runner-result@v1; "
        f"all four required negative categories present: {sorted(required_negative_rules)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
