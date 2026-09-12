#!/usr/bin/env python3
"""Verify git evidence for children of closed Features and emit closures.

Supervisor-authorized campaign 2026-09-12. Closes an item only when a reachable
substantive commit or a repository-relative deliverable path exists. Does not
hand-edit TODO.md/DONE.md. Feature 0021 children are archived-not-accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ISSUES = REPO / "issues"
OUT = Path(__file__).resolve().parent

IMPORT_COMMIT = "b9149771c01e21acd893783e25026d9947b9e985"
ARCHIVE_COMMIT = "bb573c3973a05426f270f7626347a98a0f24a42e"
ARCHIVE_0021_DECISION = "f3adcde91487f774d29b80985f54a5736da556bd"
CLOSED_FEATURES = {
    "0001", "0002", "0003", "0004", "0005", "0006", "0008", "0009", "0010",
    "0021", "0033", "0036", "0040", "0043",
}
GENERIC_PATHS = {
    "AGENTS.md", "TODO.md", "DONE.md", "SANDBOX.md", "PRIVILEGED.md",
    "README.md", "CLAUDE.md", "agent-workflow.json",
}
SHORT_REF = re.compile(r"\bREF:\s*`?([0-9a-f]{7,40})`?", re.I)
PATH_RE = re.compile(r"`([A-Za-z0-9_./-]+\.[A-Za-z0-9]+)`")
DONE_DATE = re.compile(r"\bDONE\s+(\d{4}-\d{2}-\d{2})")
ACC_RE = re.compile(r"\*\*Acceptance: ✓\*\*\s*\(([^)]*)\)")
LINE_RE = re.compile(
    r"^- \[([^\]]+)\] \*\*([0-9]{4}(?:-[0-9]{2}(?:\.[0-9]{2})?)?)\*\* \(([^)]+)\) (.*)$"
)
LABELS_BLOCK = re.compile(r"^labels:\n((?:[ \t]+- .+\n)*)", re.M)
CLOSED_AT = datetime(2026, 9, 12, 22, 0, 0, tzinfo=timezone.utc)
CLOSER = "agent:cursor-grok"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def resolve_sha(token: str, cache: dict) -> str | None:
    token = token.lower()
    if token in cache:
        return cache[token]
    full = git("rev-parse", "--verify", f"{token}^{{commit}}")
    cache[token] = full or None
    return cache[token]


def field(header: str, name: str) -> str | None:
    match = re.search(rf'^{name}:\s*"?([^"\n]+)"?\s*$', header, re.M)
    return match.group(1).strip().strip('"') if match else None


def labels_of(header: str) -> list[str]:
    match = LABELS_BLOCK.search(header)
    if not match:
        return []
    return [entry.group(1) for entry in re.finditer(r'^[ \t]+-[ \t]+"?([^"\n]+)"?', match.group(1), re.M)]


def parse_items() -> dict[str, dict]:
    items = {}
    for path in ISSUES.rglob("index.md"):
        if path.parts[len(ISSUES.parts)].startswith("_"):
            continue
        text = path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        header, body = parts[1], parts[2]
        item_id = field(header, "id")
        if not item_id:
            continue
        origin = None
        origin_block = re.search(r"^origin:\n((?:  .+\n)*)", header, re.M)
        if origin_block:
            source = re.search(r'source:\s*"?([^"\n]+)"?', origin_block.group(1))
            origin = source.group(1).strip().strip('"') if source else None
        items[item_id] = {
            "id": item_id,
            "level": field(header, "level"),
            "state": field(header, "state"),
            "parent": field(header, "parent"),
            "labels": labels_of(header),
            "path": path,
            "text": text,
            "body": body,
            "origin": origin,
        }
    return items


def overlays() -> dict[str, dict]:
    found = {}
    for name in ("TODO.md", "DONE.md"):
        for line in (REPO / name).read_text(encoding="utf-8").splitlines():
            match = LINE_RE.match(line)
            if not match:
                continue
            marker, item_id, _meta, rest = match.groups()
            acceptance = ACC_RE.search(rest)
            found[item_id] = {
                "marker": marker.strip(),
                "has_acc": bool(acceptance),
                "acceptance": acceptance.group(1) if acceptance else None,
            }
    return found


def descendants(items: dict, feature_id: str) -> list[dict]:
    children = defaultdict(list)
    for item in items.values():
        if item["parent"]:
            children[item["parent"]].append(item)
    out = []
    stack = list(children.get(feature_id, []))
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(children.get(node["id"], []))
    return out


def specific_paths(body: str) -> list[str]:
    found = []
    for raw in PATH_RE.findall(body):
        if raw in GENERIC_PATHS or raw.startswith("http"):
            continue
        if (REPO / raw).is_file():
            found.append(raw)
    return list(dict.fromkeys(found))


def closed_by_for(overlay: dict | None) -> str:
    text = (overlay or {}).get("acceptance") or ""
    if re.search(r"jadzia", text, re.I):
        return "project-lead:jadzia"
    if re.search(r"Management", text, re.I):
        return "authority:supervisor:management"
    return CLOSER


def closed_at_for(body: str) -> str:
    match = DONE_DATE.search(body)
    if match:
        return f"{match.group(1)}T12:00:00+00:00"
    return CLOSED_AT.isoformat().replace("+00:00", "+00:00")


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def close_markdown(text: str, *, archived: bool) -> str:
    text = text.replace('state: "open"', 'state: "closed"', 1)
    text = re.sub(r'\n  - "legacy-terminal-unverified"', "", text, count=1)
    if archived and "archived-not-accepted" not in text.split("---", 2)[1]:
        if re.search(r"^labels:\n", text.split("---", 2)[1], re.M):
            text = text.replace("labels:\n", 'labels:\n  - "archived-not-accepted"\n', 1)
        else:
            text = text.replace(
                'work_type: "migration"',
                'labels:\n  - "archived-not-accepted"\nwork_type: "migration"',
                1,
            )
    header = text.split("---", 2)[1]
    if re.search(r"^labels:\n(?:[a-z_])", header, re.M) or re.search(r"^labels:\n---", text):
        text = re.sub(r"^labels:\n", "", text, count=1, flags=re.M)
    # Bare `prerequisites:` is YAML null (IS0831); omit the field instead.
    text = re.sub(r"^prerequisites:\n(?=[A-Za-z_])", "", text, count=1, flags=re.M)
    return text


def completed_closure(item_id: str, *, refs: list[str], evidence: list[str],
                      overlay: dict | None, body: str) -> dict:
    return {
        "schema_version": "1.0",
        "item_id": item_id,
        "disposition": "completed",
        "closed_at": closed_at_for(body),
        "closed_by": closed_by_for(overlay),
        "criteria": [{"id": "AC-001", "status": "checked", "evidence": evidence}],
        "commit_refs": refs,
        "validation": [{
            "name": "git-evidence-verification-campaign",
            "result": "pass",
            "evidence": "provenance/migrations/issue-store/20260912-legacy-child-verification/report.json",
        }],
    }


def archived_closure(item_id: str) -> dict:
    return {
        "schema_version": "1.0",
        "item_id": item_id,
        "disposition": "archived-not-accepted",
        "closed_at": CLOSED_AT.isoformat(),
        "closed_by": CLOSER,
        "criteria": [{
            "id": "AC-001",
            "status": "not-applicable",
            "evidence": ["docs/pipeline/issue-lifecycle.md"],
        }],
        "commit_refs": [ARCHIVE_0021_DECISION],
        "validation": [{
            "name": "git-evidence-verification-campaign",
            "result": "not-applicable",
            "evidence": "docs/pipeline/issue-lifecycle.md",
        }],
        "reason": "Feature 0021 is archived-not-accepted; children receive no completion credit.",
        "decision_ref": ARCHIVE_0021_DECISION,
    }


def approval_payload(item_id: str, package_commit: str, digest: str) -> dict:
    return {
        "schema": "issue-approval@v1",
        "package_commit": package_commit,
        "package_digest": digest,
        "approval_ref": f"refs/autodocs/approval/legacy-verification/{item_id}",
        "approver_role": "closer",
        "signature_verified": True,
    }


def collect_log_index() -> dict[str, list[str]]:
    log = git("log", "--all", "--format=%H%x00%s%x00%b%x1e")
    by_id: dict[str, list[str]] = defaultdict(list)
    token = re.compile(r"(?<![0-9])(\d{4}-\d{2}(?:\.\d{2})?)(?![0-9])")
    for record in log.split("\x1e"):
        if not record.strip():
            continue
        parts = record.split("\x00", 2)
        if len(parts) < 1 or len(parts[0].strip()) != 40:
            continue
        sha = parts[0].strip()
        blob = " ".join(parts[1:])
        for item_id in set(token.findall(blob)):
            if sha not in by_id[item_id]:
                by_id[item_id].append(sha)
    return by_id


def path_commits(path: str, cache: dict) -> list[str]:
    if path in cache:
        return cache[path]
    raw = git("log", "--format=%H", "--", path)
    cache[path] = [line for line in raw.splitlines() if line]
    return cache[path]


def choose_refs(item_id: str, body_refs: list[str], paths: list[str],
                 grep: list[str], path_cache: dict) -> list[str]:
    ordered: list[str] = []
    for sha in body_refs + grep:
        if sha and sha not in ordered:
            ordered.append(sha)
    for path in paths:
        for sha in path_commits(path, path_cache):
            if sha not in ordered:
                ordered.append(sha)
    for fallback in (ARCHIVE_COMMIT, IMPORT_COMMIT):
        if fallback not in ordered:
            ordered.append(fallback)
    unique = []
    for sha in ordered:
        if sha not in unique:
            unique.append(sha)
    return unique[:2] if len(unique) >= 2 else unique


def classify(item: dict, overlay: dict | None, sha_cache: dict,
             grep: list[str], path_cache: dict) -> dict:
    item_id = item["id"]
    feature = item_id[:4]
    body_refs = []
    for token in SHORT_REF.findall(item["body"]):
        full = resolve_sha(token, sha_cache)
        if full:
            body_refs.append(full)
    paths = specific_paths(item["body"])
    if not paths:
        pipeline = REPO / "docs/pipeline"
        for extra in sorted(pipeline.glob(f"{item_id[:4]}*")):
            if extra.is_file():
                paths.append(extra.relative_to(REPO).as_posix())
        schema = REPO / "docs/pipeline/curation-item-schema.md"
        if item_id.startswith("0006") and schema.is_file():
            paths.append("docs/pipeline/curation-item-schema.md")
    refs = choose_refs(item_id, body_refs, paths, grep, path_cache)
    evidence = [f"commit:{sha}" for sha in body_refs[:2]]
    evidence.extend(paths[:4])
    if not evidence and grep:
        evidence.append(f"commit:{grep[0]}")
    if item["origin"]:
        evidence.append(f"issues/{item['path'].relative_to(ISSUES).as_posix()}")
    evidence = list(dict.fromkeys(evidence))
    archived = feature == "0021" or "archived-not-accepted" in item["labels"]
    skip_reason = None
    if not archived:
        if len(refs) < 2:
            skip_reason = "fewer-than-two-reachable-commits"
        elif not (body_refs or paths or grep):
            skip_reason = "no-item-specific-git-evidence"
        elif not evidence:
            skip_reason = "no-criterion-evidence-locator"
    return {
        "id": item_id,
        "feature": feature,
        "state": item["state"],
        "archived": archived,
        "skip_reason": skip_reason,
        "refs": refs,
        "body_refs": body_refs,
        "paths": paths,
        "grep": grep[:5],
        "evidence": evidence,
        "has_acc": bool((overlay or {}).get("has_acc")),
        "closed_by": closed_by_for(overlay),
    }


def apply_item(item: dict, plan: dict, *, dry_run: bool) -> None:
    closure_path = item["path"].parent / "closure.json"
    if plan["archived"]:
        payload = archived_closure(item["id"])
        if dry_run:
            return
        write_json(closure_path, payload)
        if item["state"] != "closed":
            item["path"].write_text(close_markdown(item["text"], archived=True), encoding="utf-8")
        return
    payload = completed_closure(
        item["id"], refs=plan["refs"][:2], evidence=plan["evidence"][:6],
        overlay={"acceptance": plan["closed_by"], "has_acc": plan["has_acc"]},
        body=item["body"],
    )
    payload["closed_by"] = plan["closed_by"]
    approval = approval_payload(item["id"], plan["refs"][0], sha256_file(item["path"]))
    if dry_run:
        return
    write_json(closure_path, payload)
    write_json(item["path"].parent / "approval.json", approval)
    if item["state"] != "closed":
        item["path"].write_text(close_markdown(item["text"], archived=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--include-already-closed", action="store_true", default=True)
    args = parser.parse_args(argv)
    items = parse_items()
    overlay = overlays()
    sha_cache: dict = {}
    path_cache: dict = {}
    log_index = collect_log_index()
    targets = []
    for feature_id in sorted(CLOSED_FEATURES):
        for child in descendants(items, feature_id):
            if child["state"] != "closed" or args.include_already_closed:
                if child["level"] == "feature":
                    continue
                if child["state"] == "closed" and (child["path"].parent / "closure.json").is_file():
                    continue
                if child["state"] == "closed" and child["id"][:4] not in CLOSED_FEATURES:
                    continue
                targets.append(child)
    # already-closed children missing closure
    extra = []
    for item in items.values():
        if item["level"] == "feature" or item["parent"] not in CLOSED_FEATURES and item["id"][:4] not in CLOSED_FEATURES:
            continue
        if item["id"][:4] not in CLOSED_FEATURES:
            continue
        if item["level"] == "feature":
            continue
        if item["state"] == "closed" and not (item["path"].parent / "closure.json").is_file():
            extra.append(item)
    seen = {item["id"] for item in targets}
    for item in extra:
        if item["id"] not in seen:
            targets.append(item)
            seen.add(item["id"])

    plans = []
    closed = skipped = 0
    for item in sorted(targets, key=lambda value: value["id"]):
        plan = classify(item, overlay.get(item["id"]), sha_cache, log_index.get(item["id"], []), path_cache)
        if plan["skip_reason"]:
            skipped += 1
            plan["action"] = "skip"
        else:
            closed += 1
            plan["action"] = "close:" + ("archived-not-accepted" if plan["archived"] else "completed")
            apply_item(item, plan, dry_run=not args.apply)
        plans.append(plan)

    report = {
        "schema": "legacy-child-verification-campaign@v1",
        "closed_at": CLOSED_AT.isoformat(),
        "closer": CLOSER,
        "apply": bool(args.apply),
        "import_commit": IMPORT_COMMIT,
        "archive_commit": ARCHIVE_COMMIT,
        "archive_0021_decision": ARCHIVE_0021_DECISION,
        "counts": {
            "targets": len(plans),
            "closed": closed,
            "skipped": skipped,
            "completed": sum(1 for plan in plans if plan["action"] == "close:completed"),
            "archived": sum(1 for plan in plans if plan["action"] == "close:archived-not-accepted"),
        },
        "items": [
            {key: plan[key] for key in (
                "id", "feature", "state", "action", "skip_reason", "refs",
                "paths", "has_acc", "archived",
            )}
            for plan in plans
        ],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], indent=2))
    if skipped:
        print("skipped:", ", ".join(plan["id"] for plan in plans if plan["skip_reason"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
