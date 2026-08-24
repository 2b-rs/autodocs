#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_build_ledger.py — Focused tests for the tracked append-only build ledger
(Task 0043-02, decision DEC-0043-001).

Covers the three behaviours the Task's Definition of Done names explicitly:
append, no-rewrite, and malformed-entry detection — plus the wiring that makes
`build_report.py combine`/`publish` record exactly one entry per run.
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import build_ledger  # noqa: E402
import build_report  # noqa: E402


def make_combined(ref="run-archive/run-20260821T090000Z-n1", exit_code=0, findings=None):
    findings = [] if findings is None else findings
    return {
        "schema_version": "1.0",
        "report_kind": "combined",
        "tool": "build_report.py",
        "command": "build_report.py combine",
        "inputs": ["_src/"],
        "started_at": "2026-08-21T09:00:00Z",
        "finished_at": "2026-08-21T09:05:00Z",
        "duration_s": 300.0,
        "exit_code": exit_code,
        "changed_artifacts": [],
        "counts": {
            "by_stage": {
                "i18n_merge": {"batches_consumed": 1},
                "i18n_diagrams": {"sources_considered": 2},
                "html_generate": {"pages_generated_per_lang": {"de": 426}},
                "validate": {"checks_performed": 42, "success": exit_code == 0},
            },
            "overall_success": exit_code == 0,
        },
        "findings": findings,
        "run_archive_ref": ref,
    }


class LedgerTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = os.path.join(self.tmp.name, "evidence", "build-ledger.jsonl")

    def write_combined(self, combined, name="combined-1.json"):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(combined, fp, ensure_ascii=False, indent=1)
        return path

    def entry_for(self, combined, **kwargs):
        path = kwargs.pop("path", None) or self.write_combined(combined)
        return build_ledger.entry_from_combined(combined, path, **kwargs)


class TestAppend(LedgerTestCase):
    def test_appending_creates_the_ledger_and_one_line_per_run(self):
        for index, ref in enumerate(("run-archive/a", "run-archive/b", "manual-20260821T090000Z-deadbeef")):
            combined = make_combined(ref=ref)
            path = self.write_combined(combined, f"combined-{index}.json")
            status, _ = build_ledger.record_run(
                combined, path, path=self.ledger, repo_commit="a" * 40)
            self.assertEqual(status, "appended")

        with open(self.ledger, encoding="utf-8") as fp:
            raw = fp.read()
        self.assertTrue(raw.endswith("\n"))
        self.assertEqual(len(raw.splitlines()), 3)

        entries, findings = build_ledger.read_entries(self.ledger)
        self.assertEqual(findings, [])
        self.assertEqual([e["run_archive_ref"] for e in entries],
                         ["run-archive/a", "run-archive/b", "manual-20260821T090000Z-deadbeef"])

    def test_entry_carries_every_field_the_task_requires(self):
        combined = make_combined(findings=[
            {"category": "x", "severity": "warning", "message": "m"},
            {"category": "y", "severity": "info", "message": "m"},
        ])
        path = self.write_combined(combined)
        entry = build_ledger.entry_from_combined(combined, path, repo_commit="b" * 40)

        self.assertEqual(entry["run_started_at"], "2026-08-21T09:00:00Z")
        self.assertEqual(entry["run_archive_ref"], "run-archive/run-20260821T090000Z-n1")
        self.assertEqual(entry["repo_commit"], "b" * 40)
        self.assertEqual(entry["exit_code"], 0)
        self.assertTrue(entry["overall_success"])
        self.assertEqual(sorted(entry["counts_by_stage"]), sorted(build_ledger.REQUIRED_STAGES))
        self.assertEqual(entry["counts_by_stage"]["validate"]["checks_performed"], 42)
        self.assertEqual(entry["findings_count"], 2)
        self.assertEqual(entry["findings_by_severity"], {"info": 1, "warning": 1, "error": 0})
        self.assertEqual(entry["combined_report_digest"], build_ledger.sha256_file(path))
        self.assertFalse(entry["backfilled"])
        self.assertEqual(build_ledger.validate_entry(entry), [])

    def test_digest_pins_the_exact_combined_report_bytes(self):
        combined = make_combined()
        path = self.write_combined(combined)
        first = build_ledger.entry_from_combined(combined, path)["combined_report_digest"]
        with open(path, "a", encoding="utf-8") as fp:
            fp.write(" ")
        second = build_ledger.entry_from_combined(combined, path)["combined_report_digest"]
        self.assertNotEqual(first, second)

    def test_second_append_of_the_same_run_is_a_no_op(self):
        combined = make_combined()
        path = self.write_combined(combined)
        self.assertEqual(
            build_ledger.record_run(combined, path, path=self.ledger, repo_commit="c" * 40)[0],
            "appended")
        before = open(self.ledger, "rb").read()
        self.assertEqual(
            build_ledger.record_run(combined, path, path=self.ledger, repo_commit="c" * 40)[0],
            "duplicate")
        self.assertEqual(open(self.ledger, "rb").read(), before)

    def test_a_run_without_a_ref_is_refused_unless_backfilled(self):
        combined = make_combined(ref=None)
        path = self.write_combined(combined)
        with self.assertRaises(build_ledger.LedgerError):
            build_ledger.entry_from_combined(combined, path)
        entry = build_ledger.entry_from_combined(combined, path, backfilled=True)
        self.assertIsNone(entry["run_archive_ref"])
        self.assertTrue(entry["backfilled"])
        self.assertEqual(build_ledger.validate_entry(entry), [])

    def test_out_of_order_recorded_at_is_refused(self):
        combined = make_combined()
        path = self.write_combined(combined)
        newer = build_ledger.entry_from_combined(
            combined, path, recorded_at="2026-08-21T10:00:00Z")
        older = build_ledger.entry_from_combined(
            make_combined(ref="run-archive/older"), path, recorded_at="2026-08-20T10:00:00Z")
        build_ledger.append_entry(newer, self.ledger)
        with self.assertRaises(build_ledger.LedgerError):
            build_ledger.append_entry(older, self.ledger)


