#!/usr/bin/env python3
"""manage_approval_readiness.py

Human-operator tool for managing and verifying the external-readiness
prerequisites of 0037-49 before the architecture approval gate (0037-07)
can open.

Usage:
    python3 manage_approval_readiness.py
        Safe default: run all readiness checks and print machine-readable
        JSON (equivalent to --check --json). Nothing is ever mutated by
        this invocation.

    python3 manage_approval_readiness.py --check
        Run all readiness checks and print a human-readable report.

    python3 manage_approval_readiness.py --check --json
        Same, but output machine-readable JSON.

    python3 manage_approval_readiness.py --fingerprint PATH
        Print the SSH fingerprint of the public key at PATH.

    python3 manage_approval_readiness.py --propose-authorities-patch
        Read the current fingerprint from the configured signing key and
        write a *candidate* copy of authorities.json with <FINGERPRINT>
        placeholders replaced, plus a unified diff, under
        output/approval-readiness/. The tracked issues/_policy/authorities.json
        file is never written by this tool. A human reviews the candidate
        and diff and applies them manually.

    python3 manage_approval_readiness.py --show-package-commit
        Print the commit SHA of the latest review-package file, for
        use as <PACKAGE_COMMIT> when writing the approval record.

Design invariants (see Task 0038-15):
  * Every check reads only structured, machine-readable state: git config,
    JSON policy files, and the allowed_signers file. Prose documentation
    (e.g. docs/pipeline/issue-approval-setup.md) is never treated as
    evidence of readiness.
  * This tool never mutates a tracked policy file. The only write this
    tool ever performs targets the git-ignored output/ tree.
  * Every policy JSON file's `schema` field is checked against a pinned
    expected value; a missing or mismatched value is reported as a
    "stale policy" finding rather than silently ignored.
  * A check distinguishes *metadata presence* ("a fingerprint string
    exists in the JSON") from *verified capability* ("the fingerprint is
    well-formed and independently recomputable from real key material, and
    cross-checks against another policy file"). The `capability` field on
    each result is one of "metadata" (presence/format only), "verified"
    (independently recomputed/cross-checked), or "unavailable" (capability
    could not be verified with locally available evidence).
  * No check ever prints a private key file path or private key material.
    Configured signing-key paths are validated but never echoed.

This script uses stdlib only. Python 3.8+.
"""

import argparse
import base64
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

# ---------------------------------------------------------------------------
# Paths (all relative to repo root, resolved per-invocation via policy_paths())
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

REQUIRED_ROLES = [
    "repository-owner",
    "architecture-approver",
    "security",
    "privacy",
    "release",
]

# Pinned expected `schema` field for each policy JSON file. A missing or
# differing value is a "stale policy" finding: the checker refuses to treat
# an unrecognized policy shape as readiness evidence.
POLICY_SCHEMAS = {
    "authorities": "issue-authorities@v1",
    "credential_handles": "credential-handles@v1",
    "runner_service": "runner-service@v1",
}

RESULT_SCHEMA = "approval-readiness-result@v1"

KEY_TYPES = (
    "ssh-ed25519",
    "ssh-rsa",
    "ssh-dss",
    "ecdsa-sha2-nistp256",
    "ecdsa-sha2-nistp384",
    "ecdsa-sha2-nistp521",
)

FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/]{43}$")

_PLACEHOLDER_MARKERS = (
    "<FINGERPRINT>", "<...>", "<ORG>", "<REPO>", "<YOUR_USERNAME>", "<DATE>",
    "placeholder", "TODO",
)


def policy_paths(root: Path) -> Dict[str, Path]:
    policy = root / "issues" / "_policy"
    schema = root / "issues" / "_schema"
    return {
        "authorities": policy / "authorities.json",
        "allowed_signers": policy / "allowed_signers",
        "credential_handles": policy / "credential-handles.json",
        "runner_service": policy / "runner-service.json",
        "approval_schema": schema / "issue-approval-v1.schema.json",
        "package_review": root / "docs" / "pipeline" / "issue-store-review-package.json",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=check,
    )


def _ssh_fingerprint(key_path: str) -> str:
    """Return the SHA256 fingerprint of an SSH public key file.

    Never echoes the input path back on failure, so this helper is safe to
    call with a private-key-adjacent path without leaking it into output.
    """
    r = subprocess.run(
        ["ssh-keygen", "-lf", key_path],
        capture_output=True, text=True, check=False,
    )
    if r.returncode != 0:
        return "ERROR: unable to compute fingerprint (see ssh-keygen exit status)"
    parts = r.stdout.strip().split()
    return parts[1] if len(parts) >= 2 else "ERROR: unexpected ssh-keygen output"


