#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chore_tool_inventory.py -- lifecycle-contract classification of tracked
mutating chore tools (Task 0038-14).

Reuses automation_safety.tracked_automation_paths() (0038-03) as the live
enumeration of tracked .py/.sh/.bash/.zsh scripts instead of re-scanning the
Git index independently, so this tool's notion of "every tracked chore tool"
never drifts from the automation-safety gate's.

Every tracked script ends up in exactly one of two buckets, read from the
companion data file (default: chore_tool_inventory_data.json next to this
module):

  classified  -- has a declared category, write set, commit points, an
                 idempotency key/journal/cleanup/failure-aggregation story,
                 ownership, retention, and a test reference. This is the
                 "full lifecycle contract" the Task's acceptance criteria
                 asks for.
  enumerated  -- known to exist and tracked, but only a heuristic category
                 guess is recorded; NOT a classification. This is the
                 explicit "classified vs. enumerated-but-not-yet-classified"
                 split the Task text requires rather than a silent claim of
                 completeness.

--check validates the data file's internal schema, cross-references it
against the live tracked-script enumeration (flagging paths that are neither
classified nor enumerated, and stale entries for paths no longer tracked),
and prints a bounded summary. Exit 0 only if there are zero schema/coverage
errors.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import automation_safety  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_DATA = Path(__file__).resolve().parent / "chore_tool_inventory_data.json"

CATEGORIES = (
    "read-only", "atomic", "per-item-resumable", "destructive",
    "migration-only", "reusable", "retired",
)

_REQUIRED_CLASSIFIED_FIELDS = (
    "path", "category", "summary", "write_set", "commit_points", "journal",
    "cleanup", "failure_aggregation", "ownership", "retention", "test_ref",
    "findings",
)
_REQUIRED_COMMIT_POINT_FIELDS = ("function", "mechanism", "idempotency_key", "idempotent")
_REQUIRED_ENUMERATED_FIELDS = ("path", "category_guess", "note")


def load_data(path: Path = DEFAULT_DATA) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def _entry_errors(entry: Any, index: int, required: Sequence[str], label: str) -> List[str]:
    errors = []
    prefix = "%s[%d]" % (label, index)
    if not isinstance(entry, dict):
        return ["%s must be an object" % prefix]
    for field in required:
        if field not in entry:
            errors.append("%s: missing required field %r" % (prefix, field))
    return errors


