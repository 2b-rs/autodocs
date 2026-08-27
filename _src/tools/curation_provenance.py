#!/usr/bin/env python3
"""Common provenance envelope for curation items, queues, decisions, findings.

Task ``0037-26.05``. Adapts the 0037-17 store (runs, findings, events, artifact
sets) onto the 0006 curation lifecycle without treating requester identity as
approval. Does not rewrite legacy queue history; unknown prior context is
``unknown``/``legacy`` via ``adapt_legacy_confidence``.
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import provenance_store as ps  # noqa: E402
import version_id as vid  # noqa: E402

ENVELOPE_SCHEMA = "provenance-envelope@v1"
PRODUCER_FAMILY = "curation"

LIFECYCLE = ("open", "claim", "decision", "apply", "publish")

# Requester transport identity never satisfies curator authority.
AUTHORITY_ROLES = frozenset({"curator", "operator", "registered-curator"})
REQUESTER_ROLES = frozenset({"requester", "submitter", "github_authenticated", "self_declared"})

TRANSITION_FROM = {
    "open": (None, "open"),
    "claim": ("open",),
    "decision": ("claimed",),
    "apply": ("accepted",),
    "publish": ("applied",),
    "invalidate": ("applied", "accepted"),
    "supersede": ("applied", "published"),
}


class CurationProvenanceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


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


def envelope_digest(envelope: Mapping[str, Any]) -> str:
    body = {key: value for key, value in envelope.items() if key != "digest"}
    return ps.sha256_bytes(ps.canonical_bytes(body))


def empty_envelope() -> Dict[str, Any]:
    return {
        "schema": ENVELOPE_SCHEMA,
        "producer_family": PRODUCER_FAMILY,
        "finding": None,
        "source": {"report": None, "evidence": None, "version": None},
        "issue": None,
        "criterion": None,
        "run": None,
        "campaign": None,
        "claim": None,
        "queue_transitions": [],
        "decision": None,
        "applied_change": None,
        "invalidation": None,
        "supersession": None,
        "published_result": None,
        "requester": None,
        "authority": None,
        "legacy": ps.adapt_legacy_confidence(None),
    }


def attach_envelope(item: Mapping[str, Any], envelope: Mapping[str, Any]) -> Dict[str, Any]:
    out = deepcopy(dict(item))
    env = dict(envelope)
    env["digest"] = envelope_digest(env)
    out["provenance"] = env
    return out


def _clock(session: "CurationProvenanceSession") -> str:
    session._ticks += 1
    return f"2026-08-27T12:{session._ticks:02d}:00Z"


class CurationProvenanceSession:
    """Hermetic producer: writes only under ``root`` (tests use TemporaryDirectory)."""

    def __init__(self, root: Path, *, file_bytes: Optional[Any] = None) -> None:
        self.root = Path(root)
        self.files: Dict[str, bytes] = {} if file_bytes is None else file_bytes
        self.store = ps.ProvenanceStore(self.root, file_bytes=self.files.__getitem__)
        self.items: Dict[str, Dict[str, Any]] = {}
        self.queue: Dict[str, Dict[str, Any]] = {"open": {}, "claimed": {}, "done": {}}
        self._ticks = 8
        self._event_n = 0x4000
        self.commit = "c" * 40

    def _event_id(self) -> str:
        self._event_n += 1
        return f"018f4a31-{self._event_n:04x}-7abc-8def-0123456789ab"

    def seed_context(
        self,
        *,
        run_id: str,
        finding_id: str,
        issue: str = "0037-26.05",
        criterion: str = "AC-001",
        campaign: str = "curation-fixture",
        report_path: str = "reports/extraction.json",
        report_bytes: bytes = b'{"schema":"extraction-report@v1"}',
        version: str = "AUTOSAR/AP/record/SWS_LOG_00201@rel:R25-11#abcd1234",
    ) -> Dict[str, Any]:
        self.files[report_path] = report_bytes
        stamp = "2026-08-27T12:01:00Z"
        set_id = "018f4a31-32ad-7abc-8def-0123456789ab"
        run = {
            "schema_version": "1.0",
            "run_id": run_id,
            "started_at": stamp,
            "ended_at": "2026-08-27T12:02:00Z",
            "environment": "assessment",
            "classification": "internal",
            "status": "succeeded",
            "producer": typed_ref("commit", self.commit),
            "inputs": [
                typed_ref("commit", self.commit),
                typed_ref("issue", issue),
                typed_ref("criterion", criterion),
                typed_ref("campaign", campaign),
            ],
            "outputs": [typed_ref("artifact-set", set_id)],
        }
        digest = ps.sha256_bytes(report_bytes)
        aset = {
            "schema_version": "1.0",
            "set_id": set_id,
            "created_at": stamp,
            "classification": "internal",
            "environment": "assessment",
            "producer": typed_ref("run", run_id),
            "members": [
                {
                    "path": report_path,
                    "digest": digest,
                    "size_bytes": len(report_bytes),
                    "media_type": "application/json",
                    "source_commit": self.commit,
                }
            ],
        }
        finding = {
            "schema_version": "1.0",
            "finding_id": finding_id,
            "detected_at": stamp,
            "state": "open",
            "classification": "internal",
            "environment": "assessment",
            "subject": typed_ref("issue", issue),
            "detected_during": typed_ref("run", run_id),
            "evidence": [
                typed_ref(
                    "artifact",
                    f"{report_path}@{digest}",
                    digest=digest,
                )
            ],
        }
        self.store.create_run(run)
        self.store.create_artifact_set(aset)
        self.store.create_finding(finding)
        return {
            "run": typed_ref("run", run_id),
            "finding": typed_ref("finding", finding_id),
            "issue": typed_ref("issue", issue),
            "criterion": typed_ref("criterion", criterion),
            "campaign": typed_ref("campaign", campaign),
            "report": typed_ref("artifact", f"{report_path}@{digest}", digest=digest),
            "evidence": typed_ref("evidence", finding_id),
            "version": typed_ref("record-version", version),
            "finding_record": finding,
            "report_digest": digest,
        }

    def _put_event(self, relation: str, source: Mapping[str, Any], target: Mapping[str, Any], run: Mapping[str, Any]) -> Dict[str, Any]:
        occurred = _clock(self)
        payload = {
            "schema_version": "1.0",
            "event_id": self._event_id(),
            "occurred_at": occurred,
            "relation": relation,
            "source": dict(source),
            "target": dict(target),
            "environment": "assessment",
            "classification": "internal",
            "run": dict(run),
        }
        return self.store.create_event(payload)

    def apply_transition(
        self,
        item_id: str,
        transition: str,
        *,
        actor: str,
        authority_role: str,
        requester: Optional[str] = None,
        outcome: Optional[str] = None,
        context: Mapping[str, Any],
        finding_digest: Optional[str] = None,
        source_version: Optional[str] = None,
        applied_commit: Optional[str] = None,
        published_path: Optional[str] = None,
        published_bytes: Optional[bytes] = None,
        allow_requester_as_approval: bool = False,
    ) -> Dict[str, Any]:
        """Advance one lifecycle step. ``allow_requester_as_approval`` is the
        pre-change baseline (always False for the candidate)."""
        if transition not in ("open", "claim", "decision", "apply", "publish", "invalidate", "supersede"):
            raise CurationProvenanceError("CUR-TRANSITION", f"unknown transition {transition}")

        if transition in ("decision", "apply", "publish", "invalidate") and not allow_requester_as_approval:
            if authority_role in REQUESTER_ROLES or authority_role not in AUTHORITY_ROLES:
                raise CurationProvenanceError(
                    "CUR-UNAUTHORIZED",
                    "requester identity is not curator approval",
                )

        finding_ref = context["finding"]
        finding_id = finding_ref["uri"].split(":", 1)[1]
        matches = list((self.root / "provenance" / "findings").glob(f"*/*/{finding_id}.json"))
        if not matches:
            raise CurationProvenanceError("CUR-FABRICATED", f"finding {finding_id} is not in the store")
        finding_record = json.loads(matches[0].read_text(encoding="utf-8"))
        evidence = finding_record.get("evidence") or []
        current_digest = evidence[0].get("digest") if evidence else None
        if finding_digest is not None and current_digest is not None and finding_digest != current_digest:
            raise CurationProvenanceError("CUR-STALE", "finding evidence digest does not match store")
        expected_version = (context.get("version") or {}).get("uri")
        if source_version is not None and expected_version and source_version != expected_version:
            raise CurationProvenanceError("CUR-STALE", "source version does not match envelope version")

        existing = self.items.get(item_id)
        current_status = None if existing is None else existing.get("status")
        allowed_from = TRANSITION_FROM[transition]
        if current_status not in allowed_from:
            if existing is None and transition != "open":
                raise CurationProvenanceError("CUR-ORPHANED", f"{transition} without an open curation item")
            if transition == "open" and existing is not None:
                raise CurationProvenanceError("CUR-DUPLICATE", "open already recorded for this item")
            if existing is not None:
                raise CurationProvenanceError(
                    "CUR-ORPHANED",
                    f"cannot {transition} from status {current_status}",
                )

        envelope = empty_envelope() if existing is None else deepcopy(existing["provenance"])
        envelope["finding"] = dict(finding_ref)
        envelope["source"] = {
            "report": dict(context["report"]),
            "evidence": dict(context["evidence"]),
            "version": dict(context["version"]),
        }
        envelope["issue"] = dict(context["issue"])
        envelope["criterion"] = dict(context["criterion"])
        envelope["run"] = dict(context["run"])
        envelope["campaign"] = dict(context["campaign"])
        envelope["requester"] = requester
        envelope["legacy"] = ps.adapt_legacy_confidence(None)

        transitions = list(envelope.get("queue_transitions") or [])
        if any(row.get("transition") == transition for row in transitions):
            raise CurationProvenanceError("CUR-DUPLICATE", f"transition {transition} already applied")

        stamp = _clock(self)
        transitions.append(
            {
                "transition": transition,
                "at": stamp,
                "actor": actor,
                "authority_role": authority_role,
                "queue": {"open": "open", "claim": "claimed", "decision": "decided", "apply": "done", "publish": "published"}.get(
                    transition, transition
                ),
            }
        )
        envelope["queue_transitions"] = transitions

        if transition == "open":
            item = {
                "schema": "curation-item@v1",
                "canonical_id": f"AUTOSAR/AP/record/{item_id}",
                "project": "AUTOSAR/AP",
                "release": "R25-11",
                "item_kind": "scrape-observation",
                "origin": "tool",
                "status": "open",
                "subject": f"curation of {item_id}",
                "current_state": None,
                "proposed_state": None,
                "evidence": [context["report"]],
                "counter_evidence": [],
                "decision_basis": {},
                "campaign": context["campaign"]["uri"].split(":", 1)[1],
                "created": stamp,
                "claimed_by": None,
                "decided_by": None,
                "completed_at": None,
                "history": [{"from": None, "to": "open", "at": stamp}],
            }
            item = attach_envelope(item, envelope)
            self.items[item_id] = item
            self.queue["open"][item_id] = {"schema": "curation-flag@v1", "id": item_id, "provenance": item["provenance"]}
            self._put_event("reported-by", finding_ref, typed_ref("curation-item", item["canonical_id"]), context["run"])
            self._put_event("detected-during", finding_ref, context["run"], context["run"])
            return item

        item = deepcopy(existing)
        history = list(item.get("history") or [])

        if transition == "claim":
            item["status"] = "claimed"
            item["claimed_by"] = actor
            envelope["claim"] = {"actor": actor, "at": stamp, "queue": "claimed"}
            self.queue["claimed"][item_id] = self.queue["open"].pop(item_id)
            self.queue["claimed"][item_id]["claimed_by"] = actor
        elif transition == "decision":
            if outcome not in ("accept", "reject"):
                raise CurationProvenanceError("CUR-TRANSITION", "decision requires accept or reject")
            item["status"] = "accepted" if outcome == "accept" else "rejected"
            item["decided_by"] = actor
            decision_id = f"curation:{vid.uuid7()}"
            envelope["authority"] = {"role": authority_role, "actor": actor}
            envelope["decision"] = {
                "id": decision_id,
                "outcome": outcome,
                "actor": actor,
                "authority_role": authority_role,
                "requester": requester,
                "requester_is_approval": False,
                "at": stamp,
            }
            self._put_event(
                "decides",
                typed_ref("decision", decision_id),
                finding_ref,
                context["run"],
            )
        elif transition == "apply":
            if not (item.get("provenance") or {}).get("decision"):
                raise CurationProvenanceError("CUR-ORPHANED", "apply without curator decision")
            if item["status"] != "accepted":
                raise CurationProvenanceError("CUR-ORPHANED", "apply requires accepted decision")
            commit = applied_commit or self.commit
            item["status"] = "applied"
            item["completed_at"] = stamp
            envelope["applied_change"] = typed_ref("commit", commit)
            decision_uri = item["provenance"]["decision"]["id"]
            self._put_event(
                "implements",
                typed_ref("commit", commit),
                typed_ref("decision", decision_uri),
                context["run"],
            )
            self.queue["done"][item_id] = self.queue["claimed"].pop(item_id, self.queue["open"].pop(item_id, {}))
        elif transition == "publish":
            if not (item.get("provenance") or {}).get("applied_change"):
                raise CurationProvenanceError("CUR-ORPHANED", "publish without applied change")
            path = published_path or "reports/curation-published.json"
            body = published_bytes or b'{"schema":"curation-publish@v1"}'
            self.files[path] = body
            digest = ps.sha256_bytes(body)
            pub = typed_ref("artifact", f"{path}@{digest}", digest=digest)
            envelope["published_result"] = pub
            self._put_event("published-as", pub, context["evidence"], context["run"])
        elif transition == "invalidate":
            envelope["invalidation"] = {"at": stamp, "actor": actor}
            self._put_event("invalidated-by", finding_ref, typed_ref("decision", item["provenance"]["decision"]["id"]), context["run"])
        elif transition == "supersede":
            envelope["supersession"] = {"at": stamp, "actor": actor}
            item["status"] = "superseded"

        history.append({"from": current_status, "to": item["status"], "at": stamp, "transition": transition})
        item["history"] = history
        # Keep envelope.decision/applied from prior steps when not overwritten.
        for key in (
            "claim",
            "decision",
            "applied_change",
            "published_result",
            "authority",
            "invalidation",
            "supersession",
        ):
            if envelope.get(key) is None and (item.get("provenance") or {}).get(key) is not None:
                envelope[key] = item["provenance"][key]
        item = attach_envelope(item, envelope)
        self.items[item_id] = item
        return item

    def reverse_links(self, item_id: str) -> Dict[str, Any]:
        item = self.items[item_id]
        env = item["provenance"]
        return {
            "item": item["canonical_id"],
            "finding": env["finding"]["uri"],
            "run": env["run"]["uri"],
            "issue": env["issue"]["uri"],
            "criterion": env["criterion"]["uri"],
            "campaign": env["campaign"]["uri"],
            "report": env["source"]["report"]["uri"],
            "decision": (env.get("decision") or {}).get("id"),
            "applied_change": (env.get("applied_change") or {}).get("uri"),
            "published_result": (env.get("published_result") or {}).get("uri"),
            "queue_transitions": [row["transition"] for row in env["queue_transitions"]],
        }


def happy_path_sequence() -> List[str]:
    return list(LIFECYCLE)


def transition_allowed(current: Optional[str], nxt: str) -> bool:
    if nxt == "open":
        return current is None
    mapping = {
        None: {"open"},
        "open": {"claim"},
        "claimed": {"decision"},
        "accepted": {"apply"},
        "applied": {"publish", "invalidate", "supersede"},
        "rejected": set(),
    }
    return nxt in mapping.get(current, set())
