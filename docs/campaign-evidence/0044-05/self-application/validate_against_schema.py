#!/usr/bin/env python3
"""Minimal stdlib-only structural JSON Schema (2020-12 subset) validator.

Written for this evidence directory because the environment has no
third-party ``jsonschema`` module (confirmed absent, see
``checkpoint-review-geordi-20260825.md``) and the matcher itself is required
to stay stdlib-only. Implements exactly the keywords the three `0044-05`
schemas use: ``type``, ``enum``, ``const``, ``pattern``, ``minLength``,
``properties``, ``additionalProperties``, ``required``, ``items``,
``minItems``, ``maxItems``, ``uniqueItems``, ``minimum``, and top-level
``allOf``/``if``/``then``. Not a general-purpose validator; sufficient to
independently re-check the exact committed instances below against the exact
committed schemas, which is the gap the rejected checkpoint review found.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    raise ValueError(f"unsupported type keyword: {expected}")


def validate(instance: Any, schema: dict, path: str = "$") -> list[str]:
    errors: list[str] = []

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")
        return errors
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']!r}")
        return errors
    if "type" in schema and not _type_ok(instance, schema["type"]):
        errors.append(f"{path}: expected type {schema['type']}, got {type(instance).__name__}")
        return errors

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: length {len(instance)} < minLength {schema['minLength']}")
        if "pattern" in schema and not re.match(schema["pattern"], instance):
            errors.append(f"{path}: {instance!r} does not match pattern {schema['pattern']!r}")

    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < minimum {schema['minimum']}")

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")
        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            extra = set(instance) - allowed
            if extra:
                errors.append(f"{path}: additionalProperties=False, forbidden keys {sorted(extra)}")
        for key, subschema in properties.items():
            if key in instance:
                errors.extend(validate(instance[key], subschema, f"{path}.{key}"))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: {len(instance)} items < minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: {len(instance)} items > maxItems {schema['maxItems']}")
        if schema.get("uniqueItems") and len(instance) != len(set(map(json.dumps, instance)) if instance and isinstance(instance[0], (dict, list)) else set(instance)):
            errors.append(f"{path}: items not unique")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors.extend(validate(item, schema["items"], f"{path}[{i}]"))

    for sub in schema.get("allOf", []):
        if "if" in sub:
            cond = sub["if"]
            matches = True
            for key, cond_schema in cond.get("properties", {}).items():
                if key not in instance or validate(instance[key], cond_schema, f"{path}.{key}"):
                    matches = False
                    break
            for key in cond.get("required", []):
                if key not in instance:
                    matches = False
                    break
            if matches:
                then = sub.get("then", {})
                for key in then.get("required", []):
                    if key not in instance:
                        errors.append(f"{path}: if-matched but missing required {key!r} (allOf/then)")
                for key, then_schema in then.get("properties", {}).items():
                    if key in instance:
                        errors.extend(validate(instance[key], then_schema, f"{path}.{key} (allOf/then)"))
                if "not" in then:
                    not_schema = then["not"]
                    if "required" in not_schema:
                        forbidden_present = [k for k in not_schema["required"] if k in instance]
                        if forbidden_present:
                            errors.append(f"{path}: forbidden by allOf/then/not: {forbidden_present}")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: validate_against_schema.py <schema.json> <instance.json> <label>", file=sys.stderr)
        return 2
    schema = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    instance = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    label = argv[2]
    errors = validate(instance, schema)
    if errors:
        print(f"{label}: INVALID ({len(errors)} error(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"{label}: VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
