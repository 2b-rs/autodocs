#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_finding_triage.py -- Test suite for ECU Assessment Finding Triage & Remediation Governance (Task 0025-06)."""

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


class TestECUFindingTriage(unittest.TestCase):
    def setUp(self):
        self.payload = eft.assemble_finding_triage_record()

    def test_schema_and_governance_metadata(self):
        self.assertEqual(self.payload["schema"], eft.SCHEMA_TRIAGE)
        self.assertEqual(self.payload["triage_record_id"], f"ECU-TRIAGE-{eft.ASSESSED_BASELINE}")
        gov = self.payload["governance"]
        self.assertEqual(gov["product_id"], eft.ASSESSED_PRODUCT)
        self.assertEqual(gov["project_id"], eft.ASSESSED_PROJECT)
        self.assertEqual(gov["baseline_id"], eft.ASSESSED_BASELINE)
        self.assertEqual(gov["baseline_commit"], eft.BASELINE_COMMIT)
        self.assertEqual(gov["assessment_report_reference"], eft.ASSESSMENT_REPORT_ID)
        self.assertEqual(gov["governance_status"], "FORMALLY_TRIAGED_AND_APPROVED")
        self.assertIn("triage_record_sha256", self.payload)
        self.assertEqual(len(self.payload["triage_record_sha256"]), 64)

    def test_triage_summary_counts(self):
        summary = self.payload["triage_summary"]
        self.assertEqual(summary["total_findings_triaged"], 5)
        self.assertEqual(summary["approved_corrections_count"], 3)
        self.assertEqual(summary["accepted_residuals_count"], 2)
        self.assertEqual(summary["blocking_nonconformances_count"], 0)
        self.assertEqual(summary["overall_remediation_risk"], "LOW_MANAGED")

    def test_all_five_findings_triaged_with_mandatory_fields(self):
        findings = self.payload["triaged_findings"]
        self.assertEqual(len(findings), 5)

        finding_ids = [f["finding_id"] for f in findings]
        self.assertEqual(finding_ids, ["FIND-0025-01", "FIND-0025-02", "FIND-0025-03", "FIND-0025-04", "FIND-0025-05"])

        for f in findings:
            self.assertTrue(len(f["title"]) > 5)
            self.assertTrue(len(f["description"]) > 10)
            self.assertTrue(len(f["root_cause"]) >= 20, f"Root cause too brief for {f['finding_id']}")
            self.assertTrue(len(f["impact_analysis"]) >= 20, f"Impact analysis too brief for {f['finding_id']}")
            self.assertTrue(len(f["owner"]) > 0)
            self.assertTrue(f["due_date"].startswith("2026-"))
            self.assertIn(f["triage_disposition"], ["APPROVED_CORRECTION", "ACCEPTED_RESIDUAL"])
            self.assertTrue(f["governance_decision_ref"].startswith("DEC-0025-TRIAGE-"))
            self.assertTrue(len(f["affected_lifecycle_evidence"]) >= 1)
            self.assertTrue(len(f["required_reverification_plan"]) >= 20)
            self.assertTrue(len(f["reverification_criteria"]) >= 2)

    def test_remediation_tracking_and_governance_signoffs(self):
        tracking = self.payload["remediation_tracking_and_governance"]
        self.assertIn("SUP.9 / SUP.10", tracking["tracking_mechanism"])
        self.assertTrue(len(tracking["reverification_protocol"]) > 30)

        signoffs = tracking["governance_signoffs"]
        self.assertIn("odo", signoffs["lead_assessor_approval"])
        self.assertIn("jake", signoffs["qa_manager_approval"])
        self.assertIn("jadzia", signoffs["project_lead_approval"])
        self.assertEqual(signoffs["approval_date"], "2026-09-19")

    def test_traceability_to_assessment_report(self):
        report_payload = ear.assemble_level1_assessment_report()
        report_finding_ids = [f["finding_id"] for f in report_payload["findings_register"]]
        triage_finding_ids = [f["finding_id"] for f in self.payload["triaged_findings"]]
        self.assertEqual(report_finding_ids, triage_finding_ids, "Triage must cover 100% of findings in assessment report")

    def test_write_and_digest_stability(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_path = tmp_root / "test-triage.json"
            md_path = tmp_root / "test-triage.md"
            eft.write_finding_triage_record(json_path, md_path)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], eft.SCHEMA_TRIAGE)
            self.assertEqual(loaded["triage_summary"]["total_findings_triaged"], 5)

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Automotive ECU Assessment Finding Triage & Remediation Governance Record", md_text)
            self.assertIn("FIND-0025-01", md_text)
            self.assertIn("APPROVED_CORRECTION", md_text)
            self.assertIn("ACCEPTED_RESIDUAL", md_text)
            self.assertIn("Re-verification Acceptance Criteria", md_text)


if __name__ == "__main__":
    unittest.main()