def _fingerprint_from_keydata(key_type: str, b64_data: str) -> Optional[str]:
    """Independently recompute the SHA256 fingerprint from raw key bytes.

    This is a pure, local, stdlib computation (matches `ssh-keygen -lf`
    exactly) used to *verify* — not merely read — that a recorded
    fingerprint corresponds to real, well-formed key material, and to
    cross-check consistency between policy files without ever needing an
    ssh-agent, a private key, or network access.
    """
    if key_type not in KEY_TYPES or not b64_data:
        return None
    try:
        raw = base64.b64decode(b64_data, validate=True)
    except Exception:
        return None
    if not raw:
        return None
    digest = hashlib.sha256(raw).digest()
    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


def _is_placeholder(value) -> bool:
    if not value or not isinstance(value, str):
        return True
    lowered = value.lower()
    return any(marker.lower() in lowered for marker in _PLACEHOLDER_MARKERS)


def _load_json(path: Path) -> Tuple[Optional[dict], Optional[str]]:
    if not path.exists():
        return None, f"File missing: {path.name}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as e:
        return None, f"malformed policy: JSON parse error: {e}"


def _check_schema(data: dict, key: str) -> Optional[str]:
    """Return an issue string if the policy schema field is missing/stale."""
    expected = POLICY_SCHEMAS[key]
    found = data.get("schema")
    if found != expected:
        return f"stale policy: expected schema '{expected}', found {found!r}"
    return None


def _check(label: str, ok: bool, detail: str = "", capability: str = "metadata") -> dict:
    status = "OK" if ok else "BLOCKED"
    line = f"  [{status:7}] {label}  (capability: {capability})"
    if detail:
        line += f"\n           {detail}"
    return {
        "label": label,
        "status": status,
        "capability": capability,
        "detail": detail,
        "_line": line,
    }


# ---------------------------------------------------------------------------
# allowed_signers parsing
# ---------------------------------------------------------------------------
def parse_allowed_signers(text: str) -> List[dict]:
    """Parse an OpenSSH allowed_signers file into structured entries.

    Each entry records whether it is malformed (cannot be used to compute a
    fingerprint) and whether it is marked revoked via a trailing
    ``# revoked`` comment. Recognizing revocation this way avoids inventing
    a private extension to the allowed_signers line format while still
    letting the "revoke" fixture category be expressed and detected.
    """
    entries: List[dict] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        comment = ""
        if "#" in line:
            line, _, comment = line.partition("#")
            line = line.strip()
            comment = comment.strip()
        tokens = line.split()
        if len(tokens) < 3:
            entries.append({"line": lineno, "malformed": True})
            continue
        principal = tokens[0]
        keytype = None
        keydata = None
        for i, tok in enumerate(tokens[1:], start=1):
            if tok in KEY_TYPES and i + 1 < len(tokens):
                keytype = tok
                keydata = tokens[i + 1]
                break
        if not keytype or not keydata:
            entries.append({"line": lineno, "malformed": True})
            continue
        fingerprint = _fingerprint_from_keydata(keytype, keydata)
        entries.append({
            "line": lineno,
            "malformed": fingerprint is None,
            "principal": principal,
            "key_type": keytype,
            "fingerprint": fingerprint,
            "revoked": "revoked" in comment.lower(),
        })
    return entries


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def check_remote(root: Path) -> dict:
    """Check: git remote 'origin' is configured (metadata presence only)."""
    r = _git(root, "remote", "get-url", "origin")
    ok = r.returncode == 0 and r.stdout.strip() != ""
    detail = r.stdout.strip() if ok else (
        "No remote 'origin'. Run: git remote add origin git@github.com:<ORG>/<REPO>.git"
    )
    return _check("Repository remote (origin)", ok, detail, capability="metadata")