class TestNoRewrite(LedgerTestCase):
    """The ledger is append-only: existing bytes are never touched."""

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True,
                              text=True, check=True)

    def setUp(self):
        super().setUp()
        self.repo = self.tmp.name
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        self._git("config", "user.email", "t@example.invalid")
        self._git("config", "user.name", "Test")
        self.ledger = os.path.join(self.repo, "docs", "evidence", "build-ledger.jsonl")
        # build_ledger computes repo-relative refs against its own ROOT; for the
        # baseline comparison it only needs the path relative to `cwd`.
        self.rel = os.path.relpath(self.ledger, self.repo)

    def _commit_ledger(self):
        self._git("add", self.rel)
        self._git("commit", "-q", "-m", "ledger")

    def _verify_against_head(self):
        old_root = build_ledger.ROOT
        build_ledger.ROOT = self.repo
        try:
            return build_ledger.verify(self.ledger, baseline="HEAD", cwd=self.repo)
        finally:
            build_ledger.ROOT = old_root

    def test_pure_append_after_a_commit_verifies_clean(self):
        combined = make_combined(ref="run-archive/first")
        build_ledger.record_run(combined, self.write_combined(combined),
                                path=self.ledger, repo_commit="d" * 40)
        self._commit_ledger()

        later = make_combined(ref="run-archive/second")
        build_ledger.record_run(later, self.write_combined(later, "combined-2.json"),
                                path=self.ledger, repo_commit="e" * 40)

        entries, findings = self._verify_against_head()
        self.assertEqual(len(entries), 2)
        self.assertEqual([f for f in findings if f["severity"] == "error"], [])

    def test_rewriting_a_committed_entry_is_detected(self):
        combined = make_combined(
            ref="run-archive/first", exit_code=1,
            findings=[{"category": "broke", "severity": "error", "message": "build failed"}])
        build_ledger.record_run(combined, self.write_combined(combined),
                                path=self.ledger, repo_commit="d" * 40)
        self._commit_ledger()

        entries, _ = build_ledger.read_entries(self.ledger)
        tampered = copy.deepcopy(entries[0])
        # A green-washed rewrite: still perfectly schema-valid.
        tampered["exit_code"] = 0
        tampered["overall_success"] = True
        tampered["findings_count"] = 0
        tampered["findings_by_severity"] = {"info": 0, "warning": 0, "error": 0}
        self.assertEqual(build_ledger.validate_entry(tampered), [])
        with open(self.ledger, "w", encoding="utf-8") as fp:
            fp.write(json.dumps(tampered, ensure_ascii=False) + "\n")

        _, findings = self._verify_against_head()
        self.assertTrue(any(f["category"] == "rewritten-build-ledger"
                            and f["severity"] == "error" for f in findings),
                        f"expected a rewrite finding, got {findings}")

    def test_deleting_a_committed_entry_is_detected(self):
        for ref in ("run-archive/first", "run-archive/second"):
            combined = make_combined(ref=ref)
            build_ledger.record_run(combined, self.write_combined(combined, ref.replace("/", "_") + ".json"),
                                    path=self.ledger, repo_commit="d" * 40)
        self._commit_ledger()

        lines = open(self.ledger, encoding="utf-8").read().splitlines(keepends=True)
        with open(self.ledger, "w", encoding="utf-8") as fp:
            fp.write(lines[1])

        _, findings = self._verify_against_head()
        self.assertTrue(any(f["category"] == "rewritten-build-ledger" for f in findings))

    def test_append_uses_o_append_and_never_truncates(self):
        combined = make_combined(ref="run-archive/first")
        build_ledger.record_run(combined, self.write_combined(combined),
                                path=self.ledger, repo_commit="d" * 40)
        first_bytes = open(self.ledger, "rb").read()
        later = make_combined(ref="run-archive/second")
        build_ledger.record_run(later, self.write_combined(later, "c2.json"),
                                path=self.ledger, repo_commit="e" * 40)
        self.assertTrue(open(self.ledger, "rb").read().startswith(first_bytes))


