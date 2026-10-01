#!/usr/bin/env python3
"""Common provenance for i18n segment/title/diagram registers (Task `0037-27.04`).

Human-authored translation registers remain authoritative build inputs. This
adapter records translation-run envelopes and shared provenance objects; it
does not rewrite register prose into generated HTML or SVG.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_TOOLS = Path(__file__).resolve().parent
_SRC = _TOOLS.parent
_ROOT = _SRC.parent
sys.path.insert(0, str(_SRC))
sys.path.insert(0, str(_TOOLS))

from i18n_translate import issue_protected_tokens, pruefe  # noqa: E402

_PS_SPEC = importlib.util.spec_from_file_location("provenance_store", _TOOLS / "provenance_store.py")
assert _PS_SPEC and _PS_SPEC.loader
ps = importlib.util.module_from_spec(_PS_SPEC)
_PS_SPEC.loader.exec_module(ps)

SCHEMA = "i18n-translation-run@v1"
FAMILIES = frozenset({"segment", "title", "diagram"})
MERGE_DECISIONS = frozenset({"accepted", "rejected", "stale", "missing", "fallback"})
WORK_STATES = frozenset({"current", "stale", "missing", "fallback"})
# Bind writers to 0037-17/19 schema files; do not fork local copies.
REPO_SCHEMA_DIR = _ROOT / "provenance" / "_schema"
BOUND_SCHEMAS = {
    "typed-reference": "typed-reference-v1.schema.json",
    "run": "run-v1.schema.json",
    "finding": "finding-v1.schema.json",
    "artifact-set": "artifact-set-v1.schema.json",
    "event": "provenance-event-v1.schema.json",
}


class I18nProvenanceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_bound_schema(kind: str, schema_dir: Optional[Path] = None) -> Dict[str, Any]:
    directory = Path(schema_dir) if schema_dir else REPO_SCHEMA_DIR
    name = BOUND_SCHEMAS[kind]
    path = directory / name
    if not path.is_file():
        raise I18nProvenanceError(
            "I18N-SCHEMA-MISSING", f"required schema {name} absent at {path}"
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
        raise I18nProvenanceError(
            "I18N-SCHEMA-DEVIATION",
            f"{kind} fields {sorted(extra)} are not in {BOUND_SCHEMAS[kind]} (finding, not a local fork)",
        )
    for key in schema.get("required") or []:
        if key not in record:
            raise I18nProvenanceError(
                "I18N-SCHEMA-DEVIATION",
                f"{kind} missing required {key} from {BOUND_SCHEMAS[kind]}",
            )


def _put_event(store: Any, payload: Mapping[str, Any]) -> Dict[str, Any]:
    result = store.create_event(payload)
    validate_against_bound_schema("event", result["record"])
    return result


def protected_tokens(family: str, source_text: str, translation: str) -> List[str]:
    if family == "title":
        return issue_protected_tokens(source_text)
    if family in {"segment", "diagram"}:
        mismatch = pruefe(source_text, translation)
        if mismatch:
            raise I18nProvenanceError("I18N-PROTECTED", mismatch)
        return sorted(set(issue_protected_tokens(source_text)))
    raise I18nProvenanceError("I18N-FAMILY", f"unknown family {family}")


def validate_entry(entry: Mapping[str, Any]) -> Dict[str, Any]:
    record = dict(entry)
    family = record.get("family")
    if family not in FAMILIES:
        raise I18nProvenanceError("I18N-FAMILY", f"unknown family {family}")
    for key in ("source_id", "source_text", "source_locale", "target_locale", "translation"):
        if not isinstance(record.get(key), str) or not record[key]:
            if key == "translation" and record.get("merge_decision") in {"missing", "stale"}:
                record["translation"] = record.get("translation") or ""
            else:
                raise I18nProvenanceError("I18N-SCHEMA", f"missing {key}")
    source_hash = sha256_text(record["source_text"])
    declared = record.get("source_hash")
    if declared and declared != source_hash:
        raise I18nProvenanceError("I18N-SOURCE-HASH", "source hash does not match source text")
    record["source_hash"] = source_hash
    decision = record.get("merge_decision", "accepted")
    if decision not in MERGE_DECISIONS:
        raise I18nProvenanceError("I18N-DECISION", f"unknown merge decision {decision}")
    record["merge_decision"] = decision
    fallback = bool(record.get("fallback", decision == "fallback"))
    record["fallback"] = fallback
    translation = record.get("translation") or ""
    if decision == "accepted" and not fallback:
        if family == "title":
            expected = issue_protected_tokens(record["source_text"])
            observed = issue_protected_tokens(translation)
            if expected != observed:
                raise I18nProvenanceError("I18N-PROTECTED", "protected-token mismatch")
            record["protected_tokens"] = expected
        else:
            record["protected_tokens"] = protected_tokens(family, record["source_text"], translation)
    else:
        record["protected_tokens"] = list(record.get("protected_tokens") or issue_protected_tokens(record["source_text"]))
    record["output_digest"] = sha256_text(translation) if translation else None
    return record


def inspect_language_work(
    *,
    family: str,
    source_locale: str,
    target_locale: str,
    source_items: Mapping[str, str],
    target_items: Mapping[str, str],
    recorded: Optional[Mapping[str, Mapping[str, Any]]] = None,
    required_locales: Optional[Sequence[str]] = None,
    present_locales: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Report current/stale/missing/fallback work without mutating registers."""
    if family not in FAMILIES:
        raise I18nProvenanceError("I18N-FAMILY", f"unknown family {family}")
    recorded = recorded or {}
    missing: List[str] = []
    stale: List[str] = []
    fallback: List[str] = []
    current: List[str] = []
    for source_id, source_text in source_items.items():
        source_hash = sha256_text(source_text)
        if source_id not in target_items:
            missing.append(source_id)
            continue
        envelope = recorded.get(source_id) or {}
        recorded_hash = envelope.get("source_hash")
        if (
            envelope.get("status") == "stale"
            or envelope.get("expected_source_title_hash")
            or (recorded_hash and recorded_hash != source_hash)
        ):
            stale.append(source_id)
            continue
        translation = target_items[source_id]
        if envelope.get("fallback") or translation == source_text:
            fallback.append(source_id)
            continue
        current.append(source_id)
    absent_locales = []
    if required_locales is not None:
        present = set(present_locales or [target_locale])
        absent_locales = sorted(set(required_locales) - present)
    return {
        "schema": "i18n-language-work@v1",
        "family": family,
        "source_locale": source_locale,
        "target_locale": target_locale,
        "counts": {
            "source": len(source_items),
            "current": len(current),
            "stale": len(stale),
            "missing": len(missing),
            "fallback": len(fallback),
        },
        "stale": sorted(stale),
        "missing": sorted(missing),
        "fallback": sorted(fallback),
        "current": sorted(current),
        "absent_locales": absent_locales,
        "complete": not missing and not stale and not absent_locales,
    }


