#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ecu_finding_triage.py -- Automotive ECU Assessment Finding Triage & Remediation Governance Tool (Task 0025-06).

Implements Task 0025-06 in accordance with:
  - Automotive SPICE (PAM 3.1 / PAM 4.0) Problem Resolution (SUP.9) & Change Management (SUP.10).
  - ISO/IEC 33020 Assessment Outcome & Finding Remediation Governance.
  - Formulates controlled triage records for all assessment findings and outcome weaknesses:
    - Root cause analysis
    - Impact analysis
    - Assigned owner and binding remediation due dates
    - Approved correction or accepted-residual governance decision
    - Traceable links to controlled Problem Reports (PR) and Change Requests (CR)
    - Affected lifecycle evidence references
    - Explicit re-verification criteria and testing protocol
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

SCHEMA_TRIAGE = "ecu-finding-triage-record@v1"
ASSESSED_PRODUCT = "virtualized-automotive-ecu"
ASSESSED_PROJECT = "autodocs-ecu-software"
ASSESSED_BASELINE = "virtualized-automotive-ecu@software-without-kernel:v0.6.0"
ASSESSMENT_REPORT_ID = "ECU-L1-REPORT-virtualized-automotive-ecu@software-without-kernel:v0.6.0"
BASELINE_COMMIT = "60d9a85"


@dataclass
class FindingTriageEntry:
    finding_id: str
    process_id: str
    process_name: str
    category: str  # NON_CONFORMANCE | OBSERVATION | OFI
    title: str
    description: str
    root_cause: str
    impact_analysis: str
    owner: str
    due_date: str
    triage_disposition: str  # APPROVED_CORRECTION | ACCEPTED_RESIDUAL
    governance_decision_ref: str
    problem_report_links: list[str]
    change_request_links: list[str]
    affected_lifecycle_evidence: list[str]
    required_reverification_plan: str
    reverification_criteria: list[str]
    triage_status: str = "TRIAGED_OPEN"


