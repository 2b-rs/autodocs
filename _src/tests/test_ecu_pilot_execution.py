#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_pilot_execution.py -- Unit tests for Automotive ECU Pilot Execution & Atomic Evidence Engine (Task 0018-02)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_pilot_execution import (
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    SCHEMA_PILOT_EVIDENCE_SET,
    SCHEMA_PILOT_EXECUTION,
    STANDARD_REF,
    TARGET_BASELINE,
    TARGET_COMMIT,
    generate_json_artifacts,
    get_all_17_execution_records,
    get_atomic_evidence_set,
    validate_execution_records,
)


def test_get_all_17_execution_records():
    records = get_all_17_execution_records()
    assert len(records) == 17

    expected_pids = {
        "SWE.1", "SWE.2", "SWE.3", "SWE.4", "SWE.5", "SWE.6",
        "SYS.2", "SYS.3", "VAL.1", "SPL.2",
        "SUP.1", "SUP.8", "SUP.9", "SUP.10",
        "MAN.3", "MAN.5", "MAN.6",
    }
    found_pids = {r.process_id for r in records}
    assert found_pids == expected_pids

    for r in records:
        assert r.target_capability_level == 2
        assert len(r.resource_allocation.allocated_roles) > 0
        assert 0 < r.resource_allocation.resource_utilization_pct <= 100.0
        assert r.competence_availability.availability_verified is True
        assert r.competence_availability.independence_verified is True
        assert len(r.interface_management.inbound_interfaces) > 0
        assert len(r.interface_management.outbound_interfaces) > 0
        assert r.interface_management.interface_agreements_status == "FORMALLY_AGREED_AND_BASELINE_FROZEN"
        assert r.actual_vs_plan.milestone_status == "COMPLETED_ON_SCHEDULE"
        assert r.closure.four_eyes_verified is True
        assert r.closure.dod_status == "FULLY_SATISFIED"
        assert len(r.closure.frozen_artifacts) >= 1


def test_get_atomic_evidence_set():
    records = get_all_17_execution_records()
    ev_set = get_atomic_evidence_set(records)

    assert ev_set.schema == SCHEMA_PILOT_EVIDENCE_SET
    assert ev_set.product_id == ASSESSED_PRODUCT
    assert ev_set.project_id == ASSESSED_PROJECT
    assert ev_set.baseline_id == TARGET_BASELINE
    assert ev_set.commit_sha == TARGET_COMMIT
    assert ev_set.standard_reference == STANDARD_REF
    assert ev_set.total_artifacts == len(ev_set.artifacts)
    assert ev_set.total_artifacts >= 17
    assert len(ev_set.artifacts_by_process) == 17
    assert len(ev_set.evidence_set_sha256) == 64
    assert any("Feature 0019" in g for g in ev_set.isolation_guarantees)


def test_validate_execution_records_pass():
    records = get_all_17_execution_records()
    valid, errors = validate_execution_records(records)
    assert valid is True
    assert len(errors) == 0


def test_validate_execution_records_failure_modes():
    records = get_all_17_execution_records()
    # 1. Missing process
    incomplete = records[:-1]
    valid, errors = validate_execution_records(incomplete)
    assert valid is False
    assert any("Missing required process instances" in e for e in errors)

    # 2. Four eyes violation
    records_corrupted = get_all_17_execution_records()
    records_corrupted[0].closure.four_eyes_verified = False
    valid, errors = validate_execution_records(records_corrupted)
    assert valid is False
    assert any("Four-eyes review not verified" in e for e in errors)


def test_generate_json_artifacts(tmp_path: Path):
    res = generate_json_artifacts(tmp_path)
    records_path = Path(res["records_path"])
    ev_set_path = Path(res["evidence_set_path"])

    assert records_path.exists()
    assert ev_set_path.exists()

    with open(records_path, "r", encoding="utf-8") as f:
        r_data = json.load(f)
    assert r_data["$schema"] == SCHEMA_PILOT_EXECUTION
    assert r_data["total_process_instances"] == 17

    with open(ev_set_path, "r", encoding="utf-8") as f:
        e_data = json.load(f)
    assert e_data["schema"] == SCHEMA_PILOT_EVIDENCE_SET
    assert len(e_data["artifacts"]) >= 17
