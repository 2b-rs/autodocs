# Requirement Candidate Inventory (0013-07)

## 1. Objective and Scope
This inventory classifies requirement-like statements currently scattered across the repository (e.g., TODOs, process documents, conventions, schemas, test assertions). It identifies duplicates, conflicts, design constraints masquerading as requirements, and imported domain content. 
**No migration into the formal `req-*` hierarchy is performed here; this is purely an analysis (Task 0013-07).**

## 2. Locations of Scattered Candidates
An automated scan for normative language (`SHALL`, `MUST`, `REQUIRED`) identified ~23,700 occurrences across the codebase. These instances are concentrated in the following artifacts:

| Source Type | Primary Files / Directories | Nature of Content |
|---|---|---|
| **Process & Governance Rules** | `AGENTS.md`, `branch-workflow.md`, `TODO.md` header | Pipeline rules, commit/merge constraints, memory governance, and task lifecycle definitions. |
| **Pipeline Scripts & Tooling** | `run.sh`, `agent-inbox` Python scripts | Implicit functional requirements for the mailbox, isolation boundaries, and signature validation. |
| **Task Definitions** | `TODO.md` (task descriptions) | Unstructured functional/process requirements mixed with acceptance criteria. |
| **Validation Schemas** | JSON/YAML schemas, CI workflows | Data integrity rules, artifact metadata bounds, and structural constraints. |
| **Tests & Assertions** | `tests/`, Pytest suites, `assert` statements | Exact dynamic behavior and boundary conditions masquerading as unit tests rather than formal requirements. |
| **Domain Content** | `docs/dossiers/`, `docs/pipeline/` | ASPICE compliance rules, evidence catalogues, and artifact definitions. |

## 3. Classification & Findings

### 3.1 Process Rules (Governance)
- **Examples**: "mutating work MUST happen in isolated worktrees", "agents SHALL NOT self-assign tasks".
- **Analysis**: These are organizational and pipeline constraints (MAN.3, SUP.8), not product software requirements (SWE.1). 
- **Conflict Risk**: High. Rules are often duplicated between `AGENTS.md`, `TODO.md` headers, and individual mailbox broadcasts (e.g., `DEC-0044-012`).

### 3.2 Design Statements vs. Requirements
- **Examples**: Hardcoded script paths in `run.sh`, exact JSON keys required in artifacts, or specific Python module imports.
- **Analysis**: Many "requirements" in tests and schemas dictate *how* the system is built (Architecture/SWE.2 or Detailed Design/SWE.3) rather than *what* it must do (SWE.1).
- **Action**: These must be filtered and pushed down to `feature-breakdown.md` or detailed design records, not the stakeholder/software requirement baseline.

### 3.3 Duplicates and Redundancy
- **Examples**: The definition of a "RenderedArtifact" appears in schema definitions, test files, and process documents like `configuration-item-catalogue.md`.
- **Analysis**: Scattered definitions lead to drift. A single source of truth is needed in the formal requirement hierarchy, with schemas/tests referencing the requirement ID.

### 3.4 Imported Domain Content
- **Examples**: ASPICE Base Practices (e.g., "The project SHALL define a lifecycle model...").
- **Analysis**: These are external compliance requirements. They are currently hardcoded directly into process definitions instead of tracing back to a formal external standard reference.

## 4. Preparation for Migration (`0013-10`)
Before migrating these candidates (Task `0013-10`), the following filters must be applied:
1. **Filter out Design**: Any statement specifying a technology choice, file format, or algorithm goes to Architecture (`0013-04`), not Requirements.
2. **Isolate Process vs. Product**: Differentiate `MAN`/`SUP` pipeline rules from `SWE` product features.
3. **Deduplicate**: Consolidate overlapping constraints into singular, testable statements.
4. **Establish Trace**: Map tests and schemas back to the new IDs rather than duplicating the normative text.
