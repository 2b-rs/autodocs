#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_reassessment_cycle.py -- Test suite for ECU Correction, Re-verification & Reassessment (Task 0025-07)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ecu_assessment_report as ear  # noqa: E402
import ecu_evidence_index as eei  # noqa: E402
import ecu_finding_triage as eft  # noqa: E402
import ecu_reassessment_cycle as erc  # noqa: E402


class TestECUReassessmentCycle(unittest.TestCase):
    def setUp(self):
        self.payload = erc.assemble_reassessment_cycle_record()

    def test_schema_and_governance_metadata(self):
        self.assertEqual(self.payload["schema"], erc.SCHEMA_REASSESSMENT)
        self.assertEqual(self.payload["reassessment_record_id"], f"ECU-REASSESS-{erc.ASSESSED_BASELINE}")
        gov = self.payload["governance"]
        self.assertEqual(gov["product_id"], erc.ASSESSED_PRODUCT)
        self.assertEqual(gov["project_id"], erc.ASSESSED_PROJECT)
        self.assertEqual(gov["original_baseline"], erc.ASSESSED_BASELINE)
        self.assertEqual(gov["revised_baseline"], erc.REVISED_BASELINE)
        self.assertEqual(gov["original_commit"], erc.BASELINE_COMMIT)
        self.assertEqual(gov["reassessment_commit"], erc.REASSESSMENT_COMMIT)
        self.assertEqual(gov["cycle_status"], "REASSESSMENT_PASSED_LEVEL_1_CERTIFIED")
        self.assertIn("reassessment_record_sha256", self.payload)
        self.assertEqual(len(self.payload["reassessment_record_sha256"]), 64)

    def test_cycle_summary(self):
        summary = self.payload["cycle_summary"]
        self.assertEqual(summary["total_in_scope_processes"], 15)
        self.assertEqual(summary["processes_achieving_level1"], 15)
        self.assertEqual(summary["level1_compliance_rate_percent"], 100.0)
        self.assertEqual(summary["total_corrections_executed"], 3)
        self.assertEqual(summary["corrections_verified_closed"], 3)
        self.assertEqual(summary["open_corrections_count"], 0)
        self.assertEqual(summary["accepted_residual_risks_count"], 2)
        self.assertEqual(summary["blocking_nonconformances_count"], 0)
        self.assertEqual(summary["exit_criteria_disposition"], "LEVEL_1_EXIT_GATE_CLEARED")

    def test_executed_corrections_completeness(self):
        corrections = self.payload["executed_corrections"]
        self.assertEqual(len(corrections), 3)

        corr_ids = [c["correction_id"] for c in corrections]
        self.assertEqual(corr_ids, ["CORR-0025-01", "CORR-0025-02", "CORR-0025-03"])

        for c in corrections:
            self.assertEqual(c["closure_status"], "VERIFIED_CLOSED")
            self.assertTrue(len(c["implementation_summary"]) >= 20)
            self.assertTrue(len(c["reverification_method"]) >= 20)
            self.assertTrue(c["reverification_result"].startswith("PASS"))
            self.assertTrue(len(c["effectiveness_evaluation"]) >= 20)
            self.assertTrue(len(c["owner"]) > 0)
            self.assertEqual(c["closed_at"], "2026-09-19")

    def test_process_reassessment_profile(self):
        profile = self.payload["process_reassessment_profile"]
        self.assertEqual(len(profile), 15)

        for p in profile:
            self.assertEqual(p["reassessed_pa11_rating"], "F")
            self.assertEqual(p["capability_level"], 1)
            self.assertTrue(p["target_met"])
            self.assertEqual(p["status"], "CONFIRMED_LEVEL_1")
            self.assertTrue(len(p["reassessment_justification"]) >= 20)

    def test_exit_criteria_evaluation(self):
        exit_eval = self.payload["exit_criteria_evaluation"]
        self.assertEqual(len(exit_eval), 4)

        for crit_key, crit_val in exit_eval.items():
            self.assertEqual(crit_val["status"], "SATISFIED", f"Exit criterion {crit_key} must be SATISFIED")
            self.assertTrue(len(crit_val["evidence"]) > 10)

    def test_formal_certification_signoffs(self):
        cert = self.payload["formal_certification_signoff"]
        self.assertEqual(cert["verdict"], "ASPICE_LEVEL_1_CAPABILITY_RECONFIRMED")
        self.assertTrue(len(cert["certification_statement"]) >= 50)

        signoffs = cert["signoffs"]
        self.assertIn("odo", signoffs["lead_assessor_signature"])
        self.assertIn("jake", signoffs["qa_manager_signature"])
        self.assertIn("jadzia", signoffs["project_lead_sponsor_signature"])
        self.assertEqual(signoffs["signed_date"], "2026-09-19")

    def test_evidence_baseline_revision(self):
        rev = self.payload["evidence_baseline_revision"]
        self.assertEqual(rev["revised_evidence_index_id"], f"ECU-EVIDENCE-INDEX-{erc.REVISED_BASELINE}")
        self.assertTrue(rev["cryptographic_integrity_verified"])
        self.assertIn("v0.6.0 to v0.6.0-rev1", rev["revision_summary"])

    def test_write_and_digest_stability(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_path = tmp_root / "test-reassessment.json"
            md_path = tmp_root / "test-reassessment.md"
            erc.write_reassessment_cycle_record(json_path, md_path)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], erc.SCHEMA_REASSESSMENT)
            self.assertEqual(loaded["cycle_summary"]["exit_criteria_disposition"], "LEVEL_1_EXIT_GATE_CLEARED")

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Automotive ECU Post-Correction Reassessment & Capability Confirmation Record", md_text)
            self.assertIn("CORR-0025-01", md_text)
            self.assertIn("LEVEL_1_EXIT_GATE_CLEARED", md_text)
            self.assertIn("ASPICE_LEVEL_1_CAPABILITY_RECONFIRMED", md_text)


if __name__ == "__main__":
    unittest.main()
