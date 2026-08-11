#!/usr/bin/env python3
"""Build a deterministic, review-first 200-record extraction benchmark draft."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ID_RE = re.compile(r"(?:RS|SWS)_[A-Za-z0-9_]+_\d{3,}")
CATEGORIES = (
    "multi_page", "dense_fields", "lists", "multiple_per_page",
    "mixed_case_id", "typography", "empty_or_dash", "single_page",
)


def load_records(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("records"), (dict, list)):
        data = data["records"]
    if isinstance(data, list):
        return {str(r.get("id") or r.get("requirement_id")): r for r in data
                if isinstance(r, dict) and (r.get("id") or r.get("requirement_id"))}
    if isinstance(data, dict):
        return {str(k): v for k, v in data.items()
                if isinstance(v, dict) and ID_RE.fullmatch(str(k))}
    return {}


def text(record: dict) -> str:
    props = record.get("props") or record.get("fields") or {}
    values = [record.get("heading"), record.get("requirement_text"), record.get("text_raw")]
    values.extend(props.values() if isinstance(props, dict) else ())
    return "\n".join(str(v) for v in values if v is not None)


def pages(record: dict) -> list[int]:
    raw = (record.get("pages") or record.get("page_range")
           or (record.get("source") or {}).get("pages")
           or record.get("pages_all_definitions")
           or record.get("page") or [])
    if isinstance(raw, int):
        return [raw]
    if isinstance(raw, str):
        return [int(x) for x in re.findall(r"\d+", raw)]
    return [int(x) for x in raw if isinstance(x, (int, float))]


def classify(rid: str, record: dict, page_count: dict[int, int]) -> list[str]:
    value, pgs = text(record), pages(record)
    props = record.get("props") or record.get("fields") or {}
    result = []
    if len(set(pgs)) >= 2: result.append("multi_page")
    if isinstance(props, dict) and len(props) >= 5: result.append("dense_fields")
    if re.search(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+", value): result.append("lists")
    if any(page_count[p] > 1 for p in pgs): result.append("multiple_per_page")
    observed = str(record.get("id_observed") or rid)
    prefix = observed.rsplit("_", 1)[0]
    if any(c.islower() for c in prefix): result.append("mixed_case_id")
    if re.search(r"[ﬁﬂ–—‘’“”]|\w-\n\w|\ufffd", value): result.append("typography")
    if any(str(v).strip() in {"", "-", "–", "—"} for v in props.values()) if isinstance(props, dict) else False:
        result.append("empty_or_dash")
    if len(set(pgs)) <= 1: result.append("single_page")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("campaign", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--size", type=int, default=200)
    args = ap.parse_args()
    raw = args.campaign / "raw"
    pairs: dict[str, dict[str, Path]] = defaultdict(dict)
    for path in sorted(raw.glob("*.json")):
        match = re.match(r"(.+)\.(pypdf|builtin)\.json$", path.name)
        if match: pairs[match.group(1)][match.group(2)] = path
    candidates = []
    for document, files in sorted(pairs.items()):
        by_backend = {b: load_records(p) for b, p in files.items()}
        ids = sorted(set().union(*(set(v) for v in by_backend.values())))
        page_count: dict[int, int] = defaultdict(int)
        preferred = by_backend.get("pypdf", {}) or by_backend.get("builtin", {})
        for rid in ids:
            for p in set(pages(preferred.get(rid, {}))): page_count[p] += 1
        for rid in ids:
            record = preferred.get(rid) or by_backend.get("builtin", {}).get(rid, {})
            candidates.append({
                "id": rid, "document": document, "categories": classify(rid, record, page_count),
                "backend_presence": sorted(b for b, records in by_backend.items() if rid in records),
                "expected": {"heading": record.get("heading"), "fields": record.get("props") or record.get("fields") or {},
                             "pages": pages(record), "complete_start": None,
                             "complete_end": record.get("complete_end")},
                "review": {"status": "needs_review", "reviewer": None, "notes": ""},
            })
    selected, used = [], set()
    def take(predicate, limit):
        for c in candidates:
            key = (c["document"], c["id"])
            if key not in used and predicate(c):
                selected.append(c); used.add(key)
                if limit and sum(1 for x in selected if predicate(x)) >= limit: break
    for document in sorted(pairs): take(lambda c, d=document: c["document"] == d, 1)
    for category in CATEGORIES[:-1]: take(lambda c, k=category: k in c["categories"], 25)
    take(lambda c: len(c["backend_presence"]) == 1, 0)
    take(lambda c: True, args.size)
    selected = selected[:args.size]
    args.output.mkdir(parents=True, exist_ok=True)
    fixture = {"schema": 1, "status": "draft-needs-manual-review", "campaign": args.campaign.name,
               "selection_policy": {"target_size": args.size, "minimum_per_difficult_shape": 25,
                                    "categories": list(CATEGORIES)}, "records": selected}
    (args.output / "benchmark-draft.json").write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {k: sum(k in c["categories"] for c in selected) for k in CATEGORIES}
    docs = {d: sum(c["document"] == d for c in selected) for d in sorted(pairs)}
    report = ["# Extraction benchmark draft", "", f"Selected: {len(selected)} / {args.size}", "",
              "This is a review queue, not a frozen truth set. Every record must be checked manually.", "",
              "## Shape coverage", ""] + [f"- {k}: {v}" for k, v in counts.items()] + ["", "## Document coverage", ""] + [f"- {k}: {v}" for k, v in docs.items()]
    (args.output / "README.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"selected": len(selected), "shape_counts": counts, "document_counts": docs}, indent=2))
    return 0 if len(selected) == args.size and all(v for v in docs.values()) else 2

if __name__ == "__main__":
    raise SystemExit(main())
