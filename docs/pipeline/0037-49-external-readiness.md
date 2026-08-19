# 0037-49 External Readiness Evidence

## Scope and decision boundary

This package records the current, read-only readiness assessment for Task `0037-49`. It does not create an architecture approval, sign a commit, publish an approval ref, mutate hosting configuration, expose credentials, deploy or restart the runner, or claim that metadata presence proves capability.

**Current verdict (2026-08-19T02:05:24Z): `BLOCKED`.** Architecture approval remains forbidden. Local policy metadata is populated, but the required independently authenticated external capabilities and signed readiness record are not available.

## Pinned baseline

| Item | Exact identity |
|---|---|
| Architecture review-package commit | `927da0690a964249f7ca0b83719601b849be801f` |
| Review-package tree | `b7abdcc5b80e5a33b8a57400a4032a5b9b3622dd` |
| Review-package file SHA-256 | `bf98dffe33da51c29e8952e7cfe10e0bb172d1d50ddb191282ea5c3330909a5f` |
| Latest combined policy-file commit | `ef350b4fbfbb4ef40b91c3587890e62431f11be2` |
| Authorities SHA-256 | `147eb3e1d9d09f2a25e8697244dc5283fd5761269ba39282b5c9befa0a336cf4` |
| Allowed-signers SHA-256 | `7e194c8ff111d85b37d7ec9f49ea59e37e5316a69de0714e4ad5095fb951d82c` |
| Credential-handles SHA-256 | `470ed91225265dfd3b7d24117c7f3e6c1b28a4757c3d54959da7d5db3b3772a5` |
| Runner-service SHA-256 | `c46ec5c542c1fc5ed53f74a4035afd3a00110b2d58f2163989853986c6279f53` |
| Approval-schema SHA-256 | `bcf0bf7833d4a20e2ffe665dd46955962b19f61a5391025fa992d15786fa3671` |

The package commit and completion-evidence commit are reachable but did not pass `git verify-commit`. The later policy commit `ef350b4f...` did pass with ED25519 fingerprint `SHA256:YWg/nPlBol+BkcbC/S0yIDBaw7xpKmfSjreQM8rgDjU`. This does not constitute package approval.

## Current capability probes

| Requirement | Probe/result | Verdict |
|---|---|---|
| Repository identity and read access | `origin` is `git@github.com:2b-rs/autodocs.git`, but `git ls-remote --heads origin` failed with `Permission denied (publickey)` | `BLOCKED` |
| Approval-ref publication | No `refs/autodocs/approval/*` refs exist; no expected-ref CAS publication was attempted | `BLOCKED` |
| Independent owner confirmation | Current user identified GitHub username `2b-rs`; `https://github.com/2b-rs.keys` returned the registered owner key with matching fingerprint `SHA256:ciGUV68+0uuJGw+HsDQmur/ZO0INAtZbg5M0A+zydl4` | `OWNER VERIFIED`; non-owner role/key bindings remain `BLOCKED` |
| Required roles | Candidate policy assigns `process` to the confirmed `agent-commit-key` and assigns `independent-quality` plus `translation-review` to qualified credential `agent-qa`; actual future independent reviewer-session assignment/availability is still recorded at review time | `ROLE POLICY PREPARED` |
| Signing operation | Canonical local config can verify the signed policy commit; the isolated worker clone does not inherit `gpg.format`, `user.signingkey`, or `gpg.ssh.allowedSignersFile`; no approved runner-visible signing operation was exercised | `BLOCKED` |
| Credential handles | One deploy-key metadata entry exists, but runner visibility/use is unproven and it does not establish hosting-policy, runner-supervisor/configuration or protocol-selector authority | `BLOCKED` |
| Runner service | Metadata names manual health/restart/rollback commands, but the configured `pgrep` health probe found no running process; persistence, restart, rollback, service-config authority and protocol switching remain unqualified | `BLOCKED` |
| Signed readiness record | No independently authenticated, digest-bound signed readiness report exists | `BLOCKED` |

