#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ecu_pilot_plan.py -- Automotive ECU Managed Pilot Process Selection & Assessment Plan Tool (Task 0018-01).

Implements Task 0018-01 in accordance with:
  - Automotive SPICE (PAM 3.1 / PAM 4.0) Capability Level 2 (Managed Process) Requirements.
  - ISO/IEC 33020 Process Assessment Planning & Sampling Specifications.
  - Formulates the authoritative ECU Managed Pilot Plan:
    1. Selection and approval of representative ECU pilot process instances and release baselines.
    2. Assessment schedule and role-based interview battery.
    3. ECU execution evidence baseline rules (Feature 0019/doc campaigns strictly restricted to reusable mechanisms only; zero imported ratings).
    4. Risk-informed adaptive sampling and aggregation protocol.
    5. Assessor independence and 4-eyes governance safeguards.
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

SCHEMA_PILOT_PLAN = "ecu-pilot-assessment-plan@v1"
ASSESSED_PRODUCT = "virtualized-automotive-ecu"
ASSESSED_PROJECT = "autodocs-ecu-software"
TARGET_BASELINE = "virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1"
PREDECESSOR_BASELINE = "virtualized-automotive-ecu@software-without-kernel:v0.6.0-rev1"
TARGET_COMMIT = "8b2c49f"
PAM_VERSION = "Automotive SPICE PAM 3.1 / PAM 4.0 Reference Model (CL2 Managed Process)"


@dataclass
class PilotProcessSelection:
    process_id: str
    process_name: str
    process_instance_id: str
    process_category: str  # SOFTWARE_ENGINEERING | SYSTEM_ENGINEERING | SUPPORTING | MANAGEMENT | RELEASE | VALIDATION
    target_capability_level: int  # 2
    primary_owner: str
    swc_scope: list[str]
    cl2_entry_justification: str


@dataclass
class InterviewRoleSchedule:
    session_id: str
    target_processes: list[str]
    session_focus: str
    interviewees: list[str]
    assessor_lead: str
    planned_date: str
    evidence_focus: list[str]


@dataclass
class SamplingAggregationRule:
    rule_id: str
    scope: str
    methodology: str
    criteria: list[str]
    prohibited_practices: list[str]


