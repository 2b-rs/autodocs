#!/usr/bin/env python3
"""Publish exactly one approved subtree into an explicitly named destination directory.

Why this tool exists
--------------------
The repository could publish *everything* or *nothing*, but not *what was
approved*. Management approves an artifact as a subtree pinned by a tree
digest; the existing publishers select by a fixed directory list
(``_src/publish.sh``) or by "all tracked files minus an exclusion list"
(``_src/tools/publish_public_site.sh``). Neither can honour an approval that
covers one bounded subtree, so an operator faced the choice between publishing
something other than what was approved or publishing nothing.

What this tool does
-------------------
It materialises one caller-named subtree into a caller-named destination
directory, and nothing else:

* the expected tree digest is a **required** argument, recomputed over the
  actual source directory immediately before the first write, and any mismatch
  is a refusal (nothing is written);
* paths outside ``<destination-root>/<subtree>`` are never created, modified or
  deleted;
* deletions happen only for paths the source no longer contains, only inside
  the destination subtree, and the complete deletion list is reported before
  the first deletion is performed;
* ``--dry-run`` reports the complete intended effect (created / modified /
  deleted, with counts and a bounded sample) and writes nothing;
* an explicit ``--authorization-ref`` (commit or record id) is required and is
  written into the publication evidence. The tool never invents authority.

What this tool deliberately does NOT do
---------------------------------------
It performs no version-control operation, contacts no network, creates no
commit and pushes nothing. It therefore embeds no destination default, no
remote, no credential and no commit identity — there is nothing of that kind in
it at all. Turning the prepared destination directory into a published state
remains a separate, separately authorised operator step under the identity and
destination rules that already govern the whole-site publishers.

Tree digest procedure (reproducible by hand)
--------------------------------------------
Identical to ``_src/tools/prepare_score_curation_export.py``:

1. list every regular file below the source directory;
2. express each as a relative POSIX path and sort the paths (code point order);
3. for each, in that order, append: the UTF-8 bytes of the relative path, one
   ``NUL`` byte (``0x00``), then the **raw 32-byte** SHA-256 of the file's
   contents (not its hex form);
4. the tree digest is the hex SHA-256 of that concatenated byte stream.

Shell equivalent for a reviewer:

    cd <source>; find . -type f | sed 's|^\\./||' | LC_ALL=C sort | while read -r p; do
      printf '%s\\0' "$p"; shasum -a 256 -b "$p" | cut -d' ' -f1 | xxd -r -p
    done | shasum -a 256

Exit codes: 0 success, 1 refusal (nothing was published), 2 usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

TOOL = "publish_approved_subtree"
CONTRACT_VERSION = 1

# Guards inherited from _src/publish.sh: these must never enter a destination.
PRIVATE_COMPONENTS = ("_src", "output", ".gitignore", ".git")

DIGEST_PROCEDURE = (
    "sha256 over path-sorted records of (utf-8 relative posix path bytes, "
    "0x00, raw 32-byte sha256 of file contents)"
)

DEFAULT_SAMPLE = 10
EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2


class Refusal(Exception):
    """Raised when the tool declines to act. Nothing has been written."""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _record_outcome(
    journal_path: Optional[str],
    phase: str,
    status: int,
    path: str,
    entries: int,
    previous: Optional[str],
    promoted: Optional[str],
    backup: Optional[str],
    task_id: str,
) -> None:
    """Append one durable outcome/recovery record for a mutating step.

    Written and flushed immediately after the step it describes, so an
    interrupted run still leaves a durable record of the last completed
    operation and of what it replaced.
    """
    if journal_path is None:
        return
    record = {
        "tool": TOOL,
        "timestamp": _now(),
        "phase": phase,
        "action": phase,
        "status": status,
        "outcome": status,
        "path": path,
        "entries": entries,
        "previous": previous,
        "promoted": promoted,
        "backup": backup,
        "task_id": task_id,
    }
    with open(journal_path, "a", encoding="utf-8") as journal:
        journal.write(json.dumps(record, sort_keys=True) + "\n")
        journal.flush()
        os.fsync(journal.fileno())


# --------------------------------------------------------------------------
# Digest
# --------------------------------------------------------------------------


def file_digest(path: Path) -> bytes:
    """Raw 32-byte SHA-256 of a file's contents."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.digest()


