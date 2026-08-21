#!/usr/bin/env python3
"""Focused tests for check_policy_provenance.py (0044-01).

Builds small throwaway git repos under a temp dir for each scenario. Never
touches the real repository. Run:

    python3 -m unittest _src/tools/test_check_policy_provenance.py -v
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import check_policy_provenance as cpp


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return proc.stdout


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")


def _commit(repo: Path, path: str, content: str, message: str) -> str:
    full = repo / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD").strip()


class CheckPolicyProvenanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        _init_repo(self.repo)
        _commit(self.repo, "README.md", "root\n", "root")
        _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v1\n",
            "policy v1",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_no_policy_touching_commits_is_clean(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(self.repo, "unrelated.txt", "x\n", "unrelated change")
        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertEqual(report.findings, [])
        self.assertFalse(report.has_foreign_branch_policy_commit)

    def test_policy_commit_authored_on_source_branch_is_not_foreign(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2 (from 0001-01)\n",
            "revise policy on 0001-01",
        )
        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual(finding.classification, "source-origin")
        self.assertFalse(report.has_foreign_branch_policy_commit)

    def test_policy_commit_reachable_from_target_is_pull_in_eligible(self):
        # Target branch changes policy after branch-out; source pulls it in
        # via merge (DEC-0044-001 permitted flow) -> must NOT be flagged.
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(self.repo, "code.txt", "impl\n", "implementation work")
        _git(self.repo, "checkout", "-q", "main")
        _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2 (from main)\n",
            "revise policy on main",
        )
        _git(self.repo, "checkout", "-q", "0001-01")
        _git(self.repo, "merge", "-q", "--no-edit", "main")

        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        classifications = {f.classification for f in report.findings}
        self.assertIn("target-pull-in-eligible", classifications)
        self.assertNotIn("foreign-branch", classifications)
        self.assertFalse(report.has_foreign_branch_policy_commit)

    def test_policy_commit_from_a_third_branch_is_flagged_foreign(self):
        # A policy change originates on an unrelated third branch and gets
        # merged onto the source branch -> DEC-0044-002 violation, must flag.
        _git(self.repo, "checkout", "-q", "-b", "0002-99")
        _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2 (from foreign branch 0002-99)\n",
            "revise policy on foreign branch",
        )
        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(self.repo, "code.txt", "impl\n", "implementation work")
        _git(self.repo, "merge", "-q", "--no-edit", "0002-99")

        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertTrue(report.has_foreign_branch_policy_commit)
        foreign = report.foreign_branch_findings[0]
        self.assertIn("0002-99", foreign.containing_branches)

    def test_cli_exit_code_reflects_verdict(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(self.repo, "unrelated.txt", "x\n", "unrelated change")
        rc = cpp.main(
            [
                "--source-branch",
                "0001-01",
                "--target-branch",
                "main",
                "--repo",
                str(self.repo),
                "--json",
            ]
        )
        self.assertEqual(rc, 0)

    def test_unknown_branch_errors_cleanly(self):
        rc = cpp.main(
            [
                "--source-branch",
                "does-not-exist",
                "--target-branch",
                "main",
                "--repo",
                str(self.repo),
            ]
        )
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
