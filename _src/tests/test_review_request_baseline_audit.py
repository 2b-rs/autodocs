import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
FIXTURE = (
    ROOT
    / "_src"
    / "tests"
    / "fixtures"
    / "review_request_baseline"
    / "manifest-v1.json"
)
DOC = ROOT / "docs" / "pipeline" / "review-request-baseline-audit.md"
TODO = ROOT / "TODO.md"

sys.path.insert(0, str(TOOLS))
import review_request_baseline_audit as audit  # noqa: E402


class ReviewRequestBaselineManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_manifest_has_unique_stable_findings_and_forward_coverage(self):
        findings = self.manifest["findings"]
        finding_ids = [finding["id"] for finding in findings]
        self.assertEqual(len(finding_ids), len(set(finding_ids)))
        self.assertTrue(all(audit.FINDING_RE.fullmatch(item) for item in finding_ids))
        mapped = {
            task
            for finding in findings
            for task in finding["forward_tasks"]
        }
        self.assertEqual(set(self.manifest["later_task_ids"]), mapped)

    def test_historical_refs_and_artifacts_are_fully_pinned(self):
        for entry in self.manifest["historical_refs"]:
            self.assertRegex(entry["commit"], r"^[0-9a-f]{40}$")
            self.assertRegex(entry["tree"], r"^[0-9a-f]{40}$")
        self.assertGreaterEqual(len(self.manifest["artifacts"]), 20)
        for artifact in self.manifest["artifacts"]:
            self.assertRegex(artifact["ref"], r"^[0-9a-f]{40}$")
            self.assertRegex(artifact["sha256"], r"^[0-9a-f]{64}$")

    def test_local_labels_receive_no_independent_evidence_credit(self):
        claims = self.manifest["local_closure_claims"]
        self.assertEqual(
            [claim["task_id"] for claim in claims],
            ["0021-06", "0021-07", "0021-08"],
        )
        for claim in claims:
            self.assertIsNone(claim["task_specific_git_object"])
            self.assertEqual(
                claim["disposition"],
                "unrecoverable / no independent evidence credit",
            )
            self.assertRegex(claim["contextual_checkpoint"], r"^[0-9a-f]{40}$")
            self.assertRegex(claim["contextual_tree"], r"^[0-9a-f]{40}$")

    def test_finding_matrix_and_backlog_reference_every_finding_and_later_task(self):
        document = DOC.read_text(encoding="utf-8")
        backlog = TODO.read_text(encoding="utf-8")
        for finding in self.manifest["findings"]:
            self.assertIn("`%s`" % finding["id"], document)
        for task_id in self.manifest["later_task_ids"]:
            task_findings = [
                finding["id"]
                for finding in self.manifest["findings"]
                if task_id in finding["forward_tasks"]
            ]
            self.assertTrue(task_findings, task_id)
            header = "**%s**" % task_id
            start = backlog.index(header)
            next_task = backlog.find("\n- [", start + len(header))
            section = backlog[start : next_task if next_task != -1 else len(backlog)]
            self.assertTrue(
                any("`%s`" % finding_id in section for finding_id in task_findings),
                "%s does not reference a mapped baseline finding" % task_id,
            )


class ReviewRequestBaselineAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.run_audit(
            ROOT,
            FIXTURE,
            run_historical_tests=False,
        )

    def test_fast_audit_reproduces_all_non_browser_runtime_cases(self):
        cases = {case["id"]: case for case in self.report["cases"]}
        self.assertEqual(
            set(cases),
            {
                "RRB-SCHEMA-001",
                "RRB-SCHEMA-002",
                "RRB-INGEST-001",
                "RRB-QUEUE-001",
                "RRB-META-001",
                "RRB-NOJS-001",
                "RRB-BROWSER-001",
            },
        )
        self.assertTrue(all(case["observed"] for case in cases.values()))
        self.assertTrue(self.report["summary"]["success"])
        self.assertFalse(self.report["summary"]["evidence_complete"])

    def test_ingestion_probe_is_isolated_and_nonconformant_for_expected_reasons(self):
        actual = self.report["details"]["ingestion_probe"]
        self.assertTrue(actual["queue_redirected"])
        self.assertTrue(actual["written_inside_temporary_queue"])
        self.assertEqual(actual["outcome"], "ok")
        self.assertNotEqual(actual["raw_canonical_id"], actual["target_canonical_id"])
        self.assertEqual(actual["normalized_origin"], "curator")
        self.assertEqual(actual["normalized_status"], "proposed")
        self.assertEqual(actual["normalized_item_kind"], "review-request")
        self.assertFalse(actual["normalized_conformant"])

    def test_real_page_payload_and_no_javascript_observation_are_pinned(self):
        detail = self.report["details"]["production_page"]
        payload = detail["payload"]
        self.assertEqual(payload["canonical_id"], "SWS_CORE_00322")
        self.assertIsNone(payload["version_id"])
        self.assertIsNone(payload["content_hash"])
        self.assertEqual(payload["source_url"], "")
        self.assertGreater(detail["trigger_button_count"], 0)
        self.assertEqual(detail["noscript_count"], 0)
        self.assertEqual(detail["review_link_count"], 0)

    def test_real_worktree_and_queue_snapshots_are_unchanged(self):
        guard = self.report["mutation_guard"]
        self.assertTrue(guard["worktree_unchanged"])
        self.assertTrue(guard["queue_roots_unchanged"])
        self.assertEqual(guard["worktree_before"], guard["worktree_after"])
        self.assertEqual(guard["queue_roots_before"], guard["queue_roots_after"])

    def test_every_artifact_and_historical_tree_matches_manifest(self):
        inputs = self.report["inputs"]
        self.assertTrue(all(item["matched"] for item in inputs["historical_refs"]))
        self.assertTrue(all(item["matched"] for item in inputs["artifacts"]))
        self.assertTrue(all(item["matched"] for item in inputs["local_closure_claims"]))
        self.assertTrue(
            all(not item["label_resolves"] for item in inputs["local_closure_claims"])
        )

    def test_safe_extract_rejects_archive_path_escape(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w") as archive:
            info = tarfile.TarInfo("../escape.txt")
            payload = b"escape"
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(audit.AuditError):
                audit._safe_extract_tar(raw.getvalue(), Path(temporary))

    def test_output_is_restricted_to_audit_log_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(audit.AuditError):
                audit._validate_output_path(ROOT, Path(temporary) / "report.json")
        allowed = ROOT / "output" / "logs" / "0033-01" / "report.json"
        self.assertEqual(audit._validate_output_path(ROOT, allowed), allowed.resolve())


if __name__ == "__main__":
    unittest.main()
