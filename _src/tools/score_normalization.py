#!/usr/bin/env python3
"""Normalize raw release-pinned S-Core observations into canonical versioned records.

This is a pure, offline transformation.  It materializes no record-store files,
never creates a curation/review queue item, and never promotes a record's
invalid/to-be-confirmed status.  Collisions are preserved as deterministic
exception candidates for Task 0019-07 to route through the governed lifecycle.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import canonical_id
import version_id

RAW_SCHEMA = "score-raw-extraction@v1"
NORMALIZED_SCHEMA = "score-normalized-corpus@v1"
RECORD_SCHEMA = "score-normalized-record@v1"
EXCEPTION_SCHEMA = "score-normalization-exception-candidate@v1"
PROJECT = "ECLIPSE/S-CORE"
SUPPORTED_KINDS = {"module", "component", "design-doc", "process-doc"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class NormalizationError(ValueError):
    """Raised when raw extraction output cannot safely be materialized."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the project canonical JSON bytes used for deterministic hashing."""
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise NormalizationError(f"{label} must be an object")
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise NormalizationError(f"{label} must be a non-empty string")
    return value


def _validate_import_date(import_date: str) -> None:
    try:
        date.fromisoformat(import_date)
    except ValueError as error:
        raise NormalizationError("import_date must be an ISO-8601 calendar date (YYYY-MM-DD)") from error


def _safe_locator(locator: Any, label: str) -> dict[str, Any]:
    value = _require_mapping(locator, f"{label}.locator")
    path = _require_string(value.get("path"), f"{label}.locator.path")
    pure_path = PurePosixPath(path)
    if pure_path.is_absolute() or ".." in pure_path.parts or path.endswith("/"):
        raise NormalizationError(f"{label}.locator.path must be a safe repository-relative path")
    start, end = value.get("line_start"), value.get("line_end")
    if not isinstance(start, int) or start < 1 or not isinstance(end, int) or end < start:
        raise NormalizationError(f"{label}.locator must have a bounded positive line range")
    anchor = _require_string(value.get("anchor"), f"{label}.locator.anchor")
    return {"path": path, "line_start": start, "line_end": end, "anchor": anchor}


def _source_provenance(record: Mapping[str, Any], corpus: Mapping[str, Any], label: str) -> dict[str, Any]:
    provenance = _require_mapping(record.get("provenance"), f"{label}.provenance")
    source_repo_origin = _require_string(provenance.get("source_repo_origin"), f"{label}.provenance.source_repo_origin")
    source_repo_url = _require_string(provenance.get("source_repo_url"), f"{label}.provenance.source_repo_url")
    source_ref_kind = _require_string(provenance.get("source_ref_kind"), f"{label}.provenance.source_ref_kind")
    if source_ref_kind not in {"tag", "release-branch"}:
        raise NormalizationError(f"{label}.provenance.source_ref_kind must be tag or release-branch")
    source_ref = _require_string(provenance.get("source_ref"), f"{label}.provenance.source_ref")
    source_commit = _require_string(provenance.get("source_commit"), f"{label}.provenance.source_commit")
    if not SHA1_RE.fullmatch(source_commit):
        raise NormalizationError(f"{label}.provenance.source_commit must be a full lowercase SHA-1")
    locator = _safe_locator(provenance.get("source_locator"), label)
    source_path = _require_string(provenance.get("source_path"), f"{label}.provenance.source_path")
    if source_path != locator["path"]:
        raise NormalizationError(f"{label}.provenance.source_path must equal source_locator.path")
    source_content_sha256 = _require_string(provenance.get("source_content_sha256"), f"{label}.provenance.source_content_sha256")
    if not SHA256_RE.fullmatch(source_content_sha256):
        raise NormalizationError(f"{label}.provenance.source_content_sha256 must be a lowercase SHA-256")
    return {
        "source_repo_origin": source_repo_origin,
        "source_repo_url": source_repo_url,
        "source_ref_kind": source_ref_kind,
        "source_ref": source_ref,
        "source_commit": source_commit,
        "source_path": source_path,
        "source_locator": locator,
        "source_content_sha256": source_content_sha256,
        "campaign_manifest_sha256": _require_string(corpus.get("manifest_sha256"), "raw.manifest_sha256"),
        "import_profile_id": _require_string(corpus.get("profile_id"), "raw.profile_id"),
        "import_profile_version": _require_string(corpus.get("profile_version"), "raw.profile_version"),
        "import_profile_sha256": _require_string(corpus.get("profile_sha256"), "raw.profile_sha256"),
    }


