#!/usr/bin/env python3
"""Parent-package consistency for Task 0037-15: combined == clean latest import + replay."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "issue_reconciliation", ROOT / "_src/tools/issue_reconciliation.py"
)
REC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REC)

TODO_EARLY = """# Backlog

## Feature: 0037 — Ticket store

- [ ] **0037-01** First task.
  - **Acceptance criteria:** Keep identity.
  - **Definition of Done:** Imported.
  PREREQ: 0037-01:0037

## Feature: 0001 — Other

- [ ] **0001-01** Alpha.
  - **Acceptance criteria:** A.
"""

TODO_MID = """# Backlog

## Feature: 0037 — Ticket store

- [ ] **0037-01** First task.
  - **Acceptance criteria:** Keep identity.
  - **Definition of Done:** Imported.
  PREREQ: 0037-01:0037

## Feature: 0001 — Other

- [ ] **0001-01** Alpha after intervening commit.
  - **Acceptance criteria:** A-mid.
- [ ] **0001-02** Added mid-stream.
  - **Acceptance criteria:** Mid.
"""

TODO_LATE = """# Backlog

## Feature: 0037 — Ticket store

- [ ] **0037-01** First task.
  - **Acceptance criteria:** Keep identity.
  - **Definition of Done:** Imported after schema target v1.
  PREREQ: 0037-01:0037

## Feature: 0001 — Other

- [ ] **0001-01** Alpha after intervening commit.
  - **Acceptance criteria:** A-mid.
- [ ] **0001-02** Added mid-stream.
  - **Acceptance criteria:** Mid.
- [ ] **0001-03** Added at latest source.
  - **Acceptance criteria:** Late.
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
    tools = path / "_src/tools"
    tools.mkdir(parents=True)
    for name in (
        "issue_import_legacy.py",
        "issue_reimport.py",
        "issue_schema_transform.py",
        "issue_event_replay.py",
        "issue_reconciliation.py",
        "provenance_store.py",
    ):
        shutil.copy(ROOT / "_src/tools" / name, tools / name)
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "early source"], cwd=path, check=True, capture_output=True)
    return _git(path, "rev-parse", "HEAD")


def _commit_todo(repo: Path, todo: str, message: str) -> str:
    (repo / "TODO.md").write_text(todo, encoding="utf-8")
    subprocess.run(["git", "add", "TODO.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)
    return _git(repo, "rev-parse", "HEAD")


class ReconciliationTests(unittest.TestCase):
    maxDiff = None

    def test_intervening_commits_and_schema_upgrade_no_loss_or_dup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            early = _init_repo(repo, TODO_EARLY)
            mid = _commit_todo(repo, TODO_MID, "intervening legacy")
            latest = _commit_todo(repo, TODO_LATE, "latest source")
            out = Path(tmp) / "out"
            report = REC.reconcile(
                repo=repo,
                output_parent=out,
                early_commit=early,
                latest_commit=latest,
                intervening_commits=[mid],
            )
            self.assertTrue(report["equivalent"], report["findings"])
            self.assertTrue(report["schema_upgrade"]["promotable"])
            self.assertEqual(report["schema_upgrade"]["from_schema"], REC.TRN.FROM_SCHEMA)
            self.assertEqual(report["schema_upgrade"]["to_schema"], REC.TRN.TO_SCHEMA)
            self.assertEqual(report["combined"]["import_tree_digest"], report["clean"]["import_tree_digest"])
            self.assertEqual(report["combined"]["item_ids"], report["clean"]["item_ids"])
            self.assertIn("0037-01", report["combined"]["item_ids"])
            self.assertIn("0001-03", report["combined"]["item_ids"])
            self.assertEqual(report["lost_items"], [])
            self.assertEqual(report["extra_items"], [])
            self.assertEqual(report["drifted_items"], [])
            self.assertEqual(report["combined"]["event_ids"], report["clean"]["event_ids"])
            self.assertEqual(report["combined"]["replayed"], 1)
            self.assertEqual(len(report["combined"]["event_ids"]), 1)

    def test_manual_shadow_cannot_win(self) -> None:
        """Equivalence is computed from importer/transform/replay outputs, not shadow edits."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            early = _init_repo(repo, TODO_EARLY)
            mid = _commit_todo(repo, TODO_MID, "mid")
            latest = _commit_todo(repo, TODO_LATE, "late")
            out = Path(tmp) / "out"
            report = REC.reconcile(
                repo=repo,
                output_parent=out,
                early_commit=early,
                latest_commit=latest,
                intervening_commits=[mid],
            )
            shadow = Path(tmp) / "manual-shadow"
            shadow.mkdir()
            (shadow / "0037-01.json").write_text('{"id":"0037-01","forged":true}\n', encoding="utf-8")
            self.assertTrue(report["equivalent"])
            self.assertNotEqual(
                report["combined"]["item_ids"],
                ["forged"],
            )
            self.assertNotIn("forged", str(report["combined"]["item_ids"]))


if __name__ == "__main__":
    unittest.main()
