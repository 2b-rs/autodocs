#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_build_report.py — Tests and fixtures for build report combination and page publishing (Task 0001-10).
"""
import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import build_report
import build_ledger


class TestBuildReport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_reports_dir = build_report.REPORTS_DIR
        self.orig_page_model = build_report.PAGE_MODEL
        build_report.REPORTS_DIR = os.path.join(self.test_dir, "build-reports")
        build_report.PAGE_MODEL = os.path.join(self.test_dir, "build-reports.json")
        os.makedirs(build_report.REPORTS_DIR, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        build_report.REPORTS_DIR = self.orig_reports_dir
        build_report.PAGE_MODEL = self.orig_page_model

    def _write_report(
        self, kind, run_archive_ref, suffix, mtime, counts=None, overrides=None, missing=()
    ):
        report = {
            "schema_version": "1.0",
            "report_kind": kind,
            "tool": f"{kind}.py",
            "command": kind,
            "inputs": [f"input-{suffix}"],
            "started_at": "2026-08-14T15:00:00Z",
            "finished_at": "2026-08-14T15:00:01Z",
            "duration_s": 1.0,
            "exit_code": 0,
            "changed_artifacts": [],
            "counts": {} if counts is None else counts,
            "findings": [],
            "run_archive_ref": run_archive_ref,
        }
        if overrides is not None:
            report.update(overrides)
        for field in missing:
            report.pop(field, None)
        path = Path(build_report.REPORTS_DIR) / f"{kind}-{suffix}.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        os.utime(path, (mtime, mtime))
        return path

    def test_combine_reports_schema_stability(self):
        # Create subreports
        ts = int(time.time())
        merge_rep = {
            "schema_version": "1.0",
            "report_kind": "i18n_merge",
            "tool": "i18n_translate.py",
            "command": "i18n_translate.py merge en",
            "inputs": ["_src/i18n/en/batches/batch_01.json"],
            "started_at": "2026-08-14T15:00:00Z",
            "finished_at": "2026-08-14T15:00:05Z",
            "duration_s": 5.0,
            "exit_code": 0,
            "changed_artifacts": ["_src/i18n/en/segments.json"],
            "counts": {"batches_consumed": 1, "accepted": 10, "rejected": 0, "register_changes": 10},
            "findings": [],
            "run_archive_ref": "output/run-archive/run-test.sh",
        }
        with open(os.path.join(build_report.REPORTS_DIR, f"i18n_merge-{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(merge_rep, f)

        val_rep = {
            "schema_version": "1.0",
            "report_kind": "validate",
            "tool": "validate.py",
            "command": "validate.py",
            "inputs": ["_src/"],
            "started_at": "2026-08-14T15:00:10Z",
            "finished_at": "2026-08-14T15:00:15Z",
            "duration_s": 5.0,
            "exit_code": 0,
            "changed_artifacts": [],
            "counts": {"checks_performed": 10, "findings_by_category": {}, "success": True},
            "findings": [{"category": "notice", "severity": "info", "message": "all good", "ref": "root"}],
            "run_archive_ref": "output/run-archive/run-test.sh",
        }
        with open(os.path.join(build_report.REPORTS_DIR, f"validate-{ts}.json"), "w", encoding="utf-8") as f:
            json.dump(val_rep, f)

        for kind, counts in (
            ("i18n_diagrams", {"sources_considered": 2}),
            ("html_generate", {"pages_generated_per_lang": {"de": 4}}),
        ):
            report = {
                "schema_version": "1.0",
                "report_kind": kind,
                "tool": f"{kind}.py",
                "command": kind,
                "inputs": [],
                "started_at": "2026-08-14T15:00:06Z",
                "finished_at": "2026-08-14T15:00:09Z",
                "duration_s": 3.0,
                "exit_code": 0,
                "changed_artifacts": [],
                "counts": counts,
                "findings": [],
                "run_archive_ref": "output/run-archive/run-test.sh",
            }
            with open(os.path.join(build_report.REPORTS_DIR, f"{kind}-{ts}.json"), "w", encoding="utf-8") as f:
                json.dump(report, f)

        combined, out_path = build_report.combine_reports("output/run-archive/run-test.sh")
        self.assertEqual(combined["schema_version"], "1.0")
        self.assertEqual(combined["report_kind"], "combined")
        self.assertTrue(combined["counts"]["overall_success"])
        self.assertEqual(combined["run_archive_ref"], "output/run-archive/run-test.sh")
        self.assertEqual(len(combined["findings"]), 1)
        self.assertIn("i18n_merge", combined["counts"]["by_stage"])
        self.assertIn("validate", combined["counts"]["by_stage"])

        # Test page model generation
        page_path = build_report.generate_report_page(combined, "output/run-archive/run-test.sh")
        self.assertTrue(os.path.exists(page_path))
        with open(page_path, encoding="utf-8") as f:
            pdata = json.load(f)
        self.assertEqual(pdata["file"], "build-reports.html")
        self.assertTrue(pdata["nolang"])
        self.assertIn("Traceable Build- &amp; Publikations-Report", pdata["main"][0]["html"].replace("& ", "&amp; "))

    def test_valid_exact_cohort_passes_strict_envelope_validation(self):
        run_ref = "output/run-archive/valid-run"
        for offset, kind in enumerate(build_report.REQUIRED_STAGES):
            self._write_report(kind, run_ref, f"valid-{offset}", 1_700_000_000 + offset)

        combined, _ = build_report.combine_reports(run_ref)

        self.assertEqual(combined["exit_code"], 0)
        self.assertTrue(combined["counts"]["overall_success"])
        self.assertEqual(combined["run_archive_ref"], run_ref)
        self.assertEqual(set(combined["counts"]["by_stage"]), set(build_report.REQUIRED_STAGES))
        self.assertFalse(
            any(item["category"] in {"malformed-build-report", "missing-build-stage"}
                for item in combined["findings"])
        )

    def test_malformed_exact_cohort_members_are_excluded_and_fail_closed(self):
        run_ref = "output/run-archive/malformed-run"
        base_mtime = 1_700_000_000
        self._write_report(
            "i18n_merge",
            run_ref,
            "malformed-merge",
            base_mtime,
            overrides={
                "tool": " ",
                "started_at": "2026-08-14 15:00:00Z",
                "finished_at": "2026-08-14T15:00:01+00:00",
            },
            missing=("schema_version",),
        )
        self._write_report(
            "i18n_diagrams",
            run_ref,
            "malformed-diagrams",
            base_mtime + 1,
            overrides={
                "command": "",
                "inputs": ["valid", 7],
                "changed_artifacts": [None],
                "finished_at": "2026-08-14T14:59:59Z",
            },
        )
        self._write_report(
            "html_generate",
            run_ref,
            "malformed-generate",
            base_mtime + 2,
            overrides={
                "duration_s": -1,
                "exit_code": 256,
                "counts": [],
                "findings": "not-a-list",
            },
        )
        self._write_report(
            "validate",
            run_ref,
            "malformed-validate",
            base_mtime + 3,
            overrides={
                "report_kind": "unknown",
                "exit_code": 3,
                "findings": [
                    {"category": "", "severity": "fatal", "message": "", "ref": 7}
                ],
            },
        )

        combined, _ = build_report.combine_reports(run_ref)

        self.assertEqual(combined["run_archive_ref"], run_ref)
        self.assertNotEqual(combined["exit_code"], 0)
        self.assertFalse(combined["counts"]["overall_success"])
        self.assertEqual(combined["inputs"], [])
        malformed = [
            item for item in combined["findings"]
            if item["category"] == "malformed-build-report"
        ]
        self.assertEqual(len(malformed), len(build_report.REQUIRED_STAGES))
        details = "\n".join(item["message"] for item in malformed)
        for field in (
            "schema_version",
            "report_kind",
            "tool",
            "command",
            "inputs",
            "started_at",
            "finished_at",
            "duration_s",
            "exit_code",
            "changed_artifacts",
            "counts",
            "findings",
            "nonzero exit_code",
        ):
            with self.subTest(field=field):
                self.assertIn(field, details)
        self.assertEqual(
            {item["ref"] for item in combined["findings"]
             if item["category"] == "missing-build-stage"},
            set(build_report.REQUIRED_STAGES),
        )
        self.assertTrue(all(not counts for counts in combined["counts"]["by_stage"].values()))

    def test_explicit_ref_does_not_relabel_stale_successful_reports(self):
        old_ref = "output/run-archive/old-run"
        current_ref = "output/run-archive/current-run"
        for offset, kind in enumerate(build_report.REQUIRED_STAGES):
            self._write_report(kind, old_ref, f"old-{offset}", 1_700_000_000 + offset)

        with mock.patch.dict(os.environ, {"RUN_ARCHIVE_REF": old_ref}):
            combined, _ = build_report.combine_reports(current_ref)

        self.assertEqual(combined["run_archive_ref"], current_ref)
        self.assertNotEqual(combined["exit_code"], 0)
        self.assertFalse(combined["counts"]["overall_success"])
        self.assertEqual(combined["inputs"], [])
        missing = [item for item in combined["findings"] if item["category"] == "missing-build-stage"]
        self.assertEqual({item["ref"] for item in missing}, set(build_report.REQUIRED_STAGES))
        self.assertTrue(all(current_ref in item["message"] for item in missing))

    def test_environment_ref_filters_exact_matches(self):
        old_ref = "output/run-archive/old-run"
        current_ref = "output/run-archive/current-run"
        for offset, kind in enumerate(build_report.REQUIRED_STAGES):
            self._write_report(kind, old_ref, f"old-{offset}", 1_700_000_000 + offset)

        with mock.patch.dict(os.environ, {"RUN_ARCHIVE_REF": current_ref}):
            combined, _ = build_report.combine_reports()

        self.assertEqual(combined["run_archive_ref"], current_ref)
        self.assertNotEqual(combined["exit_code"], 0)
        self.assertEqual(
            {item["ref"] for item in combined["findings"] if item["category"] == "missing-build-stage"},
            set(build_report.REQUIRED_STAGES),
        )

    def test_infers_newest_nonempty_cohort_without_mixing_stages(self):
        old_ref = "output/run-archive/old-run"
        current_ref = "output/run-archive/current-run"
        for offset, kind in enumerate(build_report.REQUIRED_STAGES):
            self._write_report(kind, old_ref, f"old-{offset}", 1_700_000_000 + offset)
        self._write_report(
            "validate",
            current_ref,
            "current",
            1_700_000_100,
            counts={"cohort": "current"},
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            combined, _ = build_report.combine_reports()

        self.assertEqual(combined["run_archive_ref"], current_ref)
        self.assertNotEqual(combined["exit_code"], 0)
        self.assertEqual(combined["counts"]["by_stage"]["validate"], {"cohort": "current"})
        missing = {item["ref"] for item in combined["findings"] if item["category"] == "missing-build-stage"}
        self.assertEqual(missing, set(build_report.REQUIRED_STAGES) - {"validate"})
        for kind in missing:
            self.assertEqual(combined["counts"]["by_stage"][kind], {})

    def test_identityless_reports_cannot_form_a_successful_cohort(self):
        for offset, kind in enumerate(build_report.REQUIRED_STAGES):
            self._write_report(kind, None, f"identityless-{offset}", 1_700_000_000 + offset)

        with mock.patch.dict(os.environ, {}, clear=True):
            combined, _ = build_report.combine_reports()

        self.assertIsNone(combined["run_archive_ref"])
        self.assertNotEqual(combined["exit_code"], 0)
        self.assertFalse(combined["counts"]["overall_success"])
        self.assertTrue(
            any("identity-less reports cannot form a correlated build" in item["message"]
                for item in combined["findings"])
        )
        self.assertEqual(
            {item["ref"] for item in combined["findings"] if item["category"] == "missing-build-stage"},
            set(build_report.REQUIRED_STAGES),
        )

    def test_page_history_is_ledger_driven_newest_first_after_append(self):
        ledger = os.path.join(self.test_dir, "build-ledger.jsonl")
        combined = {
            "report_kind": "combined", "started_at": "2026-08-22T10:00:00Z",
            "finished_at": "2026-08-22T10:01:00Z", "exit_code": 0,
            "counts": {"overall_success": True, "by_stage": {
                "i18n_merge": {}, "i18n_diagrams": {"sources_considered": 3},
                "html_generate": {"pages_generated_per_lang": {"de": 7}},
                "validate": {"checks_performed": 11}}},
            "findings": [], "run_archive_ref": "manual-newest-deadbeef",
        }
        combined_path = os.path.join(self.test_dir, "combined.json")
        Path(combined_path).write_text(json.dumps(combined), encoding="utf-8")
        build_ledger.append_entry(build_ledger.entry_from_combined(
            combined, combined_path, repo_commit="a" * 40,
            recorded_at="2026-08-22T10:02:00Z"), ledger)
        build_report.generate_report_page(combined, ledger_path=ledger)
        first = json.loads(Path(build_report.PAGE_MODEL).read_text(encoding="utf-8"))["main"][0]["html"]
        self.assertIn("manual-newest-deadbeef", first)
        later = dict(combined, run_archive_ref="manual-later-cafebabe",
                     finished_at="2026-08-22T11:01:00Z")
        Path(combined_path).write_text(json.dumps(later), encoding="utf-8")
        build_ledger.append_entry(build_ledger.entry_from_combined(
            later, combined_path, repo_commit="b" * 40,
            recorded_at="2026-08-22T11:02:00Z"), ledger)
        build_report.generate_report_page(later, ledger_path=ledger)
        html = json.loads(Path(build_report.PAGE_MODEL).read_text(encoding="utf-8"))["main"][0]["html"]
        self.assertLess(html.index("manual-later-cafebabe"), html.index("manual-newest-deadbeef"))
        self.assertIn('id="latest-run"', html)

    def _history_row_html(self, ledger, combined_path_name="combined.json",
                          combined_report_ref=None):
        """Render one ledger row and return the page HTML (0043-03)."""
        combined = {
            "report_kind": "combined", "started_at": "2026-08-23T10:00:00Z",
            "finished_at": "2026-08-23T10:01:00Z", "exit_code": 0,
            "counts": {"overall_success": True, "by_stage": {
                "i18n_merge": {}, "i18n_diagrams": {"sources_considered": 1},
                "html_generate": {"pages_generated_per_lang": {"de": 2}},
                "validate": {"checks_performed": 3}}},
            "findings": [], "run_archive_ref": "manual-detailref-0043aa03",
        }
        combined_path = os.path.join(self.test_dir, combined_path_name)
        Path(combined_path).write_text(json.dumps(combined), encoding="utf-8")
        entry = build_ledger.entry_from_combined(
            combined, combined_path, repo_commit="c" * 40,
            recorded_at="2026-08-23T10:02:00Z")
        if combined_report_ref is not None:
            entry["combined_report_ref"] = combined_report_ref
        build_ledger.append_entry(entry, ledger)
        build_report.generate_report_page(combined, ledger_path=ledger)
        return json.loads(
            Path(build_report.PAGE_MODEL).read_text(encoding="utf-8"))["main"][0]["html"]

    def test_unresolvable_detail_ref_is_plain_text_not_a_dead_link(self):
        """0043-03 / F-BELANNA-0043-03-01: combined_report_ref points into the
        permanently git-ignored output/build-reports/ tree (DEC-0043-001), so it must
        never be rendered as a link — but its value must stay visible."""
        ledger = os.path.join(self.test_dir, "build-ledger.jsonl")
        ref = "output/build-reports/combined-20260823T100100Z.json"
        html = self._history_row_html(ledger, combined_report_ref=ref)
        self.assertIn(ref, html)
        self.assertNotIn(f'<a href="{ref}"', html)
        self.assertNotIn("JSON-Details", html)

    def test_published_detail_ref_is_still_rendered_as_a_link(self):
        ledger = os.path.join(self.test_dir, "build-ledger.jsonl")
        tracked = "docs/evidence/build-ledger.jsonl"
        self.assertTrue(
            build_report._ref_is_published(tracked),
            "fixture assumes %s is tracked in this repository" % tracked)
        html = self._history_row_html(ledger, combined_report_ref=tracked)
        self.assertIn(f'<a href="{tracked}">JSON-Details</a>', html)

    def test_empty_detail_ref_keeps_the_placeholder(self):
        """An entry without a usable ref keeps the existing placeholder. The ledger
        schema rejects an empty combined_report_ref on append, so this defensive
        branch is exercised at the rendering level."""
        combined = {
            "report_kind": "combined", "started_at": "2026-08-23T10:00:00Z",
            "finished_at": "2026-08-23T10:01:00Z", "exit_code": 0,
            "counts": {"overall_success": True, "by_stage": {}},
            "findings": [], "run_archive_ref": "manual-placeholder-0043aa03",
        }
        entry = {"run_finished_at": "2026-08-23T10:01:00Z", "overall_success": True,
                 "run_archive_ref": "manual-placeholder-0043aa03",
                 "counts_by_stage": {}, "findings_count": 0,
                 "combined_report_ref": ""}
        with mock.patch.object(build_ledger, "read_entries", return_value=([entry], [])):
            build_report.generate_report_page(combined)
        html = json.loads(
            Path(build_report.PAGE_MODEL).read_text(encoding="utf-8"))["main"][0]["html"]
        self.assertIn("<td>–</td>", html)
        self.assertNotIn("JSON-Details", html)

    def test_ref_is_unpublished_when_git_cannot_be_consulted(self):
        """The lookup fails closed: no tracked-path knowledge means no link."""
        build_report._TRACKED_PATHS_CACHE.clear()
        try:
            with mock.patch.object(build_report.subprocess, "run",
                                   side_effect=OSError("git unavailable")):
                self.assertFalse(
                    build_report._ref_is_published("docs/evidence/build-ledger.jsonl"))
        finally:
            build_report._TRACKED_PATHS_CACHE.clear()


if __name__ == "__main__":
    unittest.main()
