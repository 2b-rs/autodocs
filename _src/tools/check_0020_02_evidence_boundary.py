#!/usr/bin/env python3
"""Optional CON-01 helper for Task 0020-02 evidence-boundary fixtures.

This is not a shared validation gate. Do not register it in ``_src/validate.py``
or any default suite other Tasks must pass (DEC-0020-002 A-01 / CON-01).

It classifies JSON fixtures against REQ-0020-01..08 as ``usable`` or
``refused`` for a named *use*. Invoke explicitly:

    python3 _src/tools/check_0020_02_evidence_boundary.py \\
        --fixtures docs/dossiers/0020-02-evidence-boundary-fixtures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ORIGINS = (
    "process-definition",
    "implemented-mechanism",
    "documentation-execution",
    "ecu-execution",
    "controlled-scenario",
)
REQUIRED = (
    "product_id",
    "project_id",
    "process_id",
    "process_instance_id",
    "baseline_id",
    "revision",
    "owner",
    "origin",
    "validity",
    "retention",
    "confidentiality",
)
IDENTITY = (
    "product_id",
    "project_id",
    "process_id",
    "process_instance_id",
    "baseline_id",
)
ECU_USES = frozenset(
    {
        "ecu-execution",
        "assessment-input",
        "catalogue",
        "selected-profile-register",
        "freeze",
    }
)
ASSESSED_PRODUCT = "virtualized-automotive-ecu"
ASSESSED_PROJECT = "autodocs-ecu-software"


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def classify_items(use: str, items: list[dict]) -> tuple[str, str]:
    """Return (usable|refused, reason)."""
    if not items:
        return "refused", "empty-set"
    for item in items:
        origin = item.get("origin")
        if origin not in ORIGINS:
            return "refused", "origin-not-canonical"
        for field in REQUIRED:
            if not _nonempty(item.get(field)):
                return "refused", f"missing:{field}"
        if use in ECU_USES:
            if origin != "ecu-execution":
                return "refused", "non-ecu-origin-for-ecu-use"
            if item.get("product_id") != ASSESSED_PRODUCT:
                return "refused", "cross-product"
            if item.get("project_id") != ASSESSED_PROJECT:
                return "refused", "cross-project"
    if len(items) > 1:
        first = items[0]
        for other in items[1:]:
            for field in IDENTITY:
                if other.get(field) != first.get(field):
                    return "refused", f"opportunistic-aggregation:{field}"
    return "usable", "ok"


def load_fixtures(directory: Path) -> list[dict]:
    fixtures = []
    for path in sorted(directory.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        payload["_path"] = str(path)
        fixtures.append(payload)
    return fixtures


def check_fixtures(fixtures: list[dict]) -> list[dict]:
    results = []
    for fixture in fixtures:
        expect = fixture["expect"]
        got, reason = classify_items(fixture["use"], fixture["items"])
        results.append(
            {
                "id": fixture["id"],
                "path": fixture.get("_path", ""),
                "expect": expect,
                "got": got,
                "reason": reason,
                "ok": got == expect,
            }
        )
    return results


def aggregation_property() -> list[dict]:
    """Finite enumeration of REQ-0020-05: two valid ECU items, one identity field differs."""
    base = {
        "product_id": ASSESSED_PRODUCT,
        "project_id": ASSESSED_PROJECT,
        "process_id": "SWE.1",
        "process_instance_id": "pi-1",
        "baseline_id": "bl-1",
        "revision": "1",
        "owner": "owner-a",
        "origin": "ecu-execution",
        "validity": "this-increment",
        "retention": "assessment-cycle",
        "confidentiality": "internal",
    }
    cases = []
    same = classify_items("freeze", [dict(base), dict(base)])
    cases.append(
        {
            "id": "P-agg-same",
            "expect": "usable",
            "got": same[0],
            "reason": same[1],
            "ok": same[0] == "usable",
        }
    )
    for field in IDENTITY:
        other = dict(base)
        other[field] = str(base[field]) + "-other"
        got, reason = classify_items("freeze", [dict(base), other])
        cases.append(
            {
                "id": f"P-agg-diff-{field}",
                "expect": "refused",
                "got": got,
                "reason": reason,
                "ok": got == "refused",
            }
        )
    return cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=Path("docs/dossiers/0020-02-evidence-boundary-fixtures"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.fixtures.is_dir():
        print(f"fixtures directory missing: {args.fixtures}", file=sys.stderr)
        return 2
    fixture_results = check_fixtures(load_fixtures(args.fixtures))
    property_results = aggregation_property()
    all_results = fixture_results + property_results
    failed = [row for row in all_results if not row["ok"]]
    payload = {
        "helper": "check_0020_02_evidence_boundary.py",
        "shared_gate": False,
        "fixture_count": len(fixture_results),
        "property_count": len(property_results),
        "failed": len(failed),
        "results": all_results,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for row in all_results:
            mark = "OK" if row["ok"] else "FAIL"
            print(f"{mark} {row['id']} expect={row['expect']} got={row['got']} ({row['reason']})")
        print(
            f"summary fixtures={len(fixture_results)} "
            f"property={len(property_results)} failed={len(failed)}"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
