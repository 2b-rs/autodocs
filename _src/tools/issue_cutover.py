#!/usr/bin/env python3
"""Non-operative, fail-closed core for the Feature 0037 cutover transaction.

Inspection, preparation, and verification are usable.  Every production effect
command is intentionally disabled until a later governance normalization makes
the authority boundary unambiguous.  The only ref-writing primitive is an
explicitly test-only helper for hermetic disposable repositories.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

MANIFEST_SCHEMA = "cutover-transaction-manifest@v1"
LEDGER_SCHEMA = "cutover-control-ledger@v2"
RESULT_SCHEMA = "issue-cutover-result@v1"
BLOCKED_EFFECT_CODE = "CUTOVER-EFFECTS-NOT-ACTIVATED"
ZERO_OID = "0" * 40
OID_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TX_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{7,127}$")
REF_RE = re.compile(r"^refs/[A-Za-z0-9][A-Za-z0-9._/-]*$")
EFFECT_COMMANDS = ("freeze", "switch", "reference", "rollback", "activate")
EPOCHS = (
    "legacy_active", "legacy_frozen", "prepared", "issue_store_active",
    "post_cutover_audit", "legacy_restored", "point_of_no_return",
    "write_frozen_repair",
)
WRITE_AUTHORITIES = ("legacy", "issue-store", "provenance-only", "none")
EXPECTED_AUTHORITY = {
    "legacy_active": "legacy",
    "legacy_frozen": "provenance-only",
    "prepared": "provenance-only",
    "issue_store_active": "issue-store",
    "post_cutover_audit": "provenance-only",
    "legacy_restored": "legacy",
    "point_of_no_return": "none",
    "write_frozen_repair": "provenance-only",
}
LEGAL_TRANSITIONS = {
    "legacy_active": frozenset({"legacy_active", "legacy_frozen"}),
    "legacy_frozen": frozenset({"legacy_frozen", "prepared", "legacy_restored"}),
    "prepared": frozenset({"prepared", "issue_store_active", "legacy_restored"}),
    "issue_store_active": frozenset({"issue_store_active", "post_cutover_audit"}),
    "post_cutover_audit": frozenset({"post_cutover_audit", "legacy_restored", "point_of_no_return"}),
    "legacy_restored": frozenset({"legacy_restored", "legacy_frozen"}),
    "point_of_no_return": frozenset({"point_of_no_return", "write_frozen_repair"}),
    "write_frozen_repair": frozenset({"write_frozen_repair", "issue_store_active"}),
}
REQUIRED_ROLES = frozenset({"control_actor", "preparer", "auditor", "approver", "integrator"})
ADAPTER_EXECUTABLES = {
    "importer": "_src/tools/issue_import_legacy.py",
    "regenerator": "_src/tools/issue_regenerate.py",
}
TOP_KEYS = frozenset({
    "schema", "transaction_id", "source", "candidate", "authority_snapshot",
    "identities", "refs", "roles", "signatures", "approvals", "quiescence",
    "ledger", "adapters", "outputs", "findings", "cas",
})


class CutoverError(ValueError):
    """Stable fail-closed contract error."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest_value(value: Any) -> str:
    return digest_bytes(canonical_json(value).encode("utf-8"))


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise CutoverError(code, message)


def _object(value: Any, keys: set[str] | frozenset[str], required: set[str] | frozenset[str], where: str) -> dict[str, Any]:
    _require(isinstance(value, dict), "CUTOVER-MALFORMED", f"{where} must be an object")
    unknown = set(value) - set(keys)
    missing = set(required) - set(value)
    _require(not unknown, "CUTOVER-UNKNOWN-FIELD", f"{where} has unknown fields: {sorted(unknown)}")
    _require(not missing, "CUTOVER-MISSING-FIELD", f"{where} lacks fields: {sorted(missing)}")
    return value


def _string(value: Any, where: str) -> str:
    _require(isinstance(value, str) and bool(value), "CUTOVER-MALFORMED", f"{where} must be a non-empty string")
    return value


