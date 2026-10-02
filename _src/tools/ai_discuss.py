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

_RECORD_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_.-]{0,199}$")
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
    if not _RECORD_ID_RE.match(text) or text in {".", ".."} or ".." in text:
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


def find_snippet(src: Path, snippet_id: str) -> dict | None:
    bare = bare_record_id(snippet_id)
    snippets_dir = Path(src) / "spec" / "snippets"
    if not snippets_dir.is_dir():
        return None
    for p in sorted(snippets_dir.rglob("*.json")):
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for snip in data.get("snippets") or []:
                    if snip.get("id") == bare or snip.get("source_element") == bare:
                        return snip
        except Exception:
            continue
    return None


def find_classic_spec_record(src: Path, record_id: str) -> dict | None:
    bare = bare_record_id(record_id)
    modules_dir = Path(src) / "spec" / "records" / "classic" / "modules"
    if not modules_dir.is_dir():
        return None
    for p in sorted(modules_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            mod = data.get("module", p.stem)
            blocks = data.get("blocks", [])
            for i, b in enumerate(blocks):
                h = b.get("html", "")
                if f'id="{bare}"' in h or f"id='{bare}'" in h:
                    m = re.search(
                        r'<h3 class=["\']recname["\'][^>]*><span class=["\']kind["\']>([^<]+)</span>\s*(.+?)\s*<span class=["\']sws["\']>(?:<a[^>]*>)?\[([^\]]+)\]',
                        h,
                    )
                    kind = m.group(1).strip() if m else "api"
                    name = m.group(2).strip() if m else bare
                    sws = m.group(3).strip() if m else bare
                    syntax = ""
                    desc = ""
                    for next_b in blocks[i + 1 :]:
                        nh = next_b.get("html", "")
                        if 'class="recname"' in nh or "class='recname'" in nh or "<h2" in nh:
                            break
                        if 'class="syntax"' in nh or "class='syntax'" in nh:
                            syntax = re.sub(r"<[^>]+>", "", nh).strip()
                        elif 'class="desc"' in nh or "class='desc'" in nh:
                            desc = re.sub(r"<[^>]+>", "", nh).strip()
                    return {
                        "id": bare,
                        "sws": sws,
                        "kind": kind,
                        "name": name,
                        "syntax": syntax,
                        "desc": desc,
                        "module": mod,
                        "document": f"AUTOSAR_SWS_{mod}",
                    }
        except Exception:
            continue
    return None


def find_guide(src: Path, record_id: str) -> dict | None:
    bare = bare_record_id(record_id)
    is_cluster = bare.startswith("ai-cluster-guide-")
    is_module = bare.startswith("ai-guide-")
    if not (is_cluster or is_module):
        return None

    root = Path(src)
    content_dir = root / "content" / "ai"
    if not content_dir.is_dir() and (root / "_src").is_dir():
        content_dir = root / "_src" / "content" / "ai"
    if not content_dir.is_dir():
        return None

    if is_cluster:
        key = bare[len("ai-cluster-guide-"):].lower()
        guide_type = "cluster"
        html_file = content_dir / "classic" / "clusters" / key / "main_01.html"
        seq_file = content_dir / "classic" / "clusters" / key / "main_01.diag-01.seq.json"
        name = f"Cluster Guide ({key.upper()})"
        mod_label = key.upper()
    else:
        key = bare[len("ai-guide-"):].lower()
        guide_type = "module"
        html_file = content_dir / "classic" / "modules" / key / "main_01.html"
        seq_file = content_dir / "classic" / "modules" / key / "main_01.diag-01.seq.json"
        name = f"User Guide ({key.capitalize()})"
        mod_label = key.capitalize()

    if not html_file.is_file():
        return None

    try:
        raw_html = html_file.read_text(encoding="utf-8")
    except Exception:
        return None

    text_clean = re.sub(r"<style[\s\S]*?</style>", "", raw_html)
    text_clean = re.sub(r"<svg[\s\S]*?</svg>", "", text_clean)
    text_clean = re.sub(r"<[^>]+>", " ", text_clean)
    text_clean = " ".join(text_clean.split())

    citations = []
    sws_matches = re.findall(r"\[(SWS_[A-Za-z0-9_]+)\]", raw_html)
    for sws in dict.fromkeys(sws_matches):
        citations.append({
            "id": sws,
            "document": f"AUTOSAR-Spezifikation für {mod_label}",
            "href": f"#{sws}",
        })

    diagram_text = ""
    diagram_info = None
    if seq_file.is_file():
        try:
            seq_data = json.loads(seq_file.read_text(encoding="utf-8"))
            diagram_info = seq_data
            titel = seq_data.get("titel", "")
            teilnehmer = [t.get("name", "") for t in seq_data.get("teilnehmer", [])]
            schritte_desc = []
            for idx, s in enumerate(seq_data.get("schritte", [])):
                von = teilnehmer[s.get("von", 0)] if s.get("von", 0) < len(teilnehmer) else "?"
                nach = teilnehmer[s.get("nach", 0)] if s.get("nach", 0) < len(teilnehmer) else "?"
                txt = " / ".join(s.get("text", []))
                schritte_desc.append(f"  {idx+1}. {von} -> {nach}: {txt}")
            diagram_text = (
                f"Kollaborations- / Sequenzdiagramm: {titel}\n"
                f"Teilnehmer: {', '.join(teilnehmer)}\n"
                f"Ablaufschritte:\n" + "\n".join(schritte_desc)
            )
        except Exception:
            pass

    return {
        "id": bare,
        "name": name,
        "guide_type": guide_type,
        "module": mod_label,
        "clean_text": text_clean,
        "raw_html": raw_html,
        "citations": citations,
        "diagram_text": diagram_text,
        "diagram_info": diagram_info,
        "html_file": str(html_file),
        "seq_file": str(seq_file) if seq_file.is_file() else None,
    }


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
    """Build the exact context manifest for one specification item or pinned snippet.

    Missing, unreadable, and oversized records contribute no invented text
    and no raw file bytes. Secrets are redacted before the manifest is returned.
    """
    bare = bare_record_id(record_id)
    path = find_record_path(Path(src), bare)
    if path is None:
        snip = find_snippet(Path(src), bare)
        if snip:
            sws = snip.get("source_element") or snip.get("id")
            doc = snip.get("source_document") or "AUTOSAR Norm"
            page = snip.get("source_page")
            category = snip.get("category") or "inbound_call"
            rationale = snip.get("relevance_rationale") or ""
            verbatim = snip.get("verbatim_text") or ""
            modul = snip.get("target_module") or ""
            sha = snip.get("sha256", "")

            requirement = (
                f"[{sws}] {verbatim}\n\n"
                f"Fundstelle: {doc} (Seite {page})\n"
                f"Kategorie: {category}\n"
                f"Zweck / Relevanz: {rationale}"
            )
            canonical = f"AUTOSAR/CP/record/{sws}" if sws and sws.startswith("SWS_") else f"AUTOSAR/CP/record/{bare}"
            context = {
                "record_id": bare,
                "canonical_id": canonical,
                "universe": "AUTOSAR Classic Platform",
                "module": modul,
                "requirement_text": requirement,
                "parent_ids": [sws] if sws and sws != bare else [],
                "cited_references": [{
                    "id": sws if sws else "",
                    "document": doc,
                    "page": page if isinstance(page, int) else None,
                    "href": "",
                }],
                "found": True,
                "truncated": False,
                "original_chars": len(requirement),
                "omitted_reason": "",
                "redaction_count": 0,
                "privacy_badge": PRIVACY_BADGE,
                "diff_basis": "full-record",
                "is_snippet": True,
                "snippet_meta": {
                    "source_document": doc,
                    "source_page": page,
                    "source_element": sws,
                    "category": category,
                    "relevance_rationale": rationale,
                    "sha256": sha,
                    "target_module": modul,
                },
            }
            context["token_count"] = estimate_tokens(transmitted_text(context))
            return context

        classic_rec = find_classic_spec_record(Path(src), bare)
        if classic_rec:
            sws = classic_rec["sws"]
            doc = classic_rec["document"]
            kind = classic_rec["kind"]
            name = classic_rec["name"]
            modul = classic_rec["module"]
            syntax = classic_rec["syntax"]
            desc = classic_rec["desc"]
            requirement = (
                f"[{sws}] {name} ({kind})\n\n"
                f"Spezifikationsdokument: {doc}\n"
                f"Syntax: {syntax}\n\n"
                f"Beschreibung: {desc}\n\n"
                f"Status: Konstituierender Spezifikations-Record für Modul {modul}"
            )
            canonical = f"AUTOSAR/CP/record/{sws}" if sws.startswith("SWS_") else f"AUTOSAR/CP/record/{bare}"
            context = {
                "record_id": bare,
                "canonical_id": canonical,
                "universe": "AUTOSAR Classic Platform",
                "module": modul,
                "requirement_text": requirement,
                "parent_ids": [sws] if sws != bare else [],
                "cited_references": [{
                    "id": sws,
                    "document": doc,
                    "page": None,
                    "href": "",
                }],
                "found": True,
                "truncated": False,
                "original_chars": len(requirement),
                "omitted_reason": "",
                "redaction_count": 0,
                "privacy_badge": PRIVACY_BADGE,
                "diff_basis": "full-record",
                "is_snippet": False,
                "is_constituting": True,
                "record_meta": classic_rec,
            }
            context["token_count"] = estimate_tokens(transmitted_text(context))
            return context

        guide = find_guide(Path(src), bare)
        if guide:
            req_text = guide["clean_text"]
            if guide.get("diagram_text"):
                req_text += "\n\n" + guide["diagram_text"]
            context = {
                "record_id": bare,
                "canonical_id": f"AUTOSAR/CP/guide/{bare}",
                "universe": "AUTOSAR Classic Platform",
                "module": guide["module"],
                "requirement_text": req_text,
                "parent_ids": [],
                "cited_references": guide["citations"],
                "found": True,
                "truncated": False,
                "original_chars": len(req_text),
                "omitted_reason": "",
                "redaction_count": 0,
                "privacy_badge": PRIVACY_BADGE,
                "diff_basis": "full-record",
                "is_snippet": False,
                "is_constituting": False,
                "is_guide": True,
                "guide_meta": guide,
                "diagram_text": guide.get("diagram_text", ""),
            }
            context["token_count"] = estimate_tokens(transmitted_text(context))
            return context

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
    if context.get("is_guide"):
        meta = context.get("guide_meta") or {}
        g_name = meta.get("name") or context.get("record_id")
        return (
            f"[STATUS: REVIEW_GUIDE / PRÜFUNG]\n"
            f"Guide: {g_name} ({context.get('record_id')})\n"
            f"Ziel: {context.get('module')}\n"
            f"Vorschlag: Abgleich der Modulinteraktionen und Sequenzdiagramm-Schritte mit der AUTOSAR-Spezifikation."
        )
    if context.get("is_snippet"):
        meta = context.get("snippet_meta") or {}
        sws = meta.get("source_element") or context.get("record_id")
        modul = context.get("module") or "LinIf"
        return (
            f"[STATUS: EXCLUDE / ÜBERPRÜFEN]\n"
            f"Snippet: {context.get('record_id')}\n"
            f"Element: {sws}\n"
            f"Zielmodul: {modul}\n"
            f"Vorschlag: Im nächsten Curation-Ingest auf Relevanz prüfen und ggf. aus Dossier entfernen."
        )
    text = str(context.get("requirement_text") or "").strip()
    if not text:
        return None
    return (
        text
        + "\n\nPrüfungshinweis: Gültigkeits- und Fehlerbedingungen sind im Anforderungstext "
        "nicht ausdrücklich genannt und sollen nur ergänzt werden, wenn die zitierten Verweise sie decken."
    )


def rationale_for(context: dict, *, source: str) -> str:
    if context.get("is_guide"):
        return f"Kurations- und Review-Prüfung für Guide {context.get('record_id')} ({source})."
    if context.get("is_snippet"):
        return f"Kurations-Beanstandung für Inbound-Snippet {context.get('record_id')} ({source})."
    basis = "dem gekürzten Kontext" if context.get("truncated") else "dem vollständigen Kontext"
    return (
        f"Abgeleitet aus {basis} von {context.get('record_id') or 'dem Datensatz'} ({source}). "
        "Der bestehende Text bleibt erhalten; ergänzt wird nur ein Prüfungshinweis. "
        "Keine automatische Freigabe."
    )


def _is_substantiated_rationale(message: str) -> bool:
    folded = " ".join(message.strip().split())
    if len(folded) < 25:
        return False
    if len(folded) >= 50:
        return True
    lower = folded.lower()
    indicators = (
        "weil", "da ", "grund", "begründ", "treiber", "schnittstelle", "schicht",
        "redundant", "intern", "fehlt", "falsche", "nicht zuständig", "architektur",
        "abstraktion", "vertrag", "hardware", "mcsl", "pdu", "can", "lin", "fr",
        "eth", "bsw", "swc", "autosar", "konform", "irrelevant", "spezifikation",
        "gehört zu", "nicht konstituierend", "kein bezug", "falsch für", "soll ausgeschlossen",
        "ausschließen", "ausgeschlossen werden", "nicht zutreffend", "unpassend",
        "revidier", "aus dem kontext", "nicht passend", "widerspr"
    )
    return any(k in lower for k in indicators)


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

    if context.get("is_snippet"):
        meta = context.get("snippet_meta") or {}
        sws = meta.get("source_element") or context.get("record_id")
        doc = meta.get("source_document") or "Spezifikation"
        page = meta.get("source_page") or "?"
        cat = meta.get("category") or "inbound_call"
        modul = context.get("module") or "LinIf"
        rat = meta.get("relevance_rationale") or ""

        # Provenance / Herkunft
        if any(w in lower for w in ("woher", "herkunft", "source", "quelle", "ursprung", "fundstelle")):
            reply = (
                f"Herkunftsnachweis für {record_id} ({sws}):\n\n"
                f"• Quelldokument: {doc}\n"
                f"• Fundstelle: Seite {page} (SWS-Identifier [{sws}])\n"
                f"• Klassifikation: {cat}\n\n"
                f"Dieses Snippet wurde während des Kontext-Distributionslaufs extrahiert und gepinnt. "
                f"Es belegt eine Inbound-Anforderung, die das Nachbardokument {doc} an das Modul {modul} stellt."
            )
            return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

        # Purpose / Sinnhaftigkeit
        if any(w in lower for w in ("sinn", "zweck", "warum", "relevan", "verbindlich", "bedeutung")):
            reply = (
                f"Sinnhaftigkeit & Zweck für {modul}:\n\n"
                f"• Erfassungsbegründung: {rat}\n\n"
                f"Dieses Snippet stellt den Schnittstellenvertrag sicher: Der KI-Agent soll bei der Generierung "
                f"des Guides wissen, welche Nachbarmodule Anforderungen an {modul} stellen (z.B. synchrone Aufrufe oder Callbacks), "
                f"anstatt das Modul isoliert ohne Systemkontext zu betrachten."
            )
            return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

        # Challenge / Beanstandung / Ausschluss
        if any(w in lower for w in ("falsch", "beanstand", "ablehn", "irrelevant", "unpassend", "unzutreffend", "ausschlie", "lösch", "entfern", "widerspr", "nicht anwendbar", "stimmt nicht")):
            if not _is_substantiated_rationale(folded):
                reply = (
                    f"Deine Beanstandung zu Snippet {record_id} ({sws}) wurde registriert.\n\n"
                    f"Um die Beanstandung fachlich zu prüfen und ein verbindliches Kurationsangebot zu erstellen, "
                    f"wird eine stichhaltige technische Begründung benötigt (z. B. Angabe von Schichtentrennung, Architekturfehler oder Redundanz).\n\n"
                    f"Bitte erläutere kurz: Warum genau ist dieses Element für {modul} unzutreffend?"
                )
                return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

            reply = (
                f"Deine Beanstandung zu Snippet {record_id} ({sws}) ist berechtigt:\n\n"
                f"Argument: „{folded}“\n\n"
                f"Wenn diese Spezifikation rein intern für {doc} gilt oder für {modul} keinen konstituierenden Schnittstellenvertrag darstellt, "
                f"ist die Aufnahme in den Agentenkontext irreführend und verfälscht die Kommentargenerierung.\n\n"
                f"Ich habe einen Curation-Vorschlag formuliert, um dieses Snippet beim nächsten Ingest-Lauf zu prüfen und ggf. auszuschließen. "
                f"Du kannst das Ergebnis jetzt mit „In Curation-Queue vormerken“ ablegen."
            )
            suggestion = (
                f"[STATUS: EXCLUDE / AUSSCHLIESSEN]\n"
                f"Snippet-ID: {record_id}\n"
                f"Referenz: {sws} aus {doc} (Seite {page})\n"
                f"Zielmodul: {modul}\n"
                f"Empfohlene Aktion: Aus dem Agenten-Kontext-Dossier ausschließen.\n"
                f"Begründung: {folded}"
            )
            rationale = (
                f"Im Curation-Dialog beanstandet: {folded}. "
                f"Fremdreferenz soll im nächsten Curation-Ingest überprüft und aus dem Kontext von {modul} entfernt werden."
            )
            return {"reply": reply, "suggestion": suggestion, "rationale": rationale, "mode": "mock"}

    attached_items = context.get("attached_items") or []
    if attached_items:
        item_names = []
        for it in attached_items:
            nid = it.get("record_id") or it.get("id") or "?"
            nname = it.get("record_meta", {}).get("name") or it.get("snippet_meta", {}).get("source_element") or nid
            item_names.append(f"{nid} ({nname})")
        item_str = ", ".join(item_names)
        modul = context.get("module") or "LinIf"

        if any(w in lower for w in ("woher", "herkunft", "source", "quelle", "ursprung", "fundstelle")):
            details = []
            for it in attached_items:
                iid = it.get("record_id")
                if it.get("is_snippet"):
                    m = it.get("snippet_meta", {})
                    details.append(f"• {iid} (Inbound): aus {m.get('source_document')}, S. {m.get('source_page')} [{m.get('source_element')}] · Zweck: {m.get('relevance_rationale')}")
                elif it.get("is_constituting"):
                    m = it.get("record_meta", {})
                    details.append(f"• {iid} (Konstituierend): {m.get('name')} ({m.get('kind')}) aus {m.get('document')}")
                else:
                    details.append(f"• {iid}: {it.get('module', '')}")
            reply = (
                f"Herkunftsnachweis für die {len(attached_items)} ausgewählten Elemente:\n\n"
                + "\n".join(details)
                + f"\n\nDiese Elemente bilden zusammen den Spezifikations- und Schnittstellenkontext für {modul}."
            )
            return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

        if any(w in lower for w in ("sinn", "zweck", "warum", "relevan", "zusammenhang", "schnittstelle", "bezug", "beziehung")):
            reply = (
                f"Schnittstellenbezug & Kontext der {len(attached_items)} Elemente:\n\n"
                f"Im Modulkontext von {modul} definieren die konstituierenden APIs den verbindlichen Implementierungsvertrag, "
                f"während die Inbound-Snippets den synchronen oder asynchronen Aufruf durch Nachbarmodule belegen.\n\n"
                f"Gemeinsame Betrachtung stellt sicher, dass Wechselwirkungen (wie Schedule-Tabellen-Trigger oder Wakeup-Validierung) "
                f"konsistent im Prompt-Dossier und den Generaten abgebildet werden."
            )
            return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

        if any(w in lower for w in ("falsch", "beanstand", "ablehn", "irrelevant", "unpassend", "unzutreffend", "ausschlie", "lösch", "entfern", "nicht konstituierend")):
            if not _is_substantiated_rationale(folded):
                reply = (
                    f"Deine Beanstandung zu den Elementen [{item_str}] wurde registriert.\n\n"
                    f"Um die Beanstandung fachlich zu prüfen und als „begründet“ zu akzeptieren, "
                    f"wird eine stichhaltige technische Begründung benötigt (z. B. warum die Zuordnung im Modulkontext von {modul} falsch ist).\n\n"
                    f"Bitte erläutere kurz: Warum genau ist die Einbindung oder Eigenschaft dieser Elemente falsch?"
                )
                return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

            reply = (
                f"Beanstandung zu den Elementen [{item_str}]:\n\n"
                f"Argument: „{folded}“\n\n"
                f"Wenn die Zuordnung, die 'konstituierend'-Eigenschaft oder die Bindung eines dieser Elemente für {modul} unzutreffend ist, "
                f"sollte die Entkopplung im nächsten Curation-Ingest geprüft und vorgenommen werden.\n\n"
                f"Ich habe einen Kurationsvorschlag vorbereitet. Du kannst ihn direkt mit „In Curation-Queue vormerken“ absenden."
            )
            suggestion = (
                f"[STATUS: EXCLUDE_OR_REVISE]\n"
                f"Elemente im Fokus: {item_str}\n"
                f"Zielmodul: {modul}\n"
                f"Empfohlene Aktion: Einbindung bzw. 'konstituierend'-Eigenschaft im nächsten Ingest prüfen und korrigieren.\n"
                f"Begründung: {folded}"
            )
            return {
                "reply": reply,
                "suggestion": suggestion,
                "rationale": f"Im Multi-Item-Curation-Dialog beanstandet: {folded}",
                "mode": "mock",
            }

    if context.get("is_constituting"):
        rec_meta = context.get("record_meta") or {}
        r_name = rec_meta.get("name") or record_id
        r_kind = rec_meta.get("kind") or "api"
        r_sws = rec_meta.get("sws") or record_id
        r_doc = rec_meta.get("document") or "Spezifikation"
        modul = context.get("module") or "LinIf"

        if any(w in lower for w in ("woher", "herkunft", "source", "quelle", "ursprung", "fundstelle")):
            reply = (
                f"Herkunftsnachweis für {record_id} ({r_name}):\n\n"
                f"• Spezifikationsdokument: {r_doc}\n"
                f"• SWS-Identifier: [{r_sws}]\n"
                f"• Element-Typ: {r_kind}\n"
                f"• Modul: {modul}\n\n"
                f"Dieser Spec-Record wurde aus der offiziellen AUTOSAR-Classic-Spezifikation für {modul} extrahiert "
                f"und konstituiert die Schnittstellendefinition des Moduls."
            )
            return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

        # Challenge / Beanstandung / Ausschluss der konstituierenden Eigenschaft
        if any(w in lower for w in ("falsch", "beanstand", "ablehn", "irrelevant", "unpassend", "unzutreffend", "ausschlie", "lösch", "entfern", "nicht konstituierend", "stimmt nicht")):
            if not _is_substantiated_rationale(folded):
                reply = (
                    f"Deine Beanstandung zu `{r_name}` [{r_sws}] wurde erfasst.\n\n"
                    f"Um die Beanstandung fachlich zu prüfen und ein Kurationsangebot zu erstellen, "
                    f"wird eine stichhaltige technische Begründung benötigt (z. B. warum dieser Record nicht zum Kernvertrag von {modul} gehört).\n\n"
                    f"Bitte erläutere kurz: Warum genau ist die Einstufung als konstituierend falsch?"
                )
                return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

            reply = (
                f"Deine Beanstandung zu `{r_name}` [{r_sws}] ist erfasst:\n\n"
                f"Argument: „{folded}“\n\n"
                f"Falls `{r_name}` nicht konstituierend für {modul} ist (z.B. optional, plattformspezifisch oder nicht zum Kernvertrag gehörig), "
                f"sollte dieser Record aus dem konstituierenden Agenten-Dossier ausgeschlossen werden.\n\n"
                f"Ich habe einen Curation-Vorschlag formuliert, den du in die Curation-Queue vormerken kannst."
            )
            suggestion = (
                f"[STATUS: EXCLUDE_CONSTITUTING / NICHT KONSTITUIEREND]\n"
                f"Record-ID: {record_id}\n"
                f"Name: {r_name} ({r_kind})\n"
                f"Spezifikation: {r_doc} [{r_sws}]\n"
                f"Zielmodul: {modul}\n"
                f"Empfohlene Aktion: 'konstituierend'-Eigenschaft für {r_name} aufheben / aus Dossier ausschließen.\n"
                f"Begründung: {folded}"
            )
            return {
                "reply": reply,
                "suggestion": suggestion,
                "rationale": f"Im Curation-Dialog als nicht-konstituierend beanstandet: {folded}",
                "mode": "mock",
            }

        # Purpose / Sinnhaftigkeit
        if any(w in lower for w in ("sinn", "zweck", "warum", "relevan", "konstituierend", "bedeutung")):
            reply = (
                f"Konstituierende Eigenschaft von {r_name} [{r_sws}]:\n\n"
                f"• Typ: {r_kind}\n"
                f"• Modul-Kontext: {modul}\n\n"
                f"Als konstituierender Record definiert `{r_name}` einen Kernbestandteil der Modulspezifikation. "
                f"Der KI-Agent verwendet diesen Record für Funktionsübersichten, Schnittstellenbeschreibungen und Sequenzdiagramme."
            )
            return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

    if context.get("is_guide"):
        g_meta = context.get("guide_meta") or {}
        g_name = g_meta.get("name") or record_id
        g_mod = context.get("module") or ""
        diag_txt = context.get("diagram_text") or ""

        if any(w in lower for w in ("diagramm", "ablauf", "schritt", "nachricht", "aufruf", "sequenz")):
            if diag_txt:
                reply = (
                    f"Ablauf- und Kollaborationsübersicht für {g_name}:\n\n"
                    f"{diag_txt}\n\n"
                    f"Diese Aufrufe spiegeln die Interaktion zwischen den Modulen wider. "
                    f"Möchtest du eine bestimmte Nachricht oder Signatur im Diagramm beanstanden?"
                )
            else:
                reply = f"Für {g_name} ist kein Sequenzdiagramm hinterlegt."
            return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

        if any(w in lower for w in ("falsch", "fehler", "korrektur", "beanstand", "stimmt nicht", "inkonsistent")):
            reply = (
                f"Deine Anmerkung zum {g_name} wurde erfasst:\n\n"
                f"Hinweis: „{folded}“\n\n"
                f"Im Guide und Sequenzdiagramm müssen alle Schnittstellenaufrufe exakt den SWS-Spezifikationen entsprechen. "
                f"Ich habe einen Korrekturvorschlag für das nächste Review-Paket vorbereitet. "
                f"Du kannst ihn über die Curation-Queue vormerken oder direkt über „Feedback melden“ einreichen."
            )
            suggestion = (
                f"[GUIDE-KORREKTUR für {record_id}]\n"
                f"Bereich: {g_name} ({g_mod})\n"
                f"Beanstandung: {folded}\n"
                f"Aktion: Überprüfung und Angleichung der API-Aufrufe an die AUTOSAR-SWS-Norm."
            )
            return {
                "reply": reply,
                "suggestion": suggestion,
                "rationale": f"Benutzer-Feedback im Guide-Diskussionsdialog: {folded}",
                "mode": "mock",
            }

        if any(w in lower for w in ("woher", "herkunft", "source", "quelle", "ursprung", "fundstelle")):
            cites = context.get("cited_references") or []
            c_lines = [f"• {c.get('id', '')}: {c.get('document', '')}" for c in cites]
            reply = (
                f"Quellennachweis für {g_name}:\n\n"
                f"Der Guide und das Sequenzdiagramm leiten sich aus folgenden Spezifikationen ab:\n"
                + "\n".join(c_lines if c_lines else ["• Siehe SWS-Spezifikationen des Clusters"])
            )
            return {"reply": reply, "suggestion": None, "rationale": "", "mode": "mock"}

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


def _agent_bridge():
    if os.environ.get("AI_DISCUSS_OFFLINE") == "1":
        return None
    try:
        import ai_agent_bridge as ab
        return ab
    except Exception:
        try:
            from tools import ai_agent_bridge as ab
            return ab
        except Exception:
            try:
                import _src.tools.ai_agent_bridge as ab
                return ab
            except Exception:
                return None


def _build_discuss_prompt(message: str, context: dict) -> str:
    rec_id = context.get("record_id", "")
    univ = context.get("universe", "AUTOSAR Classic")
    mod = context.get("module", "")
    req_text = str(context.get("requirement_text") or "")[:4000]
    diagram_text = str(context.get("diagram_text") or "")[:2000]
    cites = ", ".join(str(c.get("id") or c.get("document") or "") for c in (context.get("cited_references") or []))

    prompt_parts = [
        "Du bist der AUTOSAR-KI-Experte im Dokumentationsportal Autodocs.",
        "Der Benutzer diskutiert mit dir über folgenden Kontext:",
        f"- ID / Element: {rec_id}",
        f"- Universum: {univ}",
        f"- Modul / Cluster: {mod}",
        f"- Inhalt / Spezifikation / Guide:\n{req_text}",
    ]
    if diagram_text:
        prompt_parts.append(f"- Sequenzdiagramm-Schritte:\n{diagram_text}")
    if cites:
        prompt_parts.append(f"- Referenzen: {cites}")

    prompt_parts.extend([
        "",
        f"Benutzer-Nachricht:\n\"{message.strip()}\"",
        "",
        "Instruktionen für deine Antwort:",
        "1. Antworte fachlich fundiert, sachlich, präzise und auf Deutsch.",
        "2. Beantworte Fragen offen und direkt: Erkläre Zusammenhänge, zeige Abhängigkeiten auf oder erläutere SWS-Anforderungen.",
        "3. Keine Einengung / kein Tunnelblick auf Fehlersuche: Ein Gespräch kann eine reine Wissensabfrage, Architekturerklärung, Validierung oder ein allgemeiner technischer Diskurs sein.",
        "4. Eskalation in ein Review-Finding: Falls der Nutzer explizit ein Review-Finding wünscht (z. B. 'Leg das als Finding an', 'Eskalieren', 'Erstelle ein Review-Ticket') ODER wenn sich im Dialog ein tatsächlicher, belegbarer Fehler oder eine Inkonsistenz in der Dokumentation/im Diagramm herausstellt und du eine formale Korrektur für geboten hältst, formuliere am Ende deiner Antwort einen strukturierten Block:",
        "   [REVIEW-FINDING]",
        "   Titel: <Kurzer, präziser Titel des Befunds>",
        "   Schweregrad: <Kritisch | Mittel | Niedrig | Hinweis>",
        "   Betroffenes Element: <ID / Modul / Diagrammschritt>",
        "   Befund & Begründung: <Konkrete Abweichung zur SWS-Norm>",
        "   Empfohlene Korrektur: <Konkreter Änderungsvorschlag>",
        "   [ENDE-REVIEW-FINDING]",
        "   Dieser Block wird vom System automatisch erkannt und dem Nutzer als 1-Klick-Aktion 'Als Review-Finding anlegen' angeboten.",
        "5. Formatiere die Antwort übersichtlich in 2-4 Absätzen oder Aufzählungspunkten.",
    ])
    return "\n".join(prompt_parts)


def _extract_finding_from_reply(out: str, message: str, rec_id: str) -> tuple[Optional[str], str, Optional[dict]]:
    """Detect if reply contains a formal [REVIEW-FINDING] or if user requested/discussed a complaint."""
    finding_dict = None
    suggestion = None
    rationale = ""
    lower_msg = message.lower()

    m_find = re.search(r"\[REVIEW-FINDING\](.*?)\[(?:ENDE-REVIEW-FINDING|/REVIEW-FINDING)\]", out, re.DOTALL | re.IGNORECASE)
    if m_find:
        raw_find = m_find.group(1).strip()
        suggestion = f"[REVIEW-FINDING für {rec_id}]\n" + raw_find
        rationale = f"Als Review-Finding im KI-Diskurs eskaliert: {message.strip()[:200]}"
        finding_dict = {
            "title": f"Review-Finding: {rec_id}",
            "body": raw_find,
            "target": rec_id,
        }
    elif any(w in lower_msg for w in ("finding", "review-ticket", "ticket", "eskalier", "falsch", "korrektur", "fehler", "mangel", "ändern", "ausschließen", "entfernen", "stimmt nicht")):
        suggestion = f"[KORREKTUR-VORSCHLAG für {rec_id}]\n" + out.strip()[:600]
        rationale = f"Im Diskussionsdialog mit KI erörtert: {message.strip()[:200]}"
        finding_dict = {
            "title": f"Review-Finding: {rec_id}",
            "body": suggestion,
            "target": rec_id,
        }

    return suggestion, rationale, finding_dict


def _live_ai_reply(message: str, context: dict) -> Optional[dict]:
    ab = _agent_bridge()
    if not ab:
        return None

    try:
        subs = ab.check_subscriptions()
    except Exception:
        return None

    has_gemini = subs.get("gemini", {}).get("available")
    has_cursor = subs.get("cursor", {}).get("available")
    if not (has_gemini or has_cursor):
        return None

    status = ab.get_health_status()
    active_prov = status.get("active_provider") or ("agy" if has_gemini else "cursor")
    rec_id = context.get("record_id", "")
    prompt = _build_discuss_prompt(message, context)

    prov_order = ["agy", "cursor"] if active_prov == "agy" else ["cursor", "agy"]
    for prov in prov_order:
        if prov == "agy" and has_gemini:
            cli = subs["gemini"]["cli_path"] or "agy"
            agy_info = status.get("providers", {}).get("agy", {})
            model_name = agy_info.get("model") or "gemini-3.8-flash-medium"
            effort = agy_info.get("thinking_effort") or "medium"
            cmd = [cli, "--model", model_name, "--effort", effort, "--dangerously-skip-permissions", "-p", prompt]
            ok, out = ab._run_cli_prompt(cmd, timeout=60)
            if ok and out and out.strip():
                suggestion, rationale, finding_dict = _extract_finding_from_reply(out, message, rec_id)
                return {
                    "reply": out.strip(),
                    "suggestion": suggestion,
                    "rationale": rationale,
                    "finding": finding_dict,
                    "provider": "agy",
                    "model": model_name,
                    "mode": "live",
                }
        elif prov == "cursor" and has_cursor:
            cli = subs["cursor"]["cli_path"] or "agent"
            model_name = status.get("providers", {}).get("cursor", {}).get("model") or "composer-2.5"
            cmd = [cli, "--print", "--trust", "--mode", "ask", "--model", model_name, prompt]
            ok, out = ab._run_cli_prompt(cmd, timeout=60)
            if ok and out and out.strip():
                suggestion, rationale, finding_dict = _extract_finding_from_reply(out, message, rec_id)
                return {
                    "reply": out.strip(),
                    "suggestion": suggestion,
                    "rationale": rationale,
                    "finding": finding_dict,
                    "provider": "cursor",
                    "model": "composer-2.5",
                    "mode": "live",
                }

    return None


def stream_discuss_reply(message: str, context: dict, min_hz: float = 4.0):
    """Generator yielding streaming SSE events at >= min_hz (default 4.0 Hz) for a discuss chat message."""
    ab = _agent_bridge()
    rec_id = context.get("record_id", "")
    prompt = _build_discuss_prompt(message, context)

    if not ab:
        fallback = contextual_reply(message, context)
        reply_txt = fallback.get("reply") or ""
        words = reply_txt.split(" ")
        chunk_sz = max(1, len(words) // 8)
        t0 = time.monotonic()
        for i in range(0, len(words), chunk_sz):
            yield {
                "event": "delta",
                "delta": " ".join(words[i:i+chunk_sz]) + " ",
                "elapsed_ms": int((time.monotonic() - t0) * 1000),
                "hz": min_hz,
            }
            time.sleep(1.0 / max(min_hz, 1.0))
        yield {
            "event": "complete",
            "ok": True,
            "reply": reply_txt,
            "suggestion": fallback.get("suggestion"),
            "rationale": fallback.get("rationale", ""),
            "mode": "offline",
            "total_updates": len(words) // chunk_sz + 1,
            "effective_hz": min_hz,
        }
        return

    try:
        subs = ab.check_subscriptions()
    except Exception:
        subs = {}

    has_gemini = subs.get("gemini", {}).get("available", False)
    has_cursor = subs.get("cursor", {}).get("available", False)

    if not (has_gemini or has_cursor):
        fallback = contextual_reply(message, context)
        reply_txt = fallback.get("reply") or ""
        words = reply_txt.split(" ")
        chunk_sz = max(1, len(words) // 8)
        t0 = time.monotonic()
        for i in range(0, len(words), chunk_sz):
            yield {
                "event": "delta",
                "delta": " ".join(words[i:i+chunk_sz]) + " ",
                "elapsed_ms": int((time.monotonic() - t0) * 1000),
                "hz": min_hz,
            }
            time.sleep(1.0 / max(min_hz, 1.0))
        yield {
            "event": "complete",
            "ok": True,
            "reply": reply_txt,
            "suggestion": fallback.get("suggestion"),
            "rationale": fallback.get("rationale", ""),
            "mode": "offline",
            "total_updates": len(words) // chunk_sz + 1,
            "effective_hz": min_hz,
        }
        return

    status = ab.get_health_status()
    active_prov = status.get("active_provider") or ("agy" if has_gemini else "cursor")
    prov_order = ["agy", "cursor"] if active_prov == "agy" else ["cursor", "agy"]

    for prov in prov_order:
        if prov == "agy" and has_gemini:
            cli = subs["gemini"]["cli_path"] or "agy"
            agy_info = status.get("providers", {}).get("agy", {})
            model_name = agy_info.get("model") or "gemini-3.8-flash-medium"
            effort = agy_info.get("thinking_effort") or "medium"
            cmd = ab.build_stream_cmd("agy", cli, model_name, effort=effort, prompt=prompt)
            for ev in ab.stream_agent_cli(cmd, provider="agy", min_hz=min_hz):
                if ev.get("event") == "complete":
                    out = ev.get("output", "")
                    suggestion, rationale, finding_dict = _extract_finding_from_reply(out, message, rec_id)
                    yield {
                        "event": "complete",
                        "ok": True,
                        "reply": out,
                        "suggestion": suggestion,
                        "rationale": rationale,
                        "finding": finding_dict,
                        "provider": "agy",
                        "model": model_name,
                        "mode": "live",
                        "total_updates": ev.get("total_updates", 0),
                        "effective_hz": ev.get("effective_hz", min_hz),
                    }
                    return
                else:
                    yield ev
            return
        elif prov == "cursor" and has_cursor:
            cli = subs["cursor"]["cli_path"] or "agent"
            model_name = status.get("providers", {}).get("cursor", {}).get("model") or "composer-2.5"
            cmd = ab.build_stream_cmd("cursor", cli, model_name, prompt=prompt)
            for ev in ab.stream_agent_cli(cmd, provider="cursor", min_hz=min_hz):
                if ev.get("event") == "complete":
                    out = ev.get("output", "")
                    suggestion, rationale, finding_dict = _extract_finding_from_reply(out, message, rec_id)
                    yield {
                        "event": "complete",
                        "ok": True,
                        "reply": out,
                        "suggestion": suggestion,
                        "rationale": rationale,
                        "finding": finding_dict,
                        "provider": "cursor",
                        "model": model_name,
                        "mode": "live",
                        "total_updates": ev.get("total_updates", 0),
                        "effective_hz": ev.get("effective_hz", min_hz),
                    }
                    return
                else:
                    yield ev
            return

    return None


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
        attached_ids = payload.get("attached_ids") or payload.get("attached_records") or []
        if isinstance(attached_ids, list) and attached_ids:
            attached_items = []
            for aid in attached_ids:
                if str(aid).strip():
                    try:
                        ctx = package_context(src, str(aid).strip())
                        if ctx.get("found"):
                            attached_items.append(ctx)
                    except Exception:
                        pass
            if attached_items:
                context["attached_items"] = attached_items
        if action == "context":
            return 200, {"ok": True, "mode": "live", "context": context}
        if action == "chat":
            message = payload.get("message")
            if not isinstance(message, str) or not message.strip():
                raise DiscussError("empty-message")
            reply = None
            if message.strip() not in QUICK_PROMPTS:
                reply = _live_ai_reply(message, context)
            if not reply or not reply.get("reply"):
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
