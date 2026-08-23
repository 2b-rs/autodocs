#!/usr/bin/env python3
"""Hermetic fixtures for the 0044-14 pre-integration hygiene checker.

Run with:
    python3 -m unittest _src/tools/test_check_integration_hygiene.py -v
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import check_integration_hygiene as hygiene


def _git(repo: Path, *args: str) -> str:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        }
    )
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return proc.stdout.strip()


class IntegrationHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="integration-hygiene-")
        self.root = Path(self.temporary.name) / "repo"
        self.root.mkdir()
        _git(self.root, "init", "-q", "-b", "main")
        (self.root / "README.md").write_text("initial\n", encoding="utf-8")
        _git(self.root, "add", "README.md")
        _git(self.root, "commit", "-q", "-m", "initial")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_clean_registered_worktree_set_passes(self) -> None:
        report = hygiene.check_integration_hygiene(self.root)
        self.assertTrue(report.ok, report.to_dict())
        self.assertEqual(report.root_worktree, str(self.root.resolve()))
        self.assertEqual(report.findings, [])

    def test_foreign_staged_tree_fails_preflight(self) -> None:
        foreign = Path(self.temporary.name) / "foreign"
        _git(self.root, "worktree", "add", "-q", "-b", "0044-foreign", str(foreign))
        (foreign / "foreign.txt").write_text("staged elsewhere\n", encoding="utf-8")
        _git(foreign, "add", "foreign.txt")

        report = hygiene.check_integration_hygiene(self.root)
        findings = {finding.code: finding for finding in report.findings}
        self.assertFalse(report.ok)
        self.assertIn("FOREIGN_STAGED_TREE", findings)
        self.assertEqual(findings["FOREIGN_STAGED_TREE"].worktree, str(foreign.resolve()))

    def test_clean_index_with_tampered_main_worktree_fails_preflight(self) -> None:
        # Reproduce the residual 2026-08-21 root state hermetically: HEAD and
        # index agree, but a tracked working file no longer matches the index.
        (self.root / "README.md").write_text("tampered but unstaged\n", encoding="utf-8")

        report = hygiene.check_integration_hygiene(self.root)
        findings = {finding.code: finding for finding in report.findings}
        root_state = next(state for state in report.worktrees if state.path == str(self.root.resolve()))
        self.assertTrue(root_state.index_equals_head)
        self.assertFalse(root_state.worktree_equals_index)
        self.assertFalse(report.ok)
        self.assertIn("MAIN_WORKTREE_DIRTY", findings)
        self.assertEqual(findings["MAIN_WORKTREE_DIRTY"].worktree, str(self.root.resolve()))
        self.assertNotIn("INDEX_NOT_HEAD", findings)

    def test_unstaged_item_worktree_is_not_a_blocking_finding(self) -> None:
        item = Path(self.temporary.name) / "item"
        _git(self.root, "worktree", "add", "-q", "-b", "0044-item", str(item))
        (item / "README.md").write_text("ordinary unfinished item work\n", encoding="utf-8")

        report = hygiene.check_integration_hygiene(item)
        item_state = next(state for state in report.worktrees if state.path == str(item.resolve()))
        self.assertTrue(item_state.index_equals_head)
        self.assertFalse(item_state.worktree_equals_index)
        self.assertTrue(report.ok, report.to_dict())
        self.assertNotIn("MAIN_WORKTREE_DIRTY", {finding.code for finding in report.findings})

    def test_update_ref_reproduces_stale_worktree_signature(self) -> None:
        # The root worktree stays on main at the initial commit. A low-level
        # ref update advances refs/heads/main without refreshing its index or
        # files, which is the suspected 0044-14 mechanism.
        _git(self.root, "checkout", "-q", "-b", "newer")
        (self.root / "README.md").write_text("newer\n", encoding="utf-8")
        _git(self.root, "add", "README.md")
        _git(self.root, "commit", "-q", "-m", "newer")
        newer_tip = _git(self.root, "rev-parse", "HEAD")
        _git(self.root, "checkout", "-q", "main")
        old_tip = _git(self.root, "rev-parse", "HEAD")

        _git(self.root, "update-ref", "refs/heads/main", newer_tip, old_tip)
        self.assertEqual(_git(self.root, "rev-parse", "HEAD"), newer_tip)
        self.assertEqual(_git(self.root, "diff", "--quiet").strip(), "")

        report = hygiene.check_integration_hygiene(self.root)
        codes = {finding.code for finding in report.findings}
        self.assertIn("INDEX_NOT_HEAD", codes)
        self.assertIn("STALE_AFTER_REF_MOVE", codes)
        stale = next(finding for finding in report.findings if finding.code == "STALE_AFTER_REF_MOVE")
        self.assertIn("refs/heads/main".replace("refs/heads/", ""), stale.detail)
        self.assertIn(old_tip, stale.detail)


if __name__ == "__main__":
    unittest.main()