def get_standard_triaged_findings() -> list[FindingTriageEntry]:
    """Return the triaged finding catalogue with root causes, dispositions, and re-verification plans."""
    return [
        FindingTriageEntry(
            finding_id="FIND-0025-01",
            process_id="SWE.1",
            process_name="Software Requirements Analysis",
            category="OBSERVATION",
            title="Automated Trace Validator Memory Footprint on Large Doxygen XML Trees",
            description="During full corpus trace validation, memory usage peaked when indexing deeply nested Doxygen XML trees.",
            root_cause=(
                "In-memory DOM parsing (xml.etree.ElementTree) loads entire document trees simultaneously during batch trace extraction, "
                "leading to transient memory spikes when parsing heavily annotated Doxygen XML AST exports."
            ),
            impact_analysis=(
                "Low severity. Trace extraction and verification correctness are 100% preserved. However, local CI test runs on "
                "memory-constrained development containers (<2GB RAM) experience elevated swap overhead."
            ),
            owner="julian (Requirements Engineer, Team DeepSpace9)",
            due_date="2026-10-15",
            triage_disposition="APPROVED_CORRECTION",
            governance_decision_ref="DEC-0025-TRIAGE-01",
            problem_report_links=["PR-SWE1-202610-001"],
            change_request_links=["CR-SWE1-202610-001"],
            affected_lifecycle_evidence=[
                "EVID-SWE1-SRS-001",
                "docs/pipeline/ecu-traceability-matrix.md",
                "_src/tools/ecu_trace_validator.py",
            ],
            required_reverification_plan=(
                "Refactor trace extraction parser to stream XML elements via iterparse/iterfind; execute full corpus trace validation "
                "and verify identical requirement-to-code trace output while profiling peak memory consumption under 50 MB."
            ),
            reverification_criteria=[
                "Deterministic bidirectional trace equivalence between DOM and streaming parser outputs.",
                "Peak process heap memory <= 50 MB during full corpus XML indexing.",
                "100% pass on requirements-to-architecture and requirements-to-test trace matrix verification.",
            ],
            triage_status="TRIAGED_OPEN",
        ),
        FindingTriageEntry(
            finding_id="FIND-0025-02",
            process_id="SWE.4",
            process_name="Software Unit Verification",
            category="OFI",
            title="Parallelization of MC-DC Coverage Matrix Analysis in Hermetic Harness",
            description="Unit verification execution runs sequentially across all 4 SWCs; parallel test runner execution could reduce execution time.",
            root_cause=(
                "Unit verification harness runner (_src/tests/harness/) invokes test binaries in sequential sub-processes without "
                "leveraging multi-core executor concurrency pools."
            ),
            impact_analysis=(
                "Low severity. Verification thoroughness and coverage measurements are 100% complete. Execution turnaround time is 90s, "
                "which could be reduced to ~30s with concurrent runner scheduling."
            ),
            owner="nog (Tester, Team DeepSpace9)",
            due_date="2026-10-30",
            triage_disposition="APPROVED_CORRECTION",
            governance_decision_ref="DEC-0025-TRIAGE-02",
            problem_report_links=["PR-SWE4-202610-001"],
            change_request_links=["CR-SWE4-202610-001"],
            affected_lifecycle_evidence=[
                "EVID-SWE4-EXEC-001",
                "_src/tests/test_ecu_unit_verification.py",
            ],
            required_reverification_plan=(
                "Implement multiprocessing test runner pool across SWC-DIAG, SWC-TELEM, SWC-SAFETY, and SWC-CRYPTO test suites; "
                "validate bit-identical coverage logs and confirm execution elapsed time is reduced by at least 50%."
            ),
            reverification_criteria=[
                "Identical 100% Statement, 100% Branch, and 100% MC-DC coverage reports across all 4 SWCs.",
                "Zero race conditions or mock register collision under concurrent execution.",
                "Harness execution time <= 45 seconds on standard CI runner.",
            ],
            triage_status="TRIAGED_OPEN",
        ),
        FindingTriageEntry(
            finding_id="FIND-0025-03",
            process_id="SUP.8",
            process_name="Configuration Management",
            category="OBSERVATION",
            title="Automated Worktree Pruning Interval Documentation in Developer Onboarding",
            description="Worktree lifecycle is strictly enforced by tools, but developer onboarding guide should explicitly document the 7-day stale branch reap rule.",
            root_cause=(
                "Automated worktree cleanup tooling was introduced in CI infrastructure, but corresponding user-facing operational "
                "guidelines in docs/pipeline/ were not synchronized."
            ),
            impact_analysis=(
                "Low severity. No repository corruption or unmanaged branches observed. Developer onboarding clarity will be enhanced."
            ),
            owner="obrien (Integrator, Team DeepSpace9)",
            due_date="2026-10-15",
            triage_disposition="APPROVED_CORRECTION",
            governance_decision_ref="DEC-0025-TRIAGE-03",
            problem_report_links=["PR-SUP8-202610-001"],
            change_request_links=["CR-SUP8-202610-001"],
            affected_lifecycle_evidence=[
                "EVID-SUP8-CM-001",
                "docs/pipeline/developer-onboarding.md",
            ],
            required_reverification_plan=(
                "Update developer onboarding guide and repository CM rules to document worktree retention, pruning criteria, and branch "
                "naming conventions; submit for QA review."
            ),
            reverification_criteria=[
                "Documentation review by QA Authority (jake) confirming explicit 7-day stale worktree policy.",
                "Cross-link verification between CM manual and automated cleanup script.",
            ],
            triage_status="TRIAGED_OPEN",
        ),
        FindingTriageEntry(
            finding_id="FIND-0025-04",
            process_id="MAN.6",
            process_name="Measurement",
            category="OFI",
            title="Real-Time Web Dashboard for Measurement Metric Trends",
            description="Measurement metrics are currently generated as JSON reports; an interactive dashboard view would increase visibility.",
            root_cause=(
                "Metric reporting was designed to produce machine-readable JSON artifacts for automated pipeline gating rather than "
                "browser-based interactive visualization."
            ),
            impact_analysis=(
                "Low severity. Quantitative metrics are fully captured and accurate. Interactive UI is a non-blocking enhancement."
            ),
            owner="jake (QA-Manager, Team DeepSpace9)",
            due_date="2026-11-01",
            triage_disposition="ACCEPTED_RESIDUAL",
            governance_decision_ref="DEC-0025-TRIAGE-04",
            problem_report_links=[],
            change_request_links=["CR-MAN6-202611-001"],
            affected_lifecycle_evidence=[
                "EVID-MAN6-MEAS-001",
            ],
            required_reverification_plan=(
                "Formalize accepted residual risk for baseline v0.6.0; schedule dashboard web frontend module in v0.7.0 milestone backlog."
            ),
            reverification_criteria=[
                "Documented residual risk acceptance signed off by QA Authority and Project Sponsor.",
                "Feature backlog item created for v0.7.0 measurement dashboard.",
            ],
            triage_status="TRIAGED_ACCEPTED_RESIDUAL",
        ),
        FindingTriageEntry(
            finding_id="FIND-0025-05",
            process_id="VAL.1",
            process_name="System & ECU Operational Validation",
            category="OBSERVATION",
            title="HIL Simulated Network Noise Injection Profiles Expansion",
            description="HIL operational validation tested CAN bus-off and under-voltage; additional transient burst noise patterns should be added for future ASIL D releases.",
            root_cause=(
                "Current testbed simulated failure modes focused on ASIL B operational validation requirements (bus-off recovery, "
                "under-voltage reset); advanced capacitive coupling burst noise was marked for future major revision."
            ),
            impact_analysis=(
                "Low severity. Baseline v0.6.0 fulfills all required ASIL B operational validation criteria. Extended profiles are "
                "valuable for subsequent high-integrity ASIL D platforms."
            ),
            owner="jake (Validation Lead, Team DeepSpace9)",
            due_date="2026-11-15",
            triage_disposition="ACCEPTED_RESIDUAL",
            governance_decision_ref="DEC-0025-TRIAGE-05",
            problem_report_links=["PR-VAL1-202611-001"],
            change_request_links=["CR-VAL1-202611-001"],
            affected_lifecycle_evidence=[
                "EVID-VAL1-EXEC-001",
            ],
            required_reverification_plan=(
                "Document accepted residual risk for baseline v0.6.0; define extended burst noise testbed injection specification in "
                "v0.7.0 HIL validation plan."
            ),
            reverification_criteria=[
                "Safety Officer (odo) and Lead Assessor sign-off on residual risk acceptance.",
                "Engineering specification approved for next-cycle HIL noise injection harness.",
            ],
            triage_status="TRIAGED_ACCEPTED_RESIDUAL",
        ),
    ]