def _oid(value: Any, where: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    _require(isinstance(value, str) and OID_RE.fullmatch(value) is not None, "CUTOVER-OID", f"{where} must be a lowercase 40-hex OID")
    return value


def _digest(value: Any, where: str) -> str:
    _require(isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None, "CUTOVER-DIGEST", f"{where} must be sha256:<64 lowercase hex>")
    return value


def _relative(value: Any, where: str) -> str:
    text = _string(value, where)
    path = PurePosixPath(text)
    _require(not path.is_absolute() and path.as_posix() == text and all(part not in ("", ".", "..") for part in path.parts), "CUTOVER-PATH", f"{where} must be a canonical relative POSIX path")
    return text


def _absolute(path: Path, where: str, *, must_exist: bool = True) -> Path:
    _require(path.is_absolute(), "CUTOVER-ABSOLUTE-PATH", f"{where} must be absolute")
    _require(".." not in path.parts, "CUTOVER-ALIAS", f"{where} contains an ambiguous alias")
    resolved = path.resolve(strict=False)
    _require(resolved == path, "CUTOVER-ALIAS", f"{where} must be canonical: {path}")
    if must_exist:
        _require(path.exists(), "CUTOVER-MISSING-PATH", f"{where} does not exist: {path}")
    return path


def _git(repo: Path, *args: str, check: bool = True, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args], input=input_bytes,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check,
        )
    except OSError as exc:
        raise CutoverError("CUTOVER-GIT-MISSING", f"cannot execute git: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", "replace").strip()
        raise CutoverError("CUTOVER-GIT", f"git {' '.join(args)} failed: {detail}") from exc


def resolve_ref(repo: Path, ref: str) -> str | None:
    result = _git(repo, "rev-parse", "--verify", "--quiet", ref, check=False)
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise CutoverError("CUTOVER-GIT", result.stderr.decode("utf-8", "replace").strip())
    oid = result.stdout.decode("ascii").strip()
    _oid(oid, f"resolved {ref}")
    return oid


def tree_digest(root: Path, *, exclude: frozenset[str] = frozenset()) -> str:
    entries: list[dict[str, str]] = []
    if root.exists():
        for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
            _require(not path.is_symlink(), "CUTOVER-SYMLINK", f"prepared output contains symlink: {path}")
            relative = path.relative_to(root).as_posix()
            if path.is_file() and relative not in exclude:
                entries.append({"path": relative, "digest": digest_bytes(path.read_bytes())})
    return digest_value(entries)


def read_manifest(path: Path) -> dict[str, Any]:
    _absolute(path, "--manifest")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CutoverError("CUTOVER-MANIFEST-READ", f"cannot read manifest: {exc}") from exc
    _require(raw == canonical_json(value).encode("utf-8"), "CUTOVER-NONCANONICAL", "manifest bytes are not canonical JSON")
    validate_manifest(value)
    return value


