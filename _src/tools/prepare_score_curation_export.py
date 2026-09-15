#!/usr/bin/env python3
"""Fail-closed local export preparation for the S-Core curation candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/campaign-evidence/eclipse-score-v0.6.0-curation-review"
DESTINATION = ROOT / "eclipse-score-v0.6.0-curation-review"
MARKER = "UNVALIDATED — AWAITING CURATOR CONFIRMATION"
STATUS = "invalid/to-be-confirmed"
EXPECTED_RECORDS = 2239
EXPECTED = {
    "evidence.json": "df65c6faca93059ff86f92ca5a2dd92ab636503cf6fe01775a857d013ee68cd2",
    "validation.json": "ff88159d2a65930c1b512297898c6a4a5f46e572d01a3da15b0e8c2a69d934cf",
}
REVIEW_CLIENT_SHA256 = "bd6e23ae7454e7dee4daba98a104fa76db0ef9cdf54713ef35569a6c992ef0e2"
STYLESHEET_SHA256 = "7fa99621f52bac786f6793024eda694f0d54454cd8715bc346292c6c5d0d133c"
PREVIOUS_APPROVED_TREE_SHA256 = "7c514686ba7241416dbab340b4cad9abe032e2c6150e807b302efac363d08283"
PUBLIC_ROOT_FILES = frozenset({"index.html", "participate.html", "process.html", "review_request.js", "style.css", "evidence.json", "validation.json"})
PUBLIC_DIRECTORIES = ("assets", "en", "records")


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []
        self.attributes: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name: value or "" for name, value in attrs}
        self.attributes.append((tag, values))
        for name in ("href", "src"):
            if values.get(name):
                self.targets.append(values[name])


def fail(message: str) -> None:
    raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular_files(tree: Path) -> dict[str, Path]:
    if not tree.is_dir() or tree.is_symlink():
        fail(f"tree must be a non-symlink directory: {tree}")
    files: dict[str, Path] = {}
    for path in tree.rglob("*"):
        relative = path.relative_to(tree)
        if path.is_symlink():
            fail(f"symlink not permitted: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            fail(f"non-regular path not permitted: {relative}")
        name = relative.as_posix()
        if not name or name.startswith("/") or ".." in PurePosixPath(name).parts:
            fail(f"unsafe tree path: {name}")
        files[name] = path
    if not files:
        fail(f"tree is empty: {tree}")
    return files


def is_public_export_path(name: str) -> bool:
    path = PurePosixPath(name)
    return name in PUBLIC_ROOT_FILES or (len(path.parts) > 1 and path.parts[0] in PUBLIC_DIRECTORIES)


def public_files(files: dict[str, Path]) -> dict[str, Path]:
    selected = {name: path for name, path in files.items() if is_public_export_path(name)}
    if not selected:
        fail("source has no public export artifacts")
    return selected


def reject_unexpected_public_paths(files: dict[str, Path]) -> None:
    unexpected = sorted(name for name in files if not is_public_export_path(name))
    if unexpected:
        fail(f"unexpected public export path: {unexpected[0]}")


def export_content(name: str, path: Path) -> bytes:
    data = path.read_bytes()
    if not name.endswith(".html"):
        return data
    if name.startswith("en/"):
        old, new = 'href="../unresolved.html"', 'href="unresolved.html"'
    elif name.startswith("records/"):
        old, new = 'href="../unresolved.html"', 'href="../en/unresolved.html"'
    else:
        old, new = 'href="unresolved.html"', 'href="en/unresolved.html"'
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"public link rewrite is not UTF-8: {name}: {exc}")
    if text.count(old) > 1:
        fail(f"unexpected public link shape: {name}")
    return text.replace(old, new).encode("utf-8")


def parsed_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON manifest {path.name}: {exc}")
    if not isinstance(value, dict):
        fail(f"JSON manifest must be an object: {path.name}")
    return value


def tree_digest(files: dict[str, Path]) -> str:
    return hashlib.sha256(b"".join(name.encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest() for name, path in sorted(files.items()))).hexdigest()


def ensure_link_scope(tree: Path, name: str, parser: Links) -> None:
    for target in parser.targets:
        if any(ord(character) < 32 or ord(character) == 127 for character in target) or "\\" in target:
            fail(f"unsafe link target: {name} -> {target!r}")
        if target.startswith("//"):
            fail(f"protocol-relative link target: {name} -> {target}")
        parsed = urlsplit(target)
        if parsed.scheme in ("https", "http", "mailto"):
            continue
        if parsed.scheme or parsed.netloc or target.startswith("/"):
            fail(f"non-allowlisted link target: {name} -> {target}")
        local_path = unquote(parsed.path)
        if "\\" in local_path or any(ord(character) < 32 or ord(character) == 127 for character in local_path):
            fail(f"unsafe normalized link target: {name} -> {target!r}")
        candidate = ((tree / name).parent / local_path).resolve()
        try:
            candidate.relative_to(tree.resolve())
        except ValueError:
            fail(f"link escapes export scope: {name} -> {target}")
        if candidate.is_symlink() or not candidate.is_file():
            fail(f"broken local link: {name} -> {target}")


def validate_tree(tree: Path) -> dict[str, Any]:
    files = regular_files(tree)
    reject_unexpected_public_paths(files)
    for required, expected in EXPECTED.items():
        if required not in files:
            fail(f"missing required manifest: {required}")
        if digest(files[required]) != expected:
            fail(f"manifest digest mismatch: {required}")
    for required, expected in (("review_request.js", REVIEW_CLIENT_SHA256), ("style.css", STYLESHEET_SHA256)):
        if required not in files or digest(files[required]) != expected:
            fail(f"pinned payload mismatch: {required}")
    process_text = files.get("process.html").read_text(encoding="utf-8") if "process.html" in files else ""
    for anchor in ("flag-for-review-protocol", "storage-and-privacy"):
        if f'id="{anchor}"' not in process_text:
            fail(f"process anchor missing: {anchor}")
    evidence = parsed_json(files["evidence.json"])
    validation = parsed_json(files["validation.json"])
    if evidence.get("scope") != "unvalidated-curation-candidates" or validation.get("scope") != "unvalidated-curation-candidates":
        fail("manifest scope mismatch")
    if evidence.get("validation_marker") != MARKER:
        fail("evidence marker mismatch")
    if validation.get("result") != "PASS":
        fail("validation result is not PASS")
    manifest = evidence.get("candidate_manifest")
    if not isinstance(manifest, list) or len(manifest) != EXPECTED_RECORDS:
        fail("candidate manifest count mismatch")
    if evidence.get("candidate_manifest_sha256") != validation.get("candidate_manifest_sha256"):
        fail("candidate manifest digest mismatch")
    counts = evidence.get("counts")
    if not isinstance(counts, dict) or counts.get("records") != EXPECTED_RECORDS or counts.get("candidate_pages") != EXPECTED_RECORDS or counts.get("by_status") != {STATUS: EXPECTED_RECORDS}:
        fail("candidate status/count mismatch")
    pages: set[str] = set()
    for entry in manifest:
        if not isinstance(entry, dict):
            fail("malformed candidate manifest entry")
        page = entry.get("page")
        status = entry.get("status")
        if not isinstance(page, str) or not page.startswith("records/") or not page.endswith(".html"):
            fail("candidate manifest page scope mismatch")
        if page in pages or page not in files:
            fail("candidate manifest page mismatch")
        pages.add(page)
        if not isinstance(status, dict) or status.get("state") != STATUS:
            fail("candidate status mismatch")
        if not all(isinstance(entry.get(key), str) and entry[key] for key in ("canonical_id", "version_id", "source_locator")):
            fail("candidate identity/provenance mismatch")
    record_pages = {name for name in files if name.startswith("records/") and name.endswith(".html") and name != "records/index.html"}
    if record_pages != pages or len(record_pages) != EXPECTED_RECORDS:
        fail("individual record HTML page count mismatch")
    for name, path in files.items():
        if not name.endswith(".html"):
            continue
        text = path.read_text(encoding="utf-8")
        if MARKER not in text:
            fail(f"no-JavaScript marker missing: {name}")
        parser = Links()
        parser.feed(text)
        ensure_link_scope(tree, name, parser)
        if name in record_pages:
            attributes = parser.attributes
            if not any(values.get("data-validation-state") == "unvalidated" for _, values in attributes):
                fail(f"candidate status marker missing: {name}")
            if not any(values.get("data-unvalidated-marker") == "awaiting-curator-confirmation" for _, values in attributes):
                fail(f"candidate marker missing: {name}")
            if not any(values.get("id") == "source-locator" for _, values in attributes):
                fail(f"candidate provenance missing: {name}")
            if not any(values.get("data-curation-route") == "review-request" for _, values in attributes):
                fail(f"candidate participation route missing: {name}")
            if any(value in text for value in ('data-validation-state="valid"', 'data-validation-state="accepted"', 'data-factual-publication="true"', 'data-authoritative="true"')):
                fail(f"misleading candidate status: {name}")
    tree_hash = tree_digest(files)
    return {"files": len(files), "record_pages": len(record_pages), "tree_sha256": tree_hash, "evidence_sha256": EXPECTED["evidence.json"], "validation_sha256": EXPECTED["validation.json"]}


def ensure_distinct(source: Path, destination: Path) -> None:
    source, destination = source.resolve(), destination.resolve()
    if source == destination or source in destination.parents or destination in source.parents:
        fail("source/destination overlap is forbidden")


def prepare(source: Path = SOURCE, destination: Path = DESTINATION) -> dict[str, Any]:
    ensure_distinct(source, destination)
    source_files = public_files(regular_files(source))
    destination_summary: dict[str, Any] | None = None
    previous_approved = False
    if destination.exists():
        destination_files = regular_files(destination)
        try:
            destination_summary = validate_tree(destination)
        except ValueError:
            previous_approved = tree_digest(destination_files) == PREVIOUS_APPROVED_TREE_SHA256
            if not previous_approved:
                raise
        if not previous_approved and (set(source_files) != set(destination_files) or any(export_content(name, path) != destination_files[name].read_bytes() for name, path in source_files.items())):
                fail("unmanaged destination file or content mismatch")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.prepare-", dir=destination.parent))
    try:
        for name, path in source_files.items():
            output = staging / name
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(export_content(name, path))
        source_summary = validate_tree(staging)
        if destination.exists():
            if not previous_approved and (destination_summary is None or destination_summary != source_summary):
                fail("destination reconciliation mismatch")
            shutil.rmtree(destination)
        os.replace(staging, destination)
        promoted = validate_tree(destination)
        if promoted != source_summary:
            fail("post-promotion reconciliation mismatch")
        return promoted
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "validate"))
    args = parser.parse_args()
    if args.command == "validate":
        summary = validate_tree(DESTINATION)
    else:
        summary = prepare()
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