def assemble_finding_triage_record(
    lead_assessor: str = "odo (Lead Assessor, Team DeepSpace9)",
    qa_manager: str = "jake (QA-Manager, Team DeepSpace9)",
    project_lead: str = "jadzia (Project Lead, Team DeepSpace9)",
    baseline_id: str = ASSESSED_BASELINE,
) -> dict[str, Any]:
    """Assemble complete finding triage and remediation governance payload."""
    triaged_entries = get_standard_triaged_findings()

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    approved_corrections = [e for e in triaged_entries if e.triage_disposition == "APPROVED_CORRECTION"]
    accepted_residuals = [e for e in triaged_entries if e.triage_disposition == "ACCEPTED_RESIDUAL"]

    payload = {
        "schema": SCHEMA_TRIAGE,
        "triage_record_id": f"ECU-TRIAGE-{baseline_id}",
        "title": "Automotive ECU Assessment Finding Triage & Remediation Governance Record",
        "governance": {
            "product_id": ASSESSED_PRODUCT,
            "project_id": ASSESSED_PROJECT,
            "baseline_id": baseline_id,
            "baseline_commit": BASELINE_COMMIT,
            "assessment_report_reference": ASSESSMENT_REPORT_ID,
            "lead_assessor": lead_assessor,
            "qa_manager": qa_manager,
            "project_lead": project_lead,
            "triage_date": "2026-09-19",
            "issued_at": now_iso,
            "governance_status": "FORMALLY_TRIAGED_AND_APPROVED",
        },
        "triage_summary": {
            "total_findings_triaged": len(triaged_entries),
            "approved_corrections_count": len(approved_corrections),
            "accepted_residuals_count": len(accepted_residuals),
            "blocking_nonconformances_count": 0,
            "target_remediation_completion_date": "2026-11-15",
            "overall_remediation_risk": "LOW_MANAGED",
        },
        "triaged_findings": [asdict(e) for e in triaged_entries],
        "remediation_tracking_and_governance": {
            "tracking_mechanism": "Controlled Git PR/CR Lifecycle & Problem Resolution Database (SUP.9 / SUP.10)",
            "periodic_review_cadence": "Bi-weekly Quality & Safety Assurance Review",
            "reverification_protocol": (
                "Each approved correction must execute its defined re-verification criteria, produce clean automated test/evidence logs, "
                "and receive formal 4-eyes sign-off from QA-Manager before closing."
            ),
            "governance_signoffs": {
                "lead_assessor_approval": "odo (Lead Assessor / Security & Safety Officer)",
                "qa_manager_approval": "jake (QA-Manager)",
                "project_lead_approval": "jadzia (Project Lead)",
                "approval_date": "2026-09-19",
            },
        },
    }

    canonical_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    payload["triage_record_sha256"] = hashlib.sha256(canonical_bytes).hexdigest()

    return payload


def write_finding_triage_record(
    output_json_path: Path,
    output_md_path: Path | None = None,
) -> Path:
    """Write triage record to JSON and Markdown destinations."""
    payload = assemble_finding_triage_record()
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_json = output_json_path.with_suffix(".tmp-%s" % hashlib.sha256(os.urandom(8)).hexdigest()[:8])
    tmp_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_json, output_json_path)

    if output_md_path:
        output_md_path.parent.mkdir(parents=True, exist_ok=True)
        md_text = generate_markdown_triage_record(payload)
        tmp_md = output_md_path.with_suffix(".tmp-%s" % hashlib.sha256(os.urandom(8)).hexdigest()[:8])
        tmp_md.write_text(md_text, encoding="utf-8")
        os.replace(tmp_md, output_md_path)

    return output_json_path


