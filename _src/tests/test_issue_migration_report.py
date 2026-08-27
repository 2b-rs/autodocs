#!/usr/bin/env python3
"""Focused positive, adversarial, integrity, and rerun tests for Task 0037-16."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional, Set

from _src.tools import issue_migration_report as report_tool


ROOT = Path(__file__).resolve().parents[2]
FIXED_TIME = "2026-08-26T19:00:00Z"


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _run(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class IssueMigrationReportTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="issue-migration-report-")
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        _run(self.repo, "init")
        _run(self.repo, "config", "user.email", "fixture@example.invalid")
        _run(self.repo, "config", "user.name", "Fixture")
        self.source_raw = (
            b"- [x] **0001-01** PREREQ: 0001-01:0001-00 Build gate.\n"
            b"  - **Acceptance criteria:** Preserve alpha; Preserve beta.\n"
            b"  - **Definition of Done:** Exact bytes.\n"
        )
        self.opaque_raw = b"owner_token: agent:fixture:0001-01:one\nstate: finalized\n"
        self.backlog_path = self.repo / "TODO.md"
        self.opaque_legacy_path = self.repo / "TODO-fixture-0001-01-one.md"
        self.backlog_path.write_bytes(self.source_raw)
        self.opaque_legacy_path.write_bytes(self.opaque_raw)
        _run(self.repo, "add", "TODO.md", "TODO-fixture-0001-01-one.md")
        _run(self.repo, "commit", "-m", "fixture: frozen source")
        self.source_commit = _run(self.repo, "rev-parse", "HEAD")
        (self.repo / "candidate-marker.txt").write_text("candidate\n", encoding="utf-8")
        _run(self.repo, "add", "candidate-marker.txt")
        _run(self.repo, "commit", "-m", "fixture: candidate identity")
        self.candidate_commit = _run(self.repo, "rev-parse", "HEAD")

        self.inventory = {
            "schema": "legacy-inventory@v1",
            "source_commit": self.source_commit,
            "items": [
                {
                    "id": "0001-01",
                    "kind": "task",
                    "path": "TODO.md",
                    "line": 1,
                    "marker": "x",
                    "title_tail": "Build gate.",
                    "prerequisites": [{"to": "0001-00"}],
                    "text_sha256": _digest(self.source_raw),
                }
            ],
            "claims": [
                {
                    "path": "TODO-fixture-0001-01-one.md",
                    "item": "0001-01",
                    "digest": _digest(self.opaque_raw),
                    "size_bytes": len(self.opaque_raw),
                }
            ],
            "findings": [],
            "dispositions": [],
            "source_artifacts": [
                {
                    "path": "TODO.md",
                    "digest": _digest(self.source_raw),
                    "size_bytes": len(self.source_raw),
                },
                {
                    "path": "TODO-fixture-0001-01-one.md",
                    "digest": _digest(self.opaque_raw),
                    "size_bytes": len(self.opaque_raw),
                },
            ],
        }
        self.inventory_path = self.root / "inventory.json"
        self._write_inventory()
        self.candidate_root = self.root / "candidate"
        self.item_path = self.candidate_root / "issues/0001/0001-01/index.md"
        self.opaque_copy_path = self.candidate_root / "legacy-claims/TODO-fixture-0001-01-one.md"
        self.item_path.parent.mkdir(parents=True)
        self.opaque_copy_path.parent.mkdir(parents=True)
        self.item_path.write_text(self._candidate_markdown(), encoding="utf-8")
        self.opaque_copy_path.write_bytes(self.opaque_raw)
        self.manifest_path = self.candidate_root / "import-manifest.json"
        self._write_manifest()
        self.output = self.root / "reports"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _candidate_markdown(self) -> str:
        return """---
schema_version: "1.0"
id: "0001-01"
level: "task"
parent: "0001"
state: "closed"
visibility: "internal"
prerequisites:
  - "0001-00"
work_type: "migration"
origin:
  kind: "migrated-from-legacy-todo"
  source: "legacy:TODO.md:1"
authority: "shadow"
criteria:
  - id: "AC-001"
    status: "active"
  - id: "AC-002"
    status: "active"
---

## Goal

Build gate.

## Scope

Imported legacy text retained under source locators.

## Acceptance criteria

