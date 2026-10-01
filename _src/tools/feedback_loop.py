#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Closed feedback loop for AI commentaries (Feature 0045 / 0046).

Detects an accepted feedback item, an accepted curator decision, or a
specification-record byte change; marks only the AI commentaries that cite
that record as stale; regenerates those fragments with an append-only
provenance trace; merges i18n segments for the fragment; rebuilds the
affected pages; and appends a hashed ledger line.

CLI:
    python3 _src/tools/feedback_loop.py run --feedback-id ID
    python3 _src/tools/feedback_loop.py run --record-id ID
    python3 _src/tools/feedback_loop.py run --all-pending

Spec records under ``spec/records/`` are read-only. ``i18n_extract.py``
rewrites the global German register from the whole corpus, so this loop
does not call ``i18n_extract.main``. It uses the same segment identity
(``lib_i18n.maskiere`` / ``seg_id`` / ``leaf_segmente``) and merges only
the regenerated fragment's keys. Existing dictionary entries are kept.

Trace status uses the ``ai_workflow.py`` vocabulary ``veraltet`` and, on
top of that, ``stale`` / ``lifecycle=invalidated`` so a later regeneration
can return the fragment to ``aktuell`` without dropping the invalidation
history.

Classic (``CP_*``) and Eclipse S-Core (``SCORE_*``) components are edges in
``causal_dependency_graph``: the component id points at its AI commentary
under ``content/ai/classic`` or ``content/ai/score`` and at the published
page under ``classic/`` or ``score/``. Feedback for that id marks the
commentary stale and, unless regeneration is disabled, rewrites it.
Spec records stay read-only. A missing commentary file is not created.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

LEDGER_SCHEMA = "feedback-loop-ledger@v1"
TRACE_SCHEMA = "ai-trace@v1"
FEEDBACK_SCHEMA = "ai-commentary-feedback@v1"
BUILTIN_MODEL = "feedback-loop-contextual-synthesis"
ACCEPTED_MARKS = frozenset({"accepted", "applied"})
TRIGGER_KINDS = ("curator-decision", "user-feedback", "spec-update")
KIND_RANK = {name: index for index, name in enumerate(TRIGGER_KINDS)}
LEDGER_NAME = "feedback-loop-ledger.jsonl"
_RECORD_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/+@#-]{0,199}$")
_SIMPLE_RECORD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_CITE_RE = re.compile(r"\[([A-Za-z0-9_.:/+@#-]+)\]")

# Mock segments are deliberately not German, so a foreign tree that has the
# key does not render the canonical German sentence.
_MOCK_TRANSLATION = {
    "en": "Regenerated commentary",
    "es": "Comentario regenerado",
    "pt": "Comentario regenerado",
    "fr": "Commentaire regenere",
    "ru": "Обновлённое пояснение",
    "ar": "شرح معاد توليده",
    "hi": "पुनर्जनित व्याख्या",
    "ko": "재생성된 설명",
    "zh": "重新生成的说明",
    "nl": "Opnieuw gegenereerde toelichting",
}
_DEFAULT_LANGS = ("en", "es")


class FeedbackLoopError(Exception):
    """Input the loop refuses before it writes anything."""

    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.message = message
        self.code = code


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def _stamp(moment: datetime.datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=datetime.timezone.utc)
    return moment.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def receipt_hash(event: Mapping[str, Any]) -> str:
    """sha256 over the event object with ``receipt_hash`` removed.

    The digest uses canonical JSON (sorted keys, compact separators, UTF-8).
    """
    body = {key: value for key, value in event.items() if key != "receipt_hash"}
    payload = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + _sha256_bytes(payload.encode("utf-8"))


def seal_event(event: Dict[str, Any]) -> Dict[str, Any]:
    event = dict(event)
    event.pop("receipt_hash", None)
    event["receipt_hash"] = receipt_hash(event)
    return event


def validate_record_id(record_id: str) -> str:
    if not isinstance(record_id, str):
        raise FeedbackLoopError("record id must be a string")
    record_id = record_id.strip()
    if not record_id or not _RECORD_ID_RE.match(record_id):
        raise FeedbackLoopError("invalid record id: %r" % (record_id,))
    if ".." in record_id.split("/"):
        raise FeedbackLoopError("invalid record id: %r" % (record_id,))
    return record_id


# record id, commentary filename, published page filename or None, spec filename.
# CP_NVRAM is the graph component; the extracted record file is CP_MEM.json.
_CLASSIC_CAUSAL = (
    ("CP_RTE", "rec_CP_RTE_01.html", "rte.html", "CP_RTE.json"),
    ("CP_OS", "rec_CP_OS_01.html", "os.html", "CP_OS.json"),
    ("CP_COM", "rec_CP_COM_01.html", "com.html", "CP_COM.json"),
    ("CP_CAN", "rec_CP_CAN_01.html", "can.html", "CP_CAN.json"),
    ("CP_ETH", "rec_CP_ETH_01.html", "ethernet.html", "CP_ETH.json"),
    ("CP_NVRAM", "rec_CP_NVRAM_01.html", "memory.html", "CP_MEM.json"),
    ("CP_MEM", "rec_CP_NVRAM_01.html", "memory.html", "CP_MEM.json"),
    ("CP_CRYPTO", "rec_CP_CRYPTO_01.html", "crypto.html", "CP_CRYPTO.json"),
    ("CP_DIAG", "rec_CP_DIAG_01.html", "diagnostics.html", "CP_DIAG.json"),
    ("CP_SYS", "rec_CP_SYS_01.html", "system.html", "CP_SYS.json"),
    ("CP_MCAL", "rec_CP_MCAL_01.html", "mcal.html", "CP_MCAL.json"),
)
_SCORE_CAUSAL = (
    ("SCORE_CORE", "rec_SCORE_CORE_01.html", "core.html", "SCORE_CORE.json"),
    ("SCORE_COM", "rec_SCORE_COM_01.html", "communication.html", "SCORE_COM.json"),
    ("SCORE_DIAG", "rec_SCORE_DIAG_01.html", "diagnostic_adapter.html", "SCORE_DIAG.json"),
    ("SCORE_MEM", "rec_SCORE_MEM_01.html", "memory.html", "SCORE_MEM.json"),
    ("SCORE_CRYPTO", "rec_SCORE_CRYPTO_01.html", "crypto.html", "SCORE_CRYPTO.json"),
    ("SCORE_SAFETY", "rec_SCORE_SAFETY_01.html", None, "SCORE_SAFETY.json"),
    ("SCORE_PROCESS", "rec_SCORE_PROCESS_01.html", "process.html", "SCORE_PROCESS.json"),
)


