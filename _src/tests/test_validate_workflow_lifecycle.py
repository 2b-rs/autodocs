#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOOLS = os.path.join(_SRC, "tools")
for path in (_SRC, _TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

import curation_item as ci  # noqa: E402
import validate  # noqa: E402


class WorkflowLifecycleValidationTests(unittest.TestCase):
    def test_queue_roots_are_below_src_spec(self):
        with patch.object(validate, "SRC", "/tmp/example/_src"):
            roots = dict(validate._workflow_queue_roots())
        self.assertEqual(
            roots,
            {
                "review-queue": "/tmp/example/_src/spec/review-queue",
                "curation-queue": "/tmp/example/_src/spec/curation-queue",
            },
        )

    def test_validator_scans_both_real_queue_layouts(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            src = Path(tmp) / "_src"
            review = src / "spec" / "review-queue" / "open" / "review.json"
            curation = src / "spec" / "curation-queue" / "open" / "curation.json"
            review.parent.mkdir(parents=True)
            curation.parent.mkdir(parents=True)
            review.write_text(
                json.dumps({"schema": "review-flag@v1", "id": "SWS_LOG_00201"}),
                encoding="utf-8",
            )
            curation.write_text(
                json.dumps(
                    {
                        "schema": "curation-flag@v1",
                        "id": "SWS_LOG_00202",
                        "outcome": "proposed_change",
                    }
                ),
                encoding="utf-8",
            )

            with (
                patch.object(validate, "SRC", str(src)),
                patch.object(validate, "checks_performed", []),
                patch.object(validate, "structured_findings", []),
                patch.object(validate, "problems", []),
                patch.object(ci, "from_review_flag", wraps=ci.from_review_flag) as review_adapter,
                patch.object(ci, "from_curation_flag", wraps=ci.from_curation_flag) as curation_adapter,
            ):
                validate.check_workflow_lifecycle()
                self.assertEqual(validate.problems, [])
                self.assertEqual(validate.structured_findings, [])
                self.assertEqual(validate.checks_performed, ["check_workflow_lifecycle"])

            review_adapter.assert_called_once()
            curation_adapter.assert_called_once()

    def test_malformed_queue_json_is_reported_and_does_not_abort_scan(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            src = Path(tmp) / "_src"
            invalid = src / "spec" / "review-queue" / "open" / "invalid.json"
            valid = src / "spec" / "curation-queue" / "open" / "valid.json"
            invalid.parent.mkdir(parents=True)
            valid.parent.mkdir(parents=True)
            invalid.write_text("{not json", encoding="utf-8")
            valid.write_text(
                json.dumps({"id": "SWS_LOG_00202", "outcome": "proposed_change"}),
                encoding="utf-8",
            )

            with (
                patch.object(validate, "SRC", str(src)),
                patch.object(validate, "checks_performed", []),
                patch.object(validate, "structured_findings", []),
                patch.object(validate, "problems", []),
                patch.object(ci, "from_curation_flag", wraps=ci.from_curation_flag) as curation_adapter,
            ):
                validate.check_workflow_lifecycle()
                categories = [finding["category"] for finding in validate.structured_findings]
                self.assertEqual(categories, ["invalid-curation-queue-json"])
                self.assertEqual(len(validate.problems), 1)

            curation_adapter.assert_called_once()


if __name__ == "__main__":
    unittest.main()
