#!/usr/bin/env python3
"""Build the backlog-evolution view used by the 3D completion visualizer.

Reads both the legacy TODO.md git history and the current issue-store catalog /
dependency-graph, and emits ``backlog-evolution@v1`` JSON. The browser widget
(``tools/backlog-evolution-core.js``) accepts the same JSON plus the raw older
formats (baked FEATURES/TIMELINE, TODO.md, issue-dependency-graph@v1).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "backlog-evolution@v1"
AUTHORITY = "generated-view"
OUT = Path("issues/_views/backlog-evolution.json")
GRAPH_SCHEMA = "issue-dependency-graph@v1"
CATALOG_SCHEMA = "issue-catalog@v1"

FEATURE_RE = re.compile(r"^##\s*Feature:\s*(\d{4})\s*(?:\u2014|--|-)?\s*(.*)$")
TASK_RE = re.compile(
    r"^-\s*\[([ xup\?wd])\]\s*(?:\*\*)?(\d{4}-\d{2}(?:\.\d{2})?)(?:\*\*)?\s*:?\s*(.*)$",
    re.I,
)
PREREQ_BLOCK_RE = re.compile(r"PREREQ:\s*(.+?)(?:\s*(?:\u2014|--)\s|\s*$)")
PREREQ_ITEM_RE = re.compile(r"(\d{4}(?:-\d{2}(?:\.\d{2})?)?)\s*:\s*(\d{4}(?:-\d{2}(?:\.\d{2})?)?)")
SOFT_RE = re.compile(r"\(soft\b", re.I)
ACCEPTANCE_RE = re.compile(r"Acceptance:\s*[✓✔]")

PALETTE = [
    "#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#fb7185",
    "#34d399", "#2dd4bf", "#a78bfa", "#fb923c", "#facc15",
    "#4ade80", "#60a5fa", "#e879f9", "#22d3ee", "#f87171",
]


class EvolutionError(ValueError):
    pass


def has_acceptance(text):
    return bool(ACCEPTANCE_RE.search(text or ""))


def promote_accepted_mark(mark, text=""):
    mark = (mark or " ").lower()
    if mark == "x" and has_acceptance(text):
        return "a"
    return mark


def lifecycle_to_mark(lifecycle_status, endpoint_status=None, title=None, prior_mark=None):
    if endpoint_status in ("missing", "malformed"):
        return "?"
    status = lifecycle_status or ""
    if has_acceptance(title) or status in ("closed", "closed:completed"):
        return "a"
    if status == "in_progress":
        return "p"
    if status == "blocked":
        return "u"
    if status == "withdrawn":
        return "w"
    if status == "closed" or status.startswith("closed:"):
        return "x"
    if status == "open" and prior_mark in ("x", "a"):
        return prior_mark
    if status == "open":
        return " "
    return "?"


def _looks_like_markdown(text):
    head = text.lstrip()[:800]
    if head.startswith("---"):
        return True
    if "## Feature:" in head or head.startswith("# "):
        return True
    if "PREREQ:" in head and "- [" in head:
        return True
    if TASK_RE.search(head) or re.search(r"^-\s*\[[ xup\?wd]\]", head, re.I | re.M):
        return True
    return False


def parse_todo_markdown(text):
    """Parse a legacy TODO.md snapshot into features + marks."""
    features = []
    order = []
    by_id = {}
    marks = {}
    current = None
    for raw in str(text).splitlines():
        line = raw.strip()
        m_feat = FEATURE_RE.match(line)
        if m_feat:
            fid = m_feat.group(1)
            name = (m_feat.group(2) or "").strip()
            if fid not in by_id:
                feat = {
                    "id": fid,
                    "name": name,
                    "color": PALETTE[len(order) % len(PALETTE)],
                    "tasks": [],
                }
                by_id[fid] = feat
                order.append(fid)
                features.append(feat)
            elif name and not by_id[fid].get("name"):
                by_id[fid]["name"] = name
            current = by_id[fid]
            continue
        m_task = TASK_RE.match(line)
        if m_task:
            mark = m_task.group(1).lower()
            tid = m_task.group(2)
            rest = (m_task.group(3) or "").strip()
            if rest.startswith(":"):
                rest = rest[1:].strip()
            prefix = tid.split("-", 1)[0]
            feature = by_id.get(prefix) or current
            if feature is None:
                feat = {
                    "id": prefix,
                    "name": prefix,
                    "color": PALETTE[len(order) % len(PALETTE)],
                    "tasks": [],
                }
                by_id[prefix] = feat
                order.append(prefix)
                features.append(feat)
                feature = feat
            prereqs = []
            block = PREREQ_BLOCK_RE.search(rest)
            if block:
                soft = bool(SOFT_RE.search(rest))
                for item in PREREQ_ITEM_RE.finditer(block.group(1)):
                    prereqs.append({"from": tid, "to": item.group(2), "soft": soft})
            task = {"id": tid, "text": rest, "description": "", "prereqs": prereqs}
            existing = next((t for t in feature["tasks"] if t["id"] == tid), None)
            if existing is None:
                feature["tasks"].append(task)
            else:
                existing.update(task)
            marks[tid] = promote_accepted_mark(mark, rest)
            current = feature
    return {"features": features, "marks": marks, "fids": [f["id"] for f in features]}


def _features_from_catalog(catalog):
    items = list(catalog.get("items") or [])
    by_id = {}
    features = []
    order = []
    for item in items:
        if item.get("level") != "feature":
            continue
        fid = item["id"]
        feat = {
            "id": fid,
            "name": item.get("title") or fid,
            "color": PALETTE[len(order) % len(PALETTE)],
            "tasks": [],
        }
        by_id[fid] = feat
        order.append(fid)
        features.append(feat)
    marks = {}
    for item in items:
        level = item.get("level")
        nid = item.get("id")
        mark = lifecycle_to_mark(
            item.get("lifecycle_status"),
            item.get("endpoint_status"),
            title=item.get("title") or item.get("name"),
        )
        if level == "feature":
            if nid:
                marks[nid] = mark
            continue
        if level not in ("task", "subtask"):
            continue
        parent = item.get("parent") or (nid.split("-", 1)[0] if nid else None)
        feat = by_id.get(parent)
        if feat is None:
            feat = {
                "id": parent or "_unresolved",
                "name": parent or "_unresolved",
                "color": PALETTE[len(order) % len(PALETTE)],
                "tasks": [],
            }
            by_id[feat["id"]] = feat
            order.append(feat["id"])
            features.append(feat)
        prereqs = []
        for target in item.get("prerequisites") or []:
            if isinstance(target, str) and target:
                prereqs.append({"from": nid, "to": target, "soft": False})
        feat["tasks"].append({
            "id": nid,
            "text": item.get("title") or "",
            "description": "",
            "prereqs": prereqs,
        })
        marks[nid] = mark
    return features, marks, [f["id"] for f in features]


def _features_from_graph(graph):
    nodes = list(graph.get("nodes") or [])
    edges = list(graph.get("edges") or [])
    by_id = {}
    features = []
    order = []
    marks = {}
    for node in nodes:
        nid = node.get("id")
        if not nid:
            continue
        marks[nid] = lifecycle_to_mark(
            node.get("lifecycle_status"),
            node.get("endpoint_status"),
            title=node.get("title") or node.get("name"),
        )
        if node.get("level") == "feature" or (
                node.get("level") is None and "-" not in str(nid)):
            feat = {
                "id": nid,
                "name": nid,
                "color": PALETTE[len(order) % len(PALETTE)],
                "tasks": [],
            }
            by_id[nid] = feat
            order.append(nid)
            features.append(feat)
    for node in nodes:
        nid = node.get("id")
        if not nid or node.get("level") == "feature":
            continue
        prefix = str(nid).split("-", 1)[0]
        feat = by_id.get(prefix)
        if feat is None:
            feat = {
                "id": prefix,
                "name": prefix,
                "color": PALETTE[len(order) % len(PALETTE)],
                "tasks": [],
            }
            by_id[prefix] = feat
            order.append(prefix)
            features.append(feat)
        feat["tasks"].append({"id": nid, "text": "", "description": "", "prereqs": []})
    tasks_by_id = {t["id"]: t for f in features for t in f["tasks"]}
    for edge in edges:
        src = edge.get("source")
        dst = edge.get("target")
        task = tasks_by_id.get(src)
        if task is None:
            continue
        task["prereqs"].append({"from": src, "to": dst, "soft": False})
    return features, marks, [f["id"] for f in features]


def _task_text_map(features):
    out = {}
    for feat in features:
        for task in feat.get("tasks") or []:
            out[task["id"]] = task.get("text") or ""
    return out


def _diff_snapshots(prev_fids, prev_marks, prev_text, cur_fids, cur_marks, cur_text, features_by_id):
    changes = []
    prev_set = set(prev_fids or [])
    for fid in cur_fids:
        if fid not in prev_set:
            name = (features_by_id.get(fid) or {}).get("name") or fid
            changes.append({"type": "feat_add", "fid": fid, "name": name})
    cur_set = set(cur_fids or [])
    for fid in prev_fids or []:
        if fid not in cur_set:
            changes.append({"type": "feat_rem", "fid": fid})
    prev_marks = prev_marks or {}
    for tid, mark in (cur_marks or {}).items():
        if "-" not in str(tid):
            continue
        if tid not in prev_marks:
            changes.append({"type": "task_add", "tid": tid, "text": (cur_text or {}).get(tid, "")[:80]})
        elif prev_marks.get(tid) != mark:
            changes.append({
                "type": "task_mark",
                "tid": tid,
                "from": prev_marks.get(tid, " "),
                "to": mark,
                "text": (cur_text or {}).get(tid, "")[:80],
            })
    return changes


def merge_feature_lists(*groups):
    by_id = {}
    order = []
    for features in groups:
        for feat in features or []:
            fid = feat["id"]
            if fid not in by_id:
                clone = {
                    "id": fid,
                    "name": feat.get("name") or fid,
                    "color": feat.get("color") or PALETTE[len(order) % len(PALETTE)],
                    "tasks": [],
                }
                by_id[fid] = clone
                order.append(fid)
            elif feat.get("name") and (not by_id[fid]["name"] or by_id[fid]["name"] == fid):
                by_id[fid]["name"] = feat["name"]
            seen = {t["id"] for t in by_id[fid]["tasks"]}
            for task in feat.get("tasks") or []:
                if task["id"] in seen:
                    continue
                by_id[fid]["tasks"].append({
                    "id": task["id"],
                    "text": task.get("text") or "",
                    "description": (task.get("description") or "")[:240],
                    "prereqs": list(task.get("prereqs") or []),
                })
                seen.add(task["id"])
    return [by_id[fid] for fid in order]


def snapshot_from_catalog(catalog, *, hash="issue-store", date="", msg="issue-store catalog"):
    features, marks, fids = _features_from_catalog(catalog)
    return {
        "features": features,
        "snapshot": {
            "idx": 0,
            "hash": hash,
            "date": date or "",
            "msg": msg,
            "fids": fids,
            "marks": marks,
            "changes": [{"type": "feat_add", "fid": f["id"], "name": f["name"]} for f in features],
        },
    }


def snapshot_from_graph(graph, *, hash="issue-graph", date="", msg="issue-dependency-graph"):
    features, marks, fids = _features_from_graph(graph)
    return {
        "features": features,
        "snapshot": {
            "idx": 0,
            "hash": hash,
            "date": date or "",
            "msg": msg,
            "fids": fids,
            "marks": marks,
            "changes": [{"type": "feat_add", "fid": f["id"], "name": f["name"]} for f in features],
        },
    }


def _history_from_timeline(timeline, features):
    texts = _task_text_map(features)
    history = {}
    for snap in timeline:
        date = snap.get("date") or ""
        for tid, mark in (snap.get("marks") or {}).items():
            if "-" not in str(tid):
                continue
            rec = history.setdefault(tid, {
                "created": date,
                "done": None,
                "title": texts.get(tid, ""),
                "description": "",
                "changes": [],
            })
            if not rec.get("created"):
                rec["created"] = date
            if mark == "x" and not rec.get("done"):
                rec["done"] = date
        for change in snap.get("changes") or []:
            tid = change.get("tid")
            if not tid:
                continue
            rec = history.setdefault(tid, {
                "created": date,
                "done": None,
                "title": change.get("text") or texts.get(tid, ""),
                "description": "",
                "changes": [],
            })
            rec["changes"].append({
                "date": date,
                "hash": snap.get("hash"),
                "msg": snap.get("msg"),
                "type": change.get("type"),
                "from": change.get("from"),
                "to": change.get("to"),
            })
            if change.get("to") == "x" and not rec.get("done"):
                rec["done"] = date
    return history


def assemble(timeline, features, *, source=None, history=None):
    numbered = []
    for idx, snap in enumerate(timeline):
        item = dict(snap)
        item["idx"] = idx
        numbered.append(item)
    return {
        "schema": SCHEMA,
        "authority": AUTHORITY,
        "features": features,
        "timeline": numbered,
        "task_history": history or _history_from_timeline(numbered, features),
        "source": source or {},
    }


def normalize_payload(document):
    if not isinstance(document, dict):
        raise EvolutionError("evolution document must be a JSON object")
    if document.get("schema") == SCHEMA:
        features = document.get("features") or []
        timeline = document.get("timeline") or []
        if not isinstance(features, list) or not isinstance(timeline, list):
            raise EvolutionError("backlog-evolution@v1 requires features and timeline arrays")
        return {
            "schema": SCHEMA,
            "authority": document.get("authority") or AUTHORITY,
            "features": features,
            "timeline": timeline,
            "task_history": document.get("task_history") or {},
            "source": document.get("source") or {},
        }
    if "FEATURES" in document or "features" in document:
        return {
            "schema": SCHEMA,
            "authority": "legacy-baked",
            "features": document.get("FEATURES") or document.get("features") or [],
            "timeline": document.get("TIMELINE") or document.get("timeline") or [],
            "task_history": document.get("TASK_HISTORY") or document.get("task_history") or {},
            "source": {"format": "legacy-baked"},
        }
    if document.get("schema") == CATALOG_SCHEMA:
        packed = snapshot_from_catalog(document)
        return assemble([packed["snapshot"]], packed["features"], source={"format": "issue-catalog@v1"})
    if document.get("schema") == GRAPH_SCHEMA:
        packed = snapshot_from_graph(document)
        return assemble([packed["snapshot"]], packed["features"], source={"format": GRAPH_SCHEMA})
    raise EvolutionError("unsupported evolution document schema")


def load_evolution(text, catalog=None):
    if not isinstance(text, str):
        raise EvolutionError("evolution input must be text")
    if _looks_like_markdown(text):
        parsed = parse_todo_markdown(text)
        snap = {
            "idx": 0,
            "hash": "todo.md",
            "date": "",
            "msg": "TODO.md",
            "fids": parsed["fids"],
            "marks": parsed["marks"],
            "changes": [{"type": "feat_add", "fid": f["id"], "name": f["name"]} for f in parsed["features"]],
        }
        return assemble([snap], parsed["features"], source={"format": "todo.md"})
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EvolutionError(f"malformed evolution JSON: {exc}") from exc
    payload = normalize_payload(document)
    if catalog is not None and document.get("schema") == GRAPH_SCHEMA:
        packed = snapshot_from_catalog(catalog)
        return assemble([packed["snapshot"]], packed["features"], source={"format": "issue-catalog+graph"})
    return payload


def _git(repo, args, *, check=True):
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        err = (completed.stderr or b"").decode("utf-8", "replace").strip()
        raise EvolutionError(f"git {' '.join(args)} failed: {err}")
    return completed


def _todo_commits(repo):
    completed = _git(repo, ["log", "--pretty=format:%H\t%ci\t%s", "--reverse", "--", "TODO.md"])
    rows = []
    for line in completed.stdout.decode("utf-8", "replace").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) < 2:
            continue
        sha, date = parts[0], parts[1][:10]
        msg = parts[2] if len(parts) > 2 else ""
        rows.append((sha, date, msg))
    return rows


def _cat_todo_batch(repo, shas):
    if not shas:
        return {}
    spec = "".join(f"{sha}:TODO.md\n" for sha in shas).encode("utf-8")
    completed = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input=spec,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        err = (completed.stderr or b"").decode("utf-8", "replace").strip()
        raise EvolutionError(f"git cat-file --batch failed: {err}")
    blobs = {}
    data = completed.stdout
    offset = 0
    for sha in shas:
        nl = data.find(b"\n", offset)
        if nl < 0:
            break
        header = data[offset:nl].decode("ascii", "replace")
        offset = nl + 1
        parts = header.split()
        if len(parts) < 3 or parts[1] == "missing":
            blobs[sha] = None
            continue
        size = int(parts[2])
        blobs[sha] = data[offset:offset + size].decode("utf-8", "replace")
        offset += size
        if offset < len(data) and data[offset:offset + 1] == b"\n":
            offset += 1
    return blobs


def build_from_repo(repo):
    repo = Path(repo)
    commits = _todo_commits(repo)
    blobs = _cat_todo_batch(repo, [row[0] for row in commits])
    timeline = []
    feature_groups = []
    prev_fids = []
    prev_marks = {}
    prev_text = {}
    last_legacy_marks = {}
    features_by_id = {}
    last_sig = None
    for sha, date, msg in commits:
        text = blobs.get(sha)
        if not text:
            continue
        parsed = parse_todo_markdown(text)
        feature_groups.append(parsed["features"])
        for feat in parsed["features"]:
            features_by_id[feat["id"]] = feat
        sig = (tuple(parsed["fids"]), tuple(sorted(parsed["marks"].items())))
        if sig == last_sig:
            continue
        last_sig = sig
        texts = _task_text_map(parsed["features"])
        changes = _diff_snapshots(
            prev_fids, prev_marks, prev_text,
            parsed["fids"], parsed["marks"], texts, features_by_id,
        )
        timeline.append({
            "hash": sha[:8],
            "date": date,
            "msg": msg,
            "fids": parsed["fids"],
            "marks": parsed["marks"],
            "changes": changes,
        })
        prev_fids = parsed["fids"]
        prev_marks = parsed["marks"]
        prev_text = texts
        last_legacy_marks.update(parsed["marks"])

    live_todo = repo / "TODO.md"
    if live_todo.is_file():
        last_legacy_marks.update(
            parse_todo_markdown(live_todo.read_text(encoding="utf-8"))["marks"])

    catalog_path = repo / "issues/_views/catalog.json"
    graph_path = repo / "issues/_views/dependency-graph.json"
    source = {"legacy_commits": len(timeline), "issue_store": False}
    if catalog_path.is_file():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        packed = snapshot_from_catalog(
            catalog, hash="issue-store", date="", msg="issue-store catalog")
        feature_groups.append(packed["features"])
        store_marks = packed["snapshot"]["marks"]
        store_fids = packed["snapshot"]["fids"]
        items = list(catalog.get("items") or [])
        by_id = {item.get("id"): item for item in items if item.get("id")}
        overlaid = {}
        for nid, mark in store_marks.items():
            item = by_id.get(nid) or {}
            overlaid[nid] = lifecycle_to_mark(
                item.get("lifecycle_status"),
                item.get("endpoint_status"),
                title=item.get("title") or item.get("name"),
                prior_mark=last_legacy_marks.get(nid) or prev_marks.get(nid),
            )
        store_marks = overlaid
        packed["snapshot"]["marks"] = store_marks
        texts = _task_text_map(packed["features"])
        for feat in packed["features"]:
            features_by_id[feat["id"]] = feat
        sig = (tuple(store_fids), tuple(sorted(store_marks.items())))
        if sig != last_sig:
            changes = _diff_snapshots(
                prev_fids, prev_marks, prev_text,
                store_fids, store_marks, texts, features_by_id,
            )
            if not timeline:
                changes = packed["snapshot"]["changes"]
            date = timeline[-1]["date"] if timeline else ""
            timeline.append({
                "hash": "issue-store",
                "date": date,
                "msg": "issue-store catalog (current)",
                "fids": store_fids,
                "marks": store_marks,
                "changes": changes,
            })
            source["issue_store"] = True
    elif graph_path.is_file():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        packed = snapshot_from_graph(graph)
        feature_groups.append(packed["features"])
        timeline.append(packed["snapshot"])
        source["issue_store"] = True

    features = merge_feature_lists(*feature_groups)
    return assemble(timeline, features, source=source)


def write_view(repo, dest=None):
    repo = Path(repo)
    payload = build_from_repo(repo)
    dest = Path(dest) if dest else repo / OUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
    return dest, payload


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate backlog-evolution@v1 JSON")
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument("--out", default=None, help="output path")
    args = parser.parse_args(argv)
    dest, payload = write_view(args.repo, args.out)
    print(
        f"wrote {dest} features={len(payload['features'])} "
        f"snapshots={len(payload['timeline'])}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
