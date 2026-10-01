#!/usr/bin/env python3
"""Validate normalized Eclipse S-CORE corpora and persist campaign evidence (0019-06).

The validator is read-only with respect to records and candidates.  It produces
an evidence report only; exception candidates remain ``discovered`` and are not
written to a curation/review queue until Task 0019-07.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import canonical_id
import version_id

TOOL_VERSION = "1.0.0"
REPORT_SCHEMA = "score-validation-report@v1"
CORPUS_SCHEMA = "score-normalized-corpus@v1"
RECORD_SCHEMA = "score-normalized-record@v1"
EXCEPTION_SCHEMA = "score-normalization-exception-candidate@v1"
PROJECT = "ECLIPSE/S-CORE"
SUPPORTED_KINDS = {"module", "component", "design-doc", "process-doc"}
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NEED_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")


def _finding(code: str, path: str, message: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "severity": severity, "path": path, "message": message}


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _counts(records: list[Mapping[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record.get(key, "<missing>")) for record in records).items()))


def _manifest_sources(manifest: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not _is_mapping(manifest):
        return {}
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        return {}
    return {
        str(source.get("repository_url")): source
        for source in sources
        if _is_mapping(source) and isinstance(source.get("repository_url"), str)
    }


def _validate_provenance(
    record: Mapping[str, Any], path: str, manifest_sources: Mapping[str, Mapping[str, Any]], findings: list[dict[str, str]]
) -> Mapping[str, Any] | None:
    provenance = record.get("provenance")
    if not _is_mapping(provenance):
        findings.append(_finding("PROVENANCE-MISSING", f"{path}.provenance", "provenance must be an object"))
        return None
    required = (
        "source_repo_origin", "source_repo_url", "source_ref_kind", "source_ref", "source_commit", "source_path",
        "source_locator", "source_content_sha256", "campaign_manifest_sha256", "import_profile_id",
        "import_profile_version", "import_profile_sha256",
    )
    for key in required:
        if not provenance.get(key):
            findings.append(_finding("PROVENANCE-MISSING", f"{path}.provenance.{key}", "required provenance value is missing"))
    if not SHA1_RE.fullmatch(str(provenance.get("source_commit", ""))):
        findings.append(_finding("SOURCE-COMMIT-SHA", f"{path}.provenance.source_commit", "must be a full lowercase SHA-1"))
    for key in ("source_content_sha256", "campaign_manifest_sha256", "import_profile_sha256"):
        if not SHA256_RE.fullmatch(str(provenance.get(key, ""))):
            findings.append(_finding("SOURCE-SHA256", f"{path}.provenance.{key}", "must be a lowercase SHA-256"))
    locator = provenance.get("source_locator")
    if not _is_mapping(locator) or not all(locator.get(key) for key in ("path", "line_start", "line_end", "anchor")):
        findings.append(_finding("PROVENANCE-LOCATOR", f"{path}.provenance.source_locator", "must contain path, bounded lines, and anchor"))
    elif provenance.get("source_path") != locator.get("path"):
        findings.append(_finding("PROVENANCE-LOCATOR", f"{path}.provenance.source_path", "must equal source_locator.path"))

    source_url = provenance.get("source_repo_url")
    source = manifest_sources.get(str(source_url))
    if source is None:
        findings.append(_finding("SOURCE-PIN-UNKNOWN", f"{path}.provenance.source_repo_url", "does not identify a manifest-pinned source"))
    else:
        for key in ("release_ref", "ref_kind", "resolved_commit"):
            provenance_key = {"release_ref": "source_ref", "ref_kind": "source_ref_kind", "resolved_commit": "source_commit"}[key]
            if provenance.get(provenance_key) != source.get(key):
                findings.append(_finding("SOURCE-PIN-MISMATCH", f"{path}.provenance.{provenance_key}", f"must match manifest source {key}"))
        archive = source.get("archive")
        if not _is_mapping(archive) or not SHA256_RE.fullmatch(str(archive.get("sha256", ""))):
            findings.append(_finding("SOURCE-ARCHIVE-SHA", f"{path}.manifest.sources", "matched source lacks a valid archive SHA-256"))
    return provenance


def _validate_traceability(record: Mapping[str, Any], provenance: Mapping[str, Any] | None, path: str, findings: list[dict[str, str]]) -> None:
    traceability = record.get("traceability")
    if not _is_mapping(traceability) or traceability.get("mode") != "source-locator" or traceability.get("required") is not True:
        findings.append(_finding("TRACEABILITY-MISSING", f"{path}.traceability", "must require source-locator traceability"))
        return
    sources = traceability.get("sources")
    if not isinstance(sources, list) or len(sources) != 1 or not _is_mapping(sources[0]):
        findings.append(_finding("TRACEABILITY-MISSING", f"{path}.traceability.sources", "must contain exactly one source"))
        return
    if provenance is None:
        return
    source = sources[0]
    expected = {
        "repository": "source_repo_origin", "repository_url": "source_repo_url", "release_ref": "source_ref",
        "ref_kind": "source_ref_kind", "resolved_commit": "source_commit", "locator": "source_locator",
        "source_content_sha256": "source_content_sha256",
    }
    for trace_key, provenance_key in expected.items():
        if source.get(trace_key) != provenance.get(provenance_key):
            findings.append(_finding("TRACEABILITY-MISMATCH", f"{path}.traceability.sources[0].{trace_key}", "must match record provenance"))


def _validate_record(
    record: Mapping[str, Any], index: int, release: str, manifest_sources: Mapping[str, Mapping[str, Any]],
    all_canonical: set[str], module_ids: set[str], findings: list[dict[str, str]], version_ids: set[str]
) -> None:
    path = f"records[{index}]"
    if record.get("schema") != RECORD_SCHEMA:
        findings.append(_finding("RECORD-SCHEMA", f"{path}.schema", f"must be {RECORD_SCHEMA}"))
    project, kind, item_id = record.get("project"), record.get("kind"), record.get("id")
    canonical = record.get("canonical_id")
    if project != PROJECT or kind not in SUPPORTED_KINDS or not canonical_id.is_valid(str(project), str(kind)):
        findings.append(_finding("REGISTRY-CONFORMANCE", path, "record project/kind is not registered for ECLIPSE/S-CORE"))
    if not isinstance(item_id, str) or not item_id or canonical != f"{project}/{kind}/{item_id}" or canonical_id.parse_canonical_id(str(canonical)) is None:
        findings.append(_finding("CANONICAL-ID", f"{path}.canonical_id", "must equal project/kind/id and parse as a canonical ID"))

    content_hash = record.get("content_hash")
    version = record.get("version_id")
    parsed = version_id.parse_version_id(str(version))
    if not SHA256_RE.fullmatch(str(content_hash)) or record.get("content_hash8") != str(content_hash)[:8]:
        findings.append(_finding("CONTENT-HASH", f"{path}.content_hash", "must be a SHA-256 with matching content_hash8"))
    if not parsed or parsed.get("canonical_id") != canonical or parsed.get("release") != release or parsed.get("hash8") != str(content_hash)[:8]:
        findings.append(_finding("VERSION-ID", f"{path}.version_id", "must bind canonical ID, corpus release, and content hash8"))
    elif version in version_ids:
        findings.append(_finding("DUPLICATE-VERSION", f"{path}.version_id", "version_id occurs more than once in the corpus"))
    else:
        version_ids.add(str(version))

    provenance = _validate_provenance(record, path, manifest_sources, findings)
    _validate_traceability(record, provenance, path, findings)

    if kind == "component":
        parent = str(item_id).split(".", 1)[0]
        if not parent or parent not in module_ids:
            findings.append(_finding("COMPONENT-CONTAINMENT", f"{path}.id", "component prefix must name a present module"))
    if kind in {"design-doc", "process-doc"}:
        if not NEED_ID_RE.fullmatch(str(item_id)) or not isinstance(record.get("sphinx_need_type"), str) or not record.get("sphinx_need_type"):
            findings.append(_finding("SPHINX-NEEDS-IDENTITY", path, "documentation record requires valid explicit sphinx_need_type and ID"))

    references = record.get("references", [])
    if references is not None:
        if not isinstance(references, list) or not all(isinstance(value, str) for value in references):
            findings.append(_finding("DANGLING-REFERENCE", f"{path}.references", "references must be a list of canonical IDs"))
        else:
            for reference in references:
                if reference not in all_canonical:
                    findings.append(_finding("DANGLING-REFERENCE", f"{path}.references", f"target {reference!r} is absent from corpus"))

    status = record.get("status")
    history = record.get("history")
    if not _is_mapping(status) or status.get("state") != "invalid/to-be-confirmed" or not status.get("reason") or not status.get("campaign"):
        findings.append(_finding("STATUS-CONSISTENCY", f"{path}.status", "must retain the import default invalid/to-be-confirmed status"))
    if not isinstance(history, list) or not history or not _is_mapping(history[0]) or not _is_mapping(status) or history[0].get("to") != status.get("state") or history[0].get("campaign") != status.get("campaign"):
        findings.append(_finding("STATUS-CONSISTENCY", f"{path}.history", "initial history must agree with status state and campaign"))


def _validate_candidates(candidates: Any, findings: list[dict[str, str]]) -> list[Mapping[str, Any]]:
    if not isinstance(candidates, list):
        findings.append(_finding("EXCEPTION-CANDIDATE-SCHEMA", "exception_candidates", "must be a list"))
        return []
    valid: list[Mapping[str, Any]] = []
    for index, candidate in enumerate(candidates):
        path = f"exception_candidates[{index}]"
        if not _is_mapping(candidate):
            findings.append(_finding("EXCEPTION-CANDIDATE-SCHEMA", path, "must be an object"))
            continue
        valid.append(candidate)
        if candidate.get("schema") != EXCEPTION_SCHEMA or candidate.get("lifecycle_state") != "discovered" or candidate.get("physical_queue_writer") != "0019-07" or candidate.get("queue_written") is not False:
            findings.append(_finding("EXCEPTION-CANDIDATE-LIFECYCLE", path, "candidate must remain discovered, unqueued, and reserved for 0019-07"))
    return valid


def validate_corpus(corpus: Mapping[str, Any], manifest: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return deterministic validation evidence for one normalized corpus."""
    findings: list[dict[str, str]] = []
    if corpus.get("schema") != CORPUS_SCHEMA:
        findings.append(_finding("CORPUS-SCHEMA", "schema", f"must be {CORPUS_SCHEMA}"))
    if corpus.get("project") != PROJECT or not isinstance(corpus.get("release"), str) or not corpus.get("release"):
        findings.append(_finding("CORPUS-IDENTITY", "project/release", "must identify an ECLIPSE/S-CORE release corpus"))
    if not _is_mapping(manifest):
        findings.append(_finding("MANIFEST-MISSING", "manifest", "a manifest-pinned source set is required for source integrity"))
    elif manifest.get("project") != PROJECT or manifest.get("release") != corpus.get("release"):
        findings.append(_finding("MANIFEST-MISMATCH", "manifest", "manifest project/release must match corpus"))

    records_value = corpus.get("records")
    records = [record for record in records_value if _is_mapping(record)] if isinstance(records_value, list) else []
    if not isinstance(records_value, list) or len(records) != len(records_value):
        findings.append(_finding("CORPUS-RECORDS", "records", "must be a list of record objects"))
    all_canonical = {str(record.get("canonical_id")) for record in records}
    module_ids = {str(record.get("id")) for record in records if record.get("kind") == "module"}
    version_ids: set[str] = set()
    sources = _manifest_sources(manifest)
    if _is_mapping(manifest) and not sources:
        findings.append(_finding("MANIFEST-SOURCES", "manifest.sources", "must contain source bindings"))
    for index, record in enumerate(records):
        _validate_record(record, index, str(corpus.get("release", "")), sources, all_canonical, module_ids, findings, version_ids)
    candidates = _validate_candidates(corpus.get("exception_candidates"), findings)
    findings.sort(key=lambda item: (item["severity"], item["code"], item["path"], item["message"]))
    errors = sum(item["severity"] == "error" for item in findings)
    return {
        "schema": REPORT_SCHEMA,
        "passed": errors == 0,
        "project": corpus.get("project"),
        "release": corpus.get("release"),
        "tool": {"name": "_src/tools/validate_score.py", "version": TOOL_VERSION},
        "input": {
            "corpus_schema": corpus.get("schema"),
            "corpus_sha256": hashlib.sha256(canonical_json_bytes(corpus)).hexdigest(),
            "manifest_sha256": hashlib.sha256(canonical_json_bytes(manifest)).hexdigest() if _is_mapping(manifest) else None,
        },
        "totals": {"records": len(records), "records_by_kind": _counts(records, "kind"), "records_by_status": _counts(records, "status_state") if False else dict(sorted(Counter(str(record.get("status", {}).get("state", "<missing>")) if _is_mapping(record.get("status")) else "<missing>" for record in records).items())), "findings": len(findings), "errors": errors, "warnings": len(findings) - errors},
        "exception_candidates": {"total": len(candidates), "by_kind": _counts(candidates, "exception_kind"), "queued": 0, "queue_statement": "Candidates are discovered evidence only; Task 0019-07 exclusively writes curation/review queue items."},
        "findings": findings,
    }


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def render_markdown(report: Mapping[str, Any]) -> str:
    totals = report["totals"]
    lines = [
        "# Eclipse S-CORE Campaign Validation Report",
        "",
        f"- **Result:** {'PASS' if report['passed'] else 'FAIL'}",
        f"- **Project / release:** `{report.get('project')}` / `{report.get('release')}`",
        f"- **Validator:** `{report['tool']['name']}` v{report['tool']['version']}",
        f"- **Records:** {totals['records']} ({', '.join(f'{key}: {value}' for key, value in totals['records_by_kind'].items()) or 'none'})",
        f"- **Status totals:** {', '.join(f'{key}: {value}' for key, value in totals['records_by_status'].items()) or 'none'}",
        f"- **Exception candidates:** {report['exception_candidates']['total']} ({', '.join(f'{key}: {value}' for key, value in report['exception_candidates']['by_kind'].items()) or 'none'})",
        f"- **Findings:** {totals['findings']} total; {totals['errors']} errors; {totals['warnings']} warnings.",
        "",
        "## Queue boundary",
        "",
        report["exception_candidates"]["queue_statement"],
        "",
        "## Actionable findings",
        "",
    ]
    if not report["findings"]:
        lines.append("No findings. The corpus is structurally valid for the next governed curation step; this report does not authorize queueing or publication.")
    else:
        for finding in report["findings"]:
            lines.append(f"- **{finding['severity'].upper()} `{finding['code']}`** — `{finding['path']}`: {finding['message']}")
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def write_report(json_path: Path, markdown_path: Path, report: Mapping[str, Any]) -> None:
    _atomic_write(json_path, canonical_json_bytes(report))
    _atomic_write(markdown_path, render_markdown(report).encode("utf-8"))


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON {path}: {error}") from error
    if not _is_mapping(value):
        raise ValueError(f"JSON {path} must contain an object")
    return dict(value)


def validate_score_records(records: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Compatibility wrapper for the pre-0019-06 structural-validator API."""
    corpus = {"schema": CORPUS_SCHEMA, "project": PROJECT, "release": "legacy", "records": records, "exception_candidates": []}
    report = validate_corpus(corpus, {"project": PROJECT, "release": "legacy", "sources": []})
    errors = [f"{item['code']}: {item['message']}" for item in report["findings"] if item["severity"] == "error"]
    return errors, []


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path, help="score-normalized-corpus@v1 JSON")
    parser.add_argument("--manifest", required=True, type=Path, help="release-pinned score-source-bom JSON")
    parser.add_argument("--report-json", required=True, type=Path, help="persisted machine-readable report path")
    parser.add_argument("--report-markdown", required=True, type=Path, help="persisted human-readable report path")
    args = parser.parse_args(argv)
    try:
        report = validate_corpus(load_json(args.corpus), load_json(args.manifest))
        write_report(args.report_json, args.report_markdown, report)
    except ValueError as error:
        parser.error(str(error))
    print(f"S-Core validation {'PASS' if report['passed'] else 'FAIL'}: {report['totals']['records']} records, {report['totals']['errors']} errors; reports: {args.report_json}, {args.report_markdown}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
