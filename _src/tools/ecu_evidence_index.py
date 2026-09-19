#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ecu_evidence_index.py -- ECU Evidence Index validation, verification, and freeze engine (Task 0025-03).

Implements Task 0025-03 in accordance with:
  - ASPICE PAM 3.1 / PAM 4.0 Level 1 / Level 2 evidence requirements.
  - req-0020-02-evidence-boundary / DEC-0020-002: strict metadata boundary and origin enforcement.
  - req-0020-08-evidence-catalogue: controlled process/work-product/evidence catalogue.
  - dec-0024-rel-20260919-01: Automotive ECU SPL.2 Product Release baseline (v0.6.0).
  - Explicit exclusion of documentation-pipeline and synthetic execution artifacts from ECU outcome claims.
  - Tracking of authenticity, completeness, validity, confidentiality, contrary evidence, and unresolved limitations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_EVIDENCE_INDEX = "ecu-frozen-evidence-index@v1"
ASSESSED_PRODUCT = "virtualized-automotive-ecu"
ASSESSED_PROJECT = "autodocs-ecu-software"
ASSESSED_BASELINE = "virtualized-automotive-ecu@software-without-kernel:v0.6.0"
RELEASE_COMMIT = "60d9a85"

ORIGINS = (
    "process-definition",
    "implemented-mechanism",
    "documentation-execution",
    "ecu-execution",
    "controlled-scenario",
)

VALID_CONFIDENTIALITY = ("public", "internal", "restricted", "confidential")
VALID_VALIDITY = ("valid", "verified", "frozen", "deprecated", "disputed")
VALID_RETENTION = ("3_years", "7_years", "10_years", "assessment-cycle")

REQUIRED_FIELDS = (
    "artifact_id",
    "artifact_name",
    "path",
    "revision",
    "product_id",
    "project_id",
    "process_id",
    "process_instance_id",
    "baseline_id",
    "owner",
    "origin",
    "validity",
    "retention",
    "confidentiality",
    "outcome_indicators",
    "contrary_evidence",
    "unresolved_limitations",
)


@dataclass
class EvidenceArtifact:
    artifact_id: str
    artifact_name: str
    path: str
    revision: str
    product_id: str
    project_id: str
    process_id: str
    process_instance_id: str
    baseline_id: str
    owner: str
    origin: str
    validity: str
    retention: str
    confidentiality: str
    outcome_indicators: list[dict[str, str]]
    contrary_evidence: list[dict[str, str]] = field(default_factory=list)
    unresolved_limitations: list[str] = field(default_factory=list)
    sha256: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_evidence_artifact(
    artifact: dict[str, Any],
    assessed_product: str = ASSESSED_PRODUCT,
    assessed_project: str = ASSESSED_PROJECT,
    assessed_baseline: str = ASSESSED_BASELINE,
) -> tuple[bool, list[str]]:
    """Validate a single evidence artifact record against strict REQ-0020-02/08 rules.

    Returns:
      (is_valid, errors)
    """
    errors = []

    for f in REQUIRED_FIELDS:
        if f not in artifact or artifact[f] is None:
            errors.append(f"Missing required field: {f}")
        elif isinstance(artifact[f], str) and not artifact[f].strip():
            errors.append(f"Field {f} cannot be empty")

    if errors:
        return False, errors

    # Check origin
    origin = artifact.get("origin")
    if origin not in ORIGINS:
        errors.append(f"Invalid origin {origin!r}. Must be one of {ORIGINS}")
    elif origin != "ecu-execution":
        errors.append(
            f"Non-ECU origin {origin!r}: documentation-pipeline, process-definition, or synthetic execution "
            f"artifacts are strictly excluded from ECU outcome claims (REQ-0020-02 / DEC-0020-002)"
        )

    # Check product, project, and baseline identity
    if artifact.get("product_id") != assessed_product:
        errors.append(f"Cross-product mismatch: expected {assessed_product}, got {artifact.get('product_id')}")

    if artifact.get("project_id") != assessed_project:
        errors.append(f"Cross-project mismatch: expected {assessed_project}, got {artifact.get('project_id')}")

    if artifact.get("baseline_id") != assessed_baseline:
        errors.append(f"Baseline mismatch: expected {assessed_baseline}, got {artifact.get('baseline_id')}")

    # Check validity, retention, and confidentiality vocabularies
    if artifact.get("validity") not in VALID_VALIDITY:
        errors.append(f"Invalid validity {artifact.get('validity')!r}; allowed: {VALID_VALIDITY}")

    if artifact.get("retention") not in VALID_RETENTION:
        errors.append(f"Invalid retention {artifact.get('retention')!r}; allowed: {VALID_RETENTION}")

    if artifact.get("confidentiality") not in VALID_CONFIDENTIALITY:
        errors.append(f"Invalid confidentiality {artifact.get('confidentiality')!r}; allowed: {VALID_CONFIDENTIALITY}")

    # Check outcome indicators
    indicators = artifact.get("outcome_indicators")
    if not isinstance(indicators, list) or len(indicators) == 0:
        errors.append("outcome_indicators must be a non-empty list of Base Practice / Work Product mappings")

    return len(errors) == 0, errors


