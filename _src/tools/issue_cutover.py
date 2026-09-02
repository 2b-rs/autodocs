#!/usr/bin/env python3
"""Non-operative, fail-closed core for the Feature 0037 cutover transaction."""
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
    "legacy_active": "legacy", "legacy_frozen": "provenance-only",
    "prepared": "provenance-only", "issue_store_active": "issue-store",
    "post_cutover_audit": "provenance-only", "legacy_restored": "legacy",
    "point_of_no_return": "none", "write_frozen_repair": "provenance-only",
}
FROZEN_EPOCHS = frozenset({
    "legacy_frozen", "prepared", "post_cutover_audit", "point_of_no_return",
    "write_frozen_repair",
})
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
EVENT_TRANSITIONS = {
    "inspect": frozenset((epoch, epoch) for epoch in EPOCHS),
    "freeze": frozenset({("legacy_active", "legacy_frozen"), ("legacy_restored", "legacy_frozen")}),
    "prepare": frozenset({("legacy_frozen", "prepared")}),
    "switch": frozenset({("prepared", "issue_store_active")}),
    "audit": frozenset({("issue_store_active", "post_cutover_audit")}),
    "rollback": frozenset({("legacy_frozen", "legacy_restored"), ("prepared", "legacy_restored"), ("post_cutover_audit", "legacy_restored")}),
    "point-of-no-return": frozenset({("post_cutover_audit", "point_of_no_return")}),
    "repair": frozenset({("point_of_no_return", "write_frozen_repair"), ("write_frozen_repair", "issue_store_active")}),
    "activation-blocked": frozenset((epoch, epoch) for epoch in EPOCHS),
}
EVENT_ROLES = {
    "inspect": "control_actor", "freeze": "control_actor", "prepare": "preparer",
    "switch": "integrator", "audit": "auditor", "rollback": "integrator",
    "point-of-no-return": "approver", "repair": "integrator",
    "activation-blocked": "control_actor",
}
REQUIRED_ROLES = frozenset({"control_actor", "preparer", "auditor", "approver", "integrator"})
ADAPTER_EXECUTABLES = {
    "importer": "_src/tools/issue_import_legacy.py",
    "regenerator": "_src/tools/issue_regenerate.py",
}
ADAPTER_CHILDREN = {"importer": "imported", "regenerator": "regenerated"}
TOP_KEYS = frozenset({
    "schema", "transaction_id", "source", "candidate", "prepared_patch",
    "authority_snapshot", "identities", "refs", "roles", "signatures",
    "approvals", "quiescence", "ledger", "adapters", "outputs", "findings", "cas",
})


class CutoverError(ValueError):
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


def _has_symlink(path: Path, stop: Path) -> bool:
    current = path
    while current != stop:
        if current.is_symlink():
            return True
        current = current.parent
    return stop.is_symlink()


def _safe_repo_file(repo: Path, relative: str, code: str = "CUTOVER-IDENTITY-PATH") -> Path:
    relative = _relative(relative, "repository path")
    path = repo / relative
    _require(not _has_symlink(path, repo), code, f"repository path contains a symlink: {relative}")
    _require(path.resolve(strict=False).is_relative_to(repo), code, f"repository path escapes: {relative}")
    return path


