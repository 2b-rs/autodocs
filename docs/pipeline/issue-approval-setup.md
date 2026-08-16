# Architecture Approval Setup — Human Operator Guide

This document describes the one-time setup a human operator must complete to
satisfy `0037-49` and enable the architecture approval gate `0037-07`. It is
authoritative for the external-readiness prerequisites; the machine-readable
policy lives in `issues/_policy/` and `issues/_schema/`.

No sandboxed agent can perform any step in this document. Agents execute only
bounded runner requests; all signing, key provisioning, remote configuration,
and role assignment are human actions.

---

## Prerequisite: 0037-37 complete

`0037-37` must be `[p]` with a committed review package before these steps
matter. The review-package commit SHA is the value that gets signed.

```bash
git log --oneline -- docs/pipeline/issue-store-review-package.json | head -1
```

Record that SHA. It is `<PACKAGE_COMMIT>` throughout this document.

---

## Step 1 — Configure the git remote

```bash
cd /tmp/autodocs
git remote add origin git@github.com:<ORG>/<REPO>.git
git remote -v
```

Verify push access:

```bash
git ls-remote origin HEAD
```

This is required for publishing approval refs (`refs/autodocs/approval/...`)
and for `git verify-commit` to resolve signing trust via a known repository
identity.

---

## Step 2 — Provision your SSH signing key

If you do not already have an ed25519 key:

```bash
ssh-keygen -t ed25519 -C "tobias.anton@users.noreply.github.com" -f ~/.ssh/autodocs_signing
```

Obtain the fingerprint:

```bash
ssh-keygen -lf ~/.ssh/autodocs_signing.pub
# SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx tobias.anton@... (ED25519)
```

Record the fingerprint. Configure git to use it for signing:

```bash
git config --local gpg.format ssh
git config --local user.signingkey ~/.ssh/autodocs_signing.pub
git config --local commit.gpgsign true
```

Verify by making a test signed commit on a scratch branch and checking it:

```bash
git checkout -b scratch-signing-test
git commit --allow-empty -m "test: signing verification"
git verify-commit HEAD
git checkout -
git branch -D scratch-signing-test
```

`git verify-commit` must exit 0 before proceeding.

---

## Step 3 — Populate `issues/_policy/allowed_signers`

Replace the current placeholder. Each line covers one principal:

```
<email> namespaces="git" <keytype> <base64-pubkey>
```

Example (replace with real values):

```
tobias.anton@users.noreply.github.com namespaces="git" ssh-ed25519 AAAAC3Nza...
```

Add one line per signer role that will sign approval commits. At minimum you
need one entry for `repository-owner`. If the same key covers multiple roles
(acceptable for a solo project — see Step 4), one line suffices.

Verify git can use the file:

```bash
git config --local gpg.ssh.allowedSignersFile issues/_policy/allowed_signers
git verify-commit HEAD
```

Commit the updated file:

```bash
git add issues/_policy/allowed_signers
git commit -m "policy: populate allowed_signers with real fingerprints"
```

---

## Step 4 — Populate `issues/_policy/authorities.json`

Replace the skeleton with real principal records. For a solo project the same
person can hold all roles; `0037-07` only requires that implementation authors
do not self-approve, so if you are both the implementer and the sole authority
you must acknowledge that constraint explicitly in the `notes` field.

```json
{
  "schema": "issue-authorities@v1",
  "bootstrap_trust": "repository-owner fingerprint confirmation via recorded independent channel",
  "independent_channel": "https://github.com/<YOUR_USERNAME>.keys",
  "principals": [
    {
      "role": "repository-owner",
      "identity": "tobias.anton <tobias.anton@users.noreply.github.com>",
      "ssh_fingerprint": "SHA256:<FINGERPRINT>",
      "key_type": "ssh-ed25519",
      "public_key_ref": "issues/_policy/allowed_signers",
      "confirmed_via": "https://github.com/<YOUR_USERNAME>.keys",
      "expiry": null,
      "revocation_path": "Remove entry from issues/_policy/allowed_signers and commit"
    },
    {
      "role": "architecture-approver",
      "identity": "tobias.anton <tobias.anton@users.noreply.github.com>",
      "ssh_fingerprint": "SHA256:<FINGERPRINT>",
      "key_type": "ssh-ed25519",
      "public_key_ref": "issues/_policy/allowed_signers",
      "confirmed_via": "https://github.com/<YOUR_USERNAME>.keys",
      "expiry": null,
      "revocation_path": "Remove entry from issues/_policy/allowed_signers and commit",
      "notes": "Solo project: approver is also implementer. Self-approval constraint acknowledged: this approval ref must be made on a separate signing occasion distinct from any implementation commit."
    },
    {
      "role": "security",
      "identity": "tobias.anton <tobias.anton@users.noreply.github.com>",
      "ssh_fingerprint": "SHA256:<FINGERPRINT>",
      "key_type": "ssh-ed25519",
      "public_key_ref": "issues/_policy/allowed_signers",
      "confirmed_via": "https://github.com/<YOUR_USERNAME>.keys",
      "expiry": null,
      "revocation_path": "Remove entry from issues/_policy/allowed_signers and commit"
    },
    {
      "role": "privacy",
      "identity": "tobias.anton <tobias.anton@users.noreply.github.com>",
      "ssh_fingerprint": "SHA256:<FINGERPRINT>",
      "key_type": "ssh-ed25519",
      "public_key_ref": "issues/_policy/allowed_signers",
      "confirmed_via": "https://github.com/<YOUR_USERNAME>.keys",
      "expiry": null,
      "revocation_path": "Remove entry from issues/_policy/allowed_signers and commit"
    },
    {
      "role": "release",
      "identity": "tobias.anton <tobias.anton@users.noreply.github.com>",
      "ssh_fingerprint": "SHA256:<FINGERPRINT>",
      "key_type": "ssh-ed25519",
      "public_key_ref": "issues/_policy/allowed_signers",
      "confirmed_via": "https://github.com/<YOUR_USERNAME>.keys",
      "expiry": null,
      "revocation_path": "Remove entry from issues/_policy/allowed_signers and commit"
    }
  ]
}
```

