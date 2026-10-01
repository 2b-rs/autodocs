#!/usr/bin/env python3
"""Common provenance envelope for scrape and extraction report producers (0037-26.01).

Family (0037-37 / chore inventory at the merged base):
  - ``spec_scrape.py`` call sites ``phase_crosscheck``, ``write_traceability_records``
  - ``extraction_report.py`` assemble/build
  - ``score_scrape.py`` JSON scrape report

Uses shared ``provenance_store`` schemas and ``provenance_query`` indexes.
Does not invent legacy history: missing commits stay unknown rather than guessed.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent.parent

_STORE_SPEC = importlib.util.spec_from_file_location(
    "provenance_store", _TOOLS / "provenance_store.py"
)
assert _STORE_SPEC and _STORE_SPEC.loader
ps = importlib.util.module_from_spec(_STORE_SPEC)
sys.modules.setdefault("provenance_store", ps)
_STORE_SPEC.loader.exec_module(ps)

_VID_SPEC = importlib.util.spec_from_file_location("version_id", _TOOLS / "version_id.py")
assert _VID_SPEC and _VID_SPEC.loader
vid = importlib.util.module_from_spec(_VID_SPEC)
_VID_SPEC.loader.exec_module(vid)

_PQ_SPEC = importlib.util.spec_from_file_location(
    "provenance_query", _TOOLS / "provenance_query.py"
)
assert _PQ_SPEC and _PQ_SPEC.loader
pq = importlib.util.module_from_spec(_PQ_SPEC)
_PQ_SPEC.loader.exec_module(pq)

SCHEMA = "scrape-extraction-provenance-envelope@v1"
# Bind writers to 0037-17/19 schema files; do not fork local copies.
REPO_SCHEMA_DIR = _ROOT / "provenance" / "_schema"
BOUND_SCHEMAS = {
    "typed-reference": "typed-reference-v1.schema.json",
    "run": "run-v1.schema.json",
    "finding": "finding-v1.schema.json",
    "artifact-set": "artifact-set-v1.schema.json",
    "event": "provenance-event-v1.schema.json",
}
PRODUCERS = frozenset(
    {
        "spec_scrape.phase_crosscheck",
        "spec_scrape.write_traceability_records",
        "extraction_report.assemble",
        "score_scrape.report",
    }
)


class ScrapeExtractionProvenanceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_bound_schema(kind: str, schema_dir: Optional[Path] = None) -> Dict[str, Any]:
    directory = Path(schema_dir) if schema_dir else REPO_SCHEMA_DIR
    name = BOUND_SCHEMAS[kind]
    path = directory / name
    if not path.is_file():
        raise ScrapeExtractionProvenanceError(
            "SEP-SCHEMA-MISSING", f"required schema {name} absent at {path}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def validate_against_bound_schema(kind: str, record: Mapping[str, Any], schema_dir: Optional[Path] = None) -> None:
    """Fail closed on extra properties or missing required fields vs provenance/_schema."""
    schema = load_bound_schema(kind, schema_dir)
    allowed = set(schema.get("properties") or {})
    extra = set(record) - allowed
    if extra and schema.get("additionalProperties") is False:
        raise ScrapeExtractionProvenanceError(
            "SEP-SCHEMA-DEVIATION",
            f"{kind} fields {sorted(extra)} are not in {BOUND_SCHEMAS[kind]} (finding, not a local fork)",
        )
    for key in schema.get("required") or []:
        if key not in record:
            raise ScrapeExtractionProvenanceError(
                "SEP-SCHEMA-DEVIATION",
                f"{kind} missing required {key} from {BOUND_SCHEMAS[kind]}",
            )


def _put_event(store: Any, payload: Mapping[str, Any]) -> Dict[str, Any]:
    result = store.create_event(payload)
    validate_against_bound_schema("event", result["record"])
    return result


def typed_ref(kind: str, ident: str, **extra: Any) -> Dict[str, Any]:
    uri = ident if str(ident).startswith(kind + ":") else f"{kind}:{ident}"
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": uri,
        "classification": extra.pop("classification", "internal"),
    }
    value.update(extra)
    return value


def _require_commit(value: str, field: str) -> str:
    if not isinstance(value, str) or not ps.COMMIT_RE.match(value):
        raise ScrapeExtractionProvenanceError(
            "SEP-COMMIT", f"{field} must be a reachable 40-hex commit, not a path or mtime"
        )
    return value


def validate_input_members(members: Sequence[Mapping[str, Any]], file_bytes: Mapping[str, bytes]) -> List[Dict[str, Any]]:
    """Reject path-only, mtime-only, and digest-mismatched member identity."""
    if not members:
        raise ScrapeExtractionProvenanceError("SEP-INPUTS", "exact input artifact set is required")
    normalized: List[Dict[str, Any]] = []
    seen = set()
    for raw in members:
        obj = dict(raw)
        if "mtime" in obj or "mtime_ns" in obj or "modified" in obj:
            if "digest" not in obj:
                raise ScrapeExtractionProvenanceError(
                    "SEP-MTIME-ONLY",
                    "mtime is not evidence identity; content digest is required",
                )
            raise ScrapeExtractionProvenanceError(
                "SEP-MTIME-ONLY",
                "mtime must not participate in scrape/extraction evidence identity",
            )
        path = obj.get("path")
        if not path or not isinstance(path, str):
            raise ScrapeExtractionProvenanceError("SEP-MEMBER", "member path required")
        if path in seen:
            raise ScrapeExtractionProvenanceError("SEP-MEMBER", f"duplicate member path {path}")
        seen.add(path)
        digest = obj.get("digest")
        if not digest:
            raise ScrapeExtractionProvenanceError(
                "SEP-PATH-ONLY",
                f"path-only provenance rejected for {path}; bind sha256 of exact source bytes",
            )
        if not ps.SHA256_RE.match(str(digest)):
            raise ScrapeExtractionProvenanceError("SEP-DIGEST", f"invalid digest for {path}")
        payload = file_bytes.get(path)
        if payload is None:
            raise ScrapeExtractionProvenanceError("SEP-BYTES", f"missing exact bytes for {path}")
        actual = sha256_bytes(payload)
        if actual != digest:
            raise ScrapeExtractionProvenanceError(
                "SEP-FABRICATED",
                f"declared digest for {path} does not match exact source bytes",
            )
        if obj.get("size_bytes") not in (None, len(payload)):
            raise ScrapeExtractionProvenanceError(
                "SEP-FABRICATED", f"size_bytes does not match exact source bytes for {path}"
            )
        commit = obj.get("source_commit")
        _require_commit(str(commit), f"member {path} source_commit")
        normalized.append(
            {
                "path": path,
                "digest": digest,
                "size_bytes": len(payload),
                "media_type": obj.get("media_type") or "application/octet-stream",
                "source_commit": commit,
            }
        )
    normalized.sort(key=lambda item: item["path"])
    return normalized


def members_from_bytes(
    files: Mapping[str, bytes],
    *,
    source_commit: str,
    media_types: Optional[Mapping[str, str]] = None,
) -> List[Dict[str, Any]]:
    _require_commit(source_commit, "source_commit")
    media_types = media_types or {}
    members = []
    for path, payload in sorted(files.items()):
        suffix = Path(path).suffix.lower()
        default_type = {
            ".pdf": "application/pdf",
            ".json": "application/json",
            ".txt": "text/plain",
            ".rst": "text/x-rst",
            ".md": "text/markdown",
            ".py": "text/x-python",
        }.get(suffix, "application/octet-stream")
        members.append(
            {
                "path": path,
                "digest": sha256_bytes(payload),
                "size_bytes": len(payload),
                "media_type": media_types.get(path, default_type),
                "source_commit": source_commit,
            }
        )
    return members


def _finding_payloads(
    *,
    disagreements: Iterable[Mapping[str, Any]],
    run_id: str,
    issue: str,
    criterion: str,
    stamp: str,
    report_digest: str,
    report_path: str,
    classification: str,
    environment: str,
) -> List[Dict[str, Any]]:
    findings = []
    for item in disagreements:
        finding_id = item.get("finding_id") or vid.uuid7()
        subject_kind = item.get("subject_kind") or "issue"
        subject_id = item.get("subject_id") or issue
        findings.append(
            {
                "schema_version": "1.0",
                "finding_id": finding_id,
                "detected_at": stamp,
                "state": "open",
                "classification": classification,
                "environment": environment,
                "subject": typed_ref(subject_kind, subject_id),
                "detected_during": typed_ref("run", run_id),
                "evidence": [
                    typed_ref(
                        "artifact",
                        f"{report_path}@{report_digest}",
                        digest=report_digest,
                    ),
                    typed_ref("criterion", criterion),
                ],
                "_cause": item.get("cause") or item.get("kind") or "backend-disagreement",
                "_detail": item.get("detail") or "",
            }
        )
    return findings


def persist_scrape_extraction_report(
    *,
    store_root: Path,
    producer: str,
    source_commit: str,
    tool_commit: str,
    config_commit: str,
    input_files: Mapping[str, bytes],
    report_path: str,
    report_bytes: bytes,
    issue: str,
    criterion: str,
    campaign: str,
    trigger_kind: str,
    trigger_id: str,
    cause: str,
    status: str = "succeeded",
    environment: str = "development-test",
    classification: str = "internal",
    started_at: Optional[str] = None,
    ended_at: Optional[str] = None,
    disagreements: Optional[Sequence[Mapping[str, Any]]] = None,
    run_id: Optional[str] = None,
    set_id: Optional[str] = None,
    claimed_run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Write run, artifact-set, findings, and causal events; return the envelope."""
    if producer not in PRODUCERS:
        raise ScrapeExtractionProvenanceError("SEP-PRODUCER", f"unknown producer {producer}")
    if claimed_run_id and run_id and claimed_run_id != run_id:
        raise ScrapeExtractionProvenanceError(
            "SEP-RUN-MISMATCH",
            "claimed run identity does not match the producing run",
        )
    _require_commit(source_commit, "source_commit")
    _require_commit(tool_commit, "tool_commit")
    _require_commit(config_commit, "config_commit")
    if status not in ps.RUN_STATUSES:
        raise ScrapeExtractionProvenanceError("SEP-STATUS", f"invalid run status {status}")

    started_at = started_at or utc_now()
    ended_at = ended_at or utc_now()
    run_id = run_id or vid.uuid7()
    set_id = set_id or vid.uuid7()
    if claimed_run_id and claimed_run_id != run_id:
        raise ScrapeExtractionProvenanceError(
            "SEP-RUN-MISMATCH", "fabricated or mismatched run id on the report"
        )

    output_files = dict(input_files)
    output_files[report_path] = report_bytes
    members = members_from_bytes(output_files, source_commit=source_commit)
    validate_input_members(
        [m for m in members if m["path"] != report_path],
        input_files,
    )
    report_digest = sha256_bytes(report_bytes)

    store = ps.ProvenanceStore(store_root, file_bytes=output_files.__getitem__)
    input_refs = [
        typed_ref("commit", source_commit),
        typed_ref("issue", issue),
        typed_ref("criterion", criterion),
        typed_ref("campaign", campaign),
    ]
    if config_commit != source_commit:
        input_refs.insert(1, typed_ref("commit", config_commit))
    run_payload = {
        "schema_version": "1.0",
        "run_id": run_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "environment": environment,
        "classification": classification,
        "status": status,
        "producer": typed_ref("commit", tool_commit),
        "inputs": input_refs,
        "outputs": [typed_ref("artifact-set", set_id)],
    }
    store.create_run(run_payload)
    validate_against_bound_schema("run", store.read_run(run_id))
    validate_against_bound_schema("typed-reference", run_payload["producer"])
    aset = store.create_artifact_set(
        {
            "schema_version": "1.0",
            "set_id": set_id,
            "created_at": ended_at,
            "classification": classification,
            "environment": environment,
            "producer": typed_ref("run", run_id),
            "members": members,
        }
    )
    validate_against_bound_schema("artifact-set", aset["record"])

    finding_records = []
    items = list(disagreements or [])
    if status == "failed" and not items:
        items = [{"kind": "producer-failure", "cause": cause, "detail": status}]
    for payload in _finding_payloads(
        disagreements=items,
        run_id=run_id,
        issue=issue,
        criterion=criterion,
        stamp=ended_at,
        report_digest=report_digest,
        report_path=report_path,
        classification=classification,
        environment=environment,
    ):
        detected = payload["detected_during"]["uri"]
        if detected != f"run:{run_id}":
            raise ScrapeExtractionProvenanceError(
                "SEP-RUN-MISMATCH",
                "finding.detected_during must be the producing run",
            )
        cause_text = payload.pop("_cause")
        detail = payload.pop("_detail")
        created = store.create_finding(payload)
        validate_against_bound_schema("finding", created["record"])
        finding_records.append({**created["record"], "cause": cause_text, "detail": detail})
        _put_event(
            store,
            {
                "schema_version": "1.0",
                "event_id": vid.uuid7(),
                "occurred_at": ended_at,
                "relation": "detected-during",
                "source": typed_ref("finding", payload["finding_id"]),
                "target": typed_ref("run", run_id),
                "environment": environment,
                "classification": classification,
                "run": typed_ref("run", run_id),
            }
        )
        _put_event(
            store,
            {
                "schema_version": "1.0",
                "event_id": vid.uuid7(),
                "occurred_at": ended_at,
                "relation": "reported-by",
                "source": typed_ref("finding", payload["finding_id"]),
                "target": typed_ref("issue", issue),
                "environment": environment,
                "classification": classification,
                "run": typed_ref("run", run_id),
            }
        )

    _put_event(
        store,
        {
            "schema_version": "1.0",
            "event_id": vid.uuid7(),
            "occurred_at": ended_at,
            "relation": "triggered",
            "source": typed_ref(trigger_kind, trigger_id),
            "target": typed_ref("run", run_id),
            "environment": environment,
            "classification": classification,
            "run": typed_ref("run", run_id),
        }
    )
    _put_event(
        store,
        {
            "schema_version": "1.0",
            "event_id": vid.uuid7(),
            "occurred_at": ended_at,
            "relation": "produced-by",
            "source": typed_ref("artifact-set", set_id),
            "target": typed_ref("run", run_id),
            "environment": environment,
            "classification": classification,
            "run": typed_ref("run", run_id),
        }
    )

    envelope = {
        "schema": SCHEMA,
        "producer": producer,
        "run_id": run_id,
        "artifact_set_id": set_id,
        "artifact_set_digest": aset["record"]["set_digest"],
        "report_digest": report_digest,
        "source_commit": source_commit,
        "tool_commit": tool_commit,
        "config_commit": config_commit,
        "issue": f"issue:{issue}" if not issue.startswith("issue:") else issue,
        "criterion": f"criterion:{criterion}" if not criterion.startswith("criterion:") else criterion,
        "campaign": f"campaign:{campaign}" if not campaign.startswith("campaign:") else campaign,
        "trigger": {"kind": trigger_kind, "id": trigger_id, "cause": cause},
        "evidence_class": environment,
        "classification": classification,
        "status": status,
        "input_digests": {path: sha256_bytes(data) for path, data in sorted(input_files.items())},
        "finding_ids": [f["finding_id"] for f in finding_records],
        "findings": [
            {"finding_id": f["finding_id"], "cause": f.get("cause"), "state": f["state"]}
            for f in finding_records
        ],
    }
    return envelope


