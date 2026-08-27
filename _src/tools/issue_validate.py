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
MAX_PROVENANCE_FILES = 20000
MAX_TRAVERSAL = 100000
UUID7 = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
TYPED_URI = re.compile(
    r"^(issue|criterion|commit|run|campaign|finding|decision|artifact|"
    r"artifact-set|record-version|evidence|curation-item):"
    r"[A-Za-z0-9][A-Za-z0-9._:/@-]{0,255}$")
FILE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
CLASSIFICATIONS = frozenset({"public", "internal", "restricted"})
ENVIRONMENTS = frozenset({"synthetic", "development-test", "production", "assessment"})
TYPED_KINDS = frozenset({
    "issue", "criterion", "commit", "run", "campaign", "finding", "decision",
    "artifact", "artifact-set", "record-version", "evidence", "curation-item",
})
RELATION_ENDPOINTS = {
    "detected-during": (frozenset({"finding"}), frozenset({"run", "campaign"})),
    "reported-by": (frozenset({"finding"}), frozenset({"issue", "curation-item"})),
    "remediates": (frozenset({"commit", "issue"}), frozenset({"finding", "issue"})),
    "implements": (frozenset({"commit", "artifact", "record-version"}),
                   frozenset({"issue", "criterion", "decision"})),
    "verifies": (frozenset({"run", "evidence"}),
                 frozenset({"criterion", "issue", "artifact", "record-version"})),
    "triggered": (frozenset({"issue", "finding", "decision"}),
                  frozenset({"run", "campaign"})),
    "produced-by": (frozenset({"artifact", "artifact-set", "record-version", "evidence"}),
                    frozenset({"run", "campaign"})),
    "derived-from": (frozenset({"artifact", "artifact-set", "record-version", "evidence"}),
                     frozenset({"artifact", "artifact-set", "record-version", "evidence"})),
    "invalidated-by": (frozenset({"artifact", "artifact-set", "record-version",
                                  "evidence", "finding"}),
                       frozenset({"finding", "decision", "run"})),
    "regenerated-by": (frozenset({"artifact", "artifact-set", "record-version"}),
                       frozenset({"run", "campaign"})),
    "supersedes": (frozenset({"issue", "finding", "decision", "artifact", "artifact-set",
                              "record-version", "evidence"}),
                   frozenset({"issue", "finding", "decision", "artifact", "artifact-set",
                              "record-version", "evidence"})),
    "published-as": (frozenset({"artifact", "artifact-set", "record-version"}),
                     frozenset({"artifact", "evidence"})),
    "decides": (frozenset({"decision"}), frozenset({"issue", "finding", "criterion"})),
    "blocks": (frozenset({"issue", "finding", "decision"}),
               frozenset({"issue", "criterion", "run", "campaign"})),
}
ACYCLIC_RELATIONS = frozenset({"derived-from", "supersedes", "blocks"})
RESOLVED_KINDS = frozenset({"finding", "run", "artifact-set", "issue", "criterion"})
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


def _kind_of_uri(uri):
    if not isinstance(uri, str) or ":" not in uri:
        return ""
    return uri.split(":", 1)[0]


