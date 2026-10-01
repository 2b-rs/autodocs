#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_readiness_review.py -- Test suite for ECU Independent Readiness Review & Limitations Record (Task 0025-08)."""

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
import ecu_readiness_review as err  # noqa: E402
import ecu_reassessment_cycle as erc  # noqa: E402


class TestECUReadinessReview(unittest.TestCase):
    def setUp(self):
        self.payload = err.assemble_readiness_review_record()

    def test_schema_and_governance_metadata(self):
        self.assertEqual(self.payload["schema"], err.SCHEMA_READINESS)
        self.assertEqual(self.payload["readiness_review_id"], f"ECU-READINESS-{err.ASSESSED_BASELINE}")
        gov = self.payload["governance"]
        self.assertEqual(gov["product_id"], err.ASSESSED_PRODUCT)
        self.assertEqual(gov["project_id"], err.ASSESSED_PROJECT)
        self.assertEqual(gov["baseline_id"], err.ASSESSED_BASELINE)
        self.assertEqual(gov["revised_baseline_id"], err.REVISED_BASELINE)
        self.assertEqual(gov["baseline_commit"], err.BASELINE_COMMIT)
        self.assertEqual(gov["reassessment_commit"], err.REASSESSMENT_COMMIT)
        self.assertEqual(gov["overall_readiness_status"], "READY_FOR_EXTERNAL_AUDIT")
        self.assertIn("readiness_review_sha256", self.payload)
        self.assertEqual(len(self.payload["readiness_review_sha256"]), 64)

    def test_review_summary_metrics(self):
        summary = self.payload["review_summary"]
        self.assertEqual(summary["total_dimensions_evaluated"], 7)
        self.assertEqual(summary["conformant_dimensions_count"], 7)
        self.assertEqual(summary["acceptable_with_limitations_count"], 0)
        self.assertEqual(summary["non_conformant_dimensions_count"], 0)
        self.assertEqual(summary["total_accepted_limitations"], 3)
        self.assertEqual(summary["readiness_disposition"], "LEVEL_1_READINESS_CONFIRMED_RECOMMEND_EXTERNAL_AUDIT")

    def test_all_seven_dimensions_evaluated_rigorously(self):
        dims = self.payload["evaluated_dimensions"]
        self.assertEqual(len(dims), 7)

        dim_ids = [d["dimension_id"] for d in dims]
        expected_ids = ["DIM-01", "DIM-02", "DIM-03", "DIM-04", "DIM-05", "DIM-06", "DIM-07"]
        self.assertEqual(dim_ids, expected_ids)

        expected_names = [
            "Scope & Process Selection",
            "Responsibility Allocations & 4-Eyes Governance",
            "Assessor Competence & Qualifications",
            "Evidence Validity & Baseline Authenticity",
            "Outcome Judgments & Rating Rationale",
            "Unresolved Risks & Triage Dispositions",
            "Claim Wording & Capability Boundary",
        ]
        actual_names = [d["dimension_name"] for d in dims]
        self.assertEqual(actual_names, expected_names)

        for d in dims:
            self.assertEqual(d["verdict"], "CONFORMANT")
            self.assertTrue(len(d["evaluated_criteria"]) >= 2)
            self.assertTrue(len(d["review_observations"]) >= 30)
            self.assertTrue(len(d["reviewer_notes"]) >= 10)

    def test_accepted_limitations_register(self):
        limitations = self.payload["accepted_limitations_register"]
        self.assertEqual(len(limitations), 3)

        lim_ids = [l["limitation_id"] for l in limitations]
        self.assertEqual(lim_ids, ["LIMIT-0025-01", "LIMIT-0025-02", "LIMIT-0025-03"])

        for l in limitations:
            self.assertTrue(len(l["title"]) > 5)
            self.assertTrue(len(l["scope_boundary"]) > 0)
            self.assertTrue(len(l["rationale"]) >= 30)
            self.assertTrue(len(l["accepted_by"]) > 0)
            self.assertTrue(len(l["mitigation_or_next_step"]) >= 10)

    def test_independent_recommendation_and_signoffs(self):
        verdict = self.payload["independent_recommendation_and_verdict"]
        self.assertEqual(verdict["readiness_verdict"], "APPROVED_FOR_FORMAL_ASSESSMENT")
        self.assertTrue(len(verdict["recommendation_statement"]) >= 50)
        self.assertIn("RECOMMENDATION: The project is fully prepared and recommended", verdict["recommendation_statement"])

        signoffs = verdict["review_signoffs"]
        self.assertIn("kira", signoffs["independent_reviewer_signature"])
        self.assertIn("odo", signoffs["lead_assessor_acknowledgment"])
        self.assertIn("jake", signoffs["qa_manager_acknowledgment"])
        self.assertIn("jadzia", signoffs["project_sponsor_acknowledgment"])
        self.assertEqual(signoffs["signed_date"], "2026-09-19")

    def test_write_and_digest_stability(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_path = tmp_root / "test-readiness.json"
            md_path = tmp_root / "test-readiness.md"
            err.write_readiness_review_record(json_path, md_path)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], err.SCHEMA_READINESS)
            self.assertEqual(loaded["review_summary"]["readiness_disposition"], "LEVEL_1_READINESS_CONFIRMED_RECOMMEND_EXTERNAL_AUDIT")

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Automotive ECU Independent Assessment Readiness Review & Limitations Record", md_text)
            self.assertIn("DIM-01: Scope & Process Selection", md_text)
            self.assertIn("LIMIT-0025-01", md_text)
            self.assertIn("APPROVED_FOR_FORMAL_ASSESSMENT", md_text)


if __name__ == "__main__":
    unittest.main()
