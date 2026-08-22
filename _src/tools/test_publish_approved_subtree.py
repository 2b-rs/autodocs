#!/usr/bin/env python3
"""Tests for _src/tools/publish_approved_subtree.py (stdlib unittest only).

Run:  python3 -m unittest discover -s _src/tools -p 'test_publish_approved_subtree.py' -v
  or: python3 _src/tools/test_publish_approved_subtree.py
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import publish_approved_subtree as tool  # noqa: E402


def snapshot(root: Path) -> dict:
    """Full byte-level snapshot of a tree: relative path -> file bytes."""
    captured = {}
    for directory, subdirectories, names in os.walk(root, followlinks=False):
        subdirectories.sort()
        for name in sorted(names):
            absolute = Path(directory) / name
            captured[absolute.relative_to(root).as_posix()] = absolute.read_bytes()
    return captured


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Harness(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.base = Path(self._temporary.name)
        self.source = self.base / "source"
        self.destination_root = self.base / "destination"
        self.evidence = self.base / "evidence.json"
        self.journal = self.base / "journal.jsonl"
        self.subtree = "campaign/report"
        write(self.source / "index.html", "<p>approved</p>\n")
        write(self.source / "records" / "a.html", "<p>a</p>\n")
        write(self.source / "records" / "b.html", "<p>b</p>\n")
        self.destination_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def digest(self) -> str:
        return tool.compute_tree_digest(self.source)[0]

    def invoke(self, *extra: str, digest: str = None, mode: str = "--apply"):
        stream = io.StringIO()
        argv = [
            "--source", str(self.source),
            "--destination-root", str(self.destination_root),
            "--subtree", self.subtree,
            "--expected-tree-digest", digest if digest is not None else self.digest(),
            "--authorization-ref", "DEC-TEST-001@abcdef1",
            mode,
        ]
        argv.extend(extra)
        code = tool.run(argv, stream=stream)
        return code, stream.getvalue()


class DigestProcedure(Harness):
    def test_digest_reproduces_documented_procedure_by_hand(self):
        """The tool's digest must equal an independent hand computation."""
        relatives = sorted(
            path.relative_to(self.source).as_posix()
            for path in self.source.rglob("*")
            if path.is_file()
        )
        stream = b""
        for relative in relatives:
            contents = (self.source / relative).read_bytes()
            stream += relative.encode("utf-8") + b"\0" + hashlib.sha256(contents).digest()
        self.assertEqual(hashlib.sha256(stream).hexdigest(), self.digest())

    def test_digest_match_publishes_the_subtree(self):
        code, report = self.invoke("--evidence", str(self.evidence), "--journal", str(self.journal))
        self.assertEqual(code, tool.EXIT_OK, report)
        published = self.destination_root / "campaign" / "report"
        self.assertEqual(
            sorted(snapshot(published)),
            ["index.html", "records/a.html", "records/b.html"],
        )
        self.assertEqual((published / "records" / "a.html").read_text(encoding="utf-8"), "<p>a</p>\n")
        evidence = json.loads(self.evidence.read_text(encoding="utf-8"))
        self.assertTrue(evidence["published"])
        self.assertEqual(evidence["authorization_ref"], "DEC-TEST-001@abcdef1")
        self.assertEqual(evidence["published_tree_digest"], self.digest())
        self.assertEqual(evidence["digest_procedure"], tool.DIGEST_PROCEDURE)

    def test_digest_mismatch_refuses_and_writes_nothing(self):
        before = snapshot(self.destination_root)
        wrong = "0" * 64
        code, report = self.invoke(
            "--evidence", str(self.evidence), digest=wrong,
        )
        self.assertEqual(code, tool.EXIT_REFUSED, report)
        self.assertIn("digest matches    : NO", report)
        self.assertEqual(snapshot(self.destination_root), before)
        self.assertFalse((self.destination_root / "campaign").exists())
        self.assertFalse(self.evidence.exists())

    def test_source_change_between_plan_and_write_is_refused(self):
        """The gate is re-evaluated immediately before the first write."""
        approved = self.digest()

        original_apply = tool.apply_plan

        def mutate_then_apply(plan, source, *args, **kwargs):
            write(source / "records" / "c.html", "<p>smuggled</p>\n")
            return original_apply(plan, source, *args, **kwargs)

        tool.apply_plan = mutate_then_apply
        try:
            code, report = self.invoke("--evidence", str(self.evidence), digest=approved)
        finally:
            tool.apply_plan = original_apply
        self.assertEqual(code, tool.EXIT_REFUSED, report)
        self.assertFalse((self.destination_root / "campaign").exists())