def get_standard_pilot_processes() -> list[PilotProcessSelection]:
    """Return the 15 selected representative process instances for the CL2 managed pilot."""
    return [
        PilotProcessSelection(
            process_id="SWE.1",
            process_name="Software Requirements Analysis",
            process_instance_id="PI-SWE1-202610-PILOT1",
            process_category="SOFTWARE_ENGINEERING",
            target_capability_level=2,
            primary_owner="julian (Requirements Engineer)",
            swc_scope=["SWC-SAFETY", "SWC-CRYPTO", "SWC-DIAG", "SWC-TELEM"],
            cl2_entry_justification="Core V-cycle entry point; requires rigorous work product governance (GP 2.2) and resource planning (GP 2.1).",
        ),
        PilotProcessSelection(
            process_id="SWE.2",
            process_name="Software Architectural Design",
            process_instance_id="PI-SWE2-202610-PILOT1",
            process_category="SOFTWARE_ENGINEERING",
            target_capability_level=2,
            primary_owner="kira (Architect)",
            swc_scope=["SWC-SAFETY", "SWC-CRYPTO", "SWC-DIAG", "SWC-TELEM"],
            cl2_entry_justification="Defines memory partitioning and dynamic messaging; essential for cross-SWC interface control and review.",
        ),
        PilotProcessSelection(
            process_id="SWE.3",
            process_name="Software Detailed Design & Unit Construction",
            process_instance_id="PI-SWE3-202610-PILOT1",
            process_category="SOFTWARE_ENGINEERING",
            target_capability_level=2,
            primary_owner="miles (Software Developer)",
            swc_scope=["SWC-SAFETY", "SWC-CRYPTO", "SWC-DIAG", "SWC-TELEM"],
            cl2_entry_justification="Conforms to MISRA C:2012 with strict complexity containment; requires work product change tracking and unit review.",
        ),
        PilotProcessSelection(
            process_id="SWE.4",
            process_name="Software Unit Verification",
            process_instance_id="PI-SWE4-202610-PILOT1",
            process_category="SOFTWARE_ENGINEERING",
            target_capability_level=2,
            primary_owner="nog (Tester)",
            swc_scope=["SWC-SAFETY", "SWC-CRYPTO", "SWC-DIAG", "SWC-TELEM"],
            cl2_entry_justification="Hermetic unit test harness achieving 100% MC-DC coverage; requires automated execution monitoring and baseline logging.",
        ),
        PilotProcessSelection(
            process_id="SWE.5",
            process_name="Software Integration & Verification",
            process_instance_id="PI-SWE5-202610-PILOT1",
            process_category="SOFTWARE_ENGINEERING",
            target_capability_level=2,
            primary_owner="obrien (Integrator)",
            swc_scope=["SWC-SAFETY", "SWC-CRYPTO", "SWC-DIAG", "SWC-TELEM"],
            cl2_entry_justification="Integrates SWCs onto virtual target; verifies memory isolation, inter-SWC queues, and timing budgets.",
        ),
        PilotProcessSelection(
            process_id="SWE.6",
            process_name="Software Qualification Testing",
            process_instance_id="PI-SWE6-202610-PILOT1",
            process_category="SOFTWARE_ENGINEERING",
            target_capability_level=2,
            primary_owner="jake (QA-Manager) & nog (Tester)",
            swc_scope=["SWC-SAFETY", "SWC-CRYPTO", "SWC-DIAG", "SWC-TELEM"],
            cl2_entry_justification="Final qualification testing against functional and security requirements; requires complete traceability and formal gate clearance.",
        ),
        PilotProcessSelection(
            process_id="SYS.2",
            process_name="System Requirements Analysis",
            process_instance_id="PI-SYS2-202610-PILOT1",
            process_category="SYSTEM_ENGINEERING",
            target_capability_level=2,
            primary_owner="julian (Requirements Engineer)",
            swc_scope=["ECU-SYSTEM"],
            cl2_entry_justification="Defines system-level requirements and external vehicle CAN message interfaces.",
        ),
        PilotProcessSelection(
            process_id="SYS.3",
            process_name="System Architectural Design",
            process_instance_id="PI-SYS3-202610-PILOT1",
            process_category="SYSTEM_ENGINEERING",
            target_capability_level=2,
            primary_owner="kira (Architect)",
            swc_scope=["ECU-SYSTEM"],
            cl2_entry_justification="Defines hardware/software allocation and hardware virtual machine virtualization boundaries.",
        ),
        PilotProcessSelection(
            process_id="VAL.1",
            process_name="System & ECU Operational Validation",
            process_instance_id="PI-VAL1-202610-PILOT1",
            process_category="VALIDATION",
            target_capability_level=2,
            primary_owner="jake (Validation Lead) & odo (Safety)",
            swc_scope=["ECU-SYSTEM"],
            cl2_entry_justification="Validates operational endurance, bus-off recovery, and fault-injection scenarios under simulated HIL testbed.",
        ),
        PilotProcessSelection(
            process_id="SPL.2",
            process_name="Product Release",
            process_instance_id="PI-SPL2-202610-PILOT1",
            process_category="RELEASE",
            target_capability_level=2,
            primary_owner="obrien (Integrator) & jadzia (Project Lead)",
            swc_scope=["ECU-SYSTEM"],
            cl2_entry_justification="Governs immutable release packaging, cryptographic digest freezing, and management authorization.",
        ),
        PilotProcessSelection(
            process_id="SUP.1",
            process_name="Quality Assurance",
            process_instance_id="PI-SUP1-202610-PILOT1",
            process_category="SUPPORTING",
            target_capability_level=2,
            primary_owner="jake (QA-Manager)",
            swc_scope=["ALL-PROCESSES"],
            cl2_entry_justification="Independent process and work product audit authority enforcing 4-eyes gate reviews and compliance tracking.",
        ),
        PilotProcessSelection(
            process_id="SUP.8",
            process_name="Configuration Management",
            process_instance_id="PI-SUP8-202610-PILOT1",
            process_category="SUPPORTING",
            target_capability_level=2,
            primary_owner="obrien (Integrator)",
            swc_scope=["ALL-PROCESSES"],
            cl2_entry_justification="Enforces task-isolated branching, baseline integrity audits, and worktree retention rules.",
        ),
        PilotProcessSelection(
            process_id="SUP.9",
            process_name="Problem Resolution Management",
            process_instance_id="PI-SUP9-202610-PILOT1",
            process_category="SUPPORTING",
            target_capability_level=2,
            primary_owner="benjamin (Dispatcher)",
            swc_scope=["ALL-PROCESSES"],
            cl2_entry_justification="Systematic defect triage, root-cause tracking, and verification of corrective actions.",
        ),
        PilotProcessSelection(
            process_id="SUP.10",
            process_name="Change Request Management",
            process_instance_id="PI-SUP10-202610-PILOT1",
            process_category="SUPPORTING",
            target_capability_level=2,
            primary_owner="jadzia (Project Lead) & kira (Architect)",
            swc_scope=["ALL-PROCESSES"],
            cl2_entry_justification="Change Control Board governance, impact analysis, and regression verification.",
        ),
        PilotProcessSelection(
            process_id="MAN.3",
            process_name="Project Management",
            process_instance_id="PI-MAN3-202610-PILOT1",
            process_category="MANAGEMENT",
            target_capability_level=2,
            primary_owner="jadzia (Project Lead)",
            swc_scope=["ALL-PROCESSES"],
            cl2_entry_justification="Work breakdown structure, resource estimation, schedule monitoring, and atomic task tracking.",
        ),
        PilotProcessSelection(
            process_id="MAN.5",
            process_name="Risk Management",
            process_instance_id="PI-MAN5-202610-PILOT1",
            process_category="MANAGEMENT",
            target_capability_level=2,
            primary_owner="odo (Safety & Security Officer)",
            swc_scope=["ALL-PROCESSES"],
            cl2_entry_justification="Proactive risk register maintenance, severity evaluation, and residual risk mitigation.",
        ),
        PilotProcessSelection(
            process_id="MAN.6",
            process_name="Measurement",
            process_instance_id="PI-MAN6-202610-PILOT1",
            process_category="MANAGEMENT",
            target_capability_level=2,
            primary_owner="jake (QA-Manager)",
            swc_scope=["ALL-PROCESSES"],
            cl2_entry_justification="Quantitative metrics collection (coverage, defect density, cyclomatic complexity) and decision reporting.",
        ),
    ]


