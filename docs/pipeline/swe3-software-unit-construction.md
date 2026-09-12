# SWE.3 Software Unit Construction

## 1. Purpose and Scope

This document specifies the process and guidelines for constructing and generating ECU software units. It ensures that software construction strictly adheres to the **SWE.3 Software Detailed Design**, complies with defined coding principles (e.g., MISRA C/C++), and maintains bidirectional traceability from the detailed design to the constructed units and source code.

## 2. Construction Guidelines and Coding Principles

All software units, whether handwritten or model-generated, must comply with the following construction principles:

### 2.1 Handwritten Code
- **Language & Standard**: C (ISO 9899:1999) or C++ (ISO/IEC 14882:2014) as specified in the project configuration.
- **Coding Guidelines**: Strict adherence to MISRA C:2012 or MISRA C++:2008. Any deviation must be explicitly justified, formally reviewed, and documented in a deviation record.
- **Style**: Code must follow the project-specific formatting guide (e.g., indentation, naming conventions for variables, constants, and functions) enforced via automated linters (e.g., `clang-format`).
- **Complexity limits**: 
  - Cyclomatic Complexity <= 15 per function.
  - Max function length <= 100 lines of executable code.

### 2.2 Model-Generated Code
- **Tool Qualification**: Code generation tools (e.g., TargetLink, Embedded Coder) must be configured and qualified according to ISO 26262 Tool Confidence Level (TCL) requirements.
- **Model Constraints**: Models must adhere to MAAB (MathWorks Automotive Advisory Board) guidelines.
- **Preservation**: Generated code must not be manually modified ("no manual patching"). Any fix must occur at the model level, followed by regeneration.

## 3. Toolchain and Environment

- **Compiler**: Defined explicitly in the Software Configuration Management (SCM) baseline (e.g., GCC for ARM v9.3.0, Tasking VX-toolset).
- **Static Analysis Tools**: e.g., Polyspace, QAC, or SonarQube for enforcing MISRA rules and detecting structural defects.
- **Version Control**: All source code, models, and generation scripts must be versioned in the canonical repository, utilizing feature branches, strict merge-request gates, and immutable commits.

## 4. Code Review and Approvals

### 4.1 Process
- **Pre-Commit Checks**: Developers must run local static analysis and formatting checks before pushing.
- **Peer Review (4-Eyes Principle)**: Every merge request must be reviewed by at least one independent, qualified peer who did not author the code.
- **Review Criteria**:
  - Implementation matches the detailed design logic and constraints.
  - Bidirectional traceability links are present in source code (e.g., via specialized comments or pragmas) and the requirements management tool.
  - All static analysis warnings are resolved or formally waived.
  - Unit boundaries and interfaces are respected.
- **Approvals**: The independent reviewer must explicitly approve the Merge Request. The CI/CD pipeline must pass all automated build and static analysis gates before integration is permitted.

### 4.2 Findings and Corrections
- Findings identified during code review or static analysis must be logged in the issue tracking system.
- Corrections must trace back to the finding and undergo a subsequent review iteration.

## 5. Bidirectional Traceability

### 5.1 Design to Source Code
Each Software Detailed Design element must be traceable to the software unit(s) implementing it.
- **Methodology**: Source files and specific functions must include traceable tags (e.g., `@trace SWE3-DESIGN-REQ-1234`) mapped directly to the Requirements/Design management tool.

### 5.2 Source Code to Design
Each software unit (module, file, or function) must explicitly state which detailed design elements it fulfills.
- **Methodology**: Automated tooling will parse the traceability tags from the source code during the CI/CD pipeline to generate a bi-directional traceability matrix (RTM). Unmapped code or unfulfilled design elements will break the build.

## 6. Documentation and Metadata

For each constructed unit, the following must be retained:
- Source identity (Commit Hash, Branch Name).
- Tool identity (Compiler version, Static Analyzer version).
- Code review logs and approval records.
- Static analysis reports and deviation waivers.