def collect_regular_files(root: Path) -> Dict[str, bytes]:
    """Map relative POSIX path -> raw per-file SHA-256 for every regular file.

    Symbolic links and other non-regular entries are a refusal: a link can name
    a path outside the approved subtree, which this tool must never publish.
    """
    if not root.is_dir() or root.is_symlink():
        raise Refusal(f"source is not an existing directory: {root}")
    collected: Dict[str, bytes] = {}
    for directory, subdirectories, names in os.walk(root, followlinks=False):
        subdirectories.sort()
        for name in sorted(names):
            absolute = Path(directory) / name
            relative = absolute.relative_to(root).as_posix()
            if absolute.is_symlink():
                raise Refusal(f"symbolic link in source is not publishable: {relative}")
            if not absolute.is_file():
                raise Refusal(f"non-regular file in source is not publishable: {relative}")
            collected[relative] = file_digest(absolute)
        for name in sorted(subdirectories):
            if (Path(directory) / name).is_symlink():
                relative = (Path(directory) / name).relative_to(root).as_posix()
                raise Refusal(f"symbolic link in source is not publishable: {relative}")
    return collected


def tree_digest(files: Dict[str, bytes]) -> str:
    """Tree digest over an already-collected {relative path: raw sha256} map."""
    stream = hashlib.sha256()
    for relative in sorted(files):
        stream.update(relative.encode("utf-8"))
        stream.update(b"\0")
        stream.update(files[relative])
    return stream.hexdigest()


def compute_tree_digest(root: Path) -> Tuple[str, Dict[str, bytes]]:
    files = collect_regular_files(root)
    return tree_digest(files), files


# --------------------------------------------------------------------------
# Path guards
# --------------------------------------------------------------------------


def check_relative_path(relative: str, label: str) -> Sequence[str]:
    if not relative or relative in (".", "/"):
        raise Refusal(f"{label} must be a non-empty relative path")
    if relative.startswith("/") or (
        len(relative) > 1 and relative[1] == ":" and relative[0].isalpha()
    ):
        raise Refusal(f"{label} must be relative, not absolute: {relative}")
    parts = [part for part in relative.replace("\\", "/").split("/") if part]
    if any(part == ".." for part in parts):
        raise Refusal(f"{label} must not traverse upwards: {relative}")
    if any(part == "." for part in parts):
        raise Refusal(f"{label} must not contain '.' components: {relative}")
    return parts


def check_private_components(parts: Sequence[str], relative: str) -> None:
    for part in parts:
        if part in PRIVATE_COMPONENTS:
            raise Refusal(
                f"refusing publication: private path component '{part}' would enter "
                f"the destination via {relative}"
            )


def check_distinct(source: Path, destination_subtree: Path) -> None:
    source = source.resolve()
    parent = destination_subtree.parent.resolve()
    destination = parent / destination_subtree.name
    if source == destination or source in destination.parents or destination in source.parents:
        raise Refusal("source and destination subtree must not overlap")


def resolve_destination_subtree(destination_root: Path, subtree: str) -> Path:
    parts = check_relative_path(subtree, "--subtree")
    check_private_components(parts, subtree)
    if not destination_root.is_dir():
        raise Refusal(f"destination root is not an existing directory: {destination_root}")
    root = destination_root.resolve()
    candidate = destination_root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise Refusal(
                f"destination subtree path traverses a symbolic link: "
                f"{candidate.relative_to(destination_root).as_posix()}"
            )
    existing = candidate
    while not existing.exists():
        existing = existing.parent
    resolved = existing.resolve()
    if resolved != root and root not in resolved.parents:
        raise Refusal("destination subtree resolves outside the destination root")
    return candidate


