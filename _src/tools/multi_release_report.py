"""Multi-release requirement delta report between two AUTOSAR releases.

Compares immutable version-store snapshots tagged with a source and target
release, classifying each canonical requirement as added, modified, unchanged,
or deprecated_or_removed (present only in the source release).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import version_store as vs  # noqa: E402
from version_id import content_hash8  # noqa: E402


def _iter_version_entries(versions_root: Path | None = None):
    root = versions_root if versions_root is not None else vs.VERSIONS_ROOT
    if not root.is_dir():
        return
    for path in root.rglob("*.jsonl"):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)


def _matches_platform(canonical_id: str, platform: str | None) -> bool:
    if platform is None:
        return True
    parts = canonical_id.split("/")
    if len(parts) < 2:
        return False
    return parts[0] == "AUTOSAR" and parts[1] == platform


def _release_snapshot(
    release: str,
    platform: str | None = None,
    versions_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Map canonical_id -> latest entry metadata for one release tag."""
    needle = f'"release": "{release}"'
    root = versions_root if versions_root is not None else vs.VERSIONS_ROOT
    snapshot: dict[str, dict[str, Any]] = {}
    if not root.is_dir():
        return snapshot
    for path in root.rglob("*.jsonl"):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if needle not in line:
                    continue
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if entry.get("release") != release:
                    continue
                canonical_id = entry["canonical_id"]
                if not _matches_platform(canonical_id, platform):
                    continue
                content = entry.get("content", "")
                snapshot[canonical_id] = {
                    "canonical_id": canonical_id,
                    "version_id": entry["version_id"],
                    "content_hash": content_hash8(content),
                }
    return snapshot


def generate_release_report(
    from_release: str,
    to_release: str,
    platform: str | None = None,
    versions_root: Path | None = None,
) -> dict[str, Any]:
    """Compare requirement snapshots between two release tags."""
    from_map = _release_snapshot(from_release, platform, versions_root)
    to_map = _release_snapshot(to_release, platform, versions_root)

    added: list[dict[str, Any]] = []
    modified: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []
    deprecated_or_removed: list[dict[str, Any]] = []

    all_ids = sorted(set(from_map) | set(to_map))
    for canonical_id in all_ids:
        src = from_map.get(canonical_id)
        dst = to_map.get(canonical_id)
        if src is None and dst is not None:
            added.append(
                {
                    "canonical_id": canonical_id,
                    "to_version_id": dst["version_id"],
                    "content_hash": dst["content_hash"],
                }
            )
        elif src is not None and dst is None:
            deprecated_or_removed.append(
                {
                    "canonical_id": canonical_id,
                    "from_version_id": src["version_id"],
                    "content_hash": src["content_hash"],
                }
            )
        elif src is not None and dst is not None:
            if src["content_hash"] == dst["content_hash"]:
                unchanged.append(
                    {
                        "canonical_id": canonical_id,
                        "content_hash": src["content_hash"],
                        "from_version_id": src["version_id"],
                        "to_version_id": dst["version_id"],
                    }
                )
            else:
                modified.append(
                    {
                        "canonical_id": canonical_id,
                        "from_version_id": src["version_id"],
                        "to_version_id": dst["version_id"],
                        "from_content_hash": src["content_hash"],
                        "to_content_hash": dst["content_hash"],
                    }
                )

    return {
        "from_release": from_release,
        "to_release": to_release,
        "platform": platform,
        "summary": {
            "from_count": len(from_map),
            "to_count": len(to_map),
            "added": len(added),
            "modified": len(modified),
            "unchanged": len(unchanged),
            "deprecated_or_removed": len(deprecated_or_removed),
        },
        "added": added,
        "modified": modified,
        "unchanged": unchanged,
        "deprecated_or_removed": deprecated_or_removed,
    }


def format_text_report(report: dict[str, Any]) -> str:
    """Human-readable summary for CLI output."""
    plat = report.get("platform") or "all"
    summary = report["summary"]
    lines = [
        "Multi-Release Requirement Delta Report",
        f"  From: {report['from_release']}  To: {report['to_release']}  Platform: {plat}",
        "",
        "Counts:",
        f"  Requirements in source release: {summary['from_count']}",
        f"  Requirements in target release: {summary['to_count']}",
        f"  Added: {summary['added']}",
        f"  Modified: {summary['modified']}",
        f"  Unchanged (identical hash): {summary['unchanged']}",
        f"  Deprecated or removed: {summary['deprecated_or_removed']}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report requirement deltas between two AUTOSAR releases",
    )
    parser.add_argument("--from", dest="from_release", required=True, help="Source release tag")
    parser.add_argument("--to", dest="to_release", required=True, help="Target release tag")
    parser.add_argument(
        "--platform",
        choices=("AP", "CP"),
        default=None,
        help="Limit to Adaptive (AP) or Classic (CP) platform",
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    args = parser.parse_args(argv)

    report = generate_release_report(args.from_release, args.to_release, args.platform)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
