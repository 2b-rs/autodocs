import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import spec_scrape as scrape


class PypdfGeometryTests(unittest.TestCase):
    def test_matrix_values_are_stable_and_detached(self):
        source = [1, 0, 0, 1, 12.123456789, 34]
        values = scrape._matrix_values(source)
        self.assertEqual(
            values,
            [1.0, 0.0, 0.0, 1.0, 12.123457, 34.0],
        )
        source[4] = 99
        self.assertEqual(values[4], 12.123457)

    def test_invalid_matrix_is_explicitly_absent(self):
        self.assertIsNone(scrape._matrix_values(None))
        self.assertIsNone(scrape._matrix_values([1, 2]))

    def test_effective_text_position_composes_matrices(self):
        self.assertEqual(
            scrape._effective_text_position(
                [2, 0, 0, 3, 10, 20], [1, 0, 0, 1, 4, 5]
            ),
            (18.0, 35.0),
        )
        self.assertIsNone(scrape._effective_text_position(None, [1, 0, 0, 1, 0, 0]))

    def test_line_clustering_uses_font_relative_baselines(self):
        spans = [
            {"id": "p1-s1", "position": (10, 100), "font_size": 12, "operation_index": 0},
            {"id": "p1-s2", "position": (40, 101.5), "font_size": 12, "operation_index": 1},
            {"id": "p1-s3", "position": (10, 80), "font_size": 12, "operation_index": 2},
            {"id": "p1-s4", "position": None, "font_size": 12, "operation_index": 3},
        ]
        lines, warnings = scrape._cluster_spans_into_lines(spans)
        self.assertEqual([line["span_ids"] for line in lines], [["p1-s1", "p1-s2"], ["p1-s3"]])
        self.assertEqual([line["id"] for line in lines], ["p1-l1", "p1-l2"])
        self.assertEqual(lines[0]["x_range"], [10, 40])
        self.assertEqual(warnings, ["p1-s4: missing-position"])

    def test_line_layout_exposes_large_gap_cells(self):
        line = {"id": "p1-l1", "span_ids": ["p1-s1", "p1-s2", "p1-s3"],
                "ordered_span_ids": ["p1-s1", "p1-s2", "p1-s3"]}
        spans = {
            "p1-s1": {"id": "p1-s1", "position": (10, 100), "font_size": 10},
            "p1-s2": {"id": "p1-s2", "position": (20, 100), "font_size": 10},
            "p1-s3": {"id": "p1-s3", "position": (100, 100), "font_size": 10},
        }
        layout = scrape._classify_line_layout(line, spans)
        self.assertEqual(layout["kind"], "cell-candidate")
        self.assertEqual([cell["span_ids"] for cell in layout["cells"]],
                         [["p1-s1", "p1-s2"], ["p1-s3"]])
        self.assertEqual(layout["cell_gap_threshold"], 36.0)

    def test_line_layout_keeps_normal_word_gaps_in_one_flow(self):
        line = {"id": "p1-l1", "span_ids": ["p1-s1", "p1-s2"],
                "ordered_span_ids": ["p1-s1", "p1-s2"]}
        spans = {
            "p1-s1": {"id": "p1-s1", "position": (10, 100), "font_size": 12},
            "p1-s2": {"id": "p1-s2", "position": (30, 100), "font_size": 12},
        }
        layout = scrape._classify_line_layout(line, spans)
        self.assertEqual(layout["kind"], "single-flow")
        self.assertEqual(len(layout["cells"]), 1)

    def test_repeated_cell_patterns_are_promoted(self):
        def line(number, starts):
            return {"id": f"p1-l{number}", "layout": {"kind": "cell-candidate", "cells": [
                {"x_range": [start, start], "span_ids": [f"p1-s{number}-{index}"]}
                for index, start in enumerate(starts, 1)
            ]}}
        lines = [line(1, [10, 100]), line(2, [10.04, 100.03]), line(3, [20, 200])]
        scrape._promote_repeated_cell_patterns(lines)
        self.assertEqual(lines[0]["layout"]["kind"], "table-row-candidate")
        self.assertEqual(lines[1]["layout"]["alignment_support"], 2)
        self.assertEqual(lines[1]["layout"]["supporting_line_ids"], ["p1-l1", "p1-l2"])
        self.assertEqual(lines[2]["layout"]["kind"], "isolated-gap-candidate")
        self.assertEqual(lines[2]["layout"]["alignment_support"], 1)

    def test_distant_matching_patterns_are_not_promoted(self):
        lines = [{"id": f"p1-l{i}", "layout": {"kind": "single-flow", "cells": []}}
                 for i in range(12)]
        for i in (0, 11):
            lines[i]["layout"] = {"kind": "cell-candidate", "cells": [
                {"x_range": [10, 10], "span_ids": [f"a{i}"]},
                {"x_range": [100, 100], "span_ids": [f"b{i}"]},
            ]}
        scrape._promote_repeated_cell_patterns(lines)
        self.assertEqual(lines[0]["layout"]["kind"], "isolated-gap-candidate")
        self.assertEqual(lines[11]["layout"]["kind"], "isolated-gap-candidate")

    def test_horizontal_order_is_geometric_and_stable(self):
        line = {"id": "p1-l1", "span_ids": ["p1-s1", "p1-s2", "p1-s3"]}
        spans = {
            "p1-s1": {"id": "p1-s1", "position": (30, 100), "operation_index": 0},
            "p1-s2": {"id": "p1-s2", "position": (10, 100), "operation_index": 1},
            "p1-s3": {"id": "p1-s3", "position": (20, 100), "operation_index": 2},
        }
        ordered, warnings = scrape._horizontal_span_order(line, spans)
        self.assertEqual(ordered, ["p1-s2", "p1-s3", "p1-s1"])
        self.assertEqual(warnings, [])

    def test_horizontal_order_ignores_layout_only_whitespace(self):
        line = {"id": "p1-l1", "span_ids": ["p1-s1", "p1-s2"]}
        spans = {
            "p1-s1": {"id": "p1-s1", "text": "\n", "position": (10, 100), "operation_index": 0},
            "p1-s2": {"id": "p1-s2", "text": "value", "position": (10, 100), "operation_index": 1},
        }
        ordered, warnings = scrape._horizontal_span_order(line, spans)
        self.assertEqual(ordered, ["p1-s1", "p1-s2"])
        self.assertEqual(warnings, [])

    def test_horizontal_order_uses_operation_order_at_identical_origin(self):
        line = {"id": "p1-l1", "span_ids": ["p1-s1", "p1-s2"]}
        spans = {
            "p1-s1": {"id": "p1-s1", "text": "first", "position": (10, 100), "operation_index": 0},
            "p1-s2": {"id": "p1-s2", "text": "second", "position": (10, 100), "operation_index": 1},
        }
        ordered, warnings = scrape._horizontal_span_order(line, spans)
        self.assertEqual(ordered, ["p1-s1", "p1-s2"])
        self.assertEqual(warnings, [])

    def test_horizontal_order_reports_ambiguous_positions(self):
        line = {"id": "p1-l1", "span_ids": ["p1-s1", "p1-s2"]}
        spans = {
            "p1-s1": {"id": "p1-s1", "text": "left", "position": (10, 100), "operation_index": 1},
            "p1-s2": {"id": "p1-s2", "text": "right", "position": (10.1, 100), "operation_index": 0},
        }
        ordered, warnings = scrape._horizontal_span_order(line, spans)
        self.assertEqual(ordered, ["p1-s1", "p1-s2"])
        self.assertEqual(len(warnings), 1)
        self.assertIn("ambiguous-horizontal-order", warnings[0])

    def test_observations_reject_non_pypdf_backend(self):
        with unittest.mock.patch.object(scrape, "discover_pdfs", return_value=[Path("x.pdf")]):
            with unittest.mock.patch.object(Path, "is_dir", return_value=True):
                self.assertEqual(
                    scrape.main(["observations", "--backend", "builtin"]),
                    2,
                )


