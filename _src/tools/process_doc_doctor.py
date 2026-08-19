#!/usr/bin/env python3
"""Read-only consistency check for the process documentation corpus.

Answers the question a QA reviewer would otherwise answer by hand: is the
written process actually reachable, indexed and cross-linked, or has a rule been
added that no other document knows about?

It checks structure, not truth. It cannot tell whether a process is *lived* --
only whether the documents that define it hang together. It never repairs
anything, never writes, and by default never fails a build: findings are
advisory. Wiring it into a blocking gate is a decision with reach beyond one
work unit and therefore needs a recorded decision (see `TK-2` in
docs/pipeline/process-roles.md). This is the same coupling mistake that Task
0038-03 made and that Feature 0040 exists to prevent.

Usage:
    python3 _src/tools/process_doc_doctor.py            # human summary
    python3 _src/tools/process_doc_doctor.py --json     # machine readable
    python3 _src/tools/process_doc_doctor.py --strict   # exit 1 on findings
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Authority documents: binding instruction text.
AUTHORITY = ["AGENTS.md", "SANDBOX.md", "PRIVILEGED.md", "CLAUDE.md", "TODO.md"]
# Process documentation and the decision/analysis archive.
PIPELINE_DIR = Path("docs/pipeline")
DOSSIER_DIR = Path("docs/dossiers")
INDEX = PIPELINE_DIR / "README.md"

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
DEC_DEF_RE = re.compile(r"^#{1,6}\s+`?(DEC-[A-Z0-9]+-\d+)`?", re.M)
DEC_REF_RE = re.compile(r"`?(DEC-[A-Z0-9]+-\d+)`?")

RULES = {
    "DOC001": ("error", "Relative link target does not exist"),
    "DOC002": ("info", "Pipeline index does not list every process document"),
    "DOC003": ("warning", "Process document is cited by authority text but anchors itself in none"),
    "DOC004": ("warning", "Process document is referenced by nothing"),
    "DOC005": ("warning", "Decision record is defined but referenced nowhere else"),
}


def _docs() -> list[Path]:
    out = [Path(p) for p in AUTHORITY if (ROOT / p).is_file()]
    for d in (PIPELINE_DIR, DOSSIER_DIR):
        if (ROOT / d).is_dir():
            out.extend(sorted(p.relative_to(ROOT) for p in (ROOT / d).glob("*.md")))
    return out


def _finding(rule, path, message, line=None):
    sev, title = RULES[rule]
    f = {"rule": rule, "severity": sev, "title": title, "path": str(path), "message": message}
    if line is not None:
        f["line"] = line
    return f


def scan(root: Path = ROOT) -> dict:
    docs = _docs()
    text = {}
    for d in docs:
        try:
            text[d] = (root / d).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return {"ok": False, "error": f"{d}: {exc}", "findings": []}

    findings = []
    # links[source] = set of resolved targets (repo-relative, as Path)
    links: dict[Path, set[Path]] = {}
    for d in docs:
        targets = set()
        for m in LINK_RE.finditer(text[d]):
            raw = m.group(1)
            if raw.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (root / d).parent.joinpath(raw).resolve()
            try:
                rel = resolved.relative_to(root)
            except ValueError:
                continue  # escapes the repo; not our concern here
            targets.add(rel)
            if not resolved.exists():
                line = text[d].count("\n", 0, m.start()) + 1
                findings.append(_finding("DOC001", d, f"link target {raw!r} does not exist", line))
        links[d] = targets

    # DOC002: index coverage, reported once. The index is curated by design, so a
    # per-document finding would drown every other signal; the count is the point.
    indexed = links.get(INDEX, set())
    pipeline_docs = [d for d in docs if d.parent == PIPELINE_DIR and d != INDEX]
    missing = sorted(str(d.name) for d in pipeline_docs if d not in indexed)
    if missing:
        shown = ", ".join(missing[:5]) + (f", … (+{len(missing) - 5})" if len(missing) > 5 else "")
        findings.append(_finding(
            "DOC002", INDEX,
            f"{len(missing)} of {len(pipeline_docs)} process documents are not listed: {shown}"))

    # DOC003: a process document cited by binding instruction text should be able
    # to lead a reader back into that corpus. Full N:N reciprocity is NOT required
    # -- a subordinate document need not link to every document that cites it.
    authority = [Path(p) for p in AUTHORITY]
    authority_set = set(authority)
    for d in pipeline_docs:
        citers = sorted(str(a) for a in authority if d in links.get(a, set()))
        if not citers:
            continue
        if not (links.get(d, set()) & authority_set):
            findings.append(_finding(
                "DOC003", d,
                f"cited by {', '.join(citers)} but links to no authority document"))

    # DOC004: process documents nothing points at
    referenced = set()
    for src, targets in links.items():
        for t in targets:
            if t != src:
                referenced.add(t)
    for d in docs:
        if d.parent != PIPELINE_DIR or d == INDEX:
            continue
        if d not in referenced:
            findings.append(_finding("DOC004", d, "no document links to it"))

    # DOC005: decision records defined but never cited elsewhere
    defined = {}
    for d in docs:
        for m in DEC_DEF_RE.finditer(text[d]):
            defined.setdefault(m.group(1), d)
    for dec, home in defined.items():
        cited = any(dec in text[d] for d in docs if d != home)
        if not cited:
            findings.append(_finding("DOC005", home, f"decision {dec} is cited by no other document"))

    order = {"error": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda f: (order[f["severity"]], f["rule"], f["path"]))
    return {
        "ok": True,
        "schema": "autodocs-process-doc-doctor@v1",
        "scanned": [str(d) for d in docs],
        "counts": {
            "documents": len(docs),
            "findings": len(findings),
            "errors": sum(1 for f in findings if f["severity"] == "error"),
        },
        "findings": findings,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--strict", action="store_true", help="exit 1 when findings exist")
    ap.add_argument("--root", default=str(ROOT), help="repository root")
    args = ap.parse_args(argv)

    report = scan(Path(args.root).resolve())
    if not report["ok"]:
        print(f"process_doc_doctor: {report['error']}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        c = report["counts"]
        print(f"scanned {c['documents']} documents, {c['findings']} finding(s), {c['errors']} error(s)")
        for f in report["findings"]:
            loc = f"{f['path']}:{f['line']}" if "line" in f else f["path"]
            print(f"  [{f['severity']:7s}] {f['rule']} {loc} — {f['message']}")
        if not report["findings"]:
            print("  process documentation is internally consistent")
    return 1 if (args.strict and report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