def check_signing_key(root: Path) -> dict:
    """Check: git is configured with an SSH signing key and allowed_signers.

    Reports configuration presence only (capability="metadata"); never
    echoes the configured key path in output.
    """
    issues = []
    r = _git(root, "config", "--local", "gpg.format")
    if r.returncode != 0 or r.stdout.strip() != "ssh":
        issues.append("gpg.format != ssh. Run: git config --local gpg.format ssh")

    r = _git(root, "config", "--local", "user.signingkey")
    keypath = r.stdout.strip()
    if not keypath:
        issues.append("user.signingkey not set. Run: git config --local user.signingkey ~/.ssh/<KEY>.pub")
    elif not Path(os.path.expanduser(keypath)).exists():
        issues.append("configured user.signingkey file does not exist")

    r = _git(root, "config", "--local", "gpg.ssh.allowedSignersFile")
    if not r.stdout.strip():
        issues.append(
            "gpg.ssh.allowedSignersFile not set. "
            "Run: git config --local gpg.ssh.allowedSignersFile issues/_policy/allowed_signers"
        )

    ok = len(issues) == 0
    detail = "signing key configured and present" if ok else " | ".join(issues)
    return _check("Git SSH signing key configuration", ok, detail, capability="metadata")


def check_allowed_signers(root: Path) -> Tuple[dict, List[dict]]:
    """Check: allowed_signers has at least one active, well-formed entry.

    Returns the check result plus the list of active (non-revoked,
    well-formed) parsed entries, so callers can cross-check authorities.json
    fingerprints against real key material (capability="verified").
    """
    paths = policy_paths(root)
    path = paths["allowed_signers"]
    if not path.exists():
        return _check("allowed_signers populated", False,
                       "File missing.", capability="metadata"), []

    entries = parse_allowed_signers(path.read_text(encoding="utf-8"))
    malformed = [e for e in entries if e.get("malformed")]
    revoked = [e for e in entries if not e.get("malformed") and e.get("revoked")]
    active = [e for e in entries if not e.get("malformed") and not e.get("revoked")]

    issues = []
    if malformed:
        lines = ", ".join(str(e["line"]) for e in malformed)
        issues.append(f"malformed policy: {len(malformed)} malformed entr{'y' if len(malformed) == 1 else 'ies'} (line {lines})")
    if not active:
        issues.append("no active (non-revoked, well-formed) signer entries. See issue-approval-setup.md Step 3.")

    ok = not issues
    capability = "verified" if ok else "metadata"
    detail = (f"{len(active)} active principal(s), {len(revoked)} revoked"
              if ok else " | ".join(issues))
    result = _check("allowed_signers populated", ok, detail, capability=capability)
    return result, active


def check_authorities(root: Path, active_signers: Optional[List[dict]] = None) -> dict:
    """Check: authorities.json has real, cross-verifiable fingerprints for
    all required roles.

    When `active_signers` (from check_allowed_signers) is supplied, a
    principal's fingerprint is additionally required to match an actual
    allowed_signers entry, elevating the result from "metadata present" to
    "verified": the fingerprint is not just a plausible-looking string, it
    corresponds to key material the repository actually trusts.
    """
    paths = policy_paths(root)
    data, err = _load_json(paths["authorities"])
    if err:
        return _check("authorities.json complete", False, err, capability="metadata")

    schema_issue = _check_schema(data, "authorities")
    if schema_issue:
        return _check("authorities.json complete", False, schema_issue, capability="metadata")

    principals = data.get("principals", [])
    if not principals:
        return _check("authorities.json complete", False,
                       "No 'principals' array. File still contains skeleton. "
                       "See issue-approval-setup.md Step 4.", capability="metadata")

    signer_fps: Optional[Set[str]] = None
    if active_signers is not None:
        signer_fps = {e["fingerprint"] for e in active_signers if e.get("fingerprint")}

    issues = []
    active_roles: Set[str] = set()
    verified_count = 0
    for p in principals:
        if not isinstance(p, dict):
            issues.append("malformed principal entry")
            continue
        role = p.get("role", "?")
        if p.get("revoked"):
            continue
        fp = p.get("ssh_fingerprint", "")
        if _is_placeholder(fp) or not FINGERPRINT_RE.match(fp):
            issues.append(f"placeholder/invalid fingerprint in role '{role}'. Run --propose-authorities-patch.")
            continue
        if signer_fps is not None:
            if fp not in signer_fps:
                issues.append(f"wrong fingerprint: role '{role}' has no matching allowed_signers entry")
                continue
            verified_count += 1
        active_roles.add(role)

    for role in REQUIRED_ROLES:
        if role not in active_roles:
            issues.append(f"missing role: {role}")

    if not data.get("independent_channel"):
        issues.append("'independent_channel' not set in authorities.json")

    ok = len(issues) == 0
    capability = "verified" if (ok and signer_fps is not None and verified_count > 0) else "metadata"
    detail = f"roles OK: {sorted(active_roles)}" if ok else " | ".join(issues)
    return _check("authorities.json complete", ok, detail, capability=capability)


