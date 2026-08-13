"""Supersession-trigger job (Feature 0006-20).

Generalizes "release-diff" into a single entry point covering all 6 trigger
kinds named in the task text: new AUTOSAR release, new curation input, user
comment, scraper update, extraction bugfix, newly available source, and AI
model/settings change.

This module does NOT reimplement graph-walking or invalidation -- both
already exist and are already tested:

- dependency_graph.find_dependents() (0006-18) finds everything downstream
  of a changed node.
- confidence.cascade_invalidate() (0006-19) already walks find_dependents()
  and marks every dependent invalidated + records a cascade_invalidation
  confidence event, which per 0006-19's own rule DOES enqueue an AI revisit
  (only dismissal blocks revisit-eligibility; cascade invalidation does not).

What was missing, and what this module adds, is the trigger-level
orchestration: given a trigger, decide whether it represents a genuine
change (diff against version_store.latest_version() using the same
content_hash8 idempotency the version store itself uses), and if so, record
the new version and invoke the existing cascade machinery -- then emit the
structured report the task explicitly asks for.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import version_id as vid  # noqa: E402
import version_store as vs  # noqa: E402
import dependency_graph as dg  # noqa: E402
import confidence as conf  # noqa: E402

SRC_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = SRC_ROOT / "spec" / "supersession-reports"

TRIGGER_KINDS = (
    "new_release",
    "new_curation_input",
    "user_comment",
    "scraper_update",
    "extraction_bugfix",
    "new_source_available",
    "ai_model_change",
)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def process_trigger(trigger_kind: str, canonical_id: str, release: str, content: str,
                     reason: str = None) -> dict:
    """Process one trigger for one requirement (canonical_id). Returns a
    report dict with: trigger_kind, canonical_id, changed (bool),
    new_version_id (or None if unchanged), dependents_invalidated (list),
    revisit_enqueued (bool, mirrors whether cascade_invalidate ran),
    unresolved (list of reasons this trigger could not be fully processed,
    e.g. an unknown trigger_kind or a missing dependency-graph node).

    A trigger that does not actually change the content is a documented
    no-op (changed=False, nothing invalidated) -- matching version_store's
    own idempotency guarantee (content_hash8 unchanged = no new version).
    """
    report = {
        "trigger_kind": trigger_kind, "canonical_id": canonical_id, "release": release,
        "processed_at": _now(), "changed": False, "new_version_id": None,
        "dependents_invalidated": [], "revisit_enqueued": False, "unresolved": [],
    }
    if trigger_kind not in TRIGGER_KINDS:
        report["unresolved"].append("unknown trigger_kind: %r" % trigger_kind)
        return report

    previous = vs.latest_version(canonical_id)
    candidate_version_id = vid.requirement_version_id(canonical_id, release, content)
    if previous is not None and previous.get("version_id") == candidate_version_id:
        return report  # no genuine change -- documented no-op, mirrors record_version()'s own idempotency check

    new_version_id = vs.record_version(canonical_id, release, content,
                                        meta={"trigger_kind": trigger_kind, "reason": reason})
    report["changed"] = True
    report["new_version_id"] = new_version_id

    dependents = conf.cascade_invalidate(canonical_id, reason or ("trigger:" + trigger_kind))
    report["dependents_invalidated"] = sorted(dependents)
    report["revisit_enqueued"] = bool(dependents)
    return report


def write_report(report: dict) -> Path:
    """Persist a single process_trigger() report as its own JSON file under
    spec/supersession-reports/, named by canonical_id + timestamp so
    multiple triggers on the same requirement never clobber each other."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = report["canonical_id"].replace("/", "_")
    ts = report["processed_at"].replace(":", "")
    path = REPORTS_DIR / ("%s.%s.json" % (safe_id, ts))
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def summarize_reports(reports: list[dict]) -> dict:
    """Aggregate a batch of process_trigger() reports into the summary shape
    the task text asks for: changed requirements, superseded decisions/
    evidence/artifacts (= dependents_invalidated across all reports),
    revisit tasks enqueued, unresolved cases."""
    changed = [r["canonical_id"] for r in reports if r["changed"]]
    superseded = sorted({dep for r in reports for dep in r["dependents_invalidated"]})
    revisits = sum(1 for r in reports if r["revisit_enqueued"])
    unresolved = [{"canonical_id": r["canonical_id"], "issues": r["unresolved"]}
                  for r in reports if r["unresolved"]]
    return {
        "changed_requirements": changed,
        "superseded_dependents": superseded,
        "revisit_tasks_enqueued": revisits,
        "unresolved": unresolved,
    }