def _check_typed_ref(diagnostics, path, field, ref, *, require_digest=False):
    if not isinstance(ref, dict):
        diagnostics.append(Diagnostic("IV0923", "typed reference is not an object",
                                      path, field=field))
        return None
    kind = ref.get("kind")
    uri = ref.get("uri")
    classification = ref.get("classification")
    if kind not in TYPED_KINDS:
        diagnostics.append(Diagnostic("IV0923", f"unknown typed-reference kind {kind!r}",
                                      path, field=f"{field}.kind"))
    if not isinstance(uri, str) or not TYPED_URI.fullmatch(uri):
        diagnostics.append(Diagnostic("IV0923", "malformed typed-reference URI",
                                      path, field=f"{field}.uri"))
    elif kind in TYPED_KINDS and _kind_of_uri(uri) != kind:
        diagnostics.append(Diagnostic("IV0923", "URI scheme does not match kind",
                                      path, field=f"{field}.uri"))
    if classification not in CLASSIFICATIONS:
        diagnostics.append(Diagnostic("IV0923", "invalid classification",
                                      path, field=f"{field}.classification"))
    if classification == "restricted" and "redacted" not in ref:
        diagnostics.append(Diagnostic("IV0933", "restricted reference is missing redacted flag",
                                      path, field=f"{field}.redacted"))
    digest = ref.get("digest")
    if digest is not None and not (isinstance(digest, str) and FILE_DIGEST.fullmatch(digest)):
        diagnostics.append(Diagnostic("IV0923", "malformed digest", path, field=f"{field}.digest"))
    if require_digest and not digest:
        diagnostics.append(Diagnostic("IV0930", "mutable path/reference is missing content digest",
                                      path, field=f"{field}.digest"))
    environment = ref.get("environment")
    if environment is not None and environment not in ENVIRONMENTS:
        diagnostics.append(Diagnostic("IV0923", "invalid environment",
                                      path, field=f"{field}.environment"))
    return ref


