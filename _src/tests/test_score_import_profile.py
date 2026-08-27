#!/usr/bin/env python3
"""Hermetic contract tests for the release-pinned S-Core import profile."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
FIXTURES = ROOT / "_src" / "tests" / "fixtures" / "score_import_profile"
PROFILE_PATH = ROOT / "_src" / "spec" / "import-profiles" / "eclipse-score-v0.6.0.json"
BOM_PATH = ROOT / "_src" / "spec" / "campaigns" / "eclipse-score-v0.6.0.json"

sys.path.insert(0, str(TOOLS))
from score_import_profile import (  # noqa: E402
    EXPECTED_CONDITIONS,
    evaluate_candidate,
    load_json,
    validate_profile,
)


def fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ScoreImportProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = load_json(PROFILE_PATH)
        cls.bom = load_json(BOM_PATH)

    def test_profile_validates_against_pinned_bom(self) -> None:
        self.assertEqual([], validate_profile(self.profile, self.bom))
        profile_text = PROFILE_PATH.read_text(encoding="utf-8").lower()
        self.assertNotIn('"main"', profile_text)
        self.assertTrue(self.profile["no_moving_ref_fallback"])

    def test_every_supported_kind_has_a_pinned_source_sample(self) -> None:
        samples = fixture("positive-artifacts.json")["source_examples"]
        self.assertEqual({"module", "component", "design-doc", "process-doc"}, {item["expected"]["kind"] for item in samples})
        self.assertEqual({"score", "process_description"}, {item["candidate"]["repository"] for item in samples})
        for sample in samples:
            result = evaluate_candidate(self.profile, sample["candidate"])
            expected = sample["expected"]
            self.assertEqual("queue", result["decision"], sample["name"])
            self.assertEqual(expected["condition_id"], result["condition_id"], sample["name"])
            self.assertEqual(expected["kind"], result["record"]["kind"], sample["name"])
            self.assertEqual(expected["canonical_id"], result["record"]["canonical_id"], sample["name"])
            self.assertEqual("invalid/to-be-confirmed", result["record"]["status"]["state"])
            self.assertEqual("source-locator", result["record"]["traceability"]["mode"])
            self.assertEqual("discovered", result["work_item"]["lifecycle_state"])
            self.assertEqual("0019-07", result["work_item"]["physical_queue_writer"])
            self.assertTrue(sample["source_excerpt"])

    def test_every_declared_decision_condition_has_a_fixture(self) -> None:
        cases = fixture("decision-cases.json")
        observed = {"QUEUE-INITIAL-CURATION"}
        for case in cases["cases"]:
            candidate = copy.deepcopy(cases["candidates"][case["candidate"]])
            candidate.update(copy.deepcopy(case["patch"]))
            before = copy.deepcopy(candidate)
            result = evaluate_candidate(self.profile, candidate)
            self.assertEqual(before, candidate, case["name"])
            self.assertEqual(case["expected"]["decision"], result["decision"], case["name"])
            self.assertEqual(case["expected"]["condition_id"], result["condition_id"], case["name"])
            observed.add(result["condition_id"])
            if result["decision"] == "reject":
                self.assertNotIn("work_item", result, case["name"])
            else:
                self.assertEqual("discovered", result["work_item"]["lifecycle_state"], case["name"])
                self.assertEqual("0019-07", result["work_item"]["physical_queue_writer"], case["name"])
        self.assertEqual(set(EXPECTED_CONDITIONS), observed)

    def test_moving_reference_in_profile_is_rejected(self) -> None:
        changed = copy.deepcopy(self.profile)
        changed["source_bindings"][0]["release_ref"] = "main"
        codes = {finding["code"] for finding in validate_profile(changed, self.bom)}
        self.assertIn("PROFILE-SOURCE-MOVING-REF", codes)
        self.assertIn("PROFILE-BOM-MISMATCH", codes)

    def test_command_line_check_is_clean(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "score_import_profile.py"),
                str(PROFILE_PATH),
                "--bom",
                str(BOM_PATH),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual({"ok": True, "profile_id": "eclipse-score-v0.6.0"}, json.loads(completed.stdout))


if __name__ == "__main__":
    unittest.main()
