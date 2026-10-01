#!/usr/bin/env python3
"""Persist AI workflow runs and typed claims (Task `0037-27.01`).

Uses the shared ProvenanceStore for runs, artifact-sets, and events. Typed
claims use their own `claim:<uuid7>` ID family and one JSON file each under
`provenance/claims/<uuid>.json`. Legacy `_src/ai/traces` adapters never invent
prompts, models, or runs; missing fields become explicit `unknown`/`legacy`
confidence.

Governed pins: record, evidence, policy, prompt, model, config, input.
Each pin is a typed reference with a sha256 digest (except an explicit
absent/unknown pin). A digest change invalidates dependent claims without
deleting prior files.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import stat
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import provenance_store as ps  # noqa: E402
import typed_claim as tc  # noqa: E402
import version_id as vid  # noqa: E402

SCHEMA = "typed-claim-persistence@v1"
RUN_SCHEMA = "ai-workflow-run@v1"
ADAPTER = "legacy-ai-trace@v1"
# Bind writers to 0037-17/19 schema files; do not fork local copies.
REPO_SCHEMA_DIR = _ROOT / "provenance" / "_schema"
BOUND_SCHEMAS = {
    "typed-reference": "typed-reference-v1.schema.json",
    "run": "run-v1.schema.json",
    "finding": "finding-v1.schema.json",
    "artifact-set": "artifact-set-v1.schema.json",
    "event": "provenance-event-v1.schema.json",
}
GOVERNED_PINS = ("record", "evidence", "policy", "prompt", "model", "config", "input")
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UUIDV7_RE = ps.UUIDV7_RE
CLAIM_ID_RE = re.compile(
    r"^claim:[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


class AIWorkflowPersistError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_bound_schema(kind: str, schema_dir: Optional[Path] = None) -> Dict[str, Any]:
    directory = Path(schema_dir) if schema_dir else REPO_SCHEMA_DIR
    name = BOUND_SCHEMAS[kind]
    path = directory / name
    if not path.is_file():
        raise AIWorkflowPersistError(
            "AWP-SCHEMA-MISSING", f"required schema {name} absent at {path}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def validate_against_bound_schema(
    kind: str, record: Mapping[str, Any], schema_dir: Optional[Path] = None
) -> None:
    """Fail closed on extra properties or missing required fields vs provenance/_schema."""
    schema = load_bound_schema(kind, schema_dir)
    allowed = set(schema.get("properties") or {})
    extra = set(record) - allowed
    if extra and schema.get("additionalProperties") is False:
        raise AIWorkflowPersistError(
            "AWP-SCHEMA-DEVIATION",
            f"{kind} fields {sorted(extra)} are not in {BOUND_SCHEMAS[kind]} (finding, not a local fork)",
        )
    for key in schema.get("required") or []:
        if key not in record:
            raise AIWorkflowPersistError(
                "AWP-SCHEMA-DEVIATION",
                f"{kind} missing required {key} from {BOUND_SCHEMAS[kind]}",
            )


def _validate_nested_typed_refs(kind: str, record: Mapping[str, Any]) -> None:
    refs: list = []
    if kind == "run":
        refs.append(record.get("producer"))
        refs.extend(record.get("inputs") or [])
        refs.extend(record.get("outputs") or [])
    elif kind == "event":
        refs.extend([record.get("source"), record.get("target"), record.get("run")])
    elif kind == "finding":
        refs.extend([record.get("subject"), record.get("detected_during")])
        refs.extend(record.get("evidence") or [])
    elif kind == "artifact-set":
        refs.append(record.get("producer"))
    for item in refs:
        if isinstance(item, Mapping):
            validate_against_bound_schema("typed-reference", item)


def _canonical_bytes(value: Any) -> bytes:
    return ps.canonical_bytes(value)


def digest_bytes(data: bytes) -> str:
    return ps.sha256_bytes(data)


def digest_text(text: str) -> str:
    return digest_bytes(text.encode("utf-8"))


def _require_digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.match(value):
        raise AIWorkflowPersistError("AWP-BARE-ID", f"{field} requires sha256:<hex> digest")
    return value


def typed_ref(
    kind: str,
    ident: str,
    *,
    digest: Optional[str] = None,
    classification: str = "internal",
    environment: str = "development-test",
    require_digest: bool = False,
) -> Dict[str, Any]:
    if not isinstance(kind, str) or not kind or kind == ident:
        raise AIWorkflowPersistError("AWP-BARE-ID", f"invalid kind {kind!r}")
    if not isinstance(ident, str) or not ident.strip():
        raise AIWorkflowPersistError("AWP-BARE-ID", "empty identifier")
    if ident.strip() == kind or ":" not in f"{kind}:{ident}":
        raise AIWorkflowPersistError("AWP-BARE-ID", f"bare identifier {ident!r}")
    if ident.startswith(kind + ":"):
        uri = ident
        rest = ident.split(":", 1)[1]
    else:
        if ":" in ident and not ident.startswith(kind + ":"):
            # Allow claim:/artifact: ids as artifact URIs.
            if kind == "artifact" and ident.startswith("claim:"):
                uri = f"artifact:{ident}"
                rest = ident
            else:
                raise AIWorkflowPersistError("AWP-BARE-ID", f"{kind} URI kind mismatch for {ident!r}")
        else:
            uri = f"{kind}:{ident}"
            rest = ident
    if not rest or rest == kind:
        raise AIWorkflowPersistError("AWP-BARE-ID", f"bare {kind} id")
    if kind == "run" and UUIDV7_RE.match(rest) is None and require_digest:
        raise AIWorkflowPersistError("AWP-BARE-ID", "run id must be UUIDv7")
    obj: Dict[str, Any] = {
        "schema_version": ps.SCHEMA_VERSION,
        "kind": kind,
        "uri": uri,
        "classification": classification,
        "environment": environment,
    }
    if digest is not None:
        obj["digest"] = _require_digest(digest, f"{kind} digest")
    elif require_digest:
        raise AIWorkflowPersistError("AWP-BARE-ID", f"{kind}:{rest} is a bare id without digest")
    validate_against_bound_schema("typed-reference", obj)
    return obj


def pin_from_bytes(kind: str, ident: str, data: bytes, **kwargs: Any) -> Dict[str, Any]:
    return typed_ref(kind, ident, digest=digest_bytes(data), require_digest=True, **kwargs)


def _absent_pin(name: str, reason: str) -> Dict[str, Any]:
    return {
        "name": name,
        "present": False,
        "invented": False,
        "reason": reason,
    }


def validate_pins(pins: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(pins, dict):
        raise AIWorkflowPersistError("AWP-PIN", "pins must be an object")
    missing = [key for key in GOVERNED_PINS if key not in pins]
    if missing:
        raise AIWorkflowPersistError("AWP-PIN", f"missing governed pins: {missing}")
    extra = sorted(set(pins) - set(GOVERNED_PINS))
    if extra:
        raise AIWorkflowPersistError("AWP-PIN", f"unknown pin keys: {extra}")
    out: Dict[str, Any] = {}
    for key in GOVERNED_PINS:
        pin = pins[key]
        if not isinstance(pin, dict):
            raise AIWorkflowPersistError("AWP-PIN", f"pin {key} must be an object")
        if pin.get("present") is False:
            if pin.get("invented"):
                raise AIWorkflowPersistError("AWP-INVENTED", f"absent pin {key} marked invented")
            out[key] = {
                "name": key,
                "present": False,
                "invented": False,
                "reason": pin.get("reason") or "unknown",
            }
            continue
        digest = pin.get("digest")
        uri = pin.get("uri") or pin.get("ident")
        kind = pin.get("kind") or "artifact"
        if not uri or not digest:
            raise AIWorkflowPersistError("AWP-BARE-ID", f"pin {key} needs uri and digest")
        out[key] = typed_ref(kind, uri, digest=digest, require_digest=True)
    return out


def pins_changed(old: Mapping[str, Any], new: Mapping[str, Any]) -> list:
    old_n = validate_pins(old)
    new_n = validate_pins(new)
    changed = []
    for key in GOVERNED_PINS:
        if _canonical_bytes(old_n[key]) != _canonical_bytes(new_n[key]):
            changed.append(key)
    return changed


def adapt_legacy_trace(trace: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Map a legacy ai/traces JSON object without inventing prompt/model/run."""
    if not trace:
        conf = ps.adapt_legacy_confidence(None)
        return {
            "adapter": ADAPTER,
            "confidence": conf["confidence"],
            "prompt": _absent_pin("prompt", "no trace"),
            "model": _absent_pin("model", "no trace"),
            "run_id": None,
            "policy_version": None,
            "legacy_status": None,
        }
    if not isinstance(trace, dict):
        raise AIWorkflowPersistError("AWP-SCHEMA", "legacy trace must be an object")
    invented = trace.get("invent_prompt") or trace.get("invent_model") or trace.get("invent_run")
    if invented:
        raise AIWorkflowPersistError("AWP-INVENTED", "refusing to invent prompt, model, or run")
    prompt = trace.get("prompt")
    model = trace.get("modell") if "modell" in trace else trace.get("model")
    laeufe = trace.get("laeufe") or []
    status = trace.get("status")
    if prompt not in (None, "") and not isinstance(prompt, str):
        raise AIWorkflowPersistError("AWP-SCHEMA", "prompt must be string or null")
    if model not in (None, "") and not isinstance(model, str):
        raise AIWorkflowPersistError("AWP-SCHEMA", "model must be string or null")
    if laeufe and not isinstance(laeufe, list):
        raise AIWorkflowPersistError("AWP-SCHEMA", "laeufe must be an array")
    record_for_conf: Dict[str, Any] = {}
    if status == "legacy" or trace.get("legacy"):
        record_for_conf["legacy"] = True
    if "confidence" in trace:
        record_for_conf["confidence"] = trace["confidence"]
    conf = ps.adapt_legacy_confidence(record_for_conf or None)
    prompt_pin = (
        _absent_pin("prompt", "legacy-null")
        if prompt in (None, "")
        else {"present": True, "kind": "artifact", "uri": "artifact:prompt", "digest": digest_text(prompt)}
    )
    model_pin = (
        _absent_pin("model", "legacy-null")
        if model in (None, "")
        else {"present": True, "kind": "artifact", "uri": "artifact:model", "digest": digest_text(model)}
    )
    run_id = None
    if laeufe:
        # Real historic runs are listed; still do not mint a provenance run_id.
        run_id = None
    if trace.get("run_id") and not UUIDV7_RE.match(str(trace["run_id"])):
        raise AIWorkflowPersistError("AWP-FABRICATED", "legacy run_id is not a UUIDv7")
    if trace.get("run_id"):
        run_id = str(trace["run_id"])
    return {
        "adapter": ADAPTER,
        "confidence": conf["confidence"],
        "prompt": prompt_pin,
        "model": model_pin,
        "run_id": run_id,
        "policy_version": trace.get("policy_version"),
        "legacy_status": status,
        "fragment": trace.get("fragment"),
    }


