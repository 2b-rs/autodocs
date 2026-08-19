# Architecture Approval Setup — Authorized Runner/Handle Procedure

## Purpose and authority boundary

This procedure prepares the external capabilities required by Task `0037-49`
and the later architecture decision in `0037-07`. It does not create an
approval.

Humans and registered authorities make and authenticate decisions, assign
roles, and provision externally controlled credentials/settings through their
native administration interfaces. They do not execute repository Git or shell
steps for this workflow. Sandboxed agents prepare bounded, parameterless
requests and never invoke them directly. The qualified less-restricted runner
performs every repository probe, signature operation, verification and
publication through named handles without exposing private material.

The authoritative approval namespace is:

```text
refs/autodocs/approvals/<decision-id>
```

Historical singular `refs/autodocs/approval/...` evidence is non-canonical and
must not be reused as plural-ref permission evidence.

## 1. Pin the exact package and policy

The runner records the architecture package commit, tree, package digest,
policy revision, authority registry, signer registry, schema and finding-log
digests. Any relevant change invalidates the candidate and requires a new
record.

The bootstrap verifier reads policy from the exact package/policy baseline. It
must never trust ambient Git configuration or an unbound working-tree file.

## 2. Confirm public identities and roles

`issues/_policy/authorities.json` records public fingerprints, role, independent
confirmation route, expiry/reconfirmation and revocation. The repository-owner
fingerprint is confirmed through `https://github.com/2b-rs.keys`. Additional
key/role assignments require an explicit current-user or registered-authority
record.

Required architecture-decision roles are process, security/privacy and release.
Independent-quality and translation-review use a separately assigned reviewer
credential and still require a fresh independent session for each review.
Implementation authors do not self-approve.

`issues/_policy/allowed_signers` contains public keys only. No private key,
private path, passphrase, token or credential value is stored in the repository,
request, result or log.

## 3. Provision named runner handles

Current qualified handles are documented in
`issues/_policy/credential-handles.json`:

- `autodocs-deploy-key`: Git authentication and publication to the canonical
  approval namespace;
- `agent-commit-key`: SSH signing in namespaces `git` and
  `autodocs-readiness` through a task-scoped agent.

The runner resolves private credentials outside the child sandbox, verifies
mode, symlink state and fixed public fingerprint, loads them into a task-scoped
`ssh-agent`, and exposes only `SSH_AUTH_SOCK` plus the exact public selector.
The agent is terminated and waited for after every run.

Two capabilities remain separate and must not be inferred from these SSH keys:

- a GitHub hosting-administration/API handle for the branch-policy operation
  later required by `0037-43`;
- a runner-visible service-control handle/action for exact
  supervisor/configuration/protocol-selector operations.

## 4. Qualify capabilities and negative paths

The retained Task `0037-49` evidence must prove:

1. exact deploy fingerprint, authenticated reads, canonical plural-ref dry-run
   negotiation and unchanged target;
2. exact signing fingerprint, real sign/verify operation, no private-path
   exposure and agent cleanup;
3. exact supervisor/runner source identities, selector, no-op deployment,
   health, crash/restart recovery, single request consumption and rollback;
4. executable rejection for reject, stale digest, wrong role, revoked signer,
   unavailable handle and deploy/signing/service failure.

Metadata presence or prose-only fixtures are insufficient. Task `0038-15`
productizes this evaluator before `0037-07` begins.

## 5. Construct and publish the readiness record

Only after every required capability is verified does a bounded runner action:

1. construct the canonical, digest-bound readiness record;
2. request the `agent-commit-key` signing operation;
3. verify the signature, role, namespace and current policy;
4. publish by expected-ref compare-and-swap through the deploy handle;
5. verify the remote ref and retain before/after identities.

A stale expected ref, existing immutable decision ref, signature mismatch,
revocation, unavailable handle, role mismatch, policy drift or service failure
must stop before mutation. A readiness record is not an architecture approval.
`0037-07` starts only after `0037-49` is complete and `0038-15` supplies the
qualified evaluator.

## Current Task 0037-49 state

Deploy, signing, owner/role registration and local service controls are
qualified. Architecture approval remains blocked until the hosting-admin/API
and runner-service-control handles above are provisioned, tested and included
in a zero-missing signed readiness record.
