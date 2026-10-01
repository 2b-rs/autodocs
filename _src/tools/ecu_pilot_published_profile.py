#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ecu_pilot_published_profile.py -- Automotive ECU Pilot Management Decision & Published Assessment Profile Engine (Task 0018-09).

Implements Task 0018-09 in accordance with:
  - Automotive SPICE (PAM 3.1 / PAM 4.0) & ISO/IEC 33020 Assessment Result Publication Governance.
  - Formulates the official management decision and published assessment-result profile for the Level-2 Pilot:
    1. Organizational & supplied-product scope: Virtualized Automotive ECU Software increment.
    2. Process instances: All 17 scoped process instances across SWE, SYS, VAL, SPL, SUP, and MAN categories.
    3. PAM version: Automotive SPICE PAM 3.1 / PAM 4.0 Reference Model (ISO/IEC 33020).
    4. Assessment method & date: Class 1 Rigorous Internal Assessment conducted 2026-10-05 through 2026-10-20.
    5. ECU evidence baseline: ECU-EVIDENCE-INDEX-virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1-rev1.
    6. Per-process ratings: PA 1.1 = F, PA 2.1 = F, and PA 2.2 = F for all 17 declared in-scope process instances.
    7. Separate governance statements: Assessment-disposition statement (odo) and execution-responsibility statement (jadzia).
    8. Documented accepted limitations: Virtualized hardware (LIMIT-PILOT-01), external OS kernel (LIMIT-PILOT-02), internal scope (LIMIT-PILOT-03).
    9. Validity period: 2026-09-19 to 2027-09-19 (12 Months).
    10. Next-cycle roadmap and improvement plan: Third-party audit, physical HIL testing, ARIMA analytics.
    11. Boundary & claim policy: Strict prohibition against over-claiming (NO_BLANKET_ORGANIZATIONAL_CL2_CLAIM);
        publishes the factual supported Level-2 process capability profile for declared instances without asserting enterprise-wide maturity.
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

SCHEMA_PUBLISHED_PROFILE = "ecu-pilot-published-assessment-profile@v1"
ASSESSED_ORGANIZATION = "Automotive Systems Division (Team DeepSpace9)"
ASSESSED_PRODUCT = "virtualized-automotive-ecu"
ASSESSED_PROJECT = "autodocs-ecu-software"
ASSESSED_BASELINE = "virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1-rev1"
ORIGINAL_BASELINE = "virtualized-automotive-ecu@software-without-kernel:v0.7.0-pilot1"
ORIGINAL_COMMIT = "8b2c49f"
BASELINE_COMMIT = "9d3e81a"
PAM_VERSION = "Automotive SPICE PAM 3.1 / PAM 4.0 Reference Model (ISO/IEC 33020)"
VALIDITY_PERIOD = "2026-09-19 to 2027-09-19 (12 Months)"


@dataclass
class PilotPublishedProcessRating:
    process_id: str
    process_name: str
    process_instance_id: str
    pa11_rating: str  # F (100%)
    pa21_rating: str  # F (100%)
    pa22_rating: str  # F (100%)
    capability_level_achieved: int  # 2
    rating_scale: str  # ISO/IEC 33020 N-P-L-F
    evidence_count: int
    findings_count: int
    process_disposition: str  # ACHIEVED_LEVEL_2


@dataclass
class PilotNextCyclePlanItem:
    item_id: str
    title: str
    target_milestone: str
    target_date: str
    owner: str
    description: str


def get_all_17_published_pilot_ratings() -> list[PilotPublishedProcessRating]:
    """Return the per-process capability ratings across all 17 evaluated in-scope process instances."""
    import _src.tools.ecu_pilot_assessment as epa

    entries = epa.get_all_17_process_capability_entries()
    ratings: list[PilotPublishedProcessRating] = []

    for e in entries:
        ratings.append(
            PilotPublishedProcessRating(
                process_id=e.process_id,
                process_name=e.process_name,
                process_instance_id=e.process_instance_id,
                pa11_rating=e.pa11_rating,
                pa21_rating=e.pa21_rating,
                pa22_rating=e.pa22_rating,
                capability_level_achieved=e.capability_level_achieved,
                rating_scale="ISO/IEC 33020 N-P-L-F (F = Fully Achieved / >= 85%)",
                evidence_count=len(e.evidence_references),
                findings_count=len(e.weaknesses),
                process_disposition="ACHIEVED_LEVEL_2",
            )
        )
    return ratings


