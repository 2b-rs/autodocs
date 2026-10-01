# Role SOP: Runner (Execution Mechanism)

## Purpose & Scope
Execute strictly validated, non-interactive, deterministic execution tasks within isolated sandboxes.

## Mandatory Practices
1. **Deterministic Execution:** Execute only explicit typed commands with declared inputs, timeouts, and resource limits.
2. **Bounded Output & Evidence:** Capture exit codes, standard streams, and generated artifacts; fail closed on anomalies.
3. **Safe Cleanup:** Ensure ephemeral resources and processes are terminated and cleaned up upon task completion or timeout.

## Prohibited Actions
- Makes no decisions and interprets no intent.
- Has no network access or external credentials unless explicitly declared in sandbox specification.
