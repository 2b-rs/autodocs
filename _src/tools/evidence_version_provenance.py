"""Common provenance envelope for raw-evidence and record-version writers (0037-26.03).

Uses the 0037-17 store, views, and query indexes. Does not rewrite existing
JSONL history. Synthetic fixture environments cannot be relabeled production.
Legacy lines without an envelope receive an explicit unknown/legacy
disposition and are never backfilled.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import provenance_store as ps  # noqa: E402
from version_id import uuid7  # noqa: E402

ENVELOPE_SCHEMA = "evidence-version-envelope@v1"
PRODUCER_FAMILY = "raw-evidence-record-version"
ALLOWED_ENV = frozenset(ps.ENVIRONMENTS)
PRODUCTION_ENV = "production"
SYNTHETIC_ENV = "synthetic"


class EnvelopeError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _unique_refs(refs: list) -> list:
    seen = set()
    out = []
    for item in refs:
        key = ps.canonical_bytes(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def typed_ref(kind: str, ident: str, classification: str = "internal", **extra: Any) -> dict:
    uri = ident if str(ident).startswith(kind + ":") else f"{kind}:{ident}"
    value = {
        "schema_version": ps.SCHEMA_VERSION,
        "kind": kind,
        "uri": uri,
        "classification": classification,
    }
    value.update(extra)
    return value


def legacy_disposition(record: Mapping[str, Any] | None) -> dict:
    """Explicit unknown/legacy mapping. Never invents run, issue, or production."""
    adapted = ps.adapt_legacy_confidence(record)
    adapted["backfill"] = False
    adapted["envelope"] = None
    if record and isinstance(record.get("provenance"), dict):
        adapted["envelope"] = dict(record["provenance"])
    return adapted


def _require_env(environment: str) -> str:
    if environment not in ALLOWED_ENV:
        raise EnvelopeError("EV-ENV", f"invalid environment {environment!r}")
    return environment


def reject_synthetic_as_production(environment: str, *, synthetic_reason: str | None) -> None:
    if environment == PRODUCTION_ENV and synthetic_reason:
        raise EnvelopeError(
            "EV-SYNTHETIC-PRODUCTION",
            "synthetic fixture data must not be relabeled production",
        )
    if environment == SYNTHETIC_ENV and not synthetic_reason:
        raise EnvelopeError("EV-SYNTHETIC-REASON", "synthetic environment requires synthetic_reason")


def normalize_envelope_request(request: Mapping[str, Any]) -> dict:
    extra = set(request) - {
        "store",
        "store_root",
        "file_bytes",
        "run_id",
        "started_at",
        "ended_at",
        "occurred_at",
        "environment",
        "classification",
        "issue",
        "criterion",
        "campaign",
        "tool_commit",
        "config_commit",
        "source_commit",
        "input_members",
        "synthetic_reason",
        "producer_uri",
    }
    if extra:
        raise EnvelopeError("EV-SCHEMA", f"unknown envelope fields: {sorted(extra)}")
    environment = _require_env(str(request.get("environment") or ""))
    reject_synthetic_as_production(environment, synthetic_reason=request.get("synthetic_reason"))
    classification = request.get("classification") or "internal"
    if classification not in ps.CLASSIFICATIONS:
        raise EnvelopeError("EV-PRIVACY", f"invalid classification {classification!r}")
    for key in ("issue", "criterion", "campaign", "tool_commit", "source_commit"):
        if not request.get(key):
            raise EnvelopeError("EV-CONTEXT", f"envelope missing {key}")
    tool = request["tool_commit"]
    source = request["source_commit"]
    config = request.get("config_commit") or tool
    for name, value in (("tool_commit", tool), ("source_commit", source), ("config_commit", config)):
        if not ps.COMMIT_RE.match(str(value)):
            raise EnvelopeError("EV-COMMIT", f"{name} must be a 40-hex commit")
    members = request.get("input_members")
    if not isinstance(members, list) or not members:
        raise EnvelopeError("EV-ARTIFACTS", "exact input artifact set (input_members) is required")
    return {
        "store": request.get("store"),
        "store_root": request.get("store_root"),
        "file_bytes": request.get("file_bytes"),
        "run_id": request.get("run_id") or uuid7(),
        "started_at": request.get("started_at") or "2026-08-27T12:00:00Z",
        "ended_at": request.get("ended_at") or "2026-08-27T12:01:00Z",
        "occurred_at": request.get("occurred_at") or "2026-08-27T12:00:30Z",
        "environment": environment,
        "classification": classification,
        "issue": request["issue"],
        "criterion": request["criterion"],
        "campaign": request["campaign"],
        "tool_commit": tool,
        "config_commit": config,
        "source_commit": source,
        "input_members": members,
        "synthetic_reason": request.get("synthetic_reason"),
        "producer_uri": request.get("producer_uri") or f"commit:{tool}",
    }


def _store_from(req: Mapping[str, Any], file_map: dict) -> ps.ProvenanceStore:
    if req.get("store") is not None:
        return req["store"]
    root = Path(req["store_root"])
    lookup = req.get("file_bytes") or file_map.__getitem__
    return ps.ProvenanceStore(root, file_bytes=lookup)


def _member_payload(member: Mapping[str, Any], source_commit: str) -> dict:
    path = member["path"]
    digest = member["digest"]
    size = member["size_bytes"]
    if not str(digest).startswith("sha256:"):
        digest = ps.sha256_bytes(member["bytes"]) if "bytes" in member else digest
    return {
        "path": path,
        "digest": digest,
        "size_bytes": size,
        "media_type": member.get("media_type") or "application/octet-stream",
        "source_commit": member.get("source_commit") or source_commit,
    }


def attach_record_version_provenance(
    *,
    version_id: str,
    content: str,
    request: Mapping[str, Any],
    existing_envelope: Mapping[str, Any] | None = None,
) -> dict:
    """Write run, input artifact-set, and produced-by/implements events. Idempotent replay."""
    req = normalize_envelope_request(request)
    file_map: dict[str, bytes] = {}
    members = []
    for raw in req["input_members"]:
        body = raw.get("bytes")
        if isinstance(body, str):
            body = body.encode("utf-8")
        if body is None:
            raise EnvelopeError("EV-ARTIFACTS", f"member {raw.get('path')} missing source bytes")
        file_map[raw["path"]] = body
        digest = ps.sha256_bytes(body)
        members.append(
            _member_payload(
                {
                    "path": raw["path"],
                    "digest": digest,
                    "size_bytes": len(body),
                    "media_type": raw.get("media_type"),
                    "source_commit": raw.get("source_commit"),
                    "bytes": body,
                },
                req["source_commit"],
            )
        )
    store = _store_from(req, file_map)
    classification = req["classification"]
    env = req["environment"]
    run_id = (existing_envelope or {}).get("run_id") or req["run_id"]
    set_id = (existing_envelope or {}).get("artifact_set_id") or uuid7()
    event_produced = (existing_envelope or {}).get("produced_by_event_id") or uuid7()
    event_implements = (existing_envelope or {}).get("implements_event_id") or uuid7()
    content_digest = ps.sha256_bytes(content.encode("utf-8"))

    run_payload = {
        "schema_version": ps.SCHEMA_VERSION,
        "run_id": run_id,
        "started_at": req["started_at"],
        "ended_at": req["ended_at"],
        "environment": env,
        "classification": classification,
        "status": "succeeded",
        "producer": typed_ref("commit", req["tool_commit"], classification),
        "inputs": _unique_refs(
            [
                typed_ref("commit", req["source_commit"], classification),
                typed_ref("commit", req["config_commit"], classification),
                typed_ref("commit", req["tool_commit"], classification),
                typed_ref("issue", req["issue"], classification),
                typed_ref("criterion", req["criterion"], classification),
                typed_ref("campaign", req["campaign"], classification),
            ]
        ),
        "outputs": [typed_ref("record-version", version_id, classification, digest=content_digest)],
    }
    if env == SYNTHETIC_ENV:
        # run schema forbids extras; synthetic_reason lives on events
        pass
    store.create_run(run_payload)
    aset = store.create_artifact_set(
        {
            "schema_version": ps.SCHEMA_VERSION,
            "set_id": set_id,
            "created_at": req["started_at"],
            "classification": classification,
            "environment": env,
            "producer": typed_ref("run", run_id, classification),
            "members": members,
        }
    )
    event_kwargs = {}
    if env == SYNTHETIC_ENV:
        event_kwargs["synthetic_reason"] = req["synthetic_reason"]
    store.create_event(
        {
            "schema_version": ps.SCHEMA_VERSION,
            "event_id": event_produced,
            "occurred_at": req["occurred_at"],
            "relation": "produced-by",
            "source": typed_ref("record-version", version_id, classification, digest=content_digest),
            "target": typed_ref("run", run_id, classification),
            "environment": env,
            "classification": classification,
            "run": typed_ref("run", run_id, classification),
            **event_kwargs,
        }
    )
    store.create_event(
        {
            "schema_version": ps.SCHEMA_VERSION,
            "event_id": event_implements,
            "occurred_at": req["occurred_at"],
            "relation": "implements",
            "source": typed_ref("record-version", version_id, classification, digest=content_digest),
            "target": typed_ref("issue", req["issue"], classification),
            "environment": env,
            "classification": classification,
            "run": typed_ref("run", run_id, classification),
            **event_kwargs,
        }
    )
    envelope = {
        "schema": ENVELOPE_SCHEMA,
        "producer_family": PRODUCER_FAMILY,
        "run_id": run_id,
        "artifact_set_id": set_id,
        "artifact_set_digest": aset["record"]["set_digest"],
        "produced_by_event_id": event_produced,
        "implements_event_id": event_implements,
        "environment": env,
        "classification": classification,
        "evidence_class": env,
        "issue": req["issue"],
        "criterion": req["criterion"],
        "campaign": req["campaign"],
        "tool_commit": req["tool_commit"],
        "config_commit": req["config_commit"],
        "source_commit": req["source_commit"],
        "source_content_digest": content_digest,
    }
    if req.get("synthetic_reason"):
        envelope["synthetic_reason"] = req["synthetic_reason"]
    return envelope


def attach_evidence_provenance(
    *,
    snippet_id: str,
    source_version: str,
    text: str,
    request: Mapping[str, Any],
    existing_envelope: Mapping[str, Any] | None = None,
) -> dict:
    req = normalize_envelope_request(request)
    file_map: dict[str, bytes] = {}
    members = []
    for raw in req["input_members"]:
        body = raw.get("bytes")
        if isinstance(body, str):
            body = body.encode("utf-8")
        if body is None:
            raise EnvelopeError("EV-ARTIFACTS", f"member {raw.get('path')} missing source bytes")
        file_map[raw["path"]] = body
        digest = ps.sha256_bytes(body)
        members.append(
            _member_payload(
                {
                    "path": raw["path"],
                    "digest": digest,
                    "size_bytes": len(body),
                    "media_type": raw.get("media_type"),
                    "source_commit": raw.get("source_commit"),
                },
                req["source_commit"],
            )
        )
    store = _store_from(req, file_map)
    classification = req["classification"]
    env = req["environment"]
    run_id = (existing_envelope or {}).get("run_id") or req["run_id"]
    set_id = (existing_envelope or {}).get("artifact_set_id") or uuid7()
    event_produced = (existing_envelope or {}).get("produced_by_event_id") or uuid7()
    event_derived = (existing_envelope or {}).get("derived_from_event_id") or uuid7()
    event_verifies = (existing_envelope or {}).get("verifies_event_id") or uuid7()
    text_digest = ps.sha256_bytes(text.encode("utf-8"))
    evid_ident = snippet_id.split(":", 1)[1] if snippet_id.startswith("evidence:") else snippet_id

    store.create_run(
        {
            "schema_version": ps.SCHEMA_VERSION,
            "run_id": run_id,
            "started_at": req["started_at"],
            "ended_at": req["ended_at"],
            "environment": env,
            "classification": classification,
            "status": "succeeded",
            "producer": typed_ref("commit", req["tool_commit"], classification),
            "inputs": _unique_refs(
                [
                    typed_ref("commit", req["source_commit"], classification),
                    typed_ref("commit", req["config_commit"], classification),
                    typed_ref("commit", req["tool_commit"], classification),
                    typed_ref("issue", req["issue"], classification),
                    typed_ref("criterion", req["criterion"], classification),
                    typed_ref("campaign", req["campaign"], classification),
                    typed_ref("record-version", source_version, classification),
                ]
            ),
            "outputs": [typed_ref("evidence", evid_ident, classification, digest=text_digest)],
        }
    )
    aset = store.create_artifact_set(
        {
            "schema_version": ps.SCHEMA_VERSION,
            "set_id": set_id,
            "created_at": req["started_at"],
            "classification": classification,
            "environment": env,
            "producer": typed_ref("run", run_id, classification),
            "members": members,
        }
    )
    event_kwargs = {}
    if env == SYNTHETIC_ENV:
        event_kwargs["synthetic_reason"] = req["synthetic_reason"]
    store.create_event(
        {
            "schema_version": ps.SCHEMA_VERSION,
            "event_id": event_produced,
            "occurred_at": req["occurred_at"],
            "relation": "produced-by",
            "source": typed_ref("evidence", evid_ident, classification, digest=text_digest),
            "target": typed_ref("run", run_id, classification),
            "environment": env,
            "classification": classification,
            "run": typed_ref("run", run_id, classification),
            **event_kwargs,
        }
    )
    store.create_event(
        {
            "schema_version": ps.SCHEMA_VERSION,
            "event_id": event_derived,
            "occurred_at": req["occurred_at"],
            "relation": "derived-from",
            "source": typed_ref("evidence", evid_ident, classification, digest=text_digest),
            "target": typed_ref("record-version", source_version, classification),
            "environment": env,
            "classification": classification,
            "run": typed_ref("run", run_id, classification),
            **event_kwargs,
        }
    )
    store.create_event(
        {
            "schema_version": ps.SCHEMA_VERSION,
            "event_id": event_verifies,
            "occurred_at": req["occurred_at"],
            "relation": "verifies",
            "source": typed_ref("evidence", evid_ident, classification, digest=text_digest),
            "target": typed_ref("record-version", source_version, classification),
            "environment": env,
            "classification": classification,
            "run": typed_ref("run", run_id, classification),
            **event_kwargs,
        }
    )
    envelope = {
        "schema": ENVELOPE_SCHEMA,
        "producer_family": PRODUCER_FAMILY,
        "run_id": run_id,
        "artifact_set_id": set_id,
        "artifact_set_digest": aset["record"]["set_digest"],
        "produced_by_event_id": event_produced,
        "derived_from_event_id": event_derived,
        "verifies_event_id": event_verifies,
        "environment": env,
        "classification": classification,
        "evidence_class": env,
        "issue": req["issue"],
        "criterion": req["criterion"],
        "campaign": req["campaign"],
        "tool_commit": req["tool_commit"],
        "config_commit": req["config_commit"],
        "source_commit": req["source_commit"],
        "source_version": source_version,
        "source_content_digest": text_digest,
    }
    if req.get("synthetic_reason"):
        envelope["synthetic_reason"] = req["synthetic_reason"]
    return envelope