def get_standard_interview_schedule() -> list[InterviewRoleSchedule]:
    """Return the planned interview schedule and role assignments."""
    return [
        InterviewRoleSchedule(
            session_id="SESS-PILOT-01",
            target_processes=["MAN.3", "SPL.2", "SUP.10"],
            session_focus="Project Governance, Scope Definition, Release Authorization, Change Management",
            interviewees=["jadzia (Project Lead)", "obrien (Integrator)"],
            assessor_lead="odo (Lead Assessor)",
            planned_date="2026-10-05",
            evidence_focus=["WBS schedule", "Release authorization", "CCB records"],
        ),
        InterviewRoleSchedule(
            session_id="SESS-PILOT-02",
            target_processes=["SYS.2", "SWE.1"],
            session_focus="Requirements Elicitation, Allocation, Testability & Traceability",
            interviewees=["julian (Requirements Engineer)", "kira (Architect)"],
            assessor_lead="odo (Lead Assessor)",
            planned_date="2026-10-06",
            evidence_focus=["SRS documents", "Traceability matrices", "Acceptance criteria"],
        ),
        InterviewRoleSchedule(
            session_id="SESS-PILOT-03",
            target_processes=["SYS.3", "SWE.2", "SWE.3"],
            session_focus="Architecture, MPU Partitioning, Detailed Design & MISRA Construction",
            interviewees=["kira (Architect)", "miles (Software Developer)"],
            assessor_lead="odo (Lead Assessor)",
            planned_date="2026-10-07",
            evidence_focus=["Architectural model", "MISRA reports", "Header interface specs"],
        ),
        InterviewRoleSchedule(
            session_id="SESS-PILOT-04",
            target_processes=["SWE.4", "SWE.5", "SWE.6"],
            session_focus="Unit MC-DC Verification, Integration Testing & Software Qualification",
            interviewees=["nog (Tester)", "obrien (Integrator)", "jake (QA-Manager)"],
            assessor_lead="odo (Lead Assessor)",
            planned_date="2026-10-08",
            evidence_focus=["Unit test coverage logs", "Integration test logs", "Qualification records"],
        ),
        InterviewRoleSchedule(
            session_id="SESS-PILOT-05",
            target_processes=["VAL.1", "MAN.5"],
            session_focus="HIL Operational Validation, CAN Fault Injection & Risk Mitigation",
            interviewees=["jake (Validation Lead)", "odo (Safety Officer)"],
            assessor_lead="kira (Independent Assessor)",
            planned_date="2026-10-09",
            evidence_focus=["HIL execution logs", "Fault injection reports", "Risk register"],
        ),
        InterviewRoleSchedule(
            session_id="SESS-PILOT-06",
            target_processes=["SUP.1", "SUP.8", "SUP.9", "MAN.6"],
            session_focus="Quality Assurance Audits, CM Baseline Governance, Defect Lifecycle, Metrics",
            interviewees=["jake (QA-Manager)", "obrien (Integrator)", "benjamin (Dispatcher)"],
            assessor_lead="odo (Lead Assessor)",
            planned_date="2026-10-10",
            evidence_focus=["QA audit reports", "Git worktree audit logs", "Problem resolution database", "Metrics summaries"],
        ),
    ]


