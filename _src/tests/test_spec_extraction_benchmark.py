import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "spec_extraction_benchmark.py"
FIXTURE = ROOT / "_src" / "tests" / "fixtures" / "spec_extraction" / "benchmark-draft.json"
SPEC = importlib.util.spec_from_file_location("spec_extraction_benchmark", TOOL)
assert SPEC and SPEC.loader
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class BenchmarkSelectionTests(unittest.TestCase):
    def test_citation_only_record_has_no_definition_anchor(self):
        citation = {"id": "RS_SAF_21101", "heading": None, "props": {}, "complete_start": False, "complete_end": False}
        self.assertFalse(benchmark.has_definition_anchor(citation))

    def test_marker_before_or_after_id_is_a_definition(self):
        before = {"id": "RS_A_00001", "complete_start": True}
        after = {"id": "RS_A_00002", "complete_end": True}
        self.assertTrue(benchmark.has_definition_anchor(before))
        self.assertTrue(benchmark.has_definition_anchor(after))

    def test_legacy_populated_record_without_boundary_flags_remains_eligible(self):
        record = {"id": "RS_A_00001", "heading": "A definition", "props": {"Description": "text"}}
        self.assertTrue(benchmark.has_definition_anchor(record))

    def test_fixture_no_longer_contains_known_citation_only_entry(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(len(data["records"]), 199)
        self.assertNotIn("RS_SAF_21101", {record["id"] for record in data["records"]})

    def test_main_skips_and_reports_citation_only_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            campaign = Path(directory) / "campaign"
            raw = campaign / "raw"
            output = Path(directory) / "output"
            raw.mkdir(parents=True)
            records = [
                {"id": "RS_A_00001", "heading": "before", "props": {"Description": "x"}, "complete_start": True, "pages": [1]},
                {"id": "RS_A_00002", "heading": "after", "props": {"Description": "y"}, "complete_end": True, "pages": [2]},
                {"id": "RS_SAF_21101", "heading": None, "props": {}, "complete_start": False, "complete_end": False, "pages": [9]},
            ]
            for backend in ("pypdf", "builtin"):
                (raw / f"AUTOSAR_TEST.{backend}.json").write_text(json.dumps(records), encoding="utf-8")
            old_argv = __import__("sys").argv
            try:
                __import__("sys").argv = ["spec_extraction_benchmark.py", str(campaign), "--output", str(output), "--size", "2"]
                result = benchmark.main()
            finally:
                __import__("sys").argv = old_argv
            self.assertEqual(result, 0)
            draft = json.loads((output / "benchmark-draft.json").read_text(encoding="utf-8"))
            self.assertEqual({record["id"] for record in draft["records"]}, {"RS_A_00001", "RS_A_00002"})
            self.assertEqual(draft["skipped"][0]["id"], "RS_SAF_21101")
            self.assertEqual(draft["skipped"][0]["reason"], "no_definition_anchor")
            self.assertIn("Skipped: 1", (output / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