def check_credential_handle(root: Path) -> dict:
    """Check: at least one active credential handle with a fingerprint that
    is independently recomputable from its own recorded public key.

    A handle whose fingerprint cannot be cross-checked this way (missing or
    malformed `public_key`) is reported as capability "unavailable": its
    metadata alone is not proof the handle is usable. The policy schema
    intentionally never records a private key path, so this check never
    touches or prints one.
    """
    paths = policy_paths(root)
    data, err = _load_json(paths["credential_handles"])
    if err:
        return _check("Credential handle", False,
                       f"{err}. See issue-approval-setup.md Step 5.", capability="metadata")

    schema_issue = _check_schema(data, "credential_handles")
    if schema_issue:
        return _check("Credential handle", False, schema_issue, capability="metadata")

    handles = data.get("handles", [])
    if not handles:
        return _check("Credential handle", False, "No handles declared.", capability="metadata")

    issues = []
    active = 0
    verified = 0
    for h in handles:
        hid = h.get("handle_id", "?")
        if h.get("revoked"):
            continue
        active += 1
        if not h.get("scope"):
            issues.append(f"handle '{hid}' has no scope")
            continue
        fp = h.get("fingerprint", "")
        if _is_placeholder(fp) or not FINGERPRINT_RE.match(fp):
            issues.append(f"handle '{hid}' has a placeholder/invalid fingerprint")
            continue
        pub = h.get("public_key", "")
        tokens = pub.split()
        if len(tokens) < 2 or tokens[0] not in KEY_TYPES:
            issues.append(f"handle '{hid}': capability unavailable — cannot independently verify "
                           f"fingerprint (public_key missing/malformed)")
            continue
        computed = _fingerprint_from_keydata(tokens[0], tokens[1])
        if computed != fp:
            issues.append(f"handle '{hid}': wrong fingerprint — recorded value does not match "
                           f"the key material in public_key")
            continue
        verified += 1

    if active == 0:
        issues.append("no active (non-revoked) handle")

    ok = len(issues) == 0
    capability = "verified" if (ok and verified > 0) else "unavailable"
    detail = f"{verified} verified handle(s)" if ok else " | ".join(issues)
    return _check("Credential handle", ok, detail, capability=capability)


def check_runner_service(root: Path) -> dict:
    """Check: runner service controls are documented (metadata presence).

    This tool intentionally never executes `health_check`/`restart_path`/
    `rollback_path` as commands: treating attacker- or typo-controlled JSON
    fields as executable shell would turn a readiness *check* into an
    arbitrary-command *mutator*, which is exactly the class of defect this
    Task exists to remove. Verifying actual runner reachability is left to
    a dedicated, explicitly-invoked operational probe, not this default
    check.
    """
    paths = policy_paths(root)
    data, err = _load_json(paths["runner_service"])
    if err:
        return _check("Runner service controls", False,
                       f"{err}. See issue-approval-setup.md Step 6.", capability="metadata")

    schema_issue = _check_schema(data, "runner_service")
    if schema_issue:
        return _check("Runner service controls", False, schema_issue, capability="metadata")

    issues = []
    for field in ["health_check", "restart_path", "rollback_path", "operator"]:
        if not data.get(field):
            issues.append(f"'{field}' not set (absent service control)")
    ok = len(issues) == 0
    detail = f"Operator: {data.get('operator')}" if ok else " | ".join(issues)
    return _check("Runner service controls", ok, detail, capability="metadata")