class DestinationIsolation(Harness):
    def populate_unrelated(self) -> dict:
        write(self.destination_root / "index.html", "<p>whole site landing page</p>\n")
        write(self.destination_root / "en" / "index.html", "<p>english</p>\n")
        write(self.destination_root / "campaign" / "other" / "keep.html", "<p>sibling</p>\n")
        write(self.destination_root / "style.css", "body{}\n")
        return snapshot(self.destination_root)

    def test_unrelated_destination_content_survives_byte_identically(self):
        """The single most important guarantee of this tool."""
        before = self.populate_unrelated()
        code, report = self.invoke("--evidence", str(self.evidence), "--journal", str(self.journal))
        self.assertEqual(code, tool.EXIT_OK, report)
        after = snapshot(self.destination_root)
        unrelated_after = {
            name: data for name, data in after.items() if not name.startswith("campaign/report/")
        }
        self.assertEqual(unrelated_after, before)
        self.assertIn("campaign/report/index.html", after)

    def test_second_run_leaves_unrelated_content_untouched(self):
        self.invoke("--evidence", str(self.evidence), "--journal", str(self.journal))
        self.populate_unrelated()
        before = {
            name: data
            for name, data in snapshot(self.destination_root).items()
            if not name.startswith("campaign/report/")
        }
        second_evidence = self.base / "evidence-2.json"
        code, report = self.invoke("--evidence", str(second_evidence))
        self.assertEqual(code, tool.EXIT_OK, report)
        after = snapshot(self.destination_root)
        unrelated_after = {
            name: data for name, data in after.items() if not name.startswith("campaign/report/")
        }
        self.assertEqual(unrelated_after, before)

    def test_subtree_escape_is_refused(self):
        for escape in ("../outside", "/absolute", "campaign/../../outside", ".", ""):
            stream = io.StringIO()
            code = tool.run(
                [
                    "--source", str(self.source),
                    "--destination-root", str(self.destination_root),
                    "--subtree", escape,
                    "--expected-tree-digest", self.digest(),
                    "--authorization-ref", "REF",
                    "--dry-run",
                ],
                stream=stream,
            )
            self.assertEqual(code, tool.EXIT_REFUSED, f"escape accepted: {escape!r}")

    def test_source_destination_overlap_is_refused(self):
        stream = io.StringIO()
        code = tool.run(
            [
                "--source", str(self.destination_root / "campaign" / "report"),
                "--destination-root", str(self.destination_root),
                "--subtree", self.subtree,
                "--expected-tree-digest", "a" * 64,
                "--authorization-ref", "REF",
                "--dry-run",
            ],
            stream=stream,
        )
        self.assertEqual(code, tool.EXIT_REFUSED)


