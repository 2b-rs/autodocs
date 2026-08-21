#!/usr/bin/env python3
"""Tests for `_src/tools/legacy_handoff_manifest.py` (Task `0038-16.01`).

Covers the live repository manifest plus fault injection for every property the
Task's Definition of Done depends on: bound review-package digests, zero
unmapped primitives, zero multiply authoritative primitives, a preserved active
singleton, and deterministic byte-stable output.
"""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "_src" / "tools"))

import legacy_handoff_manifest as lhm  # noqa: E402

MANIFEST_REL = lhm.DEFAULT_MANIFEST
TOOLS_REL = lhm.DEFAULT_TOOLS_DOC


def load_manifest() -> dict:
    return json.loads((REPO_ROOT / MANIFEST_REL).read_text(encoding="utf-8"))


def rules(report: dict) -> set:
    return {f["rule"] for f in report["findings"]}


class LiveManifestTests(unittest.TestCase):
    """The committed manifest must validate cleanly, as-is."""

    def setUp(self) -> None:
        self.report = lhm.validate(REPO_ROOT, REPO_ROOT / MANIFEST_REL, REPO_ROOT / TOOLS_REL)

    def test_verdict_is_pass(self) -> None:
        self.assertEqual(self.report["verdict"], "PASS", self.report["findings"])

    def test_zero_unmapped_and_zero_multiply_authoritative(self) -> None:
        self.assertEqual(self.report["stats"]["unmapped"], 0)
        self.assertEqual(self.report["stats"]["multiply_authoritative"], 0)

    def test_every_category_is_represented(self) -> None:
        for category in lhm.CATEGORIES:
            self.assertIn(category, self.report["stats"]["by_category"], category)

    def test_both_queue_consumers_are_named(self) -> None:
        manifest = load_manifest()
        self.assertEqual(
            sorted(c["task"] for c in manifest["consumers"]), ["0037-46.01", "0037-46.02"]
        )

    def test_manifest_bytes_are_canonical_and_deterministic(self) -> None:
        raw = (REPO_ROOT / MANIFEST_REL).read_bytes()
        self.assertEqual(raw, lhm.canonical_bytes(json.loads(raw.decode("utf-8"))))

    def test_review_package_binds_the_0037_37_ref(self) -> None:
        pkg = load_manifest()["review_package"]
        self.assertEqual(pkg["producer_task"], "0037-37")
        self.assertTrue(lhm.COMMIT_RE.match(pkg["producer_ref"]))
        self.assertEqual(len(pkg["contracts"]), 17)

    def test_singleton_is_preserved_and_queue_is_not_activated(self) -> None:
        manifest = load_manifest()
        self.assertEqual(manifest["singleton"]["state"], "active")
        self.assertFalse(manifest["singleton"]["queue_activated"])
        self.assertFalse(manifest["activates_queue"])
        self.assertFalse(manifest["changes_authority"])

    def test_retirement_triggers_exist_for_the_singleton_path(self) -> None:
        ids = {
            p["id"]
            for p in load_manifest()["primitives"]
            if p["disposition"]["kind"] == "retirement-trigger"
        }
        self.assertIn("action.singleton.run-sh", ids)
        self.assertIn("action.singleton.run-loop", ids)

    def test_checker_is_read_only(self) -> None:
        before = {
            p: (REPO_ROOT / p).stat().st_mtime_ns
            for p in (MANIFEST_REL, TOOLS_REL, "_src/tools/legacy_handoff_manifest.py")
        }
        lhm.validate(REPO_ROOT, REPO_ROOT / MANIFEST_REL, REPO_ROOT / TOOLS_REL)
        for path, mtime in before.items():
            self.assertEqual((REPO_ROOT / path).stat().st_mtime_ns, mtime, path)