def get_standard_sampling_rules() -> list[SamplingAggregationRule]:
    """Return risk-informed adaptive sampling and aggregation governance rules."""
    return [
        SamplingAggregationRule(
            rule_id="SAMP-RULE-01",
            scope="Safety-Critical Software Components (SWC-SAFETY, SWC-CRYPTO)",
            methodology="100% Census Audit (Exhaustive Verification)",
            criteria=[
                "100% Statement, 100% Branch, 100% MC-DC structural unit coverage required.",
                "Zero MISRA C:2012 violations allowed.",
                "100% bidirectional traceability to safety/security requirements.",
            ],
            prohibited_practices=[
                "No statistical down-sampling of safety-critical functions.",
                "No exclusion of fault-injection or boundary cases.",
            ],
        ),
        SamplingAggregationRule(
            rule_id="SAMP-RULE-02",
            scope="General Diagnostic & Telemetry Components (SWC-DIAG, SWC-TELEM)",
            methodology="Risk-Informed Representative Sampling",
            criteria=[
                "Exhaustive testing of state machine transitions and UDS service handlers.",
                "Coverage sampling representative of all operational communication modes.",
            ],
            prohibited_practices=[
                "No arbitrary fixed count sampling (must be risk-justified).",
                "No averaging of pass rates across heterogeneous components.",
            ],
        ),
        SamplingAggregationRule(
            rule_id="SAMP-RULE-03",
            scope="Cross-Campaign Evidence Isolation Policy",
            methodology="Strict Boundary Segregation for Execution Evidence",
            criteria=[
                "ECU execution evidence must originate exclusively from genuine compiled C code running on virtual/target hardware.",
                "Documentation campaigns (such as Feature 0019) may provide reusable definitions, schemas, and governance templates only.",
            ],
            prohibited_practices=[
                "Zero importation of ratings from documentation campaigns.",
                "Zero inclusion of documentation or synthetic artifacts as ECU execution proof.",
            ],
        ),
    ]


