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
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Set

try:
    from _src.tools import agent_bootstrap, runner_transaction
except ModuleNotFoundError:  # Direct script execution outside an installed package.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from _src.tools import agent_bootstrap, runner_transaction

_IMPORTER_SPEC = importlib.util.spec_from_file_location(
    "issue_import_legacy_candidate", Path(__file__).with_name("issue_import_legacy.py")
)
if _IMPORTER_SPEC is None or _IMPORTER_SPEC.loader is None:
    raise RuntimeError("candidate issue importer module is unavailable")
issue_import_legacy = importlib.util.module_from_spec(_IMPORTER_SPEC)
_IMPORTER_SPEC.loader.exec_module(issue_import_legacy)

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
FROZEN_CLOSURE_MANIFEST = runner_transaction.FROZEN_CLOSURE_MANIFEST_PATH
CLAIMLESS_0037_31_MANIFEST = "provenance/migrations/issue-store/0037-31-final-frozen-candidate.json"
CLAIMLESS_0037_31_ASSIGNMENT = "1788519031177-793919ee"
CLAIMLESS_0037_31_ITEM = "0037-31-final-frozen-migration"
CLAIMLESS_0037_31_SOURCE = "7dbc94db262979b41bc225d6571d610123a47814"
CLAIMLESS_0037_31_SOURCE_TREE = "6a6c40de53f15245a084bbdc68b526f07ab5b534"
CLAIMLESS_0037_31_TRANSACTION = "f5a806c52a63e00edac5c0aa8bb0793227ae3af1"
CLAIMLESS_0037_31_RUN_ID = "0037-31-post-delta-7dbc94db-r2"
CLAIMLESS_0037_31_RUN_ROOT = f"_src/output/issue-migration/{CLAIMLESS_0037_31_RUN_ID}"
CLAIMLESS_0037_31_EVIDENCE = frozenset({
    CLAIMLESS_0037_31_MANIFEST,
    "provenance/migrations/issue-store/0037-31-final-frozen-candidate.md",
    "docs/dossiers/0037-31-final-frozen-migration-20260904.md",
})
CLAIMLESS_0037_31_SCOPE = frozenset({
    "_src/tools/issue_import_legacy.py", "_src/tools/issue_integration_policy.py",
    "_src/tests/test_issue_import_legacy.py", "_src/tests/test_issue_integration_policy.py",
    CLAIMLESS_0037_31_RUN_ROOT, *CLAIMLESS_0037_31_EVIDENCE,
})
PROMOTION_0037_31_ASSIGNMENT = "1788546750193-fb7f5f95"
PROMOTION_0037_31_DELEGATION = "1788547915174-4a5b7bc0"
PROMOTION_0037_31_EXTENSION_AWARD = "1788578218939-4aee4c00"
PROMOTION_0037_31_BASE_CANDIDATE = "6923deec89fc15575fb23047d8236a89b3fd286e"
PROMOTION_0037_31_CANONICAL_BASE = "d40d104519625fe019e0fccf04b9b32c49ac4562"
PROMOTION_0037_31_RUN_ID = "0037-31-promoted-dispositions-20260904-r2"
PROMOTION_0037_31_RUN_ROOT = f"_src/output/issue-migration/{PROMOTION_0037_31_RUN_ID}"
PROMOTION_0037_31_RETAINED_RUN_ROOT = "_src/output/issue-migration/0037-31-promoted-dispositions-20260904-r1"
PROMOTION_0037_31_RETAINED_TREE = "93e1703e2103fd304ec2f22fa4f6f2b83008179a"
PROMOTION_0037_31_RETAINED_MANIFEST_SHA256 = "0bb49bee19793152d0b87f677a5793f642057e3db9ab6722194810d3ac217620"
PROMOTION_0037_31_RETAINED_COUNT = 975
PROMOTION_0037_31_AUTHORITY = "provenance/migrations/issue-store/0037-31-promotion/migration-disposition-authority.json"
PROMOTION_0037_31_DISPOSITIONS = "provenance/migrations/issue-store/0037-31-promotion/migration-dispositions.json"
PROMOTION_0037_31_EVIDENCE = frozenset({
    CLAIMLESS_0037_31_MANIFEST,
    "provenance/migrations/issue-store/0037-31-final-frozen-candidate.md",
    "docs/dossiers/0037-31-final-frozen-migration-20260904.md",
    PROMOTION_0037_31_AUTHORITY,
    PROMOTION_0037_31_DISPOSITIONS,
})
PROMOTION_0037_31_GOVERNANCE = frozenset({
    "docs/dossiers/0037-31-promotion-policy-scope-review-20260904.md",
    "docs/dossiers/dec-0037-035-promotion-policy-proof-extension.md",
    "docs/dossiers/0037-31-promotion-rework-scope-review-20260904.md",
})
PROMOTION_0037_31_FILES = frozenset({
    "_src/tools/issue_import_legacy.py", "_src/tests/test_issue_import_legacy.py",
    "_src/tools/issue_integration_policy.py", "_src/tests/test_issue_integration_policy.py",
    *PROMOTION_0037_31_EVIDENCE,
})
PROMOTION_0037_31_REPORTS = {
    "migration_report_sha256": PROMOTION_0037_31_RUN_ROOT + "/reports/migration-report.json",
    "migration_state_sha256": PROMOTION_0037_31_RUN_ROOT + "/reports/migration-state.json",
    "disposition_coverage_sha256": PROMOTION_0037_31_RUN_ROOT + "/issues/import-disposition-coverage.json",
    "disposition_runs_sha256": PROMOTION_0037_31_RUN_ROOT + "/issues/import-disposition-runs.jsonl",
    "findings_sha256": PROMOTION_0037_31_RUN_ROOT + "/issues/import-findings.json",
    "import_manifest_sha256": PROMOTION_0037_31_RUN_ROOT + "/issues/import-manifest.json",
}
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