def _traceability(provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Build a traceability source that is complete and tied to provenance."""
    source = {
        "repository": provenance["source_repo_origin"],
        "repository_url": provenance["source_repo_url"],
        "release_ref": provenance["source_ref"],
        "ref_kind": provenance["source_ref_kind"],
        "resolved_commit": provenance["source_commit"],
        "locator": copy.deepcopy(provenance["source_locator"]),
        "source_content_sha256": provenance["source_content_sha256"],
    }
    return {"mode": "source-locator", "required": True, "sources": [source]}


def _status_and_history(record: Mapping[str, Any], import_date: str, label: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    status = copy.deepcopy(_require_mapping(record.get("status"), f"{label}.status"))
    state = _require_string(status.get("state"), f"{label}.status.state")
    _require_string(status.get("reason"), f"{label}.status.reason")
    _require_string(status.get("campaign"), f"{label}.status.campaign")
    if state != "invalid/to-be-confirmed":
        raise NormalizationError(f"{label}.status.state must retain the import profile's invalid/to-be-confirmed default")
    template = _require_mapping(record.get("history_template"), f"{label}.history_template")
    history = {
        "campaign": _require_string(template.get("campaign"), f"{label}.history_template.campaign"),
        "date": import_date,
        "from": template.get("from"),
        "to": _require_string(template.get("to"), f"{label}.history_template.to"),
        "reason": _require_string(template.get("reason"), f"{label}.history_template.reason"),
        "actor": _require_string(template.get("actor"), f"{label}.history_template.actor"),
    }
    if history["to"] != state:
        raise NormalizationError(f"{label}.history_template.to must match status.state")
    if history["actor"] not in {"tool", "ai", "curator"}:
        raise NormalizationError(f"{label}.history_template.actor must be tool, ai, or curator")
    return status, [history]


def _normalized_record(record: Mapping[str, Any], corpus: Mapping[str, Any], import_date: str, index: int) -> dict[str, Any]:
    label = f"raw.observations[{index}].decision.record"
    project = _require_string(record.get("project"), f"{label}.project")
    kind = _require_string(record.get("kind"), f"{label}.kind")
    item_id = _require_string(record.get("id"), f"{label}.id")
    canonical = _require_string(record.get("canonical_id"), f"{label}.canonical_id")
    if project != PROJECT or kind not in SUPPORTED_KINDS or not canonical_id.is_valid(project, kind):
        raise NormalizationError(f"{label} must use a registered ECLIPSE/S-CORE kind")
    if canonical != f"{project}/{kind}/{item_id}":
        raise NormalizationError(f"{label}.canonical_id does not match project/kind/id")
    parsed = canonical_id.parse_canonical_id(canonical)
    if parsed is None or parsed != {"project": project, "kind": kind, "id": item_id}:
        raise NormalizationError(f"{label}.canonical_id is malformed")
    release = _require_string(corpus.get("release"), "raw.release")
    title = _require_string(record.get("title"), f"{label}.title")
    description = record.get("description", "")
    if not isinstance(description, str):
        raise NormalizationError(f"{label}.description must be a string")
    provenance = _source_provenance(record, corpus, label)
    status, history = _status_and_history(record, import_date, label)
    content: dict[str, Any] = {
        "project": project,
        "kind": kind,
        "id": item_id,
        "canonical_id": canonical,
        "release": release,
        "title": title,
        "description": description,
        "provenance": provenance,
        "traceability": _traceability(provenance),
        "status": status,
    }
    if kind in {"design-doc", "process-doc"}:
        content["sphinx_need_type"] = _require_string(record.get("sphinx_need_type"), f"{label}.sphinx_need_type")
    content_json = canonical_json_bytes(content).decode("utf-8")
    content_hash = hashlib.sha256(content_json.encode("utf-8")).hexdigest()
    version = version_id.requirement_version_id(canonical, release, content_json)
    return {
        "schema": RECORD_SCHEMA,
        **content,
        "content_hash": content_hash,
        "content_hash8": content_hash[:8],
        "version_id": version,
        "history": history,
    }


def _observation_key(observation: Mapping[str, Any]) -> tuple[Any, ...]:
    candidate = observation.get("candidate") if isinstance(observation.get("candidate"), Mapping) else {}
    locator = candidate.get("locator") if isinstance(candidate.get("locator"), Mapping) else {}
    return (
        str(candidate.get("repository", "")),
        str(locator.get("path", "")),
        int(locator.get("line_start", 0)) if isinstance(locator.get("line_start"), int) else 0,
        str(candidate.get("source_class", "")),
        str(locator.get("anchor", "")),
    )


def _exception_candidate(
    *,
    exception_kind: str,
    condition_id: str,
    canonical: str,
    release: str,
    message: str,
    source: Mapping[str, Any],
    existing_version_id: str | None,
    competing_version_id: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": EXCEPTION_SCHEMA,
        "exception_kind": exception_kind,
        "condition_id": condition_id,
        "lifecycle_state": "discovered",
        "physical_queue_writer": "0019-07",
        "queue_written": False,
        "project": PROJECT,
        "canonical_id": canonical,
        "release": release,
        "subject": message,
        "source": copy.deepcopy(dict(source)),
        "existing_version_id": existing_version_id,
        "competing_version_id": competing_version_id,
    }
    payload["candidate_id"] = f"score-normalization-exception:{_sha256(payload)[:16]}"
    return payload


def _raw_exception_source(observation: Mapping[str, Any]) -> dict[str, Any]:
    candidate = _require_mapping(observation.get("candidate"), "raw exception candidate")
    locator = _safe_locator(candidate.get("locator"), "raw exception candidate")
    return {
        "repository": candidate.get("repository"),
        "repository_url": candidate.get("repository_url"),
        "release_ref": candidate.get("release_ref"),
        "ref_kind": candidate.get("ref_kind"),
        "resolved_commit": candidate.get("resolved_commit"),
        "locator": locator,
        "source_content_sha256": candidate.get("source_content_sha256"),
    }


def normalize(raw: Mapping[str, Any], import_date: str) -> dict[str, Any]:
    """Materialize deterministic canonical records and unqueued exception candidates."""
    _validate_import_date(import_date)
    if raw.get("schema") != RAW_SCHEMA:
        raise NormalizationError(f"raw.schema must be {RAW_SCHEMA}")
    if raw.get("project") != PROJECT:
        raise NormalizationError(f"raw.project must be {PROJECT}")
    observations = raw.get("observations")
    if not isinstance(observations, list):
        raise NormalizationError("raw.observations must be a list")
    release = _require_string(raw.get("release"), "raw.release")
    for digest_key in ("manifest_sha256", "profile_sha256"):
        if not SHA256_RE.fullmatch(str(raw.get(digest_key, ""))):
            raise NormalizationError(f"raw.{digest_key} must be a lowercase SHA-256")

    records: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    by_canonical: dict[str, dict[str, Any]] = {}
    ordered = sorted(enumerate(observations), key=lambda item: _observation_key(_require_mapping(item[1], f"raw.observations[{item[0]}]")))
    for original_index, observation_value in ordered:
        observation = _require_mapping(observation_value, f"raw.observations[{original_index}]")
        decision = _require_mapping(observation.get("decision"), f"raw.observations[{original_index}].decision")
        record_value = decision.get("record")
        if record_value is None:
            continue
        normalized = _normalized_record(_require_mapping(record_value, f"raw.observations[{original_index}].decision.record"), raw, import_date, original_index)
        canonical = normalized["canonical_id"]
        prior = by_canonical.get(canonical)
        if prior is None:
            by_canonical[canonical] = normalized
            records.append(normalized)
            continue
        same_content = prior["content_hash"] == normalized["content_hash"]
        exceptions.append(
            _exception_candidate(
                exception_kind="identity-collision" if same_content else "source-contradiction",
                condition_id="NORMALIZATION-DUPLICATE-CANONICAL" if same_content else "NORMALIZATION-CONTRADICTING-CANONICAL",
                canonical=canonical,
                release=release,
                message="multiple raw observations materialize the same canonical identity",
                source=normalized["provenance"],
                existing_version_id=prior["version_id"],
                competing_version_id=normalized["version_id"],
            )
        )

    # The extractor deliberately leaves reviewed duplicates/conflicts record-less.
    # Preserve those observations as candidates instead of manufacturing a queue item.
    for original_index, observation_value in ordered:
        observation = _require_mapping(observation_value, f"raw.observations[{original_index}]")
        decision = _require_mapping(observation.get("decision"), f"raw.observations[{original_index}].decision")
        if decision.get("record") is not None:
            continue
        condition_id = decision.get("condition_id")
        if condition_id not in {"REVIEW-DUPLICATE-CANONICAL", "REVIEW-CONFLICTING-CANONICAL"}:
            continue
        work_item = decision.get("work_item")
        canonical = work_item.get("canonical_id") if isinstance(work_item, Mapping) else None
        if not isinstance(canonical, str) or not canonical:
            raise NormalizationError(f"raw.observations[{original_index}] {condition_id} must identify a canonical_id")
        prior = by_canonical.get(canonical)
        exceptions.append(
            _exception_candidate(
                exception_kind="identity-collision" if condition_id == "REVIEW-DUPLICATE-CANONICAL" else "source-contradiction",
                condition_id=str(condition_id),
                canonical=canonical,
                release=release,
                message=_require_string(decision.get("message"), f"raw.observations[{original_index}].decision.message"),
                source=_raw_exception_source(observation),
                existing_version_id=prior["version_id"] if prior else None,
                competing_version_id=None,
            )
        )

    records.sort(key=lambda record: (record["canonical_id"], record["version_id"]))
    exceptions.sort(key=lambda item: (item["canonical_id"], item["exception_kind"], item["candidate_id"]))
    return {
        "schema": NORMALIZED_SCHEMA,
        "project": PROJECT,
        "release": release,
        "manifest_sha256": raw["manifest_sha256"],
        "profile_id": raw["profile_id"],
        "profile_version": raw["profile_version"],
        "profile_sha256": raw["profile_sha256"],
        "import_date": import_date,
        "canonical_corpus_written": False,
        "queue_written": False,
        "publication_permitted": False,
        "completion_reason": "normalized records remain invalid/to-be-confirmed; Task 0019-07 exclusively writes curation/review queue items",
        "records": records,
        "exception_candidates": exceptions,
        "summary": {
            "raw_observations": len(observations),
            "records": len(records),
            "records_by_kind": {kind: sum(record["kind"] == kind for record in records) for kind in sorted(SUPPORTED_KINDS)},
            "exception_candidates": len(exceptions),
            "exception_candidates_by_kind": {
                kind: sum(item["exception_kind"] == kind for item in exceptions)
                for kind in ("identity-collision", "source-contradiction")
            },
        },
    }


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise NormalizationError(f"cannot read raw extraction JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise NormalizationError(f"raw extraction JSON {path} must contain an object")
    return value


def write_output(output: Path, result: Mapping[str, Any]) -> None:
    """Atomically promote a complete normalized result."""
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(result))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, output)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path, help="score-raw-extraction@v1 JSON produced by Task 0019-04")
    parser.add_argument("--import-date", required=True, help="deterministic ISO-8601 import date (YYYY-MM-DD)")
    parser.add_argument("--output", required=True, type=Path, help="normalized corpus JSON to atomically write")
    args = parser.parse_args(argv)
    try:
        write_output(args.output, normalize(load_json(args.raw), args.import_date))
    except NormalizationError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