## Repository-owner deployment-key attestation

On 2026-08-19 the current user stated verbatim:

> Runner können via ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAKQmbt0mV7MHbXdDOKo761E9ilS6ktKAJsZGnwDK9Vs autodocs-deploy-key publizieren.

The supplied public key is byte-identical to the key in `issues/_policy/credential-handles.json`. `ssh-keygen -lf` yields fingerprint `SHA256:wtCFvdCIurWZj2NT4deL9Rg9uwqsL5nj17jlaoTW7a0`, matching the registered credential-handle metadata.

This is authoritative repository-owner attestation that the runner publication credential exists and is intended for this repository. It resolves the public-key identity/registration question. It does not expose private material. Task completion still requires a bounded runner-side authentication/permission probe using the handle and retained result; the canonical agent's default SSH identity failing `ls-remote` is not evidence that the separately handled deploy key fails.

## Independent repository-owner fingerprint verification

On 2026-08-19 the current user identified the GitHub username as `2b-rs`. A read-only fetch of `https://github.com/2b-rs.keys` returned:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMlRrxfZEXy4CbElR7MsHF0VZ6En4IRT/8+qemBb0Fdz
```

`ssh-keygen -lf` yields `SHA256:ciGUV68+0uuJGw+HsDQmur/ZO0INAtZbg5M0A+zydl4`, exactly matching the registered `repository-owner` fingerprint and manual operator key in `allowed_signers`. The independent-channel blocker is therefore resolved for the repository-owner identity, and the correct candidate policy URL is `https://github.com/2b-rs.keys`.

The endpoint does **not** expose the separately registered agent/architecture key `SHA256:YWg/nPlBol+BkcbC/S0yIDBaw7xpKmfSjreQM8rgDjU`. It therefore cannot authenticate the current `confirmed_via` claims for architecture-approver, security, privacy and release roles. Those role/key bindings still require a valid independent channel or an explicit policy decision assigning the independently verified owner key to those roles.

## Current-user confirmation of the agent signing key

After being shown the configured signing-key path and fingerprint, the current user stated verbatim:

> das ist der richtige Key.

This is recorded as current-user confirmation that `SHA256:YWg/nPlBol+BkcbC/S0yIDBaw7xpKmfSjreQM8rgDjU` is the correct agent/architecture signing key. The key already verified signed policy commit `ef350b4fbfbb4ef40b91c3587890e62431f11be2` against `allowed_signers`.

This resolves the key-identity question. It does not by itself assign every required process/review role to that key, establish reviewer independence, or authorize architecture approval. Those role assignments and the later exact approval decision remain separate authority records.

## Independent QA and translation-review credential candidate

At the current user's explicit request, a new ED25519 signing credential named `agent-qa` was generated under `~/devel/identities/agent-qa`:

```text
public key:  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFxs6cut47w2Km6mFmwDxwAnJe4Jd+y9E1a2yDzWx5Ux agent-qa
fingerprint: SHA256:EKkZT+UDK8tIlIx1pVpxJtM+xDNcu0kKNfLpVAbPtxs
principal:   agent-qa@autodocs.invalid
```

The private key was not printed or persisted in the repository. Host permissions are mode `0700` on the directory, `0600` on the private key and `0644` on the public key.

The isolated policy candidate assigns this credential to exactly `independent-quality` and `translation-review`. Candidate digests are:

- `issues/_policy/authorities.json`: `sha256:c2e4a21954a72a10333e0f98d762c5bf5b0d7c1a6c1bd93111c418a8a24ab8ac`
- `issues/_policy/allowed_signers`: `sha256:6040f488288328769e8ffca006e673586b914bb87eb2fa1a9aad43184a1b7df6`

A hermetic `ssh-keygen -Y sign`/`verify` qualification passed with namespace `git`, the candidate `allowed_signers`, principal `agent-qa@autodocs.invalid` and the exact fingerprint above.

