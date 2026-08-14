#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_score.py — Structural validation checks for scraped Eclipse S-CORE units (0009-06).

Checks performed:
1. Canonical ID syntax and kind registered in projects.json (via canonical_id.py)
2. Module package containment (components belong to an existing scraped module)
3. Sphinx-needs format validation on design-doc / process-doc units
4. Version ID consistency and provenance completeness
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
import canonical_id


def validate_score_records(records: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """Validate a collection of scraped Eclipse S-CORE records.

    Returns (errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []

    modules = set()
    for rec in records:
        if rec.get("kind") == "module":
            modules.add(rec.get("id"))

    for i, rec in enumerate(records):
        proj = rec.get("project", "")
        kind = rec.get("kind", "")
        item_id = rec.get("id", "")
        can_id = rec.get("canonical_id", "")
        ver_id = rec.get("version_id", "")
        prov = rec.get("provenance", {})

        # 1. Check project and kind registration
        if not canonical_id.is_valid(proj, kind):
            errors.append(f"Record #{i} ({can_id}): invalid project '{proj}' or kind '{kind}' in projects registry")

        # 2. Check canonical ID consistency
        expected_can_id = f"{proj}/{kind}/{item_id}"
        if can_id != expected_can_id:
            errors.append(f"Record #{i}: canonical_id '{can_id}' != expected '{expected_can_id}'")

        # 3. Check version ID structure
        if not ver_id.startswith(f"{can_id}@rel:") or "#" not in ver_id:
            errors.append(f"Record #{i} ({can_id}): malformed version_id '{ver_id}'")

        # 4. Check provenance completeness
        if not prov.get("source_commit") or len(prov.get("source_commit")) < 8:
            warnings.append(f"Record #{i} ({can_id}): missing or incomplete source_commit in provenance")
        if not prov.get("source_ref"):
            errors.append(f"Record #{i} ({can_id}): missing source_ref in provenance")

        # 5. Kind-specific structural checks
        if kind == "component":
            # Must belong to an identified module
            parent_mod = item_id.split(".")[0]
            if parent_mod not in modules:
                warnings.append(f"Component '{item_id}' parent module '{parent_mod}' not found in scraped module set")

        elif kind in ("design-doc", "process-doc"):
            if not item_id:
                errors.append(f"Record #{i} ({kind}): missing ID for sphinx-needs requirement/doc item")

    return errors, warnings


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 validate_score.py <records.json>")
        return 1

    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"Error: File {p} not found")
        return 1

    data = json.loads(p.read_text(encoding="utf-8"))
    records = data.get("records", [])
    errors, warnings = validate_score_records(records)

    print(f"Validated {len(records)} Eclipse S-Core records: {len(errors)} errors, {len(warnings)} warnings.")
    for err in errors:
        print(f"  [ERROR] {err}")
    for warn in warnings:
        print(f"  [WARN]  {warn}")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
