#!/usr/bin/env python3
"""Tests for branch-aware frontier query (Task 0044-19 / DEC-0044-019).

Verifies AE-3, AE-4, AE-5, three-state prerequisites, and 5-state fail-closed partition.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from frontier_query import (
    BLIND_SPOTS,
    classify_prereq_state,
    parse_todo_items,
    query_frontier,
)


class TestFrontierQuery(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.repo_dir = Path(self.tmp_dir) / "repo"
        self.repo_dir.mkdir()
        self.inbox_dir = Path(self.tmp_dir) / "inbox"
        self.inbox_dir.mkdir()

        # Initialize test git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Agent"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@starfleet.network"], cwd=self.repo_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def _commit(self, msg="commit"):
        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", msg, "--allow-empty"], cwd=self.repo_dir, check=True)

    def test_blind_spots_present(self):
        """Mandatory blind spots must always be present."""
        self.assertEqual(len(BLIND_SPOTS), 5)
        self.assertTrue(any("uncommitted" in s for s in BLIND_SPOTS))
        self.assertTrue(any("0039-01" in s for s in BLIND_SPOTS))

    def test_three_state_prerequisites(self):
        """Test classification of prerequisites: terminal-accepted, terminal-recorded, terminal-contested."""
        accepted = {'marker': 'x', 'has_acceptance': True, 'is_contested': False}
        recorded = {'marker': 'x', 'has_acceptance': False, 'is_contested': False}
        contested = {'marker': 'x', 'has_acceptance': True, 'is_contested': True}
        open_item = {'marker': ' ', 'has_acceptance': False, 'is_contested': False}

        self.assertEqual(classify_prereq_state(accepted), 'terminal-accepted')
        self.assertEqual(classify_prereq_state(recorded), 'terminal-recorded')
        self.assertEqual(classify_prereq_state(contested), 'terminal-contested')
        self.assertEqual(classify_prereq_state(open_item), 'non-terminal')

    def test_ae3_falsification_chain_in_flight(self):
        """AE-3 Falsification case: 0041-05 on chain-0041-benjamin is in-flight, not available."""
        todo_content = """
- [x] **0041-01** Baseline setup. Acceptance: ✓
- [ ] **0041-05** PREREQ: 0041-05:0041-01 Feature integration.
"""
        (self.repo_dir / "TODO.md").write_text(todo_content)
        self._commit("initial main")

        # Create branch chain-0041-benjamin with a claim for 0041-05
        subprocess.run(["git", "checkout", "-b", "chain-0041-benjamin"], cwd=self.repo_dir, check=True, capture_output=True)
        claim_content = """# Claim: Task 0041-05
item: `0041-05`
owner_token: `agent:benjamin:0041-05`
state: in_progress
"""
        (self.repo_dir / "TODO-benjamin-0041-05.md").write_text(claim_content)
        self._commit("0041-05: claim and initial work")

        # Return to main
        subprocess.run(["git", "checkout", "main"], cwd=self.repo_dir, check=True, capture_output=True)

        res = query_frontier(self.repo_dir, self.inbox_dir)
        self.assertIn("0041-05", res.in_flight_items)
        self.assertNotIn("0041-05", res.available_items)
        self.assertEqual(res.items["0041-05"].state, "in-flight")

    def test_ae4_adjacent_cases(self):
        """AE-4 Adjacent cases: (a) merged branch is not in-flight, (b) live award without branch is in-flight."""
        todo_content = """
- [x] **0001-01** Prereq task. Acceptance: ✓
- [ ] **0001-02** PREREQ: 0001-02:0001-01 Merged branch task.
- [ ] **0001-03** PREREQ: 0001-03:0001-01 Live offer task.
"""
        (self.repo_dir / "TODO.md").write_text(todo_content)
        self._commit("initial main")

        # Case (a): branch created, committed, and merged to main -> should be available
        subprocess.run(["git", "checkout", "-b", "feature-0001-02"], cwd=self.repo_dir, check=True, capture_output=True)
        (self.repo_dir / "feature.txt").write_text("done")
        self._commit("0001-02: implement feature")
        subprocess.run(["git", "checkout", "main"], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "merge", "--no-ff", "feature-0001-02", "-m", "merge feature"], cwd=self.repo_dir, check=True, capture_output=True)

        # Case (b): live offer in offers.jsonl for 0001-03
        offers_file = self.inbox_dir / "offers.jsonl"
        offer_entry = {
            "offer_id": "offer-12345",
            "item": "0001-03",
            "event": "awarded",
            "winner": "benjamin"
        }
        offers_file.write_text(json.dumps(offer_entry) + "\n")

        res = query_frontier(self.repo_dir, self.inbox_dir)

        # Case (a) has no unmerged commits on feature-0001-02 relative to main -> available
        self.assertIn("0001-02", res.available_items)
        self.assertEqual(res.items["0001-02"].state, "available")

        # Case (b) has live award in E5 -> in-flight
        self.assertIn("0001-03", res.in_flight_items)
        self.assertEqual(res.items["0001-03"].state, "in-flight")

    def test_ae5_partition_property(self):
        """AE-5 Property test: every item in TODO.md receives exactly one state in the partition."""
        todo_content = """
- [x] **0010-01** Completed item. Acceptance: ✓
- [ ] **0010-02** PREREQ: 0010-02:0010-01 Available open item.
- [ ] **0010-03** PREREQ: 0010-03:0010-02 Blocked on open item.
- [d] **0010-04** PREREQ: 0010-04:0010-01 Held reservation item.
- [p] **0010-05** In-progress item.
"""
        (self.repo_dir / "TODO.md").write_text(todo_content)
        self._commit("commit TODO.md")

        res = query_frontier(self.repo_dir, self.inbox_dir)
        self.assertEqual(res.evaluated_items_count, 5)

        all_categorized = (
            set(res.available_items)
            | set(res.in_flight_items)
            | set(res.blocked_prereq_items)
            | set(res.held_items)
            | set(res.indeterminate_items)
            | set(res.terminal_items)
        )

        self.assertEqual(all_categorized, {"0010-01", "0010-02", "0010-03", "0010-04", "0010-05"})
        # Verify disjointness
        self.assertEqual(
            len(res.available_items)
            + len(res.in_flight_items)
            + len(res.blocked_prereq_items)
            + len(res.held_items)
            + len(res.indeterminate_items)
            + len(res.terminal_items),
            5
        )


if __name__ == "__main__":
    unittest.main()
