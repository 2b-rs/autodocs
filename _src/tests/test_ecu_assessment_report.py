#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_assessment_report.py -- Test suite for ECU Level-1 Assessment Report (Task 0025-05)."""

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
import ecu_process_assessment as epa  # noqa: E402


class TestECUAssessmentReport(unittest.TestCase):
    def setUp(self):
        self.payload = ear.assemble_level1_assessment_report()

    def test_schema_and_metadata(self):
        self.assertEqual(self.payload["schema"], ear.SCHEMA_REPORT)
        self.assertEqual(self.payload["report_id"], f"ECU-L1-REPORT-{ear.ASSESSED_BASELINE}")
        gov = self.payload["governance"]
        self.assertEqual(gov["product_id"], ear.ASSESSED_PRODUCT)
        self.assertEqual(gov["project_id"], ear.ASSESSED_PROJECT)
        self.assertEqual(gov["baseline_id"], ear.ASSESSED_BASELINE)
        self.assertEqual(gov["baseline_commit"], ear.BASELINE_COMMIT)
        self.assertIn("report_sha256", self.payload)
        self.assertEqual(len(self.payload["report_sha256"]), 64)

    def test_executive_summary_disposition(self):
        summary = self.payload["executive_summary"]
        self.assertEqual(summary["overall_assessment_disposition"], "LEVEL_1_CAPABILITY_CONFIRMED")
        self.assertEqual(summary["total_in_scope_processes"], 15)
        self.assertEqual(summary["processes_achieving_level1"], 15)
        self.assertEqual(summary["level1_compliance_rate_percent"], 100.0)
        self.assertEqual(summary["findings_summary"]["non_conformances"], 0)
        self.assertEqual(summary["findings_summary"]["observations"], 3)
        self.assertEqual(summary["findings_summary"]["opportunities_for_improvement"], 2)

    def test_scope_and_boundary_definition(self):
        scope_def = self.payload["scope_and_boundary_definition"]
        self.assertEqual(len(scope_def["in_scope_processes"]), 15)

        expected_in_scope = [
            "SYS.1", "SYS.2", "SYS.3", "SYS.4", "SYS.5",
            "SWE.1", "SWE.2", "SWE.3", "SWE.4", "SWE.5", "SWE.6",
            "VAL.1", "SPL.2", "SUP.1", "SUP.8", "SUP.9", "SUP.10",
            "MAN.3", "MAN.5", "MAN.6", "PIM.3",
        ]
        actual_in_scope = scope_def["in_scope_processes"]
        for ep in actual_in_scope:
            self.assertIn(ep, expected_in_scope)

        # Out of scope and external processes
        oos_list = scope_def["out_of_scope_and_external_processes"]
        oos_ids = [p["process_id"] for p in oos_list]
        self.assertIn("HWE.1", oos_ids)
        self.assertIn("HWE.2", oos_ids)
        self.assertIn("HWE.3", oos_ids)
        self.assertIn("HWE.4", oos_ids)
        self.assertIn("ACQ.4", oos_ids)

        for oos in oos_list:
            self.assertIn(oos["disposition"], ["OUT_OF_SCOPE_UNRATED", "EXTERNAL_INTERFACE_ONLY"])
            self.assertTrue(len(oos["rationale"]) > 10)

        self.assertIn("Shared in-scope processes rated on approved process-instance boundary", scope_def["boundary_isolation_rule"])

    def test_process_capability_profile(self):
        profile = self.payload["process_capability_profile"]
        self.assertEqual(len(profile), 15)

        for p in profile:
            self.assertEqual(p["pa11_rating"], "F")
            self.assertEqual(p["capability_level"], 1)
            self.assertTrue(p["evidence_count"] >= 1)
            self.assertTrue(len(p["strengths"]) >= 1)
            self.assertTrue(len(p["outcome_summary"]) > 10)

    def test_execution_responsibility_and_certification(self):
        cert = self.payload["assessment_disposition_and_certification"]
        self.assertEqual(cert["verdict"], "CERTIFIED_LEVEL_1_CAPABLE")
        self.assertTrue(len(cert["statement"]) > 50)
        
        exec_resp = cert["execution_responsibility"]
        self.assertIn("odo", exec_resp["lead_assessor_signature"])
        self.assertIn("jake", exec_resp["qa_manager_signature"])
        self.assertIn("jadzia", exec_resp["project_lead_sponsor_signature"])
        self.assertEqual(exec_resp["certification_date"], "2026-09-19")

    def test_controlled_findings_register(self):
        findings = self.payload["findings_register"]
        self.assertEqual(len(findings), 5)

        finding_ids = [f["finding_id"] for f in findings]
        self.assertEqual(finding_ids, ["FIND-0025-01", "FIND-0025-02", "FIND-0025-03", "FIND-0025-04", "FIND-0025-05"])

        categories = [f["category"] for f in findings]
        self.assertEqual(categories.count("OBSERVATION"), 3)
        self.assertEqual(categories.count("OFI"), 2)
        self.assertEqual(categories.count("NON_CONFORMANCE"), 0)

        for f in findings:
            self.assertEqual(f["status"], "OPEN")
            self.assertTrue(len(f["title"]) > 5)
            self.assertTrue(len(f["description"]) > 10)
            self.assertTrue(len(f["impact"]) > 5)
            self.assertTrue(len(f["owner"]) > 0)

    def test_institutional_strengths_and_risks(self):
        strengths = self.payload["key_institutional_strengths"]
        risks = self.payload["residual_risks_and_mitigations"]

        self.assertTrue(len(strengths) >= 4)
        self.assertTrue(len(risks) >= 2)

        for r in risks:
            self.assertIn("risk_id", r)
            self.assertIn("description", r)
            self.assertIn("mitigation", r)
            self.assertIn("status", r)

    def test_evidence_baseline_linkage(self):
        ref = self.payload["evidence_baseline_reference"]
        self.assertEqual(ref["evidence_index_id"], f"ECU-EVIDENCE-INDEX-{ear.ASSESSED_BASELINE}")
        self.assertTrue(ref["total_artifacts"] >= 15)
        self.assertIn("ecu-execution exclusively", ref["origin_filter_enforced"])

    def test_write_and_digest_stability(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_path = tmp_root / "test-report.json"
            md_path = tmp_root / "test-report.md"
            ear.write_level1_assessment_report(json_path, md_path)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], ear.SCHEMA_REPORT)
            self.assertEqual(loaded["executive_summary"]["overall_assessment_disposition"], "LEVEL_1_CAPABILITY_CONFIRMED")

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Automotive ECU Level-1 Process Capability Assessment Report", md_text)
            self.assertIn("LEVEL_1_CAPABILITY_CONFIRMED", md_text)
            self.assertIn("FIND-0025-01", md_text)
            self.assertIn("HWE.1", md_text)
            self.assertIn("ACQ.4", md_text)


if __name__ == "__main__":
    unittest.main()
