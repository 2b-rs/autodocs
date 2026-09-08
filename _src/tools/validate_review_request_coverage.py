#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_review_request_coverage.py -- Validate corpus-wide review-request metadata coverage (0033-09).

Reconciles record, eligible, excluded, rendered-action, and active-request counts.
Ensures every eligible real record derives authoritative canonical ID, latest version ID,
content hash, controlled status, and deep source locator without synthetic overrides.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "_src"
TOOLS = SRC / "tools"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import canonical_id as cid_util  # noqa: E402
import curation_flags as cf  # noqa: E402
import lib_docmodel as dm  # noqa: E402
import review_request_package as rrp  # noqa: E402
import version_id as vid_util  # noqa: E402
import version_store as vstore  # noqa: E402

INVENTORY_SCHEMA = "review-request-coverage-inventory@v1"


def audit_corpus_coverage(srcdir: Path = SRC) -> Dict[str, Any]:
    """Scan all records under spec/records and evaluate review-request metadata readiness."""
    records_root = srcdir / "spec" / "records"
    record_files = sorted(records_root.glob("**/*.json"))

    total_records = len(record_files)
    eligible_count = 0
    excluded_count = 0
    rendered_actions_count = 0
    active_requests_count = 0

    status_breakdown: Dict[str, int] = {}
    eligible_records: List[str] = []
    excluded_records: List[Dict[str, str]] = []
    errors: List[str] = []

    # Check active queue items
    open_index = dm._load_open_review_request_index(str(srcdir))
    active_requests_count = len(set(open_index.keys()))

    for rpath in record_files:
        try:
            with rpath.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            errors.append(f"Failed to read JSON at {rpath}: {exc}")
            continue

        raw_id = data.get("id") or rpath.stem
        parsed_cid = cid_util.parse_canonical_id(raw_id)
        if parsed_cid is None:
            resolved_cid = cid_util.resolve_legacy(raw_id)
            parsed_cid = cid_util.parse_canonical_id(resolved_cid)
        else:
            resolved_cid = raw_id

        if parsed_cid is None:
            excluded_count += 1
            excluded_records.append({
                "path": str(rpath.relative_to(ROOT)),
                "id": raw_id,
                "reason": "unresolvable_canonical_id",
            })
            continue

        proj = parsed_cid["project"]
        kind = parsed_cid["kind"]
        if not cid_util.is_valid(proj, kind):
            excluded_count += 1
            excluded_records.append({
                "path": str(rpath.relative_to(ROOT)),
                "id": raw_id,
                "reason": f"invalid_project_or_kind_registry:{proj}/{kind}",
            })
            continue

        eligible_count += 1
        eligible_records.append(resolved_cid)

        # Render panel block to verify metadata derivation
        status_dict = data.get("status") or {}
        st_state = status_dict.get("state", "unspecified")
        status_breakdown[st_state] = status_breakdown.get(st_state, 0) + 1

        panel_html = dm._render_review_request_panel(
            raw_id,
            data.get("review_request") or {},
            status_dict,
            page_dir_depth=1,
            srcdir=str(srcdir),
            rec_blocks=data.get("blocks"),
        )

        if not panel_html:
            errors.append(f"Empty panel rendered for eligible record: {resolved_cid}")
            continue

        # Extract embedded JSON payload
        m = re.search(r'<script type="application/json" class="review-request-data">(\{.*?\})</script>', panel_html)
        if not m:
            errors.append(f"Missing review-request-data script in panel for: {resolved_cid}")
            continue

        payload = json.loads(m.group(1))
        # Validate required fields
        p_cid = payload.get("canonical_id")
        p_vid = payload.get("version_id")
        p_hash = payload.get("content_hash")
        p_source = payload.get("source_url")
        p_status = payload.get("status")

        if not p_cid or p_cid != resolved_cid:
            errors.append(f"Canonical ID mismatch for {resolved_cid}: {p_cid}")
        if not p_vid or not re.match(r"^.+@rel:.+#.+$", p_vid):
            errors.append(f"Invalid or null version_id for {resolved_cid}: {p_vid}")
        if not p_hash or len(p_hash) != 8:
            errors.append(f"Invalid or null content_hash for {resolved_cid}: {p_hash}")
        if not p_source or not p_source.startswith("http"):
            errors.append(f"Invalid or missing deep source_url for {resolved_cid}: {p_source}")
        if not p_status:
            errors.append(f"Missing status in payload for {resolved_cid}")

        if "Queue file" in panel_html or "spec/curation-queue" in panel_html:
            errors.append(f"Local filesystem path leaked in public HTML for {resolved_cid}")

        rendered_actions_count += 1

    report = {
        "schema": INVENTORY_SCHEMA,
        "audited_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "totals": {
            "total_records": total_records,
            "eligible_records": eligible_count,
            "excluded_records": excluded_count,
            "rendered_actions": rendered_actions_count,
            "active_requests_in_queue": active_requests_count,
        },
        "status_breakdown": status_breakdown,
        "errors": errors,
        "passed": len(errors) == 0 and (eligible_count == total_records or excluded_count == 0),
    }
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="Print report as JSON")
    ap.add_argument("--check", action="store_true", help="Exit 1 if any coverage errors are detected")
    args = ap.parse_args(argv)

    report = audit_corpus_coverage(SRC)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Review Request Metadata Coverage Inventory")
        print(f"Audited at:         {report['audited_at']}")
        print(f"Total records:      {report['totals']['total_records']}")
        print(f"Eligible records:   {report['totals']['eligible_records']}")
        print(f"Excluded records:   {report['totals']['excluded_records']}")
        print(f"Rendered actions:   {report['totals']['rendered_actions']}")
        print(f"Active in queue:    {report['totals']['active_requests_in_queue']}")
        print("Status breakdown:")
        for st, count in sorted(report['status_breakdown'].items()):
            print(f"  - {st}: {count}")
        if report["errors"]:
            print(f"\nERRORS ({len(report['errors'])}):")
            for err in report["errors"][:20]:
                print(f"  ! {err}")
            if len(report["errors"]) > 20:
                print(f"  ... and {len(report['errors']) - 20} more.")
        else:
            print("\nCoverage validation PASSED with zero errors.")

    if args.check and not report["passed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
