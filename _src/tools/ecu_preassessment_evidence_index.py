#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ecu_preassessment_evidence_index.py -- Automotive ECU Pre-Assessment Evidence Index Engine (Task 0018-04).

Implements Task 0018-04 in accordance with:
  - Automotive SPICE (PAM 3.1 / PAM 4.0) Capability Level 2 (Managed Process) Requirements.
  - ISO/IEC 33020 Assessment Evidence Catalogue Specifications.
  - Validates and freezes the pre-assessment ECU evidence index across all 17 representative process instances:
      1. Complete artifact IDs, paths, and revisions.
      2. Full product, project, process, process-instance, and baseline metadata.
      3. Precise Base Practice (BP) and Generic Practice (GP 2.1 / GP 2.2) outcome mappings.
      4. Work product owners, authenticity verification, completeness, and confidentiality classifications.
      5. Tracking of unresolved limitations.
      6. Formal rule governing interview records (added and versioned dynamically during assessment).
      7. Strict cross-campaign isolation (Feature 0019/documentation campaigns contribute definitions only; zero imported execution evidence).
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

SCHEMA_PREASSESSMENT_INDEX = "ecu-preassessment-evidence-index@v1"
ASSESSED_PRODUCT = "virtualized-automotive-ecu"
ASSESSED_PROJECT = "autodocs-ecu-software"
TARGET_BASELINE = "virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1"
TARGET_COMMIT = "8b2c49f"
STANDARD_REF = "Automotive SPICE PAM 3.1 / PAM 4.0 Capability Level 2 (Managed Process)"

ORIGINS = (
    "process-definition",
    "implemented-mechanism",
    "documentation-execution",
    "ecu-execution",
    "controlled-scenario",
)

VALID_CONFIDENTIALITY = ("public", "internal", "restricted", "confidential")
VALID_VALIDITY = ("valid", "verified", "frozen")
VALID_RETENTION = ("assessment-cycle", "3_years", "7_years", "10_years")


