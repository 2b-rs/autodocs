#!/usr/bin/env python3
"""Negative-fixture and evidence-report tests for Task 0019-06."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
FIXTURE = ROOT / "_src" / "tests" / "fixtures" / "score_normalization" / "raw-fixture-corpus.json"
NEGATIVE = ROOT / "_src" / "tests" / "fixtures" / "score_validation" / "negative-cases.json"
MANIFEST = ROOT / "_src" / "spec" / "campaigns" / "eclipse-score-v0.6.0.json"
PROFILE = ROOT / "_src" / "spec" / "import-profiles" / "eclipse-score-v0.6.0.json"
sys.path.insert(0, str(TOOLS))
import score_import_profile as profile  # noqa: E402
import score_normalization as normalization  # noqa: E402
import validate_score as validator  # noqa: E402


def corpus_fixture():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    contract = json.loads(PROFILE.read_text(encoding="utf-8"))
    observations = [
        {"candidate": copy.deepcopy(item["candidate"]), "decision": profile.evaluate_candidate(contract, copy.deepcopy(item["candidate"]))}
        for item in fixture["candidates"]
    ]
    raw = {
        "schema": "score-raw-extraction@v1", "project": fixture["project"], "release": fixture["release"],
        "manifest_sha256": "a" * 64, "profile_id": contract["profile_id"], "profile_version": contract["profile_version"],
        "profile_sha256": "b" * 64, "observations": observations,
    }
    return normalization.normalize(raw, fixture["import_date"])


def findings_for(corpus):
    report = validator.validate_corpus(corpus, json.loads(MANIFEST.read_text(encoding="utf-8")))
    return {finding["code"] for finding in report["findings"]}, report


class ScoreValidationTests(unittest.TestCase):
    def test_fixture_corpus_passes_and_never_claims_queueing(self):
        codes, report = findings_for(corpus_fixture())
        self.assertEqual(set(), codes)
        self.assertTrue(report["passed"])
        self.assertEqual(4, report["totals"]["records"])
        self.assertEqual({"module", "component", "design-doc", "process-doc"}, set(report["totals"]["records_by_kind"]))
        self.assertEqual(2, report["exception_candidates"]["total"])
        self.assertEqual(0, report["exception_candidates"]["queued"])
        self.assertIn("0019-07", report["exception_candidates"]["queue_statement"])

    def test_every_required_validation_class_has_a_negative_fixture(self):
        expected = json.loads(NEGATIVE.read_text(encoding="utf-8"))["validation_classes"]
        corpus = corpus_fixture()
        mutations = {
            "schema": lambda value: value.__setitem__("schema", "wrong"),
            "registry": lambda value: value["records"][0].__setitem__("kind", "unregistered"),
            "source_pin": lambda value: value["records"][0]["provenance"].__setitem__("source_commit", "0" * 40),
            "provenance": lambda value: value["records"][0].pop("provenance"),
            "traceability": lambda value: value["records"][0]["traceability"]["sources"][0].__setitem__("resolved_commit", "0" * 40),
            "containment": lambda value: value["records"][0].__setitem__("id", "missing.child"),
            "dangling_reference": lambda value: value["records"][0].__setitem__("references", ["ECLIPSE/S-CORE/module/missing"]),
            "sphinx_needs": lambda value: value["records"][1].__setitem__("id", "bad id"),
            "duplicate_version": lambda value: value["records"].append(copy.deepcopy(value["records"][0])),
            "status": lambda value: value["records"][0]["status"].__setitem__("state", "valid"),
        }
        for name, expected_code in expected.items():
            with self.subTest(name=name):
                bad = copy.deepcopy(corpus)
                mutations[name](bad)
                codes, _ = findings_for(bad)
                self.assertIn(expected_code, codes)

    def test_reports_are_machine_readable_human_readable_and_cli_returns_status(self):
        corpus = corpus_fixture()
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            corpus_path = temporary_path / "corpus.json"
            report_json = temporary_path / "campaign-report.json"
            report_markdown = temporary_path / "campaign-report.md"
            corpus_path.write_bytes(validator.canonical_json_bytes(corpus))
            command = [sys.executable, str(TOOLS / "validate_score.py"), str(corpus_path), "--manifest", str(MANIFEST), "--report-json", str(report_json), "--report-markdown", str(report_markdown)]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(0, completed.returncode, completed.stderr)
            report = json.loads(report_json.read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            markdown = report_markdown.read_text(encoding="utf-8")
            self.assertIn("Result:** PASS", markdown)
            self.assertIn("Task 0019-07", markdown)

            corpus["records"][0]["status"]["state"] = "valid"
            corpus_path.write_bytes(validator.canonical_json_bytes(corpus))
            failed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertNotEqual(0, failed.returncode)
            self.assertFalse(json.loads(report_json.read_text(encoding="utf-8"))["passed"])


if __name__ == "__main__":
    unittest.main()
