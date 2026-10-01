# ASPICE CL2 Managed Process Roles

**Status:** Normative definition of roles required for Managed Process Performance (PA 2.1 and MAN.3) under ASPICE CL2 scope.
**Reference:** Feature 0011-04

This document defines and assigns the required roles for the approved ECU profile, ensuring separation of concerns, explicit authorities, and competence requirements.

## 1. Role Definitions & Assignments

| Role | Responsibility | Authority | Independence Requirement | Required Competency | Assigned To (Primary) | Assigned To (Deputy) |
|---|---|---|---|---|---|---|
| **Process Owner** | Defines, maintains, and measures the process. Ensures process capability. | Authorizes process changes and tailored waivers. | Must be independent from daily execution pressures. | Process engineering, ASPICE framework, quantitative measurement. | **Jadzia** (Project Lead) | **Benjamin Sisko** |
| **Performer** (Implementer) | Executes the process, creates work products according to the process definition. | Can modify the assigned work product within scoped boundaries. | Cannot approve or formally QA their own work (TK-1). | Domain expertise (e.g., C++, Rust, AI inference, Requirements). | *Varies by task* (e.g., **Worf**, **Data**, **Tasha Yar**) | *Varies by task* |
| **Reviewer** | Inspects work products against criteria and guidelines before integration. | Can return work for rework. | Must not be the sole producer of the validation evidence or author of the work product. | Domain expertise matching the performer, review techniques. | *Varies by task* (e.g., **Miles O'Brien**, **Jake Sisko**) | *Varies by task* |
| **Approver** | Makes the final Acceptance decision on work products crossing integration checkpoints. | Grants `Acceptance: ✓`, authorizing integration. | Must satisfy TK-1 (cannot be the principal implementer). | System integration, impact analysis, boundary checking. | **Miles O'Brien** (Integrator) | **Kira Nerys** |
| **Curator** | Resolves ambiguous requirement data and decides on extraction ground truth. | Final decision on requirement validity and state. | Must not be the AI agent that proposed the value. | Product domain knowledge, requirements engineering. | **Julian Bashir** | **Jadzia** |
| **Release Authority** | Approves the final product baseline for publication or customer delivery. | Authorizes the final release and signs off on the readiness review. | Must be management or a designated release manager. | Release management, risk assessment, compliance. | **Benjamin Sisko** | **Jadzia** |
| **QA (Quality Assurance)** | Evaluates process adherence (process audits, nonconformance tracking). | Can issue binding process findings. Cannot repair the artifacts directly. | Must be organizationally independent from the project performers (QA Manager). | Audit practices, process norms (ASPICE), objective evaluation. | **Nog** (QA Manager) | **Odo** (if available) / External |
| **Assessor** | Conducts formal capability assessments (e.g., ASPICE CL2 assessment). | Determines capability level ratings and issues the assessment report. | Must be a Competent Assessor, completely independent of the project team. | Certified ISO/IEC 33020 / intacs Assessor. | **External Assessor** | N/A |
| **Escalation Role** | Resolves technical or process dissents that cannot be solved at the peer level. | Final arbiter of disputes, grants structural waivers. | Must have organizational authority over the conflicting parties. | Conflict resolution, architectural oversight, management. | **Jadzia** (Technical) / **Benjamin Sisko** (Process) | **Management** |

## 2. Independence Requirements (Summary)
- **TK-1 (Producer != Approver)**: The person who produces a work product or decisively defines its scope cannot be the sole approver or integrator of that work.
- **QA Independence**: The QA role must not write or repair the assessed artifact. They must remain objective reporters of process adherence.
- **Assessor Independence**: The Assessor must not be a member of the project team being assessed to ensure unbiased capability rating.

## 3. Deputies & Continuity
Deputies are assigned to ensure process continuity. A deputy assumes the full authority and competency requirements of the primary role when acting in that capacity. When a deputy acts, the resulting decision record must clearly state that the deputy exercised the authority.