def _git(repo: Path, *args: str, check: bool = True, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], input=input_bytes, capture_output=True, check=check)
    except OSError as exc:
        raise CutoverError("CUTOVER-GIT-MISSING", f"cannot execute git: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        raise CutoverError("CUTOVER-GIT", f"git {' '.join(args)} failed: {exc.stderr.decode('utf-8', 'replace').strip()}") from exc


def resolve_ref(repo: Path, ref: str) -> str | None:
    result = _git(repo, "rev-parse", "--verify", "--quiet", ref, check=False)
    if result.returncode == 1:
        return None
    _require(result.returncode == 0, "CUTOVER-GIT", result.stderr.decode("utf-8", "replace").strip())
    oid = result.stdout.decode("ascii").strip()
    _oid(oid, f"resolved {ref}")
    return oid


def git_identity(repo: Path, oid: str) -> dict[str, str]:
    _oid(oid, "commit OID")
    kind = _git(repo, "cat-file", "-t", oid, check=False)
    _require(kind.returncode == 0 and kind.stdout == b"commit\n", "CUTOVER-NOT-COMMIT", f"{oid} is not an existing commit")
    tree_oid = _git(repo, "rev-parse", f"{oid}^{{tree}}").stdout.decode().strip()
    listing = _git(repo, "ls-tree", "-r", "-z", "--full-tree", oid).stdout
    return {"commit_oid": oid, "tree_oid": tree_oid, "tree_digest": digest_bytes(listing)}


def patch_identity(repo: Path, source_oid: str, candidate_oid: str) -> dict[str, str]:
    diff = _git(repo, "diff", "--binary", "--full-index", source_oid, candidate_oid, "--").stdout
    return {"base_oid": source_oid, "candidate_oid": candidate_oid, "digest": digest_bytes(diff)}


def tree_manifest(root: Path, *, exclude: frozenset[str] = frozenset()) -> dict[str, str]:
    result: dict[str, str] = {}
    if not root.exists():
        return result
    _require(root.is_dir() and not root.is_symlink(), "CUTOVER-RETAINED-PATH", f"tree root is unsafe: {root}")
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        relative = path.relative_to(root).as_posix()
        _require(not path.is_symlink(), "CUTOVER-RETAINED-SYMLINK", f"retained tree contains symlink: {relative}")
        if path.is_file() and relative not in exclude:
            result[relative] = digest_bytes(path.read_bytes())
    return result


def tree_digest(root: Path, *, exclude: frozenset[str] = frozenset()) -> str:
    return digest_value(tree_manifest(root, exclude=exclude))


def adapter_tree_digest(adapter: str, root: Path) -> str:
    manifest = tree_manifest(root)
    if adapter == "importer" and "import-manifest.json" in manifest:
        value = json.loads((root / "import-manifest.json").read_text(encoding="utf-8"))
        value["disposable_root"] = "<declared-disposable-root>"
        manifest["import-manifest.json"] = digest_bytes(canonical_json(value).encode("utf-8"))
    return digest_value(manifest)


def snapshot_token(snapshot: Mapping[str, Any]) -> str:
    return digest_value({key: value for key, value in snapshot.items() if key != "token_digest"})


def package_payload(manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "transaction_id": manifest["transaction_id"], "source": manifest["source"],
        "candidate": manifest["candidate"], "prepared_patch": manifest["prepared_patch"],
        "authority_snapshot_token": manifest["authority_snapshot"]["token_digest"],
    }


def package_digest(manifest: Mapping[str, Any]) -> str:
    return digest_value(package_payload(manifest))


def signature_payload_digest(package: str, role: str, actor: str) -> str:
    return digest_value({"actor": actor, "package_digest": package, "role": role})


def event_digest(event: Mapping[str, Any]) -> str:
    return digest_value({key: value for key, value in event.items() if key != "event_digest"})


def read_manifest(path: Path) -> dict[str, Any]:
    _absolute(path, "--manifest")
    _require(not path.is_symlink(), "CUTOVER-MANIFEST-SYMLINK", "manifest must not be a symlink")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CutoverError("CUTOVER-MANIFEST-READ", f"cannot read manifest: {exc}") from exc
    _require(raw == canonical_json(value).encode(), "CUTOVER-NONCANONICAL", "manifest bytes are not canonical JSON")
    return validate_manifest(value)


def _validate_snapshot(snapshot: Any) -> dict[str, Any]:
    value = _object(snapshot, {"baseline_oid", "epoch", "allowed_write_authority", "issue_store_frozen", "authorities", "selector_path", "selector_digest", "token_digest"}, {"baseline_oid", "epoch", "allowed_write_authority", "issue_store_frozen", "authorities", "selector_path", "selector_digest", "token_digest"}, "authority_snapshot")
    _oid(value["baseline_oid"], "authority_snapshot.baseline_oid")
    epoch = value["epoch"]
    _require(epoch in EPOCHS, "CUTOVER-EPOCH", f"unknown epoch {epoch!r}")
    _require(value["allowed_write_authority"] == EXPECTED_AUTHORITY[epoch], "CUTOVER-AUTHORITY-MATRIX", "snapshot epoch/write authority mismatch")
    _require(value["issue_store_frozen"] is (epoch in FROZEN_EPOCHS), "CUTOVER-FROZEN-STATE", "snapshot frozen state mismatch")
    _require(isinstance(value["authorities"], list) and len(value["authorities"]) == 1 and isinstance(value["authorities"][0], str) and bool(value["authorities"][0]), "CUTOVER-EXACTLY-ONE-AUTHORITY", "exactly one authority is required")
    _relative(value["selector_path"], "authority_snapshot.selector_path")
    _digest(value["selector_digest"], "authority_snapshot.selector_digest")
    _require(value["token_digest"] == snapshot_token(value), "CUTOVER-AUTHORITY-TOKEN", "authority snapshot token mismatch")
    return value


def validate_ledger(events: Any, transaction_id: str, roles: Mapping[str, str], authority: str) -> None:
    _require(isinstance(events, list) and bool(events), "CUTOVER-LEDGER", "ledger must be non-empty")
    previous_digest = None
    previous_epoch = None
    for index, raw in enumerate(events):
        event = _object(raw, {"schema", "transaction_id", "sequence", "event_kind", "from_epoch", "to_epoch", "allowed_write_authority", "issue_store_frozen", "previous_event_digest", "payload_digest", "actor", "role", "signature_policy", "signature_verified", "event_digest"}, {"schema", "transaction_id", "sequence", "event_kind", "from_epoch", "to_epoch", "allowed_write_authority", "issue_store_frozen", "previous_event_digest", "payload_digest", "actor", "role", "signature_policy", "signature_verified", "event_digest"}, f"ledger[{index}]")
        _require(event["schema"] == LEDGER_SCHEMA, "CUTOVER-LEDGER-SCHEMA", "unsupported ledger schema")
        _require(event["transaction_id"] == transaction_id, "CUTOVER-TRANSACTION-MISMATCH", "ledger transaction mismatch")
        _require(event["sequence"] == index + 1, "CUTOVER-SEQUENCE", "ledger sequence is not contiguous")
        kind = event["event_kind"]
        _require(kind in EVENT_TRANSITIONS, "CUTOVER-EVENT-KIND", f"unsupported event kind {kind!r}")
        transition = (event["from_epoch"], event["to_epoch"])
        _require(transition in EVENT_TRANSITIONS[kind], "CUTOVER-EVENT-TRANSITION", f"event kind {kind} cannot represent {transition}")
        _require(event["to_epoch"] in LEGAL_TRANSITIONS[event["from_epoch"]], "CUTOVER-ILLEGAL-TRANSITION", f"illegal transition {transition}")
        if previous_epoch is not None:
            _require(event["from_epoch"] == previous_epoch, "CUTOVER-EVENT-CHAIN", "ledger epoch chain is discontinuous")
        _require(event["previous_event_digest"] == previous_digest, "CUTOVER-EVENT-CHAIN", "previous event digest mismatch")
        _require(event["allowed_write_authority"] == EXPECTED_AUTHORITY[event["to_epoch"]], "CUTOVER-AUTHORITY-MATRIX", "ledger authority mismatch")
        _require(event["issue_store_frozen"] is (event["to_epoch"] in FROZEN_EPOCHS), "CUTOVER-FROZEN-WRITE", "ledger frozen state mismatch")
        expected_role = EVENT_ROLES[kind]
        _require(event["role"] == expected_role and roles.get(expected_role) == event["actor"] == authority, "CUTOVER-EVENT-ACTOR-BINDING", "event actor/role is not bound to sole authority")
        _require(event["signature_policy"] == "single-authority-self-attestation@v1" and event["signature_verified"] is True, "CUTOVER-EVENT-SIGNATURE", "event signature policy is invalid")
        _digest(event["payload_digest"], "ledger.payload_digest")
        _require(event["event_digest"] == event_digest(event), "CUTOVER-EVENT-DIGEST", "ledger event digest mismatch")
        previous_digest = event["event_digest"]
        previous_epoch = event["to_epoch"]


def validate_manifest(value: Any) -> dict[str, Any]:
    manifest = _object(value, TOP_KEYS, TOP_KEYS, "manifest")
    _require(manifest["schema"] == MANIFEST_SCHEMA, "CUTOVER-SCHEMA", "unsupported manifest schema")
    _require(isinstance(manifest["transaction_id"], str) and TX_RE.fullmatch(manifest["transaction_id"]) is not None, "CUTOVER-TRANSACTION-ID", "invalid transaction ID")
    for name in ("source", "candidate"):
        record = _object(manifest[name], {"ref", "commit_oid", "tree_oid", "tree_digest"}, {"ref", "commit_oid", "tree_oid", "tree_digest"}, name)
        _require(isinstance(record["ref"], str) and REF_RE.fullmatch(record["ref"]) is not None, "CUTOVER-REF", f"invalid {name} ref")
        _oid(record["commit_oid"], f"{name}.commit_oid"); _oid(record["tree_oid"], f"{name}.tree_oid"); _digest(record["tree_digest"], f"{name}.tree_digest")
    patch = _object(manifest["prepared_patch"], {"base_oid", "candidate_oid", "digest"}, {"base_oid", "candidate_oid", "digest"}, "prepared_patch")
    _oid(patch["base_oid"], "prepared_patch.base_oid"); _oid(patch["candidate_oid"], "prepared_patch.candidate_oid"); _digest(patch["digest"], "prepared_patch.digest")
    _require(patch["base_oid"] == manifest["source"]["commit_oid"] and patch["candidate_oid"] == manifest["candidate"]["commit_oid"], "CUTOVER-PATCH-BINDING", "prepared patch endpoints do not match source/candidate")
    snapshot = _validate_snapshot(manifest["authority_snapshot"])
    _require(snapshot["baseline_oid"] == manifest["source"]["commit_oid"], "CUTOVER-SNAPSHOT-BASELINE", "snapshot baseline does not equal source")
    authority = snapshot["authorities"][0]

    identities = _object(manifest["identities"], {"tools", "schemas"}, {"tools", "schemas"}, "identities")
    for group in ("tools", "schemas"):
        _require(isinstance(identities[group], list) and bool(identities[group]), "CUTOVER-IDENTITY", f"{group} identities must be non-empty")
        seen = set()
        for raw in identities[group]:
            record = _object(raw, {"path", "digest"}, {"path", "digest"}, f"identities.{group}")
            path = _relative(record["path"], "identity.path")
            _require(path not in seen, "CUTOVER-IDENTITY", f"duplicate identity {path}"); seen.add(path); _digest(record["digest"], "identity.digest")

    refs = manifest["refs"]
    _require(isinstance(refs, list) and bool(refs), "CUTOVER-REF", "refs must be non-empty")
    declared = set()
    for raw in refs:
        record = _object(raw, {"name", "expected_oid", "target_oid"}, {"name", "expected_oid", "target_oid"}, "ref expectation")
        name = _string(record["name"], "ref.name")
        _require(REF_RE.fullmatch(name) is not None, "CUTOVER-REF", "invalid ref")
        _require(name != "refs/heads/main", "CUTOVER-MAIN-REF", "refs/heads/main is forbidden")
        _require(name not in declared, "CUTOVER-DUPLICATE-REF", f"duplicate ref {name}"); declared.add(name)
        _oid(record["expected_oid"], "ref.expected_oid", nullable=True); _oid(record["target_oid"], "ref.target_oid", nullable=True)

    roles = manifest["roles"]
    _require(isinstance(roles, dict) and set(roles) == REQUIRED_ROLES, "CUTOVER-ROLE-SET", "role set is incomplete or unknown")
    _require(all(actor == authority for actor in roles.values()), "CUTOVER-ROLE-AUTHORITY", "all roles must bind to sole authority")
    package = package_digest(manifest)
    signatures = manifest["signatures"]
    _require(isinstance(signatures, list) and len(signatures) == len(REQUIRED_ROLES), "CUTOVER-SIGNATURE-SET", "one signature per role is required")
    seen_roles = set()
    for raw in signatures:
        record = _object(raw, {"role", "actor", "policy", "payload_digest", "verified"}, {"role", "actor", "policy", "payload_digest", "verified"}, "signature")
        role = record["role"]
        _require(role in REQUIRED_ROLES and role not in seen_roles, "CUTOVER-SIGNATURE-SET", "signature role is unknown or duplicated"); seen_roles.add(role)
        _require(record["actor"] == roles[role] == authority, "CUTOVER-SIGNATURE-ACTOR", "signature actor is not role authority")
        _require(record["policy"] == "single-authority-self-attestation@v1" and record["verified"] is True, "CUTOVER-SIGNATURE-POLICY", "signature policy/verification invalid")
        _require(record["payload_digest"] == signature_payload_digest(package, role, authority), "CUTOVER-SIGNATURE-PAYLOAD", "signature payload is unrelated")
    approval = _object(manifest["approvals"], {"ref", "base_oid", "role", "actor", "payload_digest", "signature_verified"}, {"ref", "base_oid", "role", "actor", "payload_digest", "signature_verified"}, "approval")
    _require(isinstance(approval["ref"], str) and approval["ref"].startswith("refs/autodocs/approval/"), "CUTOVER-APPROVAL-REF", "approval prefix is invalid")
    _require(approval["base_oid"] == manifest["source"]["commit_oid"], "CUTOVER-APPROVAL-BASE", "approval base is not source")
    _require(approval["role"] == "approver" and approval["actor"] == roles["approver"] == authority and approval["signature_verified"] is True, "CUTOVER-APPROVAL-ACTOR", "approval actor/role/signature invalid")
    _require(approval["payload_digest"] == package, "CUTOVER-APPROVAL-PAYLOAD", "approval payload is unrelated")

    quiescence = _object(manifest["quiescence"], {"clients", "jobs", "claims", "observed_at_oid", "snapshot_token", "digest"}, {"clients", "jobs", "claims", "observed_at_oid", "snapshot_token", "digest"}, "quiescence")
    for field in ("clients", "jobs", "claims"):
        _require(isinstance(quiescence[field], list) and not quiescence[field], f"CUTOVER-QUIESCENCE-{field.upper()}", f"stale {field} remain")
    _require(quiescence["observed_at_oid"] == snapshot["baseline_oid"] and quiescence["snapshot_token"] == snapshot["token_digest"], "CUTOVER-QUIESCENCE-BINDING", "quiescence is not bound to baseline/snapshot")
    qp = {key: quiescence[key] for key in ("clients", "jobs", "claims", "observed_at_oid", "snapshot_token")}
    _require(quiescence["digest"] == digest_value(qp), "CUTOVER-QUIESCENCE-DIGEST", "quiescence digest mismatch")

    validate_ledger(manifest["ledger"], manifest["transaction_id"], roles, authority)
    terminal = manifest["ledger"][-1]
    _require((terminal["to_epoch"], terminal["allowed_write_authority"], terminal["issue_store_frozen"]) == (snapshot["epoch"], snapshot["allowed_write_authority"], snapshot["issue_store_frozen"]), "CUTOVER-TERMINAL-SNAPSHOT", "terminal ledger state differs from snapshot")
    _require(all(event["payload_digest"] == package for event in manifest["ledger"]), "CUTOVER-EVENT-PAYLOAD", "ledger payload is unrelated")

    adapters = manifest["adapters"]
    _require(isinstance(adapters, list) and len(adapters) == 2, "CUTOVER-ADAPTER-SET", "exactly importer and regenerator are required")
    seen_adapters = set()
    for raw in adapters:
        record = _object(raw, {"id", "config"}, {"id", "config"}, "adapter")
        adapter_id = record["id"]
        _require(adapter_id in ADAPTER_EXECUTABLES and adapter_id not in seen_adapters, "CUTOVER-ADAPTER-SET", "adapter unknown or duplicated"); seen_adapters.add(adapter_id)
        if adapter_id == "importer":
            config = _object(record["config"], {"source", "files"}, {"source", "files"}, "importer.config")
            _require(config["source"] == "manifest-source", "CUTOVER-IMPORTER-CONFIG", "importer source must be manifest-source")
            _require(isinstance(config["files"], list) and all(isinstance(item, str) and _relative(item, "importer file") for item in config["files"]), "CUTOVER-IMPORTER-CONFIG", "importer files invalid")
        else:
            config = _object(record["config"], {"mode", "dag_path"}, {"mode", "dag_path"}, "regenerator.config")
            _require(config["mode"] == "write-disposable", "CUTOVER-REGENERATOR-MODE", "regenerator must use explicit disposable write mode")
            _relative(config["dag_path"], "regenerator dag_path")
    _require(seen_adapters == set(ADAPTER_EXECUTABLES), "CUTOVER-ADAPTER-SET", "adapter set incomplete")
    outputs = manifest["outputs"]
    _require(isinstance(outputs, list) and len(outputs) == 2, "CUTOVER-OUTPUT-SET", "one complete tree identity per adapter is required")
    output_ids = set()
    for raw in outputs:
        record = _object(raw, {"adapter", "tree_digest"}, {"adapter", "tree_digest"}, "output identity")
        _require(record["adapter"] in ADAPTER_EXECUTABLES and record["adapter"] not in output_ids, "CUTOVER-OUTPUT-SET", "output adapter unknown or duplicated"); output_ids.add(record["adapter"]); _digest(record["tree_digest"], "output.tree_digest")
    _require(output_ids == set(ADAPTER_EXECUTABLES), "CUTOVER-OUTPUT-SET", "output identity set incomplete")
    _require(isinstance(manifest["findings"], list), "CUTOVER-FINDING", "findings must be an array")
    for raw in manifest["findings"]:
        finding = _object(raw, {"code", "severity", "path", "message"}, {"code", "severity", "path", "message"}, "finding")
        _string(finding["code"], "finding.code"); _string(finding["path"], "finding.path"); _string(finding["message"], "finding.message")
        _require(finding["severity"] in {"info", "warning", "blocking"}, "CUTOVER-FINDING", "finding severity invalid")
    cas = _object(manifest["cas"], {"disposable_test_repo", "declared_refs"}, {"disposable_test_repo", "declared_refs"}, "cas")
    _require(isinstance(cas["disposable_test_repo"], bool), "CUTOVER-CAS", "disposable_test_repo must be boolean")
    _require(cas["declared_refs"] == sorted(declared), "CUTOVER-UNDECLARED-REF", "CAS declaration differs from ref expectations")
    return manifest


def _identity_findings(repo: Path, manifest: Mapping[str, Any]) -> list[dict[str, str]]:
    findings = []
    for group in ("tools", "schemas"):
        for identity in manifest["identities"][group]:
            try:
                path = _safe_repo_file(repo, identity["path"])
            except CutoverError as exc:
                findings.append({"code": exc.code, "path": identity["path"], "message": exc.message}); continue
            if not path.is_file(): findings.append({"code": "CUTOVER-MISSING-IDENTITY", "path": identity["path"], "message": "identity path missing"})
            elif digest_bytes(path.read_bytes()) != identity["digest"]: findings.append({"code": "CUTOVER-IDENTITY-DRIFT", "path": identity["path"], "message": "identity digest differs"})
    selector = _safe_repo_file(repo, manifest["authority_snapshot"]["selector_path"], "CUTOVER-SELECTOR-PATH")
    if not selector.is_file() or digest_bytes(selector.read_bytes()) != manifest["authority_snapshot"]["selector_digest"]:
        findings.append({"code": "CUTOVER-SELECTOR-MISMATCH", "path": manifest["authority_snapshot"]["selector_path"], "message": "selector identity differs"})
    return findings


def inspect(repo: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    findings = _identity_findings(repo, manifest)
    for name in ("source", "candidate"):
        record = manifest[name]
        observed = resolve_ref(repo, record["ref"])
        if observed != record["commit_oid"]:
            findings.append({"code": f"CUTOVER-{name.upper()}-REF-DRIFT", "path": record["ref"], "message": "ref differs from pinned commit"}); continue
        try:
            actual = git_identity(repo, observed)
            if any(actual[key] != record[key] for key in ("commit_oid", "tree_oid", "tree_digest")):
                findings.append({"code": f"CUTOVER-{name.upper()}-IDENTITY-DRIFT", "path": record["ref"], "message": "Git/tree identity differs"})
        except CutoverError as exc:
            findings.append({"code": exc.code, "path": record["ref"], "message": exc.message})
    actual_patch = patch_identity(repo, manifest["source"]["commit_oid"], manifest["candidate"]["commit_oid"])
    if actual_patch != manifest["prepared_patch"]:
        findings.append({"code": "CUTOVER-PATCH-DRIFT", "path": "prepared_patch", "message": "prepared patch identity differs"})
    refs = []
    for record in manifest["refs"]:
        observed = resolve_ref(repo, record["name"]); refs.append({"name": record["name"], "expected_oid": record["expected_oid"], "observed_oid": observed})
        if observed != record["expected_oid"]: findings.append({"code": "CUTOVER-STALE-OID", "path": record["name"], "message": "ref expectation differs"})
    return {"schema": RESULT_SCHEMA, "command": "inspect", "status": "PASS" if not findings else "BLOCKED", "transaction_id": manifest["transaction_id"], "manifest_digest": digest_value(manifest), "refs": refs, "findings": findings, "mutation": "none"}


def _authorize_output(repo: Path, output: Path) -> Path:
    _absolute(output, "--output-root", must_exist=False)
    _require(output.parent.is_dir() and not _has_symlink(output, output.parent), "CUTOVER-OUTPUT-PATH", "unsafe output path")
    _require(output.name.startswith("cutover-"), "CUTOVER-OUTPUT-PATH", "output basename must start cutover-")
    _require(not output.is_relative_to(repo) and not repo.is_relative_to(output), "CUTOVER-LIVE-WRITE", "output overlaps repository")
    roots = (Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve())
    _require(any(output != root and output.is_relative_to(root) for root in roots), "CUTOVER-OUTPUT-PATH", "output must be under temporary root")
    return output


def _adapter_command(repo: Path, staging: Path, adapter: Mapping[str, Any], manifest: Mapping[str, Any]) -> tuple[Path, list[str], Path]:
    adapter_id = adapter["id"]
    executable = _safe_repo_file(repo, ADAPTER_EXECUTABLES[adapter_id], "CUTOVER-ADAPTER-PATH")
    destination = staging / ADAPTER_CHILDREN[adapter_id]
    _require(destination.parent == staging and not destination.exists(), "CUTOVER-ADAPTER-DESTINATION", "adapter destination repeated or escaped")
    if adapter_id == "importer":
        command = [sys.executable, str(executable), "--repo", str(repo), "--root", str(destination), "--source-commit", manifest["source"]["commit_oid"]]
        for item in adapter["config"]["files"]: command.extend(["--file", item])
    else:
        dag = _safe_repo_file(repo, adapter["config"]["dag_path"], "CUTOVER-ADAPTER-PATH")
        command = [sys.executable, str(executable), "--repo", str(repo), "--output-root", str(destination), "--dag", str(dag), "--write", "--format", "json"]
    return executable, command, destination


def _run_adapters(repo: Path, staging: Path, manifest: Mapping[str, Any]) -> list[dict[str, str]]:
    expected_tools = {item["path"]: item["digest"] for item in manifest["identities"]["tools"]}
    summaries = []
    for adapter in manifest["adapters"]:
        executable, command, destination = _adapter_command(repo, staging, adapter, manifest)
        _require(executable.is_file(), "CUTOVER-MISSING-EXECUTABLE", f"missing {executable}")
        _require(expected_tools.get(ADAPTER_EXECUTABLES[adapter["id"]]) == digest_bytes(executable.read_bytes()), "CUTOVER-ADAPTER-IDENTITY", "adapter identity differs")
        temporary_input = None
        if adapter["id"] == "regenerator":
            imported = staging / ADAPTER_CHILDREN["importer"] / "issues"
            _require(imported.is_dir(), "CUTOVER-ADAPTER-COMPOSITION", "importer produced no issues tree")
            temporary_input = tempfile.TemporaryDirectory(prefix="cutover-regeneration-input-")
            input_repo = Path(temporary_input.name).resolve()
            shutil.copytree(repo / "_src", input_repo / "_src")
            shutil.copytree(repo / "provenance", input_repo / "provenance")
            shutil.copytree(repo / "docs", input_repo / "docs")
            shutil.copytree(imported, input_repo / "issues")
            shutil.copytree(repo / "issues/_schema", input_repo / "issues/_schema")
            shutil.copyfile(repo / "agent-workflow.json", input_repo / "agent-workflow.json")
            dag = _safe_repo_file(input_repo, adapter["config"]["dag_path"], "CUTOVER-ADAPTER-PATH")
            command = [sys.executable, str(executable), "--repo", str(input_repo), "--output-root", str(destination), "--dag", str(dag), "--write", "--format", "json"]
        try:
            result = subprocess.run(command, cwd=repo, env={"PATH": os.environ.get("PATH", ""), "TMPDIR": tempfile.gettempdir()}, capture_output=True, check=False)
        finally:
            if temporary_input is not None:
                temporary_input.cleanup()
        _require(result.returncode == 0, "CUTOVER-ADAPTER-FAILED", f"{adapter['id']} failed ({result.returncode}): {result.stderr.decode('utf-8', 'replace')[:1000]}")
        summaries.append({"adapter": adapter["id"], "tree_digest": adapter_tree_digest(adapter["id"], destination), "stdout_digest": digest_bytes(result.stdout)})
    return summaries


def prepare(repo: Path, output: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    output = _authorize_output(repo, output); fingerprint = digest_value(manifest); receipt_path = output / "preparation.json"
    if output.exists():
        _require(receipt_path.is_file() and not receipt_path.is_symlink(), "CUTOVER-RETRY-CONFLICT", "existing output lacks safe receipt")
        receipt = json.loads(receipt_path.read_text())
        _require(receipt.get("transaction_id") == manifest["transaction_id"] and receipt.get("manifest_digest") == fingerprint, "CUTOVER-TRANSACTION-REUSE", "transaction reused with changed input")
        _require(receipt.get("prepared_tree_digest") == tree_digest(output, exclude=frozenset({"preparation.json"})), "CUTOVER-PREPARED-DRIFT", "complete retained tree differs")
        _verify_retained(output, manifest, receipt)
        return {**receipt, "command": "prepare", "status": "PASS", "idempotent": True, "mutation": "none"}
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        summaries = _run_adapters(repo, staging, manifest)
        expected = {item["adapter"]: item["tree_digest"] for item in manifest["outputs"]}
        _require({item["adapter"]: item["tree_digest"] for item in summaries} == expected, "CUTOVER-OUTPUT-DRIFT", "adapter output tree identity differs")
        receipt = {"schema": "cutover-preparation@v1", "transaction_id": manifest["transaction_id"], "manifest_digest": fingerprint, "source": manifest["source"], "candidate": manifest["candidate"], "prepared_patch": manifest["prepared_patch"], "adapters": summaries, "prepared_tree_digest": tree_digest(staging), "mutation": "disposable-output-only"}
        (staging / "preparation.json").write_text(canonical_json(receipt))
        os.rename(staging, output)
        return {**receipt, "command": "prepare", "status": "PASS", "idempotent": False}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True); raise


def _verify_retained(output: Path, manifest: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    entries = tree_manifest(output)
    top = {path.split("/", 1)[0] for path in entries}
    _require(top == {"imported", "regenerated", "preparation.json"}, "CUTOVER-RETAINED-EXTRA", "retained tree has missing or undeclared top-level paths")
    complete = tree_digest(output, exclude=frozenset({"preparation.json"}))
    _require(receipt.get("prepared_tree_digest") == complete, "CUTOVER-PREPARED-DRIFT", "complete retained tree digest differs")
    expected = {item["adapter"]: item["tree_digest"] for item in manifest["outputs"]}
    for adapter, child in ADAPTER_CHILDREN.items():
        _require(adapter_tree_digest(adapter, output / child) == expected[adapter], "CUTOVER-OUTPUT-DRIFT", f"retained {adapter} tree differs")


def verify(repo: Path, manifest: Mapping[str, Any], output: Path | None = None) -> dict[str, Any]:
    result = inspect(repo, manifest); findings = list(result["findings"])
    if output is not None:
        try:
            _absolute(output, "--output-root"); _require(not _has_symlink(output, output.parent), "CUTOVER-RETAINED-PATH", "unsafe retained output")
            receipt_path = output / "preparation.json"; _require(receipt_path.is_file() and not receipt_path.is_symlink(), "CUTOVER-MISSING-PREPARATION", "preparation receipt missing")
            receipt = json.loads(receipt_path.read_text())
            _require(receipt.get("manifest_digest") == digest_value(manifest), "CUTOVER-PREPARED-DRIFT", "receipt manifest differs")
            _verify_retained(output, manifest, receipt)
        except (CutoverError, OSError, json.JSONDecodeError) as exc:
            code = exc.code if isinstance(exc, CutoverError) else "CUTOVER-PREPARATION-READ"
            findings.append({"code": code, "path": str(output), "message": str(exc)})
    return {"schema": RESULT_SCHEMA, "command": "verify", "status": "PASS" if not findings else "BLOCKED", "transaction_id": manifest["transaction_id"], "manifest_digest": digest_value(manifest), "findings": findings, "mutation": "none"}


def plan_cas(expectations: Sequence[Mapping[str, Any]], declared_refs: Sequence[str], *, include_commit: bool = True) -> bytes:
    declared = set(declared_refs); _require(len(declared) == len(declared_refs), "CUTOVER-DUPLICATE-REF", "declared refs duplicate"); _require(bool(expectations), "CUTOVER-CAS", "CAS empty")
    chunks = [b"start\0"]; seen =\
        set()
    for item in expectations:
        name, expected, target = item.get("name"), item.get("expected_oid"), item.get("target_oid")
        _require(isinstance(name, str) and REF_RE.fullmatch(name) is not None, "CUTOVER-REF", "invalid CAS ref"); assert isinstance(name, str)
        _require(name != "refs/heads/main", "CUTOVER-MAIN-REF", "refs/heads/main forbidden")
        _require(name in declared and name not in seen, "CUTOVER-UNDECLARED-REF", f"undeclared/duplicate CAS ref {name}"); seen.add(name)
        _oid(expected, "CAS expected", nullable=True); _oid(target, "CAS target", nullable=True); old = expected or ZERO_OID
        if target is None: chunks.extend([f"delete {name}\0".encode(), f"{old}\0".encode()])
        else: chunks.extend([f"update {name}\0".encode(), f"{target}\0".encode(), f"{old}\0".encode()])
    _require(seen == declared, "CUTOVER-UNDECLARED-REF", "CAS does not cover declared refs")
    chunks.append(b"prepare\0")
    if include_commit: chunks.append(b"commit\0")
    return b"".join(chunks)


def _write_cas_receipt(path: Path | None, payload: Mapping[str, Any]) -> None:
    if path is None: return
    _absolute(path, "CAS receipt", must_exist=False); _require(path.parent.is_dir() and not path.is_symlink(), "CUTOVER-CAS-RECEIPT", "unsafe receipt path")
    path.write_text(canonical_json(payload))


def execute_disposable_cas(repo: Path, expectations: Sequence[Mapping[str, Any]], declared_refs: Sequence[str], *, dry_run: bool, crash_at: str | None = None, receipt_path: Path | None = None) -> dict[str, Any]:
    repo = _absolute(repo, "CAS repo"); _require((repo / ".git").is_dir(), "CUTOVER-CAS-NOT-DISPOSABLE", "CAS repo must be standalone")
    marker = repo / ".issue-cutover-disposable-test-repo"; _require(marker.is_file() and marker.read_text() == "issue-cutover-disposable-test-repo@v1\n", "CUTOVER-CAS-NOT-DISPOSABLE", "missing disposable marker")
    transaction = plan_cas(expectations, declared_refs)
    for item in expectations:
        target = item["target_oid"]
        if target is not None:
            exists = _git(repo, "cat-file", "-e", f"{target}^{{object}}", check=False)
            _require(exists.returncode == 0, "CUTOVER-CAS-TARGET-MISSING", f"target object missing: {target}")
    before = {name: resolve_ref(repo, name) for name in declared_refs}; targets = {item["name"]: item["target_oid"] for item in expectations}
    if dry_run:
        return {"schema": "cutover-cas-result@v1", "status": "PLANNED", "dry_run": True, "before": before, "after": before, "transaction_digest": digest_bytes(transaction), "mutation": "none"}
    if before == targets:
        payload = {"schema": "cutover-cas-result@v1", "status": "RECOVERED", "dry_run": False, "before": before, "after": before, "transaction_digest": digest_bytes(transaction), "mutation": "receipt-only"}
        _write_cas_receipt(receipt_path, payload); return payload
    if crash_at == "before-prepare": raise CutoverError("CUTOVER-CAS-CRASH-BEFORE-PREPARE", "injected crash before prepare")
    if crash_at == "between-prepare-commit":
        partial = plan_cas(expectations, declared_refs, include_commit=False)
        _git(repo, "update-ref", "--stdin", "-z", check=False, input_bytes=partial)
        after = {name: resolve_ref(repo, name) for name in declared_refs}
        _require(after == before, "CUTOVER-CAS-PARTIAL", "abandoned prepared transaction changed refs")
        raise CutoverError("CUTOVER-CAS-CRASH-BETWEEN", "injected crash between prepare and commit")
    result = _git(repo, "update-ref", "--stdin", "-z", check=False, input_bytes=transaction); after = {name: resolve_ref(repo, name) for name in declared_refs}
    if result.returncode != 0:
        _require(after == before, "CUTOVER-CAS-PARTIAL", "failed CAS changed refs")
        raise CutoverError("CUTOVER-CAS-COMPETITOR", result.stderr.decode("utf-8", "replace").strip())
    if crash_at == "after-commit-before-receipt": raise CutoverError("CUTOVER-CAS-CRASH-AFTER-COMMIT", "injected crash after commit before receipt")
    payload = {"schema": "cutover-cas-result@v1", "status": "APPLIED", "dry_run": False, "before": before, "after": after, "transaction_digest": digest_bytes(transaction), "mutation": "disposable-refs-only"}
    _write_cas_receipt(receipt_path, payload); return payload


def blocked_effect(command: str) -> dict[str, Any]:
    return {"schema": RESULT_SCHEMA, "command": command, "status": "BLOCKED", "code": BLOCKED_EFFECT_CODE, "message": "effect activation awaits governance normalization; no override exists", "mutation": "none"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "prepare", "verify", *EFFECT_COMMANDS):
        child = sub.add_parser(command); child.add_argument("--repo", required=True); child.add_argument("--manifest", required=True)
        if command in ("prepare", "verify"): child.add_argument("--output-root", required=command == "prepare")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    if args.command in EFFECT_COMMANDS:
        sys.stdout.write(canonical_json(blocked_effect(args.command))); return 2
    try:
        repo = _absolute(Path(args.repo), "--repo"); _require((repo / ".git").exists(), "CUTOVER-REPO", "not a Git worktree")
        manifest = read_manifest(Path(args.manifest))
        result = inspect(repo, manifest) if args.command == "inspect" else prepare(repo, Path(args.output_root), manifest) if args.command == "prepare" else verify(repo, manifest, Path(args.output_root) if args.output_root else None)
        sys.stdout.write(canonical_json(result)); return 0 if result["status"] == "PASS" else 2
    except CutoverError as exc:
        sys.stdout.write(canonical_json({"schema": RESULT_SCHEMA, "command": args.command, "status": "BLOCKED", "code": exc.code, "message": exc.message, "mutation": "none"})); return 2


if __name__ == "__main__":
    raise SystemExit(main())