def attach_envelope(report: Dict[str, Any], envelope: Mapping[str, Any]) -> Dict[str, Any]:
    attached = dict(report)
    attached["provenance_envelope"] = dict(envelope)
    return attached


def trace_report_to_source(
    store_root: Path,
    *,
    report_path: str,
    report_digest: str,
) -> Dict[str, Any]:
    return pq.query_trace(
        store_root,
        kind="artifact",
        identifier=f"{report_path}@{report_digest}",
        direction="reverse",
    )


def assert_not_fabricated_run(store_root: Path, run_id: str) -> None:
    path = Path(store_root) / "provenance" / "runs" / f"{run_id}.json"
    if not path.is_file():
        raise ScrapeExtractionProvenanceError(
            "SEP-FABRICATED", f"run {run_id} is not a stored producing run"
        )


def record_crosscheck_report(
    report: Dict[str, Any],
    *,
    pdf_files: Mapping[str, bytes],
    store_root: Path,
    source_commit: str,
    tool_commit: str,
    config_commit: str,
    issue: str = "0037-26.01",
    criterion: str = "AC-scrape-envelope",
    campaign: str = "scrape-extraction",
    cause: str = "spec_scrape.phase_crosscheck",
) -> Dict[str, Any]:
    disagreements = []
    for item in report.get("backend_deviations") or []:
        disagreements.append(
            {
                "kind": "backend-disagreement",
                "cause": "backend-disagreement",
                "detail": json.dumps(item, sort_keys=True, default=str),
                "subject_id": issue,
            }
        )
    status = "failed" if disagreements else "succeeded"
    raw = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    envelope = persist_scrape_extraction_report(
        store_root=store_root,
        producer="spec_scrape.phase_crosscheck",
        source_commit=source_commit,
        tool_commit=tool_commit,
        config_commit=config_commit,
        input_files=pdf_files,
        report_path="output/reports/spec-scrape-crosscheck.json",
        report_bytes=raw,
        issue=issue,
        criterion=criterion,
        campaign=campaign,
        trigger_kind="issue",
        trigger_id=issue,
        cause=cause,
        status=status,
        disagreements=disagreements,
    )
    return attach_envelope(report, envelope)