def validate_manifest(value: Any) -> dict[str, Any]:
    manifest = _object(value, TOP_KEYS, TOP_KEYS, "manifest")
    _require(manifest["schema"] == MANIFEST_SCHEMA, "CUTOVER-SCHEMA", "unsupported transaction manifest schema")
    _require(isinstance(manifest["transaction_id"], str) and TX_RE.fullmatch(manifest["transaction_id"]) is not None, "CUTOVER-TRANSACTION-ID", "invalid transaction_id")

    source = _object(manifest["source"], {"ref", "oid", "digest"}, {"ref", "oid", "digest"}, "source")
    source_ref = _string(source["ref"], "source.ref")
    _require(REF_RE.fullmatch(source_ref) is not None, "CUTOVER-REF", "invalid source.ref")
    _oid(source["oid"], "source.oid")
    _digest(source["digest"], "source.digest")
    candidate = _object(manifest["candidate"], {"ref", "oid", "digest", "prepared_patch_digest"}, {"ref", "oid", "digest", "prepared_patch_digest"}, "candidate")
    candidate_ref = _string(candidate["ref"], "candidate.ref")
    _require(REF_RE.fullmatch(candidate_ref) is not None, "CUTOVER-REF", "invalid candidate.ref")
    _oid(candidate["oid"], "candidate.oid")
    _digest(candidate["digest"], "candidate.digest")
    _digest(candidate["prepared_patch_digest"], "candidate.prepared_patch_digest")

    snapshot = _object(
        manifest["authority_snapshot"],
        {"epoch", "allowed_write_authority", "issue_store_frozen", "authorities", "selector_path", "selector_digest", "token_digest"},
        {"epoch", "allowed_write_authority", "issue_store_frozen", "authorities", "selector_path", "selector_digest", "token_digest"},
        "authority_snapshot",
    )
    epoch = snapshot["epoch"]
    _require(epoch in EPOCHS, "CUTOVER-EPOCH", f"unknown epoch {epoch!r}")
    _require(snapshot["allowed_write_authority"] in WRITE_AUTHORITIES, "CUTOVER-AUTHORITY", "unknown allowed_write_authority")
    _require(snapshot["allowed_write_authority"] == EXPECTED_AUTHORITY[epoch], "CUTOVER-DUAL-AUTHORITY", "epoch/write-authority matrix mismatch")
    frozen_expected = epoch in {"legacy_frozen", "prepared", "post_cutover_audit", "point_of_no_return", "write_frozen_repair"}
    _require(isinstance(snapshot["issue_store_frozen"], bool) and snapshot["issue_store_frozen"] == frozen_expected, "CUTOVER-FROZEN-STATE", "issue_store_frozen does not match epoch semantics")
    authorities = snapshot["authorities"]
    _require(isinstance(authorities, list) and len(authorities) == 1 and isinstance(authorities[0], str) and bool(authorities[0]), "CUTOVER-EXACTLY-ONE-AUTHORITY", "exactly one authority is required")
    _relative(snapshot["selector_path"], "authority_snapshot.selector_path")
    _digest(snapshot["selector_digest"], "authority_snapshot.selector_digest")
    snapshot_payload = {key: value for key, value in snapshot.items() if key != "token_digest"}
    _require(snapshot["token_digest"] == digest_value(snapshot_payload), "CUTOVER-AUTHORITY-TOKEN", "authority snapshot token digest mismatch")

    identities = _object(manifest["identities"], {"tools", "schemas"}, {"tools", "schemas"}, "identities")
    for group in ("tools", "schemas"):
        values = identities[group]
        _require(isinstance(values, list) and bool(values), "CUTOVER-IDENTITY", f"identities.{group} must be non-empty")
        seen: set[str] = set()
        for index, item in enumerate(values):
            record = _object(item, {"path", "digest"}, {"path", "digest"}, f"identities.{group}[{index}]")
            path = _relative(record["path"], f"identities.{group}[{index}].path")
            _require(path not in seen, "CUTOVER-IDENTITY", f"duplicate identity path {path}")
            seen.add(path)
            _digest(record["digest"], f"identity {path}")

    refs = manifest["refs"]
    _require(isinstance(refs, list) and bool(refs), "CUTOVER-REF", "refs must be non-empty")
    declared: set[str] = set()
    for index, item in enumerate(refs):
        record = _object(item, {"name", "expected_oid", "target_oid"}, {"name", "expected_oid", "target_oid"}, f"refs[{index}]")
        name = _string(record["name"], f"refs[{index}].name")
        _require(REF_RE.fullmatch(name) is not None, "CUTOVER-REF", f"invalid ref {name!r}")
        _require(name != "refs/heads/main", "CUTOVER-MAIN-REF", "refs/heads/main is never a cutover primitive target")
        _require(name not in declared, "CUTOVER-EXTRA-REF", f"duplicate ref declaration {name}")
        declared.add(name)
        _oid(record["expected_oid"], f"refs[{index}].expected_oid", nullable=True)
        _oid(record["target_oid"], f"refs[{index}].target_oid", nullable=True)

    roles = manifest["roles"]
    _require(isinstance(roles, dict), "CUTOVER-ROLE", "roles must be an object")
    _require(set(roles) == REQUIRED_ROLES, "CUTOVER-ROLE", f"roles must be exactly {sorted(REQUIRED_ROLES)}")
    authority = authorities[0]
    for role, actor in roles.items():
        _require(actor == authority, "CUTOVER-WRONG-ROLE", f"{role} is not bound to the sole authority")

    signatures = manifest["signatures"]
    _require(isinstance(signatures, list), "CUTOVER-SIGNATURE", "signatures must be an array")
    signed_roles: set[str] = set()
    for index, item in enumerate(signatures):
        record = _object(item, {"role", "actor", "policy", "payload_digest", "verified"}, {"role", "actor", "policy", "payload_digest", "verified"}, f"signatures[{index}]")
        role = record["role"]
        _require(role in REQUIRED_ROLES and role not in signed_roles, "CUTOVER-SIGNATURE", "signature roles must be unique and declared")
        signed_roles.add(role)
        _require(record["actor"] == roles[role], "CUTOVER-WRONG-SIGNATURE-ROLE", "signature actor/role mismatch")
        _require(record["policy"] == "single-authority-self-attestation@v1", "CUTOVER-WRONG-SIGNATURE-POLICY", "unsupported signature policy")
        _digest(record["payload_digest"], "signature.payload_digest")
        _require(record["verified"] is True, "CUTOVER-SIGNATURE", "signature must be verified")
    _require(signed_roles == REQUIRED_ROLES, "CUTOVER-SIGNATURE", "every role requires one signature")

    approvals = manifest["approvals"]
    _require(isinstance(approvals, list) and len(approvals) == 1, "CUTOVER-APPROVAL-TOPOLOGY", "exactly one approval is required")
    approval = _object(approvals[0], {"ref", "base_oid", "role", "actor", "package_digest", "signature_verified"}, {"ref", "base_oid", "role", "actor", "package_digest", "signature_verified"}, "approvals[0]")
    _require(isinstance(approval["ref"], str) and approval["ref"].startswith("refs/autodocs/approval/"), "CUTOVER-APPROVAL-REF", "approval ref prefix is not normalized")
    _oid(approval["base_oid"], "approval.base_oid")
    _require(approval["role"] == "approver" and approval["actor"] == roles["approver"], "CUTOVER-WRONG-APPROVAL", "approval role/actor mismatch")
    _digest(approval["package_digest"], "approval.package_digest")
    _require(approval["package_digest"] == manifest["candidate"]["prepared_patch_digest"], "CUTOVER-WRONG-APPROVAL", "approval is not bound to the prepared patch digest")
    _require(approval["signature_verified"] is True, "CUTOVER-WRONG-APPROVAL", "approval signature is not verified")

    quiescence = _object(manifest["quiescence"], {"clients", "jobs", "claims", "observed_at_oid", "digest"}, {"clients", "jobs", "claims", "observed_at_oid", "digest"}, "quiescence")
    for field in ("clients", "jobs", "claims"):
        _require(isinstance(quiescence[field], list) and not quiescence[field], "CUTOVER-NOT-QUIESCENT", f"quiescence.{field} must be empty")
    _oid(quiescence["observed_at_oid"], "quiescence.observed_at_oid")
    q_payload = {key: quiescence[key] for key in ("clients", "jobs", "claims", "observed_at_oid")}
    _require(quiescence["digest"] == digest_value(q_payload), "CUTOVER-QUIESCENCE-DIGEST", "quiescence digest mismatch")

    validate_ledger(manifest["ledger"], manifest["transaction_id"])

    adapters = manifest["adapters"]
    _require(isinstance(adapters, list), "CUTOVER-ADAPTER", "adapters must be an array")
    adapter_ids: set[str] = set()
    for index, item in enumerate(adapters):
        record = _object(item, {"id", "executable", "argv", "output_subdir"}, {"id", "executable", "argv", "output_subdir"}, f"adapters[{index}]")
        adapter_id = record["id"]
        _require(adapter_id in ADAPTER_EXECUTABLES and adapter_id not in adapter_ids, "CUTOVER-ADAPTER", "unknown or duplicate adapter")
        adapter_ids.add(adapter_id)
        _require(record["executable"] == ADAPTER_EXECUTABLES[adapter_id], "CUTOVER-ADAPTER", "adapter executable is not the integrated tool")
        _require(isinstance(record["argv"], list) and all(isinstance(part, str) and part and "\x00" not in part for part in record["argv"]), "CUTOVER-ADAPTER", "adapter argv must be a literal string array")
        _relative(record["output_subdir"], "adapter.output_subdir")
    _require(adapter_ids == set(ADAPTER_EXECUTABLES), "CUTOVER-ADAPTER", "importer and regenerator adapters are both required")

    outputs = manifest["outputs"]
    _require(isinstance(outputs, list), "CUTOVER-OUTPUT", "outputs must be an array")
    output_paths: set[str] = set()
    for index, item in enumerate(outputs):
        record = _object(item, {"path", "digest"}, {"path", "digest"}, f"outputs[{index}]")
        path = _relative(record["path"], "output.path")
        _require(path not in output_paths, "CUTOVER-OUTPUT", f"duplicate output {path}")
        output_paths.add(path)
        _digest(record["digest"], "output.digest")

    findings = manifest["findings"]
    _require(isinstance(findings, list), "CUTOVER-FINDING", "findings must be an array")
    for index, item in enumerate(findings):
        finding = _object(item, {"code", "severity", "path", "message"}, {"code", "severity", "path", "message"}, f"findings[{index}]")
        _string(finding["code"], "finding.code")
        _require(finding["severity"] in {"info", "warning", "blocking"}, "CUTOVER-FINDING", "finding severity is invalid")
        _string(finding["path"], "finding.path")
        _string(finding["message"], "finding.message")

    cas = _object(manifest["cas"], {"disposable_test_repo", "declared_refs"}, {"disposable_test_repo", "declared_refs"}, "cas")
    _require(isinstance(cas["disposable_test_repo"], bool), "CUTOVER-CAS", "cas.disposable_test_repo must be boolean")
    _require(cas["declared_refs"] == sorted(declared), "CUTOVER-EXTRA-REF", "CAS declared refs differ from ref expectations")
    return manifest


