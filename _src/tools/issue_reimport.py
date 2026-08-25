#!/usr/bin/env python3
"""Source-watermark tracking and fresh full re-import (Task 0037-15.01).

Wraps ``issue_import_legacy`` as a library. Every run creates a disposable
root, records ``migration-state@v1`` watermarks, writes provenance run and
source artifact-set records via ``ProvenanceStore``, and promotes only after
validation. Interrupted or stale candidates are discarded rather than resumed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

TOOL_REL = "_src/tools/issue_reimport.py"
IMPORTER_REL = "_src/tools/issue_import_legacy.py"
MIGRATION_SCHEMA = "migration-state@v1"
CANDIDATE_SCHEMA = "issue-item@v1"
RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{7,63}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
FEATURE_0037 = "0037"

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


IMP = _load("issue_import_legacy", ROOT / IMPORTER_REL)
PS = _load("provenance_store", ROOT / "_src/tools/provenance_store.py")


class ReimportError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def uuid7() -> str:
    if hasattr(uuid, "uuid7"):
        return str(uuid.uuid7())
    # RFC-9562-shaped fallback: version nibble 7, variant 10xx.
    ts_ms = int(time.time() * 1000)
    rand = os.urandom(10)
    b = bytearray(16)
    b[0] = (ts_ms >> 40) & 0xFF
    b[1] = (ts_ms >> 32) & 0xFF
    b[2] = (ts_ms >> 24) & 0xFF
    b[3] = (ts_ms >> 16) & 0xFF
    b[4] = (ts_ms >> 8) & 0xFF
    b[5] = ts_ms & 0xFF
    b[6] = 0x70 | (rand[0] & 0x0F)
    b[7] = rand[1]
    b[8] = 0x80 | (rand[2] & 0x3F)
    b[9:] = rand[3:]
    hx = bytes(b).hex()
    return f"{hx[0:8]}-{hx[8:12]}-{hx[12:16]}-{hx[16:20]}-{hx[20:32]}"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def git_commit_hex(repo: Path, rev: str = "HEAD") -> str:
    out = _git(repo, "rev-parse", rev).stdout.strip()
    if not COMMIT_RE.fullmatch(out):
        raise ReimportError("REI-COMMIT", f"not a 40-hex commit: {out}")
    return out


def git_tree_hex(repo: Path, commit: str) -> str:
    out = _git(repo, "rev-parse", f"{commit}^{{tree}}").stdout.strip()
    if not COMMIT_RE.fullmatch(out):
        raise ReimportError("REI-TREE", f"not a 40-hex tree: {out}")
    return out


def legacy_source_dirty(repo: Path) -> List[str]:
    """Return porcelain entries for backlog source paths (TODO/DONE/claims)."""
    proc = _git(repo, "status", "--porcelain", "-uall", "--", "TODO.md", "DONE.md", "TODO-*.md", check=False)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    extra = _git(
        repo,
        "ls-files",
        "--others",
        "--exclude-standard",
        "--",
        "TODO.md",
        "DONE.md",
        ".",
        check=False,
    )
    for ln in extra.stdout.splitlines():
        name = ln.strip()
        if name.startswith("TODO-") and name.endswith(".md"):
            entry = f"?? {name}"
            if entry not in lines and name not in " ".join(lines):
                lines.append(entry)
    return lines


def make_run_id() -> str:
    raw = f"shadow-{int(time.time())}-{os.urandom(3).hex()}"
    return raw[:64]


def parse_frontmatter_prereqs(text: str) -> List[str]:
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    if end < 0:
        return []
    block = text[3:end]
    prereqs: List[str] = []
    in_list = False
    for line in block.splitlines():
        if line.startswith("prerequisites:"):
            rest = line.split(":", 1)[1].strip()
            in_list = rest in ("", "[]")
            if rest == "[]":
                return []
            continue
        if in_list:
            stripped = line.strip()
            if stripped.startswith("- "):
                val = stripped[2:].strip().strip('"')
                if val:
                    prereqs.append(val)
            elif stripped and not line.startswith(" ") and not line.startswith("\t"):
                break
    return prereqs


def item_index_from_root(root: Path, items: Sequence[Mapping[str, Any]]) -> Dict[str, dict]:
    index: Dict[str, dict] = {}
    for item in items:
        item_id = item["id"]
        rel = item["path"]
        prereqs: List[str] = []
        path = root / rel
        if path.is_file():
            prereqs = parse_frontmatter_prereqs(path.read_text(encoding="utf-8"))
        index[item_id] = {
            "id": item_id,
            "path": rel,
            "state": item.get("state"),
            "locator": item.get("locator"),
            "prerequisites": prereqs,
        }
    return index


def detect_deltas(
    previous: Optional[Mapping[str, dict]],
    current: Mapping[str, dict],
    *,
    require_feature_0037: bool = True,
) -> List[dict]:
    findings: List[dict] = []
    current_ids = set(current)
    prev_ids = set(previous or {})

    if require_feature_0037 and FEATURE_0037 not in current_ids:
        findings.append(
            {
                "code": "missing-feature-0037",
                "severity": "blocking",
                "message": "latest source does not represent Feature 0037",
            }
        )

    if previous is None:
        return findings

    deleted = sorted(prev_ids - current_ids)
    for item_id in deleted:
        findings.append(
            {
                "code": "deleted-id",
                "severity": "blocking",
                "message": f"ID {item_id} present at prior watermark is absent from latest source",
            }
        )

    for item_id in sorted(current_ids & prev_ids):
        old = previous[item_id]
        new = current[item_id]
        if old.get("path") != new.get("path"):
            findings.append(
                {
                    "code": "task-moved",
                    "severity": "blocking",
                    "message": f"ID {item_id} moved {old.get('path')} -> {new.get('path')}",
                }
            )
        old_pr = list(old.get("prerequisites") or [])
        new_pr = list(new.get("prerequisites") or [])
        if old_pr != new_pr:
            findings.append(
                {
                    "code": "prerequisites-changed",
                    "severity": "blocking",
                    "message": f"ID {item_id} prerequisites changed",
                }
            )
        # Reuse: same ID, different source locator after an intervening delete
        # is covered by deleted-id plus reappearance below.

    reappeared = sorted(current_ids & getattr(previous, "_deleted_ids", set()))
    for item_id in reappeared:
        findings.append(
            {
                "code": "reused-id",
                "severity": "blocking",
                "message": f"ID {item_id} was deleted at an earlier watermark and reused",
            }
        )
    return findings


def write_git_tree(files: Mapping[str, bytes]) -> str:
    """Create an isolated Git tree object for the candidate file set."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _git(repo, "init")
        env_git = {"GIT_DIR": str(repo / ".git")}
        for rel, payload in sorted(files.items()):
            dest = repo / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(payload)
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
        tree = subprocess.check_output(["git", "write-tree"], cwd=repo).decode().strip()
        if not COMMIT_RE.fullmatch(tree):
            raise ReimportError("REI-TREE", f"write-tree produced {tree}")
        return tree


