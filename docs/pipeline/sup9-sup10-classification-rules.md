# SUP.9 Problem Resolution and SUP.10 Change Request Classification Rules (0016-03)

## 1. Scope & Purpose
- **Feature / Task**: `0016-03` (PREREQ: `0016-01`, `0016-02`)
- **Governing Standard**: Automotive SPICE (PAM 4.0 / PAM 3.1)
- **Objective**: Establish strict classification and linking boundaries between:
  1. `MAN.3` Work Packages & Process Improvements (Managed Project Plan).
  2. `SUP.9` Problem Resolution Records (Defects, Non-conformances, Unexpected Behaviors).
  3. `SUP.10` Change Requests (Requested modifications to baselines, requirements, or architecture).

---

## 2. Classification Decision Matrix

| Item Trigger / Nature | Classification | Lifecycle Model | Owning Process | Key Record Artifact |
|---|---|---|---|---|
| Planned development task or sprint milestone | `MAN.3` Work Package | Plan -> Dispatched -> In Progress -> Accepted | `MAN.3` | `man3-project-management-plan.md` / `TODO-*.md` |
| Process improvement proposal (internal enhancement) | `MAN.3` Improvement WP | Proposed -> Evaluated -> Integrated -> Reviewed | `MAN.3` | `man3-project-management-plan.md` |
| Test failure, unexpected crash, data corruption, or schema violation | `SUP.9` Problem Record | Logged -> Triaged -> Root Cause -> Fix -> Verified -> Closed | `SUP.9` | `_src/spec/problems/PRB-*.json` |
| Stakeholder request to alter requirements, API, or release scope | `SUP.10` Change Request | Initiated -> Impact Analysis -> Authorized -> Implemented -> Verified -> Closed | `SUP.10` | `_src/spec/changes/CR-*.json` |

---

## 3. Linking & Segregation Rules
- **No Conflation Rule**:
  - A `SUP.9` Problem Record is never created for planned feature work or routine tasks.
  - A `SUP.10` Change Request is never created solely to track a bug fix unless the fix necessitates a baseline/requirement change.
- **Traceability Links**:
  - When a `SUP.9` problem fix requires modifying a frozen baseline, a child `SUP.10` Change Request is generated and linked (`PRB-xxx` -> `CR-yyy`).
  - When a `SUP.10` change is authorized, implementation tasks are dispatched as `MAN.3` work packages referencing the Change Request ID.
