#!/usr/bin/env python3
"""Hermetic tests for the fail-open reference-transaction warning hook."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import reference_transaction_hook as hook


CONTRACT = """# Backlog

## Feature: 0044 — Pipeline

- [x] **0044-12** Provenance predecessor.
- [ ] **0044-13** PREREQ: 0044-13:0044-12 Hook successor.
"""


class ReferenceTransactionHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self._git("init", "--initial-branch=main", str(self.repo), outside=True)
        self.base = self._commit(None, {"TODO.md": CONTRACT}, "base")
        self._git("update-ref", "refs/heads/main", self.base)
        self._git("read-tree", "--reset", "-u", self.base)

    def _git(
        self,
        *args: str,
        input_text: str | None = None,
        outside: bool = False,
        environment: dict[str, str] | None = None,
    ) -> str:
        command = ["git", *args] if outside else ["git", "-C", str(self.repo), *args]
        process = subprocess.run(
            command,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env=environment,
        )
        if process.returncode != 0:
            self.fail(
                f"{' '.join(command)} failed ({process.returncode}): "
                f"{process.stderr.strip()}"
            )
        return process.stdout.strip()

    def _commit(self, parent: str | None, files: dict[str, str], message: str) -> str:
        entries: list[str] = []
        for path, content in sorted(files.items()):
            blob = self._git("hash-object", "-w", "--stdin", input_text=content)
            entries.append(f"100644 blob {blob}\t{path}\n")
        tree = self._git("mktree", input_text="".join(entries))
        arguments = ["commit-tree", tree, "-m", message]
        if parent is not None:
            arguments.extend(["-p", parent])
        environment = os.environ.copy()
        environment.update(
            {
                "GIT_AUTHOR_NAME": "Fixture",
                "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "Fixture",
                "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
            }
        )
        return self._git(*arguments, environment=environment)

    def _foreign_tip(self) -> str:
        tip = self._commit(
            self.base,
            {"TODO.md": CONTRACT, "foreign.txt": "foreign\n"},
            "foreign",
        )
        self._git("update-ref", "refs/heads/foreign", tip)
        return tip

    def _install(self) -> dict[str, object]:
        result = hook.install(self.repo)
        self.assertEqual("installed", result["status"])
        return result

    def _events(self) -> list[dict[str, object]]:
        log_path = hook._discover_context(self.repo).log_path
        if not log_path.is_file():
            return []
        return [json.loads(line) for line in log_path.read_text().splitlines() if line]

    def test_install_and_presence_check_are_exact_and_idempotent(self) -> None:
        result = self._install()
        installed = Path(str(result["hook_path"]))
        self.assertTrue(installed.is_file())
        self.assertTrue(os.access(installed, os.X_OK))

        evidence = hook.presence(self.repo)
        self.assertTrue(evidence["present"])
        self.assertEqual(result["sha256"], evidence["actual_sha256"])
        self.assertEqual("already-installed", hook.install(self.repo)["status"])

    def test_install_never_overwrites_a_different_existing_hook(self) -> None:
        context = hook._discover_context(self.repo)
        hooks_dir = context.common_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        installed = hooks_dir / hook.HOOK_NAME
        installed.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

        with self.assertRaises(hook.HookError):
            hook.install(self.repo)

        self.assertEqual("#!/bin/sh\nexit 0\n", installed.read_text(encoding="utf-8"))

    def test_install_refuses_a_symlinked_hook_target(self) -> None:
        context = hook._discover_context(self.repo)
        hooks_dir = context.common_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        other = Path(self.temporary.name) / "other-hook"
        other.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        installed = hooks_dir / hook.HOOK_NAME
        installed.symlink_to(other)

        with self.assertRaises(hook.HookError):
            hook.install(self.repo)

        self.assertFalse(hook.presence(self.repo)["present"])
        self.assertEqual("#!/bin/sh\nexit 0\n", other.read_text(encoding="utf-8"))

    def test_fast_forward_merge_logs_committed_foreign_origin(self) -> None:
        foreign = self._foreign_tip()
        self._install()

        self._git("merge", "--ff-only", "foreign")

        events = self._events()
        self.assertEqual(1, len(events))
        self.assertEqual("committed", events[0]["outcome"])
        finding = events[0]["findings"][0]
        self.assertEqual("refs/heads/main", finding["target_ref"])
        self.assertEqual(foreign, finding["new_oid"])
        self.assertEqual(
            [{"commit": foreign, "also_on": ["refs/heads/foreign"]}],
            finding["foreign_origin"],
        )

    def test_update_ref_logs_committed_foreign_origin(self) -> None:
        foreign = self._foreign_tip()
        self._install()

        self._git("update-ref", "refs/heads/main", foreign, self.base)

        events = self._events()
        self.assertEqual(1, len(events))
        finding = events[0]["findings"][0]
        self.assertEqual("refs/heads/main", finding["target_ref"])
        self.assertEqual(foreign, finding["foreign_origin"][0]["commit"])

    def test_direct_prerequisite_and_successor_tips_are_carve_outs(self) -> None:
        predecessor = self._commit(
            self.base,
            {"TODO.md": CONTRACT, "predecessor.txt": "predecessor\n"},
            "predecessor",
        )
        self._git("update-ref", "refs/heads/0044-12", predecessor)
        self._git("update-ref", "refs/heads/0044-13", self.base)
        self._install()

        self._git("update-ref", "refs/heads/0044-13", predecessor, self.base)
        self.assertEqual([], self._events())

        successor = self._commit(
            predecessor,
            {
                "TODO.md": CONTRACT,
                "predecessor.txt": "predecessor\n",
                "successor.txt": "successor\n",
            },
            "successor",
        )
        self._git("update-ref", "refs/heads/0044-13", successor, predecessor)
        self._git("update-ref", "refs/heads/0044-12", successor, predecessor)

        self.assertEqual([], self._events())

    def test_hook_failure_never_blocks_reference_transaction(self) -> None:
        foreign = self._foreign_tip()
        self._install()
        evidence_path = hook._discover_context(self.repo).evidence_dir
        evidence_path.write_text("not a directory", encoding="utf-8")

        self._git("update-ref", "refs/heads/main", foreign, self.base)

        self.assertEqual(foreign, self._git("rev-parse", "refs/heads/main"))
        self.assertTrue(evidence_path.is_file())

    def test_malformed_hook_input_fails_open(self) -> None:
        with tempfile.TemporaryFile(mode="w+") as stream:
            stream.write("malformed\n")
            stream.seek(0)
            self.assertEqual(0, hook.hook_entry("prepared", stream))


if __name__ == "__main__":
    unittest.main()
