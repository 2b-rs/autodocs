#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_pilot_repeatability.py -- Unit tests for Automotive ECU Pilot Repeatability Engine (Task 0018-03)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_pilot_repeatability import (
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    PILOT1_BASELINE,
    PILOT2_BASELINE,
    SCHEMA_REPEATABILITY_EVALUATION,
    STANDARD_REF,
    evaluate_repeatability,
    generate_json_artifacts,
    get_all_17_repeatability_comparisons,
    get_standard_process_adjustments,
)


def test_get_standard_process_adjustments():
    adjs = get_standard_process_adjustments()
    assert len(adjs) == 4
    expected_ids = {"ADJ-001", "ADJ-002", "ADJ-003", "ADJ-004"}
    assert {a.adjustment_id for a in adjs} == expected_ids
    for a in adjs:
        assert a.verification_status == "VERIFIED_IN_PILOT2"
        assert a.implemented_in_baseline == PILOT2_BASELINE


def test_get_all_17_repeatability_comparisons():
    comparisons = get_all_17_repeatability_comparisons()
    assert len(comparisons) == 17

    expected_pids = {
        "SWE.1", "SWE.2", "SWE.3", "SWE.4", "SWE.5", "SWE.6",
        "SYS.2", "SYS.3", "VAL.1", "SPL.2",
        "SUP.1", "SUP.8", "SUP.9", "SUP.10",
        "MAN.3", "MAN.5", "MAN.6",
    }
    assert {c.process_id for c in comparisons} == expected_pids

    for c in comparisons:
        assert c.repeatability_verdict == "REPEATABLE_AND_CONTROLLED"
        assert c.learning_loop_effective is True
        assert 0.90 <= c.stability_index <= 1.0
        assert c.pilot1_metrics.four_eyes_verified is True
        assert c.pilot2_metrics.four_eyes_verified is True
        assert c.pilot2_metrics.unresolved_deviations == 0


def test_evaluate_repeatability():
    report = evaluate_repeatability()
    assert report.schema == SCHEMA_REPEATABILITY_EVALUATION
    assert report.product_id == ASSESSED_PRODUCT
    assert report.project_id == ASSESSED_PROJECT
    assert report.pilot1_baseline == PILOT1_BASELINE
    assert report.pilot2_baseline == PILOT2_BASELINE
    assert report.standard_reference == STANDARD_REF
    assert report.total_processes_evaluated == 17
    assert report.repeatable_processes_count == 17
    assert report.overall_process_stability_index >= 0.95
    assert report.overall_repeatability_verdict == "CONFIRMED_REPEATABLE_AND_STABLE"
    assert len(report.report_sha256) == 64
    assert any("Feature 0019" in g for g in report.repeatability_guarantees)


def test_generate_json_artifacts(tmp_path: Path):
    res = generate_json_artifacts(tmp_path)
    report_path = Path(res["report_path"])
    assert report_path.exists()

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == SCHEMA_REPEATABILITY_EVALUATION
    assert data["total_processes_evaluated"] == 17
    assert data["overall_repeatability_verdict"] == "CONFIRMED_REPEATABLE_AND_STABLE"
