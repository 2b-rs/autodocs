#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_cl2_handoff.py -- Test suite for ECU Level-1 Success & CL2 Handoff (Task 0025-10)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ecu_assessment_report as ear  # noqa: E402
import ecu_cl2_handoff as ech  # noqa: E402
import ecu_evidence_index as eei  # noqa: E402
import ecu_finding_triage as eft  # noqa: E402
import ecu_published_profile as epp  # noqa: E402
import ecu_readiness_review as err  # noqa: E402
import ecu_reassessment_cycle as erc  # noqa: E402


class TestECUCL2Handoff(unittest.TestCase):
    def setUp(self):
        self.payload = ech.assemble_cl2_handoff_record()

    def test_schema_and_metadata(self):
        self.assertEqual(self.payload["schema"], ech.SCHEMA_HANDOFF)
        self.assertEqual(self.payload["handoff_record_id"], f"ECU-CL2-HANDOFF-{ech.ASSESSED_BASELINE}")
        gov = self.payload["governance"]
        self.assertEqual(gov["product_id"], ech.ASSESSED_PRODUCT)
        self.assertEqual(gov["project_id"], ech.ASSESSED_PROJECT)
        self.assertEqual(gov["release_baseline"], ech.ASSESSED_BASELINE)
        self.assertEqual(gov["commit_reference"], ech.BASELINE_COMMIT)
        self.assertEqual(gov["evidence_baseline_reference"], ech.EVIDENCE_INDEX_ID)
        self.assertEqual(gov["handoff_status"], "CL2_HANDOFF_AUTHORIZED")
        self.assertIn("handoff_record_sha256", self.payload)
        self.assertEqual(len(self.payload["handoff_record_sha256"]), 64)

    def test_success_confirmation_summary(self):
        summary = self.payload["success_confirmation_summary"]
        self.assertEqual(summary["total_cl2_entry_processes"], 15)
        self.assertEqual(summary["processes_with_pa11_at_least_l"], 15)
        self.assertEqual(summary["cl1_compliance_rate_percent"], 100.0)
        self.assertEqual(summary["total_gate_edges_evaluated"], 5)
        self.assertEqual(summary["gate_edges_satisfied"], 5)
        self.assertTrue(summary["all_conditional_edges_satisfied"])
        self.assertEqual(summary["overall_pilot_disposition"], "SUCCESSFUL_PILOT_LEVEL1_CERTIFIED")

    def test_all_five_conditional_gate_edges_satisfied(self):
        edges = self.payload["conditional_gate_edges_register"]
        self.assertEqual(len(edges), 5)

        edge_ids = [e["edge_id"] for e in edges]
        self.assertEqual(edge_ids, ["EDGE-01", "EDGE-02", "EDGE-03", "EDGE-04", "EDGE-05"])

        for e in edges:
            self.assertEqual(e["status"], "SATISFIED")
            self.assertTrue(len(e["description"]) > 10)
            self.assertTrue(len(e["required_condition"]) > 20)
            self.assertTrue(len(e["observed_evidence"]) > 20)

    def test_cl2_entry_process_validations(self):
        procs = self.payload["cl2_entry_process_validations"]
        self.assertEqual(len(procs), 15)

        for p in procs:
            self.assertEqual(p["pa11_rating"], "F")
            self.assertEqual(p["cl1_performance_status"], "FULLY_SATISFIED")
            self.assertTrue(p["cl2_entry_eligible"])

    def test_formal_level1_success_statement(self):
        stmt = self.payload["formal_level1_success_statement"]
        self.assertEqual(stmt["statement_title"], "Official Confirmation of Automotive SPICE Level 1 Success")
        self.assertTrue(len(stmt["statement_text"]) >= 50)
        self.assertIn("jadzia", stmt["authorized_by"])
        self.assertIn("odo", stmt["concurred_by"])
        self.assertEqual(stmt["date"], "2026-09-19")

    def test_formal_cl2_handoff_authorization(self):
        auth = self.payload["formal_cl2_handoff_authorization"]
        self.assertEqual(auth["statement_title"], "Executive Authorization for Automotive SPICE Capability Level 2 Progression")
        self.assertTrue(len(auth["statement_text"]) >= 50)
        self.assertIn("Level 2", auth["cl2_governance_target"])
        self.assertEqual(auth["target_milestone"], "Milestone v0.7.0")

        signoffs = auth["signoffs"]
        self.assertIn("jadzia", signoffs["project_sponsor_signature"])
        self.assertIn("odo", signoffs["lead_assessor_signature"])
        self.assertIn("jake", signoffs["qa_manager_signature"])
        self.assertIn("kira", signoffs["architect_signature"])
        self.assertEqual(signoffs["signed_date"], "2026-09-19")

    def test_accepted_limitations(self):
        limitations = self.payload["accepted_limitations_boundary"]
        self.assertEqual(len(limitations), 3)

        lim_ids = [l["limitation_id"] for l in limitations]
        self.assertEqual(lim_ids, ["LIMIT-0025-01", "LIMIT-0025-02", "LIMIT-0025-03"])

    def test_write_and_digest_stability(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_path = tmp_root / "test-handoff.json"
            md_path = tmp_root / "test-handoff.md"
            ech.write_cl2_handoff_record(json_path, md_path)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], ech.SCHEMA_HANDOFF)
            self.assertEqual(loaded["governance"]["handoff_status"], "CL2_HANDOFF_AUTHORIZED")

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Automotive ECU Level-1 Success Confirmation & CL2-Handoff Authorization Record", md_text)
            self.assertIn("SUCCESSFUL_PILOT_LEVEL1_CERTIFIED", md_text)
            self.assertIn("EDGE-01", md_text)
            self.assertIn("Official Confirmation of Automotive SPICE Level 1 Success", md_text)


if __name__ == "__main__":
    unittest.main()
