#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_pilot_reassessment_cycle.py -- Unit tests for ECU Pilot Reassessment Cycle Engine (Task 0018-07)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_pilot_reassessment_cycle import (
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    ORIGINAL_BASELINE,
    ORIGINAL_COMMIT,
    REASSESSMENT_COMMIT,
    REVISED_BASELINE,
    SCHEMA_REASSESSMENT,
    STANDARD_REF,
    assemble_pilot_reassessment_cycle_record,
    get_all_5_pilot_correction_executions,
    get_all_17_reassessed_process_entries,
    write_pilot_reassessment_cycle_record,
)


def test_get_all_5_pilot_correction_executions():
    corrections = get_all_5_pilot_correction_executions()
    assert len(corrections) == 5

    corr_ids = [c.correction_id for c in corrections]
    assert corr_ids == ["CORR-0018-01", "CORR-0018-02", "CORR-0018-03", "CORR-0018-04", "CORR-0018-05"]

    verified_count = sum(1 for c in corrections if c.closure_status == "VERIFIED_CLOSED")
    accepted_count = sum(1 for c in corrections if c.closure_status == "ACCEPTED_RESIDUAL_LOGGED")
    assert verified_count == 3
    assert accepted_count == 2

    for c in corrections:
        assert len(c.implementation_summary) >= 20
        assert len(c.reverification_method) >= 20
        assert c.reverification_result.startswith("PASS")
        assert len(c.effectiveness_evaluation) >= 20
        assert len(c.owner) > 0
        assert c.closed_at.startswith("2026-")


def test_get_all_17_reassessed_process_entries():
    entries = get_all_17_reassessed_process_entries()
    assert len(entries) == 17

    for e in entries:
        assert e.reassessed_pa11_rating == "F"
        assert e.reassessed_pa21_rating == "F"
        assert e.reassessed_pa22_rating == "F"
        assert e.reassessed_capability_level == 2
        assert e.cl2_blocking_findings_count == 0
        assert e.cl2_target_met is True
        assert e.status == "CONFIRMED_LEVEL_2"
        assert len(e.reassessment_justification) >= 20


def test_assemble_pilot_reassessment_cycle_record():
    payload = assemble_pilot_reassessment_cycle_record()
    assert payload["schema"] == SCHEMA_REASSESSMENT
    assert payload["reassessment_record_id"] == f"ECU-PILOT-REASSESS-{ORIGINAL_BASELINE}"

    gov = payload["governance"]
    assert gov["product_id"] == ASSESSED_PRODUCT
    assert gov["project_id"] == ASSESSED_PROJECT
    assert gov["original_baseline"] == ORIGINAL_BASELINE
    assert gov["revised_baseline"] == REVISED_BASELINE
    assert gov["original_commit"] == ORIGINAL_COMMIT
    assert gov["reassessment_commit"] == REASSESSMENT_COMMIT
    assert gov["cycle_status"] == "REASSESSMENT_PASSED_LEVEL_2_CERTIFIED"
    assert len(payload["reassessment_record_sha256"]) == 64

    summary = payload["cycle_summary"]
    assert summary["total_in_scope_processes"] == 17
    assert summary["processes_achieving_level2"] == 17
    assert summary["level2_compliance_rate_percent"] == 100.0
    assert summary["total_corrections_executed"] == 5
    assert summary["corrections_verified_closed"] == 3
    assert summary["accepted_residuals_count"] == 2
    assert summary["open_corrections_count"] == 0
    assert summary["cl2_blocking_findings_count"] == 0
    assert summary["exit_criteria_disposition"] == "LEVEL_2_EXIT_GATE_CLEARED"

    exit_eval = payload["exit_criteria_evaluation"]
    assert len(exit_eval) == 4
    for k, v in exit_eval.items():
        assert v["status"] == "SATISFIED"

    cert = payload["formal_certification_signoff"]
    assert cert["verdict"] == "ASPICE_LEVEL_2_CAPABILITY_RECONFIRMED"
    assert "odo" in cert["signoffs"]["lead_assessor_signature"]
    assert "jake" in cert["signoffs"]["qa_manager_signature"]
    assert "jadzia" in cert["signoffs"]["project_lead_sponsor_signature"]


def test_write_and_digest_stability(tmp_path: Path):
    json_path = tmp_path / "test-pilot-reassessment.json"
    md_path = tmp_path / "test-pilot-reassessment.md"

    write_pilot_reassessment_cycle_record(json_path, md_path)

    assert json_path.exists()
    assert md_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == SCHEMA_REASSESSMENT
    assert data["cycle_summary"]["exit_criteria_disposition"] == "LEVEL_2_EXIT_GATE_CLEARED"

    md_text = md_path.read_text(encoding="utf-8")
    assert "Automotive ECU Pilot Post-Correction Reassessment & Level-2 Capability Confirmation Record" in md_text
    assert "CORR-0018-01" in md_text
    assert "LEVEL_2_EXIT_GATE_CLEARED" in md_text
    assert "ASPICE_LEVEL_2_CAPABILITY_RECONFIRMED" in md_text
