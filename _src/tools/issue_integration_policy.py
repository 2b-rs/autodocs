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
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Set

try:
    from _src.tools import agent_bootstrap
except ModuleNotFoundError:  # Direct script execution outside an installed package.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from _src.tools import agent_bootstrap

POLICY_SCHEMA = "issue-integration-policy@v1"
SELECTOR_NAME = "agent-workflow.json"

LEGACY_CLAIM_PATTERN = re.compile(r"^TODO-[A-Za-z0-9._-]+\.md$")
LEGACY_COMPLETION_PATTERN = re.compile(r"^DONE-[A-Za-z0-9._-]+\.md$")
FROZEN_CUTOVER_TASK_PATTERN = re.compile(r"(?<![0-9])0037-(?:3[0-9]|40)(?![0-9])")
ASSIGNMENT_ID_PATTERN = re.compile(r"(?<![0-9])[0-9]{13}-[0-9a-f]{8}(?![0-9a-f])")
PROHIBITED_DIRECT_GENERATED_FILES = frozenset({"TODO.md", "DONE.md"})
FROZEN_METADATA_PATHS = frozenset({
    "agent-workflow.json",
    ".github/workflows/issue-policy.yml",
    "_src/tools/issue_integration_policy.py",
    "_src/tests/test_issue_integration_policy.py",
})
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

LEGACY_V1_CONTRACT = {
    "schema": "agent-workflow-bootstrap@v1",
    "workflow_version": "1.0.0",
    "authority_epoch": "legacy-writable",
    "authority_profile": "legacy-lists",
    "write_phase": "legacy-writable",
    "required_capability": "sandboxed-grunt",
    "runner_protocol": "runner-request@v1",
    "instruction_bundle": "docs/pipeline/agent-instructions/legacy/index.md",
}
V2_PHASES = {
    "legacy-writable": ("legacy-lists", "legacy-writable", "legacy"),
    "legacy-frozen": ("legacy-lists", "frozen", "current"),
    "legacy-restored": ("legacy-lists", "legacy-restored", "legacy"),
    "issue-store-writable": ("issue-store", "issue-store-writable", "future"),
    "issue-store-write-frozen": ("issue-store", "write-frozen", "future"),
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
    """Use the bootstrap doctor's canonical recursive bundle traversal."""
    diagnostics: List[Dict[str, str]] = []
    members = agent_bootstrap._bundle_members(repo, bundle, diagnostics)
    if diagnostics:
        first = diagnostics[0]
        raise IntegrationPolicyViolation(first["id"], first["message"], bundle)
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
    unknown_keys = sorted(set(data) - req_keys)
    if unknown_keys:
        raise IntegrationPolicyViolation("UNKNOWN-SELECTOR-FIELDS", f"Unknown selector field(s): {', '.join(unknown_keys)}", str(wf_file))
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

    # Bind every compatibility field to one supported transition contract.
    if schema == "agent-workflow-bootstrap@v1":
        mismatches = [key for key, expected in LEGACY_V1_CONTRACT.items() if data.get(key) != expected]
        if mismatches:
            raise IntegrationPolicyViolation("UNSUPPORTED-V1-CONTRACT", f"Unsupported v1 contract field(s): {', '.join(mismatches)}", str(wf_file))
        bundle = data["instruction_bundle"]
        declared_members = None
    else:
        expected_phase = V2_PHASES.get(str(epoch))
        if expected_phase is None or (profile, phase) != expected_phase[:2]:
            raise IntegrationPolicyViolation("PROFILE-PHASE-CONTRADICTION", "v2 authority epoch/profile/phase is unsupported", str(wf_file))
        if ver != "2.0.0" or data.get("execution_model") != "direct" or data.get("required_capability") not in {"unprivileged", "privileged"}:
            raise IntegrationPolicyViolation("UNSUPPORTED-V2-CONTRACT", "v2 requires version 2.0.0, direct execution, and an unprivileged/privileged capability", str(wf_file))
        bundle_value = data.get("instruction_bundle")
        if not isinstance(bundle_value, dict) or set(bundle_value) != {"path", "members"}:
            raise IntegrationPolicyViolation("INVALID-BUNDLE-DECLARATION", "v2 instruction_bundle must contain exactly path and members", str(wf_file))
        bundle = bundle_value.get("path")
        declared_members = bundle_value.get("members")
        expected_bundle = f"docs/pipeline/agent-instructions/{expected_phase[2]}/index.md"
        if bundle != expected_bundle:
            raise IntegrationPolicyViolation("UNSUPPORTED-BUNDLE-PATH", f"Expected bundle {expected_bundle}", str(wf_file))

    # The live legacy selector's all-a digest is the sole transitional exception.
    claimed_digest = data.get("selector_digest", "")
    if not isinstance(claimed_digest, str) or not DIGEST_RE.fullmatch(claimed_digest):
        raise IntegrationPolicyViolation("SELECTOR-DIGEST-INVALID", f"Invalid selector digest format: {claimed_digest!r}", str(wf_file))

    computed_digest = agent_bootstrap.selector_digest(data)
    legacy_placeholder = schema.endswith("@v1") and data == {**LEGACY_V1_CONTRACT, "selector_digest": claimed_digest} and claimed_digest == "sha256:" + "a" * 64
    if claimed_digest != computed_digest and not legacy_placeholder:
        raise IntegrationPolicyViolation("SELECTOR-DIGEST-MISMATCH", f"Claimed digest {claimed_digest} != computed digest {computed_digest}", str(wf_file))

    actual_members = validate_instruction_bundle(candidate_root, bundle)
    if schema.endswith("@v2"):
        if not isinstance(declared_members, dict) or declared_members != actual_members:
            raise IntegrationPolicyViolation("BUNDLE-MEMBER-DIGEST-MISMATCH", "Declared bundle members do not exactly match candidate bytes", str(wf_file))

    return data


def _resolve_commit(candidate_root: Path, ref: str, label: str) -> str:
    res = subprocess.run(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], cwd=candidate_root, capture_output=True, text=True)
    if res.returncode != 0:
        raise IntegrationPolicyViolation(f"INVALID-{label}-REF", f"Cannot resolve immutable {label.lower()} commit", ref)
    return res.stdout.strip()


