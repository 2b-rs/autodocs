#!/usr/bin/env python3
"""Resolve canonical AUTOSAR RS references and update record metadata safely.

This module is deliberately independent from PDF extraction.  It consumes the
records produced by spec_scrape, builds a canonical RS index, and returns new
record values rather than mutating caller-owned dictionaries.
"""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

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
    rebuilt = copy.deepcopy(dict(record))
    if resolution.status == "none":
        return rebuilt, "none"
    value = list(resolution.upstream)
    if rebuilt.get("upstream") == value:
        return rebuilt, "unchanged"
    rebuilt["upstream"] = value
    return rebuilt, resolution.status if resolution.status in {"missing", "ambiguous"} else "updated"


def rebuild_record_files(record_paths: Iterable[Path], index: UpstreamIndex, *, write=False) -> dict:
    """Compare or rebuild files; writes are atomic and only touch changed files."""
    counts = {name: 0 for name in ("unchanged", "updated", "missing", "ambiguous", "none")}
    for path in record_paths:
        path = Path(path)
        before = json.loads(path.read_text(encoding="utf-8"))
        after, outcome = rebuild_upstream(before, index)
        counts[outcome] += 1
        if write and after != before:
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(json.dumps(after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temporary.replace(path)
    return counts
