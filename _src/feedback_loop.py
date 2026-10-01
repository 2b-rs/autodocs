#!/usr/bin/env python3
"""Regenerate local AI-comment sidecars from the demonstration feedback queue.

The loop reads ``_src/spec/feedback-queue/{open,proposals,decisions}`` and
writes only ``comments`` and ``rendered`` beneath that same queue. A page
path cited by feedback is quoted inside the comment. It is never opened
for writing, renamed, or deleted.

No external model is called. Comment text is a bounded restatement of the
stored feedback plus curator decisions already recorded as envelopes.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

QUEUE_REL = Path("_src") / "spec" / "feedback-queue"
COMMENT_LIMIT = 100
TEXT_LIMIT = 4000

STEREOTYPES: Tuple[str, ...] = (
    "foundation",
    "service",
    "platform",
    "protocol",
    "unspecified",
)
DECISIONS: Tuple[str, ...] = (
    "accept",
    "reject",
    "change_stereotype",
    "delete_mapping",
)

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def inside(root: Path, path: Path) -> Path:
    """Return ``path`` resolved, or raise ``ValueError`` if it leaves ``root``."""
    root_resolved = root.resolve()
    resolved = path.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError("path escapes repository")
    return resolved


def queue_dir(root: Path, *parts: str) -> Path:
    root_resolved = root.resolve()
    return inside(root_resolved, root_resolved.joinpath(QUEUE_REL, *parts))


def safe_name(value: str, fallback: str) -> str:
    cleaned = _SAFE.sub("-", str(value)).strip(".-_")[:80]
    return cleaned or fallback


def atomic_write(root: Path, path: Path, text: str) -> None:
    """Atomically replace ``path`` with ``text``. ``path`` must stay inside ``root``."""
    destination = inside(root, path)
    parent = inside(root, destination.parent)
    parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".tmp-", suffix=".partial", dir=parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def read_json_objects(directory: Path) -> Tuple[List[Tuple[Path, Dict[str, Any]]], List[Dict[str, str]]]:
    items: List[Tuple[Path, Dict[str, Any]]] = []
    errors: List[Dict[str, str]] = []
    if not directory.exists():
        return items, errors
    if directory.is_symlink() or not directory.is_dir():
        errors.append({"path": directory.name, "error": "not a directory"})
        return items, errors
    files = sorted(
        child
        for child in directory.iterdir()
        if child.is_file()
        and not child.is_symlink()
        and child.suffix == ".json"
        and not child.name.startswith(".")
    )
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append({"path": path.name, "error": type(exc).__name__})
            continue
        if not isinstance(data, dict):
            errors.append({"path": path.name, "error": "JSON object required"})
            continue
        items.append((path, data))
    return items, errors


def comment_body(source: Mapping[str, Any]) -> str:
    text = str(source.get("feedback_text") or "").strip()
    context = source.get("demo_context")
    context = context if isinstance(context, dict) else {}
    page = str(context.get("page") or "")
    universe = str(context.get("universe") or "")
    component = str(context.get("component_id") or "")
    parts = [
        "Neu erzeugter KI-Kommentar aus der lokalen Feedback-Schleife.",
        "Grundlage ist nur das gespeicherte Feedback. Es wurde kein externes Modell aufgerufen.",
    ]
    if universe:
        parts.append(f"Universum: {universe}.")
    if component:
        parts.append(f"Komponente: {component}.")
    if page:
        parts.append(f"Zitierte Seite: {page}. Diese Datei wurde nicht verändert.")
    parts.append("Feedback: " + text[:TEXT_LIMIT])
    return " ".join(parts)


def _targets(comment: Mapping[str, Any]) -> set:
    return {
        str(comment.get("source_id") or ""),
        str(comment.get("component_id") or ""),
        str(comment.get("page") or ""),
        str(comment.get("target_agent") or ""),
    }


def apply_decision(comment: Dict[str, Any], decision: Mapping[str, Any]) -> None:
    kind = decision.get("decision")
    target = str(decision.get("target_id") or "")
    if kind not in DECISIONS or not target or target not in _targets(comment):
        return
    if kind == "reject":
        comment["published"] = False
        comment["curator_disposition"] = "reject"
    elif kind == "accept":
        comment["published"] = True
        comment["curator_disposition"] = "accept"
    elif kind == "change_stereotype":
        stereotype = decision.get("stereotype")
        if stereotype in STEREOTYPES:
            comment["stereotype"] = stereotype
            comment["curator_disposition"] = "change_stereotype"
    elif kind == "delete_mapping":
        comment["mapping"] = "unbound"
        comment["curator_disposition"] = "delete_mapping"
        comment["canonical_mutation"] = False


def render_html(comment: Mapping[str, Any]) -> str:
    title = html.escape(str(comment.get("comment_id") or "comment"), quote=True)
    body = html.escape(str(comment.get("text") or ""), quote=True)
    page = html.escape(str(comment.get("page") or ""), quote=True)
    mapping = html.escape(str(comment.get("mapping") or "bound"), quote=True)
    stereotype = html.escape(str(comment.get("stereotype") or "unspecified"), quote=True)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="de">\n'
        f"<head><meta charset=\"utf-8\"><title>KI-Kommentar {title}</title></head>\n"
        "<body><main>\n"
        f"<h1>KI-Kommentar {title}</h1>\n"
        "<p>Lokale Neuerzeugung. Die zitierte Dokumentseite wurde nicht überschrieben.</p>\n"
        f"<p>Seite: {page}</p>\n"
        f"<p>Stereotyp: {stereotype}</p>\n"
        f"<p>Zuordnung: {mapping}</p>\n"
        f"<p>{body}</p>\n"
        "</main></body></html>\n"
    )


def _feedback_sources(
    items: Sequence[Tuple[Path, Dict[str, Any]]],
    errors: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []
    for path, data in items:
        schema = str(data.get("schema") or "")
        if schema and not schema.startswith("agent-profile-feedback"):
            errors.append({"path": path.name, "error": "unexpected schema"})
            continue
        if not str(data.get("feedback_text") or "").strip():
            errors.append({"path": path.name, "error": "missing feedback_text"})
            continue
        sources.append(data)
    return sources


def _proposal_sources(
    items: Sequence[Tuple[Path, Dict[str, Any]]],
    errors: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []
    for path, data in items:
        if data.get("schema") != "demo-discuss-proposal@v1":
            errors.append({"path": path.name, "error": "unexpected proposal schema"})
            continue
        proposal = data.get("proposal")
        proposal = proposal if isinstance(proposal, dict) else {}
        text = str(proposal.get("text") or "").strip()
        if not text:
            errors.append({"path": path.name, "error": "missing proposal text"})
            continue
        context = data.get("context")
        context = context if isinstance(context, dict) else {}
        sources.append(
            {
                "schema": "demo-discuss-proposal@v1",
                "envelope_id": data.get("proposal_id"),
                "feedback_text": text,
                "target_agent": "discuss",
                "demo_context": {
                    "page": str(context.get("page") or ""),
                    "universe": str(context.get("universe") or ""),
                    "component_id": str(context.get("component_id") or ""),
                },
            }
        )
    return sources


def run(repo: Path, limit: int = COMMENT_LIMIT) -> Dict[str, Any]:
    """Rebuild comment sidecars. Never returns a write path outside the queue."""
    root = repo.expanduser().resolve()
    if not root.is_dir():
        return {
            "ok": False,
            "error": "repository is not a directory",
            "canonical_mutation": False,
        }
    try:
        open_dir = queue_dir(root, "open")
        proposal_dir = queue_dir(root, "proposals")
        decision_dir = queue_dir(root, "decisions")
        comment_dir = queue_dir(root, "comments")
        rendered_dir = queue_dir(root, "rendered")
    except ValueError:
        return {
            "ok": False,
            "error": "queue path is not inside the repository",
            "canonical_mutation": False,
        }
    if open_dir.exists() and (open_dir.is_symlink() or not open_dir.is_dir()):
        return {
            "ok": False,
            "error": "feedback open queue is not a real directory",
            "canonical_mutation": False,
        }

    feedback_items, errors = read_json_objects(open_dir)
    proposals, proposal_errors = read_json_objects(proposal_dir)
    decisions, decision_errors = read_json_objects(decision_dir)
    errors.extend(proposal_errors)
    errors.extend(decision_errors)
    if any(item["error"] == "not a directory" for item in proposal_errors + decision_errors):
        return {
            "ok": False,
            "error": "queue path is not a real directory",
            "canonical_mutation": False,
            "errors": errors,
        }

    sources = _feedback_sources(feedback_items, errors)
    proposal_sources = _proposal_sources(proposals, errors)
    processed_feedback = len(sources)
    processed_proposals = len(proposal_sources)
    sources.extend(proposal_sources)
    truncated = len(sources) > limit
    if truncated:
        sources = sources[:limit]

    decision_rows = [
        data
        for _path, data in decisions
        if data.get("schema") == "demo-curator-decision@v1"
    ]
    written: List[str] = []
    rebuilt: List[str] = []
    suppressed: List[str] = []
    for source in sources:
        source_id = str(source.get("envelope_id") or "item")
        context = source.get("demo_context")
        context = context if isinstance(context, dict) else {}
        comment_id = "c-" + safe_name(source_id, "item")
        comment: Dict[str, Any] = {
            "schema": "demo-ai-comment@v1",
            "comment_id": comment_id,
            "source_id": source_id,
            "target_agent": source.get("target_agent"),
            "component_id": str(context.get("component_id") or ""),
            "page": str(context.get("page") or ""),
            "universe": str(context.get("universe") or ""),
            "stereotype": "unspecified",
            "mapping": "bound",
            "published": True,
            "canonical_mutation": False,
            "generated_at": _now(),
            "generator": "local-feedback-loop",
            "model": None,
            "text": comment_body(source),
        }
        for decision in decision_rows:
            apply_decision(comment, decision)
        comment_path = comment_dir / f"{comment_id}.json"
        try:
            atomic_write(
                root,
                comment_path,
                json.dumps(comment, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
        except (OSError, ValueError) as exc:
            errors.append({"path": comment_id + ".json", "error": type(exc).__name__})
            continue
        written.append(comment_path.relative_to(root).as_posix())
        if comment["published"]:
            page_path = rendered_dir / f"{comment_id}.html"
            try:
                atomic_write(root, page_path, render_html(comment))
            except (OSError, ValueError) as exc:
                errors.append({"path": comment_id + ".html", "error": type(exc).__name__})
                continue
            rebuilt.append(page_path.relative_to(root).as_posix())
        else:
            suppressed.append(comment_id)

    return {
        "ok": True,
        "canonical_mutation": False,
        "processed_feedback": processed_feedback,
        "processed_proposals": processed_proposals,
        "comments_written": len(written),
        "pages_rebuilt": rebuilt,
        "suppressed": suppressed,
        "truncated": truncated,
        "errors": errors,
        "written": written,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate demonstration AI comments from the feedback queue.",
    )
    parser.add_argument("--repo", required=True)
    parser.add_argument("--limit", type=int, default=COMMENT_LIMIT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.limit < 1 or args.limit > COMMENT_LIMIT:
        summary: Dict[str, Any] = {
            "ok": False,
            "error": "limit must be between 1 and 100",
            "canonical_mutation": False,
        }
        code = 1
    else:
        summary = run(Path(args.repo), limit=args.limit)
        code = 0 if summary.get("ok") else 1
    json.dump(summary, sys.stdout, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