def check_outside_destination(path: Optional[Path], destination_subtree: Path, label: str) -> None:
    if path is None:
        return
    target = path.parent.resolve() / path.name
    subtree = destination_subtree.parent.resolve() / destination_subtree.name
    if target == subtree or subtree in target.parents:
        raise Refusal(f"{label} must not be written inside the published subtree: {path}")


# --------------------------------------------------------------------------
# Plan
# --------------------------------------------------------------------------


def destination_inventory(destination_subtree: Path) -> Dict[str, bytes]:
    if not destination_subtree.exists():
        return {}
    return collect_regular_files(destination_subtree)


def build_plan(
    source: Path,
    destination_root: Path,
    destination_subtree: Path,
    subtree: str,
    expected_digest: str,
    authorization_ref: str,
    mode: str,
    sample_size: int,
) -> Dict[str, object]:
    actual_digest, source_files = compute_tree_digest(source)
    for relative in source_files:
        parts = check_relative_path(relative, "source path")
        check_private_components(parts, f"{subtree}/{relative}")
    existing = destination_inventory(destination_subtree)

    created = sorted(name for name in source_files if name not in existing)
    modified = sorted(
        name
        for name in source_files
        if name in existing and existing[name] != source_files[name]
    )
    unchanged = sorted(
        name
        for name in source_files
        if name in existing and existing[name] == source_files[name]
    )
    deleted = sorted(name for name in existing if name not in source_files)

    return {
        "tool": TOOL,
        "contract_version": CONTRACT_VERSION,
        "timestamp": _now(),
        "mode": mode,
        "authorization_ref": authorization_ref,
        "source": str(source),
        "destination_root": str(destination_root),
        "subtree": subtree,
        "destination_subtree": str(destination_subtree),
        "expected_tree_digest": expected_digest,
        "actual_tree_digest": actual_digest,
        "digest_matches": actual_digest == expected_digest,
        "digest_procedure": DIGEST_PROCEDURE,
        "counts": {
            "source_files": len(source_files),
            "destination_files_before": len(existing),
            "created": len(created),
            "modified": len(modified),
            "deleted": len(deleted),
            "unchanged": len(unchanged),
        },
        "created": created,
        "modified": modified,
        "deleted": deleted,
        "sample": {
            "created": created[:sample_size],
            "modified": modified[:sample_size],
            "deleted": deleted[:sample_size],
        },
        "sample_size": sample_size,
        "source_files": sorted(source_files),
    }


def format_report(plan: Dict[str, object], stream) -> None:
    counts = plan["counts"]
    sample = plan["sample"]
    print(f"{TOOL}: mode={plan['mode']}", file=stream)
    print(f"  authorization_ref : {plan['authorization_ref']}", file=stream)
    print(f"  source            : {plan['source']}", file=stream)
    print(f"  destination_root  : {plan['destination_root']}", file=stream)
    print(f"  subtree           : {plan['subtree']}", file=stream)
    print(f"  expected digest   : {plan['expected_tree_digest']}", file=stream)
    print(f"  actual digest     : {plan['actual_tree_digest']}", file=stream)
    print(f"  digest matches    : {'yes' if plan['digest_matches'] else 'NO'}", file=stream)
    print(f"  digest procedure  : {plan['digest_procedure']}", file=stream)
    print(
        "  counts            : source_files={source_files} created={created} "
        "modified={modified} deleted={deleted} unchanged={unchanged}".format(**counts),
        file=stream,
    )
    for category in ("created", "modified", "deleted"):
        total = counts[category]
        shown = sample[category]
        print(f"  {category} ({total}), showing {len(shown)}:", file=stream)
        for name in shown:
            print(f"    {category[0].upper()} {plan['subtree']}/{name}", file=stream)
        if total > len(shown):
            print(f"    ... {total - len(shown)} more (full list in the evidence record)", file=stream)
    print(
        "  outside the subtree: nothing is created, modified or deleted by this tool",
        file=stream,
    )


