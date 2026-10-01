#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Interactive AI discussion: context manifest, proposal envelope, curation queue.

The local ``/api/discuss`` route and the offline panel share this module.
A proposal is written only as a new file under
``spec/curation-queue/open/<proposal_id>.json`` (curation-flag@v1,
outcome ``proposed_change``). Existing queue files are never replaced.
Nothing in a record file is modified, and no proposal is stored as accepted.
"""
from __future__ import annotations

import difflib
import html
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from canonical_id import load_projects, parse_canonical_id, resolve_legacy  # noqa: E402
import curation_item  # noqa: E402

PRIVACY_BADGE = "Keine internen Geheimnisse übertragen"
CONTEXT_TEXT_LIMIT = 6000
MAX_BODY_BYTES = 200_000
MAX_RECORD_BYTES = 2_000_000
MAX_MESSAGE_CHARS = 4000
MAX_SUGGESTION_CHARS = 20_000
MAX_RATIONALE_CHARS = 8000
TRUNCATION_MARK = "\n…[Kontext gekürzt]"
REDACTION = "[REDACTED]"
CAMPAIGN = "ai-discuss"

PROMPT_EXPLAIN = "Erkläre diese Anforderung einfach"
PROMPT_DEPS = "Gibt es Abhängigkeiten?"
PROMPT_IMPROVE = "Formuliere einen Verbesserungsvorschlag"
QUICK_PROMPTS = (PROMPT_EXPLAIN, PROMPT_DEPS, PROMPT_IMPROVE)

_RECORD_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
_PROPOSAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_REQ_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_HREF_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)
_SECRET_RES = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|bearer)\b\s*[:=]\s*\S+"),
    re.compile(r"\b(ghp_|github_pat_|sk-|xai-|AKIA)[A-Za-z0-9_\-]{8,}"),
)
_FORBIDDEN_AUTHORITY = {"accepted", "applied", "accept"}


class DiscussError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def estimate_tokens(text: str) -> int:
    """Approximate token count: one token per four UTF-8 bytes."""
    if not text:
        return 0
    return (len(text.encode("utf-8")) + 3) // 4


def redact_secrets(text: str) -> tuple[str, int]:
    """Replace credential-shaped substrings. Ordinary prose is left intact."""
    count = 0
    for pattern in _SECRET_RES:
        text, found = pattern.subn(REDACTION, text)
        count += found
    return text, count


def src_dir(repo: Path) -> Path:
    repo = Path(repo)
    nested = repo / "_src"
    if (nested / "spec").is_dir():
        return nested
    return repo


def bare_record_id(value: str) -> str:
    if not isinstance(value, str):
        raise DiscussError("invalid-record-id")
    text = value.strip()
    parsed = parse_canonical_id(text)
    if parsed:
        text = parsed["id"]
    if not _RECORD_ID_RE.match(text):
        raise DiscussError("invalid-record-id")
    return text


def canonical_record_id(value: str) -> str:
    if isinstance(value, str):
        parsed = parse_canonical_id(value.strip())
        if parsed:
            return value.strip()
    return resolve_legacy(bare_record_id(value))


def sanitize_proposal_id(value: str) -> str:
    if not isinstance(value, str) or not _PROPOSAL_ID_RE.match(value):
        raise DiscussError("invalid-proposal-id")
    if value in {".", ".."} or "/" in value or "\\" in value or ".." in value:
        raise DiscussError("invalid-proposal-id")
    return value


def new_proposal_id(record_id: str, *, now: datetime | None = None, suffix: str | None = None) -> str:
    bare = bare_record_id(record_id)
    moment = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    tail = suffix or uuid.uuid4().hex[:8]
    return sanitize_proposal_id(f"discuss-{bare}-{moment}-{tail}")


def _html_text(fragment: str) -> str:
    text = _TAG_RE.sub(" ", fragment or "")
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def _requirement_text(record: dict) -> str:
    parts: list[str] = []
    for block in record.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        if block.get("t") == "html":
            raw = str(block.get("html") or "")
            if any(token in raw for token in ('class="desc"', "class='desc'", 'class="syntax"', 'class="recname"')):
                text = _html_text(raw)
                if text:
                    parts.append(text)
        elif block.get("t") == "props":
            for row in block.get("rows") or []:
                if not isinstance(row, dict):
                    continue
                th = _html_text(str(row.get("th") or ""))
                td = _html_text(str(row.get("td") or ""))
                line = f"{th}: {td}".strip(": ").strip()
                if line:
                    parts.append(line)
    return "\n".join(parts)


def _parents(record: dict, self_id: str) -> list[str]:
    parents: list[str] = []
    seen: set[str] = set()
    for upstream in record.get("upstream") or []:
        if not isinstance(upstream, dict):
            continue
        parent = str(upstream.get("id") or "")
        if not _REQ_ID_RE.match(parent) or parent == self_id or parent in seen:
            continue
        seen.add(parent)
        parents.append(parent)
    return parents


def _citations(record: dict) -> list[dict]:
    refs: list[dict] = []
    seen: set[tuple] = set()

    def add(item: dict) -> None:
        page = item.get("page")
        key = (item.get("id") or "", item.get("document") or "", item.get("href") or "", page)
        if key in seen or not any(key):
            return
        seen.add(key)
        refs.append(item)

    for upstream in record.get("upstream") or []:
        if not isinstance(upstream, dict):
            continue
        href = upstream.get("href")
        safe_href = href if isinstance(href, str) and href.startswith(("http://", "https://")) else ""
        page = upstream.get("page") if isinstance(upstream.get("page"), int) else None
        add({
            "id": str(upstream.get("id") or ""),
            "document": str(upstream.get("document") or ""),
            "page": page,
            "href": safe_href,
        })
    for block in record.get("blocks") or []:
        if not isinstance(block, dict):
            continue
        raw = str(block.get("html") or "")
        for href in _HREF_RE.findall(raw):
            href = html.unescape(href)
            if href.startswith(("http://", "https://")):
                add({"id": "", "document": "", "page": None, "href": href})
    return refs


def _universe(project: str) -> str:
    entry = load_projects().get("projects", {}).get(project) or {}
    name = entry.get("display_name")
    return str(name) if name else project


def _redact_value(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        return redact_secrets(value)
    if isinstance(value, list):
        total = 0
        items = []
        for item in value:
            new, count = _redact_value(item)
            items.append(new)
            total += count
        return items, total
    if isinstance(value, dict):
        total = 0
        items = {}
        for key, item in value.items():
            new, count = _redact_value(item)
            items[key] = new
            total += count
        return items, total
    return value, 0


def _empty_context(record_id: str, *, found: bool, reason: str) -> dict:
    canonical = ""
    universe = _universe("AUTOSAR/AP")
    try:
        canonical = canonical_record_id(record_id)
        parsed = parse_canonical_id(canonical) or {}
        universe = _universe(str(parsed.get("project") or "AUTOSAR/AP"))
        bare = bare_record_id(record_id)
    except DiscussError:
        bare = record_id if isinstance(record_id, str) else ""
    context = {
        "record_id": bare,
        "canonical_id": canonical,
        "universe": universe,
        "module": "",
        "requirement_text": "",
        "parent_ids": [],
        "cited_references": [],
        "found": found,
        "truncated": reason == "record-too-large",
        "original_chars": 0,
        "omitted_reason": reason,
        "redaction_count": 0,
        "privacy_badge": PRIVACY_BADGE,
        "diff_basis": "unavailable",
    }
    context["token_count"] = estimate_tokens(transmitted_text(context))
    return context


def transmitted_text(context: dict) -> str:
    """The record fields the reply is allowed to use, excluding the badge."""
    citations = []
    for item in context.get("cited_references") or []:
        if not isinstance(item, dict):
            continue
        citations.append(" ".join(str(item.get(key) or "") for key in ("id", "document", "href")))
    parts = [
        str(context.get("record_id") or ""),
        str(context.get("universe") or ""),
        str(context.get("module") or ""),
        str(context.get("requirement_text") or ""),
        " ".join(context.get("parent_ids") or []),
        " ".join(citations),
    ]
    return "\n".join(parts)


def find_record_path(src: Path, record_id: str) -> Path | None:
    bare = bare_record_id(record_id)
    name = bare + ".json"
    for base in (src / "spec" / "records", src / "spec" / "traceability"):
        if not base.is_dir():
            continue
        matches = sorted(
            path for path in base.rglob(name)
            if path.is_file() and path.name == name and _inside(path, base)
        )
        if matches:
            return matches[0]
    return None


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def package_context(src: Path, record_id: str, *, max_bytes: int = MAX_RECORD_BYTES) -> dict:
    """Build the exact context manifest for one specification item.

    Missing, unreadable, and oversized records contribute no invented text
    and no raw file bytes. Secrets are redacted before the manifest is returned.
    """
    bare = bare_record_id(record_id)
    path = find_record_path(Path(src), bare)
    if path is None:
        return _empty_context(bare, found=False, reason="record-not-found")
    try:
        size = path.stat().st_size
    except OSError:
        return _empty_context(bare, found=True, reason="record-unreadable")
    if size > max_bytes:
        context = _empty_context(bare, found=True, reason="record-too-large")
        context["original_chars"] = size
        return context
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _empty_context(bare, found=True, reason="record-unreadable")
    if not isinstance(record, dict):
        return _empty_context(bare, found=True, reason="record-unreadable")

    canonical = canonical_record_id(str(record.get("canonical_id") or bare))
    parsed = parse_canonical_id(canonical) or {}
    project = str(parsed.get("project") or "AUTOSAR/AP")
    meta = record.get("namespace_meta") if isinstance(record.get("namespace_meta"), dict) else {}
    module = meta.get("module") if isinstance(meta.get("module"), str) else ""
    requirement = _requirement_text(record)
    original_chars = len(requirement)
    context = {
        "record_id": bare,
        "canonical_id": canonical,
        "universe": _universe(project),
        "module": module,
        "requirement_text": requirement,
        "parent_ids": _parents(record, bare),
        "cited_references": _citations(record),
        "found": True,
        "truncated": False,
        "original_chars": original_chars,
        "omitted_reason": "",
        "redaction_count": 0,
        "privacy_badge": PRIVACY_BADGE,
        "diff_basis": "full-record",
    }
    context, redactions = _redact_value(context)
    context["redaction_count"] = redactions
    context["privacy_badge"] = PRIVACY_BADGE
    if len(context["requirement_text"]) > CONTEXT_TEXT_LIMIT:
        context["requirement_text"] = context["requirement_text"][:CONTEXT_TEXT_LIMIT].rstrip() + TRUNCATION_MARK
        context["truncated"] = True
        context["diff_basis"] = "truncated-context"
    context["token_count"] = estimate_tokens(transmitted_text(context))
    return context


def make_diff(record_id: str, original: str, suggested: str) -> str:
    original_lines = original.splitlines(keepends=True)
    suggested_lines = suggested.splitlines(keepends=True)
    if original_lines and not original_lines[-1].endswith("\n"):
        original_lines[-1] += "\n"
    if suggested_lines and not suggested_lines[-1].endswith("\n"):
        suggested_lines[-1] += "\n"
    diff = "".join(difflib.unified_diff(
        original_lines,
        suggested_lines,
        fromfile=f"{record_id}:current",
        tofile=f"{record_id}:proposed",
    ))
    if not diff.strip():
        raise DiscussError("suggestion-unchanged", 422)
    return diff


def suggestion_for(context: dict) -> str | None:
    text = str(context.get("requirement_text") or "").strip()
    if not text:
        return None
    return (
        text
        + "\n\nPrüfungshinweis: Gültigkeits- und Fehlerbedingungen sind im Anforderungstext "
        "nicht ausdrücklich genannt und sollen nur ergänzt werden, wenn die zitierten Verweise sie decken."
    )


def rationale_for(context: dict, *, source: str) -> str:
    basis = "dem gekürzten Kontext" if context.get("truncated") else "dem vollständigen Kontext"
    return (
        f"Abgeleitet aus {basis} von {context.get('record_id') or 'dem Datensatz'} ({source}). "
        "Der bestehende Text bleibt erhalten; ergänzt wird nur ein Prüfungshinweis. "
        "Keine automatische Freigabe."
    )


def contextual_reply(message: str, context: dict) -> dict:
    """Answer from the packaged context only. Record text is quoted, not executed."""
    if not isinstance(message, str) or not message.strip():
        raise DiscussError("empty-message")
    if len(message) > MAX_MESSAGE_CHARS:
        raise DiscussError("message-too-long")
    record_id = context.get("record_id") or "(kein Datensatz)"
    if not context.get("found"):
        reply = (
            f"Für {record_id} liegt kein lesbarer Datensatz im Kontext. "
            "Es wird kein Anforderungstext ergänzt."
        )
        return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

    text = str(context.get("requirement_text") or "").strip()
    folded = message.strip()
    lower = folded.casefold()
    if folded == PROMPT_EXPLAIN or "erklär" in lower or "explain" in lower:
        body = text or "(kein Anforderungstext im Kontext)"
        module = context.get("module") or "ohne Modul"
        reply = (
            f"{record_id} gehört zum Modul {module} im Universum {context.get('universe')}. "
            f"Einfach gesagt steht dort: {body}"
        )
        return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}
    if folded == PROMPT_DEPS or "abhäng" in lower or "depend" in lower:
        parents = list(context.get("parent_ids") or [])
        cites = []
        for item in context.get("cited_references") or []:
            if isinstance(item, dict):
                label = item.get("id") or item.get("document") or item.get("href")
                if label:
                    cites.append(str(label))
        parent_text = ", ".join(parents) if parents else "keine Eltern-IDs"
        cite_text = ", ".join(cites) if cites else "keine zitierten Verweise"
        reply = f"Für {record_id} nennt der Kontext als Eltern-IDs: {parent_text}. Zitierte Verweise: {cite_text}."
        return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}
    if folded == PROMPT_IMPROVE or "verbesser" in lower or "vorschlag" in lower:
        suggestion = suggestion_for(context)
        if suggestion is None:
            reply = f"Für {record_id} fehlt der Anforderungstext. Ein Änderungsvorschlag wird nicht erfunden."
            return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}
        rationale = rationale_for(context, source="Verbesserungsvorschlag")
        reply = suggestion + "\n\nBegründung: " + rationale
        return {"reply": reply, "suggestion": suggestion, "rationale": rationale, "mode": "mock"}

    body = text or "(kein Anforderungstext im Kontext)"
    reply = f"Zum Datensatz {record_id} verwendet die Antwort nur den Inspektor-Kontext: {body}"
    return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}


def build_proposal(context: dict, suggestion: str, rationale: str, proposal_id: str | None = None) -> dict:
    if not context.get("found"):
        raise DiscussError("record-not-found", 404)
    if context.get("omitted_reason") == "record-too-large":
        raise DiscussError("record-too-large", 422)
    if not isinstance(suggestion, str) or not suggestion.strip():
        raise DiscussError("empty-suggestion")
    if len(suggestion) > MAX_SUGGESTION_CHARS:
        raise DiscussError("suggestion-too-long")
    if not isinstance(rationale, str) or not rationale.strip():
        raise DiscussError("empty-rationale")
    if len(rationale) > MAX_RATIONALE_CHARS:
        raise DiscussError("rationale-too-long")
    suggestion, suggestion_redactions = redact_secrets(suggestion.strip())
    rationale, rationale_redactions = redact_secrets(rationale.strip())
    record_id = str(context["record_id"])
    diff = make_diff(record_id, str(context.get("requirement_text") or ""), suggestion)
    return {
        "proposal_id": sanitize_proposal_id(proposal_id) if proposal_id else new_proposal_id(record_id),
        "target_record": record_id,
        "proposed_diff": diff,
        "rationale": rationale,
        "authority": "proposal-only",
        "auto_accepted": False,
        "status": "proposed",
        "diff_basis": context.get("diff_basis") or "full-record",
        "redaction_count": int(context.get("redaction_count") or 0) + suggestion_redactions + rationale_redactions,
        "suggested_text": suggestion,
    }


def _reject_asserted_acceptance(payload: dict) -> None:
    if payload.get("auto_accepted") is True:
        raise DiscussError("auto-accept-forbidden")
    for key in ("outcome", "status"):
        if str(payload.get(key) or "").lower() in _FORBIDDEN_AUTHORITY:
            raise DiscussError("auto-accept-forbidden")


def _queue_open_dir(src: Path) -> Path:
    path = Path(src) / "spec" / "curation-queue" / "open"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _display_path(src: Path, path: Path) -> str:
    relative = path.resolve().relative_to(Path(src).resolve()).as_posix()
    if Path(src).name == "_src":
        return f"_src/{relative}"
    return relative


def _flag_payload(context: dict, proposal: dict) -> dict:
    bare = proposal["target_record"]
    canonical = context.get("canonical_id") or canonical_record_id(bare)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema": "curation-flag@v1",
        "id": proposal["proposal_id"],
        "canonical_id": canonical,
        "item_kind": "ai-amendment",
        "origin": "ai",
        "outcome": "proposed_change",
        "created": now,
        "campaign": CAMPAIGN,
        "decided_by": None,
        "decided_at": None,
        "identity": None,
        "completed_at": None,
        "claimed_by": None,
        "subject": f"AI-Diskussionsvorschlag für {bare}",
        "rationale": proposal["rationale"],
        "proposal_id": proposal["proposal_id"],
        "target_record": bare,
        "proposed_diff": proposal["proposed_diff"],
        "current_state": context.get("requirement_text") or "",
        "proposed_state": proposal.get("suggested_text") or "",
        "evidence": list(context.get("cited_references") or []),
        "counter_evidence": [],
        "history": [],
        "decision_basis": {
            "proposal_id": proposal["proposal_id"],
            "target_record": bare,
            "authority": "proposal-only",
            "auto_accepted": False,
            "context_token_count": context.get("token_count"),
            "privacy_badge": PRIVACY_BADGE,
            "redaction_count": proposal.get("redaction_count", 0),
            "diff_basis": proposal.get("diff_basis"),
            "truncated": bool(context.get("truncated")),
        },
        "instruction": {
            "goal": f"Den Diskussionsvorschlag für {bare} prüfen. Nicht selbst übernehmen.",
            "forbidden": [
                "Die Aenderung direkt committen oder mergen",
                "Den Vorschlag automatisch akzeptieren oder complete_flag() aufrufen",
                "Den Normtext ohne Beleg aendern",
            ],
            "steps": [
                *(
                    ["Der Diff basiert auf dem gekürzten Kontext. Nicht als vollständigen Ersatz des Datensatzes übernehmen."]
                    if context.get("truncated") else []
                ),
                "Lies proposed_diff, rationale und decision_basis.",
                "Prüfe den Diff gegen den Datensatz. Der Diff ist ein Vorschlag, keine Entscheidung.",
                "Lege eine eigene Entscheidung ab oder verwirf den Vorschlag.",
            ],
        },
    }


def _exclusive_create(path: Path, text: str) -> bool:
    """Create ``path`` without replacing an existing file. Temporary files are removed."""
    if path.exists():
        return False
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        try:
            os.link(temporary, path)
        except FileExistsError:
            return False
        return True
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def _same_proposal(existing: dict, proposal: dict) -> bool:
    return (
        existing.get("proposal_id") == proposal["proposal_id"]
        and existing.get("target_record") == proposal["target_record"]
        and existing.get("proposed_diff") == proposal["proposed_diff"]
        and existing.get("rationale") == proposal["rationale"]
        and existing.get("outcome") == "proposed_change"
        and (existing.get("decision_basis") or {}).get("auto_accepted") is False
    )


def write_proposal(src: Path, context: dict, proposal: dict) -> dict:
    """Write one open curation flag. An existing file is left byte-for-byte unchanged."""
    _reject_asserted_acceptance(proposal)
    proposal_id = sanitize_proposal_id(proposal["proposal_id"])
    open_dir = _queue_open_dir(src)
    path = open_dir / f"{proposal_id}.json"
    if not _inside(path, open_dir):
        raise DiscussError("invalid-proposal-id")
    payload = _flag_payload(context, proposal)
    item = curation_item.from_curation_flag(payload)
    if not curation_item.is_conformant(item) or item.get("status") != "proposed":
        raise DiscussError("proposal-not-conformant", 500)
    encoded = json.dumps(payload, ensure_ascii=False, indent=1) + "\n"
    created = _exclusive_create(path, encoded)
    if not created:
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DiscussError("queue-conflict", 409) from exc
        if not _same_proposal(existing, proposal):
            raise DiscussError("queue-conflict", 409)
        return {
            "ok": True,
            "created": False,
            "idempotent": True,
            "path": _display_path(src, path),
            "status": "proposed",
            "proposal": proposal,
        }
    return {
        "ok": True,
        "created": True,
        "idempotent": False,
        "path": _display_path(src, path),
        "status": "proposed",
        "proposal": proposal,
    }


def _record_id_from(query: dict | None, payload: dict | None) -> str:
    for source in (payload or {},):
        for key in ("record_id", "target_record", "record"):
            if source.get(key):
                return str(source[key])
    query = query or {}
    for key in ("record_id", "target_record", "record"):
        value = query.get(key)
        if isinstance(value, list):
            value = value[0] if value else ""
        if value:
            return str(value)
    raise DiscussError("invalid-record-id")


def _load_body(body: bytes | None) -> dict:
    if body is None:
        raise DiscussError("content-length-required", 411)
    if body == b"":
        raise DiscussError("empty-body")
    if len(body) > MAX_BODY_BYTES:
        raise DiscussError("body-too-large", 413)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise DiscussError("invalid-json") from exc
    if not isinstance(payload, dict):
        raise DiscussError("invalid-json")
    return payload


def handle_http(method: str, query: dict | None, body: bytes | None, repo: Path) -> tuple[int, dict]:
    """Serve ``/api/discuss``. Client-supplied requirement text is not trusted."""
    src = src_dir(repo)
    try:
        if method == "GET":
            context = package_context(src, _record_id_from(query, None))
            return 200, {"ok": True, "mode": "live", "context": context}
        if method != "POST":
            return 405, {"ok": False, "error": "method-not-allowed"}
        payload = _load_body(body)
        _reject_asserted_acceptance(payload)
        action = str(payload.get("action") or "chat")
        context = package_context(src, _record_id_from(query, payload))
        if action == "context":
            return 200, {"ok": True, "mode": "live", "context": context}
        if action == "chat":
            message = payload.get("message")
            if not isinstance(message, str):
                raise DiscussError("empty-message")
            reply = contextual_reply(message, context)
            reply["mode"] = "live"
            return 200, {"ok": True, "mode": "live", "context": context, **reply}
        if action == "propose":
            suggestion = payload.get("suggestion")
            rationale = payload.get("rationale")
            if not isinstance(suggestion, str) or not suggestion.strip():
                generated = suggestion_for(context)
                if generated is None:
                    raise DiscussError("empty-suggestion", 422)
                suggestion = generated
                if not isinstance(rationale, str) or not rationale.strip():
                    rationale = rationale_for(context, source="Vorschlag ableiten")
            elif not isinstance(rationale, str) or not rationale.strip():
                rationale = rationale_for(context, source="Vorschlag ableiten")
            proposal = build_proposal(
                context,
                suggestion,
                rationale,
                payload.get("proposal_id") if payload.get("proposal_id") else None,
            )
            client_diff = payload.get("proposed_diff")
            if isinstance(client_diff, str) and client_diff and client_diff != proposal["proposed_diff"]:
                raise DiscussError("diff-mismatch", 409)
            return 200, {"ok": True, "mode": "live", "context": context, "proposal": proposal}
        if action == "submit":
            proposal_body = payload.get("proposal") if isinstance(payload.get("proposal"), dict) else payload
            _reject_asserted_acceptance(proposal_body)
            suggestion = proposal_body.get("suggestion")
            rationale = proposal_body.get("rationale")
            if not isinstance(suggestion, str) or not suggestion.strip():
                suggestion = suggestion_for(context)
                if suggestion is None:
                    raise DiscussError("empty-suggestion", 422)
            if not isinstance(rationale, str) or not rationale.strip():
                rationale = rationale_for(context, source="In Curation übergeben")
            proposal_id = proposal_body.get("proposal_id") or payload.get("proposal_id")
            proposal = build_proposal(
                context,
                str(suggestion),
                str(rationale),
                str(proposal_id) if proposal_id else None,
            )
            client_diff = proposal_body.get("proposed_diff")
            if isinstance(client_diff, str) and client_diff and client_diff != proposal["proposed_diff"]:
                raise DiscussError("diff-mismatch", 409)
            result = write_proposal(src, context, proposal)
            result["mode"] = "live"
            result["context"] = context
            return 200, result
        raise DiscussError("unknown-action")
    except DiscussError as exc:
        return exc.status, {"ok": False, "error": str(exc)}
