#!/usr/bin/env python3
"""Generated TODO.md, DONE.md, and open/blocked/unclear/owner summaries (Task 0037-11.01).

Outputs are generated views. They must never replace live repository TODO.md or
DONE.md. Write only under a caller-supplied output root (fixture-owned in tests).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

import importlib.util

_VIEWS_FILE = Path(__file__).resolve().parent / "issue_views.py"
_SPEC = importlib.util.spec_from_file_location("issue_views", _VIEWS_FILE)
VIEWS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(VIEWS)

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path("_src/tools/issue_lists.py")
LIVE_AUTHORITY = frozenset({"TODO.md", "DONE.md"})
OUTPUT_NAMES = {
    "todo": "TODO.md",
    "done": "DONE.md",
    "open": "summaries/open.md",
    "blocked": "summaries/blocked.md",
    "unclear": "summaries/unclear.md",
    "owners": "summaries/owners.md",
    "manifest": "run-manifest.json",
}
CONFIG = {
    "schema": "issue-lists-config@v1",
    "lists_schema": "issue-lists@v1",
    "warning": "GENERATED-VIEW: not authoritative. Do not hand-edit. Live TODO.md/DONE.md remain authority until cutover.",
}
MARKER = {
    "open": "[ ]",
    "in_progress": "[p]",
    "blocked": "[d]",
    "closed": "[x]",
    "withdrawn": "[w]",
    "malformed": "[?]",
}
TERMINAL = frozenset({"closed", "withdrawn"})
OPENISH = frozenset({"open", "in_progress", "blocked"})


class IssueListsError(ValueError):
    pass


def _digest_bytes(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _generation_id(source_digests, schema_digest, tool_digest, config_digest):
    payload = VIEWS._canonical_json({
        "config": config_digest,
        "inputs": list(source_digests),
        "schema": schema_digest,
        "tool": tool_digest,
    })
    encoded = payload.encode("utf-8") if isinstance(payload, str) else payload
    return _digest_bytes(encoded)


def refuse_live_authority_path(path, repository_root):
    path = Path(path).resolve()
    repo = Path(repository_root).resolve()
    if path == repo / "TODO.md" or path == repo / "DONE.md":
        raise IssueListsError(
            f"refuses live authority path {path} (repository TODO.md/DONE.md are forbidden product outputs)")
    try:
        path.relative_to(repo)
        if path.name in LIVE_AUTHORITY and path.parent == repo:
            raise IssueListsError(f"refuses live authority path {path}")
    except ValueError:
        pass
    return path


def _owner_label(item):
    labels = item.get("labels") or []
    owners = [label[6:] for label in labels if label.startswith("owner-")]
    if owners:
        return ",".join(sorted(owners))
    return "unassigned"


def _item_line(item):
    state = item.get("state") or "malformed"
    marker = MARKER.get(state, "[?]")
    title = item.get("title") or "(untitled)"
    level = item.get("level") or "item"
    archive = item.get("archive_status")
    extra = f" archive={archive}" if archive else ""
    criteria = item.get("criteria") or []
    crit = ""
    if criteria:
        crit = " criteria=" + ",".join(
            f"{entry['id']}:{entry.get('status', 'unknown')}" for entry in criteria)
    return (
        f"- {marker} **{item['id']}** ({level}, {item.get('lifecycle_status') or state}"
        f"{extra}) {title}{crit}"
    )


def _header(kind, catalog):
    digests = catalog["digests"]
    lines = [
        f"<!-- {CONFIG['warning']} -->",
        f"<!-- schema: {CONFIG['lists_schema']} kind: {kind} authority: generated-view -->",
        f"<!-- generation_id: {catalog['generation_id']} -->",
        f"<!-- source_sha256: {','.join(digests['source_sha256'])} -->",
        f"<!-- schema_sha256: {digests['schema_sha256']} -->",
        f"<!-- tool_sha256: {digests['tool_sha256']} -->",
        f"<!-- config_sha256: {digests['config_sha256']} -->",
        "<!-- volatile execution run is recorded only in run-manifest.json -->",
        "",
        f"# Generated {kind}",
        "",
    ]
    return "\n".join(lines)


def _dedupe_ids(items):
    seen = {}
    duplicates = []
    for item in items:
        key = item["id"]
        if key in seen:
            duplicates.append(key)
        seen[key] = item
    if duplicates:
        raise IssueListsError(f"duplicated item: {sorted(set(duplicates))}")
    return items


def classify(catalog):
    items = _dedupe_ids(list(catalog["items"]))
    todo = []
    done = []
    unclear = []
    blocked = []
    open_items = []
    owners = {}
    for item in items:
        state = item.get("state")
        if item.get("endpoint_status") == "malformed" or state is None:
            unclear.append(item)
            continue
        if state == "blocked":
            blocked.append(item)
            todo.append(item)
        elif state in OPENISH:
            open_items.append(item)
            todo.append(item)
        elif state in TERMINAL:
            done.append(item)
        else:
            unclear.append(item)
        owners.setdefault(_owner_label(item), []).append(item["id"])
    for bucket in (todo, done, unclear, blocked, open_items):
        bucket.sort(key=lambda entry: entry["id"] or "")
    return {
        "todo": todo,
        "done": done,
        "open": open_items,
        "blocked": blocked,
        "unclear": unclear,
        "owners": owners,
    }


def render_lists(issues_root, repository_root):
    catalog, _graph = VIEWS.render(issues_root, repository_root)
    parsed, _malformed, _sources = VIEWS.load_store(issues_root, repository_root)
    labels_by_id = {
        value["item"]["id"]: list(value["item"].get("labels") or [])
        for value in parsed
    }
    catalog = dict(catalog)
    catalog["items"] = [dict(item) for item in catalog["items"]]
    for item in catalog["items"]:
        item["labels"] = labels_by_id.get(item["id"], [])
    tool_bytes = (Path(repository_root) / TOOL_PATH).read_bytes()
    config_digest = _digest_bytes(VIEWS._canonical_json(CONFIG).encode("utf-8"))
    source_digests = catalog["digests"]["source_sha256"]
    schema_digest = catalog["digests"]["schema_sha256"]
    tool_digest = _digest_bytes(tool_bytes)
    catalog["digests"] = dict(catalog["digests"])
    catalog["digests"]["tool_sha256"] = tool_digest
    catalog["digests"]["config_sha256"] = config_digest
    catalog["generation_id"] = _generation_id(
        source_digests, schema_digest, tool_digest, config_digest)
    groups = classify(catalog)
    documents = {}
    for kind in ("todo", "done", "open", "blocked", "unclear"):
        body = "\n".join(_item_line(item) for item in groups[kind])
        documents[kind] = _header(kind, catalog) + (body + "\n" if body else "(none)\n")
    owner_lines = []
    for owner in sorted(groups["owners"]):
        ids = ",".join(sorted(groups["owners"][owner]))
        owner_lines.append(f"- **{owner}**: {ids}")
    documents["owners"] = _header("owners", catalog) + (
        "\n".join(owner_lines) + "\n" if owner_lines else "(none)\n")
    return catalog, groups, documents


def write_lists(documents, output_root, repository_root, *, run_id=None):
    output_root = Path(output_root).resolve()
    repository_root = Path(repository_root).resolve()
    refuse_live_authority_path(output_root / "TODO.md", repository_root)
    refuse_live_authority_path(output_root / "DONE.md", repository_root)
    if output_root == repository_root:
        raise IssueListsError("output root must not be the repository root")
    output_root.mkdir(parents=True, exist_ok=True)
    written = {}
    for kind, relative in OUTPUT_NAMES.items():
        if kind == "manifest":
            continue
        dest = refuse_live_authority_path(output_root / relative, repository_root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(documents[kind], encoding="utf-8")
        written[kind] = dest.as_posix()
    manifest = {
        "schema": "issue-lists-run@v1",
        "run_id": run_id or str(uuid.uuid4()),
        "outputs": written,
        "note": "run_id is volatile and must not be embedded in generated list bytes",
    }
    man_path = output_root / OUTPUT_NAMES["manifest"]
    man_path.write_text(VIEWS._canonical_json(manifest), encoding="utf-8")
    written["manifest"] = man_path.as_posix()
    return written, manifest


def verify_lists(output_root, issues_root, repository_root):
    catalog, groups, expected = render_lists(issues_root, repository_root)
    output_root = Path(output_root)
    observed_ids = []
    for kind in ("todo", "done", "open", "blocked", "unclear", "owners"):
        path = output_root / OUTPUT_NAMES[kind]
        actual = path.read_text(encoding="utf-8")
        if actual != expected[kind]:
            raise IssueListsError(f"manual divergence or stale bytes in {OUTPUT_NAMES[kind]}")
        if kind in ("todo", "done"):
            for item in groups[kind]:
                observed_ids.append(item["id"])
    source_ids = {item["id"] for item in catalog["items"]}
    if set(observed_ids) | {item["id"] for item in groups["unclear"]} != source_ids:
        raise IssueListsError("omission: generated lists do not reconcile source IDs")
    for item in groups["done"]:
        if item.get("state") not in TERMINAL:
            raise IssueListsError(f"false completion: {item['id']} is not terminal")
    todo_ids = {item["id"] for item in groups["todo"]}
    done_ids = {item["id"] for item in groups["done"]}
    if todo_ids & done_ids:
        raise IssueListsError(f"duplicated item across TODO/DONE: {sorted(todo_ids & done_ids)}")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=str(ROOT))
    parser.add_argument("--issues-root")
    parser.add_argument("--output-root")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    repository_root = Path(args.repository_root).resolve()
    issues_root = Path(args.issues_root) if args.issues_root else repository_root / "issues"
    output_root = Path(args.output_root) if args.output_root else None
    try:
        catalog, _groups, documents = render_lists(issues_root, repository_root)
        if args.write:
            if output_root is None:
                raise IssueListsError("--output-root is required for --write")
            write_lists(documents, output_root, repository_root)
        if args.verify:
            if output_root is None:
                raise IssueListsError("--output-root is required for --verify")
            verify_lists(output_root, issues_root, repository_root)
        if not args.write:
            sys.stdout.write(documents["todo"])
        return 0
    except (IssueListsError, VIEWS.IssueViewsError, VIEWS.IssueStoreError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
