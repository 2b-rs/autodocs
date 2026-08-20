#!/usr/bin/env python3
"""Resolve canonical AUTOSAR RS references and update record metadata safely.

This module is deliberately independent from PDF extraction.  It consumes the
records produced by spec_scrape, builds a canonical RS index, and returns new
record values rather than mutating caller-owned dictionaries.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from concurrent.futures import ProcessPoolExecutor

# NOTE: real OS processes. This previously failed under the MCP sandbox
# because ProcessPoolExecutor's inter-process queue needs POSIX semaphores
# (multiprocessing.synchronize.SemLock raised PermissionError: [Errno 1]
# Operation not permitted). The sandbox profile in runner-host/run-loop.sh now
# explicitly allows ipc-posix-sem-*/ipc-posix-shm-*, so process-based
# parallelism works again and gives true multi-core scaling (unlike threads,
# which are capped by the GIL for the CPU-bound regex/JSON work here).
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

LOG = logging.getLogger("spec_upstream")
if not LOG.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(message)s"))
    LOG.addHandler(_handler)
LOG.setLevel(logging.INFO)

EXPECTED_UNRESOLVED = {"RS_AP_00154", "RS_DIAG_04005"}
TRACE_RECORDS = Path(__file__).resolve().parent.parent / "spec" / "traceability"

RS_ID_RE = re.compile(r"(?<![A-Z0-9_])(RS_[A-Z0-9]+(?:_[A-Z0-9]+)+)(?![A-Z0-9_])", re.I)


def canonical_requirement_id(value: str) -> str:
    """Return a stable uppercase requirement identifier."""
    return re.sub(r"\s+", "", str(value)).upper()


def _walk_text(value, *, key=""):
    if key == "upstream":
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for child_key, child in value.items():
            yield from _walk_text(child, key=str(child_key))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            yield from _walk_text(child, key=key)


def referenced_rs_ids(record: Mapping) -> tuple[str, ...]:
    """Find explicit RS identifiers while ignoring already-derived metadata."""
    found = {
        canonical_requirement_id(match.group(1))
        for text in _walk_text(record)
        for match in RS_ID_RE.finditer(text)
    }
    return tuple(sorted(found))


def _record_id(record: Mapping) -> str:
    return canonical_requirement_id(
        record.get("id") or record.get("requirement_id") or record.get("requirement") or ""
    )


@dataclass(frozen=True)
class Resolution:
    status: str
    references: tuple[str, ...]
    upstream: tuple[dict, ...]


def _traceability_reverse_index() -> dict[str, tuple[dict, ...]]:
    """Satisfier-ID -> tuple of RS entries it satisfies, built once from disk.

    A module-level cache keeps ``resolve()`` calls O(1) per record instead of
    re-scanning every ``_src/spec/traceability/*.json`` file for each of the
    thousands of DB records being rebuilt.
    """
    reverse: dict[str, list[dict]] = {}
    if not TRACE_RECORDS.is_dir():
        return {}
    for path in sorted(TRACE_RECORDS.rglob("*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        rid = canonical_requirement_id(rec.get("id") or "")
        if not rid.startswith("RS_"):
            continue
        meta = rec.get("traceability_meta") or {}
        entry = {
            "id": rid,
            **({"document": meta.get("document")} if meta.get("document") else {}),
            **({"page": meta.get("page")} if meta.get("page") is not None else {}),
            "source": "traceability",
            "traceability_record": str(path),
        }
        for satisfier in (meta.get("satisfied_by") or []):
            satisfier_id = canonical_requirement_id(satisfier)
            if not satisfier_id:
                continue
            reverse.setdefault(satisfier_id, []).append(entry)
    return {key: tuple(values) for key, values in reverse.items()}


_TRACEABILITY_REVERSE_INDEX_CACHE: dict[str, tuple[dict, ...]] | None = None


def _traceability_rows_for_record(record_id: str) -> tuple[dict, ...]:
    global _TRACEABILITY_REVERSE_INDEX_CACHE
    if not record_id:
        return ()
    if _TRACEABILITY_REVERSE_INDEX_CACHE is None:
        _TRACEABILITY_REVERSE_INDEX_CACHE = _traceability_reverse_index()
    return _TRACEABILITY_REVERSE_INDEX_CACHE.get(canonical_requirement_id(record_id), ())


class UpstreamIndex:
    """Index canonical RS records without silently collapsing duplicates."""

    def __init__(self, records: Iterable[Mapping]):
        grouped: dict[str, list[dict]] = {}
        for source in records:
            rid = _record_id(source)
            if rid.startswith("RS_"):
                grouped.setdefault(rid, []).append(dict(source))
        self._records = {key: tuple(values) for key, values in grouped.items()}

    @classmethod
    def from_paths(cls, paths: Iterable[Path]) -> "UpstreamIndex":
        records = []
        for path in paths:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
            records.extend(value if isinstance(value, list) else [value])
        return cls(records)

    def resolve(self, record: Mapping) -> Resolution:
        refs = referenced_rs_ids(record)
        resolved, expected, missing, ambiguous = [], [], [], []
        seen = set()
        def add_resolution(entry):
            key = canonical_requirement_id(entry.get("id") or "")
            if not key or key in seen:
                return
            seen.add(key)
            resolved.append(entry)
        for rid in refs:
            matches = self._records.get(rid, ())
            if not matches and rid in EXPECTED_UNRESOLVED:
                expected.append(rid)
            elif not matches:
                missing.append(rid)
            elif len(matches) > 1:
                ambiguous.append(rid)
            else:
                source = matches[0]
                add_resolution({
                    "id": rid,
                    **({"document": source["document"]} if source.get("document") else {}),
                    **({"page": source["page"]} if source.get("page") is not None else {}),
                    **({"url": source["url"]} if source.get("url") else {}),
                    "source": "inline",
                })
        for entry in _traceability_rows_for_record(_record_id(record)):
            add_resolution(entry)
        status = "ambiguous" if ambiguous else "missing" if missing else "resolved" if (refs or resolved) else "none"
        diagnostics = [
            *({"id": rid, "status": "expected-unresolved"} for rid in expected),
            *({"id": rid, "status": "missing"} for rid in missing),
            *({"id": rid, "status": "ambiguous"} for rid in ambiguous),
        ]
        return Resolution(status, refs, tuple([*resolved, *diagnostics]))


def rebuild_upstream(record: Mapping, index: UpstreamIndex) -> tuple[dict, str]:
    """Return (rebuilt record, outcome), changing only ``upstream``.

    Outcomes are ``unchanged``, ``updated``, ``missing`` and ``ambiguous``;
    records without an RS reference are left unchanged with outcome ``none``.
    """
    resolution = index.resolve(record)
    if resolution.status == "none":
        return dict(record), "none"
    value = list(resolution.upstream)
    if record.get("upstream") == value:
        return dict(record), "unchanged"
    rebuilt = dict(record)
    rebuilt["upstream"] = value
    return rebuilt, resolution.status if resolution.status in {"missing", "ambiguous"} else "updated"


_WORKER_INDEX: UpstreamIndex | None = None
_WORKER_WRITE: bool = False


def _init_worker(index: UpstreamIndex, write: bool) -> None:
    """Pool initializer: unpickle ``index`` once per worker process, not per file.

    Passing ``index`` inside every task tuple forces the parent process to
    re-pickle the whole RS index for each of the thousands of files before a
    worker ever sees it. Binding it once via the pool's ``initializer``
    fixes that: pickling now happens exactly ``worker_count`` times instead
    of ``len(paths)`` times. Requires the sandbox profile's ipc-posix-sem-*/
    ipc-posix-shm-* allow rules (see runner-host/run-loop.sh) for SemLock creation.
    """
    global _WORKER_INDEX, _WORKER_WRITE
    _WORKER_INDEX = index
    _WORKER_WRITE = write


def _rebuild_record_file(path_str: str) -> tuple[str, str, bool, float, int, int]:
    started = time.perf_counter()
    path = Path(path_str)
    before = json.loads(path.read_text(encoding="utf-8"))
    after, outcome = rebuild_upstream(before, _WORKER_INDEX)
    changed = after != before
    if _WORKER_WRITE and changed:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    elapsed = time.perf_counter() - started
    return path_str, outcome, changed, elapsed, len(json.dumps(before, ensure_ascii=False)), len(json.dumps(after, ensure_ascii=False))


def rebuild_record_files(record_paths: Iterable[Path], index: UpstreamIndex, *, write=False, jobs: int | None = None) -> dict:
    """Compare or rebuild files; writes are atomic and only touch changed files."""
    counts = {name: 0 for name in ("unchanged", "updated", "missing", "ambiguous", "none")}
    paths = [str(Path(path)) for path in record_paths]
    if not paths:
        return counts
    worker_count = max(1, jobs or (os.cpu_count() or 1))
    started = time.perf_counter()
    durations: list[float] = []
    changed_files = 0
    bytes_before = 0
    bytes_after = 0
    LOG.info(
        "rebuild_record_files start mode=%s files=%d workers=%d",
        "write" if write else "compare",
        len(paths),
        worker_count,
    )
    with ProcessPoolExecutor(
        max_workers=worker_count,
        initializer=_init_worker,
        initargs=(index, write),
    ) as executor:
        for idx, (path_str, outcome, changed, elapsed, size_before, size_after) in enumerate(
            executor.map(_rebuild_record_file, paths, chunksize=25),
            start=1,
        ):
            counts[outcome] += 1
            durations.append(elapsed)
            bytes_before += size_before
            bytes_after += size_after
            if changed:
                changed_files += 1
            if idx == 1 or idx % 250 == 0 or idx == len(paths):
                LOG.info(
                    "rebuild_record_files progress processed=%d/%d changed=%d rate=%.1f files/s last=%.4fs path=%s",
                    idx,
                    len(paths),
                    changed_files,
                    idx / max(time.perf_counter() - started, 1e-9),
                    elapsed,
                    path_str,
                )
    total_elapsed = time.perf_counter() - started
    report = dict(counts)
    report["files"] = len(paths)
    report["workers"] = worker_count
    report["changed_files"] = changed_files
    report["elapsed_seconds"] = round(total_elapsed, 6)
    report["files_per_second"] = round(len(paths) / max(total_elapsed, 1e-9), 3)
    report["avg_file_seconds"] = round(sum(durations) / len(durations), 6)
    report["max_file_seconds"] = round(max(durations), 6)
    report["bytes_before"] = bytes_before
    report["bytes_after"] = bytes_after
    LOG.info(
        "rebuild_record_files done files=%d changed=%d elapsed=%.3fs rate=%.1f files/s avg=%.4fs max=%.4fs",
        len(paths),
        changed_files,
        total_elapsed,
        len(paths) / max(total_elapsed, 1e-9),
        sum(durations) / len(durations),
        max(durations),
    )
    return report
