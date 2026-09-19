#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_published_profile.py -- Test suite for ECU Management Decision & Published Profile (Task 0025-09)."""

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
import ecu_published_profile as epp  # noqa: E402
import ecu_readiness_review as err  # noqa: E402
import ecu_reassessment_cycle as erc  # noqa: E402


class TestECUPublishedProfile(unittest.TestCase):
    def setUp(self):
        self.payload = epp.assemble_published_assessment_profile()

    def test_schema_and_metadata(self):
        self.assertEqual(self.payload["schema"], epp.SCHEMA_PUBLISHED_PROFILE)
        self.assertEqual(self.payload["profile_id"], f"ECU-PUBLISHED-PROFILE-{epp.ASSESSED_BASELINE}")
        scope = self.payload["organizational_and_product_scope"]
        self.assertEqual(scope["organization_name"], epp.ASSESSED_ORGANIZATION)
        self.assertEqual(scope["product_id"], epp.ASSESSED_PRODUCT)
        self.assertEqual(scope["project_id"], epp.ASSESSED_PROJECT)
        self.assertEqual(scope["release_instance"], epp.ASSESSED_BASELINE)
        self.assertEqual(scope["commit_reference"], epp.BASELINE_COMMIT)
        
        gov = self.payload["assessment_methodology_and_governance"]
        self.assertEqual(gov["pam_version"], epp.PAM_VERSION)
        self.assertEqual(gov["validity_period"], epp.VALIDITY_PERIOD)
        self.assertIn("published_profile_sha256", self.payload)
        self.assertEqual(len(self.payload["published_profile_sha256"]), 64)

    def test_management_decision_record(self):
        dec = self.payload["management_decision"]
        self.assertEqual(dec["decision_id"], "DEC-0025-PUBLISH-20260919-01")
        self.assertEqual(dec["decision_disposition"], "APPROVED_FOR_PUBLICATION")
        self.assertIn("jadzia", dec["approving_authority"])
        self.assertEqual(dec["decision_date"], "2026-09-19")
        self.assertTrue(len(dec["decision_text"]) >= 50)

    def test_boundary_and_claim_policy_enforcement(self):
        policy = self.payload["boundary_and_claim_policy"]
        self.assertEqual(policy["claim_policy_rule"], "NO_BLANKET_LEVEL1_OR_CL2_ENTRY_CLAIM")
        self.assertTrue(len(policy["claim_statement"]) >= 50)
        self.assertIn("does not constitute an organizational maturity rating", policy["claim_statement"])
        self.assertIn("nor does it assert entry into Automotive SPICE Level 2", policy["claim_statement"])

        ext_procs = policy["external_and_excluded_processes"]
        ext_ids = [p["process_id"] for p in ext_procs]
        self.assertIn("HWE.1-4", ext_ids)
        self.assertIn("ACQ.4", ext_ids)

    def test_published_process_ratings(self):
        ratings = self.payload["published_process_ratings"]
        self.assertEqual(len(ratings), 15)

        for r in ratings:
            self.assertEqual(r["pa11_rating"], "F")
            self.assertEqual(r["process_disposition"], "FULLY_ACHIEVED")
            self.assertIn("ISO/IEC 33020", r["rating_scale"])
            self.assertTrue(r["evidence_count"] >= 1)

    def test_separate_governance_statements(self):
        statements = self.payload["separate_governance_statements"]
        self.assertIn("assessment_disposition_statement", statements)
        self.assertIn("execution_responsibility_statement", statements)

        disp = statements["assessment_disposition_statement"]
        self.assertIn("odo", disp["author"])
        self.assertTrue(len(disp["statement"]) >= 30)

        resp = statements["execution_responsibility_statement"]
        self.assertIn("jadzia", resp["author"])
        self.assertTrue(len(resp["statement"]) >= 30)

    def test_accepted_limitations(self):
        limitations = self.payload["accepted_limitations"]
        self.assertEqual(len(limitations), 3)

        lim_ids = [l["limitation_id"] for l in limitations]
        self.assertEqual(lim_ids, ["LIMIT-0025-01", "LIMIT-0025-02", "LIMIT-0025-03"])

    def test_next_cycle_improvement_plan(self):
        plan = self.payload["next_cycle_improvement_plan"]
        self.assertEqual(len(plan), 3)

        plan_ids = [p["item_id"] for p in plan]
        self.assertEqual(plan_ids, ["PLAN-0025-01", "PLAN-0025-02", "PLAN-0025-03"])

        for p in plan:
            self.assertTrue(len(p["title"]) > 5)
            self.assertTrue(p["target_date"].startswith("2026-"))
            self.assertTrue(len(p["owner"]) > 0)
            self.assertTrue(len(p["description"]) >= 20)

    def test_write_and_digest_stability(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_path = tmp_root / "test-profile.json"
            md_path = tmp_root / "test-profile.md"
            epp.write_published_assessment_profile(json_path, md_path)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], epp.SCHEMA_PUBLISHED_PROFILE)
            self.assertEqual(loaded["management_decision"]["decision_disposition"], "APPROVED_FOR_PUBLICATION")

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Automotive ECU Published Process Capability Assessment Profile", md_text)
            self.assertIn("NO_BLANKET_LEVEL1_OR_CL2_ENTRY_CLAIM", md_text)
            self.assertIn("DEC-0025-PUBLISH-20260919-01", md_text)
            self.assertIn("PLAN-0025-01", md_text)


if __name__ == "__main__":
    unittest.main()
