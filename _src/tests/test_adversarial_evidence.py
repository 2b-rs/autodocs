#!/usr/bin/env python3
"""Fixtures for `check_adversarial_evidence.py` (`DEC-0038-004`, Task `0038-34`).

The Architect scope review for `0038-34` requires, before implementation
completion, "at least one positive fixture and negative fixtures for:
out-of-scope bookkeeping, missing red baseline, always-green negative, fewer
than two neighbors, missing neighbor result, set claim without property
evidence, missing oracle/domain, and inconsistent partial projection."

Each of those nine is a named test below. Every negative fixture is derived
from the positive one by a single mutation, so each test isolates exactly the
condition it names.
"""

from __future__ import annotations

import copy
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "_src" / "tools"))

import check_adversarial_evidence as mod  # noqa: E402


def codes(findings) -> set[str]:
    return {f.code for f in findings}


#: The positive fixture. A set-invariant change with complete conforming evidence.
#: Modelled on the shape `0038-31` should have produced.
CONFORMING = {
    "schema": "completion-evidence@v1",
    "item": "0038-31",
    "change_kinds": ["counting-cardinality", "set-sequence-invariant"],
    "baselines": {"pre_change": "77c4d0aee", "candidate": "5aebcd2a7"},
    "falsification_cases": [
        {
            "name": "index-1/worktree-2 with line collision drops a real finding",
            "derived_from_claim": "the union keeps the largest occurrence count "
            "observed in any single variant",
            "command": "python3 -m unittest _src.tests.test_automation_safety"
            ".IndexWorktreeVariantMergeTests.test_collision_does_not_drop",
            "output": "AssertionError: merged report on dirty tree: "
            "[(6, 'AUTO001')] != [(5, 'AUTO001'), (6, 'AUTO001')]",
            "result_pre_change": "red",
            "result_candidate": "green",
        }
    ],
    "adjacent_cases": [
        {
            "name": "two byte-identical statements in one symbol, clean tree",
            "dimension": "multiplicity within a single variant",
            "expected": "both retained",
            "observed": "both retained",
            "why_adjacent": "same dedupe key path, one variant instead of two",
        },
        {
            "name": "index 2 / worktree 2",
            "dimension": "equal multiplicity across variants",
            "expected": "2, no padding needed",
            "observed": "2",
            "why_adjacent": "the padding branch is skipped rather than exercised",
        },
    ],
    "property_evidence": {
        "invariant": "per code location, merged count equals the max count in any variant",
        "domain": "randomized line placements and multiplicities over two variants",
        "seed": "0xC0FFEE",
        "generative": True,
        "executed_cases": 10000,
        "command": "python3 -m unittest _src.tests.test_automation_safety.PropertyTests",
    },
}


class PositiveFixture(unittest.TestCase):
    def test_conforming_record_yields_no_findings(self):
        self.assertEqual(mod.check_evidence(CONFORMING), [])


class NegativeFixtures(unittest.TestCase):
    """One named negative per condition required by the Architect scope review."""

    def test_out_of_scope_bookkeeping_carries_no_obligation(self):
        """A bookkeeping-only change is excluded and must not be asked for evidence."""
        rec = {
            "schema": "completion-evidence@v1",
            "item": "0038-34",
            "change_kinds": ["bookkeeping-only"],
        }
        self.assertEqual(mod.check_evidence(rec), [])

    def test_unclassified_change_is_a_finding(self):
        """Declaring neither an in-scope class nor an exclusion is not a way out."""
        rec = {"schema": "completion-evidence@v1", "change_kinds": []}
        self.assertIn("AE-1-UNCLASSIFIED", codes(mod.check_evidence(rec)))

    def test_missing_red_baseline(self):
        rec = copy.deepcopy(CONFORMING)
        del rec["falsification_cases"][0]["result_pre_change"]
        found = codes(mod.check_evidence(rec))
        self.assertIn("AE-3-NO-RED-BASELINE", found)
        self.assertIn("AE-3-NO-CONFORMING-CASE", found)

    def test_always_green_negative(self):
        rec = copy.deepcopy(CONFORMING)
        rec["falsification_cases"][0]["result_pre_change"] = "green"
        found = codes(mod.check_evidence(rec))
        self.assertIn("AE-3-ALWAYS-GREEN", found)
        self.assertIn("AE-3-NO-CONFORMING-CASE", found)

    def test_fewer_than_two_neighbors(self):
        rec = copy.deepcopy(CONFORMING)
        rec["adjacent_cases"] = rec["adjacent_cases"][:1]
        self.assertIn("AE-4-TOO-FEW-NEIGHBORS", codes(mod.check_evidence(rec)))

    def test_missing_neighbor_result(self):
        rec = copy.deepcopy(CONFORMING)
        del rec["adjacent_cases"][1]["observed"]
        found = codes(mod.check_evidence(rec))
        self.assertIn("AE-4-INCOMPLETE-CASE", found)
        self.assertIn("AE-4-TOO-FEW-NEIGHBORS", found)

    def test_set_claim_without_property_evidence(self):
        rec = copy.deepcopy(CONFORMING)
        del rec["property_evidence"]
        self.assertIn("AE-5-NO-PROPERTY-EVIDENCE", codes(mod.check_evidence(rec)))

    def test_missing_oracle_and_domain(self):
        rec = copy.deepcopy(CONFORMING)
        del rec["property_evidence"]["invariant"]
        del rec["property_evidence"]["domain"]
        found = codes(mod.check_evidence(rec))
        self.assertIn("AE-5-NO-ORACLE", found)
        self.assertIn("AE-5-NO-DOMAIN", found)

    def test_missing_executed_case_count(self):
        rec = copy.deepcopy(CONFORMING)
        rec["property_evidence"]["executed_cases"] = 0
        self.assertIn("AE-5-NO-CASE-COUNT", codes(mod.check_evidence(rec)))


