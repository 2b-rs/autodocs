#!/usr/bin/env python3
"""manage_approval_readiness.py

Human-operator tool for managing and verifying the external-readiness
prerequisites of 0037-49 before the architecture approval gate (0037-07)
can open.

Usage:
    python3 manage_approval_readiness.py --check
        Run all six readiness checks and report status.

    python3 manage_approval_readiness.py --check --json
        Same, but output machine-readable JSON.

    python3 manage_approval_readiness.py --fingerprint PATH
        Print the SSH fingerprint of the key at PATH.

    python3 manage_approval_readiness.py --patch-authorities
        Read the current fingerprint from the configured signing key
        and patch all <FINGERPRINT> placeholders in authorities.json.

    python3 manage_approval_readiness.py --show-package-commit
        Print the commit SHA of the latest review-package file, for
        use as <PACKAGE_COMMIT> when writing the approval record.

All operations are read-only except --patch-authorities (which edits
issues/_policy/authorities.json in place).

This script uses stdlib only. Python 3.8+.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (all relative to repo root)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
POLICY    = REPO_ROOT / "issues" / "_policy"
SCHEMA    = REPO_ROOT / "issues" / "_schema"

AUTHORITIES_JSON       = POLICY / "authorities.json"
ALLOWED_SIGNERS        = POLICY / "allowed_signers"
CREDENTIAL_HANDLES     = POLICY / "credential-handles.json"
RUNNER_SERVICE         = POLICY / "runner-service.json"
APPROVAL_SCHEMA        = SCHEMA / "issue-approval-v1.schema.json"
PKG_REVIEW             = REPO_ROOT / "docs" / "pipeline" / "issue-store-review-package.json"

REQUIRED_ROLES = [
    "repository-owner",
    "architecture-approver",
    "security",
    "privacy",
    "release",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _git(*args, check=True):
    return subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def _ssh_fingerprint(key_path: str) -> str:
    """Return SHA256 fingerprint of an SSH public key file."""
    r = subprocess.run(
        ["ssh-keygen", "-lf", key_path],
        capture_output=True, text=True, check=False,
    )
    if r.returncode != 0:
        return f"ERROR: {r.stderr.strip()}"
    # format: "256 SHA256:xxx comment (ED25519)"
    parts = r.stdout.strip().split()
    return parts[1] if len(parts) >= 2 else r.stdout.strip()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return f"sha256:{h.hexdigest()}"


def _check(label: str, ok: bool, detail: str = "") -> dict:
    status = "OK" if ok else "BLOCKED"
    line = f"  [{status:7}] {label}"
    if detail:
        line += f"\n           {detail}"
    return {"label": label, "status": status, "detail": detail, "_line": line}


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def check_remote() -> dict:
    """Check 1: git remote 'origin' is configured."""
    r = _git("remote", "get-url", "origin", check=False)
    ok = r.returncode == 0 and r.stdout.strip() != ""
    detail = r.stdout.strip() if ok else "No remote 'origin'. Run: git remote add origin git@github.com:<ORG>/<REPO>.git"
    return _check("Repository remote (origin)", ok, detail)


def check_signing_key() -> dict:
    """Check 2: git is configured with an SSH signing key and allowed_signers."""
    issues = []
    # gpg.format
    r = _git("config", "--local", "gpg.format", check=False)
    if r.returncode != 0 or r.stdout.strip() != "ssh":
        issues.append("gpg.format != ssh. Run: git config --local gpg.format ssh")
    # user.signingkey
    r = _git("config", "--local", "user.signingkey", check=False)
    keypath = r.stdout.strip()
    if not keypath:
        issues.append("user.signingkey not set. Run: git config --local user.signingkey ~/.ssh/<KEY>.pub")
    elif not Path(os.path.expanduser(keypath)).exists():
        issues.append(f"user.signingkey path does not exist: {keypath}")
    # gpg.ssh.allowedSignersFile
    r = _git("config", "--local", "gpg.ssh.allowedSignersFile", check=False)
    asf = r.stdout.strip()
    if not asf:
        issues.append("gpg.ssh.allowedSignersFile not set. Run: git config --local gpg.ssh.allowedSignersFile issues/_policy/allowed_signers")
    ok = len(issues) == 0
    return _check("Git SSH signing key configuration", ok, " | ".join(issues) if issues else f"key: {keypath}")


def check_allowed_signers() -> dict:
    """Check 3: allowed_signers has at least one real entry (not just a placeholder)."""
    if not ALLOWED_SIGNERS.exists():
        return _check("allowed_signers populated", False, f"File missing: {ALLOWED_SIGNERS}")
    real_entries = []
    for line in ALLOWED_SIGNERS.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # A real entry has three whitespace-separated fields (principal, options, keydata)
        parts = line.split()
        if len(parts) >= 3 and not "placeholder" in line.lower():
            real_entries.append(parts[0])
    ok = len(real_entries) > 0
    detail = f"Principals: {real_entries}" if ok else "Only placeholder entries found. Add real fingerprints (see issue-approval-setup.md Step 3)."
    return _check("allowed_signers populated", ok, detail)


def check_authorities() -> dict:
    """Check 4: authorities.json has real fingerprints for all required roles."""
    if not AUTHORITIES_JSON.exists():
        return _check("authorities.json complete", False, f"File missing: {AUTHORITIES_JSON}")
    try:
        data = json.loads(AUTHORITIES_JSON.read_text())
    except json.JSONDecodeError as e:
        return _check("authorities.json complete", False, f"JSON parse error: {e}")

    principals = data.get("principals", [])
    if not principals:
        return _check("authorities.json complete", False,
            "No 'principals' array. File still contains skeleton. See issue-approval-setup.md Step 4.")

    issues = []
    roles_found = {p["role"] for p in principals if isinstance(p, dict)}
    for role in REQUIRED_ROLES:
        if role not in roles_found:
            issues.append(f"missing role: {role}")
    # Check for placeholder fingerprints
    for p in principals:
        if isinstance(p, dict):
            fp = p.get("ssh_fingerprint", "")
            if "<FINGERPRINT>" in fp or not fp:
                issues.append(f"placeholder fingerprint in role '{p.get('role', '?')}'. Run --patch-authorities.")
    # Check independent_channel
    if not data.get("independent_channel"):
        issues.append("'independent_channel' not set in authorities.json")

    ok = len(issues) == 0
    return _check("authorities.json complete", ok,
        " | ".join(issues) if issues else f"Roles OK: {sorted(roles_found)}")


def check_credential_handle() -> dict:
    """Check 5: credential handle metadata file exists and is not a placeholder."""
    if not CREDENTIAL_HANDLES.exists():
        return _check("Credential handle", False,
            f"File missing: {CREDENTIAL_HANDLES}. See issue-approval-setup.md Step 5.")
    try:
        data = json.loads(CREDENTIAL_HANDLES.read_text())
    except json.JSONDecodeError as e:
        return _check("Credential handle", False, f"JSON parse error: {e}")
    handles = data.get("handles", [])
    issues = []
    for h in handles:
        if "<FINGERPRINT>" in h.get("public_key_fingerprint", ""):
            issues.append(f"Placeholder fingerprint in handle '{h.get('handle_id', '?')}'")
        if not h.get("scope"):
            issues.append(f"No scope in handle '{h.get('handle_id', '?')}'")
    ok = len(handles) > 0 and len(issues) == 0
    return _check("Credential handle", ok,
        " | ".join(issues) if issues else f"Handles: {[h.get('handle_id') for h in handles]}")


def check_runner_service() -> dict:
    """Check 6: runner service controls documented."""
    if not RUNNER_SERVICE.exists():
        return _check("Runner service controls", False,
            f"File missing: {RUNNER_SERVICE}. See issue-approval-setup.md Step 6.")
    try:
        data = json.loads(RUNNER_SERVICE.read_text())
    except json.JSONDecodeError as e:
        return _check("Runner service controls", False, f"JSON parse error: {e}")
    issues = []
    for field in ["health_check", "restart_path", "rollback_path", "operator"]:
        if not data.get(field):
            issues.append(f"'{field}' not set")
    ok = len(issues) == 0
    return _check("Runner service controls", ok,
        " | ".join(issues) if issues else f"Operator: {data.get('operator')}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_check(as_json: bool) -> int:
    results = [
        check_remote(),
        check_signing_key(),
        check_allowed_signers(),
        check_authorities(),
        check_credential_handle(),
        check_runner_service(),
    ]
    all_ok = all(r["status"] == "OK" for r in results)

    if as_json:
        out = {
            "all_ok": all_ok,
            "checks": [{k: v for k, v in r.items() if k != "_line"} for r in results],
        }
        print(json.dumps(out, indent=2))
    else:
        print("=" * 60)
        print(" Approval Readiness Check (0037-49)")
        print("=" * 60)
        for r in results:
            print(r["_line"])
        print("=" * 60)
        if all_ok:
            print(" RESULT: ALL OK — ready for 0037-07 approval gate.")
        else:
            blocked = sum(1 for r in results if r["status"] == "BLOCKED")
            print(f" RESULT: {blocked} BLOCKED — complete items above before proceeding.")
            print(" See: docs/pipeline/issue-approval-setup.md")
        print("=" * 60)

    return 0 if all_ok else 1


def cmd_fingerprint(path: str) -> int:
    fp = _ssh_fingerprint(os.path.expanduser(path))
    print(fp)
    return 0 if not fp.startswith("ERROR") else 1


def cmd_patch_authorities() -> int:
    """Patch <FINGERPRINT> placeholders in authorities.json with the actual fingerprint."""
    # Resolve signing key
    r = _git("config", "--local", "user.signingkey", check=False)
    keypath = r.stdout.strip()
    if not keypath:
        print("ERROR: user.signingkey not configured. Run git config --local user.signingkey <path> first.", file=sys.stderr)
        return 1
    keypath = os.path.expanduser(keypath)
    if not Path(keypath).exists():
        print(f"ERROR: signing key not found: {keypath}", file=sys.stderr)
        return 1
    fp = _ssh_fingerprint(keypath)
    if fp.startswith("ERROR"):
        print(f"ERROR getting fingerprint: {fp}", file=sys.stderr)
        return 1
    print(f"Fingerprint: {fp}")
    if not AUTHORITIES_JSON.exists():
        print(f"ERROR: {AUTHORITIES_JSON} not found", file=sys.stderr)
        return 1
    text = AUTHORITIES_JSON.read_text()
    patched, count = re.subn(r"SHA256:<FINGERPRINT>", fp, text)
    if count == 0:
        print("No <FINGERPRINT> placeholders found. Nothing to patch.")
        return 0
    AUTHORITIES_JSON.write_text(patched)
    print(f"Patched {count} placeholder(s) in {AUTHORITIES_JSON}")
    print("Review the file, then: git add issues/_policy/authorities.json && git commit -m 'policy: populate authorities.json fingerprints'")
    return 0


def cmd_show_package_commit() -> int:
    r = _git("log", "--format=%H", "-1", "--",
             str(REPO_ROOT / "docs" / "pipeline" / "issue-store-review-package.json"),
             check=False)
    sha = r.stdout.strip()
    if not sha:
        print("ERROR: no commit found for issue-store-review-package.json", file=sys.stderr)
        return 1
    print(sha)
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manage 0037-49 approval readiness prerequisites.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--check", action="store_true",
        help="Run all six readiness checks and report status.")
    parser.add_argument("--json", action="store_true",
        help="Output check results as JSON (use with --check).")
    parser.add_argument("--fingerprint", metavar="PATH",
        help="Print the SSH fingerprint of the key at PATH.")
    parser.add_argument("--patch-authorities", action="store_true",
        help="Patch <FINGERPRINT> placeholders in authorities.json with the real fingerprint.")
    parser.add_argument("--show-package-commit", action="store_true",
        help="Print the latest commit SHA for issue-store-review-package.json.")
    args = parser.parse_args()

    if args.check:
        return cmd_check(args.json)
    elif args.fingerprint:
        return cmd_fingerprint(args.fingerprint)
    elif args.patch_authorities:
        return cmd_patch_authorities()
    elif args.show_package_commit:
        return cmd_show_package_commit()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
