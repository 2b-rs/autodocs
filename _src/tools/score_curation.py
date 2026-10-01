#!/usr/bin/env python3
"""Route S-Core exception candidates through the canonical curation lifecycle.

Task 0019-07 owns the only transition from a validated S-Core exception
candidate's ``discovered`` state to a persisted queue item.  It deliberately
keeps final content decisions out of automation: tools may queue/publish and AI
may claim/propose, but only an explicitly supplied curator role can record an
``accepted`` or ``rejected`` decision or apply an accepted proposal.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import curation_item
import workflow_lifecycle

PROJECT = "ECLIPSE/S-CORE"
CAMPAIGN = "eclipse-score-v0.6.0"
CANDIDATE_SCHEMA = "score-normalization-exception-candidate@v1"
ITEM_SCHEMA = curation_item.CURATION_ITEM_SCHEMA
QUEUE_STATES = ("open", "claimed", "done")
SUPPORTED_EXCEPTION_KINDS = {
    "unsupported",
    "ambiguous",
    "identity-collision",
    "source-contradiction",
    "conflicting",
    "missing-provenance",
    "non-auto-verifiable",
}


class CurationLifecycleError(ValueError):
    """Raised when an actor or state violates the governed queue contract."""


def _canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_canonical_json_bytes(payload))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CurationLifecycleError(f"cannot read queue item {path}: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema") != ITEM_SCHEMA:
        raise CurationLifecycleError(f"{path} is not a {ITEM_SCHEMA} item")
    return payload


def _require_role(actual: str, allowed: set[str], action: str) -> None:
    if actual not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise CurationLifecycleError(f"{action} requires role {allowed_text}; got {actual!r}")


def _source_url(source: Mapping[str, Any]) -> str:
    repository_url = source.get("repository_url")
    resolved_commit = source.get("resolved_commit")
    locator = source.get("locator")
    if not isinstance(repository_url, str) or not isinstance(resolved_commit, str) or not isinstance(locator, Mapping):
        raise CurationLifecycleError("candidate source must contain repository_url, resolved_commit, and locator")
    path = locator.get("path")
    start = locator.get("line_start")
    end = locator.get("line_end")
    if not isinstance(path, str) or not path or not isinstance(start, int) or start < 1 or not isinstance(end, int) or end < start:
        raise CurationLifecycleError("candidate source locator must contain a path and bounded positive lines")
    return f"{repository_url.removesuffix('.git')}/blob/{resolved_commit}/{path}#L{start}-L{end}"


def _candidate_item(candidate: Mapping[str, Any], created: str) -> dict[str, Any]:
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        raise CurationLifecycleError(f"candidate schema must be {CANDIDATE_SCHEMA}")
    if candidate.get("project") != PROJECT:
        raise CurationLifecycleError(f"candidate project must be {PROJECT}")
    if candidate.get("lifecycle_state") != "discovered" or candidate.get("queue_written") is not False:
        raise CurationLifecycleError("only discovered, unqueued exception candidates may be queued")
    candidate_id = candidate.get("candidate_id")
    canonical_id = candidate.get("canonical_id")
    release = candidate.get("release")
    exception_kind = candidate.get("exception_kind")
    source = candidate.get("source")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise CurationLifecycleError("candidate_id is required")
    if not isinstance(canonical_id, str) or not canonical_id:
        raise CurationLifecycleError("canonical_id is required")
    if not isinstance(release, str) or not release:
        raise CurationLifecycleError("release is required")
    if exception_kind not in SUPPORTED_EXCEPTION_KINDS:
        raise CurationLifecycleError(f"unsupported S-Core exception kind {exception_kind!r}")
    if not isinstance(source, Mapping):
        raise CurationLifecycleError("candidate source is required")
    source_url = _source_url(source)
    versions = [value for value in (candidate.get("existing_version_id"), candidate.get("competing_version_id")) if isinstance(value, str) and value]
    item: dict[str, Any] = {
        "schema": ITEM_SCHEMA,
        "queue_id": f"score-curation:{hashlib.sha256(candidate_id.encode('utf-8')).hexdigest()[:20]}",
        "canonical_id": canonical_id,
        "project": PROJECT,
        "release": release,
        "item_kind": "record",
        "origin": "tool",
        "status": "open",
        "lifecycle_state": "queued",
        "subject": str(candidate.get("subject") or exception_kind),
        "current_state": {"exception_kind": exception_kind, "condition_id": candidate.get("condition_id")},
        "proposed_state": None,
        "evidence": [copy.deepcopy(dict(source))],
        "counter_evidence": [],
        "decision_basis": {
            "exception_candidate_id": candidate_id,
            "condition_id": candidate.get("condition_id"),
            "source_versions": versions,
            "source_locator_url": source_url,
            "record_locator": {
                "canonical_id": canonical_id,
                "release": release,
                "version_ids": versions,
            },
        },
        "campaign": CAMPAIGN,
        "created": created,
        "claimed_by": None,
        "decided_by": None,
        "completed_at": None,
        "history": [{"from": "discovered", "to": "queued", "actor": "tool", "at": created}],
        "decided_on_version": versions[0] if len(versions) == 1 else None,
        # The normalized S-Core corpus has no generated record page before
        # Task 0019-09.  Until then each record/version link resolves to its
        # release-pinned source locator, while the version IDs remain explicit
        # in decision_basis.record_locator for the reviewer to inspect.
        "links": {
            "record": source_url,
            "versions": [source_url for _ in versions],
            "source": source_url,
        },
    }
    if not curation_item.is_conformant(item):
        raise CurationLifecycleError("internal error: constructed item is not curation-item@v1 conformant")
    return item


def _queue_path(queue_root: Path, item: Mapping[str, Any], state: str) -> Path:
    if state not in QUEUE_STATES:
        raise CurationLifecycleError(f"unknown physical queue state {state!r}")
    queue_id = item.get("queue_id")
    if not isinstance(queue_id, str) or not queue_id:
        raise CurationLifecycleError("queue item lacks queue_id")
    safe_name = hashlib.sha256(queue_id.encode("utf-8")).hexdigest()[:24]
    return queue_root / state / f"{safe_name}.json"


def queue_candidates(candidates: Sequence[Mapping[str, Any]], queue_root: Path, *, created: str) -> list[Path]:
    """Write S-Core candidates as canonical, unclaimed queue items.

    This is intentionally idempotent and is the only tool-owned content-state
    transition: ``discovered -> queued``.  It cannot record a final decision.
    """
    paths: list[Path] = []
    for candidate in candidates:
        item = _candidate_item(candidate, created)
        path = _queue_path(queue_root, item, "open")
        if path.exists():
            existing = _load(path)
            if existing.get("decision_basis", {}).get("exception_candidate_id") != candidate.get("candidate_id"):
                raise CurationLifecycleError(f"queue path collision at {path}")
        else:
            _atomic_write(path, item)
        paths.append(path)
    return paths


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CurationLifecycleError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise CurationLifecycleError(f"JSON {path} must contain an object")
    return value


def queue_validated_corpus(corpus_path: Path, report_path: Path, queue_root: Path, *, created: str) -> list[Path]:
    """Queue only candidates bound to a passing 0019-06 validation report."""
    corpus = _load_json(corpus_path)
    report = _load_json(report_path)
    expected_hash = hashlib.sha256(_canonical_json_bytes(corpus)).hexdigest()
    actual_hash = report.get("input", {}).get("corpus_sha256") if isinstance(report.get("input"), Mapping) else None
    if report.get("schema") != "score-validation-report@v1" or report.get("passed") is not True:
        raise CurationLifecycleError("a passing score-validation-report@v1 is required before queueing")
    if actual_hash != expected_hash:
        raise CurationLifecycleError("validation report is not bound to the candidate corpus")
    candidates = corpus.get("exception_candidates")
    if not isinstance(candidates, list):
        raise CurationLifecycleError("validated corpus exception_candidates must be a list")
    return queue_candidates(candidates, queue_root, created=created)


def _transition(item: dict[str, Any], from_state: str, to_state: str, actor_role: str, actor_identity: str, at: str) -> None:
    if item.get("lifecycle_state") != from_state:
        raise CurationLifecycleError(f"expected lifecycle state {from_state!r}, found {item.get('lifecycle_state')!r}")
    if not workflow_lifecycle.validate_transition(from_state, to_state):
        raise CurationLifecycleError(f"invalid lifecycle transition {from_state!r} -> {to_state!r}")
    item["lifecycle_state"] = to_state
    item.setdefault("history", []).append({"from": from_state, "to": to_state, "actor": actor_role, "actor_identity": actor_identity, "at": at})


def claim(path: Path, *, actor_role: str, actor_identity: str, at: str) -> Path:
    """Atomically let an AI worker claim a queued item; it cannot decide it."""
    _require_role(actor_role, {"ai"}, "claim")
    item = _load(path)
    _transition(item, "queued", "claimed", actor_role, actor_identity, at)
    item["status"] = "claimed"
    item["claimed_by"] = actor_identity
    target = _queue_path(path.parents[1], item, "claimed")
    if target.exists():
        raise CurationLifecycleError(f"claim target already exists: {target}")
    _atomic_write(target, item)
    path.unlink()
    return target


def propose(path: Path, proposal: Mapping[str, Any], *, actor_role: str, actor_identity: str, at: str) -> Path:
    """Persist an AI proposal without allowing it to make a final decision."""
    _require_role(actor_role, {"ai"}, "propose")
    if not isinstance(proposal, Mapping) or not proposal:
        raise CurationLifecycleError("proposal must be a non-empty object")
    item = _load(path)
    _transition(item, "claimed", "proposed", actor_role, actor_identity, at)
    item["status"] = "proposed"
    item["proposed_state"] = copy.deepcopy(dict(proposal))
    _atomic_write(path, item)
    return path


def record_curator_decision(path: Path, decision: str, rationale: str, *, actor_role: str, actor_identity: str, at: str) -> Path:
    """Record a human curator's explicit accepted/rejected content decision."""
    _require_role(actor_role, {"curator"}, "final curation decision")
    if decision not in {"accepted", "rejected"}:
        raise CurationLifecycleError("decision must be 'accepted' or 'rejected'")
    if not isinstance(rationale, str) or not rationale.strip():
        raise CurationLifecycleError("curator rationale is required")
    item = _load(path)
    _transition(item, "proposed", decision, actor_role, actor_identity, at)
    item["status"] = decision
    item["decided_by"] = actor_identity
    item["decision"] = {"outcome": decision, "rationale": rationale, "decided_at": at, "actor_role": actor_role}
    if decision == "rejected":
        item["completed_at"] = at
        target = _queue_path(path.parents[1], item, "done")
        _atomic_write(target, item)
        path.unlink()
        return target
    _atomic_write(path, item)
    return path


