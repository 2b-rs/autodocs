#!/usr/bin/env python3
"""Fail-closed, stdlib-only emergency recovery for the Git-native issue store.

The tool operates only on explicit roots.  It never reads or writes legacy
TODO/DONE authority and never discovers credentials.  Every mutating command
uses generation compare-and-swap and atomic file replacement.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from agent_bootstrap import selector_digest

SCHEMA = "issue-recovery-result@v1"
SETS = ("issues", "provenance", "claims", "artifacts")


class RecoveryError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(f"{code}: {message}")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryError("RECOVERY-INVALID-JSON", f"{path}: {exc}") from exc


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(canonical(value)); handle.flush(); os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def write_selector(path: Path, selector: Dict[str, Any]) -> None:
    selector["selector_digest"] = selector_digest(selector)
    atomic_json(path, selector)


def safe_rel(value: str) -> Path:
    path = Path(value)
    if (not value or not path.parts or path.is_absolute() or ".." in path.parts
            or path.parts[0] not in SETS):
        raise RecoveryError("RECOVERY-UNSAFE-PATH", value)
    return path


def control_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"schema": "issue-recovery-control@v1", "generation": 0,
                "phase": "issue-store-writable", "applied_events": {}}
    value = load(path)
    if value.get("schema") != "issue-recovery-control@v1" or not isinstance(value.get("generation"), int):
        raise RecoveryError("RECOVERY-CONTROL", "invalid control record")
    return value


def require_generation(state: Mapping[str, Any], expected: int) -> None:
    if state["generation"] != expected:
        raise RecoveryError("RECOVERY-STALE-EPOCH", f"expected {expected}, observed {state['generation']}")


def cmd_freeze(args: argparse.Namespace) -> Dict[str, Any]:
    repo, control = Path(args.repo).resolve(), Path(args.control).resolve()
    state = control_state(control); require_generation(state, args.expected_generation)
    selector_path = repo / "agent-workflow.json"; selector = load(selector_path)
    if selector.get("authority_profile") != "issue-store" or selector.get("authority_epoch") != "issue-store-writable":
        raise RecoveryError("RECOVERY-NOT-WRITABLE", "selector is not issue-store-writable")
    generation = state["generation"] + 1
    invalidated = repo / ".issue-recovery" / f"generation-{generation}" / "invalidated"
    moved = []
    for name in ("sessions", "claims"):
        source = repo / name
        if source.exists():
            target = invalidated / name; target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, target); moved.append(name)
    selector.update(authority_epoch="issue-store-write-frozen", write_phase="write-frozen")
    write_selector(selector_path, selector)
    frozen = {"schema": "issue-recovery-control@v1", "generation": generation,
              "phase": "issue-store-write-frozen", "actor": args.actor,
              "invalidated": moved, "applied_events": state.get("applied_events", {})}
    atomic_json(control, frozen)
    return {"status": "FROZEN", "generation": generation, "invalidated": moved}


def iter_files(repo: Path) -> Iterable[tuple[str, Path]]:
    roots = [(name, repo / name) for name in SETS]
    recovery = repo / ".issue-recovery"
    if recovery.exists():
        for claims in sorted(recovery.glob("generation-*/invalidated/claims")):
            roots.append(("claims", claims))
    seen = set()
    for logical, root in roots:
        if not root.exists(): continue
        for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
            rel = f"{logical}/{path.relative_to(root).as_posix()}"
            if rel in seen: raise RecoveryError("RECOVERY-DUPLICATE-PATH", rel)
            seen.add(rel); yield rel, path


def cmd_export(args: argparse.Namespace) -> Dict[str, Any]:
    repo, control = Path(args.repo).resolve(), Path(args.control).resolve()
    state = control_state(control)
    if state["phase"] != "issue-store-write-frozen":
        raise RecoveryError("RECOVERY-NOT-FROZEN", "export requires frozen control")
    entries = []
    for rel, path in iter_files(repo):
        data = path.read_bytes()
        entries.append({"path": rel, "sha256": digest(data), "data": base64.b64encode(data).decode()})
    bundle = {"schema": "issue-recovery-export@v1", "generation": state["generation"], "entries": entries}
    bundle["manifest_sha256"] = digest(canonical(bundle))
    atomic_json(Path(args.bundle).resolve(), bundle)
    return {"status": "EXPORTED", "generation": state["generation"], "files": len(entries),
            "manifest_sha256": bundle["manifest_sha256"]}


def validate_bundle(bundle: Mapping[str, Any]) -> list[tuple[Path, bytes]]:
    if bundle.get("schema") != "issue-recovery-export@v1":
        raise RecoveryError("RECOVERY-BUNDLE-SCHEMA", "unsupported bundle")
    copy = dict(bundle); claimed = copy.pop("manifest_sha256", None)
    if claimed != digest(canonical(copy)):
        raise RecoveryError("RECOVERY-BUNDLE-DIGEST", "manifest digest mismatch")
    result, names = [], set()
    for entry in bundle.get("entries", []):
        rel = safe_rel(entry.get("path", ""))
        if str(rel) in names: raise RecoveryError("RECOVERY-DUPLICATE-PATH", str(rel))
        names.add(str(rel))
        try: data = base64.b64decode(entry["data"], validate=True)
        except Exception as exc: raise RecoveryError("RECOVERY-BUNDLE-DATA", str(rel)) from exc
        if digest(data) != entry.get("sha256"):
            raise RecoveryError("RECOVERY-BUNDLE-DIGEST", str(rel))
        result.append((rel, data))
    return result


def cmd_restore(args: argparse.Namespace) -> Dict[str, Any]:
    entries = validate_bundle(load(Path(args.bundle).resolve()))
    target = Path(args.target).resolve()
    if target.exists() and any(target.iterdir()):
        raise RecoveryError("RECOVERY-TARGET-NONEMPTY", str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.restore-", dir=str(target.parent)))
    try:
        for rel, data in entries:
            path = staging / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        if target.exists(): target.rmdir()
        os.replace(staging, target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True); raise
    return {"status": "RESTORED", "files": len(entries)}


def cmd_replay(args: argparse.Namespace) -> Dict[str, Any]:
    target = Path(args.target).resolve(); events = load(Path(args.events).resolve())
    if not isinstance(events, list): raise RecoveryError("RECOVERY-EVENTS", "events must be a list")
    for event in events:
        if (not isinstance(event, dict) or not isinstance(event.get("id"), str)
                or not event["id"] or not isinstance(event.get("sequence"), int)
                or not isinstance(event.get("content"), str)):
            raise RecoveryError("RECOVERY-EVENTS", "each event requires string id/content and integer sequence")
    ledger_path = target / ".replay-ledger.json"
    ledger = load(ledger_path) if ledger_path.exists() else {"schema": "issue-replay-ledger@v1", "events": {}}
    applied = dict(ledger.get("events", {})); count = 0
    for event in sorted(events, key=lambda e: (e.get("sequence"), e.get("id"))):
        event_id = event.get("id"); rel = safe_rel(event.get("path", "")); data = event.get("content", "").encode()
        event_digest = digest(canonical(event))
        if event_id in applied:
            if applied[event_id] != event_digest: raise RecoveryError("RECOVERY-REPLAY-CONFLICT", event_id)
            continue
        path = target / rel
        if path.exists() and path.read_bytes() != data:
            raise RecoveryError("RECOVERY-REPLAY-COLLISION", str(rel))
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists(): path.write_bytes(data)
        applied[event_id] = event_digest; count += 1
    atomic_json(ledger_path, {"schema": "issue-replay-ledger@v1", "events": applied})
    return {"status": "REPLAYED", "applied": count, "total": len(applied)}


def cmd_repair(args: argparse.Namespace) -> Dict[str, Any]:
    state = control_state(Path(args.control).resolve())
    if state["phase"] != "issue-store-write-frozen": raise RecoveryError("RECOVERY-NOT-FROZEN", "repair requires freeze")
    target, plan = Path(args.target).resolve(), load(Path(args.plan).resolve())
    if not isinstance(plan, list): raise RecoveryError("RECOVERY-REPAIR-PLAN", "plan must be a list")
    changed = 0
    for item in plan:
        path = target / safe_rel(item.get("path", ""))
        if not path.is_file() or digest(path.read_bytes()) != item.get("expected_sha256"):
            raise RecoveryError("RECOVERY-REPAIR-CAS", str(path))
        data = item.get("content", "").encode(); tmp = path.with_name(f".{path.name}.repair")
        tmp.write_bytes(data); os.replace(tmp, path); changed += 1
    return {"status": "REPAIRED", "changed": changed}


def cmd_regenerate(args: argparse.Namespace) -> Dict[str, Any]:
    state = control_state(Path(args.control).resolve())
    if state["phase"] != "issue-store-write-frozen": raise RecoveryError("RECOVERY-NOT-FROZEN", "regeneration requires freeze")
    command = [sys.executable, str(Path(args.repo).resolve() / "_src/tools/issuectl.py"), "regenerate", "--all",
               "--repo", str(Path(args.repo).resolve()), "--output-root", str(Path(args.output_root).resolve()), "--write", "--format", "json"]
    cp = subprocess.run(command, text=True, capture_output=True)
    if cp.returncode: raise RecoveryError("RECOVERY-REGENERATE", cp.stderr[-2000:] or cp.stdout[-2000:])
    return {"status": "REGENERATED", "result": json.loads(cp.stdout)}


def cmd_release(args: argparse.Namespace) -> Dict[str, Any]:
    repo, control = Path(args.repo).resolve(), Path(args.control).resolve()
    state = control_state(control); require_generation(state, args.expected_generation)
    if state["phase"] != "issue-store-write-frozen": raise RecoveryError("RECOVERY-NOT-FROZEN", "release requires freeze")
    release = load(Path(args.release).resolve()); copy = dict(release); claimed = copy.pop("payload_sha256", None)
    if release.get("schema") != "issue-recovery-release@v1" or release.get("signature_verified") is not True:
        raise RecoveryError("RECOVERY-UNSIGNED-RELEASE", "verified release signature required")
    if release.get("generation") != state["generation"] or claimed != digest(canonical(copy).rstrip(b"\n")):
        raise RecoveryError("RECOVERY-RELEASE-MISMATCH", "release payload/generation mismatch")
    selector_path = repo / "agent-workflow.json"; selector = load(selector_path)
    if selector.get("authority_epoch") != "issue-store-write-frozen": raise RecoveryError("RECOVERY-SELECTOR-DRIFT", "selector not frozen")
    selector.update(authority_epoch="issue-store-writable", write_phase="issue-store-writable")
    write_selector(selector_path, selector)
    generation = state["generation"] + 1
    atomic_json(control, {"schema": "issue-recovery-control@v1", "generation": generation,
                          "phase": "issue-store-writable", "release": release,
                          "applied_events": state.get("applied_events", {})})
    return {"status": "RELEASED", "generation": generation}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("freeze"); f.add_argument("--repo", required=True); f.add_argument("--control", required=True); f.add_argument("--expected-generation", type=int, required=True); f.add_argument("--actor", required=True); f.set_defaults(func=cmd_freeze)
    e = sub.add_parser("export"); e.add_argument("--repo", required=True); e.add_argument("--control", required=True); e.add_argument("--bundle", required=True); e.set_defaults(func=cmd_export)
    s = sub.add_parser("restore"); s.add_argument("--bundle", required=True); s.add_argument("--target", required=True); s.set_defaults(func=cmd_restore)
    r = sub.add_parser("replay"); r.add_argument("--target", required=True); r.add_argument("--events", required=True); r.set_defaults(func=cmd_replay)
    q = sub.add_parser("repair"); q.add_argument("--target", required=True); q.add_argument("--control", required=True); q.add_argument("--plan", required=True); q.set_defaults(func=cmd_repair)
    g = sub.add_parser("regenerate"); g.add_argument("--repo", required=True); g.add_argument("--control", required=True); g.add_argument("--output-root", required=True); g.set_defaults(func=cmd_regenerate)
    l = sub.add_parser("release"); l.add_argument("--repo", required=True); l.add_argument("--control", required=True); l.add_argument("--release", required=True); l.add_argument("--expected-generation", type=int, required=True); l.set_defaults(func=cmd_release)
    return p


def main() -> int:
    try:
        args = parser().parse_args(); result = args.func(args)
        print(canonical({"schema": SCHEMA, **result}).decode(), end=""); return 0
    except RecoveryError as exc:
        print(canonical({"schema": SCHEMA, "status": "BLOCKED", "code": exc.code, "message": exc.message}).decode(), end=""); return 2


if __name__ == "__main__":
    raise SystemExit(main())