def validate(data: Dict[str, Any], root: Path) -> Tuple[List[str], Dict[str, Any]]:
    """Validate schema + cross-reference against live tracked scripts.

    Returns (errors, stats). Empty errors == PASS.
    """
    errors: List[str] = []

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be %d" % SCHEMA_VERSION)

    classified = data.get("classified")
    enumerated = data.get("enumerated")
    if not isinstance(classified, list):
        errors.append("classified must be an array")
        classified = []
    if not isinstance(enumerated, list):
        errors.append("enumerated must be an array")
        enumerated = []

    seen_paths = set()
    classified_paths = set()
    for index, entry in enumerate(classified):
        errors.extend(_entry_errors(entry, index, _REQUIRED_CLASSIFIED_FIELDS, "classified"))
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if isinstance(path, str):
            if path in seen_paths:
                errors.append("classified[%d]: duplicate path %r" % (index, path))
            seen_paths.add(path)
            classified_paths.add(path)
        category = entry.get("category")
        if category not in CATEGORIES:
            errors.append("classified[%d]: category %r not one of %s" % (index, category, CATEGORIES))
        write_set = entry.get("write_set")
        if not isinstance(write_set, list):
            errors.append("classified[%d]: write_set must be an array (use [] for read-only)" % index)
        commit_points = entry.get("commit_points")
        if not isinstance(commit_points, list):
            errors.append("classified[%d]: commit_points must be an array (use [] for read-only)" % index)
        else:
            for cp_index, cp in enumerate(commit_points):
                cp_prefix = "classified[%d].commit_points[%d]" % (index, cp_index)
                if not isinstance(cp, dict):
                    errors.append("%s must be an object" % cp_prefix)
                    continue
                for field in _REQUIRED_COMMIT_POINT_FIELDS:
                    if field not in cp:
                        errors.append("%s: missing required field %r" % (cp_prefix, field))
        findings = entry.get("findings")
        if not isinstance(findings, list):
            errors.append("classified[%d]: findings must be an array (use [] when there is none)" % index)
        # category/commit_points/write_set consistency: a category with real
        # runtime mutation must declare at least one commit point or write.
        if category in ("atomic", "per-item-resumable", "destructive") and isinstance(commit_points, list):
            if not commit_points and not write_set:
                errors.append(
                    "classified[%d]: category %r declares no commit_points and no write_set" % (index, category)
                )
        if category == "read-only" and (write_set or commit_points):
            errors.append("classified[%d]: category 'read-only' must not declare write_set/commit_points" % index)

    for index, entry in enumerate(enumerated):
        errors.extend(_entry_errors(entry, index, _REQUIRED_ENUMERATED_FIELDS, "enumerated"))
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if isinstance(path, str):
            if path in seen_paths:
                errors.append("enumerated[%d]: path %r already present (classified and/or duplicate enumerated)" % (index, path))
            seen_paths.add(path)

    tracked, tracked_errors = automation_safety.tracked_automation_paths(root)
    for item in tracked_errors:
        errors.append("tracked-script enumeration error: %s" % item.get("message", item))
    tracked_set = set(tracked)

    inventory_set = seen_paths
    missing = sorted(tracked_set - inventory_set)
    stale = sorted(inventory_set - tracked_set)

    stats = {
        "classified_count": len(classified),
        "enumerated_count": len(enumerated),
        "tracked_count": len(tracked_set),
        "missing_from_inventory": missing,
        "stale_inventory_entries": stale,
        "classified_paths": sorted(classified_paths),
    }

    # A stale entry (path no longer tracked, e.g. renamed/deleted script) is
    # a data-quality error: the inventory must reflect real tracked state.
    for path in stale:
        errors.append("inventory entry %r no longer matches a tracked script (rename/removal not reconciled)" % path)

    # Missing paths are NOT an error: Task 0038-14 explicitly scoped its
    # first pass to four named categories and records the remainder as a
    # structured backlog rather than claiming exhaustive coverage. They are
    # surfaced in stats/--json for transparency instead.

    return errors, stats


def _print_summary(stats: Dict[str, Any], errors: List[str]) -> None:
    print("chore-tool-inventory: classified=%d enumerated=%d tracked=%d missing=%d stale=%d"
          % (stats["classified_count"], stats["enumerated_count"], stats["tracked_count"],
             len(stats["missing_from_inventory"]), len(stats["stale_inventory_entries"])))
    print("verdict:", "PASS" if not errors else "FAIL")
    for message in errors[:20]:
        print(" -", message)
    if len(errors) > 20:
        print(" - ... %d more" % (len(errors) - 20))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--check", action="store_true", help="validate schema + cross-reference; exit nonzero on any error")
    ap.add_argument("--json", action="store_true", help="emit stable JSON instead of the human summary")
    ap.add_argument("--list", choices=("classified", "enumerated", "missing", "stale"), help="print one bounded path list and exit")
    ap.add_argument("--category", choices=CATEGORIES, help="filter --list classified to one category")
    args = ap.parse_args(argv)

    data = load_data(args.data)
    errors, stats = validate(data, args.root)

    if args.list:
        if args.list == "classified":
            items = [c for c in data.get("classified", []) if isinstance(c, dict)]
            if args.category:
                items = [c for c in items if c.get("category") == args.category]
            for item in items:
                print(item.get("path"), "--", item.get("category"))
        elif args.list == "enumerated":
            for item in data.get("enumerated", []):
                print(item.get("path"), "--", item.get("category_guess"))
        elif args.list == "missing":
            for path in stats["missing_from_inventory"]:
                print(path)
        elif args.list == "stale":
            for path in stats["stale_inventory_entries"]:
                print(path)
        return 0

    if args.json:
        print(json.dumps({"errors": errors, "stats": stats}, ensure_ascii=False, indent=1))
    else:
        _print_summary(stats, errors)

    if args.check:
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
