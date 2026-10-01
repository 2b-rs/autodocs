"""Point-in-time ("as of release R" / "as of date D") view (Feature 0006-23).

Explicitly a READ-SIDE query problem, per the task text: because nothing in
0006-16 through 0006-19 is ever deleted, reconstructing "what was true as of
R/D" never needs redundant snapshot storage -- it only needs to query the
existing append-only stores correctly. This module adds ZERO new storage.

Query contract: given a release tag OR a date, resolved to the latest
version/decision/artifact at or before that point, return:
  - the requirement-version active at that point
  - the curation decision(s) whose decided_on_version matches or precedes it
  - the evidence/artifact graph nodes valid as of that point
... WITHOUT filtering out superseded/invalidated items: "superseded now"
must not mean "absent from a past view" (explicit task requirement).

Release-ordering assumption (documented, not hidden): release tags recorded
by version_store follow the project's fixed-width AUTOSAR convention
("R25-11", "R32-11", ...) and therefore sort correctly as plain Python
strings. If a non-fixed-width release tag is ever introduced, this ordering
breaks and would need a dedicated parser -- out of scope here since no such
tag exists in this corpus today.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from canonical_id import parse_canonical_id, resolve_legacy  # noqa: E402
import version_store as vs  # noqa: E402
import curation_item as ci  # noqa: E402
import dependency_graph as dg  # noqa: E402
import confidence as conf  # noqa: E402


def _canonicalize(record_id: str) -> str:
    if parse_canonical_id(record_id) is not None:
        return record_id
    return resolve_legacy(record_id)


def _version_at_or_before_release(canonical_id: str, release: str) -> dict | None:
    """Latest version whose recorded release tag sorts <= the requested
    release (string-ordered, per this module's documented assumption).
    None if no version qualifies (e.g. requested release predates the
    requirement's first recorded version)."""
    candidates = [v for v in vs.list_versions(canonical_id) if v["release"] <= release]
    if not candidates:
        return None
    return max(candidates, key=lambda v: v["release"])


def _version_at_or_before_date(canonical_id: str, date: str) -> dict | None:
    """Latest version whose recorded_at timestamp sorts <= the requested
    ISO date/timestamp. ISO 8601 timestamps sort correctly as strings."""
    candidates = [v for v in vs.list_versions(canonical_id) if v["recorded_at"] <= date]
    if not candidates:
        return None
    return max(candidates, key=lambda v: v["recorded_at"])


def _artifact_graph_snapshot(canonical_id: str) -> dict:
    """Evidence/artifact graph nodes reachable from canonical_id, WITHOUT
    filtering by dismissal or invalidation state -- per the task's explicit
    requirement that a past view must not hide superseded/invalidated
    items. Each dependent is annotated with its current invalidated/
    dismissed flags so the caller can see (not lose) that state."""
    dependents = sorted(dg.find_dependents(canonical_id))
    return {
        dep: {
            "invalidated": conf.is_invalidated(dep),
            "dismissed": dg.is_dismissed(dep),
        }
        for dep in dependents
    }


def _decisions_for_version(canonical_id: str, version_id: str | None) -> list[dict]:
    """Curation decisions whose decided_on_version matches OR precedes the
    given version_id. \"Precedes\" is judged by release-tag ordering (an
    older decision pinned to an earlier version of the same requirement is
    still a decision that applied \"as of\" a later point in time, since it
    was never superseded by a newer decision at or before that point).
    Never filters by outcome (accepted/rejected decisions both count).
    """
    if version_id is None:
        return []
    resolved = ci.resolve_decided_on_version(canonical_id)
    if resolved is None:
        return []
    if resolved == version_id or resolved <= version_id:
        return [{"canonical_id": canonical_id, "decided_on_version": resolved}]
    return []


def as_of_release(canonical_id: str, release: str) -> dict:
    """The full point-in-time view \"as of release R\" for one requirement."""
    cid = _canonicalize(canonical_id)
    version = _version_at_or_before_release(cid, release)
    version_id = version["version_id"] if version else None
    lifecycle = vs.get_requirement_lifecycle(cid)
    is_dropped = release in lifecycle.get("dropped_in", [])
    return {
        "canonical_id": cid,
        "as_of": {"kind": "release", "value": release},
        "version": version,
        "decisions": _decisions_for_version(cid, version_id),
        "artifact_graph": _artifact_graph_snapshot(cid),
        "is_dropped": is_dropped,
        "lifecycle": lifecycle,
    }


def as_of_date(canonical_id: str, date: str) -> dict:
    """The full point-in-time view \"as of date D\" for one requirement."""
    cid = _canonicalize(canonical_id)
    version = _version_at_or_before_date(cid, date)
    version_id = version["version_id"] if version else None
    return {
        "canonical_id": cid,
        "as_of": {"kind": "date", "value": date},
        "version": version,
        "decisions": _decisions_for_version(cid, version_id),
        "artifact_graph": _artifact_graph_snapshot(cid),
    }


def _format_req_lines(text: str) -> list[str]:
    """Break requirement text into readable lines along AUTOSAR section keywords,
    header artifacts, parameter labels, and sentence boundaries.
    """
    if not text:
        return []
    delimiters = [
        r"Definition of callback function",
        r"Definition of",
        r"Upstream requirements:?",
        r"Service [Nn]ame:?",
        r"Syntax:?",
        r"Service ID\s*(?:\[[^\]]+\])?:?",
        r"Sync\s*/\s*Async:?",
        r"Reentrancy:?",
        r"Parameters\s*\((?:in|out|inout)\):?",
        r"Parameters:?",
        r"\(in\)",
        r"\(inout\)",
        r"\(out\)",
        r"Return value:?",
        r"E_OK:?",
        r"E_ OK:?",
        r"E_NOT_OK:?",
        r"E_ NOT_ OK:?",
        r"Description:?",
        r"Available via:?",
        r"Specification of [^\n:]+:",
        r"Specification of [^\n]+",
        r"Document ID \d+ : [^\n]*",
        r"Document ID \d+ :",
        r"AUTOSAR_[A-Z0-9_]+",
    ]
    pattern = r"(\b(?:" + "|".join(delimiters) + r")|(?:\([a-z]+\)))"
    parts = re.split(pattern, text)
    lines = []
    curr = ""
    for p in parts:
        if not p:
            continue
        p_strip = p.strip()
        is_delim = any(re.match(f"^{d}$", p_strip, re.I) for d in delimiters) or p_strip in ("(in)", "(out)", "(inout)")
        if is_delim:
            if curr.strip():
                lines.append(curr.strip())
            curr = p_strip + " "
        else:
            curr += p
    if curr.strip():
        lines.append(curr.strip())

    final_lines = []
    for l in lines:
        l_str = l.strip()
        if not l_str:
            continue
        if len(l_str) > 100:
            sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", l_str)
            for s in sents:
                if s.strip():
                    final_lines.append(s.strip() + "\n")
        else:
            final_lines.append(l_str + "\n")
    return final_lines


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Query coherent point-in-time view as of release R or date D (Feature 0006-23)")
    parser.add_argument("id", help="Canonical ID or legacy record ID (e.g. SWS_CORE_00017)")
    parser.add_argument("--release", "-r", help="Release tag (e.g. R25-11, R20-11)")
    parser.add_argument("--date", "-d", help="ISO 8601 date/timestamp (e.g. 2026-08-13)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--full", action="store_true", help="Print full requirement content without truncation")
    parser.add_argument("--diff-with", dest="diff_with", help="Compare with another release (e.g. R20-11) as a unified diff")
    args = parser.parse_args()

    cid = _canonicalize(args.id)

    if args.date:
        res = as_of_date(cid, args.date)
    elif args.release:
        res = as_of_release(cid, args.release)
    else:
        latest = vs.latest_version(cid)
        rel = latest["release"] if latest else "R25-11"
        res = as_of_release(cid, rel)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        v = res.get("version")
        is_dropped = res.get("is_dropped", False)
        lifecycle = res.get("lifecycle", {})
        print(f"Point-in-Time View for {res['canonical_id']}")
        print(f"As of: {res['as_of']['kind']} {res['as_of']['value']}")
        if is_dropped:
            first_drop = lifecycle.get("first_dropped_release") or res["as_of"]["value"]
            last_act = lifecycle.get("last_active_release") or "frühere Version"
            print(f"Status:     🚫 Entfallen / Wegfall (in {res['as_of']['value']} nicht mehr enthalten; entfällt ab {first_drop}; letzter Stand: {last_act})")
        if v:
            note = " (letzter Stand vor Wegfall)" if is_dropped else ""
            print(f"Version ID: {v.get('version_id')}{note}")
            print(f"Release:    {v.get('release')}")
            print(f"Recorded:   {v.get('recorded_at')}")
            content = v.get('content', '')
            if args.full:
                print("\n--- Content ---")
                for line in _format_req_lines(content):
                    print(line, end="")
                print("---------------\n")
            else:
                content_preview = content
                if len(content_preview) > 120:
                    content_preview = content_preview[:117] + "..."
                print(f"Content:    {content_preview}")
        else:
            print("Version:    None (no active version at this point)")

        if args.diff_with:
            other_res = as_of_release(cid, args.diff_with)
            other_v = other_res.get("version")
            other_dropped = other_res.get("is_dropped", False)
            this_dropped = res.get("is_dropped", False)
            content_a = "" if other_dropped else (other_v.get("content", "") if other_v else "")
            content_b = "" if this_dropped else (v.get("content", "") if v else "")
            text_a = _format_req_lines(content_a)
            text_b = _format_req_lines(content_b)
            label_a = f"{args.diff_with} ({'ENTFALLEN' if other_dropped else (other_v.get('version_id') if other_v else 'none')})"
            label_b = f"{res['as_of']['value']} ({'ENTFALLEN' if this_dropped else (v.get('version_id') if v else 'none')})"
            import difflib
            diff = list(difflib.unified_diff(text_a, text_b, fromfile=label_a, tofile=label_b))
            print(f"\n--- Unified Diff vs {args.diff_with} ---")
            if diff:
                for line in diff:
                    print(line, end="" if line.endswith("\n") else "\n")
            else:
                print("(Identical content)")
            print("----------------------------------------\n")

        print(f"Decisions ({len(res.get('decisions', []))}):")
        for d in res.get("decisions", []):
            print(f"  - on {d.get('decided_on_version')}")
        print(f"Reachable artifact graph ({len(res.get('artifact_graph', {}))}):")
        for node, flags in res.get("artifact_graph", {}).items():
            inv = " [invalidated]" if flags.get("invalidated") else ""
            dis = " [dismissed]" if flags.get("dismissed") else ""
            print(f"  - {node}{inv}{dis}")


if __name__ == "__main__":
    main()

