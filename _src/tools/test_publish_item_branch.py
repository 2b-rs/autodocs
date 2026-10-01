"""Hermetic tests for direct, item-scoped branch publication.

Every remote is a disposable local repository.  No network URL, credential,
protected ref, canonical repository, or shared root is mutated by this suite.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
PUBLISHER = TOOLS / "publish_item_branch.py"
sys.path.insert(0, str(TOOLS))

import publish_item_branch as publisher  # noqa: E402


ITEM = "0041-04"


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


class ItemBranchPublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="publish-item-branch-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.canonical = self.tmp / "canonical"
        self.worker = self.tmp / "worker"
        self._init_repo(self.canonical, "main")
        (self.canonical / "payload.txt").write_text("base\n", encoding="utf-8")
        self._commit(self.canonical, "base")
        git(self.canonical, "branch", ITEM)
        git(self.tmp, "clone", "--quiet", "--branch", ITEM, str(self.canonical), str(self.worker))
        self._identity(self.worker)
        self.expected_old = self.rev(self.canonical, ITEM)
        (self.worker / "payload.txt").write_text("candidate\n", encoding="utf-8")
        self._commit(self.worker, "candidate")
        self.source_oid = self.rev(self.worker, ITEM)

    def _identity(self, repo: Path) -> None:
        git(repo, "config", "user.name", "Test Worker")
        git(repo, "config", "user.email", "worker@example.invalid")

    def _init_repo(self, repo: Path, branch: str) -> None:
        repo.mkdir(parents=True)
        git(repo, "init", "--quiet", "-b", branch)
        self._identity(repo)

    def _commit(self, repo: Path, message: str) -> None:
        git(repo, "add", "--all")
        git(repo, "commit", "--quiet", "-m", message)

    def rev(self, repo: Path, ref: str) -> str:
        return git(repo, "rev-parse", ref).stdout.strip()

    def canonical_snapshot(self) -> tuple[str, str, str]:
        return (
            self.rev(self.canonical, "HEAD"),
            git(self.canonical, "symbolic-ref", "--short", "HEAD").stdout.strip(),
            git(self.canonical, "status", "--porcelain=v1", "--untracked-files=all").stdout,
        )

    def command(self, **overrides: object) -> list[str]:
        values = {
            "repo": str(self.worker),
            "item": ITEM,
            "source": ITEM,
            "target": ITEM,
            "remote": "origin",
            "expected_old": self.expected_old,
        }
        values.update(overrides)
        command = [sys.executable, str(PUBLISHER)]
        for key in ("repo", "item", "source", "target", "remote", "expected_old"):
            value = values[key]
            if value is not None:
                command.extend(["--" + key.replace("_", "-"), str(value)])
        if values.get("dry_run"):
            command.append("--dry-run")
        return command

    def run_tool(self, **overrides: object) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        result = subprocess.run(
            self.command(**overrides),
            cwd=str(self.tmp),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        try:
            outcome = json.loads(result.stdout)
        except json.JSONDecodeError as exc:  # pragma: no cover - diagnostic path
            self.fail(f"publisher did not emit one JSON outcome: {exc}\nstdout={result.stdout!r}\nstderr={result.stderr!r}")
        return result, outcome

    def assert_refused(self, expected_code: str, **overrides: object) -> dict[str, object]:
        result, outcome = self.run_tool(**overrides)
        self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["status"], "refused")
        self.assertEqual(outcome["code"], expected_code)
        self.assertFalse(outcome["push_attempted"])
        return outcome

    def test_success_is_cas_bound_non_force_and_preserves_canonical_worktree(self) -> None:
        before = self.canonical_snapshot()
        result, outcome = self.run_tool()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertTrue(outcome["ok"])
        self.assertEqual(outcome["status"], "published")
        self.assertEqual(self.rev(self.canonical, ITEM), self.source_oid)
        self.assertEqual(before, self.canonical_snapshot())
        self.assertTrue(outcome["source_worktree_preserved"])
        self.assertNotIn(str(self.canonical), result.stdout)

    def test_dry_run_performs_every_guard_without_mutating_remote(self) -> None:
        result, outcome = self.run_tool(dry_run=True)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(outcome["status"], "dry_run")
        self.assertFalse(outcome["push_attempted"])
        self.assertEqual(self.rev(self.canonical, ITEM), self.expected_old)

    def test_protected_and_noncanonical_targets_are_refused(self) -> None:
        self.assert_refused("PUB-TARGET-PROTECTED", target="main")
        self.assert_refused("PUB-TARGET-MISMATCH", target="0041-05")
        self.assert_refused("PUB-TARGET-NONCANONICAL", target="refs/heads/0041-04")

    def test_missing_or_mismatched_assignment_is_refused(self) -> None:
        result, outcome = self.run_tool(item=None)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outcome["code"], "PUB-ARGUMENT")
        self.assert_refused("PUB-ITEM-INVALID", item="not-an-item")
        self.assert_refused("PUB-SOURCE-MISMATCH", source="candidate")

    def test_checked_out_branch_must_match_explicit_source(self) -> None:
        git(self.worker, "branch", "candidate", ITEM)
        git(self.worker, "switch", "candidate")
        self.assert_refused("PUB-CHECKOUT-MISMATCH", source=ITEM)

    def test_dirty_tracked_or_untracked_state_is_refused(self) -> None:
        (self.worker / "payload.txt").write_text("dirty\n", encoding="utf-8")
        self.assert_refused("PUB-WORKTREE-DIRTY")
        git(self.worker, "restore", "--", "payload.txt")
        (self.worker / "untracked.txt").write_text("untracked\n", encoding="utf-8")
        self.assert_refused("PUB-WORKTREE-DIRTY")

    def test_missing_or_ambiguous_remote_is_refused(self) -> None:
        self.assert_refused("PUB-REMOTE-MISSING", remote="missing")
        second = self.tmp / "second.git"
        git(self.tmp, "init", "--quiet", "--bare", str(second))
        git(self.worker, "remote", "set-url", "--add", "--push", "origin", str(self.canonical))
        git(self.worker, "remote", "set-url", "--add", "--push", "origin", str(second))
        self.assert_refused("PUB-REMOTE-AMBIGUOUS")

    def test_remote_must_be_a_name_not_a_url_or_option(self) -> None:
        self.assert_refused("PUB-REMOTE-INVALID", remote=str(self.canonical))
        result, outcome = self.run_tool(remote="--upload-pack=bad")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outcome["code"], "PUB-ARGUMENT")

    def test_expected_old_must_be_full_object_id(self) -> None:
        self.assert_refused("PUB-EXPECTED-INVALID", expected_old=self.expected_old[:12])
        self.assert_refused("PUB-EXPECTED-INVALID", expected_old="f" * 40)

    def advance_remote(self, message: str = "racer") -> str:
        attacker = self.tmp / ("attacker-" + message)
        git(self.tmp, "clone", "--quiet", "--branch", ITEM, str(self.canonical), str(attacker))
        self._identity(attacker)
        (attacker / "race.txt").write_text(message + "\n", encoding="utf-8")
        self._commit(attacker, message)
        git(attacker, "push", "--quiet", "origin", f"{ITEM}:{ITEM}")
        return self.rev(self.canonical, ITEM)

    def test_stale_expected_old_is_refused_before_push(self) -> None:
        observed = self.advance_remote()
        outcome = self.assert_refused("PUB-EXPECTED-STALE")
        self.assertEqual(outcome["observed_old"], observed)
        self.assertEqual(self.rev(self.canonical, ITEM), observed)

    def test_non_fast_forward_source_is_refused_before_push(self) -> None:
        git(self.worker, "switch", "--orphan", "replacement")
        for path in self.worker.iterdir():
            if path.name != ".git" and path.is_file():
                path.unlink()
        (self.worker / "replacement.txt").write_text("replacement\n", encoding="utf-8")
        self._commit(self.worker, "replacement")
        git(self.worker, "branch", "-M", ITEM)
        self.assert_refused("PUB-NON-FAST-FORWARD")
        self.assertEqual(self.rev(self.canonical, ITEM), self.expected_old)

    def test_cas_race_is_rejected_and_reports_observed_remote(self) -> None:
        config = publisher.Config(
            repo=self.worker,
            item=ITEM,
            source=ITEM,
            target=ITEM,
            remote="origin",
            expected_old=self.expected_old,
            dry_run=False,
        )
        raced_oid: list[str] = []

        def race() -> None:
            raced_oid.append(self.advance_remote("cas-race"))

        outcome = publisher.publish(config, before_push=race)
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["code"], "PUB-CAS-LOST")
        self.assertTrue(outcome["push_attempted"])
        self.assertEqual(outcome["observed_after"], raced_oid[0])
        self.assertEqual(self.rev(self.canonical, ITEM), raced_oid[0])

    def test_local_state_race_is_refused_before_push(self) -> None:
        config = publisher.Config(
            repo=self.worker,
            item=ITEM,
            source=ITEM,
            target=ITEM,
            remote="origin",
            expected_old=self.expected_old,
            dry_run=False,
        )

        def dirty_after_preflight() -> None:
            (self.worker / "payload.txt").write_text("raced locally\n", encoding="utf-8")

        outcome = publisher.publish(config, before_push=dirty_after_preflight)
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["code"], "PUB-LOCAL-RACE")
        self.assertFalse(outcome["push_attempted"])
        self.assertEqual(self.rev(self.canonical, ITEM), self.expected_old)

    def test_interruption_before_push_is_recoverable_and_retry_succeeds(self) -> None:
        config = publisher.Config(
            repo=self.worker,
            item=ITEM,
            source=ITEM,
            target=ITEM,
            remote="origin",
            expected_old=self.expected_old,
            dry_run=False,
        )

        def interrupt() -> None:
            raise publisher.PublicationInterrupted("test interruption")

        interrupted = publisher.publish(config, before_push=interrupt)
        self.assertFalse(interrupted["ok"])
        self.assertEqual(interrupted["status"], "interrupted")
        self.assertFalse(interrupted["push_attempted"])
        self.assertEqual(self.rev(self.canonical, ITEM), self.expected_old)

        retry, outcome = self.run_tool()
        self.assertEqual(retry.returncode, 0, msg=retry.stdout + retry.stderr)
        self.assertEqual(outcome["status"], "published")

    def test_retry_after_success_is_idempotent_even_with_original_expected_old(self) -> None:
        first, first_outcome = self.run_tool()
        self.assertEqual(first.returncode, 0, msg=first.stdout + first.stderr)
        self.assertEqual(first_outcome["status"], "published")
        second, second_outcome = self.run_tool()
        self.assertEqual(second.returncode, 0, msg=second.stdout + second.stderr)
        self.assertEqual(second_outcome["status"], "already_published")
        self.assertFalse(second_outcome["push_attempted"])

    def test_absent_target_uses_zero_oid_lease(self) -> None:
        git(self.canonical, "update-ref", "-d", f"refs/heads/{ITEM}")
        zeros = "0" * 40
        result, outcome = self.run_tool(expected_old=zeros)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(outcome["status"], "published")
        self.assertEqual(self.rev(self.canonical, ITEM), self.source_oid)

    def test_push_failure_reports_safe_retry_when_remote_is_unchanged(self) -> None:
        hook = self.canonical / ".git" / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        result, outcome = self.run_tool()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outcome["code"], "PUB-PUSH-FAILED")
        self.assertEqual(outcome["recovery"]["action"], "retry_same_command")
        self.assertEqual(self.rev(self.canonical, ITEM), self.expected_old)


if __name__ == "__main__":
    unittest.main()
