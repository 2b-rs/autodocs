#!/usr/bin/env python3
"""Hermetic local-Git tests for publish_worker_clone.sh."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any, final


SCRIPT = Path(__file__).with_name("publish_worker_clone.sh")
ITEM = "0041-04"


@final
class PublishWorkerCloneTests(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.temporary: Any = None
        self.root = Path()
        self.seed = Path()
        self.canonical = Path()
        self.worker = Path()

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="publish-worker-clone-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.seed = self.root / "seed"
        self.canonical = self.root / "canonical.git"
        self.worker = self.root / "worker"

        self.git("init", "-b", "main", str(self.seed), cwd=self.root)
        self.git("config", "user.name", "Publish Worker Test", cwd=self.seed)
        self.git("config", "user.email", "publish-worker@example.invalid", cwd=self.seed)
        (self.seed / "base.txt").write_text("base\n", encoding="utf-8")
        self.git("add", "base.txt", cwd=self.seed)
        self.git("commit", "-m", "base", cwd=self.seed)
        self.git("branch", "0041", cwd=self.seed)
        self.git("branch", ITEM, cwd=self.seed)
        self.git("clone", "--bare", str(self.seed), str(self.canonical), cwd=self.root)
        self.git("clone", "--branch", ITEM, str(self.canonical), str(self.worker), cwd=self.root)
        self.git("config", "user.name", "Publish Worker Test", cwd=self.worker)
        self.git("config", "user.email", "publish-worker@example.invalid", cwd=self.worker)

    def git(
        self, *args: str, cwd: Path, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "--no-pager", *args],
            cwd=str(cwd),
            env={**os.environ, "GIT_EDITOR": "true"},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    def publish(
        self,
        item: str = ITEM,
        clone: Path | None = None,
        target: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = ["bash", str(SCRIPT), item, str(clone or self.worker)]
        if target is not None:
            command.append(target)
        return subprocess.run(
            command,
            cwd=str(self.root),
            env={**os.environ, "AUTODOCS_DEVEL": str(self.canonical)},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def commit_worker(self, name: str = "worker.txt", content: str = "worker\n") -> str:
        (self.worker / name).write_text(content, encoding="utf-8")
        self.git("add", name, cwd=self.worker)
        self.git("commit", "-m", f"add {name}", cwd=self.worker)
        return self.git("rev-parse", "HEAD", cwd=self.worker).stdout.strip()

    def assert_refused(self, result: subprocess.CompletedProcess[str], text: str) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("refusing:", result.stderr)
        self.assertIn(text, result.stderr)

    def test_positive_normal_push_to_matching_item_branch(self) -> None:
        worker_head = self.commit_worker()

        result = self.publish()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"published '{ITEM}'", result.stdout)
        canonical_head = self.git(
            "rev-parse", f"refs/heads/{ITEM}", cwd=self.canonical
        ).stdout.strip()
        self.assertEqual(canonical_head, worker_head)

    def test_refuses_mismatched_target_branch(self) -> None:
        result = self.publish(target="0041-05")
        self.assert_refused(result, "does not match assigned item ID")

    def test_refuses_mismatched_source_branch(self) -> None:
        self.git("switch", "-c", "0041-05", cwd=self.worker)
        result = self.publish()
        self.assert_refused(result, "source branch '0041-05' does not match")

    def test_refuses_protected_targets(self) -> None:
        for target in ("main", "0041"):
            with self.subTest(target=target):
                result = self.publish(target=target)
                self.assert_refused(result, "protected ref")

    def test_refuses_non_fast_forward_publication(self) -> None:
        other = self.root / "other"
        self.git("clone", "--branch", ITEM, str(self.canonical), str(other), cwd=self.root)
        self.git("config", "user.name", "Publish Worker Test", cwd=other)
        self.git("config", "user.email", "publish-worker@example.invalid", cwd=other)
        (other / "remote.txt").write_text("remote\n", encoding="utf-8")
        self.git("add", "remote.txt", cwd=other)
        self.git("commit", "-m", "advance remote", cwd=other)
        self.git("push", "origin", ITEM, cwd=other)
        canonical_before = self.git(
            "rev-parse", f"refs/heads/{ITEM}", cwd=self.canonical
        ).stdout.strip()
        self.commit_worker()

        result = self.publish()

        self.assert_refused(result, "non-fast-forward")
        canonical_after = self.git(
            "rev-parse", f"refs/heads/{ITEM}", cwd=self.canonical
        ).stdout.strip()
        self.assertEqual(canonical_after, canonical_before)

    def test_refuses_detached_head_and_dirty_clone(self) -> None:
        self.git("checkout", "--detach", cwd=self.worker)
        self.assert_refused(self.publish(), "detached HEAD")
        self.git("switch", ITEM, cwd=self.worker)
        (self.worker / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        self.assert_refused(self.publish(), "worker clone is dirty")

    def test_refuses_missing_or_mismatched_origin(self) -> None:
        self.git("remote", "remove", "origin", cwd=self.worker)
        self.assert_refused(self.publish(), "origin remote is missing")
        self.git("remote", "add", "origin", str(self.seed), cwd=self.worker)
        self.assert_refused(self.publish(), "expected canonical")

    def test_refuses_symlinked_or_worktree_git_topology(self) -> None:
        symlink_clone = self.root / "symlink-clone"
        symlink_clone.mkdir()
        (symlink_clone / ".git").symlink_to(self.worker / ".git", target_is_directory=True)
        self.assert_refused(self.publish(clone=symlink_clone), ".git' is a symlink")

        worktree = self.root / "linked-worktree"
        self.git("worktree", "add", "-b", "0041-05", str(worktree), cwd=self.seed)
        self.assert_refused(self.publish(clone=worktree), ".git' is not a directory")


if __name__ == "__main__":
    unittest.main()
