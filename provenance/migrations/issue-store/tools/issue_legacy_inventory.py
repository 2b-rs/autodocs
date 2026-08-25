#!/usr/bin/env python3
"""Inventory legacy TODO.md / DONE.md / claims from an exact Git commit or tree.

Task 0037-13. Read-only versus issues/ and provenance/events/. Writes only to
an explicit output directory (normally provenance/migrations/issue-store/<run-id>/).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SCHEMA = "legacy-inventory@v1"
TASK_ID_RE = re.compile(r"^[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?$")
FEATURE_ID_RE = re.compile(r"^[0-9]{4}$")
TASK_HEADER_RE = re.compile(
    r"^- \[(?P<marker>[^]]*)\] \*\*(?P<id>[0-9]{4}-[0-9]{2}(?:\.[0-9]{2})?)\*\*(?P<tail>.*)$"
)
LEGACY_TASK_RE = re.compile(r"^- \[(?P<marker>[^]]*)\](?P<tail>.*)$")
FEATURE_HEADER_RE = re.compile(
    r"^## Feature:\s*(?:(?P<id>[0-9]{4})\s+[—-]\s+)?(?P<title>.+?)\s*$"
)
PREREQ_PAIR_RE = re.compile(
    r"(?P<left>[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?):"
    r"(?P<right>[0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?)"
)
REF_RE = re.compile(
    r"\bREF:\s*(?:`(?P<quoted>[^`\n]+)`|(?P<pending>pending\s+commit)|(?P<plain>[^\s<,;]+))?",
    re.IGNORECASE,
)
LOCAL_PLACEHOLDER_RE = re.compile(r"\blocal-[A-Za-z0-9._-]+\b")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHORT_COMMIT_RE = re.compile(r"^[0-9a-f]{7,39}$")
VALID_MARKERS = frozenset({" ", "u", "p", "?", "w", "x", "d"})
NO_CREDIT_LOCAL_REFS = frozenset(
    {
        "local-20260815-0021-06",
        "local-20260815-0021-07",
        "local-20260815-0021-08",
    }
)
ARCHIVED_NOT_ACCEPTED_FEATURE = "0021"

LOSSLESS = "lossless"
STABLE_FINDING = "stable_migration_finding"
AUTHORITY_REQUIRED = "authority_required_disposition"


def _sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _finding_id(rule: str, item: str, field: str, locator: str) -> str:
    payload = "|".join((rule, item, field, locator)).encode("utf-8")
    return "INV-" + hashlib.sha256(payload).hexdigest()[:16]


def _git(repo: Path, *args: str) -> bytes:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["LC_ALL"] = "C"
    completed = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        err = completed.stderr.decode("utf-8", "replace")[:400]
        raise RuntimeError(f"git {' '.join(args)} failed: {err}")
    return completed.stdout


def load_commit_blobs(repo: Path, commit: str) -> Dict[str, Tuple[bytes, str]]:
    if not FULL_COMMIT_RE.fullmatch(commit):
        raise ValueError("source_commit must be a 40-hex SHA")
    names = _git(repo, "ls-tree", "-r", "--name-only", commit).decode("utf-8").splitlines()
    selected = [n for n in names if n in {"TODO.md", "DONE.md"} or (
        n.startswith("TODO-") and n.endswith(".md") and "/" not in n
    )]
    blobs: Dict[str, Tuple[bytes, str]] = {}
    for path in selected:
        raw = _git(repo, "show", f"{commit}:{path}")
        blobs[path] = (raw, _sha256_bytes(raw))
    return blobs


def load_tree_blobs(tree: Path) -> Dict[str, Tuple[bytes, str]]:
    blobs: Dict[str, Tuple[bytes, str]] = {}
    for name in sorted(os.listdir(tree)):
        if name in {"TODO.md", "DONE.md"} or (
            name.startswith("TODO-") and name.endswith(".md")
        ):
            raw = (tree / name).read_bytes()
            blobs[name] = (raw, _sha256_bytes(raw))
    return blobs


def _split_features(path: str, text: str) -> List[dict]:
    lines = text.splitlines()
    features: List[dict] = []
    current: Optional[dict] = None
    preamble: List[str] = []
    for idx, line in enumerate(lines, 1):
        if line.startswith("## Feature:"):
            if current is not None:
                features.append(current)
            match = FEATURE_HEADER_RE.match(line)
            fid = match.group("id") if match else None
            title = match.group("title") if match else line[len("## Feature:") :].strip()
            current = {
                "kind": "feature",
                "id": fid,
                "title": title.strip() if title else "",
                "path": path,
                "line": idx,
                "header": line,
                "body_lines": [],
                "malformed_header": fid is None and (
                    path == "TODO.md" or bool(re.match(r"[0-9]", (title or "").strip()))
                ),
            }
        elif current is None:
            preamble.append(line)
        else:
            current["body_lines"].append((idx, line))
    if current is not None:
        features.append(current)
    if preamble and path == "TODO.md":
        features.insert(
            0,
            {
                "kind": "preamble",
                "id": None,
                "title": "TODO.md header",
                "path": path,
                "line": 1,
                "header": "",
                "body_lines": [(i + 1, l) for i, l in enumerate(preamble)],
                "malformed_header": False,
            },
        )
    return features


def _extract_refs(text: str) -> List[dict]:
    refs = []
    for match in REF_RE.finditer(text):
        value = match.group("quoted") or match.group("plain") or match.group("pending") or ""
        value = value.strip().strip("`")
        kind = "missing"
        if match.group("pending") or value.lower() == "pending commit":
            kind = "pending"
        elif value in NO_CREDIT_LOCAL_REFS or value.startswith("local-"):
            kind = "local_placeholder"
        elif FULL_COMMIT_RE.fullmatch(value):
            kind = "full_commit"
        elif SHORT_COMMIT_RE.fullmatch(value):
            kind = "short_commit"
        elif value:
            kind = "opaque"
        refs.append({"value": value, "kind": kind})
    for match in LOCAL_PLACEHOLDER_RE.finditer(text):
        value = match.group(0)
        if not any(r["value"] == value for r in refs):
            refs.append({"value": value, "kind": "local_placeholder"})
    return refs


def _extract_prereqs(text: str) -> List[dict]:
    edges = []
    seen = set()
    for match in PREREQ_PAIR_RE.finditer(text):
        left, right = match.group("left"), match.group("right")
        key = (left, right)
        if key in seen:
            continue
        seen.add(key)
        edges.append({"from": left, "to": right, "raw": f"{left}:{right}"})
    return edges


def _block_text(start_idx: int, body: Sequence[Tuple[int, str]]) -> str:
    chunks = []
    for i, (line_no, line) in enumerate(body):
        if i < start_idx:
            continue
        if i > start_idx and line.startswith("- [") and "**" in line:
            break
        if i > start_idx and line.startswith("## "):
            break
        chunks.append(line)
    return "\n".join(chunks)


def _parse_tasks(feature: dict) -> List[dict]:
    tasks: List[dict] = []
    body = feature["body_lines"]
    i = 0
    while i < len(body):
        line_no, line = body[i]
        match = TASK_HEADER_RE.match(line)
        if match:
            tid = match.group("id")
            marker = match.group("marker")
            tail = match.group("tail") or ""
            block = _block_text(i, body)
            notes = []
            if "ARCHIVED — NOT ACCEPTED" in block or "archived-not-accepted" in block.lower():
                notes.append("archived-not-accepted")
            if "Acceptance: ✓" in block or "**Acceptance:** ✓" in block:
                notes.append("acceptance-mark")
            tasks.append(
                {
                    "kind": "subtask" if "." in tid else "task",
                    "id": tid,
                    "parent_feature": feature.get("id"),
                    "marker": marker,
                    "path": feature["path"],
                    "line": line_no,
                    "title_tail": tail.strip(),
                    "prerequisites": _extract_prereqs(block),
                    "refs": _extract_refs(block),
                    "has_acceptance_criteria": "Acceptance criteria:" in block
                    or "**Acceptance criteria:**" in block,
                    "has_definition_of_done": "Definition of Done:" in block
                    or "**Definition of Done:**" in block,
                    "notes": notes,
                    "text_sha256": _sha256_bytes(block.encode("utf-8")),
                    "byte_length": len(block.encode("utf-8")),
                }
            )
            i += 1
            continue
        legacy = LEGACY_TASK_RE.match(line)
        if legacy and line.startswith("- [") and "**" in line:
            candidate = re.search(r"\*\*(?P<id>[0-9][0-9.-]*)\*\*", line)
            tasks.append(
                {
                    "kind": "malformed_task",
                    "id": candidate.group("id") if candidate else f"malformed@{feature['path']}:{line_no}",
                    "parent_feature": feature.get("id"),
                    "marker": legacy.group("marker"),
                    "path": feature["path"],
                    "line": line_no,
                    "title_tail": (legacy.group("tail") or "").strip(),
                    "prerequisites": [],
                    "refs": _extract_refs(line),
                    "has_acceptance_criteria": False,
                    "has_definition_of_done": False,
                    "notes": ["malformed-header"],
                    "text_sha256": _sha256_bytes(line.encode("utf-8")),
                    "byte_length": len(line.encode("utf-8")),
                }
            )
        i += 1
    return tasks


def _parse_claim(path: str, text: str) -> dict:
    owner = None
    item = None
    for line in text.splitlines():
        m = re.match(r"^-?\s*owner_token:\s*`?([^`\s]+)`?", line)
        if m:
            owner = m.group(1).strip()
        m = re.match(r"^-?\s*item:\s*`?([^`\s]+)`?", line)
        if m:
            item = m.group(1).strip()
        m = re.search(r"\bowner_token:\s*`([^`]+)`", line)
        if m and owner is None:
            owner = m.group(1)
    return {
        "path": path,
        "item": item,
        "owner_token": owner,
        "sha256": _sha256_bytes(text.encode("utf-8") if isinstance(text, str) else text),
        "size_bytes": len(text.encode("utf-8")),
    }


def inventory_from_blobs(
    blobs: Mapping[str, Tuple[bytes, str]],
    *,
    source_commit: Optional[str],
    run_id: str,
    produced_at: str,
    tool_path: str,
    tool_digest: str,
) -> dict:
    items: List[dict] = []
    findings: List[dict] = []
    features_out: List[dict] = []
    id_index: Dict[str, List[Tuple[str, int]]] = defaultdict(list)

    def add_finding(rule: str, item: str, field: str, locator: str, message: str, severity: str) -> None:
        findings.append(
            {
                "id": _finding_id(rule, item, field, locator),
                "rule": rule,
                "item": item,
                "field": field,
                "locator": locator,
                "message": message,
                "severity": severity,
            }
        )

    for path in ("TODO.md", "DONE.md"):
        if path not in blobs:
            add_finding("INV-SOURCE-MISSING", path, "blob", f"{source_commit or 'tree'}:{path}", f"required source {path} absent", "error")
            continue
        raw, digest = blobs[path]
        text = raw.decode("utf-8")
        for feature in _split_features(path, text):
            if feature["kind"] == "preamble":
                continue
            fid = feature["id"]
            archived = False
            body_text = "\n".join(l for _, l in feature["body_lines"][:40])
            if "ARCHIVED — NOT ACCEPTED" in body_text or fid == ARCHIVED_NOT_ACCEPTED_FEATURE:
                archived = True
            mapping = LOSSLESS
            if feature["malformed_header"]:
                mapping = STABLE_FINDING
                add_finding(
                    "INV-FEATURE-HEADER-MALFORMED",
                    fid or feature["title"],
                    "header",
                    f"{path}:{feature['line']}",
                    "Feature header lacks canonical four-digit ID",
                    "error",
                )
            if archived and fid == ARCHIVED_NOT_ACCEPTED_FEATURE:
                mapping = AUTHORITY_REQUIRED
            feat_item = {
                "kind": "feature",
                "id": fid,
                "title": feature["title"],
                "path": path,
                "line": feature["line"],
                "archive": "archived-not-accepted" if archived and fid == ARCHIVED_NOT_ACCEPTED_FEATURE else (
                    "done" if path == "DONE.md" else "open"
                ),
                "mapping_class": mapping,
                "text_sha256": _sha256_bytes(feature["header"].encode("utf-8")),
            }
            features_out.append(feat_item)
            items.append(feat_item)
            if fid:
                id_index[fid].append((path, feature["line"]))
            tasks = _parse_tasks(feature)
            for task in tasks:
                mapping = LOSSLESS
                notes = list(task["notes"])
                if "malformed-header" in notes or not TASK_ID_RE.fullmatch(str(task["id"])) if task["kind"] != "malformed_task" else True:
                    if task["kind"] == "malformed_task" or "malformed-header" in notes:
                        mapping = STABLE_FINDING
                        add_finding(
                            "INV-TASK-HEADER-MALFORMED",
                            str(task["id"]),
                            "header",
                            f"{task['path']}:{task['line']}",
                            "Task-like checklist entry has a malformed canonical ID/header",
                            "error",
                        )
                if task["marker"] not in VALID_MARKERS:
                    mapping = STABLE_FINDING
                    add_finding(
                        "INV-MARKER-UNDEFINED",
                        str(task["id"]),
                        "marker",
                        f"{task['path']}:{task['line']}",
                        f"undefined marker [{task['marker']}]",
                        "error",
                    )
                for ref in task["refs"]:
                    if ref["kind"] == "pending":
                        mapping = STABLE_FINDING if mapping != AUTHORITY_REQUIRED else mapping
                        add_finding(
                            "INV-REF-PENDING",
                            str(task["id"]),
                            "ref",
                            f"{task['path']}:{task['line']}",
                            "REF is a pending placeholder, not a Git object",
                            "warning",
                        )
                    if ref["value"] in NO_CREDIT_LOCAL_REFS:
                        mapping = AUTHORITY_REQUIRED
                        notes.append("no-evidence-credit")
                        add_finding(
                            "INV-REF-NO-EVIDENCE-CREDIT",
                            str(task["id"]),
                            "ref",
                            f"{task['path']}:{task['line']}:{ref['value']}",
                            f"{ref['value']} is not a Git object and receives no independent evidence credit",
                            "error",
                        )
                    elif ref["kind"] == "local_placeholder":
                        mapping = STABLE_FINDING if mapping != AUTHORITY_REQUIRED else mapping
                        add_finding(
                            "INV-REF-LOCAL-PLACEHOLDER",
                            str(task["id"]),
                            "ref",
                            f"{task['path']}:{task['line']}:{ref['value']}",
                            f"{ref['value']} is not a Git object",
                            "warning",
                        )
                if fid == ARCHIVED_NOT_ACCEPTED_FEATURE:
                    mapping = AUTHORITY_REQUIRED
                    notes.append("parent-archived-not-accepted")
                task_out = dict(task)
                task_out["mapping_class"] = mapping
                task_out["notes"] = sorted(set(notes))
                items.append(task_out)
                id_index[str(task["id"])].append((task["path"], task["line"]))

    for identifier, occurrences in sorted(id_index.items()):
        if len(occurrences) > 1:
            path, line = occurrences[0]
            add_finding(
                "INV-ID-DUPLICATE",
                identifier,
                "id",
                f"{path}:{line}",
                f"ID occurs {len(occurrences)} times across TODO.md/DONE.md",
                "error",
            )
            for item in items:
                if item.get("id") == identifier:
                    item["mapping_class"] = STABLE_FINDING if item.get("mapping_class") == LOSSLESS else item["mapping_class"]

    claims = []
    for path, (raw, digest) in sorted(blobs.items()):
        if not (path.startswith("TODO-") and path.endswith(".md")):
            continue
        text = raw.decode("utf-8")
        claim = _parse_claim(path, text)
        claim["digest"] = digest
        claims.append(claim)
        if not claim.get("owner_token"):
            add_finding(
                "INV-CLAIM-OWNER-TOKEN-MISSING",
                path,
                "owner_token",
                path,
                "claim file does not declare owner_token",
                "warning",
            )

    dispositions = [
        {
            "item": ARCHIVED_NOT_ACCEPTED_FEATURE,
            "disposition": "archived-not-accepted",
            "authority": "DONE.md Feature 0021 archive header",
            "evidence_credit": False,
            "excluded_placeholders": sorted(NO_CREDIT_LOCAL_REFS),
            "mapping_class": AUTHORITY_REQUIRED,
        }
    ]

    classes = {LOSSLESS: [], STABLE_FINDING: [], AUTHORITY_REQUIRED: []}
    for item in items:
        classes.setdefault(item.get("mapping_class") or LOSSLESS, []).append(item.get("id"))

    source_artifacts = []
    for path, (raw, digest) in sorted(blobs.items()):
        source_artifacts.append(
            {
                "path": path,
                "digest": digest,
                "size_bytes": len(raw),
                "source_commit": source_commit,
                "media_type": "text/markdown",
                "classification": "internal",
            }
        )

    counts = {
        "features": sum(1 for i in items if i.get("kind") == "feature"),
        "tasks": sum(1 for i in items if i.get("kind") == "task"),
        "subtasks": sum(1 for i in items if i.get("kind") == "subtask"),
        "malformed_tasks": sum(1 for i in items if i.get("kind") == "malformed_task"),
        "claims": len(claims),
        "findings": len(findings),
        "lossless": sum(1 for i in items if i.get("mapping_class") == LOSSLESS),
        "stable_migration_finding": sum(1 for i in items if i.get("mapping_class") == STABLE_FINDING),
        "authority_required_disposition": sum(
            1 for i in items if i.get("mapping_class") == AUTHORITY_REQUIRED
        ),
        "no_credit_local_refs": sum(
            1
            for i in items
            for r in i.get("refs") or []
            if r.get("value") in NO_CREDIT_LOCAL_REFS
        ),
    }

    inventory = {
        "schema": SCHEMA,
        "run_id": run_id,
        "source_commit": source_commit,
        "produced_at": produced_at,
        "tool": {"path": tool_path, "digest": tool_digest},
        "policy": {
            "feature_0021": "archived-not-accepted",
            "no_evidence_credit": sorted(NO_CREDIT_LOCAL_REFS),
            "databases_mutated": [],
        },
        "counts": counts,
        "source_artifacts": source_artifacts,
        "items": items,
        "claims": claims,
        "findings": findings,
        "dispositions": dispositions,
        "mapping_class_ids": {
            k: [x for x in v if x is not None]
            for k, v in classes.items()
        },
    }
    return inventory


def render_markdown(inventory: dict) -> str:
    c = inventory["counts"]
    lines = [
        f"# Legacy issue-store inventory `{inventory['run_id']}`",
        "",
        f"- Schema: `{inventory['schema']}`",
        f"- Source commit: `{inventory.get('source_commit') or 'fixture-tree'}`",
        f"- Produced at: `{inventory['produced_at']}`",
        f"- Tool: `{inventory['tool']['path']}` (`{inventory['tool']['digest']}`)",
        "",
        "## Policy",
        "",
        "- Feature `0021` is retained as **archived-not-accepted**.",
        "- Placeholders `local-20260815-0021-06` through `-08` receive **no evidence credit**.",
        "- Neither `issues/` nor the provenance event store is modified by this run.",
        "",
        "## Counts",
        "",
        f"- Features: {c['features']}",
        f"- Tasks: {c['tasks']}",
        f"- Subtasks: {c['subtasks']}",
        f"- Malformed task headers: {c['malformed_tasks']}",
        f"- Active claim files: {c['claims']}",
        f"- Findings: {c['findings']}",
        f"- Lossless mappings: {c['lossless']}",
        f"- Stable migration findings: {c['stable_migration_finding']}",
        f"- Authority-required dispositions: {c['authority_required_disposition']}",
        f"- No-credit local placeholders observed: {c['no_credit_local_refs']}",
        "",
        "## Source artifacts",
        "",
    ]
    for art in inventory["source_artifacts"]:
        lines.append(
            f"- `{art['path']}` {art['digest']} ({art['size_bytes']} bytes)"
        )
    lines.extend(["", "## Dispositions", ""])
    for d in inventory["dispositions"]:
        lines.append(
            f"- `{d['item']}`: `{d['disposition']}` (evidence_credit={d['evidence_credit']})"
        )
        lines.append(f"  - excluded: {', '.join('`' + x + '`' for x in d['excluded_placeholders'])}")
    lines.extend(["", "## Findings (stable IDs)", ""])
    if not inventory["findings"]:
        lines.append("- none")
    else:
        for f in inventory["findings"]:
            lines.append(
                f"- `{f['id']}` `{f['rule']}` `{f['item']}` @ `{f['locator']}` — {f['message']}"
            )
    lines.extend(
        [
            "",
            "## Importer fidelity baseline",
            "",
            "A later importer (`0037-14`) MUST:",
            "",
            "1. Preserve item IDs, markers, prerequisite pairs, criterion/DoD text, and source locators (`path:line`).",
            "2. Map `lossless` items without introducing claims, closures, or approvals absent in source.",
            "3. Emit blocking findings whose IDs equal the `INV-` values recorded here for the same rule/item/field/locator tuple.",
            "4. Carry Feature `0021` as archived-not-accepted and refuse to treat `local-20260815-0021-06`…`-08` as Git evidence.",
            "5. Refuse to write live `issues/` or `provenance/events/` when building a disposable candidate.",
            "",
        ]
    )
    return "\n".join(lines)


def artifact_set_doc(inventory: dict, inventory_json_digest: str, inventory_md_digest: str, json_size: int, md_size: int) -> dict:
    members = []
    for art in inventory["source_artifacts"]:
        members.append(
            {
                "path": art["path"],
                "digest": art["digest"],
                "media_type": art["media_type"],
                "size_bytes": art["size_bytes"],
                "source_commit": art["source_commit"] or "0" * 40,
                "classification": "internal",
            }
        )
    members.extend(
        [
            {
                "path": "legacy-inventory.json",
                "digest": inventory_json_digest,
                "media_type": "application/json",
                "size_bytes": json_size,
                "source_commit": inventory.get("source_commit") or "0" * 40,
                "classification": "internal",
            },
            {
                "path": "legacy-inventory.md",
                "digest": inventory_md_digest,
                "media_type": "text/markdown",
                "size_bytes": md_size,
                "source_commit": inventory.get("source_commit") or "0" * 40,
                "classification": "internal",
            },
        ]
    )
    return {
        "schema": "artifact-set@v1",
        "classification": "internal",
        "environment": "development-test",
        "created_at": inventory["produced_at"],
        "members": members,
        "producer_run": inventory["run_id"],
    }


def write_outputs(out_dir: Path, inventory: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_text = _canonical_json(inventory)
    md_text = render_markdown(inventory)
    json_bytes = json_text.encode("utf-8")
    md_bytes = md_text.encode("utf-8")
    (out_dir / "legacy-inventory.json").write_bytes(json_bytes)
    (out_dir / "legacy-inventory.md").write_bytes(md_bytes)
    aset = artifact_set_doc(
        inventory,
        _sha256_bytes(json_bytes),
        _sha256_bytes(md_bytes),
        len(json_bytes),
        len(md_bytes),
    )
    (out_dir / "source-artifact-set.json").write_text(_canonical_json(aset), encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="Git worktree or clone")
    parser.add_argument("--source-commit", help="40-hex commit to inventory")
    parser.add_argument("--from-tree", type=Path, help="Directory with TODO.md/DONE.md/claims (fixtures)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--produced-at", default=None)
    args = parser.parse_args(argv)

    tool_path = "provenance/migrations/issue-store/tools/issue_legacy_inventory.py"
    tool_raw = Path(__file__).read_bytes()
    tool_digest = _sha256_bytes(tool_raw)
    produced_at = args.produced_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.from_tree:
        blobs = load_tree_blobs(args.from_tree)
        commit = args.source_commit
    else:
        if not args.repo or not args.source_commit:
            parser.error("--repo and --source-commit are required unless --from-tree is set")
        blobs = load_commit_blobs(args.repo, args.source_commit)
        commit = args.source_commit

    inventory = inventory_from_blobs(
        blobs,
        source_commit=commit,
        run_id=args.run_id,
        produced_at=produced_at,
        tool_path=tool_path,
        tool_digest=tool_digest,
    )
    write_outputs(args.out, inventory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