Get your fingerprint:

```bash
ssh-keygen -lf ~/.ssh/autodocs_signing.pub
```

Commit when complete:

```bash
git add issues/_policy/authorities.json
git commit -m "policy: populate authorities.json with real principals"
```

---

## Step 5 — Provision the credential handle

The runner needs a narrowly scoped credential to push approval refs
(`refs/autodocs/approval/*`) without full repository write access.

Recommended: a GitHub deploy key scoped to this repository.

```bash
# Generate a dedicated deploy key (separate from your signing key)
ssh-keygen -t ed25519 -C "autodocs-runner-approval-push" \
    -f /Users/tobias.anton/devel/aradocs-runner-key/id_ed25519
ssh-keygen -lf /Users/tobias.anton/devel/aradocs-runner-key/id_ed25519.pub
```

Add the public key as a deploy key in the GitHub repository settings with
**write access**. Then record the handle metadata (never the secret) by
creating `issues/_policy/credential-handles.json`:

```json
{
  "schema": "credential-handles@v1",
  "handles": [
    {
      "handle_id": "autodocs-runner-approval-push",
      "scope": "push refs/autodocs/approval/* to origin",
      "key_path": "/Users/tobias.anton/devel/aradocs-runner-key/id_ed25519",
      "public_key_fingerprint": "SHA256:<FINGERPRINT>",
      "provisioned": "<DATE>",
      "expiry": null,
      "revocation_path": "Revoke deploy key in GitHub repository Settings > Deploy keys",
      "audit_route": "GitHub repository Settings > Deploy keys > last used"
    }
  ]
}
```

Verify push works:

```bash
GIT_SSH_COMMAND='ssh -i /Users/tobias.anton/devel/aradocs-runner-key/id_ed25519' \
    git push origin HEAD:refs/autodocs/approval/test-probe 2>&1
# then immediately delete it:
GIT_SSH_COMMAND='ssh -i /Users/tobias.anton/devel/aradocs-runner-key/id_ed25519' \
    git push origin :refs/autodocs/approval/test-probe
```

Commit the handle metadata file:

```bash
git add issues/_policy/credential-handles.json
git commit -m "policy: record runner credential handle metadata"
```

---

## Step 6 — Document runner service controls

Create `issues/_policy/runner-service.json` recording the runner service
identity and control paths:

```json
{
  "schema": "runner-service@v1",
  "repo_path": "/tmp/autodocs",
  "run_slot": "/tmp/autodocs/run.sh",
  "health_check": "ls /tmp/autodocs/run.sh 2>/dev/null && echo occupied || echo free",
  "restart_path": "The runner process watches for run.sh; killing and restarting the watcher restores the slot.",
  "rollback_path": "git reset --hard <known-good-ref> inside /tmp/autodocs after stopping the runner.",
  "operator": "tobias.anton",
  "notes": "Runner persists as long as the watcher process is alive. Slot is always released on exit (trap in run.sh)."
}
```

Commit:

```bash
git add issues/_policy/runner-service.json
git commit -m "policy: record runner service controls"
```

---

## Step 7 — Verify readiness with the helper script

Run the readiness manager script:

```bash
python3 _src/tools/manage_approval_readiness.py --check
```

All six prerequisite categories must report `OK` before proceeding to `0037-07`.

---

## Step 8 — Sign the architecture package (0037-07)

Once the readiness check passes, the runner will construct the exact
digest-bound approval record and request a signing operation. You sign a
commit on `refs/autodocs/approval/<package-commit>` using:

```bash
git commit -S -m "approval: architecture review package <PACKAGE_COMMIT>"
```

The bootstrap verifier (`_src/tools/verify_issue_approval_bootstrap.py`) then
confirms `git verify-commit`, checks the fingerprint against `allowed_signers`,
and validates the approval record against `issue-approval-v1.schema.json`.
