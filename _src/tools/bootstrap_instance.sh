#!/usr/bin/env bash
# bootstrap_instance.sh
# Declared purpose: bootstrap a fresh working instance of this project.
#
# What this does:
#   1. Verifies runtime prerequisites (git, python3, ssh, ssh-keygen)
#   2. Adds GitHub's host key via bootstrap_ssh_known_hosts.sh
#   3. Configures the authoritative remote (git@github.com:2b-rs/autodocs.git)
#   4. Probes the remote read-only (git ls-remote) to confirm access
#   5. Confirms the runner SSH key identity matches the registered reviewer fingerprint
#   6. Reports readiness for subsequent approval or runner steps
#
# What this does NOT do:
#   push, commit, sign, export credentials, write to .git/config beyond remote,
#   or execute any privileged or external-service mutation.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REMOTE_URL='git@github.com:2b-rs/autodocs.git'
RUNNER_KEY_PUB="${HOME}/devel/aradocs-runner-key/id_ed25519.pub"
EXPECTED_PUB='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMlRrxfZEXy4CbElR7MsHF0VZ6En4IRT/8+qemBb0Fdz tobias.anton@accenture.com'
EXPECTED_FP='SHA256:ciGUV68+0uuJGw+HsDQmur/ZO0INAtZbg5M0A+zydl4'

step() { printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"; }
pass() { printf '  PASS: %s\n' "$*"; }
fail() { printf '  FAIL: %s\n' "$*" >&2; exit 1; }

step "1. Prerequisites"
for cmd in git python3 ssh ssh-keygen; do
  command -v "$cmd" > /dev/null || fail "$cmd not found in PATH"
  pass "$cmd found at $(command -v $cmd)"
done

step "2. GitHub SSH host key"
bash "$SCRIPT_DIR/bootstrap_ssh_known_hosts.sh"

step "3. Configure remote"
cd "$REPO_ROOT"
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE_URL"
pass "remote origin set to $REMOTE_URL"

step "4. Probe remote read-only"
git ls-remote --heads origin > /dev/null
pass "git ls-remote succeeded — repository resolves"
git ls-remote --heads origin | awk '{print $2}'

step "5. Verify runner SSH key identity"
[ -f "$RUNNER_KEY_PUB" ] || fail "runner public key not found at $RUNNER_KEY_PUB"
actual_pub="$(cat $RUNNER_KEY_PUB)"
[ "$actual_pub" = "$EXPECTED_PUB" ] || fail "runner public key content mismatch"
actual_fp="$(ssh-keygen -lf "$RUNNER_KEY_PUB" | awk '{print $2}')"
[ "$actual_fp" = "$EXPECTED_FP" ] || fail "fingerprint mismatch — expected $EXPECTED_FP got $actual_fp"
pass "runner key matches reviewer identity: $actual_fp"

step "6. Bootstrap complete"
echo ""
echo "  Repository : $REMOTE_URL"
echo "  Reviewer   : tobias.anton@accenture.com"
echo "  Fingerprint: $EXPECTED_FP"
echo "  Role       : Architecture Review Board member"
echo ""
echo "  Ready for: approval-checklist step 3 (signer policy registration)"
echo "  NOT YET:   push, signing, credential use, or ref publication"
