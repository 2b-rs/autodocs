#!/usr/bin/env python3
"""Focused refusal tests for the migration-manifest validator."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from unittest import mock
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("migration_validator",HERE/"validate_manifest.py"); assert SPEC and SPEC.loader
validator=importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name]=validator; SPEC.loader.exec_module(validator)


class MigrationManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((HERE.parent/"manifest.json").read_text()); cls.inventory=json.loads((HERE/"inventory.json").read_text()); cls.branch_snapshot=json.loads((HERE/"branch-ref-map.json").read_text())

    def result(self,mutation=None):
        manifest=copy.deepcopy(self.manifest); inventory=copy.deepcopy(self.inventory); snapshot=copy.deepcopy(self.branch_snapshot)
        if mutation: mutation(manifest,inventory)
        return validator.validate(manifest,inventory,snapshot)

    def test_positive_exact_population(self): self.assertTrue(self.result()["valid"])
    def test_duplicate_and_missing_rows_refused(self):
        def mutation(m,i): m["rows"][-1]=copy.deepcopy(m["rows"][0])
        codes=self.result(mutation)["findings"]; self.assertIn("MIGRATION-POPULATION-MISMATCH",codes); self.assertIn("MIGRATION-DUPLICATE-FEATURE",codes)
    def test_unknown_disposition_refused(self): self.assertTrue(any(x.startswith("MIGRATION-DISPOSITION:") for x in self.result(lambda m,i:m["rows"][0].update(disposition="grandfathered"))["findings"]))
    def test_empty_owner_and_trigger_refused(self): self.assertTrue(any(x.startswith("MIGRATION-OWNER-TRIGGER:") for x in self.result(lambda m,i:m["rows"][0].update(owner="",revisit_trigger=""))["findings"]))
    def test_unreachable_branch_refused(self):
        def mutation(m,i): m["rows"][0]["feature_branch"]={"name":"0046","state":"reachable","ref":"f"*40}
        self.assertTrue(any(x.startswith("MIGRATION-BRANCH-UNREACHABLE:") for x in self.result(mutation)["findings"]))
    def test_substituted_reachable_branch_refused(self):
        def mutation(m,i): m["rows"][0]["feature_branch"]["ref"]=m["baseline_ref"]
        self.assertTrue(any(x.startswith("MIGRATION-BRANCH-BINDING:") for x in self.result(mutation)["findings"]))
    def test_missing_or_mismatched_row_baseline_refused(self):
        for value in (None,"0"*40):
            with self.subTest(value=value): self.assertTrue(any(x.startswith("MIGRATION-ROW-BASELINE:") for x in self.result(lambda m,i,v=value:m["rows"][0].update(baseline_ref=v))["findings"]))
    def test_invalid_branch_name_and_state_refused(self):
        for change in ({"name":"wrong"},{"state":"grandfathered"}):
            with self.subTest(change=change): self.assertTrue(any(x.startswith("MIGRATION-BRANCH-IDENTITY:") for x in self.result(lambda m,i,c=change:m["rows"][0]["feature_branch"].update(c))["findings"]))
    def test_blank_evidence_path_or_ref_refused(self):
        for key in ("path","ref"):
            with self.subTest(key=key): self.assertTrue(any(x.startswith("MIGRATION-EVIDENCE-BINDING:") for x in self.result(lambda m,i,k=key:m["rows"][0]["wtp_evidence"][0].update({k:""}))["findings"]))
    def test_inventory_never_reads_ambient_branch_refs(self):
        build_spec=importlib.util.spec_from_file_location("migration_builder",HERE/"build_manifest.py"); assert build_spec and build_spec.loader
        builder=importlib.util.module_from_spec(build_spec); sys.modules[build_spec.name]=builder; build_spec.loader.exec_module(builder)
        snapshot=json.loads((HERE/"branch-ref-map.json").read_text()); todo=builder.subprocess.check_output(["git","-C",str(builder.ROOT),"show",f"{self.manifest['baseline_ref']}:TODO.md"])
        with mock.patch.object(builder.subprocess,"check_output",return_value=todo), mock.patch.object(builder.subprocess,"run",side_effect=AssertionError("ambient branch lookup")):
            _,rows=builder.inventory(self.manifest["baseline_ref"],snapshot)
        self.assertEqual([x["feature_branch"] for x in rows],[snapshot["branches"][x["feature_id"]] for x in rows])
    def test_branch_snapshot_tampering_refused(self):
        snapshot=copy.deepcopy(self.branch_snapshot); snapshot["branches"]["0046"]["ref"]=self.manifest["baseline_ref"]
        findings=validator.validate(copy.deepcopy(self.manifest),copy.deepcopy(self.inventory),snapshot)["findings"]
        self.assertIn("MIGRATION-BRANCH-SNAPSHOT-DIGEST",findings)
        self.assertTrue(any(x.startswith("MIGRATION-BRANCH-SNAPSHOT-BINDING:") for x in findings))
    def test_inventory_drift_refused(self): self.assertTrue(any(x.startswith("MIGRATION-INVENTORY-DRIFT:") for x in self.result(lambda m,i:m["rows"][0]["work_units"].pop())["findings"]))
    def test_digest_mismatch_refused(self): self.assertIn("MIGRATION-DIGEST-MISMATCH",self.result(lambda m,i:m.update(manifest_digest="sha256:"+"0"*64))["findings"])
    def test_migrated_requires_both_plans(self):
        def mutation(m,i): m["rows"][1].update(disposition="migrated",wtp_evidence=[],ip_evidence=[])
        self.assertTrue(any(x.startswith("MIGRATION-HIDDEN-COMPLIANCE:") for x in self.result(mutation)["findings"]))


if __name__=="__main__": unittest.main()
