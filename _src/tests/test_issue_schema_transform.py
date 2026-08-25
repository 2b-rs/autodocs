#!/usr/bin/env python3
"""Fixtures for Task 0037-15.02 versioned shadow schema transforms."""
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
    "issue_schema_transform", ROOT / "_src/tools/issue_schema_transform.py"
)
TRN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRN)

IMP_SPEC = importlib.util.spec_from_file_location(
    "issue_import_legacy", ROOT / "_src/tools/issue_import_legacy.py"
)
IMP = importlib.util.module_from_spec(IMP_SPEC)
IMP_SPEC.loader.exec_module(IMP)

FIXTURE = ROOT / "issues/_schema/fixtures/issue-item-v1-draft-to-v1"

TODO = """# Backlog

## Feature: 0037 — Ticket store

- [ ] **0037-01** First task.
  - **Acceptance criteria:** Keep identity.
  - **Definition of Done:** Imported.
  PREREQ: 0037-01:0037
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _init_repo(path: Path) -> str:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "TODO.md").write_text(TODO, encoding="utf-8")
    (path / "DONE.md").write_text("# none\n", encoding="utf-8")
    dest_tool = path / "provenance/migrations/issue-store/tools"
    dest_tool.mkdir(parents=True)
    shutil.copy(
        ROOT / "provenance/migrations/issue-store/tools/issue_legacy_inventory.py",
        dest_tool / "issue_legacy_inventory.py",
    )
    (path / "_src/tools").mkdir(parents=True)
    shutil.copy(ROOT / "_src/tools/issue_import_legacy.py", path / "_src/tools/issue_import_legacy.py")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "src"], cwd=path, check=True, capture_output=True)
    return _git(path, "rev-parse", "HEAD")


def _write_input(root: Path, *objs: dict) -> None:
    items = root / "items"
    items.mkdir(parents=True)
    for obj in objs:
        (items / f"{obj['id']}.json").write_text(
            json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def _load_fixture(rel: str) -> dict:
    return json.loads((FIXTURE / rel).read_text(encoding="utf-8"))


class SchemaTransformTests(unittest.TestCase):
    maxDiff = None

    def test_upgrade_equivalence_and_idempotence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            commit = _init_repo(repo)
            import_root = tmp_path / "import"
            import_root.mkdir()
            IMP.import_legacy(repo=repo, root=import_root, source_commit=commit)
            drafts = []
            for md_path in sorted(import_root.rglob("index.md")):
                sem = TRN.parse_imported_markdown(md_path.read_text(encoding="utf-8"))
                draft = {
                    "schema": TRN.FROM_SCHEMA,
                    "schema_version": TRN.DRAFT_SCHEMA_VERSION,
                    "id": sem["id"],
                    "level": sem["level"],
                    "parent": sem["parent"],
                    "state": sem["state"],
                    "prerequisites": sem["prerequisites"],
                    "labels": sem["labels"],
                    "goal": sem["goal"],
                    "scope": sem["scope"],
                    "criteria": sem["criteria"],
                    "definition_of_done": sem["definition_of_done"],
                    "source_locator": "legacy:TODO.md:fixture",
                }
                drafts.append({k: v for k, v in draft.items() if v is not None})
            inp = tmp_path / "in"
            _write_input(inp, *drafts)
            out_parent = tmp_path / "out"
            first = TRN.transform(
                repo=repo,
                input_root=inp,
                output_parent=out_parent,
                from_schema=TRN.FROM_SCHEMA,
                to_schema=TRN.TO_SCHEMA,
                run_id="upgrade-eq-1",
                clean_import_root=import_root,
                source_commit=commit,
            )
            self.assertEqual(first["status"], "validated")
            self.assertTrue(first["promotable"])
            self.assertEqual(first["from_schema"], TRN.FROM_SCHEMA)
            self.assertEqual(first["to_schema"], TRN.TO_SCHEMA)
            self.assertTrue(first["tool_digest"].startswith("sha256:"))
            self.assertIn("output_tree_digest", first)
            art = json.loads((out_parent / "upgrade-eq-1" / "artifact-set.json").read_text(encoding="utf-8"))
            self.assertTrue(art["members"])
            self.assertEqual(art["from_schema"], TRN.FROM_SCHEMA)
            v1 = json.loads((out_parent / "upgrade-eq-1" / "issues/0037/0037-01/item.json").read_text())
            self.assertEqual(v1["schema"], TRN.TO_SCHEMA)
            self.assertEqual(v1["schema_version"], "1.0")
            second = TRN.transform(
                repo=repo,
                input_root=inp,
                output_parent=out_parent,
                from_schema=TRN.FROM_SCHEMA,
                to_schema=TRN.TO_SCHEMA,
                run_id="upgrade-eq-2",
                clean_import_root=import_root,
                source_commit=commit,
            )
            self.assertEqual(first["output_tree_digest"], second["output_tree_digest"])
            self.assertEqual(first["source_tree_digest"], second["source_tree_digest"])
            self.assertFalse((ROOT / "issues/_schema/issue-item-v1.schema.json").read_text().find("1.0-draft") >= 0)

    def test_downgrade_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            _init_repo(repo)
            inp = tmp_path / "in"
            _write_input(inp, _load_fixture("valid/draft-0037-01.json"))
            with self.assertRaises(TRN.TransformError) as ctx:
                TRN.transform(
                    repo=repo,
                    input_root=inp,
                    output_parent=tmp_path / "out",
                    from_schema=TRN.TO_SCHEMA,
                    to_schema=TRN.FROM_SCHEMA,
                    run_id="down-1",
                )
            self.assertEqual(ctx.exception.code, "transform-downgrade-rejected")

    def test_unknown_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            _init_repo(repo)
            inp = tmp_path / "in"
            _write_input(inp, _load_fixture("invalid/unknown-schema.json"))
            with self.assertRaises(TRN.TransformError) as ctx:
                TRN.transform(
                    repo=repo,
                    input_root=inp,
                    output_parent=tmp_path / "out",
                    from_schema="issue-item@v9",
                    to_schema=TRN.TO_SCHEMA,
                    run_id="unk-1",
                )
            self.assertEqual(ctx.exception.code, "transform-unknown-version")
            # Adjacent pair declared but item schema is wrong.
            rec = TRN.transform(
                repo=repo,
                input_root=inp,
                output_parent=tmp_path / "out",
                from_schema=TRN.FROM_SCHEMA,
                to_schema=TRN.TO_SCHEMA,
                run_id="unk-item",
            )
            self.assertEqual(rec["status"], "blocked")
            self.assertIn("transform-unknown-version", rec["blocking_findings"])

    def test_lossy_transform(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            _init_repo(repo)
            inp = tmp_path / "in"
            _write_input(inp, _load_fixture("invalid/lossy-extra-field.json"))
            rec = TRN.transform(
                repo=repo,
                input_root=inp,
                output_parent=tmp_path / "out",
                from_schema=TRN.FROM_SCHEMA,
                to_schema=TRN.TO_SCHEMA,
                run_id="lossy-1",
            )
            self.assertEqual(rec["status"], "blocked")
            self.assertIn("upgrade-lossy-transform", rec["blocking_findings"])
            self.assertFalse(rec["promotable"])
            self.assertNotIn("output_tree_digest", rec)

    def test_crash_fresh_root_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            commit = _init_repo(repo)
            inp = tmp_path / "in"
            _write_input(inp, _load_fixture("valid/draft-0037-01.json"))
            out_parent = tmp_path / "out"
            crashed = TRN.transform(
                repo=repo,
                input_root=inp,
                output_parent=out_parent,
                from_schema=TRN.FROM_SCHEMA,
                to_schema=TRN.TO_SCHEMA,
                run_id="crash-1",
                source_commit=commit,
                crash_after=1,
            )
            self.assertEqual(crashed["status"], "blocked")
            self.assertIn("transform-crash", crashed["blocking_findings"])
            self.assertTrue((out_parent / "crash-1" / "CRASHED").is_file())
            recovered = TRN.transform(
                repo=repo,
                input_root=inp,
                output_parent=out_parent,
                from_schema=TRN.FROM_SCHEMA,
                to_schema=TRN.TO_SCHEMA,
                run_id="crash-1",
                source_commit=commit,
            )
            self.assertEqual(recovered["status"], "validated")
            self.assertFalse((out_parent / "crash-1" / "CRASHED").exists())

    def test_representation_drift_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            commit = _init_repo(repo)
            import_root = tmp_path / "import"
            import_root.mkdir()
            IMP.import_legacy(repo=repo, root=import_root, source_commit=commit)
            draft = _load_fixture("valid/draft-0037-01.json")
            draft["goal"] = "DIFFERENT GOAL THAT MUST NOT DRIFT"
            inp = tmp_path / "in"
            _write_input(inp, draft)
            rec = TRN.transform(
                repo=repo,
                input_root=inp,
                output_parent=tmp_path / "out",
                from_schema=TRN.FROM_SCHEMA,
                to_schema=TRN.TO_SCHEMA,
                run_id="drift-1",
                clean_import_root=import_root,
                source_commit=commit,
            )
            self.assertEqual(rec["status"], "blocked")
            self.assertIn("upgrade-representation-drift", rec["blocking_findings"])

    def test_refuses_live_issues_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo = tmp_path / "repo"
            _init_repo(repo)
            inp = tmp_path / "in"
            _write_input(inp, _load_fixture("valid/draft-0037-01.json"))
            with self.assertRaises(TRN.TransformError) as ctx:
                TRN.transform(
                    repo=ROOT,
                    input_root=inp,
                    output_parent=ROOT / "issues",
                    from_schema=TRN.FROM_SCHEMA,
                    to_schema=TRN.TO_SCHEMA,
                    run_id="live-1",
                )
            self.assertEqual(ctx.exception.code, "TRN-LIVE")


if __name__ == "__main__":
    unittest.main()