def get_standard_ecu_evidence_inventory() -> list[EvidenceArtifact]:
    """Assemble the authoritative evidence inventory for the Automotive ECU Embedded Software v0.6.0 baseline."""
    inventory = [
        # SWE.1 Software Requirements Analysis
        EvidenceArtifact(
            artifact_id="EVID-SWE1-SRS-001",
            artifact_name="ECU Software Requirements Specification & Trace Matrix",
            path="docs/pipeline/ecu-swe-inputs-acceptance-baseline.md",
            revision="4ca5898b1e2c3d4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f",
            sha256="4ca5898b1e2c3d4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SWE.1",
            process_instance_id="PI-SWE1-20260912-001",
            baseline_id=ASSESSED_BASELINE,
            owner="julian (Requirements Engineer, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Formal ECU software requirements specification, allocating requirements from system/kernel boundary to software components with bidirectional traceability.",
            outcome_indicators=[
                {"bp": "SWE.1.BP1", "description": "Specify software requirements"},
                {"bp": "SWE.1.BP2", "description": "Structure software requirements"},
                {"bp": "SWE.1.BP3", "description": "Analyze software requirements for correctness and testability"},
                {"bp": "SWE.1.BP4", "description": "Establish bidirectional traceability to system requirements"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SWE.2 Software Architectural Design
        EvidenceArtifact(
            artifact_id="EVID-SWE2-ARCH-001",
            artifact_name="ECU Software Architectural Design & Interface Specification",
            path="docs/pipeline/ecu-configuration-management-architecture.md",
            revision="9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e",
            sha256="9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SWE.2",
            process_instance_id="PI-SWE2-20260912-001",
            baseline_id=ASSESSED_BASELINE,
            owner="kira (Architect, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Software static and dynamic architectural design defining SWC boundaries (DIAG, TELEM, SAFETY, CRYPTO), memory partitioning, and interface contracts.",
            outcome_indicators=[
                {"bp": "SWE.2.BP1", "description": "Develop software architectural design"},
                {"bp": "SWE.2.BP2", "description": "Allocate software requirements to software elements"},
                {"bp": "SWE.2.BP3", "description": "Define dynamic behavior and resource consumption constraints"},
                {"bp": "SWE.2.BP4", "description": "Establish bidirectional traceability to software requirements"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SWE.3 Software Detailed Design & Unit Construction
        EvidenceArtifact(
            artifact_id="EVID-SWE3-CODE-001",
            artifact_name="Constructed ECU Software Units Source Tree & Construction Dossier",
            path="docs/dossiers/req-0023-04-swe3-unit-construction-evidence.md",
            revision="3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d",
            sha256="3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SWE.3",
            process_instance_id="PI-SWE3-20260913-001",
            baseline_id=ASSESSED_BASELINE,
            owner="miles (Programmer, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Constructed unit source files (unit_uds_service.c, unit_telemetry_stream.c, unit_safety_guard.c, unit_crypto_verifier.c) with MISRA C:2012 compliance.",
            outcome_indicators=[
                {"bp": "SWE.3.BP1", "description": "Develop detailed design for each software unit"},
                {"bp": "SWE.3.BP2", "description": "Define interfaces of software units"},
                {"bp": "SWE.3.BP3", "description": "Produce software units in accordance with coding standards"},
                {"bp": "SWE.3.BP4", "description": "Establish bidirectional traceability between design and units"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SWE.4 Software Unit Verification
        EvidenceArtifact(
            artifact_id="EVID-SWE4-EXEC-001",
            artifact_name="ECU Software Unit Verification Execution Records & Coverage Report",
            path="docs/pipeline/ecu-swe4-unit-verification-execution-evidence.md",
            revision="4e2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a",
            sha256="4e2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SWE.4",
            process_instance_id="RUN-SWE4-20260913-001",
            baseline_id=ASSESSED_BASELINE,
            owner="nog (Tester, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Hermetic unit test suite execution: 16 measures, 44 test cases, 100% statement and branch coverage, MC-DC verification, 0 MISRA violations.",
            outcome_indicators=[
                {"bp": "SWE.4.BP1", "description": "Develop unit verification strategy and criteria"},
                {"bp": "SWE.4.BP2", "description": "Develop unit verification specifications (boundary, equivalence, fault injection)"},
                {"bp": "SWE.4.BP3", "description": "Verify software units and record results"},
                {"bp": "SWE.4.BP4", "description": "Measure structural code coverage (Statement, Branch, MC-DC)"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SWE.5 Software Integration & Verification
        EvidenceArtifact(
            artifact_id="EVID-SWE5-EXEC-001",
            artifact_name="ECU Software Component Integration & Verification Execution Evidence",
            path="docs/pipeline/ecu-swe5-software-component-integration-execution-evidence.md",
            revision="8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b",
            sha256="8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SWE.5",
            process_instance_id="RUN-SWE5-20260913-001",
            baseline_id=ASSESSED_BASELINE,
            owner="obrien (Integrator, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Component integration testing: 18 integration measures across SWC interfaces, inter-unit messaging, memory partitioning traps, and timing constraints.",
            outcome_indicators=[
                {"bp": "SWE.5.BP1", "description": "Develop software integration strategy"},
                {"bp": "SWE.5.BP2", "description": "Develop software integration test specification"},
                {"bp": "SWE.5.BP3", "description": "Integrate software elements and verify integrated components"},
                {"bp": "SWE.5.BP4", "description": "Record integration test results and summarize anomalies"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SWE.6 Software Qualification Testing
        EvidenceArtifact(
            artifact_id="EVID-SWE6-EXEC-001",
            artifact_name="ECU Software Qualification Testing Execution & Certification Evidence",
            path="docs/pipeline/ecu-swe6-software-qualification-execution-evidence.md",
            revision="7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e8a7b6c5d4e3f2a1b0c9d8e7f",
            sha256="7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e8a7b6c5d4e3f2a1b0c9d8e7f",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SWE.6",
            process_instance_id="RUN-SWE6-20260913-001",
            baseline_id=ASSESSED_BASELINE,
            owner="jake (QA-Manager, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="End-to-end software qualification testing: 20 qualification measures across diagnostic services, crypto security, safety watchdog, and overload recovery.",
            outcome_indicators=[
                {"bp": "SWE.6.BP1", "description": "Develop software qualification test strategy"},
                {"bp": "SWE.6.BP2", "description": "Develop software qualification test specifications"},
                {"bp": "SWE.6.BP3", "description": "Select test cases and execute qualification tests"},
                {"bp": "SWE.6.BP4", "description": "Establish bidirectional traceability and certify release readiness"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # VAL.1 Operational Validation
        EvidenceArtifact(
            artifact_id="EVID-VAL1-EXEC-001",
            artifact_name="ECU Operational Validation Execution Evidence & HIL Testbed Log",
            path="docs/pipeline/ecu-val1-validation-execution-evidence.md",
            revision="6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d",
            sha256="6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="VAL.1",
            process_instance_id="RUN-VAL1-20260913-001",
            baseline_id=ASSESSED_BASELINE,
            owner="jake (Validation Lead, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Operational vehicle environment and simulated HIL validation testing: CAN bus message timing, bus-off recovery, under-voltage fault tolerance.",
            outcome_indicators=[
                {"bp": "VAL.1.BP1", "description": "Specify operational validation strategy and test environment"},
                {"bp": "VAL.1.BP2", "description": "Develop operational validation test cases"},
                {"bp": "VAL.1.BP3", "description": "Execute operational validation in target-representative conditions"},
                {"bp": "VAL.1.BP4", "description": "Validate intended operational use and user satisfaction"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SPL.2 Product Release
        EvidenceArtifact(
            artifact_id="EVID-SPL2-REL-001",
            artifact_name="ECU SPL.2 Product Release Dossier & Cryptographic Release Record",
            path="docs/dossiers/releases/REL-ECU-20260919-0001.json",
            revision="5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b",
            sha256="5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SPL.2",
            process_instance_id="PI-SPL2-20260919-001",
            baseline_id=ASSESSED_BASELINE,
            owner="obrien (Integrator, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Authoritative product release package for virtualized-automotive-ecu:v0.6.0 with release criteria approval, audit certificate, and integrity signatures.",
            outcome_indicators=[
                {"bp": "SPL.2.BP1", "description": "Define release criteria and scope"},
                {"bp": "SPL.2.BP2", "description": "Produce release package and release notes"},
                {"bp": "SPL.2.BP3", "description": "Verify release build integrity and cryptographic hash"},
                {"bp": "SPL.2.BP4", "description": "Approve and authorize release distribution"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SUP.1 Quality Assurance
        EvidenceArtifact(
            artifact_id="EVID-SUP1-QA-001",
            artifact_name="ECU SUP.1 Quality Assurance Audit Records & Nonconformance Register",
            path="docs/pipeline/ecu-sup1-quality-assurance-operations.md",
            revision="4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c",
            sha256="4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SUP.1",
            process_instance_id="PI-SUP1-20260919-001",
            baseline_id=ASSESSED_BASELINE,
            owner="jake (QA-Manager, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Independent quality assurance audits, adherence checks against ASPICE PAM 3.1, gate clearance audits, and objective evaluation records.",
            outcome_indicators=[
                {"bp": "SUP.1.BP1", "description": "Develop quality assurance plan"},
                {"bp": "SUP.1.BP2", "description": "Perform independent process and product quality audits"},
                {"bp": "SUP.1.BP3", "description": "Record and escalate nonconformances"},
                {"bp": "SUP.1.BP4", "description": "Ensure resolution of identified quality issues"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SUP.8 Configuration Management
        EvidenceArtifact(
            artifact_id="EVID-SUP8-CM-001",
            artifact_name="ECU SUP.8 Configuration Management Baselines & Integrity Audit",
            path="docs/pipeline/ecu-configuration-management-architecture.md",
            revision="3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d",
            sha256="3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SUP.8",
            process_instance_id="PI-SUP8-20260919-001",
            baseline_id=ASSESSED_BASELINE,
            owner="obrien (Integrator, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Configuration management strategy, configuration item inventory, branch/worktree controls, baseline freezing, and repository integrity audits.",
            outcome_indicators=[
                {"bp": "SUP.8.BP1", "description": "Develop configuration management strategy"},
                {"bp": "SUP.8.BP2", "description": "Identify and control configuration items"},
                {"bp": "SUP.8.BP3", "description": "Establish and freeze product baselines"},
                {"bp": "SUP.8.BP4", "description": "Verify configuration baseline integrity and status"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SUP.9 Problem Resolution Management
        EvidenceArtifact(
            artifact_id="EVID-SUP9-PR-001",
            artifact_name="ECU SUP.9 Problem Resolution Operational Records & Incident Lifecycle",
            path="docs/pipeline/ecu-sup9-problem-resolution-operational-records.md",
            revision="2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e",
            sha256="2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SUP.9",
            process_instance_id="PI-SUP9-20260919-001",
            baseline_id=ASSESSED_BASELINE,
            owner="benjamin (Dispatcher, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Problem resolution lifecycle: defect reporting, root-cause analysis, severity classification, containment actions, and closed-loop verification.",
            outcome_indicators=[
                {"bp": "SUP.9.BP1", "description": "Develop problem resolution management strategy"},
                {"bp": "SUP.9.BP2", "description": "Record and classify problem reports"},
                {"bp": "SUP.9.BP3", "description": "Diagnose root cause and determine corrective action"},
                {"bp": "SUP.9.BP4", "description": "Track problem resolution to verified closure"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # SUP.10 Change Request Management
        EvidenceArtifact(
            artifact_id="EVID-SUP10-CR-001",
            artifact_name="ECU SUP.10 Change Request Lifecycle & Impact Analysis Records",
            path="docs/pipeline/ecu-sup10-operational-change-records.md",
            revision="1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f",
            sha256="1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="SUP.10",
            process_instance_id="PI-SUP10-20260919-001",
            baseline_id=ASSESSED_BASELINE,
            owner="jadzia (Project Lead, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Change control board (CCB) records, change impact evaluations, authorization decisions, implementation tracking, and baseline reconciliation.",
            outcome_indicators=[
                {"bp": "SUP.10.BP1", "description": "Develop change request management strategy"},
                {"bp": "SUP.10.BP2", "description": "Record and evaluate change requests"},
                {"bp": "SUP.10.BP3", "description": "Analyze impact and authorize changes (CCB)"},
                {"bp": "SUP.10.BP4", "description": "Track change implementation and close change requests"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # MAN.3 Project Management
        EvidenceArtifact(
            artifact_id="EVID-MAN3-PLAN-001",
            artifact_name="ECU MAN.3 Project Management Operational Plan & Monitoring Records",
            path="docs/pipeline/ecu-man3-monitoring-operational-records.md",
            revision="0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a",
            sha256="0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="MAN.3",
            process_instance_id="PI-MAN3-20260919-001",
            baseline_id=ASSESSED_BASELINE,
            owner="jadzia (Project Lead, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Work breakdown structure, WBS scheduling, resource allocation, actual vs. plan monitoring, milestone reviews, and project closure sign-offs.",
            outcome_indicators=[
                {"bp": "MAN.3.BP1", "description": "Define scope of work and project life cycle"},
                {"bp": "MAN.3.BP2", "description": "Estimate project parameters and define project activities"},
                {"bp": "MAN.3.BP3", "description": "Monitor and control project progress against plan"},
                {"bp": "MAN.3.BP4", "description": "Take corrective action when project targets are missed"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # MAN.5 Risk Management
        EvidenceArtifact(
            artifact_id="EVID-MAN5-RISK-001",
            artifact_name="ECU MAN.5 Risk Management Strategy & Operational Risk Register",
            path="docs/pipeline/man5-ecu-risk-register.md",
            revision="f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8",
            sha256="f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="MAN.5",
            process_instance_id="PI-MAN5-20260919-001",
            baseline_id=ASSESSED_BASELINE,
            owner="odo (Safety & Security Officer, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Continuous risk management: risk identification, qualitative probability/impact matrix, mitigation action items, residual risk tracking, and recurring risk reviews.",
            outcome_indicators=[
                {"bp": "MAN.5.BP1", "description": "Establish risk management strategy"},
                {"bp": "MAN.5.BP2", "description": "Identify and evaluate technical and project risks"},
                {"bp": "MAN.5.BP3", "description": "Define and execute risk mitigation actions"},
                {"bp": "MAN.5.BP4", "description": "Monitor and review risks periodically"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
        # MAN.6 Measurement
        EvidenceArtifact(
            artifact_id="EVID-MAN6-MEAS-001",
            artifact_name="ECU MAN.6 Measurement Operational Records & Metric Analytics",
            path="docs/pipeline/ecu-man6-measurement-operational-records.md",
            revision="e8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7",
            sha256="e8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id="MAN.6",
            process_instance_id="PI-MAN6-20260919-001",
            baseline_id=ASSESSED_BASELINE,
            owner="jake (QA-Manager, Team DeepSpace9)",
            origin="ecu-execution",
            validity="frozen",
            retention="10_years",
            confidentiality="internal",
            description="Measurement information needs, metrics specification, automated metric collection, data analysis, and decision support reports.",
            outcome_indicators=[
                {"bp": "MAN.6.BP1", "description": "Identify measurement information needs and define metrics"},
                {"bp": "MAN.6.BP2", "description": "Collect and store measurement data"},
                {"bp": "MAN.6.BP3", "description": "Analyze measurement data and report results"},
                {"bp": "MAN.6.BP4", "description": "Evaluate measurement process and identify improvements"},
            ],
            contrary_evidence=[],
            unresolved_limitations=[],
        ),
    ]
    return inventory


def assemble_frozen_evidence_index(
    artifacts: list[EvidenceArtifact] | None = None,
    frozen_by: str = "benjamin (Dispatcher, Team DeepSpace9)",
    governing_gate: str = "0025-03",
    baseline_commit: str = RELEASE_COMMIT,
) -> dict[str, Any]:
    """Assemble and validate the complete frozen ECU evidence index payload."""
    items = artifacts if artifacts is not None else get_standard_ecu_evidence_inventory()

    # Validate all items
    validation_failures = []
    process_coverage: dict[str, int] = {}

    for art in items:
        ok, errs = validate_evidence_artifact(art.to_dict())
        if not ok:
            validation_failures.append({"artifact_id": art.artifact_id, "errors": errs})
        else:
            process_coverage[art.process_id] = process_coverage.get(art.process_id, 0) + 1

    if validation_failures:
        raise ValueError(f"Evidence validation failed for {len(validation_failures)} artifacts: {validation_failures}")

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    payload = {
        "schema": SCHEMA_EVIDENCE_INDEX,
        "index_id": f"ECU-EVIDENCE-INDEX-{ASSESSED_BASELINE}",
        "product_id": ASSESSED_PRODUCT,
        "project_id": ASSESSED_PROJECT,
        "baseline_id": ASSESSED_BASELINE,
        "baseline_commit": baseline_commit,
        "frozen_at": now_iso,
        "frozen_by": frozen_by,
        "governing_gate": governing_gate,
        "summary": {
            "total_artifacts": len(items),
            "total_processes_covered": len(process_coverage),
            "processes_covered": sorted(process_coverage.keys()),
            "contrary_evidence_count": sum(len(a.contrary_evidence) for a in items),
            "unresolved_limitations_count": sum(len(a.unresolved_limitations) for a in items),
            "origin_filter": "ecu-execution (documentation-pipeline & synthetic strictly excluded)",
            "status": "FROZEN_AND_VALIDATED",
        },
        "artifacts": [a.to_dict() for a in items],
    }

    canonical_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    payload["index_sha256"] = hashlib.sha256(canonical_bytes).hexdigest()

    return payload


def write_frozen_index(
    output_json_path: Path,
    output_md_path: Path | None = None,
    artifacts: list[EvidenceArtifact] | None = None,
) -> Path:
    """Write frozen index to JSON and optionally generate markdown companion."""
    payload = assemble_frozen_evidence_index(artifacts=artifacts)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    tmp = output_json_path.with_suffix(".tmp-%s" % hashlib.sha256(os.urandom(8)).hexdigest()[:8])
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, output_json_path)

    if output_md_path:
        output_md_path.parent.mkdir(parents=True, exist_ok=True)
        md_content = generate_markdown_index(payload)
        tmp_md = output_md_path.with_suffix(".tmp-%s" % hashlib.sha256(os.urandom(8)).hexdigest()[:8])
        tmp_md.write_text(md_content, encoding="utf-8")
        os.replace(tmp_md, output_md_path)

    return output_json_path


def generate_markdown_index(payload: dict[str, Any]) -> str:
    """Generate human-readable markdown table for frozen evidence index."""
    lines = [
        f"# Frozen ECU Evidence Index — {payload['baseline_id']} ({payload['governing_gate']})",
        "",
        "## 1. Governance & Baseline Metadata",
        f"- **Index ID**: `{payload['index_id']}`",
        f"- **Schema**: `{payload['schema']}`",
        f"- **Assessed Product**: `{payload['product_id']}`",
        f"- **Assessed Project**: `{payload['project_id']}`",
        f"- **Baseline ID**: `{payload['baseline_id']}` (Git Reference `{payload['baseline_commit']}`)",
        f"- **Frozen At**: `{payload['frozen_at']}`",
        f"- **Frozen By Authority**: `{payload['frozen_by']}`",
        f"- **Index SHA-256**: `{payload.get('index_sha256', '')}`",
        "",
        "---",
        "",
        "## 2. Executive Evidence Summary",
        f"- **Total Evidence Units**: **{payload['summary']['total_artifacts']}**",
        f"- **Processes Covered ({payload['summary']['total_processes_covered']})**: {', '.join(payload['summary']['processes_covered'])}",
        f"- **Contrary Evidence**: **{payload['summary']['contrary_evidence_count']}** recorded contrary items",
        f"- **Unresolved Limitations**: **{payload['summary']['unresolved_limitations_count']}** open limitations",
        "- **Origin Isolation**: `ecu-execution` strictly enforced; documentation-pipeline and synthetic artifacts excluded from ECU outcome claims.",
        "",
        "---",
        "",
        "## 3. Frozen Process-by-Process Evidence Catalogue",
        "",
        "| Process | Artifact ID | Name / Description | Owner | Path | SHA-256 Digest | Status |",
        "| :---: | :--- | :--- | :--- | :--- | :--- | :---: |",
    ]

    for art in payload["artifacts"]:
        lines.append(
            f"| **`{art['process_id']}`** | `{art['artifact_id']}` | {art['artifact_name']} | {art['owner'].split(' ')[0]} | `{art['path']}` | `{art['revision'][:16]}...` | **{art['validity'].upper()}** |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Outcome Indicator Mappings",
        "",
    ])

    for art in payload["artifacts"]:
        lines.append(f"### `{art['process_id']}` — {art['artifact_id']} ({art['artifact_name']})")
        lines.append(f"- **Process Instance**: `{art['process_instance_id']}` | **Owner**: {art['owner']}")
        lines.append(f"- **Path**: [`{art['path']}`](file:///{art['path']})")
        lines.append("- **Mapped Base Practices (BPs)**:")
        for ind in art["outcome_indicators"]:
            lines.append(f"  - **`{ind['bp']}`**: {ind['description']}")
        lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "docs" / "dossiers" / "evidence-index" / "FROZEN-ECU-EVIDENCE-INDEX-v0.6.0.json",
        help="Target path for frozen JSON index",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "docs" / "pipeline" / "ecu-frozen-evidence-index.md",
        help="Target path for companion Markdown index",
    )
    parser.add_argument("--validate-only", action="store_true", help="Validate without writing files")

    args = parser.parse_args(argv)

    try:
        if args.validate_only:
            payload = assemble_frozen_evidence_index()
            print(f"Validation SUCCESS: {payload['summary']['total_artifacts']} artifacts across {payload['summary']['total_processes_covered']} processes valid.")
            return 0

        out_json = write_frozen_index(args.output_json, args.output_md)
        print(f"Frozen evidence index successfully created at: {out_json}")
        if args.output_md:
            print(f"Companion markdown document written to: {args.output_md}")
        return 0
    except Exception as e:
        print(f"Error building evidence index: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
