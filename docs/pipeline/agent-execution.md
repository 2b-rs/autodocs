# Agent Capability and Runner Protocol

Status: review-ready contract for Task `0037-45`.

## Capability classes

`SANDBOX.md`, `AGENTS.md`, and `PRIVILEGED.md` remain canonical human policy. Every agent defaults fail-safe to `sandboxed-grunt`: it may inspect declared inputs and prepare non-execution edits, but cannot directly execute processes, Git operations, network traffic, credential use, or authority-changing actions. `privileged` is explicit, policy-digested, and never inferred from a request.

## Request queue and lifecycle

Bootstrap uses a singleton root request only for discovery. After discovery, a versioned request queue uses request IDs, owner tokens, expected base and authority epoch, read/write scopes, leases, typed allowlisted actions, digest-bound preflight, resources, cleanup, idempotence, cancellation, structured progress/logs/results, and recovery. Conflicting scopes, stale base/epoch, unknown actions, missing dependencies/credential handles, and queue/lease races reject before mutation.

Allowed runner transactions are read-only discovery, focused validation, generation, external-service configuration, signing verification, path-limited substantive commit, and optional separate bookkeeping commit that injects a real prior `REF`. The legacy pending-discovery claim exception is allowed only before discovery; all later requests require runner-issued reservations. No step requires user or privileged-agent execution.

## Threat controls

- Fail closed on absent/unknown capability class, protocol version, base, epoch, scope, action, dependency, credential handle, or digest.
- Preserve result integrity with request binding, observed base/epoch, declared outputs, immutable result digest, and tamper rejection.
- Recover partial mutations only through a named recovery transaction; retries reuse an idempotence key and link `retry_of`.
- Reject overlapping writes and ensure a bookkeeping commit may reference only the actual substantive commit returned by the preceding runner result.
