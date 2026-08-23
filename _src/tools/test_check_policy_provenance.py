#!/usr/bin/env python3
"""Focused tests for check_policy_provenance.py (0044-01).

Builds small throwaway git repos under a temp dir for each scenario. Never
touches the real repository. Run:

    python3 -m unittest _src/tools/test_check_policy_provenance.py -v

Test organization: this file went through two rounds of independent-review
findings against branch-containment-based classification (a detached-HEAD
worktree's synthetic "(no branch)" line; a downstream review/Task branch
built on top of source; an old branch sitting at an earlier point on
source's own mainline). The tool was rewritten to classify purely from the
topology of the commit itself relative to source_commit's first-parent
history (see the module docstring's relationship table), which makes branch
*names* irrelevant to the decision. `TopologyMatrixTest` below enumerates,
as explicit individual tests, every branch-tip-vs-source_commit relationship
this tool could plausibly encounter, to confirm none of them leak into the
classification any more -- not just the three specific shapes that were
previously reported broken one at a time.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import check_policy_provenance as cpp


def _git(repo: Path, *args: str, env: dict | None = None) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
        env={**os.environ, **(env or {})},
    )
    return proc.stdout


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")


def _commit(repo: Path, path: str, content: str, message: str, env: dict | None = None) -> str:
    full = repo / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)
    _git(repo, "add", path)
    _git(repo, "commit", "-q", "-m", message, env=env)
    return _git(repo, "rev-parse", "HEAD").strip()


class CheckPolicyProvenanceTest(unittest.TestCase):
    """Baseline behavioral tests: the classification contract itself."""

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

    def test_required_policy_origin_trailer_is_reported(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2\n",
            "revise policy\n\nPolicy-Origin-Branch: 0001-01",
        )
        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        finding = report.findings[0]
        self.assertEqual(finding.policy_origin_branch, "0001-01")
        self.assertFalse(finding.missing_policy_origin_trailer)
        self.assertFalse(report.has_missing_policy_origin_trailer)

    def test_missing_required_policy_origin_trailer_is_a_finding_and_fails_cli(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(self.repo, "docs/pipeline/branch-workflow.md", "policy v2\n", "revise policy")
        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertTrue(report.has_missing_policy_origin_trailer)
        self.assertTrue(report.findings[0].missing_policy_origin_trailer)
        self.assertEqual(
            cpp.main(["--source-branch", "0001-01", "--target-branch", "main", "--repo", str(self.repo)]),
            1,
        )

    def test_pre_decision_policy_commit_does_not_require_a_trailer(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2\n",
            "legacy policy",
            env={"GIT_AUTHOR_DATE": "2026-08-20T12:00:00+00:00", "GIT_COMMITTER_DATE": "2026-08-20T12:00:00+00:00"},
        )
        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertFalse(report.has_missing_policy_origin_trailer)
        self.assertFalse(report.findings[0].missing_policy_origin_trailer)

    def test_malformed_policy_origin_trailer_is_a_finding(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2\n",
            "revise policy\n\nPolicy-Origin-Branch: bad..branch",
        )
        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertTrue(report.has_missing_policy_origin_trailer)
        self.assertIsNone(report.findings[0].policy_origin_branch)

    def test_duplicate_policy_origin_trailers_are_a_finding(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2\n",
            "revise policy\n\nPolicy-Origin-Branch: 0001-01\nPolicy-Origin-Branch: main",
        )
        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertTrue(report.has_missing_policy_origin_trailer)
        self.assertIsNone(report.findings[0].policy_origin_branch)

    def test_empty_policy_origin_trailer_is_a_finding(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2\n",
            "revise policy\n\nPolicy-Origin-Branch:",
        )
        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertTrue(report.has_missing_policy_origin_trailer)
        self.assertIsNone(report.findings[0].policy_origin_branch)

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

    def test_foreign_finding_survives_deletion_of_the_foreign_branch(self):
        # Robustness win of the topology-based rewrite: the old
        # branch-containment approach could only name a foreign branch that
        # still exists. Classification must not depend on that -- the
        # merge-commit topology is the evidence, independent of whether any
        # ref still names the foreign commit.
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
        _git(self.repo, "branch", "-D", "0002-99")

        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertTrue(report.has_foreign_branch_policy_commit)
        foreign = report.foreign_branch_findings[0]
        self.assertNotIn("0002-99", foreign.containing_branches)

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


class TopologyMatrixTest(unittest.TestCase):
    """Enumerated matrix: every branch-tip-vs-source_commit relationship a
    surviving/visible branch/worktree can have, confirmed to have NO effect
    on classification of a mainline source-origin commit. This is the
    adversarial pass requested after the third branch-containment false
    positive (2026-08-21): rather than adding one more targeted regression
    for the specific case reported, enumerate the whole relationship space
    once so the same class of defect can't resurface a fourth time.

    Fixture shape shared by every test in this class: `source_branch`
    ("0001-01") has exactly one policy-touching commit, `policy_tip`,
    authored directly on it (a mainline commit by construction). Each test
    then adds one additional branch/worktree in a specific topological
    relationship to `source_commit` and asserts `policy_tip` is still
    classified `source-origin` and nothing is flagged foreign.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "repo"
        _init_repo(self.repo)
        _commit(self.repo, "README.md", "root\n", "root")
        _commit(self.repo, "docs/pipeline/branch-workflow.md", "policy v1\n", "policy v1")
        _git(self.repo, "checkout", "-q", "-b", "0001-01")
        self.policy_tip = _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v2 (from 0001-01)\n",
            "revise policy on 0001-01",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _assert_still_clean_source_origin(self):
        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertEqual(len(report.findings), 1, report.to_dict())
        finding = report.findings[0]
        self.assertEqual(finding.sha, self.policy_tip)
        self.assertEqual(finding.classification, "source-origin")
        self.assertFalse(report.has_foreign_branch_policy_commit)

    # -- 1. Equal: another ref points at exactly source_commit. ------------
    def test_relationship_equal(self):
        _git(self.repo, "branch", "another-name-same-tip", "0001-01")
        self._assert_still_clean_source_origin()

    # -- 2. Downstream/descendant: a branch built ON TOP of source. --------
    def test_relationship_downstream_descendant(self):
        _git(self.repo, "checkout", "-q", "-b", "0001-01-review-someone", "0001-01")
        _commit(self.repo, "review-notes.md", "notes\n", "review notes, no policy change")
        self._assert_still_clean_source_origin()

    # -- 3. Upstream/ancestor via first-parent: an old branch sitting at an
    #       earlier point on source's OWN mainline (Tom's second-verdict
    #       repro shape: "stale-wip-branch" at an ancestor commit). --------
    def test_relationship_upstream_ancestor_via_first_parent(self):
        # Tom's second-verdict repro shape: an old, retained branch sitting
        # at an earlier commit already on source's OWN first-parent line
        # (setUp's "policy v1" root commit, one before policy_tip) -- not a
        # commit added by this test, so policy_tip stays the actual tip.
        before_policy = _git(self.repo, "rev-parse", "0001-01~1").strip()
        _git(self.repo, "branch", "stale-wip-branch", before_policy)
        self.assertNotEqual(before_policy, self.policy_tip)
        self._assert_still_clean_source_origin()

    # -- 4. Upstream/ancestor via merge: genuinely foreign -- must STILL be
    #       flagged (the one relationship that IS real evidence). ---------
    def test_relationship_upstream_ancestor_via_merge_is_still_foreign(self):
        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "checkout", "-q", "-b", "0002-99")
        foreign_tip = _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v3 (from foreign branch 0002-99)\n",
            "revise policy on foreign branch",
        )
        _git(self.repo, "checkout", "-q", "0001-01")
        # policy_tip (from setUp) and foreign_tip both touch
        # branch-workflow.md, so a plain merge would conflict on content
        # that is irrelevant to this test (we only care that foreign_tip's
        # *commit* is reachable via the merge, not what the merged text
        # says) -- resolve deterministically in favor of the incoming side.
        _git(self.repo, "merge", "-q", "--no-edit", "-X", "theirs", "0002-99")

        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        shas = {f.sha: f.classification for f in report.findings}
        self.assertEqual(shas.get(self.policy_tip), "source-origin")
        self.assertEqual(shas.get(foreign_tip), "foreign-branch")
        self.assertTrue(report.has_foreign_branch_policy_commit)

    # -- 5. Genuinely disjoint: an orphan branch sharing no history at all,
    #       and not containing policy_tip either. Must simply not appear
    #       and must not affect classification. -----------------------
    def test_relationship_disjoint_orphan_branch(self):
        _git(self.repo, "checkout", "-q", "--orphan", "unrelated-orphan")
        _git(self.repo, "reset", "-q", "--hard")
        _commit(self.repo, "island.txt", "island\n", "unrelated orphan history")
        _git(self.repo, "checkout", "-q", "0001-01")

        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        self.assertEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual(finding.classification, "source-origin")
        self.assertNotIn("unrelated-orphan", finding.containing_branches)

    # -- 6. Detached HEAD in another worktree at exactly source_commit. ----
    def test_relationship_detached_head_worktree_at_source_tip(self):
        with tempfile.TemporaryDirectory() as extra:
            worktree_path = Path(extra) / "detached-wt"
            _git(self.repo, "worktree", "add", "--detach", str(worktree_path), self.policy_tip)
            try:
                # Confirm the historically-problematic artifact is really
                # present from the worktree's own vantage point.
                raw = _git(
                    worktree_path,
                    "branch",
                    "--all",
                    "--contains",
                    self.policy_tip,
                    "--format=%(refname:short)",
                )
                self.assertIn("(no branch)", raw)

                report_primary = cpp.check_policy_provenance(self.repo, "0001-01", "main")
                report_worktree = cpp.check_policy_provenance(worktree_path, "0001-01", "main")
                for report in (report_primary, report_worktree):
                    self.assertEqual(len(report.findings), 1)
                    finding = report.findings[0]
                    self.assertEqual(finding.classification, "source-origin")
                    self.assertNotIn("(no branch)", finding.containing_branches)
                    self.assertFalse(report.has_foreign_branch_policy_commit)
            finally:
                _git(self.repo, "worktree", "remove", "--force", str(worktree_path))

    # -- 7. All relationships present simultaneously -- combined sanity. ---
    def test_relationship_matrix_combined_does_not_misclassify(self):
        before_policy = _git(self.repo, "rev-parse", "0001-01~1").strip()
        _git(self.repo, "branch", "stale-wip-branch", before_policy)  # (3) upstream/first-parent
        _git(self.repo, "branch", "same-tip-branch", "0001-01")  # (1) equal
        _git(self.repo, "checkout", "-q", "-b", "0001-01-review-someone", "0001-01")
        _commit(self.repo, "review-notes.md", "notes\n", "review notes")  # (2) downstream
        _git(self.repo, "checkout", "-q", "0001-01")

        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "checkout", "-q", "-b", "0002-99")
        foreign_tip = _commit(
            self.repo,
            "docs/pipeline/branch-workflow.md",
            "policy v3 (from foreign branch 0002-99)\n",
            "revise policy on foreign branch",
        )  # (4) upstream/via-merge, added next
        _git(self.repo, "checkout", "-q", "0001-01")
        _git(self.repo, "merge", "-q", "--no-edit", "-X", "theirs", "0002-99")

        report = cpp.check_policy_provenance(self.repo, "0001-01", "main")
        shas = {f.sha: f.classification for f in report.findings}
        # The mainline policy commit stays source-origin regardless of the
        # five benign relationships (equal/downstream/upstream-first-parent)
        # now coexisting with it.
        self.assertEqual(shas.get(self.policy_tip), "source-origin")
        # foreign_tip (authored on 0002-99, merged in) is flagged. The merge
        # commit that carried it in may legitimately also be flagged (its
        # own diff-vs-first-parent also shows non-source, non-target policy
        # content, via `-X theirs`) -- both are correct evidence of the same
        # foreign-origin event, not a double-count bug. What must NOT happen
        # is the mainline policy_tip being swept into that set.
        self.assertIn(foreign_tip, {sha for sha, c in shas.items() if c == "foreign-branch"})
        self.assertNotIn(self.policy_tip, {sha for sha, c in shas.items() if c == "foreign-branch"})


if __name__ == "__main__":
    unittest.main()
