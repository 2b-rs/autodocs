#!/usr/bin/env python3
"""Hermetic fixtures for the 0044-14 pre-integration hygiene checker.

Run with:
    python3 -m unittest _src/tools/test_check_integration_hygiene.py -v
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import check_integration_hygiene as hygiene
import integration_hygiene_policy as policy


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

    def _commit_memory_file(self, relative: str = "logs/agent-memory/roles/Architect.md") -> Path:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("baseline\n", encoding="utf-8")
        _git(self.root, "add", relative)
        _git(self.root, "commit", "-q", "-m", "add memory fixture")
        return target

    def test_exclusive_unstaged_memory_divergence_passes(self) -> None:
        target = self._commit_memory_file()
        target.write_text("ephemeral learning\n", encoding="utf-8")

        report = hygiene.check_integration_hygiene(self.root)

        self.assertTrue(report.ok, report.to_dict())
        root_state = next(state for state in report.worktrees if state.path == str(self.root.resolve()))
        self.assertFalse(root_state.worktree_equals_index)
        self.assertEqual(
            set(report.to_dict()["worktrees"][0]),
            {"path", "head", "branch", "index_equals_head", "worktree_equals_index"},
        )

    def test_empty_root_state_is_clean_not_exception(self) -> None:
        report = hygiene.check_root_preflight(self.root)
        root_state = next(state for state in report.worktrees if state.path == str(self.root.resolve()))
        self.assertTrue(report.ok, report.to_dict())
        self.assertTrue(root_state.worktree_equals_index)

    def test_memory_directory_itself_is_not_an_allowed_child(self) -> None:
        target = self.root / "logs" / "agent-memory"
        target.parent.mkdir()
        target.write_text("baseline\n", encoding="utf-8")
        _git(self.root, "add", "logs/agent-memory")
        _git(self.root, "commit", "-q", "-m", "add exact directory-name file")
        target.write_text("changed\n", encoding="utf-8")

        report = hygiene.check_integration_hygiene(self.root)

        self.assertFalse(report.ok)
        self.assertIn("MAIN_WORKTREE_DIRTY", {finding.code for finding in report.findings})

    def test_path_predicate_is_exact_case_sensitive_and_nul_safe(self) -> None:
        payload = (
            b"logs/agent-memory/roles/A.md\0"
            b"logs/agent-memory/line\nbreak.md\0"
            b"logs/agent-memory\0"
            b"logs/agent-memory-lookalike/A.md\0"
            b"logs/Agent-Memory/A.md\0"
        )
        paths = policy.split_nul_paths(payload)
        classified = policy.classify_unstaged_paths(paths)
        self.assertEqual(
            classified.allowed_memory_paths,
            (b"logs/agent-memory/roles/A.md", b"logs/agent-memory/line\nbreak.md"),
        )
        self.assertEqual(
            classified.blocking_paths,
            (
                b"logs/agent-memory",
                b"logs/agent-memory-lookalike/A.md",
                b"logs/Agent-Memory/A.md",
            ),
        )
        with self.assertRaises(ValueError):
            policy.split_nul_paths(b"logs/agent-memory/unterminated")

    def test_newline_bearing_memory_child_passes_without_line_parsing(self) -> None:
        target = self._commit_memory_file("logs/agent-memory/line\nbreak.md")
        target.write_text("changed\n", encoding="utf-8")

        report = hygiene.check_root_preflight(self.root)

        self.assertTrue(report.ok, report.to_dict())

    def test_mixed_memory_and_non_memory_divergence_blocks(self) -> None:
        memory = self._commit_memory_file()
        memory.write_text("ephemeral\n", encoding="utf-8")
        (self.root / "README.md").write_text("non-memory\n", encoding="utf-8")

        report = hygiene.check_root_preflight(self.root)

        self.assertFalse(report.ok)
        self.assertIn("MAIN_WORKTREE_DIRTY", {finding.code for finding in report.findings})

    def test_staged_memory_divergence_blocks(self) -> None:
        target = self._commit_memory_file()
        target.write_text("staged\n", encoding="utf-8")
        _git(self.root, "add", "logs/agent-memory/roles/Architect.md")

        report = hygiene.check_root_preflight(self.root)

        codes = {finding.code for finding in report.findings}
        self.assertFalse(report.ok)
        self.assertIn("INDEX_NOT_HEAD", codes)
        self.assertIn("ROOT_INDEX_NOT_HEAD", codes)

    def test_candidate_memory_overlap_blocks_for_equal_and_different_bytes(self) -> None:
        target = self._commit_memory_file()
        _git(self.root, "checkout", "-q", "-b", "candidate")
        target.write_text("candidate\n", encoding="utf-8")
        _git(self.root, "add", "logs/agent-memory/roles/Architect.md")
        _git(self.root, "commit", "-q", "-m", "candidate changes memory")
        candidate = _git(self.root, "rev-parse", "HEAD")
        _git(self.root, "checkout", "-q", "main")

        for content in ("candidate\n", "different dirty bytes\n"):
            with self.subTest(content=content):
                target.write_text(content, encoding="utf-8")
                report = hygiene.check_root_preflight(self.root, candidate_ref=candidate)
                self.assertFalse(report.ok)
                self.assertIn("CANDIDATE_MEMORY_OVERLAP", {finding.code for finding in report.findings})
        _git(self.root, "checkout", "--", "logs/agent-memory/roles/Architect.md")

    def test_root_preflight_wrong_worktree_and_unavailable_repo_fail_closed(self) -> None:
        item = Path(self.temporary.name) / "item-preflight"
        _git(self.root, "worktree", "add", "-q", "-b", "item-preflight", str(item))
        report = hygiene.check_root_preflight(item)
        self.assertFalse(report.ok)
        self.assertIn("ROOT_WORKTREE_REQUIRED", {finding.code for finding in report.findings})
        with self.assertRaises(hygiene.GitError):
            hygiene.check_root_preflight(Path(self.temporary.name) / "absent")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = hygiene.main(
                ["--repo", str(Path(self.temporary.name) / "absent"), "--root-preflight"]
            )
        self.assertEqual(exit_code, 2)
        self.assertIn("integration hygiene: ERROR", stderr.getvalue())
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = hygiene.main(
                ["--repo", str(self.root), "--candidate-ref", "missing-candidate"]
            )
        self.assertEqual(exit_code, 2)
        self.assertIn("integration hygiene: ERROR", stderr.getvalue())

    def test_role_and_procedure_docs_assign_hygiene_to_integrator(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        agents = (repository / "AGENTS.md").read_text(encoding="utf-8")
        workflow = (repository / "docs/pipeline/branch-workflow.md").read_text(encoding="utf-8")
        lead = (repository / "docs/pipeline/roles/project-lead.md").read_text(encoding="utf-8")
        integrator = (repository / "docs/pipeline/roles/integrator.md").read_text(encoding="utf-8")
        matrix = (repository / "docs/pipeline/role_artifact_matrix.csv").read_text(encoding="utf-8")
        self.assertIn("Only the expressly assigned privileged Integrator", agents)
        self.assertIn("--root-preflight", workflow)
        self.assertIn("does not run the gate or merge `main`", workflow)
        self.assertIn("Do not run the integration hygiene gate", lead)
        self.assertIn("Post-Merge Verification", integrator)
        self.assertIn('"Repository Hygiene and Post-Merge Verdict","Integrator"', matrix)

    def test_transient_foreign_staged_tree_resolves_before_second_sample(self) -> None:
        foreign = Path(self.temporary.name) / "foreign"
        _git(self.root, "worktree", "add", "-q", "-b", "0044-transient", str(foreign))
        (foreign / "foreign.txt").write_text("commit in flight\n", encoding="utf-8")
        _git(foreign, "add", "foreign.txt")
        observed_delays: list[float] = []

        def finish_commit(delay: float) -> None:
            observed_delays.append(delay)
            _git(foreign, "commit", "-q", "-m", "finish in-flight commit")

        report = hygiene.check_integration_hygiene(
            self.root,
            foreign_resample_delay_seconds=0.25,
            sleeper=finish_commit,
        )
        self.assertEqual(observed_delays, [0.25])
        self.assertTrue(report.ok, report.to_dict())
        self.assertNotIn("FOREIGN_STAGED_TREE", {finding.code for finding in report.findings})

    def test_persistent_foreign_staged_tree_fails_with_index_age(self) -> None:
        foreign = Path(self.temporary.name) / "foreign"
        _git(self.root, "worktree", "add", "-q", "-b", "0044-foreign", str(foreign))
        (foreign / "foreign.txt").write_text("staged elsewhere\n", encoding="utf-8")
        _git(foreign, "add", "foreign.txt")
        sample_time = 1_700_000_000.0
        index_mtime = sample_time - (11 * 60 * 60)
        os.utime(hygiene._index_path(foreign), (index_mtime, index_mtime))

        report = hygiene.check_integration_hygiene(
            self.root,
            clock=lambda: sample_time,
        )
        findings = {finding.code: finding for finding in report.findings}
        self.assertFalse(report.ok)
        self.assertIn("FOREIGN_STAGED_TREE", findings)
        finding = findings["FOREIGN_STAGED_TREE"]
        self.assertEqual(finding.worktree, str(foreign.resolve()))
        self.assertEqual(finding.index_age_seconds, 39_600.0)
        self.assertEqual(finding.resample_delay_seconds, 2.0)
        self.assertIsNotNone(finding.index_mtime_utc)
        parsed_mtime = datetime.fromisoformat(finding.index_mtime_utc.replace("Z", "+00:00"))
        self.assertEqual(parsed_mtime.timestamp(), index_mtime)
        self.assertIn("index age 39600.000s", finding.detail)
        serialized = next(
            item for item in report.to_dict()["findings"] if item["code"] == "FOREIGN_STAGED_TREE"
        )
        self.assertEqual(serialized["index_age_seconds"], 39_600.0)
        self.assertEqual(serialized["index_mtime_utc"], finding.index_mtime_utc)
        self.assertEqual(serialized["resample_delay_seconds"], 2.0)

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
        serialized = next(
            item for item in report.to_dict()["findings"] if item["code"] == "MAIN_WORKTREE_DIRTY"
        )
        self.assertNotIn("index_age_seconds", serialized)
        self.assertNotIn("index_mtime_utc", serialized)
        self.assertNotIn("resample_delay_seconds", serialized)

    def test_post_merge_root_preflight_uses_same_memory_classification(self) -> None:
        target = self._commit_memory_file()
        target.write_text("post-merge ephemeral state\n", encoding="utf-8")
        self.assertTrue(hygiene.check_root_preflight(self.root).ok)
        (self.root / "README.md").write_text("post-merge non-memory drift\n", encoding="utf-8")
        report = hygiene.check_root_preflight(self.root)
        self.assertFalse(report.ok)
        self.assertIn("MAIN_WORKTREE_DIRTY", {finding.code for finding in report.findings})

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
