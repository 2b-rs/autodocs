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
                resolved.append({
                    "id": rid,
                    **({"document": source["document"]} if source.get("document") else {}),
                    **({"page": source["page"]} if source.get("page") is not None else {}),
                    **({"url": source["url"]} if source.get("url") else {}),
                })
        status = "ambiguous" if ambiguous else "missing" if missing else "resolved" if refs else "none"
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
