#!/usr/bin/env python3
"""Parent-package moving-source / moving-schema / authorized-event reconciliation (Task 0037-15).

Calls ``issue_reimport``, ``issue_schema_transform``, and ``issue_event_replay`` as
libraries. Combined candidate = latest-source re-import targeting ``issue-item@v1``
plus exactly-once replay of compatible authorized events. Manual shadow edits
cannot win: only importer/transform/replay outputs are compared.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

TOOL_REL = "_src/tools/issue_reconciliation.py"
ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REI = _load("issue_reimport", ROOT / "_src/tools/issue_reimport.py")
TRN = _load("issue_schema_transform", ROOT / "_src/tools/issue_schema_transform.py")
RPL = _load("issue_event_replay", ROOT / "_src/tools/issue_event_replay.py")


class ReconciliationError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _ref(kind: str, ident: str, **extra: Any) -> dict:
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}",
        "classification": "internal",
    }
    value.update(extra)
    return value


def drafts_from_import_root(import_root: Path) -> List[dict]:
    drafts: List[dict] = []
    for md_path in sorted(import_root.rglob("index.md")):
        sem = TRN.parse_imported_markdown(md_path.read_text(encoding="utf-8"))
        draft = {
            "schema": TRN.FROM_SCHEMA,
            "schema_version": TRN.DRAFT_SCHEMA_VERSION,
            "id": sem["id"],
            "level": sem["level"],
            "parent": sem["parent"],
            "state": sem["state"],
            "prerequisites": sem["prerequisites"],
            "labels": sem["labels"],
            "goal": sem["goal"],
            "scope": sem["scope"],
            "criteria": sem["criteria"],
            "definition_of_done": sem["definition_of_done"],
            "source_locator": "legacy:TODO.md:reconciliation",
        }
        drafts.append({k: v for k, v in draft.items() if v is not None})
    return drafts


def write_draft_root(dest: Path, drafts: Sequence[Mapping[str, Any]]) -> None:
    items = dest / "items"
    items.mkdir(parents=True, exist_ok=True)
    for obj in drafts:
        (items / f"{obj['id']}.json").write_text(_canonical_json(obj), encoding="utf-8")


def item_bodies(run_root: Path, items: Sequence[Mapping[str, Any]]) -> Dict[str, bytes]:
    bodies: Dict[str, bytes] = {}
    for rec in items:
        path = run_root / rec["path"]
        if path.is_file():
            bodies[rec["id"]] = path.read_bytes()
    return bodies


def replay_candidate_from_reimport(rei: Mapping[str, Any], latest_source: str) -> dict:
    run_root = Path(rei["run_root"])
    items: Dict[str, dict] = {}
    for rec in rei.get("items") or []:
        path = rec["path"]
        full = run_root / path
        body = full.read_bytes() if full.is_file() else b""
        items[rec["id"]] = {
            "id": rec["id"],
            "path": path,
            "digest": RPL.item_digest(body),
            "deleted": False,
            "active_claims": [],
        }
    return {
        "source_commit": rei["watermarks"]["latest_source"],
        "latest_source": latest_source,
        "schema": "issue-item@v1",
        "issues_root": str(run_root),
        "items": items,
    }


def collect_event_ids(store_root: Path) -> List[str]:
    events_root = store_root / "provenance" / "events"
    if not events_root.is_dir():
        return []
    ids = [p.stem for p in events_root.glob("*/*/*.json")]
    return sorted(ids)


def seed_replay_store(store_root: Path, *, run_id: str, finding_id: str, commit: str, issue_id: str) -> None:
    store = RPL.PS.ProvenanceStore(store_root)
    store.create_run(
        {
            "schema_version": "1.0",
            "run_id": run_id,
            "started_at": "2026-08-16T08:00:00Z",
            "ended_at": "2026-08-16T08:02:00Z",
            "environment": "assessment",
            "classification": "internal",
            "status": "succeeded",
            "producer": _ref("commit", commit),
            "inputs": [_ref("commit", commit), _ref("issue", issue_id)],
            "outputs": [],
        }
    )
    store.create_finding(
        {
            "schema_version": "1.0",
            "finding_id": finding_id,
            "detected_at": "2026-08-16T08:01:00Z",
            "state": "open",
            "classification": "internal",
            "environment": "assessment",
            "subject": _ref("issue", issue_id),
            "detected_during": _ref("run", run_id),
        }
    )


def authorized_event(*, event_id: str, item_id: str, digest: str, latest: str, run_id: str, finding_id: str) -> dict:
    return {
        "schema_version": "1.0",
        "event_id": event_id,
        "occurred_at": "2026-08-16T08:01:00Z",
        "relation": "detected-during",
        "source": _ref("finding", finding_id),
        "target": _ref("run", run_id),
        "environment": "assessment",
        "classification": "internal",
        "run": _ref("run", run_id),
        "reconciliation_authorized_by": "decision:0037-06.02",
        "base_source": latest,
        "item_id": item_id,
        "item_digest": digest,
        "mutates_item": False,
    }


def compare_item_sets(
    left: Mapping[str, bytes],
    right: Mapping[str, bytes],
) -> Tuple[List[str], List[str], List[str]]:
    left_ids = set(left)
    right_ids = set(right)
    lost = sorted(left_ids - right_ids)
    extra = sorted(right_ids - left_ids)
    drifted = sorted(i for i in left_ids & right_ids if left[i] != right[i])
    return lost, extra, drifted


def reconcile(
    *,
    repo: Path,
    output_parent: Path,
    early_commit: str,
    latest_commit: str,
    intervening_commits: Sequence[str],
    event_id: str = "018f4a31-32ac-7abc-8def-0123456789ab",
    replay_run_id: str = "018f4a31-32aa-7abc-8def-0123456789ab",
    finding_id: str = "018f4a31-32ab-7abc-8def-0123456789ab",
    replay_item_id: str = "0037-01",
) -> dict:
    """Run combined (watermark chain + schema upgrade + replay) vs clean latest import + replay."""
    repo = repo.resolve()
    output_parent = output_parent.resolve()
    output_parent.mkdir(parents=True, exist_ok=True)

    findings: List[dict] = []

    combined_out = output_parent / "combined"
    clean_out = output_parent / "clean"
    combined_out.mkdir()
    clean_out.mkdir()

    # Combined: reimport early watermark, schema-upgrade drafts, then intervening
    # commits, then latest source, then replay.
    early = REI.reimport(
        repo=repo,
        output_parent=combined_out / "reimport",
        source_commit=early_commit,
        baseline=early_commit,
    )
    prev_state = Path(early["run_root"]) / "migration-state.json"
    draft_root = combined_out / "drafts-early"
    write_draft_root(draft_root, drafts_from_import_root(Path(early["run_root"])))
    upgrade = TRN.transform(
        repo=repo,
        input_root=draft_root,
        output_parent=combined_out / "transform",
        from_schema=TRN.FROM_SCHEMA,
        to_schema=TRN.TO_SCHEMA,
        run_id="parent-upgrade-early",
        clean_import_root=Path(early["run_root"]),
        source_commit=early_commit,
    )
    if not upgrade.get("promotable"):
        findings.append(
            {
                "code": "schema-upgrade-not-equivalent",
                "severity": "blocking",
                "message": "early-source transform is not equivalent to clean import",
            }
        )

    last = early
    for idx, commit in enumerate(list(intervening_commits) + [latest_commit]):
        last = REI.reimport(
            repo=repo,
            output_parent=combined_out / "reimport",
            source_commit=commit,
            previous_state_path=prev_state,
        )
        prev_state = Path(last["run_root"]) / "migration-state.json"

    combined_latest = last

    # Clean: one latest-source import targeting latest schema (importer v1).
    clean = REI.reimport(
        repo=repo,
        output_parent=clean_out / "reimport",
        source_commit=latest_commit,
        baseline=early_commit,
    )

    combined_bodies = item_bodies(Path(combined_latest["run_root"]), combined_latest.get("items") or [])
    clean_bodies = item_bodies(Path(clean["run_root"]), clean.get("items") or [])
    lost, extra, drifted = compare_item_sets(clean_bodies, combined_bodies)
    if lost or extra or drifted:
        findings.append(
            {
                "code": "item-set-mismatch",
                "severity": "blocking",
                "message": f"lost={lost} extra={extra} drifted={drifted}",
            }
        )

    if combined_latest.get("import_tree_digest") != clean.get("import_tree_digest"):
        findings.append(
            {
                "code": "import-tree-mismatch",
                "severity": "blocking",
                "message": "combined latest import_tree_digest differs from clean latest import",
            }
        )

    if replay_item_id not in combined_bodies:
        raise ReconciliationError("REC-ITEM", f"replay item {replay_item_id} missing from combined latest")

    digest = RPL.item_digest(combined_bodies[replay_item_id])
    event = authorized_event(
        event_id=event_id,
        item_id=replay_item_id,
        digest=digest,
        latest=latest_commit,
        run_id=replay_run_id,
        finding_id=finding_id,
    )

    combined_store = combined_out / "prov"
    clean_store = clean_out / "prov"
    combined_store.mkdir()
    clean_store.mkdir()
    seed_replay_store(
        combined_store, run_id=replay_run_id, finding_id=finding_id, commit=latest_commit, issue_id=replay_item_id
    )
    seed_replay_store(
        clean_store, run_id=replay_run_id, finding_id=finding_id, commit=latest_commit, issue_id=replay_item_id
    )

    cand_combined = replay_candidate_from_reimport(combined_latest, latest_commit)
    cand_clean = replay_candidate_from_reimport(clean, latest_commit)

    report_combined = RPL.replay_events(
        candidate=cand_combined,
        events=[event],
        store_root=combined_store,
        replay_run_id=replay_run_id,
        record_findings=True,
    )
    report_clean = RPL.replay_events(
        candidate=cand_clean,
        events=[event],
        store_root=clean_store,
        replay_run_id=replay_run_id,
        record_findings=True,
    )

    # Exactly-once: replay the same authorized event again on combined; must be idempotent.
    again = RPL.replay_events(
        candidate=cand_combined,
        events=[event],
        store_root=combined_store,
        replay_run_id=replay_run_id,
        record_findings=True,
    )

    combined_ids = collect_event_ids(combined_store)
    clean_ids = collect_event_ids(clean_store)
    if combined_ids != clean_ids:
        findings.append(
            {
                "code": "event-id-mismatch",
                "severity": "blocking",
                "message": f"combined events {combined_ids} vs clean {clean_ids}",
            }
        )
    if combined_ids.count(event_id) not in (0, 1) or len([i for i in combined_ids if i == event_id]) > 1:
        findings.append(
            {
                "code": "event-duplicated",
                "severity": "blocking",
                "message": f"event {event_id} stored more than once",
            }
        )
    if event_id not in combined_ids:
        findings.append(
            {
                "code": "event-lost",
                "severity": "blocking",
                "message": f"authorized event {event_id} not stored",
            }
        )
    if not report_combined.get("promotable") or not report_clean.get("promotable"):
        findings.append(
            {
                "code": "replay-not-promotable",
                "severity": "blocking",
                "message": "replay of compatible authorized events failed",
            }
        )
    if again.get("results") and again["results"][0].get("status") != "replay":
        findings.append(
            {
                "code": "replay-not-exactly-once",
                "severity": "blocking",
                "message": "second replay of identical event was not idempotent",
            }
        )
    if report_combined.get("candidate_items_mutated") or report_clean.get("candidate_items_mutated"):
        findings.append(
            {
                "code": "shadow-mutation",
                "severity": "blocking",
                "message": "replay mutated candidate item files",
            }
        )

    blocking = [f for f in findings if f.get("severity") == "blocking"]
    equivalent = not blocking
    report = {
        "schema": "reconciliation-report@v1",
        "early_commit": early_commit,
        "intervening_commits": list(intervening_commits),
        "latest_commit": latest_commit,
        "schema_upgrade": {
            "from_schema": TRN.FROM_SCHEMA,
            "to_schema": TRN.TO_SCHEMA,
            "promotable": bool(upgrade.get("promotable")),
            "status": upgrade.get("status"),
        },
        "combined": {
            "import_tree_digest": combined_latest.get("import_tree_digest"),
            "item_ids": sorted(combined_bodies),
            "replayed": report_combined.get("replayed"),
            "event_ids": combined_ids,
        },
        "clean": {
            "import_tree_digest": clean.get("import_tree_digest"),
            "item_ids": sorted(clean_bodies),
            "replayed": report_clean.get("replayed"),
            "event_ids": clean_ids,
        },
        "lost_items": lost,
        "extra_items": extra,
        "drifted_items": drifted,
        "findings": findings,
        "equivalent": equivalent,
        "promotable": equivalent,
    }
    (output_parent / "reconciliation-report.json").write_text(_canonical_json(report), encoding="utf-8")
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output-parent", required=True)
    parser.add_argument("--early-commit", required=True)
    parser.add_argument("--latest-commit", required=True)
    parser.add_argument("--intervening-commit", action="append", default=[])
    args = parser.parse_args(argv)
    report = reconcile(
        repo=Path(args.repo),
        output_parent=Path(args.output_parent),
        early_commit=args.early_commit,
        latest_commit=args.latest_commit,
        intervening_commits=args.intervening_commit,
    )
    print(_canonical_json(report), end="")
    return 0 if report["equivalent"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
