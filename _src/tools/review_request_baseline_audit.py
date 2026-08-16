#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduce Feature 0021 review-request defects in isolated Git exports.

The audit reads immutable Git objects, extracts only pinned historical paths
into system temporary directories, redirects every historical queue constant
to another temporary directory, and compares the repository status plus real
``_src/spec/*-queue`` stores before and after the probes.

This tool intentionally confirms the historical defects. A case passes when
its pinned defective observation is reproduced; fixed-behavior assertions are
owned by the later Feature 0033 tasks listed in the manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import html.parser
import importlib.util
import io
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


MANIFEST_SCHEMA = "review-request-historical-baseline-manifest@v1"
REPORT_SCHEMA = "review-request-historical-baseline-report@v1"
DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "review_request_baseline"
    / "manifest-v1.json"
)
FINDING_RE = re.compile(r"^RRB-[A-Z]+-[0-9]{3}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AuditError(RuntimeError):
    """Raised when the baseline contract or isolated execution is invalid."""


class _ReviewPageParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture_payload = False
        self._payload_parts: List[str] = []
        self.payloads: List[Dict[str, Any]] = []
        self.noscript_count = 0
        self.trigger_buttons = 0
        self.review_links: List[str] = []

    @staticmethod
    def _attrs(attrs: Iterable[Tuple[str, Optional[str]]]) -> Dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        values = self._attrs(attrs)
        classes = set(values.get("class", "").split())
        if tag == "noscript":
            self.noscript_count += 1
        if tag == "script" and "review-request-data" in classes:
            self._capture_payload = True
            self._payload_parts = []
        if tag == "button" and (
            "review-request-trigger" in classes or "data-review-request-open" in values
        ):
            self.trigger_buttons += 1
        if tag == "a" and values.get("href") and (
            "review-request" in values.get("class", "")
            or "data-review-request-open" in values
            or "flag-for-review" in values.get("href", "").lower()
        ):
            self.review_links.append(values["href"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._capture_payload:
            raw = "".join(self._payload_parts).strip()
            try:
                value = json.loads(raw)
            except (TypeError, ValueError):
                value = None
            if isinstance(value, dict):
                self.payloads.append(value)
            self._capture_payload = False
            self._payload_parts = []

    def handle_data(self, data: str) -> None:
        if self._capture_payload:
            self._payload_parts.append(data)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bounded_tail(value: str, max_lines: int = 20, max_bytes: int = 8192) -> str:
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) > max_bytes:
        encoded = encoded[-max_bytes:]
        value = encoded.decode("utf-8", errors="replace")
    lines = value.splitlines()
    return "\n".join(lines[-max_lines:])


def _display_arg(value: str, replacements: Optional[Dict[str, str]]) -> str:
    if not replacements:
        return value
    result = value
    for actual, display in sorted(replacements.items(), key=lambda item: -len(item[0])):
        result = result.replace(actual, display)
    return result


def _run_command(
    argv: Sequence[str],
    cwd: Path,
    commands: List[Dict[str, Any]],
    *,
    timeout: int = 30,
    check: bool = False,
    env: Optional[Dict[str, str]] = None,
    cwd_label: str = "<repo>",
    replacements: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess[bytes]:
    started = time.monotonic()
    try:
        result = subprocess.run(
            list(argv),
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        commands.append(
            {
                "argv": [_display_arg(str(arg), replacements) for arg in argv],
                "cwd": cwd_label,
                "exit_code": None,
                "timed_out": True,
                "timeout_seconds": timeout,
            }
        )
        raise AuditError("command timed out after %ss: %s" % (timeout, " ".join(argv))) from exc

    commands.append(
        {
            "argv": [_display_arg(str(arg), replacements) for arg in argv],
            "cwd": cwd_label,
            "exit_code": result.returncode,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "stdout_sha256": _sha256_bytes(result.stdout),
            "stdout_bytes": len(result.stdout),
            "stderr_tail": _bounded_tail(result.stderr.decode("utf-8", errors="replace")),
        }
    )
    if check and result.returncode != 0:
        detail = _bounded_tail(result.stderr.decode("utf-8", errors="replace"))
        raise AuditError("command failed (%s): %s\n%s" % (
            result.returncode,
            " ".join(argv),
            detail,
        ))
    return result



def _git_show(
    root: Path,
    spec: str,
    commands: List[Dict[str, Any]],
    *,
    check: bool = True,
) -> bytes:
    return _run_command(
        ["git", "--no-pager", "show", spec],
        root,
        commands,
        check=check,
        timeout=30,
    ).stdout


def _load_manifest(path: Path) -> Tuple[Dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise AuditError("cannot load manifest %s: %s" % (path, exc)) from exc
    if not isinstance(value, dict) or value.get("schema") != MANIFEST_SCHEMA:
        raise AuditError("unsupported baseline manifest schema")

    findings = value.get("findings")
    if not isinstance(findings, list) or not findings:
        raise AuditError("manifest findings must be a non-empty array")
    ids = [finding.get("id") for finding in findings if isinstance(finding, dict)]
    if len(ids) != len(findings) or len(ids) != len(set(ids)):
        raise AuditError("manifest finding IDs must be present and unique")
    if any(not isinstance(item, str) or FINDING_RE.fullmatch(item) is None for item in ids):
        raise AuditError("manifest contains an invalid finding ID")

    later = value.get("later_task_ids")
    if not isinstance(later, list) or len(later) != len(set(later)):
        raise AuditError("later_task_ids must be a unique array")
    mapped = {
        task
        for finding in findings
        for task in finding.get("forward_tasks", [])
        if isinstance(task, str)
    }
    missing = sorted(set(later) - mapped)
    if missing:
        raise AuditError("later tasks without a finding mapping: %s" % ", ".join(missing))

    for ref in value.get("historical_refs", []):
        if not SHA1_RE.fullmatch(str(ref.get("commit", ""))):
            raise AuditError("invalid historical commit in manifest")
        if not SHA1_RE.fullmatch(str(ref.get("tree", ""))):
            raise AuditError("invalid historical tree in manifest")
    for artifact in value.get("artifacts", []):
        if not SHA1_RE.fullmatch(str(artifact.get("ref", ""))):
            raise AuditError("invalid artifact ref in manifest")
        if not SHA256_RE.fullmatch(str(artifact.get("sha256", ""))):
            raise AuditError("invalid artifact sha256 in manifest")
        path_value = artifact.get("path")
        if not isinstance(path_value, str) or path_value.startswith("/") or ".." in Path(path_value).parts:
            raise AuditError("invalid artifact path in manifest")
    return value, raw


def _git_status_snapshot(root: Path, commands: List[Dict[str, Any]]) -> Dict[str, Any]:
    result = _run_command(
        [
            "git",
            "--no-optional-locks",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        root,
        commands,
        check=True,
    )
    lines = result.stdout.splitlines()
    return {
        "sha256": _sha256_bytes(result.stdout),
        "entry_count": len(lines),
    }


def _snapshot_tree(path: Path) -> Dict[str, Any]:
    if not path.exists() and not path.is_symlink():
        return {"exists": False, "sha256": _sha256_bytes(b"missing\n"), "file_count": 0}
    digest = hashlib.sha256()
    file_count = 0
    root = path.parent
    candidates = [path]
    if path.is_dir() and not path.is_symlink():
        candidates.extend(sorted(path.rglob("*"), key=lambda item: item.as_posix()))
    for candidate in candidates:
        relative = candidate.relative_to(root).as_posix()
        if candidate.is_symlink():
            payload = os.readlink(str(candidate)).encode("utf-8", errors="surrogateescape")
            digest.update(b"L\0" + relative.encode("utf-8") + b"\0" + payload + b"\n")
        elif candidate.is_dir():
            digest.update(b"D\0" + relative.encode("utf-8") + b"\n")
        elif candidate.is_file():
            data = candidate.read_bytes()
            digest.update(
                b"F\0"
                + relative.encode("utf-8")
                + b"\0"
                + str(len(data)).encode("ascii")
                + b"\0"
                + hashlib.sha256(data).digest()
                + b"\n"
            )
            file_count += 1
        else:
            digest.update(b"O\0" + relative.encode("utf-8") + b"\n")
    return {"exists": True, "sha256": digest.hexdigest(), "file_count": file_count}


def _queue_snapshot(root: Path) -> Dict[str, Dict[str, Any]]:
    spec_root = root / "_src" / "spec"
    queue_paths = sorted(spec_root.glob("*-queue"), key=lambda item: item.name)
    return {path.relative_to(root).as_posix(): _snapshot_tree(path) for path in queue_paths}


def _verify_refs(
    root: Path, manifest: Dict[str, Any], commands: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], bool]:
    results = []
    success = True
    for expected in manifest["historical_refs"]:
        commit = expected["commit"]
        result = _run_command(
            ["git", "--no-pager", "show", "-s", "--format=%H %T", commit],
            root,
            commands,
            check=False,
        )
        fields = result.stdout.decode("ascii", errors="replace").strip().split()
        actual_commit = fields[0] if len(fields) == 2 else None
        actual_tree = fields[1] if len(fields) == 2 else None
        matched = (
            result.returncode == 0
            and actual_commit == expected["commit"]
            and actual_tree == expected["tree"]
        )
        success = success and matched
        results.append(
            {
                "task_id": expected["task_id"],
                "expected_commit": expected["commit"],
                "actual_commit": actual_commit,
                "expected_tree": expected["tree"],
                "actual_tree": actual_tree,
                "matched": matched,
            }
        )
    return results, success


def _verify_artifacts(
    root: Path, manifest: Dict[str, Any], commands: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], bool]:
    results = []
    success = True
    for expected in manifest["artifacts"]:
        spec = "%s:%s" % (expected["ref"], expected["path"])
        result = _run_command(
            ["git", "--no-pager", "show", spec],
            root,
            commands,
            check=False,
        )
        actual = _sha256_bytes(result.stdout) if result.returncode == 0 else None
        matched = result.returncode == 0 and actual == expected["sha256"]
        success = success and matched
        results.append(
            {
                "task_id": expected["task_id"],
                "ref": expected["ref"],
                "path": expected["path"],
                "expected_sha256": expected["sha256"],
                "actual_sha256": actual,
                "size": len(result.stdout) if result.returncode == 0 else None,
                "matched": matched,
            }
        )
    return results, success


def _verify_local_claims(
    root: Path, manifest: Dict[str, Any], commands: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], bool]:
    results = []
    success = True
    for claim in manifest["local_closure_claims"]:
        label_result = _run_command(
            [
                "git",
                "--no-pager",
                "rev-parse",
                "--verify",
                "--quiet",
                "%s^{object}" % claim["label"],
            ],
            root,
            commands,
            check=False,
        )
        label_resolves = label_result.returncode == 0
        checkpoint = claim["contextual_checkpoint"]
        checkpoint_result = _run_command(
            ["git", "--no-pager", "show", "-s", "--format=%T", checkpoint],
            root,
            commands,
            check=False,
        )
        checkpoint_available = checkpoint_result.returncode == 0
        actual_tree = (
            checkpoint_result.stdout.decode("ascii", errors="replace").strip()
            if checkpoint_available
            else None
        )
        tree_matches = not checkpoint_available or actual_tree == claim["contextual_tree"]
        matched = not label_resolves and tree_matches
        success = success and matched
        results.append(
            {
                "task_id": claim["task_id"],
                "label": claim["label"],
                "label_resolves": label_resolves,
                "disposition": claim["disposition"],
                "contextual_checkpoint": checkpoint,
                "contextual_checkpoint_available": checkpoint_available,
                "expected_contextual_tree": claim["contextual_tree"],
                "actual_contextual_tree": actual_tree,
                "contextual_tree_matched_if_available": tree_matches,
                "evidence_credit": "none",
                "matched": matched,
            }
        )
    return results, success


def _safe_extract_tar(raw: bytes, destination: Path) -> None:
    destination_resolved = destination.resolve()
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        members = archive.getmembers()
        for member in members:
            member_path = (destination / member.name).resolve()
            try:
                common = os.path.commonpath([str(destination_resolved), str(member_path)])
            except ValueError as exc:
                raise AuditError("invalid archive path: %s" % member.name) from exc
            if common != str(destination_resolved):
                raise AuditError("archive path escapes temporary root: %s" % member.name)
            if member.issym() or member.islnk():
                raise AuditError("historical probe archive contains a link: %s" % member.name)
        archive.extractall(str(destination), members=members)


def _export_paths(
    root: Path,
    export: Dict[str, Any],
    destination: Path,
    commands: List[Dict[str, Any]],
) -> Dict[str, Any]:
    argv = ["git", "--no-pager", "archive", "--format=tar", export["ref"], "--"]
    argv.extend(export["paths"])
    result = _run_command(argv, root, commands, check=True, timeout=60)
    _safe_extract_tar(result.stdout, destination)
    missing = [path for path in export["paths"] if not (destination / path).exists()]
    if missing:
        raise AuditError("historical export omitted paths: %s" % ", ".join(missing))
    return {
        "ref": export["ref"],
        "path_count": len(export["paths"]),
        "tar_sha256": _sha256_bytes(result.stdout),
        "tar_size": len(result.stdout),
    }


_VALIDATOR_PROBE = r'''
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
sys.path.insert(0, str(root / "_src" / "tools"))
import review_request_package as rrp

fixture = root / "_src" / "tests" / "fixtures" / "review_request" / "valid_json_export.json"
package = json.loads(fixture.read_text(encoding="utf-8"))
package.update({
    "client_schema_version": [1, 0, 0],
    "target_status_snapshot": {"server_owned": True},
    "source_url": {"scheme": "javascript"},
    "rationale": ["not", "a", "string"],
    "actor_claim": {"display_name": 17, "identity_kind": "self_declared"},
    "evidence_refs": [{"kind": 7, "value": {"nested": True}}],
    "trust": {"verified": True, "authoritative_actor": "caller-authored"},
    "received_at": "2026-08-15T00:00:00Z",
    "server_timestamp": "2026-08-15T00:00:00Z",
    "session_id": "reserved-client-value"
})
accepted_errors = rrp.validate(package)
integer_package = dict(package)
integer_package["request_id"] = 7
exception = None
try:
    rrp.validate(integer_package)
except Exception as exc:
    exception = {"type": type(exc).__name__, "message": str(exc)}
print(json.dumps({"accepted_errors": accepted_errors, "exception": exception}, sort_keys=True))
'''


_INGESTION_PROBE = r'''
import json
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
sys.path.insert(0, str(root / "_src" / "tools"))
import curation_flags as cf
import curation_item as ci
import review_request_ingest as rri

fixture = root / "_src" / "tests" / "fixtures" / "review_request" / "valid_json_export.json"
package = json.loads(fixture.read_text(encoding="utf-8"))
original_queue = cf.QUEUE
with tempfile.TemporaryDirectory(prefix="review-request-baseline-queue-") as temporary:
    queue = Path(temporary) / "curation-queue"
    cf.QUEUE = queue
    cf.OPEN_DIR = queue / "open"
    cf.CLAIMED_DIR = queue / "claimed"
    cf.DONE_DIR = queue / "done"
    report = rri.ingest(package, apply=True)
    written = Path(report["path"])
    raw = json.loads(written.read_text(encoding="utf-8"))
    normalized = ci.from_curation_flag(raw)
    result = {
        "outcome": report["outcome"],
        "live_arguments_omitted": True,
        "queue_redirected": cf.QUEUE != original_queue,
        "written_name": written.name,
        "written_inside_temporary_queue": queue in written.parents,
        "raw_id": raw.get("id"),
        "raw_canonical_id": raw.get("canonical_id"),
        "target_canonical_id": package["target_canonical_id"],
        "normalized_canonical_id": normalized.get("canonical_id"),
        "normalized_origin": normalized.get("origin"),
        "normalized_status": normalized.get("status"),
        "normalized_item_kind": normalized.get("item_kind"),
        "normalized_conformant": ci.is_conformant(normalized)
    }
print(json.dumps(result, sort_keys=True))
'''


def _run_json_probe(
    code: str,
    export_root: Path,
    label: str,
    commands: List[Dict[str, Any]],
) -> Dict[str, Any]:
    script = export_root / (label + ".py")
    script.write_text(code, encoding="utf-8")
    replacements = {
        str(export_root): "<isolated-%s-export>" % label,
        str(script): "<isolated-%s-probe>" % label,
        sys.executable: "<python>",
    }
    result = _run_command(
        [sys.executable, str(script), str(export_root)],
        export_root,
        commands,
        check=True,
        timeout=30,
        cwd_label="<isolated-%s-export>" % label,
        replacements=replacements,
    )
    try:
        value = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise AuditError("%s probe returned invalid JSON" % label) from exc
    if not isinstance(value, dict):
        raise AuditError("%s probe did not return an object" % label)
    return value


def _validator_cases(actual: Dict[str, Any]) -> List[Dict[str, Any]]:
    malformed_observed = actual.get("accepted_errors") == []
    exception = actual.get("exception") or {}
    type_error_observed = exception.get("type") == "TypeError"
    return [
        {
            "id": "RRB-SCHEMA-001",
            "source_ref": "3cfdbe72b097b971ef9fd9d4757eed37bef93e1b",
            "expected": "malformed types and reserved trust/server fields are accepted",
            "actual": {"validation_errors": actual.get("accepted_errors")},
            "observed": malformed_observed,
        },
        {
            "id": "RRB-SCHEMA-002",
            "source_ref": "3cfdbe72b097b971ef9fd9d4757eed37bef93e1b",
            "expected": "integer request_id raises TypeError",
            "actual": exception,
            "observed": type_error_observed,
        },
    ]


def _ingestion_cases(actual: Dict[str, Any]) -> List[Dict[str, Any]]:
    apply_observed = all(
        [
            actual.get("outcome") == "ok",
            actual.get("live_arguments_omitted") is True,
            actual.get("queue_redirected") is True,
            actual.get("written_inside_temporary_queue") is True,
        ]
    )
    mapping_observed = all(
        [
            actual.get("raw_canonical_id") is None,
            actual.get("raw_id", "").startswith("review-request:"),
            actual.get("normalized_canonical_id") != actual.get("target_canonical_id"),
            actual.get("normalized_canonical_id", "").endswith(actual.get("raw_id", "__missing__")),
            actual.get("normalized_origin") == "curator",
            actual.get("normalized_status") == "proposed",
            actual.get("normalized_item_kind") == "review-request",
            actual.get("normalized_conformant") is False,
        ]
    )
    return [
        {
            "id": "RRB-INGEST-001",
            "source_ref": "a03be1e6735f940da1e6e62ba9a408077e6143cb",
            "expected": "apply=True succeeds with both live-target arguments omitted",
            "actual": {
                key: actual.get(key)
                for key in (
                    "outcome",
                    "live_arguments_omitted",
                    "queue_redirected",
                    "written_inside_temporary_queue",
                    "written_name",
                )
            },
            "observed": apply_observed,
        },
        {
            "id": "RRB-QUEUE-001",
            "source_ref": "a03be1e6735f940da1e6e62ba9a408077e6143cb",
            "expected": "written item maps canonical/status/origin/item kind incorrectly and fails conformance",
            "actual": {
                key: actual.get(key)
                for key in (
                    "raw_id",
                    "raw_canonical_id",
                    "target_canonical_id",
                    "normalized_canonical_id",
                    "normalized_origin",
                    "normalized_status",
                    "normalized_item_kind",
                    "normalized_conformant",
                )
            },
            "observed": mapping_observed,
        },
    ]


def _production_cases(
    root: Path, manifest: Dict[str, Any], commands: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    expected = manifest["production_page"]
    raw = _git_show(root, "%s:%s" % (expected["ref"], expected["path"]), commands)
    parser = _ReviewPageParser()
    parser.feed(raw.decode("utf-8"))
    parser.close()
    payload = next(
        (
            item
            for item in parser.payloads
            if item.get("canonical_id") == expected["record_id"]
        ),
        None,
    )
    expected_payload = expected["expected_payload"]
    payload_observed = isinstance(payload, dict) and all(
        payload.get(key) == value for key, value in expected_payload.items()
    )
    no_js_observed = (
        parser.trigger_buttons > 0
        and parser.noscript_count == 0
        and not parser.review_links
    )
    detail = {
        "payload": payload,
        "payload_count": len(parser.payloads),
        "trigger_button_count": parser.trigger_buttons,
        "noscript_count": parser.noscript_count,
        "review_link_count": len(parser.review_links),
        "page_sha256": _sha256_bytes(raw),
    }
    return [
        {
            "id": "RRB-META-001",
            "source_ref": expected["ref"],
            "source_path": expected["path"],
            "expected": expected_payload,
            "actual": payload,
            "observed": payload_observed,
        },
        {
            "id": "RRB-NOJS-001",
            "source_ref": expected["ref"],
            "source_path": expected["path"],
            "expected": "JavaScript button present with no noscript or review intake link",
            "actual": {
                "trigger_button_count": parser.trigger_buttons,
                "noscript_count": parser.noscript_count,
                "review_link_count": len(parser.review_links),
            },
            "observed": no_js_observed,
        },
    ], detail


def _browser_coverage_case(
    root: Path, commands: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    ref = "62f638bfd9ff956e417ef617dbcab160448b8406"
    test_text = _git_show(root, ref + ":_src/tests/test_review_request_browser.py", commands).decode("utf-8")
    checker_text = _git_show(root, ref + ":_src/tools/check_review_request_ui.cjs", commands).decode("utf-8")
    checks = {
        "webkit_only": "const { webkit } = require('playwright')" in checker_text
        and "chromium" not in checker_text
        and "firefox" not in checker_text,
        "single_mobile_viewport": "width: 390, height: 844" in checker_text,
        "synthetic_complete_metadata": "'review_request': {" in test_text
        and "'source_url': 'https://example.invalid/spec.pdf'" in test_text,
        "identity_preseeded": "localStorage.setItem('ara-review-identity'" in checker_text,
        "export_only": "page.click('[data-export]'" in checker_text
        and "data-submit" not in checker_text,
        "server_payload_read": "locator('.review-request-data').innerText()" in checker_text,
        "download_bytes_unchecked": "expect_download" not in test_text.lower()
        and "download" not in checker_text.lower(),
        "no_nojs_coverage": "noscript" not in test_text.lower()
        and "javascript_enabled" not in test_text.lower(),
    }
    observed = all(checks.values())
    return {
        "id": "RRB-BROWSER-001",
        "source_ref": ref,
        "expected": "single synthetic WebKit/mobile/export path does not inspect downloaded bytes or no-JS behavior",
        "actual": checks,
        "observed": observed,
    }, checks


def _historical_tests(
    root: Path,
    export: Dict[str, Any],
    commands: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="review-request-baseline-tests-") as temporary:
        export_root = Path(temporary)
        export_info = _export_paths(root, export, export_root, commands)
        dependency_shims: List[Dict[str, Any]] = []
        if importlib.util.find_spec("lxml") is None:
            # lib_docmodel imports lxml at module load, but none of the 25
            # historical review-request tests exercises an lxml API. The shim
            # fails on any attribute access, preserving that boundary rather
            # than silently emulating parser behavior.
            shim_source = '''class _FailOnUse:\n    def __getattr__(self, name):\n        raise RuntimeError("temporary lxml import shim was used: " + name)\n\netree = _FailOnUse()\nhtml = _FailOnUse()\n'''
            shim_path = export_root / "lxml" / "__init__.py"
            shim_path.parent.mkdir(parents=True, exist_ok=True)
            shim_path.write_text(shim_source, encoding="utf-8")
            dependency_shims.append(
                {
                    "module": "lxml",
                    "reason": "module unavailable; fail-on-use import shim for unexercised lib_docmodel dependency",
                    "sha256": _sha256_bytes(shim_source.encode("utf-8")),
                }
            )
        env = dict(os.environ)
        node_modules = root / "output" / "npm-prefix" / "node_modules"
        if node_modules.is_dir():
            existing = env.get("NODE_PATH", "")
            env["NODE_PATH"] = str(node_modules) + (os.pathsep + existing if existing else "")
        replacements = {
            str(export_root): "<isolated-historical-test-export>",
            sys.executable: "<python>",
            str(root): "<repo>",
        }
        argv = [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "_src/tests",
            "-p",
            export["pattern"],
        ]
        result = _run_command(
            argv,
            export_root,
            commands,
            timeout=120,
            check=False,
            env=env,
            cwd_label="<isolated-historical-test-export>",
            replacements=replacements,
        )
        combined = (result.stdout + b"\n" + result.stderr).decode("utf-8", errors="replace")
        match = re.search(r"Ran ([0-9]+) tests?", combined)
        count = int(match.group(1)) if match else None
        actual = {
            "exit_code": result.returncode,
            "test_count": count,
            "expected_test_count": export["expected_count"],
            "summary_tail": _bounded_tail(combined, max_lines=8, max_bytes=4096),
            "export": export_info,
            "dependency_shims": dependency_shims,
        }
        observed = result.returncode == 0 and count == export["expected_count"]
        return {
            "id": "RRB-VALID-001",
            "source_ref": export["ref"],
            "expected": "%s historical focused tests pass" % export["expected_count"],
            "actual": actual,
            "observed": observed,
        }, actual


def _tool_version(
    argv: Sequence[str], root: Path, commands: List[Dict[str, Any]]
) -> Optional[str]:
    result = _run_command(argv, root, commands, check=False, timeout=10)
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace").strip()


def run_audit(
    root: Path,
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    run_historical_tests: bool = True,
) -> Dict[str, Any]:
    """Run the isolated baseline and return a machine-readable report."""
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    manifest, manifest_raw = _load_manifest(manifest_path)
    commands: List[Dict[str, Any]] = []
    started_at = _utc_now()

    worktree_before = _git_status_snapshot(root, commands)
    queues_before = _queue_snapshot(root)

    environment = {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "git_version": _tool_version(["git", "--version"], root, commands),
        "node_version": _tool_version(["node", "--version"], root, commands),
    }
    head_result = _run_command(
        ["git", "--no-pager", "rev-parse", "HEAD"],
        root,
        commands,
        check=True,
    )
    head = head_result.stdout.decode("ascii").strip()

    refs, refs_ok = _verify_refs(root, manifest, commands)
    artifacts, artifacts_ok = _verify_artifacts(root, manifest, commands)
    local_claims, local_claims_ok = _verify_local_claims(root, manifest, commands)

    cases: List[Dict[str, Any]] = []
    details: Dict[str, Any] = {}
    input_ok = refs_ok and artifacts_ok and local_claims_ok
    if input_ok:
        with tempfile.TemporaryDirectory(prefix="review-request-baseline-validator-") as temporary:
            export_root = Path(temporary)
            details["validator_export"] = _export_paths(
                root, manifest["probe_exports"]["validator"], export_root, commands
            )
            validator_actual = _run_json_probe(
                _VALIDATOR_PROBE, export_root, "validator", commands
            )
            details["validator_probe"] = validator_actual
            cases.extend(_validator_cases(validator_actual))

        with tempfile.TemporaryDirectory(prefix="review-request-baseline-ingestion-") as temporary:
            export_root = Path(temporary)
            details["ingestion_export"] = _export_paths(
                root, manifest["probe_exports"]["ingestion"], export_root, commands
            )
            ingestion_actual = _run_json_probe(
                _INGESTION_PROBE, export_root, "ingestion", commands
            )
            details["ingestion_probe"] = ingestion_actual
            cases.extend(_ingestion_cases(ingestion_actual))

        production_cases, production_detail = _production_cases(root, manifest, commands)
        details["production_page"] = production_detail
        cases.extend(production_cases)

        browser_case, browser_detail = _browser_coverage_case(root, commands)
        details["browser_coverage"] = browser_detail
        cases.append(browser_case)

        if run_historical_tests:
            historical_case, historical_detail = _historical_tests(
                root, manifest["probe_exports"]["historical_tests"], commands
            )
            details["historical_tests"] = historical_detail
            cases.append(historical_case)
        else:
            details["historical_tests"] = {"skipped": True}

    worktree_after = _git_status_snapshot(root, commands)
    queues_after = _queue_snapshot(root)
    worktree_unchanged = worktree_before == worktree_after
    queues_unchanged = queues_before == queues_after
    mutation_guard = {
        "worktree_before": worktree_before,
        "worktree_after": worktree_after,
        "worktree_unchanged": worktree_unchanged,
        "queue_roots_before": queues_before,
        "queue_roots_after": queues_after,
        "queue_roots_unchanged": queues_unchanged,
    }

    observed_cases = all(case.get("observed") is True for case in cases)
    complete = input_ok and run_historical_tests and observed_cases and worktree_unchanged and queues_unchanged
    success = input_ok and observed_cases and worktree_unchanged and queues_unchanged
    if run_historical_tests and not complete:
        success = False

    report = {
        "schema": REPORT_SCHEMA,
        "task_id": manifest["task_id"],
        "manifest_version": manifest["version"],
        "started_at": started_at,
        "finished_at": _utc_now(),
        "repository_head": head,
        "environment": environment,
        "inputs": {
            "manifest_path": manifest_path.relative_to(root).as_posix()
            if root in manifest_path.parents
            else str(manifest_path),
            "manifest_sha256": _sha256_bytes(manifest_raw),
            "audit_tool_path": Path(__file__).resolve().relative_to(root).as_posix(),
            "audit_tool_sha256": _sha256_file(Path(__file__).resolve()),
            "historical_refs": refs,
            "artifacts": artifacts,
            "local_closure_claims": local_claims,
            "cumulative_context": manifest["cumulative_context"],
        },
        "cases": cases,
        "pending_forward_findings": manifest["findings"],
        "details": details,
        "mutation_guard": mutation_guard,
        "commands": commands,
        "summary": {
            "input_contract_matched": input_ok,
            "case_count": len(cases),
            "observed_case_count": sum(case.get("observed") is True for case in cases),
            "historical_tests_executed": run_historical_tests,
            "evidence_complete": complete,
            "success": success,
        },
    }
    return report


def _validate_output_path(root: Path, output: Path) -> Path:
    output = output.resolve()
    allowed = [
        (root / "output" / "logs").resolve(),
        (root / "logs" / "review-request-baseline").resolve(),
    ]
    if not any(os.path.commonpath([str(base), str(output)]) == str(base) for base in allowed):
        raise AuditError(
            "output must be under output/logs/ or logs/review-request-baseline/"
        )
    return output


def _write_report(path: Path, report: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    temporary = path.with_name(path.name + ".tmp-%s" % os.getpid())
    temporary.write_bytes(raw)
    os.replace(str(temporary), str(path))


def main(argv: Optional[Sequence[str]] = None) -> int:
    description = (__doc__ or "Historical review-request baseline audit.").splitlines()[0]
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="pinned baseline manifest (default: %(default)s)",
    )
    parser.add_argument("--output", type=Path, required=True, help="JSON report path")
    parser.add_argument(
        "--skip-historical-tests",
        action="store_true",
        help="skip the 25-test historical suite; produces incomplete evidence",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    try:
        output = _validate_output_path(root, args.output)
        report = run_audit(
            root,
            args.manifest,
            run_historical_tests=not args.skip_historical_tests,
        )
        _write_report(output, report)
    except AuditError as exc:
        print("baseline-audit: FAIL: %s" % exc, file=sys.stderr)
        return 2

    summary = report["summary"]
    print(
        "baseline-audit: %s; cases=%s/%s; historical-tests=%s; queues/worktree-unchanged=%s/%s"
        % (
            "PASS" if summary["success"] else "FAIL",
            summary["observed_case_count"],
            summary["case_count"],
            "executed" if summary["historical_tests_executed"] else "skipped",
            report["mutation_guard"]["queue_roots_unchanged"],
            report["mutation_guard"]["worktree_unchanged"],
        )
    )
    print("report: %s" % output)
    print("report-sha256: %s" % _sha256_file(output))
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
