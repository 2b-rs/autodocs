import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("spec_extraction_campaign", TOOLS / "spec_extraction_campaign.py")
campaign = importlib.util.module_from_spec(spec); spec.loader.exec_module(campaign)


class ExtractionCampaignTests(unittest.TestCase):
    def test_create_emits_two_backend_jobs_and_hashes(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); pdf = root / "AUTOSAR_FO_RS_Test.pdf"
            pdf.write_bytes(b"stable pdf fixture")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                value = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            self.assertEqual([job["backend"] for job in value["jobs"]], ["pypdf", "builtin"])
            self.assertEqual(len(value["documents"][0]["sha256"]), 64)
            stored = json.loads((root / "campaign" / "manifest.json").read_text())
            self.assertEqual(stored["git_revision"], "abc")

    def test_applies_to_comma_spacing_is_layout_only(self):
        left = {"RS_X_00001": {"props": {"AppliesTo": "FO, CP , AP"}}}
        right = {"RS_X_00001": {"props": {"AppliesTo": "FO,CP,AP"}}}
        rows, summary = campaign.compare_records(left, right)
        self.assertEqual(summary, {"total_ids": 1, "normalized": 1})
        self.assertEqual(rows[0]["field_differences"], [])

    def test_commas_remain_significant_outside_applies_to(self):
        left = {"RS_X_00001": {"props": {"Description": "alpha , beta"}}}
        right = {"RS_X_00001": {"props": {"Description": "alpha,beta"}}}
        rows, summary = campaign.compare_records(left, right)
        self.assertEqual(summary, {"total_ids": 1, "different": 1})
        self.assertEqual(rows[0]["field_differences"][0]["field"], "Description")

    def test_compare_is_field_aware(self):
        left = {"RS_X_00001": {"heading": "Heading", "props": {"Description": "alpha beta"}, "page": 2}}
        right = {"RS_X_00001": {"heading": "Heading", "props": {"Description": "alpha  beta"}, "page": 2},
                 "RS_X_00002": {"heading": "Only builtin", "props": {}, "page": 3}}
        rows, summary = campaign.compare_records(left, right)
        self.assertEqual(rows[0]["status"], "normalized")
        self.assertEqual(rows[1]["status"], "only-builtin")
        self.assertEqual(summary["total_ids"], 2)

    def test_report_writes_side_by_side_artifacts(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); (root / "raw").mkdir()
            manifest = {"campaign": "fixture", "documents": [{"name": "Doc"}]}
            (root / "manifest.json").write_text(json.dumps(manifest))
            a = {"RS_X_00001": {"heading": "A", "props": {"Description": "left"}, "page": 1}}
            b = {"RS_X_00001": {"heading": "A", "props": {"Description": "right"}, "page": 1}}
            (root / "raw" / "Doc.pypdf.json").write_text(json.dumps(a))
            (root / "raw" / "Doc.builtin.json").write_text(json.dumps(b))
            score = campaign.report(root)
            self.assertEqual(score["documents_complete"], 1)
            for name in ("comparison.json", "scorecard.json", "comparison.csv", "comparison.html"):
                self.assertTrue((root / name).is_file(), name)
            self.assertIn("pypdf", (root / "comparison.html").read_text())
            self.assertIn("builtin", (root / "comparison.html").read_text())


if __name__ == "__main__":
    unittest.main()
