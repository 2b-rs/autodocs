#!/usr/bin/env python3
"""Tests for Task 0037-15.01 source-watermark tracking and full re-import."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "issue_reimport", ROOT / "_src/tools/issue_reimport.py"
)
REI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REI)

TODO_A = """# Backlog

## Feature: 0037 — Ticket store

- [ ] **0037-01** First task.
  - **Acceptance criteria:** Keep identity.
  - **Definition of Done:** Imported.
  PREREQ: 0037-01:0037

## Feature: 0001 — Other

- [ ] **0001-01** Alpha.
  - **Acceptance criteria:** A.
"""

TODO_B = """# Backlog

## Feature: 0037 — Ticket store

- [ ] **0037-01** First task moved context.
  - **Acceptance criteria:** Keep identity.
  - **Definition of Done:** Imported.
  PREREQ: 0037-01:0037-15.01

## Feature: 0001 — Other

- [x] **0001-02** Replacement after delete.
  - **Acceptance criteria:** B.
"""

TODO_REUSE = """# Backlog

## Feature: 0037 — Ticket store

- [ ] **0037-01** First task.
  - **Acceptance criteria:** Keep identity.

## Feature: 0001 — Other

- [ ] **0001-01** Reused identity with new meaning.
  - **Acceptance criteria:** Z.
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _init_repo(path: Path, todo: str) -> str:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "TODO.md").write_text(todo, encoding="utf-8")
    (path / "DONE.md").write_text("# none\n", encoding="utf-8")
    dest_tool = path / "provenance/migrations/issue-store/tools"
    dest_tool.mkdir(parents=True)
    shutil.copy(
        ROOT / "provenance/migrations/issue-store/tools/issue_legacy_inventory.py",
        dest_tool / "issue_legacy_inventory.py",
    )
    (path / "_src/tools").mkdir(parents=True)
    shutil.copy(ROOT / "_src/tools/issue_import_legacy.py", path / "_src/tools/issue_import_legacy.py")
    shutil.copy(ROOT / "_src/tools/issue_reimport.py", path / "_src/tools/issue_reimport.py")
    shutil.copy(ROOT / "_src/tools/provenance_store.py", path / "_src/tools/provenance_store.py")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "src"], cwd=path, check=True, capture_output=True)
    return _git(path, "rev-parse", "HEAD")


