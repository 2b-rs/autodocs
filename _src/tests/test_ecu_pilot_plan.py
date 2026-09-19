#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_pilot_plan.py -- Test suite for ECU Managed Pilot Plan & Process Selection (Task 0018-01)."""

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
import ecu_pilot_plan as epp  # noqa: E402
import ecu_published_profile as epub  # noqa: E402
import ecu_readiness_review as err  # noqa: E402
import ecu_reassessment_cycle as erc  # noqa: E402


class TestECUPilotPlan(unittest.TestCase):
    def setUp(self):
        self.payload = epp.assemble_pilot_assessment_plan()

    def test_schema_and_governance_metadata(self):
        self.assertEqual(self.payload["schema"], epp.SCHEMA_PILOT_PLAN)
        self.assertEqual(self.payload["plan_id"], f"ECU-PILOT-PLAN-{epp.TARGET_BASELINE}")
        gov = self.payload["governance"]
        self.assertEqual(gov["product_id"], epp.ASSESSED_PRODUCT)
        self.assertEqual(gov["project_id"], epp.ASSESSED_PROJECT)
        self.assertEqual(gov["target_release_baseline"], epp.TARGET_BASELINE)
        self.assertEqual(gov["predecessor_baseline"], epp.PREDECESSOR_BASELINE)
        self.assertEqual(gov["target_commit"], epp.TARGET_COMMIT)
        self.assertEqual(gov["reference_standard"], epp.PAM_VERSION)
        self.assertEqual(gov["plan_status"], "FORMALLY_APPROVED_FOR_EXECUTION")
        self.assertIn("pilot_plan_sha256", self.payload)
        self.assertEqual(len(self.payload["pilot_plan_sha256"]), 64)

    def test_pilot_scope_summary(self):
        summary = self.payload["pilot_scope_summary"]
        self.assertEqual(summary["total_selected_processes"], 17)
        self.assertEqual(summary["target_capability_level"], 2)
        self.assertIn("GP 2.1 Performance Management", summary["target_generic_practices"])
        self.assertIn("GP 2.2 Work Product Management", summary["target_generic_practices"])
        self.assertEqual(summary["total_interview_sessions_planned"], 6)
        self.assertEqual(summary["total_sampling_rules"], 3)
        self.assertTrue(summary["evidence_isolation_rule_enforced"])

    def test_selected_pilot_processes_completeness(self):
        procs = self.payload["selected_pilot_processes"]
        self.assertEqual(len(procs), 17)

        proc_ids = [p["process_id"] for p in procs]
        expected_ids = [
            "SWE.1", "SWE.2", "SWE.3", "SWE.4", "SWE.5", "SWE.6",
            "SYS.2", "SYS.3", "VAL.1", "SPL.2",
            "SUP.1", "SUP.8", "SUP.9", "SUP.10",
            "MAN.3", "MAN.5", "MAN.6",
        ]
        for ep in expected_ids:
            self.assertIn(ep, proc_ids)

        for p in procs:
            self.assertEqual(p["target_capability_level"], 2)
            self.assertTrue(len(p["primary_owner"]) > 0)
            self.assertTrue(len(p["swc_scope"]) >= 1)
            self.assertTrue(len(p["cl2_entry_justification"]) >= 20)

    def test_interview_schedule_and_roles(self):
        schedules = self.payload["interview_schedule_and_roles"]
        self.assertEqual(len(schedules), 6)

        for s in schedules:
            self.assertTrue(len(s["target_processes"]) >= 1)
            self.assertTrue(len(s["session_focus"]) >= 10)
            self.assertTrue(len(s["interviewees"]) >= 1)
            self.assertTrue(len(s["assessor_lead"]) > 0)
            self.assertTrue(s["planned_date"].startswith("2026-10-"))
            self.assertTrue(len(s["evidence_focus"]) >= 1)

    def test_sampling_and_evidence_isolation_rules(self):
        rules = self.payload["sampling_and_aggregation_protocol"]
        self.assertEqual(len(rules), 3)

        rule_ids = [r["rule_id"] for r in rules]
        self.assertEqual(rule_ids, ["SAMP-RULE-01", "SAMP-RULE-02", "SAMP-RULE-03"])

        # Check documentation isolation policy
        iso = self.payload["evidence_baseline_and_isolation_policy"]
        self.assertEqual(iso["execution_origin_mandatory"], "ecu-execution exclusively")
        self.assertIn("Feature 0019", iso["documentation_campaign_constraint"])
        self.assertIn("reusable definitions, schemas, and procedural mechanisms ONLY", iso["documentation_campaign_constraint"])
        self.assertIn("Under NO circumstances may documentation artifacts or synthetic fixtures enter as ECU execution evidence", iso["documentation_campaign_constraint"])

    def test_assessor_independence_and_signoffs(self):
        safe = self.payload["assessor_independence_and_governance_safeguards"]
        self.assertIn("independence", safe["separation_of_duties_rule"])
        self.assertIn("4-eyes", safe["four_eyes_authorization_rule"])

        signoffs = safe["governance_approvals"]
        self.assertIn("jadzia", signoffs["project_sponsor_signature"])
        self.assertIn("odo", signoffs["lead_assessor_signature"])
        self.assertIn("jake", signoffs["qa_manager_signature"])
        self.assertIn("kira", signoffs["architect_signature"])
        self.assertEqual(signoffs["signed_date"], "2026-09-19")

    def test_write_and_digest_stability(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_path = tmp_root / "test-pilot-plan.json"
            md_path = tmp_root / "test-pilot-plan.md"
            epp.write_pilot_assessment_plan(json_path, md_path)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], epp.SCHEMA_PILOT_PLAN)
            self.assertEqual(loaded["governance"]["plan_status"], "FORMALLY_APPROVED_FOR_EXECUTION")

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Automotive ECU Managed Pilot Process Selection & Assessment Plan", md_text)
            self.assertIn("SAMP-RULE-01", md_text)
            self.assertIn("SESS-PILOT-01", md_text)


if __name__ == "__main__":
    unittest.main()
