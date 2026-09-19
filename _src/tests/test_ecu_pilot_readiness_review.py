#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_pilot_readiness_review.py -- Unit tests for ECU Pilot Independent Readiness Review (Task 0018-08)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_pilot_readiness_review import (
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    ORIGINAL_BASELINE,
    ORIGINAL_COMMIT,
    REASSESSMENT_COMMIT,
    REVISED_BASELINE,
    SCHEMA_READINESS,
    STANDARD_REF,
    assemble_pilot_readiness_review_record,
    get_all_3_pilot_accepted_limitations,
    get_all_7_pilot_review_dimensions,
    write_pilot_readiness_review_record,
)


def test_get_all_7_pilot_review_dimensions():
    dims = get_all_7_pilot_review_dimensions()
    assert len(dims) == 7

    dim_ids = [d.dimension_id for d in dims]
    expected_ids = [
        "DIM-PILOT-01",
        "DIM-PILOT-02",
        "DIM-PILOT-03",
        "DIM-PILOT-04",
        "DIM-PILOT-05",
        "DIM-PILOT-06",
        "DIM-PILOT-07",
    ]
    assert dim_ids == expected_ids

    for d in dims:
        assert d.verdict == "CONFORMANT"
        assert len(d.evaluated_criteria) >= 2
        assert len(d.review_observations) >= 30
        assert len(d.reviewer_notes) >= 10


def test_get_all_3_pilot_accepted_limitations():
    limitations = get_all_3_pilot_accepted_limitations()
    assert len(limitations) == 3

    lim_ids = [l.limitation_id for l in limitations]
    assert lim_ids == ["LIMIT-PILOT-01", "LIMIT-PILOT-02", "LIMIT-PILOT-03"]

    for l in limitations:
        assert len(l.title) > 5
        assert len(l.scope_boundary) > 0
        assert len(l.rationale) >= 30
        assert len(l.accepted_by) > 0
        assert len(l.mitigation_or_next_step) >= 10


def test_assemble_pilot_readiness_review_record():
    payload = assemble_pilot_readiness_review_record()
    assert payload["schema"] == SCHEMA_READINESS
    assert payload["readiness_review_id"] == f"ECU-PILOT-READINESS-{ORIGINAL_BASELINE}"

    gov = payload["governance"]
    assert gov["product_id"] == ASSESSED_PRODUCT
    assert gov["project_id"] == ASSESSED_PROJECT
    assert gov["baseline_id"] == ORIGINAL_BASELINE
    assert gov["revised_baseline_id"] == REVISED_BASELINE
    assert gov["baseline_commit"] == ORIGINAL_COMMIT
    assert gov["reassessment_commit"] == REASSESSMENT_COMMIT
    assert gov["overall_readiness_status"] == "READY_FOR_EXTERNAL_AUDIT"
    assert len(payload["readiness_review_sha256"]) == 64

    summary = payload["review_summary"]
    assert summary["total_dimensions_evaluated"] == 7
    assert summary["conformant_dimensions_count"] == 7
    assert summary["acceptable_with_limitations_count"] == 0
    assert summary["non_conformant_dimensions_count"] == 0
    assert summary["total_accepted_limitations"] == 3
    assert summary["readiness_disposition"] == "LEVEL_2_READINESS_CONFIRMED_RECOMMEND_EXTERNAL_AUDIT"

    verdict = payload["independent_recommendation_and_verdict"]
    assert verdict["readiness_verdict"] == "APPROVED_FOR_FORMAL_EXTERNAL_ASSESSMENT"
    assert "RECOMMENDATION: The project has achieved internal Level-2" in verdict["recommendation_statement"]
    assert "kira" in verdict["review_signoffs"]["independent_reviewer_signature"]
    assert "odo" in verdict["review_signoffs"]["lead_assessor_acknowledgment"]
    assert "jake" in verdict["review_signoffs"]["qa_manager_acknowledgment"]
    assert "jadzia" in verdict["review_signoffs"]["project_sponsor_acknowledgment"]


def test_write_and_digest_stability(tmp_path: Path):
    json_path = tmp_path / "test-pilot-readiness.json"
    md_path = tmp_path / "test-pilot-readiness.md"

    write_pilot_readiness_review_record(json_path, md_path)

    assert json_path.exists()
    assert md_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == SCHEMA_READINESS
    assert data["review_summary"]["readiness_disposition"] == "LEVEL_2_READINESS_CONFIRMED_RECOMMEND_EXTERNAL_AUDIT"

    md_text = md_path.read_text(encoding="utf-8")
    assert "Automotive ECU Pilot Independent Assessment Readiness Review & Limitations Record" in md_text
    assert "DIM-PILOT-01" in md_text
    assert "LIMIT-PILOT-01" in md_text
    assert "APPROVED_FOR_FORMAL_EXTERNAL_ASSESSMENT" in md_text
