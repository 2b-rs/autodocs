"""First-class AI-proposed NEW spec elements (Feature 0006-05).

Before this module, 'hypothesized/unconfirmed' existed only as prose in the
process docs -- no CLI or queue path ever created such an element. This
module is that missing piece.

Why a SEPARATE store, not a lightweight stub in _src/spec/records/: an
unconfirmed AI guess must never be indistinguishable -- even transiently --
from a real curated record. Hypotheses live under
_src/spec/hypotheses/<project>/<kind>/<hypothesis-id-slug>.json until a
human curator promotes or rejects them.

Identity: hypothesis:<uuid7> (version_id.hypothesis_id(), same generator as
the curation:/evidence:/artifact: families from 0006-15). This is
deliberately NOT a canonical_id (project/kind/id) yet -- proposed_id is
plain text until promotion, because canonical_id.is_valid() only validates
(project, kind) registration, not id uniqueness against not-yet-existing
records.

Lifecycle: open -> accepted (promoted, mints a real canonical id and writes
into _src/spec/records/) or rejected (marked in place, never deleted -- same
never-delete precedent as the 0006-16 version store). status/history follow
the curation-item@v1 enum from 0006-03 so hypotheses remain expressible in
that unified schema, just with item_kind='ai-hypothesis'.
"""
from __future__ import annotations
import json
import os
import sys
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_DIR = str(Path(__file__).resolve().parent)
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)
from canonical_id import canonical_id as _mint_canonical_id, is_valid, slug  # noqa: E402
from version_id import hypothesis_id as _mint_hypothesis_id, parse_prefixed_id  # noqa: E402

HYPOTHESES_ROOT = Path(__file__).resolve().parents[1] / "spec" / "hypotheses"
RECORDS_ROOT = Path(__file__).resolve().parents[1] / "spec" / "records"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _path_for(hyp_id: str) -> Path:
    parsed = parse_prefixed_id(hyp_id)
    if parsed is None or parsed["prefix"] != "hypothesis":
        raise ValueError(f"not a hypothesis id: {hyp_id!r}")
    return HYPOTHESES_ROOT / (slug(hyp_id) + ".json")


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp-%s" % _uuid.uuid4().hex[:8])
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def record_hypothesis(project: str, kind: str, proposed_id: str, subject: str,
                       proposed_state, evidence: list | None = None,
                       decision_basis: dict | None = None) -> dict:
    """Create a new open hypothesis. Raises ValueError if (project, kind)
    isn't a registered pair in projects.json -- kind validity is checked
    even though the id itself doesn't exist as a real record yet."""
    if not is_valid(project, kind):
        raise ValueError(f"not a registered (project, kind): ({project!r}, {kind!r})")
    if not proposed_id:
        raise ValueError("proposed_id is required")
    hyp_id = _mint_hypothesis_id()
    entry = {
        "schema": "hypothesis@v1",
        "id": hyp_id,
        "project": project,
        "kind": kind,
        "proposed_id": proposed_id,
        "item_kind": "ai-hypothesis",
        "origin": "ai",
        "status": "open",
        "subject": subject,
        "current_state": None,
        "proposed_state": proposed_state,
        "evidence": evidence or [],
        "decision_basis": decision_basis or {},
        "created": _now(),
        "promoted_to": None,
        "history": [{"date": _now(), "from": None, "to": "open", "actor": "ai", "reason": "created"}],
    }
    _atomic_write(_path_for(hyp_id), entry)
    return entry


def get_hypothesis(hyp_id: str) -> dict | None:
    path = _path_for(hyp_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_hypotheses(project: str | None = None, status: str | None = None) -> list[dict]:
    if not HYPOTHESES_ROOT.exists():
        return []
    out = []
    for path in sorted(HYPOTHESES_ROOT.rglob("*.json")):
        entry = json.loads(path.read_text(encoding="utf-8"))
        if project and entry.get("project") != project:
            continue
        if status and entry.get("status") != status:
            continue
        out.append(entry)
    return out


def reject_hypothesis(hyp_id: str, reason: str, decided_by: str) -> dict:
    entry = get_hypothesis(hyp_id)
    if entry is None:
        raise ValueError(f"unknown hypothesis: {hyp_id!r}")
    if entry["status"] not in ("open", "proposed"):
        raise ValueError(f"hypothesis {hyp_id!r} is already {entry['status']!r}, cannot reject")
    entry["history"].append({"date": _now(), "from": entry["status"], "to": "rejected",
                              "actor": decided_by, "reason": reason})
    entry["status"] = "rejected"
    _atomic_write(_path_for(hyp_id), entry)
    return entry


def promote_hypothesis(hyp_id: str, decided_by: str, reason: str = "promoted from hypothesis") -> dict:
    """Mint a REAL canonical id and write a new record into
    _src/spec/records/<kind-dir>/<id>.json, with a first-history entry that
    links back to the source hypothesis -- "promotes without losing
    history" per 0006-05's own wording. Refuses to overwrite an existing
    record at that path (promotion is one-shot per proposed_id).
    """
    entry = get_hypothesis(hyp_id)
    if entry is None:
        raise ValueError(f"unknown hypothesis: {hyp_id!r}")
    if entry["status"] not in ("open", "proposed"):
        raise ValueError(f"hypothesis {hyp_id!r} is already {entry['status']!r}, cannot promote")

    project, kind, item_id = entry["project"], entry["kind"], entry["proposed_id"]
    new_canonical = _mint_canonical_id(item_id, project=project, kind=kind)
    kind_dir = project.split("/")[-1].upper() if kind == "record" else kind
    record_path = RECORDS_ROOT / kind_dir / f"{item_id}.json"
    if record_path.exists():
        raise ValueError(f"a record already exists at {record_path}, refusing to overwrite via promotion")

    now = _now()
    record = {
        "id": item_id,
        "canonical_id": new_canonical,
        "status": {
            "state": "proposed/from-ai-hypothesis",
            "reason": f"promoted from {hyp_id}: {reason}",
            "campaign": None,
        },
        "history": [{
            "date": now, "from": None, "to": "proposed/from-ai-hypothesis",
            "actor": decided_by, "reason": f"promoted from {hyp_id}: {reason}",
            "source_hypothesis": hyp_id,
        }],
        "content": entry.get("proposed_state"),
        "evidence": entry.get("evidence") or [],
    }
    _atomic_write(record_path, record)

    entry["history"].append({"date": now, "from": entry["status"], "to": "applied",
                              "actor": decided_by, "reason": reason,
                              "promoted_to": new_canonical})
    entry["status"] = "applied"
    entry["promoted_to"] = new_canonical
    _atomic_write(_path_for(hyp_id), entry)
    return {"hypothesis": entry, "record_path": str(record_path), "canonical_id": new_canonical}
