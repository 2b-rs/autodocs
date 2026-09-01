# Architect Scope Review: Delegated Escalation Pipeline

## 1. Exact affected work units/gates
- **Affected work units:** `repository:autodocs`
- **Affected gates:** `integration` (specifically the rejection/rework and escalation pathways).

## 2. Smallest safe text changes
- Update `docs/pipeline/integration-flow-control.md` to define the escalation ladder.
- Add text specifying that an Integrator must decide within the accepted contract and that findings route to actionable same-slot rework.
- Add text establishing the documented trilateral (Implementer/Integrator/Coordinator-or-Architect) round for unresolved technical disagreements.
- State clearly that only non-delegable product, policy, authority, material-risk, external-effect, or waiver questions reach Management.

## 3. Retained hygiene/independence/Acceptance/security/release controls
- **Hygiene/Independence:** The Integrator role remains completely independent from the Implementer. The four-eyes principle (TK-1) is strictly maintained.
- **Acceptance:** Trilateral resolution must document its outcome and preserve current Acceptance structures (a privileged agent must still record Acceptance).
- **Security/Release:** All existing credential boundaries, public release limits, and material risk gates remain exactly as configured. Management alone handles waivers.

## 4. Explicit exclusions
- This change does not authorize mutation of operative pipeline/authority files in this Architect step.
- This change does not authorize GUI integration or any GUI-based persistence changes.
- This change does not bypass canonical receipts or `main` source branch constraints.
- This change does not allocate a conflicting DEC-* ID.
