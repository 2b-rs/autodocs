# Agent Bootstrap, Authority Discovery, and Instruction Cutover

Status: review-ready contract for Task `0037-41`.

## Canonical bootstrap

Agents read `SANDBOX.md`, `AGENTS.md`, and `PRIVILEGED.md` as canonical human policy, then read root `agent-workflow.json` as the canonical machine selector. The selector is schema-validated and digest-bound before any mutation. It declares workflow version, capability class, approved runner protocol, authority epoch/profile, write phase, and one bundle path. Missing, corrupt, unsupported, or digest-mismatched selectors fail closed.

## Precedence and stale clients

The selector controls authority and mutation permissions; its named instruction bundle controls task procedure; human policy controls capability limits; a runner result controls only its own declared transaction. Conflicts resolve toward less privilege and no mutation. A stale client that observes an unexpected base, selector digest, protocol version, authority epoch, or instruction bundle must stop mutation, reread `agent-workflow.json` and the named bundle, then run `issuectl bootstrap --refresh`.

## Profiles and cutover

`legacy-lists` uses the legacy bundle during `legacy-writable`, freezes all issue writes for `legacy-frozen`, and restores only through the matching `legacy-restored` bundle. `issue-store` permits canonical item writes only at `issue-store-writable`; `issue-store-write-frozen` permits provenance-only controls. The cutover transaction atomically changes selector epoch, profile, phase, digest, and bundle. Partial bundle changes and direct legacy writes after issue-store selection are rejected.

## Recovery table

| Failure | Required behavior | Exact recovery command |
|---|---|---|
| Missing/corrupt selector | Stop mutation | `issuectl bootstrap --refresh` |
| Unsupported workflow/runner version | Stop mutation | `issuectl bootstrap --refresh` |
| Stale base/epoch/bundle | Stop mutation, reread selector/bundle | `issuectl bootstrap --refresh` |
| Conflicting policy/instruction | Apply least privilege, stop mutation | `issuectl bootstrap --refresh` |
| Direct legacy write after cutover | Reject and preserve finding | `issuectl bootstrap --refresh` |
| Partial switch or rollback mismatch | Reject and preserve control evidence | `issuectl bootstrap --refresh` |
