#!/usr/bin/env python3
"""Build or verify the retained offline Eclipse S-Core source snapshot.

The verifier reads only the release BOM, the tracked plain-tar snapshots, and
its tracked inventory.  It neither invokes Git nor accesses the network, so a
fresh checkout containing those files can verify the retained source evidence
without the upstream repositories being available.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from urllib.parse import quote

import score_campaign_manifest as campaign_manifest

INVENTORY_SCHEMA = "score-source-snapshot-inventory@v1"
SNAPSHOT_SCHEMA = "score-source-snapshot@v1"
CHUNK_SIZE = 1024 * 1024


class SnapshotError(ValueError):
    """Raised when retained source evidence is absent, malformed, or altered."""


def canonical_json_bytes(value: Any) -> bytes:
    """Encode inventory output in one deterministic UTF-8 representation."""
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _sha256_stream(stream: Any) -> str:
    digest = hashlib.sha256()
    while chunk := stream.read(CHUNK_SIZE):
        digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    try:
        with path.open("rb") as stream:
            return _sha256_stream(stream)
    except OSError as error:
        raise SnapshotError(f"cannot read retained archive {path}: {error}") from error


def _repository_path(repository_root: Path, relative_path: str, label: str) -> Path:
    root = repository_root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise SnapshotError(f"{label} escapes repository root: {relative_path}") from error
    return candidate


def _safe_tar_path(name: str, source: str) -> None:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts:
        raise SnapshotError(f"retained archive for {source!r} contains unsafe member path {name!r}")


def _is_selected(path: str, selected_paths: Sequence[str]) -> bool:
    return any(path == selected or path.startswith(f"{selected}/") for selected in selected_paths)


def _locator(source: Mapping[str, Any], path: str) -> str:
    repository_url = str(source["repository_url"])
    repository_web_url = repository_url.removesuffix(".git")
    return f"{repository_web_url}/blob/{source['resolved_commit']}/{quote(path, safe='/')}"


def _artifact_record(source: Mapping[str, Any], path: str, size: int, digest: str) -> dict[str, Any]:
    return {
        "locator": _locator(source, path),
        "path": path,
        "release_ref": source["release_ref"],
        "repository": source["repository"],
        "repository_url": source["repository_url"],
        "resolved_commit": source["resolved_commit"],
        "sha256": digest,
        "size_bytes": size,
    }


def _archive_artifacts(source: Mapping[str, Any], archive_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected_paths = source["source_paths"]
    license_notice = source["license_notice"]
    artifacts: list[dict[str, Any]] = []
    license_artifact: dict[str, Any] | None = None
    seen_files: set[str] = set()

    try:
        with tarfile.open(archive_path, mode="r:") as archive:
            for member in archive.getmembers():
                _safe_tar_path(member.name, str(source["repository"]))
                if member.isdir():
                    continue
                if not member.isfile():
                    raise SnapshotError(
                        f"retained archive for {source['repository']!r} contains unsupported member "
                        f"type at {member.name!r}"
                    )
                if member.name in seen_files:
                    raise SnapshotError(
                        f"retained archive for {source['repository']!r} repeats file {member.name!r}"
                    )
                seen_files.add(member.name)

                selected = _is_selected(member.name, selected_paths)
                notice = member.name == license_notice
                if not selected and not notice:
                    continue
                stream = archive.extractfile(member)
                if stream is None:
                    raise SnapshotError(
                        f"retained archive for {source['repository']!r} cannot read member {member.name!r}"
                    )
                with stream:
                    digest = _sha256_stream(stream)
                record = _artifact_record(source, member.name, member.size, digest)
                if selected:
                    artifacts.append(record)
                if notice:
                    license_artifact = record
    except (OSError, tarfile.TarError) as error:
        raise SnapshotError(f"cannot read retained archive {archive_path}: {error}") from error

    artifacts.sort(key=lambda item: item["path"])
    if not artifacts:
        raise SnapshotError(
            f"retained archive for {source['repository']!r} contains no regular file under "
            f"the selected source paths {selected_paths!r}"
        )
    if license_artifact is None:
        raise SnapshotError(
            f"retained archive for {source['repository']!r} lacks manifest license notice {license_notice!r}"
        )
    return artifacts, license_artifact


def build_inventory(value: Any, repository_root: Path) -> dict[str, Any]:
    """Derive a deterministic selected-artifact inventory from retained archives."""
    errors = campaign_manifest.validate_bom(value, require_complete=True)
    if errors:
        raise SnapshotError("BOM validation failed: " + "; ".join(errors))
    assert isinstance(value, Mapping)
    sources = value["sources"]
    assert isinstance(sources, list)

    inventory_sources: list[dict[str, Any]] = []
    for source in sorted(sources, key=lambda item: str(item["repository"])):
        assert isinstance(source, Mapping)
        archive_path = _repository_path(
            repository_root,
            str(source["snapshot_archive"]),
            f"snapshot archive for {source['repository']!r}",
        )
        if not archive_path.is_file():
            raise SnapshotError(f"retained archive for {source['repository']!r} is not a file: {archive_path}")
        archive_sha256 = sha256_file(archive_path)
        expected_sha256 = source["archive"]["sha256"]
        if archive_sha256 != expected_sha256:
            raise SnapshotError(
                f"retained archive for {source['repository']!r} has SHA-256 {archive_sha256}, "
                f"expected {expected_sha256}"
            )
        artifacts, license_artifact = _archive_artifacts(source, archive_path)
        inventory_sources.append(
            {
                "archive_sha256": archive_sha256,
                "archive_size_bytes": archive_path.stat().st_size,
                "artifact_count": len(artifacts),
                "artifacts": artifacts,
                "license_notice": license_artifact,
                "ref_kind": source["ref_kind"],
                "release_ref": source["release_ref"],
                "repository": source["repository"],
                "repository_url": source["repository_url"],
                "resolved_commit": source["resolved_commit"],
                "snapshot_archive": source["snapshot_archive"],
                "source_paths": source["source_paths"],
            }
        )

    return {
        "project": value["project"],
        "release": value["release"],
        "schema": INVENTORY_SCHEMA,
        "sources": inventory_sources,
    }


def write_inventory(value: Any, repository_root: Path) -> tuple[Path, str, int]:
    """Write the canonical inventory to the manifest-linked retained path."""
    assert isinstance(value, Mapping)
    snapshot = value["snapshot"]
    assert isinstance(snapshot, Mapping)
    inventory_path = _repository_path(repository_root, str(snapshot["inventory"]), "snapshot inventory")
    inventory = build_inventory(value, repository_root)
    encoded = canonical_json_bytes(inventory)
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_bytes(encoded)
    return inventory_path, hashlib.sha256(encoded).hexdigest(), sum(
        source["artifact_count"] for source in inventory["sources"]
    )


def verify_snapshot(value: Any, repository_root: Path) -> tuple[str, int]:
    """Verify archives and prove the committed inventory is their exact derivation."""
    assert isinstance(value, Mapping)
    snapshot = value["snapshot"]
    assert isinstance(snapshot, Mapping)
    inventory_path = _repository_path(repository_root, str(snapshot["inventory"]), "snapshot inventory")
    if not inventory_path.is_file():
        raise SnapshotError(f"retained inventory is not a file: {inventory_path}")
    actual_bytes = inventory_path.read_bytes()
    actual_sha256 = hashlib.sha256(actual_bytes).hexdigest()
    expected_inventory_sha256 = snapshot["inventory_sha256"]
    if actual_sha256 != expected_inventory_sha256:
        raise SnapshotError(
            f"retained inventory has SHA-256 {actual_sha256}, expected {expected_inventory_sha256}"
        )
    expected_bytes = canonical_json_bytes(build_inventory(value, repository_root))
    if actual_bytes != expected_bytes:
        raise SnapshotError(
            f"retained inventory {inventory_path} does not match a deterministic reconstruction from the archives"
        )
    inventory = json.loads(actual_bytes)
    return actual_sha256, sum(source["artifact_count"] for source in inventory["sources"])


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SnapshotError(f"cannot read BOM {path}: {error}") from error


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write-inventory", action="store_true", help="derive and write the canonical inventory")
    action.add_argument("--verify", action="store_true", help="verify retained archives and canonical inventory offline")
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="repository root containing the manifest-linked snapshot paths (default: current directory)",
    )
    parser.add_argument("manifest", type=Path, help="path to the score-source-bom@v2 manifest")
    args = parser.parse_args(argv)

    try:
        value = _load_json(args.manifest)
        if args.write_inventory:
            path, digest, artifact_count = write_inventory(value, args.repository_root)
            print(f"WROTE: {path} SHA-256={digest} artifacts={artifact_count}")
        else:
            digest, artifact_count = verify_snapshot(value, args.repository_root)
            print(f"OK: retained snapshot verifies offline SHA-256={digest} artifacts={artifact_count}")
    except SnapshotError as error:
        print(f"ERROR: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
