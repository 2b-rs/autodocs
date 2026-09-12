# MAN.3 Project-Plan Schemas, Validators, and Evidence Control (0012-07)

**Status:** Normative
**Reference:** Feature `0012-07`
**Prerequisites:** `0012-02`, `0012-03`, `0012-04`, `0012-05`, `0012-06`, `0012-08`
**Standard Baseline:** Automotive SPICE (ASPICE PAM 3.1 / PAM 4.0) MAN.3 (Project Management) & Process Attribute PA 2.1 (Performance Management Attribute)

---

## 1. Purpose, Scope & Governance

### 1.1 Objective
This document establishes the normative schemas, programmatic validators, reporting templates, and controlled retention pathways for Automotive SPICE PA 2.1 performance management. It ensures that all project planning, execution monitoring, resource accounting, interface communications, and deviation tracking evidence is generated continuously, deterministically, and correlated through normal execution rather than reconstructed retrospectively.

### 1.2 Scope
This standard governs all engineering, quality, architecture, and integration campaigns across the software development lifecycle (SWE.1 through SWE.6 and supporting processes SUP.1, SUP.8, SUP.9, SUP.10, MAN.3, MAN.5).

### 1.3 Key Principles
1. **Continuous Native Emission:** Evidence artifacts must be emitted by CI runners, tools, and mailbox orchestrators during task execution, not authored post-hoc.
2. **Immutable Traceability:** Every evidence artifact must be cryptographically hashed, linked to exact Git commit SHAs, and retained in controlled repository paths.
3. **Rigorous Negative Verification:** Automated validators must enforce negative checks against missing, stale, cross-process-instance, or retrospectively fabricated stage evidence.
4. **Four-Eyes Separation:** Verification and acceptance evidence must enforce strict role separation between implementers, reviewers, and integrators.

---

## 2. Core Schemas for PA 2.1 Evidence Generation

All JSON evidence records must validate against JSON Schema Draft-07 schemas defined below.