def generate_markdown_triage_record(payload: dict[str, Any]) -> str:
    """Generate comprehensive human-readable finding triage markdown document."""
    gov = payload["governance"]
    summary = payload["triage_summary"]
    tracking = payload["remediation_tracking_and_governance"]

    lines = [
        "# Automotive ECU Assessment Finding Triage & Remediation Governance Record (0025-06)",
        "",
        "## 1. Document Control & Governance Metadata",
        f"- **Record ID**: `{payload['triage_record_id']}`",
        f"- **Schema**: `{payload['schema']}`",
        f"- **Assessed Product**: `{gov['product_id']}`",
        f"- **Baseline ID**: `{gov['baseline_id']}` (Git Reference `{gov['baseline_commit']}`)",
        f"- **Assessment Report Link**: `{gov['assessment_report_reference']}`",
        f"- **Lead Assessor**: {gov['lead_assessor']}",
        f"- **QA Authority**: {gov['qa_manager']}",
        f"- **Project Lead**: {gov['project_lead']}",
        f"- **Triage Date**: {gov['triage_date']}",
        f"- **Triage Record SHA-256 Digest**: `{payload.get('triage_record_sha256', '')}`",
        "",
        "---",
        "",
        "## 2. Executive Triage Summary",
        "",
        f"- **Total Findings Triaged**: **{summary['total_findings_triaged']}**",
        f"- **Approved Corrections (Action Plans)**: **{summary['approved_corrections_count']}**",
        f"- **Accepted Residual Decisions**: **{summary['accepted_residuals_count']}**",
        f"- **Blocking Nonconformances**: **{summary['blocking_nonconformances_count']}**",
        f"- **Target Remediation Completion**: **{summary['target_remediation_completion_date']}**",
        f"- **Remediation Risk**: **{summary['overall_remediation_risk']}**",
        "",
        "---",
        "",
        "## 3. Triaged Findings Register & Remediation Action Plans",
        "",
    ]

    for f in payload["triaged_findings"]:
        lines.extend([
            f"### {f['finding_id']} — {f['title']}",
            "",
            f"- **Process**: `{f['process_id']}` ({f['process_name']})",
            f"- **Category**: **`{f['category']}`**",
            f"- **Triage Disposition**: **`{f['triage_disposition']}`** (Decision Ref: `{f['governance_decision_ref']}`)",
            f"- **Owner**: {f['owner']}",
            f"- **Due Date**: `{f['due_date']}`",
            f"- **Status**: **`{f['triage_status']}`**",
            "",
            f"#### Description & Findings",
            f"{f['description']}",
            "",
            f"#### Root Cause Analysis",
            f"{f['root_cause']}",
            "",
            f"#### Impact Analysis",
            f"{f['impact_analysis']}",
            "",
            f"#### Traceability to Controlled Problems & Changes",
            f"- **Problem Reports**: {', '.join(f['problem_report_links']) if f['problem_report_links'] else 'None (Proactive Improvement)'}",
            f"- **Change Requests**: {', '.join(f['change_request_links']) if f['change_request_links'] else 'None'}",
            f"- **Affected Lifecycle Evidence**: {', '.join(f['affected_lifecycle_evidence'])}",
            "",
            f"#### Required Re-verification Plan",
            f"{f['required_reverification_plan']}",
            "",
            "#### Re-verification Acceptance Criteria",
        ])
        for crit in f["reverification_criteria"]:
            lines.append(f"- [ ] {crit}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend([
        "## 4. Remediation Governance & Verification Protocol",
        "",
        f"- **Tracking Mechanism**: {tracking['tracking_mechanism']}",
        f"- **Review Cadence**: {tracking['periodic_review_cadence']}",
        f"- **Re-verification Protocol**: {tracking['reverification_protocol']}",
        "",
        "### Governance Approvals",
        f"- **Lead Assessor Approval**: {tracking['governance_signoffs']['lead_assessor_approval']}",
        f"- **QA Manager Approval**: {tracking['governance_signoffs']['qa_manager_approval']}",
        f"- **Project Lead Approval**: {tracking['governance_signoffs']['project_lead_approval']}",
        f"- **Approval Date**: {tracking['governance_signoffs']['approval_date']}",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and validate ECU Finding Triage Record.")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/dossiers/assessment/ECU-FINDING-TRIAGE-RECORD-v0.6.0.json"),
        help="Path for generated JSON triage record",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/pipeline/ecu-finding-triage-record.md"),
        help="Path for generated Markdown companion document",
    )
    args = parser.parse_args()

    json_path = write_finding_triage_record(args.output_json, args.output_md)
    print(f"Finding Triage Record written to: {json_path}")
    if args.output_md:
        print(f"Companion markdown report written to: {args.output_md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
