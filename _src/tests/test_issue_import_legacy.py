#!/usr/bin/env python3
"""Tests for Task 0037-14 issue_import_legacy."""
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
    "issue_import_legacy", ROOT / "_src/tools/issue_import_legacy.py"
)
IMP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMP)
FIXTURE_13 = ROOT / "provenance/migrations/issue-store/fixtures/0037-13"


class ImportLegacyTests(unittest.TestCase):
    maxDiff = None

    def _import_fixture(self, dest: Path):
        return IMP.import_legacy(repo=ROOT, root=dest, source_tree=FIXTURE_13)

    def test_repeated_imports_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a"
            b = Path(tmp) / "b"
            first = self._import_fixture(a)
            second = self._import_fixture(b)
            self.assertEqual(first["tree_digest"], second["tree_digest"])
            written = first["written"]
            self.assertTrue(written)
            for rel in written:
                self.assertEqual((a / rel).read_bytes(), (b / rel).read_bytes())
            self.assertEqual((a / "import-findings.json").read_bytes(), (b / "import-findings.json").read_bytes())
            # Manifest includes absolute disposable_root; compare minus that field.
            ma = json.loads((a / "import-manifest.json").read_text(encoding="utf-8"))
            mb = json.loads((b / "import-manifest.json").read_text(encoding="utf-8"))
            ma.pop("disposable_root")
            mb.pop("disposable_root")
            self.assertEqual(ma, mb)

    def test_ac_ids_by_document_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            tree = Path(tmp) / "src"
            tree.mkdir()
            (tree / "TODO.md").write_text(
                "# t\n\n## Feature: 0099 — Order\n\n"
                "- [ ] **0099-01** Example legacy task.\n"
                "  - **Acceptance criteria:** First stated requirement; second stated requirement; third\n"
                "    stated requirement.\n"
                "  - **Definition of Done:** Done.\n",
                encoding="utf-8",
            )
            (tree / "DONE.md").write_text("# empty\n", encoding="utf-8")
            IMP.import_legacy(repo=ROOT, root=dest, source_tree=tree)
            body = (dest / "issues/0099/0099-01/index.md").read_text(encoding="utf-8")
            self.assertIn("- **AC-001** First stated requirement", body)
            self.assertIn("- **AC-002** second stated requirement", body)
            self.assertIn("- **AC-003** third stated requirement", body)

    def test_states_refs_and_0021(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            manifest = self._import_fixture(dest)
            by_id = {i["id"]: i for i in manifest["items"]}
            self.assertEqual(by_id["0037-06"]["state"], "closed")
            self.assertEqual(by_id["0037-13"]["state"], "in_progress")
            self.assertEqual(by_id["0037"]["state"], "open")
            self.assertEqual(by_id["0021"]["state"], "closed")
            text_0021 = (dest / "issues/0021/index.md").read_text(encoding="utf-8")
            self.assertIn("archived-not-accepted", text_0021)
            rules = {f["rule"] for f in manifest["findings"]}
            self.assertIn("IMP-REF-NO-EVIDENCE-CREDIT", rules)
            self.assertIn("IMP-ID-DUPLICATE", rules)
            self.assertIn("IMP-MARKER-UNDEFINED", rules)
            self.assertIn("IMP-TASK-HEADER-MALFORMED", rules)
            self.assertIn("IMP-REF-PENDING", rules)
            self.assertFalse(manifest["claim_json_emitted"])
            self.assertFalse(manifest["closure_json_emitted"])
            self.assertTrue(any(p.startswith("legacy-claims/") for p in manifest["written"]))
            self.assertFalse(list(dest.rglob("claim.json")))
            self.assertFalse(list(dest.rglob("closure.json")))

    def test_refuse_live_roots(self):
        with self.assertRaises(IMP.ImportErrorClosed) as ctx:
            IMP.resolve_disposable_root(ROOT / "issues", ROOT)
        self.assertEqual(ctx.exception.code, "IMP-LIVE-ROOT")
        with self.assertRaises(IMP.ImportErrorClosed):
            IMP.resolve_disposable_root(ROOT / "provenance", ROOT)
        with self.assertRaises(IMP.ImportErrorClosed):
            IMP.resolve_disposable_root(ROOT, ROOT)

    def test_path_confusion_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            dest.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            (outside / "secret").write_text("nope\n", encoding="utf-8")
            trap = dest / "issues"
            trap.symlink_to(outside)
            with self.assertRaises(IMP.ImportErrorClosed):
                IMP.atomic_write(dest / "issues" / "0037" / "index.md", b"x\n", dest.resolve())

    def test_malformed_fixture_does_not_write_bad_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            manifest = self._import_fixture(dest)
            ids = {i["id"] for i in manifest["items"]}
            self.assertNotIn("not-an-id", ids)
            self.assertTrue(manifest["blocking"])

    def test_git_commit_source_and_named_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
            (repo / "TODO.md").write_text(
                "## Feature: 0001 — One\n\n- [ ] **0001-01** Task.\n  - **Acceptance criteria:** A.\n",
                encoding="utf-8",
            )
            (repo / "DONE.md").write_text("# none\n", encoding="utf-8")
            (repo / "TODO-agent.md").write_text("- item: 0001-01\n- owner_token: agent:x:0001-01:1\n", encoding="utf-8")
            # copy inventory tool so importer can load it
            dest_tool = repo / "provenance/migrations/issue-store/tools"
            dest_tool.mkdir(parents=True)
            shutil.copy(
                ROOT / "provenance/migrations/issue-store/tools/issue_legacy_inventory.py",
                dest_tool / "issue_legacy_inventory.py",
            )
            (repo / "_src/tools").mkdir(parents=True)
            shutil.copy(ROOT / "_src/tools/issue_import_legacy.py", repo / "_src/tools/issue_import_legacy.py")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "src"], cwd=repo, check=True, capture_output=True)
            sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
            out = Path(tmp) / "out"
            manifest = IMP.import_legacy(
                repo=repo,
                root=out,
                source_commit=sha,
                named_files=["TODO.md", "DONE.md", "TODO-agent.md"],
            )
            self.assertIn("issues/0001/0001-01/index.md", manifest["written"])
            self.assertEqual(manifest["source_commit"], sha)

    def test_mutation_guard_all_writes_under_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "root"
            manifest = self._import_fixture(dest)
            root = dest.resolve()
            for rel in manifest["written"] + ["import-manifest.json", "import-findings.json"]:
                path = (dest / rel).resolve()
                path.relative_to(root)


if __name__ == "__main__":
    unittest.main()