def apply(path: Path, application: Mapping[str, Any], *, actor_role: str, actor_identity: str, at: str) -> Path:
    """Record a curator-applied, accepted proposal; no AI/tool application path exists."""
    _require_role(actor_role, {"curator"}, "application")
    if not isinstance(application, Mapping) or not application:
        raise CurationLifecycleError("application evidence must be a non-empty object")
    item = _load(path)
    _transition(item, "accepted", "applied", actor_role, actor_identity, at)
    item["status"] = "applied"
    item["application"] = copy.deepcopy(dict(application))
    item["completed_at"] = at
    target = _queue_path(path.parents[1], item, "done")
    _atomic_write(target, item)
    path.unlink()
    return target


def publish(path: Path, publication: Mapping[str, Any], *, actor_role: str, actor_identity: str, at: str) -> Path:
    """Record tool publication only after an already curator-applied item."""
    _require_role(actor_role, {"tool"}, "publication")
    if not isinstance(publication, Mapping) or not publication:
        raise CurationLifecycleError("publication evidence must be a non-empty object")
    item = _load(path)
    _transition(item, "applied", "published", actor_role, actor_identity, at)
    # ``published`` is a lifecycle position, not a persisted curation-item@v1
    # status. Keep the valid persisted ``applied`` value while exposing the
    # terminal lifecycle state to reports.
    item["publication"] = copy.deepcopy(dict(publication))
    _atomic_write(path, item)
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path, help="validated score-normalized-corpus@v1 JSON")
    parser.add_argument("--report", required=True, type=Path, help="passing score-validation-report@v1 bound to corpus")
    parser.add_argument("--queue-root", required=True, type=Path, help="curation queue root containing open/claimed/done")
    parser.add_argument("--created", required=True, help="ISO-8601 queue creation timestamp supplied by the operator")
    args = parser.parse_args(argv)
    try:
        paths = queue_validated_corpus(args.corpus, args.report, args.queue_root, created=args.created)
    except CurationLifecycleError as error:
        parser.error(str(error))
    print(f"Queued {len(paths)} validated S-Core exception candidate(s) under {args.queue_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