def validate_ledger(events: Any, transaction_id: str) -> None:
    _require(isinstance(events, list) and bool(events), "CUTOVER-LEDGER", "ledger must be a non-empty array")
    previous_digest: str | None = None
    previous_epoch: str | None = None
    for index, item in enumerate(events):
        event = _object(
            item,
            {"schema", "transaction_id", "sequence", "event_kind", "from_epoch", "to_epoch", "allowed_write_authority", "issue_store_frozen", "previous_event_digest", "payload_digest", "actor", "role", "signature_policy", "signature_verified", "event_digest"},
            {"schema", "transaction_id", "sequence", "event_kind", "from_epoch", "to_epoch", "allowed_write_authority", "issue_store_frozen", "previous_event_digest", "payload_digest", "actor", "role", "signature_policy", "signature_verified", "event_digest"},
            f"ledger[{index}]",
        )
        _require(event["schema"] == LEDGER_SCHEMA, "CUTOVER-LEDGER-SCHEMA", "unsupported ledger schema")
        _require(event["transaction_id"] == transaction_id, "CUTOVER-TRANSACTION-MISMATCH", "ledger transaction_id mismatch")
        _require(event["sequence"] == index + 1, "CUTOVER-SEQUENCE", "ledger sequence must be contiguous from one")
        _require(event["from_epoch"] in EPOCHS and event["to_epoch"] in EPOCHS, "CUTOVER-EPOCH", "ledger epoch is unknown")
        _require(event["to_epoch"] in LEGAL_TRANSITIONS[event["from_epoch"]], "CUTOVER-ILLEGAL-TRANSITION", f"illegal transition {event['from_epoch']}->{event['to_epoch']}")
        if previous_epoch is not None:
            _require(event["from_epoch"] == previous_epoch, "CUTOVER-EVENT-CHAIN", "ledger epoch chain is discontinuous")
        _require(event["previous_event_digest"] == previous_digest, "CUTOVER-EVENT-CHAIN", "previous event digest mismatch")
        _require(event["allowed_write_authority"] == EXPECTED_AUTHORITY[event["to_epoch"]], "CUTOVER-DUAL-AUTHORITY", "ledger authority matrix mismatch")
        frozen = event["to_epoch"] in {"legacy_frozen", "prepared", "post_cutover_audit", "point_of_no_return", "write_frozen_repair"}
        _require(event["issue_store_frozen"] is frozen, "CUTOVER-FROZEN-WRITE", "ledger frozen state mismatch")
        _digest(event["payload_digest"], "ledger.payload_digest")
        _require(event["role"] in REQUIRED_ROLES and isinstance(event["actor"], str) and bool(event["actor"]), "CUTOVER-WRONG-CONTROL-ROLE", "ledger role/actor invalid")
        _require(event["signature_policy"] == "single-authority-self-attestation@v1" and event["signature_verified"] is True, "CUTOVER-WRONG-SIGNATURE-POLICY", "ledger signature policy/verification invalid")
        payload = {key: value for key, value in event.items() if key != "event_digest"}
        expected = digest_value(payload)
        _require(event["event_digest"] == expected, "CUTOVER-EVENT-DIGEST", "ledger event digest mismatch")
        previous_digest = expected
        previous_epoch = event["to_epoch"]