def _commit_todo(repo: Path, todo: str, message: str) -> str:
    (repo / "TODO.md").write_text(todo, encoding="utf-8")
    subprocess.run(["git", "add", "TODO.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)
    return _git(repo, "rev-parse", "HEAD")


class ReimportTests(unittest.TestCase):
    maxDiff = None

    def test_multiple_source_commits_and_latest_equivalence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sha1 = _init_repo(repo, TODO_A)
            out = Path(tmp) / "out"
            first = REI.reimport(repo=repo, output_parent=out, source_commit=sha1, baseline=sha1)
            self.assertEqual(first["watermarks"]["baseline"], sha1)
            self.assertEqual(first["watermarks"]["latest_source"], sha1)
            self.assertEqual(first["watermarks"]["candidate"], sha1)
            self.assertIn(first["status"], {"validated", "rejected"})
            self.assertTrue(first.get("provenance_run_id"))
            self.assertTrue(first.get("source_artifact_set_id"))
            ids = {i["id"] for i in first["items"]}
            self.assertIn("0037", ids)
            self.assertIn("0037-01", ids)
            self.assertIn("0001-01", ids)

            sha2 = _commit_todo(repo, TODO_B, "second")
            second = REI.reimport(
                repo=repo,
                output_parent=out,
                source_commit=sha2,
                previous_state_path=Path(first["run_root"]) / "migration-state.json",
            )
            self.assertEqual(second["watermarks"]["latest_source"], sha2)
            self.assertEqual(second["watermarks"]["baseline"], sha1)
            self.assertNotEqual(second["run_id"], first["run_id"])
            codes = {f["code"] for f in second["findings"]}
            self.assertIn("deleted-id", codes)
            self.assertIn("prerequisites-changed", codes)

            again = REI.reimport(repo=repo, output_parent=out, source_commit=sha2, baseline=sha1)
            self.assertEqual(again["import_tree_digest"], second["import_tree_digest"])
            self.assertEqual(again["candidate"]["tree_digest"], second["candidate"]["tree_digest"])

    def test_interrupted_run_is_discarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sha = _init_repo(repo, TODO_A)
            out = Path(tmp) / "out"
            first = REI.reimport(repo=repo, output_parent=out, source_commit=sha)
            state_path = Path(first["run_root"]) / "migration-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["status"] = "interrupted"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            leftover = Path(first["run_root"]) / "partial"
            leftover.mkdir()
            (leftover / "junk").write_text("x", encoding="utf-8")
            second = REI.reimport(
                repo=repo,
                output_parent=out,
                source_commit=sha,
                previous_state_path=state_path,
            )
            codes = {f["code"] for f in second["findings"]}
            self.assertIn("interrupted-run-discarded", codes)
            self.assertNotEqual(second["run_id"], first["run_id"])
            self.assertTrue(Path(second["run_root"]).is_dir())

    def test_stale_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sha1 = _init_repo(repo, TODO_A)
            out = Path(tmp) / "out"
            first = REI.reimport(repo=repo, output_parent=out, source_commit=sha1)
            sha2 = _commit_todo(repo, TODO_B, "move")
            second = REI.reimport(
                repo=repo,
                output_parent=out,
                source_commit=sha2,
                previous_state_path=Path(first["run_root"]) / "migration-state.json",
            )
            codes = {f["code"] for f in second["findings"]}
            self.assertIn("stale-candidate", codes)
            self.assertEqual(second["status"], "rejected")
            self.assertFalse(second["candidate"]["promotable"])

    def test_dirty_final_source_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sha = _init_repo(repo, TODO_A)
            (repo / "TODO.md").write_text(TODO_A + "\n# dirty\n", encoding="utf-8")
            out = Path(tmp) / "out"
            result = REI.reimport(
                repo=repo,
                output_parent=out,
                source_commit=sha,
                require_clean=True,
            )
            codes = {f["code"] for f in result["findings"]}
            self.assertIn("dirty-legacy-source", codes)
            self.assertEqual(result["status"], "rejected")
            self.assertFalse(result["source"]["working_tree_clean"])

    def test_deleted_and_reused_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sha1 = _init_repo(repo, TODO_A)
            out = Path(tmp) / "out"
            first = REI.reimport(repo=repo, output_parent=out, source_commit=sha1)
            sha2 = _commit_todo(repo, TODO_B, "delete 0001-01")
            mid = REI.reimport(
                repo=repo,
                output_parent=out,
                source_commit=sha2,
                previous_state_path=Path(first["run_root"]) / "migration-state.json",
            )
            deleted = {f["message"] for f in mid["findings"] if f["code"] == "deleted-id"}
            self.assertTrue(any("0001-01" in m for m in deleted))
            sha3 = _commit_todo(repo, TODO_REUSE, "reuse 0001-01")
            third = REI.reimport(
                repo=repo,
                output_parent=out,
                source_commit=sha3,
                previous_state_path=Path(mid["run_root"]) / "migration-state.json",
                seen_deleted_ids=["0001-01"],
            )
            codes = {f["code"] for f in third["findings"]}
            self.assertIn("reused-id", codes)

    def test_atomic_promote_after_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sha = _init_repo(repo, TODO_A)
            out = Path(tmp) / "out"
            dest = Path(tmp) / "promoted-issues"
            result = REI.reimport(
                repo=repo,
                output_parent=out,
                source_commit=sha,
                promote_to=dest,
            )
            self.assertEqual(result["status"], "promoted")
            self.assertTrue((dest / "0037" / "index.md").is_file())
            self.assertTrue((dest / "0001" / "0001-01" / "index.md").is_file())

    def test_missing_feature_0037_blocks(self):
        todo = "# x\n\n## Feature: 0001 — Only\n\n- [ ] **0001-01** T.\n  - **Acceptance criteria:** A.\n"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            sha = _init_repo(repo, todo)
            out = Path(tmp) / "out"
            result = REI.reimport(repo=repo, output_parent=out, source_commit=sha)
            codes = {f["code"] for f in result["findings"]}
            self.assertIn("missing-feature-0037", codes)
            self.assertFalse(result["candidate"]["promotable"])


if __name__ == "__main__":
    unittest.main()
