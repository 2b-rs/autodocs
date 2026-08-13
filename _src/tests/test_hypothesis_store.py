import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import hypothesis_store as hs  # noqa: E402


class HypothesisStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_hyp_root = hs.HYPOTHESES_ROOT
        self._orig_rec_root = hs.RECORDS_ROOT
        hs.HYPOTHESES_ROOT = Path(self._tmpdir.name) / "hypotheses"
        hs.RECORDS_ROOT = Path(self._tmpdir.name) / "records"

    def tearDown(self):
        hs.HYPOTHESES_ROOT = self._orig_hyp_root
        hs.RECORDS_ROOT = self._orig_rec_root
        self._tmpdir.cleanup()

    def test_rejects_unregistered_project_kind(self):
        with self.assertRaises(ValueError):
            hs.record_hypothesis("NOT/A/PROJECT", "record", "SWS_XX_00001", "x", "y")

    def test_record_and_get_roundtrip(self):
        entry = hs.record_hypothesis("AUTOSAR/AP", "record", "SWS_XX_00001",
                                      "new requirement guess", "proposed text")
        self.assertTrue(entry["id"].startswith("hypothesis:"))
        self.assertEqual(entry["status"], "open")
        fetched = hs.get_hypothesis(entry["id"])
        self.assertEqual(fetched["id"], entry["id"])

    def test_list_hypotheses_filters(self):
        hs.record_hypothesis("AUTOSAR/AP", "record", "SWS_XX_00001", "a", "x")
        hs.record_hypothesis("AUTOSAR/AP", "record", "SWS_XX_00002", "b", "y")
        all_open = hs.list_hypotheses(status="open")
        self.assertEqual(len(all_open), 2)

    def test_reject_marks_status_without_deleting(self):
        entry = hs.record_hypothesis("AUTOSAR/AP", "record", "SWS_XX_00003", "a", "x")
        rejected = hs.reject_hypothesis(entry["id"], "not supported by spec text", "curator1")
        self.assertEqual(rejected["status"], "rejected")
        self.assertIsNotNone(hs.get_hypothesis(entry["id"]))
        with self.assertRaises(ValueError):
            hs.reject_hypothesis(entry["id"], "again", "curator1")

    def test_promote_writes_real_record_with_history_link(self):
        entry = hs.record_hypothesis("AUTOSAR/AP", "record", "SWS_XX_00004",
                                      "new requirement guess", "proposed text",
                                      evidence=["evidence:deadbeef-0000-7000-8000-000000000000"])
        result = hs.promote_hypothesis(entry["id"], "curator1", reason="confirmed against spec")
        record_path = Path(result["record_path"])
        self.assertTrue(record_path.exists())
        record = json.loads(record_path.read_text(encoding="utf-8"))
        self.assertEqual(record["history"][0]["source_hypothesis"], entry["id"])
        self.assertEqual(record["status"]["state"], "proposed/from-ai-hypothesis")
        promoted = hs.get_hypothesis(entry["id"])
        self.assertEqual(promoted["status"], "applied")
        self.assertEqual(promoted["promoted_to"], result["canonical_id"])

    def test_promote_refuses_to_overwrite_existing_record(self):
        entry = hs.record_hypothesis("AUTOSAR/AP", "record", "SWS_XX_00005", "a", "x")
        hs.RECORDS_ROOT.mkdir(parents=True, exist_ok=True)
        (hs.RECORDS_ROOT / "AP").mkdir(parents=True, exist_ok=True)
        (hs.RECORDS_ROOT / "AP" / "SWS_XX_00005.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            hs.promote_hypothesis(entry["id"], "curator1")


if __name__ == "__main__":
    unittest.main()
