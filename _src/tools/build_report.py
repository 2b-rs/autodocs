#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_report.py — Orchestrates and publishes traceable publication build reports.

Tasks:
  - 0001-07: Combines merge, diagram, generate, and validate subreports into a
    single combined publication report (output/build-reports/combined-<timestamp>.json)
    conforming to docs/pipeline/build-report-schema.md.
  - 0001-08 / 0001-09: Generates the canonical browsable HTML report page model
    (_src/sources/pages/build-reports.json) with links to archived logs,
    referenced artifacts, and per-stage counters.

CLI:
    python3 _src/tools/build_report.py combine [--run-archive-ref=<ref>]
    python3 _src/tools/build_report.py publish [--run-archive-ref=<ref>]
"""
import glob
import html
import json
import os
import sys
import time
from pathlib import Path

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
REPORTS_DIR = os.path.join(ROOT, "output", "build-reports")
PAGE_MODEL = os.path.join(SRC, "sources", "pages", "build-reports.json")


def _esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def load_latest_subreports(since_ts=None):
    """Load the latest reports for each producer kind."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    by_kind = {}
    pattern = os.path.join(REPORTS_DIR, "*.json")
    for f in sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True):
        if os.path.basename(f).startswith("combined-"):
            continue
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            kind = data.get("report_kind")
            if kind and kind not in by_kind:
                if since_ts is None or data.get("started_at", "") >= since_ts:
                    by_kind[kind] = data
        except Exception:
            continue
    return by_kind