def atomic_promote(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = dest.parent / (dest.name + ".promoting")
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(src, staging)
    if dest.exists():
        bak = dest.parent / (dest.name + ".prev")
        if bak.exists():
            shutil.rmtree(bak)
        dest.rename(bak)
        staging.rename(dest)
        shutil.rmtree(bak, ignore_errors=True)
    else:
        staging.rename(dest)


def load_state(path: Path) -> Optional[dict]:
    if path is None or not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def dump_state(path: Path, state: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(_canonical_json(state), encoding="utf-8")
    os.replace(tmp, path)


def collect_candidate_files(issues_root: Path) -> Dict[str, bytes]:
    files: Dict[str, bytes] = {}
    for path in sorted(issues_root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(issues_root).as_posix()
            files[rel] = path.read_bytes()
    return files


def _ref(kind: str, ident: str, **extra: Any) -> dict:
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}",
        "classification": "internal",
    }
    value.update(extra)
    return value


def record_provenance(
    *,
    store_root: Path,
    source_commit: str,
    importer_commit: str,
    importer_digest: str,
    started_at: str,
    ended_at: str,
    status: str,
    member_files: Mapping[str, bytes],
    source_commit_for_members: str,
) -> Tuple[str, str]:
    file_map = dict(member_files)
    store = PS.ProvenanceStore(store_root, file_bytes=file_map.__getitem__)
    run_id = uuid7()
    set_id = uuid7()
    members = []
    for path, raw in sorted(member_files.items()):
        members.append(
            {
                "path": path.replace("\\", "/"),
                "digest": PS.sha256_bytes(raw),
                "size_bytes": len(raw),
                "media_type": "text/plain" if path.endswith(".md") else "application/json",
                "source_commit": source_commit_for_members,
            }
        )
    run_payload = {
        "schema_version": "1.0",
        "run_id": run_id,
        "started_at": started_at,
        "ended_at": ended_at,
        "environment": "synthetic",
        "classification": "internal",
        "status": status,
        "producer": _ref("commit", importer_commit, digest=f"sha256:{importer_digest}"),
        "inputs": [
            _ref("commit", source_commit),
            _ref("issue", "0037-15.01"),
            _ref("criterion", "AC-001"),
            _ref("campaign", "0037-C-migration"),
        ],
        "outputs": [_ref("artifact-set", set_id)],
    }
    if status == "running":
        run_payload.pop("ended_at")
        run_payload.pop("outputs")
    store.create_run(run_payload)
    if members and status != "running":
        store.create_artifact_set(
            {
                "schema_version": "1.0",
                "set_id": set_id,
                "created_at": ended_at,
                "classification": "internal",
                "environment": "synthetic",
                "producer": _ref("run", run_id),
                "members": members,
            }
        )
    return run_id, set_id


def reimport(
    *,
    repo: Path,
    output_parent: Path,
    source_commit: Optional[str] = None,
    baseline: Optional[str] = None,
    previous_state_path: Optional[Path] = None,
    require_clean: bool = False,
    promote_to: Optional[Path] = None,
    provenance_root: Optional[Path] = None,
    run_id: Optional[str] = None,
    seen_deleted_ids: Optional[Sequence[str]] = None,
) -> dict:
    repo = repo.resolve()
    source_commit = source_commit or git_commit_hex(repo)
    importer_commit = git_commit_hex(repo)
    importer_bytes = (repo / IMPORTER_REL).read_bytes() if (repo / IMPORTER_REL).is_file() else (ROOT / IMPORTER_REL).read_bytes()
    importer_digest = _sha256_hex(importer_bytes)
    tree = git_tree_hex(repo, source_commit)
    tree_digest = _sha256_hex(_git(repo, "rev-parse", f"{source_commit}^{{tree}}").stdout.encode())

    previous = load_state(previous_state_path) if previous_state_path else None

    findings: List[dict] = []
    dirty = legacy_source_dirty(repo)
    if require_clean and dirty:
        findings.append(
            {
                "code": "dirty-legacy-source",
                "severity": "blocking",
                "message": "dirty or staged backlog source blocks a final source watermark: "
                + "; ".join(dirty),
            }
        )

    if previous and previous.get("status") == "interrupted":
        old_root = previous.get("candidate", {}).get("root")
        if old_root:
            leftover = output_parent / Path(old_root).name if not Path(old_root).is_absolute() else Path(old_root)
            if leftover.exists():
                shutil.rmtree(leftover, ignore_errors=True)
        findings.append(
            {
                "code": "interrupted-run-discarded",
                "severity": "warning",
                "message": f"discarded interrupted run {previous.get('run_id')}; starting a fresh root",
            }
        )

    if previous and previous.get("watermarks", {}).get("candidate") not in (None, source_commit):
        if previous.get("status") in {"validated", "promoted", "imported"}:
            findings.append(
                {
                    "code": "stale-candidate",
                    "severity": "blocking",
                    "message": "latest source differs from candidate watermark; prior candidate rejected",
                }
            )

    run_id = run_id or make_run_id()
    if not RUN_ID_RE.fullmatch(run_id):
        raise ReimportError("REI-RUN-ID", f"invalid run_id {run_id}")

    run_root = output_parent / run_id
    if run_root.exists():
        shutil.rmtree(run_root)
    issues_root = run_root / "issues"
    reports_root = run_root / "reports"
    issues_root.mkdir(parents=True)
    reports_root.mkdir(parents=True)

    rel_root = f"_src/output/issue-migration/{run_id}/"
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    state = {
        "schema": MIGRATION_SCHEMA,
        "run_id": run_id,
        "source": {
            "commit": source_commit,
            "tree": tree,
            "tree_digest": tree_digest,
            "files": ["TODO.md", "DONE.md", "claim-blobs"],
            "working_tree_clean": not bool(dirty),
        },
        "importer": {
            "commit": importer_commit,
            "digest": importer_digest,
            "schema_versions": {
                "issue-item": "1.0",
                "migration-state": "1",
                "candidate-schema": CANDIDATE_SCHEMA,
            },
        },
        "watermarks": {
            "baseline": baseline or (previous.get("watermarks", {}).get("baseline") if previous else source_commit),
            "latest_source": source_commit,
            "candidate": source_commit,
        },
        "candidate": {
            "root": rel_root,
            "issues_root": rel_root + "issues/",
            "reports_root": rel_root + "reports/",
            "tree": "0" * 40,
            "tree_digest": "0" * 64,
            "promotable": False,
        },
        "status": "created",
        "findings": findings,
    }
    dump_state(run_root / "migration-state.json", state)

    if require_clean and any(f["code"] == "dirty-legacy-source" for f in findings):
        state["status"] = "rejected"
        dump_state(run_root / "migration-state.json", state)
        return {**state, "run_root": str(run_root), "items": []}

    import_dest = run_root
    try:
        manifest = IMP.import_legacy(
            repo=repo,
            root=import_dest,
            source_commit=source_commit,
        )
    except Exception as exc:
        state["status"] = "interrupted"
        state["findings"] = findings + [
            {"code": "import-interrupted", "severity": "blocking", "message": str(exc)}
        ]
        dump_state(run_root / "migration-state.json", state)
        return {**state, "run_root": str(run_root), "items": []}

    current_index = item_index_from_root(run_root, manifest.get("items") or [])
    previous_index = None
    if previous and previous.get("items"):
        previous_index = {i["id"]: i for i in previous["items"]}
        class _Idx(dict):
            pass

        wrapped = _Idx(previous_index)
        wrapped._deleted_ids = set(seen_deleted_ids or [])  # type: ignore[attr-defined]
        previous_index = wrapped

    delta_findings = detect_deltas(previous_index, current_index)
    findings.extend(delta_findings)
    if seen_deleted_ids:
        for item_id in current_index:
            if item_id in set(seen_deleted_ids):
                findings.append(
                    {
                        "code": "reused-id",
                        "severity": "blocking",
                        "message": f"ID {item_id} was deleted at an earlier watermark and reused",
                    }
                )

    files = collect_candidate_files(issues_root)
    cand_tree = write_git_tree(files) if files else "0" * 40
    cand_digest = manifest.get("tree_digest") or _sha256_hex(b"".join(files[k] for k in sorted(files)))
    blocking = [f for f in findings if f.get("severity") == "blocking"] or []
    if manifest.get("blocking"):
        blocking.append(
            {
                "code": "importer-blocking",
                "severity": "blocking",
                "message": "issue_import_legacy reported blocking findings",
            }
        )
    promotable = not blocking and bool(files) and (not require_clean or not dirty)
    status = "validated" if promotable else "rejected"
    if not promotable and any(f.get("code") == "stale-candidate" for f in findings):
        status = "rejected"

    ended = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    pv_root = provenance_root or (run_root / "provenance-host")
    source_members = {}
    for name in ("TODO.md", "DONE.md"):
        blob = _git(repo, "show", f"{source_commit}:{name}", check=False)
        if blob.returncode == 0:
            source_members[name] = blob.stdout.encode("utf-8")
    pv_status = "succeeded" if promotable else "failed"
    run_uuid, set_id = record_provenance(
        store_root=pv_root,
        source_commit=source_commit,
        importer_commit=importer_commit,
        importer_digest=importer_digest,
        started_at=started,
        ended_at=ended,
        status=pv_status,
        member_files=source_members or {"TODO.md": b"# empty\n"},
        source_commit_for_members=source_commit,
    )

    items_out = [current_index[k] for k in sorted(current_index)]
    state.update(
        {
            "status": status,
            "findings": findings,
            "candidate": {
                "root": rel_root,
                "issues_root": rel_root + "issues/",
                "reports_root": rel_root + "reports/",
                "tree": cand_tree,
                "tree_digest": cand_digest,
                "promotable": promotable,
            },
            "provenance_run_id": run_uuid,
            "source_artifact_set_id": set_id,
            "items": items_out,
            "import_tree_digest": manifest.get("tree_digest"),
        }
    )
    dump_state(run_root / "migration-state.json", state)
    dump_state(reports_root / "reimport-report.json", {"run_id": run_id, "findings": findings, "status": status})

    promoted = False
    if promotable and promote_to is not None:
        atomic_promote(issues_root, Path(promote_to))
        state["status"] = "promoted"
        dump_state(run_root / "migration-state.json", state)
        promoted = True

    return {**state, "run_root": str(run_root), "promoted": promoted}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output-parent", required=True, help="directory that receives <run-id>/")
    parser.add_argument("--source-commit")
    parser.add_argument("--baseline")
    parser.add_argument("--previous-state")
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--promote-to")
    parser.add_argument("--provenance-root")
    args = parser.parse_args(argv)
    try:
        result = reimport(
            repo=Path(args.repo),
            output_parent=Path(args.output_parent),
            source_commit=args.source_commit,
            baseline=args.baseline,
            previous_state_path=Path(args.previous_state) if args.previous_state else None,
            require_clean=args.require_clean,
            promote_to=Path(args.promote_to) if args.promote_to else None,
            provenance_root=Path(args.provenance_root) if args.provenance_root else None,
        )
        sys.stdout.write(
            _canonical_json(
                {
                    "run_id": result["run_id"],
                    "status": result["status"],
                    "watermarks": result["watermarks"],
                    "promotable": result["candidate"]["promotable"],
                }
            )
        )
        return 0 if result["status"] in {"validated", "promoted"} else 2
    except (ReimportError, IMP.ImportErrorClosed) as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