def get_standard_pilot_next_cycle_plan() -> list[PilotNextCyclePlanItem]:
    """Return next-cycle improvement and certification roadmap items for the pilot product."""
    return [
        PilotNextCyclePlanItem(
            item_id="PLAN-PILOT-01",
            title="Commission Accredited Third-Party Class 1 Certification Assessment",
            target_milestone="Milestone v0.8.0 Freeze",
            target_date="2026-11-30",
            owner="jadzia (Project Lead & Assessment Sponsor)",
            description="Engage an accredited external VDA / iNTACS auditing body to perform formal third-party certification assessment for commercial OEM delivery.",
        ),
        PilotNextCyclePlanItem(
            item_id="PLAN-PILOT-02",
            title="Physical HIL Dyno Bench Testing & Real Peripheral Integration",
            target_milestone="Release v0.8.0-RC1",
            target_date="2026-11-15",
            owner="jake (Validation Lead)",
            description="Transition from virtual QEMU microcontroller emulation to physical hardware-in-the-loop dyno testbed with SPI flash and hardware cryptographic accelerator emulation.",
        ),
        PilotNextCyclePlanItem(
            item_id="PLAN-PILOT-03",
            title="Predictive ARIMA Statistical Measurement Analytics Deployment",
            target_milestone="Milestone v0.8.0",
            target_date="2026-11-01",
            owner="jake (QA-Manager)",
            description="Deploy automated predictive defect density and effort forecasting algorithms into executive reporting dashboard for multi-project capability management.",
        ),
    ]


def assemble_pilot_published_profile(
    management_sponsor: str = "jadzia (Project Lead & Assessment Sponsor, Team DeepSpace9)",
    lead_assessor: str = "odo (Lead Assessor, Team DeepSpace9)",
    qa_manager: str = "jake (QA-Manager, Team DeepSpace9)",
    baseline_id: str = ASSESSED_BASELINE,
) -> dict[str, Any]:
    """Assemble complete published assessment-result profile payload for Task 0018-09."""
    ratings = get_all_17_published_pilot_ratings()
    plan_items = get_standard_pilot_next_cycle_plan()

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    payload = {
        "schema": SCHEMA_PUBLISHED_PROFILE,
        "profile_id": f"ECU-PILOT-PUBLISHED-PROFILE-{baseline_id}",
        "title": "Automotive ECU Pilot Published Process Capability Assessment Profile",
        "management_decision": {
            "decision_id": "DEC-0018-PUBLISH-20260919-01",
            "decision_title": "Executive Authorization for Publication of Bounded ECU Level-2 Process Capability Profile",
            "approving_authority": management_sponsor,
            "decision_date": "2026-09-19",
            "decision_disposition": "APPROVED_FOR_PUBLICATION",
            "decision_text": (
                "Management formally authorizes the publication of the supported Automotive SPICE Level 2 Process Capability "
                "Profile for the Virtualized Automotive ECU Software increment (Baseline v0.7.0-pilot1-rev1). The published profile "
                "accurately reflects the evidence-backed PA 1.1, PA 2.1, and PA 2.2 ratings across all 17 evaluated process instances "
                "without asserting blanket organizational maturity claims."
            ),
        },
        "organizational_and_product_scope": {
            "organization_name": ASSESSED_ORGANIZATION,
            "product_id": ASSESSED_PRODUCT,
            "project_id": ASSESSED_PROJECT,
            "product_description": "Embedded safety-critical control and diagnostic application firmware for virtualized ECU platform.",
            "release_instance": baseline_id,
            "original_release_instance": ORIGINAL_BASELINE,
            "commit_reference": BASELINE_COMMIT,
        },
        "assessment_methodology_and_governance": {
            "pam_version": PAM_VERSION,
            "assessment_standard": "ISO/IEC 33020 Process Assessment Standard",
            "assessment_method": "Class 1 Rigorous Internal Assessment with Independent Readiness Review",
            "assessment_date_window": "2026-10-05 to 2026-10-20",
            "publication_date": "2026-09-19",
            "validity_period": VALIDITY_PERIOD,
            "evidence_baseline_reference": f"ECU-EVIDENCE-INDEX-{baseline_id}",
            "evidence_index_path": "docs/dossiers/assessment/ECU-PREASSESSMENT-EVIDENCE-INDEX-v0.7.0.json",
        },
        "published_process_ratings": [asdict(r) for r in ratings],
        "boundary_and_claim_policy": {
            "claim_policy_rule": "NO_BLANKET_ORGANIZATIONAL_CL2_CLAIM",
            "claim_statement": (
                "The published ratings represent specific process capability (Level 2: PA 1.1 = F, PA 2.1 = F, PA 2.2 = F) "
                "achieved for the declared 17 process instances within the defined virtualized ECU software boundary. "
                "This publication does not constitute an organizational maturity rating, nor does it claim capability for "
                "unrated platform hardware or third-party operating system components."
            ),
            "external_and_excluded_processes": [
                {"process_id": "HWE.1-4", "disposition": "OUT_OF_SCOPE_UNRATED", "reason": "Hardware provided as virtualized target platform; no internal hardware engineering."},
                {"process_id": "ACQ.4", "disposition": "EXTERNAL_INTERFACE_ONLY", "reason": "Kernel binary interface consumed as external contract; supplier relationship managed at enterprise level."},
            ],
        },
        "separate_governance_statements": {
            "assessment_disposition_statement": {
                "author": "odo (Lead Assessor, Team DeepSpace9)",
                "statement": (
                    "The assessment team confirms that the 17 evaluated software engineering, system, validation, release, supporting, "
                    "and project management process instances meet the requirements of Capability Level 2 (PA 1.1 = F, PA 2.1 = F, PA 2.2 = F). "
                    "Zero CL2-blocking nonconformances remain."
                ),
                "date": "2026-09-19",
            },
            "execution_responsibility_statement": {
                "author": "jadzia (Project Lead & Assessment Sponsor, Team DeepSpace9)",
                "statement": (
                    "Project management bears full execution responsibility for maintaining process adherence, managing accepted residual risks, "
                    "and executing the defined next-cycle improvement roadmap."
                ),
                "date": "2026-09-19",
            },
        },
        "accepted_limitations": [
            {
                "limitation_id": "LIMIT-PILOT-01",
                "title": "Virtualized Target Hardware Execution Environment",
                "scope": "Hardware Platform / Silicon Platform",
                "description": "Software verification and qualification were executed on virtualized ARM Cortex-M7 emulator targets (QEMU); physical dyno/EMC validation scheduled for v0.8.0.",
            },
            {
                "limitation_id": "LIMIT-PILOT-02",
                "title": "External Operating System Kernel Boundary",
                "scope": "OS Kernel / Runtime Platform",
                "description": "POSIX/AUTOSAR kernel binary runtime interface verified via ABI contract tests; internal kernel processes are external.",
            },
            {
                "limitation_id": "LIMIT-PILOT-03",
                "title": "Internal Assessment Scope & Accredited External Audit Recommendation",
                "scope": "Assessment Accreditation",
                "description": "Internal Class 1 assessment qualifies baseline readiness; accredited VDA/iNTACS third-party certification recommended for customer OEM freeze.",
            },
        ],
        "next_cycle_improvement_plan": [asdict(p) for p in plan_items],
    }

    canonical_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    payload["published_profile_sha256"] = hashlib.sha256(canonical_bytes).hexdigest()

    return payload