def _identity_findings(repo: Path, manifest: Mapping[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for group in ("tools", "schemas"):
        for identity in manifest["identities"][group]:
            path = repo / identity["path"]
            if not path.is_file():
                findings.append({"code": "CUTOVER-MISSING-IDENTITY", "path": identity["path"], "message": "identity path is missing"})
            elif digest_bytes(path.read_bytes()) != identity["digest"]:
                findings.append({"code": "CUTOVER-IDENTITY-DRIFT", "path": identity["path"], "message": "identity digest differs"})
    selector = repo / manifest["authority_snapshot"]["selector_path"]
    if not selector.is_file() or digest_bytes(selector.read_bytes()) != manifest["authority_snapshot"]["selector_digest"]:
        findings.append({"code": "CUTOVER-SELECTOR-MISMATCH", "path": manifest["authority_snapshot"]["selector_path"], "message": "selector identity differs"})
    return findings


def inspect(repo: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    findings = _identity_findings(repo, manifest)
    observed_refs: list[dict[str, Any]] = []
    for record in manifest["refs"]:
        observed = resolve_ref(repo, record["name"])
        observed_refs.append({"name": record["name"], "expected_oid": record["expected_oid"], "observed_oid": observed})
        if observed != record["expected_oid"]:
            findings.append({"code": "CUTOVER-STALE-OID", "path": record["name"], "message": "observed ref differs from expected OID"})
    source_observed = resolve_ref(repo, manifest["source"]["ref"])
    if source_observed != manifest["source"]["oid"]:
        findings.append({"code": "CUTOVER-SOURCE-DRIFT", "path": manifest["source"]["ref"], "message": "source ref differs from pinned OID"})
    candidate_observed = resolve_ref(repo, manifest["candidate"]["ref"])
    if candidate_observed != manifest["candidate"]["oid"]:
        findings.append({"code": "CUTOVER-CANDIDATE-DRIFT", "path": manifest["candidate"]["ref"], "message": "candidate ref differs from pinned OID"})
    return {
        "schema": RESULT_SCHEMA,
        "command": "inspect",
        "status": "PASS" if not findings else "BLOCKED",
        "transaction_id": manifest["transaction_id"],
        "manifest_digest": digest_value(manifest),
        "authority": manifest["authority_snapshot"],
        "refs": observed_refs,
        "findings": findings,
        "mutation": "none",
    }


def _authorize_output(repo: Path, output: Path) -> Path:
    _absolute(output, "--output-root", must_exist=False)
    parent = output.parent
    _require(parent.is_dir(), "CUTOVER-OUTPUT", "output parent must exist")
    _require(output.name.startswith("cutover-"), "CUTOVER-OUTPUT", "output basename must start with cutover-")
    resolved_repo = repo.resolve()
    try:
        output.relative_to(resolved_repo)
        raise CutoverError("CUTOVER-LIVE-WRITE", "output root must be outside the repository")
    except ValueError:
        pass
    try:
        resolved_repo.relative_to(output)
        raise CutoverError("CUTOVER-LIVE-WRITE", "output root cannot contain the repository")
    except ValueError:
        pass
    temporary_roots = (Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve())
    _require(any(output != root and output.is_relative_to(root) for root in temporary_roots), "CUTOVER-OUTPUT", "output root must be under a temporary root")
    return output


def _run_adapters(repo: Path, staging: Path, manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    summaries = []
    tool_digests = {item["path"]: item["digest"] for item in manifest["identities"]["tools"]}
    for adapter in manifest["adapters"]:
        executable = repo / adapter["executable"]
        _require(executable.is_file(), "CUTOVER-MISSING-EXECUTABLE", f"adapter executable missing: {adapter['executable']}")
        _require(tool_digests.get(adapter["executable"]) == digest_bytes(executable.read_bytes()), "CUTOVER-IDENTITY-DRIFT", f"adapter executable identity mismatch: {adapter['executable']}")
        destination = staging / adapter["output_subdir"]
        destination.mkdir(parents=True, exist_ok=False)
        argv = [part.replace("{output}", str(destination)).replace("{repo}", str(repo)) for part in adapter["argv"]]
        _require(all("{" not in part and "}" not in part for part in argv), "CUTOVER-ADAPTER", "unknown adapter placeholder")
        result = subprocess.run([sys.executable, str(executable), *argv], cwd=repo, env={"PATH": os.environ.get("PATH", "")}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        _require(result.returncode == 0, "CUTOVER-ADAPTER-FAILED", f"adapter {adapter['id']} failed with {result.returncode}: {result.stderr.decode('utf-8', 'replace')[:1000]}")
        summaries.append({"id": adapter["id"], "output_subdir": adapter["output_subdir"], "tree_digest": tree_digest(destination), "stdout_digest": digest_bytes(result.stdout)})
    return summaries


def prepare(repo: Path, output: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    output = _authorize_output(repo, output)
    fingerprint = digest_value(manifest)
    receipt_path = output / "preparation.json"
    if output.exists():
        _require(receipt_path.is_file(), "CUTOVER-RETRY-CONFLICT", "existing output lacks preparation receipt")
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CutoverError("CUTOVER-RETRY-CONFLICT", f"existing receipt unreadable: {exc}") from exc
        _require(receipt.get("transaction_id") == manifest["transaction_id"] and receipt.get("manifest_digest") == fingerprint, "CUTOVER-TRANSACTION-REUSE", "transaction ID reused with changed input")
        _require(receipt.get("prepared_tree_digest") == tree_digest(output, exclude=frozenset({"preparation.json"})), "CUTOVER-PREPARED-DRIFT", "prepared output changed after promotion")
        return {**receipt, "command": "prepare", "status": "PASS", "idempotent": True, "mutation": "none"}
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        summaries = _run_adapters(repo, staging, manifest)
        for expected in manifest["outputs"]:
            path = staging / expected["path"]
            _require(path.is_file(), "CUTOVER-OUTPUT-MISSING", f"prepared output missing: {expected['path']}")
            _require(digest_bytes(path.read_bytes()) == expected["digest"], "CUTOVER-OUTPUT-DRIFT", f"prepared output digest mismatch: {expected['path']}")
        receipt = {
            "schema": "cutover-preparation@v1",
            "transaction_id": manifest["transaction_id"],
            "manifest_digest": fingerprint,
            "source": manifest["source"],
            "candidate": manifest["candidate"],
            "adapters": summaries,
            "prepared_tree_digest": tree_digest(staging),
            "mutation": "disposable-output-only",
        }
        receipt_path_staging = staging / "preparation.json"
        receipt_path_staging.write_text(canonical_json(receipt), encoding="utf-8")
        os.rename(staging, output)
        return {**receipt, "command": "prepare", "status": "PASS", "idempotent": False}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def verify(repo: Path, manifest: Mapping[str, Any], output: Path | None = None) -> dict[str, Any]:
    result = inspect(repo, manifest)
    findings = list(result["findings"])
    if output is not None:
        _absolute(output, "--output-root")
        receipt = output / "preparation.json"
        if not receipt.is_file():
            findings.append({"code": "CUTOVER-MISSING-PREPARATION", "path": str(receipt), "message": "preparation receipt missing"})
        else:
            value = json.loads(receipt.read_text(encoding="utf-8"))
            if value.get("manifest_digest") != digest_value(manifest):
                findings.append({"code": "CUTOVER-PREPARED-DRIFT", "path": str(receipt), "message": "receipt manifest identity differs"})
            for expected in manifest["outputs"]:
                path = output / expected["path"]
                if not path.is_file() or digest_bytes(path.read_bytes()) != expected["digest"]:
                    findings.append({"code": "CUTOVER-OUTPUT-DRIFT", "path": expected["path"], "message": "retained output identity differs"})
    return {
        "schema": RESULT_SCHEMA, "command": "verify", "status": "PASS" if not findings else "BLOCKED",
        "transaction_id": manifest["transaction_id"], "manifest_digest": digest_value(manifest),
        "checks": {"authority_count": 1, "ledger_events": len(manifest["ledger"]), "declared_refs": len(manifest["refs"]), "signatures": len(manifest["signatures"])},
        "findings": findings, "mutation": "none",
    }


def plan_cas(expectations: Sequence[Mapping[str, Any]], declared_refs: Sequence[str]) -> bytes:
    declared = set(declared_refs)
    _require(len(declared) == len(declared_refs), "CUTOVER-EXTRA-REF", "declared refs contain duplicates")
    _require(bool(expectations), "CUTOVER-CAS", "CAS requires at least one ref")
    chunks: list[bytes] = [b"start\0"]
    seen: set[str] = set()
    for item in expectations:
        name = item.get("name")
        expected = item.get("expected_oid")
        target = item.get("target_oid")
        _require(isinstance(name, str) and REF_RE.fullmatch(name) is not None, "CUTOVER-REF", "invalid CAS ref")
        assert isinstance(name, str)
        _require(name != "refs/heads/main", "CUTOVER-MAIN-REF", "refs/heads/main is forbidden")
        _require(name in declared and name not in seen, "CUTOVER-EXTRA-REF", f"undeclared or duplicate CAS ref {name}")
        seen.add(name)
        _oid(expected, "CAS expected_oid", nullable=True)
        _oid(target, "CAS target_oid", nullable=True)
        old = expected or ZERO_OID
        if target is None:
            chunks.extend([f"delete {name}\0".encode(), f"{old}\0".encode()])
        else:
            chunks.extend([f"update {name}\0".encode(), f"{target}\0".encode(), f"{old}\0".encode()])
    _require(seen == declared, "CUTOVER-EXTRA-REF", "CAS plan does not cover exactly the declared refs")
    chunks.extend([b"prepare\0", b"commit\0"])
    return b"".join(chunks)


def execute_disposable_cas(repo: Path, expectations: Sequence[Mapping[str, Any]], declared_refs: Sequence[str], *, dry_run: bool) -> dict[str, Any]:
    repo = _absolute(repo, "CAS repo")
    _require((repo / ".git").is_dir(), "CUTOVER-CAS-NOT-DISPOSABLE", "CAS repo must be a standalone disposable Git repository")
    marker = repo / ".issue-cutover-disposable-test-repo"
    _require(marker.is_file() and marker.read_text(encoding="utf-8") == "issue-cutover-disposable-test-repo@v1\n", "CUTOVER-CAS-NOT-DISPOSABLE", "missing disposable test repository marker")
    transaction = plan_cas(expectations, declared_refs)
    before = {name: resolve_ref(repo, name) for name in declared_refs}
    if dry_run:
        return {"schema": "cutover-cas-result@v1", "status": "PLANNED", "dry_run": True, "before": before, "after": before, "transaction_digest": digest_bytes(transaction), "mutation": "none"}
    result = _git(repo, "update-ref", "--stdin", "-z", check=False, input_bytes=transaction)
    after = {name: resolve_ref(repo, name) for name in declared_refs}
    if result.returncode != 0:
        _require(after == before, "CUTOVER-CAS-PARTIAL", "failed CAS changed at least one ref")
        raise CutoverError("CUTOVER-CAS-COMPETITOR", result.stderr.decode("utf-8", "replace").strip())
    return {"schema": "cutover-cas-result@v1", "status": "APPLIED", "dry_run": False, "before": before, "after": after, "transaction_digest": digest_bytes(transaction), "mutation": "disposable-refs-only"}


def blocked_effect(command: str, transaction_id: str | None = None) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA, "command": command, "status": "BLOCKED",
        "code": BLOCKED_EFFECT_CODE, "transaction_id": transaction_id,
        "message": "effect activation awaits governance normalization; no override exists",
        "mutation": "none",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "prepare", "verify", *EFFECT_COMMANDS):
        child = subparsers.add_parser(command)
        child.add_argument("--repo", required=True)
        child.add_argument("--manifest", required=True)
        if command in ("prepare", "verify"):
            child.add_argument("--output-root", required=command == "prepare")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    if args.command in EFFECT_COMMANDS:
        # Parse paths, but deliberately do not read them: effects stay disabled even
        # for malformed or missing inputs and cannot acquire a validation side effect.
        result = blocked_effect(args.command)
        sys.stdout.write(canonical_json(result))
        return 2
    try:
        repo = _absolute(Path(args.repo), "--repo")
        _require((repo / ".git").exists(), "CUTOVER-REPO", "--repo is not a Git worktree")
        manifest = read_manifest(Path(args.manifest))
        if args.command == "inspect":
            result = inspect(repo, manifest)
        elif args.command == "prepare":
            result = prepare(repo, Path(args.output_root), manifest)
        else:
            result = verify(repo, manifest, Path(args.output_root) if args.output_root else None)
        sys.stdout.write(canonical_json(result))
        return 0 if result["status"] == "PASS" else 2
    except CutoverError as exc:
        sys.stdout.write(canonical_json({"schema": RESULT_SCHEMA, "command": args.command, "status": "BLOCKED", "code": exc.code, "message": exc.message, "mutation": "none"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
