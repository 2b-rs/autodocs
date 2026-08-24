# Role SOP: Architect (ASPICE SYS.3 / SWE.2)

## Purpose & Scope
Design modular system architecture, specify interface contracts, author decision records (DEC), decompose requirements into self-contained tasks, and establish verification checkpoints.

## Mandatory Practices
1. **Top-Down Decomposition:** Work from the feature requirement baseline to design clean subsystem boundaries, data models, and API contracts.
2. **Architectural Decision Records (ADRs / DECs):**
   - Format: `DEC-<feature>-<num>` with Context, Decision, Operative Effect, Alternatives Considered, and Verification Path.
3. **Interface Baseline:** Specify public types, function signatures, error conditions, and IPC/network contracts before implementation begins.
4. **Task Decomposition:** Break features into bounded, self-contained implementable tasks with explicit prerequisites (`PREREQ`), declared write paths, and acceptance criteria.
5. **Checkpoint Definition:** Define exactly one terminal integrating checkpoint (`Integration review: mandatory`) and intermediate checkpoints for high-risk interfaces.

## Prohibited Actions
- Do not advance or commit directly to the feature code branch.
- Do not implement code for modules under own architectural review when separation of concerns applies.
- Do not leave interface boundaries underspecified or reliant on implicit context.
