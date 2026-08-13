"""Inventory and classification of queue items / special-case review surfaces
into the unified curation model (Feature 0006-12).

Four input categories named in the 0006-12 task text, each classified into
exactly one of CLASSIFICATIONS with a documented, non-arbitrary rule:

- review-queue / curation-queue open items -> "first_class": these ARE live,
  pending decisions. curation_item.py's 0006-03 read adapters
  (from_review_flag/from_curation_flag) already normalize them losslessly
  and read-only, so there is nothing destructive to migrate -- normalizing
  on read IS the migration for these two categories.
- extraction_report.py's RESIDUAL list -> "report_only": each entry is
  already a FINISHED code-level decision (a hardcoded exception baked into
  the extraction logic itself), not a pending item awaiting a lifecycle
  state. It belongs in a report as a fact about the extraction, not in a
  curation queue as something to act on.
- SWS_LOG pilot records' requirement_meta.review_status/review_reason ->
  "historical_archive": this predates the unified model (0006-03/0006-06)
  and its campaign (2026-08-sws-log-pilot-after-tool-improvement, see
  0006-08) has already completed for the pilot module -- it is a record of
  what WAS decided, not something with an open lifecycle state today.

This module is read-only: it inventories and classifies, it does not delete,
rewrite, or move any of the scanned files. Building a first-class,
queue-format-independent live view of "first_class" items is 0006-09's job
(the curation report); this module answers the prior question of WHICH
surfaces that report should even look at.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

SRC_ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = SRC_ROOT / "spec"
RECORDS_DIR = SPEC_ROOT / "records"
EXTRACTION_REPORT_PY = SRC_ROOT / "tools" / "extraction_report.py"

CLASSIFICATIONS = ("first_class", "report_only", "historical_archive")


def _queue_open_items(queue_name: str) -> list:
    base = SPEC_ROOT / queue_name / "open"
    if not base.is_dir():
        return []
    items = []
    for f in sorted(base.glob("*.json")):
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        items.append({"source": queue_name, "file": f.name, "id": payload.get("id"),
                      "campaign": payload.get("campaign"), "schema": payload.get("schema")})
    return items


def _residual_entries() -> list:
    if not EXTRACTION_REPORT_PY.is_file():
        return []
    src = EXTRACTION_REPORT_PY.read_text(encoding="utf-8")
    m = re.search(r"RESIDUAL\s*=\s*\[(.*?)\n\]", src, re.S)
    if not m:
        return []
    ids = re.findall(r'"id"\s*:\s*"([^"]+)"', m.group(1))
    return [{"source": "extraction_report.RESIDUAL", "id": rid} for rid in ids]


def _pilot_review_status_records() -> list:
    if not RECORDS_DIR.is_dir():
        return []
    out = []
    for f in sorted(RECORDS_DIR.glob("SWS_LOG/*.json")):
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        meta = payload.get("requirement_meta") or {}
        if "review_status" in meta or "review_reason" in meta:
            out.append({"source": "requirement_meta.review_*", "id": f.stem,
                        "review_status": meta.get("review_status"),
                        "review_reason": meta.get("review_reason")})
    return out


def build_inventory() -> dict:
    """Returns a dict with one key per classification, each a list of
    category summaries: {category, classification, rule, count, items}."""
    review_items = _queue_open_items("review-queue")
    curation_items = _queue_open_items("curation-queue")
    residual = _residual_entries()
    pilot = _pilot_review_status_records()

    categories = [
        {
            "category": "review-queue (open)",
            "classification": "first_class",
            "rule": "live pending decisions; curation_item.from_review_flag() already normalizes these read-only",
            "count": len(review_items),
            "items": review_items,
        },
        {
            "category": "curation-queue (open)",
            "classification": "first_class",
            "rule": "live pending decisions; curation_item.from_curation_flag() already normalizes these read-only",
            "count": len(curation_items),
            "items": curation_items,
        },
        {
            "category": "extraction_report.RESIDUAL",
            "classification": "report_only",
            "rule": "finished code-level decisions baked into extraction logic, not pending items awaiting a lifecycle state",
            "count": len(residual),
            "items": residual,
        },
        {
            "category": "SWS_LOG requirement_meta.review_*",
            "classification": "historical_archive",
            "rule": "predates the unified model; pilot campaign already completed for this module",
            "count": len(pilot),
            "items": pilot,
        },
    ]

    by_classification = {c: [] for c in CLASSIFICATIONS}
    for cat in categories:
        by_classification[cat["classification"]].append(cat)
    return {"categories": categories, "by_classification": by_classification}


def classification_for(category_name: str) -> str | None:
    inv = build_inventory()
    for cat in inv["categories"]:
        if cat["category"] == category_name:
            return cat["classification"]
    return None
