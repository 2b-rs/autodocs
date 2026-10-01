#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_review_request_metadata_coverage.py -- Tests for production metadata and corpus coverage (0033-09).

Validates:
  - Authoritative metadata derivation (canonical ID, version ID, content hash, deep source URL, status).
  - No synthetic per-record metadata required on checked-in production records.
  - Strict package validation and live ingestion of real production record payloads.
  - Absence of local filesystem paths in public rendered HTML.
  - Corpus-wide coverage reconciliation via validate_review_request_coverage.py.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
SRC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(SRC_DIR))

import canonical_id as cid_util  # noqa: E402
import curation_flags as cf  # noqa: E402
import lib_docmodel as dm  # noqa: E402
import review_request_ingest as rri  # noqa: E402
import review_request_package as rrp  # noqa: E402
import validate_review_request_coverage as vrrc  # noqa: E402
import version_id as vid_util  # noqa: E402


class ReviewRequestMetadataCoverageTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._root = Path(self._tmpdir.name)

        # Queue redirection
        self._orig_queue = cf.QUEUE
        self._orig_open = cf.OPEN_DIR
        self._orig_claimed = cf.CLAIMED_DIR
        self._orig_done = cf.DONE_DIR
        cf.QUEUE = self._root / "spec" / "curation-queue"
        cf.OPEN_DIR = cf.QUEUE / "open"
        cf.CLAIMED_DIR = cf.QUEUE / "claimed"
        cf.DONE_DIR = cf.QUEUE / "done"
        cf.OPEN_DIR.mkdir(parents=True, exist_ok=True)
        cf.CLAIMED_DIR.mkdir(parents=True, exist_ok=True)
        cf.DONE_DIR.mkdir(parents=True, exist_ok=True)

        # Symlink spec/records into temporary test root
        os.symlink(SRC_DIR / "spec" / "records", self._root / "spec" / "records")

        dm._REVIEW_REQUEST_INDEX = None

    def tearDown(self):
        cf.QUEUE = self._orig_queue
        cf.OPEN_DIR = self._orig_open
        cf.CLAIMED_DIR = self._orig_claimed
        cf.DONE_DIR = self._orig_done
        dm._REVIEW_REQUEST_INDEX = None
        self._tmpdir.cleanup()

    def test_real_production_record_metadata_derivation(self):
        """A checked-in production record without synthetic review_request metadata derives full metadata."""
        rec_path = SRC_DIR / "spec" / "records" / "SWS_CORE" / "SWS_CORE_00009.json"
        self.assertTrue(rec_path.exists(), f"Production record not found at {rec_path}")

        with rec_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertNotIn("review_request", data, "Production record must not contain synthetic review_request")

        panel_html = dm._render_review_request_panel(
            data["id"],
            {},
            data.get("status"),
            page_dir_depth=1,
            srcdir=str(SRC_DIR),
            rec_blocks=data.get("blocks"),
        )

        self.assertIn("review-request-panel", panel_html)
        self.assertIn('data-review-request-root', panel_html)
        self.assertIn('data-review-request-open', panel_html)

        m = re.search(r'<script type="application/json" class="review-request-data">(\{.*?\})</script>', panel_html)
        self.assertIsNotNone(m, "review-request-data script block missing from rendered HTML")

        payload = json.loads(m.group(1))
        self.assertEqual(payload["canonical_id"], "AUTOSAR/AP/record/SWS_CORE_00009")
        self.assertTrue(payload["version_id"].startswith("AUTOSAR/AP/record/SWS_CORE_00009@rel:R25-11#"))
        self.assertEqual(len(payload["content_hash"]), 8)
        self.assertEqual(payload["status"], "valid/unmigrated")
        self.assertEqual(
            payload["source_url"],
            "https://www.autosar.org/fileadmin/standards/R25-11/AP/AUTOSAR_AP_SWS_Core.pdf#nameddest=SWS_CORE_00009",
        )
        self.assertFalse(payload["has_open_review_request"])

    def test_strict_package_validation_and_live_ingestion_with_real_record(self):
        """Derived production metadata passes strict package validation and live ingestion."""
        rec_path = SRC_DIR / "spec" / "records" / "SWS_CORE" / "SWS_CORE_00009.json"
        with rec_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        panel_html = dm._render_review_request_panel(
            data["id"],
            {},
            data.get("status"),
            page_dir_depth=1,
            srcdir=str(SRC_DIR),
            rec_blocks=data.get("blocks"),
        )
        m = re.search(r'<script type="application/json" class="review-request-data">(\{.*?\})</script>', panel_html)
        payload = json.loads(m.group(1))

        # Ensure version store reflects the authoritative version
        vstore_root = self._root / "spec" / "versions"
        vstore_root.mkdir(parents=True, exist_ok=True)
        (vstore_root / "AUTOSAR" / "AP" / "record").mkdir(parents=True, exist_ok=True)
        (vstore_root / "AUTOSAR" / "AP" / "record" / "SWS_CORE_00009.jsonl").write_text(
            json.dumps({
                "version_id": payload["version_id"],
                "canonical_id": payload["canonical_id"],
                "release": "R25-11",
                "content": payload["content_hash"],
                "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }) + "\n",
            encoding="utf-8",
        )

        # Construct conformant package from derived payload
        package = {
            "schema": "review-request-package@v1",
            "client_schema_version": "1.0.0",
            "request_id": f"review-request:{rrp.uuid7()}",
            "target_canonical_id": payload["canonical_id"],
            "target_version_id": payload["version_id"],
            "target_content_hash": payload["content_hash"],
            "target_status_snapshot": payload["status"],
            "source_url": payload["source_url"],
            "category": "factual-accuracy",
            "rationale": "Verify copy constructor exception safety specification in R25-11.",
            "evidence_refs": [],
            "actor_claim": {
                "display_name": "QA Auditor",
                "identity_kind": "self_declared",
            },
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "transport": "json_export",
        }

        # Strict validation
        errors = rrp.validate(package)
        self.assertEqual(errors, [], f"Package failed strict validation: {errors}")

        # Ingestion into queue
        result = rri.ingest(
            package,
            apply=True,
            records_root=self._root / "spec" / "records",
            versions_root=vstore_root,
        )
        self.assertEqual(result["outcome"], "ok", f"Ingestion failed: {result['errors']}")
        self.assertIsNotNone(result["path"])
        self.assertTrue(Path(result["path"]).exists())

    def test_queue_lookup_does_not_leak_local_filesystem_paths(self):
        """Open queue state renders in panel without leaking local filesystem paths."""
        open_item_path = cf.OPEN_DIR / "req-test-prod.json"
        open_item_path.write_text(json.dumps({
            "item_kind": "review-request",
            "id": "req-test-prod",
            "identity": "github_authenticated",
            "decided_by": "auditor-jane",
            "created": "2026-09-01T12:00:00Z",
            "decision_basis": {
                "target_canonical_id": "AUTOSAR/AP/record/SWS_CORE_00009",
                "target_version_id": "AUTOSAR/AP/record/SWS_CORE_00009@rel:R25-11#abc12345",
                "target_status_snapshot": "valid/unmigrated",
                "authoritative_actor": "auditor-jane",
                "request_id": "req-test-prod",
            },
        }), encoding="utf-8")

        dm._REVIEW_REQUEST_INDEX = None
        panel_html = dm._render_review_request_panel(
            "SWS_CORE_00009",
            {},
            {"state": "valid/unmigrated"},
            page_dir_depth=1,
            srcdir=str(self._root),
        )

        self.assertIn("review-request-duplicate", panel_html)
        self.assertIn("req-test-prod", panel_html)
        self.assertIn("auditor-jane", panel_html)
        self.assertNotIn("Queue file", panel_html)
        self.assertNotIn(str(self._root), panel_html)
        self.assertNotIn("spec/curation-queue", panel_html)

    def test_corpus_wide_coverage_inventory(self):
        """Corpus coverage audit runs and validates 100% of 3,882 production records."""
        report = vrrc.audit_corpus_coverage(SRC_DIR)
        self.assertTrue(report["passed"], f"Corpus coverage audit failed: {report['errors'][:5]}")
        self.assertEqual(report["totals"]["total_records"], 3882)
        self.assertEqual(report["totals"]["eligible_records"], 3882)
        self.assertEqual(report["totals"]["excluded_records"], 0)
        self.assertEqual(report["totals"]["rendered_actions"], 3882)
        self.assertEqual(len(report["errors"]), 0)


if __name__ == "__main__":
    unittest.main()
