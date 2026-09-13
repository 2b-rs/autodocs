#!/usr/bin/env python3
"""Pretty-print local issue status pages for the canonical issue store.

``python3 -m http.server`` lists ``issues/0037/`` as a naked directory because
canonical items are ``index.md``, not ``index.html``.  This previewer intercepts
those URLs and renders a status page from the item plus the generated catalog.
It never writes into ``issues/``; generated HTML is not a second authority.

CLI:
    _src/serve.sh
    python3 _src/tools/issue_preview.py serve --port 8100
    python3 _src/tools/issue_preview.py render --id 0037
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse

TOOLS = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


views = _load("issue_views", TOOLS / "issue_views.py")
STORE = views.STORE
IssueStoreError = STORE.IssueStoreError

FEATURE_ID = re.compile(r"^[0-9]{4}$")
ITEM_ID = re.compile(r"^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$")
PREVIEW_PATH = re.compile(
    r"^/issues/(?:(?P<feature>[0-9]{4})(?:/(?P<item>[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?))?)?/?$"
)
INLINE_CODE = re.compile(r"`([^`]+)`")
INLINE_BOLD = re.compile(r"\*\*(.+?)\*\*")
INLINE_TOKEN = re.compile(
    r"(?P<img>!\[(?P<img_alt>[^\]]*)\]\((?P<img_src>[^)]+)\))"
    r"|(?P<link>\[(?P<link_text>[^\]]+)\]\((?P<link_href>[^)]+)\))"
    r"|(?P<code>`(?P<code_text>[^`]+)`)"
    r"|(?P<bold>\*\*(?P<bold_text>.+?)\*\*)"
)
HEADING_LINE = re.compile(r"^(#{1,6})\s+(.*)$")
HR_LINE = re.compile(r"^\s*(?:(?:-\s*){3,}|(?:\*\s*){3,}|(?:_\s*){3,})\s*$")
UL_LINE = re.compile(r"^(\s*)([-*+])\s+(.*)$")
OL_LINE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
TASK_LINE = re.compile(r"^\[([ xXpP?uUwW])\]\s+(.*)$")
FENCE_LINE = re.compile(r"^```([^`]*)$")
MAX_MARKDOWN_BYTES = 2 * 1024 * 1024
MARKDOWN_SUFFIXES = (".md", ".markdown", ".mdown")
STATE_LABELS = {
    "open": "Open",
    "in_progress": "In progress",
    "blocked": "Blocked",
    "closed": "Closed",
    "malformed": "Malformed",
    "legacy-unverified": "Legacy terminal · unverified",
}
LEGACY_UNVERIFIED_LABEL = "legacy-terminal-unverified"
LABELS_BLOCK = re.compile(r"^labels:\n((?:[ \t]+- .+\n)*)", re.M)
LABEL_ENTRY = re.compile(r'^[ \t]+-[ \t]+"?([^"\n]+)"?[ \t]*$', re.M)
PAGE_STYLE = """
.issue-preview { --ok:#2F6B3A; --warn:#8A5A00; --bad:#8B1E1E; }
.issue-preview .hero { background:var(--surface); border:1px solid var(--border);
  border-radius:12px; padding:18px 20px; margin:0 0 22px; }
.issue-preview .hero h1 { margin:6px 0 10px; }
.issue-preview .chips { display:flex; flex-wrap:wrap; gap:8px; margin:0 0 12px; }
.issue-preview .chip { display:inline-block; border-radius:999px; padding:2px 10px;
  font-size:12px; letter-spacing:.04em; text-transform:uppercase; font-weight:650; }
.issue-preview .chip-open { background:#EEECE6; color:#5C5A54; }
.issue-preview .chip-in_progress { background:#01696F; color:#fff; }
.issue-preview .chip-blocked { background:#8B1E1E; color:#fff; }
.issue-preview .chip-closed { background:#2F6B3A; color:#fff; }
.issue-preview .chip-legacy-unverified { background:#8A5A00; color:#fff; }
.issue-preview .chip-closed-archived-not-accepted,
.issue-preview .chip-closed-wontfix,
.issue-preview .chip-closed-superseded,
.issue-preview .chip-closed-duplicate,
.issue-preview .chip-closed-cancelled { background:#5C5A54; color:#fff; }
.issue-preview .chip-malformed { background:#8B1E1E; color:#fff; }
.issue-preview .chip-active { background:#EEECE6; color:#5C5A54; }
.issue-preview .chip-checked { background:#2F6B3A; color:#fff; }
.issue-preview .chip-level, .issue-preview .chip-meta { background:#E4EEF0; color:#0C4E54; }
.issue-preview .counts { display:flex; flex-wrap:wrap; gap:10px 18px; color:var(--muted); font-size:14px; }
.issue-preview .counts strong { color:var(--text); font-variant-numeric:tabular-nums; }
.issue-preview .meter { display:flex; height:8px; background:#E6E4DE; border-radius:99px;
  overflow:hidden; margin:12px 0 0; }
.issue-preview .meter span { display:block; height:100%; }
.issue-preview .meter .seg-closed { background:#2F6B3A; }
.issue-preview .meter .seg-unverified { background:#8A5A00; }
.issue-preview .notice { background:#F7F0E0; border:1px solid #E0D2A8; border-radius:10px;
  padding:12px 14px; margin:0 0 16px; }
.issue-preview table.items { width:100%; border-collapse:collapse; font-size:14px; }
.issue-preview table.items th { text-align:left; font-size:12px; color:var(--muted);
  border-bottom:1px solid var(--border); padding:8px 10px; }
.issue-preview table.items td { border-bottom:1px solid var(--border); padding:8px 10px; vertical-align:top; }
.issue-preview tr.sub td:first-child { padding-left:28px; color:var(--muted); }
.issue-preview .note { color:var(--muted); font-size:13px; }
.issue-preview .error { background:#F8EAEA; border:1px solid #E3B6B6; border-radius:10px; padding:12px 14px; }
.issue-preview .body p { margin:0 0 10px; }
.issue-preview ul.ac { list-style:none; padding:0; margin:0; }
.issue-preview ul.ac li { background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:10px 12px; margin:0 0 8px; }
.issue-preview .frontmatter { background:var(--surface); border:1px solid var(--border);
  border-radius:10px; padding:12px 14px; margin:0 0 22px; }
.issue-preview .frontmatter summary { cursor:pointer; color:var(--muted); font-size:13px; }
.issue-preview .md-body h1 { font-size:26px; margin:8px 0 12px; }
.issue-preview .md-body h2 { font-size:20px; margin:28px 0 10px; padding-bottom:6px;
  border-bottom:2px solid var(--primary); }
.issue-preview .md-body h3 { font-size:17px; margin:20px 0 8px; }
.issue-preview .md-body pre { background:#1C1B19; color:#CDCCCA; padding:12px 14px;
  border-radius:8px; overflow-x:auto; }
.issue-preview .md-body blockquote { margin:0 0 12px; padding:4px 0 4px 14px;
  border-left:3px solid var(--primary); color:var(--muted); }
.issue-preview .md-body table { border-collapse:collapse; margin:10px 0 16px; width:100%; }
.issue-preview .md-body th, .issue-preview .md-body td {
  border:1px solid var(--border); padding:6px 10px; vertical-align:top; }
.issue-preview .md-body th { background:var(--surface2); color:var(--muted); text-align:left; }
.issue-preview .task { display:inline-block; width:1.05em; text-align:center;
  margin-right:.35em; font-weight:700; }
.issue-preview .task-open::before { content:"☐"; }
.issue-preview .task-done::before { content:"☑"; color:#2F6B3A; }
.issue-preview .task-progress::before { content:"◐"; color:#01696F; }
.issue-preview .task-blocked::before { content:"⛔"; }
.issue-preview .task-unknown::before { content:"❓"; }
.issue-preview .task-wontfix::before { content:"☒"; color:#5C5A54; }
"""


def e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def short_title(text: Optional[str], limit: int = 140) -> str:
    line = (text or "").strip().splitlines()[0] if text else ""
    if len(line) <= limit:
        return line
    return line[: limit - 1].rstrip() + "…"


def format_inline(text: str) -> str:
    escaped = e(text)
    escaped = INLINE_CODE.sub(r"<code>\1</code>", escaped)
    return INLINE_BOLD.sub(r"<strong>\1</strong>", escaped)


def format_body(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return '<p class="note">No text.</p>'
    blocks: List[str] = []
    list_items: List[str] = []

    def flush_list() -> None:
        if list_items:
            items = "".join(f"<li>{format_inline(item)}</li>" for item in list_items)
            blocks.append(f"<ul>{items}</ul>")
            list_items.clear()

    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("- "):
            list_items.append(stripped[2:])
            continue
        flush_list()
        if stripped:
            blocks.append(f"<p>{format_inline(stripped)}</p>")
    flush_list()
    return "".join(blocks) or '<p class="note">No text.</p>'


def is_markdown_path(path: str) -> bool:
    return Path(urlparse(path).path).name.lower().endswith(MARKDOWN_SUFFIXES)


def split_frontmatter_text(text: str) -> Tuple[Optional[str], str]:
    if not text.startswith("---\n"):
        return None, text
    closing = text.find("\n---\n", 4)
    if closing < 0:
        return None, text
    return text[4:closing], text[closing + 5:]


def format_rich_inline(text: str) -> str:
    out: List[str] = []
    pos = 0
    for match in INLINE_TOKEN.finditer(text):
        out.append(e(text[pos:match.start()]))
        if match.group("img") is not None:
            out.append(
                f'<img alt="{e(match.group("img_alt"))}" src="{e(match.group("img_src"))}">'
            )
        elif match.group("link") is not None:
            out.append(
                f'<a href="{e(match.group("link_href").strip())}">'
                f"{e(match.group('link_text'))}</a>"
            )
        elif match.group("code") is not None:
            out.append(f"<code>{e(match.group('code_text'))}</code>")
        else:
            out.append(f"<strong>{e(match.group('bold_text'))}</strong>")
        pos = match.end()
    out.append(e(text[pos:]))
    return "".join(out)


def _task_span(mark: str) -> str:
    kind = {
        " ": "open", "x": "done", "p": "progress", "?": "unknown",
        "u": "blocked", "w": "wontfix",
    }.get(mark.lower(), "open")
    return f'<span class="task task-{kind}" aria-hidden="true"></span>'


def _list_item_html(text: str) -> str:
    task = TASK_LINE.match(text)
    if task:
        return _task_span(task.group(1)) + format_rich_inline(task.group(2))
    return format_rich_inline(text)


def _is_table_row(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _is_table_divider(line: str) -> bool:
    stripped = line.strip()
    if not _is_table_row(stripped):
        return False
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def _table_cells(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _collect_list(lines: List[str], start: int) -> Tuple[str, int]:
    items: List[Tuple[int, str, str]] = []
    index = start
    while index < len(lines):
        unordered = UL_LINE.match(lines[index])
        ordered = OL_LINE.match(lines[index])
        if unordered:
            indent, _, text = unordered.group(1), unordered.group(2), unordered.group(3)
            kind = "ul"
        elif ordered:
            indent, _, text = ordered.group(1), ordered.group(2), ordered.group(3)
            kind = "ol"
        else:
            break
        depth = len(indent.expandtabs(4)) // 2
        items.append((depth, kind, text))
        index += 1
        while index < len(lines):
            nxt = lines[index]
            if not nxt.strip():
                break
            if UL_LINE.match(nxt) or OL_LINE.match(nxt) or HEADING_LINE.match(nxt) or FENCE_LINE.match(nxt):
                break
            if nxt.startswith("    ") or nxt.startswith("\t"):
                items[-1] = (items[-1][0], items[-1][1], items[-1][2] + " " + nxt.strip())
                index += 1
                continue
            break
    html_parts: List[str] = []
    stack: List[Tuple[int, str]] = []

    def close_to(depth: int) -> None:
        while stack and stack[-1][0] >= depth:
            html_parts.append(f"</{stack.pop()[1]}>")

    for depth, kind, text in items:
        if not stack or depth > stack[-1][0]:
            html_parts.append(f"<{kind}>")
            stack.append((depth, kind))
        elif depth < stack[-1][0] or kind != stack[-1][1]:
            close_to(depth)
            if not stack or stack[-1][1] != kind or stack[-1][0] != depth:
                html_parts.append(f"<{kind}>")
                stack.append((depth, kind))
        html_parts.append(f"<li>{_list_item_html(text)}</li>")
    close_to(-1)
    return "".join(html_parts), index


def markdown_to_html(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: List[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        fence = FENCE_LINE.match(line)
        if fence:
            lang = fence.group(1).strip()
            index += 1
            buf: List[str] = []
            while index < len(lines) and not lines[index].startswith("```"):
                buf.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            klass = f' class="language-{e(lang)}"' if lang else ""
            blocks.append(f"<pre><code{klass}>{e(chr(10).join(buf))}</code></pre>")
            continue
        heading = HEADING_LINE.match(line)
        if heading:
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{format_rich_inline(heading.group(2).rstrip())}</h{level}>")
            index += 1
            continue
        if HR_LINE.match(line) and line.strip():
            blocks.append("<hr>")
            index += 1
            continue
        if line.lstrip().startswith(">"):
            quote: List[str] = []
            while index < len(lines) and lines[index].lstrip().startswith(">"):
                quote.append(re.sub(r"^>\s?", "", lines[index].lstrip()))
                index += 1
            inner = markdown_to_html("\n".join(quote))
            blocks.append(f"<blockquote>{inner}</blockquote>")
            continue
        if index + 1 < len(lines) and _is_table_row(line) and _is_table_divider(lines[index + 1]):
            headers = _table_cells(line)
            index += 2
            rows: List[str] = []
            while index < len(lines) and _is_table_row(lines[index]):
                cells = _table_cells(lines[index])
                padded = cells + [""] * max(0, len(headers) - len(cells))
                tds = "".join(f"<td>{format_rich_inline(cell)}</td>" for cell in padded[:len(headers)])
                rows.append(f"<tr>{tds}</tr>")
                index += 1
            ths = "".join(f"<th>{format_rich_inline(cell)}</th>" for cell in headers)
            blocks.append(f"<table><thead><tr>{ths}</tr></thead><tbody>{''.join(rows)}</tbody></table>")
            continue
        if UL_LINE.match(line) or OL_LINE.match(line):
            html, index = _collect_list(lines, index)
            blocks.append(html)
            continue
        if not line.strip():
            index += 1
            continue
        para = [line]
        index += 1
        while index < len(lines):
            nxt = lines[index]
            if not nxt.strip():
                break
            if (HEADING_LINE.match(nxt) or FENCE_LINE.match(nxt) or HR_LINE.match(nxt)
                    or UL_LINE.match(nxt) or OL_LINE.match(nxt) or nxt.lstrip().startswith(">")):
                break
            para.append(nxt)
            index += 1
        blocks.append(f"<p>{format_rich_inline(' '.join(part.strip() for part in para))}</p>")
    return "\n".join(blocks)


def markdown_title(text: str, fallback: str) -> str:
    _, body = split_frontmatter_text(text)
    for line in body.splitlines():
        heading = HEADING_LINE.match(line)
        if heading:
            return heading.group(2).strip()
        if line.strip():
            return short_title(line.strip(), 80) or fallback
    return fallback


def path_crumbs(url_path: str) -> str:
    parts = [part for part in url_path.split("/") if part]
    crumbs = ['<a href="/">Start</a>']
    acc = ""
    for index, part in enumerate(parts):
        acc += "/" + part
        if index == len(parts) - 1:
            crumbs.append(e(part))
        else:
            href = acc + ("/" if not part.lower().endswith(MARKDOWN_SUFFIXES) else "")
            crumbs.append(f'<a href="{e(href)}">{e(part)}</a>')
    return " / ".join(crumbs)


def render_markdown_page(text: str, *, url_path: str, filename: str) -> str:
    frontmatter, body = split_frontmatter_text(text)
    title = markdown_title(body, filename)
    parts = []
    if frontmatter is not None:
        parts.append(
            "<details class=\"frontmatter\" open><summary>Frontmatter</summary>"
            f"<pre>{e(frontmatter.strip())}</pre></details>"
        )
    parts.append(f'<article class="md-body">{markdown_to_html(body)}</article>')
    footer = f'Rendered from <code>{e(filename)}</code>. <a href="?raw=1">View source</a>'
    return document(title, path_crumbs(url_path), "".join(parts), footer=footer)


def match_preview_path(path: str) -> Optional[Tuple[str, Optional[str]]]:
    parsed = urlparse(path)
    match = PREVIEW_PATH.fullmatch(parsed.path)
    if not match:
        return None
    feature = match.group("feature")
    item = match.group("item")
    if item:
        if not item.startswith(feature + "-"):
            return None
        return "item", item
    if feature:
        return "item", feature
    return "index", None


def needs_slash_redirect(path: str) -> bool:
    parsed = urlparse(path)
    return bool(PREVIEW_PATH.fullmatch(parsed.path)) and not parsed.path.endswith("/")


def item_url(item_id: str, level: Optional[str] = None) -> str:
    if level is None:
        if FEATURE_ID.fullmatch(item_id):
            level = "feature"
        elif ITEM_ID.fullmatch(item_id):
            level = "task" if "." not in item_id else "subtask"
        else:
            return f"/issues/{item_id}/"
    return views.item_url(item_id, level)


def state_class(lifecycle: Optional[str], state: Optional[str]) -> str:
    token = (lifecycle or state or "open").replace(":", "-")
    return re.sub(r"[^a-z0-9_-]+", "-", token.lower())


def state_label(lifecycle: Optional[str], state: Optional[str]) -> str:
    if lifecycle and lifecycle.startswith("closed:"):
        disposition = lifecycle.split(":", 1)[1]
        return f"Closed · {disposition}"
    return STATE_LABELS.get(state or lifecycle or "", (state or lifecycle or "unknown").replace("_", " "))


def read_item_labels(path: Path) -> List[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    if not text.startswith("---\n"):
        return []
    end = text.find("\n---\n", 4)
    if end < 0:
        return []
    match = LABELS_BLOCK.search(text[4:end] + "\n")
    if not match:
        return []
    return [entry.group(1).strip() for entry in LABEL_ENTRY.finditer(match.group(1))]


def item_labels(entry: Mapping[str, Any], parsed_item: Optional[Mapping[str, Any]] = None) -> List[str]:
    for source in ((parsed_item or {}).get("labels"), entry.get("labels")):
        if isinstance(source, list):
            return [str(value) for value in source]
    return []


def is_legacy_unverified(entry: Mapping[str, Any], parsed_item: Optional[Mapping[str, Any]] = None) -> bool:
    state = str(entry.get("lifecycle_status") or entry.get("state") or "")
    if state.startswith("closed"):
        return False
    return LEGACY_UNVERIFIED_LABEL in item_labels(entry, parsed_item)


def display_state(
    entry: Mapping[str, Any], parsed_item: Optional[Mapping[str, Any]] = None
) -> Tuple[str, str]:
    if is_legacy_unverified(entry, parsed_item):
        return "legacy-unverified", STATE_LABELS["legacy-unverified"]
    return (
        state_class(entry.get("lifecycle_status"), entry.get("state")),
        state_label(entry.get("lifecycle_status"), entry.get("state")),
    )


def attach_item_labels(catalog: Mapping[str, Any], issues_root: Path) -> Dict[str, Any]:
    items = []
    for item in catalog.get("items") or []:
        labeled = dict(item)
        if not isinstance(labeled.get("labels"), list):
            item_id = labeled.get("id")
            labeled["labels"] = read_item_labels(item_index_path(issues_root, item_id)) if item_id else []
        items.append(labeled)
    attached = dict(catalog)
    attached["items"] = items
    return attached


def item_index_path(issues_root: Path, item_id: str) -> Path:
    if FEATURE_ID.fullmatch(item_id):
        return issues_root / item_id / "index.md"
    feature = item_id.split("-", 1)[0]
    return issues_root / feature / item_id / "index.md"


def _index_path(repo: Path, item_id: str) -> Path:
    return item_index_path(repo / "issues", item_id)


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"malformed": True, "path": path.as_posix()}
    return payload if isinstance(payload, dict) else {"malformed": True, "path": path.as_posix()}


def load_catalog(repo: Path, issues_root: Optional[Path] = None) -> Dict[str, Any]:
    issues_root = Path(issues_root) if issues_root else repo / "issues"
    committed = issues_root / "_views" / "catalog.json"
    if committed.is_file() and issues_root == repo / "issues":
        payload = json.loads(committed.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("schema") == "issue-catalog@v1":
            return payload
    catalog, _ = views.render(issues_root, repo)
    return catalog


def catalog_by_id(catalog: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {item["id"]: item for item in catalog.get("items") or [] if item.get("id")}


def children_of(by_id: Mapping[str, Mapping[str, Any]], parent_id: str) -> List[Dict[str, Any]]:
    kids = [item for item in by_id.values() if item.get("parent") == parent_id]
    kids.sort(key=lambda item: item.get("id") or "")
    return kids


def descendants(by_id: Mapping[str, Mapping[str, Any]], parent_id: str) -> List[Dict[str, Any]]:
    found: List[Dict[str, Any]] = []
    stack = list(children_of(by_id, parent_id))
    while stack:
        item = stack.pop(0)
        found.append(item)
        stack[0:0] = children_of(by_id, item["id"])
    return found


def count_states(items: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    counts = {
        "open": 0, "in_progress": 0, "blocked": 0, "closed": 0,
        "malformed": 0, "legacy_unverified": 0, "other": 0,
    }
    for item in items:
        state = item.get("lifecycle_status") or item.get("state") or "open"
        if is_legacy_unverified(item):
            counts["legacy_unverified"] += 1
        elif str(state).startswith("closed"):
            counts["closed"] += 1
        elif state in counts:
            counts[state] += 1
        else:
            counts["other"] += 1
    return counts


def load_item(repo: Path, item_id: str, issues_root: Optional[Path] = None) -> Dict[str, Any]:
    issues_root = Path(issues_root) if issues_root else repo / "issues"
    path = item_index_path(issues_root, item_id)
    try:
        relative = path.resolve().relative_to(Path(repo).resolve()).as_posix()
    except ValueError:
        relative = path.as_posix()
    result: Dict[str, Any] = {
        "id": item_id,
        "path": relative,
        "claim": _read_json(path.parent / "claim.json") if path.parent.is_dir() else None,
        "closure": _read_json(path.parent / "closure.json") if path.parent.is_dir() else None,
    }
    if not path.is_file():
        result["error"] = f"canonical item not found: {path}"
        return result
    try:
        parsed = STORE.parse_issue(path, issues_root=issues_root, repository_root=repo)
    except (IssueStoreError, OSError) as exc:
        result["error"] = str(exc)
        result["raw"] = path.read_text(encoding="utf-8", errors="replace")
        return result
    result["parsed"] = parsed
    return result


def _chip(kind: str, label: str) -> str:
    return f'<span class="chip chip-{e(kind)}">{e(label)}</span>'


def _meter(closed: int, unverified: int, total: int) -> str:
    if total <= 0:
        return ""
    return (
        f'<div class="meter" role="meter" aria-valuemin="0" aria-valuemax="{total}" '
        f'aria-valuenow="{closed + unverified}" aria-label="Closed and legacy-unverified children">'
        f'<span class="seg-closed" style="width:{100.0 * closed / total:.1f}%"></span>'
        f'<span class="seg-unverified" style="width:{100.0 * unverified / total:.1f}%"></span></div>'
    )


def _item_link(item_id: str, by_id: Mapping[str, Mapping[str, Any]]) -> str:
    entry = by_id.get(item_id)
    level = (entry or {}).get("level")
    href = item_url(item_id, level)
    title = (entry or {}).get("title") or ""
    label = e(item_id)
    extra = f" — {e(title[:80])}" if title else ""
    if entry:
        return f'<a href="{e(href)}"><code>{label}</code></a>{extra}'
    return f"<code>{label}</code> <span class=\"note\">(missing)</span>"


def _status_chips(entry: Mapping[str, Any], parsed_item: Optional[Mapping[str, Any]]) -> str:
    klass, label = display_state(entry, parsed_item)
    chips = [
        _chip(klass, label),
        _chip("level", (entry.get("level") or "item").replace("_", " ")),
    ]
    visibility = entry.get("visibility") or (parsed_item or {}).get("visibility")
    if visibility:
        chips.append(_chip("meta", visibility))
    work_type = (parsed_item or {}).get("work_type")
    if work_type:
        chips.append(_chip("meta", work_type))
    skip = {LEGACY_UNVERIFIED_LABEL} if klass == "legacy-unverified" else set()
    for item_label in item_labels(entry, parsed_item):
        if item_label not in skip:
            chips.append(_chip("meta", item_label))
    return f'<div class="chips">{"".join(chips)}</div>'


def _prereq_list(ids: Sequence[str], by_id: Mapping[str, Mapping[str, Any]]) -> str:
    if not ids:
        return '<p class="note">No prerequisites.</p>'
    rows = []
    for item_id in ids:
        entry = by_id.get(item_id) or {}
        klass, status = display_state(entry)
        rows.append(
            f"<tr><td>{_item_link(item_id, by_id)}</td>"
            f"<td>{_chip(klass, status)}</td></tr>"
        )
    return (
        '<table class="items"><thead><tr><th>Item</th><th>Status</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _criteria_list(parsed: Optional[Mapping[str, Any]], closure: Optional[Mapping[str, Any]]) -> str:
    criteria = list((parsed or {}).get("criteria") or [])
    checked = {}
    if isinstance(closure, dict) and not closure.get("malformed"):
        for record in closure.get("criteria") or []:
            if isinstance(record, dict) and record.get("id"):
                checked[record["id"]] = record
    if not criteria:
        return '<p class="note">No acceptance criteria.</p>'
    items = []
    for criterion in criteria:
        cid = criterion.get("id") or ""
        status = criterion.get("status") or "active"
        record = checked.get(cid)
        if record and record.get("status") == "checked":
            status = "checked"
        items.append(
            f'<li><div class="chips">{_chip(status, status)} <strong>{e(cid)}</strong></div>'
            f'<div class="body">{format_body(criterion.get("text") or "")}</div></li>'
        )
    return f'<ul class="ac">{"".join(items)}</ul>'


def _child_rows(parent_id: str, by_id: Mapping[str, Mapping[str, Any]]) -> str:
    rows: List[str] = []
    for child in children_of(by_id, parent_id):
        rows.append(_child_row(child, by_id, sub=False))
        for sub in children_of(by_id, child["id"]):
            rows.append(_child_row(sub, by_id, sub=True))
    if not rows:
        return '<p class="note">No child items.</p>'
    return (
        '<table class="items"><thead><tr><th>ID</th><th>Status</th><th>Title</th>'
        "<th>Criteria</th><th>Prerequisites</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _child_row(item: Mapping[str, Any], by_id: Mapping[str, Mapping[str, Any]], *, sub: bool) -> str:
    criteria = item.get("criteria") or []
    n = len(criteria)
    href = e(item.get("url") or item_url(item["id"], item.get("level")))
    klass = " class=\"sub\"" if sub else ""
    prereqs = ", ".join(e(value) for value in (item.get("prerequisites") or [])) or "—"
    return (
        f"<tr{klass}><td><a href=\"{href}\"><code>{e(item.get('id'))}</code></a></td>"
        f"<td>{_chip(*display_state(item))}</td>"
        f"<td>{e(short_title(item.get('title'), 110))}</td>"
        f"<td>{n}</td><td>{prereqs}</td></tr>"
    )


def _sidecar_block(title: str, payload: Optional[Mapping[str, Any]]) -> str:
    if not payload:
        return ""
    if payload.get("malformed"):
        return f"<h2 class=\"sect\">{e(title)}</h2><p class=\"error\">Malformed sidecar.</p>"
    interesting = []
    for key in ("item_id", "disposition", "closed_at", "closed_by", "reason",
                "owner", "owner_token", "state", "base_commit", "expires_at"):
        if key in payload and payload[key] not in (None, "", []):
            interesting.append(f"<tr><th>{e(key)}</th><td>{e(payload[key])}</td></tr>")
    if not interesting:
        interesting.append(f"<tr><th>keys</th><td>{e(', '.join(sorted(payload)))}</td></tr>")
    return (
        f"<h2 class=\"sect\">{e(title)}</h2>"
        f"<table class=\"props\"><tbody>{''.join(interesting)}</tbody></table>"
    )


def _child_rollup_text(counts: Mapping[str, int], total: int) -> str:
    parts = [f"{counts['closed']}/{total} closed"]
    if counts["legacy_unverified"]:
        parts.append(f"{counts['legacy_unverified']} legacy unverified")
    parts.append(f"{counts['in_progress']} in progress")
    parts.append(f"{counts['blocked']} blocked")
    parts.append(f"{counts['open']} open")
    return " · ".join(parts)


def _closed_parent_notice(entry: Mapping[str, Any], counts: Mapping[str, int]) -> str:
    state = str(entry.get("lifecycle_status") or entry.get("state") or "")
    if not state.startswith("closed"):
        return ""
    actionable = counts["open"] + counts["in_progress"] + counts["blocked"]
    unverified = counts["legacy_unverified"]
    if not actionable and not unverified:
        return ""
    if actionable:
        return (
            '<p class="error">This item is closed while children remain actionable '
            f"({actionable} open/in progress/blocked"
            f"{f', {unverified} legacy unverified' if unverified else ''}). "
            "A Feature may close only after each required child is terminal.</p>"
        )
    return (
        '<p class="notice">Children were legacy terminals without verifiable Acceptance, '
        "so import kept them open with <code>legacy-terminal-unverified</code> "
        "(DEC-0037-008). They are not current work and have no <code>closure.json</code>. "
        "DONE.md / DONE-* overlays were retained as provenance only.</p>"
    )


def document(title: str, crumbs: str, body: str, *, footer: Optional[str] = None) -> str:
    if footer is None:
        footer = (
            "Generated view — not authority. Canonical source is "
            "<code>issues/**/index.md</code>. "
            '<a href="?listing=1">Show directory listing</a>'
        )
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{e(title)}</title><link rel=\"stylesheet\" href=\"/style.css\">"
        f"<style>{PAGE_STYLE}</style></head><body class=\"issue-preview\">"
        "<header><div class=\"titleblock\"><a class=\"home\" href=\"/\">ara::* API-Referenz</a>"
        "<span class=\"rel\">Local preview</span></div></header>"
        f"<nav class=\"crumbs\">{crumbs}</nav><main>{body}</main>"
        f"<footer>{footer}</footer></body></html>\n"
    )


def render_index(catalog: Mapping[str, Any], issues_root: Optional[Path] = None) -> str:
    if issues_root:
        catalog = attach_item_labels(catalog, Path(issues_root))
    by_id = catalog_by_id(catalog)
    features = [item for item in by_id.values() if item.get("level") == "feature"]
    features.sort(key=lambda item: item.get("id") or "")
    rows = []
    for feature in features:
        kids = descendants(by_id, feature["id"])
        counts = count_states(kids)
        total = len(kids)
        href = e(feature.get("url") or item_url(feature["id"], "feature"))
        klass, status = display_state(feature)
        rows.append(
            f"<tr><td><a href=\"{href}\"><code>{e(feature['id'])}</code></a></td>"
            f"<td>{_chip(klass, status)}</td>"
            f"<td>{e(feature.get('title') or '')}</td>"
            f"<td>{_child_rollup_text(counts, total)}</td></tr>"
        )
    table = (
        '<table class="items"><thead><tr><th>Feature</th><th>Status</th><th>Title</th>'
        "<th>Children</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        if rows else '<p class="note">No features in the catalog.</p>'
    )
    body = (
        "<div class=\"hero\"><h1>Issues</h1>"
        f"<p class=\"note\">Catalog of {len(by_id)} items "
        f"({len(features)} features). Generated view from "
        "<code>issues/_views/catalog.json</code>.</p></div>"
        f"{table}"
    )
    crumbs = '<a href="/">Start</a> / Issues'
    return document("Issues", crumbs, body)


def render_item(repo: Path, item_id: str, catalog: Mapping[str, Any],
                issues_root: Optional[Path] = None) -> str:
    issues_root = Path(issues_root) if issues_root else Path(repo) / "issues"
    catalog = attach_item_labels(catalog, issues_root)
    by_id = catalog_by_id(catalog)
    loaded = load_item(repo, item_id, issues_root=issues_root)
    parsed = loaded.get("parsed")
    parsed_item = (parsed or {}).get("item") if parsed else None
    entry = dict(by_id.get(item_id) or {})
    if parsed_item:
        entry.setdefault("id", parsed_item.get("id"))
        entry.setdefault("level", parsed_item.get("level"))
        entry.setdefault("state", parsed_item.get("state"))
        entry.setdefault("parent", parsed_item.get("parent"))
        entry.setdefault("prerequisites", parsed_item.get("prerequisites") or [])
        if parsed_item.get("labels") is not None:
            entry["labels"] = parsed_item.get("labels")
        goal = ((parsed or {}).get("sections") or {}).get("Goal", {}).get("text") or ""
        entry.setdefault("title", goal.splitlines()[0] if goal else item_id)
        if not entry.get("lifecycle_status"):
            entry["lifecycle_status"] = views._lifecycle_status(
                parsed_item.get("state"), loaded.get("closure"),
                title=entry.get("title") or "",
                labels=parsed_item.get("labels") or [],
            )
    entry.setdefault("id", item_id)
    title = short_title(entry.get("title") or item_id) or item_id
    kids = descendants(by_id, item_id)
    counts = count_states(kids)
    total = len(kids)
    criteria = (parsed or {}).get("criteria") or entry.get("criteria") or []
    checked = sum(1 for row in criteria if (row or {}).get("status") == "checked")
    if isinstance(loaded.get("closure"), dict) and not loaded["closure"].get("malformed"):
        checked = sum(
            1 for row in loaded["closure"].get("criteria") or []
            if isinstance(row, dict) and row.get("status") == "checked"
        )
    crumbs = ['<a href="/">Start</a>', '<a href="/issues/">Issues</a>']
    parent_id = entry.get("parent")
    if parent_id:
        crumbs.append(f'<a href="{e(item_url(parent_id))}">{e(parent_id)}</a>')
    crumbs.append(e(item_id))
    error_html = ""
    if loaded.get("error"):
        error_html = f'<p class="error">{e(loaded["error"])}</p>'
    source = entry.get("source", {}).get("path") or loaded.get("path") or ""
    notice_html = _closed_parent_notice(entry, counts)
    counts_html = ""
    if total:
        unverified_html = ""
        if counts["legacy_unverified"]:
            unverified_html = (
                f"<span><strong>{counts['legacy_unverified']}</strong> legacy unverified</span>"
            )
        counts_html = (
            '<div class="counts">'
            f"<span><strong>{counts['closed']}</strong> closed</span>"
            f"{unverified_html}"
            f"<span><strong>{counts['in_progress']}</strong> in progress</span>"
            f"<span><strong>{counts['blocked']}</strong> blocked</span>"
            f"<span><strong>{counts['open']}</strong> open</span>"
            f"<span><strong>{total}</strong> children</span></div>"
            f"{_meter(counts['closed'], counts['legacy_unverified'], total)}"
        )
    sections = (parsed or {}).get("sections") or {}
    body = (
        f"<div class=\"hero\">{_status_chips(entry, parsed_item)}"
        f"<h1>{e(item_id)} — {e(title)}</h1>"
        f"{error_html}{notice_html}{counts_html}"
        f"<p class=\"note\">Canonical: <a href=\"/{e(source)}\"><code>{e(source)}</code></a>"
        f" · Criteria {checked}/{len(criteria)} checked</p></div>"
        "<h2 class=\"sect\">Goal</h2>"
        f"<div class=\"body\">{format_body((sections.get('Goal') or {}).get('text') or entry.get('title') or '')}</div>"
        "<h2 class=\"sect\">Scope</h2>"
        f"<div class=\"body\">{format_body((sections.get('Scope') or {}).get('text') or '')}</div>"
        "<h2 class=\"sect\">Acceptance criteria</h2>"
        f"{_criteria_list(parsed, loaded.get('closure'))}"
        "<h2 class=\"sect\">Definition of Done</h2>"
        f"<div class=\"body\">{format_body((sections.get('Definition of Done') or {}).get('text') or '')}</div>"
        "<h2 class=\"sect\">Prerequisites</h2>"
        f"{_prereq_list(entry.get('prerequisites') or [], by_id)}"
        "<h2 class=\"sect\">Children</h2>"
        f"{_child_rows(item_id, by_id)}"
        f"{_sidecar_block('Active claim', loaded.get('claim'))}"
        f"{_sidecar_block('Closure', loaded.get('closure'))}"
    )
    return document(f"{item_id} — {title}", " / ".join(crumbs), body)


def render_not_found(item_id: str) -> str:
    body = (
        f"<div class=\"hero\"><h1>{e(item_id)}</h1>"
        f"<p class=\"error\">No issue item at this path.</p></div>"
        '<p><a href="/issues/">Back to issues</a></p>'
    )
    crumbs = f'<a href="/">Start</a> / <a href="/issues/">Issues</a> / {e(item_id)}'
    return document(f"{item_id} not found", crumbs, body)


class IssuePreviewHandler(SimpleHTTPRequestHandler):
    repo: Path = ROOT
    preview: Optional["Preview"] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.repo), **kwargs)

    def do_GET(self) -> None:
        if self._serve_preview() or self._serve_markdown():
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        if self._serve_preview(body=False) or self._serve_markdown(body=False):
            return
        super().do_HEAD()

    def _write_bytes(self, status: int, content_type: str, data: bytes, body: bool) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(data)

    def _serve_markdown(self, body: bool = True) -> bool:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if not is_markdown_path(self.path):
            return False
        fs_path = Path(self.translate_path(parsed.path))
        if not fs_path.is_file():
            return False
        try:
            data = fs_path.read_bytes()
        except OSError:
            return False
        if query.get("raw") == ["1"]:
            self._write_bytes(200, "text/plain; charset=utf-8", data, body)
            return True
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", "replace")
        if len(data) > MAX_MARKDOWN_BYTES:
            payload = document(
                fs_path.name,
                path_crumbs(parsed.path),
                f'<p class="error">File too large to render.</p><pre>{e(text[:20000])}</pre>',
                footer=f'<a href="?raw=1">View source</a>',
            )
        else:
            payload = render_markdown_page(text, url_path=parsed.path, filename=fs_path.name)
        self._write_bytes(200, "text/html; charset=utf-8", payload.encode("utf-8"), body)
        return True

    def _serve_preview(self, body: bool = True) -> bool:
        query = parse_qs(urlparse(self.path).query)
        if query.get("listing") == ["1"]:
            return False
        if needs_slash_redirect(self.path):
            target = urlparse(self.path).path + "/"
            self.send_response(301)
            self.send_header("Location", target)
            self.end_headers()
            return True
        matched = match_preview_path(self.path)
        if not matched:
            return False
        preview = self.preview or Preview(self.repo)
        kind, item_id = matched
        try:
            if kind == "index":
                payload = render_index(preview.catalog(), issues_root=preview.issues_root)
                status = 200
            else:
                assert item_id is not None
                by_id = catalog_by_id(preview.catalog())
                path = item_index_path(preview.issues_root, item_id)
                if item_id not in by_id and not path.is_file():
                    payload = render_not_found(item_id)
                    status = 404
                else:
                    payload = render_item(
                        self.repo, item_id, preview.catalog(),
                        issues_root=preview.issues_root,
                    )
                    status = 200
        except Exception as exc:
            payload = document(
                "Issue preview error",
                '<a href="/">Start</a> / Issues',
                f'<p class="error">{e(type(exc).__name__)}: {e(exc)}</p>',
            )
            status = 500
        data = payload.encode("utf-8")
        self._write_bytes(status, "text/html; charset=utf-8", data, body)
        return True

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


class Preview:
    def __init__(self, repo: Path, issues_root: Optional[Path] = None):
        self.repo = Path(repo)
        self.issues_root = Path(issues_root) if issues_root else self.repo / "issues"
        self._catalog: Optional[Dict[str, Any]] = None
        self._mtime: Optional[float] = None

    def catalog(self) -> Dict[str, Any]:
        committed = self.issues_root / "_views" / "catalog.json"
        mtime = committed.stat().st_mtime if committed.is_file() else None
        if self._catalog is not None and mtime == self._mtime:
            return self._catalog
        self._catalog = attach_item_labels(
            load_catalog(self.repo, issues_root=self.issues_root),
            self.issues_root,
        )
        self._mtime = mtime
        return self._catalog


def serve(repo: Path, host: str, port: int) -> None:
    handler = IssuePreviewHandler
    handler.repo = repo
    handler.preview = Preview(repo)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"Local preview at http://{host}:{port}/", file=sys.stderr)
    httpd.serve_forever()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(ROOT), help="repository root")
    sub = parser.add_subparsers(dest="cmd", required=True)
    serve_cmd = sub.add_parser("serve", help="HTTP preview replacing python -m http.server")
    serve_cmd.add_argument("--host", default="0.0.0.0")
    serve_cmd.add_argument("--port", type=int, default=8100)
    render_cmd = sub.add_parser("render", help="print one HTML page to stdout")
    render_cmd.add_argument("--id", help="issue id, omitted for the feature index")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    if args.cmd == "serve":
        serve(repo, args.host, args.port)
        return 0
    preview = Preview(repo)
    catalog = preview.catalog()
    if args.id:
        sys.stdout.write(render_item(repo, args.id, catalog, issues_root=preview.issues_root))
    else:
        sys.stdout.write(render_index(catalog, issues_root=preview.issues_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
