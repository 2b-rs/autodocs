#!/usr/bin/env python3
"""Deterministic issue derived-artifact regeneration.

The orchestrator executes the declared ``issue-regeneration-dag@v1`` without
shelling out.  Canonical issue items and claims are read-only inputs.  A run is
built completely in an isolated sibling directory and only then promoted to an
explicit generated/shadow/check root.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

TOOLS = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DAG = Path("docs/pipeline/issue-derived-artifacts-v1.json")
SELECTOR = Path("agent-workflow.json")
RESULT_SCHEMA = "issue-regeneration-result@v1"
REPORT_SCHEMA = "issue-regeneration-report@v1"
BOOTSTRAP_SCHEMA = "issue-bootstrap-refresh-result@v1"
MAX_FINDINGS = 20
LEGACY_PROFILES = frozenset({"legacy-lists"})
LEGACY_PHASES = frozenset({"legacy-writable"})
FROZEN_PHASES = frozenset({"frozen", "issue-store-frozen"})
WRITABLE_PHASES = frozenset({"issue-store-writable"})
SAFE_ROOT_TOKENS = frozenset({"shadow", "check", "generated", "regenerated"})
SAFE_ROOT_RE = re.compile(r"^(?:shadow|check|generated|regenerated)(?:[-_.][a-z0-9]+)*$")
AUTHORITY_NAMES = frozenset({
    "TODO.md", "DONE.md", "AGENTS.md", "SANDBOX.md", "PRIVILEGED.md",
    "CLAUDE.md", "agent-workflow.json",
})
LOCK_SCHEMA = "issue-regeneration-collision@v1"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


iv = _load("issue_validate", TOOLS / "issue_validate.py")
views = _load("issue_views", TOOLS / "issue_views.py")
lists = _load("issue_lists", TOOLS / "issue_lists.py")


class RegenerateError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest_value(value: Any) -> str:
    return digest_bytes(canonical_json(value).encode("utf-8"))


def read_object(path: Path, code: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegenerateError(code, f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RegenerateError(code, f"{path} must contain a JSON object")
    return value


def load_selector(repo: Path) -> Dict[str, Any]:
    selector = read_object(repo / SELECTOR, "IR1001")
    profile = selector.get("authority_profile")
    phase = selector.get("write_phase") or selector.get("authority_epoch")
    if profile not in LEGACY_PROFILES | {"issue-store"}:
        raise RegenerateError("IR1002", f"unsupported authority profile {profile!r}")
    if phase not in LEGACY_PHASES | FROZEN_PHASES | WRITABLE_PHASES:
        raise RegenerateError("IR1002", f"unsupported write phase {phase!r}")
    if profile in LEGACY_PROFILES and phase not in LEGACY_PHASES:
        raise RegenerateError("IR1002", "legacy-lists profile requires legacy-writable phase")
    if profile == "issue-store" and phase in LEGACY_PHASES:
        raise RegenerateError("IR1002", "issue-store profile cannot use legacy-writable phase")
    return selector


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _path_has_symlink(path: Path) -> bool:
    if path.is_symlink():
        return True
    absolute = path.absolute()
    parts = list(absolute.parts)
    if len(parts) >= 2 and parts[0] == "/" and parts[1] in ("var", "tmp", "etc"):
        current = Path("/private") / parts[1]
        remaining = parts[2:]
    elif len(parts) >= 3 and parts[0] == "/" and parts[1] == "private" and parts[2] in ("var", "tmp", "etc"):
        current = Path("/private") / parts[2]
        remaining = parts[3:]
    else:
        current = Path(absolute.anchor)
        remaining = parts[1:]
    for part in remaining:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _safe_root_name(path: Path) -> bool:
    return bool(SAFE_ROOT_RE.fullmatch(path.name.lower()))


def _strictly_inside(path: Path, parent: Path) -> bool:
    return path != parent and _inside(path, parent)


def authorize_output_root(
    repo: Path, output_root: Path, selector: Mapping[str, Any]
) -> Path:
    del selector  # all authority phases share the same derived-output containment.
    repo = repo.resolve()
    if ".." in output_root.parts:
        raise RegenerateError("IR1005", f"output root is a noncanonical alias: {output_root}")
    supplied = output_root.expanduser().absolute()
    if _path_has_symlink(supplied):
        raise RegenerateError("IR1005", f"output root contains an unsafe symlink: {supplied}")
    resolved = supplied.resolve(strict=False)
    filesystem_root = Path(resolved.anchor)
    home = Path.home().resolve()
    in_foreign_home = _strictly_inside(resolved, home) and not _inside(resolved, repo)
    if resolved == filesystem_root or resolved == home or in_foreign_home:
        raise RegenerateError("IR1003", f"unsafe broad or home output root: {resolved}")
    if resolved == repo or _inside(repo, resolved):
        raise RegenerateError("IR1003", f"output root is the repository or its ancestor: {resolved}")
    if resolved == repo.parent:
        raise RegenerateError("IR1003", f"repository parent is not an output root: {resolved}")
    if not _safe_root_name(resolved):
        raise RegenerateError(
            "IR1004", "output root basename must start with generated, shadow, check, or regenerated"
        )
    if _inside(resolved, repo):
        first = resolved.relative_to(repo).parts[0]
        if not _safe_root_name(Path(first)):
            raise RegenerateError("IR1004", "in-repository output must live below an explicit derived root")
    else:
        temporary_roots = {Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve()}
        if not any(_strictly_inside(resolved, root) for root in temporary_roots):
            raise RegenerateError("IR1003", "outside-repository output roots are restricted to a temporary root")
    if resolved.exists() and not resolved.is_dir():
        raise RegenerateError("IR1003", f"output root is not a directory: {resolved}")
    if not resolved.parent.is_dir():
        raise RegenerateError("IR1003", f"output-root parent must already exist: {resolved.parent}")
    forbidden = (
        repo / "issues", repo / "provenance", repo / "docs/pipeline",
        *(repo / name for name in AUTHORITY_NAMES),
    )
    for path in forbidden:
        canonical = path.resolve(strict=False)
        if resolved == canonical or _inside(resolved, canonical):
            raise RegenerateError("IR1003", f"authority/canonical path is never an output target: {resolved}")
    return resolved


def output_state(root: Path) -> Dict[str, str]:
    return tree_manifest(root)


@contextlib.contextmanager
def output_root_lease(output_root: Path):
    """Serialize one output root and provide an optimistic-CAS baseline."""
    lock = output_root.parent / f".{output_root.name}.issue-regeneration.lock"
    if lock.exists() and lock.is_symlink():
        raise RegenerateError("IR1034", f"regeneration collision at {output_root}")
    payload = canonical_json({"schema": LOCK_SCHEMA, "output_root": str(output_root)})
    try:
        descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise RegenerateError("IR1034", f"regeneration collision at {output_root}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        baseline = output_state(output_root)
        yield baseline
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def assert_output_cas(output_root: Path, baseline: Mapping[str, str]) -> None:
    if output_state(output_root) != dict(baseline):
        raise RegenerateError("IR1035", f"output root changed during regeneration: {output_root}")


def validate_relative_path(value: str, *, context: str) -> str:
    if not value or "\x00" in value or value != value.strip():
        raise RegenerateError("IR1018", f"{context} path is empty, contains NUL, or has surrounding whitespace")
    if "\\" in value:
        raise RegenerateError("IR1018", f"{context} path must use canonical POSIX separators: {value!r}")
    windows = PureWindowsPath(value)
    posix = PurePosixPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise RegenerateError("IR1018", f"{context} path must be relative: {value!r}")
    if value in {".", ".."} or any(part in {".", ".."} for part in posix.parts):
        raise RegenerateError("IR1018", f"{context} path contains dot traversal: {value!r}")
    if posix.as_posix() != value or not posix.parts:
        raise RegenerateError("IR1018", f"{context} path is noncanonical: {value!r}")
    return value


def destination_under(root: Path, relative: str) -> Path:
    relative = validate_relative_path(relative, context="output")
    root = root.absolute()
    resolved_root = root.resolve()
    candidate = root / relative
    current = candidate.parent
    while current != root:
        if current.is_symlink():
            raise RegenerateError("IR1019", f"output parent is a symlink: {current}")
        current = current.parent
    resolved = candidate.resolve(strict=False)
    try:
        rel = resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RegenerateError("IR1019", f"output escapes staging root: {relative}") from exc
    if not rel.parts:
        raise RegenerateError("IR1019", "output must be strictly below staging root")
    return candidate


def derived_input_under(root: Path, relative: str) -> Path:
    relative = validate_relative_path(relative, context="derived input")
    candidate = destination_under(root, relative)
    if candidate.is_symlink() or _path_has_symlink(candidate):
        raise RegenerateError("IR1019", f"derived input contains a symlink: {relative}")
    return candidate


def load_manifest(path: Path) -> Dict[str, Any]:
    manifest = read_object(path, "IR1010")
    if manifest.get("schema") != "issue-regeneration-dag@v1":
        raise RegenerateError("IR1010", "unsupported regeneration manifest schema")
    stages = manifest.get("stages")
    if not isinstance(stages, list) or not stages:
        raise RegenerateError("IR1010", "manifest stages must be a non-empty list")
    by_id: Dict[str, Dict[str, Any]] = {}
    owners: Dict[str, str] = {}
    for raw in stages:
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
            raise RegenerateError("IR1010", "every stage requires an object and string id")
        stage = dict(raw)
        stage_id = stage["id"]
        if stage_id in by_id:
            raise RegenerateError("IR1011", f"duplicate stage id {stage_id}")
        if not isinstance(stage.get("argv"), list) or not stage["argv"] or not all(
            isinstance(part, str) and part for part in stage["argv"]
        ):
            raise RegenerateError("IR1012", f"stage {stage_id} requires a literal argv array")
        outputs = stage.get("outputs")
        if not isinstance(outputs, list) or not all(isinstance(item, str) and item for item in outputs):
            raise RegenerateError("IR1012", f"stage {stage_id} outputs must be strings")
        for output in outputs:
            validate_relative_path(output, context=f"stage {stage_id} output")
            if output in owners:
                raise RegenerateError("IR1013", f"output {output} has multiple writers")
            owners[output] = stage_id
        by_id[stage_id] = stage
    required = tuple(getattr(iv, "REQUIRED_STAGE_IDS", ()))
    missing = [stage_id for stage_id in required if stage_id not in by_id]
    if missing:
        raise RegenerateError("IR1014", "missing required stages: " + ",".join(missing))
    for stage_id, stage in by_id.items():
        dependencies = stage.get("depends_on") or []
        if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
            raise RegenerateError("IR1012", f"stage {stage_id} dependencies must be strings")
        if stage_id in dependencies:
            raise RegenerateError("IR1015", f"stage {stage_id} depends on itself")
        unknown = sorted(set(dependencies) - set(by_id))
        if unknown:
            raise RegenerateError("IR1015", f"stage {stage_id} has unknown dependencies {unknown}")
        for entry in stage.get("inputs") or []:
            if not isinstance(entry, dict) or not isinstance(entry.get("glob"), str):
                raise RegenerateError("IR1012", f"stage {stage_id} has malformed input")
            if entry.get("kind") == "derived":
                validate_relative_path(entry["glob"], context=f"stage {stage_id} derived input")
            if entry.get("kind") == "derived" and entry["glob"] not in owners:
                raise RegenerateError("IR1016", f"derived input {entry['glob']} has no producer")
            if entry.get("kind") == "derived" and owners.get(entry["glob"]) not in dependencies:
                raise RegenerateError("IR1016", f"producer of {entry['glob']} is not a dependency of {stage_id}")
    order = topological_order(by_id, [stage["id"] for stage in stages])
    return {"manifest": manifest, "by_id": by_id, "owners": owners, "order": order}


def topological_order(
    by_id: Mapping[str, Mapping[str, Any]], preferred: Optional[Sequence[str]] = None
) -> List[str]:
    rank = {stage_id: index for index, stage_id in enumerate(preferred or sorted(by_id))}
    incoming = {stage_id: set(stage.get("depends_on") or []) for stage_id, stage in by_id.items()}
    ready = sorted((stage_id for stage_id, deps in incoming.items() if not deps), key=lambda item: (rank.get(item, 10**9), item))
    result: List[str] = []
    while ready:
        current = ready.pop(0)
        result.append(current)
        for stage_id in sorted(incoming):
            deps = incoming[stage_id]
            if current in deps:
                deps.remove(current)
                if not deps and stage_id not in result and stage_id not in ready:
                    ready.append(stage_id)
                    ready.sort(key=lambda item: (rank.get(item, 10**9), item))
    if len(result) != len(by_id):
        raise RegenerateError("IR1017", "regeneration DAG contains a cycle")
    return result


def _write(root: Path, relative: str, data: bytes) -> Dict[str, Any]:
    path = destination_under(root, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise RegenerateError("IR1019", f"output parent became a symlink: {path.parent}")
    path.write_bytes(data)
    return {"path": relative, "sha256": digest_bytes(data), "bytes": len(data)}


def _write_json(root: Path, relative: str, value: Any) -> Dict[str, Any]:
    return _write(root, relative, canonical_json(value).encode("utf-8"))


def _public_catalog(catalog: Mapping[str, Any]) -> Dict[str, Any]:
    items = []
    for source in catalog.get("items") or []:
        if source.get("visibility") != "public":
            continue
        item = {
            key: source.get(key)
            for key in ("id", "level", "parent", "state", "lifecycle_status", "archive_status", "url", "title", "prerequisites", "criteria")
        }
        items.append(item)
    items.sort(key=lambda item: item.get("id") or "")
    payload = {
        "schema": "issue-catalog-public@v1",
        "authority": "generated-view",
        "source_generation_id": catalog.get("generation_id"),
        "items": items,
    }
    payload["generation_id"] = digest_value(payload)
    return payload


def _dot(graph: Mapping[str, Any]) -> str:
    lines = ["digraph issues {"]
    for node in graph.get("nodes") or []:
        lines.append(f'  "{node.get("id")}";')
    for edge in graph.get("edges") or []:
        lines.append(f'  "{edge.get("source")}" -> "{edge.get("target")}" [label="{edge.get("kind")}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def _svg(graph: Mapping[str, Any]) -> str:
    labels = " ".join(html.escape(str(node.get("id"))) for node in graph.get("nodes") or [])
    return f'<svg xmlns="http://www.w3.org/2000/svg" data-generation-id="{graph.get("generation_id")}"><text>{labels}</text></svg>\n'


def _languages(stage: Mapping[str, Any]) -> List[str]:
    languages = []
    for output in stage.get("outputs") or []:
        parts = Path(output).parts
        if len(parts) >= 3 and parts[-2:] == ("issues", "index.html"):
            languages.append(parts[0])
    return languages


def _validate_payload(repo: Path, *, include_provenance: bool = True) -> Dict[str, Any]:
    diagnostics, parsed = iv.validate(
        repo=repo,
        source="working-tree",
        root=repo / "issues",
        compare_head=False,
        provenance_root=repo / "provenance" if include_provenance else None,
    )
    payload = iv.result_payload(diagnostics, "working-tree", len(parsed))
    payload["diagnostics"] = payload.get("diagnostics", [])[:MAX_FINDINGS]
    return payload


def _stage_validate(ctx: Dict[str, Any], stage: Mapping[str, Any]) -> List[Dict[str, Any]]:
    payload = _validate_payload(ctx["repo"], include_provenance=True)
    if payload.get("exit_code") != 0:
        raise RegenerateError("IR1020", f"canonical validation failed with {len(payload.get('diagnostics') or [])} findings")
    return [_write_json(ctx["staging"], stage["outputs"][0], payload)]


def _render_fresh(ctx: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if "catalog" not in ctx:
        catalog, graph = views.render(ctx["repo"] / "issues", ctx["repo"])
        ctx["catalog"], ctx["graph"] = catalog, graph
    return ctx["catalog"], ctx["graph"]


def _stage_internal(ctx: Dict[str, Any], stage: Mapping[str, Any]) -> List[Dict[str, Any]]:
    catalog, _ = _render_fresh(ctx)
    return [_write_json(ctx["staging"], stage["outputs"][0], catalog)]


def _fresh_internal_catalog(ctx: Dict[str, Any]) -> Dict[str, Any]:
    path = derived_input_under(ctx["staging"], "data/issue-catalog.internal.json")
    catalog = read_object(path, "IR1022")
    fresh, _ = _render_fresh(ctx)
    if canonical_json(catalog) != canonical_json(fresh):
        raise RegenerateError("IR1022", "internal catalog is stale or unexplained")
    return catalog


def _stage_public(ctx: Dict[str, Any], stage: Mapping[str, Any]) -> List[Dict[str, Any]]:
    catalog = _fresh_internal_catalog(ctx)
    return [_write_json(ctx["staging"], stage["outputs"][0], _public_catalog(catalog))]


def _stage_graphs(ctx: Dict[str, Any], stage: Mapping[str, Any]) -> List[Dict[str, Any]]:
    _fresh_internal_catalog(ctx)
    _, graph = _render_fresh(ctx)
    payloads = {
        ".json": canonical_json(graph).encode("utf-8"),
        ".dot": _dot(graph).encode("utf-8"),
        ".svg": _svg(graph).encode("utf-8"),
    }
    outputs = []
    for relative in stage["outputs"]:
        suffix = Path(relative).suffix
        if suffix not in payloads:
            raise RegenerateError("IR1021", f"unsupported graph output {relative}")
        outputs.append(_write(ctx["staging"], relative, payloads[suffix]))
    return outputs


def _stage_pages(ctx: Dict[str, Any], stage: Mapping[str, Any]) -> List[Dict[str, Any]]:
    public = read_object(derived_input_under(ctx["staging"], "data/issue-catalog.public.json"), "IR1022")
    graph = read_object(derived_input_under(ctx["staging"], "data/issue-graph.json"), "IR1022")
    catalog = _fresh_internal_catalog(ctx)
    if canonical_json(public) != canonical_json(_public_catalog(catalog)):
        raise RegenerateError("IR1022", "public catalog is stale or unexplained")
    _, fresh_graph = _render_fresh(ctx)
    if canonical_json(graph) != canonical_json(fresh_graph):
        raise RegenerateError("IR1022", "dependency graph is stale or unexplained")
    html_stage = ctx["loaded"]["by_id"].get("render-html") or {}
    languages = _languages(html_stage)
    pages = {
        "schema": "issue-pages@v1",
        "generation_id": digest_value({"catalog": public["generation_id"], "graph": graph.get("generation_id"), "languages": languages}),
        "languages": languages,
        "pages": [
            {"id": item["id"], "path": f"issues/{item['id']}/index.html", "title": item.get("title") or ""}
            for item in public["items"]
        ],
    }
    register = {
        "schema": "issue-i18n-register@v1",
        "generation_id": pages["generation_id"],
        "languages": languages,
        "graph_node_count": len(graph.get("nodes") or []),
    }
    values = {"data/issue-pages.json": pages, "data/issue-i18n-register.json": register}
    return [_write_json(ctx["staging"], relative, values[relative]) for relative in stage["outputs"]]


def _stage_html(ctx: Dict[str, Any], stage: Mapping[str, Any]) -> List[Dict[str, Any]]:
    pages = read_object(ctx["staging"] / "data/issue-pages.json", "IR1022")
    outputs = []
    for relative in stage["outputs"]:
        language = Path(relative).parts[0]
        body = (
            f'<!DOCTYPE html><html lang="{html.escape(language)}"><head><meta charset="utf-8">'
            f'<title>Issues</title></head><body data-generation-id="{pages.get("generation_id")}">'
            f'<h1>Issues</h1><p>count={len(pages.get("pages") or [])}</p></body></html>\n'
        ).encode("utf-8")
        outputs.append(_write(ctx["staging"], relative, body))
    return outputs


def report_documents(validation: Mapping[str, Any], graph: Mapping[str, Any]) -> Tuple[Dict[str, Any], str]:
    findings = list(validation.get("diagnostics") or [])[:MAX_FINDINGS]
    report = {
        "schema": REPORT_SCHEMA,
        "status": "PASS" if validation.get("exit_code") == 0 else "FAIL",
        "counts": {
            "items": int(validation.get("item_count") or 0),
            "nodes": len(graph.get("nodes") or []),
            "edges": len(graph.get("edges") or []),
            "findings": len(validation.get("diagnostics") or []),
        },
        "generation_id": graph.get("generation_id"),
        "findings": findings,
    }
    escaped = html.escape(canonical_json(report))
    return report, f"<!DOCTYPE html><html><body><pre>{escaped}</pre></body></html>\n"


def _stage_report(ctx: Dict[str, Any], stage: Mapping[str, Any]) -> List[Dict[str, Any]]:
    validation = read_object(derived_input_under(ctx["staging"], "output/issue-validation.json"), "IR1023")
    graph = read_object(derived_input_under(ctx["staging"], "data/issue-graph.json"), "IR1023")
    _, fresh_graph = _render_fresh(ctx)
    if canonical_json(graph) != canonical_json(fresh_graph):
        raise RegenerateError("IR1023", "report graph input is stale or unexplained")
    report, rendered = report_documents(validation, graph)
    values = {
        "output/issue-report.json": canonical_json(report).encode("utf-8"),
        "output/issue-report.html": rendered.encode("utf-8"),
    }
    outputs = []
    for relative in stage["outputs"]:
        outputs.append(_write(ctx["staging"], relative, values[relative]))
    return outputs


HANDLERS: Dict[str, Callable[[Dict[str, Any], Mapping[str, Any]], List[Dict[str, Any]]]] = {
    "validate-canonical": _stage_validate,
    "build-internal-catalog": _stage_internal,
    "build-public-projection": _stage_public,
    "build-graphs": _stage_graphs,
    "build-page-models": _stage_pages,
    "render-html": _stage_html,
    "render-reports": _stage_report,
}


def tree_manifest(root: Path) -> Dict[str, str]:
    if not root.is_dir():
        return {}
    result: Dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().encode("utf-8")):
        if path.is_symlink():
            raise RegenerateError("IR1005", f"generated tree contains a symlink: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = digest_bytes(path.read_bytes())
    return result


def compare_trees(expected: Path, observed: Path) -> Dict[str, List[str]]:
    left, right = tree_manifest(expected), tree_manifest(observed)
    return {
        "missing": sorted(set(left) - set(right)),
        "stale": sorted(path for path in set(left) & set(right) if left[path] != right[path]),
        "unexplained": sorted(set(right) - set(left)),
    }


def _promote(staging: Path, target: Path) -> bool:
    diff = compare_trees(staging, target)
    if not any(diff.values()):
        shutil.rmtree(staging)
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.parent / f".{target.name}.backup-{uuid.uuid4().hex}"
    moved_old = False
    try:
        if target.exists():
            os.replace(target, backup)
            moved_old = True
        os.replace(staging, target)
    except Exception:
        if moved_old and not target.exists() and backup.exists():
            os.replace(backup, target)
        raise
    if backup.exists():
        shutil.rmtree(backup)
    return True


def _execute_locked(
    *,
    repo: Path,
    output_root: Path,
    selector: Mapping[str, Any],
    loaded: Mapping[str, Any],
    baseline: Mapping[str, str],
    write: bool,
    fail_stage: Optional[str],
) -> Dict[str, Any]:
    source_before = tree_manifest(repo / "issues")
    provenance_before = tree_manifest(repo / "provenance")
    staging_parent = output_root.parent
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=staging_parent))
    ctx: Dict[str, Any] = {"repo": repo, "staging": staging, "loaded": loaded}
    summaries: List[Dict[str, Any]] = []
    try:
        for stage_id in loaded["order"]:
            if fail_stage == stage_id:
                raise RegenerateError("IR1099", f"injected failure at {stage_id}")
            handler = HANDLERS.get(stage_id)
            if handler is None:
                raise RegenerateError("IR1024", f"no handler for stage {stage_id}")
            outputs = handler(ctx, loaded["by_id"][stage_id])
            expected = list(loaded["by_id"][stage_id].get("outputs") or [])
            actual = [item["path"] for item in outputs]
            if actual != expected:
                raise RegenerateError("IR1025", f"stage {stage_id} output set/order mismatch")
            summaries.append({"id": stage_id, "outputs": outputs})
        if tree_manifest(repo / "issues") != source_before or tree_manifest(repo / "provenance") != provenance_before:
            raise RegenerateError("IR1026", "canonical source changed during regeneration")
        expected_paths = sorted(output for stage in loaded["by_id"].values() for output in stage.get("outputs") or [])
        actual_paths = sorted(tree_manifest(staging))
        if actual_paths != expected_paths:
            raise RegenerateError("IR1027", "generated tree contains missing or undeclared outputs")
        diff = compare_trees(staging, output_root)
        run_id = digest_value({
            "selector": selector,
            "dag": loaded["manifest"],
            "outputs": tree_manifest(staging),
        })
        changed = False
        if write:
            if diff["unexplained"]:
                raise RegenerateError("IR1028", "unexplained existing outputs: " + ",".join(diff["unexplained"][:MAX_FINDINGS]))
            assert_output_cas(output_root, baseline)
            changed = _promote(staging, output_root)
        else:
            shutil.rmtree(staging)
        return {
            "schema": RESULT_SCHEMA,
            "status": "PASS" if write or not any(diff.values()) else "STALE",
            "mode": "write" if write else "check",
            "authority": {
                "profile": selector.get("authority_profile"),
                "phase": selector.get("write_phase") or selector.get("authority_epoch"),
                "canonical_sources_mutated": False,
            },
            "run_id": run_id,
            "stage_order": loaded["order"],
            "stages": summaries,
            "counts": {
                "stages": len(summaries),
                "outputs": len(expected_paths),
                "missing": len(diff["missing"]),
                "stale": len(diff["stale"]),
                "unexplained": len(diff["unexplained"]),
            },
            "diff": {key: value[:MAX_FINDINGS] for key, value in diff.items()},
            "changed": changed,
            "exit_code": 0 if write or not any(diff.values()) else 1,
        }
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def execute(
    *,
    repo: Path,
    output_root: Path,
    dag_path: Optional[Path] = None,
    write: bool = False,
    fail_stage: Optional[str] = None,
) -> Dict[str, Any]:
    repo = repo.resolve()
    selector = load_selector(repo)
    output_root = authorize_output_root(repo, output_root, selector)
    dag = (dag_path or repo / DEFAULT_DAG).resolve()
    loaded = load_manifest(dag)
    with output_root_lease(output_root) as baseline:
        return _execute_locked(
            repo=repo,
            output_root=output_root,
            selector=selector,
            loaded=loaded,
            baseline=baseline,
            write=write,
            fail_stage=fail_stage,
        )


def _first_diff_index(left: List[Any], right: List[Any]) -> Optional[int]:
    for index, (l_value, r_value) in enumerate(zip(left, right)):
        if l_value != r_value:
            return index
    if len(left) != len(right):
        return min(len(left), len(right))
    return None


def _strict_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool-is-an-int coercion."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _strict_json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _strict_json_equal(l_value, r_value)
            for l_value, r_value in zip(left, right)
        )
    return left == right


def _strict_labels(value: Any) -> Optional[List[str]]:
    """Return labels only for an actual JSON array of strings."""
    if type(value) is not list or any(type(label) is not str for label in value):
        return None
    return list(value)


def _canonical_labels_by_id(issues_root: Path, repository_root: Path) -> Dict[str, List[str]]:
    """Independently derive each item's canonical labels straight from the
    parsed issue store (views.load_store), never from the views or lists
    rendering paths -- so the comparison below cannot circularly trust
    either side it is checking. Absence of a labels field on the parsed
    record is treated as an empty list (DEC-0037-037: "absence=>[]")."""
    parsed, _malformed, _sources = views.load_store(issues_root, repository_root)
    canonical: Dict[str, List[str]] = {}
    for value in parsed:
        labels = _strict_labels(value["item"].get("labels", []))
        if labels is None:
            raise RegenerateError(
                "IR1030", f"canonical labels for item {value['item']['id']!r} are not an array of strings"
            )
        canonical[value["item"]["id"]] = labels
    return canonical


def _verify_bootstrap_catalog_agreement(
    catalog: Mapping[str, Any],
    rendered_catalog: Mapping[str, Any],
    issues_root: Path,
    repository_root: Path,
) -> None:
    """Representation-correct IR1030 comparison (DEC-0037-037 / ALT-01,
    Architect scope 1788622388397-a0f0f9a3). Real difference classes are
    still fail-closed: wrong labels, any non-label difference, missing or
    extra items, identity mismatch, reordering, and duplication all raise
    IR1030. Only a *labels-only* difference between the views and lists
    representations -- each independently correct against canonical issue
    labels -- is not an error, because that is the two renderers' genuine,
    intended division of responsibility (views omits labels; lists carries
    them), not a defect.

    Never uses set()/sorted()/dedup on the id sequence (would hide
    reordering, duplication, or multiplicity changes) and never zips before
    proving equal length/order (would silently truncate on a real
    cardinality mismatch instead of raising)."""
    view_items = catalog.get("items") or []
    list_items = rendered_catalog.get("items") or []

    view_ids = [item.get("id") for item in view_items]
    list_ids = [item.get("id") for item in list_items]
    if view_ids != list_ids:
        raise RegenerateError(
            "IR1030",
            "view/list catalog identity, order, or multiplicity mismatch: "
            f"views has {len(view_ids)} item id(s), lists has {len(list_ids)} item id(s); "
            f"first divergence at index {_first_diff_index(view_ids, list_ids)}",
        )

    canonical = _canonical_labels_by_id(issues_root, repository_root)

    # Lengths and order already proven equal above; zip here cannot hide a
    # real cardinality mismatch.
    for index, (view_item, list_item) in enumerate(zip(view_items, list_items)):
        item_id = view_item.get("id")
        view_rest = {key: value for key, value in view_item.items() if key != "labels"}
        list_rest = {key: value for key, value in list_item.items() if key != "labels"}
        if not _strict_json_equal(view_rest, list_rest):
            raise RegenerateError(
                "IR1030",
                f"view/list catalog non-label field disagreement for item {item_id!r} at index {index}",
            )
        canonical_labels = canonical.get(item_id, [])
        if "labels" not in list_item:
            raise RegenerateError(
                "IR1030", f"lists catalog item {item_id!r} at index {index} is missing the required labels field"
            )
        observed_list_labels = _strict_labels(list_item["labels"])
        if observed_list_labels is None or not _strict_json_equal(observed_list_labels, canonical_labels):
            raise RegenerateError(
                "IR1030",
                f"lists catalog labels for item {item_id!r} do not exactly equal canonical labels "
                f"(order/multiplicity-sensitive): observed {observed_list_labels!r}, canonical {canonical_labels!r}",
            )
        if "labels" in view_item:
            observed_view_labels = _strict_labels(view_item["labels"])
            if observed_view_labels is None or not _strict_json_equal(observed_view_labels, canonical_labels):
                raise RegenerateError(
                    "IR1030",
                    f"views catalog labels for item {item_id!r} do not exactly equal canonical labels: "
                    f"observed {observed_view_labels!r}, canonical {canonical_labels!r}",
                )


def bootstrap_refresh(
    *, repo: Path, output_root: Optional[Path], write: bool
) -> Dict[str, Any]:
    repo = repo.resolve()
    selector = load_selector(repo)
    catalog, graph = views.render(repo / "issues", repo)
    rendered_catalog, groups, documents = lists.render_lists(repo / "issues", repo)
    _verify_bootstrap_catalog_agreement(catalog, rendered_catalog, repo / "issues", repo)
    validation = _validate_payload(repo, include_provenance=False)
    if validation.get("exit_code") != 0:
        raise RegenerateError("IR1031", "bootstrap refresh canonical validation failed")
    expected = {
        "issues/_views/catalog.json": canonical_json(catalog).encode("utf-8"),
        "issues/_views/dependency-graph.json": canonical_json(graph).encode("utf-8"),
    }
    for kind, relative in lists.OUTPUT_NAMES.items():
        if kind != "manifest":
            expected[f"lists/{relative}"] = documents[kind].encode("utf-8")
    manifest = {path: digest_bytes(data) for path, data in sorted(expected.items())}
    run_id = digest_value({"selector": selector, "outputs": manifest})
    diff = {"missing": [], "stale": [], "unexplained": []}
    changed = False
    if output_root is not None:
        output_root = authorize_output_root(repo, output_root, selector)
        with output_root_lease(output_root) as baseline:
            staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=output_root.parent))
            try:
                for relative, data in expected.items():
                    _write(staging, relative, data)
                diff = compare_trees(staging, output_root)
                if write:
                    if diff["unexplained"]:
                        raise RegenerateError("IR1032", "unexplained bootstrap outputs: " + ",".join(diff["unexplained"][:MAX_FINDINGS]))
                    assert_output_cas(output_root, baseline)
                    changed = _promote(staging, output_root)
                else:
                    shutil.rmtree(staging)
            except Exception:
                shutil.rmtree(staging, ignore_errors=True)
                raise
    elif write:
        raise RegenerateError("IR1033", "--output-root is required for persistent refresh")
    return {
        "schema": BOOTSTRAP_SCHEMA,
        "status": "PASS" if output_root is None or write or not any(diff.values()) else "STALE",
        "mode": "write" if write else "check",
        "authority": {
            "profile": selector.get("authority_profile"),
            "phase": selector.get("write_phase") or selector.get("authority_epoch"),
            "canonical_sources_mutated": False,
        },
        "run_id": run_id,
        "counts": {
            "items": len(catalog.get("items") or []),
            "nodes": len(graph.get("nodes") or []),
            "open": len(groups["open"]),
            "blocked": len(groups["blocked"]),
            "outputs": len(expected),
        },
        "diff": {key: value[:MAX_FINDINGS] for key, value in diff.items()},
        "changed": changed,
        "exit_code": 0 if output_root is None or write or not any(diff.values()) else 1,
    }


def emit(result: Mapping[str, Any], fmt: str) -> int:
    if fmt == "json":
        sys.stdout.write(canonical_json(result))
    else:
        counts = result.get("counts") or {}
        sys.stdout.write(
            f"{result.get('status')} mode={result.get('mode')} "
            f"stages={counts.get('stages', 0)} outputs={counts.get('outputs', 0)}\n"
        )
    return int(result.get("exit_code", 2))


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(ROOT))
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--dag")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", "--dry-run", dest="write", action="store_false")
    parser.set_defaults(write=False)
    parser.add_argument("--format", choices=("json", "human"), default="json")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = execute(
            repo=Path(args.repo),
            output_root=Path(args.output_root),
            dag_path=Path(args.dag) if args.dag else None,
            write=args.write,
        )
        return emit(result, args.format)
    except (RegenerateError, OSError, json.JSONDecodeError, views.IssueViewsError, lists.IssueListsError) as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