### 2.1 Campaign Project Plan Schema (`campaign-project-plan-v1.schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CampaignProjectPlan-v1",
  "type": "object",
  "required": [
    "schema",
    "campaign_id",
    "plan_version",
    "created_at",
    "updated_at",
    "lead_authority",
    "process_scope",
    "milestones",
    "work_packages",
    "resource_allocations",
    "communication_interfaces",
    "risk_allocations",
    "baseline_refs"
  ],
  "properties": {
    "schema": { "type": "string", "enum": ["campaign-project-plan-v1"] },
    "campaign_id": { "type": "string", "pattern": "^[a-z0-9-]+$" },
    "plan_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "lead_authority": { "type": "string", "description": "Project Lead agent identity" },
    "process_scope": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1
    },
    "milestones": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["milestone_id", "title", "target_date", "entry_criteria", "exit_criteria", "deliverables"],
        "properties": {
          "milestone_id": { "type": "string" },
          "title": { "type": "string" },
          "target_date": { "type": "string", "format": "date" },
          "entry_criteria": { "type": "array", "items": { "type": "string" } },
          "exit_criteria": { "type": "array", "items": { "type": "string" } },
          "deliverables": { "type": "array", "items": { "type": "string" } }
        }
      },
      "minItems": 1
    },
    "work_packages": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["task_id", "title", "assigned_role", "planned_minutes", "prerequisites", "target_deliverable"],
        "properties": {
          "task_id": { "type": "string" },
          "title": { "type": "string" },
          "assigned_role": { "type": "string" },
          "planned_minutes": { "type": "integer", "minimum": 1 },
          "prerequisites": { "type": "array", "items": { "type": "string" } },
          "target_deliverable": { "type": "string" }
        }
      },
      "minItems": 1
    },
    "resource_allocations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["role", "agent_id", "allocation_pct", "competency_record_ref"],
        "properties": {
          "role": { "type": "string" },
          "agent_id": { "type": "string" },
          "allocation_pct": { "type": "integer", "minimum": 1, "maximum": 100 },
          "competency_record_ref": { "type": "string" }
        }
      },
      "minItems": 1
    },
    "communication_interfaces": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["interface_id", "source_role", "target_role", "channel", "cadence"],
        "properties": {
          "interface_id": { "type": "string" },
          "source_role": { "type": "string" },
          "target_role": { "type": "string" },
          "channel": { "type": "string" },
          "cadence": { "type": "string" }
        }
      },
      "minItems": 1
    },
    "risk_allocations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["risk_id", "description", "mitigation_plan_ref"],
        "properties": {
          "risk_id": { "type": "string" },
          "description": { "type": "string" },
          "mitigation_plan_ref": { "type": "string" }
        }
      }
    },
    "baseline_refs": {
      "type": "object",
      "required": ["git_base_commit", "requirements_baseline", "architecture_baseline"],
      "properties": {
        "git_base_commit": { "type": "string", "pattern": "^[0-9a-f]{7,40}$" },
        "requirements_baseline": { "type": "string" },
        "architecture_baseline": { "type": "string" }
      }
    }
  }
}
```

### 2.2 Stage Evidence Manifest Schema (`stage-evidence-manifest-v1.schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StageEvidenceManifest-v1",
  "type": "object",
  "required": [
    "schema",
    "evidence_id",
    "campaign_id",
    "process_id",
    "stage_id",
    "task_id",
    "git_commit",
    "tree_digest",
    "timestamp_start",
    "timestamp_complete",
    "author",
    "reviewer",
    "integrator",
    "input_artifacts",
    "output_artifacts",
    "test_results",
    "four_eyes_verified"
  ],
  "properties": {
    "schema": { "type": "string", "enum": ["stage-evidence-manifest-v1"] },
    "evidence_id": { "type": "string" },
    "campaign_id": { "type": "string" },
    "process_id": { "type": "string" },
    "stage_id": { "type": "string" },
    "task_id": { "type": "string" },
    "git_commit": { "type": "string", "pattern": "^[0-9a-f]{7,40}$" },
    "tree_digest": { "type": "string" },
    "timestamp_start": { "type": "string", "format": "date-time" },
    "timestamp_complete": { "type": "string", "format": "date-time" },
    "author": { "type": "string" },
    "reviewer": { "type": "string" },
    "integrator": { "type": "string" },
    "input_artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "sha256"],
        "properties": {
          "path": { "type": "string" },
          "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" }
        }
      }
    },
    "output_artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "sha256"],
        "properties": {
          "path": { "type": "string" },
          "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" }
        }
      },
      "minItems": 1
    },
    "test_results": {
      "type": "object",
      "required": ["command", "exit_code", "tests_passed", "tests_failed", "coverage_pct"],
      "properties": {
        "command": { "type": "string" },
        "exit_code": { "type": "integer" },
        "tests_passed": { "type": "integer", "minimum": 0 },
        "tests_failed": { "type": "integer", "minimum": 0 },
        "coverage_pct": { "type": "number", "minimum": 0.0, "maximum": 100.0 }
      }
    },
    "four_eyes_verified": { "type": "boolean", "enum": [true] }
  }
}
```

---

## 3. Controlled Retention Pathways & Directory Topology

To ensure strict evidence provenance and prevent unversioned or floating files, all PA 2.1 evidence artifacts MUST be stored in the following deterministic directory hierarchy under version control:

```
docs/campaign-evidence/
  └── <campaign-id>/
      ├── plan/
      │   ├── project-plan.json                   # Validates against campaign-project-plan-v1
      │   └── baseline-approval.json              # Formal sign-off record
      ├── manifests/
      │   ├── manifest-<task-id>-<commit>.json    # Validates against stage-evidence-manifest-v1
      │   └── stage-transitions.log               # Append-only state transitions
      ├── reviews/
      │   ├── review-actual-vs-plan-<milestone>.json
      │   └── variance-closure-evidence.json
      ├── metrics/
      │   ├── effort-variance-summary.json
      │   └── test-coverage-trends.json
      └── communications/
          ├── baseline-announcement.log
          └── delivery-receipts.json
