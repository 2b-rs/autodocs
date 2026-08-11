import json
import tempfile
import unittest
from pathlib import Path

import sys

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from spec_upstream import (  # noqa: E402
    UpstreamIndex,
    rebuild_record_files,
    rebuild_upstream,
    referenced_rs_ids,
)


class SpecUpstreamTest(unittest.TestCase):
    def setUp(self):
        self.index = UpstreamIndex([
            {"id": "RS_MAIN_00001", "document": "AUTOSAR_RS_Main", "page": 7},
            {"id": "RS_DUP_00002", "document": "a"},
            {"id": "rs_dup_00002", "document": "b"},
        ])

    def test_reference_extraction_ignores_existing_upstream(self):
        value = {"text": "Satisfies [RS_MAIN_00001].", "upstream": [{"id": "RS_OLD_9"}]}
        self.assertEqual(referenced_rs_ids(value), ("RS_MAIN_00001",))

    def test_expected_unresolved_is_diagnostic_not_failure(self):
        index = UpstreamIndex([])
        after, outcome = rebuild_upstream({"id": "SWS_X_1", "blocks": [{"text": "RS_AP_00154"}]}, index)
        self.assertEqual(outcome, "updated")
        self.assertEqual(after["upstream"], [{"id": "RS_AP_00154", "status": "expected-unresolved"}])

    def test_updated_and_unchanged(self):
        source = {"id": "SWS_X_1", "text": "See RS_MAIN_00001", "keep": {"x": 1}}
        updated, outcome = rebuild_upstream(source, self.index)
        self.assertEqual(outcome, "updated")
        self.assertEqual(updated["keep"], source["keep"])
        same, outcome = rebuild_upstream(updated, self.index)
        self.assertEqual(outcome, "unchanged")
        self.assertEqual(same, updated)

    def test_missing_and_ambiguous_are_explicit(self):
        missing, status = rebuild_upstream({"text": "RS_MISSING_00003"}, self.index)
        self.assertEqual((status, missing["upstream"][0]["status"]), ("missing", "missing"))
        ambiguous, status = rebuild_upstream({"text": "RS_DUP_00002"}, self.index)
        self.assertEqual((status, ambiguous["upstream"][0]["status"]), ("ambiguous", "ambiguous"))

    def test_compare_does_not_write_and_rebuild_is_idempotent(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as root:
            path = Path(root) / "record.json"
            path.write_text(json.dumps({"id": "SWS_X_1", "text": "RS_MAIN_00001"}))
            before = path.read_bytes()
            self.assertEqual(rebuild_record_files([path], self.index)["updated"], 1)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(rebuild_record_files([path], self.index, write=True)["updated"], 1)
            self.assertEqual(rebuild_record_files([path], self.index)["unchanged"], 1)


if __name__ == "__main__":
    unittest.main()