class AIWorkflowPersist:
    def __init__(self, root: Path, *, file_bytes=None) -> None:
        self.root = Path(root)
        self.store = ps.ProvenanceStore(self.root, file_bytes=file_bytes)
        self.claims_dir = self.root / "provenance" / "claims"

    def claim_path(self, claim_id: str) -> Path:
        parsed = vid.parse_prefixed_id(claim_id)
        if parsed is None or parsed["prefix"] != "claim":
            raise AIWorkflowPersistError("AWP-SCHEMA", f"not a claim id: {claim_id}")
        return self.claims_dir / f"{parsed['uuid']}.json"

    def persist_run(
        self,
        *,
        run_id: str,
        started_at: str,
        ended_at: str,
        commit: str,
        issue: str,
        criterion: str,
        campaign: str,
        pins: Mapping[str, Any],
        outputs: Optional[list] = None,
        status: str = "succeeded",
        classification: str = "internal",
        environment: str = "development-test",
        producer: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not UUIDV7_RE.match(run_id):
            raise AIWorkflowPersistError("AWP-BARE-ID", "run_id must be UUIDv7")
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise AIWorkflowPersistError("AWP-BARE-ID", "commit must be a 40-hex SHA")
        pins_n = validate_pins(pins)
        inputs = [
            typed_ref("commit", commit),
            typed_ref("issue", issue),
            typed_ref("criterion", criterion),
            typed_ref("campaign", campaign),
        ]
        for key in GOVERNED_PINS:
            pin = pins_n[key]
            if pin.get("present") is False:
                continue
            inputs.append(pin)
        payload = {
            "schema_version": ps.SCHEMA_VERSION,
            "run_id": run_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "environment": environment,
            "classification": classification,
            "status": status,
            "producer": dict(producer) if producer else typed_ref("commit", commit),
            "inputs": inputs,
            "outputs": list(outputs or []),
        }
        created = self._put_bound("run", self.store.create_run, payload)
        envelope = {
            "schema": RUN_SCHEMA,
            "run_id": run_id,
            "pins": pins_n,
            "issue": f"issue:{issue}" if not issue.startswith("issue:") else issue,
            "criterion": f"criterion:{criterion}" if not criterion.startswith("criterion:") else criterion,
            "campaign": f"campaign:{campaign}" if not campaign.startswith("campaign:") else campaign,
            "path": created["path"],
            "status": created["status"],
        }
        return envelope

    def persist_claim(
        self,
        *,
        content: str,
        parent_artifact_id: str,
        pins: Mapping[str, Any],
        run_id: Optional[str],
        issue: str,
        criterion: str,
        campaign: str,
        evidence_refs: Optional[list] = None,
        claim_type: str = "ai_inferred",
        confidence: Any = None,
        claim_id: Optional[str] = None,
        supersedes_claim_ids: Optional[list] = None,
        classification: str = "internal",
        environment: str = "development-test",
        created: Optional[str] = None,
    ) -> Dict[str, Any]:
        pins_n = validate_pins(pins)
        if run_id is not None:
            if not UUIDV7_RE.match(run_id):
                raise AIWorkflowPersistError("AWP-BARE-ID", "run_id must be UUIDv7")
            if not self.store.run_path(run_id).is_file():
                raise AIWorkflowPersistError("AWP-FABRICATED", f"run {run_id} does not exist")
        if confidence in (ps.LEGACY_CONFIDENCE, ps.UNKNOWN_CONFIDENCE, None):
            numeric = 0.0
            conf_label = confidence or ps.UNKNOWN_CONFIDENCE
        else:
            numeric = float(confidence)
            conf_label = numeric
        claim = tc.new_claim(
            parent_artifact_id,
            claim_type,
            content,
            evidence_refs=evidence_refs,
            current_confidence=numeric,
            supersedes_claim_ids=supersedes_claim_ids,
        )
        if claim_id:
            if not CLAIM_ID_RE.match(claim_id):
                raise AIWorkflowPersistError("AWP-BARE-ID", f"invalid claim id {claim_id}")
            claim["claim_id"] = claim_id
        if created:
            claim["created"] = created
            claim["updated"] = created
        cause = "legacy-confidence@v1" if conf_label in (ps.LEGACY_CONFIDENCE, ps.UNKNOWN_CONFIDENCE) else "ai-run"
        tc.append_confidence(claim, numeric, cause, {"confidence": conf_label, "run_id": run_id})
        record = {
            "schema": SCHEMA,
            "claim": claim,
            "pins": pins_n,
            "run_id": run_id,
            "issue": issue if issue.startswith("issue:") else f"issue:{issue}",
            "criterion": criterion if criterion.startswith("criterion:") else f"criterion:{criterion}",
            "campaign": campaign if campaign.startswith("campaign:") else f"campaign:{campaign}",
            "confidence": conf_label,
            "classification": classification,
            "environment": environment,
        }
        path = self.claim_path(claim["claim_id"])
        self._exclusive_put(path, record)
        if run_id:
            run_rec = self.store.read_run(run_id)
            occurred = run_rec.get("ended_at") or run_rec["started_at"]
            self._link_claim_to_run(record, run_id, occurred)
        return record

    def read_claim(self, claim_id: str) -> Dict[str, Any]:
        path = self.claim_path(claim_id)
        if not path.is_file():
            raise AIWorkflowPersistError("AWP-MISSING", f"no claim at {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def trace_claim(self, claim_id: str) -> Dict[str, Any]:
        record = self.read_claim(claim_id)
        run = None
        if record.get("run_id"):
            run = self.store.read_run(record["run_id"])
        evidence = list(record["claim"].get("evidence_refs") or [])
        return {
            "claim_id": claim_id,
            "claim": record["claim"],
            "pins": record["pins"],
            "run": run,
            "evidence_refs": evidence,
            "issue": record["issue"],
            "criterion": record["criterion"],
            "campaign": record["campaign"],
        }

    def invalidate_for_pin_change(
        self,
        claim_id: str,
        live_pins: Mapping[str, Any],
        *,
        reason: Optional[str] = None,
        occurred_at: Optional[str] = None,
        invalidating_run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        record = self.read_claim(claim_id)
        changed = pins_changed(record["pins"], live_pins)
        if not changed:
            return {"status": "unchanged", "claim_id": claim_id, "changed": []}
        stamp = occurred_at or _now()
        why = reason or f"governed pin change: {','.join(changed)}"
        tc.mark_invalidated(record["claim"], why)
        record["claim"]["updated"] = stamp
        path = self.claim_path(claim_id)
        path.write_text(json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n", encoding="utf-8")
        if invalidating_run_id:
            self._write_invalidation_event(record, invalidating_run_id, stamp)
        return {"status": "invalidated", "claim_id": claim_id, "changed": changed, "record": record}

    def supersede_claim(
        self,
        old_claim_id: str,
        *,
        content: str,
        run_id: str,
        pins: Mapping[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        old = self.read_claim(old_claim_id)
        new = self.persist_claim(
            content=content,
            parent_artifact_id=old["claim"]["parent_artifact_id"],
            pins=pins,
            run_id=run_id,
            issue=kwargs.get("issue", old["issue"]),
            criterion=kwargs.get("criterion", old["criterion"]),
            campaign=kwargs.get("campaign", old["campaign"]),
            evidence_refs=kwargs.get("evidence_refs", old["claim"].get("evidence_refs")),
            claim_type=kwargs.get("claim_type", old["claim"]["claim_type"]),
            confidence=kwargs.get("confidence", 0.0),
            supersedes_claim_ids=[old_claim_id],
        )
        tc.link_supersession(old["claim"], new["claim"])
        old["claim"] = old["claim"]
        self.claim_path(old_claim_id).write_text(
            json.dumps(old, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        self.claim_path(new["claim"]["claim_id"]).write_text(
            json.dumps(new, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return new

    def persist_from_legacy_trace(
        self,
        trace: Mapping[str, Any],
        *,
        pins: Mapping[str, Any],
        issue: str,
        criterion: str,
        campaign: str,
        parent_artifact_id: str,
        content: str,
        commit: Optional[str] = None,
        run_id: Optional[str] = None,
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        adapted = adapt_legacy_trace(trace)
        merged = dict(pins)
        if adapted["prompt"].get("present") is False:
            merged["prompt"] = adapted["prompt"]
        if adapted["model"].get("present") is False:
            merged["model"] = adapted["model"]
        if commit is not None and run_id is None and adapted["run_id"] is None:
            raise AIWorkflowPersistError(
                "AWP-INVENTED",
                "refusing to mint a provenance run for a legacy trace",
            )
        if adapted["run_id"] is None and run_id is None:
            return self.persist_claim(
                content=content,
                parent_artifact_id=parent_artifact_id,
                pins=merged,
                run_id=None,
                issue=issue,
                criterion=criterion,
                campaign=campaign,
                confidence=adapted["confidence"],
            )
        if run_id is None:
            raise AIWorkflowPersistError("AWP-INVENTED", "refusing to mint a run for a legacy trace")
        if commit is None:
            raise AIWorkflowPersistError("AWP-PIN", "commit required to persist a real AI run")
        self.persist_run(
            run_id=run_id,
            started_at=started_at or _now(),
            ended_at=ended_at or _now(),
            commit=commit,
            issue=issue,
            criterion=criterion,
            campaign=campaign,
            pins=merged,
        )
        return self.persist_claim(
            content=content,
            parent_artifact_id=parent_artifact_id,
            pins=merged,
            run_id=run_id,
            issue=issue,
            criterion=criterion,
            campaign=campaign,
            confidence=adapted["confidence"] if adapted["confidence"] not in (ps.LEGACY_CONFIDENCE, ps.UNKNOWN_CONFIDENCE) else adapted["confidence"],
        )

    def list_claim_ids(self) -> list:
        if not self.claims_dir.is_dir():
            return []
        ids = []
        for path in sorted(self.claims_dir.glob("*.json")):
            ids.append(f"claim:{path.stem}")
        return ids

    def _link_claim_to_run(self, record: Mapping[str, Any], run_id: str, occurred_at: str) -> None:
        claim_id = record["claim"]["claim_id"]
        digest = digest_bytes(_canonical_bytes(record["claim"]))
        event_id = vid.uuid7()
        source = typed_ref("artifact", f"claim:{claim_id.split(':', 1)[1]}", digest=digest, require_digest=True)
        # artifact URI uses artifact:<rest>; keep claim uuid as identity in uri path.
        source["uri"] = f"artifact:{claim_id}"
        self._put_bound(
            "event",
            self.store.create_event,
            {
                "schema_version": ps.SCHEMA_VERSION,
                "event_id": event_id,
                "occurred_at": occurred_at,
                "relation": "produced-by",
                "source": source,
                "target": typed_ref("run", run_id),
                "environment": record.get("environment") or "development-test",
                "classification": record.get("classification") or "internal",
                "run": typed_ref("run", run_id),
            },
        )

    def _write_invalidation_event(self, record: Mapping[str, Any], run_id: str, occurred_at: str) -> None:
        claim_id = record["claim"]["claim_id"]
        digest = digest_bytes(_canonical_bytes(record["claim"]))
        source = typed_ref("artifact", claim_id, digest=digest, require_digest=True)
        source["uri"] = f"artifact:{claim_id}"
        self._put_bound(
            "event",
            self.store.create_event,
            {
                "schema_version": ps.SCHEMA_VERSION,
                "event_id": vid.uuid7(),
                "occurred_at": occurred_at,
                "relation": "invalidated-by",
                "source": source,
                "target": typed_ref("run", run_id),
                "environment": record.get("environment") or "development-test",
                "classification": record.get("classification") or "internal",
                "run": typed_ref("run", run_id),
            },
        )

    def persist_finding(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        return self._put_bound("finding", self.store.create_finding, payload)

    def persist_artifact_set(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        return self._put_bound("artifact-set", self.store.create_artifact_set, payload)

    def _put_bound(self, kind: str, create_fn, payload: Mapping[str, Any]) -> Dict[str, Any]:
        try:
            created = create_fn(payload)
        except ps.ProvenanceError as exc:
            raise AIWorkflowPersistError(exc.code, exc.message) from exc
        record = created["record"]
        validate_against_bound_schema(kind, record)
        _validate_nested_typed_refs(kind, record)
        return created

    def _exclusive_put(self, path: Path, record: Mapping[str, Any]) -> None:
        payload = _canonical_bytes(record) + b"\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            existing = path.read_bytes()
            if existing == payload:
                return
            raise AIWorkflowPersistError("AWP-COLLISION", f"claim file already exists: {path}")
        temporary_name = f".{path.name}.{secrets.token_hex(8)}.tmp"
        tmp_path = path.parent / temporary_name
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(str(tmp_path), flags, 0o600)
        try:
            os.write(fd, payload)
            os.fsync(fd)
            os.fchmod(fd, stat.S_IMODE(0o644))
        finally:
            os.close(fd)
        os.link(str(tmp_path), str(path))
        os.unlink(str(tmp_path))
