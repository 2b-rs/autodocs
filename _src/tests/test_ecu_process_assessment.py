#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_process_assessment.py -- Test suite for ECU Level-1 Process Assessment and PA 1.1 Ratings (Task 0025-04)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ecu_evidence_index as eei  # noqa: E402
import ecu_process_assessment as epa  # noqa: E402


class TestECUProcessAssessment(unittest.TestCase):
    def setUp(self):
        self.payload = epa.assemble_assessment_record()

    def test_schema_and_metadata(self):
        self.assertEqual(self.payload["schema"], epa.SCHEMA_ASSESSMENT)
        self.assertEqual(self.payload["product_id"], epa.ASSESSED_PRODUCT)
        self.assertEqual(self.payload["project_id"], epa.ASSESSED_PROJECT)
        self.assertEqual(self.payload["baseline_id"], epa.ASSESSED_BASELINE)
        self.assertIn("record_sha256", self.payload)
        self.assertEqual(len(self.payload["record_sha256"]), 64)

    def test_all_eight_interview_sessions_conducted(self):
        sessions = self.payload["interview_sessions"]
        self.assertEqual(len(sessions), 8)
        session_ids = [s["session_id"] for s in sessions]
        expected_ids = ["SESSION-A", "SESSION-B", "SESSION-C", "SESSION-D", "SESSION-E", "SESSION-F", "SESSION-G", "SESSION-H"]
        self.assertEqual(session_ids, expected_ids)

        for s in sessions:
            self.assertTrue(len(s["interviewees"]) >= 2)
            self.assertTrue(len(s["topics_covered"]) >= 1)
            self.assertTrue(len(s["inquiries_and_evidence_observations"]) >= 1)

    def test_process_characterizations_and_pa11_ratings(self):
        procs = self.payload["process_characterizations"]
        self.assertGreaterEqual(len(procs), 14)  # At least 14 processes in nucleus profile

        proc_ids = [p["process_id"] for p in procs]
        required_procs = [
            "SWE.1", "SWE.2", "SWE.3", "SWE.4", "SWE.5", "SWE.6",
            "SPL.2", "SUP.1", "SUP.8", "SUP.9", "SUP.10", "MAN.3", "MAN.5", "MAN.6"
        ]
        for rp in required_procs:
            self.assertIn(rp, proc_ids, f"Required nucleus process {rp} missing from characterizations")

        for p in procs:
            self.assertIn(p["pa11_rating"], epa.RATING_SCALE)
            self.assertTrue(len(p["rating_justification"]) > 20)
            self.assertTrue(len(p["base_practice_evaluations"]) >= 4)
            for bp in p["base_practice_evaluations"]:
                self.assertEqual(bp["status"], "SATISFIED")
                self.assertTrue(len(bp["findings"]) > 5)
                self.assertTrue(bp["evidence_ref"].startswith("EVID-"))

    def test_no_cross_process_averaging(self):
        # Verify that each process characterization specifies its own justification
        procs = self.payload["process_characterizations"]
        justifications = [p["rating_justification"] for p in procs]
        self.assertEqual(len(justifications), len(set(justifications)), "Process justifications must be unique and independently reasoned")

    def test_evidence_references_resolve_to_frozen_evidence_index(self):
        frozen_index = eei.assemble_frozen_evidence_index()
        valid_artifact_ids = {a["artifact_id"] for a in frozen_index["artifacts"]}

        for p in self.payload["process_characterizations"]:
            for ref in p["evidence_references"]:
                self.assertIn(ref, valid_artifact_ids, f"Evidence reference {ref} in process {p['process_id']} not found in frozen index")

    def test_write_assessment_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_path = tmp_root / "test-assessment.json"
            md_path = tmp_root / "test-assessment.md"
            epa.write_assessment_record(json_path, md_path)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], epa.SCHEMA_ASSESSMENT)
            self.assertEqual(loaded["summary"]["verdict"], "LEVEL_1_CAPABILITY_CONFIRMED_ALL_PROCESSES")

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Automotive ECU Level-1 Process Assessment", md_text)
            self.assertIn("SESSION-A", md_text)
            self.assertIn("SWE.1", md_text)
            self.assertIn("LEVEL 1 ACHIEVED", md_text)


if __name__ == "__main__":
    unittest.main()