class TestMalformedDetection(LedgerTestCase):
    def _write_lines(self, *lines):
        os.makedirs(os.path.dirname(self.ledger), exist_ok=True)
        with open(self.ledger, "w", encoding="utf-8") as fp:
            fp.write("".join(lines))

    def _valid_entry(self, ref="run-archive/ok"):
        combined = make_combined(ref=ref)
        return build_ledger.entry_from_combined(
            combined, self.write_combined(combined, ref.replace("/", "_") + ".json"),
            repo_commit="f" * 40)

    def test_unparsable_line_is_reported_and_does_not_hide_the_rest(self):
        good = json.dumps(self._valid_entry()) + "\n"
        self._write_lines(good, "{not json\n")
        entries, findings = build_ledger.read_entries(self.ledger)
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["category"], "malformed-build-ledger")
        self.assertIn("Line 2", findings[0]["message"])

    def test_missing_trailing_newline_is_reported(self):
        self._write_lines(json.dumps(self._valid_entry()))
        _, findings = build_ledger.read_entries(self.ledger)
        self.assertTrue(any("newline" in f["message"] for f in findings))

    def test_blank_line_is_reported(self):
        self._write_lines(json.dumps(self._valid_entry()) + "\n", "\n")
        _, findings = build_ledger.read_entries(self.ledger)
        self.assertTrue(any("blank" in f["message"] for f in findings))

    def test_schema_violations_are_named_individually(self):
        cases = {
            "schema_version": ("schema_version", "9.9"),
            "entry_kind": ("entry_kind", "nonsense"),
            "recorded_at": ("recorded_at", "2026-08-21 09:00"),
            "run_archive_ref": ("run_archive_ref", "   "),
            "repo_commit": ("repo_commit", "not-a-sha"),
            "exit_code": ("exit_code", 999),
            "overall_success": ("overall_success", "yes"),
            "counts_by_stage": ("counts_by_stage", {"validate": {}}),
            "findings_count": ("findings_count", -1),
            "combined_report_digest": ("combined_report_digest", "sha256:xyz"),
            "combined_report_ref": ("combined_report_ref", ""),
            "backfilled": ("backfilled", "false"),
        }
        for label, (field, value) in cases.items():
            with self.subTest(field=label):
                entry = self._valid_entry()
                entry[field] = value
                errors = build_ledger.validate_entry(entry)
                self.assertTrue(errors, f"{field}={value!r} should not validate")
                self.assertTrue(any(field in err for err in errors), errors)

    def test_missing_required_field_is_reported(self):
        entry = self._valid_entry()
        del entry["combined_report_digest"]
        self.assertIn("missing required field 'combined_report_digest'",
                      build_ledger.validate_entry(entry))

    def test_overall_success_must_agree_with_exit_code(self):
        entry = self._valid_entry()
        entry["exit_code"] = 1
        self.assertIn("overall_success must agree with exit_code == 0",
                      build_ledger.validate_entry(entry))

    def test_null_ref_outside_a_backfilled_entry_is_rejected(self):
        entry = self._valid_entry()
        entry["run_archive_ref"] = None
        self.assertIn("run_archive_ref may only be null on a backfilled entry",
                      build_ledger.validate_entry(entry))

    def test_appending_to_a_defective_ledger_is_refused(self):
        self._write_lines("{broken\n")
        entry = self._valid_entry()
        with self.assertRaises(build_ledger.LedgerError):
            build_ledger.append_entry(entry, self.ledger)

    def test_appending_a_malformed_entry_is_refused_and_leaves_no_trace(self):
        entry = self._valid_entry()
        entry["exit_code"] = "zero"
        with self.assertRaises(build_ledger.LedgerError):
            build_ledger.append_entry(entry, self.ledger)
        self.assertFalse(os.path.exists(self.ledger))

    def test_verify_reports_duplicate_run_refs(self):
        entry = self._valid_entry()
        self._write_lines(json.dumps(entry) + "\n", json.dumps(entry) + "\n")
        _, findings = build_ledger.verify(self.ledger)
        self.assertTrue(any(f["category"] == "duplicate-build-ledger-entry" for f in findings))

    def test_verify_warns_about_a_late_backfilled_entry(self):
        first = self._valid_entry("run-archive/one")
        second = self._valid_entry("run-archive/two")
        second["backfilled"] = True
        self._write_lines(json.dumps(first) + "\n", json.dumps(second) + "\n")
        _, findings = build_ledger.verify(self.ledger)
        self.assertTrue(any(f["severity"] == "warning" and "backfilled" in f["message"]
                            for f in findings))


