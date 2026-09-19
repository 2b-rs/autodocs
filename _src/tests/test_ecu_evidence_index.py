#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_evidence_index.py -- Test suite for ECU Evidence Index validation and freeze (Task 0025-03)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ecu_evidence_index as eei  # noqa: E402


class TestECUEvidenceValidation(unittest.TestCase):
    def setUp(self):
        self.valid_artifact = {
            "artifact_id": "EVID-SWE4-TEST-001",
            "artifact_name": "Unit Verification Results",
            "path": "docs/pipeline/ecu-swe4-unit-verification-execution-evidence.md",
            "revision": "4e2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a",
            "product_id": eei.ASSESSED_PRODUCT,
            "project_id": eei.ASSESSED_PROJECT,
            "process_id": "SWE.4",
            "process_instance_id": "RUN-SWE4-20260913-001",
            "baseline_id": eei.ASSESSED_BASELINE,
            "owner": "nog (Tester)",
            "origin": "ecu-execution",
            "validity": "frozen",
            "retention": "10_years",
            "confidentiality": "internal",
            "outcome_indicators": [
                {"bp": "SWE.4.BP3", "description": "Verify software units"}
            ],
            "contrary_evidence": [],
            "unresolved_limitations": [],
        }

    def test_valid_artifact_passes(self):
        ok, errors = eei.validate_evidence_artifact(self.valid_artifact)
        self.assertTrue(ok)
        self.assertEqual(len(errors), 0)

    def test_reject_documentation_execution_origin(self):
        art = dict(self.valid_artifact)
        art["origin"] = "documentation-execution"
        ok, errors = eei.validate_evidence_artifact(art)
        self.assertFalse(ok)
        self.assertTrue(any("Non-ECU origin" in e for e in errors))

    def test_reject_process_definition_origin(self):
        art = dict(self.valid_artifact)
        art["origin"] = "process-definition"
        ok, errors = eei.validate_evidence_artifact(art)
        self.assertFalse(ok)
        self.assertTrue(any("Non-ECU origin" in e for e in errors))

    def test_reject_cross_product_substitution(self):
        art = dict(self.valid_artifact)
        art["product_id"] = "other-product-ecu"
        ok, errors = eei.validate_evidence_artifact(art)
        self.assertFalse(ok)
        self.assertTrue(any("Cross-product mismatch" in e for e in errors))

    def test_reject_cross_project_substitution(self):
        art = dict(self.valid_artifact)
        art["project_id"] = "other-project"
        ok, errors = eei.validate_evidence_artifact(art)
        self.assertFalse(ok)
        self.assertTrue(any("Cross-project mismatch" in e for e in errors))

    def test_reject_baseline_mismatch(self):
        art = dict(self.valid_artifact)
        art["baseline_id"] = "virtualized-automotive-ecu:v0.5.0"
        ok, errors = eei.validate_evidence_artifact(art)
        self.assertFalse(ok)
        self.assertTrue(any("Baseline mismatch" in e for e in errors))

    def test_reject_missing_required_fields(self):
        for f in eei.REQUIRED_FIELDS:
            art = dict(self.valid_artifact)
            del art[f]
            ok, errors = eei.validate_evidence_artifact(art)
            self.assertFalse(ok, f"Failed to reject missing field {f}")
            self.assertTrue(any(f"Missing required field: {f}" in e for e in errors))

    def test_reject_empty_outcome_indicators(self):
        art = dict(self.valid_artifact)
        art["outcome_indicators"] = []
        ok, errors = eei.validate_evidence_artifact(art)
        self.assertFalse(ok)
        self.assertTrue(any("outcome_indicators must be a non-empty list" in e for e in errors))

    def test_reject_invalid_confidentiality(self):
        art = dict(self.valid_artifact)
        art["confidentiality"] = "top-secret-unauthorized"
        ok, errors = eei.validate_evidence_artifact(art)
        self.assertFalse(ok)
        self.assertTrue(any("Invalid confidentiality" in e for e in errors))


class TestECUEvidenceIndexAssembly(unittest.TestCase):
    def test_standard_inventory_all_valid(self):
        inventory = eei.get_standard_ecu_evidence_inventory()
        self.assertGreaterEqual(len(inventory), 14)  # At least 14 nucleus processes covered
        for art in inventory:
            ok, errors = eei.validate_evidence_artifact(art.to_dict())
            self.assertTrue(ok, f"Artifact {art.artifact_id} failed: {errors}")

    def test_index_assembly_and_serialization(self):
        payload = eei.assemble_frozen_evidence_index()
        self.assertEqual(payload["schema"], eei.SCHEMA_EVIDENCE_INDEX)
        self.assertEqual(payload["product_id"], eei.ASSESSED_PRODUCT)
        self.assertEqual(payload["project_id"], eei.ASSESSED_PROJECT)
        self.assertEqual(payload["baseline_id"], eei.ASSESSED_BASELINE)
        self.assertEqual(payload["summary"]["status"], "FROZEN_AND_VALIDATED")
        self.assertIn("index_sha256", payload)
        self.assertEqual(len(payload["index_sha256"]), 64)

    def test_write_frozen_index_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            json_path = tmp_root / "test-index.json"
            md_path = tmp_root / "test-index.md"
            eei.write_frozen_index(json_path, md_path)

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            loaded = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], eei.SCHEMA_EVIDENCE_INDEX)
            self.assertGreaterEqual(loaded["summary"]["total_artifacts"], 14)

            md_text = md_path.read_text(encoding="utf-8")
            self.assertIn("Frozen ECU Evidence Index", md_text)
            self.assertIn("SWE.1", md_text)
            self.assertIn("SWE.4", md_text)
            self.assertIn("SPL.2", md_text)


if __name__ == "__main__":
    unittest.main()