# ---------------------------------------------------------------------------
# Aggregate check runner
# ---------------------------------------------------------------------------
def run_checks(root: Path) -> List[dict]:
    signer_result, active_signers = check_allowed_signers(root)
    results = [
        check_remote(root),
        check_signing_key(root),
        signer_result,
        check_authorities(root, active_signers),
        check_credential_handle(root),
        check_runner_service(root),
    ]
    return results


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_check(root: Path, as_json: bool) -> int:
    results = run_checks(root)
    all_ok = all(r["status"] == "OK" for r in results)

    if as_json:
        out = {
            "schema": RESULT_SCHEMA,
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


def cmd_propose_authorities_patch(root: Path, out_dir: Optional[Path] = None) -> int:
    """Write a reviewed *candidate* authorities.json plus a unified diff.

    This never writes to the tracked issues/_policy/authorities.json file.
    Output goes under the git-ignored output/ tree so it can never be
    accidentally committed as though it were policy. A human reviews the
    candidate and diff and applies them manually.
    """
    paths = policy_paths(root)
    authorities_path = paths["authorities"]

    r = _git(root, "config", "--local", "user.signingkey")
    keypath = r.stdout.strip()
    if not keypath:
        print("ERROR: user.signingkey not configured. Run git config --local user.signingkey <path> first.", file=sys.stderr)
        return 1
    key_file = Path(os.path.expanduser(keypath))
    if not key_file.exists():
        print("ERROR: configured signing key file does not exist.", file=sys.stderr)
        return 1

    fp = _ssh_fingerprint(str(key_file))
    if fp.startswith("ERROR"):
        print(f"ERROR computing fingerprint: {fp}", file=sys.stderr)
        return 1

    if not authorities_path.exists():
        print(f"ERROR: {authorities_path} not found", file=sys.stderr)
        return 1

    original = authorities_path.read_text(encoding="utf-8")
    candidate_text, count = re.subn(r"SHA256:<FINGERPRINT>", fp, original)
    if count == 0:
        print("No <FINGERPRINT> placeholders found. Nothing to propose.")
        return 0

    candidate_root = out_dir or (root / "output" / "approval-readiness")
    candidate_root.mkdir(parents=True, exist_ok=True)
    candidate_path = candidate_root / "authorities.candidate.json"
    candidate_path.write_text(candidate_text, encoding="utf-8")

    diff_text = "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        candidate_text.splitlines(keepends=True),
        fromfile="issues/_policy/authorities.json (tracked, unchanged)",
        tofile="authorities.candidate.json (proposed)",
    ))
    diff_path = candidate_root / "authorities.candidate.diff"
    diff_path.write_text(diff_text, encoding="utf-8")

    print(f"Patched {count} placeholder(s) in a reviewed candidate. The tracked policy file was NOT modified.")
    print(f"Candidate: {candidate_path}")
    print(f"Diff:      {diff_path}")
    print("After human review, apply manually, e.g.:")
    print(f"  cp {candidate_path} {authorities_path}")
    print(f"  git add {authorities_path} && git commit -m 'policy: populate authorities.json fingerprints'")
    return 0


def cmd_show_package_commit(root: Path) -> int:
    paths = policy_paths(root)
    r = _git(root, "log", "--format=%H", "-1", "--", str(paths["package_review"]))
    sha = r.stdout.strip()
    if not sha:
        print("ERROR: no commit found for issue-store-review-package.json", file=sys.stderr)
        return 1
    print(sha)
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manage 0037-49 approval readiness prerequisites.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--check", action="store_true",
        help="Run all readiness checks and report status.")
    parser.add_argument("--json", action="store_true",
        help="Output check results as JSON (use with --check).")
    parser.add_argument("--fingerprint", metavar="PATH",
        help="Print the SSH fingerprint of the key at PATH.")
    parser.add_argument("--propose-authorities-patch", dest="propose_patch", action="store_true",
        help="Write a reviewed candidate + diff for authorities.json under output/approval-readiness/. "
             "Never writes the tracked policy file.")
    parser.add_argument("--patch-authorities", dest="propose_patch", action="store_true",
        help=argparse.SUPPRESS)  # backward-compatible alias for --propose-authorities-patch
    parser.add_argument("--show-package-commit", action="store_true",
        help="Print the latest commit SHA for issue-store-review-package.json.")
    parser.add_argument("--root", metavar="PATH", help=argparse.SUPPRESS)  # test/CLI override
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else REPO_ROOT

    action_selected = args.check or bool(args.fingerprint) or args.propose_patch or args.show_package_commit

    if not action_selected:
        # Safe default: read-only, machine-readable check. Nothing mutates.
        return cmd_check(root, True)
    if args.fingerprint:
        return cmd_fingerprint(args.fingerprint)
    if args.propose_patch:
        return cmd_propose_authorities_patch(root)
    if args.show_package_commit:
        return cmd_show_package_commit(root)
    return cmd_check(root, args.json)


if __name__ == "__main__":
    sys.exit(main())
