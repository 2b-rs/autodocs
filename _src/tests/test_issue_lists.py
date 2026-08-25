"""Tests for generated TODO.md / DONE.md / summaries (Task 0037-11.01)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("issue_lists", ROOT / "_src/tools/issue_lists.py")
LISTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LISTS)
FIXTURES = ROOT / "_src/tests/fixtures/0037-11.01"
ISSUES = FIXTURES / "issues"
GOLDEN = FIXTURES / "generated"


class IssueListsTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.catalog, self.groups, self.documents = LISTS.render_lists(ISSUES, ROOT)

    def test_byte_determinism_repeated_runs(self):
        second = LISTS.render_lists(ISSUES, ROOT)[2]
        for kind in self.documents:
            self.assertEqual(self.documents[kind], second[kind])
        self.assertNotIn("run_id", self.documents["todo"])
        self.assertIn("GENERATED-VIEW", self.documents["todo"])
        self.assertIn(self.catalog["generation_id"], self.documents["todo"])

    def test_golden_and_reconciliation(self):
        GOLDEN.mkdir(parents=True, exist_ok=True)
        written, manifest = LISTS.write_lists(self.documents, GOLDEN, ROOT, run_id="fixture-run")
        self.assertTrue(manifest["run_id"])
        self.assertNotIn(manifest["run_id"], self.documents["todo"])
        LISTS.verify_lists(GOLDEN, ISSUES, ROOT)
        todo_ids = {item["id"] for item in self.groups["todo"]}
        done_ids = {item["id"] for item in self.groups["done"]}
        unclear_ids = {item["id"] for item in self.groups["unclear"]}
        all_ids = {item["id"] for item in self.catalog["items"]}
        self.assertEqual(todo_ids | done_ids | unclear_ids, all_ids)
        self.assertIn("0081", todo_ids)
        self.assertIn("0081-01", todo_ids)
        self.assertIn("0081-02", todo_ids)
        self.assertIn("0082", done_ids)
        self.assertIn("0081-04", done_ids)
        self.assertIn("0081-03", unclear_ids)
        self.assertIn("AC-001", self.documents["todo"])
        self.assertIn("archived-not-accepted", self.documents["done"])
        self.assertIn("**gabriel**: 0081-01", self.documents["owners"])
        for kind, rel in LISTS.OUTPUT_NAMES.items():
            if kind == "manifest":
                continue
            self.assertEqual((GOLDEN / rel).read_text(encoding="utf-8"), self.documents[kind])
        self.assertIn("generated", written["todo"])

    def test_refuses_live_todo_done(self):
        with self.assertRaises(LISTS.IssueListsError):
            LISTS.refuse_live_authority_path(ROOT / "TODO.md", ROOT)
        with self.assertRaises(LISTS.IssueListsError):
            LISTS.refuse_live_authority_path(ROOT / "DONE.md", ROOT)
        with tempfile.TemporaryDirectory() as temp:
            live = Path(temp)
            (live / "TODO.md").write_text("legacy", encoding="utf-8")
            (live / "DONE.md").write_text("legacy", encoding="utf-8")
            with self.assertRaises(LISTS.IssueListsError):
                LISTS.write_lists(self.documents, live, live)
            self.assertEqual(LISTS.main([
                "--repository-root", str(ROOT),
                "--issues-root", str(ISSUES),
                "--output-root", str(ROOT),
                "--write",
            ]), 2)

    def test_divergence_omission_duplicate_false_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out"
            LISTS.write_lists(self.documents, out, ROOT, run_id="t")
            todo = out / "TODO.md"
            text = todo.read_text(encoding="utf-8")
            todo.write_text(text.replace("0081-01", "hand-edited", 1), encoding="utf-8")
            with self.assertRaises(LISTS.IssueListsError) as ctx:
                LISTS.verify_lists(out, ISSUES, ROOT)
            self.assertIn("divergence", str(ctx.exception))
            LISTS.write_lists(self.documents, out, ROOT, run_id="t2")
            # omission: drop a terminal item from DONE
            done = out / "DONE.md"
            done.write_text(self.documents["done"].replace(_line_for("0082"), ""), encoding="utf-8")
            with self.assertRaises(LISTS.IssueListsError):
                LISTS.verify_lists(out, ISSUES, ROOT)
        catalog, groups, documents = LISTS.render_lists(ISSUES, ROOT)
        fake = dict(catalog)
        fake["items"] = list(catalog["items"]) + [dict(catalog["items"][0])]
        with self.assertRaises(LISTS.IssueListsError) as dup:
            LISTS.classify(fake)
        self.assertIn("duplicated", str(dup.exception))
        groups["done"].append({"id": "0081-01", "state": "open", "title": "x"})
        with self.assertRaises(LISTS.IssueListsError) as false_c:
            _check_false(groups)
        self.assertIn("false completion", str(false_c.exception))

    def test_cli_write_verify_twice(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "gen"
            argv = [
                "--repository-root", str(ROOT),
                "--issues-root", str(ISSUES),
                "--output-root", str(out),
                "--write",
                "--verify",
            ]
            self.assertEqual(LISTS.main(argv), 0)
            self.assertEqual(LISTS.main(argv), 0)
            first = (out / "TODO.md").read_text(encoding="utf-8")
            self.assertEqual(LISTS.main(argv), 0)
            self.assertEqual((out / "TODO.md").read_text(encoding="utf-8"), first)


def _line_for(item_id):
    catalog, groups, documents = LISTS.render_lists(ISSUES, ROOT)
    for item in groups["done"]:
        if item["id"] == item_id:
            return LISTS._item_line(item)
    raise AssertionError(item_id)


def _check_false(groups):
    for item in groups["done"]:
        if item.get("state") not in LISTS.TERMINAL:
            raise LISTS.IssueListsError(f"false completion: {item['id']} is not terminal")


if __name__ == "__main__":
    unittest.main()