def _candidate_blob_sha256(candidate_root: Path, candidate: str, relative: str) -> Optional[str]:
    result = subprocess.run(
        ["git", "show", f"{candidate}:{relative}"], cwd=candidate_root, capture_output=True
    )
    return hashlib.sha256(result.stdout).hexdigest() if result.returncode == 0 else None


def _claimless_0037_31_proof(
    candidate_root: Path, candidate: str, relative: str, changed_files: Set[str]
) -> bool:
    """Validate DEC-0037-033's closed assignment/source/transaction proof."""
    if relative not in CLAIMLESS_0037_31_EVIDENCE:
        return False
    try:
        manifest = json.loads(_candidate_blob(candidate_root, candidate, CLAIMLESS_0037_31_MANIFEST))
    except (TypeError, ValueError):
        return False
    if not isinstance(manifest, dict):
        return False
    proof = manifest.get("authority_proof")
    expected_keys = {
        "schema", "task_id", "assignment_id", "atomic_award", "item_identity",
        "claim_mode", "authority_epoch", "source_commit", "source_tree",
        "closure_transaction", "run_id", "run_root", "allowed_paths",
        "evidence_paths", "companion_sha256",
    }
    if not isinstance(proof, dict) or set(proof) != expected_keys:
        return False
    expected = {
        "schema": "claimless-frozen-assignment-proof@v1", "task_id": "0037-31",
        "assignment_id": CLAIMLESS_0037_31_ASSIGNMENT,
        "atomic_award": CLAIMLESS_0037_31_ASSIGNMENT,
        "item_identity": CLAIMLESS_0037_31_ITEM,
        "claim_mode": "claimless-frozen-transaction", "authority_epoch": "legacy-frozen",
        "source_commit": CLAIMLESS_0037_31_SOURCE, "source_tree": CLAIMLESS_0037_31_SOURCE_TREE,
        "closure_transaction": CLAIMLESS_0037_31_TRANSACTION,
        "run_id": CLAIMLESS_0037_31_RUN_ID, "run_root": CLAIMLESS_0037_31_RUN_ROOT + "/",
    }
    if any(proof.get(key) != value for key, value in expected.items()):
        return False
    if proof.get("allowed_paths") != sorted(CLAIMLESS_0037_31_SCOPE):
        return False
    if proof.get("evidence_paths") != sorted(CLAIMLESS_0037_31_EVIDENCE):
        return False
    normalized = {path.replace("\\", "/") for path in changed_files}
    if any(path not in CLAIMLESS_0037_31_SCOPE and not path.startswith(CLAIMLESS_0037_31_RUN_ROOT + "/")
           for path in normalized):
        return False
    if not CLAIMLESS_0037_31_EVIDENCE.issubset(normalized):
        return False
    companions = proof.get("companion_sha256")
    companion_paths = CLAIMLESS_0037_31_EVIDENCE - {CLAIMLESS_0037_31_MANIFEST}
    if not isinstance(companions, dict) or set(companions) != companion_paths:
        return False
    for path in companion_paths:
        text = _candidate_blob(candidate_root, candidate, path)
        if "0037-31" not in text or CLAIMLESS_0037_31_ASSIGNMENT not in text:
            return False
        if companions[path] != _candidate_blob_sha256(candidate_root, candidate, path):
            return False
    candidate_info = manifest.get("candidate")
    if not isinstance(candidate_info, dict) or candidate_info.get("root") != CLAIMLESS_0037_31_RUN_ROOT + "/":
        return False
    for key in ("identity", "tree_digest"):
        if not isinstance(candidate_info.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", candidate_info[key]):
            return False
    reports = candidate_info.get("reports")
    report_paths = {
        "migration_report_sha256": CLAIMLESS_0037_31_RUN_ROOT + "/reports/migration-report.json",
        "migration_state_sha256": CLAIMLESS_0037_31_RUN_ROOT + "/reports/migration-state.json",
    }
    if not isinstance(reports, dict) or set(reports) != set(report_paths):
        return False
    return all(reports[key] == _candidate_blob_sha256(candidate_root, candidate, path)
               for key, path in report_paths.items())



def _canonical_promotion_path(relative: object) -> Optional[str]:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        return None
    posix = PurePosixPath(relative)
    if posix.is_absolute() or any(part in {"", ".", ".."} for part in posix.parts):
        return None
    return posix.as_posix() if posix.as_posix() == relative else None


def _candidate_json(candidate_root: Path, candidate: str, relative: str) -> Optional[dict]:
    try:
        value = json.loads(_candidate_blob(candidate_root, candidate, relative))
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _regular_candidate_blob(candidate_root: Path, candidate: str, relative: str) -> bool:
    result = subprocess.run(
        ["git", "ls-tree", candidate, "--", relative], cwd=candidate_root,
        capture_output=True, text=True,
    )
    fields = result.stdout.strip().split(None, 3)
    return result.returncode == 0 and len(fields) == 4 and fields[0] == "100644" and fields[1] == "blob"


def _exact_tree_manifest(
    candidate_root: Path, candidate: str, root: str, expected_tree: str,
    expected_digest: str, expected_count: int,
) -> Optional[Set[str]]:
    tree = subprocess.run(
        ["git", "rev-parse", "--verify", f"{candidate}:{root}"],
        cwd=candidate_root, capture_output=True, text=True,
    )
    listing = subprocess.run(
        ["git", "ls-tree", "-r", candidate, "--", root],
        cwd=candidate_root, capture_output=True,
    )
    if tree.returncode or tree.stdout.strip() != expected_tree or listing.returncode:
        return None
    if hashlib.sha256(listing.stdout).hexdigest() != expected_digest:
        return None
    try:
        lines = listing.stdout.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return None
    paths: Set[str] = set()
    for line in lines:
        try:
            metadata, relative = line.split("\t", 1)
            mode, kind, oid = metadata.split(" ")
        except ValueError:
            return None
        canonical = _canonical_promotion_path(relative)
        if mode != "100644" or kind != "blob" or not re.fullmatch(r"[0-9a-f]{40,64}", oid) or canonical is None:
            return None
        if canonical in paths:
            return None
        paths.add(canonical)
    return paths if len(paths) == expected_count else None


def _promotion_path_envelope_valid(changed: Set[str], declared: object, retained: Set[str]) -> bool:
    if declared != sorted(changed) or not PROMOTION_0037_31_EVIDENCE.issubset(changed):
        return False
    for path in changed:
        if path in PROMOTION_0037_31_FILES or path.startswith(PROMOTION_0037_31_RUN_ROOT + "/"):
            continue
        if path not in retained:
            return False
    return retained.issubset(changed)


def _authority_records_valid(entries: object, records: object) -> bool:
    if not isinstance(entries, list) or len(entries) != 930 or not isinstance(records, list):
        return False
    try:
        expected = [issue_import_legacy.generate_authority_record(entry) for entry in entries]
        canonical = [json.dumps(record, sort_keys=True, separators=(",", ":")) for record in records]
        expected_canonical = [json.dumps(record, sort_keys=True, separators=(",", ":")) for record in expected]
    except (KeyError, TypeError):
        return False
    return len(set(expected_canonical)) == 930 and sorted(canonical) == sorted(expected_canonical)


def _promotion_reports_valid(
    proof: Mapping[str, Any], report: object, state: object, coverage: object,
    import_manifest: object, findings: object, run_records: object,
) -> bool:
    if not all(isinstance(value, dict) for value in (report, state, coverage, import_manifest)):
        return False
    if report.get("run_id") != PROMOTION_0037_31_RUN_ID or state.get("run_id") != PROMOTION_0037_31_RUN_ID:
        return False
    if report.get("status") != "promoted" or state.get("status") != "promoted" or state.get("phase") != "promoted":
        return False
    source = state.get("source")
    if not isinstance(source, dict) or source.get("commit") != CLAIMLESS_0037_31_SOURCE or source.get("tree") != CLAIMLESS_0037_31_SOURCE_TREE or source.get("tree_digest") != proof.get("legacy_tree_digest") or source.get("working_tree_clean") is not True:
        return False
    candidate_info, state_candidate = report.get("candidate"), state.get("candidate")
    if not isinstance(candidate_info, dict) or not isinstance(state_candidate, dict):
        return False
    if candidate_info.get("identity") != proof.get("candidate_identity") or candidate_info.get("observed_tree_digest") != proof.get("candidate_tree_digest") or candidate_info.get("logical_root") != PROMOTION_0037_31_RUN_ROOT + "/":
        return False
    if state_candidate.get("identity") != proof.get("candidate_identity") or state_candidate.get("tree_digest") != proof.get("candidate_tree_digest") or state_candidate.get("promotable") is not True or state_candidate.get("root") != PROMOTION_0037_31_RUN_ROOT + "/":
        return False
    expected_summary = {"blocking": 0, "error": 0, "info": 1, "total": 2, "warning": 1}
    if report.get("finding_summary") != expected_summary or state.get("finding_summary") != expected_summary:
        return False
    disposition_input = report.get("disposition_input")
    if not isinstance(disposition_input, dict) or disposition_input.get("path") != PROMOTION_0037_31_DISPOSITIONS or disposition_input.get("digest") != "sha256:" + proof.get("disposition_manifest_sha256", ""):
        return False
    pairs = coverage.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != 930:
        return False
    identities = {(pair.get("finding_id"), pair.get("rule")) for pair in pairs if isinstance(pair, dict)}
    if len(identities) != 930 or coverage.get("blocking_after_coverage") is not False or coverage.get("closure_json_synthesized") is not False or coverage.get("credit_granted") is not False or coverage.get("disposition_manifest_digest") != "sha256:" + proof.get("disposition_manifest_sha256", ""):
        return False
    if import_manifest.get("disposition_coverage") != coverage or import_manifest.get("finding_summary") != expected_summary:
        return False
    if not isinstance(findings, list) or len(findings) != 931:
        return False
    severities = [entry.get("severity") for entry in findings if isinstance(entry, dict)]
    if severities.count("blocking") != 930 or severities.count("warning") != 1:
        return False
    if not isinstance(run_records, list) or len(run_records) != 1 or run_records[0].get("result") != "covered" or run_records[0].get("source_commit") != CLAIMLESS_0037_31_SOURCE or run_records[0].get("disposition_manifest_digest") != "sha256:" + proof.get("disposition_manifest_sha256", ""):
        return False
    return import_manifest.get("blocking") is False and all(import_manifest.get(key) is False for key in ("approval_emitted", "claim_json_emitted", "closure_json_emitted"))


def _promotion_authority_valid(candidate_root: Path, candidate: str, disposition: dict) -> bool:
    entries = disposition.get("entries")
    if not isinstance(entries, list) or len(entries) != 930:
        return False
    try:
        issue_import_legacy.validate_disposition_document(disposition)
        material = entries[0]["signature_material"]
        records = issue_import_legacy._load_authority_records(material, candidate_root)
    except (KeyError, TypeError, issue_import_legacy.ImportErrorClosed):
        return False
    if any(entry.get("signature_material") != material for entry in entries):
        return False
    return _authority_records_valid(entries, records)


def _promotion_0037_31_proof_uncached(
    candidate_root: Path, candidate: str, relative: str, changed_files: Set[str]
) -> Optional[bool]:
    """Validate DEC-0037-035's separate, exact, closed promotion proof.

    None means no recognized promotion proof. False means a recognized promotion proof
    is invalid and must not fall back to the historical claimless verifier.
    """
    manifest = _candidate_json(candidate_root, candidate, CLAIMLESS_0037_31_MANIFEST)
    if manifest is None:
        return None
    if "promotion" not in manifest:
        return None
    promotion = manifest.get("promotion")
    if not isinstance(promotion, dict) or "policy_proof" not in promotion:
        return False
    if relative not in PROMOTION_0037_31_EVIDENCE | PROMOTION_0037_31_GOVERNANCE:
        return False
    proof = promotion.get("policy_proof")
    expected_keys = {
        "schema", "task_id", "assignment_id", "delegation_offer", "extension_award",
        "authority_decisions", "canonical_base", "overlay_base_candidate",
        "source_commit", "source_tree", "legacy_tree_digest", "run_id", "run_root",
        "authority_sha256", "disposition_manifest_sha256", "candidate_identity",
        "candidate_tree_digest", "reports", "evidence_paths", "changed_paths",
        "companion_sha256", "historical_proof", "retained_r1_evidence",
    }
    if not isinstance(proof, dict) or set(proof) != expected_keys:
        return False
    expected = {
        "schema": "0037-31-promotion-policy-proof@v1", "task_id": "0037-31",
        "assignment_id": PROMOTION_0037_31_ASSIGNMENT,
        "delegation_offer": PROMOTION_0037_31_DELEGATION,
        "extension_award": PROMOTION_0037_31_EXTENSION_AWARD,
        "authority_decisions": ["DEC-0037-034", "DEC-0037-035", "DEC-0037-036"],
        "canonical_base": PROMOTION_0037_31_CANONICAL_BASE,
        "overlay_base_candidate": PROMOTION_0037_31_BASE_CANDIDATE,
        "source_commit": CLAIMLESS_0037_31_SOURCE,
        "source_tree": CLAIMLESS_0037_31_SOURCE_TREE,
        "legacy_tree_digest": "95084ca98c1d84bca6215da5d8763084ebc0f2a90c5a4e9d33a3a38aa96423d8",
        "run_id": PROMOTION_0037_31_RUN_ID,
        "run_root": PROMOTION_0037_31_RUN_ROOT + "/",
        "authority_sha256": "512ae4acec856e74625ea6c6dd3ad5fafd03b901fe29e51af84fc9548001fe55",
        "disposition_manifest_sha256": "82275efcd478fe3518b33ca9f61876077ae8c3e8594f0c6ba6064d6567b079b9",
        "candidate_identity": "f23a0cb083515f964e624658ba2cd89252e9cc16708a1d41e85f8a276a1beb10",
        "candidate_tree_digest": "61bc158665cf84e8c8ba4b394ea15724525d97d97a58dafa4ef61cffd4def3d9",
    }
    if any(proof.get(key) != value for key, value in expected.items()):
        return False
    canonical_delta = subprocess.run(
        ["git", "diff", "--name-only", PROMOTION_0037_31_CANONICAL_BASE, candidate],
        cwd=candidate_root, capture_output=True, text=True,
    )
    if canonical_delta.returncode != 0:
        return False
    canonical_files = {line for line in canonical_delta.stdout.splitlines() if line}
    normalized = [_canonical_promotion_path(path) for path in canonical_files]
    if any(path is None for path in normalized) or len(normalized) != len(set(normalized)):
        return False
    changed = set(normalized)
    if relative in PROMOTION_0037_31_GOVERNANCE:
        if (_candidate_blob_sha256(candidate_root, candidate, relative) !=
                _candidate_blob_sha256(candidate_root, PROMOTION_0037_31_CANONICAL_BASE, relative)):
            return False
    retained = _exact_tree_manifest(
        candidate_root, candidate, PROMOTION_0037_31_RETAINED_RUN_ROOT,
        PROMOTION_0037_31_RETAINED_TREE, PROMOTION_0037_31_RETAINED_MANIFEST_SHA256,
        PROMOTION_0037_31_RETAINED_COUNT,
    )
    if retained is None or not _promotion_path_envelope_valid(changed, proof.get("changed_paths"), retained):
        return False
    if proof.get("evidence_paths") != sorted(PROMOTION_0037_31_EVIDENCE):
        return False
    if proof.get("retained_r1_evidence") != {
        "source_candidate": PROMOTION_0037_31_BASE_CANDIDATE,
        "root": PROMOTION_0037_31_RETAINED_RUN_ROOT + "/",
        "root_tree": PROMOTION_0037_31_RETAINED_TREE,
        "manifest_sha256": PROMOTION_0037_31_RETAINED_MANIFEST_SHA256,
        "entries": PROMOTION_0037_31_RETAINED_COUNT,
        "credit_granted": False,
    }:
        return False
    if not all(_regular_candidate_blob(candidate_root, candidate, path) for path in PROMOTION_0037_31_EVIDENCE):
        return False
    if proof.get("authority_sha256") != _candidate_blob_sha256(candidate_root, candidate, PROMOTION_0037_31_AUTHORITY):
        return False
    if proof.get("disposition_manifest_sha256") != _candidate_blob_sha256(candidate_root, candidate, PROMOTION_0037_31_DISPOSITIONS):
        return False
    reports = proof.get("reports")
    if not isinstance(reports, dict) or set(reports) != set(PROMOTION_0037_31_REPORTS):
        return False
    if any(reports[key] != _candidate_blob_sha256(candidate_root, candidate, path)
           for key, path in PROMOTION_0037_31_REPORTS.items()):
        return False
    companions = proof.get("companion_sha256")
    companion_paths = PROMOTION_0037_31_EVIDENCE - {CLAIMLESS_0037_31_MANIFEST}
    if not isinstance(companions, dict) or set(companions) != companion_paths:
        return False
    if any(companions[path] != _candidate_blob_sha256(candidate_root, candidate, path) for path in companion_paths):
        return False
    for path in companion_paths & {"provenance/migrations/issue-store/0037-31-final-frozen-candidate.md", "docs/dossiers/0037-31-final-frozen-migration-20260904.md"}:
        text = _candidate_blob(candidate_root, candidate, path)
        if PROMOTION_0037_31_ASSIGNMENT not in text or PROMOTION_0037_31_RUN_ID not in text:
            return False
    historical = proof.get("historical_proof")
    if historical != {
        "assignment_id": CLAIMLESS_0037_31_ASSIGNMENT,
        "closure_transaction": CLAIMLESS_0037_31_TRANSACTION,
        "run_id": CLAIMLESS_0037_31_RUN_ID,
        "report_sha256": "9b5660a92d50757dd20f950286c8a24b62978c2dd0ed3250177ba62343d2ea7e",
    }:
        return False
    report = _candidate_json(candidate_root, candidate, PROMOTION_0037_31_REPORTS["migration_report_sha256"])
    state = _candidate_json(candidate_root, candidate, PROMOTION_0037_31_REPORTS["migration_state_sha256"])
    coverage = _candidate_json(candidate_root, candidate, PROMOTION_0037_31_REPORTS["disposition_coverage_sha256"])
    import_manifest = _candidate_json(candidate_root, candidate, PROMOTION_0037_31_REPORTS["import_manifest_sha256"])
    findings_text = _candidate_blob(candidate_root, candidate, PROMOTION_0037_31_REPORTS["findings_sha256"])
    run_text = _candidate_blob(candidate_root, candidate, PROMOTION_0037_31_REPORTS["disposition_runs_sha256"])
    disposition = _candidate_json(candidate_root, candidate, PROMOTION_0037_31_DISPOSITIONS)
    try:
        findings = json.loads(findings_text)
        run_document = json.loads(run_text)
        run_records = [run_document] if isinstance(run_document, dict) else run_document
    except (TypeError, ValueError):
        try:
            run_records = [json.loads(line) for line in run_text.splitlines() if line.strip()]
        except (TypeError, ValueError):
            return False
    if not isinstance(disposition, dict):
        return False
    if not _promotion_reports_valid(proof, report, state, coverage, import_manifest, findings, run_records):
        return False
    return _promotion_authority_valid(candidate_root, candidate, disposition)

_PROMOTION_PROOF_CACHE: Dict[tuple[str, str, tuple[str, ...]], Optional[bool]] = {}

def _promotion_0037_31_proof(
    candidate_root: Path, candidate: str, relative: str, changed_files: Set[str]
) -> Optional[bool]:
    key = (str(candidate_root.resolve()), candidate, tuple(sorted(changed_files)))
    if key not in _PROMOTION_PROOF_CACHE:
        _PROMOTION_PROOF_CACHE[key] = _promotion_0037_31_proof_uncached(
            candidate_root, candidate, relative, changed_files
        )
    result = _PROMOTION_PROOF_CACHE[key]
    if result is True and relative not in PROMOTION_0037_31_EVIDENCE | PROMOTION_0037_31_GOVERNANCE:
        return False
    return result

def frozen_authority_proof(
    candidate_root: Path, candidate: str, relative: str,
    changed_files: Optional[Set[str]] = None,
) -> bool:
    """Require task and assignment binding in the immutable candidate blob."""
    task_match = FROZEN_CUTOVER_TASK_PATTERN.search(relative)
    if task_match is None:
        return False
    text = _candidate_blob(candidate_root, candidate, relative)
    task_id = task_match.group(0)
    if task_id == "0037-31" and changed_files is not None:
        promotion = _promotion_0037_31_proof(candidate_root, candidate, relative, changed_files)
        if promotion is not None:
            return promotion
        if _claimless_0037_31_proof(candidate_root, candidate, relative, changed_files):
            return True
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

    closure_paths: Set[str] = set()
    if epoch == "legacy-frozen" and phase == "frozen" and FROZEN_CLOSURE_MANIFEST in files_to_check:
        try:
            runner_transaction.verify_frozen_closure_delta(candidate_root, base_commit, candidate_commit)
        except runner_transaction.FrozenClosureViolation as error:
            code = getattr(error, "code", "FCD-UNAVAILABLE")
            message = getattr(error, "message", str(error))
            locator = getattr(error, "locator", FROZEN_CLOSURE_MANIFEST)
            violations.append({
                "code": f"POLICY-FROZEN-CLOSURE-{code}",
                "message": f"Scoped frozen closure proof rejected: {message}",
                "locator": locator,
            })
        else:
            closure_paths = set(runner_transaction.FROZEN_CLOSURE_MUTATION_PATHS)

    for rel in files_to_check:
        norm = rel.replace("\\", "/")

        if epoch == "legacy-frozen" and phase == "frozen":
            path_class = classify_frozen_path(norm)
            if norm in closure_paths:
                pass
            elif path_class == "legacy-backlog":
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
            elif path_class in {"cutover-record", "cutover-evidence"} and not frozen_authority_proof(
                candidate_root, candidate_commit, norm, set(files_to_check)
            ):
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
