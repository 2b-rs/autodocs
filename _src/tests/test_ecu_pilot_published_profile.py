#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ecu_pilot_published_profile.py -- Unit tests for ECU Pilot Published Profile Engine (Task 0018-09)."""

import json
from pathlib import Path

import pytest
from _src.tools.ecu_pilot_published_profile import (
    ASSESSED_BASELINE,
    ASSESSED_ORGANIZATION,
    ASSESSED_PRODUCT,
    ASSESSED_PROJECT,
    BASELINE_COMMIT,
    PAM_VERSION,
    SCHEMA_PUBLISHED_PROFILE,
    VALIDITY_PERIOD,
    assemble_pilot_published_profile,
    get_all_17_published_pilot_ratings,
    get_standard_pilot_next_cycle_plan,
    write_pilot_published_profile,
)


def test_get_all_17_published_pilot_ratings():
    ratings = get_all_17_published_pilot_ratings()
    assert len(ratings) == 17

    for r in ratings:
        assert r.pa11_rating == "F"
        assert r.pa21_rating == "F"
        assert r.pa22_rating == "F"
        assert r.capability_level_achieved == 2
        assert r.process_disposition == "ACHIEVED_LEVEL_2"
        assert "ISO/IEC 33020" in r.rating_scale
        assert r.evidence_count >= 2


def test_get_standard_pilot_next_cycle_plan():
    plan = get_standard_pilot_next_cycle_plan()
    assert len(plan) == 3

    plan_ids = [p.item_id for p in plan]
    assert plan_ids == ["PLAN-PILOT-01", "PLAN-PILOT-02", "PLAN-PILOT-03"]

    for p in plan:
        assert len(p.title) > 5
        assert p.target_date.startswith("2026-")
        assert len(p.owner) > 0
        assert len(p.description) >= 20


def test_assemble_pilot_published_profile():
    payload = assemble_pilot_published_profile()
    assert payload["schema"] == SCHEMA_PUBLISHED_PROFILE
    assert payload["profile_id"] == f"ECU-PILOT-PUBLISHED-PROFILE-{ASSESSED_BASELINE}"

    dec = payload["management_decision"]
    assert dec["decision_id"] == "DEC-0018-PUBLISH-20260919-01"
    assert dec["decision_disposition"] == "APPROVED_FOR_PUBLICATION"
    assert "jadzia" in dec["approving_authority"]
    assert dec["decision_date"] == "2026-09-19"
    assert len(dec["decision_text"]) >= 50

    scope = payload["organizational_and_product_scope"]
    assert scope["organization_name"] == ASSESSED_ORGANIZATION
    assert scope["product_id"] == ASSESSED_PRODUCT
    assert scope["project_id"] == ASSESSED_PROJECT
    assert scope["release_instance"] == ASSESSED_BASELINE
    assert scope["commit_reference"] == BASELINE_COMMIT

    gov = payload["assessment_methodology_and_governance"]
    assert gov["pam_version"] == PAM_VERSION
    assert gov["validity_period"] == VALIDITY_PERIOD
    assert len(payload["published_profile_sha256"]) == 64

    policy = payload["boundary_and_claim_policy"]
    assert policy["claim_policy_rule"] == "NO_BLANKET_ORGANIZATIONAL_CL2_CLAIM"
    assert "does not constitute an organizational maturity rating" in policy["claim_statement"]

    ratings = payload["published_process_ratings"]
    assert len(ratings) == 17
    for r in ratings:
        assert r["capability_level_achieved"] == 2
        assert r["process_disposition"] == "ACHIEVED_LEVEL_2"

    statements = payload["separate_governance_statements"]
    assert "odo" in statements["assessment_disposition_statement"]["author"]
    assert "jadzia" in statements["execution_responsibility_statement"]["author"]

    limitations = payload["accepted_limitations"]
    assert len(limitations) == 3


def test_write_and_digest_stability(tmp_path: Path):
    json_path = tmp_path / "test-pilot-published-profile.json"
    md_path = tmp_path / "test-pilot-published-profile.md"

    write_pilot_published_profile(json_path, md_path)

    assert json_path.exists()
    assert md_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema"] == SCHEMA_PUBLISHED_PROFILE
    assert data["management_decision"]["decision_disposition"] == "APPROVED_FOR_PUBLICATION"

    md_text = md_path.read_text(encoding="utf-8")
    assert "Automotive ECU Pilot Published Process Capability Assessment Profile" in md_text
    assert "NO_BLANKET_ORGANIZATIONAL_CL2_CLAIM" in md_text
    assert "DEC-0018-PUBLISH-20260919-01" in md_text
    assert "PLAN-PILOT-01" in md_text