def classify_frozen_path(relative: str) -> str:
    """Classify one changed path under the Architect-approved frozen scope."""
    norm = relative.replace("\\", "/")
    name = PurePosixPath(norm).name
    if norm in PROHIBITED_DIRECT_GENERATED_FILES:
        return "legacy-backlog"
    if "/" not in norm and (LEGACY_CLAIM_PATTERN.fullmatch(name) or LEGACY_COMPLETION_PATTERN.fullmatch(name)):
        return "cutover-record" if FROZEN_CUTOVER_TASK_PATTERN.search(name) else "legacy-claim"
    if (
        norm.startswith("docs/dossiers/0037-")
        or norm.startswith("provenance/migrations/issue-store/0037-")
    ) and FROZEN_CUTOVER_TASK_PATTERN.search(norm):
        return "cutover-evidence"
    if norm in FROZEN_METADATA_PATHS:
        return "epoch-metadata"
    if norm.startswith("_src/output/issue-migration/") or norm.startswith("issues/"):
        return "migration-output"
    return "unrestricted"


def _candidate_blob(candidate_root: Path, candidate: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{candidate}:{relative}"],
        cwd=candidate_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout


def frozen_authority_proof(candidate_root: Path, candidate: str, relative: str) -> bool:
    """Require task and assignment binding in the immutable candidate blob."""
    task_match = FROZEN_CUTOVER_TASK_PATTERN.search(relative)
    if task_match is None:
        return False
    text = _candidate_blob(candidate_root, candidate, relative)
    task_id = task_match.group(0)
    if task_id not in text:
        return False
    assignment_ids = set(re.findall(
        r"(?im)^\s*[-*]?\s*[\"`*]*(?:assignment|assignment_id|authority)[\"`*]*\s*[:=][^\n]*?([0-9]{13}-[0-9a-f]{8})",
        text,
    ))
    try:
        payload = json.loads(text)
    except (TypeError, ValueError):
        payload = None
    if isinstance(payload, dict):
        for key in ("assignment", "assignment_id", "authority"):
            value = payload.get(key)
            if isinstance(value, str):
                assignment_ids.update(ASSIGNMENT_ID_PATTERN.findall(value))
    owner_ids = set(re.findall(
        rf"agent:[a-z0-9._-]+:{re.escape(task_id)}[^\n`]*?:([0-9]{{13}}-[0-9a-f]{{8}})",
        text,
    ))
    if classify_frozen_path(relative) == "cutover-record":
        return bool(assignment_ids & owner_ids)
    if not assignment_ids:
        if relative.endswith(".md"):
            companion = relative[:-3] + ".json"
            if _candidate_blob(candidate_root, candidate, companion):
                return frozen_authority_proof(candidate_root, candidate, companion)
        return False

    listing = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", candidate],
        cwd=candidate_root,
        capture_output=True,
        text=True,
    )
    if listing.returncode != 0:
        return False
    for claim_path in listing.stdout.splitlines():
        if "/" in claim_path or classify_frozen_path(claim_path) != "cutover-record" or task_id not in claim_path:
            continue
        claim_text = _candidate_blob(candidate_root, candidate, claim_path)
        claim_assignment_ids = set(ASSIGNMENT_ID_PATTERN.findall(claim_text))
        claim_owner_ids = set(re.findall(
            rf"agent:[a-z0-9._-]+:{re.escape(task_id)}[^\n`]*?:([0-9]{{13}}-[0-9a-f]{{8}})",
            claim_text,
        ))
        if assignment_ids & claim_assignment_ids & claim_owner_ids:
            return True
    return False


