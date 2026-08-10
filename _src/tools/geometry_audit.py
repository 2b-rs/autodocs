"""Audit geometry classifiers across a whole PDF corpus.

Checks document-independent invariants and reports per-document counts so
layout regressions surface on every cached specification, not only on one
canonical document.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import geometry_schema  # noqa: E402
import spec_scrape  # noqa: E402


def audit_document(pdf_dir: Path, doc: str) -> dict:
    path = pdf_dir / f"{doc}.pdf"
    pages = spec_scrape._pypdf_page_observations(path)
    legacy = spec_scrape._pypdf_pages(path)
    violations: list[str] = []
    counts = {
        "pages": len(pages), "spans": 0, "lines": 0, "body_lines": 0,
        "header_lines": 0, "footer_lines": 0, "bullets": 0, "wraps": 0,
        "block_starts": 0, "column_pages": 0, "zero_baseline_lines": 0,
        "max_indent_level": 0,
    }
    if [page["raw_text"] for page in pages] != legacy:
        violations.append("raw-text-parity")
    violations.extend(f"schema:{issue}" for issue in geometry_schema.validate_document(pages)[:20])
    for page in pages:
        counts["spans"] += len(page["spans"])
        counts["lines"] += len(page["lines"])
        seen: set[str] = set()
        body_ids = set()
        for line in page["lines"]:
            for span_id in line.get("ordered_span_ids", []):
                if span_id in seen:
                    violations.append(f"span-reused:{page['page_number']}:{span_id}")
                seen.add(span_id)
            if float(line["baseline_y"]) <= 0:
                counts["zero_baseline_lines"] += 1
            band = line.get("margin_band")
            if band == "header":
                counts["header_lines"] += 1
            elif band == "footer":
                counts["footer_lines"] += 1
            elif float(line["baseline_y"]) > 0 and line.get("ordered_span_ids"):
                counts["body_lines"] += 1
                body_ids.add(line["id"])
            if line.get("bullet"):
                counts["bullets"] += 1
            if line.get("flow") == "wrap":
                counts["wraps"] += 1
            elif line.get("flow") == "block-start":
                counts["block_starts"] += 1
            level = line.get("indent_level")
            if isinstance(level, int):
                counts["max_indent_level"] = max(counts["max_indent_level"], level)
        if page.get("columns"):
            counts["column_pages"] += 1
        order = page.get("reading_order", [])
        if sorted(order) != sorted(body_ids):
            violations.append(f"reading-order-coverage:{page['page_number']}")
        if len(set(order)) != len(order):
            violations.append(f"reading-order-duplicate:{page['page_number']}")
    return {"document": doc, "counts": counts, "violations": violations}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", required=True, type=Path)
    parser.add_argument("--doc", required=True)
    args = parser.parse_args()
    result = audit_document(args.pdf_dir, args.doc)
    print(json.dumps(result))
    return 1 if result["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