def causal_dependency_graph() -> Dict[str, dict]:
    """Component id → AI commentary under ``_src`` and published page.

    The commentary path is relative to ``_src`` (``content/ai/...``).
    ``ai_src`` is the same path from the repository root. ``page`` is the
    published HTML file. ``SCORE_SAFETY`` has a commentary and no dedicated
    published page in the score tree, so ``page`` is None and no page rebuild
    is scheduled for it.
    """
    graph: Dict[str, dict] = {}
    rows = (
        ("classic", _CLASSIC_CAUSAL, "spec/records/classic"),
        ("score", _SCORE_CAUSAL, "spec/records/score"),
    )
    for universe, table, record_dir in rows:
        for record_id, fragment_name, page_name, record_file in table:
            fragment = "content/ai/%s/%s" % (universe, fragment_name)
            page = ("%s/%s" % (universe, page_name)) if page_name else None
            graph[record_id] = {
                "record_id": record_id,
                "universe": universe,
                "ai_fragment": fragment,
                "ai_fragments": [fragment],
                "ai_src": "_src/" + fragment,
                "page": page,
                "record_path": "%s/%s" % (record_dir, record_file),
            }
    return graph


def record_filename(record_id: str) -> Optional[str]:
    """Id → ``spec/records/<group>/<ID>.json``. Other ids have no single file.

    Adaptive ids keep the ``SWS_CM`` / ``SWS_CORE`` grouping. Classic ids live
    in ``spec/records/classic/`` and S-Core ids in ``spec/records/score/``.
    """
    if not _SIMPLE_RECORD_RE.match(record_id):
        return None
    if record_id.startswith("CP_"):
        return "spec/records/classic/%s.json" % record_id
    if record_id.startswith("SCORE_"):
        return "spec/records/score/%s.json" % record_id
    parts = record_id.split("_")
    group = "_".join(parts[:2]) if len(parts) >= 3 else "_SONSTIGE"
    return "spec/records/%s/%s.json" % (group, record_id)


def _contains_id(text: str, record_id: str) -> bool:
    """True when ``record_id`` occurs as its own token, not inside a longer id.

    Continuation characters are the ones a record id itself may contain, so
    ``SWS_CM_00701`` does not match ``SWS_CM_007010`` or ``SWS_CM_00701_04``,
    and a dotted S-Core id does not match that id plus a further segment.
    """
    if not text or not record_id:
        return False
    edge = r"[A-Za-z0-9_.:/+@#-]"
    pattern = r"(?<!" + edge + r")" + re.escape(record_id) + r"(?!" + edge + r")"
    return re.search(pattern, text) is not None


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _esc_attr(text: str) -> str:
    return _esc(text).replace('"', "&quot;")


