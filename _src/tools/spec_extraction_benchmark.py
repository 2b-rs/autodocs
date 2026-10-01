#!/usr/bin/env python3
"""Frozen extraction-benchmark oracle and review-first draft builder."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ID_RE = re.compile(r"(?:RS|SWS)_[A-Za-z0-9_]+_\d{3,}")
CATEGORIES = (
    "multi_page", "dense_fields", "lists", "multiple_per_page",
    "mixed_case_id", "typography", "empty_or_dash", "single_page",
)
FROZEN_STATUS = "frozen"
FROZEN_RECORD_COUNT = 199
FROZEN_FILENAME = "benchmark.json"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FROZEN_PATH = (
    REPO_ROOT / "_src" / "tests" / "fixtures" / "spec_extraction" / FROZEN_FILENAME
)
DEFAULT_DRAFT_PATH = DEFAULT_FROZEN_PATH.with_name("benchmark-draft.json")
ORACLE_EXPECTED_KEYS = ("heading", "fields", "pages", "complete_start", "complete_end")


class FrozenOverwriteError(RuntimeError):
    """Raised when a write would replace the frozen oracle."""


class FrozenOracleError(ValueError):
    """Raised when the frozen oracle is missing, malformed, or drifted."""


def load_records(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("records"), (dict, list)):
        data = data["records"]
    if isinstance(data, list):
        return {str(r.get("id") or r.get("requirement_id")): r for r in data
                if isinstance(r, dict) and (r.get("id") or r.get("requirement_id"))}
    if isinstance(data, dict):
        return {str(k): v for k, v in data.items()
                if isinstance(v, dict) and ID_RE.fullmatch(str(k))}
    return {}


def text(record: dict) -> str:
    props = record.get("props") or record.get("fields") or {}
    values = [record.get("heading"), record.get("requirement_text"), record.get("text_raw")]
    values.extend(props.values() if isinstance(props, dict) else ())
    return "\n".join(str(v) for v in values if v is not None)


def pages(record: dict) -> list[int]:
    raw = (record.get("pages") or record.get("page_range")
           or (record.get("source") or {}).get("pages")
           or record.get("pages_all_definitions")
           or record.get("page") or [])
    if isinstance(raw, int):
        return [raw]
    if isinstance(raw, str):
        return [int(x) for x in re.findall(r"\d+", raw)]
    return [int(x) for x in raw if isinstance(x, (int, float))]


def has_definition_anchor(record: dict) -> bool:
    """Return whether extraction found a definition block around the ID.

    Citation-only mentions have neither completion boundary. A populated
    heading/field payload remains accepted for older campaign records that do
    not persist the boundary flags.
    """
    if record.get("complete_start") is True or record.get("complete_end") is True:
        return True
    for key in ("definition_start", "definition_end", "anchor_before", "anchor_after"):
        if record.get(key) is True:
            return True
    props = record.get("props") or record.get("fields") or {}
    return bool(record.get("heading") and isinstance(props, dict) and props)


def classify(rid: str, record: dict, page_count: dict[int, int]) -> list[str]:
    value, pgs = text(record), pages(record)
    props = record.get("props") or record.get("fields") or {}
    result = []
    if len(set(pgs)) >= 2: result.append("multi_page")
    if isinstance(props, dict) and len(props) >= 5: result.append("dense_fields")
    if re.search(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+", value): result.append("lists")
    if any(page_count[p] > 1 for p in pgs): result.append("multiple_per_page")
    observed = str(record.get("id_observed") or rid)
    prefix = observed.rsplit("_", 1)[0]
    if any(c.islower() for c in prefix): result.append("mixed_case_id")
    if re.search(r"[ﬁﬂ–—‘’“”]|\w-\n\w|\ufffd", value): result.append("typography")
    if any(str(v).strip() in {"", "-", "–", "—"} for v in props.values()) if isinstance(props, dict) else False:
        result.append("empty_or_dash")
    if len(set(pgs)) <= 1: result.append("single_page")
    return result


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_canonical(value) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def oracle_payload(record: dict) -> dict:
    expected = record.get("expected") if isinstance(record.get("expected"), dict) else {}
    fields = expected.get("fields")
    if not isinstance(fields, dict):
        fields = {}
    return {
        "id": record.get("id"),
        "document": record.get("document"),
        "categories": list(record.get("categories") or []),
        "backend_presence": list(record.get("backend_presence") or []),
        "expected": {
            "heading": expected.get("heading"),
            "fields": fields,
            "pages": list(expected.get("pages") or []),
            "complete_start": expected.get("complete_start"),
            "complete_end": expected.get("complete_end"),
        },
    }


def record_digest(record: dict) -> str:
    return sha256_canonical(oracle_payload(record))


def manifest_from_records(records: list[dict]) -> dict[str, str]:
    return {str(record["id"]): record_digest(record) for record in records}


def content_sha256_from_manifest(manifest: dict[str, str]) -> str:
    return sha256_canonical([[rid, manifest[rid]] for rid in sorted(manifest)])


def freeze_from_draft(draft: dict, *, draft_path: Path | None = None,
                      draft_sha256: str | None = None) -> dict:
    records = list(draft.get("records") or [])
    manifest = manifest_from_records(records)
    frozen = {
        "schema": draft.get("schema", 1),
        "status": FROZEN_STATUS,
        "campaign": draft.get("campaign"),
        "source_draft": {
            "path": None if draft_path is None else str(draft_path.as_posix()),
            "sha256": draft_sha256,
        },
        "selection_policy": draft.get("selection_policy"),
        "frozen_record_count": FROZEN_RECORD_COUNT,
        "content_sha256": content_sha256_from_manifest(manifest),
        "record_manifest": dict(sorted(manifest.items())),
        "records": records,
    }
    if "skipped" in draft:
        frozen["skipped"] = draft["skipped"]
    return frozen


def draft_write_targets(output: Path) -> list[Path]:
    return [output / "benchmark-draft.json", output / "README.md"]


def guard_frozen_overwrite(destinations: list[Path], frozen: Path) -> None:
    frozen_resolved = frozen.resolve()
    for destination in destinations:
        resolved = destination.resolve()
        if resolved == frozen_resolved or destination.name == FROZEN_FILENAME:
            raise FrozenOverwriteError(
                f"refusing to write {destination} over frozen oracle {frozen}"
            )


def expected_view(record: dict) -> dict | None:
    if isinstance(record.get("expected"), dict):
        expected = record["expected"]
        fields = expected.get("fields")
        page_values = expected.get("pages")
    else:
        expected = record
        fields = record.get("props") if isinstance(record.get("props"), dict) else record.get("fields")
        page_values = pages(record)
    if not isinstance(fields, dict):
        return None
    if isinstance(page_values, int):
        page_list = [page_values]
    elif isinstance(page_values, list):
        page_list = [int(page) for page in page_values if isinstance(page, (int, float, str)) and str(page).lstrip("-").isdigit()]
    else:
        page_list = []
    return {
        "heading": expected.get("heading"),
        "fields": fields,
        "pages": page_list,
        "complete_start": expected.get("complete_start"),
        "complete_end": expected.get("complete_end"),
    }


def index_candidate_records(records: list) -> tuple[dict[str, dict], list[str], list[dict]]:
    by_id: dict[str, dict] = {}
    duplicates: list[str] = []
    unresolved: list[dict] = []
    for record in records:
        if not isinstance(record, dict):
            unresolved.append({"id": None, "reason": "record_not_object"})
            continue
        rid = str(record.get("id") or record.get("requirement_id") or "").strip()
        if not rid:
            unresolved.append({"id": None, "reason": "missing_id"})
            continue
        if expected_view(record) is None:
            unresolved.append({"id": rid, "reason": "unresolved_expected"})
            continue
        if rid in by_id:
            duplicates.append(rid)
            continue
        by_id[rid] = record
    return by_id, duplicates, unresolved


def load_candidate_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return list(data["records"])
    if isinstance(data, list):
        return list(data)
    if isinstance(data, dict):
        return [{"id": key, **value} if isinstance(value, dict) else {"id": key}
                for key, value in data.items() if ID_RE.fullmatch(str(key))]
    raise FrozenOracleError("candidate is not a JSON object or list of records")


def validate_frozen(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["frozen oracle is not a JSON object"]
    if data.get("status") != FROZEN_STATUS:
        errors.append(f"status must be {FROZEN_STATUS!r}, got {data.get('status')!r}")
    records = data.get("records")
    if not isinstance(records, list):
        errors.append("records must be a list")
        return errors
    if len(records) != FROZEN_RECORD_COUNT:
        errors.append(f"expected {FROZEN_RECORD_COUNT} records, got {len(records)}")
    ids = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not record.get("id"):
            errors.append(f"records[{index}] is missing id")
            continue
        ids.append(str(record["id"]))
        view = expected_view(record)
        if view is None:
            errors.append(f"{record.get('id')} has unresolved expected fields")
        elif any(key not in (record.get("expected") or {}) for key in ORACLE_EXPECTED_KEYS):
            errors.append(f"{record.get('id')} is missing an expected oracle field")
    unique = set(ids)
    if len(ids) != len(unique):
        extra = sorted({rid for rid in ids if ids.count(rid) > 1})
        errors.append(f"duplicate ids: {extra}")
    manifest = data.get("record_manifest")
    if not isinstance(manifest, dict):
        errors.append("record_manifest must be an object")
        return errors
    manifest_ids = {str(key) for key in manifest}
    missing = sorted(unique - manifest_ids)
    extra = sorted(manifest_ids - unique)
    if missing:
        errors.append(f"manifest missing ids: {missing}")
    if extra:
        errors.append(f"manifest extra ids: {extra}")
    if data.get("frozen_record_count") != FROZEN_RECORD_COUNT:
        errors.append("frozen_record_count does not match the frozen cardinality")
    recomputed = manifest_from_records([record for record in records if isinstance(record, dict) and record.get("id")])
    for rid, digest in recomputed.items():
        expected_digest = manifest.get(rid)
        if expected_digest != digest:
            errors.append(f"digest mismatch for {rid}")
    expected_content = content_sha256_from_manifest(recomputed)
    if data.get("content_sha256") != expected_content:
        errors.append("content_sha256 does not match the record manifest")
    return errors


def load_frozen(path: Path) -> dict:
    if not path.is_file():
        raise FrozenOracleError(f"frozen oracle missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FrozenOracleError(f"frozen oracle is not valid JSON: {exc}") from exc
    errors = validate_frozen(data)
    if errors:
        raise FrozenOracleError("; ".join(errors))
    return data


def compare_to_frozen(frozen: dict, candidate_records: list) -> dict:
    frozen_records = frozen.get("records") or []
    frozen_by_id = {str(record["id"]): record for record in frozen_records if isinstance(record, dict) and record.get("id")}
    candidate_by_id, duplicates, unresolved = index_candidate_records(candidate_records)
    missing = sorted(set(frozen_by_id) - set(candidate_by_id))
    extra = sorted(set(candidate_by_id) - set(frozen_by_id))
    changed = []
    for rid, record in sorted(candidate_by_id.items()):
        if rid not in frozen_by_id:
            continue
        left = expected_view(frozen_by_id[rid])
        right = expected_view(record)
        if left != right:
            fields = [key for key in ORACLE_EXPECTED_KEYS if (left or {}).get(key) != (right or {}).get(key)]
            changed.append({"id": rid, "fields": fields})
    ok = not (missing or extra or duplicates or changed or unresolved)
    return {
        "ok": ok,
        "compared": len(frozen_by_id),
        "missing": missing,
        "extra": extra,
        "duplicate": sorted(set(duplicates)),
        "changed": changed,
        "unresolved": unresolved,
    }


def check_report(path: Path) -> dict:
    data = load_frozen(path)
    return {
        "ok": True,
        "status": data["status"],
        "path": str(path),
        "records": len(data["records"]),
        "content_sha256": data["content_sha256"],
        "source_draft": data.get("source_draft"),
    }


def build_draft(campaign: Path, output: Path, size: int, frozen: Path | None = None) -> int:
    frozen_path = (frozen or DEFAULT_FROZEN_PATH)
    guard_frozen_overwrite([output, *draft_write_targets(output)], frozen_path)
    raw = campaign / "raw"
    pairs: dict[str, dict[str, Path]] = defaultdict(dict)
    for path in sorted(raw.glob("*.json")):
        match = re.match(r"(.+)\.(pypdf|builtin)\.json$", path.name)
        if match: pairs[match.group(1)][match.group(2)] = path
    candidates = []
    skipped = []
    for document, files in sorted(pairs.items()):
        by_backend = {b: load_records(p) for b, p in files.items()}
        ids = sorted(set().union(*(set(v) for v in by_backend.values())))
        page_count: dict[int, int] = defaultdict(int)
        preferred = by_backend.get("pypdf", {}) or by_backend.get("builtin", {})
        for rid in ids:
            for p in set(pages(preferred.get(rid, {}))): page_count[p] += 1
        for rid in ids:
            records = [by_backend[backend][rid] for backend in ("pypdf", "builtin")
                       if rid in by_backend.get(backend, {})]
            record = preferred.get(rid) or (records[0] if records else {})
            anchored = next((item for item in records if has_definition_anchor(item)), None)
            if anchored is None:
                skipped.append({"id": rid, "document": document, "reason": "no_definition_anchor",
                                "backend_presence": sorted(b for b, records_by_id in by_backend.items() if rid in records_by_id)})
                continue
            if not has_definition_anchor(record):
                record = anchored
            candidates.append({
                "id": rid, "document": document, "categories": classify(rid, record, page_count),
                "backend_presence": sorted(b for b, records in by_backend.items() if rid in records),
                "expected": {"heading": record.get("heading"), "fields": record.get("props") or record.get("fields") or {},
                             "pages": pages(record), "complete_start": None,
                             "complete_end": record.get("complete_end")},
                "review": {"status": "needs_review", "reviewer": None, "notes": ""},
            })
    selected, used = [], set()
    def take(predicate, limit):
        for c in candidates:
            key = (c["document"], c["id"])
            if key not in used and predicate(c):
                selected.append(c); used.add(key)
                if limit and sum(1 for x in selected if predicate(x)) >= limit: break
    for document in sorted(pairs): take(lambda c, d=document: c["document"] == d, 1)
    for category in CATEGORIES[:-1]: take(lambda c, k=category: k in c["categories"], 25)
    take(lambda c: len(c["backend_presence"]) == 1, 0)
    take(lambda c: True, size)
    selected = selected[:size]
    output.mkdir(parents=True, exist_ok=True)
    fixture = {"schema": 1, "status": "draft-needs-manual-review", "campaign": campaign.name,
               "selection_policy": {"target_size": size, "minimum_per_difficult_shape": 25,
                                    "categories": list(CATEGORIES), "requires_definition_anchor": True},
               "records": selected, "skipped": sorted(skipped, key=lambda item: (item["document"], item["id"]))}
    (output / "benchmark-draft.json").write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {k: sum(k in c["categories"] for c in selected) for k in CATEGORIES}
    docs = {d: sum(c["document"] == d for c in selected) for d in sorted(pairs)}
    report = ["# Extraction benchmark draft", "", f"Selected: {len(selected)} / {size}", f"Skipped: {len(skipped)} (no definition anchor)", "",
              "This is a review queue, not a frozen truth set. Every record must be checked manually.", "",
              "## Shape coverage", ""] + [f"- {k}: {v}" for k, v in counts.items()] + ["", "## Document coverage", ""] + [f"- {k}: {v}" for k, v in docs.items()]
    (output / "README.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"selected": len(selected), "shape_counts": counts, "document_counts": docs}, indent=2))
    return 0 if len(selected) == size and all(v for v in docs.values()) else 2


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check the frozen extraction-benchmark oracle; build a draft only when a campaign is given."
    )
    ap.add_argument("campaign", nargs="?", type=Path, help="campaign directory (draft-build mode)")
    ap.add_argument("--output", type=Path, help="directory for draft artifacts (draft-build mode)")
    ap.add_argument("--size", type=int, default=200)
    ap.add_argument("--frozen", type=Path, default=DEFAULT_FROZEN_PATH,
                    help="frozen oracle path (default: _src/tests/fixtures/spec_extraction/benchmark.json)")
    ap.add_argument("--compare", type=Path, help="candidate JSON compared against the frozen oracle")
    args = ap.parse_args()
    frozen_path = args.frozen
    if args.campaign is not None:
        if args.output is None:
            ap.error("--output is required when building a draft")
        try:
            return build_draft(args.campaign, args.output, args.size, frozen_path)
        except FrozenOverwriteError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
            return 2
    try:
        if args.compare is not None:
            frozen = load_frozen(frozen_path)
            report = compare_to_frozen(frozen, load_candidate_records(args.compare))
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["ok"] else 2
        print(json.dumps(check_report(frozen_path), indent=2))
        return 0
    except FrozenOracleError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
