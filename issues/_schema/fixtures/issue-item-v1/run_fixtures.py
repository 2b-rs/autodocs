#!/usr/bin/env python3
"""Executable evidence for issues/_schema/issue-item-v1.schema.json (Task 0037-02.03).

Loads the schema and every fixture declared in manifest.json, asserts every 'valid'
fixture validates cleanly and every 'invalid' fixture fails validation. This is a
self-contained probe harness, NOT the production frontmatter parser (that is Campaign B
scope) -- it depends only on the schema file and stdlib json, plus the optional
'jsonschema' package if installed (falling back to a minimal structural checker
otherwise so this script has zero hard third-party dependency).

Exit code 0 = all assertions passed. Non-zero = at least one fixture behaved
unexpectedly (printed to stderr with the fixture name and reason).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "..", "..", "issue-item-v1.schema.json")
MANIFEST_PATH = os.path.join(HERE, "manifest.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_with_jsonschema(instance, schema):
    import jsonschema
    jsonschema.validate(instance=instance, schema=schema)


def validate_minimal(instance, schema):
    """Minimal structural fallback covering this schema's actual constructs, used only
    if the 'jsonschema' package is not installed in this environment. Not a general
    JSON Schema implementation."""
    import re

    def check_obj(inst, sch, path):
        if sch.get("type") == "object":
            if not isinstance(inst, dict):
                raise ValueError(f"{path}: expected object")
            props = sch.get("properties", {})
            for req in sch.get("required", []):
                if req not in inst:
                    raise ValueError(f"{path}: missing required field '{req}'")
            if sch.get("additionalProperties") is False:
                for k in inst:
                    if k not in props:
                        raise ValueError(f"{path}: unknown field '{k}'")
            for k, v in inst.items():
                if k in props:
                    check_value(v, props[k], f"{path}.{k}")
            for rule in sch.get("allOf", []):
                cond = rule.get("if", {})
                cond_props = cond.get("properties", {})
                matches = True
                for ck, cv in cond_props.items():
                    if "const" in cv:
                        matches = matches and inst.get(ck) == cv["const"]
                    elif "enum" in cv:
                        matches = matches and inst.get(ck) in cv["enum"]
                if matches:
                    then = rule.get("then", {})
                    if "not" in then and "required" in then["not"]:
                        for f in then["not"]["required"]:
                            if f in inst:
                                raise ValueError(f"{path}: forbidden field '{f}' present")
                    if "required" in then:
                        for f in then["required"]:
                            if f not in inst:
                                raise ValueError(f"{path}: conditionally required field '{f}' missing")

    def check_value(val, sch, path):
        t = sch.get("type")
        if t == "string":
            if not isinstance(val, str):
                raise ValueError(f"{path}: expected string, got {type(val).__name__}")
            if "enum" in sch and val not in sch["enum"]:
                raise ValueError(f"{path}: '{val}' not in enum {sch['enum']}")
            if "pattern" in sch and not re.match(sch["pattern"], val):
                raise ValueError(f"{path}: '{val}' does not match pattern {sch['pattern']}")
        elif t == "integer":
            if not isinstance(val, int) or isinstance(val, bool):
                raise ValueError(f"{path}: expected integer")
            if "minimum" in sch and val < sch["minimum"]:
                raise ValueError(f"{path}: {val} below minimum {sch['minimum']}")
            if "maximum" in sch and val > sch["maximum"]:
                raise ValueError(f"{path}: {val} above maximum {sch['maximum']}")
        elif t == "array":
            if not isinstance(val, list):
                raise ValueError(f"{path}: expected array")
            if sch.get("uniqueItems") and len(val) != len(set(json.dumps(x, sort_keys=True) for x in val)):
                raise ValueError(f"{path}: duplicate items not allowed")
            items_sch = sch.get("items", {})
            for i, item in enumerate(val):
                if items_sch.get("type") == "object":
                    check_obj(item, items_sch, f"{path}[{i}]")
                else:
                    check_value(item, items_sch, f"{path}[{i}]")
        elif t == "object":
            check_obj(val, sch, path)

    check_obj(instance, schema, "$")


def validate(instance, schema):
    try:
        import jsonschema  # noqa: F401
        validate_with_jsonschema(instance, schema)
    except ImportError:
        validate_minimal(instance, schema)


def main():
    schema = load_json(SCHEMA_PATH)
    manifest = load_json(MANIFEST_PATH)
    failures = []

    for name in manifest["valid"]:
        instance = load_json(os.path.join(HERE, name))
        try:
            validate(instance, schema)
        except Exception as e:
            failures.append(f"VALID fixture '{name}' unexpectedly failed: {e}")

    for entry in manifest["invalid"]:
        name = entry["file"]
        instance = load_json(os.path.join(HERE, name))
        try:
            validate(instance, schema)
            failures.append(f"INVALID fixture '{name}' (rule: {entry['rule']}) unexpectedly PASSED")
        except Exception:
            pass  # expected to fail

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {len(manifest['valid'])} valid + {len(manifest['invalid'])} invalid fixtures behaved as expected")
    sys.exit(0)


if __name__ == "__main__":
    main()