```

### 3.1 Immutability Rules
1. **No In-Place Modification:** Evidence files written to `docs/campaign-evidence/<campaign-id>/` are append-only and cryptographically sealed.
2. **Supersession via Versioning:** If a stage or plan is revised, a new versioned file (`project-plan-v2.json` or `manifest-<task-id>-rev2.json`) must be created with explicit reference to the superseded file hash.
3. **No Phantom Artifacts:** Every file listed in `input_artifacts` or `output_artifacts` must exist at the specified path and match the recorded SHA-256 hash.

---

## 4. Negative Verification Checks & Validation Rules

The automated validation suite (`_src/tools/validate_pa21_evidence.py`) enforces the following negative checks prior to any milestone gate sign-off or integration merge:

| Rule ID | Check Name | Negative Trigger Condition | Enforcement Action |
| :--- | :--- | :--- | :--- |
| **NEG-PA21-01** | **Missing Stage Evidence Check** | Milestone marked complete in `TODO.md` or plan without corresponding signed `stage-evidence-manifest-v1` records for all prerequisite work packages. | Hard build/merge failure; integration blocked. |
| **NEG-PA21-02** | **Stale Evidence Check** | Manifest references a `git_commit` SHA or `input_artifact` hash that does not match the active integration baseline branch. | Rejection; requires re-execution and updated evidence. |
| **NEG-PA21-03** | **Cross-Process-Instance Leakage Check** | An evidence record from Campaign X is reused in Campaign Y without formal cross-campaign qualification and unique hash reassignment. | Hard failure; flagged as cross-instance pollution. |
| **NEG-PA21-04** | **Retrospective Fabrication Check** | Inverted timestamp monotonicity (e.g., test timestamp later than git commit, or review timestamp earlier than implementation start). | Hard rejection; flagged as unverified post-hoc fabrication. |
| **NEG-PA21-05** | **Four-Eyes Role Collusion Check** | `author == reviewer` or `author == integrator` on any stage manifest or milestone review. | Immediate verification failure; self-acceptance prohibited. |
| **NEG-PA21-06** | **Unrecorded Deviation Check** | Effort or schedule variance > 20% detected without a corresponding entry in `reviews/review-actual-vs-plan-*.json`. | Milestone gate blocked until corrective action is documented. |

---

## 5. Templates for PA 2.1 Reports & Records

### 5.1 Actual-Versus-Plan Milestone Gate Review Report Template

```markdown
# Milestone Review Report: [<Campaign-ID>] - [<Milestone-ID>]

- **Campaign:** `<campaign-id>`
- **Milestone:** `<milestone-id>` (`<milestone-title>`)
- **Review Date:** `YYYY-MM-DD`
- **Project Lead:** `@<agent-id>`
- **Integrator:** `@<agent-id>`
- **Baseline Git SHA:** `<commit-sha>`

## 1. Planned vs. Actual Performance Summary

| Work Package / Task ID | Planned Effort (min) | Actual Effort (min) | Variance (%) | Schedule Slippage (days) | Deliverable Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TASK-001` | 120 | 110 | -8.3% | 0 | PASS (REF: `<sha>`) |
| `TASK-002` | 180 | 230 | +27.8% | +1 | PASS (Deviation recorded) |

## 2. Deviation Analysis & Corrective Actions
- **Variance > 20% Items:** `TASK-002`
- **Root Cause:** Additional boundary test vectors required for SWE.4 compliance.
- **Impact Assessment:** Schedule contingency absorbed the 1-day variance; overall milestone delivery preserved.
- **Corrective Action ID:** `CA-<campaign>-001`
- **Action Owner:** `@<agent-id>`
- **Resolution Status:** CLOSED / VERIFIED

## 3. Four-Eyes Independence Verification
- Author & Reviewer Separation confirmed across all child work packages: [x] YES / [ ] NO
- Preflight integration validation clean (`git diff --check` PASS): [x] YES / [ ] NO

## 4. Milestone Gate Verdict
- **Verdict:** [APPROVED / CONDITIONAL / REJECTED]
- **Sign-Off Authority:** `@<project-lead>` (Date: `YYYY-MM-DD`)
```

