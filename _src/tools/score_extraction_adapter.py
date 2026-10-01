#!/usr/bin/env python3
"""Extract deterministic, non-canonical S-Core candidates from retained snapshots.

This adapter is deliberately offline: it accepts a complete release-pinned BOM,
its matching import profile, and the retained tar archives only.  It never
invokes Git, resolves a ref, contacts a network service, or writes a canonical
record corpus.  Task 0019-05 owns canonical normalization and Task 0019-07
owns materialization of review items.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from urllib.parse import quote

import score_campaign_manifest as campaign_manifest
import score_import_profile as import_profile
import score_source_snapshot as source_snapshot

RAW_SCHEMA = "score-raw-extraction@v1"
MOVING_REFS = {"main", "master", "head", "latest", "develop", "development"}
MODULE_RE = re.compile(r"\bmodule\s*\(\s*name\s*=\s*[\"']([^\"']+)[\"']")
RST_DIRECTIVE_RE = re.compile(r"^(\s*)\.\.\s+([A-Za-z][A-Za-z0-9_-]*)::\s*(.+?)\s*$")
MYST_DIRECTIVE_RE = re.compile(r"^```\{([A-Za-z][A-Za-z0-9_-]*)}\s*(.+?)\s*$")
ID_RE = re.compile(r"^\s*:id:\s*(.*?)\s*$")


class ExtractionError(ValueError):
    """Raised before output promotion when retained source evidence is invalid."""


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_repository_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as error:
        raise ExtractionError(f"repository-relative path escapes root: {relative}") from error
    return candidate


def _source_context(source: Mapping[str, Any], path: str = "", locator: str = "") -> str:
    return (
        f"repository={source.get('repository')!r} ref={source.get('release_ref')!r} "
        f"commit={source.get('resolved_commit')!r} path={path!r} locator={locator!r}"
    )


def _locator(source: Mapping[str, Any], path: str) -> str:
    return f"{str(source['repository_url']).removesuffix('.git')}/blob/{source['resolved_commit']}/{quote(path, safe='/')}"


def _line_locator(source: Mapping[str, Any], path: str, start: int, end: int, anchor: str) -> dict[str, Any]:
    return {"path": path, "line_start": start, "line_end": end, "anchor": anchor}


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExtractionError(f"cannot read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ExtractionError(f"{label} {path} must contain a JSON object")
    return value


def _validate_inputs(manifest: dict[str, Any], profile: dict[str, Any]) -> None:
    bom_errors = campaign_manifest.validate_bom(manifest, require_complete=True)
    if bom_errors:
        source = manifest.get("sources", [{}])[0] if isinstance(manifest.get("sources"), list) else {}
        context = _source_context(source if isinstance(source, Mapping) else {})
        raise ExtractionError(f"manifest-pinned source set is invalid: {'; '.join(bom_errors)}; {context}")
    profile_findings = import_profile.validate_profile(profile, manifest)
    if profile_findings:
        bindings = profile.get("source_bindings", [])
        binding = bindings[0] if isinstance(bindings, list) and bindings else {}
        context = _source_context(binding if isinstance(binding, Mapping) else {})
        raise ExtractionError(f"manifest/profile pin mismatch: {json.dumps(profile_findings, sort_keys=True)}; {context}")
    for source in manifest["sources"]:
        if str(source["release_ref"]).lower() in MOVING_REFS or source["ref_kind"] != "tag":
            raise ExtractionError(f"moving or non-tag ref forbidden; {_source_context(source)}")


def _archive_members(source: Mapping[str, Any], archive_path: Path) -> dict[str, bytes]:
    if not archive_path.is_file():
        raise ExtractionError(f"retained source archive is missing; {_source_context(source, str(archive_path))}")
    members: dict[str, bytes] = {}
    try:
        with tarfile.open(archive_path, "r:") as archive:
            for member in archive.getmembers():
                pure_path = PurePosixPath(member.name)
                if not member.name or pure_path.is_absolute() or ".." in pure_path.parts:
                    raise ExtractionError(f"unsafe retained archive member; {_source_context(source, member.name)}")
                if member.isdir():
                    continue
                if not member.isfile() or member.name in members:
                    raise ExtractionError(f"invalid retained archive member; {_source_context(source, member.name)}")
                stream = archive.extractfile(member)
                if stream is None:
                    raise ExtractionError(f"unreadable retained archive member; {_source_context(source, member.name)}")
                with stream:
                    members[member.name] = stream.read()
    except (OSError, tarfile.TarError) as error:
        raise ExtractionError(f"cannot read retained source archive; {_source_context(source, str(archive_path))}: {error}") from error
    return members


def _decode(source: Mapping[str, Any], path: str, raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ExtractionError(f"selected text artifact is not UTF-8; {_source_context(source, path, _locator(source, path))}") from error


def _candidate(source: Mapping[str, Any], source_class: str, path: str, raw: bytes, locator: dict[str, Any], fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_class": source_class,
        "repository": source["repository"],
        "repository_url": source["repository_url"],
        "release_ref": source["release_ref"],
        "ref_kind": source["ref_kind"],
        "resolved_commit": source["resolved_commit"],
        "locator": locator,
        "source_content_sha256": _sha256(raw),
        "fields": fields,
    }


def _need_candidates(source: Mapping[str, Any], source_class: str, path: str, raw: bytes) -> list[dict[str, Any]]:
    text = _decode(source, path, raw)
    lines = text.splitlines()
    found: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        rst = RST_DIRECTIVE_RE.match(lines[index])
        myst = MYST_DIRECTIVE_RE.match(lines[index])
        if not rst and not myst:
            index += 1
            continue
        start = index
        if rst:
            directive_type, title = rst.group(2), rst.group(3)
            indent = len(rst.group(1))
            index += 1
            while index < len(lines) and (not lines[index].strip() or len(lines[index]) - len(lines[index].lstrip()) > indent):
                index += 1
        else:
            directive_type, title = myst.group(1), myst.group(2)
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                index += 1
            if index < len(lines):
                index += 1
        end = index
        block = lines[start:end]
        need_id = next((match.group(1).strip() for line in block if (match := ID_RE.match(line))), None)
        # A generic Sphinx directive is relevant only when it declares the profile-required explicit id.
        if not need_id:
            continue
        found.append(
            _candidate(
                source,
                source_class,
                path,
                raw,
                _line_locator(source, path, start + 1, max(start + 1, end), need_id),
                {"need_id": need_id, "need_type": directive_type.lower(), "title": title, "description": "\n".join(block)},
            )
        )
    return found


def _selected_docs(source: Mapping[str, Any], path: str) -> bool:
    return any(path.startswith(f"{root}/") and path.endswith((".rst", ".md")) for root in source["source_paths"])


def extract(manifest: dict[str, Any], profile: dict[str, Any], repository_root: Path) -> dict[str, Any]:
    """Return deterministic raw candidates after validating the entire snapshot first."""
    _validate_inputs(manifest, profile)
    try:
        source_snapshot.verify_snapshot(manifest, repository_root)
    except source_snapshot.SnapshotError as error:
        contexts = " | ".join(
            _source_context(source, str(source["snapshot_archive"]), _locator(source, str(source["snapshot_archive"])))
            for source in sorted(manifest["sources"], key=lambda item: item["repository"])
        )
        raise ExtractionError(f"retained source verification failed: {error}; {contexts}") from error

    classes = {item["source_class"]: item for item in profile["artifact_classes"]}
    profile_sources = {item["repository"]: item for item in profile["source_bindings"]}
    observed_ids: set[str] = set()
    observations: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for source in sorted(manifest["sources"], key=lambda item: item["repository"]):
        archive = _safe_repository_path(repository_root, source["snapshot_archive"])
        members = _archive_members(source, archive)
        repository = source["repository"]
        binding = profile_sources[repository]
        if binding["resolved_commit"] != source["resolved_commit"]:
            raise ExtractionError(f"source pin differs from manifest; {_source_context(source)}")

        if repository == "score":
            module_path = "MODULE.bazel"
            module_raw = members.get(module_path)
            if module_raw is None:
                raise ExtractionError(f"required module manifest is absent; {_source_context(source, module_path, _locator(source, module_path))}")
            module_text = _decode(source, module_path, module_raw)
            match = MODULE_RE.search(module_text)
            if not match:
                raise ExtractionError(f"module manifest lacks module(name=...); {_source_context(source, module_path, _locator(source, module_path))}")
            module_name = match.group(1).strip()
            line = module_text[:match.start()].count("\n") + 1
            module = _candidate(source, "score-module-manifest", module_path, module_raw, _line_locator(source, module_path, line, line, module_name), {"module_name": module_name, "title": f"S-Core module {module_name}", "description": "release-pinned Bazel module manifest"})
            observations.append({"candidate": module, "decision": import_profile.evaluate_candidate(profile, module)})

            component_class = classes["score-bazel-package"]
            for path in sorted(members):
                if not import_profile._selector_matches(component_class["selector"], path):
                    continue
                package_path = path.rsplit("/", 1)[0]
                component = _candidate(source, "score-bazel-package", path, members[path], _line_locator(source, path, 1, max(1, members[path].count(b"\n") + 1), package_path), {"module_name": module_name, "package_path": package_path, "title": f"S-Core Bazel package {package_path}", "description": "release-pinned Bazel package declaration"})
                component["existing_canonical_ids"] = sorted(observed_ids)
                decision = import_profile.evaluate_candidate(profile, component)
                observations.append({"candidate": component, "decision": decision})
                if decision.get("record"):
                    observed_ids.add(decision["record"]["canonical_id"])

        for path in sorted(members):
            if not _selected_docs(source, path):
                continue
            source_class = "score-design-need" if repository == "score" else "process-sphinx-need"
            for candidate in _need_candidates(source, source_class, path, members[path]):
                candidate["existing_canonical_ids"] = sorted(observed_ids)
                decision = import_profile.evaluate_candidate(profile, candidate)
                observations.append({"candidate": candidate, "decision": decision})
                if decision.get("record"):
                    observed_ids.add(decision["record"]["canonical_id"])
        for path in sorted(members):
            if any(path.startswith(f"{root}/") for root in source["source_paths"]) and not _selected_docs(source, path):
                skipped.append({"repository": repository, "release_ref": source["release_ref"], "resolved_commit": source["resolved_commit"], "path": path, "locator": _locator(source, path), "reason": "UNSUPPORTED-ARTIFACT"})

    observations.sort(key=lambda item: (item["candidate"]["repository"], item["candidate"]["locator"]["path"], item["candidate"]["locator"]["line_start"], item["candidate"]["source_class"]))
    skipped.sort(key=lambda item: (item["repository"], item["path"]))
    counts: dict[str, int] = {}
    for item in observations:
        key = str(item["decision"]["condition_id"])
        counts[key] = counts.get(key, 0) + 1
    return {
        "schema": RAW_SCHEMA,
        "project": manifest["project"],
        "release": manifest["release"],
        "manifest_sha256": _sha256(canonical_json_bytes(manifest)),
        "profile_id": profile["profile_id"],
        "profile_version": profile["profile_version"],
        "profile_sha256": _sha256(canonical_json_bytes(profile)),
        "canonical_corpus_written": False,
        "complete": False,
        "completion_reason": "raw candidates require Task 0019-05 normalization and Task 0019-07 curation; this is not a canonical corpus",
        "observations": observations,
        "skipped_artifacts": skipped,
        "summary": {"observations": len(observations), "skipped_artifacts": len(skipped), "conditions": dict(sorted(counts.items()))},
    }


def write_output(output: Path, result: dict[str, Any]) -> None:
    """Atomically promote an already-complete raw result; failures never create partial output."""
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_json_bytes(result)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, output)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="complete score-source-bom@v2 manifest")
    parser.add_argument("profile", type=Path, help="matching score-import-profile@v1")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd(), help="root containing retained snapshot paths")
    parser.add_argument("--output", type=Path, required=True, help="raw extraction JSON to atomically write")
    args = parser.parse_args(argv)
    try:
        result = extract(_load_object(args.manifest, "manifest"), _load_object(args.profile, "profile"), args.repository_root)
        write_output(args.output, result)
    except ExtractionError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
