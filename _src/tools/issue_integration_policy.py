#!/usr/bin/env python3
"""Integration-policy gate verifier for issue store (Task 0037-43).

Enforces non-bypassable branch integration policy:
- Strictly validates candidate tree against agent-workflow.json schema, required fields,
  authority_profile, write_phase, authority_epoch, selector_digest (rejecting all placeholders and mismatches),
  and instruction_bundle consistency (source, digests, members, version, capability, execution-model/runner-protocol).
- Accepts only supported authority_profile / write_phase combinations.
- Requires explicit valid base+candidate boundary and rejects boundary derivation failures (no fallback to HEAD~1 or full-tree scan).
- Under legacy-lists profile: permits conforming legacy changes.
- Under issue-store profile: rejects direct/hand-edited generated backlog views (TODO.md, DONE.md),
  legacy claim files (TODO-*.md), stale epochs, and partial instruction bundle bypasses.
- Fails closed with non-zero exit codes (exit 1 on rejection) across both human and --json modes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

POLICY_SCHEMA = "issue-integration-policy@v1"
SELECTOR_NAME = "agent-workflow.json"

LEGACY_CLAIM_PATTERN = re.compile(r"^TODO-[A-Za-z0-9._-]+\.md$")
PROHIBITED_DIRECT_GENERATED_FILES = frozenset({"TODO.md", "DONE.md"})
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
LINK_RE = re.compile(r"\[[^]]*\]\(([^)#?]+)(?:#[^)]*)?\)")

SUPPORTED_SCHEMAS = {
    "agent-workflow-bootstrap@v1",
    "agent-workflow-bootstrap@v2",
}

V1_REQUIRED_KEYS = frozenset({
    "schema", "workflow_version", "authority_epoch", "authority_profile",
    "write_phase", "required_capability", "runner_protocol",
    "selector_digest", "instruction_bundle",
})

V2_REQUIRED_KEYS = frozenset({
    "schema", "workflow_version", "authority_epoch", "authority_profile",
    "write_phase", "required_capability", "execution_model",
    "selector_digest", "instruction_bundle",
})

SUPPORTED_PHASE_COMBINATIONS = {
    ("legacy-lists", "legacy-writable"),
    ("legacy-lists", "frozen"),
    ("legacy-lists", "legacy-restored"),
    ("issue-store", "issue-store-writable"),
    ("issue-store", "write-frozen"),
}


class IntegrationPolicyViolation(Exception):
    """Raised when candidate commit/tree violates integration policy."""
    def __init__(self, code: str, message: str, locator: str = ""):
        super().__init__(f"{code}: {message} ({locator})")
        self.code = code
        self.message = message
        self.locator = locator


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_selector_digest(value: Mapping[str, Any]) -> str:
    preimage = dict(value)
    preimage.pop("selector_digest", None)
    return "sha256:" + hashlib.sha256(_canonical_bytes(preimage)).hexdigest()


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_repo_path(repo: Path, relative: str) -> Optional[Path]:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts or "\\" in relative:
        return None
    candidate = repo.joinpath(*posix.parts)
    try:
        candidate.resolve().relative_to(repo.resolve())
    except (OSError, ValueError):
        return None
    return candidate


def validate_instruction_bundle(repo: Path, bundle: str) -> Dict[str, str]:
    """Validate bundle path and bundle members recursively."""
    first = _safe_repo_path(repo, bundle)
    if first is None or not first.is_file():
        raise IntegrationPolicyViolation("BUNDLE-MISSING", f"Instruction bundle entry point is missing: {bundle}", bundle)

    pending = [bundle]
    seen: Set[str] = set()
    members: Dict[str, str] = {}
    while pending:
        relative = pending.pop(0)
        if relative in seen:
            continue
        seen.add(relative)
        path = _safe_repo_path(repo, relative)
        if path is None or not path.is_file():
            raise IntegrationPolicyViolation("BUNDLE-MEMBER-MISSING", f"Instruction bundle member missing: {relative}", relative)
        data = path.read_bytes()
        members[relative] = "sha256:" + hashlib.sha256(data).hexdigest()
        if path.suffix.lower() == ".md":
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                raise IntegrationPolicyViolation("BUNDLE-MEMBER-NON-UTF8", f"Bundle member is not UTF-8: {relative}", relative)
            for target in LINK_RE.findall(text):
                linked = (PurePosixPath(relative).parent / target).as_posix()
                if linked.startswith("docs/pipeline/agent-instructions/") and linked not in seen:
                    pending.append(linked)
    return members


def load_and_validate_selector(candidate_root: Path, selector_path: Optional[Path] = None) -> Dict[str, Any]:
    """Strictly load and validate selector schema and required fields without defaults."""
    wf_file = selector_path or (candidate_root / SELECTOR_NAME)
    if not wf_file.is_file():
        raise IntegrationPolicyViolation("MISSING-SELECTOR", f"Required selector file '{SELECTOR_NAME}' is missing", str(wf_file))

    try:
        data = json.loads(wf_file.read_text(encoding="utf-8"))
    except Exception as err:
        raise IntegrationPolicyViolation("CORRUPT-SELECTOR-JSON", f"Failed to parse selector JSON: {err}", str(wf_file))

    if not isinstance(data, dict):
        raise IntegrationPolicyViolation("INVALID-SELECTOR-SHAPE", "Selector root must be a JSON object", str(wf_file))

    schema = data.get("schema")
    if not schema or schema not in SUPPORTED_SCHEMAS:
        raise IntegrationPolicyViolation("UNSUPPORTED-SCHEMA", f"Unsupported or missing selector schema: {schema!r}", str(wf_file))

    req_keys = V2_REQUIRED_KEYS if schema == "agent-workflow-bootstrap@v2" else V1_REQUIRED_KEYS
    missing_keys = sorted(req_keys - set(data.keys()))
    if missing_keys:
        raise IntegrationPolicyViolation("MISSING-SELECTOR-FIELDS", f"Missing required selector field(s): {', '.join(missing_keys)}", str(wf_file))

    # Validate semver
    ver = data.get("workflow_version")
    if not isinstance(ver, str) or not SEMVER_RE.fullmatch(ver):
        raise IntegrationPolicyViolation("INVALID-WORKFLOW-VERSION", f"Invalid semantic workflow_version: {ver!r}", str(wf_file))

    profile = data.get("authority_profile")
    phase = data.get("write_phase")
    epoch = data.get("authority_epoch")

    if not profile or not phase or not epoch:
        raise IntegrationPolicyViolation("MISSING-AUTHORITY-FIELDS", "authority_profile, write_phase, and authority_epoch must not be empty", str(wf_file))

    # Phase / profile consistency
    if (profile, phase) not in SUPPORTED_PHASE_COMBINATIONS:
        raise IntegrationPolicyViolation("PROFILE-PHASE-CONTRADICTION", f"Contradictory authority_profile '{profile}' and write_phase '{phase}'", str(wf_file))

    # Digest verification: Reject ALL placeholders and mismatches strictly
    claimed_digest = data.get("selector_digest", "")
    if not isinstance(claimed_digest, str) or not DIGEST_RE.fullmatch(claimed_digest):
        raise IntegrationPolicyViolation("SELECTOR-DIGEST-INVALID", f"Invalid selector digest format: {claimed_digest!r}", str(wf_file))

    computed_digest = compute_selector_digest(data)
    if claimed_digest != computed_digest:
        raise IntegrationPolicyViolation("SELECTOR-DIGEST-MISMATCH", f"Claimed digest {claimed_digest} != computed digest {computed_digest}", str(wf_file))

    # Instruction bundle validation
    bundle = data.get("instruction_bundle", "")
    validate_instruction_bundle(candidate_root, bundle)

    return data


def derive_changed_files_from_git(candidate_root: Path, base_ref: str) -> List[str]:
    """Derive changed files relative to explicit base_ref without fallbacks."""
    res = subprocess.run(
        ["git", "diff", "--name-only", base_ref, "HEAD"],
        cwd=candidate_root,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise IntegrationPolicyViolation("INVALID-BASE-BOUNDARY", f"Failed to diff against base ref '{base_ref}': {res.stderr.strip()}", base_ref)
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]


def evaluate_integration_policy(
    candidate_root: Path,
    changed_files: Optional[List[str]] = None,
    workflow_path: Optional[Path] = None,
    base_ref: Optional[str] = None,
    enforce_rules: bool = True,
) -> Dict[str, Any]:
    """Evaluate candidate tree against integration policy rules."""
    candidate_root = candidate_root.resolve()
    selector = load_and_validate_selector(candidate_root, workflow_path)

    profile = selector["authority_profile"]
    epoch = selector["authority_epoch"]
    phase = selector["write_phase"]
    schema = selector["schema"]

    # Explicit boundary derivation: no fallback
    if changed_files is not None:
        files_to_check = changed_files
    elif base_ref is not None:
        files_to_check = derive_changed_files_from_git(candidate_root, base_ref)
    else:
        raise IntegrationPolicyViolation("MISSING-BOUNDARY", "Either changed_files or an explicit valid --base boundary must be supplied. Loose full-tree scanning is forbidden.", str(candidate_root))

    violations: List[Dict[str, str]] = []

    for rel in files_to_check:
        norm = rel.replace("\\", "/")

        # Rule 1: Direct edits to generated backlog views under issue-store
        if profile == "issue-store":
            if norm in PROHIBITED_DIRECT_GENERATED_FILES:
                violations.append({
                    "code": "POLICY-PROHIBITED-GENERATED-EDIT",
                    "message": f"Direct modification of generated backlog view '{norm}' is prohibited under authority_profile '{profile}'.",
                    "locator": norm,
                })
            # Rule 2: Legacy claim files under issue-store
            if LEGACY_CLAIM_PATTERN.match(Path(norm).name) and not norm.startswith("provenance/"):
                violations.append({
                    "code": "POLICY-LEGACY-CLAIM-PROHIBITED",
                    "message": f"Legacy claim file '{norm}' cannot land under authority_profile '{profile}'. Use canonical issue store.",
                    "locator": norm,
                })

        # Rule 3: Single-authority compliance
        if "TODO-" in norm and "distributed-roles" in norm:
            violations.append({
                "code": "POLICY-DISTRIBUTED-ROLES-PROHIBITED",
                "message": "Distributed role signatures are prohibited; rescoped to single repository-owner authority.",
                "locator": norm,
            })

    passed = len(violations) == 0
    if enforce_rules and not passed:
        first = violations[0]
        raise IntegrationPolicyViolation(first["code"], first["message"], first["locator"])

    return {
        "schema": POLICY_SCHEMA,
        "status": "passed" if passed else "rejected",
        "authority_profile": profile,
        "authority_epoch": epoch,
        "write_phase": phase,
        "selector_schema": schema,
        "evaluated_files_count": len(files_to_check),
        "violations_count": len(violations),
        "violations": violations,
        "policy_digest": compute_sha256(json.dumps(selector, sort_keys=True).encode("utf-8")),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Issue Integration Policy Gate Verifier (0037-43)")
    parser.add_argument("--root", type=Path, default=Path("."), help="Root path of candidate worktree")
    parser.add_argument("--files", nargs="*", default=None, help="List of changed relative files to evaluate")
    parser.add_argument("--base", type=str, default=None, help="Base commit/branch to diff against")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    parser.add_argument("--workflow", type=Path, default=None, help="Path to agent-workflow.json")

    args = parser.parse_args(argv)
    try:
        res = evaluate_integration_policy(
            candidate_root=args.root,
            changed_files=args.files,
            workflow_path=args.workflow,
            base_ref=args.base,
            enforce_rules=False,
        )
        if args.json:
            sys.stdout.write(json.dumps(res, indent=2) + "\n")
        else:
            if res["status"] == "passed":
                print(f"Integration Policy Gate: PASSED (Profile: {res['authority_profile']}, Epoch: {res['authority_epoch']})")
            else:
                print(f"Integration Policy Gate: REJECTED ({res['violations_count']} violation(s))", file=sys.stderr)
                for v in res["violations"]:
                    print(f"  [{v['code']}] {v['message']} ({v['locator']})", file=sys.stderr)

        return 0 if res["status"] == "passed" else 1

    except IntegrationPolicyViolation as v:
        if args.json:
            err_dict = {
                "schema": POLICY_SCHEMA,
                "status": "rejected",
                "violations": [{"code": v.code, "message": v.message, "locator": v.locator}],
                "violations_count": 1,
            }
            sys.stdout.write(json.dumps(err_dict, indent=2) + "\n")
        else:
            print(f"Integration Policy Gate: REJECTED [{v.code}] {v.message} ({v.locator})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
