import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "spec_extraction_benchmark.py"
DRAFT = ROOT / "_src" / "tests" / "fixtures" / "spec_extraction" / "benchmark-draft.json"
FROZEN = ROOT / "_src" / "tests" / "fixtures" / "spec_extraction" / "benchmark.json"
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
        data = json.loads(DRAFT.read_text(encoding="utf-8"))
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


class FrozenOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
        cls.draft = json.loads(DRAFT.read_text(encoding="utf-8"))

    def test_frozen_file_exists_and_parses_as_json(self):
        self.assertTrue(FROZEN.is_file())
        self.assertIsInstance(self.frozen, dict)
        self.assertEqual(json.loads(FROZEN.read_text(encoding="utf-8"))["status"], "frozen")

    def test_frozen_completeness_199_unique_ids_no_missing(self):
        records = self.frozen["records"]
        ids = [record["id"] for record in records]
        self.assertEqual(len(records), 199)
        self.assertEqual(len(set(ids)), 199)
        self.assertEqual(set(ids), set(self.frozen["record_manifest"]))
        self.assertNotIn("RS_SAF_21101", set(ids))
        self.assertEqual(set(ids), {record["id"] for record in self.draft["records"]})

    def test_frozen_fields_and_ids_are_immutable_versus_draft(self):
        draft_by_id = {record["id"]: record for record in self.draft["records"]}
        for record in self.frozen["records"]:
            source = draft_by_id[record["id"]]
            self.assertEqual(record["id"], source["id"])
            self.assertEqual(record["expected"], source["expected"])
            self.assertEqual(record["document"], source["document"])

    def test_frozen_status_and_manifest_validate(self):
        self.assertEqual(self.frozen["status"], "frozen")
        self.assertEqual(benchmark.validate_frozen(self.frozen), [])
        loaded = benchmark.load_frozen(FROZEN)
        self.assertEqual(loaded["content_sha256"], self.frozen["content_sha256"])
        self.assertEqual(len(loaded["record_manifest"]), 199)

    def test_manifest_bijection_property_over_all_frozen_records(self):
        executed = 0
        manifest = self.frozen["record_manifest"]
        seen = []
        for record in self.frozen["records"]:
            digest = benchmark.record_digest(record)
            self.assertEqual(manifest[record["id"]], digest)
            seen.append(record["id"])
            executed += 1
        self.assertEqual(executed, 199)
        self.assertEqual(len(set(seen)), 199)
        self.assertEqual(set(seen), set(manifest))
        self.assertEqual(
            self.frozen["content_sha256"],
            benchmark.content_sha256_from_manifest(benchmark.manifest_from_records(self.frozen["records"])),
        )

    def test_expected_field_mutation_breaks_every_record_digest(self):
        executed = 0
        for record in self.frozen["records"]:
            original = benchmark.record_digest(record)
            mutated = copy.deepcopy(record)
            mutated["expected"]["pages"] = list(mutated["expected"]["pages"]) + [99999]
            self.assertNotEqual(original, benchmark.record_digest(mutated))
            executed += 1
        self.assertEqual(executed, 199)

    def test_default_main_checks_frozen_oracle(self):
        old_argv = __import__("sys").argv
        try:
            __import__("sys").argv = ["spec_extraction_benchmark.py"]
            result = benchmark.main()
        finally:
            __import__("sys").argv = old_argv
        self.assertEqual(result, 0)

    def test_builder_refuses_to_overwrite_frozen_oracle(self):
        with tempfile.TemporaryDirectory() as directory:
            frozen = Path(directory) / "benchmark.json"
            frozen.write_text("{}\n", encoding="utf-8")
            campaign = Path(directory) / "campaign"
            (campaign / "raw").mkdir(parents=True)
            with self.assertRaises(benchmark.FrozenOverwriteError):
                benchmark.build_draft(campaign, frozen, 1, frozen)

    def test_compare_clean_frozen_copy_has_no_drift(self):
        report = benchmark.compare_to_frozen(self.frozen, copy.deepcopy(self.frozen["records"]))
        self.assertTrue(report["ok"])
        self.assertEqual(report["compared"], 199)
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["changed"], [])

    def test_compare_detects_changed_heading(self):
        records = copy.deepcopy(self.frozen["records"])
        records[0]["expected"]["heading"] = " Drifted heading "
        report = benchmark.compare_to_frozen(self.frozen, records)
        self.assertFalse(report["ok"])
        self.assertEqual(report["changed"][0]["id"], records[0]["id"])
        self.assertIn("heading", report["changed"][0]["fields"])

    def test_compare_detects_missing_id(self):
        records = copy.deepcopy(self.frozen["records"])
        missing_id = records.pop(0)["id"]
        report = benchmark.compare_to_frozen(self.frozen, records)
        self.assertFalse(report["ok"])
        self.assertEqual(report["missing"], [missing_id])

    def test_compare_detects_duplicate_id(self):
        records = copy.deepcopy(self.frozen["records"])
        records.append(copy.deepcopy(records[0]))
        report = benchmark.compare_to_frozen(self.frozen, records)
        self.assertFalse(report["ok"])
        self.assertEqual(report["duplicate"], [records[0]["id"]])

    def test_compare_detects_unresolved_entry(self):
        records = copy.deepcopy(self.frozen["records"])
        records[1]["expected"]["fields"] = None
        report = benchmark.compare_to_frozen(self.frozen, records)
        self.assertFalse(report["ok"])
        self.assertEqual(report["unresolved"][0]["id"], records[1]["id"])
        self.assertEqual(report["unresolved"][0]["reason"], "unresolved_expected")

    def test_compare_detects_unknown_extra_id(self):
        records = copy.deepcopy(self.frozen["records"])
        extra = copy.deepcopy(records[0])
        extra["id"] = "RS_EXTRA_99999"
        records.append(extra)
        report = benchmark.compare_to_frozen(self.frozen, records)
        self.assertFalse(report["ok"])
        self.assertEqual(report["extra"], ["RS_EXTRA_99999"])

    def test_review_note_change_is_not_semantic_drift(self):
        records = copy.deepcopy(self.frozen["records"])
        records[0]["review"] = {"status": "needs_review", "reviewer": "adjacent", "notes": "not an expected field"}
        report = benchmark.compare_to_frozen(self.frozen, records)
        self.assertTrue(report["ok"])

    def test_validate_rejects_status_or_cardinality_drift(self):
        drifted = copy.deepcopy(self.frozen)
        drifted["status"] = "draft-needs-manual-review"
        self.assertTrue(any("status" in error for error in benchmark.validate_frozen(drifted)))
        drifted = copy.deepcopy(self.frozen)
        drifted["records"] = drifted["records"][:-1]
        self.assertTrue(any("199" in error for error in benchmark.validate_frozen(drifted)))

    def test_freeze_from_draft_does_not_rewrite_review_status(self):
        frozen = benchmark.freeze_from_draft(self.draft, draft_path=DRAFT, draft_sha256="abc")
        self.assertEqual(frozen["status"], "frozen")
        review_status = {record["review"]["status"] for record in frozen["records"]}
        self.assertEqual(review_status, {record["review"]["status"] for record in self.draft["records"]})
        self.assertIn("reviewed", review_status)


if __name__ == "__main__":
    unittest.main()
