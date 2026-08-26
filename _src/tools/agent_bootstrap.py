#!/usr/bin/env python3
"""Offline, side-effect-free agent workflow selector doctor.

This module intentionally uses only the Python standard library.  Importing it
does not inspect the repository; callers must invoke :func:`doctor` explicitly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Mapping


SELECTOR_NAME = "agent-workflow.json"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
BUNDLE_RE = re.compile(r"^docs/pipeline/agent-instructions/(legacy|current|future)/index\.md$")
LINK_RE = re.compile(r"\[[^]]*\]\(([^)#?]+)(?:#[^)]*)?\)")
V2_KEYS = {
    "schema", "workflow_version", "authority_epoch", "authority_profile",
    "write_phase", "required_capability", "execution_model",
    "selector_digest", "instruction_bundle",
}
V1_KEYS = {
    "schema", "workflow_version", "authority_epoch", "authority_profile",
    "write_phase", "required_capability", "runner_protocol",
    "selector_digest", "instruction_bundle",
}
PHASES = {
    "legacy-writable": ("legacy-lists", "legacy-writable"),
    "legacy-frozen": ("legacy-lists", "frozen"),
    "legacy-restored": ("legacy-lists", "legacy-restored"),
    "issue-store-writable": ("issue-store", "issue-store-writable"),
    "issue-store-write-frozen": ("issue-store", "write-frozen"),
}
DIAGNOSTIC_ORDER = {
    name: index for index, name in enumerate((
        "AB001_SELECTOR_MISSING", "AB002_SELECTOR_JSON", "AB003_SELECTOR_SHAPE",
        "AB004_SCHEMA_UNSUPPORTED", "AB005_UNKNOWN_FIELD", "AB006_MISSING_FIELD",
        "AB007_WORKFLOW_VERSION", "AB008_AUTHORITY_CONTRADICTION",
        "AB009_EXECUTION_MODEL", "AB010_CAPABILITY", "AB011_DIGEST_FORMAT",
        "AB012_DIGEST_PLACEHOLDER", "AB013_DIGEST_MISMATCH", "AB014_BUNDLE_PATH",
        "AB015_BUNDLE_MISSING", "AB016_BUNDLE_MEMBER_MISSING", "AB022_BUNDLE_MEMBER_DRIFT",
        "AB017_EXPECTED_EPOCH", "AB018_EXPECTED_PROFILE", "AB019_EXPECTED_VERSION",
        "AB020_REBOOTSTRAP_COMMAND_MISSING", "AB021_LEGACY_TRANSPORT",
    ))
}


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def selector_digest(value: Mapping[str, Any]) -> str:
    preimage = dict(value)
    preimage.pop("selector_digest", None)
    return "sha256:" + hashlib.sha256(_canonical_bytes(preimage)).hexdigest()


def _diagnostic(items: list[dict[str, str]], diagnostic_id: str, message: str) -> None:
    items.append({"id": diagnostic_id, "message": message})


def _safe_repo_path(repo: Path, relative: str) -> Path | None:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts or "\\" in relative:
        return None
    candidate = repo.joinpath(*posix.parts)
    try:
        candidate.resolve().relative_to(repo.resolve())
    except (OSError, ValueError):
        return None
    return candidate


def _bundle_members(repo: Path, bundle: str, diagnostics: list[dict[str, str]]) -> dict[str, str]:
    first = _safe_repo_path(repo, bundle)
    if first is None:
        _diagnostic(diagnostics, "AB014_BUNDLE_PATH", "instruction_bundle is not a safe repository-relative bundle path")
        return {}
    if not first.is_file():
        _diagnostic(diagnostics, "AB015_BUNDLE_MISSING", f"instruction bundle is missing: {bundle}")
        return {}
    pending = [bundle]
    seen: set[str] = set()
    members: dict[str, str] = {}
    while pending:
        relative = pending.pop(0)
        if relative in seen:
            continue
        seen.add(relative)
        path = _safe_repo_path(repo, relative)
        if path is None or not path.is_file():
            _diagnostic(diagnostics, "AB016_BUNDLE_MEMBER_MISSING", f"instruction bundle member is missing: {relative}")
            continue
        data = path.read_bytes()
        members[relative] = "sha256:" + hashlib.sha256(data).hexdigest()
        if path.suffix.lower() == ".md":
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                _diagnostic(diagnostics, "AB016_BUNDLE_MEMBER_MISSING", f"instruction bundle member is not UTF-8: {relative}")
                continue
            for target in LINK_RE.findall(text):
                linked = (PurePosixPath(relative).parent / target).as_posix()
                if linked.startswith("docs/pipeline/agent-instructions/") and linked not in seen:
                    pending.append(linked)
    return dict(sorted(members.items()))


def doctor(repo: str | Path, expected_epoch: str, expected_profile: str,
           expected_workflow_version: str) -> dict[str, Any]:
    """Return a deterministic ``agent-bootstrap-doctor@v1`` result."""
    root = Path(repo)
    diagnostics: list[dict[str, str]] = []
    selector: dict[str, Any] = {}
    selector_path = root / SELECTOR_NAME
    if not selector_path.is_file():
        _diagnostic(diagnostics, "AB001_SELECTOR_MISSING", f"missing {SELECTOR_NAME}")
    else:
        try:
            loaded = json.loads(selector_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            _diagnostic(diagnostics, "AB002_SELECTOR_JSON", f"{SELECTOR_NAME} is not valid UTF-8 JSON")
        else:
            if isinstance(loaded, dict):
                selector = loaded
            else:
                _diagnostic(diagnostics, "AB003_SELECTOR_SHAPE", "selector root must be an object")

    schema = selector.get("schema")
    is_v2 = schema == "agent-workflow-bootstrap@v2"
    is_v1 = schema == "agent-workflow-bootstrap@v1"
    keys = V2_KEYS if is_v2 else V1_KEYS if is_v1 else set()
    if selector and not keys:
        _diagnostic(diagnostics, "AB004_SCHEMA_UNSUPPORTED", f"unsupported selector schema: {schema!r}")
    if keys:
        for key in sorted(set(selector) - keys):
            _diagnostic(diagnostics, "AB005_UNKNOWN_FIELD", f"unknown selector field: {key}")
        for key in sorted(keys - set(selector)):
            _diagnostic(diagnostics, "AB006_MISSING_FIELD", f"missing selector field: {key}")

    version = selector.get("workflow_version")
    if keys and (not isinstance(version, str) or not SEMVER_RE.fullmatch(version)):
        _diagnostic(diagnostics, "AB007_WORKFLOW_VERSION", "workflow_version must be semantic version x.y.z")
    epoch = selector.get("authority_epoch")
    profile = selector.get("authority_profile")
    phase = selector.get("write_phase")
    if keys and (not isinstance(epoch, str) or epoch not in PHASES or PHASES.get(epoch) != (profile, phase)):
        _diagnostic(diagnostics, "AB008_AUTHORITY_CONTRADICTION", "authority_epoch, authority_profile, and write_phase contradict the canonical policy")

    execution_model = selector.get("execution_model") if is_v2 else "legacy-runner"
    capability = selector.get("required_capability")
    if is_v2 and execution_model != "direct":
        _diagnostic(diagnostics, "AB009_EXECUTION_MODEL", "v2 execution_model must be direct")
    if is_v2 and capability not in {"unprivileged", "privileged"}:
        _diagnostic(diagnostics, "AB010_CAPABILITY", "v2 required_capability must be unprivileged or privileged")
    if is_v1:
        _diagnostic(diagnostics, "AB021_LEGACY_TRANSPORT", "v1 selector is readable compatibility input but selects retired runner transport")

    claimed_digest = selector.get("selector_digest")
    computed_digest = selector_digest(selector) if selector else None
    if keys and (not isinstance(claimed_digest, str) or not DIGEST_RE.fullmatch(claimed_digest)):
        _diagnostic(diagnostics, "AB011_DIGEST_FORMAT", "selector_digest must be sha256 plus 64 lowercase hexadecimal characters")
    elif isinstance(claimed_digest, str):
        payload = claimed_digest.removeprefix("sha256:")
        if len(set(payload)) == 1:
            _diagnostic(diagnostics, "AB012_DIGEST_PLACEHOLDER", "selector_digest is a repeated-character placeholder")
        if computed_digest != claimed_digest:
            _diagnostic(diagnostics, "AB013_DIGEST_MISMATCH", "selector_digest does not match canonical JSON with selector_digest omitted")

    bundle_value = selector.get("instruction_bundle")
    bundle = bundle_value if is_v1 else bundle_value.get("path") if isinstance(bundle_value, dict) else None
    declared_members = bundle_value.get("members") if is_v2 and isinstance(bundle_value, dict) else None
    members: dict[str, str] = {}
    if keys:
        if not isinstance(bundle, str) or not BUNDLE_RE.fullmatch(bundle):
            _diagnostic(diagnostics, "AB014_BUNDLE_PATH", "instruction_bundle is outside the versioned instruction bundle paths")
        else:
            members = _bundle_members(root, bundle, diagnostics)
            if is_v2:
                if not isinstance(declared_members, dict) or not declared_members:
                    _diagnostic(diagnostics, "AB016_BUNDLE_MEMBER_MISSING", "v2 instruction_bundle must declare a non-empty members digest map")
                else:
                    for path, digest in sorted(declared_members.items()):
                        if not isinstance(path, str) or not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest):
                            _diagnostic(diagnostics, "AB016_BUNDLE_MEMBER_MISSING", "instruction bundle member declarations must map paths to SHA-256 digests")
                        elif members.get(path) != digest:
                            _diagnostic(diagnostics, "AB022_BUNDLE_MEMBER_DRIFT", f"instruction bundle member digest drift: {path}")
                    for path in sorted(set(members) - set(declared_members)):
                        _diagnostic(diagnostics, "AB022_BUNDLE_MEMBER_DRIFT", f"undeclared instruction bundle member: {path}")

    if epoch != expected_epoch:
        _diagnostic(diagnostics, "AB017_EXPECTED_EPOCH", f"expected authority_epoch {expected_epoch!r}, observed {epoch!r}")
    if profile != expected_profile:
        _diagnostic(diagnostics, "AB018_EXPECTED_PROFILE", f"expected authority_profile {expected_profile!r}, observed {profile!r}")
    if version != expected_workflow_version:
        _diagnostic(diagnostics, "AB019_EXPECTED_VERSION", f"expected workflow_version {expected_workflow_version!r}, observed {version!r}")

    command = root / "_src/tools/agent_bootstrap.py"
    if not command.is_file():
        _diagnostic(diagnostics, "AB020_REBOOTSTRAP_COMMAND_MISSING", "re-bootstrap command implementation is missing: _src/tools/agent_bootstrap.py")

    diagnostics.sort(key=lambda item: (DIAGNOSTIC_ORDER[item["id"]], item["message"]))
    ready = not diagnostics
    normalized = {
        "schema": schema,
        "workflow_version": version,
        "authority_epoch": epoch,
        "authority_profile": profile,
        "write_phase": phase,
        "selector_digest": claimed_digest,
        "computed_selector_digest": computed_digest,
        "instruction_bundle": bundle,
    }
    return {
        "schema": "agent-bootstrap-doctor@v1",
        "status": "ready" if ready else "stale-or-invalid",
        "selector": normalized,
        "instruction_bundle_members": members,
        "direct_capability": {
            "execution_model": execution_model,
            "required_capability": capability,
            "status": "ready" if is_v2 and execution_model == "direct" and capability in {"unprivileged", "privileged"} else "unsupported",
        },
        "diagnostics": diagnostics,
        "rebootstrap_argv": [
            "python3", "_src/tools/agent_bootstrap.py", "doctor", "--repo", str(root),
            "--expected-epoch", expected_epoch, "--expected-profile", expected_profile,
            "--expected-workflow-version", expected_workflow_version, "--json",
        ],
    }


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(3, f"{self.prog}: error: {message}\n")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="agent_bootstrap.py")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    command = sub.add_parser("doctor")
    command.add_argument("--repo", required=True)
    command.add_argument("--expected-epoch", required=True)
    command.add_argument("--expected-profile", required=True)
    command.add_argument("--expected-workflow-version", required=True)
    command.add_argument("--json", action="store_true", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = doctor(args.repo, args.expected_epoch, args.expected_profile, args.expected_workflow_version)
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