def _ref(kind: str, ident: str, **extra: Any) -> Dict[str, Any]:
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}",
        "classification": extra.pop("classification", "internal"),
    }
    value.update(extra)
    return value


def record_translation_run(
    store: ps.ProvenanceStore,
    *,
    run_id: str,
    set_id: str,
    event_ids: Mapping[str, str],
    started_at: str,
    ended_at: str,
    commit: str,
    issue: str,
    criterion: str,
    producer_path: str,
    family: str,
    target_locale: str,
    translator: Mapping[str, Any],
    model: Mapping[str, Any],
    policy: Mapping[str, Any],
    config: Mapping[str, Any],
    entries: Sequence[Mapping[str, Any]],
    register_path: str,
    environment: str = "development-test",
) -> Dict[str, Any]:
    validated = [validate_entry(entry) for entry in entries]
    for entry in validated:
        if entry["family"] != family:
            raise I18nProvenanceError("I18N-FAMILY", "mixed families in one translation run")
        if entry["target_locale"] != target_locale:
            raise I18nProvenanceError("I18N-LOCALE", "mixed target locales in one translation run")
    envelope = {
        "schema": SCHEMA,
        "run_id": run_id,
        "family": family,
        "target_locale": target_locale,
        "translator": dict(translator),
        "model": dict(model),
        "policy": dict(policy),
        "config": dict(config),
        "issue": issue,
        "criterion": criterion,
        "entries": validated,
        "register_path": register_path,
        "output_digest": sha256_text(json.dumps(validated, sort_keys=True, separators=(",", ":"))),
    }
    rel_path = f"provenance/i18n/runs/{run_id}.json"
    payload = json.dumps(envelope, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    dest = store.root / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(payload, encoding="utf-8")
    digest = ps.sha256_bytes(payload.encode("utf-8"))
    files = {rel_path: payload.encode("utf-8")}
    bound = ps.ProvenanceStore(store.root, file_bytes=files.__getitem__)

    run_payload = {
        "schema_version": "1.0",
        "run_id": run_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "environment": environment,
        "classification": "internal",
        "status": "succeeded",
        "producer": _ref("commit", commit),
        "inputs": [
            _ref("commit", commit),
            _ref("issue", issue),
            _ref("criterion", criterion),
            _ref("artifact", f"{register_path}@sha256:{digest.split(':', 1)[1]}", digest=digest),
        ],
        "outputs": [],
    }
    run = bound.create_run(run_payload)
    validate_against_bound_schema("run", bound.read_run(run_id))
    validate_against_bound_schema("typed-reference", run_payload["producer"])
    artifact_set = bound.create_artifact_set(
        {
            "schema_version": "1.0",
            "set_id": set_id,
            "created_at": ended_at,
            "classification": "internal",
            "environment": environment,
            "producer": _ref("run", run_id),
            "members": [
                {
                    "path": rel_path,
                    "digest": digest,
                    "size_bytes": len(payload.encode("utf-8")),
                    "media_type": "application/json",
                    "source_commit": commit,
                }
            ],
        }
    )
    validate_against_bound_schema("artifact-set", artifact_set["record"])
    set_digest = artifact_set["record"]["set_digest"]
    produced = _put_event(
        bound,
        {
            "schema_version": "1.0",
            "event_id": event_ids["produced-by"],
            "occurred_at": ended_at,
            "relation": "produced-by",
            "source": _ref("artifact-set", set_id, digest=set_digest),
            "target": _ref("run", run_id),
            "environment": environment,
            "classification": "internal",
            "run": _ref("run", run_id),
        },
    )
    derived = _put_event(
        bound,
        {
            "schema_version": "1.0",
            "event_id": event_ids["derived-from"],
            "occurred_at": ended_at,
            "relation": "derived-from",
            "source": _ref("artifact", f"{rel_path}@{digest}"),
            "target": _ref("artifact", f"{register_path}@{digest}"),
            "environment": environment,
            "classification": "internal",
            "run": _ref("run", run_id),
        },
    )
    invalidation = None
    stale_ids = [entry["source_id"] for entry in validated if entry["merge_decision"] == "stale"]
    if stale_ids:
        invalidation = _put_event(
            bound,
            {
                "schema_version": "1.0",
                "event_id": event_ids["invalidated-by"],
                "occurred_at": ended_at,
                "relation": "invalidated-by",
                "source": _ref("artifact", f"{rel_path}@{digest}"),
                "target": _ref("run", run_id),
                "environment": environment,
                "classification": "internal",
                "run": _ref("run", run_id),
            },
        )
    return {
        "envelope": envelope,
        "run": run,
        "artifact_set": artifact_set,
        "events": {"produced-by": produced, "derived-from": derived, "invalidated-by": invalidation},
        "path": rel_path,
        "digest": digest,
    }


def trace_to_run(envelope: Mapping[str, Any], source_id: str) -> Dict[str, Any]:
    for entry in envelope.get("entries") or []:
        if entry.get("source_id") == source_id:
            return {
                "source_id": source_id,
                "source_hash": entry["source_hash"],
                "source_locale": entry["source_locale"],
                "target_locale": entry["target_locale"],
                "run_id": envelope["run_id"],
                "family": envelope["family"],
                "translator": envelope["translator"],
                "model": envelope["model"],
                "policy": envelope["policy"],
                "config": envelope["config"],
                "merge_decision": entry["merge_decision"],
                "output_digest": entry["output_digest"],
                "fallback": entry["fallback"],
                "protected_tokens": entry["protected_tokens"],
            }
    raise I18nProvenanceError("I18N-TRACE", f"no envelope entry for {source_id}")


def load_segment_items(path: Path) -> Dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise I18nProvenanceError("I18N-REGISTER", f"invalid segment register {path}")
    items = {}
    for key, value in data.items():
        if isinstance(value, dict) and "m" in value:
            items[key] = value["m"]
        elif isinstance(value, str):
            items[key] = value
        else:
            raise I18nProvenanceError("I18N-REGISTER", f"invalid segment {key}")
    return items


def load_label_items(path: Path) -> Dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise I18nProvenanceError("I18N-REGISTER", f"invalid label register {path}")
    items = {}
    for key, value in data.items():
        if isinstance(value, int):
            items[key] = key
        elif isinstance(value, str):
            items[key] = value
        else:
            raise I18nProvenanceError("I18N-REGISTER", f"invalid label {key}")
    return items


def load_title_items(path: Path) -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items: Dict[str, str] = {}
    recorded: Dict[str, Dict[str, Any]] = {}
    for record in data.get("records") or []:
        item_id = record["item_id"]
        items[item_id] = record.get("translation") or ""
        recorded[item_id] = {
            "source_hash": record.get("source_title_hash"),
            "fallback": record.get("status") in {"pending", "canonical"} and record.get("source_locale") != data.get("language"),
            "status": record.get("status"),
            "expected_source_title_hash": record.get("expected_source_title_hash"),
        }
        if record.get("status") == "stale":
            recorded[item_id]["source_hash"] = record.get("expected_source_title_hash") or ""
    return items, recorded
