#!/usr/bin/env python3
"""User-guide / process-page composition provenance (Task `0037-27.03`).

Links a guide/page fragment to exact records, evidence, typed claims,
instructions, policy, and config; records authoring issue/criterion/run,
composition input/output hashes, the review decision, and invalidation
cause. Generated HTML stays derived from `_src/` sources: provenance lives
in `provenance/` manifests, never as injection into HTML.

Writers bind to `provenance_store.SCHEMA_VERSION` and existing endpoint
kinds/relations. Typed claims use `ai_workflow_persist` (0037-27.01).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import ai_workflow_persist as awp  # noqa: E402
import provenance_query as pq  # noqa: E402
import provenance_store as ps  # noqa: E402
import provenance_views as pv  # noqa: E402
import version_id as vid  # noqa: E402

SCHEMA = "page-composition-provenance@v1"
INPUT_ROLES = (
    "fragment",
    "records",
    "evidence",
    "claims",
    "instructions",
    "policy",
    "config",
)
OUTPUT_ROLE = "composed-page"
MEMBER_ROLES = INPUT_ROLES + (OUTPUT_ROLE,)
IDENTITY_ROLES = (
    "fragment",
    "records",
    "evidence",
    "instructions",
    "policy",
    "config",
)
HTML_PROVENANCE_MARKERS = (
    "page-composition-provenance@",
    "provenance/runs/",
    "run_id",
    "set_digest",
    "invalidated-by",
    "regenerated-by",
)


class PageCompositionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ref(kind: str, ident: str, **extra: Any) -> Dict[str, Any]:
    uri = ident if str(ident).startswith(kind + ":") else f"{kind}:{ident}"
    value = {
        "schema_version": ps.SCHEMA_VERSION,
        "kind": kind,
        "uri": uri,
        "classification": extra.pop("classification", "internal"),
    }
    value.update(extra)
    return value


def _artifact_ref(path: str, digest: str) -> Dict[str, Any]:
    return _ref("artifact", f"{path}@{digest}", digest=digest)


def _member(
    path: str,
    content: bytes,
    *,
    source_commit: str,
    media_type: str,
    role: str,
) -> Dict[str, Any]:
    if role not in MEMBER_ROLES:
        raise PageCompositionError("PCP-ROLE", f"unknown member role {role}")
    return {
        "path": path,
        "digest": ps.sha256_bytes(content),
        "size_bytes": len(content),
        "media_type": media_type,
        "source_commit": source_commit,
        "role": role,
    }


def input_identity(members: Sequence[Mapping[str, Any]]) -> str:
    keyed = {}
    for member in members:
        role = member.get("role")
        if role in IDENTITY_ROLES:
            keyed[role] = member["digest"]
    missing = [role for role in IDENTITY_ROLES if role not in keyed]
    if missing:
        raise PageCompositionError("PCP-IDENTITY", f"missing identity roles: {missing}")
    return ps.sha256_bytes(ps.canonical_bytes(keyed))


def assert_html_without_provenance(html_text: str) -> None:
    """Reject uncontrolled provenance injection into generated HTML."""
    lowered = html_text.lower()
    for marker in HTML_PROVENANCE_MARKERS:
        if marker.lower() in lowered:
            raise PageCompositionError(
                "PCP-HTML-INJECT",
                f"HTML contains provenance marker {marker!r}",
            )


class PageCompositionWorkflow:
    def __init__(self, root: Path, *, clock: Any = utc_now) -> None:
        self.root = Path(root)
        self.store = ps.ProvenanceStore(self.root)
        self.persist = awp.AIWorkflowPersist(self.root)
        self.clock = clock
        self._index: List[Dict[str, Any]] = []
        self._load_index()

    def _stamp(self) -> str:
        return self.clock() if callable(self.clock) else str(self.clock)

    def _put_file(self, path: str, content: bytes) -> None:
        disk = self.root / path
        disk.parent.mkdir(parents=True, exist_ok=True)
        disk.write_bytes(content)

    def _event(
        self,
        *,
        relation: str,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
        run_id: str,
        occurred_at: str,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "schema_version": ps.SCHEMA_VERSION,
            "event_id": vid.uuid7(),
            "occurred_at": occurred_at,
            "relation": relation,
            "source": dict(source),
            "target": dict(target),
            "environment": "development-test",
            "classification": "internal",
            "run": _ref("run", run_id),
        }
        if extra:
            payload.update(dict(extra))
        return self.store.create_event(payload)

    def _load_index(self) -> None:
        sets_dir = self.root / "provenance" / "artifact-sets"
        if not sets_dir.is_dir():
            return
        for path in sorted(sets_dir.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            members = record.get("members") or []
            out = [m for m in members if m.get("role") == OUTPUT_ROLE]
            frag = [m for m in members if m.get("role") == "fragment"]
            if not out or not frag:
                continue
            self._index.append(
                {
                    "schema": SCHEMA,
                    "run_id": ((record.get("producer") or {}).get("uri") or "run:").split(":", 1)[-1],
                    "set_id": record.get("set_id"),
                    "identity": input_identity(members),
                    "fragment_path": frag[0]["path"],
                    "output_path": out[0]["path"],
                    "output_digest": out[0]["digest"],
                    "members": members,
                    "artifact_set": {"record": record},
                }
            )

    def require_approved_claims(
        self,
        claim_ids: Sequence[str],
        *,
        decision_id: str,
    ) -> List[Dict[str, Any]]:
        """Every published claim must trace to approved source evidence and the review decision."""
        traces = []
        decision_uri = (
            decision_id if decision_id.startswith("decision:") else f"decision:{decision_id}"
        )
        for claim_id in claim_ids:
            try:
                trace = self.persist.trace_claim(claim_id)
            except awp.AIWorkflowPersistError as exc:
                raise PageCompositionError("PCP-CLAIM", exc.message) from exc
            claim = trace["claim"]
            if claim.get("invalidation", {}).get("invalidated"):
                raise PageCompositionError(
                    "PCP-UNAPPROVED",
                    f"{claim_id} is invalidated and cannot be published",
                )
            evidence = list(claim.get("evidence_refs") or [])
            if not evidence:
                raise PageCompositionError(
                    "PCP-UNAPPROVED",
                    f"{claim_id} has no evidence_refs",
                )
            pins = trace["pins"]
            for key in ("record", "evidence"):
                pin = pins.get(key) or {}
                if pin.get("present") is False or not pin.get("digest"):
                    raise PageCompositionError(
                        "PCP-UNAPPROVED",
                        f"{claim_id} missing approved {key} pin",
                    )
            if decision_uri not in evidence:
                raise PageCompositionError(
                    "PCP-UNAPPROVED",
                    f"{claim_id} is not linked to review decision {decision_uri}",
                )
            traces.append(trace)
        return traces

    def compose(
        self,
        *,
        fragment_path: str,
        fragment_bytes: bytes,
        records_path: str,
        records_bytes: bytes,
        evidence_path: str,
        evidence_bytes: bytes,
        instructions_path: str,
        instructions_bytes: bytes,
        policy_path: str,
        policy_bytes: bytes,
        config_path: str,
        config_bytes: bytes,
        output_path: str,
        output_bytes: bytes,
        claim_ids: Sequence[str],
        issue: str,
        criterion: str,
        decision_id: str,
        source_commit: str,
        tool_commit: str,
        config_commit: str,
        campaign: str = "0037-27.03-pages",
        previous: Optional[Mapping[str, Any]] = None,
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        if output_path.endswith(".html") or b"<html" in output_bytes[:400].lower():
            assert_html_without_provenance(output_bytes.decode("utf-8", errors="replace"))
            raise PageCompositionError(
                "PCP-HTML-SOURCE",
                "composed output must be a _src page-model, not generated HTML",
            )
        traces = self.require_approved_claims(claim_ids, decision_id=decision_id)
        started = started_at or self._stamp()
        ended = ended_at or self._stamp()
        run_id = vid.uuid7()
        set_id = vid.uuid7()

        claims_blob = ps.canonical_bytes(
            [{"claim_id": cid, "digest": ps.sha256_bytes(ps.canonical_bytes(self.persist.read_claim(cid)))} for cid in claim_ids]
        )
        claims_path = "provenance/_page-inputs/published-claims.json"

        self._put_file(fragment_path, fragment_bytes)
        self._put_file(records_path, records_bytes)
        self._put_file(evidence_path, evidence_bytes)
        self._put_file(instructions_path, instructions_bytes)
        self._put_file(policy_path, policy_bytes)
        self._put_file(config_path, config_bytes)
        self._put_file(claims_path, claims_blob)
        self._put_file(output_path, output_bytes)

        members = [
            _member(fragment_path, fragment_bytes, source_commit=source_commit, media_type="application/json", role="fragment"),
            _member(records_path, records_bytes, source_commit=source_commit, media_type="application/json", role="records"),
            _member(evidence_path, evidence_bytes, source_commit=source_commit, media_type="application/json", role="evidence"),
            _member(claims_path, claims_blob, source_commit=source_commit, media_type="application/json", role="claims"),
            _member(instructions_path, instructions_bytes, source_commit=source_commit, media_type="text/plain", role="instructions"),
            _member(policy_path, policy_bytes, source_commit=source_commit, media_type="application/json", role="policy"),
            _member(config_path, config_bytes, source_commit=config_commit, media_type="application/json", role="config"),
            _member(output_path, output_bytes, source_commit=source_commit, media_type="application/json", role=OUTPUT_ROLE),
        ]
        identity = input_identity(members)
        in_digest = identity
        out_digest = ps.sha256_bytes(output_bytes)
        fragment_digest = ps.sha256_bytes(fragment_bytes)

        run_inputs = [
            _ref("commit", source_commit),
            _ref("commit", tool_commit),
            _ref("commit", config_commit),
            _ref("issue", issue),
            _ref("criterion", criterion),
            _ref("campaign", campaign),
            _ref("decision", decision_id),
            _artifact_ref(fragment_path, fragment_digest),
            _artifact_ref(records_path, ps.sha256_bytes(records_bytes)),
            _artifact_ref(evidence_path, ps.sha256_bytes(evidence_bytes)),
            _artifact_ref(instructions_path, ps.sha256_bytes(instructions_bytes)),
            _artifact_ref(policy_path, ps.sha256_bytes(policy_bytes)),
            _artifact_ref(config_path, ps.sha256_bytes(config_bytes)),
        ]
        for cid in claim_ids:
            rec = self.persist.read_claim(cid)
            digest = ps.sha256_bytes(ps.canonical_bytes(rec["claim"]))
            cref = _ref("artifact", cid, digest=digest)
            cref["uri"] = f"artifact:{cid}"
            run_inputs.append(cref)

        run = self.store.create_run(
            {
                "schema_version": ps.SCHEMA_VERSION,
                "run_id": run_id,
                "started_at": started,
                "ended_at": ended,
                "environment": "development-test",
                "classification": "internal",
                "status": "succeeded",
                "producer": _ref("commit", tool_commit),
                "inputs": run_inputs,
                "outputs": [_ref("artifact-set", set_id)],
            }
        )
        aset = self.store.create_artifact_set(
            {
                "schema_version": ps.SCHEMA_VERSION,
                "set_id": set_id,
                "created_at": ended,
                "classification": "internal",
                "environment": "development-test",
                "producer": _ref("run", run_id),
                "members": members,
            }
        )
        out_ref = _artifact_ref(output_path, out_digest)
        frag_ref = _artifact_ref(fragment_path, fragment_digest)
        self._event(relation="produced-by", source=out_ref, target=_ref("run", run_id), run_id=run_id, occurred_at=ended)
        self._event(relation="derived-from", source=out_ref, target=frag_ref, run_id=run_id, occurred_at=ended)
        self._event(relation="implements", source=out_ref, target=_ref("issue", issue), run_id=run_id, occurred_at=ended)
        self._event(relation="implements", source=out_ref, target=_ref("decision", decision_id), run_id=run_id, occurred_at=ended)
        self._event(relation="verifies", source=_ref("run", run_id), target=_ref("criterion", criterion), run_id=run_id, occurred_at=ended)
        self._event(
            relation="decides",
            source=_ref("decision", decision_id),
            target=_ref("criterion", criterion),
            run_id=run_id,
            occurred_at=ended,
        )
        self._event(
            relation="triggered",
            source=_ref("issue", issue),
            target=_ref("run", run_id),
            run_id=run_id,
            occurred_at=ended,
        )

        invalidation = None
        if previous is not None:
            invalidation = self._link_replacement(previous, out_ref, run_id, ended, identity)

        record = {
            "schema": SCHEMA,
            "schema_version": ps.SCHEMA_VERSION,
            "run_id": run_id,
            "set_id": set_id,
            "identity": identity,
            "issue": issue,
            "criterion": criterion,
            "decision_id": decision_id if decision_id.startswith("decision:") else f"decision:{decision_id}",
            "fragment_path": fragment_path,
            "output_path": output_path,
            "input_hash": in_digest,
            "output_hash": out_digest,
            "claim_ids": list(claim_ids),
            "claim_traces": [
                {
                    "claim_id": t["claim_id"],
                    "evidence_refs": t["evidence_refs"],
                    "record_pin": t["pins"]["record"],
                    "evidence_pin": t["pins"]["evidence"],
                }
                for t in traces
            ],
            "members": members,
            "run": run,
            "artifact_set": aset,
            "invalidation": invalidation,
        }
        self._index.append(record)
        return record

    def _link_replacement(
        self,
        previous: Mapping[str, Any],
        new_out: Mapping[str, Any],
        run_id: str,
        occurred_at: str,
        new_identity: str,
    ) -> Dict[str, Any]:
        old_out = _artifact_ref(previous["output_path"], previous["output_hash"])
        finding_id = vid.uuid7()
        finding = self.store.create_finding(
            {
                "schema_version": ps.SCHEMA_VERSION,
                "finding_id": finding_id,
                "detected_at": occurred_at,
                "state": "invalidated",
                "classification": "internal",
                "environment": "development-test",
                "subject": old_out,
                "detected_during": _ref("run", run_id),
                "evidence": [old_out, dict(new_out)],
            }
        )
        self._event(
            relation="invalidated-by",
            source=old_out,
            target=_ref("run", run_id),
            run_id=run_id,
            occurred_at=occurred_at,
        )
        self._event(
            relation="regenerated-by",
            source=new_out,
            target=_ref("run", run_id),
            run_id=run_id,
            occurred_at=occurred_at,
        )
        self._event(
            relation="supersedes",
            source=new_out,
            target=old_out,
            run_id=run_id,
            occurred_at=occurred_at,
        )
        return {
            "previous_page": old_out,
            "replacement_page": dict(new_out),
            "finding": finding,
            "previous_identity": previous.get("identity"),
            "new_identity": new_identity,
            "cause": "governed composition input change",
        }

    def stale_pages(
        self,
        *,
        fragment_path: str,
        fragment_bytes: bytes,
        records_bytes: bytes,
        evidence_bytes: bytes,
        instructions_bytes: bytes,
        policy_bytes: bytes,
        config_bytes: bytes,
    ) -> List[Dict[str, Any]]:
        current = {
            "fragment": ps.sha256_bytes(fragment_bytes),
            "records": ps.sha256_bytes(records_bytes),
            "evidence": ps.sha256_bytes(evidence_bytes),
            "instructions": ps.sha256_bytes(instructions_bytes),
            "policy": ps.sha256_bytes(policy_bytes),
            "config": ps.sha256_bytes(config_bytes),
        }
        stale: List[Dict[str, Any]] = []
        for record in self._index:
            if record["fragment_path"] != fragment_path:
                continue
            keyed = {
                m["role"]: m["digest"]
                for m in record["members"]
                if m.get("role") in IDENTITY_ROLES
            }
            if keyed != current:
                stale.append(
                    {
                        "output_path": record["output_path"],
                        "output_hash": record["output_hash"],
                        "run_id": record["run_id"],
                        "previous_identity": record["identity"],
                    }
                )
        return stale

    def regeneration_work(
        self,
        *,
        fragment_path: str,
        fragment_bytes: bytes,
        records_bytes: bytes,
        evidence_bytes: bytes,
        instructions_bytes: bytes,
        policy_bytes: bytes,
        config_bytes: bytes,
    ) -> List[Dict[str, Any]]:
        """Bounded linked regeneration work for drifted composition inputs."""
        return self.stale_pages(
            fragment_path=fragment_path,
            fragment_bytes=fragment_bytes,
            records_bytes=records_bytes,
            evidence_bytes=evidence_bytes,
            instructions_bytes=instructions_bytes,
            policy_bytes=policy_bytes,
            config_bytes=config_bytes,
        )

    def trace(self, *, kind: str, identifier: str, direction: str = "reverse") -> Dict[str, Any]:
        pv.build_views(self.root)
        return pq.query_trace(self.root, kind=kind, identifier=identifier, direction=direction)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Record page-composition provenance")
    parser.add_argument("--root", required=True)
    parser.add_argument("--fragment", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    print(json.dumps({"root": args.root, "fragment": args.fragment, "output": args.output}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
