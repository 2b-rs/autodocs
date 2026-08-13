"""Campaign manifests (Feature 0006-08).

docs/pipeline/campaigns.md documents the intended schema in detail
(spec/campaigns/<id>.json: trigger, release, scope, tool version/git commit,
backend list, PDF-cache hash) but no manifest files existed on disk -- this
module materializes writers for exactly that schema plus two small
additions the docs implied but did not name: a queue snapshot (open/
claimed/done counts at manifest-write time) and append-only lists for
curator decisions and published reports referencing this campaign, so a
curator can later answer "which exact state of the corpus and tools
produced this request, and what happened to it since".

Corpus hashing is deliberately a hash of a (path, mtime) LISTING, not of
full file contents: hashing ~3882 records' full content on every manifest
write would be slow and would also flag false changes on whitespace-only
re-writes from unrelated tooling. A listing hash still answers the actual
question ("did the record set change since this campaign ran") which is
what 0006-08's task text asks for.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
from version_id import content_hash8  # noqa: E402

SRC_ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = SRC_ROOT / "spec"
CAMPAIGNS_DIR = SPEC_ROOT / "campaigns"
RECORDS_DIR = SPEC_ROOT / "records"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git_file_version(relpath: str) -> str | None:
    """Git commit hash that last touched relpath, or None if not tracked /
    git unavailable. Same pattern as extraction_report.py's _git_file_version()."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", relpath],
            cwd=str(SRC_ROOT.parent), capture_output=True, text=True, timeout=10,
        )
        rev = out.stdout.strip()
        return rev or None
    except Exception:
        return None


def corpus_hash(records_dir: Path = None) -> str | None:
    """hash8 of a deterministic (relative path, mtime) listing of every
    record file, sorted by path. Returns None if records_dir doesn't exist
    (e.g. this sandbox may not have the full corpus materialized).

    records_dir defaults to None (NOT to the module-level RECORDS_DIR
    directly) so the module global is re-read at CALL time rather than
    captured once at function-definition time -- a plain `= RECORDS_DIR`
    default would silently ignore any later reassignment of
    campaign_manifest.RECORDS_DIR (e.g. by tests, or by any future caller
    that legitimately points this module at a different records tree).
    """
    if records_dir is None:
        records_dir = RECORDS_DIR
    if not records_dir.is_dir():
        return None
    entries = []
    for root, _dirs, files in os.walk(records_dir):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            full = Path(root) / fn
            rel = full.relative_to(records_dir)
            entries.append("%s:%d" % (rel, int(full.stat().st_mtime)))
    entries.sort()
    return content_hash8("\n".join(entries))


def _queue_snapshot() -> dict:
    snap = {}
    for queue_name in ("review-queue", "curation-queue"):
        base = SPEC_ROOT / queue_name
        counts = {}
        for sub in ("open", "claimed", "done"):
            d = base / sub
            counts[sub] = len(list(d.glob("*.json"))) if d.is_dir() else 0
        snap[queue_name] = counts
    return snap


def manifest_path(campaign_id: str) -> Path:
    return CAMPAIGNS_DIR / (campaign_id + ".json")


def write_manifest(campaign_id: str, trigger: str = None, release: str = None,
                    scope: str = None, backends: list = None, overwrite: bool = False) -> Path:
    """Create (or, if overwrite=True, refresh) spec/campaigns/<campaign_id>.json.
    Refreshing preserves any existing curator_decisions/published_reports lists
    (those only ever grow via append_decision()/append_report()) but recomputes
    corpus_hash/queue_snapshot/tool_git_commit to their CURRENT values -- a
    manifest describes the campaign's state at last-write time, not a frozen
    point in the past, unless the caller stops calling write_manifest() again.
    """
    CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
    path = manifest_path(campaign_id)
    existing = {}
    if path.exists():
        if not overwrite:
            return path
        existing = json.loads(path.read_text(encoding="utf-8"))
    manifest = {
        "schema": "campaign-manifest@v1",
        "campaign": campaign_id,
        "trigger": trigger if trigger is not None else existing.get("trigger"),
        "release": release if release is not None else existing.get("release"),
        "scope": scope if scope is not None else existing.get("scope"),
        "created": existing.get("created") or _now(),
        "updated": _now(),
        "tool_git_commit": _git_file_version("_src/tools/spec_scrape.py"),
        "backends": backends if backends is not None else existing.get("backends") or [],
        "corpus_hash": corpus_hash(),
        "queue_snapshot": _queue_snapshot(),
        "curator_decisions": existing.get("curator_decisions") or [],
        "published_reports": existing.get("published_reports") or [],
    }
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")
    return path


def append_decision(campaign_id: str, decision_ref: str) -> None:
    """Append a reference (e.g. a curation-flag file stem, or a
    curation-item canonical_id) to this campaign's curator_decisions list.
    No-op (creates a bare manifest first) if the manifest doesn't exist yet."""
    path = manifest_path(campaign_id)
    if not path.exists():
        write_manifest(campaign_id)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if decision_ref not in manifest["curator_decisions"]:
        manifest["curator_decisions"].append(decision_ref)
        manifest["updated"] = _now()
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")


def append_report(campaign_id: str, report_ref: str) -> None:
    """Append a reference (e.g. a generated report page's relative path) to
    this campaign's published_reports list."""
    path = manifest_path(campaign_id)
    if not path.exists():
        write_manifest(campaign_id)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if report_ref not in manifest["published_reports"]:
        manifest["published_reports"].append(report_ref)
        manifest["updated"] = _now()
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")


def read_manifest(campaign_id: str) -> dict | None:
    path = manifest_path(campaign_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
