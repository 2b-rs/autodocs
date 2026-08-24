#!/usr/bin/env python3
"""Validate structural issue-store invariants in a working tree or Git index."""

from dataclasses import asdict, dataclass
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
STORE_PATH = ROOT / "_src/tools/issue_store.py"
SPEC = importlib.util.spec_from_file_location("issue_store", STORE_PATH)
STORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STORE)

EXIT_OK = 0
EXIT_INVALID = 2
EXIT_USAGE = 3
MAX_ITEMS = 10000
MAX_EDGES = 100000


@dataclass(frozen=True, order=True)
class Diagnostic:
    rule: str
    message: str
    path: str = ""
    item: str = ""
    line: int = 0
    field: str = ""


class ConfigurationError(RuntimeError):
    pass


def _git(repo, *args, text=False):
    command = ["git", "-C", str(repo), *args]
    try:
        return subprocess.run(command, check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=text).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr.strip() if getattr(exc, "stderr", None) else str(exc)
        raise ConfigurationError(f"IV0900: git command failed: {' '.join(command)}: {detail}")


def _working_files(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ConfigurationError(f"IV0900: candidate root does not exist: {root}")
    values = {}
    for path in sorted(root.rglob("index.md"), key=lambda value: value.as_posix().encode("utf-8")):
        relative = path.relative_to(root).as_posix()
        if relative.split("/", 1)[0].startswith("_"):
            continue
        values[f"issues/{relative}"] = path.read_bytes()
    return values


def _index_files(repo):
    output = _git(repo, "ls-files", "-z", "--", "issues")
    values = {}
    for raw in output.split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8")
        if path.endswith("/index.md") and not path.startswith("issues/_"):
            values[path] = _git(repo, "show", f":{path}")
    return values


def _head_files(repo):
    try:
        output = _git(repo, "ls-tree", "-r", "--name-only", "-z", "HEAD", "--", "issues")
    except ConfigurationError:
        return {}
    values = {}
    for raw in output.split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8")
        if path.endswith("/index.md") and not path.startswith("issues/_"):
            values[path] = _git(repo, "show", f"HEAD:{path}")
    return values


def _snapshot(files, repository_root):
    """Materialize a bounded read-only input snapshot outside the repository."""
    temporary = tempfile.TemporaryDirectory(prefix="issue-validate-")
    root = Path(temporary.name)
    for relative in (STORE.SCHEMA_PATH, STORE.TOOL_PATH):
        source = Path(repository_root) / relative
        if not source.is_file():
            temporary.cleanup()
            raise ConfigurationError(f"IV0900: required parser input missing: {source}")
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for relative, data in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return temporary, root


def _parse_snapshot(files, repository_root):
    parsed = {}
    diagnostics = []
    temporary, root = _snapshot(files, repository_root)
    try:
        if len(files) > MAX_ITEMS:
            diagnostics.append(Diagnostic("IV0901", f"item count exceeds {MAX_ITEMS}"))
            return parsed, diagnostics
        for relative in sorted(files, key=lambda value: value.encode("utf-8")):
            path = root / relative
            try:
                item = STORE.parse_issue(path, issues_root=root / "issues", repository_root=root)
                item["source"]["path"] = relative
                parsed[relative] = item
            except STORE.IssueStoreError as exc:
                diagnostics.append(Diagnostic(
                    exc.rule_id, str(exc).split(": ", 1)[-1], relative,
                    line=exc.line or 0, field=exc.field or ""))
    finally:
        temporary.cleanup()
    return parsed, diagnostics


def _criterion_history(current, baseline):
    diagnostics = []
    for path, old in baseline.items():
        if path not in current:
            continue
        old_by_id = {entry["id"]: entry for entry in old["criteria"]}
        new_by_id = {entry["id"]: entry for entry in current[path]["criteria"]}
        for criterion_id, old_entry in old_by_id.items():
            item_id = current[path]["item"]["id"]
            if criterion_id not in new_by_id:
                diagnostics.append(Diagnostic(
                    "IV0907", "previously allocated criterion is missing instead of tombstoned",
                    path, item_id, field=f"criteria.{criterion_id}"))
            elif old_entry["status"] != "active" and new_by_id[criterion_id]["status"] == "active":
                diagnostics.append(Diagnostic(
                    "IV0908", "withdrawn/superseded/moved criterion ID was reused as active",
                    path, item_id, new_by_id[criterion_id]["locator"]["line_start"],
                    f"criteria.{criterion_id}"))
    return diagnostics


def _graph_checks(parsed):
    diagnostics = []
    by_id = {}
    for path, value in parsed.items():
        item_id = value["item"]["id"]
        if item_id in by_id:
            diagnostics.append(Diagnostic("IV0902", "duplicate item ID", path, item_id, field="id"))
        else:
            by_id[item_id] = (path, value)
    edges = []
    for item_id, (path, value) in by_id.items():
        for target in value["item"].get("prerequisites", []):
            edges.append((item_id, target))
            if target == item_id:
                diagnostics.append(Diagnostic("IV0903", "self-dependency", path, item_id,
                                              field="prerequisites"))
            elif target not in by_id:
                diagnostics.append(Diagnostic("IV0904", f"missing prerequisite endpoint {target}",
                                              path, item_id, field="prerequisites"))
            elif value["item"]["level"] != "feature" and by_id[target][1]["item"]["level"] == "feature":
                diagnostics.append(Diagnostic(
                    "IV0905", "Feature closure cannot be used as a Task/Subtask implementation start gate",
                    path, item_id, field="prerequisites"))
    if len(edges) > MAX_EDGES:
        diagnostics.append(Diagnostic("IV0901", f"edge count exceeds {MAX_EDGES}"))
        return diagnostics
    adjacency = {item_id: [] for item_id in by_id}
    for source, target in edges:
        if target in adjacency and target != source:
            adjacency[source].append(target)
    state = {}
    stack = []

    def visit(node):
        state[node] = 1
        stack.append(node)
        for target in sorted(adjacency[node]):
            if state.get(target) == 1:
                cycle = stack[stack.index(target):] + [target]
                path = by_id[node][0]
                diagnostics.append(Diagnostic("IV0906", "dependency cycle: " + " -> ".join(cycle),
                                              path, node, field="prerequisites"))
            elif state.get(target, 0) == 0:
                visit(target)
        stack.pop()
        state[node] = 2

    for node in sorted(adjacency):
        if state.get(node, 0) == 0:
            visit(node)
    return diagnostics


def validate(*, repo=ROOT, source="working-tree", root=None,
             authoritative_root=None, compare_head=True):
    repo = Path(repo).resolve()
    if source == "working-tree":
        files = _working_files(root or repo / "issues")
    elif source == "staged-index":
        if root is not None:
            raise ConfigurationError("IV0900: --root is incompatible with staged-index source")
        files = _index_files(repo)
    else:
        raise ConfigurationError(f"IV0900: unsupported source {source!r}")
    current, diagnostics = _parse_snapshot(files, repo)
    if compare_head:
        baseline_files = (_working_files(authoritative_root) if authoritative_root is not None
                          else _head_files(repo))
        baseline, baseline_diagnostics = _parse_snapshot(baseline_files, repo)
        # Historical malformed data is not attributed to the candidate. Only
        # compare histories when the baseline item itself parsed successfully.
        del baseline_diagnostics
        diagnostics.extend(_criterion_history(current, baseline))
    diagnostics.extend(_graph_checks(current))
    return sorted(set(diagnostics)), current


def result_payload(diagnostics, source, item_count):
    return {
        "schema": "issue-validation-result@v1",
        "source": source,
        "status": "PASS" if not diagnostics else "FAIL",
        "exit_code": EXIT_OK if not diagnostics else EXIT_INVALID,
        "item_count": item_count,
        "diagnostics": [asdict(value) for value in diagnostics],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--source", choices=("working-tree", "staged-index"), default="working-tree")
    parser.add_argument("--root", help="explicit candidate issue root for working-tree mode")
    parser.add_argument("--authoritative-root", help="explicit read-only baseline issue root (default: HEAD)")
    parser.add_argument("--no-compare-head", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        diagnostics, parsed = validate(repo=args.repo, source=args.source, root=args.root,
                                       authoritative_root=args.authoritative_root,
                                       compare_head=not args.no_compare_head)
        payload = result_payload(diagnostics, args.source, len(parsed))
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            for diagnostic in diagnostics:
                print(f"{diagnostic.rule} {diagnostic.path}:{diagnostic.line} "
                      f"item={diagnostic.item} field={diagnostic.field}: {diagnostic.message}")
            print(payload["status"])
        return payload["exit_code"]
    except ConfigurationError as exc:
        print(exc, file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