class TestBuildReportWiring(LedgerTestCase):
    """`combine`/`publish` write the ledger; `--no-ledger` opts out."""

    def test_combine_records_the_run_once(self):
        combined = make_combined(ref="run-archive/wired")
        path = self.write_combined(combined)
        ok, message = build_report.record_in_ledger(combined, path, ledger_path=self.ledger)
        self.assertTrue(ok, message)
        self.assertIn("ergaenzt", message)

        ok, message = build_report.record_in_ledger(combined, path, ledger_path=self.ledger)
        self.assertTrue(ok)
        self.assertIn("bereits verzeichnet", message)
        self.assertEqual(len(build_ledger.read_entries(self.ledger)[0]), 1)

    def test_a_failed_append_is_reported_not_swallowed(self):
        combined = make_combined(ref=None)  # uncorrelated: cannot be recorded
        path = self.write_combined(combined)
        ok, message = build_report.record_in_ledger(combined, path, ledger_path=self.ledger)
        self.assertFalse(ok)
        self.assertIn("NICHT aktualisiert", message)

    def test_failed_ledger_append_makes_combine_exit_nonzero(self):
        # An otherwise green run whose evidence could not be recorded is not green.
        combined = make_combined(ref=None)
        path = self.write_combined(combined)
        self.assertEqual(combined["exit_code"], 0)
        ok, _ = build_report.record_in_ledger(combined, path, ledger_path=self.ledger)
        self.assertFalse(ok)

    def test_cli_no_ledger_flag_is_recognised(self):
        self.assertIn("--no-ledger", build_report.__doc__)


class TestCommittedLedger(unittest.TestCase):
    """The ledger that is actually checked in must be conforming."""

    def test_repository_ledger_verifies(self):
        entries, findings = build_ledger.verify()
        errors = [f for f in findings if f["severity"] == "error"]
        self.assertEqual(errors, [], f"committed ledger has defects: {errors}")
        self.assertGreaterEqual(len(entries), 1, "the historic run must be backfilled")
        self.assertTrue(entries[0]["backfilled"],
                        "the first ledger entry is the backfilled historic run")


if __name__ == "__main__":
    unittest.main()
