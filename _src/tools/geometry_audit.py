"""Audit geometry classifiers across a whole PDF corpus.

Checks document-independent invariants and reports per-document counts so
layout regressions surface on every cached specification, not only on one
canonical document.
"""
from __future__ import annotations

import argparse
import collections
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
        "max_indent_level": 0, "non_upright_spans": 0, "unmapped_glyph_spans": 0,
        "unmapped_glyphs": 0, "single_span_lines": 0, "unclassified_body_lines": 0,
        "quarantined_spans": 0, "body_word_shortfall": 0,
    }
    if [page["raw_text"] for page in pages] != legacy:
        violations.append("raw-text-parity")
    violations.extend(f"schema:{issue}" for issue in geometry_schema.validate_document(pages)[:20])
    for page in pages:
        counts["spans"] += len(page["spans"])
        for span in page["spans"]:
            if span.get("orientation") != "upright":
                counts["non_upright_spans"] += 1
            if span.get("unmapped_glyphs"):
                counts["unmapped_glyph_spans"] += 1
                counts["unmapped_glyphs"] += span["unmapped_glyphs"]
            clustered = any(
                span["id"] in line.get("span_ids", []) for line in page["lines"]
            )
            if span.get("orientation") in ("vertical", "skewed") and clustered:
                violations.append(f"non-horizontal-clustered:{page['page_number']}:{span['id']}")
            if span.get("unmapped_glyphs") and clustered:
                violations.append(f"unmapped-glyphs-clustered:{page['page_number']}:{span['id']}")
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
                if len(line.get("ordered_span_ids", [])) == 1:
                    counts["single_span_lines"] += 1
                if line.get("flow") is None or line.get("indent_level") is None:
                    counts["unclassified_body_lines"] += 1
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
        spans_by_id = {span["id"]: span for span in page["spans"]}
        clustered = {
            span_id for line in page["lines"]
            for span_id in line.get("span_ids", [])
        }
        counts["quarantined_spans"] += sum(
            1 for span in page["spans"] if span["id"] not in clustered
        )
        body_words: collections.Counter = collections.Counter()
        for line in page["lines"]:
            if line.get("margin_band"):
                continue
            text = spec_scrape._reconstructed_line_text(line, spans_by_id)
            body_words.update(text.split())
        margin_words: collections.Counter = collections.Counter()
        for line in page["lines"]:
            if not line.get("margin_band"):
                continue
            text = spec_scrape._reconstructed_line_text(line, spans_by_id)
            margin_words.update(text.split())
        expected = collections.Counter(page["raw_text"].split())
        expected.subtract(margin_words)
        shortfall = sum(
            count - body_words[word]
            for word, count in expected.items()
            if count > body_words[word]
        )
        counts["body_word_shortfall"] += max(shortfall, 0)
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
