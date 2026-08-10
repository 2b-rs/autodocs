import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import geometry_schema  # noqa: E402


def _page() -> dict:
    return {
        "page_number": 1, "raw_text": "x", "backend": "pypdf", "warnings": [],
        "columns": [], "reading_order": ["l1"],
        "spans": [{
            "id": "s1", "text": "x", "current_matrix": [1, 0, 0, 1, 0, 0],
            "text_matrix": [1, 0, 0, 1, 10, 700], "position": [10, 700],
            "font": "/F1", "font_size": 10.0, "operation_index": 0,
            "inferred_spacing": False, "inferred_line_break": False,
            "orientation": "upright", "unmapped_glyphs": 0,
        }],
        "lines": [{
            "id": "l1", "baseline_y": 700.0, "x_range": [10, 50],
            "span_ids": ["s1"], "ordered_span_ids": ["s1"], "tolerance": 2.0,
            "operation_index": 0, "layout": {"kind": "single-flow"},
            "same_origin_groups": [], "margin_band": None, "margin_band_support": 0,
            "margin_span_roles": {}, "bullet": None, "indent_level": 0,
            "flow": "block-start", "flow_gap": None, "column_index": None,
            "reading_position": 0,
        }],
    }


class GeometrySchemaTests(unittest.TestCase):
    def test_valid_page_has_no_errors(self):
        self.assertEqual(geometry_schema.validate_page(_page()), [])

    def test_unexpected_field_is_reported(self):
        page = _page()
        page["lines"][0]["surprise"] = 1
        self.assertTrue(any("unexpected field surprise" in e for e in geometry_schema.validate_page(page)))

    def test_missing_field_is_reported(self):
        page = _page()
        del page["lines"][0]["flow"]
        self.assertTrue(any("missing field flow" in e for e in geometry_schema.validate_page(page)))

    def test_unknown_span_reference_is_reported(self):
        page = _page()
        page["lines"][0]["ordered_span_ids"] = ["ghost"]
        errors = geometry_schema.validate_page(page)
        self.assertTrue(any("unknown span ghost" in e for e in errors))

    def test_invalid_enumeration_is_reported(self):
        page = _page()
        page["lines"][0]["margin_band"] = "sidebar"
        self.assertTrue(any("invalid margin_band" in e for e in geometry_schema.validate_page(page)))

    def test_document_validation_aggregates_pages(self):
        good, bad = _page(), _page()
        bad["page_number"] = 2
        bad["lines"][0]["flow"] = "sideways"
        self.assertEqual(len(geometry_schema.validate_document([good, bad])), 1)


if __name__ == "__main__":
    unittest.main()