def _walk_json(value, prefix=""):
    if isinstance(value, dict):
        yield prefix, value
        for key, child in value.items():
            yield from _walk_json(child, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_json(child, f"{prefix}[{index}]")


def _collect_provenance_files(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ConfigurationError(f"IV0900: provenance root does not exist: {root}")
    base = root / "provenance" if (root / "provenance").is_dir() else root
    values = {}
    for path in sorted(base.rglob("*.json"), key=lambda value: value.as_posix().encode("utf-8")):
        if not path.is_file():
            continue
        relative = path.relative_to(base).as_posix()
        values[relative] = path.read_bytes()
        if len(values) > MAX_PROVENANCE_FILES:
            break
    return values, base


def _classify_prov_path(relative):
    if relative == "public-projection.json" or relative.endswith("/public-projection.json"):
        return "projection"
    if relative.startswith("_views/") or "/_views/" in relative:
        return "view"
    if relative.startswith("events/") or "/events/" in relative:
        return "event"
    if relative.startswith("runs/") or "/runs/" in relative:
        return "run"
    if relative.startswith("findings/") or "/findings/" in relative:
        return "finding"
    if relative.startswith("artifact-sets/") or "/artifact-sets/" in relative:
        return "artifact-set"
    if relative.startswith("fixtures/"):
        return "ignore"
    return "other"


def _register_uri(catalog, collisions, uri, path, payload_digest):
    if not uri:
        return
    previous = catalog.get(uri)
    if previous is None:
        catalog[uri] = (path, payload_digest)
        return
    if previous[1] != payload_digest:
        collisions.append((uri, path, previous[0]))


def _provenance_checks(parsed_issues, provenance_root, projection_path, repo, now):
    diagnostics = []
    files, base = _collect_provenance_files(provenance_root)
    if len(files) > MAX_PROVENANCE_FILES:
        diagnostics.append(Diagnostic("IV0901", f"provenance file count exceeds {MAX_PROVENANCE_FILES}"))
        return diagnostics
    catalog = {}
    collisions = []
    digest_owners = {}
    events = []
    restricted_tokens = set()
    objects_by_type = {"event": [], "run": [], "finding": [], "artifact-set": []}
    views = []
    projections = []

    issue_ids = {value["item"]["id"] for value in parsed_issues.values()}
    criterion_ids = set()
    for value in parsed_issues.values():
        for criterion in value.get("criteria") or []:
            criterion_ids.add(criterion["id"])
        catalog[f"issue:{value['item']['id']}"] = (value["item"]["id"], "issue")

    traversal = 0
    for relative, data in files.items():
        traversal += 1
        if traversal > MAX_TRAVERSAL:
            diagnostics.append(Diagnostic("IV0901", f"traversal exceeds {MAX_TRAVERSAL}", relative))
            return diagnostics
        kind = _classify_prov_path(relative)
        if kind == "ignore":
            continue
        path = f"provenance/{relative}"
        payload = _parse_json_blob(path, data, diagnostics)
        if not isinstance(payload, dict):
            continue
        payload_digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        if kind == "event":
            objects_by_type["event"].append((path, payload))
            _check_event(diagnostics, path, payload)
            event_id = payload.get("event_id")
            if isinstance(event_id, str):
                _register_uri(catalog, collisions, f"event:{event_id}", path, payload_digest)
            events.append((path, payload))
        elif kind == "run":
            objects_by_type["run"].append((path, payload))
            _check_run(diagnostics, path, payload)
            run_id = payload.get("run_id")
            if isinstance(run_id, str):
                _register_uri(catalog, collisions, f"run:{run_id}", path, payload_digest)
                catalog[f"run:{run_id}"] = catalog.get(f"run:{run_id}", (path, payload_digest))
        elif kind == "finding":
            objects_by_type["finding"].append((path, payload))
            _check_finding(diagnostics, path, payload)
            finding_id = payload.get("finding_id")
            if isinstance(finding_id, str):
                _register_uri(catalog, collisions, f"finding:{finding_id}", path, payload_digest)
        elif kind == "artifact-set":
            objects_by_type["artifact-set"].append((path, payload))
            _check_artifact_set(diagnostics, path, payload, digest_owners, repo)
            set_id = payload.get("set_id")
            if isinstance(set_id, str):
                _register_uri(catalog, collisions, f"artifact-set:{set_id}", path, payload_digest)
        elif kind == "view":
            views.append((path, payload))
        elif kind == "projection":
            projections.append((path, payload, data.decode("utf-8", "replace")))
        _collect_restricted_tokens(payload, restricted_tokens)
        env = payload.get("environment")
        classification = payload.get("classification")
        if env == "synthetic" and classification == "production":
            diagnostics.append(Diagnostic(
                "IV0931", "synthetic object is presented as production evidence",
                path, field="environment"))
        if env == "synthetic" and not payload.get("synthetic_reason") and kind == "event":
            diagnostics.append(Diagnostic(
                "IV0931", "synthetic event is missing synthetic_reason",
                path, field="synthetic_reason"))

    for uri, path, previous in collisions:
        diagnostics.append(Diagnostic(
            "IV0927", f"ID collision for {uri} (also {previous})", path, field="id"))

    for digest, owners in digest_owners.items():
        if len(owners) > 1:
            diagnostics.append(Diagnostic(
                "IV0928", f"digest collision {digest} owned by {owners[0]} and {owners[1]}",
                owners[1], field="digest"))

    known_runs = {payload.get("run_id") for _, payload in objects_by_type["run"]}
    known_findings = {payload.get("finding_id") for _, payload in objects_by_type["finding"]}
    known_sets = {payload.get("set_id") for _, payload in objects_by_type["artifact-set"]}

    forward_edges = []
    exclusive_supersede = {}
    for path, payload in events:
        relation = payload.get("relation")
        source = payload.get("source") or {}
        target = payload.get("target") or {}
        source_uri = source.get("uri")
        target_uri = target.get("uri")
        source_kind = source.get("kind")
        target_kind = target.get("kind")
        expected = RELATION_ENDPOINTS.get(relation)
        if expected is None:
            continue
        allowed_source, allowed_target = expected
        if source_kind in allowed_target and target_kind in allowed_source and (
                source_kind not in allowed_source or target_kind not in allowed_target):
            diagnostics.append(Diagnostic(
                "IV0925", f"reversed {relation} edge {source_uri} -> {target_uri}",
                path, field="relation"))
        elif source_kind not in allowed_source or target_kind not in allowed_target:
            diagnostics.append(Diagnostic(
                "IV0923", f"invalid {relation} endpoints {source_kind} -> {target_kind}",
                path, field="relation"))
        if source_uri == target_uri:
            allowed_self = (relation == "derived-from" and source_kind == "record-version"
                            and source_uri != target_uri)
            if not allowed_self:
                diagnostics.append(Diagnostic(
                    "IV0926", "self-edge violates relation cardinality",
                    path, field="source"))
        if relation == "supersedes" and target_uri:
            previous = exclusive_supersede.get(target_uri)
            if previous and previous != source_uri:
                diagnostics.append(Diagnostic(
                    "IV0926", f"multiple superseding sources for {target_uri}",
                    path, field="source"))
            exclusive_supersede[target_uri] = source_uri
        _flag_dangling(diagnostics, path, "source", source, issue_ids, criterion_ids,
                       known_runs, known_findings, known_sets)
        _flag_dangling(diagnostics, path, "target", target, issue_ids, criterion_ids,
                       known_runs, known_findings, known_sets)
        occurred = _parse_time(payload.get("occurred_at"))
        if occurred is not None and now is not None and occurred > now + dt.timedelta(days=1):
            diagnostics.append(Diagnostic(
                "IV0929", "event occurred_at is fabricated future context",
                path, field="occurred_at"))
        run_ref = payload.get("run") or {}
        run_uri = run_ref.get("uri") if isinstance(run_ref, dict) else None
        if run_uri and run_uri.split(":", 1)[-1] not in known_runs and known_runs:
            diagnostics.append(Diagnostic(
                "IV0929", "event cites fabricated run context", path, field="run"))
        if payload.get("environment") == "synthetic" and (
                (target.get("environment") == "production") or
                (source.get("environment") == "production")):
            diagnostics.append(Diagnostic(
                "IV0931", "synthetic event binds production endpoints as production evidence",
                path, field="environment"))
        forward_edges.append((source_uri, relation, target_uri, path))

    _acyclic_provenance(diagnostics, forward_edges)
    _check_views(diagnostics, views, forward_edges)
    extra_projection = None
    if projection_path:
        extra = Path(projection_path)
        if extra.is_file():
            extra_projection = extra.read_text(encoding="utf-8")
            projections.append((str(extra), json.loads(extra_projection), extra_projection))
    _check_projections(diagnostics, projections, restricted_tokens)
    return diagnostics


def _collect_restricted_tokens(payload, tokens):
    for _, value in _walk_json(payload):
        if not isinstance(value, dict):
            continue
        if value.get("classification") == "restricted":
            uri = value.get("uri")
            if isinstance(uri, str):
                tokens.add(uri)
            digest = value.get("digest")
            if isinstance(digest, str):
                tokens.add(digest)
            reason = value.get("redaction_reason")
            if isinstance(reason, str) and reason:
                tokens.add(reason)


def _flag_dangling(diagnostics, path, field, ref, issue_ids, criterion_ids,
                   known_runs, known_findings, known_sets):
    if not isinstance(ref, dict):
        return
    uri = ref.get("uri")
    kind = ref.get("kind")
    if not isinstance(uri, str):
        return
    ident = uri.split(":", 1)[-1]
    missing = False
    if kind == "finding" and known_findings and ident not in known_findings:
        missing = True
    elif kind == "run" and known_runs and ident not in known_runs:
        missing = True
    elif kind == "artifact-set" and known_sets and ident not in known_sets:
        missing = True
    elif kind == "issue" and issue_ids and ident not in issue_ids:
        missing = True
    elif kind == "criterion" and criterion_ids and ident not in criterion_ids:
        missing = True
    if missing:
        diagnostics.append(Diagnostic(
            "IV0924", f"dangling {kind} endpoint {uri}", path, field=field))


def _check_event(diagnostics, path, payload):
    if payload.get("schema_version") != "1.0":
        diagnostics.append(Diagnostic("IV0923", "unsupported provenance-event schema",
                                      path, field="schema_version"))
    event_id = payload.get("event_id")
    if not isinstance(event_id, str) or not UUID7.fullmatch(event_id):
        diagnostics.append(Diagnostic("IV0923", "event_id is not UUIDv7", path, field="event_id"))
    if payload.get("environment") not in ENVIRONMENTS:
        diagnostics.append(Diagnostic("IV0923", "invalid event environment",
                                      path, field="environment"))
    if payload.get("classification") not in CLASSIFICATIONS:
        diagnostics.append(Diagnostic("IV0923", "invalid event classification",
                                      path, field="classification"))
    relation = payload.get("relation")
    if relation not in RELATION_ENDPOINTS:
        diagnostics.append(Diagnostic("IV0923", f"unknown relation {relation!r}",
                                      path, field="relation"))
    _check_typed_ref(diagnostics, path, "source", payload.get("source"))
    _check_typed_ref(diagnostics, path, "target", payload.get("target"))
    if payload.get("run") is not None:
        _check_typed_ref(diagnostics, path, "run", payload.get("run"))


def _check_run(diagnostics, path, payload):
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not UUID7.fullmatch(run_id):
        diagnostics.append(Diagnostic("IV0923", "run_id is not UUIDv7", path, field="run_id"))
    if payload.get("environment") not in ENVIRONMENTS:
        diagnostics.append(Diagnostic("IV0923", "invalid run environment", path, field="environment"))
    if payload.get("classification") == "restricted" and "redacted" not in payload:
        diagnostics.append(Diagnostic("IV0933", "restricted run is missing redacted flag",
                                      path, field="redacted"))
    for field in ("producer",):
        if payload.get(field) is not None:
            _check_typed_ref(diagnostics, path, field, payload.get(field))
    for field in ("inputs", "outputs"):
        for index, ref in enumerate(payload.get(field) or []):
            _check_typed_ref(diagnostics, path, f"{field}[{index}]", ref)


def _check_finding(diagnostics, path, payload):
    finding_id = payload.get("finding_id")
    if not isinstance(finding_id, str) or not UUID7.fullmatch(finding_id):
        diagnostics.append(Diagnostic("IV0923", "finding_id is not UUIDv7",
                                      path, field="finding_id"))
    if payload.get("classification") == "restricted" and not payload.get("redaction_reason"):
        diagnostics.append(Diagnostic(
            "IV0933", "restricted finding is missing redaction_reason",
            path, field="redaction_reason"))
    _check_typed_ref(diagnostics, path, "subject", payload.get("subject"))
    if payload.get("detected_during") is not None:
        _check_typed_ref(diagnostics, path, "detected_during", payload.get("detected_during"))
    for index, ref in enumerate(payload.get("evidence") or []):
        _check_typed_ref(diagnostics, path, f"evidence[{index}]", ref)
    detected = _parse_time(payload.get("detected_at"))
    if detected is None:
        diagnostics.append(Diagnostic("IV0923", "finding detected_at is invalid",
                                      path, field="detected_at"))


def _check_artifact_set(diagnostics, path, payload, digest_owners, repo):
    set_id = payload.get("set_id")
    if not isinstance(set_id, str) or not UUID7.fullmatch(set_id):
        diagnostics.append(Diagnostic("IV0923", "set_id is not UUIDv7", path, field="set_id"))
    set_digest = payload.get("set_digest")
    if not isinstance(set_digest, str) or not FILE_DIGEST.fullmatch(set_digest):
        diagnostics.append(Diagnostic("IV0923", "malformed set_digest", path, field="set_digest"))
    members = payload.get("members") or []
    for index, member in enumerate(members):
        if not isinstance(member, dict):
            diagnostics.append(Diagnostic("IV0923", "artifact member is not an object",
                                          path, field=f"members[{index}]"))
            continue
        member_path = member.get("path")
        digest = member.get("digest")
        if member_path and not digest:
            diagnostics.append(Diagnostic(
                "IV0930", "mutable member path is missing digest",
                path, field=f"members[{index}].digest"))
        elif isinstance(digest, str) and FILE_DIGEST.fullmatch(digest):
            digest_owners.setdefault(digest, []).append(f"{path}#{member_path}")
        if member.get("classification") == "restricted" and "redacted" not in member:
            diagnostics.append(Diagnostic(
                "IV0933", "restricted artifact member is missing redacted flag",
                path, field=f"members[{index}].redacted"))
        commit = member.get("source_commit")
        if commit == "0" * 40:
            diagnostics.append(Diagnostic(
                "IV0929", "fabricated all-zero source_commit context",
                path, field=f"members[{index}].source_commit"))
    if payload.get("producer") is not None:
        _check_typed_ref(diagnostics, path, "producer", payload.get("producer"))


def _acyclic_provenance(diagnostics, edges):
    adjacency = {}
    for source, relation, target, path in edges:
        if relation not in ACYCLIC_RELATIONS or not source or not target:
            continue
        adjacency.setdefault(relation, {}).setdefault(source, []).append((target, path))
    for relation, graph in adjacency.items():
        state = {}

        def visit(node, stack):
            state[node] = 1
            stack.append(node)
            for target, path in graph.get(node, []):
                if state.get(target) == 1:
                    diagnostics.append(Diagnostic(
                        "IV0926", f"{relation} cycle involving {node}",
                        path, field="relation"))
                elif state.get(target, 0) == 0:
                    visit(target, stack)
            stack.pop()
            state[node] = 2

        for node in sorted(graph):
            if state.get(node, 0) == 0:
                visit(node, [])


def _check_views(diagnostics, views, forward_edges):
    expected = {(source, relation, target) for source, relation, target, _ in forward_edges
                if source and relation and target}
    for path, payload in views:
        listed = set()
        raw_edges = payload.get("edges")
        if not isinstance(raw_edges, list):
            diagnostics.append(Diagnostic(
                "IV0934", "reverse index is missing edges table", path, field="edges"))
            continue
        for entry in raw_edges:
            if not isinstance(entry, dict):
                continue
            listed.add((entry.get("source"), entry.get("relation"), entry.get("target")))
        missing = expected - listed
        extra = listed - expected
        if missing or extra:
            diagnostics.append(Diagnostic(
                "IV0934", "stale or incomplete reverse index", path, field="edges"))


def _check_projections(diagnostics, projections, restricted_tokens):
    for path, payload, text in projections:
        if not isinstance(payload, dict):
            continue
        if payload.get("classification") == "restricted":
            diagnostics.append(Diagnostic(
                "IV0932", "public projection retains restricted classification",
                path, field="classification"))
        leaked = [token for token in sorted(restricted_tokens) if token and token in text]
        if leaked:
            diagnostics.append(Diagnostic(
                "IV0932", f"restricted field/endpoint leaked in public projection: {leaked[0]}",
                path, field="projection"))
        redacted_uris = payload.get("redacted_uris") if isinstance(payload, dict) else None
        if isinstance(payload.get("omit_failed"), str):
            diagnostics.append(Diagnostic(
                "IV0933", "public projection replaces restricted values instead of omitting them",
                path, field="omit_failed"))
        for _, value in _walk_json(payload):
            if isinstance(value, dict) and value.get("classification") == "restricted":
                diagnostics.append(Diagnostic(
                    "IV0932", "restricted endpoint leaked in public projection",
                    path, field="classification"))
                break
        del redacted_uris


def validate(*, repo=ROOT, source="working-tree", root=None,
             authoritative_root=None, compare_head=True, now=None,
             provenance_root=None, projection_path=None):
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
    if provenance_root is not None:
        diagnostics.extend(_provenance_checks(current, provenance_root, projection_path, repo, clock))
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
    parser.add_argument("--provenance-root", help="explicit provenance tree (events/runs/findings/views)")
    parser.add_argument("--projection", help="explicit public projection JSON path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        diagnostics, parsed = validate(repo=args.repo, source=args.source, root=args.root,
                                       authoritative_root=args.authoritative_root,
                                       compare_head=not args.no_compare_head,
                                       provenance_root=args.provenance_root,
                                       projection_path=args.projection)
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