class BuiltinCMapTests(unittest.TestCase):
    def test_bfchar_bfrange_and_array_are_decoded(self):
        cmap = scrape._parse_tounicode(b"""beginbfchar <63> <2308> endbfchar
beginbfrange <64> <65> <230A> <66> <67> [<0041> <0042>] endbfrange""")
        self.assertEqual(scrape._decode_pdf_string(b"(cdefg)", cmap), "⌈⌊⌋AB")

    def test_active_font_selects_tounicode_map(self):
        text = scrape._content_to_text(b"/F1 10 Tf [(c)(d)]TJ /F2 10 Tf (A) Tj",
                                       {"F1": {b"c": "⌈", b"d": "⌋"}, "F2": {b"A": "X"}})
        self.assertEqual(text, "⌈⌋X")


class RequirementFieldTests(unittest.TestCase):
    def test_normative_fields_are_split_when_cells_are_concatenated(self):
        text = """[RS_X_00001] Heading ⌈Description: The platform shall work.Rationale: Safety reason.Dependencies: RS_X_00002Use Case: Startup.AppliesTo: AP, CPSupporting Material: [1]⌋"""
        rec = scrape.parse_record(text, "RS_X_00001")
        self.assertEqual(rec["heading"], "Heading")
        self.assertEqual(rec["props"]["Description"], "The platform shall work")
        self.assertEqual(rec["props"]["Rationale"], "Safety reason")
        self.assertEqual(rec["props"]["Dependencies"], "RS_X_00002")
        self.assertEqual(rec["props"]["Use Case"], "Startup")
        self.assertEqual(rec["props"]["AppliesTo"], "AP, CP")
        self.assertEqual(rec["props"]["Supporting Material"], "[1]")

    def test_normative_labels_without_colons_are_boundaries(self):
        text = "[RS_X_00001] Heading ⌈Description Alpha Rationale – Dependencies RS_X_00002 Use Case Startup AppliesTo AP Supporting Material [1]⌋"
        rec = scrape.parse_record(text, "RS_X_00001")
        self.assertEqual(rec["props"]["Description"], "Alpha")
        self.assertEqual(rec["props"]["Rationale"], "")
        self.assertEqual(rec["props"]["Dependencies"], "RS_X_00002")
        self.assertEqual(rec["props"]["Use Case"], "Startup")
        self.assertEqual(rec["props"]["AppliesTo"], "AP")
        self.assertEqual(rec["props"]["Supporting Material"], "[1]")

    def test_heading_joins_positioning_lines_until_status(self):
        text = "[RS_X_00001]\nUCM\nshall support uninstalling software on\nAUTOSAR Adap-\ntive Platform\nStatus:\nDRAFT\n⌈Description: body⌋"
        rec = scrape.parse_record(text, "RS_X_00001")
        self.assertEqual(rec["heading"], "UCM shall support uninstalling software on AUTOSAR Adap- tive Platform")
        self.assertEqual(rec["props"]["Description"], "body")

    def test_next_requirement_never_spills_into_field(self):
        text = """[RS_X_00001] First ⌈Description: AlphaRationale: Because⌋
[RS_X_00002] Second ⌈Description: BetaRationale: Other⌋"""
        rec = scrape.parse_record(text, "RS_X_00001")
        self.assertEqual(rec["props"]["Description"], "Alpha")
        self.assertEqual(rec["props"]["Rationale"], "Because")
        self.assertNotIn("Beta", str(rec))

    def test_prose_requirement_without_labels_remains_requirement_text(self):
        text = "[RS_X_00001] Heading ⌈The platform shall preserve this prose.⌋"
        rec = scrape.parse_record(text, "RS_X_00001")
        self.assertEqual(rec["requirement_text"], "The platform shall preserve this prose")
        self.assertEqual(rec["props"], {})


if __name__ == "__main__":
    unittest.main()
