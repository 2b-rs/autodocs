#!/usr/bin/env python3
"""Deterministic, read-only collision planner for legacy Task scopes."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

import legacy_task_doctor

REQUEST_SCHEMA = "legacy-scope-planner-request@v1"
RESULT_SCHEMA = "legacy-scope-planner-result@v1"
DAG_SCHEMA = "issue-regeneration-dag@v1"
DAG_PATH = "docs/pipeline/issue-derived-artifacts-v1.json"
MAX_REQUEST_BYTES = 1024 * 1024
MAX_DAG_BYTES = 1024 * 1024
MAX_PARTICIPANTS = 128
MAX_SCOPES = 4096
MAX_ACTIONS = 512
MAX_EXPANDED_SCOPES = 16384
MAX_COLLISIONS = 16384
MAX_PATH_BYTES = 512
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GLOB_CHARS = "*?["


class ContractError(ValueError):
    """A closed-contract input is invalid."""


class DuplicateKeyError(ContractError):
    pass


def _pairs_no_duplicates(pairs: Sequence[Tuple[str, object]]) -> Dict[str, object]:
    result: Dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _load_json(raw: bytes, label: str, limit: int) -> object:
    if len(raw) > limit:
        raise ContractError(f"{label} exceeds {limit} bytes")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_no_duplicates)
    except UnicodeDecodeError as exc:
        raise ContractError(f"{label} is not UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid {label} JSON: {exc.msg}") from exc


def _canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _closed(value: object, required: Set[str], optional: Set[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    keys = set(value)
    missing = sorted(required - keys)
    unknown = sorted(keys - required - optional)
    if missing:
        raise ContractError(f"{label} missing fields: {', '.join(missing)}")
    if unknown:
        raise ContractError(f"{label} unknown fields: {', '.join(unknown)}")
    return value


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ContractError(f"{label} must be a stable identifier")
    return value


def _safe_path(value: object, label: str, *, glob: bool = False) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > MAX_PATH_BYTES:
        raise ContractError(f"{label} must be a non-empty bounded POSIX path")
    if "\\" in value or value.startswith("/") or value.endswith("/") or "//" in value:
        raise ContractError(f"{label} must be a normalized relative POSIX path")
    path = PurePosixPath(value)
    if value != path.as_posix() or any(part in ("", ".", "..") for part in path.parts):
        raise ContractError(f"{label} must be a normalized relative POSIX path")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ContractError(f"{label} may not contain control characters")
    if not path.parts or path.parts[0] in (".git", "run.sh"):
        raise ContractError(f"{label} may not address .git or root run.sh")
    if not glob and any(character in value for character in GLOB_CHARS):
        raise ContractError(f"{label} may not contain a glob")
    return value


def _scope(value: object, label: str) -> Dict[str, str]:
    item = _closed(value, {"path", "kind"}, set(), label)
    path = _safe_path(item["path"], f"{label}.path")
    kind = item["kind"]
    if kind not in ("file", "directory"):
        raise ContractError(f"{label}.kind must be file or directory")
    return {"path": path, "kind": str(kind)}


def _scope_list(value: object, label: str) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    if len(value) > MAX_SCOPES:
        raise ContractError(f"{label} exceeds {MAX_SCOPES} entries")
    result = [_scope(item, f"{label}[{index}]") for index, item in enumerate(value)]
    keys = [(item["path"], item["kind"]) for item in result]
    if len(keys) != len(set(keys)):
        raise ContractError(f"{label} contains duplicate scopes")
    return sorted(result, key=lambda item: (item["path"], item["kind"]))


def _path_matches(path: str, pattern: str) -> bool:
    # fnmatch does not give ** its segment semantics, so test both the literal
    # pattern and its zero-directory form.
    if fnmatch.fnmatchcase(path, pattern):
        return True
    while "**/" in pattern:
        pattern = pattern.replace("**/", "", 1)
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def _validate_dag(value: object) -> Dict[str, object]:
    dag = _closed(value, {"schema", "generation_id_rule", "stages"}, set(), "DAG")
    if dag["schema"] != DAG_SCHEMA or not isinstance(dag["generation_id_rule"], str):
        raise ContractError(f"DAG must use {DAG_SCHEMA}")
    stages_value = dag["stages"]
    if not isinstance(stages_value, list) or not stages_value or len(stages_value) > 128:
        raise ContractError("DAG.stages must be a non-empty bounded array")
    required = {"id", "argv", "depends_on", "inputs", "outputs", "sole_writer", "required", "retention", "privacy", "determinism", "promotion_group", "cleanup", "validator"}
    stages: List[Dict[str, object]] = []
    ids: Set[str] = set()
    output_owner: Dict[str, str] = {}
    for index, raw_stage in enumerate(stages_value):
        stage = dict(_closed(raw_stage, required, set(), f"DAG.stages[{index}]"))
        stage_id = _identifier(stage["id"], f"DAG.stages[{index}].id")
        if stage_id in ids:
            raise ContractError(f"duplicate DAG stage id: {stage_id}")
        ids.add(stage_id)
        if stage["sole_writer"] != stage_id:
            raise ContractError(f"DAG stage {stage_id} must be its own sole_writer")
        argv = stage["argv"]
        if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or not arg for arg in argv):
            raise ContractError(f"DAG stage {stage_id} has invalid argv")
        depends = stage["depends_on"]
        if not isinstance(depends, list) or any(not isinstance(item, str) for item in depends) or len(depends) != len(set(depends)):
            raise ContractError(f"DAG stage {stage_id} has invalid dependencies")
        inputs = stage["inputs"]
        if not isinstance(inputs, list):
            raise ContractError(f"DAG stage {stage_id} inputs must be an array")
        normalized_inputs = []
        for input_index, raw_input in enumerate(inputs):
            entry = _closed(raw_input, {"glob", "kind"}, set(), f"DAG stage {stage_id} input {input_index}")
            pattern = _safe_path(entry["glob"], f"DAG stage {stage_id} input glob", glob=True)
            if entry["kind"] not in ("canonical", "configuration", "derived"):
                raise ContractError(f"DAG stage {stage_id} has invalid input kind")
            normalized_inputs.append({"glob": pattern, "kind": entry["kind"]})
        input_keys = [(entry["glob"], entry["kind"]) for entry in normalized_inputs]
        if len(input_keys) != len(set(input_keys)):
            raise ContractError(f"DAG stage {stage_id} repeats an input")
        outputs_value = stage["outputs"]
        if not isinstance(outputs_value, list) or not outputs_value:
            raise ContractError(f"DAG stage {stage_id} outputs must be non-empty")
        outputs = [_safe_path(item, f"DAG stage {stage_id} output") for item in outputs_value]
        if len(outputs) != len(set(outputs)):
            raise ContractError(f"DAG stage {stage_id} repeats an output")
        for output in outputs:
            if output in output_owner:
                raise ContractError(f"DAG output {output} has multiple sole writers")
            output_owner[output] = stage_id
        if not isinstance(stage["required"], bool):
            raise ContractError(f"DAG stage {stage_id} required must be boolean")
        if stage["promotion_group"] is not None:
            _identifier(stage["promotion_group"], f"DAG stage {stage_id} promotion_group")
        for field in ("retention", "privacy", "determinism", "cleanup", "validator"):
            if not isinstance(stage[field], str) or not stage[field]:
                raise ContractError(f"DAG stage {stage_id} has invalid {field}")
        stage["id"] = stage_id
        stage["depends_on"] = list(depends)
        stage["inputs"] = normalized_inputs
        stage["outputs"] = outputs
        stages.append(stage)

    by_id = {str(stage["id"]): stage for stage in stages}
    for stage in stages:
        stage_id = str(stage["id"])
        for dependency in stage["depends_on"]:
            if dependency not in by_id:
                raise ContractError(f"DAG stage {stage_id} has unknown dependency {dependency}")
            if dependency == stage_id:
                raise ContractError(f"DAG stage {stage_id} depends on itself")

    visiting: Set[str] = set()
    visited: Set[str] = set()
    def visit(stage_id: str) -> None:
        if stage_id in visiting:
            raise ContractError(f"DAG contains a cycle at {stage_id}")
        if stage_id in visited:
            return
        visiting.add(stage_id)
        for dependency in by_id[stage_id]["depends_on"]:
            visit(str(dependency))
        visiting.remove(stage_id)
        visited.add(stage_id)
    for stage_id in sorted(by_id):
        visit(stage_id)

    def ancestors(stage_id: str) -> Set[str]:
        result: Set[str] = set()
        pending = list(by_id[stage_id]["depends_on"])
        while pending:
            dependency = str(pending.pop())
            if dependency not in result:
                result.add(dependency)
                pending.extend(by_id[dependency]["depends_on"])
        return result

    for stage in stages:
        stage_id = str(stage["id"])
        prior = ancestors(stage_id)
        for entry in stage["inputs"]:
            if entry["kind"] != "derived":
                continue
            producer = output_owner.get(str(entry["glob"]))
            if producer is None:
                raise ContractError(f"DAG stage {stage_id} derived input has no exact producer: {entry['glob']}")
            if producer not in prior:
                raise ContractError(f"DAG stage {stage_id} does not depend on derived-input producer {producer}")
    return {"schema": DAG_SCHEMA, "generation_id_rule": dag["generation_id_rule"], "stages": stages}


def _validate_request(value: object) -> Dict[str, object]:
    request = _closed(value, {"schema", "participants", "snapshots"}, set(), "request")
    if request["schema"] != REQUEST_SCHEMA:
        raise ContractError(f"request.schema must equal {REQUEST_SCHEMA}")
    participants_value = request["participants"]
    if not isinstance(participants_value, list) or not participants_value or len(participants_value) > MAX_PARTICIPANTS:
        raise ContractError("request.participants must be a non-empty bounded array")
    participants: List[Dict[str, object]] = []
    ids: Set[str] = set()
    actor_ids: Set[str] = set()
    global_action_ids: Set[str] = set()
    action_count = 0
    for index, raw in enumerate(participants_value):
        item = dict(_closed(raw, {"id", "actor", "reads", "writes", "sources", "actions", "after"}, set(), f"participant[{index}]"))
        if isinstance(item["id"], str) and item["id"].startswith(("claim:", "@")):
            raise ContractError(f"participant id uses reserved prefix: {item['id']}")
        participant_id = _identifier(item["id"], f"participant[{index}].id")
        if participant_id.startswith(("claim:", "@")):
            raise ContractError(f"participant id uses reserved prefix: {participant_id}")
        if participant_id in ids:
            raise ContractError(f"duplicate participant id: {participant_id}")
        ids.add(participant_id)
        actor = dict(_closed(item["actor"], {"id"}, {"owner_token", "claim_path"}, f"participant {participant_id}.actor"))
        actor["id"] = _identifier(actor["id"], f"participant {participant_id}.actor.id")
        if actor["id"] in actor_ids:
            raise ContractError(f"duplicate actor id: {actor['id']}")
        actor_ids.add(str(actor["id"]))
        supplied = {"owner_token", "claim_path"} & set(actor)
        if supplied and supplied != {"owner_token", "claim_path"}:
            raise ContractError(f"participant {participant_id} must supply owner_token and claim_path together")
        if supplied:
            actor["owner_token"] = _identifier(actor["owner_token"], f"participant {participant_id}.actor.owner_token")
            actor["claim_path"] = _safe_path(actor["claim_path"], f"participant {participant_id}.actor.claim_path")
            if not str(actor["claim_path"]).startswith("TODO-") or not str(actor["claim_path"]).endswith(".md"):
                raise ContractError(f"participant {participant_id} claim_path must name a legacy claim")
        reads = _scope_list(item["reads"], f"participant {participant_id}.reads")
        writes = _scope_list(item["writes"], f"participant {participant_id}.writes")
        sources = _scope_list(item["sources"], f"participant {participant_id}.sources")
        if any(scope["kind"] != "file" for scope in sources):
            raise ContractError(f"participant {participant_id} sources must be exact files")
        actions_value = item["actions"]
        if not isinstance(actions_value, list):
            raise ContractError(f"participant {participant_id}.actions must be an array")
        action_count += len(actions_value)
        if action_count > MAX_ACTIONS:
            raise ContractError(f"request exceeds {MAX_ACTIONS} actions")
        actions: List[Dict[str, object]] = []
        action_ids: Set[str] = set()
        for action_index, raw_action in enumerate(actions_value):
            action = dict(_closed(raw_action, {"id", "type", "outputs", "prefixes", "promotion_group"}, set(), f"participant {participant_id}.action[{action_index}]"))
            action_id = _identifier(action["id"], f"participant {participant_id}.action.id")
            if action_id in action_ids or action_id in global_action_ids:
                raise ContractError(f"duplicate action id: {action_id}")
            action_ids.add(action_id)
            global_action_ids.add(action_id)
            if action["type"] not in ("generator", "i18n", "publication"):
                raise ContractError(f"action {action_id} has unsupported type")
            action["outputs"] = _scope_list(action["outputs"], f"action {action_id}.outputs")
            action["prefixes"] = _scope_list(action["prefixes"], f"action {action_id}.prefixes")
            if not action["outputs"] and not action["prefixes"]:
                raise ContractError(f"action {action_id} must declare an output or prefix")
            if any(scope["kind"] != "directory" for scope in action["prefixes"]):
                raise ContractError(f"action {action_id} prefixes must be directory scopes")
            if action["promotion_group"] is not None:
                action["promotion_group"] = _identifier(action["promotion_group"], f"action {action_id}.promotion_group")
            actions.append(action)
        after = item["after"]
        if not isinstance(after, list) or any(not isinstance(value, str) for value in after) or len(after) != len(set(after)):
            raise ContractError(f"participant {participant_id}.after must contain unique participant ids")
        participants.append({"id": participant_id, "actor": actor, "reads": reads, "writes": writes, "sources": sources, "actions": actions, "after": sorted(after)})
    for participant in participants:
        for dependency in participant["after"]:
            if dependency not in ids or dependency == participant["id"]:
                raise ContractError(f"participant {participant['id']} has invalid after dependency {dependency}")

    snapshots = _closed(request["snapshots"], {"git", "runner"}, set(), "request.snapshots")
    git = _closed(snapshots["git"], {"head", "index_tree", "worktree_digest", "dirty"}, set(), "request.snapshots.git")
    runner = _closed(snapshots["runner"], {"snapshot_id", "reads", "writes"}, set(), "request.snapshots.runner")
    if not isinstance(git["head"], str) or not COMMIT_RE.fullmatch(git["head"]):
        raise ContractError("request.snapshots.git.head must be a full lowercase commit")
    if not isinstance(git["index_tree"], str) or not COMMIT_RE.fullmatch(git["index_tree"]):
        raise ContractError("request.snapshots.git.index_tree must be a full lowercase tree OID")
    if not isinstance(git["worktree_digest"], str) or not DIGEST_RE.fullmatch(git["worktree_digest"]):
        raise ContractError("request.snapshots.git.worktree_digest must be a sha256 digest")
    snapshot_id = _identifier(runner["snapshot_id"], "request.snapshots.runner.snapshot_id")
    return {"schema": REQUEST_SCHEMA, "participants": participants, "snapshots": {"git": {"head": git["head"], "index_tree": git["index_tree"], "worktree_digest": git["worktree_digest"], "dirty": _scope_list(git["dirty"], "git.dirty")}, "runner": {"snapshot_id": snapshot_id, "reads": _scope_list(runner["reads"], "runner.reads"), "writes": _scope_list(runner["writes"], "runner.writes")}}}


def _check_scope_target(root: Path, scope: Mapping[str, str], label: str, *, require_existing: bool = False) -> None:
    current = root
    parts = PurePosixPath(scope["path"]).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            if require_existing:
                raise ContractError(f"{label} target does not exist: {scope['path']}")
            return
        except OSError as exc:
            raise ContractError(f"{label} target cannot be inspected: {scope['path']}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ContractError(f"{label} traverses symlink: {scope['path']}")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            raise ContractError(f"{label} has a non-directory ancestor: {scope['path']}")
        if index == len(parts) - 1:
            expected = stat.S_ISREG(info.st_mode) if scope["kind"] == "file" else stat.S_ISDIR(info.st_mode)
            if not expected:
                raise ContractError(f"{label} existing target type mismatches {scope['kind']}: {scope['path']}")


def _validate_scope_targets(root: Path, request: Mapping[str, object]) -> None:
    for participant in request["participants"]:
        participant_id = str(participant["id"])
        for field in ("reads", "writes", "sources"):
            for scope in participant[field]:
                _check_scope_target(root, scope, f"participant {participant_id}.{field}")
        for action in participant["actions"]:
            for field in ("outputs", "prefixes"):
                for scope in action[field]:
                    _check_scope_target(root, scope, f"action {action['id']}.{field}")
    for scope in request["snapshots"]["git"]["dirty"]:
        _check_scope_target(root, scope, "git.dirty")
    for field in ("reads", "writes"):
        for scope in request["snapshots"]["runner"][field]:
            _check_scope_target(root, scope, f"runner.{field}")


def _infer_claim_scope(root: Path, value: str) -> Optional[Dict[str, str]]:
    try:
        path = _safe_path(value, "doctor claim scope")
    except ContractError:
        return None
    target = root / path
    try:
        info = target.lstat()
    except OSError:
        return None
    if stat.S_ISLNK(info.st_mode):
        return None
    if stat.S_ISREG(info.st_mode):
        kind = "file"
    elif stat.S_ISDIR(info.st_mode):
        kind = "directory"
    else:
        return None
    scope = {"path": path, "kind": kind}
    try:
        _check_scope_target(root, scope, "doctor claim scope", require_existing=True)
    except ContractError:
        return None
    return scope


def _doctor_digest(report: Mapping[str, object]) -> str:
    return _sha256(_canonical_bytes(report))


def _merge_active_claims(root: Path, request: Dict[str, object], report: Mapping[str, object]) -> Tuple[List[Dict[str, object]], List[str]]:
    participants = [dict(item) for item in request["participants"]]
    by_claim = {
        str(item["actor"].get("claim_path")): item
        for item in participants
        if item["actor"].get("claim_path") is not None
    }
    problems: List[str] = []
    normalized = report.get("normalized", {})
    claims = normalized.get("claims", []) if isinstance(normalized, dict) else []
    if report.get("verdict") == "INCOMPLETE" or not isinstance(claims, list):
        return participants, ["legacy_task_doctor scan is incomplete"]
    active = [claim for claim in claims if isinstance(claim, dict) and claim.get("state") == "p"]
    active_paths = {claim.get("path") for claim in active}
    claim_integrity_rules = {
        "LTD-CLAIM-FIELDS-MISSING", "LTD-CLAIM-FIELD-DUPLICATE",
        "LTD-CLAIM-IDENTITY-MISMATCH", "LTD-CLAIM-SCOPE-MISSING",
        "LTD-CLAIM-SCOPE-MISMATCH", "LTD-CLAIM-SCOPE-INVALID",
    }
    findings = report.get("findings", [])
    if isinstance(findings, list):
        for finding in findings:
            if isinstance(finding, dict) and finding.get("path") in active_paths and finding.get("rule") in claim_integrity_rules:
                problems.append(f"active claim {finding.get('path')} is malformed: {finding.get('rule')}")
    for claim in sorted(active, key=lambda item: str(item.get("path", ""))):
        path = claim.get("path")
        owner = claim.get("owner_token")
        if not isinstance(path, str) or not isinstance(owner, str):
            problems.append(f"active claim {path or '<unknown>'} has incomplete identity")
            continue
        supplied = by_claim.get(path)
        if supplied is not None:
            actor = supplied["actor"]
            if actor.get("owner_token") != owner or actor.get("id") != owner:
                problems.append(f"participant {supplied['id']} does not exactly match active claim {path}")
            doctor_scopes = set(claim.get("scopes", [])) if isinstance(claim.get("scopes"), list) else set()
            supplied_scopes = {scope["path"] for scope in supplied["writes"]}
            if doctor_scopes != supplied_scopes:
                problems.append(f"participant {supplied['id']} write paths do not exactly match doctor claim {path}")
            continue
        raw_scopes = claim.get("scopes")
        if not isinstance(raw_scopes, list) or not raw_scopes:
            problems.append(f"foreign active claim {path} has missing scope")
            continue
        inferred = [_infer_claim_scope(root, value) for value in raw_scopes]
        if any(value is None for value in inferred):
            problems.append(f"foreign active claim {path} has unknown or malformed exact scope")
            continue
        participants.append({
            "id": f"claim:{path}",
            "actor": {"id": owner, "owner_token": owner, "claim_path": path},
            "reads": [], "writes": sorted(inferred, key=lambda item: (item["path"], item["kind"])),
            "sources": [], "actions": [], "after": [], "foreign_claim": True,
        })
    participant_ids = [str(item["id"]) for item in participants]
    if len(participant_ids) != len(set(participant_ids)):
        problems.append("participant IDs are not unique after active-claim synthesis")
    return sorted(participants, key=lambda item: str(item["id"])), sorted(problems)


def _descendants(stages: Sequence[Mapping[str, object]], initial: Set[str]) -> Set[str]:
    selected = set(initial)
    changed = True
    while changed:
        changed = False
        for stage in stages:
            stage_id = str(stage["id"])
            if stage_id not in selected and any(str(dep) in selected for dep in stage["depends_on"]):
                selected.add(stage_id)
                changed = True
    return selected


def _producer_chain(stages: Sequence[Mapping[str, object]], source: str, target_stage: str, source_kind: str = "file") -> List[str]:
    by_id = {str(stage["id"]): stage for stage in stages}
    starts = sorted(_source_stages(stages, source, source_kind))
    queue: List[Tuple[str, List[str]]] = [(stage, [source, stage]) for stage in starts]
    seen: Set[str] = set()
    while queue:
        current, chain = queue.pop(0)
        if current == target_stage:
            return chain
        if current in seen:
            continue
        seen.add(current)
        for candidate in sorted(by_id):
            if current in by_id[candidate]["depends_on"]:
                queue.append((candidate, chain + [candidate]))
    return [source, target_stage]


def _glob_epsilon_closure(pattern: Sequence[str], states: Set[int]) -> Set[int]:
    result = set(states)
    pending = list(states)
    while pending:
        index = pending.pop()
        if index < len(pattern) and pattern[index] == "**" and index + 1 not in result:
            result.add(index + 1)
            pending.append(index + 1)
    return result


def _directory_intersects_input_glob(directory: str, pattern: str) -> bool:
    """Return whether a glob can match at least one path below a directory.

    Matching is segment based: ``issues`` intersects ``issues/**/*.md`` while
    ``issues-archive`` does not. ``**`` may consume zero or more whole segments;
    other wildcard syntax is confined to one segment by ``fnmatchcase``.
    """
    pattern_parts = PurePosixPath(pattern).parts
    states = _glob_epsilon_closure(pattern_parts, {0})
    for segment in PurePosixPath(directory).parts:
        next_states: Set[int] = set()
        for index in states:
            if index >= len(pattern_parts):
                continue
            pattern_segment = pattern_parts[index]
            if pattern_segment == "**":
                next_states.add(index)
            elif fnmatch.fnmatchcase(segment, pattern_segment):
                next_states.add(index + 1)
        states = _glob_epsilon_closure(pattern_parts, next_states)
        if not states:
            return False
    # A contained input must consume at least one additional segment. Any
    # nonterminal NFA state can do so; a fully consumed exact pattern cannot.
    return any(index < len(pattern_parts) for index in states)


def _source_stages(stages: Sequence[Mapping[str, object]], path: str, kind: str = "file") -> Set[str]:
    def matches(pattern: str) -> bool:
        if kind == "directory":
            return _directory_intersects_input_glob(path, pattern)
        return _path_matches(path, pattern)

    return {
        str(stage["id"])
        for stage in stages
        if any(entry["kind"] != "derived" and matches(str(entry["glob"])) for entry in stage["inputs"])
    }


def _entries(participants: Sequence[Mapping[str, object]], dag: Mapping[str, object], snapshots: Mapping[str, object]) -> Tuple[List[Dict[str, object]], Dict[str, List[str]], List[str]]:
    stages = dag["stages"]
    entries: List[Dict[str, object]] = []
    groups: Dict[str, List[str]] = {}
    problems: List[str] = []
    for participant in participants:
        participant_id = str(participant["id"])
        write_paths = {scope["path"] for scope in participant["writes"]}
        for mode in ("reads", "writes"):
            for scope in participant[mode]:
                entries.append({"participant": participant_id, "mode": mode[:-1], "path": scope["path"], "kind": scope["kind"], "origin": "explicit", "chain": [scope["path"]]})
        source_by_path = {source["path"]: source for source in participant["sources"]}
        for source in participant["sources"]:
            if not _source_stages(stages, source["path"], source["kind"]):
                problems.append(f"participant {participant_id} source matches no authoritative non-derived DAG input: {source['path']}")
        for scope in participant["writes"]:
            if _source_stages(stages, scope["path"], scope["kind"]):
                source_by_path.setdefault(scope["path"], {"path": scope["path"], "kind": scope["kind"]})
        for source_path in sorted(source_by_path):
            source = source_by_path[source_path]
            if source_path not in write_paths:
                entries.append({"participant": participant_id, "mode": "write", "path": source_path, "kind": source["kind"], "origin": "source", "chain": [source_path]})
            initial = _source_stages(stages, source_path, source["kind"])
            for stage_id in sorted(_descendants(stages, initial)):
                stage = next(item for item in stages if item["id"] == stage_id)
                chain = _producer_chain(stages, source_path, stage_id, source["kind"])
                group = stage.get("promotion_group")
                if group:
                    groups.setdefault(str(group), []).append(participant_id)
                for output in stage["outputs"]:
                    entries.append({"participant": participant_id, "mode": "derived", "path": output, "kind": "file", "origin": "source-derived", "producer": stage_id, "sole_writer": stage["sole_writer"], "promotion_group": group, "chain": chain + [output]})
        for action in participant["actions"]:
            if action["promotion_group"]:
                groups.setdefault(str(action["promotion_group"]), []).append(participant_id)
            for scope in list(action["outputs"]) + list(action["prefixes"]):
                entries.append({"participant": participant_id, "mode": "write", "path": scope["path"], "kind": scope["kind"], "origin": "action", "action": action["id"], "promotion_group": action["promotion_group"], "chain": [action["id"], scope["path"]]})
    for scope in snapshots["git"]["dirty"]:
        entries.append({"participant": "@git-dirty", "mode": "write", "path": scope["path"], "kind": scope["kind"], "origin": "git", "chain": ["git-dirty", scope["path"]]})
    for mode in ("reads", "writes"):
        for scope in snapshots["runner"][mode]:
            entries.append({"participant": "@runner", "mode": mode[:-1], "path": scope["path"], "kind": scope["kind"], "origin": "runner", "chain": ["runner-snapshot", scope["path"]]})
    if len(entries) > MAX_EXPANDED_SCOPES:
        raise ContractError(f"expanded scopes exceed {MAX_EXPANDED_SCOPES} entries")
    entries.sort(key=lambda item: (str(item["participant"]), str(item["path"]), str(item["mode"]), str(item["origin"])))
    return entries, {key: sorted(set(value)) for key, value in sorted(groups.items())}, sorted(problems)


def _overlap(left: Mapping[str, object], right: Mapping[str, object]) -> Optional[str]:
    left_path, right_path = str(left["path"]), str(right["path"])
    if left_path == right_path:
        return "exact"
    if left["kind"] == "directory" and right_path.startswith(left_path + "/"):
        return "ancestor"
    if right["kind"] == "directory" and left_path.startswith(right_path + "/"):
        return "ancestor"
    return None


def _collision_class(left: Mapping[str, object], right: Mapping[str, object], relation: str, dag_outputs: Mapping[str, str]) -> str:
    origins = {str(left["origin"]), str(right["origin"])}
    modes = {str(left["mode"]), str(right["mode"])}
    if "git" in origins:
        return "git-dirty"
    if "runner" in origins:
        return "runner-snapshot"
    if "source-derived" in origins and len(origins) > 1:
        return "source-vs-derived"
    if origins == {"source-derived"}:
        return "derived-output"
    if left["path"] == right["path"] and str(left["path"]) in dag_outputs and "read" not in modes:
        return "sole-writer"
    if "read" in modes:
        return "write-vs-read"
    return "exact-direct" if relation == "exact" else "ancestor-directory"


def _collisions(entries: Sequence[Mapping[str, object]], groups: Mapping[str, Sequence[str]], dag: Mapping[str, object]) -> List[Dict[str, object]]:
    output_owner = {str(output): str(stage["sole_writer"]) for stage in dag["stages"] for output in stage["outputs"]}
    result: List[Dict[str, object]] = []
    for index, left in enumerate(entries):
        for right in entries[index + 1:]:
            if left["participant"] == right["participant"]:
                continue
            if str(left["participant"]).startswith("@") and str(right["participant"]).startswith("@"):
                continue
            if left["mode"] == right["mode"] == "read":
                continue
            relation = _overlap(left, right)
            if relation is None:
                continue
            collision_class = _collision_class(left, right, relation, output_owner)
            participants = sorted((str(left["participant"]), str(right["participant"])))
            chains = sorted([list(left["chain"]), list(right["chain"])], key=lambda chain: tuple(chain))
            if len(result) >= MAX_COLLISIONS:
                raise ContractError(f"collisions exceed {MAX_COLLISIONS} entries")
            result.append({
                "class": collision_class,
                "participants": participants,
                "paths": sorted(set((str(left["path"]), str(right["path"])))),
                "producer_chains": chains,
                "explanation": f"{collision_class}: {participants[0]} and {participants[1]} overlap at {' <-> '.join(sorted(set((str(left['path']), str(right['path'])))))}; chains: {' -> '.join(chains[0])} | {' -> '.join(chains[1])}",
            })
    for group, participants_value in groups.items():
        participants = sorted(set(participants_value))
        for index, left in enumerate(participants):
            for right in participants[index + 1:]:
                if len(result) >= MAX_COLLISIONS:
                    raise ContractError(f"collisions exceed {MAX_COLLISIONS} entries")
                result.append({
                    "class": "promotion-group",
                    "participants": [left, right],
                    "paths": [],
                    "producer_chains": [[group]],
                    "explanation": f"promotion-group: {left} and {right} both require atomic group {group}",
                })
    unique: Dict[Tuple[object, ...], Dict[str, object]] = {}
    for item in result:
        key = (item["class"], tuple(item["participants"]), tuple(item["paths"]), tuple(tuple(chain) for chain in item["producer_chains"]))
        unique[key] = item
    return [unique[key] for key in sorted(unique)]


def _ordered_groups(participants: Sequence[Mapping[str, object]]) -> List[List[str]]:
    ids = {str(item["id"]) for item in participants if not item.get("foreign_claim")}
    dependencies = {str(item["id"]): set(item["after"]) & ids for item in participants if str(item["id"]) in ids}
    groups: List[List[str]] = []
    remaining = set(ids)
    while remaining:
        ready = sorted(item for item in remaining if not dependencies[item] & remaining)
        if not ready:
            raise ContractError("participant after dependencies contain a cycle")
        groups.append(ready)
        remaining.difference_update(ready)
    return groups


def _incomplete_result(message: str, bindings: Optional[Mapping[str, object]] = None) -> Dict[str, object]:
    if bindings is None:
        bindings = {"request": None, "dag": None, "dag_path": None, "dag_source": None, "doctor_inputs": None, "doctor_schema": None, "doctor_source": None, "snapshots": None}
    return {
        "schema": RESULT_SCHEMA,
        "verdict": "INCOMPLETE",
        "plan": {"strategy": "incomplete", "ordered_groups": [], "safe_serialization_order": []},
        "bindings": dict(bindings),
        "counts": {"participants": 0, "collisions": 1},
        "collisions": [{"class": "unknown-incomplete-scope", "participants": [], "paths": [], "producer_chains": [], "explanation": message}],
        "summary": [f"legacy-scope-planner INCOMPLETE: {message}"],
    }


def plan_request(
    root: Path,
    request_value: object,
    *,
    doctor_report: Optional[Mapping[str, object]] = None,
    dag_value: Optional[object] = None,
    request_raw: Optional[bytes] = None,
    dag_raw: Optional[bytes] = None,
    injected_inputs: bool = False,
) -> Dict[str, object]:
    """Plan without executing actions or mutating repository or Git state."""
    root = root.resolve()
    if request_raw is None:
        request_raw = _canonical_bytes(request_value)
    if len(request_raw) > MAX_REQUEST_BYTES:
        raise ContractError(f"request exceeds {MAX_REQUEST_BYTES} bytes")
    if _load_json(request_raw, "request", MAX_REQUEST_BYTES) != request_value:
        raise ContractError("request_raw does not encode request_value exactly")
    request = _validate_request(request_value)
    _validate_scope_targets(root, request)
    if injected_inputs:
        if dag_value is None or doctor_report is None:
            raise ContractError("injected_inputs requires both dag_value and doctor_report")
        if dag_raw is None:
            dag_raw = _canonical_bytes(dag_value)
        elif _load_json(dag_raw, "DAG", MAX_DAG_BYTES) != dag_value:
            raise ContractError("dag_raw does not encode dag_value exactly")
        dag_source = "injected"
        doctor_source = "injected"
        dag_path_binding = None
        report = doctor_report
    else:
        if dag_value is not None or dag_raw is not None or doctor_report is not None:
            raise ContractError("dag_value, dag_raw, and doctor_report require injected_inputs=True")
        dag_raw = _read_regular(root / DAG_PATH, "authoritative DAG", MAX_DAG_BYTES)
        dag_value = _load_json(dag_raw, "DAG", MAX_DAG_BYTES)
        report = legacy_task_doctor.scan_repository(root)
        dag_source = "authoritative-root"
        doctor_source = "authoritative-scan"
        dag_path_binding = DAG_PATH
    if len(dag_raw) > MAX_DAG_BYTES:
        raise ContractError(f"DAG exceeds {MAX_DAG_BYTES} bytes")
    dag = _validate_dag(dag_value)
    bindings = {
        "request": _sha256(request_raw),
        "dag": _sha256(dag_raw),
        "dag_path": dag_path_binding,
        "dag_source": dag_source,
        "doctor_inputs": _doctor_digest(report),
        "doctor_schema": report.get("schema"),
        "doctor_source": doctor_source,
        "snapshots": request["snapshots"],
    }
    participants, problems = _merge_active_claims(root, request, report)
    if problems:
        return _incomplete_result("; ".join(problems), bindings)
    ordered = _ordered_groups(participants)
    entries, promotion_groups, source_problems = _entries(participants, dag, request["snapshots"])
    if source_problems:
        return _incomplete_result("; ".join(source_problems), bindings)
    collisions = _collisions(entries, promotion_groups, dag)
    ordered_ids = [participant_id for group in ordered for participant_id in group]
    foreign_ids = sorted(str(item["id"]) for item in participants if item.get("foreign_claim"))
    snapshot_ids = sorted({participant for collision in collisions for participant in collision["participants"] if str(participant).startswith("@")})
    serialization = snapshot_ids + foreign_ids + [item for item in ordered_ids if item not in foreign_ids]
    if collisions:
        verdict = "BLOCK"
        strategy = "block"
    elif len(ordered) > 1:
        verdict = "SERIALIZE"
        strategy = "serialize"
    else:
        verdict = "PARALLEL"
        strategy = "parallel"
    result = {
        "schema": RESULT_SCHEMA,
        "verdict": verdict,
        "plan": {
            "strategy": strategy,
            "ordered_groups": ordered,
            "safe_serialization_order": serialization if collisions else [],
        },
        "bindings": bindings,
        "counts": {"participants": len(participants), "collisions": len(collisions)},
        "collisions": collisions,
        "summary": [f"legacy-scope-planner {verdict}: {len(participants)} participants, {len(collisions)} collisions, strategy {strategy}"],
    }
    return result


def _read_regular(path: Path, label: str, limit: int) -> bytes:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ContractError(f"{label} must be a regular file")
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ContractError(f"{label} exceeds {limit} bytes")
    return raw


def render_summary(result: Mapping[str, object]) -> Tuple[str, ...]:
    summary = result.get("summary", [])
    if not isinstance(summary, list) or any(not isinstance(item, str) for item in summary):
        return ("legacy-scope-planner INCOMPLETE: malformed result",)
    return tuple(summary[:10])


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="repository root")
    parser.add_argument("--request", type=Path, required=True, help="closed planner request JSON")
    parser.add_argument("--json", action="store_true", help="emit canonical deterministic JSON")
    args = parser.parse_args(argv)
    try:
        request_raw = _read_regular(args.request, "request", MAX_REQUEST_BYTES)
        request_value = _load_json(request_raw, "request", MAX_REQUEST_BYTES)
        result = plan_request(args.root, request_value, request_raw=request_raw)
    except (ContractError, OSError) as exc:
        result = _incomplete_result(" ".join(str(exc).split()))
    if args.json:
        sys.stdout.buffer.write(_canonical_bytes(result))
    else:
        for line in render_summary(result):
            print(line)
    return {"PARALLEL": 0, "SERIALIZE": 0, "BLOCK": 1}.get(str(result.get("verdict")), 2)


if __name__ == "__main__":
    raise SystemExit(main())
