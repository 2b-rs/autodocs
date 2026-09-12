# Backlog Classification and Migration Rules (0016-13)

**Status:** Normative
**Reference:** Feature `0016-13` (Prerequisites: `0012-02`, `0016-03`)

This document defines the normative classification semantics for `TODO.md` and `BACKLOG.md` items, ensuring strict separation between MAN.3 planned work packages, SUP.9 problems, and SUP.10 change requests, as required by ASPICE. It also retires competing ad-hoc backlog semantics to ensure a single source of truth.

## 1. Decommissioning of Competing Semantics

Prior to this specification, the repository contained unclassified TODOs scattered across various documents and formats (e.g., Markdown checkboxes, Jira exports, ad-hoc text files). 
**Rule 1:** The `TODO.md` file in the repository root is the singular, authoritative backlog for all project execution. All other active backlog formats or scattered TODO lists are hereby **RETIRED**.

## 2. Classification Schema

Every item in `TODO.md` MUST be explicitly classified according to the `0016-03` rules:

### 2.1 Managed Work Packages (MAN.3)
- **Type:** `feature` or `task`
- **Definition:** Planned project work derived from the Integrated Project Plan (`docs/pipeline/man3-project-management-plan.md`). Examples: Writing a specification, implementing a planned module, executing a planned test phase.
- **Format:** `- [ ] **<id>** (task, open) PREREQ: <deps> <description>...`
- **Handling:** These remain in `TODO.md` as standard execution items tracked by the Coordinator.

### 2.2 Problems (SUP.9)
- **Type:** `problem` (or `defect`)
- **Definition:** An identified non-conformance, defect, or unexpected behavior in an already baselined work product. Examples: A failing test in `main`, a crashed process, a documented memory leak.
- **Handling:** True problems MUST be migrated/tagged as SUP.9 records. In `TODO.md`, they must include the alias `[BUG-XXXX]` or `[SUP9-XXXX]` preserving the historical issue ID. They require Root Cause Analysis and Impact Analysis before implementation.

### 2.3 Change Requests (SUP.10)
- **Type:** `change`
- **Definition:** A stakeholder request to alter an already baselined requirement, architecture, or plan (where no defect exists). Examples: Changing an interface protocol, adding a new user configuration option, modifying a risk threshold.
- **Handling:** True changes MUST be migrated/tagged as SUP.10 records. In `TODO.md`, they must include the alias `[CR-XXXX]` or `[SUP10-XXXX]`. They require CCB Authorization and Impact Analysis before implementation.

## 3. Migration and Alias Preservation

When migrating legacy items into the formal `TODO.md` structure:
1. **Preserve Aliases:** Do not destroy original Jira, GitHub, or internal tracking IDs. Append them to the description (e.g., `REF: GH-123`).
2. **Preserve History:** Do not delete historical context. If an item is converted to a formal `problem`, link the original discussion artifact in the PREREQ or REF tag.
3. **Migrate Only True Problems/Changes:** Do not pollute SUP.9/10 with standard development tasks. If a developer thinks of a refactoring idea, it is a MAN.3 `task` (or skipped entirely), not a SUP.10 `change` unless it alters a baselined requirement.

## 4. Enforcement

The Integrator (`obrien`) and Dispatcher (`benjamin`) MUST reject any commit that adds an unclassified item to `TODO.md`. Valid types are strictly limited to: `(feature, ...)`, `(task, ...)`, `(problem, ...)`, `(change, ...)`.