def assemble_pilot_assessment_plan(
    project_sponsor: str = "jadzia (Project Lead, Team DeepSpace9)",
    lead_assessor: str = "odo (Lead Assessor, Team DeepSpace9)",
    qa_manager: str = "jake (QA-Manager, Team DeepSpace9)",
    architect: str = "kira (Architect, Team DeepSpace9)",
    target_baseline: str = TARGET_BASELINE,
) -> dict[str, Any]:
    """Assemble complete ECU Managed Pilot Assessment Plan payload."""
    procs = get_standard_pilot_processes()
    schedules = get_standard_interview_schedule()
    rules = get_standard_sampling_rules()

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    payload = {
        "schema": SCHEMA_PILOT_PLAN,
        "plan_id": f"ECU-PILOT-PLAN-{target_baseline}",
        "title": "Automotive ECU Managed Pilot Process Selection & Assessment Plan (CL2)",
        "governance": {
            "product_id": ASSESSED_PRODUCT,
            "project_id": ASSESSED_PROJECT,
            "target_release_baseline": target_baseline,
            "predecessor_baseline": PREDECESSOR_BASELINE,
            "target_commit": TARGET_COMMIT,
            "reference_standard": PAM_VERSION,
            "project_sponsor": project_sponsor,
            "lead_assessor": lead_assessor,
            "qa_manager": qa_manager,
            "architect": architect,
            "approval_date": "2026-09-19",
            "issued_at": now_iso,
            "plan_status": "FORMALLY_APPROVED_FOR_EXECUTION",
        },
        "pilot_scope_summary": {
            "total_selected_processes": len(procs),
            "target_capability_level": 2,
            "target_generic_practices": ["GP 2.1 Performance Management", "GP 2.2 Work Product Management"],
            "total_interview_sessions_planned": len(schedules),
            "total_sampling_rules": len(rules),
            "evidence_isolation_rule_enforced": True,
        },
        "selected_pilot_processes": [asdict(p) for p in procs],
        "interview_schedule_and_roles": [asdict(s) for s in schedules],
        "sampling_and_aggregation_protocol": [asdict(r) for r in rules],
        "evidence_baseline_and_isolation_policy": {
            "approved_evidence_baseline_id": f"ECU-EVIDENCE-INDEX-{target_baseline}",
            "execution_origin_mandatory": "ecu-execution exclusively",
            "documentation_campaign_constraint": (
                "Documentation campaigns (including Feature 0019) may contribute reusable definitions, schemas, "
                "and procedural mechanisms ONLY. Under NO circumstances may documentation artifacts or synthetic "
                "fixtures enter as ECU execution evidence or imported process ratings."
            ),
        },
        "assessor_independence_and_governance_safeguards": {
            "separation_of_duties_rule": (
                "Assessors and QA Authorities maintain complete independence from software development and integration tasks. "
                "Lead Assessor (odo) and QA Manager (jake) report directly to Executive Leadership."
            ),
            "four_eyes_authorization_rule": (
                "All assessment ratings, gate clearance decisions, and finding closures require independent 4-eyes review and approval."
            ),
            "governance_approvals": {
                "project_sponsor_signature": project_sponsor,
                "lead_assessor_signature": lead_assessor,
                "qa_manager_signature": qa_manager,
                "architect_signature": architect,
                "signed_date": "2026-09-19",
            },
        },
    }

    canonical_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    payload["pilot_plan_sha256"] = hashlib.sha256(canonical_bytes).hexdigest()

    return payload


def write_pilot_assessment_plan(
    output_json_path: Path,
    output_md_path: Path | None = None,
) -> Path:
    """Write pilot assessment plan to JSON and Markdown destinations."""
    payload = assemble_pilot_assessment_plan()
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_json = output_json_path.with_suffix(".tmp-%s" % hashlib.sha256(os.urandom(8)).hexdigest()[:8])
    tmp_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_json, output_json_path)

    if output_md_path:
        output_md_path.parent.mkdir(parents=True, exist_ok=True)
        md_text = generate_markdown_pilot_plan(payload)
        tmp_md = output_md_path.with_suffix(".tmp-%s" % hashlib.sha256(os.urandom(8)).hexdigest()[:8])
        tmp_md.write_text(md_text, encoding="utf-8")
        os.replace(tmp_md, output_md_path)

    return output_json_path


