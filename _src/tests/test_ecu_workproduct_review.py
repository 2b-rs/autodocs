#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_workproduct_review.py -- Unit tests for Automotive ECU PA 2.2 Work-Product Review Engine (Task 0015-10)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_workproduct_review import (
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    SCHEMA_WORKPRODUCT_REVIEW,
    STANDARD_REF,
    TARGET_BASELINE,
    TARGET_COMMIT,
    evaluate_workproduct_review_coverage,
    generate_json_artifacts,
    get_all_17_workproduct_review_records,
    get_standard_no_review_classifications,
)


def test_get_standard_no_review_classifications():
    no_rev = get_standard_no_review_classifications()
    assert len(no_rev) >= 2
    types = {n.work_product_type for n in no_rev}
    assert "TRANSIENT_INTERMEDIATE_OBJECT_FILE" in types
    assert "TRANSIENT_LINTER_SCRATCH_CACHE" in types
    for n in no_rev:
        assert len(n.justification) > 20
        assert len(n.approval_authority) > 0


def test_get_all_17_workproduct_review_records():
    records = get_all_17_workproduct_review_records()
    assert len(records) >= 17

    process_ids = {r.process_id for r in records}
    expected_pids = {
        "SWE.1", "SWE.2", "SWE.3", "SWE.4", "SWE.5", "SWE.6",
        "SYS.2", "SYS.3", "VAL.1", "SPL.2",
        "SUP.1", "SUP.8", "SUP.9", "SUP.10",
        "MAN.3", "MAN.5", "MAN.6",
    }
    assert process_ids == expected_pids

    for r in records:
        assert r.author != r.primary_reviewer, f"4-eyes violation in {r.review_id}"
        assert r.four_eyes_verified is True
        assert r.review_decision in ("APPROVED_WITHOUT_RESERVATION", "APPROVED_AFTER_REVISION")
        assert len(r.criteria.content_criteria) > 0
        assert len(r.criteria.quality_criteria) > 0
        assert len(r.criteria.review_criteria) > 0
        assert len(r.resulting_revisions) > 0
        assert len(r.consistency_checks) > 0
        for f in r.findings:
            assert f.status in ("RESOLVED", "VERIFIED_CLOSED")


def test_evaluate_workproduct_review_coverage():
    report = evaluate_workproduct_review_coverage()
    assert report.schema == SCHEMA_WORKPRODUCT_REVIEW
    assert report.product_id == ASSESSED_PRODUCT
    assert report.project_id == ASSESSED_PROJECT
    assert report.baseline_id == TARGET_BASELINE
    assert report.commit_sha == TARGET_COMMIT
    assert report.standard_reference == STANDARD_REF
    assert report.total_processes_evaluated == 17
    assert report.review_coverage_pct == 100.0
    assert report.unresolved_findings_count == 0
    assert report.four_eyes_compliance_pct == 100.0
    assert report.gate_verdict.startswith("PASS")
    assert len(report.report_sha256) == 64
    assert any("Feature 0019" in g for g in report.isolation_guarantees)


def test_generate_json_artifacts(tmp_path: Path):
    res = generate_json_artifacts(tmp_path)
    report_path = Path(res["report_path"])
    assert report_path.exists()

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == SCHEMA_WORKPRODUCT_REVIEW
    assert data["review_coverage_pct"] == 100.0
    assert data["gate_verdict"].startswith("PASS")