Role independence is procedural as well as cryptographic: this `0037-49` implementation session is prohibited from using `agent-qa` to review or accept its own work. A fresh, explicitly assigned reviewer session that did not implement or decisively author the reviewed scope must perform each independent review. The candidate is not active policy until reviewed and published through the Task branch.

## Process-role assignment

At the current user's explicit direction, candidate policy assigns role `process` to the confirmed `agent-commit-key`, fingerprint `SHA256:YWg/nPlBol+BkcbC/S0yIDBaw7xpKmfSjreQM8rgDjU`. The independent credential `agent-qa` remains restricted to `independent-quality` and `translation-review`. This preserves separation between process authority and independent review credentials.

## Helper/tool assessment

`python3 _src/tools/manage_approval_readiness.py --check --json` returned `all_ok: true` in the canonical checkout. That result is **metadata readiness only** and is not the Task verdict:

- the remote check verifies only that an `origin` URL is present, not authentication or repository/ref permissions;
- the signing check verifies local configuration and key-path existence, not a signing operation, policy-fingerprint match, clean-clone availability or approval signature;
- the role list omits process, independent-quality and translation-review roles;
- a non-empty independent-channel URL passes without fetching or authenticating it;
- the credential check does not prove runner visibility or usable scope and checks a different fingerprint field name from the current record;
- runner-service strings pass even when the process is absent;
- the seven retained fixtures assert expected labels but execute no signature, remote, role, revocation, credential, service or rollback behavior.

These tool/fixture gaps belong to Task `0038-15`, which productizes the readiness check and is a direct prerequisite of approval Task `0037-07`. They are retained here so a green metadata check cannot be mistaken for external readiness.

## Historical discovery

The 2026-08-16 discovery correctly reported that the then-current policy was placeholder-only and no remote, signer registry, credential metadata or service-control metadata was available. Later commits populated those files. That historical result is retained, but it is not the current assessment.

## Criterion disposition and next action

Local discovery, policy pinning, digest capture, negative fixture inventory and read-only capability probes are complete. Task `0037-49` is `[p]`: the runner-side handle resolver is implemented and awaiting runner-private registry provisioning plus the independently authenticated operations below:

1. provide a working, narrowly scoped remote credential handle and prove repository plus approval-ref permissions without exposing key material;
2. register and independently confirm every required role, including process, independent-quality and translation-review, with current reviewer availability;
3. replace or correct the 404 owner-confirmation channel and retain its authenticated fingerprint result;
4. qualify a runner-visible signing operation and the runner-service health/restart/rollback/configuration/protocol controls;
5. after `0038-15` supplies a non-false-positive evaluator, construct, sign, verify and expected-ref-CAS-publish the exact digest-bound readiness record.

Until all five actions succeed, `0037-07` must not begin and no architecture approval may be inferred.


## Runner-private deploy credential contract

`_src/run-loop.sh` resolves the allowlisted handle `autodocs-deploy-key` from the runner-private registry `${RUNNER_CREDENTIAL_DIR:-$HOME/.config/autodocs/credentials}/autodocs-deploy-key`. The registry is outside the repository and outside the `/tmp` work order. The runner verifies the fixed public fingerprint `SHA256:wtCFvdCIurWZj2NT4deL9Rg9uwqsL5nj17jlaoTW7a0` before execution, loads the private key into a task-scoped SSH agent outside the sandbox, exposes only `SSH_AUTH_SOCK` plus a public selector to the work order, and destroys the agent after every run. Unknown, unavailable and wrong-fingerprint handles fail before network access; logs identify only the handle and never the private path or key material.

The mode is selected by setting `GITHUB_SSH_CREDENTIAL_HANDLE=autodocs-deploy-key` on the runner process. Provisioning the private registry entry remains an operator-controlled external action and is not performed by repository code.
