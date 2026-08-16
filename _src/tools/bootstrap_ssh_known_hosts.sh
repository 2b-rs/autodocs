#!/usr/bin/env bash
# bootstrap_ssh_known_hosts.sh
# Reusable: safely add GitHub's Ed25519 host key to known_hosts.
# Safe to run repeatedly; exits 0 if key is already present.
# No private key, no credential, no push, no commit.
set -euo pipefail

GITHUB_ED25519_FP='SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU'
KNOWN_HOSTS="${HOME}/.ssh/known_hosts"
mkdir -p "${HOME}/.ssh" && chmod 700 "${HOME}/.ssh"

if ssh-keygen -F github.com -l 2>/dev/null | grep -qF "$GITHUB_ED25519_FP"; then
  echo "OK: GitHub host key already present and fingerprint matches."
  exit 0
fi

echo "Adding GitHub Ed25519 host key..."
scanned=$(ssh-keyscan -t ed25519 github.com 2>/dev/null)
if [ -z "$scanned" ]; then
  echo "FAIL: ssh-keyscan returned nothing — check network access."; exit 1
fi
echo "$scanned" >> "$KNOWN_HOSTS"

# Verify the key we just added matches the known-good fingerprint
added_fp=$(ssh-keygen -lf <(echo "$scanned") | awk '{print $2}')
if [ "$added_fp" != "$GITHUB_ED25519_FP" ]; then
  echo "FAIL: fingerprint mismatch — expected $GITHUB_ED25519_FP got $added_fp"
  # Remove the untrusted entry we just appended
  grep -vF "$scanned" "$KNOWN_HOSTS" > "${KNOWN_HOSTS}.tmp" && mv "${KNOWN_HOSTS}.tmp" "$KNOWN_HOSTS"
  exit 1
fi

echo "VERIFIED: GitHub host key added — fingerprint $added_fp"
