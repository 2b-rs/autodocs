"""Inventory embedded fonts and glyph-mapping failures per document.

Records which fonts a document uses, whether each declares a /ToUnicode map,
and how many characters actually decode to control codes or replacement
characters, because a declared map does not prove a usable one.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import spec_scrape  # noqa: E402


def _declared_fonts(path: Path) -> dict[str, dict]:
    from pypdf import PdfReader  # type: ignore

    declared: dict[str, dict] = {}
    for number, page in enumerate(PdfReader(str(path)).pages, 1):
        resources = page.get("/Resources") or {}
        fonts = resources.get("/Font") or {}
        try:
            items = list(fonts.items())
        except AttributeError:
            continue
        for _, reference in items:
            try:
                font = reference.get_object()
            except Exception:  # pragma: no cover - defensive
                continue
            base = str(font.get("/BaseFont", ""))
            entry = declared.setdefault(base, {
                "base_font": base, "subtype": str(font.get("/Subtype", "")),
                "has_to_unicode": False, "first_page": number,
            })
            if "/ToUnicode" in font:
                entry["has_to_unicode"] = True
    return declared


def inventory(pdf_dir: Path, doc: str) -> dict:
    path = pdf_dir / f"{doc}.pdf"
    pages = spec_scrape._pypdf_page_observations(path)
    declared = _declared_fonts(path)
    spans = collections.Counter()
    failures = collections.Counter()
    failing_pages: dict[str, set] = collections.defaultdict(set)
    for page in pages:
        for span in page["spans"]:
            font = span.get("font") or "(unnamed)"
            spans[font] += 1
            if span.get("unmapped_glyphs"):
                failures[font] += span["unmapped_glyphs"]
                failing_pages[font].add(page["page_number"])
    fonts = []
    for font, count in sorted(spans.items(), key=lambda item: -item[1]):
        info = declared.get(font, {})
        fonts.append({
            "font": font, "spans": count,
            "subtype": info.get("subtype", ""),
            "declares_to_unicode": info.get("has_to_unicode", False),
            "unmapped_glyphs": failures.get(font, 0),
            "failing_pages": sorted(failing_pages.get(font, []))[:10],
        })
    return {
        "document": doc,
        "font_count": len(fonts),
        "fonts_with_failures": sum(1 for f in fonts if f["unmapped_glyphs"]),
        "unmapped_glyphs": sum(failures.values()),
        "silent_failures": [
            f["font"] for f in fonts
            if f["unmapped_glyphs"] and f["declares_to_unicode"]
        ],
        "fonts": fonts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", required=True, type=Path)
    parser.add_argument("--doc", required=True)
    args = parser.parse_args()
    print(json.dumps(inventory(args.pdf_dir, args.doc)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
