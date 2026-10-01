import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("spec_extraction_campaign", TOOLS / "spec_extraction_campaign.py")
campaign = importlib.util.module_from_spec(spec); spec.loader.exec_module(campaign)


class ExtractionCampaignTests(unittest.TestCase):
    @staticmethod
    def _success_envelope(job, records):
        return {
            "schema": campaign.RESULT_SCHEMA,
            "attempt_id": job["attempt_id"],
            "job_id": job["job_id"],
            "document": job["document"],
            "document_sha256": job["document_sha256"],
            "backend": job["backend"],
            "extractor_argv": job["extractor_argv"],
            "extractor_contract_digest": job["extractor_contract_digest"],
            "exit_code": 0,
            "records": records,
        }

    @classmethod
    def _write_outputs(cls, manifest, pypdf, builtin):
        values = {"pypdf": pypdf, "builtin": builtin}
        for job in manifest["jobs"]:
            envelope = cls._success_envelope(job, values[job["backend"]])
            Path(job["output"]).write_text(json.dumps(envelope), encoding="utf-8")

    def test_create_emits_attempt_bound_jobs_and_deterministic_identity(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); pdf = root / "AUTOSAR_FO_RS_Test.pdf"
            pdf.write_bytes(b"stable pdf fixture")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                value = campaign.create(root / "campaign", root, [pdf], r"^RS_")
                repeated = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            self.assertEqual(value["schema"], 3)
            self.assertEqual(value["attempt_id"], repeated["attempt_id"])
            self.assertEqual([job["backend"] for job in value["jobs"]], ["pypdf", "builtin"])
            self.assertEqual(len(value["documents"][0]["sha256"]), 64)
            self.assertEqual(len(value["attempt_id"]), 64)
            attempt_dir = (root / "campaign").resolve() / "attempts" / value["attempt_id"]
            for job in value["jobs"]:
                self.assertEqual(job["schema"], 2)
                self.assertEqual(job["attempt_id"], value["attempt_id"])
                self.assertEqual(len(job["job_id"]), 64)
                self.assertEqual(len(job["extractor_contract_digest"]), 64)
                self.assertEqual(Path(job["output"]).parent, attempt_dir / "raw")
                self.assertEqual(Path(job["log"]).parent, attempt_dir / "logs")
                self.assertEqual(job["extractor_argv"][1],
                                 value["tool_contract"]["extractor"]["path"])
                self.assertEqual(job["argv"], [
                    value["runtime_contract"]["executable"],
                    value["tool_contract"]["harness"]["path"],
                    "run-job", str(attempt_dir / "manifest.json"),
                    "--job-id", job["job_id"],
                ])
            stored = json.loads((root / "campaign" / "manifest.json").read_text())
            snapshot = json.loads((attempt_dir / "manifest.json").read_text())
            self.assertEqual(stored, value)
            self.assertEqual(snapshot, value)
            self.assertEqual(stored["git_revision"], "abc")
            self.assertEqual(stored["tool_contract"]["extractor"]["sha256"],
                             stored["backend_contract"][1]["tool_sha256"])

            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                changed = campaign.create(root / "campaign", root, [pdf], r"^SWS_")
            self.assertNotEqual(changed["attempt_id"], value["attempt_id"])
            self.assertTrue((attempt_dir / "manifest.json").is_file())
            self.assertTrue(all(value_job["output"] != changed_job["output"]
                                for value_job, changed_job in zip(value["jobs"], changed["jobs"])))

    def test_applies_to_comma_spacing_is_layout_only(self):
        left = {"RS_X_00001": {"props": {"AppliesTo": "FO, CP , AP"}}}
        right = {"RS_X_00001": {"props": {"AppliesTo": "FO,CP,AP"}}}
        rows, summary = campaign.compare_records(left, right)
        self.assertEqual(summary, {"total_ids": 1, "normalized": 1})
        self.assertEqual(rows[0]["field_differences"], [])

    def test_commas_remain_significant_outside_applies_to(self):
        left = {"RS_X_00001": {"props": {"Description": "alpha , beta"}}}
        right = {"RS_X_00001": {"props": {"Description": "alpha,beta"}}}
        rows, summary = campaign.compare_records(left, right)
        self.assertEqual(summary, {"total_ids": 1, "different": 1})
        self.assertEqual(rows[0]["field_differences"][0]["field"], "Description")

    def test_compare_is_field_aware(self):
        left = {"RS_X_00001": {"heading": "Heading", "props": {"Description": "alpha beta"}, "page": 2}}
        right = {"RS_X_00001": {"heading": "Heading", "props": {"Description": "alpha  beta"}, "page": 2},
                 "RS_X_00002": {"heading": "Only builtin", "props": {}, "page": 3}}
        rows, summary = campaign.compare_records(left, right)
        self.assertEqual(rows[0]["status"], "normalized")
        self.assertEqual(rows[1]["status"], "only-builtin")
        self.assertEqual(summary["total_ids"], 2)

    def test_worker_emits_current_envelope_and_report_writes_artifacts(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); pdf = root / "Doc.pdf"
            pdf.write_bytes(b"report pdf fixture")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                manifest = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            records = {
                "pypdf": {"RS_X_00001": {"heading": "A", "props": {"Description": "left"}, "page": 1}},
                "builtin": {"RS_X_00001": {"heading": "A", "props": {"Description": "right"}, "page": 1}},
            }

            calls = []

            def extractor(argv, **kwargs):
                calls.append((argv, kwargs))
                backend = argv[argv.index("--backend") + 1]
                return subprocess.CompletedProcess(
                    argv, 0, stdout=json.dumps(records[backend]), stderr=""
                )

            with mock.patch.object(campaign.subprocess, "run", side_effect=extractor):
                for job in manifest["jobs"]:
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        result = campaign.main(job["argv"][2:])
                    self.assertEqual(result, 0)
                    envelope = json.loads(stdout.getvalue())
                    self.assertEqual(envelope,
                                     self._success_envelope(job, records[job["backend"]]))
                    Path(job["output"]).write_text(stdout.getvalue(), encoding="utf-8")

            self.assertEqual([call[0] for call in calls],
                             [job["extractor_argv"] for job in manifest["jobs"]])
            self.assertTrue(all(call[1]["check"] is False for call in calls))
            report_dir = root / "campaign"
            score = campaign.report(report_dir)
            self.assertEqual(score["documents_complete"], 1)
            self.assertEqual(score["failures"], [])
            self.assertEqual(score["attempt_id"], manifest["attempt_id"])
            for name in ("comparison.json", "scorecard.json", "comparison.csv", "comparison.html"):
                self.assertTrue((report_dir / name).is_file(), name)
            self.assertIn("pypdf", (report_dir / "comparison.html").read_text())
            self.assertIn("builtin", (report_dir / "comparison.html").read_text())

    def test_report_rejects_current_tool_runtime_and_backend_drift(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); pdf = root / "Doc.pdf"
            pdf.write_bytes(b"contract drift fixture")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                manifest = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            self._write_outputs(manifest, {}, {})

            tools = json.loads(json.dumps(campaign._tool_contract()))
            tools["extractor"]["sha256"] = "0" * 64
            runtime = json.loads(json.dumps(campaign._runtime_contract()))
            runtime["python_version"] = "drifted"
            backends = json.loads(json.dumps(
                campaign._backend_contract(campaign._tool_contract())
            ))
            backends[0]["version"] = "drifted"
            cases = (
                ("_tool_contract", tools,
                 "current extractor/harness tool contract differs"),
                ("_runtime_contract", runtime,
                 "current runtime contract differs"),
                ("_backend_contract", backends,
                 "current backend contract differs"),
            )
            for function, value, expected in cases:
                with self.subTest(contract=function), \
                        mock.patch.object(campaign, function, return_value=value):
                    score = campaign.report(root / "campaign")
                self.assertEqual(score["documents_complete"], 0)
                self.assertEqual(score["failures"][0]["reason"], "invalid-manifest")
                self.assertIn(expected, " ".join(score["failures"][0]["errors"]))
                self.assertTrue((root / "campaign" / "scorecard.json").is_file())

    def test_report_rejects_bare_and_malformed_outputs(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); pdf = root / "Doc.pdf"
            pdf.write_bytes(b"invalid result fixture")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                manifest = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            jobs = {job["backend"]: job for job in manifest["jobs"]}
            Path(jobs["pypdf"]["output"]).write_text(
                json.dumps({"RS_X_00001": {"heading": "bare records"}}), encoding="utf-8"
            )
            Path(jobs["builtin"]["output"]).write_text("{broken", encoding="utf-8")

            score = campaign.report(root / "campaign")
            self.assertEqual(score["documents_complete"], 0)
            errors = {item["backend"]: item["reason"]
                      for item in score["failures"][0]["backend_errors"]}
            self.assertEqual(errors["pypdf"], "result-envelope-job-mismatch")
            self.assertEqual(errors["builtin"], "output-unreadable")
            for name in ("comparison.json", "scorecard.json", "comparison.csv", "comparison.html"):
                self.assertTrue((root / "campaign" / name).is_file(), name)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(campaign.main(["report", str(root / "campaign")]), 1)

    def test_report_rejects_envelope_copied_from_another_job(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); pdf = root / "Doc.pdf"
            pdf.write_bytes(b"copied envelope fixture")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                manifest = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            jobs = {job["backend"]: job for job in manifest["jobs"]}
            copied = self._success_envelope(jobs["pypdf"], {})
            for job in jobs.values():
                Path(job["output"]).write_text(json.dumps(copied), encoding="utf-8")

            score = campaign.report(root / "campaign")
            self.assertEqual(score["documents_complete"], 0)
            error = score["failures"][0]["backend_errors"][0]
            self.assertEqual(error["backend"], "builtin")
            self.assertEqual(error["reason"], "result-envelope-job-mismatch")
            self.assertIn("job_id", error["fields"])
            self.assertIn("backend", error["fields"])
            self.assertIn("extractor_contract_digest", error["fields"])

    def test_worker_nonzero_emits_bound_failure_without_records(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); pdf = root / "Doc.pdf"
            pdf.write_bytes(b"worker failure fixture")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                manifest = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            job, other = manifest["jobs"]
            completed = subprocess.CompletedProcess(
                job["extractor_argv"], 9, stdout=json.dumps({"ignored": {}}),
                stderr="extractor failed\n",
            )
            stdout = io.StringIO(); stderr = io.StringIO()
            with mock.patch.object(campaign.subprocess, "run", return_value=completed) as run, \
                    contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = campaign.main(job["argv"][2:])
            self.assertEqual(result, 9)
            run.assert_called_once_with(
                job["extractor_argv"], cwd=campaign.ROOT, check=False,
                capture_output=True, text=True,
            )
            envelope = json.loads(stdout.getvalue())
            expected = self._success_envelope(job, {})
            expected.pop("records")
            expected["exit_code"] = 9
            expected["error"] = "extractor-nonzero"
            self.assertEqual(envelope, expected)
            self.assertNotIn("records", envelope)
            self.assertIn("extractor failed", stderr.getvalue())

            Path(job["output"]).write_text(stdout.getvalue(), encoding="utf-8")
            Path(other["output"]).write_text(
                json.dumps(self._success_envelope(other, {})), encoding="utf-8"
            )
            score = campaign.report(root / "campaign")
            error = score["failures"][0]["backend_errors"][0]
            self.assertEqual(error["backend"], job["backend"])
            self.assertEqual(error["reason"], "extractor-exit-nonzero")
            self.assertEqual(error["exit_code"], 9)

    def test_report_rejects_jobs_not_bound_to_current_attempt(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); pdf = root / "Doc.pdf"
            pdf.write_bytes(b"job binding fixture")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                manifest = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            stale = root / "campaign" / "raw" / "Doc.pypdf.json"
            stale.parent.mkdir()
            stale.write_text("{}", encoding="utf-8")
            manifest["jobs"][0]["output"] = str(stale)
            serialized = campaign._stable_json(manifest)
            (root / "campaign" / "manifest.json").write_text(serialized, encoding="utf-8")
            snapshot = (root / "campaign" / "attempts" / manifest["attempt_id"] / "manifest.json")
            snapshot.write_text(serialized, encoding="utf-8")

            score = campaign.report(root / "campaign")
            self.assertEqual(score["documents_complete"], 0)
            self.assertEqual(score["failures"][0]["reason"], "invalid-manifest")
            self.assertIn("jobs do not match", " ".join(score["failures"][0]["errors"]))
            self.assertTrue(stale.is_file())

    def test_recreate_changed_pdf_does_not_accept_stale_outputs(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as td:
            root = Path(td); pdf = root / "Doc.pdf"
            pdf.write_bytes(b"original pdf fixture")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                original = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            stale_records = {"RS_OLD_00001": {"heading": "stale", "props": {}, "page": 1}}
            self._write_outputs(original, stale_records, stale_records)
            historical_outputs = {Path(job["output"]) for job in original["jobs"]}

            pdf.write_bytes(b"changed PDF fixture!")
            with mock.patch.object(campaign, "_git_revision", return_value="abc"):
                current = campaign.create(root / "campaign", root, [pdf], r"^RS_")
            current_outputs = {Path(job["output"]) for job in current["jobs"]}
            self.assertNotEqual(current["documents"][0]["sha256"],
                                original["documents"][0]["sha256"])
            self.assertNotEqual(current["attempt_id"], original["attempt_id"])
            self.assertTrue(historical_outputs.isdisjoint(current_outputs))
            self.assertTrue(all(path.is_file() for path in historical_outputs))
            self.assertTrue(all(not path.exists() for path in current_outputs))

            report_dir = root / "campaign"
            score = campaign.report(report_dir)
            self.assertEqual(score["attempt_id"], current["attempt_id"])
            self.assertEqual(score["documents_complete"], 0)
            self.assertEqual(score["failures"][0]["missing_backends"], ["pypdf", "builtin"])
            for name in ("comparison.json", "scorecard.json", "comparison.csv", "comparison.html"):
                self.assertTrue((report_dir / name).is_file(), name)
            comparison = json.loads((report_dir / "comparison.json").read_text(encoding="utf-8"))
            self.assertEqual(comparison["documents"], [])

            with contextlib.redirect_stdout(io.StringIO()):
                result = campaign.main(["report", str(report_dir)])
            self.assertEqual(result, 1)
            self.assertTrue(all(path.is_file() for path in historical_outputs))


if __name__ == "__main__":
    unittest.main()
