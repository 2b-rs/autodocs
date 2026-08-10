import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import spec_scrape as scrape


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
