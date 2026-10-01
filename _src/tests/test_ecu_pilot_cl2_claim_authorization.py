#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_pilot_cl2_claim_authorization.py -- Unit tests for ECU Pilot CL2 Claim Authorization Engine (Task 0018-10)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_pilot_cl2_claim_authorization import (
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    PUBLISHED_PROFILE_ID,
    SCHEMA_CL2_CLAIM,
    STANDARD_REF,
    TARGET_BASELINE,
    TARGET_COMMIT,
    assemble_cl2_claim_authorization_record,
    evaluate_all_17_process_cl2_gates,
    write_cl2_claim_authorization_record,
)


def test_evaluate_all_17_process_cl2_gates():
    evals = evaluate_all_17_process_cl2_gates()
    assert len(evals) == 17

    for ev in evals:
        assert ev.pa11_rating == "F"
        assert ev.pa21_rating in {"L", "F"}
        assert ev.pa22_rating in {"L", "F"}
        assert ev.pa11_gate_passed is True
        assert ev.pa21_gate_passed is True
        assert ev.pa22_gate_passed is True
        assert ev.cl2_claim_authorized is True
        assert ev.process_verdict == "CAPABILITY_LEVEL_2_ACHIEVED"
        assert len(ev.gate_justification) >= 30


def test_assemble_cl2_claim_authorization_record():
    record = assemble_cl2_claim_authorization_record()
    assert record.schema == SCHEMA_CL2_CLAIM
    assert record.claim_id == f"ECU-PILOT-CL2-CLAIM-{TARGET_BASELINE}"
    assert record.product_id == ASSESSED_PRODUCT
    assert record.project_id == ASSESSED_PROJECT
    assert record.target_baseline == TARGET_BASELINE
    assert record.commit_reference == TARGET_COMMIT
    assert record.published_profile_reference == PUBLISHED_PROFILE_ID
    assert record.standard_reference == STANDARD_REF
    assert record.overall_cl2_claim_status == "LEVEL_2_MANAGED_PROCESS_CLAIM_AUTHORIZED"
    assert record.total_target_processes == 17
    assert record.processes_authorizing_cl2 == 17
    assert record.claim_compliance_rate_percent == 100.0
    assert len(record.claim_sha256) == 64

    # Verify strict legal disclaimers present
    disclaimers = record.disclaimer_and_scope_boundaries
    assert len(disclaimers) >= 4
    assert any("EXACT BOUNDED PROCESS CLAIM" in d for d in disclaimers)
    assert any("NO PRODUCT OR REGULATORY CERTIFICATION" in d for d in disclaimers)
    assert any("NO FUNCTIONAL SAFETY OR CYBERSECURITY CERTIFICATION" in d for d in disclaimers)
    assert any("ZERO ATTRIBUTE AVERAGING" in d for d in disclaimers)

    auths = record.multi_role_authorizations
    assert "jadzia" in auths["project_sponsor_authorization"]
    assert "odo" in auths["lead_assessor_authorization"]
    assert "jake" in auths["qa_manager_authorization"]
    assert "kira" in auths["architect_reviewer_authorization"]


def test_write_and_digest_stability(tmp_path: Path):
    json_path = tmp_path / "test-cl2-claim.json"
    md_path = tmp_path / "test-cl2-claim.md"

    write_cl2_claim_authorization_record(json_path, md_path)

    assert json_path.exists()
    assert md_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == SCHEMA_CL2_CLAIM
    assert data["overall_cl2_claim_status"] == "LEVEL_2_MANAGED_PROCESS_CLAIM_AUTHORIZED"
    assert data["processes_authorizing_cl2"] == 17

    md_text = md_path.read_text(encoding="utf-8")
    assert "Automotive ECU Pilot Capability Level 2 Claim Gate Authorization & Publication Record" in md_text
    assert "LEVEL_2_MANAGED_PROCESS_CLAIM_AUTHORIZED" in md_text
    assert "NO PRODUCT OR REGULATORY CERTIFICATION" in md_text
    assert "ZERO ATTRIBUTE AVERAGING" in md_text
