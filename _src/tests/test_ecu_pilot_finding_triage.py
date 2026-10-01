#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_pilot_finding_triage.py -- Unit tests for ECU Finding Triage Engine (Task 0018-06)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_pilot_finding_triage import (
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    ASSESSMENT_REPORT_ID,
    SCHEMA_TRIAGE,
    STANDARD_REF,
    TARGET_BASELINE,
    TARGET_COMMIT,
    build_finding_triage_record,
    generate_json_artifacts,
    get_all_5_triaged_findings,
)


def test_get_all_5_triaged_findings():
    findings = get_all_5_triaged_findings()
    assert len(findings) == 5

    expected_ids = {"FIND-0018-01", "FIND-0018-02", "FIND-0018-03", "FIND-0018-04", "FIND-0018-05"}
    assert {f.finding_id for f in findings} == expected_ids

    for f in findings:
        assert f.triage_status == "TRIAGED_AND_BOUNDED"
        assert len(f.root_cause) > 20
        assert len(f.impact_analysis) > 20
        assert len(f.owner) > 0
        assert len(f.due_date) > 0
        assert f.triage_disposition in ("APPROVED_CORRECTION", "ACCEPTED_RESIDUAL")
        assert len(f.child_remediation_task_id) > 0
        assert len(f.reverification_criteria) >= 2


def test_build_finding_triage_record():
    record = build_finding_triage_record()
    assert record.schema == SCHEMA_TRIAGE
    assert record.product_id == ASSESSED_PRODUCT
    assert record.project_id == ASSESSED_PROJECT
    assert record.baseline_id == TARGET_BASELINE
    assert record.commit_sha == TARGET_COMMIT
    assert record.assessment_report_id == ASSESSMENT_REPORT_ID
    assert record.standard_reference == STANDARD_REF
    assert record.total_findings == 5
    assert record.approved_corrections_count == 3
    assert record.accepted_residuals_count == 2
    assert len(record.record_sha256) == 64
    assert any("Feature 0019" in g for g in record.governance_safeguards)


def test_generate_json_artifacts(tmp_path: Path):
    res = generate_json_artifacts(tmp_path)
    record_path = Path(res["record_path"])
    assert record_path.exists()

    with open(record_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == SCHEMA_TRIAGE
    assert data["total_findings"] == 5
    assert data["approved_corrections_count"] == 3
    assert data["accepted_residuals_count"] == 2
