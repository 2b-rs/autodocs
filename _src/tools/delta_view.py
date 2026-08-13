"""Delta view: everything changed, superseded, or invalidated since a
given release or date (Feature 0006-24).

Per the task text, this is implemented as a QUERY over the stored cascade
results already produced by 0006-18 (dependency_graph), 0006-19
(confidence), and 0006-20 (supersession_trigger) -- it adds no new cascade
mechanism and no new storage. It aggregates across an arbitrary time/
release window, distinct from 0006-20's per-trigger report (which reports
the immediate blast radius of ONE trigger event).

Baseline resolution: "since release R" is resolved to "since the timestamp
that release tag was first recorded anywhere in the version store" --
documented, not hidden, because invalidation/revisit timestamps are
wall-clock ISO 8601, not release-tagged, so a release baseline must be
converted to a timestamp to be comparable against those two stores. "Since
date D" needs no such conversion.

Schema alignment with 0006-20 (explicit task requirement): field names below
deliberately echo supersession_trigger.summarize_reports()'s output shape
(changed_requirements, revisit_tasks_enqueued) rather than inventing a
second, incompatible "what changed" format.
"""
from __future__ import annotations
import sys
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import version_store as vs  # noqa: E402
import confidence as conf  # noqa: E402


def _all_version_entries() -> list[dict]:
    """Every version entry across the whole corpus (all canonical ids),
    read directly from the JSONL tree rather than duplicating
    version_store's own path-resolution logic per canonical id (we don't
    know all canonical ids up front -- we discover them by walking the
    store)."""
    if not vs.VERSIONS_ROOT.is_dir():
        return []
    out = []
    for f in vs.VERSIONS_ROOT.rglob("*.jsonl"):
        out.extend(vs._read_jsonl(f) if hasattr(vs, "_read_jsonl") else
                   [__import__("json").loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()])
    return out


def resolve_baseline_timestamp(release: str = None, date: str = None) -> str | None:
    """Exactly one of release/date must be given. For a release, returns
    the earliest recorded_at timestamp of any version tagged with that
    release anywhere in the corpus (None if that release was never
    recorded). For a date, returns the date unchanged (already a
    timestamp/date string, ISO-sortable)."""
    if (release is None) == (date is None):
        raise ValueError("exactly one of release or date must be given")
    if date is not None:
        return date
    matches = [v["recorded_at"] for v in _all_version_entries() if v["release"] == release]
    return min(matches) if matches else None


def delta_view(release: str = None, date: str = None) -> dict:
    """Everything changed/superseded/invalidated since the resolved
    baseline. Returns None-baseline safely (empty delta) if the release
    was never recorded, rather than raising -- an unknown baseline release
    is a valid (if unusual) query, not a caller error."""
    baseline_ts = resolve_baseline_timestamp(release=release, date=date)
    if baseline_ts is None:
        return {
            "baseline": {"release": release, "date": date, "resolved_timestamp": None},
            "changed_requirements": [], "invalidated_nodes": [], "revisit_tasks_enqueued": 0,
            "revisit_tasks": [],
        }

    changed_requirements = sorted({
        v["canonical_id"] for v in _all_version_entries() if v["recorded_at"] > baseline_ts
    })

    invalidated_nodes = [
        e for e in conf._read_jsonl(conf.INVALIDATED_FILE) if e["invalidated_at"] > baseline_ts
    ]

    revisit_tasks = [
        e for e in conf._read_jsonl(conf.REVISITS_FILE) if e["enqueued_at"] > baseline_ts
    ]

    return {
        "baseline": {"release": release, "date": date, "resolved_timestamp": baseline_ts},
        "changed_requirements": changed_requirements,
        "invalidated_nodes": invalidated_nodes,
        "revisit_tasks_enqueued": len(revisit_tasks),
        "revisit_tasks": revisit_tasks,
    }
