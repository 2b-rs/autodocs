import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "_src"
sys.path[:0] = [str(SRC / "tools"), str(SRC)]

from task_acceptance_policy import expand_batch, validate_feature_acceptance

FIXTURE = ROOT / "_src/tests/fixtures/task_acceptance_policy/cases.json"
AUTHORITY_PATHS = [
    "TODO.md", "AGENTS.md", "SANDBOX.md", "PRIVILEGED.md", "DONE.md",
    "docs/pipeline/task-acceptance.md", "docs/pipeline/branch-workflow.md",
    "docs/pipeline/process-roles.md",
]


class TaskAcceptancePolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.docs = {path: (ROOT / path).read_text(encoding="utf-8") for path in AUTHORITY_PATHS}

    def test_graph_cases(self):
        for case in self.fixture["cases"]:
            with self.subTest(case=case["name"]):
                if case["expected_error"]:
                    with self.assertRaisesRegex(ValueError, re.escape(case["expected_error"])):
                        expand_batch(case["tasks"], case["assigned"], case["accepted"])
                else:
                    self.assertEqual(case["expected_batch"], expand_batch(case["tasks"], case["assigned"], case["accepted"]))

    def test_required_scenario_inventory(self):
        graph_names = {case["name"] for case in self.fixture["cases"]}
        semantic_names = {case["name"] for case in self.fixture["semantic_cases"]}
        self.assertTrue({"linear-unflagged-predecessors", "accepted-boundary", "branching-deterministic", "unassigned-predecessor-checkpoint", "explicit-predecessor-checkpoint-batch", "wontfix-predecessor", "missing-endpoint", "cycle"} <= graph_names)
        self.assertTrue({"blocking-finding", "unauthorized-review", "later-defect-successor", "missing-feature-edge", "historical-invalidation", "duplicate-acceptance", "feature-closure"} <= semantic_names)

    def test_feature_acceptance_validation(self):
        tasks = {
            "0039-01": {"prereq": []},
            "0039-02": {"prereq": ["0039-01"]},
            "0039-03": {"prereq": ["0039-02"]},
            "0039-04": {"prereq": ["0039-03"]},
            "0039-05": {"prereq": ["0039-04"]},
        }
        self.assertTrue(validate_feature_acceptance(tasks, "0039-05"))
        # Missing edge
        tasks_orphan = dict(tasks)
        tasks_orphan["0039-99"] = {"prereq": []}
        self.assertFalse(validate_feature_acceptance(tasks_orphan, "0039-05"))

    def test_canonical_policy_is_create_once_and_successor_based(self):
        policy = self.docs["docs/pipeline/task-acceptance.md"]
        for phrase in [
            "Task acceptance means that the exact reviewed work-product baseline satisfies the Task contract",
            "The attribute requires a privileged integration review",
            "prerequisite-closed Task-Acceptance batch",
            "Acceptance is orthogonal to the legacy checkbox marker",
        ]:
            self.assertIn(phrase, policy)


if __name__ == "__main__":
    unittest.main()
