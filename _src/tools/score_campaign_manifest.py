#!/usr/bin/env python3
"""Validate the release-pinned Eclipse S-Core source bill of materials.

The validator intentionally checks only the campaign boundary.  It does not
fetch repositories or infer a source inventory: a complete BOM is evidence,
not a best-effort scrape of the current upstream organisation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "score-source-bom@v2"
PROJECT = "ECLIPSE/S-CORE"
SCRAPER_PATH = "_src/tools/score_scrape.py"
STATES = {"draft-blocked", "complete"}
REF_KINDS = {"tag", "release-branch"}
MOVING_REFS = {"head", "main", "master", "trunk", "develop", "development"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

ROOT_KEYS = {
    "schema",
    "project",
    "release",
    "state",
    "sources",
    "exclusions",
    "scraper",
    "snapshot",
    "blocker",
}
SOURCE_KEYS = {
    "repository",
    "repository_url",
    "release_ref",
    "ref_kind",
    "resolved_commit",
    "source_paths",
    "archive",
    "license_notice",
    "snapshot_archive",
}
ARCHIVE_KEYS = {"algorithm", "sha256"}
EXCLUSION_KEYS = {"repository", "rationale"}
SCRAPER_KEYS = {"path", "commit"}
SNAPSHOT_KEYS = {"schema", "root", "inventory", "inventory_sha256", "verification_tool"}
SNAPSHOT_SCHEMA = "score-source-snapshot@v1"
SNAPSHOT_TOOL_PATH = "_src/tools/score_source_snapshot.py"
BLOCKER_KEYS = {"reason", "evidence"}


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_exact_keys(value: Mapping[str, Any], allowed: set[str], label: str, errors: list[str]) -> None:
    unexpected = sorted(set(value) - allowed)
    missing = sorted(allowed - set(value))
    if unexpected:
        errors.append(f"{label} has unexpected keys: {', '.join(unexpected)}")
    if missing:
        errors.append(f"{label} is missing keys: {', '.join(missing)}")


def _validate_relative_path(value: Any, label: str, errors: list[str]) -> None:
    if not _is_nonempty_string(value):
        errors.append(f"{label} must be a non-empty relative path")
        return
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{label} must be a repository-relative path without '..'")


def _validate_source(source: Any, index: int, errors: list[str]) -> str | None:
    label = f"sources[{index}]"
    if not _is_mapping(source):
        errors.append(f"{label} must be an object")
        return None

    _validate_exact_keys(source, SOURCE_KEYS, label, errors)
    repository = source.get("repository")
    if not _is_nonempty_string(repository) or not REPOSITORY_RE.fullmatch(repository):
        errors.append(f"{label}.repository must be a lowercase Eclipse S-Core repository slug")
        repository = None

    if repository is not None:
        expected_url = f"https://github.com/eclipse-score/{repository}.git"
        if source.get("repository_url") != expected_url:
            errors.append(f"{label}.repository_url must be {expected_url}")

    release_ref = source.get("release_ref")
    if not _is_nonempty_string(release_ref):
        errors.append(f"{label}.release_ref must be a non-empty immutable release label/ref")
    elif release_ref.strip().lower() in MOVING_REFS:
        errors.append(f"{label}.release_ref must not be a moving ref such as {release_ref!r}")

    if source.get("ref_kind") not in REF_KINDS:
        errors.append(f"{label}.ref_kind must be one of {', '.join(sorted(REF_KINDS))}")

    resolved_commit = source.get("resolved_commit")
    if not isinstance(resolved_commit, str) or not GIT_SHA_RE.fullmatch(resolved_commit):
        errors.append(f"{label}.resolved_commit must be a lowercase full 40-character Git SHA")

    source_paths = source.get("source_paths")
    if not isinstance(source_paths, list) or not source_paths:
        errors.append(f"{label}.source_paths must be a non-empty list")
    else:
        seen_paths: set[str] = set()
        for path_index, source_path in enumerate(source_paths):
            path_label = f"{label}.source_paths[{path_index}]"
            _validate_relative_path(source_path, path_label, errors)
            if isinstance(source_path, str):
                if source_path in seen_paths:
                    errors.append(f"{label}.source_paths must not repeat {source_path!r}")
                seen_paths.add(source_path)

    archive = source.get("archive")
    if not _is_mapping(archive):
        errors.append(f"{label}.archive must be an object")
    else:
        _validate_exact_keys(archive, ARCHIVE_KEYS, f"{label}.archive", errors)
        if archive.get("algorithm") != "sha256-git-archive":
            errors.append(f"{label}.archive.algorithm must be 'sha256-git-archive'")
        archive_hash = archive.get("sha256")
        if not isinstance(archive_hash, str) or not SHA256_RE.fullmatch(archive_hash):
            errors.append(f"{label}.archive.sha256 must be a lowercase 64-character SHA-256")

    _validate_relative_path(source.get("license_notice"), f"{label}.license_notice", errors)
    _validate_relative_path(source.get("snapshot_archive"), f"{label}.snapshot_archive", errors)
    return repository


def _validate_exclusion(exclusion: Any, index: int, errors: list[str]) -> str | None:
    label = f"exclusions[{index}]"
    if not _is_mapping(exclusion):
        errors.append(f"{label} must be an object")
        return None
    _validate_exact_keys(exclusion, EXCLUSION_KEYS, label, errors)
    repository = exclusion.get("repository")
    if not _is_nonempty_string(repository) or not REPOSITORY_RE.fullmatch(repository):
        errors.append(f"{label}.repository must be a lowercase Eclipse S-Core repository slug")
        return None
    if not _is_nonempty_string(exclusion.get("rationale")):
        errors.append(f"{label}.rationale must be a non-empty explanation")
    return repository


def _validate_scraper(scraper: Any, errors: list[str]) -> None:
    if not _is_mapping(scraper):
        errors.append("scraper must be an object")
        return
    _validate_exact_keys(scraper, SCRAPER_KEYS, "scraper", errors)
    if scraper.get("path") != SCRAPER_PATH:
        errors.append(f"scraper.path must be {SCRAPER_PATH!r}")
    commit = scraper.get("commit")
    if not isinstance(commit, str) or not GIT_SHA_RE.fullmatch(commit):
        errors.append("scraper.commit must be a lowercase full 40-character Git SHA")


def _validate_snapshot(snapshot: Any, state: Any, errors: list[str]) -> None:
    if state == "complete":
        if not _is_mapping(snapshot):
            errors.append("complete BOMs require a snapshot object")
            return
        _validate_exact_keys(snapshot, SNAPSHOT_KEYS, "snapshot", errors)
        if snapshot.get("schema") != SNAPSHOT_SCHEMA:
            errors.append(f"snapshot.schema must be {SNAPSHOT_SCHEMA!r}")
        root = snapshot.get("root")
        _validate_relative_path(root, "snapshot.root", errors)
        inventory = snapshot.get("inventory")
        _validate_relative_path(inventory, "snapshot.inventory", errors)
        if isinstance(root, str) and isinstance(inventory, str) and inventory != f"{root}/inventory.json":
            errors.append("snapshot.inventory must be snapshot.root plus '/inventory.json'")
        digest = snapshot.get("inventory_sha256")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            errors.append("snapshot.inventory_sha256 must be a lowercase 64-character SHA-256")
        if snapshot.get("verification_tool") != SNAPSHOT_TOOL_PATH:
            errors.append(f"snapshot.verification_tool must be {SNAPSHOT_TOOL_PATH!r}")
    elif snapshot is not None:
        errors.append("draft-blocked BOMs must not claim a retained snapshot")


def _validate_blocker(blocker: Any, state: Any, errors: list[str]) -> None:
    if state == "draft-blocked":
        if not _is_mapping(blocker):
            errors.append("draft-blocked BOMs require a blocker object")
            return
        _validate_exact_keys(blocker, BLOCKER_KEYS, "blocker", errors)
        if not _is_nonempty_string(blocker.get("reason")):
            errors.append("blocker.reason must be a non-empty explanation")
        if not _is_nonempty_string(blocker.get("evidence")):
            errors.append("blocker.evidence must identify the missing authoritative evidence")
    elif blocker is not None:
        errors.append("complete BOMs must not contain blocker")


def validate_bom(value: Any, *, require_complete: bool = False) -> list[str]:
    """Return deterministic validation errors for a S-Core source BOM.

    ``draft-blocked`` permits an empty source list only to preserve a durable,
    explicit record that source evidence is unavailable.  It never satisfies
    the release-import completion gate; callers use ``require_complete`` for
    that gate.
    """
    errors: list[str] = []
    if not _is_mapping(value):
        return ["manifest root must be an object"]

    unexpected = sorted(set(value) - ROOT_KEYS)
    missing = sorted({"schema", "project", "release", "state", "sources", "exclusions", "scraper"} - set(value))
    if unexpected:
        errors.append(f"manifest has unexpected keys: {', '.join(unexpected)}")
    if missing:
        errors.append(f"manifest is missing keys: {', '.join(missing)}")

    if value.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA!r}")
    if value.get("project") != PROJECT:
        errors.append(f"project must be {PROJECT!r}")
    if not _is_nonempty_string(value.get("release")):
        errors.append("release must be a non-empty release label")

    state = value.get("state")
    if state not in STATES:
        errors.append(f"state must be one of {', '.join(sorted(STATES))}")
    elif require_complete and state != "complete":
        errors.append("BOM is not complete: authoritative source evidence remains blocked")

    sources = value.get("sources")
    source_repositories: set[str] = set()
    if not isinstance(sources, list):
        errors.append("sources must be a list")
    else:
        if state == "complete" and not sources:
            errors.append("complete BOMs require at least one source")
        for index, source in enumerate(sources):
            repository = _validate_source(source, index, errors)
            if repository is not None:
                if repository in source_repositories:
                    errors.append(f"sources must not repeat repository {repository!r}")
                source_repositories.add(repository)

    exclusions = value.get("exclusions")
    exclusion_repositories: set[str] = set()
    if not isinstance(exclusions, list):
        errors.append("exclusions must be a list")
    else:
        for index, exclusion in enumerate(exclusions):
            repository = _validate_exclusion(exclusion, index, errors)
            if repository is not None:
                if repository in exclusion_repositories:
                    errors.append(f"exclusions must not repeat repository {repository!r}")
                if repository in source_repositories:
                    errors.append(f"repository {repository!r} cannot be both a source and an exclusion")
                exclusion_repositories.add(repository)

    snapshot = value.get("snapshot")
    _validate_scraper(value.get("scraper"), errors)
    _validate_snapshot(snapshot, state, errors)
    if _is_mapping(snapshot) and isinstance(snapshot.get("root"), str) and isinstance(sources, list):
        archive_prefix = f"{snapshot['root']}/archives/"
        for index, source in enumerate(sources):
            if _is_mapping(source) and source.get("snapshot_archive") != "" and isinstance(source.get("snapshot_archive"), str):
                if not source["snapshot_archive"].startswith(archive_prefix):
                    errors.append(f"sources[{index}].snapshot_archive must be under {archive_prefix!r}")
    _validate_blocker(value.get("blocker"), state, errors)
    return errors


def load_manifest(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _git_output(checkout: Path, *args: str) -> tuple[str | None, str | None]:
    try:
        result = subprocess.run(
            ["git", "-C", str(checkout), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as error:
        return None, str(error)
    if result.returncode:
        return None, result.stderr.strip() or f"git exited {result.returncode}"
    return result.stdout.strip(), None


def _git_archive_sha256(checkout: Path, commit: str) -> tuple[str | None, str | None]:
    try:
        process = subprocess.Popen(
            ["git", "-C", str(checkout), "archive", "--format=tar", commit],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as error:
        return None, str(error)

    assert process.stdout is not None
    digest = hashlib.sha256()
    while chunk := process.stdout.read(1024 * 1024):
        digest.update(chunk)
    process.stdout.close()
    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    if process.stderr:
        process.stderr.close()
    if process.wait() != 0:
        return None, stderr.strip() or "git archive failed"
    return digest.hexdigest(), None


def verify_bom_checkouts(value: Any, checkouts: Mapping[str, Path]) -> list[str]:
    """Verify checkout commits, remotes, and deterministic Git-archive hashes.

    This deliberately operates only on caller-supplied local clones.  Network
    retrieval and durable snapshot retention are the responsibility of
    Task 0019-02; this verification detects source drift without fetching.
    """
    errors = validate_bom(value, require_complete=True)
    if errors or not _is_mapping(value) or not isinstance(value.get("sources"), list):
        return errors

    sources = {source.get("repository"): source for source in value["sources"] if _is_mapping(source)}
    expected_repositories = set(sources)
    provided_repositories = set(checkouts)
    for repository in sorted(expected_repositories - provided_repositories):
        errors.append(f"missing checkout for source repository {repository!r}")
    for repository in sorted(provided_repositories - expected_repositories):
        errors.append(f"checkout supplied for unknown repository {repository!r}")

    for repository in sorted(expected_repositories & provided_repositories):
        source = sources[repository]
        checkout = checkouts[repository]
        if not checkout.is_dir():
            errors.append(f"checkout for {repository!r} is not a directory: {checkout}")
            continue

        head, error = _git_output(checkout, "rev-parse", "HEAD")
        if error:
            errors.append(f"cannot resolve checkout for {repository!r}: {error}")
            continue
        if head != source["resolved_commit"]:
            errors.append(
                f"checkout for {repository!r} resolves to {head}, expected {source['resolved_commit']}"
            )

        remote_url, error = _git_output(checkout, "remote", "get-url", "origin")
        if error:
            errors.append(f"cannot read origin for {repository!r}: {error}")
        elif remote_url != source["repository_url"]:
            errors.append(
                f"checkout for {repository!r} has origin {remote_url!r}, expected {source['repository_url']!r}"
            )

        archive_hash, error = _git_archive_sha256(checkout, source["resolved_commit"])
        if error:
            errors.append(f"cannot archive checkout for {repository!r}: {error}")
        elif archive_hash != source["archive"]["sha256"]:
            errors.append(
                f"checkout archive for {repository!r} has SHA-256 {archive_hash}, expected {source['archive']['sha256']}"
            )
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="reject draft-blocked manifests at an import/reproducibility completion gate",
    )
    parser.add_argument(
        "--verify-checkout",
        action="append",
        default=[],
        metavar="REPOSITORY=PATH",
        help="verify a local checkout's origin, commit, and Git-archive SHA-256; repeat for every source",
    )
    parser.add_argument("manifest", type=Path, help="path to a score-source-bom@v1 JSON file")
    args = parser.parse_args(argv)

    try:
        value = load_manifest(args.manifest)
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: cannot read {args.manifest}: {error}", file=sys.stderr)
        return 2

    checkouts: dict[str, Path] = {}
    for specification in args.verify_checkout:
        repository, separator, path = specification.partition("=")
        if not separator or not repository or not path:
            print("ERROR: --verify-checkout must use REPOSITORY=PATH", file=sys.stderr)
            return 2
        if repository in checkouts:
            print(f"ERROR: duplicate --verify-checkout for {repository!r}", file=sys.stderr)
            return 2
        checkouts[repository] = Path(path)

    errors = validate_bom(value, require_complete=args.require_complete or bool(checkouts))
    if not errors and checkouts:
        errors = verify_bom_checkouts(value, checkouts)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if checkouts:
        print(f"OK: {args.manifest} validates and all local source archives match")
    else:
        print(f"OK: {args.manifest} validates as {SCHEMA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
