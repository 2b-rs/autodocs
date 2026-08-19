# 0037 Architecture Approval — Administrator Handoff

## Reviewer decision

- **Decision:** Approve.
- **Role:** Architecture Review Board member.
- **Public SSH fingerprint:** `SHA256:ciGUV68+0uuJGw+HsDQmur/ZO0INAtZbg5M0A+zydl4`.
- **Exact package commit:** `e3a176aeb8e10a0d08a977e08db1aaec6d69cb4f`.
- **Exact package digest:** `sha256:bf98dffe33da51c29e8952e7cfe10e0bb172d1d50ddb191282ea5c3330909a5f`.
- **Proposed approval ref:** `refs/autodocs/approvals/0037-architecture`.

## Administrator checklist

1. Confirm the authoritative repository remote and repository-owner identity through the independent organizational channel. Record the confirmation location and date in the approved external administration record; do not place credentials in Git.
2. Confirm that the reviewer identity and the public fingerprint above belong to an authorized Architecture Review Board member through that same independent channel.
3. Register the principal, role, and public fingerprint in the authoritative public signer policy, with no private key material.
4. Confirm an auditable credential handle for the qualified runner: publication scope limited to the approval ref; defined expiry, revocation, and audit route.
5. Confirm the runner-service operational authority: named endpoint, health check, restart, protocol-switch, and tested rollback route, with authorized operator.
6. Generate the final digest-bound approval record from the draft. Remove draft-only fields, retain exactly the schema fields, and set `signature_verified` to `true` only after successful independent verification.
7. Sign the approval commit through the approved non-exportable signing service/key operation. Do not export or transmit private material.
8. Verify the signed commit with `git verify-commit`; confirm record commit/digest/ref exactly match the review package.
9. Publish using expected-ref compare-and-swap to the approved ref. Verify the published ref resolves to the signed approval commit.
10. Retain the external evidence and report either success or the precise blocking control. Do not begin implementation merely because this unsigned draft exists.

## Required success evidence

- Independent owner and reviewer-role confirmation.
- Public signer-policy entry for the verified fingerprint.
- Signed approval commit and successful `git verify-commit` output.
- Published `refs/autodocs/approvals/0037-architecture` pointing to that commit.
- Verified credential-handle metadata and runner-service control authorization.

## Stop conditions

Stop and report a blocker if the repository identity, reviewer role, fingerprint, signature, package digest, approval ref, credential handle, or service-control authority cannot be independently verified.
