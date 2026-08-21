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

    def test_detached_head_worktree_at_source_tip_does_not_cause_false_foreign(self):
        # Regression test for the integration-review finding (Seven-Tom,
        # 2026-08-21): `git branch --all --contains <sha>` emits a synthetic
        # "(no branch)" line whenever <sha> is a detached-HEAD checkout in
        # *any* worktree of this repository -- including the reviewer's own
        # isolated worktree, which is exactly how this tool's documented
        # usage (and this repository's branch-workflow) is normally
        # exercised. That placeholder must never be treated as an
        # unrecognized third/foreign branch.
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        tip = _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2 (from 0001-01)\n",
            "revise policy on 0001-01",
        )

        with tempfile.TemporaryDirectory() as extra_worktree_parent:
            worktree_path = Path(extra_worktree_parent) / "detached-review-worktree"
            _git(self.repo, "worktree", "add", "--detach", str(worktree_path), tip)
            try:
                # Sanity: `git branch --all --contains` really does emit the
                # synthetic "(no branch)" artifact the review reported --
                # but only when queried *from within* the detached worktree
                # itself (its own current-HEAD marker line), which is
                # exactly how an independent reviewer's isolated worktree
                # setup invokes this tool.
                raw_from_primary = _git(
                    self.repo, "branch", "--all", "--contains", tip, "--format=%(refname:short)"
                )
                self.assertNotIn("(no branch)", raw_from_primary)
                raw_from_worktree = _git(
                    worktree_path, "branch", "--all", "--contains", tip, "--format=%(refname:short)"
                )
                self.assertIn("(no branch)", raw_from_worktree)

                # The tool must classify identically regardless of which of
                # the two locations it is invoked from.
                report_from_primary = cpp.check_policy_provenance(self.repo, "0001-01", "main")
                report_from_worktree = cpp.check_policy_provenance(
                    worktree_path, "0001-01", "main"
                )
                for report in (report_from_primary, report_from_worktree):
                    self.assertEqual(len(report.findings), 1)
                    finding = report.findings[0]
                    self.assertEqual(finding.sha, tip)
                    self.assertNotIn("(no branch)", finding.containing_branches)
                    self.assertEqual(finding.classification, "source-origin")
                    self.assertFalse(report.has_foreign_branch_policy_commit)
            finally:
                _git(self.repo, "worktree", "remove", "--force", str(worktree_path))

    def test_downstream_review_branch_on_top_of_source_is_not_foreign(self):
        # Second half of the same integration-review finding: even with the
        # "(no branch)" placeholder filtered, a branch created *on top of*
        # source_branch (e.g. a reviewer's audit branch, or a later Task
        # branch chained onto this one -- both routine here per
        # branch-workflow.md) trivially contains every source commit through
        # plain ancestry. That must not be treated as foreign-origin
        # evidence either.
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        tip = _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2 (from 0001-01)\n",
            "revise policy on 0001-01",
        )
        _git(self.repo, "checkout", "-q", "-b", "0001-01-review-someone", "0001-01")
        _commit(self.repo, "review-notes.md", "notes\n", "review notes, no policy change")

        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual(finding.sha, tip)
        self.assertIn("0001-01-review-someone", finding.containing_branches)
        self.assertEqual(finding.classification, "source-origin")
        self.assertFalse(report.has_foreign_branch_policy_commit)

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
