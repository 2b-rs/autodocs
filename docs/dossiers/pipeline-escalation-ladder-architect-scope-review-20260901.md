# Architect Scope Review: Delegated Escalation Pipeline

## 1. Exact affected work units/gates
- **Affected work units:** `repository:autodocs`
- **Affected gates:** `integration:pipeline`, `validation:docs/pipeline/process-roles.md`, `validation:docs/pipeline/task-acceptance.md`

## 2. Smallest safe text changes
- **`docs/pipeline/integration-flow-control.md`**: Define the new escalation ladder (Integrator decision -> actionable same-slot rework -> trilateral round -> Management for non-delegable).
- **`AGENTS.md`**: Update the "integration verdict" rules to reflect that `[u]` hands resolution to actionable rework or a trilateral round before reaching Management, aligning with the new escalation ladder.
- **`docs/pipeline/process-roles.md`**: Update the `TK-2 dissent` resolution path so that technical dissent resolves via the trilateral round before escalating to Management.
- **`docs/pipeline/task-acceptance.md`**: Update the Feature rejection (`[u]` verdict) rules to integrate the new escalation ladder instead of immediately demanding explicit user (Management) interaction for delegable issues.
- **`docs/pipeline/decision-record.md`**: Clarify trigger interpretation to reflect the new boundaries for when an escalation triggers a Management review versus a trilateral round.
- **`PRIVILEGED.md`**: Checked for consistency; ensure no contradictory direct-to-user escalation pathways bypass the trilateral round.

## 3. Retained hygiene/independence/Acceptance/security/release controls
- **Hygiene/Independence:** The Integrator role remains completely independent from the Implementer. The four-eyes principle (TK-1) is strictly maintained.
- **Acceptance:** Trilateral resolution must document its outcome and preserve current Acceptance structures (a privileged agent must still record Acceptance).
- **Security/Release:** All existing credential boundaries, public release limits, and material risk gates remain exactly as configured. Management alone handles waivers.

## 4. Explicit exclusions
- This change does not authorize mutation of operative pipeline/authority files in this Architect step.
- This change does not authorize GUI integration or any GUI-based persistence changes.
- This change does not bypass canonical receipts or `main` source branch constraints.
- This change does not allocate a conflicting DEC-* ID.
