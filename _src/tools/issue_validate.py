#!/usr/bin/env python3
"""Validate structural issue-store invariants in a working tree or Git index."""

from dataclasses import asdict, dataclass
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
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
MAX_SIDECARS = 20000
MAX_SIDECAR_BYTES = 256 * 1024
AUTHORITY_POLICY_REVISION = "issue-authority-policy@v1"
PLACEHOLDER_EVIDENCE = re.compile(r"^(pending|local-[A-Za-z0-9._-]+)$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
LEGAL_TRANSITIONS = {
    "open": frozenset({"open", "in_progress", "blocked", "closed", "withdrawn"}),
    "in_progress": frozenset({"in_progress", "blocked", "closed", "open", "withdrawn"}),
    "blocked": frozenset({"blocked", "in_progress", "open"}),
    "closed": frozenset({"closed"}),
    "withdrawn": frozenset({"withdrawn"}),
}
ACTIVE_CLAIM_STATES = frozenset({"active", "renewing", "proposed", "takeover-pending"})
SIDECAR_SUFFIXES = ("/claim.json", "/closure.json", "/approval.json")


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
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix().encode("utf-8")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.split("/", 1)[0].startswith("_"):
            continue
        keyed = f"issues/{relative}"
        if _is_tracked_issue_input(keyed):
            values[keyed] = path.read_bytes()
    return values


def _index_files(repo):
    output = _git(repo, "ls-files", "-z", "--", "issues")
    values = {}
    for raw in output.split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8")
        if _is_tracked_issue_input(path):
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
        if _is_tracked_issue_input(path):
            values[path] = _git(repo, "show", f"HEAD:{path}")
    return values


def _is_tracked_issue_input(path):
    if path.startswith("issues/_"):
        return False
    if path.endswith("/index.md"):
        return True
    if any(path.endswith(suffix) for suffix in SIDECAR_SUFFIXES):
        return True
    return "/decisions/" in path and path.endswith(".json")


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
            if not relative.endswith("/index.md"):
                continue
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


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parse_json_blob(path, data, diagnostics):
    if len(data) > MAX_SIDECAR_BYTES:
        diagnostics.append(Diagnostic("IV0901", f"sidecar exceeds {MAX_SIDECAR_BYTES} bytes", path))
        return None
    try:
        text = data.decode("utf-8")
        return json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        diagnostics.append(Diagnostic("IV0915", f"malformed JSON sidecar: {exc}", path, field="json"))
        return None


def _claim_digest(payload):
    body = {key: value for key, value in payload.items() if key != "cas_ref_digest"}
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def _parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _object_type(repo, sha):
    try:
        kind = _git(repo, "cat-file", "-t", sha, text=True).strip()
    except ConfigurationError:
        return None
    return kind


def _is_ancestor(repo, ancestor, head="HEAD"):
    try:
        _git(repo, "merge-base", "--is-ancestor", ancestor, head)
        return True
    except ConfigurationError:
        return False


def _split_sidecars(files):
    items = {}
    claims = {}
    closures = {}
    approvals = {}
    decisions = {}
    for path, data in files.items():
        if path.endswith("/index.md"):
            items[path] = data
        elif path.endswith("/claim.json"):
            claims[path] = data
        elif path.endswith("/closure.json"):
            closures[path] = data
        elif path.endswith("/approval.json"):
            approvals[path] = data
        elif "/decisions/" in path and path.endswith(".json"):
            decisions[path] = data
    return items, claims, closures, approvals, decisions


def _dir_of(index_path):
    return index_path.rsplit("/", 1)[0]


def _lifecycle_checks(parsed, files, repo, *, now, compare_head, head_sha=None):
    diagnostics = []
    item_files, claim_files, closure_files, approval_files, decision_files = _split_sidecars(files)
    if (len(claim_files) + len(closure_files) + len(approval_files) + len(decision_files)) > MAX_SIDECARS:
        diagnostics.append(Diagnostic("IV0901", f"sidecar count exceeds {MAX_SIDECARS}"))
        return diagnostics

    by_id = {value["item"]["id"]: (path, value) for path, value in parsed.items()}
    claims_by_item = {}
    for path, data in claim_files.items():
        payload = _parse_json_blob(path, data, diagnostics)
        if not isinstance(payload, dict):
            continue
        item_id = payload.get("item_id")
        directory = path.rsplit("/", 1)[0]
        expected = directory.rsplit("/", 1)[-1]
        if item_id != expected:
            diagnostics.append(Diagnostic("IV0915", "claim item_id does not match canonical path",
                                          path, str(item_id or ""), field="item_id"))
        cas_ref = payload.get("cas_ref")
        if cas_ref != f"refs/autodocs/claims/{item_id}":
            diagnostics.append(Diagnostic("IV0915", "invalid claim CAS ref", path, str(item_id or ""),
                                          field="cas_ref"))
        digest = payload.get("cas_ref_digest")
        if isinstance(payload, dict) and digest != _claim_digest(payload):
            diagnostics.append(Diagnostic("IV0915", "CAS digest does not match canonical claim bytes",
                                          path, str(item_id or ""), field="cas_ref_digest"))
        issued = _parse_time(payload.get("issued_at"))
        expires = _parse_time(payload.get("expires_at"))
        if issued is None or expires is None or not (issued < expires):
            diagnostics.append(Diagnostic("IV0915", "issued_at must precede expires_at", path,
                                          str(item_id or ""), field="expires_at"))
        base = payload.get("base_commit")
        if not (isinstance(base, str) and COMMIT_SHA.fullmatch(base)):
            diagnostics.append(Diagnostic("IV0915", "base_commit is not a 40-hex commit id", path,
                                          str(item_id or ""), field="base_commit"))
        elif compare_head and not _is_ancestor(repo, base):
            diagnostics.append(Diagnostic("IV0914", "claim base_commit is stale relative to HEAD",
                                          path, str(item_id or ""), field="base_commit"))
        state = payload.get("state")
        if state in ACTIVE_CLAIM_STATES and expires is not None and now > expires:
            diagnostics.append(Diagnostic("IV0912", "claim is expired while remaining in an active state",
                                          path, str(item_id or ""), field="expires_at"))
        if item_id:
            claims_by_item.setdefault(item_id, []).append((path, payload))

    active_scopes = []
    for item_id, entries in claims_by_item.items():
        live = [(path, payload) for path, payload in entries
                if payload.get("state") in {"active", "renewing"}]
        if len(live) > 1:
            diagnostics.append(Diagnostic("IV0913", "overlapping claims for the same item",
                                          live[1][0], item_id, field="state"))
        for path, payload in live:
            scopes = payload.get("write_scopes") or []
            for other_path, other_scopes, other_id in active_scopes:
                if item_id == other_id:
                    continue
                if _scopes_overlap(scopes, other_scopes):
                    diagnostics.append(Diagnostic(
                        "IV0913", f"write scope overlaps claim for {other_id}",
                        path, item_id, field="write_scopes"))
            active_scopes.append((path, scopes, item_id))

    closures_by_item = {}
    for path, data in closure_files.items():
        payload = _parse_json_blob(path, data, diagnostics)
        if not isinstance(payload, dict):
            continue
        item_id = payload.get("item_id")
        directory = path.rsplit("/", 1)[0]
        expected = directory.rsplit("/", 1)[-1]
        if item_id != expected:
            diagnostics.append(Diagnostic("IV0916", "closure item_id does not match path", path,
                                          str(item_id or ""), field="item_id"))
        closures_by_item[item_id] = (path, payload)

    approvals_by_dir = {}
    for path, data in approval_files.items():
        payload = _parse_json_blob(path, data, diagnostics)
        if not isinstance(payload, dict):
            continue
        directory = path.rsplit("/", 1)[0]
        approvals_by_dir[directory] = (path, payload)
        if payload.get("signature_verified") is not True:
            diagnostics.append(Diagnostic("IV0918", "approval signature is not verified", path,
                                          field="signature_verified"))
        if payload.get("schema") != "issue-approval@v1":
            diagnostics.append(Diagnostic("IV0918", "unsupported approval schema/policy revision",
                                          path, field="schema"))

    revoked = set()
    for path, data in decision_files.items():
        payload = _parse_json_blob(path, data, diagnostics)
        if not isinstance(payload, dict):
            continue
        if payload.get("kind") == "approval" and payload.get("status") == "rejected":
            revoked.add(payload.get("item_id"))
            diagnostics.append(Diagnostic("IV0918", "approval decision is revoked/rejected", path,
                                          payload.get("item_id") or "", field="status"))

    for path, value in parsed.items():
        item = value["item"]
        item_id = item["id"]
        state = item["state"]
        directory = _dir_of(path)
        live_claims = [payload for _, payload in claims_by_item.get(item_id, [])
                       if payload.get("state") in {"active", "renewing"}]
        if state == "in_progress" and not live_claims:
            diagnostics.append(Diagnostic("IV0911", "in_progress item has no active claim",
                                          path, item_id, field="state"))
        if state != "closed" and item_id in closures_by_item:
            diagnostics.append(Diagnostic("IV0910", "closure present for a non-closed item",
                                          closures_by_item[item_id][0], item_id, field="state"))
        if state == "closed":
            _check_closure(diagnostics, repo, path, value, closures_by_item.get(item_id),
                           approvals_by_dir.get(directory), revoked, now, head_sha)

    return diagnostics


def _scopes_overlap(left, right):
    for a in left:
        for b in right:
            if a == b or a.startswith(b.rstrip("/") + "/") or b.startswith(a.rstrip("/") + "/"):
                return True
    return False


def _check_closure(diagnostics, repo, path, parsed_item, closure_entry, approval_entry,
                   revoked, now, head_sha):
    item = parsed_item["item"]
    item_id = item["id"]
    if closure_entry is None:
        diagnostics.append(Diagnostic("IV0916", "closed item is missing terminal closure.json",
                                      path, item_id, field="closure"))
        return
    closure_path, closure = closure_entry
    disposition = closure.get("disposition")
    if disposition == "archived-not-accepted":
        if any(entry.get("result") == "pass" for entry in closure.get("validation") or []):
            diagnostics.append(Diagnostic(
                "IV0922", "archived-not-accepted closure must not present validation success credit",
                closure_path, item_id, field="validation"))
        if disposition == "completed":
            pass
    if item_id == "0021" and disposition == "completed":
        diagnostics.append(Diagnostic("IV0922", "Feature 0021 must remain archived-not-accepted",
                                      closure_path, item_id, field="disposition"))
    if disposition == "completed":
        criteria = {entry["id"]: entry for entry in parsed_item.get("criteria") or []
                    if entry.get("status") == "active"}
        closed_by_id = {entry.get("id"): entry for entry in closure.get("criteria") or []}
        for criterion_id in criteria:
            record = closed_by_id.get(criterion_id)
            if record is None or record.get("status") != "checked":
                diagnostics.append(Diagnostic(
                    "IV0916", f"active criterion {criterion_id} is not checked in closure",
                    closure_path, item_id, field=f"criteria.{criterion_id}"))
            else:
                _check_evidence(diagnostics, repo, closure_path, item_id, criterion_id,
                                record.get("evidence") or [])
        if approval_entry is None:
            diagnostics.append(Diagnostic(
                "IV0916", "completed closure requires role approval evidence",
                closure_path, item_id, field="approval"))
        elif item_id in revoked:
            diagnostics.append(Diagnostic("IV0918", "completed closure cites a revoked approval",
                                          closure_path, item_id, field="approval"))
        refs = closure.get("commit_refs") or []
        unique = []
        for sha in refs:
            if not isinstance(sha, str) or not COMMIT_SHA.fullmatch(sha):
                diagnostics.append(Diagnostic("IV0919", "commit ref is not a 40-hex object id",
                                              closure_path, item_id, field="commit_refs"))
                continue
            if PLACEHOLDER_EVIDENCE.fullmatch(sha):
                diagnostics.append(Diagnostic("IV0917", "placeholder commit ref is not evidence",
                                              closure_path, item_id, field="commit_refs"))
                continue
            kind = _object_type(repo, sha)
            if kind is None:
                diagnostics.append(Diagnostic("IV0917", f"commit ref {sha} is not reachable",
                                              closure_path, item_id, field="commit_refs"))
            elif kind != "commit":
                diagnostics.append(Diagnostic("IV0919", f"object {sha} is {kind}, not a commit",
                                              closure_path, item_id, field="commit_refs"))
            unique.append(sha)
        if len(set(unique)) < 2:
            diagnostics.append(Diagnostic(
                "IV0920", "two-commit rule violated: need distinct substantive and bookkeeping refs",
                closure_path, item_id, field="commit_refs"))
        if head_sha and unique and set(unique) == {head_sha}:
            diagnostics.append(Diagnostic(
                "IV0920", "closure commit_refs name only the current/same commit",
                closure_path, item_id, field="commit_refs"))


def _check_evidence(diagnostics, repo, path, item_id, criterion_id, evidence):
    for locator in evidence:
        if not isinstance(locator, str) or PLACEHOLDER_EVIDENCE.fullmatch(locator):
            diagnostics.append(Diagnostic(
                "IV0917", f"criterion {criterion_id} uses placeholder or empty evidence",
                path, item_id, field=f"criteria.{criterion_id}.evidence"))
            continue
        if locator.startswith("commit:"):
            sha = locator.split(":", 1)[1]
            if not COMMIT_SHA.fullmatch(sha) or _object_type(repo, sha) != "commit":
                diagnostics.append(Diagnostic(
                    "IV0917", f"criterion {criterion_id} evidence commit is not reachable",
                    path, item_id, field=f"criteria.{criterion_id}.evidence"))
        elif locator.startswith("sha256:"):
            continue
        else:
            file_part = locator.split("#", 1)[0]
            if file_part and not (Path(repo) / file_part).is_file():
                # Repository-relative path may exist only as a git blob.
                try:
                    _git(repo, "cat-file", "-e", f"HEAD:{file_part}")
                except ConfigurationError:
                    diagnostics.append(Diagnostic(
                        "IV0917", f"criterion {criterion_id} evidence path is not reachable: {file_part}",
                        path, item_id, field=f"criteria.{criterion_id}.evidence"))


def _feature_closure_checks(parsed):
    diagnostics = []
    by_parent = {}
    for path, value in parsed.items():
        parent = value["item"].get("parent")
        if parent:
            by_parent.setdefault(parent, []).append((path, value))
    for path, value in parsed.items():
        item = value["item"]
        if item["level"] != "feature" or item["state"] != "closed":
            continue
        for child_path, child in by_parent.get(item["id"], []):
            if child["item"]["state"] != "closed":
                diagnostics.append(Diagnostic(
                    "IV0921", f"Feature closed while child {child['item']['id']} is not terminal",
                    path, item["id"], field="state"))
    return diagnostics


def _transition_checks(current, baseline):
    diagnostics = []
    old_by_id = {value["item"]["id"]: value["item"]["state"] for value in baseline.values()}
    for path, value in current.items():
        item_id = value["item"]["id"]
        new_state = value["item"]["state"]
        old_state = old_by_id.get(item_id)
        if old_state is None:
            continue
        allowed = LEGAL_TRANSITIONS.get(old_state, frozenset())
        if new_state not in allowed:
            diagnostics.append(Diagnostic(
                "IV0910", f"illegal lifecycle transition {old_state} -> {new_state}",
                path, item_id, field="state"))
    return diagnostics


def validate(*, repo=ROOT, source="working-tree", root=None,
             authoritative_root=None, compare_head=True, now=None):
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
    clock = now or dt.datetime.now(dt.timezone.utc)
    head_sha = None
    if compare_head:
        baseline_files = (_working_files(authoritative_root) if authoritative_root is not None
                          else _head_files(repo))
        baseline, baseline_diagnostics = _parse_snapshot(baseline_files, repo)
        del baseline_diagnostics
        diagnostics.extend(_criterion_history(current, baseline))
        diagnostics.extend(_transition_checks(current, baseline))
        try:
            head_sha = _git(repo, "rev-parse", "HEAD", text=True).strip()
        except ConfigurationError:
            head_sha = None
    diagnostics.extend(_graph_checks(current))
    diagnostics.extend(_lifecycle_checks(current, files, repo, now=clock,
                                         compare_head=compare_head, head_sha=head_sha))
    diagnostics.extend(_feature_closure_checks(current))
    return sorted(set(diagnostics)), current


def result_payload(diagnostics, source, item_count):
    return {
        "schema": "issue-validation-result@v1",
        "source": source,
        "status": "PASS" if not diagnostics else "FAIL",
        "exit_code": EXIT_OK if not diagnostics else EXIT_INVALID,
        "item_count": item_count,
        "authority_policy_revision": AUTHORITY_POLICY_REVISION,
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
