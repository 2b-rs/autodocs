#!/usr/bin/env python3
"""Focused refusal tests for the migration-manifest validator."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("migration_validator",HERE/"validate_manifest.py"); assert SPEC and SPEC.loader
validator=importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name]=validator; SPEC.loader.exec_module(validator)


class MigrationManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((HERE.parent/"manifest.json").read_text()); cls.inventory=json.loads((HERE/"inventory.json").read_text())

    def result(self,mutation=None):
        manifest=copy.deepcopy(self.manifest); inventory=copy.deepcopy(self.inventory)
        if mutation: mutation(manifest,inventory)
        return validator.validate(manifest,inventory)

    def test_positive_exact_population(self): self.assertTrue(self.result()["valid"])
    def test_duplicate_and_missing_rows_refused(self):
        def mutation(m,i): m["rows"][-1]=copy.deepcopy(m["rows"][0])
        codes=self.result(mutation)["findings"]; self.assertIn("MIGRATION-POPULATION-MISMATCH",codes); self.assertIn("MIGRATION-DUPLICATE-FEATURE",codes)
    def test_unknown_disposition_refused(self): self.assertTrue(any(x.startswith("MIGRATION-DISPOSITION:") for x in self.result(lambda m,i:m["rows"][0].update(disposition="grandfathered"))["findings"]))
    def test_empty_owner_and_trigger_refused(self): self.assertTrue(any(x.startswith("MIGRATION-OWNER-TRIGGER:") for x in self.result(lambda m,i:m["rows"][0].update(owner="",revisit_trigger=""))["findings"]))
    def test_unreachable_branch_refused(self):
        def mutation(m,i): m["rows"][0]["feature_branch"]={"name":"0046","state":"reachable","ref":"f"*40}
        self.assertTrue(any(x.startswith("MIGRATION-BRANCH-UNREACHABLE:") for x in self.result(mutation)["findings"]))
    def test_inventory_drift_refused(self): self.assertTrue(any(x.startswith("MIGRATION-INVENTORY-DRIFT:") for x in self.result(lambda m,i:m["rows"][0]["work_units"].pop())["findings"]))
    def test_digest_mismatch_refused(self): self.assertIn("MIGRATION-DIGEST-MISMATCH",self.result(lambda m,i:m.update(manifest_digest="sha256:"+"0"*64))["findings"])
    def test_migrated_requires_both_plans(self):
        def mutation(m,i): m["rows"][1].update(disposition="migrated",wtp_evidence=[],ip_evidence=[])
        self.assertTrue(any(x.startswith("MIGRATION-HIDDEN-COMPLIANCE:") for x in self.result(mutation)["findings"]))


if __name__=="__main__": unittest.main()
