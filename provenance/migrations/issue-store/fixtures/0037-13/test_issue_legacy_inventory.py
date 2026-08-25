#!/usr/bin/env python3
"""Frozen-fixture tests for the 0037-13 legacy inventory baseline."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parents[1] / "tools" / "issue_legacy_inventory.py"
sys.path.insert(0, str(TOOL.parent))
import issue_legacy_inventory as inv  # noqa: E402


class InventoryFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        blobs = inv.load_tree_blobs(HERE)
        cls.inventory = inv.inventory_from_blobs(
            blobs,
            source_commit=None,
            run_id="fixture-0037-13",
            produced_at="2026-08-25T08:26:00Z",
            tool_path="provenance/migrations/issue-store/tools/issue_legacy_inventory.py",
            tool_digest=inv._sha256_bytes(TOOL.read_bytes()),
        )

    def test_covers_required_surfaces(self) -> None:
        paths = {a["path"] for a in self.inventory["source_artifacts"]}
        self.assertIn("TODO.md", paths)
        self.assertIn("DONE.md", paths)
        self.assertTrue(any(p.startswith("TODO-") for p in paths))
        ids = {i["id"] for i in self.inventory["items"]}
        self.assertIn("0037", ids)
        self.assertIn("0037-13", ids)
        self.assertIn("0021", ids)

    def test_feature_0021_archived_not_accepted(self) -> None:
        feat = next(i for i in self.inventory["items"] if i["id"] == "0021")
        self.assertEqual(feat["mapping_class"], inv.AUTHORITY_REQUIRED)
        self.assertEqual(feat["archive"], "archived-not-accepted")
        disp = self.inventory["dispositions"][0]
        self.assertEqual(disp["item"], "0021")
        self.assertEqual(disp["disposition"], "archived-not-accepted")
        self.assertFalse(disp["evidence_credit"])

    def test_no_credit_local_placeholders(self) -> None:
        rules = {f["rule"] for f in self.inventory["findings"]}
        self.assertIn("INV-REF-NO-EVIDENCE-CREDIT", rules)
        for item in self.inventory["items"]:
            if item.get("id") in {"0021-06", "0021-07", "0021-08"}:
                self.assertEqual(item["mapping_class"], inv.AUTHORITY_REQUIRED)
                self.assertIn("no-evidence-credit", item["notes"])
        self.assertGreaterEqual(self.inventory["counts"]["no_credit_local_refs"], 3)

    def test_anomaly_findings(self) -> None:
        rules = {f["rule"] for f in self.inventory["findings"]}
        self.assertIn("INV-ID-DUPLICATE", rules)
        self.assertIn("INV-TASK-HEADER-MALFORMED", rules)
        self.assertIn("INV-FEATURE-HEADER-MALFORMED", rules)
        self.assertIn("INV-MARKER-UNDEFINED", rules)
        self.assertIn("INV-REF-PENDING", rules)

    def test_lossless_0037_06(self) -> None:
        item = next(i for i in self.inventory["items"] if i["id"] == "0037-06")
        self.assertEqual(item["mapping_class"], inv.LOSSLESS)
        self.assertEqual(item["refs"][0]["kind"], "full_commit")

    def test_finding_ids_stable(self) -> None:
        first = [f["id"] for f in self.inventory["findings"]]
        blobs = inv.load_tree_blobs(HERE)
        second = inv.inventory_from_blobs(
            blobs,
            source_commit=None,
            run_id="fixture-0037-13",
            produced_at="2026-08-25T08:26:00Z",
            tool_path="provenance/migrations/issue-store/tools/issue_legacy_inventory.py",
            tool_digest=inv._sha256_bytes(TOOL.read_bytes()),
        )
        self.assertEqual(first, [f["id"] for f in second["findings"]])

    def test_write_outputs_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            inv.write_outputs(out, self.inventory)
            a = (out / "legacy-inventory.json").read_bytes()
            inv.write_outputs(out, self.inventory)
            b = (out / "legacy-inventory.json").read_bytes()
            self.assertEqual(a, b)
            md = (out / "legacy-inventory.md").read_text(encoding="utf-8")
            self.assertIn("archived-not-accepted", md)
            self.assertIn("local-20260815-0021-06", md)
            aset = json.loads((out / "source-artifact-set.json").read_text(encoding="utf-8"))
            self.assertEqual(aset["producer_run"], "fixture-0037-13")

    def test_claim_parsed(self) -> None:
        claim = self.inventory["claims"][0]
        self.assertEqual(claim["item"], "0037-13")
        self.assertTrue(claim["owner_token"].startswith("agent:gabriel-saru"))


if __name__ == "__main__":
    unittest.main()