def derive_changed_files_from_git(candidate_root: Path, base_ref: str, candidate_ref: str) -> tuple[List[str], str, str]:
    """Resolve and validate an explicit immutable ancestor boundary."""
    base = _resolve_commit(candidate_root, base_ref, "BASE")
    candidate = _resolve_commit(candidate_root, candidate_ref, "CANDIDATE")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", base, candidate], cwd=candidate_root)
    if ancestor.returncode != 0:
        raise IntegrationPolicyViolation("NON-ANCESTOR-BOUNDARY", "Base is not an ancestor of candidate", f"{base}..{candidate}")
    head = _resolve_commit(candidate_root, "HEAD", "CANDIDATE")
    dirty = subprocess.run(["git", "diff", "--quiet", candidate], cwd=candidate_root).returncode
    if head != candidate or dirty != 0:
        raise IntegrationPolicyViolation("CANDIDATE-TREE-MISMATCH", "Worktree tracked bytes do not match explicit candidate commit", candidate)
    res = subprocess.run(
        ["git", "diff", "--name-only", base, candidate],
        cwd=candidate_root,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise IntegrationPolicyViolation("INVALID-BASE-BOUNDARY", f"Failed to diff against base ref '{base_ref}': {res.stderr.strip()}", base_ref)
    return [line.strip() for line in res.stdout.splitlines() if line.strip()], base, candidate


def evaluate_integration_policy(
    candidate_root: Path,
    workflow_path: Optional[Path] = None,
    base_ref: Optional[str] = None,
    candidate_ref: Optional[str] = None,
    enforce_rules: bool = True,
) -> Dict[str, Any]:
    """Evaluate candidate tree against integration policy rules."""
    candidate_root = candidate_root.resolve()
    if not base_ref or not candidate_ref:
        raise IntegrationPolicyViolation("MISSING-BOUNDARY", "Explicit immutable base_ref and candidate_ref are required", str(candidate_root))
    files_to_check, base_commit, candidate_commit = derive_changed_files_from_git(candidate_root, base_ref, candidate_ref)
    selector = load_and_validate_selector(candidate_root, workflow_path)

    profile = selector["authority_profile"]
    epoch = selector["authority_epoch"]
    phase = selector["write_phase"]
    schema = selector["schema"]

    violations: List[Dict[str, str]] = []

    for rel in files_to_check:
        norm = rel.replace("\\", "/")

        if epoch == "legacy-frozen" and phase == "frozen":
            path_class = classify_frozen_path(norm)
            if path_class == "legacy-backlog":
                violations.append({
                    "code": "POLICY-FROZEN-BACKLOG-EDIT-PROHIBITED",
                    "message": f"Legacy backlog file '{norm}' is immutable while authority epoch is legacy-frozen.",
                    "locator": norm,
                })
            elif path_class == "legacy-claim":
                violations.append({
                    "code": "POLICY-FROZEN-LEGACY-CLAIM-PROHIBITED",
                    "message": f"Ordinary legacy claim or completion record '{norm}' cannot land while authority epoch is legacy-frozen.",
                    "locator": norm,
                })
            elif path_class in {"cutover-record", "cutover-evidence"} and not frozen_authority_proof(candidate_root, candidate_commit, norm):
                violations.append({
                    "code": "POLICY-FROZEN-AUTHORITY-PROOF-REQUIRED",
                    "message": f"Frozen-window cutover record '{norm}' lacks task- and assignment-bound authority proof.",
                    "locator": norm,
                })

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
        "base_commit": base_commit,
        "candidate_commit": candidate_commit,
        "evaluated_files_count": len(files_to_check),
        "violations_count": len(violations),
        "violations": violations,
        "policy_digest": compute_sha256(json.dumps(selector, sort_keys=True).encode("utf-8")),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Issue Integration Policy Gate Verifier (0037-43)")
    parser.add_argument("--root", type=Path, default=Path("."), help="Root path of candidate worktree")
    parser.add_argument("--base-ref", required=True, help="Explicit immutable base commit")
    parser.add_argument("--candidate-ref", required=True, help="Explicit immutable candidate commit")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    parser.add_argument("--workflow", type=Path, default=None, help="Path to agent-workflow.json")

    args = parser.parse_args(argv)
    try:
        res = evaluate_integration_policy(
            candidate_root=args.root,
            workflow_path=args.workflow,
            base_ref=args.base_ref,
            candidate_ref=args.candidate_ref,
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