class NeighborDistinctnessFixtures(unittest.TestCase):
    """AE-4 requires two *distinct* neighbors, not the same one twice."""

    def test_two_neighbors_probing_the_same_dimension(self):
        rec = copy.deepcopy(CONFORMING)
        rec["adjacent_cases"][1]["dimension"] = rec["adjacent_cases"][0]["dimension"]
        self.assertIn("AE-4-NOT-DISTINCT", codes(mod.check_evidence(rec)))

    def test_mocked_changed_path_is_not_conforming(self):
        rec = copy.deepcopy(CONFORMING)
        rec["falsification_cases"][0]["mocked_changed_path"] = True
        self.assertIn("AE-3-MOCK-BYPASS", codes(mod.check_evidence(rec)))


class ProjectionFixtures(unittest.TestCase):
    """AE-8: inconsistent partial projection, and the live repository state."""

    BLOCK = (
        "<!-- BEGIN adversarial-completion-evidence@v1 -->\n"
        "normative text\n"
        "<!-- END adversarial-completion-evidence@v1 -->\n"
    )

    def _repo(self, agents: str, todo: str) -> Path:
        tmp = Path(tempfile.mkdtemp())
        (tmp / "AGENTS.md").write_text(agents, encoding="utf-8")
        (tmp / "TODO.md").write_text(todo, encoding="utf-8")
        return tmp

    def test_inconsistent_partial_projection(self):
        """Present in one operative location only."""
        repo = self._repo(self.BLOCK, "no block here\n")
        found = codes(mod.check_projection(repo))
        self.assertIn("AE-8-PARTIAL-PROJECTION", found)

    def test_divergent_projection(self):
        """Present in both, but not the same normative text."""
        other = self.BLOCK.replace("normative text", "subtly different text")
        repo = self._repo(self.BLOCK, other)
        self.assertIn("AE-8-DIVERGENT-PROJECTION", codes(mod.check_projection(repo)))

    def test_absent_from_both_is_reported_as_inactive(self):
        repo = self._repo("nothing\n", "nothing\n")
        self.assertIn("AE-8-NOT-PROJECTED", codes(mod.check_projection(repo)))

    def test_identical_projection_passes(self):
        repo = self._repo(self.BLOCK, self.BLOCK)
        self.assertEqual(mod.check_projection(repo), [])

    def test_live_repository_projections_are_identical(self):
        """The real AGENTS.md/TODO.md of this candidate must satisfy AE-8."""
        self.assertEqual(mod.check_projection(REPO_ROOT), [])


class CliFixtures(unittest.TestCase):
    def test_projection_mode_exit_zero_on_live_repo(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "_src" / "tools" / "check_adversarial_evidence.py"),
                "--projection",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("PASS", proc.stdout)

    def test_malformed_input_exits_two_and_never_passes(self):
        tmp = Path(tempfile.mkdtemp()) / "bad.json"
        tmp.write_text("{not json", encoding="utf-8")
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "_src" / "tools" / "check_adversarial_evidence.py"),
                "--evidence",
                str(tmp),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout)


class BlockContentFixtures(unittest.TestCase):
    """The projected block must actually carry all eight propositions."""

    def test_all_eight_propositions_present_in_both_files(self):
        for name in ("AGENTS.md", "TODO.md"):
            text = (REPO_ROOT / name).read_text(encoding="utf-8")
            block = mod.BLOCK_RE.findall(text)
            self.assertEqual(len(block), 1, name)
            for n in range(1, 9):
                self.assertIn(f"AE-{n} —", block[0], f"{name} missing AE-{n}")

    def test_block_is_additive_and_names_its_decision_record(self):
        block = mod.BLOCK_RE.findall((REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8"))[0]
        self.assertIn("DEC-0038-004", block)
        self.assertIn("add to", block)
        self.assertTrue(re.search(r"claim-bound", block))


if __name__ == "__main__":
    unittest.main(verbosity=2)
