#!/usr/bin/env python3
"""Hermetic tests for `_src/tools/provision_tmp_worktree.sh` (Task 0038-22).

Builds a throwaway "canonical repo" under a temp directory and drives the
shell script against it via `AUTODOCS_DEVEL`/`AUTODOCS_WORKTREES_ROOT` env
overrides, so nothing here ever touches the real repository or its live
`.worktrees/` directory.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "_src" / "tools" / "provision_tmp_worktree.sh"


class FixtureRepo:
    """A minimal bare-bones git repo used as the fake canonical `devel` repo."""

    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="provision-tmp-worktree-test-")
        self.root = Path(self.temporary.name) / "devel"
        self.root.mkdir()
        self.wt_root = Path(self.temporary.name) / "worktrees"
        self._init_repo()

    def close(self) -> None:
        self.temporary.cleanup()

    def git(
        self,
        *args: str,
        cwd: Optional[Path] = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["GIT_EDITOR"] = "true"
        env.setdefault("GIT_AUTHOR_NAME", "Test")
        env.setdefault("GIT_AUTHOR_EMAIL", "test@example.invalid")
        env.setdefault("GIT_COMMITTER_NAME", "Test")
        env.setdefault("GIT_COMMITTER_EMAIL", "test@example.invalid")
        return subprocess.run(
            ["git", "-C", str(cwd or self.root), *args],
            check=check,
            capture_output=True,
            text=True,
            env=env,
        )

    def _init_repo(self) -> None:
        self.git("init", "-q", "-b", "main")
        (self.root / "README.md").write_text("root\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "initial")

    def branch(self, name: str, base: str = "main") -> None:
        self.git("branch", name, base)

    def run_script(
        self,
        args: List[str],
        env_overrides: Optional[Dict[str, str]] = None,
        check: bool = False,
    ) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["AUTODOCS_DEVEL"] = str(self.root)
        env["AUTODOCS_WORKTREES_ROOT"] = str(self.wt_root)
        env.setdefault("GIT_AUTHOR_NAME", "Test")
        env.setdefault("GIT_AUTHOR_EMAIL", "test@example.invalid")
        env.setdefault("GIT_COMMITTER_NAME", "Test")
        env.setdefault("GIT_COMMITTER_EMAIL", "test@example.invalid")
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            env=env,
            check=check,
        )

    def make_extra_worktree(self, branch: str, base: str = "main") -> Path:
        """Create a worktree directly with `git worktree add`, bypassing the
        script under test — used to seed "pre-existing scratch worktree"
        fixtures for the reap-sweep tests."""
        self.branch(branch, base)
        target = self.wt_root / branch
        target.parent.mkdir(parents=True, exist_ok=True)
        self.git("worktree", "add", str(target), branch)
        return target


class ProvisionOneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FixtureRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def test_syntax_is_valid(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_invalid_item_id(self) -> None:
        result = self.repo.run_script(["not-an-item"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid item branch", result.stderr)

    def test_rejects_missing_args(self) -> None:
        result = self.repo.run_script([])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)

    def test_fresh_provision_creates_feature_branch_off_main(self) -> None:
        result = self.repo.run_script(["0100"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.repo.wt_root / "0100"
        self.assertTrue((target / ".git").exists())
        branch = self.repo.git("rev-parse", "--abbrev-ref", "HEAD", cwd=target).stdout.strip()
        self.assertEqual(branch, "0100")

    def test_fresh_provision_task_branch_off_feature_branch(self) -> None:
        self.repo.branch("0100", "main")
        (self.repo.root / "feature-marker.txt").write_text("x\n", encoding="utf-8")
        self.repo.git("checkout", "0100")
        self.repo.git("add", "feature-marker.txt")
        self.repo.git("commit", "-q", "-m", "feature work")
        self.repo.git("checkout", "main")

        result = self.repo.run_script(["0100-01"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.repo.wt_root / "0100-01"
        self.assertTrue((target / "feature-marker.txt").exists())
        merge_base = self.repo.git(
            "merge-base", "0100-01", "0100", cwd=self.repo.root
        ).stdout.strip()
        tip_of_feature = self.repo.git(
            "rev-parse", "0100", cwd=self.repo.root
        ).stdout.strip()
        self.assertEqual(merge_base, tip_of_feature)

    def test_fresh_provision_falls_back_to_main_when_parent_missing(self) -> None:
        # No '0100' branch exists yet; '0100-02' must fall back to 'main'.
        result = self.repo.run_script(["0100-02"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("falling back to 'main'", result.stderr)

    def test_custom_worktree_path_is_honored(self) -> None:
        custom = Path(self.repo.temporary.name) / "custom-location"
        result = self.repo.run_script(
            ["0100", str(custom)], env_overrides={"AUTODOCS_NO_REAP": "1"}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((custom / ".git").exists())

    def test_idempotent_reheal_restores_only_reaped_tracked_files(self) -> None:
        first = self.repo.run_script(["0100"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertEqual(first.returncode, 0, first.stderr)
        target = self.repo.wt_root / "0100"

        # Commit a tracked file, then simulate an external reap deleting it
        # from disk without going through Git (e.g. a nightly /tmp sweep).
        tracked = target / "tracked.txt"
        tracked.write_text("committed content\n", encoding="utf-8")
        self.repo.git("add", "tracked.txt", cwd=target)
        self.repo.git("commit", "-q", "-m", "add tracked file", cwd=target)
        tracked.unlink()

        # Surviving uncommitted work that must NOT be clobbered by re-heal.
        untracked = target / "untracked-survivor.txt"
        untracked.write_text("must survive\n", encoding="utf-8")
        modified = target / "README.md"
        modified.write_text("locally modified, uncommitted\n", encoding="utf-8")

        second = self.repo.run_script(["0100"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertEqual(second.returncode, 0, second.stderr)

        self.assertTrue(tracked.exists(), "reaped tracked file was not restored")
        self.assertEqual(tracked.read_text(encoding="utf-8"), "committed content\n")
        self.assertTrue(untracked.exists(), "surviving untracked file was clobbered")
        self.assertEqual(untracked.read_text(encoding="utf-8"), "must survive\n")
        self.assertEqual(
            modified.read_text(encoding="utf-8"),
            "locally modified, uncommitted\n",
            "surviving uncommitted edit was clobbered",
        )

    def test_directory_gone_is_rebuilt_from_registration(self) -> None:
        first = self.repo.run_script(["0100"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertEqual(first.returncode, 0, first.stderr)
        target = self.repo.wt_root / "0100"
        shutil.rmtree(target)

        second = self.repo.run_script(["0100"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue((target / ".git").exists())

    def test_refuses_to_rebuild_unexpected_branch_with_uncommitted_content(self) -> None:
        self.repo.branch("0101", "main")
        target = self.repo.wt_root / "0100"
        target.parent.mkdir(parents=True, exist_ok=True)
        self.repo.git("worktree", "add", str(target), "0101")
        (target / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")

        result = self.repo.run_script(["0100"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uncommitted content", result.stderr)
        # Must not have been deleted.
        self.assertTrue((target / "dirty.txt").exists())

    def test_refuses_to_collide_same_branch_two_targets(self) -> None:
        first = self.repo.run_script(["0100"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertEqual(first.returncode, 0, first.stderr)

        other_target = Path(self.repo.temporary.name) / "other-location"
        second = self.repo.run_script(
            ["0100", str(other_target)], env_overrides={"AUTODOCS_NO_REAP": "1"}
        )
        self.assertNotEqual(second.returncode, 0)


class ReapSweepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FixtureRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def test_reaps_clean_claimless_scratch_worktree(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-01")
        self.assertTrue(scratch.exists())

        result = self.repo.run_script(["0100"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reaped orphaned scratch worktree", result.stderr)
        self.assertFalse(scratch.exists())
        listing = self.repo.git("worktree", "list").stdout
        self.assertNotIn("0200-01", listing)

    def test_surfaces_dirty_claimless_scratch_worktree_without_deleting(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-02")
        (scratch / "uncommitted.txt").write_text("wip\n", encoding="utf-8")

        result = self.repo.run_script(["0100"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SURFACE", result.stderr)
        self.assertIn(str(scratch), result.stderr)
        self.assertTrue(scratch.exists(), "a worktree with uncommitted content must never be deleted")
        self.assertTrue((scratch / "uncommitted.txt").exists())

    def test_never_reaps_worktree_carrying_a_claim_file(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-03")
        claim = scratch / "TODO-someone-0200-03-req1.md"
        claim.write_text("# claim\n", encoding="utf-8")
        self.repo.git("add", "TODO-someone-0200-03-req1.md", cwd=scratch)
        self.repo.git("commit", "-q", "-m", "claim", cwd=scratch)
        # Fully clean from Git's perspective, but must still be protected.
        self.assertTrue(self.repo.git("status", "--porcelain", cwd=scratch).stdout.strip() == "")

        result = self.repo.run_script(["0100"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(scratch.exists())
        self.assertTrue(claim.exists())

    def test_never_touches_worktrees_outside_configured_root(self) -> None:
        outside = Path(self.repo.temporary.name) / "outside-root"
        self.repo.branch("0200-04", "main")
        self.repo.git("worktree", "add", str(outside), "0200-04")

        result = self.repo.run_script(["0100"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(outside.exists())

    def test_never_reaps_the_just_requested_target(self) -> None:
        result = self.repo.run_script(["0100"])
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.repo.wt_root / "0100"
        self.assertTrue(target.exists(), "freshly provisioned target must survive its own reap sweep")

    def test_reap_only_mode_does_not_provision(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-05")
        result = self.repo.run_script(["--reap-only", str(self.repo.wt_root)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(scratch.exists())
        self.assertFalse((self.repo.wt_root / "0100").exists())

    def test_concurrent_different_items_do_not_collide(self) -> None:
        first = self.repo.run_script(["0100"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        second = self.repo.run_script(["0101"], env_overrides={"AUTODOCS_NO_REAP": "1"})
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertTrue((self.repo.wt_root / "0100").exists())
        self.assertTrue((self.repo.wt_root / "0101").exists())
        branch_a = self.repo.git(
            "rev-parse", "--abbrev-ref", "HEAD", cwd=self.repo.wt_root / "0100"
        ).stdout.strip()
        branch_b = self.repo.git(
            "rev-parse", "--abbrev-ref", "HEAD", cwd=self.repo.wt_root / "0101"
        ).stdout.strip()
        self.assertEqual(branch_a, "0100")
        self.assertEqual(branch_b, "0101")


if __name__ == "__main__":
    unittest.main()