### 5.2 Baseline Availability Announcement & Communication Journal Template

```markdown
# Project Management Baseline Communication Record: [<Campaign-ID>]

- **Baseline ID:** `BL-MAN3-<campaign-id>-<version>`
- **Release Date:** `YYYY-MM-DD`
- **Dispatched By:** `@<project-lead>`
- **Scope of Baselined Assets:**
  * Project Management Plan (`docs/pipeline/man3-project-management-plan.md`)
  * Resource Allocation Matrix (`docs/pipeline/man3-resource-allocations.md`)
  * Interface Communication Matrix (`docs/pipeline/man3-interface-communication-matrix.md`)
  * Actual-vs-Plan Review Mechanism (`docs/pipeline/man3-actual-vs-plan-review-mechanism.md`)
  * Process Performance Strategy (`docs/pipeline/process-performance-strategy.md`)

## Recipient Acknowledgement & Delivery Evidence

| Role | Target Agent | Mailbox Thread ID | Dispatch Timestamp | Ack Timestamp | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Software Architect | `@kira` | `thread-bl-man3-announcement` | `YYYY-MM-DDTHH:MM:SSZ` | `YYYY-MM-DDTHH:MM:SSZ` | ACKNOWLEDGED |
| Integrator | `@obrien` | `thread-bl-man3-announcement` | `YYYY-MM-DDTHH:MM:SSZ` | `YYYY-MM-DDTHH:MM:SSZ` | ACKNOWLEDGED |
| Software Engineer | `@julian` | `thread-bl-man3-announcement` | `YYYY-MM-DDTHH:MM:SSZ` | `YYYY-MM-DDTHH:MM:SSZ` | ACKNOWLEDGED |
| QA Manager | `@jake` | `thread-bl-man3-announcement` | `YYYY-MM-DDTHH:MM:SSZ` | `YYYY-MM-DDTHH:MM:SSZ` | ACKNOWLEDGED |
| Verification Engineer | `@nog` | `thread-bl-man3-announcement` | `YYYY-MM-DDTHH:MM:SSZ` | `YYYY-MM-DDTHH:MM:SSZ` | ACKNOWLEDGED |
| Safety & Compliance | `@worf` | `thread-bl-man3-announcement` | `YYYY-MM-DDTHH:MM:SSZ` | `YYYY-MM-DDTHH:MM:SSZ` | ACKNOWLEDGED |
```

---

## 6. MAN.3 Baselined Package Integration & Communication Protocol

### 6.1 Baselined Package Composition
The complete MAN.3 baseline package integrates the following normative assets:
1. `docs/pipeline/man3-project-management-plan.md` (PMP, Milestones, WBS, Entry/Exit criteria)
2. `docs/pipeline/man3-resource-needs.md` (Human, tooling, infrastructure resource estimation)
3. `docs/pipeline/man3-resource-allocations.md` (Named assignments, competence records, allocation quotas)
4. `docs/pipeline/man3-interface-communication-matrix.md` (Stakeholder communication channels, SLAs)
5. `docs/pipeline/man3-actual-vs-plan-review-mechanism.md` (Deviation tracking, escalation schemas)
6. `docs/pipeline/process-performance-strategy.md` (Measurable objectives, metrics, monitoring methods)
7. `docs/pipeline/man3-plan-schemas-validators-evidence-control.md` (This document: schemas, retention, negative checks)

### 6.2 Communication & Evidence Retention Procedure
Upon integration of this baselined package onto `main`:
1. The Project Lead dispatches a formal baseline announcement via `agent-inbox` to all active project roles.
2. Each role agent reads the announcement and returns a formal ACK with their verification acknowledgment.
3. The Project Lead records the delivery and ACK timestamps in `docs/campaign-evidence/<campaign-id>/communications/baseline-announcement.log`.
4. The Integrator verifies that all ACKs are present and unbroken before unlocking execution gates for subsequent engineering campaigns (`0012-09` and `0018-02`).
