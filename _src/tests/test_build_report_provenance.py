"""Integration tests for build-report@v2 provenance (Task 0037-26.06)."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
sys.path.insert(0, str(TOOLS))

import build_report  # noqa: E402
import build_report_envelope as envelope  # noqa: E402

ps_spec = importlib.util.spec_from_file_location("provenance_store", TOOLS / "provenance_store.py")
ps = importlib.util.module_from_spec(ps_spec)
ps_spec.loader.exec_module(ps)
pq_spec = importlib.util.spec_from_file_location("provenance_query", TOOLS / "provenance_query.py")
pq = importlib.util.module_from_spec(pq_spec)
sys.modules["provenance_query"] = pq
pq_spec.loader.exec_module(pq)

COMMIT = "c" * 40
RUN = "018f4a31-2606-7abc-8def-0123456789aa"
RUN2 = "018f4a31-2606-7abc-8def-0123456789bb"
FINDING = "018f4a31-2606-7abc-8def-0123456789f1"
SET_IN = "018f4a31-2606-7abc-8def-0123456789a1"
SET_OUT = "018f4a31-2606-7abc-8def-0123456789a2"
EVT_T = "018f4a31-2606-7abc-8def-0123456789e1"
EVT_P = "018f4a31-2606-7abc-8def-0123456789e2"
EVT_D = "018f4a31-2606-7abc-8def-0123456789e3"
STAMP = "2026-08-27T12:00:00Z"
END = "2026-08-27T12:01:00Z"


def _stage(kind, run_id=RUN, extra=None, finding=None, inputs=None, outputs=None):
    inputs = inputs or [f"src/{kind}.txt"]
    outputs = outputs or [f"out/{kind}.txt"]
    report = {
        "schema_version": "2.0",
        "schema": "build-report@v2",
        "report_kind": kind,
        "tool": f"{kind}.py",
        "command": kind,
        "inputs": inputs,
        "started_at": STAMP,
        "finished_at": END,
        "duration_s": 1.0,
        "exit_code": 0,
        "changed_artifacts": outputs,
        "counts": {},
        "findings": finding or [],
        "run_archive_ref": "output/run-archive/prov",
        "run_id": run_id,
        "source_commit": COMMIT,
        "tool_commit": COMMIT,
        "config_commit": COMMIT,
        "trigger": {"kind": "issue", "id": "0037-26.06"},
        "input_artifact_set": envelope.artifact_set_from_members(
            envelope.members_for_paths(inputs, COMMIT)
        ),
        "output_artifact_set": envelope.artifact_set_from_members(
            envelope.members_for_paths(outputs, COMMIT)
        ),
        "success": True,
    }
    if extra:
        report.update(extra)
    return report


class BuildReportProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.orig = build_report.REPORTS_DIR
        build_report.REPORTS_DIR = self.dir

    def tearDown(self):
        build_report.REPORTS_DIR = self.orig
        self.tmp.cleanup()

    def _dump(self, report, name):
        Path(self.dir, name).write_text(json.dumps(report), encoding="utf-8")

    def test_explicit_v1_migration_then_combine(self):
        legacy = {
            "schema_version": "1.0",
            "report_kind": "validate",
            "tool": "validate.py",
            "command": "validate.py",
            "inputs": ["_src/"],
            "started_at": STAMP,
            "finished_at": END,
            "duration_s": 1.0,
            "exit_code": 0,
            "changed_artifacts": ["out/validate.txt"],
            "counts": {},
            "findings": [],
            "run_archive_ref": "output/run-archive/prov",
        }
        migrated = envelope.migrate_build_report_v1(
            legacy,
            run_id=RUN,
            source_commit=COMMIT,
            tool_commit=COMMIT,
            config_commit=COMMIT,
            trigger={"kind": "issue", "id": "0037-26.06"},
            input_artifact_set=envelope.artifact_set_from_members(
                envelope.members_for_paths(["_src/"], COMMIT)
            ),
            output_artifact_set=envelope.artifact_set_from_members(
                envelope.members_for_paths(["out/validate.txt"], COMMIT)
            ),
        )
        self.assertEqual(migrated["legacy_disposition"]["from_schema"], "build-report@1.0")
        for kind in build_report.REQUIRED_STAGES:
            payload = migrated if kind == "validate" else _stage(kind)
            self._dump(payload, f"{kind}.json")
        combined, _ = build_report.combine_reports(run_id=RUN)
        self.assertEqual(combined["exit_code"], 0)
        self.assertEqual(combined["run_id"], RUN)

    def test_unmigrated_v1_is_rejected(self):
        self._dump(
            {
                "schema_version": "1.0",
                "report_kind": "validate",
                "tool": "validate.py",
                "command": "x",
                "inputs": [],
                "started_at": STAMP,
                "finished_at": END,
                "duration_s": 1,
                "exit_code": 0,
                "changed_artifacts": [],
                "counts": {},
                "findings": [],
                "run_archive_ref": "r",
            },
            "validate.json",
        )
        combined, _ = build_report.combine_reports()
        self.assertTrue(
            any(i["category"] == "legacy-build-report-unmigrated" for i in combined["findings"])
        )

    def test_mixed_runs_rejected(self):
        for kind in build_report.REQUIRED_STAGES:
            self._dump(_stage(kind, RUN), f"{kind}-a.json")
        self._dump(_stage("validate", RUN2), "validate-b.json")
        combined, _ = build_report.combine_reports()
        self.assertTrue(any(i["category"] == "mixed-run-cohort" for i in combined["findings"]))
        self.assertNotEqual(combined["exit_code"], 0)

    def test_mtime_does_not_select_cohort(self):
        for kind in build_report.REQUIRED_STAGES:
            self._dump(_stage(kind, RUN), f"{kind}-old.json")
        newer = _stage("validate", RUN2)
        path = Path(self.dir, "validate-new.json")
        path.write_text(json.dumps(newer), encoding="utf-8")
        os.utime(path, (9_999_999_999, 9_999_999_999))
        combined, _ = build_report.combine_reports()
        self.assertTrue(any(i["category"] == "mixed-run-cohort" for i in combined["findings"]))

    def test_missing_and_malformed_stages(self):
        self._dump(_stage("i18n_merge"), "i18n_merge.json")
        bad = _stage("i18n_diagrams", extra={"tool": " "})
        self._dump(bad, "i18n_diagrams.json")
        combined, _ = build_report.combine_reports(run_id=RUN)
        cats = {i["category"] for i in combined["findings"]}
        self.assertIn("missing-build-stage", cats)
        self.assertIn("malformed-build-report", cats)

    def test_unstable_finding_rejected(self):
        finding = [{"category": "x", "severity": "info", "message": "no id"}]
        for kind in build_report.REQUIRED_STAGES:
            extra = {"findings": finding} if kind == "validate" else None
            self._dump(_stage(kind, extra=extra, finding=finding if kind == "validate" else []), f"{kind}.json")
        combined, _ = build_report.combine_reports(run_id=RUN)
        self.assertTrue(
            any("unstable finding" in i["message"] for i in combined["findings"])
        )

    def test_incomplete_artifact_set_rejected(self):
        for kind in build_report.REQUIRED_STAGES:
            report = _stage(kind)
            report["input_artifact_set"] = {"schema_version": "1.0", "members": [], "set_digest": "sha256:" + "0" * 64}
            self._dump(report, f"{kind}.json")
        combined, _ = build_report.combine_reports(run_id=RUN)
        self.assertTrue(
            any("input_artifact_set.members" in i["message"] or i["category"] == "incomplete-artifact-set"
                for i in combined["findings"])
        )

    def test_self_validating_report_injection_rejected(self):
        for kind in build_report.REQUIRED_STAGES:
            inputs = ["output/build-reports/validate.json"] if kind == "validate" else [f"src/{kind}.txt"]
            self._dump(_stage(kind, inputs=inputs), f"{kind}.json")
        combined, _ = build_report.combine_reports(run_id=RUN)
        self.assertTrue(
            any("self-validating report injection" in i["message"] for i in combined["findings"])
        )

    def test_reverse_trace_from_combined_to_trigger(self):
        for kind in build_report.REQUIRED_STAGES:
            self._dump(_stage(kind), f"{kind}.json")
        combined, path = build_report.combine_reports(run_id=RUN)
        self.assertEqual(combined["exit_code"], 0)
        store_root = Path(self.dir, "provroot")
        store_root.mkdir()
        files = {}
        for member in combined["input_artifact_set"]["members"] + combined["output_artifact_set"]["members"]:
            files[member["path"]] = member["path"].encode("utf-8")
        store = ps.ProvenanceStore(store_root, file_bytes=files.__getitem__)
        envelope.persist_combined_provenance(
            store,
            run_id=RUN,
            started_at=STAMP,
            ended_at=END,
            success=True,
            trigger=combined["trigger"],
            input_set=combined["input_artifact_set"],
            output_set=combined["output_artifact_set"],
            findings=combined["findings"],
            set_id_input=SET_IN,
            set_id_output=SET_OUT,
            event_ids={"triggered": EVT_T, "produced": EVT_P, "derived": EVT_D},
        )
        shutil.copytree(ROOT / "provenance" / "_schema", store_root / "provenance" / "_schema")
        (store_root / "_src" / "tools").mkdir(parents=True, exist_ok=True)
        shutil.copy(TOOLS / "provenance_store.py", store_root / "_src" / "tools" / "provenance_store.py")
        shutil.copy(TOOLS / "provenance_views.py", store_root / "_src" / "tools" / "provenance_views.py")
        shutil.copy(TOOLS / "provenance_query.py", store_root / "_src" / "tools" / "provenance_query.py")
        result = pq.query_trace(store_root, kind="run", identifier=RUN, direction="reverse")
        self.assertTrue(result.get("found"))
        self.assertIn("issue:0037-26.06", result.get("issues") or [])
        self.assertTrue(any(c.get("commit") == COMMIT for c in result.get("commits") or []))


if __name__ == "__main__":
    unittest.main()
