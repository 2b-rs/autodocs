# 0037-49 External Readiness Evidence

## Scope and boundary

This evidence package establishes only whether the externally controlled prerequisites for the issue-store architecture-approval bootstrap are present and independently verifiable. It neither requests nor records private credentials, performs signing, creates a review, changes hosting settings, publishes artifacts, deploys software, or restarts a service.

## Evidence basis

- Discovery request: `0037-49-readiness-discovery-20260816-1448`.
- Discovery base: `1e8e9cfcecbf450c849ed23a11774f44027442d8`.
- Policy basis: `docs/pipeline/issue-approval.md` requires exact-commit policy, `git verify-commit`, and independent repository-owner fingerprint confirmation.
- Local signer registry: `issues/_policy/allowed_signers` contains a review-ready placeholder only and names no verifiable principal or fingerprint.
- Local Git configuration identifies `tobias.anton <tobias.anton@users.noreply.github.com>`, but discovery found no configured remote or authenticated hosting-admin capability.

## Readiness matrix

| Prerequisite | Required independent proof | Local finding | Result |
| --- | --- | --- | --- |
| Approval authority | Named authorized reviewer and durable approval record on approved ref | No approval ref or authenticated reviewer-role record | BLOCKED |
| Commit signing | Public fingerprint registry plus valid `git verify-commit` chain | Placeholder signer registry; no fingerprint or signed approval ref | BLOCKED |
| Repository administration | Verified remote and repository-owner confirmation channel | No configured remote or verified owner channel | BLOCKED |
| Credential handle | Non-secret handle metadata, scope, expiry, revocation and audit route | No configured metadata or verifiable handle | BLOCKED |
| Hosting publication | Verified permission and bounded publication target | No remote/target/permission evidence | BLOCKED |
| Service controls | Verified health, restart and rollback endpoints plus operator authorization | No qualified endpoint or control interface | BLOCKED |

## Fixture verdicts

Fixtures are deterministic negative/control records. Each prohibits approval or external mutation when a prerequisite is missing, stale, wrong-role, unavailable, or digest-mismatched. The service-control fixture further proves that a no-op local probe cannot be confused with a deployment, restart, or rollback.

## Decision

`0037-49` cannot certify external readiness. Architecture approval remains forbidden until a human with the relevant external authority supplies independently verifiable approval, signing, hosting-administration, credential-handle, reviewer-role, and service-control evidence. The local package is complete only after the validator reports all fixture verdicts as expected.
