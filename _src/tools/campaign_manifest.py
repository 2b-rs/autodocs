"""Campaign manifests (Feature 0006-08, adapted by Task 0037-26.02).

``campaign-manifest@v1`` files under ``_src/spec/campaigns/`` remain the
on-disk schema name. Evidence identity is a sorted content artifact set
(path, content digest, size). The listing/mtime ``corpus_hash`` is retained
only as a staleness hint and is never used as identity.

Existing on-disk manifests that lack a content artifact set are **legacy**.
They are adapted in memory with an explicit legacy disposition and are never
rewritten. New snapshots are exclusive-create, content-addressed files.
"""
from __future__ import annotations
import hashlib
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

SCHEMA = "campaign-manifest@v1"
LEGACY_ADAPTER = "campaign-manifest-legacy@v1"
LEGACY_DISPOSITION = {
    "kind": "legacy",
    "adapter": LEGACY_ADAPTER,
    "reason": (
        "pre-content-artifact campaign-manifest@v1; corpus_hash is a "
        "listing/mtime staleness hint, not evidence identity"
    ),
}
CURRENT_DISPOSITION = {
    "kind": "current",
    "adapter": "campaign-manifest-content@v1",
}
STALENESS_HINT = "staleness-hint"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _canonical_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


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
    """Staleness hint: hash8 of a deterministic (relative path, mtime) listing.

    Not evidence identity. Identity is ``content_set_digest`` of
    ``content_artifact_members``. A listing hash still answers whether the
    record *set or mtimes* moved since a snapshot was written.
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


def content_artifact_members(records_dir: Path = None) -> list:
    """Sorted content artifact set: path, content digest, size. No mtimes."""
    if records_dir is None:
        records_dir = RECORDS_DIR
    if not records_dir.is_dir():
        return []
    members = []
    for root, _dirs, files in os.walk(records_dir):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            full = Path(root) / fn
            rel = str(full.relative_to(records_dir)).replace("\\", "/")
            raw = full.read_bytes()
            members.append(
                {
                    "path": rel,
                    "digest": _sha256_bytes(raw),
                    "size_bytes": len(raw),
                }
            )
    members.sort(key=lambda item: item["path"])
    return members


def content_set_digest(members: list | None = None, records_dir: Path = None) -> str:
    """Evidence identity: SHA-256 of the canonical sorted content artifact set."""
    if members is None:
        members = content_artifact_members(records_dir)
    body = [
        {"path": m["path"], "digest": m["digest"], "size_bytes": m["size_bytes"]}
        for m in members
    ]
    return _sha256_bytes(_canonical_bytes(body))


def is_legacy_manifest(manifest: dict | None) -> bool:
    if not isinstance(manifest, dict):
        return True
    artifacts = manifest.get("content_artifacts")
    digest = manifest.get("content_set_digest")
    if not isinstance(artifacts, list) or not isinstance(digest, str) or not digest:
        return True
    return False


def adapt_manifest(manifest: dict) -> dict:
    """In-memory adaptation. Never rewrites on-disk bytes.

    Old listing/mtime manifests receive an explicit legacy disposition.
    ``corpus_hash`` is labeled as a staleness hint, not identity.
    """
    adapted = json.loads(json.dumps(manifest))
    adapted["corpus_hash_role"] = STALENESS_HINT
    if is_legacy_manifest(manifest):
        adapted["disposition"] = dict(LEGACY_DISPOSITION)
        adapted.setdefault("content_artifacts", None)
        adapted.setdefault("content_set_digest", None)
    else:
        disposition = adapted.get("disposition")
        if not isinstance(disposition, dict) or disposition.get("kind") != "legacy":
            adapted["disposition"] = dict(CURRENT_DISPOSITION)
    return adapted


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


def snapshot_dir(campaign_id: str) -> Path:
    return CAMPAIGNS_DIR / campaign_id / "snapshots"


def snapshot_path(campaign_id: str, snapshot_digest: str) -> Path:
    hex_part = snapshot_digest.split(":")[-1]
    return snapshot_dir(campaign_id) / (hex_part + ".json")


def _exclusive_write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    data = encoded.encode("utf-8")
    if path.exists():
        existing = path.read_bytes()
        if existing == data:
            return path
        raise FileExistsError(f"immutable snapshot already exists with different bytes: {path}")
    tmp = path.with_name(path.name + ".tmp-" + secrets_token())
    try:
        tmp.write_bytes(data)
        os.link(tmp, path)
    except FileExistsError:
        if path.read_bytes() != data:
            raise
    finally:
        if tmp.exists():
            tmp.unlink()
    return path


def secrets_token() -> str:
    return hashlib.sha256(os.urandom(16)).hexdigest()[:16]


def _snapshot_digest(payload: dict) -> str:
    identity = {key: value for key, value in payload.items() if key != "updated"}
    return _sha256_bytes(_canonical_bytes(identity))


def _iter_on_disk_manifests(campaign_id: str) -> list[tuple[Path, dict]]:
    found: list[tuple[Path, dict]] = []
    listing = manifest_path(campaign_id)
    if listing.is_file():
        found.append((listing, json.loads(listing.read_text(encoding="utf-8"))))
    snap_root = snapshot_dir(campaign_id)
    if snap_root.is_dir():
        for path in sorted(snap_root.glob("*.json")):
            found.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return found


def list_snapshots(campaign_id: str) -> list[dict]:
    """Queryable adapted snapshots for a campaign, oldest-created first."""
    rows = []
    for path, raw in _iter_on_disk_manifests(campaign_id):
        adapted = adapt_manifest(raw)
        adapted["_path"] = str(path)
        rows.append(adapted)
    rows.sort(
        key=lambda item: (
            item.get("snapshot_seq") if isinstance(item.get("snapshot_seq"), int) else 0,
            item.get("created") or "",
            item.get("_path") or "",
        )
    )
    return rows


def query_snapshots(campaign_id: str, content_set_digest_value: str | None = None) -> list[dict]:
    rows = list_snapshots(campaign_id)
    if content_set_digest_value is None:
        return rows
    return [
        row
        for row in rows
        if row.get("content_set_digest") == content_set_digest_value
        and row.get("disposition", {}).get("kind") != "legacy"
    ]


def _snapshot_seq(raw: dict, path: Path) -> int:
    seq = raw.get("snapshot_seq")
    if isinstance(seq, int):
        return seq
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


def _latest_raw(campaign_id: str) -> tuple[Path | None, dict]:
    found = _iter_on_disk_manifests(campaign_id)
    if not found:
        return None, {}
    non_legacy = [(path, raw) for path, raw in found if not is_legacy_manifest(raw)]
    pool = non_legacy or found
    pool.sort(key=lambda item: (_snapshot_seq(item[1], item[0]), str(item[0])))
    return pool[-1]


def write_manifest(
    campaign_id: str,
    trigger: str = None,
    release: str = None,
    scope: str = None,
    backends: list = None,
    overwrite: bool = False,
    trigger_issue: str = None,
    trigger_criterion: str = None,
    runs: list = None,
    source_commit: str = None,
    config_commit: str = None,
) -> Path:
    """Create an immutable campaign snapshot.

    Never rewrites an existing file. If ``overwrite`` is false and any
    snapshot (including a legacy listing) already exists, return that path.
    A later write with different content identity creates a new snapshot
    file; mtime-only corpus changes do not change ``content_set_digest``.
    """
    CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
    existing_path, existing = _latest_raw(campaign_id)
    if existing and not overwrite:
        return existing_path

    members = content_artifact_members()
    identity = content_set_digest(members)
    listing_hint = corpus_hash()
    prev_seq = existing.get("snapshot_seq") if existing and not is_legacy_manifest(existing) else 0
    if not isinstance(prev_seq, int):
        prev_seq = 0
    manifest = {
        "schema": SCHEMA,
        "campaign": campaign_id,
        "trigger": trigger if trigger is not None else existing.get("trigger"),
        "trigger_issue": trigger_issue if trigger_issue is not None else existing.get("trigger_issue"),
        "trigger_criterion": trigger_criterion
        if trigger_criterion is not None
        else existing.get("trigger_criterion"),
        "release": release if release is not None else existing.get("release"),
        "scope": scope if scope is not None else existing.get("scope"),
        "created": _now(),
        "updated": _now(),
        "source_commit": source_commit if source_commit is not None else _git_file_version("_src/spec/records"),
        "tool_git_commit": _git_file_version("_src/tools/spec_scrape.py"),
        "config_commit": config_commit
        if config_commit is not None
        else _git_file_version("_src/tools/campaign_manifest.py"),
        "backends": backends if backends is not None else existing.get("backends") or [],
        "runs": runs if runs is not None else existing.get("runs") or [],
        "content_artifacts": members,
        "content_set_digest": identity,
        "corpus_hash": listing_hint,
        "corpus_hash_role": STALENESS_HINT,
        "queue_snapshot": _queue_snapshot(),
        "curator_decisions": list(existing.get("curator_decisions") or [])
        if existing and not is_legacy_manifest(existing)
        else [],
        "published_reports": list(existing.get("published_reports") or [])
        if existing and not is_legacy_manifest(existing)
        else [],
        "disposition": dict(CURRENT_DISPOSITION),
        "snapshot_seq": prev_seq + 1,
    }
    digest = _snapshot_digest(manifest)
    manifest["snapshot_digest"] = digest
    path = snapshot_path(campaign_id, digest)
    written = _exclusive_write_json(path, manifest)
    listing = manifest_path(campaign_id)
    if not listing.exists():
        try:
            _exclusive_write_json(listing, manifest)
        except FileExistsError:
            pass
    return written


def append_decision(campaign_id: str, decision_ref: str) -> None:
    """Append a decision ref by writing a new immutable snapshot.

    No-op create if nothing exists yet. Never mutates an existing file.
    """
    path = manifest_path(campaign_id)
    found = _iter_on_disk_manifests(campaign_id)
    if not found:
        write_manifest(campaign_id)
    _latest_path, latest = _latest_raw(campaign_id)
    if is_legacy_manifest(latest):
        write_manifest(campaign_id, overwrite=True)
        _latest_path, latest = _latest_raw(campaign_id)
    if decision_ref in (latest.get("curator_decisions") or []):
        return
    latest = dict(latest)
    latest["curator_decisions"] = list(latest.get("curator_decisions") or []) + [decision_ref]
    latest["updated"] = _now()
    seq = latest.get("snapshot_seq")
    latest["snapshot_seq"] = (seq + 1) if isinstance(seq, int) else 1
    latest.pop("snapshot_digest", None)
    digest = _snapshot_digest(latest)
    latest["snapshot_digest"] = digest
    _exclusive_write_json(snapshot_path(campaign_id, digest), latest)
    if not path.exists():
        return


def append_report(campaign_id: str, report_ref: str) -> None:
    """Append a published-report ref by writing a new immutable snapshot."""
    found = _iter_on_disk_manifests(campaign_id)
    if not found:
        write_manifest(campaign_id)
    _latest_path, latest = _latest_raw(campaign_id)
    if is_legacy_manifest(latest):
        write_manifest(campaign_id, overwrite=True)
        _latest_path, latest = _latest_raw(campaign_id)
    if report_ref in (latest.get("published_reports") or []):
        return
    latest = dict(latest)
    latest["published_reports"] = list(latest.get("published_reports") or []) + [report_ref]
    latest["updated"] = _now()
    seq = latest.get("snapshot_seq")
    latest["snapshot_seq"] = (seq + 1) if isinstance(seq, int) else 1
    latest.pop("snapshot_digest", None)
    digest = _snapshot_digest(latest)
    latest["snapshot_digest"] = digest
    _exclusive_write_json(snapshot_path(campaign_id, digest), latest)


def read_manifest(campaign_id: str) -> dict | None:
    snapshots = list_snapshots(campaign_id)
    if not snapshots:
        return None
    current = [
        row for row in snapshots if row.get("disposition", {}).get("kind") != "legacy"
    ]
    chosen = (current or snapshots)[-1]
    chosen = dict(chosen)
    chosen.pop("_path", None)
    return chosen
