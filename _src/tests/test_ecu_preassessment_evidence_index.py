#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_preassessment_evidence_index.py -- Unit tests for ECU Pre-Assessment Evidence Index Engine (Task 0018-04)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_preassessment_evidence_index import (
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    SCHEMA_PREASSESSMENT_INDEX,
    STANDARD_REF,
    TARGET_BASELINE,
    TARGET_COMMIT,
    build_preassessment_evidence_index,
    generate_json_artifacts,
    get_all_34_preassessment_artifacts,
    validate_preassessment_index,
)


def test_get_all_34_preassessment_artifacts():
    artifacts = get_all_34_preassessment_artifacts()
    assert len(artifacts) == 34

    expected_pids = {
        "SWE.1", "SWE.2", "SWE.3", "SWE.4", "SWE.5", "SWE.6",
        "SYS.2", "SYS.3", "VAL.1", "SPL.2",
        "SUP.1", "SUP.8", "SUP.9", "SUP.10",
        "MAN.3", "MAN.5", "MAN.6",
    }
    assert {a.process_id for a in artifacts} == expected_pids

    for a in artifacts:
        assert a.product_id == ASSESSED_PRODUCT
        assert a.project_id == ASSESSED_PROJECT
        assert a.baseline_id == TARGET_BASELINE
        assert a.commit_sha == TARGET_COMMIT
        assert a.validity == "frozen"
        assert a.authenticity_verified is True
        assert len(a.sha256) == 64
        assert len(a.outcome_indicators) > 0


def test_build_preassessment_evidence_index():
    index = build_preassessment_evidence_index()
    assert index.schema == SCHEMA_PREASSESSMENT_INDEX
    assert index.total_processes == 17
    assert index.total_artifacts == 34
    assert len(index.index_sha256) == 64
    assert "SESS-PILOT" in index.interview_records_rule
    assert any("Feature 0019" in g for g in index.isolation_guarantees)
    assert len(index.process_attribute_coverage["PA_1.1_PROCESS_PERFORMANCE"]) > 0
    assert len(index.process_attribute_coverage["PA_2.1_PERFORMANCE_MANAGEMENT"]) > 0
    assert len(index.process_attribute_coverage["PA_2.2_WORK_PRODUCT_MANAGEMENT"]) > 0


def test_validate_preassessment_index():
    index = build_preassessment_evidence_index()
    valid, errors = validate_preassessment_index(index)
    assert valid is True
    assert len(errors) == 0


def test_generate_json_artifacts(tmp_path: Path):
    res = generate_json_artifacts(tmp_path)
    report_path = Path(res["report_path"])
    assert report_path.exists()

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == SCHEMA_PREASSESSMENT_INDEX
    assert data["total_processes"] == 17
    assert data["total_artifacts"] == 34