- **AC-001** Preserve alpha
- **AC-002** Preserve beta

## Definition of Done

Exact bytes.
"""

    def _write_inventory(self) -> None:
        self.inventory_path.write_text(
            report_tool.canonical_json(self.inventory), encoding="utf-8"
        )

    def _manifest(self) -> dict:
        return {
            "schema": "issue-legacy-import@v1",
            "source_commit": self.source_commit,
            "items": [
                {
                    "id": "0001-01",
                    "path": "issues/0001/0001-01/index.md",
                    "state": "closed",
                    "locator": "TODO.md:1",
                }
            ],
            "findings": [],
        }

    def _write_manifest(self, value: Optional[dict] = None) -> None:
        self.manifest_path.write_text(
            report_tool.canonical_json(value or self._manifest()), encoding="utf-8"
        )

    def _generate(
        self,
        run_id: str,
        *,
        candidate_commit: Optional[str] = None,
        previous_report: Optional[Path] = None,
        migration_state: Optional[Path] = None,
        generated_view_manifest: Optional[Path] = None,
    ) -> dict:
        return report_tool.generate_report(
            repo=self.repo,
            source_inventory_path=self.inventory_path,
            candidate_root=self.candidate_root,
            output_parent=self.output,
            run_id=run_id,
            candidate_commit=candidate_commit or self.candidate_commit,
            previous_report_path=previous_report,
            migration_state_path=migration_state,
            generated_view_manifest_path=generated_view_manifest,
            produced_at=FIXED_TIME,
        )

    @staticmethod
    def _rules(report: dict) -> Set[str]:
        return {finding["rule"] for finding in report["findings"]}

    def test_matching_candidate_passes_schema_and_integrity(self) -> None:
        report = self._generate("positive")
        self.assertTrue(report["decision"]["pass"])
        self.assertFalse(report["decision"]["cutover_blocked"])
        report_path = self.output / "positive/report.json"
        valid, detail = report_tool.verify_report(report_path)
        self.assertTrue(valid, detail)
        self.assertEqual("0037-16", report["identity"]["producing_issue"])
        self.assertRegex(report["identity"]["tool"]["digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(report["identity"]["report_schema"]["digest"], r"^sha256:[0-9a-f]{64}$")
        schema = json.loads(
            (ROOT / "provenance/_schema/issue-migration-report-v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("issue-migration-report@v1", schema["title"])
        self.assertEqual("issue-migration-report@v1", schema["properties"]["schema"]["const"])
        try:
            import jsonschema
        except ImportError:
            pass
        else:  # pragma: no cover - exercised where the optional validator exists
            jsonschema.validate(instance=report, schema=schema)

    def test_source_omission_blocks_cutover(self) -> None:
        self.item_path.unlink()
        report = self._generate("omission")
        self.assertIn("MIG-SOURCE-OMISSION", self._rules(report))
        self.assertTrue(report["decision"]["cutover_blocked"])

    def test_duplicate_and_mismatched_candidate_identities_block(self) -> None:
        manifest = self._manifest()
        manifest["items"].append(dict(manifest["items"][0]))
        self._write_manifest(manifest)
        duplicate = self._generate("duplicate-candidate-id")
        self.assertIn("MIG-DUPLICATE-CANDIDATE-ID", self._rules(duplicate))
        self._write_manifest()
        self.item_path.write_text(
            self._candidate_markdown().replace('id: "0001-01"', 'id: "0001-99"'),
            encoding="utf-8",
        )
        mismatch = self._generate("mismatched-candidate-id")
        self.assertIn("MIG-CANDIDATE-ID-MISMATCH", self._rules(mismatch))
        self.assertTrue(mismatch["decision"]["cutover_blocked"])

    def test_semantic_and_preserved_byte_drift_are_distinct(self) -> None:
        self.item_path.write_text(
            self._candidate_markdown().replace("Build gate.", "Build altered."),
            encoding="utf-8",
        )
        semantic = self._generate("semantic-drift")
        self.assertIn("MIG-SEMANTIC-DRIFT", self._rules(semantic))
        self.assertNotIn("MIG-BYTE-DRIFT", self._rules(semantic))
        self.item_path.write_text(self._candidate_markdown(), encoding="utf-8")
        self.opaque_copy_path.write_bytes(self.opaque_raw + b"changed\n")
        byte_drift = self._generate("byte-drift")
        self.assertIn("MIG-BYTE-DRIFT", self._rules(byte_drift))
        self.assertNotIn("MIG-SEMANTIC-DRIFT", self._rules(byte_drift))

    def test_state_edge_authority_evidence_and_ref_inflation_block(self) -> None:
        changed = self._candidate_markdown()
        changed = changed.replace('state: "closed"', 'state: "open"')
        changed = changed.replace('  - "0001-00"', '  - "0001-00"\n  - "0001-99"')
        changed = changed.replace('authority: "shadow"', 'authority: "canonical"')
        changed = changed.replace('work_type: "migration"', 'work_type: "migration"\nacceptance: "fabricated"')
        changed = changed.replace("Imported legacy text", "abcdef1 Imported legacy text")
        self.item_path.write_text(changed, encoding="utf-8")
        report = self._generate("inflation")
        rules = self._rules(report)
        self.assertTrue(
            {
                "MIG-STATE-DRIFT",
                "MIG-EDGE-DRIFT",
                "MIG-AUTHORITY-INFLATION",
                "MIG-EVIDENCE-INFLATION",
                "MIG-FABRICATED-REF",
            }.issubset(rules)
        )
        self.assertTrue(report["decision"]["cutover_blocked"])

    def test_criteria_dod_and_archive_drift_block(self) -> None:
        changed = self._candidate_markdown()
        changed = changed.replace('visibility: "internal"', 'visibility: "internal"\nlabels:\n  - "archived-not-accepted"')
        changed = changed.replace("Preserve beta", "Changed beta")
        changed = changed.replace("Exact bytes.", "Different completion.")
        self.item_path.write_text(changed, encoding="utf-8")
        report = self._generate("contract-drift")
        self.assertTrue(
            {"MIG-CRITERIA-DRIFT", "MIG-DOD-DRIFT", "MIG-ARCHIVE-DRIFT"}.issubset(
                self._rules(report)
            )
        )
        self.assertTrue(report["decision"]["cutover_blocked"])

    def test_generated_view_reconciliation_matches_then_blocks_stale_view(self) -> None:
        view_path = self.candidate_root / "views/issues.json"
        view_path.parent.mkdir()
        view_path.write_bytes(b'{"items":[]}\n')
        view_manifest = self.root / "views.json"
        view_manifest.write_text(
            report_tool.canonical_json(
                {
                    "views": [
                        {
                            "path": "views/issues.json",
                            "digest": _digest(view_path.read_bytes()),
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        matching = self._generate(
            "views-match", generated_view_manifest=view_manifest
        )
        self.assertTrue(matching["decision"]["pass"])
        self.assertEqual("match", matching["comparisons"]["generated_views"]["status"])
        view_path.write_bytes(b'{"items":["stale"]}\n')
        stale = self._generate("views-stale", generated_view_manifest=view_manifest)
        self.assertIn("MIG-GENERATED-VIEW-DRIFT", self._rules(stale))
        self.assertTrue(stale["decision"]["cutover_blocked"])

    def test_stale_and_self_baselined_candidates_block(self) -> None:
        manifest = self._manifest()
        manifest["source_commit"] = self.candidate_commit
        self._write_manifest(manifest)
        stale = self._generate("stale")
        self.assertIn("MIG-STALE-CANDIDATE", self._rules(stale))
        self._write_manifest()
        self_baselined = self._generate(
            "self-baselined", candidate_commit=self.source_commit
        )
        self.assertIn("MIG-SELF-BASELINED", self._rules(self_baselined))

    def test_finding_id_does_not_depend_on_observed_value(self) -> None:
        self.item_path.write_text(
            self._candidate_markdown().replace("Build gate.", "Observed A."),
            encoding="utf-8",
        )
        first = self._generate("finding-a")
        first_id = next(
            finding["id"]
            for finding in first["findings"]
            if finding["rule"] == "MIG-SEMANTIC-DRIFT" and finding["field"] == "goal"
        )
        self.item_path.write_text(
            self._candidate_markdown().replace("Build gate.", "Observed B."),
            encoding="utf-8",
        )
        second = self._generate("finding-b")
        second_id = next(
            finding["id"]
            for finding in second["findings"]
            if finding["rule"] == "MIG-SEMANTIC-DRIFT" and finding["field"] == "goal"
        )
        self.assertEqual(first_id, second_id)

    def test_previous_run_links_resolved_findings(self) -> None:
        self.item_path.write_text(
            self._candidate_markdown().replace("Build gate.", "Drift."),
            encoding="utf-8",
        )
        first = self._generate("previous-failing")
        previous_path = self.output / "previous-failing/report.json"
        prior_ids = {finding["id"] for finding in first["findings"]}
        self.item_path.write_text(self._candidate_markdown(), encoding="utf-8")
        resolved = self._generate("resolved", previous_report=previous_path)
        self.assertTrue(resolved["decision"]["pass"])
        self.assertEqual(prior_ids, set(resolved["previous_run"]["resolved_finding_ids"]))
        self.assertEqual("previous-failing", resolved["previous_run"]["run_id"])

    def test_undispositioned_warning_fails_and_explicit_disposition_resolves(self) -> None:
        self.inventory["findings"] = [
            {
                "rule": "LEGACY-ANOMALY",
                "item": "0001-01",
                "field": "source",
                "locator": "TODO.md:1",
                "severity": "warning",
                "message": "legacy anomaly",
            }
        ]
        self._write_inventory()
        blocked = self._generate("warning-blocked")
        self.assertFalse(blocked["decision"]["pass"])
        self.assertTrue(blocked["decision"]["unresolved_warning_ids"])
        self.inventory["dispositions"] = [
            {
                "item": "0001-01",
                "rule": "MIG-SOURCE-LEGACY-ANOMALY",
                "disposition": "retained-source-anomaly",
                "authority": "fixture:recorded-authority",
            }
        ]
        self._write_inventory()
        resolved = self._generate("warning-dispositioned")
        self.assertTrue(resolved["decision"]["pass"])

    def test_json_and_markdown_tampering_are_detected(self) -> None:
        self._generate("tamper-json")
        json_path = self.output / "tamper-json/report.json"
        tampered = json.loads(json_path.read_text(encoding="utf-8"))
        tampered["decision"]["pass"] = False
        json_path.write_text(report_tool.canonical_json(tampered), encoding="utf-8")
        valid, detail = report_tool.verify_report(json_path)
        self.assertFalse(valid)
        self.assertIn("MIG-REPORT-TAMPERED", detail)
        with self.assertRaisesRegex(
            report_tool.MigrationReportError, "MIG-EXISTING-REPORT-TAMPERED"
        ):
            self._generate("tamper-json")

        self._generate("tamper-markdown")
        markdown_path = self.output / "tamper-markdown/report.md"
        markdown_path.write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(
            report_tool.MigrationReportError, "MIG-EXISTING-REPORT-TAMPERED"
        ):
            self._generate("tamper-markdown")

    def test_same_run_id_is_idempotent_but_rebinding_is_refused(self) -> None:
        first = self._generate("immutable-run")
        second = self._generate("immutable-run")
        self.assertEqual(first["integrity"], second["integrity"])
        self.item_path.write_text(
            self._candidate_markdown().replace("Build gate.", "Different."),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            report_tool.MigrationReportError, "MIG-RUN-ID-COLLISION"
        ):
            self._generate("immutable-run")

    def test_missing_markdown_is_recovered_from_valid_json_commit_marker(self) -> None:
        report = self._generate("recover-markdown")
        markdown_path = self.output / "recover-markdown/report.md"
        markdown_path.unlink()
        recovered = self._generate("recover-markdown")
        self.assertEqual(report["integrity"], recovered["integrity"])
        self.assertEqual(
            report["identity"]["report_markdown"]["digest"],
            _digest(markdown_path.read_bytes()),
        )

    def test_unsafe_run_ids_and_output_symlink_escape_fail_closed(self) -> None:
        with self.assertRaisesRegex(report_tool.MigrationReportError, "MIG-RUN-ID"):
            self._generate("../escape")
        outside = self.root / "outside"
        outside.mkdir()
        self.output.mkdir()
        (self.output / "linked").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(report_tool.MigrationReportError, "MIG-PATH-ESCAPE"):
            self._generate("linked")
        self.assertEqual([], list(outside.iterdir()))


if __name__ == "__main__":
    unittest.main()