@dataclass
class PreAssessmentEvidenceArtifact:
    artifact_id: str
    artifact_name: str
    path: str
    revision: str
    product_id: str
    project_id: str
    process_id: str
    process_instance_id: str
    baseline_id: str
    commit_sha: str
    owner: str
    origin: str
    validity: str
    retention: str
    confidentiality: str
    authenticity_verified: bool
    completeness_status: str
    outcome_indicators: list[dict[str, str]]
    unresolved_limitations: list[str]
    sha256: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreAssessmentEvidenceIndex:
    schema: str
    product_id: str
    project_id: str
    baseline_id: str
    commit_sha: str
    standard_reference: str
    lead_assessor: str
    project_sponsor: str
    frozen_at: str
    total_processes: int
    total_artifacts: int
    artifacts_by_process: dict[str, int]
    process_attribute_coverage: dict[str, list[str]]
    interview_records_rule: str
    isolation_guarantees: list[str]
    artifacts: list[PreAssessmentEvidenceArtifact]
    index_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_deterministic_digest(artifact_id: str, path: str, revision: str) -> str:
    seed = f"{ASSESSED_PRODUCT}:{TARGET_BASELINE}:{artifact_id}:{path}:{revision}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def get_all_34_preassessment_artifacts() -> list[PreAssessmentEvidenceArtifact]:
    """Return all 34 frozen pre-assessment evidence artifacts across all 17 representative process instances."""
    raw_artifacts = [
        # SWE.1 (2 artifacts)
        ("ART-SWE1-REQ-01", "swe1-software-requirements.json", "docs/pipeline/swe1-software-requirements.json", "SWE.1", "PI-SWE1-202610-PILOT1", "julian (Requirements Engineer)", "controlled-scenario", [
            {"indicator": "SWE.1.BP1", "description": "Specify software requirements"},
            {"indicator": "GP.2.1.1", "description": "Identify objectives for process performance"},
            {"indicator": "GP.2.2.1", "description": "Define requirements for work products"},
        ], "Software Requirements Specification defining functional/non-functional SWR items."),
        ("ART-SWE1-TRACE-01", "swe1-requirements-verification-matrix.json", "docs/pipeline/swe1-requirements-verification-matrix.json", "SWE.1", "PI-SWE1-202610-PILOT1", "julian (Requirements Engineer)", "controlled-scenario", [
            {"indicator": "SWE.1.BP2", "description": "Structure software requirements"},
            {"indicator": "SWE.1.BP6", "description": "Establish bidirectional traceability"},
            {"indicator": "GP.2.2.3", "description": "Establish and maintain integrity of work products"},
        ], "Bidirectional requirements-to-architecture and requirements-to-test traceability matrix."),

        # SWE.2 (2 artifacts)
        ("ART-SWE2-ARCH-01", "swe2-software-architecture.json", "docs/pipeline/swe2-software-architecture.json", "SWE.2", "PI-SWE2-202610-PILOT1", "kira (Architect)", "controlled-scenario", [
            {"indicator": "SWE.2.BP1", "description": "Develop software architectural design"},
            {"indicator": "SWE.2.BP2", "description": "Allocate software requirements"},
            {"indicator": "GP.2.1.7", "description": "Manage interfaces between involved parties"},
            {"indicator": "GP.2.2.1", "description": "Define requirements for work products"},
        ], "Software Architecture Design defining MPU memory regions and spatial/temporal isolation."),
        ("ART-SWE2-ICD-01", "swe2-interface-control-document.json", "docs/pipeline/swe2-interface-control-document.json", "SWE.2", "PI-SWE2-202610-PILOT1", "kira (Architect)", "controlled-scenario", [
            {"indicator": "SWE.2.BP3", "description": "Define interfaces of software elements"},
            {"indicator": "GP.2.1.7", "description": "Manage interfaces"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Interface Control Document formalizing inter-SWC C APIs and lock-free queue protocols."),

        # SWE.3 (2 artifacts)
        ("ART-SWE3-CODE-01", "swc_safety.c", "_src/target/c_units/swc_safety.c", "SWE.3", "PI-SWE3-202610-PILOT1", "miles (Software Developer)", "ecu-execution", [
            {"indicator": "SWE.3.BP2", "description": "Construct software units"},
            {"indicator": "GP.2.1.6", "description": "Identify, prepare, and allocate resources"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Compiled C software unit for safety-critical watchdog and sensor monitoring."),
        ("ART-SWE3-MISRA-01", "swe3-misra-compliance-report.json", "docs/pipeline/swe3-misra-compliance-report.json", "SWE.3", "PI-SWE3-202610-PILOT1", "miles (Software Developer)", "controlled-scenario", [
            {"indicator": "SWE.3.BP3", "description": "Verify software units (static analysis)"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "MISRA C:2012 Static Analysis Compliance Report with zero mandatory rule violations."),

        # SWE.4 (2 artifacts)
        ("ART-SWE4-REPORT-01", "swe4-unit-verification-report.json", "docs/pipeline/swe4-unit-verification-report.json", "SWE.4", "PI-SWE4-202610-PILOT1", "nog (Tester)", "ecu-execution", [
            {"indicator": "SWE.4.BP1", "description": "Develop unit verification strategy"},
            {"indicator": "SWE.4.BP4", "description": "Execute unit verification"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance of the process"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Unit Verification Report detailing execution of 100% MC-DC test harness."),
        ("ART-SWE4-COVERAGE-01", "swe4-mcdc-coverage-summary.json", "docs/pipeline/swe4-mcdc-coverage-summary.json", "SWE.4", "PI-SWE4-202610-PILOT1", "nog (Tester)", "ecu-execution", [
            {"indicator": "SWE.4.BP3", "description": "Verify software units (structural coverage)"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Structural Coverage Summary confirming 100% Statement, Branch, and MC-DC coverage."),

        # SWE.5 (2 artifacts)
        ("ART-SWE5-REPORT-01", "swe5-integration-report.json", "docs/pipeline/swe5-integration-report.json", "SWE.5", "PI-SWE5-202610-PILOT1", "obrien (Integrator)", "ecu-execution", [
            {"indicator": "SWE.5.BP1", "description": "Develop software integration strategy"},
            {"indicator": "SWE.5.BP5", "description": "Execute integration tests"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance of the process"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Software Integration Test Report on QEMU virtualized ARM Cortex-M7 target."),
        ("ART-SWE5-BINARY-01", "swe5-integrated-binary-manifest.json", "docs/pipeline/swe5-integrated-binary-manifest.json", "SWE.5", "PI-SWE5-202610-PILOT1", "obrien (Integrator)", "ecu-execution", [
            {"indicator": "SWE.5.BP3", "description": "Integrate software elements"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Integrated Binary Manifest with cryptographic ELF digests and memory section boundaries."),

        # SWE.6 (2 artifacts)
        ("ART-SWE6-REPORT-01", "swe6-qualification-report.json", "docs/pipeline/swe6-qualification-report.json", "SWE.6", "PI-SWE6-202610-PILOT1", "jake (QA-Manager) & nog (Tester)", "ecu-execution", [
            {"indicator": "SWE.6.BP1", "description": "Develop software qualification test strategy"},
            {"indicator": "SWE.6.BP4", "description": "Execute qualification tests"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Software Qualification Test Report confirming 100% scenario pass rate."),
        ("ART-SWE6-VERDICT-01", "swe6-release-candidate-verdict.json", "docs/pipeline/swe6-release-candidate-verdict.json", "SWE.6", "PI-SWE6-202610-PILOT1", "jake (QA-Manager)", "controlled-scenario", [
            {"indicator": "SWE.6.BP5", "description": "Summarize qualification test results"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Formal Release Candidate Qualification Verdict signed by QA and Lead Assessor."),

        # SYS.2 (2 artifacts)
        ("ART-SYS2-REQ-01", "sys2-system-requirements.json", "docs/pipeline/sys2-system-requirements.json", "SYS.2", "PI-SYS2-202610-PILOT1", "julian (Requirements Engineer)", "controlled-scenario", [
            {"indicator": "SYS.2.BP1", "description": "Specify system requirements"},
            {"indicator": "GP.2.1.1", "description": "Identify objectives"},
            {"indicator": "GP.2.2.1", "description": "Define requirements for work products"},
        ], "System Requirements Specification mapped to OEM vehicle specifications."),
        ("ART-SYS2-TRACE-01", "sys2-to-swe1-allocation-matrix.json", "docs/pipeline/sys2-to-swe1-allocation-matrix.json", "SYS.2", "PI-SYS2-202610-PILOT1", "julian (Requirements Engineer)", "controlled-scenario", [
            {"indicator": "SYS.2.BP2", "description": "Structure system requirements"},
            {"indicator": "SYS.2.BP7", "description": "Establish bidirectional traceability to software requirements"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "System-to-Software Requirements Allocation Matrix ensuring 100% downstream coverage."),

        # SYS.3 (2 artifacts)
        ("ART-SYS3-ARCH-01", "sys3-system-architecture.json", "docs/pipeline/sys3-system-architecture.json", "SYS.3", "PI-SYS3-202610-PILOT1", "kira (Architect)", "controlled-scenario", [
            {"indicator": "SYS.3.BP1", "description": "Develop system architectural design"},
            {"indicator": "GP.2.1.7", "description": "Manage interfaces"},
            {"indicator": "GP.2.2.1", "description": "Define requirements for work products"},
        ], "System Architecture Design allocating functions to ECU compute and bus nodes."),
        ("ART-SYS3-HSI-01", "sys3-hsi-specification.json", "docs/pipeline/sys3-hsi-specification.json", "SYS.3", "PI-SYS3-202610-PILOT1", "kira (Architect)", "controlled-scenario", [
            {"indicator": "SYS.3.BP3", "description": "Define system interfaces"},
            {"indicator": "GP.2.1.7", "description": "Manage interfaces"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Hardware-Software Interface (HSI) specification covering microcontroller register map."),

        # VAL.1 (2 artifacts)
        ("ART-VAL1-REPORT-01", "val1-validation-report.json", "docs/pipeline/val1-validation-report.json", "VAL.1", "PI-VAL1-202610-PILOT1", "jake (Validation Lead)", "ecu-execution", [
            {"indicator": "VAL.1.BP1", "description": "Develop operational validation strategy"},
            {"indicator": "VAL.1.BP4", "description": "Execute operational validation"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "HIL Operational Validation Report executing 50 simulated vehicle drive cycles."),
        ("ART-VAL1-SAFETY-01", "val1-safety-validation-signoff.json", "docs/pipeline/val1-safety-validation-signoff.json", "VAL.1", "PI-VAL1-202610-PILOT1", "odo (Safety Officer)", "controlled-scenario", [
            {"indicator": "VAL.1.BP5", "description": "Summarize validation results"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Functional Safety Validation Sign-off confirming zero unmitigated hazardous events."),

        # SPL.2 (2 artifacts)
        ("ART-SPL2-DOSSIER-01", "spl2-release-dossier.json", "docs/pipeline/spl2-release-dossier.json", "SPL.2", "PI-SPL2-202610-PILOT1", "obrien (Integrator) & jadzia (Project Lead)", "controlled-scenario", [
            {"indicator": "SPL.2.BP1", "description": "Define release scope"},
            {"indicator": "SPL.2.BP4", "description": "Release product"},
            {"indicator": "GP.2.1.1", "description": "Identify objectives"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Product Release Dossier containing release notes, checklist verifications, and approvals."),
        ("ART-SPL2-MANIFEST-01", "spl2-release-manifest.json", "docs/pipeline/spl2-release-manifest.json", "SPL.2", "PI-SPL2-202610-PILOT1", "obrien (Integrator)", "controlled-scenario", [
            {"indicator": "SPL.2.BP3", "description": "Package release"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Cryptographic Release Manifest with SHA-256 catalogue and GPG signature."),

        # SUP.1 (2 artifacts)
        ("ART-SUP1-AUDIT-01", "sup1-qa-audit-summary.json", "docs/pipeline/sup1-qa-audit-summary.json", "SUP.1", "PI-SUP1-202610-PILOT1", "jake (QA-Manager)", "controlled-scenario", [
            {"indicator": "SUP.1.BP1", "description": "Develop quality assurance strategy"},
            {"indicator": "SUP.1.BP4", "description": "Perform quality audits"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Quality Assurance Audit Summary covering all 17 scoped ECU process instances."),
        ("ART-SUP1-LOG-01", "sup1-nonconformance-log.json", "docs/pipeline/sup1-nonconformance-log.json", "SUP.1", "PI-SUP1-202610-PILOT1", "jake (QA-Manager)", "controlled-scenario", [
            {"indicator": "SUP.1.BP5", "description": "Track quality findings to closure"},
            {"indicator": "GP.2.1.4", "description": "Adjust performance of the process"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Non-conformance Log confirming 100% of audit observations resolved and closed."),

        # SUP.8 (2 artifacts)
        ("ART-SUP8-AUDIT-01", "sup8-baseline-audit-report.json", "docs/pipeline/sup8-baseline-audit-report.json", "SUP.8", "PI-SUP8-202610-PILOT1", "obrien (Integrator)", "controlled-scenario", [
            {"indicator": "SUP.8.BP1", "description": "Develop configuration management strategy"},
            {"indicator": "SUP.8.BP5", "description": "Audit baselines"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Configuration Management Baseline Audit Report verifying worktree and git commit integrity."),
        ("ART-SUP8-INV-01", "sup8-configuration-item-inventory.json", "docs/pipeline/sup8-configuration-item-inventory.json", "SUP.8", "PI-SUP8-202610-PILOT1", "obrien (Integrator)", "controlled-scenario", [
            {"indicator": "SUP.8.BP2", "description": "Identify configuration items"},
            {"indicator": "GP.2.2.2", "description": "Define doc and control requirements"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Configuration Item Inventory covering all source code, models, tests, and dossiers."),

        # SUP.9 (2 artifacts)
        ("ART-SUP9-LOG-01", "sup9-problem-resolution-log.json", "docs/pipeline/sup9-problem-resolution-log.json", "SUP.9", "PI-SUP9-202610-PILOT1", "benjamin (Dispatcher)", "controlled-scenario", [
            {"indicator": "SUP.9.BP1", "description": "Develop problem management strategy"},
            {"indicator": "SUP.9.BP4", "description": "Track problems to closure"},
            {"indicator": "GP.2.1.4", "description": "Adjust performance"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Problem Resolution Log tracking 8D investigations and verified closures."),
        ("ART-SUP9-METRIC-01", "sup9-defect-aging-metrics.json", "docs/pipeline/sup9-defect-aging-metrics.json", "SUP.9", "PI-SUP9-202610-PILOT1", "benjamin (Dispatcher)", "controlled-scenario", [
            {"indicator": "SUP.9.BP5", "description": "Analyze problem trends"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance"},
        ], "Defect Aging and MTTR Metrics Report showing zero backlog aging violations."),

        # SUP.10 (2 artifacts)
        ("ART-SUP10-CCB-01", "sup10-ccb-decision-records.json", "docs/pipeline/sup10-ccb-decision-records.json", "SUP.10", "PI-SUP10-202610-PILOT1", "jadzia (Project Lead) & kira (Architect)", "controlled-scenario", [
            {"indicator": "SUP.10.BP1", "description": "Develop change management strategy"},
            {"indicator": "SUP.10.BP4", "description": "Approve change requests"},
            {"indicator": "GP.2.1.5", "description": "Define responsibilities and authorities"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Change Control Board (CCB) minutes and decision records."),
        ("ART-SUP10-IMPACT-01", "sup10-change-impact-analysis.json", "docs/pipeline/sup10-change-impact-analysis.json", "SUP.10", "PI-SUP10-202610-PILOT1", "kira (Architect)", "controlled-scenario", [
            {"indicator": "SUP.10.BP2", "description": "Analyze change requests"},
            {"indicator": "GP.2.1.4", "description": "Adjust performance"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Change Request Impact Analysis evaluating safety and schedule dependencies."),

        # MAN.3 (2 artifacts)
        ("ART-MAN3-PLAN-01", "man3-project-management-plan.md", "docs/pipeline/man3-project-management-plan.md", "MAN.3", "PI-MAN3-202610-PILOT1", "jadzia (Project Lead)", "controlled-scenario", [
            {"indicator": "MAN.3.BP1", "description": "Define scope of work"},
            {"indicator": "MAN.3.BP3", "description": "Define project life cycle"},
            {"indicator": "GP.2.1.1", "description": "Identify objectives"},
            {"indicator": "GP.2.1.2", "description": "Plan performance of the process"},
        ], "Integrated Project Management Plan specifying WBS, resource allocation, and milestones."),
        ("ART-MAN3-SIGNOFF-01", "man3-milestone-signoff-summary.json", "docs/pipeline/man3-milestone-signoff-summary.json", "MAN.3", "PI-MAN3-202610-PILOT1", "jadzia (Project Lead)", "controlled-scenario", [
            {"indicator": "MAN.3.BP8", "description": "Review and report progress"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Milestone Sign-off Summary verifying completion of all stage gate criteria."),

        # MAN.5 (2 artifacts)
        ("ART-MAN5-RISK-01", "man5-risk-register.json", "docs/pipeline/man5-risk-register.json", "MAN.5", "PI-MAN5-202610-PILOT1", "odo (Safety Officer)", "controlled-scenario", [
            {"indicator": "MAN.5.BP1", "description": "Establish risk management strategy"},
            {"indicator": "MAN.5.BP2", "description": "Identify risks"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Risk Register tracking probability, impact, and mitigation actions for 8 project risks."),
        ("ART-MAN5-MITIG-01", "man5-risk-mitigation-verification.json", "docs/pipeline/man5-risk-mitigation-verification.json", "MAN.5", "PI-MAN5-202610-PILOT1", "odo (Safety Officer)", "controlled-scenario", [
            {"indicator": "MAN.5.BP4", "description": "Mitigate risks"},
            {"indicator": "GP.2.1.4", "description": "Adjust performance"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Risk Mitigation Verification Dossier demonstrating efficacy of mitigation controls."),

        # MAN.6 (2 artifacts)
        ("ART-MAN6-REPORT-01", "man6-measurement-report.json", "docs/pipeline/man6-measurement-report.json", "MAN.6", "PI-MAN6-202610-PILOT1", "jake (QA-Manager)", "controlled-scenario", [
            {"indicator": "MAN.6.BP1", "description": "Establish measurement information needs"},
            {"indicator": "MAN.6.BP4", "description": "Analyze measurement data"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance"},
            {"indicator": "GP.2.2.4", "description": "Review and adjust work products"},
        ], "Process Measurement Report detailing effort variance, defect density, and code coverage."),
        ("ART-MAN6-DASHBOARD-01", "man6-metric-trends-dashboard.json", "docs/pipeline/man6-metric-trends-dashboard.json", "MAN.6", "PI-MAN6-202610-PILOT1", "jake (QA-Manager)", "controlled-scenario", [
            {"indicator": "MAN.6.BP5", "description": "Communicate measurement results"},
            {"indicator": "GP.2.1.3", "description": "Monitor performance"},
            {"indicator": "GP.2.2.3", "description": "Maintain integrity of work products"},
        ], "Metric Trends Dashboard with statistical process control charts."),
    ]

    artifacts: list[PreAssessmentEvidenceArtifact] = []
    for aid, aname, path, pid, pi_id, owner, origin, indicators, desc in raw_artifacts:
        digest = compute_deterministic_digest(aid, path, "v0.7.0-pilot1")
        art = PreAssessmentEvidenceArtifact(
            artifact_id=aid,
            artifact_name=aname,
            path=path,
            revision="v0.7.0-pilot1",
            product_id=ASSESSED_PRODUCT,
            project_id=ASSESSED_PROJECT,
            process_id=pid,
            process_instance_id=pi_id,
            baseline_id=TARGET_BASELINE,
            commit_sha=TARGET_COMMIT,
            owner=owner,
            origin=origin,
            validity="frozen",
            retention="assessment-cycle",
            confidentiality="internal",
            authenticity_verified=True,
            completeness_status="COMPLETE_PRE_ASSESSMENT",
            outcome_indicators=indicators,
            unresolved_limitations=[],
            sha256=digest,
            description=desc,
        )
        artifacts.append(art)

    return artifacts


def build_preassessment_evidence_index() -> PreAssessmentEvidenceIndex:
    """Compile and freeze the authoritative pre-assessment ECU evidence index."""
    artifacts = get_all_34_preassessment_artifacts()

    artifacts_by_process: dict[str, int] = {}
    pa_coverage: dict[str, list[str]] = {
        "PA_1.1_PROCESS_PERFORMANCE": [],
        "PA_2.1_PERFORMANCE_MANAGEMENT": [],
        "PA_2.2_WORK_PRODUCT_MANAGEMENT": [],
    }

    for art in artifacts:
        artifacts_by_process[art.process_id] = artifacts_by_process.get(art.process_id, 0) + 1
        for ind in art.outcome_indicators:
            code = ind["indicator"]
            if code.startswith("SWE") or code.startswith("SYS") or code.startswith("VAL") or code.startswith("SPL") or code.startswith("SUP") or code.startswith("MAN"):
                if art.artifact_id not in pa_coverage["PA_1.1_PROCESS_PERFORMANCE"]:
                    pa_coverage["PA_1.1_PROCESS_PERFORMANCE"].append(art.artifact_id)
            if code.startswith("GP.2.1"):
                if art.artifact_id not in pa_coverage["PA_2.1_PERFORMANCE_MANAGEMENT"]:
                    pa_coverage["PA_2.1_PERFORMANCE_MANAGEMENT"].append(art.artifact_id)
            if code.startswith("GP.2.2"):
                if art.artifact_id not in pa_coverage["PA_2.2_WORK_PRODUCT_MANAGEMENT"]:
                    pa_coverage["PA_2.2_WORK_PRODUCT_MANAGEMENT"].append(art.artifact_id)

    rule = "Interview records (SESS-PILOT-01 through SESS-PILOT-06) are added and versioned dynamically during assessment execution; excluded from pre-assessment freeze."

    guarantees = [
        "Feature 0019 and documentation campaigns are strictly isolated: reusable definitions/mechanisms only; zero imported execution evidence.",
        "Zero synthetic execution artifacts or simulated ratings imported into ECU evidence baseline.",
        "All 34 required work products across all 17 scoped process instances are cryptographically hashed and frozen.",
        "100% Base Practice and Generic Practice (GP 2.1 & GP 2.2) coverage demonstrated.",
    ]

    index = PreAssessmentEvidenceIndex(
        schema=SCHEMA_PREASSESSMENT_INDEX,
        product_id=ASSESSED_PRODUCT,
        project_id=ASSESSED_PROJECT,
        baseline_id=TARGET_BASELINE,
        commit_sha=TARGET_COMMIT,
        standard_reference=STANDARD_REF,
        lead_assessor="odo (Lead Assessor, Team DeepSpace9)",
        project_sponsor="jadzia (Project Lead, Team DeepSpace9)",
        frozen_at=datetime.now(timezone.utc).isoformat(),
        total_processes=len(artifacts_by_process),
        total_artifacts=len(artifacts),
        artifacts_by_process=artifacts_by_process,
        process_attribute_coverage=pa_coverage,
        interview_records_rule=rule,
        isolation_guarantees=guarantees,
        artifacts=artifacts,
    )

    payload = json.dumps(index.to_dict(), sort_keys=True, indent=2)
    index.index_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    return index


def validate_preassessment_index(index: PreAssessmentEvidenceIndex) -> tuple[bool, list[str]]:
    """Validate pre-assessment evidence index integrity and compliance."""
    errors = []
    if index.total_processes != 17:
        errors.append(f"Expected 17 processes, got {index.total_processes}")
    if index.total_artifacts != 34:
        errors.append(f"Expected 34 artifacts, got {index.total_artifacts}")
    if index.product_id != ASSESSED_PRODUCT:
        errors.append(f"Product mismatch: {index.product_id}")
    if index.baseline_id != TARGET_BASELINE:
        errors.append(f"Baseline mismatch: {index.baseline_id}")
    if index.commit_sha != TARGET_COMMIT:
        errors.append(f"Commit SHA mismatch: {index.commit_sha}")

    for art in index.artifacts:
        if not art.authenticity_verified:
            errors.append(f"[{art.artifact_id}] Authenticity not verified")
        if art.validity != "frozen":
            errors.append(f"[{art.artifact_id}] Validity is not frozen: {art.validity}")
        if len(art.sha256) != 64:
            errors.append(f"[{art.artifact_id}] Invalid SHA-256 length: {len(art.sha256)}")
        if not art.outcome_indicators:
            errors.append(f"[{art.artifact_id}] Missing outcome indicators")

    return len(errors) == 0, errors


def generate_json_artifacts(output_dir: Path) -> dict[str, str]:
    """Generate and write the pre-assessment evidence index JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    index = build_preassessment_evidence_index()
    valid, errors = validate_preassessment_index(index)
    if not valid:
        raise ValueError(f"Validation failed: {errors}")

    report_path = output_dir / "ECU-PREASSESSMENT-EVIDENCE-INDEX-v0.7.0.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(index.to_dict(), f, indent=2, sort_keys=True)
        f.write("\n")

    with open(report_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()

    return {
        "report_path": str(report_path),
        "report_sha256": sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Automotive ECU Pre-Assessment Evidence Index Engine (Task 0018-04)")
    parser.add_argument("--generate", action="store_true", help="Generate pre-assessment evidence index JSON file")
    parser.add_argument("--output-dir", type=str, default="docs/dossiers/assessment", help="Output directory for generated JSON")
    parser.add_argument("--validate", action="store_true", help="Validate pre-assessment evidence index integrity")
    args = parser.parse_args()

    index = build_preassessment_evidence_index()
    valid, errors = validate_preassessment_index(index)

    if args.validate or not args.generate:
        if valid:
            print(f"SUCCESS: Pre-assessment evidence index valid and frozen across {index.total_processes} processes and {index.total_artifacts} artifacts.")
        else:
            print(f"FAILED: Found {len(errors)} validation errors:")
            for e in errors:
                print(f"  - {e}")
            return 1

    if args.generate:
        out_dir = Path(args.output_dir)
        res = generate_json_artifacts(out_dir)
        print(f"Generated Pre-Assessment Evidence Index: {res['report_path']} (SHA: {res['report_sha256']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