# --------------------------------------------------------------------------
# Apply
# --------------------------------------------------------------------------


def _write_file(destination: Path, source_file: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / f".{destination.name}.{os.getpid()}.tmp"
    data = source_file.read_bytes()
    with open(temporary, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, destination)
    return str(destination)


def apply_plan(
    plan: Dict[str, object],
    source: Path,
    destination_subtree: Path,
    expected_digest: str,
    authorization_ref: str,
    journal_path: Optional[str],
    stream,
) -> Dict[str, object]:
    """Re-verify the gate, then perform exactly the planned effect.

    The digest is recomputed over the actual source directory here, immediately
    before the first write, so a source that changed between planning and
    writing is refused rather than published.
    """
    verify_digest, verify_files = compute_tree_digest(source)
    if verify_digest != expected_digest:
        raise Refusal(
            "refusing publication: tree digest mismatch immediately before writing "
            f"(expected {expected_digest}, actual {verify_digest})"
        )
    if sorted(verify_files) != list(plan["source_files"]):
        raise Refusal("refusing publication: source inventory changed after planning")

    deleted: List[str] = list(plan["deleted"])
    if deleted:
        print(f"  deletions to be performed inside {plan['subtree']} ({len(deleted)}):", file=stream)
        for name in deleted:
            print(f"    D {plan['subtree']}/{name}", file=stream)
    else:
        print(f"  deletions to be performed inside {plan['subtree']}: none", file=stream)

    written: List[str] = []
    destination_subtree.mkdir(parents=True, exist_ok=True)
    for name in list(plan["created"]) + list(plan["modified"]):
        parts = check_relative_path(name, "source path")
        check_private_components(parts, f"{plan['subtree']}/{name}")
        target = destination_subtree.joinpath(*parts)
        promoted = _write_file(target, source.joinpath(*parts))
        _record_outcome(
            journal_path, "write", 0, str(target), len(written) + 1,
            None, promoted, None, authorization_ref,
        )
        written.append(name)

    removed: List[str] = []
    for name in deleted:
        parts = check_relative_path(name, "destination path")
        target = destination_subtree.joinpath(*parts)
        target.unlink()
        _record_outcome(
            journal_path, "delete", 0, str(target), len(removed) + 1,
            name, None, None, authorization_ref,
        )
        removed.append(name)

    pruned: List[str] = []
    for directory, _subdirectories, _names in os.walk(destination_subtree, topdown=False):
        current = Path(directory)
        if current == destination_subtree:
            continue
        if any(current.iterdir()):
            continue
        os.rmdir(current)
        _record_outcome(
            journal_path, "prune", 0, str(current), len(pruned) + 1,
            current.relative_to(destination_subtree).as_posix(), None, None, authorization_ref,
        )
        pruned.append(current.relative_to(destination_subtree).as_posix())

    final_digest, _final_files = compute_tree_digest(destination_subtree)
    result = dict(plan)
    result["mode"] = "apply"
    result["written"] = written
    result["removed"] = removed
    result["pruned_directories"] = pruned
    result["published_tree_digest"] = final_digest
    result["published_digest_matches"] = final_digest == expected_digest
    result["completed_at"] = _now()
    if not result["published_digest_matches"]:
        raise Refusal(
            "post-publication verification failed: destination subtree digest "
            f"{final_digest} does not equal the approved digest {expected_digest}"
        )
    _record_outcome(
        journal_path, "complete", 0, str(destination_subtree), len(written) + len(removed),
        expected_digest, final_digest, None, authorization_ref,
    )
    return result


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=TOOL,
        description="Publish exactly one approved, digest-pinned subtree into an "
        "explicitly named destination directory.",
    )
    parser.add_argument("--source", required=True, help="directory holding the approved subtree content")
    parser.add_argument(
        "--destination-root",
        required=True,
        help="destination working directory (no default; never resolved implicitly)",
    )
    parser.add_argument(
        "--subtree",
        required=True,
        help="relative POSIX path under the destination root that this publication owns",
    )
    parser.add_argument(
        "--expected-tree-digest",
        required=True,
        help="the approved tree digest; recomputed over the source before writing",
    )
    parser.add_argument(
        "--authorization-ref",
        required=True,
        help="commit hash or record id authorising this publication; written into the evidence",
    )
    parser.add_argument("--evidence", help="path for the JSON publication evidence record")
    parser.add_argument("--journal", help="path for the append-only outcome/recovery journal")
    parser.add_argument(
        "--sample",
        type=int,
        default=DEFAULT_SAMPLE,
        help=f"bounded per-category sample size in the report (default {DEFAULT_SAMPLE})",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="report the complete intended effect, write nothing")
    group.add_argument("--apply", action="store_true", help="verify the digest and perform the publication")
    return parser


