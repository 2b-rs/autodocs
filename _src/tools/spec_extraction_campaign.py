#!/usr/bin/env python3
"""Reproducible side-by-side PDF extraction campaign reports.

The campaign runner intentionally performs no PDF extraction itself.  It emits
an executable job manifest for run.sh and combines backend JSON artifacts after
all independent document/backend workers have finished.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]
sys.path.insert(0, str(TOOLS))
import spec_scrape

BACKENDS = ("pypdf", "builtin")
FIELDS = ("heading", "requirement_text", "Description", "Rationale", "AppliesTo",
          "Dependencies", "Use Case", "Supporting Material")


def _stable_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_revision() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _documents(pdf_dir: Path, docs: list[str] | None, rs_docs: bool) -> list[Path]:
    selected = list(docs or [])
    if rs_docs:
        selected.extend(value[1] for value in spec_scrape.RS_DOCS.values())
    return spec_scrape.discover_pdfs(pdf_dir, docs=list(dict.fromkeys(selected)) or None)


def create(campaign_dir: Path, pdf_dir: Path, documents: list[Path], pattern: str) -> dict:
    campaign_dir.mkdir(parents=True, exist_ok=True)
    (campaign_dir / "raw").mkdir(exist_ok=True)
    (campaign_dir / "logs").mkdir(exist_ok=True)
    jobs = []
    docs = []
    for pdf in documents:
        docs.append({"name": pdf.stem, "path": str(pdf), "sha256": _sha256(pdf),
                     "size": pdf.stat().st_size})
        for backend in BACKENDS:
            output = campaign_dir / "raw" / f"{pdf.stem}.{backend}.json"
            log = campaign_dir / "logs" / f"{pdf.stem}.{backend}.log"
            jobs.append({
                "document": pdf.stem,
                "backend": backend,
                "output": str(output),
                "log": str(log),
                "argv": [sys.executable, str(TOOLS / "spec_scrape.py"), "props",
                         "--pdf-dir", str(pdf_dir), "--doc", pdf.stem,
                         "--pattern", pattern, "--backend", backend, "--json"],
            })
    manifest = {
        "schema": 1,
        "campaign": campaign_dir.name,
        "created_by": "spec_extraction_campaign.py",
        "git_revision": _git_revision(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pattern": pattern,
        "backends": list(BACKENDS),
        "documents": docs,
        "jobs": jobs,
    }
    (campaign_dir / "manifest.json").write_text(_stable_json(manifest), encoding="utf-8")
    return manifest


def _value(record: dict | None, field: str) -> str:
    if not record:
        return ""
    if field in ("heading", "requirement_text"):
        return str(record.get(field) or "")
    return str((record.get("props") or {}).get(field) or "")


def _normalized(value: str, field: str | None = None) -> str:
    """Normalize backend-only layout differences without hiding content changes."""
    value = " ".join(value.split())
    if field == "AppliesTo":
        # pypdf inserts a space before commas in AUTOSAR platform lists while
        # the builtin backend does not; punctuation carries no semantics here.
        value = re.sub(r"\s*,\s*", ",", value)
    return value


def compare_records(left: dict, right: dict) -> tuple[list[dict], dict]:
    rows = []
    ids = sorted(set(left) | set(right))
    totals = Counter()
    for rid in ids:
        a, b = left.get(rid), right.get(rid)
        if not a or not b:
            status = "only-pypdf" if a else "only-builtin"
            similarity = 0.0
        else:
            values_a = [_normalized(_value(a, field), field) for field in FIELDS]
            values_b = [_normalized(_value(b, field), field) for field in FIELDS]
            if values_a == values_b:
                status, similarity = "normalized", 1.0
            else:
                status = "different"
                similarity = SequenceMatcher(None, "\n".join(values_a),
                                             "\n".join(values_b)).ratio()
        totals[status] += 1
        field_diffs = []
        for field in FIELDS:
            av, bv = _value(a, field), _value(b, field)
            if _normalized(av, field) != _normalized(bv, field):
                field_diffs.append({"field": field, "pypdf": av, "builtin": bv,
                                    "similarity": SequenceMatcher(None, _normalized(av, field),
                                                                  _normalized(bv, field)).ratio()})
        rows.append({
            "id": rid,
            "status": status,
            "similarity": round(similarity, 6),
            "pypdf_page": a.get("page") if a else None,
            "builtin_page": b.get("page") if b else None,
            "field_differences": field_diffs,
        })
    summary = {"total_ids": len(ids), **dict(sorted(totals.items()))}
    return rows, summary


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, documents: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("document", "id", "status", "similarity",
                                                    "pypdf_page", "builtin_page", "different_fields"))
        writer.writeheader()
        for document in documents:
            for row in document["records"]:
                writer.writerow({
                    "document": document["document"], "id": row["id"],
                    "status": row["status"], "similarity": row["similarity"],
                    "pypdf_page": row["pypdf_page"], "builtin_page": row["builtin_page"],
                    "different_fields": ",".join(x["field"] for x in row["field_differences"]),
                })


def _write_html(path: Path, documents: list[dict], summary: dict) -> None:
    out = ["<!doctype html><meta charset=utf-8><title>Extraction campaign</title>",
           "<style>body{font:14px system-ui;margin:2rem}table{border-collapse:collapse;width:100%}th,td{border:1px solid #bbb;padding:.35rem;vertical-align:top}pre{white-space:pre-wrap;max-width:48vw}.different{background:#fff1c7}.only-pypdf,.only-builtin{background:#ffd8d8}details{margin:.2rem 0}</style>",
           f"<h1>Extraction campaign</h1><pre>{html.escape(_stable_json(summary))}</pre>"]
    for document in documents:
        out.append(f"<h2>{html.escape(document['document'])}</h2>")
        out.append("<table><tr><th>ID</th><th>Status</th><th>Similarity</th><th>Side-by-side fields</th></tr>")
        for row in document["records"]:
            details = []
            for diff in row["field_differences"]:
                details.append("<details><summary>%s (%.3f)</summary><table><tr><th>pypdf</th><th>builtin</th></tr><tr><td><pre>%s</pre></td><td><pre>%s</pre></td></tr></table></details>" %
                               (html.escape(diff["field"]), diff["similarity"],
                                html.escape(diff["pypdf"]), html.escape(diff["builtin"])))
            out.append('<tr class="%s"><td>%s</td><td>%s</td><td>%.3f</td><td>%s</td></tr>' %
                       (row["status"], html.escape(row["id"]), row["status"],
                        row["similarity"], "".join(details) or "agreement"))
        out.append("</table>")
    path.write_text("\n".join(out), encoding="utf-8")


def report(campaign_dir: Path) -> dict:
    manifest = _load(campaign_dir / "manifest.json")
    documents = []
    total = Counter()
    failures = []
    for document in manifest["documents"]:
        name = document["name"]
        paths = {backend: campaign_dir / "raw" / f"{name}.{backend}.json" for backend in BACKENDS}
        missing = [backend for backend, path in paths.items() if not path.is_file()]
        if missing:
            failures.append({"document": name, "missing_backends": missing})
            continue
        rows, summary = compare_records(_load(paths["pypdf"]), _load(paths["builtin"]))
        documents.append({"document": name, "summary": summary, "records": rows})
        total.update(summary)
    scorecard = {"schema": 1, "campaign": manifest["campaign"],
                 "documents_complete": len(documents), "failures": failures,
                 "summary": dict(total)}
    payload = {"scorecard": scorecard, "documents": documents}
    (campaign_dir / "comparison.json").write_text(_stable_json(payload), encoding="utf-8")
    (campaign_dir / "scorecard.json").write_text(_stable_json(scorecard), encoding="utf-8")
    _write_csv(campaign_dir / "comparison.csv", documents)
    _write_html(campaign_dir / "comparison.html", documents, scorecard)
    return scorecard


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    create_parser = sub.add_parser("create")
    create_parser.add_argument("campaign_dir", type=Path)
    create_parser.add_argument("--pdf-dir", type=Path, default=spec_scrape.PDF_CACHE)
    create_parser.add_argument("--doc", action="append")
    create_parser.add_argument("--rs-docs", action="store_true")
    create_parser.add_argument("--pattern", default=r"^RS_")
    report_parser = sub.add_parser("report")
    report_parser.add_argument("campaign_dir", type=Path)
    args = parser.parse_args(argv)
    if args.action == "create":
        documents = _documents(args.pdf_dir, args.doc, args.rs_docs)
        result = create(args.campaign_dir, args.pdf_dir, documents, args.pattern)
        print(_stable_json({"documents": len(result["documents"]), "jobs": len(result["jobs"])}), end="")
    else:
        print(_stable_json(report(args.campaign_dir)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