def _strip_tags(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", text).strip()


def _record_bits(record: Optional[Mapping[str, Any]]) -> Tuple[str, str]:
    label, desc = "", ""
    if not isinstance(record, Mapping):
        return label, desc
    for block in record.get("blocks") or []:
        if not isinstance(block, Mapping):
            continue
        html = block.get("html") or ""
        if not isinstance(html, str):
            continue
        if "recname" in html and not label:
            label = _strip_tags(html)[:180]
        elif 'class="desc"' in html and not desc:
            desc = _strip_tags(html)[:500]
    return label, desc


def _safe_fragment(rel: str) -> Optional[str]:
    if not isinstance(rel, str) or not rel:
        return None
    rel = rel.replace("\\", "/").lstrip("/")
    parts = Path(rel).parts
    if ".." in parts:
        return None
    if not rel.startswith("content/ai/") or not rel.endswith(".html"):
        return None
    return rel


def _fragment_from_trace_path(src: Path, trace_path: Path) -> Optional[str]:
    try:
        rel = trace_path.resolve().relative_to((src / "ai" / "traces").resolve())
    except ValueError:
        return None
    if rel.suffix != ".json":
        return None
    return _safe_fragment("content/ai/" + str(rel.with_suffix(".html")).replace("\\", "/"))


def _load_json(path: Path) -> Tuple[Optional[Any], Optional[str]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, str(exc)
    try:
        return json.loads(raw.decode("utf-8")), None
    except (UnicodeError, json.JSONDecodeError) as exc:
        return None, str(exc)


def _dump_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=1) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def trace_schema_errors(trace: Mapping[str, Any], record_id: str) -> List[str]:
    """Problems in a trace written by a successful regeneration. Empty means valid."""
    errors: List[str] = []
    if not isinstance(trace, Mapping):
        return ["trace is not an object"]
    if trace.get("trace_schema") != TRACE_SCHEMA:
        errors.append("trace_schema")
    if not isinstance(trace.get("fragment"), str) or not trace.get("fragment"):
        errors.append("fragment")
    if trace.get("status") != "aktuell":
        errors.append("status")
    if trace.get("stale") is not False:
        errors.append("stale")
    if trace.get("lifecycle") != "current":
        errors.append("lifecycle")
    prompt = trace.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip() or record_id not in prompt:
        errors.append("prompt")
    modell = trace.get("modell")
    if not isinstance(modell, str) or not modell.strip():
        errors.append("modell")
    meta = trace.get("modell_meta")
    if not isinstance(meta, Mapping) or not meta.get("id") or not meta.get("synthesis"):
        errors.append("modell_meta")
    if "policy_version" not in trace:
        errors.append("policy_version")
    for key in ("elemente", "zitate", "quellen", "wissen", "annahmen", "laeufe", "invalidierungen"):
        if not isinstance(trace.get(key), list):
            errors.append(key)
    if isinstance(trace.get("elemente"), list) and record_id not in trace["elemente"]:
        errors.append("elemente missing record")
    if not isinstance(trace.get("diagramme"), dict):
        errors.append("diagramme")
    stand = trace.get("elemente_stand")
    if not isinstance(stand, dict) or record_id not in stand:
        errors.append("elemente_stand")
    trigger = trace.get("trigger")
    if not isinstance(trigger, Mapping) or trigger.get("record_id") != record_id:
        errors.append("trigger")
    elif not isinstance(trigger.get("timestamp"), str) or not trigger.get("kind"):
        errors.append("trigger fields")
    laeufe = trace.get("laeufe") or []
    if not laeufe or not isinstance(laeufe[-1], Mapping):
        errors.append("laeufe")
    else:
        last = laeufe[-1]
        for key in ("datum", "timestamp", "modell", "transkript", "trigger"):
            if key not in last:
                errors.append("lauf.%s" % key)
    history = trace.get("invalidierungen") or []
    if not history or not isinstance(history[-1], Mapping) or history[-1].get("state") != "invalidated":
        errors.append("invalidierungen")
    return errors


def invalidation_schema_errors(trace: Mapping[str, Any], record_id: str) -> List[str]:
    errors: List[str] = []
    if trace.get("status") != "veraltet":
        errors.append("status")
    if trace.get("stale") is not True:
        errors.append("stale")
    if trace.get("lifecycle") != "invalidated":
        errors.append("lifecycle")
    mark = trace.get("invalidiert")
    if not isinstance(mark, Mapping):
        errors.append("invalidiert")
    else:
        if mark.get("state") != "invalidated":
            errors.append("invalidiert.state")
        if mark.get("record_id") != record_id:
            errors.append("invalidiert.record_id")
    return errors


class FeedbackLoop:
    """One closed-loop run against a single ``_src`` tree."""

    def __init__(
        self,
        src: os.PathLike,
        *,
        now: Optional[Callable[[], datetime.datetime]] = None,
        generate_fn: Optional[Callable[[str], None]] = None,
        invoke_generate: bool = False,
    ):
        self.src = Path(src)
        self.now = now or _utc_now
        self.generate_fn = generate_fn
        self.invoke_generate = invoke_generate
        self.repo_root = self.src.parent
        self.dependency_graph = causal_dependency_graph()

    # ----------------------------------------------------------------- paths

    @property
    def ledger_path(self) -> Path:
        return self.src / "output" / LEDGER_NAME

    def record_path(self, record_id: str) -> Optional[Path]:
        rel = record_filename(record_id)
        primary = None
        if rel is not None:
            candidate = self.src / rel
            if _inside(self.src, candidate):
                primary = candidate
        if primary is not None and primary.is_file():
            return primary
        # CP_NVRAM is stored as CP_MEM.json. Use that file when it exists,
        # and keep the id-derived path when nothing is on disk so the loop
        # does not invent a spec record.
        node = self.dependency_graph.get(record_id)
        alt_rel = node.get("record_path") if isinstance(node, dict) else None
        if isinstance(alt_rel, str) and alt_rel:
            alt = self.src / alt_rel
            if _inside(self.src, alt) and alt.is_file():
                return alt
        return primary

    def record_bytes(self, record_id: str) -> Optional[bytes]:
        path = self.record_path(record_id)
        if path is None or not path.is_file():
            return None
        return path.read_bytes()

    def record_sha1(self, record_id: str) -> Optional[str]:
        data = self.record_bytes(record_id)
        if data is None:
            return None
        return _sha1_bytes(data)

    def load_record(self, record_id: str) -> Optional[dict]:
        path = self.record_path(record_id)
        if path is None or not path.is_file():
            return None
        data, err = _load_json(path)
        if err or not isinstance(data, dict):
            return None
        return data

    def _moment(self) -> datetime.datetime:
        moment = self.now()
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=datetime.timezone.utc)
        return moment.astimezone(datetime.timezone.utc).replace(microsecond=0)

    def _policy(self) -> Tuple[Any, Optional[str], Optional[str]]:
        path = self.src / "ai" / "policy.json"
        if not path.is_file():
            return None, BUILTIN_MODEL, None
        data, err = _load_json(path)
        if err or not isinstance(data, dict):
            return None, BUILTIN_MODEL, err or "policy is not an object"
        version = data.get("version")
        model = None
        modell = data.get("modell")
        if isinstance(modell, dict):
            model = modell.get("erklaerungen")
        if not isinstance(model, str) or not model.strip():
            model = BUILTIN_MODEL
        return version, model, None

    def languages(self) -> List[str]:
        path = self.src / "site.json"
        if path.is_file():
            data, err = _load_json(path)
            if not err and isinstance(data, dict):
                ziele = (data.get("sprachen") or {}).get("ziele")
                if isinstance(ziele, list) and all(isinstance(item, str) and item for item in ziele):
                    return list(ziele)
        return list(_DEFAULT_LANGS)

    # --------------------------------------------------------------- triggers

    def _feedback_dirs(self) -> Iterable[Path]:
        for rel in ("spec/feedback-inbox", "spec/curation-queue"):
            directory = self.src / rel
            if directory.is_dir():
                yield directory

    def _iter_feedback_docs(self) -> Iterable[Tuple[Path, dict]]:
        for directory in self._feedback_dirs():
            for path in sorted(directory.rglob("*.json")):
                if not path.is_file() or not _inside(self.src, path):
                    continue
                data, err = _load_json(path)
                if err or not isinstance(data, dict):
                    continue
                yield path, data

    def _accepted(self, doc: Mapping[str, Any]) -> bool:
        decision = doc.get("decision") if isinstance(doc.get("decision"), dict) else {}
        markers = [
            value
            for value in (doc.get("status"), doc.get("outcome"), decision.get("outcome"))
            if isinstance(value, str) and value.strip()
        ]
        if not markers or any(mark not in ACCEPTED_MARKS for mark in markers):
            return False
        kind = doc.get("kind")
        role = decision.get("actor_role") or doc.get("actor_role")
        if kind == "curator-decision" or decision.get("outcome"):
            if role is not None and role != "curator":
                return False
        return True

    def _doc_record_id(self, doc: Mapping[str, Any], path: Path) -> Optional[str]:
        for key in ("record_id", "record"):
            value = doc.get(key)
            if isinstance(value, str) and value.strip():
                try:
                    return validate_record_id(value)
                except FeedbackLoopError:
                    return None
        basis = doc.get("decision_basis") if isinstance(doc.get("decision_basis"), dict) else {}
        for key in ("record_id", "id"):
            value = basis.get(key)
            if isinstance(value, str) and value.strip():
                try:
                    return validate_record_id(value)
                except FeedbackLoopError:
                    return None
        for key in ("id", "canonical_id"):
            value = doc.get(key)
            if isinstance(value, str) and value.strip():
                try:
                    return validate_record_id(value)
                except FeedbackLoopError:
                    continue
        try:
            return validate_record_id(path.stem)
        except FeedbackLoopError:
            return None

    def _doc_feedback_id(self, doc: Mapping[str, Any], path: Path) -> str:
        for key in ("feedback_id", "id"):
            value = doc.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return path.stem

    def _doc_kind(self, doc: Mapping[str, Any]) -> str:
        kind = doc.get("kind")
        if kind in TRIGGER_KINDS and kind != "spec-update":
            return str(kind)
        if kind == "spec-update":
            return "spec-update"
        decision = doc.get("decision") if isinstance(doc.get("decision"), dict) else {}
        if decision.get("outcome") or doc.get("actor_role") == "curator" or doc.get("outcome") in ACCEPTED_MARKS:
            return "curator-decision"
        return "user-feedback"

    def _trigger_from_doc(self, path: Path, doc: Mapping[str, Any]) -> Optional[dict]:
        if not self._accepted(doc):
            return None
        record_id = self._doc_record_id(doc, path)
        if not record_id:
            return None
        return {
            "kind": self._doc_kind(doc),
            "feedback_id": self._doc_feedback_id(doc, path),
            "record_id": record_id,
            "record_sha1": self.record_sha1(record_id),
            "source": str(path.relative_to(self.src)).replace("\\", "/"),
        }

    def find_feedback(self, feedback_id: str) -> List[Tuple[Path, dict]]:
        matches = []
        for path, doc in self._iter_feedback_docs():
            if self._doc_feedback_id(doc, path) == feedback_id or path.stem == feedback_id:
                matches.append((path, doc))
        return matches

    def _drift_acknowledged(self, trace: Mapping[str, Any], record_id: str, current: str) -> bool:
        marks = []
        if isinstance(trace.get("invalidiert"), dict):
            marks.append(trace["invalidiert"])
        history = trace.get("invalidierungen")
        if isinstance(history, list):
            marks.extend(item for item in history if isinstance(item, dict))
        return any(
            mark.get("record_id") == record_id and mark.get("record_sha1") == current
            for mark in marks
        )

    def changed_record_ids(self) -> List[str]:
        """Records whose stored ``elemente_stand`` no longer matches the file bytes.

        A missing record file is not a change: deleting or hiding the file must
        not invalidate every commentary that still names it.
        """
        changed = set()
        traces = self.src / "ai" / "traces"
        if not traces.is_dir():
            return []
        for path in sorted(traces.rglob("*.json")):
            data, err = _load_json(path)
            if err or not isinstance(data, dict):
                continue
            stand = data.get("elemente_stand")
            if not isinstance(stand, dict):
                continue
            for record_id, stored in stand.items():
                if not isinstance(record_id, str) or not isinstance(stored, str) or not stored:
                    continue
                try:
                    record_id = validate_record_id(record_id)
                except FeedbackLoopError:
                    continue
                current = self.record_sha1(record_id)
                if current is None or current == stored:
                    continue
                # Already flagged against these exact bytes. Do not invalidate
                # again; a further edit produces a different hash and reopens it.
                if self._drift_acknowledged(data, record_id, current):
                    continue
                changed.add(record_id)
        return sorted(changed)

    def _ledger_events(self) -> List[dict]:
        path = self.ledger_path
        if not path.is_file():
            return []
        events = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                events.append(item)
        return events

    def _done(self, trigger: Mapping[str, Any]) -> bool:
        for event in self._ledger_events():
            if event.get("noop") or not event.get("complete"):
                continue
            if event.get("record_id") != trigger.get("record_id"):
                continue
            if event.get("record_sha1") != trigger.get("record_sha1"):
                continue
            if event.get("trigger_kind") != trigger.get("kind"):
                continue
            if (event.get("feedback_id") or None) != (trigger.get("feedback_id") or None):
                continue
            return True
        return False

    def _coalesce(self, triggers: Sequence[Mapping[str, Any]]) -> List[dict]:
        grouped: Dict[str, List[dict]] = {}
        for trigger in triggers:
            grouped.setdefault(trigger["record_id"], []).append(dict(trigger))
        merged = []
        for record_id in sorted(grouped):
            group = sorted(grouped[record_id], key=lambda item: (KIND_RANK.get(item["kind"], 9), item.get("feedback_id") or ""))
            # Distinct accepted feedbacks stay distinct. A spec-update for a
            # record that already has an accepted feedback folds into that
            # feedback so the commentary is regenerated once.
            feedbacks = [item for item in group if item["kind"] != "spec-update"]
            specs = [item for item in group if item["kind"] == "spec-update"]
            if feedbacks:
                for item in feedbacks:
                    also = [other["kind"] for other in specs]
                    if also:
                        item["also"] = also
                    merged.append(item)
            else:
                merged.extend(specs)
        return merged

    def _explicit_trigger(self, *, feedback_id: Optional[str], record_id: Optional[str]) -> dict:
        if feedback_id:
            matches = self.find_feedback(feedback_id)
            if not matches:
                raise FeedbackLoopError("unknown feedback id: %s" % feedback_id)
            if len(matches) > 1:
                raise FeedbackLoopError("ambiguous feedback id: %s" % feedback_id)
            path, doc = matches[0]
            if not self._accepted(doc):
                raise FeedbackLoopError("feedback is not an accepted decision: %s" % feedback_id)
            trigger = self._trigger_from_doc(path, doc)
            if trigger is None:
                raise FeedbackLoopError("feedback has no usable record id: %s" % feedback_id)
            if record_id and trigger["record_id"] != record_id:
                raise FeedbackLoopError(
                    "feedback %s targets %s, not %s" % (feedback_id, trigger["record_id"], record_id)
                )
            return trigger
        assert record_id
        return {
            "kind": "spec-update",
            "feedback_id": None,
            "record_id": record_id,
            "record_sha1": self.record_sha1(record_id),
            "source": record_filename(record_id),
        }

    def _pending_triggers(self) -> List[dict]:
        triggers = []
        for record_id in self.changed_record_ids():
            trigger = {
                "kind": "spec-update",
                "feedback_id": None,
                "record_id": record_id,
                "record_sha1": self.record_sha1(record_id),
                "source": record_filename(record_id),
            }
            if not self._done(trigger):
                triggers.append(trigger)
        for path, doc in self._iter_feedback_docs():
            trigger = self._trigger_from_doc(path, doc)
            if trigger and not self._done(trigger):
                triggers.append(trigger)
        return self._coalesce(triggers)

    # -------------------------------------------------------------- fragments

    def _iter_traces(self) -> Iterable[Path]:
        root = self.src / "ai" / "traces"
        if not root.is_dir():
            return []
        return sorted(path for path in root.rglob("*.json") if path.is_file())

    def _iter_html(self) -> Iterable[Path]:
        root = self.src / "content" / "ai"
        if not root.is_dir():
            return []
        return sorted(path for path in root.rglob("*.html") if path.is_file())

    def _trace_mentions(self, trace: Mapping[str, Any], raw: str, record_id: str) -> bool:
        elemente = trace.get("elemente") or []
        zitate = trace.get("zitate") or []
        stand = trace.get("elemente_stand") or {}
        if isinstance(elemente, list) and record_id in elemente:
            return True
        if isinstance(zitate, list) and record_id in zitate:
            return True
        if isinstance(stand, dict) and record_id in stand:
            return True
        return _contains_id(raw, record_id)

    def affected_fragments(self, record_id: str) -> Dict[str, dict]:
        """Map ``content/ai/...html`` → location info for commentaries that cite ``record_id``."""
        found: Dict[str, dict] = {}
        for path in self._iter_traces():
            raw = path.read_text(encoding="utf-8", errors="replace")
            data, err = _load_json(path)
            derived = _fragment_from_trace_path(self.src, path)
            if err or not isinstance(data, dict):
                if derived and _contains_id(raw, record_id):
                    info = found.setdefault(derived, {"fragment": derived})
                    info["trace_path"] = path
                    info["trace_malformed"] = True
                continue
            fragment = _safe_fragment(str(data.get("fragment") or "")) or derived
            if fragment is None:
                continue
            if not self._trace_mentions(data, raw, record_id):
                continue
            info = found.setdefault(fragment, {"fragment": fragment})
            info["trace_path"] = path
            info["trace"] = data
        for path in self._iter_html():
            try:
                rel = str(path.resolve().relative_to(self.src.resolve())).replace("\\", "/")
            except ValueError:
                continue
            fragment = _safe_fragment(rel)
            if fragment is None:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not _contains_id(text, record_id):
                continue
            info = found.setdefault(fragment, {"fragment": fragment})
            info["html_path"] = path
            if "trace" not in info and "trace_malformed" not in info:
                trace_path = self._trace_path_for(fragment, info)
                if trace_path.is_file():
                    data, err = _load_json(trace_path)
                    info["trace_path"] = trace_path
                    if err or not isinstance(data, dict):
                        info["trace_malformed"] = True
                    else:
                        info["trace"] = data
        self._attach_graph_fragments(found, record_id)
        return found

    def _attach_graph_fragments(self, found: Dict[str, dict], record_id: str) -> None:
        """Add the commentary named by the causal graph when that file exists.

        A missing commentary is left absent. The loop must not create an AI
        fragment, a trace, or a spec record just because the graph names it.
        """
        node = self.dependency_graph.get(record_id)
        if not isinstance(node, dict):
            return
        page = node.get("page")
        for fragment in node.get("ai_fragments") or []:
            safe = _safe_fragment(fragment) if isinstance(fragment, str) else None
            if safe is None:
                continue
            html_path = self._html_path_for(safe)
            trace_path = self._trace_path_for(safe, {})
            html_exists = html_path.is_file()
            trace_exists = trace_path.is_file()
            if not html_exists and not trace_exists:
                continue
            info = found.setdefault(safe, {"fragment": safe})
            info["universe"] = node.get("universe")
            info["graph_record"] = record_id
            if isinstance(page, str) and page:
                info["page"] = page
            if html_exists:
                info["html_path"] = html_path
            if trace_exists and "trace" not in info and "trace_malformed" not in info:
                data, err = _load_json(trace_path)
                info["trace_path"] = trace_path
                if err or not isinstance(data, dict):
                    info["trace_malformed"] = True
                else:
                    info["trace"] = data

    def _trace_path_for(self, fragment: str, info: Mapping[str, Any]) -> Path:
        existing = info.get("trace_path")
        if isinstance(existing, Path):
            return existing
        stem = fragment[len("content/ai/"):-len(".html")]
        return self.src / "ai" / "traces" / (stem + ".json")

    def _html_path_for(self, fragment: str) -> Path:
        return self.src / fragment

    # ------------------------------------------------------------- mutation

    def _backup_html(self, fragment: str, html_path: Path) -> Optional[str]:
        if not html_path.is_file():
            return None
        data = html_path.read_bytes()
        digest = _sha256_bytes(data)
        stem = fragment[len("content/ai/"):]
        rel = "output/feedback-loop-history/%s/%s.html" % (stem, digest[:16])
        dest = self.src / rel
        if not _inside(self.src, dest):
            return None
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, dest)
        return rel

    def _mark_invalid(self, trace: dict, trigger: Mapping[str, Any], moment: datetime.datetime) -> dict:
        mark = {
            "datum": moment.strftime("%Y-%m-%d"),
            "timestamp": _stamp(moment),
            "grund": trigger["kind"],
            "ausloeser": trigger.get("feedback_id") or trigger["record_id"],
            "state": "invalidated",
            "record_id": trigger["record_id"],
            "record_sha1": trigger.get("record_sha1"),
        }
        history = trace.get("invalidierungen")
        if not isinstance(history, list):
            history = []
        if not history or history[-1] != mark:
            history.append(mark)
        trace["invalidierungen"] = history
        trace["invalidiert"] = dict(mark)
        trace["status"] = "veraltet"
        trace["stale"] = True
        trace["lifecycle"] = "invalidated"
        trace["trace_schema"] = TRACE_SCHEMA
        return mark

    def _blank_trace(self, fragment: str, record_id: str, html: str) -> dict:
        art = "abschnitt"
        if 'class="ai usage' in html or "class='ai usage" in html:
            art = "usage"
        elif "module-guide" in html:
            art = "guide"
        return {
            "fragment": fragment,
            "seite": None,
            "art": art,
            "elemente": [],
            "zitate": [],
            "quellen": [],
            "wissen": [],
            "annahmen": [],
            "prompt": None,
            "modell": None,
            "policy_version": None,
            "laeufe": [],
            "diagramme": {},
            "status": "legacy",
            "elemente_stand": {},
        }

    def _fragment_is_current(self, trace: Mapping[str, Any], trigger: Mapping[str, Any]) -> bool:
        if trace.get("status") != "aktuell":
            return False
        stand = trace.get("elemente_stand") if isinstance(trace.get("elemente_stand"), dict) else {}
        if stand.get(trigger["record_id"]) != trigger.get("record_sha1"):
            return False
        laeufe = trace.get("laeufe") if isinstance(trace.get("laeufe"), list) else []
        if not laeufe or not isinstance(laeufe[-1], Mapping):
            return False
        previous = laeufe[-1].get("trigger") if isinstance(laeufe[-1].get("trigger"), Mapping) else {}
        return (
            previous.get("record_id") == trigger["record_id"]
            and previous.get("kind") == trigger["kind"]
            and (previous.get("feedback_id") or None) == (trigger.get("feedback_id") or None)
        )

    def _synthesize(self, fragment: str, trace: Mapping[str, Any], trigger: Mapping[str, Any], html_before: str) -> str:
        record = self.load_record(trigger["record_id"])
        label, _desc = _record_bits(record)
        record_id = trigger["record_id"]
        art = trace.get("art") or "abschnitt"
        css = {"usage": "ai usage", "guide": "ai module-guide"}.get(art, "ai")
        if html_before:
            match = re.search(r'<div class="(ai[^"]*)"', html_before)
            if match:
                css = match.group(1)
        cause = trigger["kind"]
        feedback = trigger.get("feedback_id") or ""
        cause_text = {
            "user-feedback": "einer akzeptierten Rückmeldung",
            "curator-decision": "einer akzeptierten Kurationsentscheidung",
            "spec-update": "einer Änderung des Spezifikationstexts",
        }.get(cause, "eines erfassten Auslösers")
        title = (" Der Datensatz ist als %s geführt." % _esc(label)) if label else ""
        feedback_text = (" Vorgang %s." % _esc(feedback)) if feedback else ""
        href = _esc_attr(record_id) if _SIMPLE_RECORD_RE.match(record_id) else ""
        if href:
            cite = '<a class="swsref" href="#%s">[%s]</a>' % (href, _esc(record_id))
        else:
            cite = "[%s]" % _esc(record_id)
        return (
            '<div class="%s">'
            '<h4>Verwendung <span class="ai-badge" title="AI generated">KI-generiert / AI generated</span></h4>'
            "<p>Diese Erklärung wurde neu erzeugt aufgrund %s.%s%s "
            "Beleg: %s.</p>"
            '<p class="ai-note">Automatisch regenerierter Hinweis aus dem geschlossenen Feedback-Loop. '
            "Kein offizieller Normtext. Beleg: [%s].</p>"
            "</div>"
        ) % (css, cause_text, feedback_text, title, cite, _esc(record_id))

    def _prompt(self, fragment: str, trigger: Mapping[str, Any], label: str) -> str:
        return (
            "Regeneriere das KI-Fragment %s.\n"
            "Auslöser: %s %s.\n"
            "Datensatz: %s.\n"
            "Kanonische Sprache: Deutsch. Belege die Aussage mit [%s]. "
            "Wurzel ist ein div mit Klasse ai und abschließender p.ai-note.\n"
            "Kontexttitel: %s\n"
        ) % (
            fragment,
            trigger["kind"],
            trigger.get("feedback_id") or "-",
            trigger["record_id"],
            trigger["record_id"],
            label or "-",
        )

    def _html_ok(self, html_text: str) -> Optional[str]:
        if "\u27e6" in html_text or "\u27e7" in html_text:
            return "i18n placeholder in canonical text"
        try:
            from lxml import html as LH
        except ImportError as exc:
            return "lxml unavailable: %s" % exc
        try:
            element = LH.fragment_fromstring(html_text)
        except Exception as exc:  # noqa: BLE001 — structure check must report parser errors
            return "html not parseable: %s" % exc
        classes = (element.get("class") or "").split()
        if element.tag != "div" or "ai" not in classes:
            return "root is not a div.ai"
        if not element.xpath(".//p[contains(@class,'ai-note')]"):
            return "ai-note missing"
        return None

    def _apply_regeneration(self, fragment: str, info: Mapping[str, Any], trigger: Mapping[str, Any], moment: datetime.datetime) -> Tuple[str, List[str]]:
        """Write HTML and trace. Returns ``(disposition, errors)``.

        Disposition is ``regenerated``, ``skipped-missing-html``, ``skipped-malformed-trace``,
        ``skipped-current``, or ``rejected-html``.
        """
        if info.get("trace_malformed"):
            return "skipped-malformed-trace", ["malformed trace left untouched: %s" % fragment]
        html_path = self._html_path_for(fragment)
        if not html_path.is_file():
            trace = info.get("trace")
            if isinstance(trace, dict):
                self._mark_invalid(trace, trigger, moment)
                trace_path = self._trace_path_for(fragment, info)
                if _inside(self.src, trace_path):
                    _dump_json(trace_path, trace)
            return "skipped-missing-html", []
        previous_html = html_path.read_text(encoding="utf-8")
        trace = info.get("trace")
        if not isinstance(trace, dict):
            trace = self._blank_trace(fragment, trigger["record_id"], previous_html)
        else:
            trace = json.loads(json.dumps(trace))
        if self._fragment_is_current(trace, trigger):
            return "skipped-current", []
        record = self.load_record(trigger["record_id"])
        label, desc = _record_bits(record)
        html_text = self._synthesize(fragment, trace, trigger, previous_html)
        problem = self._html_ok(html_text)
        if problem:
            return "rejected-html", ["%s: %s" % (fragment, problem)]
        version, model, policy_error = self._policy()
        errors = ["policy: %s" % policy_error] if policy_error else []
        backup = self._backup_html(fragment, html_path)
        self._mark_invalid(trace, trigger, moment)
        prompt = self._prompt(fragment, trigger, label)
        trigger_view = {
            "kind": trigger["kind"],
            "feedback_id": trigger.get("feedback_id"),
            "record_id": trigger["record_id"],
            "record_sha1": trigger.get("record_sha1"),
            "timestamp": _stamp(moment),
            "also": list(trigger.get("also") or []),
        }
        if not isinstance(trace.get("elemente"), list):
            trace["elemente"] = []
        if trigger["record_id"] not in trace["elemente"]:
            trace["elemente"].append(trigger["record_id"])
        cites = set(trace.get("zitate") or [])
        cites.update(_CITE_RE.findall(html_text))
        trace["zitate"] = sorted(cites)
        if not isinstance(trace.get("quellen"), list):
            trace["quellen"] = []
        if not isinstance(trace.get("wissen"), list):
            trace["wissen"] = []
        if desc and not any(isinstance(item, dict) and item.get("aussage") == desc for item in trace["wissen"]):
            trace["wissen"].append({"aussage": desc, "fundstelle": trigger["record_id"]})
        if not isinstance(trace.get("annahmen"), list):
            trace["annahmen"] = []
        if not isinstance(trace.get("diagramme"), dict):
            trace["diagramme"] = {}
        if not isinstance(trace.get("laeufe"), list):
            trace["laeufe"] = []
        trace["laeufe"].append({
            "datum": moment.strftime("%Y-%m-%d"),
            "timestamp": _stamp(moment),
            "modell": model,
            "policy_version": version,
            "transkript": "Kontextsynthese ohne externes Modell. Auslöser %s %s." % (
                trigger["kind"], trigger.get("feedback_id") or trigger["record_id"]),
            "trigger": trigger_view,
            "previous_fragment_sha256": _sha256_bytes(previous_html.encode("utf-8")),
            "previous_fragment_backup": backup,
        })
        trace["prompt"] = prompt
        trace["modell"] = model
        trace["modell_meta"] = {
            "id": model,
            "synthesis": "builtin-contextual",
            "policy_version": version,
        }
        trace["policy_version"] = version
        trace["trigger"] = trigger_view
        trace["status"] = "aktuell"
        trace["stale"] = False
        trace["lifecycle"] = "current"
        trace["fragment"] = fragment
        stand = trace.get("elemente_stand") if isinstance(trace.get("elemente_stand"), dict) else {}
        stand = dict(stand)
        stand[trigger["record_id"]] = trigger.get("record_sha1")
        for element in trace["elemente"]:
            if element == trigger["record_id"]:
                continue
            if element not in stand:
                stand[element] = self.record_sha1(element) if isinstance(element, str) else None
        trace["elemente_stand"] = stand
        trace.pop("invalidiert", None)
        self._stamp_universe(trace, fragment, trigger, moment, regenerated=True)
        html_tmp = html_path.with_name(html_path.name + ".tmp")
        html_tmp.write_text(html_text, encoding="utf-8")
        os.replace(html_tmp, html_path)
        trace_path = self._trace_path_for(fragment, info)
        if not _inside(self.src, trace_path):
            return "rejected-html", ["trace path escapes src: %s" % fragment]
        _dump_json(trace_path, trace)
        return "regenerated", errors

    def _flag_only(self, fragment: str, info: Mapping[str, Any], trigger: Mapping[str, Any], moment: datetime.datetime) -> Tuple[str, List[str]]:
        if info.get("trace_malformed"):
            return "skipped-malformed-trace", ["malformed trace left untouched: %s" % fragment]
        trace = info.get("trace")
        html_path = self._html_path_for(fragment)
        html = html_path.read_text(encoding="utf-8") if html_path.is_file() else ""
        if not isinstance(trace, dict):
            if not html_path.is_file():
                return "skipped-missing-html", []
            trace = self._blank_trace(fragment, trigger["record_id"], html)
        else:
            trace = json.loads(json.dumps(trace))
        self._mark_invalid(trace, trigger, moment)
        if trigger["record_id"] not in (trace.get("elemente") or []):
            trace.setdefault("elemente", []).append(trigger["record_id"])
        trace["fragment"] = fragment
        self._stamp_universe(trace, fragment, trigger, moment, regenerated=False)
        trace_path = self._trace_path_for(fragment, info)
        if not _inside(self.src, trace_path):
            return "skipped-malformed-trace", ["trace path escapes src: %s" % fragment]
        _dump_json(trace_path, trace)
        return "flagged", []

    def _stamp_universe(
        self,
        trace: dict,
        fragment: str,
        trigger: Mapping[str, Any],
        moment: datetime.datetime,
        *,
        regenerated: bool,
    ) -> None:
        """Record which universe produced this commentary. Adaptive traces are unchanged."""
        node = self.dependency_graph.get(trigger["record_id"])
        if not isinstance(node, dict):
            return
        page = node.get("page")
        fragments = node.get("ai_fragments") or []
        provenance = {
            "universe": node.get("universe"),
            "record_id": trigger["record_id"],
            "ai_fragment": fragment,
            "ai_src": node.get("ai_src"),
            "page": page,
            "record_path": node.get("record_path"),
            "state": "regenerated" if regenerated else "invalidated",
            "timestamp": _stamp(moment),
        }
        if regenerated and fragment in fragments and isinstance(page, str) and page:
            previous = trace.get("seite")
            if isinstance(previous, str) and previous and previous != page:
                provenance["previous_seite"] = previous
            trace["seite"] = page
        trace["universe"] = node.get("universe")
        trace["provenance"] = provenance

    # -------------------------------------------------------------------- i18n

    def extract_segments(self, html_text: str) -> Dict[str, str]:
        """Segment id → masked German text, using the i18n_extract identity."""
        src_root = Path(__file__).resolve().parents[1]
        if str(src_root) not in sys.path:
            sys.path.insert(0, str(src_root))
        from lxml import html as LH
        from lib_i18n import hat_prosa, leaf_segmente, maskiere, seg_id

        wrapper = LH.fragment_fromstring(html_text, create_parent="x")
        found: Dict[str, str] = {}
        for element in leaf_segmente(wrapper):
            masked, _tags = maskiere(element)
            text = masked.strip()
            if not text or not hat_prosa(re.sub(r"\u27e6\d+\u27e7", "", text)):
                continue
            found[seg_id(text)] = text
        return found

    def _merge_missing(self, path: Path, updates: Mapping[str, Any]) -> Optional[str]:
        """Insert keys that are absent. A corrupt file is left byte-for-byte."""
        current, err = _load_json(path) if path.exists() else ({}, None)
        if path.exists() and (err or not isinstance(current, dict)):
            return err or "not an object"
        merged = dict(current or {})
        for key, value in updates.items():
            if key not in merged:
                merged[key] = value
        if not _inside(self.src, path):
            return "path escapes src"
        _dump_json(path, merged)
        return None

    def sync_i18n(self, fragments: Sequence[str]) -> Tuple[List[str], List[str]]:
        """Merge new segment keys. Never deletes an existing key and never rewrites a corrupt file."""
        segments: Dict[str, str] = {}
        for fragment in fragments:
            path = self._html_path_for(fragment)
            if not path.is_file():
                continue
            segments.update(self.extract_segments(path.read_text(encoding="utf-8")))
        if not segments:
            return [], []
        errors: List[str] = []
        de_path = self.src / "i18n" / "segments.de.json"
        de_updates = {
            sid: {"m": text, "n": 1, "ctx": ["ai"]}
            for sid, text in segments.items()
        }
        problem = self._merge_missing(de_path, de_updates)
        if problem:
            errors.append("segments.de.json: %s" % problem)
        for lang in self.languages():
            lang_path = self.src / "i18n" / lang / "segments.json"
            updates = {}
            for sid, german in segments.items():
                label = _MOCK_TRANSLATION.get(lang, "Regenerated commentary")
                translated = "%s [%s]" % (label, sid)
                if translated == german:
                    translated = "[%s] %s" % (lang, translated)
                updates[sid] = translated
            problem = self._merge_missing(lang_path, updates)
            if problem:
                errors.append("%s: %s" % (lang, problem))
        return sorted(segments), errors

    # ----------------------------------------------------------------- rebuild

    def generate_command(self, page: str) -> str:
        return "python3 _src/generate.py %s" % page

    def _write_preview(self, page: str, fragments: Sequence[str]) -> None:
        parts = [
            "<!-- feedback-loop incremental preview -->",
            "<!-- %s -->" % self.generate_command(page),
        ]
        for fragment in fragments:
            path = self._html_path_for(fragment)
            if path.is_file():
                parts.append(path.read_text(encoding="utf-8"))
        dest = self.src / "output" / "feedback-loop-pages" / page
        if not _inside(self.src, dest):
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        _dump_text(dest, "\n".join(parts) + "\n")

    def _rebuild(self, page: str, fragments: Sequence[str]) -> dict:
        command = self.generate_command(page)
        self._write_preview(page, fragments)
        if self.generate_fn is not None:
            self.generate_fn(page)
            return {"page": page, "status": "ok", "command": command}
        if not self.invoke_generate:
            return {"page": page, "status": "preview-only", "command": command}
        script = self.repo_root / "_src" / "generate.py"
        if not script.is_file():
            return {"page": page, "status": "skipped-missing-generator", "command": command}
        try:
            proc = subprocess.run(
                [sys.executable, str(script), page],
                cwd=str(self.repo_root),
                timeout=120,
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return {"page": page, "status": "failed", "command": command, "error": str(exc)}
        return {
            "page": page,
            "status": "ok" if proc.returncode == 0 else "failed",
            "command": command,
            "exit_code": proc.returncode,
        }

    def _pages_for(self, infos: Sequence[Mapping[str, Any]]) -> List[str]:
        pages = set()
        for info in infos:
            trace = info.get("trace")
            candidates = [trace.get("seite") if isinstance(trace, Mapping) else None, info.get("page")]
            for candidate in candidates:
                if (
                    isinstance(candidate, str)
                    and candidate.endswith(".html")
                    and ".." not in Path(candidate).parts
                ):
                    pages.add(candidate)
        return sorted(pages)

    # ------------------------------------------------------------------- ledger

    def _append_ledger(self, event: Mapping[str, Any]) -> None:
        path = self.ledger_path
        if not _inside(self.src, path):
            raise FeedbackLoopError("ledger path escapes src")
        path.parent.mkdir(parents=True, exist_ok=True)
        line = (json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        existing = path.read_bytes() if path.exists() else b""
        separator = b"" if (not existing or existing.endswith(b"\n")) else b"\n"
        with path.open("ab") as handle:
            handle.write(separator + line)

    def _record_mutation_audit(self, event: Mapping[str, Any], *, regenerate: bool) -> None:
        """Append universal mutation-audit receipts; never roll back the loop."""
        if event.get("noop"):
            return
        tools_dir = str(Path(__file__).resolve().parent)
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        try:
            import mutation_ledger as mutation_audit
        except ImportError:
            return
        flagged = [item for item in (event.get("flagged") or []) if isinstance(item, str)]
        regenerated = [item for item in (event.get("regenerated") or []) if isinstance(item, str)]
        pages = [item for item in (event.get("pages") or []) if isinstance(item, str)]
        inputs = [self.src / rel for rel in flagged]
        outputs = [self.src / rel for rel in regenerated + pages]
        details = {
            "event": event.get("event"),
            "feedback_id": event.get("feedback_id"),
            "record_id": event.get("record_id"),
            "complete": event.get("complete"),
            "flagged": flagged,
            "regenerated": regenerated,
        }
        success = bool(event.get("complete"))
        try:
            mutation_audit.record_mutation(
                "feedback-loop-invalidation",
                "feedback-loop",
                details,
                inputs=inputs,
                outputs=outputs,
                success=success,
                root=self.repo_root,
                metadata={"source": "feedback_loop.py"},
            )
            if regenerate:
                mutation_audit.record_mutation(
                    "feedback-loop-regeneration",
                    "feedback-loop",
                    details,
                    inputs=inputs,
                    outputs=outputs,
                    success=success,
                    root=self.repo_root,
                    metadata={"source": "feedback_loop.py"},
                )
        except Exception:  # noqa: BLE001 — audit failure must not undo a completed loop
            return

    def _event(
        self,
        name: str,
        trigger: Mapping[str, Any],
        moment: datetime.datetime,
        *,
        flagged: Sequence[str],
        regenerated: Sequence[str],
        pages: Sequence[str],
        rebuild: Sequence[Mapping[str, Any]],
        i18n_segments: Sequence[str],
        i18n_errors: Sequence[str],
        trace_errors: Sequence[str],
        complete: bool,
        noop: bool,
    ) -> dict:
        return seal_event({
            "schema_version": LEDGER_SCHEMA,
            "event": name,
            "recorded_at": _stamp(moment),
            "feedback_id": trigger.get("feedback_id"),
            "record_id": trigger.get("record_id"),
            "record_sha1": trigger.get("record_sha1"),
            "trigger_kind": trigger.get("kind"),
            "fragments": list(flagged),
            "flagged": list(flagged),
            "regenerated": list(regenerated),
            "pages": list(pages),
            "rebuild": [dict(item) for item in rebuild],
            "i18n_segments": list(i18n_segments),
            "i18n_errors": list(i18n_errors),
            "trace_errors": list(trace_errors),
            "spec_records_mutated": False,
            "complete": complete,
            "noop": noop,
        })

    # ----------------------------------------------------------------------- run

    def run(
        self,
        *,
        feedback_id: Optional[str] = None,
        record_id: Optional[str] = None,
        all_pending: bool = False,
        dry_run: bool = False,
        regenerate: bool = True,
    ) -> dict:
        selectors = sum(bool(item) for item in (feedback_id, record_id, all_pending))
        # record-id may narrow an explicit feedback id. all-pending stays exclusive.
        if all_pending and (feedback_id or record_id):
            raise FeedbackLoopError(
                "pass only one of --all-pending or --feedback-id/--record-id",
                code=2,
            )
        if selectors == 0:
            raise FeedbackLoopError(
                "pass --feedback-id, --record-id, or --all-pending",
                code=2,
            )
        if record_id:
            record_id = validate_record_id(record_id)
        if all_pending:
            triggers = self._pending_triggers()
        else:
            triggers = [self._explicit_trigger(feedback_id=feedback_id, record_id=record_id)]
            if not self._done(triggers[0]):
                triggers = self._coalesce(triggers)
            # An explicit request that is already satisfied still returns one noop.
        if not triggers:
            return {
                "ok": True,
                "dry_run": dry_run,
                "triggers": [],
                "flagged": [],
                "regenerated": [],
                "events": [],
            }
        events = []
        flagged_all: List[str] = []
        regenerated_all: List[str] = []
        for trigger in triggers:
            moment = self._moment()
            if self._done(trigger):
                event = self._event(
                    "noop", trigger, moment,
                    flagged=[], regenerated=[], pages=[], rebuild=[],
                    i18n_segments=[], i18n_errors=[], trace_errors=[],
                    complete=True, noop=True,
                )
                if not dry_run:
                    self._append_ledger(event)
                events.append(event)
                continue
            affected = self.affected_fragments(trigger["record_id"])
            ordered = [affected[key] for key in sorted(affected)]
            flagged = [info["fragment"] for info in ordered]
            flagged_all.extend(flagged)
            pages = self._pages_for(ordered)
            if dry_run:
                events.append(self._event(
                    "dry-run", trigger, moment,
                    flagged=flagged, regenerated=[], pages=pages, rebuild=[],
                    i18n_segments=[], i18n_errors=[], trace_errors=[],
                    complete=False, noop=False,
                ))
                continue
            regenerated: List[str] = []
            i18n_targets: List[str] = []
            trace_errors: List[str] = []
            dispositions: List[str] = []
            for info in ordered:
                if regenerate:
                    disposition, problems = self._apply_regeneration(info["fragment"], info, trigger, moment)
                    if disposition == "regenerated":
                        regenerated.append(info["fragment"])
                    if disposition in ("regenerated", "skipped-current"):
                        i18n_targets.append(info["fragment"])
                else:
                    disposition, problems = self._flag_only(info["fragment"], info, trigger, moment)
                dispositions.append(disposition)
                trace_errors.extend(problems)
            i18n_segments: List[str] = []
            i18n_errors: List[str] = []
            rebuild: List[dict] = []
            if regenerate:
                try:
                    i18n_segments, i18n_errors = self.sync_i18n(i18n_targets)
                except Exception as exc:  # noqa: BLE001 — i18n failure must not roll back the fragment
                    i18n_errors = [str(exc)]
                for page in pages:
                    try:
                        rebuild.append(self._rebuild(page, regenerated))
                    except Exception as exc:  # noqa: BLE001 — page rebuild is reported, not fatal
                        rebuild.append({
                            "page": page,
                            "status": "failed",
                            "command": self.generate_command(page),
                            "error": str(exc),
                        })
            regenerated_all.extend(regenerated)
            # A malformed trace or rejected fragment is not "done": a later run
            # must be able to retry without having thrown the provenance away.
            blocking = {"skipped-malformed-trace", "rejected-html"}
            rebuild_failed = any(item.get("status") == "failed" for item in rebuild)
            complete = not any(item in blocking for item in dispositions) and not i18n_errors and not rebuild_failed
            name = "regenerated" if regenerate else "invalidated"
            event = self._event(
                name, trigger, moment,
                flagged=flagged, regenerated=regenerated, pages=pages, rebuild=rebuild,
                i18n_segments=i18n_segments, i18n_errors=i18n_errors, trace_errors=trace_errors,
                complete=complete, noop=False,
            )
            self._append_ledger(event)
            events.append(event)
            self._record_mutation_audit(event, regenerate=regenerate)
        return {
            "ok": True,
            "dry_run": dry_run,
            "triggers": triggers,
            "flagged": flagged_all,
            "regenerated": regenerated_all,
            "events": events,
        }


class FeedbackLoopEngine(FeedbackLoop):
    """Same loop, constructible without a tree so the causal graph is readable.

    The default tree is this repository's ``_src``. Construction only builds
    the in-memory graph; it does not scan or write the corpus.
    """

    def __init__(self, src: Optional[os.PathLike] = None, **kwargs: Any):
        if src is None:
            src = Path(__file__).resolve().parents[1]
        super().__init__(src, **kwargs)


def _dump_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="feedback_loop.py")
    sub = parser.add_subparsers(dest="cmd")
    run_parser = sub.add_parser("run", help="invalidate and regenerate commentaries for one trigger")
    run_parser.add_argument("--feedback-id", default=None)
    run_parser.add_argument("--record-id", default=None)
    run_parser.add_argument("--all-pending", action="store_true")
    run_parser.add_argument("--src", default=None, help="override the _src directory (default: this tree)")
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--no-generate", action="store_true")
    run_parser.add_argument("--no-regenerate", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.cmd != "run":
        parser.print_help()
        return 2
    src = Path(args.src) if args.src else Path(__file__).resolve().parents[1]
    engine = FeedbackLoop(src, invoke_generate=not args.no_generate)
    try:
        report = engine.run(
            feedback_id=args.feedback_id,
            record_id=args.record_id,
            all_pending=args.all_pending,
            dry_run=args.dry_run,
            regenerate=not args.no_regenerate,
        )
    except FeedbackLoopError as exc:
        sys.stderr.write(exc.message + "\n")
        return exc.code
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