def record_traceability_write_report(
    report: Dict[str, Any],
    *,
    input_files: Mapping[str, bytes],
    store_root: Path,
    source_commit: str,
    tool_commit: str,
    config_commit: str,
    issue: str = "0037-26.01",
    criterion: str = "AC-scrape-envelope",
    campaign: str = "scrape-extraction",
) -> Dict[str, Any]:
    raw = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    envelope = persist_scrape_extraction_report(
        store_root=store_root,
        producer="spec_scrape.write_traceability_records",
        source_commit=source_commit,
        tool_commit=tool_commit,
        config_commit=config_commit,
        input_files=input_files,
        report_path="output/reports/spec-scrape-trace-write.json",
        report_bytes=raw,
        issue=issue,
        criterion=criterion,
        campaign=campaign,
        trigger_kind="issue",
        trigger_id=issue,
        cause="spec_scrape.write_traceability_records",
        status="succeeded",
    )
    return attach_envelope(report, envelope)


def record_extraction_assemble(
    page_model: Dict[str, Any],
    *,
    input_files: Mapping[str, bytes],
    store_root: Path,
    source_commit: str,
    tool_commit: str,
    config_commit: str,
    issue: str = "0037-26.01",
    criterion: str = "AC-extraction-envelope",
    campaign: str = "scrape-extraction",
) -> Dict[str, Any]:
    raw = json.dumps(page_model, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )
    envelope = persist_scrape_extraction_report(
        store_root=store_root,
        producer="extraction_report.assemble",
        source_commit=source_commit,
        tool_commit=tool_commit,
        config_commit=config_commit,
        input_files=input_files,
        report_path="_src/sources/pages/extraction-report.json",
        report_bytes=raw,
        issue=issue,
        criterion=criterion,
        campaign=campaign,
        trigger_kind="issue",
        trigger_id=issue,
        cause="extraction_report.assemble",
        status="succeeded",
    )
    return attach_envelope(page_model, envelope)


def record_score_scrape_report(
    report: Dict[str, Any],
    *,
    input_files: Mapping[str, bytes],
    store_root: Path,
    source_commit: str,
    tool_commit: str,
    config_commit: str,
    issue: str = "0037-26.01",
    criterion: str = "AC-score-scrape-envelope",
    campaign: str = "scrape-extraction",
) -> Dict[str, Any]:
    raw = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    envelope = persist_scrape_extraction_report(
        store_root=store_root,
        producer="score_scrape.report",
        source_commit=source_commit,
        tool_commit=tool_commit,
        config_commit=config_commit,
        input_files=input_files,
        report_path="output/reports/score-scrape.json",
        report_bytes=raw,
        issue=issue,
        criterion=criterion,
        campaign=campaign,
        trigger_kind="issue",
        trigger_id=issue,
        cause="score_scrape.report",
        status="succeeded",
    )
    return attach_envelope(report, envelope)


def git_head_commit(repo: Path) -> str:
    import subprocess

    return subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
    ).strip()
