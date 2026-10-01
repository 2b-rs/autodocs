#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_pilot_assessment.py -- Unit tests for ECU Level-2 Assessment & Profile Engine (Task 0018-05)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_pilot_assessment import (
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    SCHEMA_ASSESSMENT_REPORT,
    SCHEMA_CAPABILITY_PROFILE,
    STANDARD_REF,
    TARGET_BASELINE,
    TARGET_COMMIT,
    build_pilot_assessment_report,
    generate_json_artifacts,
    get_all_6_interview_sessions,
    get_all_17_process_capability_entries,
    get_standard_pilot_findings,
)


def test_get_all_6_interview_sessions():
    sessions = get_all_6_interview_sessions()
    assert len(sessions) == 6
    expected_ids = {"SESS-PILOT-01", "SESS-PILOT-02", "SESS-PILOT-03", "SESS-PILOT-04", "SESS-PILOT-05", "SESS-PILOT-06"}
    assert {s.session_id for s in sessions} == expected_ids
    for s in sessions:
        assert s.assessor_verdict == "CONFORMANT_LEVEL_2"
        assert len(s.interviewees) >= 2
        assert len(s.evidence_examined) >= 2


def test_get_standard_pilot_findings():
    findings = get_standard_pilot_findings()
    assert len(findings) == 5
    assert all(f.status == "LOGGED_FOR_TRIAGE" for f in findings)
    assert all(f.category in ("OBSERVATION", "OFI") for f in findings)


def test_get_all_17_process_capability_entries():
    entries = get_all_17_process_capability_entries()
    assert len(entries) == 17
    for e in entries:
        assert e.pa11_rating == "F"
        assert e.pa21_rating == "F"
        assert e.pa22_rating == "F"
        assert e.capability_level_achieved == 2
        assert len(e.strengths) >= 1
        assert len(e.evidence_references) >= 2
        assert len(e.interview_references) >= 1


def test_build_pilot_assessment_report():
    report = build_pilot_assessment_report()
    assert report.schema == SCHEMA_ASSESSMENT_REPORT
    assert report.product_id == ASSESSED_PRODUCT
    assert report.project_id == ASSESSED_PROJECT
    assert report.baseline_id == TARGET_BASELINE
    assert report.commit_sha == TARGET_COMMIT
    assert report.standard_reference == STANDARD_REF
    assert report.overall_disposition == "CAPABILITY_LEVEL_2_ACHIEVED"
    assert report.total_processes_assessed == 17
    assert report.level2_achieved_count == 17
    assert len(report.capability_profile) == 17
    for pid, pdata in report.capability_profile.items():
        assert pdata["capability_level"] == 2
        assert pdata["status"] == "ACHIEVED_LEVEL_2"
    assert len(report.report_sha256) == 64
    assert any("Feature 0019" in g for g in report.isolation_guarantees)


def test_generate_json_artifacts(tmp_path: Path):
    res = generate_json_artifacts(tmp_path)
    report_path = Path(res["report_path"])
    profile_path = Path(res["profile_path"])

    assert report_path.exists()
    assert profile_path.exists()

    with open(report_path, "r", encoding="utf-8") as f:
        r_data = json.load(f)
    assert r_data["schema"] == SCHEMA_ASSESSMENT_REPORT
    assert r_data["overall_disposition"] == "CAPABILITY_LEVEL_2_ACHIEVED"

    with open(profile_path, "r", encoding="utf-8") as f:
        p_data = json.load(f)
    assert p_data["$schema"] == SCHEMA_CAPABILITY_PROFILE
    assert p_data["capability_level_achieved"] == 2