class DeletionReporting(Harness):
    def test_in_subtree_deletion_is_reported_before_it_is_performed(self):
        self.invoke("--evidence", str(self.evidence), "--journal", str(self.journal))
        published = self.destination_root / "campaign" / "report"
        write(published / "records" / "obsolete.html", "<p>withdrawn</p>\n")
        write(published / "records" / "nested" / "deep.html", "<p>withdrawn</p>\n")
        self.assertTrue((published / "records" / "obsolete.html").exists())

        second_evidence = self.base / "evidence-2.json"
        code, report = self.invoke(
            "--evidence", str(second_evidence), "--journal", str(self.journal)
        )
        self.assertEqual(code, tool.EXIT_OK, report)

        self.assertIn("deletions to be performed inside campaign/report (2)", report)
        self.assertIn("D campaign/report/records/obsolete.html", report)
        self.assertIn("D campaign/report/records/nested/deep.html", report)
        announcement = report.index("deletions to be performed")
        completion = report.index("publication complete")
        self.assertLess(announcement, completion)

        self.assertFalse((published / "records" / "obsolete.html").exists())
        self.assertFalse((published / "records" / "nested").exists())

        evidence = json.loads(second_evidence.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(evidence["removed"]),
            ["records/nested/deep.html", "records/obsolete.html"],
        )
        journal = [
            json.loads(line)
            for line in self.journal.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        deletes = [entry for entry in journal if entry["phase"] == "delete"]
        self.assertEqual(len(deletes), 2)
        self.assertTrue(all(entry["task_id"] == "DEC-TEST-001@abcdef1" for entry in deletes))

    def test_deletion_never_reaches_outside_the_subtree(self):
        write(self.destination_root / "campaign" / "sibling.html", "<p>sibling</p>\n")
        before = snapshot(self.destination_root)
        code, report = self.invoke("--evidence", str(self.evidence))
        self.assertEqual(code, tool.EXIT_OK, report)
        self.assertEqual(
            (self.destination_root / "campaign" / "sibling.html").read_bytes(),
            before["campaign/sibling.html"],
        )


class PrivatePathGuard(Harness):
    def test_private_subtree_is_refused(self):
        for private in ("_src", "output", ".git", "en/_src/x", "docs/output"):
            stream = io.StringIO()
            code = tool.run(
                [
                    "--source", str(self.source),
                    "--destination-root", str(self.destination_root),
                    "--subtree", private,
                    "--expected-tree-digest", self.digest(),
                    "--authorization-ref", "REF",
                    "--dry-run",
                ],
                stream=stream,
            )
            self.assertEqual(code, tool.EXIT_REFUSED, f"private subtree accepted: {private}")

    def test_private_path_inside_the_source_is_refused(self):
        write(self.source / "_src" / "generate.py", "print('private')\n")
        code, report = self.invoke("--evidence", str(self.evidence))
        self.assertEqual(code, tool.EXIT_REFUSED, report)
        self.assertFalse((self.destination_root / "campaign").exists())

    def test_gitignore_in_the_source_is_refused(self):
        write(self.source / ".gitignore", "output/\n")
        code, report = self.invoke("--evidence", str(self.evidence))
        self.assertEqual(code, tool.EXIT_REFUSED, report)
        self.assertFalse((self.destination_root / "campaign").exists())

    def test_symlink_in_the_source_is_refused(self):
        approved = self.digest()
        outside = self.base / "outside.html"
        outside.write_text("<p>outside</p>\n", encoding="utf-8")
        os.symlink(outside, self.source / "link.html")
        code, report = self.invoke("--evidence", str(self.evidence), digest=approved)
        self.assertEqual(code, tool.EXIT_REFUSED, report)
        self.assertFalse((self.destination_root / "campaign").exists())

    def test_no_embedded_destination_identity_or_credential_default(self):
        text = Path(tool.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "git@", "https://", "ssh -i", "id_ed25519", "@gmail", "refs/heads/",
            "publish_remote", "publish_identity", "subprocess", "git_ssh_command",
        ):
            self.assertNotIn(forbidden, text.lower(), f"embedded default found: {forbidden}")
        for required in ("--source", "--destination-root", "--subtree", "--authorization-ref"):
            self.assertIn(required, text)


class DryRun(Harness):
    def test_dry_run_reports_complete_intended_effect_and_writes_nothing(self):
        published = self.destination_root / "campaign" / "report"
        write(published / "index.html", "<p>stale</p>\n")
        write(published / "obsolete.html", "<p>withdrawn</p>\n")
        write(self.destination_root / "unrelated.html", "<p>unrelated</p>\n")
        before = snapshot(self.destination_root)

        code, report = self.invoke(
            "--evidence", str(self.evidence), mode="--dry-run"
        )
        self.assertEqual(code, tool.EXIT_OK, report)

        self.assertIn("mode=dry-run", report)
        self.assertIn("authorization_ref : DEC-TEST-001@abcdef1", report)
        self.assertIn("digest matches    : yes", report)
        self.assertIn("digest procedure  :", report)
        self.assertIn("created=2", report)
        self.assertIn("modified=1", report)
        self.assertIn("deleted=1", report)
        self.assertIn("unchanged=0", report)
        self.assertIn("C campaign/report/records/a.html", report)
        self.assertIn("M campaign/report/index.html", report)
        self.assertIn("D campaign/report/obsolete.html", report)
        self.assertIn("dry-run complete: nothing was written", report)

        self.assertEqual(snapshot(self.destination_root), before)

        evidence = json.loads(self.evidence.read_text(encoding="utf-8"))
        self.assertEqual(evidence["mode"], "dry-run")
        self.assertFalse(evidence["published"])
        self.assertEqual(evidence["counts"]["created"], 2)
        self.assertEqual(evidence["deleted"], ["obsolete.html"])
        self.assertEqual(evidence["expected_tree_digest"], self.digest())

    def test_dry_run_sample_is_bounded_and_the_remainder_is_disclosed(self):
        for index in range(25):
            write(self.source / "bulk" / f"page-{index:02d}.html", f"<p>{index}</p>\n")
        code, report = self.invoke("--sample", "3", mode="--dry-run")
        self.assertEqual(code, tool.EXIT_OK, report)
        self.assertIn("created (28), showing 3:", report)
        self.assertIn("... 25 more (full list in the evidence record)", report)

    def test_apply_requires_evidence(self):
        code, report = self.invoke()
        self.assertEqual(code, tool.EXIT_REFUSED, report)
        self.assertFalse((self.destination_root / "campaign").exists())

    def test_existing_evidence_is_never_overwritten(self):
        self.evidence.write_text("{}\n", encoding="utf-8")
        code, report = self.invoke("--evidence", str(self.evidence))
        self.assertEqual(code, tool.EXIT_REFUSED, report)
        self.assertEqual(self.evidence.read_text(encoding="utf-8"), "{}\n")

    def test_evidence_and_journal_may_not_live_inside_the_published_subtree(self):
        inside = self.destination_root / "campaign" / "report" / "evidence.json"
        code, report = self.invoke("--evidence", str(inside))
        self.assertEqual(code, tool.EXIT_REFUSED, report)

    def test_authorization_reference_is_required_and_non_empty(self):
        stream = io.StringIO()
        code = tool.run(
            [
                "--source", str(self.source),
                "--destination-root", str(self.destination_root),
                "--subtree", self.subtree,
                "--expected-tree-digest", self.digest(),
                "--authorization-ref", "   ",
                "--dry-run",
            ],
            stream=stream,
        )
        self.assertEqual(code, tool.EXIT_REFUSED)

    def test_malformed_digest_argument_is_refused(self):
        for bad in ("abc", "z" * 64, ""):
            code, report = self.invoke(digest=bad, mode="--dry-run")
            self.assertEqual(code, tool.EXIT_REFUSED, f"accepted digest {bad!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