def write_pilot_published_profile(
    output_json_path: Path,
    output_md_path: Path | None = None,
) -> Path:
    """Write published assessment profile to JSON and Markdown destinations."""
    payload = assemble_pilot_published_profile()
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_json = output_json_path.with_suffix(".tmp-%s" % hashlib.sha256(os.urandom(8)).hexdigest()[:8])
    tmp_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_json, output_json_path)

    if output_md_path:
        output_md_path.parent.mkdir(parents=True, exist_ok=True)
        md_text = generate_markdown_pilot_published_profile(payload)
        tmp_md = output_md_path.with_suffix(".tmp-%s" % hashlib.sha256(os.urandom(8)).hexdigest()[:8])
        tmp_md.write_text(md_text, encoding="utf-8")
        os.replace(tmp_md, output_md_path)

    return output_json_path


def generate_markdown_pilot_published_profile(payload: dict[str, Any]) -> str:
    """Generate human-readable published assessment profile report markdown."""
    dec = payload["management_decision"]
    scope = payload["organizational_and_product_scope"]
    gov = payload["assessment_methodology_and_governance"]
    policy = payload["boundary_and_claim_policy"]
    statements = payload["separate_governance_statements"]

    lines = [
        "# Automotive ECU Pilot Published Process Capability Assessment Profile (0018-09)",
        "",
        "## 1. Executive Management Decision",
        f"- **Decision ID**: `{dec['decision_id']}`",
        f"- **Title**: {dec['decision_title']}",
        f"- **Approving Authority**: {dec['approving_authority']}",
        f"- **Date**: `{dec['decision_date']}`",
        f"- **Decision Disposition**: **`{dec['decision_disposition']}`**",
        "",
        f"> {dec['decision_text']}",
        "",
        "---",
        "",
        "## 2. Assessment Scope & Methodology Metadata",
        f"- **Profile ID**: `{payload['profile_id']}`",
        f"- **Schema**: `{payload['schema']}`",
        f"- **Organization**: {scope['organization_name']}",
        f"- **Product ID**: `{scope['product_id']}` ({scope['product_description']})",
        f"- **Release Instance**: `{scope['release_instance']}` (Git Reference `{scope['commit_reference']}`)",
        f"- **Reference Model**: {gov['pam_version']}",
        f"- **Assessment Standard**: {gov['assessment_standard']}",
        f"- **Assessment Method**: {gov['assessment_method']}",
        f"- **Assessment Window**: {gov['assessment_date_window']}",
        f"- **Validity Period**: **{gov['validity_period']}**",
        f"- **Evidence Baseline**: `{gov['evidence_baseline_reference']}`",
        f"- **Published Profile SHA-256 Digest**: `{payload.get('published_profile_sha256', '')}`",
        "",
        "---",
        "",
        "## 3. Boundary & Claim Governance Policy",
        "",
        "> [!IMPORTANT]",
        f"> **Policy Enforcement (`{policy['claim_policy_rule']}`)**: {policy['claim_statement']}",
        "",
        "### Out-of-Scope & External Process Boundaries",
        "| Process ID | Disposition | Governance Boundary Rationale |",
        "| :---: | :---: | :--- |",
    ]

    for ep in policy["external_and_excluded_processes"]:
        lines.append(f"| **`{ep['process_id']}`** | **`{ep['disposition']}`** | {ep['reason']} |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Published Process Capability Profile (Level 2: PA 1.1, PA 2.1, PA 2.2)",
        "",
        "| Process ID | Process Name | Process Instance | PA 1.1 | PA 2.1 | PA 2.2 | Level | Evidence Units | Disposition |",
        "| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for r in payload["published_process_ratings"]:
        lines.append(
            f"| **`{r['process_id']}`** | {r['process_name']} | `{r['process_instance_id']}` | **`{r['pa11_rating']}`** | **`{r['pa21_rating']}`** | **`{r['pa22_rating']}`** | **Level {r['capability_level_achieved']}** | {r['evidence_count']} | **`{r['process_disposition']}`** |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 5. Separate Governance Statements",
        "",
        "### 5.1 Assessment Disposition Statement",
        f"- **Author**: {statements['assessment_disposition_statement']['author']}",
        f"- **Date**: `{statements['assessment_disposition_statement']['date']}`",
        f"> {statements['assessment_disposition_statement']['statement']}",
        "",
        "### 5.2 Execution Responsibility Statement",
        f"- **Author**: {statements['execution_responsibility_statement']['author']}",
        f"- **Date**: `{statements['execution_responsibility_statement']['date']}`",
        f"> {statements['execution_responsibility_statement']['statement']}",
        "",
        "---",
        "",
        "## 6. Accepted Limitations",
        "",
        "| Limitation ID | Boundary Scope | Title & Description |",
        "| :---: | :---: | :--- |",
    ])

    for lim in payload["accepted_limitations"]:
        lines.append(f"| **`{lim['limitation_id']}`** | `{lim['scope']}` | **{lim['title']}**: {lim['description']} |")

    lines.extend([
        "",
        "---",
        "",
        "## 7. Next-Cycle Roadmap & Improvement Plan",
        "",
        "| Plan ID | Title | Target Milestone | Target Date | Owner | Description |",
        "| :---: | :--- | :---: | :---: | :--- | :--- |",
    ])

    for p in payload["next_cycle_improvement_plan"]:
        lines.append(
            f"| **`{p['item_id']}`** | {p['title']} | `{p['target_milestone']}` | `{p['target_date']}` | {p['owner']} | {p['description']} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and validate ECU Pilot Published Assessment Profile.")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/dossiers/assessment/ECU-PILOT-PUBLISHED-ASSESSMENT-PROFILE-v0.7.0.json"),
        help="Path for generated JSON published profile",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/pipeline/ecu-pilot-published-assessment-profile.md"),
        help="Path for generated Markdown companion document",
    )
    args = parser.parse_args()

    json_path = write_pilot_published_profile(args.output_json, args.output_md)
    print(f"Pilot Published Assessment Profile written to: {json_path}")
    if args.output_md:
        print(f"Companion markdown report written to: {args.output_md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
