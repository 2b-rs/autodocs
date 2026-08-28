#!/usr/bin/env python3
"""Hermetic tests for `_src/tools/provision_tmp_worktree.sh` (Tasks 0038-22/0044-17).

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

    def record_item(
        self,
        target: Path,
        item: str,
        *,
        accepted: bool,
        claim_prefix: str,
        extra_claim_item: Optional[str] = None,
    ) -> Path:
        acceptance = " **Acceptance: ✓**" if accepted else ""
        (target / "TODO.md").write_text(
            f"## Feature: {item[:4]} — Fixture\n\n"
            f"- [x] **{item}** Fixture item.{acceptance}\n",
            encoding="utf-8",
        )
        claim = target / f"{claim_prefix}-owner-{item}-request.md"
        claim.write_text(
            f"task_id: {item}\nrequest_id: request\nowner_token: agent:owner:{item}:request\n",
            encoding="utf-8",
        )
        paths = ["TODO.md", claim.name]
        if extra_claim_item:
            extra = target / f"TODO-other-{extra_claim_item}-request.md"
            extra.write_text(
                f"task_id: {extra_claim_item}\nrequest_id: other\n"
                f"owner_token: agent:other:{extra_claim_item}:other\n",
                encoding="utf-8",
            )
            paths.append(extra.name)
        self.git("add", *paths, cwd=target)
        self.git("commit", "-q", "-m", f"record {item}", cwd=target)
        return claim

    def merge_to_main(self, branch: str) -> None:
        self.git("merge", "--no-ff", "-m", f"merge {branch}", branch)


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

    def test_keeps_clean_claimless_worktree_without_terminal_evidence(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-01")
        result = self.repo.run_script(["0100"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(scratch.exists())

    def test_reaps_accepted_clean_main_reachable_worktree(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-02")
        self.repo.record_item(scratch, "0200-02", accepted=True, claim_prefix="DONE")
        self.repo.merge_to_main("0200-02")

        result = self.repo.run_script(["--reap-only", str(self.repo.wt_root)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reaped accepted worktree", result.stderr)
        self.assertFalse(scratch.exists())
        self.assertEqual(
            self.repo.git("rev-parse", "--verify", "refs/heads/0200-02").returncode,
            0,
        )

    def test_historical_prerequisite_claim_does_not_block_terminal_item(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-03")
        self.repo.record_item(
            scratch,
            "0200-03",
            accepted=True,
            claim_prefix="DONE",
            extra_claim_item="0199-01",
        )
        self.repo.merge_to_main("0200-03")

        result = self.repo.run_script(["--reap-only", str(self.repo.wt_root)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(scratch.exists())

    def test_keeps_exact_item_todo_claim(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-04")
        self.repo.record_item(scratch, "0200-04", accepted=True, claim_prefix="TODO")
        self.repo.merge_to_main("0200-04")
        result = self.repo.run_script(["--reap-only", str(self.repo.wt_root)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(scratch.exists())

    def test_keeps_accepted_but_unmerged_worktree(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-05")
        self.repo.record_item(scratch, "0200-05", accepted=True, claim_prefix="DONE")
        result = self.repo.run_script(["--reap-only", str(self.repo.wt_root)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(scratch.exists())

    def test_surfaces_dirty_accepted_worktree_without_deleting(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-06")
        self.repo.record_item(scratch, "0200-06", accepted=True, claim_prefix="DONE")
        self.repo.merge_to_main("0200-06")
        (scratch / "uncommitted.txt").write_text("wip\n", encoding="utf-8")
        result = self.repo.run_script(["--reap-only", str(self.repo.wt_root)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("uncommitted or untracked", result.stderr)
        self.assertTrue(scratch.exists())

    def test_keeps_unaccepted_done_claim(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-07")
        self.repo.record_item(scratch, "0200-07", accepted=False, claim_prefix="DONE")
        self.repo.merge_to_main("0200-07")
        result = self.repo.run_script(["--reap-only", str(self.repo.wt_root)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no unique current Acceptance", result.stderr)
        self.assertTrue(scratch.exists())

    def test_keeps_locked_accepted_worktree(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-08")
        self.repo.record_item(scratch, "0200-08", accepted=True, claim_prefix="DONE")
        self.repo.merge_to_main("0200-08")
        self.repo.git("worktree", "lock", str(scratch))
        result = self.repo.run_script(["--reap-only", str(self.repo.wt_root)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(scratch.exists())

    def test_never_touches_worktrees_outside_configured_root(self) -> None:
        outside = Path(self.repo.temporary.name) / "outside-root"
        self.repo.branch("0200-09", "main")
        self.repo.git("worktree", "add", str(outside), "0200-09")
        self.repo.record_item(outside, "0200-09", accepted=True, claim_prefix="DONE")
        self.repo.merge_to_main("0200-09")

        result = self.repo.run_script(["--reap-only", str(self.repo.wt_root)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(outside.exists())

    def test_never_reaps_the_just_requested_target(self) -> None:
        result = self.repo.run_script(["0100"])
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.repo.wt_root / "0100"
        self.assertTrue(target.exists(), "freshly provisioned target must survive its own reap sweep")

    def test_reap_only_mode_does_not_provision(self) -> None:
        scratch = self.repo.make_extra_worktree("0200-10")
        self.repo.record_item(scratch, "0200-10", accepted=True, claim_prefix="DONE")
        self.repo.merge_to_main("0200-10")
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


class AcceptedLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FixtureRepo()

    def tearDown(self) -> None:
        self.repo.close()

    def test_finalize_renames_only_exact_item_claim_byte_identically(self) -> None:
        target = self.repo.make_extra_worktree("0300-01")
        claim = self.repo.record_item(
            target,
            "0300-01",
            accepted=True,
            claim_prefix="TODO",
            extra_claim_item="0299-01",
        )
        before = claim.read_bytes()
        unrelated = target / "TODO-other-0299-01-request.md"

        result = self.repo.run_script(["--finalize-accepted", "0300-01", str(target)])
        self.assertEqual(result.returncode, 0, result.stderr)
        done = target / "DONE-owner-0300-01-request.md"
        self.assertFalse(claim.exists())
        self.assertEqual(done.read_bytes(), before)
        self.assertTrue(unrelated.exists())
        self.assertIn("R  TODO-owner-0300-01-request.md -> DONE-owner-0300-01-request.md", self.repo.git("status", "--short", cwd=target).stdout)

    def test_finalize_collision_refuses_before_any_rename(self) -> None:
        target = self.repo.make_extra_worktree("0300-02")
        claim = self.repo.record_item(target, "0300-02", accepted=True, claim_prefix="TODO")
        destination = target / "DONE-owner-0300-02-request.md"
        destination.write_text("collision\n", encoding="utf-8")
        result = self.repo.run_script(["--finalize-accepted", "0300-02", str(target)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination", result.stderr)
        self.assertTrue(claim.exists())
        self.assertEqual(destination.read_text(encoding="utf-8"), "collision\n")

    def test_finalize_refuses_without_acceptance(self) -> None:
        target = self.repo.make_extra_worktree("0300-03")
        claim = self.repo.record_item(target, "0300-03", accepted=False, claim_prefix="TODO")
        result = self.repo.run_script(["--finalize-accepted", "0300-03", str(target)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Acceptance", result.stderr)
        self.assertTrue(claim.exists())

    def test_finalize_runs_on_acceptance_branch_distinct_from_item_branch(self) -> None:
        target = self.repo.make_extra_worktree("0300")
        claim = self.repo.record_item(target, "0300-09", accepted=True, claim_prefix="TODO")
        result = self.repo.run_script(["--finalize-accepted", "0300-09", str(target)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(claim.exists())
        self.assertTrue((target / "DONE-owner-0300-09-request.md").exists())

    def test_remove_completed_removes_only_worktree_and_retains_branch(self) -> None:
        target = self.repo.make_extra_worktree("0300-04")
        self.repo.record_item(target, "0300-04", accepted=True, claim_prefix="DONE")
        tip = self.repo.git("rev-parse", "0300-04").stdout.strip()
        result = self.repo.run_script(["--remove-completed", "0300-04", str(target), "0300-04"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.exists())
        self.assertEqual(self.repo.git("rev-parse", "0300-04").stdout.strip(), tip)

    def test_remove_completed_refuses_dirty_worktree(self) -> None:
        target = self.repo.make_extra_worktree("0300-05")
        self.repo.record_item(target, "0300-05", accepted=True, claim_prefix="DONE")
        (target / "dirty.txt").write_text("keep\n", encoding="utf-8")
        result = self.repo.run_script(["--remove-completed", "0300-05", str(target), "0300-05"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uncommitted or untracked", result.stderr)
        self.assertTrue((target / "dirty.txt").exists())

    def test_remove_completed_refuses_active_exact_item_claim(self) -> None:
        target = self.repo.make_extra_worktree("0300-06")
        self.repo.record_item(target, "0300-06", accepted=True, claim_prefix="TODO")
        result = self.repo.run_script(["--remove-completed", "0300-06", str(target), "0300-06"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("still carries TODO", result.stderr)
        self.assertTrue(target.exists())

    def test_remove_completed_refuses_locked_worktree(self) -> None:
        target = self.repo.make_extra_worktree("0300-07")
        self.repo.record_item(target, "0300-07", accepted=True, claim_prefix="DONE")
        self.repo.git("worktree", "lock", str(target))
        result = self.repo.run_script(["--remove-completed", "0300-07", str(target), "0300-07"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("locked", result.stderr)
        self.assertTrue(target.exists())

    def test_remove_completed_refuses_live_process_cwd(self) -> None:
        target = self.repo.make_extra_worktree("0300-08")
        self.repo.record_item(target, "0300-08", accepted=True, claim_prefix="DONE")
        sleeper = subprocess.Popen(["sleep", "30"], cwd=target)
        self.addCleanup(lambda: sleeper.poll() is None and sleeper.kill())
        try:
            result = self.repo.run_script(["--remove-completed", "0300-08", str(target), "0300-08"])
        finally:
            sleeper.kill()
            sleeper.wait()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("live process", result.stderr)
        self.assertTrue(target.exists())


if __name__ == "__main__":
    unittest.main()