def combine_reports(run_archive_ref=None):
    """Combine latest producer subreports into a unified canonical build-report."""
    subreports = load_latest_subreports()
    now = time.time()
    started_at = min((r.get("started_at") for r in subreports.values() if r.get("started_at")),
                     default=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)))
    finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))

    all_inputs = []
    all_changed = []
    all_findings = []
    by_stage = {}
    overall_exit_code = 0

    for kind in ("i18n_merge", "i18n_diagrams", "html_generate", "validate"):
        sub = subreports.get(kind, {})
        counts = sub.get("counts", {})
        by_stage[kind] = counts
        for inp in sub.get("inputs", []):
            if inp not in all_inputs:
                all_inputs.append(inp)
        for art in sub.get("changed_artifacts", []):
            if art not in all_changed:
                all_changed.append(art)
        all_findings.extend(sub.get("findings", []))
        if sub.get("exit_code", 0) != 0:
            overall_exit_code = max(overall_exit_code, sub.get("exit_code", 1))

    ref = run_archive_ref or os.environ.get("RUN_ARCHIVE_REF")
    if not ref:
        # Check if subreports provided a run_archive_ref
        for sub in subreports.values():
            if sub.get("run_archive_ref"):
                ref = sub.get("run_archive_ref")
                break

    combined = {
        "schema_version": "1.0",
        "report_kind": "combined",
        "tool": "build_report.py",
        "command": "build_report.py combine",
        "inputs": all_inputs,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_s": round(now - time.mktime(time.strptime(started_at, "%Y-%m-%dT%H:%M:%SZ")) if "T" in started_at else 0.0, 3),
        "exit_code": overall_exit_code,
        "changed_artifacts": all_changed,
        "counts": {
            "by_stage": by_stage,
            "overall_success": overall_exit_code == 0,
        },
        "findings": all_findings,
        "run_archive_ref": ref,
    }

    out_file = os.path.join(REPORTS_DIR, f"combined-{int(now)}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=1)

    return combined, out_file


def generate_report_page(combined_report=None, run_archive_ref=None):
    """Generate the static page model for build-reports.html."""
    if combined_report is None:
        # Load most recent combined report or build one
        combined_files = sorted(glob.glob(os.path.join(REPORTS_DIR, "combined-*.json")),
                                key=os.path.getmtime, reverse=True)
        if combined_files:
            with open(combined_files[0], encoding="utf-8") as f:
                combined_report = json.load(f)
        else:
            combined_report, _ = combine_reports(run_archive_ref)

    stage_counts = (combined_report.get("counts") or {}).get("by_stage", {})
    overall_success = (combined_report.get("counts") or {}).get("overall_success", True)
    ref = combined_report.get("run_archive_ref") or "N/A"
    started = combined_report.get("started_at", "")
    finished = combined_report.get("finished_at", "")
    findings = combined_report.get("findings", [])

    # Format runner archive link / info
    if ref != "N/A" and os.path.exists(os.path.join(ROOT, ref)):
        archive_html = f'<code><a href="{_esc(ref)}">{_esc(ref)}</a></code>'
    else:
        archive_html = f'<code>{_esc(ref)}</code>'

    html_parts = []
    html_parts.append("""<style>
.br-head{padding:1.15rem 1.35rem;border:1px solid #d9dce3;border-radius:14px;background:linear-gradient(135deg,#f7f8ff,#eef5ff);margin:1rem 0 1.4rem}
.br-meta{display:flex;gap:.5rem;flex-wrap:wrap;margin:.6rem 0 0}
.br-meta span{background:#fff;border:1px solid #d7dcea;border-radius:999px;padding:.28rem .66rem;font-size:.88rem}
.br-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.8rem;margin:1rem 0 1.5rem}
.br-grid article{border:1px solid #d9dce3;border-radius:12px;padding:.95rem;background:#fff;box-shadow:0 3px 14px rgba(20,40,80,.06)}
.br-grid span,.br-grid small{display:block;color:#596274}
.br-grid strong{display:block;font-size:1.7rem;margin:.18rem 0;font-variant-numeric:tabular-nums}
.br-section{border:1px solid #d9dce3;border-radius:10px;margin:.8rem 0;background:#fff;overflow:hidden}
.br-section summary{display:flex;justify-content:space-between;gap:1rem;padding:.8rem 1rem;cursor:pointer;background:#f7f8fa}
.br-table-wrap{overflow:auto;max-height:42rem}
.br-table{border-collapse:collapse;width:100%;font-size:.9rem}
.br-table th{position:sticky;top:0;background:#eef1f6;text-align:left;z-index:1}
.br-table th,.br-table td{padding:.5rem .7rem;border-bottom:1px solid #e4e7ec;vertical-align:top}
.br-badge-ok{color:#166534;background:#dcfce7;border-radius:999px;padding:.15rem .6rem;font-weight:bold}
.br-badge-err{color:#991b1b;background:#fee2e2;border-radius:999px;padding:.15rem .6rem;font-weight:bold}
</style>""")

    status_badge = '<span class="br-badge-ok">ERFOLG</span>' if overall_success else '<span class="br-badge-err">FEHLER</span>'
    html_parts.append(f"""<h1>Traceable Build- & Publikations-Report</h1>
<section class="br-head">
<p>Zusammenfassender Veröffentlichungs- und Validierungsbericht der Dokumentations-Pipeline. Jeder Lauf aggregiert die Befunde aus Übersetzung, Diagrammerzeugung, HTML-Generierung und Konsistenzprüfung.</p>
<p class="br-meta">
<span>Status: <strong>{status_badge}</strong></span>
<span>Start: <strong>{_esc(started)}</strong></span>
<span>Ende: <strong>{_esc(finished)}</strong></span>
<span>Runner-Referenz: {archive_html}</span>
</p>
</section>""")

    # Grid metrics
    gen_counts = stage_counts.get("html_generate", {})
    val_counts = stage_counts.get("validate", {})
    diag_counts = stage_counts.get("i18n_diagrams", {})
    merge_counts = stage_counts.get("i18n_merge", {})

    de_pages = (gen_counts.get("pages_generated_per_lang") or {}).get("de", 0)
    checks_n = val_counts.get("checks_performed", 0)
    findings_n = len(findings)

    html_parts.append(f"""<h2 class="sect">Pipeline-Kennzahlen</h2>
<div class="br-grid">
<article><span>Generierte Seiten</span><strong>{de_pages}</strong><small>im kanonischen Hauptbaum (de)</small></article>
<article><span>Qualitätsprüfungen</span><strong>{checks_n}</strong><small>automatisierte Prüfschritte</small></article>
<article><span>Befunde & Warnungen</span><strong>{findings_n}</strong><small>in der aktuellen Validierung</small></article>
<article><span>Diagramm-Quellen</span><strong>{diag_counts.get('sources_considered', 0)}</strong><small>bearbeitet / synchronisiert</small></article>
</div>""")

    # Stage details
    html_parts.append("""<h2 class="sect">Stufen-Details & Sub-Reports</h2>""")

    # Validation findings table
    html_parts.append(f"""<details class="br-section" open>
<summary><strong>Validierungs-Befunde ({len(findings)})</strong></summary>
<div class="br-table-wrap">
<table class="br-table">
<thead><tr><th>Kategorie</th><th>Schweregrad</th><th>Nachricht</th><th>Referenz</th></tr></thead>
<tbody>""")
    if findings:
        for f in findings:
            cat = _esc(f.get("category", "-"))
            sev = _esc(f.get("severity", "-"))
            msg = _esc(f.get("message", "-"))
            ref_val = _esc(f.get("ref", "-"))
            html_parts.append(f"<tr><td><code>{cat}</code></td><td>{sev}</td><td>{msg}</td><td>{ref_val}</td></tr>")
    else:
        html_parts.append("<tr><td colspan=\"4\">Keine offenen Befunde. Alle Validierungsprüfungen erfolgreich.</td></tr>")
    html_parts.append("</tbody></table></div></details>")

    # Stage breakdown
    html_parts.append("""<details class="br-section">
<summary><strong>Aggregierte Zähler je Pipeline-Stufe</strong></summary>
<div class="br-table-wrap">
<table class="br-table">
<thead><tr><th>Pipeline-Stufe</th><th>Zähler & Kennzahlen</th></tr></thead>
<tbody>""")
    for stage_name, c in stage_counts.items():
        html_parts.append(f"<tr><td><strong>{_esc(stage_name)}</strong></td><td><code>{_esc(json.dumps(c, ensure_ascii=False))}</code></td></tr>")
    html_parts.append("</tbody></table></div></details>")

    page_data = {
        "file": "build-reports.html",
        "title": "Build- & Publikations-Bericht",
        "body_class": None,
        "nolang": True,
        "nav_html": "<a href=\"index.html\">Start</a> / <a href=\"process.html\">Prozess</a> / Build-Bericht",
        "footer": "extracted",
        "main_lead": "",
        "main": [
            {
                "t": "html",
                "html": "".join(html_parts)
            }
        ]
    }

    os.makedirs(os.path.dirname(PAGE_MODEL), exist_ok=True)
    with open(PAGE_MODEL, "w", encoding="utf-8") as f:
        json.dump(page_data, f, ensure_ascii=False, indent=1)

    return PAGE_MODEL


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "combine"
    ref = None
    for a in args:
        if a.startswith("--run-archive-ref="):
            ref = a.split("=", 1)[1]

    if cmd == "combine":
        combined, out = combine_reports(ref)
        print(f"Aggregierter Build-Report geschrieben: {out} (Exit-Code {combined['exit_code']})")
    elif cmd in ("publish", "page"):
        combined, _ = combine_reports(ref)
        page_path = generate_report_page(combined, ref)
        print(f"Seitenmodell fuer Build-Report erzeugt: {page_path}")
    else:
        print(f"Unbekannter Befehl: {cmd}. Erlaubt: combine, publish")
        sys.exit(1)


if __name__ == "__main__":
    main()