def run(argv: Optional[Sequence[str]] = None, stream=None) -> int:
    stream = stream if stream is not None else sys.stdout
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.sample < 0:
            raise Refusal("--sample must not be negative")
        expected = args.expected_tree_digest.strip().lower()
        if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
            raise Refusal("--expected-tree-digest must be a 64-character hex sha256")
        if not args.authorization_ref.strip():
            raise Refusal("--authorization-ref must name a commit or record id")

        source = Path(args.source)
        destination_root = Path(args.destination_root)
        destination_subtree = resolve_destination_subtree(destination_root, args.subtree)
        check_distinct(source, destination_subtree)

        evidence_path = Path(args.evidence) if args.evidence else None
        journal_path = Path(args.journal) if args.journal else None
        check_outside_destination(evidence_path, destination_subtree, "--evidence")
        check_outside_destination(journal_path, destination_subtree, "--journal")
        if args.apply and evidence_path is None:
            raise Refusal("--apply requires --evidence: publication evidence is not optional")
        if evidence_path is not None and evidence_path.exists():
            raise Refusal(f"--evidence path already exists, refusing to overwrite: {evidence_path}")

        mode = "apply" if args.apply else "dry-run"
        plan = build_plan(
            source,
            destination_root,
            destination_subtree,
            args.subtree,
            expected,
            args.authorization_ref,
            mode,
            args.sample,
        )
        format_report(plan, stream)

        if not plan["digest_matches"]:
            raise Refusal(
                "refusing publication: tree digest mismatch "
                f"(expected {expected}, actual {plan['actual_tree_digest']})"
            )

        if args.dry_run:
            plan["published"] = False
            plan["note"] = "dry-run: nothing was created, modified or deleted"
            result = plan
            print("  dry-run complete: nothing was written", file=stream)
        else:
            result = apply_plan(
                plan,
                source,
                destination_subtree,
                expected,
                args.authorization_ref,
                str(journal_path) if journal_path else None,
                stream,
            )
            result["published"] = True
            print(
                "  publication complete: {written} written, {removed} deleted, "
                "destination digest verified".format(
                    written=len(result["written"]), removed=len(result["removed"])
                ),
                file=stream,
            )

        if evidence_path is not None:
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            with open(evidence_path, "w", encoding="utf-8") as handle:
                json.dump(result, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            print(f"  evidence written: {evidence_path}", file=stream)
        return EXIT_OK
    except Refusal as refusal:
        print(f"{TOOL}: {refusal}", file=sys.stderr)
        return EXIT_REFUSED
    except OSError as error:
        print(f"{TOOL}: filesystem error, publication not completed: {error}", file=sys.stderr)
        return EXIT_REFUSED


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        return run(argv)
    except SystemExit as exit_request:
        code = exit_request.code
        return EXIT_USAGE if code not in (0, None) else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