class FaultInjectionTests(unittest.TestCase):
    """Every guard must actually fire when its property is violated."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="lhm-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.manifest = load_manifest()

    def _run(self, manifest: dict) -> dict:
        """Validate a mutated manifest against the real repository tree."""
        path = self.tmp / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return lhm.validate(REPO_ROOT, path, REPO_ROOT / TOOLS_REL)

    def _first_typed_action_primitive(self, manifest: dict) -> dict:
        for prim in manifest["primitives"]:
            if prim["disposition"]["kind"] == "typed-action":
                return prim
        raise AssertionError("no typed-action primitive")

    def test_missing_disposition_is_unmapped(self) -> None:
        m = copy.deepcopy(self.manifest)
        prim = self._first_typed_action_primitive(m)
        prim["disposition"].pop("typed_actions")
        report = self._run(m)
        self.assertIn("LHM056", rules(report))
        self.assertGreaterEqual(report["stats"]["unmapped"], 1)

    def test_both_dispositions_is_rejected(self) -> None:
        m = copy.deepcopy(self.manifest)
        prim = self._first_typed_action_primitive(m)
        prim["disposition"]["retirement_trigger"] = "both at once"
        self.assertIn("LHM056", rules(self._run(m)))

    def test_duplicate_authority_key_is_multiply_authoritative(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["primitives"][1]["authority_key"] = m["primitives"][0]["authority_key"]
        report = self._run(m)
        self.assertIn("LHM048", rules(report))
        self.assertGreaterEqual(report["stats"]["multiply_authoritative"], 1)

    def test_duplicate_typed_action_is_multiply_authoritative(self) -> None:
        m = copy.deepcopy(self.manifest)
        typed = [p for p in m["primitives"] if p["disposition"]["kind"] == "typed-action"]
        typed[1]["disposition"]["typed_actions"] = list(typed[0]["disposition"]["typed_actions"])
        report = self._run(m)
        self.assertIn("LHM061", rules(report))
        self.assertGreaterEqual(report["stats"]["multiply_authoritative"], 1)

    def test_review_package_digest_drift_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["review_package"]["sha256"] = "0" * 64
        self.assertIn("LHM015", rules(self._run(m)))

    def test_contract_digest_drift_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["review_package"]["contracts"][0]["sha256"] = "1" * 64
        found = rules(self._run(m))
        self.assertTrue({"LHM021", "LHM024"} & found, found)

    def test_dropping_a_bound_contract_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["review_package"]["contracts"].pop()
        self.assertIn("LHM020", rules(self._run(m)))

    def test_unmapped_tools_md_mechanism_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["primitives"] = [
            p for p in m["primitives"] if "_src/tools/runner_transaction.py" not in p["sources"]
        ]
        report = self._run(m)
        self.assertIn("LHM074", rules(report))
        self.assertGreaterEqual(report["stats"]["unmapped"], 1)

    def test_unjustified_exclusion_is_rejected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["coverage"]["excluded"].append({"mechanism": "_src/tools/does_not_exist.py", "reason": "x"})
        self.assertIn("LHM075", rules(self._run(m)))

    def test_dangling_superseded_by_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["primitives"][0]["disposition"]["superseded_by"] = ["ghost.action@v1"]
        self.assertIn("LHM065", rules(self._run(m)))

    def test_unsorted_primitives_break_determinism(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["primitives"] = list(reversed(m["primitives"]))
        self.assertIn("LHM066", rules(self._run(m)))

    def test_claiming_activation_is_rejected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["activates_queue"] = True
        m["singleton"]["queue_activated"] = True
        m["singleton"]["state"] = "retired"
        found = rules(self._run(m))
        self.assertTrue({"LHM031", "LHM032", "LHM033"} <= found, found)

    def test_claiming_authority_change_is_rejected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["changes_authority"] = True
        self.assertIn("LHM034", rules(self._run(m)))

    def test_existing_queue_runtime_root_contradicts_the_manifest(self) -> None:
        """A repository where `.runner/` already exists must fail this manifest."""
        fake_root = self.tmp / "repo"
        (fake_root / ".runner").mkdir(parents=True)
        (fake_root / "docs" / "pipeline").mkdir(parents=True)
        shutil.copy(REPO_ROOT / MANIFEST_REL, fake_root / MANIFEST_REL)
        report = lhm.validate(fake_root, fake_root / MANIFEST_REL, REPO_ROOT / TOOLS_REL)
        self.assertIn("LHM035", rules(report))

    def test_missing_consumer_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["consumers"] = [c for c in m["consumers"] if c["task"] != "0037-46.02"]
        self.assertIn("LHM084", rules(self._run(m)))

    def test_unknown_category_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["primitives"][0]["category"] = "invented"
        self.assertIn("LHM045", rules(self._run(m)))

    def test_missing_test_fixtures_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["primitives"][0]["test_fixtures"] = []
        self.assertIn("LHM051", rules(self._run(m)))

    def test_missing_removal_condition_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["primitives"][0]["disposition"].pop("removal_condition")
        self.assertIn("LHM055", rules(self._run(m)))

    def test_wrong_consumer_for_kind_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        prim = self._first_typed_action_primitive(m)
        prim["disposition"]["consumer"] = "0037-46.02"
        self.assertIn("LHM058", rules(self._run(m)))

    def test_nonexistent_primitive_source_is_detected(self) -> None:
        m = copy.deepcopy(self.manifest)
        m["primitives"][0]["sources"] = ["_src/tools/never_existed.py"]
        self.assertIn("LHM076", rules(self._run(m)))

    def test_malformed_json_fails_closed(self) -> None:
        path = self.tmp / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        report = lhm.validate(REPO_ROOT, path, REPO_ROOT / TOOLS_REL)
        self.assertEqual(report["verdict"], "FAIL")

    def test_missing_manifest_fails_closed(self) -> None:
        report = lhm.validate(REPO_ROOT, self.tmp / "absent.json", REPO_ROOT / TOOLS_REL)
        self.assertEqual(report["verdict"], "FAIL")


class CliTests(unittest.TestCase):
    def test_cli_exit_zero_on_live_manifest(self) -> None:
        self.assertEqual(lhm.main(["--check", "--root", str(REPO_ROOT)]), 0)

    def test_cli_exit_nonzero_on_missing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                lhm.main(["--check", "--root", str(REPO_ROOT), "--manifest", str(Path(tmp) / "x.json")]),
                1,
            )

    def test_tools_doc_inventory_is_non_empty(self) -> None:
        mechanisms = lhm.tools_doc_mechanisms(REPO_ROOT / TOOLS_REL)
        self.assertGreater(len(mechanisms), 10)
        self.assertIn("_src/tools/runner_transaction.py", mechanisms)


if __name__ == "__main__":
    unittest.main()
