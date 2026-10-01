# 0044-07: Role Catalog Review against Capability Model

## 1. Context and Objective
As part of Task `0044-07`, this document reviews the existing role catalog (`docs/pipeline/roles/`) against the new capability matching model (`0044-05`). The goal is to identify gaps and propose new roles at a workable granularity, allowing the orchestrator to assign specialized, token-efficient agents (especially those without execution needs) to specific tasks.

## 2. Capability Model Overview
The capability model (`agent-capability-descriptor@v1` and `task-requirement-profile@v1`) introduces:
- **Capability Classes:** `sandboxed-grunt`, `unprivileged`, `privileged`.
- **Execution Needs:** `none`, `runner`, `direct`.
- **Cognitive Demand:** `low`, `medium`, `high`, `critical`.

## 3. Analysis of Existing Roles
The current roles are: `architect`, `dispatcher`, `integrator`, `process-optimizer`, `programmer`, `project-lead`, `qa-manager`, `requirements-engineer`, `runner`, `security-engineer`, `tester`.

**Observations:**
- Most current roles imply active execution (`execution_needs=direct` or `runner`) to run validation, tests, or compilation.
- The `programmer` role covers all implementation, whether it's complex algorithmic logic (`direct`, `high` cognitive demand) or simple typo fixes/doc updates (`none`, `low` cognitive demand).
- Using a full `programmer` for simple text/documentation changes forces the use of agents with higher capability requirements, wasting token budgets and execution resources.
- `sandboxed-grunt` agents are constrained by the runner protocol if `execution_needs=runner` is used, but can operate highly efficiently if `execution_needs=none`.

## 4. Proposed New Roles

To optimize agent selection, we propose the following new roles:

### 4.1 Technical Writer (`technical-writer`)
- **Purpose:** Write, edit, or format documentation, requirements prose, or comments without executing code.
- **Capability Profile:** `sandboxed-grunt` or `unprivileged`; `execution_needs=none`; `cognitive_demand=low` to `medium`.
- **Benefit:** Allows lightweight, fast agents to process documentation tasks in parallel with code implementation, completely avoiding the runner protocol overhead.

### 4.2 Static Code Reviewer (`static-reviewer`)
- **Purpose:** Perform static analysis and peer review of code/documents without running tests or interacting with the environment.
- **Capability Profile:** `sandboxed-grunt` or `unprivileged`; `execution_needs=none`; `cognitive_demand=medium` to `high`.
- **Benefit:** Decouples the QA review process from execution requirements. Specialized large-context reasoning models can perform this without needing direct shell access.

### 4.3 Data Annotator / Curator (`data-curator`)
- **Purpose:** Process, label, or structure static data files (JSON, CSV) based on predefined rules.
- **Capability Profile:** `sandboxed-grunt`; `execution_needs=none`; `cognitive_demand=low`.
- **Benefit:** Ideal for batch tasks where a lightweight model edits files in bulk without execution.

## 5. Conclusion
Adding these granular roles allows the deterministic matcher (`capability_match.py`) to assign pure text-manipulation tasks to restricted (`sandboxed-grunt`), non-executing (`execution_needs: none`) agents. This fulfills the user's intent to save tokens and avoid unnecessary runner overhead for simple tasks.