def generate_markdown_pilot_plan(payload: dict[str, Any]) -> str:
    """Generate human-readable ECU Managed Pilot Assessment Plan markdown."""
    gov = payload["governance"]
    summary = payload["pilot_scope_summary"]
    iso = payload["evidence_baseline_and_isolation_policy"]
    safe = payload["assessor_independence_and_governance_safeguards"]

    lines = [
        "# Automotive ECU Managed Pilot Process Selection & Assessment Plan (0018-01)",
        "",
        "## 1. Document Control & Governance Metadata",
        f"- **Plan ID**: `{payload['plan_id']}`",
        f"- **Schema**: `{payload['schema']}`",
        f"- **Product ID**: `{gov['product_id']}`",
        f"- **Target Release Baseline**: `{gov['target_release_baseline']}` (Predecessor: `{gov['predecessor_baseline']}`)",
        f"- **Target Commit**: `{gov['target_commit']}`",
        f"- **Reference Standard**: {gov['reference_standard']}",
        f"- **Project Sponsor**: {gov['project_sponsor']}",
        f"- **Lead Assessor**: {gov['lead_assessor']}",
        f"- **QA Authority**: {gov['qa_manager']}",
        f"- **Architect**: {gov['architect']}",
        f"- **Approval Date**: {gov['approval_date']}",
        f"- **Plan Status**: **`{gov['plan_status']}`**",
        f"- **Plan SHA-256 Digest**: `{payload.get('pilot_plan_sha256', '')}`",
        "",
        "---",
        "",
        "## 2. Executive Pilot Scope Summary",
        "",
        f"- **Total Selected Process Instances**: **{summary['total_selected_processes']}**",
        f"- **Target Capability Level**: **Level {summary['target_capability_level']} (Managed Process)**",
        f"- **Target Generic Practices**: {', '.join(summary['target_generic_practices'])}",
        f"- **Planned Interview Sessions**: **{summary['total_interview_sessions_planned']}**",
        f"- **Sampling & Aggregation Rules**: **{summary['total_sampling_rules']}**",
        "",
        "---",
        "",
        "## 3. Approved Pilot Process Instances",
        "",
        "| Process ID | Process Name | Process Instance | Category | Target Level | Primary Owner | SWC Scope |",
        "| :---: | :--- | :--- | :---: | :---: | :--- | :--- |",
    ]

    for p in payload["selected_pilot_processes"]:
        lines.append(
            f"| **`{p['process_id']}`** | {p['process_name']} | `{p['process_instance_id']}` | `{p['process_category']}` | **Level {p['target_capability_level']}** | {p['primary_owner']} | {', '.join(p['swc_scope'])} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Planned Assessment Interview Battery & Schedule",
        "",
        "| Session ID | Target Processes | Focus & Topics | Interviewees | Lead Assessor | Planned Date |",
        "| :---: | :--- | :--- | :--- | :--- | :---: |",
    ])

    for s in payload["interview_schedule_and_roles"]:
        lines.append(
            f"| **`{s['session_id']}`** | {', '.join(s['target_processes'])} | {s['session_focus']} | {', '.join(s['interviewees'])} | {s['assessor_lead']} | `{s['planned_date']}` |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 5. Risk-Informed Adaptive Sampling & Aggregation Rules",
        "",
    ])

    for r in payload["sampling_and_aggregation_protocol"]:
        lines.extend([
            f"### {r['rule_id']}: {r['scope']}",
            f"- **Methodology**: {r['methodology']}",
            "",
            "#### Governance Criteria",
        ])
        for c in r["criteria"]:
            lines.append(f"- [x] {c}")
        lines.extend([
            "",
            "#### Prohibited Practices",
        ])
        for p in r["prohibited_practices"]:
            lines.append(f"- [x] **PROHIBITED**: {p}")
        lines.extend([
            "",
            "---",
            "",
        ])

    lines.extend([
        "## 6. Evidence Baseline & Cross-Campaign Isolation Policy",
        "",
        "> [!IMPORTANT]",
        f"> **Mandatory Origin Filter**: `{iso['execution_origin_mandatory']}`",
        f"> **Documentation Isolation Rule**: {iso['documentation_campaign_constraint']}",
        "",
        "---",
        "",
        "## 7. Assessor Independence & Governance Approvals",
        "",
        f"- **Separation of Duties**: {safe['separation_of_duties_rule']}",
        f"- **4-Eyes Authorization**: {safe['four_eyes_authorization_rule']}",
        "",
        "### Formal Plan Signatures",
        f"- **Project Sponsor**: {safe['governance_approvals']['project_sponsor_signature']}",
        f"- **Lead Assessor**: {safe['governance_approvals']['lead_assessor_signature']}",
        f"- **QA Authority**: {safe['governance_approvals']['qa_manager_signature']}",
        f"- **Architect**: {safe['governance_approvals']['architect_signature']}",
        f"- **Date**: {safe['governance_approvals']['signed_date']}",
        "",
    ])

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and validate ECU Managed Pilot Assessment Plan.")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/dossiers/assessment/ECU-PILOT-ASSESSMENT-PLAN-v0.7.0.json"),
        help="Path for generated JSON pilot plan",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/pipeline/ecu-pilot-managed-assessment-plan.md"),
        help="Path for generated Markdown companion document",
    )
    args = parser.parse_args()

    json_path = write_pilot_assessment_plan(args.output_json, args.output_md)
    print(f"Pilot Assessment Plan written to: {json_path}")
    if args.output_md:
        print(f"Companion markdown report written to: {args.output_md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
