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
    python3 _src/tools/build_report.py combine --no-ledger
    python3 _src/tools/build_report.py mint-ref
        Mints and prints a distinguishably marked fallback RUN_ARCHIVE_REF
        (see mint_manual_run_archive_ref) for a manual/out-of-runner build
        (0043-01), so `combine` can still correlate its cohort. Export it
        before invoking the producers, e.g.:
            export RUN_ARCHIVE_REF="$(python3 _src/tools/build_report.py mint-ref)"

  - 0043-02: `combine` and `publish` append exactly one entry per publication
    run to the tracked append-only build ledger `docs/evidence/build-ledger.jsonl`
    (see build_ledger.py and docs/pipeline/build-ledger.md). `--no-ledger`
    suppresses the append for a diagnostic re-run that must not enter the
    permanent build history. Such a diagnostic combined report is machine-marked
    with `"diagnostic_no_ledger": true` so `validate.py`'s freshness check can
    tell an expressly diagnostic cohort from a publication cohort whose ledger
    append simply failed (0043-04 / DEC-0043-003).
  - 0043-04: `publish` (and the `provenance` command) write the structured
    `publication_provenance` object into the page model, binding the published
    page to exactly one schema-valid ledger entry. `validate.py` compares that
    binding against the ledger and the local cohorts and reports staleness as
    an error finding.

CLI (0043-04):
    python3 _src/tools/build_report.py provenance
        Recompute only the `publication_provenance` object of the existing page
        model from the tracked ledger, leaving the rendered body untouched. This
        is the supported way to refresh the binding when the raw combined report
        of the recorded run is no longer present (it lives under git-ignored
        `output/` per DEC-0043-001), and it is idempotent.
"""
import datetime
import glob
import html
from report_page_header import report_page_header
import json
import math
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ledger  # noqa: E402  (same-directory sibling module)

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
REPORTS_DIR = os.path.join(ROOT, "output", "build-reports")
PAGE_MODEL = os.path.join(SRC, "sources", "pages", "build-reports.json")
REQUIRED_STAGES = ("i18n_merge", "i18n_diagrams", "html_generate", "validate")
ALLOWED_FINDING_SEVERITIES = frozenset(("info", "warning", "error"))
SCHEMA_VERSION = "1.0"

# 0043-04: schema version of the `publication_provenance` object written into
# the page model. Bump only on a breaking change; validate.py refuses an
# unknown version rather than guessing its meaning.
PROVENANCE_SCHEMA_VERSION = "1.0"
PROVENANCE_KEY = "publication_provenance"

# Runner-issued refs name a real output/run-archive/run-<timestamp>-n<seq>
# pair (see runner-host/run-loop.sh). A build run outside the runner (the
# manual WARTUNG.md path) has no such pair to name, but `combine` still
# requires a non-empty run_archive_ref shared by every subreport in the
# cohort (0043-01: "combine cannot starve on missing cohorts"). This prefix
# marks a minted fallback so it can never be mistaken for, or collide with, a
# real runner-issued ref.
MANUAL_REF_PREFIX = "manual-"

# A ledger entry's combined_report_ref names output/build-reports/combined-*.json,
# which DEC-0043-001 keeps permanently git-ignored — it never reaches the published
# site. Rendering it as a link therefore produces a dead link on every history row
# (0043-03, finding F-BELANNA-0043-03-01). Following the same idea as
# MANUAL_REF_PREFIX above — mark what cannot resolve instead of pretending it does —
# such a ref is rendered as plain text that still shows its value. Only a ref naming
# a *tracked* (published) path is rendered as a link; the local, git-ignored
# output/ tree is deliberately not consulted, since a check that passes only because
# this machine happens to hold an artifact is exactly the defect being fixed.
_TRACKED_PATHS_CACHE = {}


def _tracked_paths(root=None):
    """Set of repository-relative paths tracked by Git, cached per root.

    Fails closed: if Git cannot be consulted, the set is empty and nothing is
    rendered as a link.
    """
    key = os.path.abspath(root or ROOT)
    if key not in _TRACKED_PATHS_CACHE:
        try:
            completed = subprocess.run(
                ["git", "-C", key, "ls-files", "-z"],
                capture_output=True, text=True, timeout=60, check=True,
            )
            paths = frozenset(p for p in completed.stdout.split("\0") if p)
        except (OSError, subprocess.SubprocessError):
            paths = frozenset()
        _TRACKED_PATHS_CACHE[key] = paths
    return _TRACKED_PATHS_CACHE[key]


def _ref_is_published(ref, root=None):
    """True only when `ref` names a tracked file, i.e. one that exists on the
    published site and can therefore be linked without producing a dead link."""
    if not isinstance(ref, str) or not ref.strip():
        return False
    candidate = ref.strip()
    if os.path.isabs(candidate):
        return False
    candidate = os.path.normpath(candidate)
    if candidate.startswith(".."):
        return False
    return candidate in _tracked_paths(root)


def _esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def mint_manual_run_archive_ref():
    """Mint a fallback RUN_ARCHIVE_REF for a publication run executed outside
    the runner lifecycle (runner-host/run-loop.sh).

    The result is distinguishably marked with MANUAL_REF_PREFIX so it is never
    indistinguishable from a real runner-issued ref, which always names an
    actual output/run-archive/run-<timestamp>-n<seq> pair. Uniqueness across
    concurrent/successive manual runs comes from a UTC timestamp plus 4 bytes
    (8 hex chars) of CSPRNG entropy from `secrets`.
    """
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{MANUAL_REF_PREFIX}{stamp}-{secrets.token_hex(4)}"


def _has_run_archive_ref(value):
    return isinstance(value, str) and bool(value.strip())


def _parse_utc_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        return None
    return parsed.replace(tzinfo=datetime.timezone.utc)


def _is_string_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _validate_subreport(data, selected_ref):
    errors = []

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION!r}")

    kind = data.get("report_kind")
    if kind not in REQUIRED_STAGES:
        errors.append(f"report_kind must be one of {REQUIRED_STAGES!r}")

    for field in ("tool", "command"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    for field in ("inputs", "changed_artifacts"):
        if not _is_string_list(data.get(field)):
            errors.append(f"{field} must be an array of strings")

    started_at = _parse_utc_timestamp(data.get("started_at"))
    finished_at = _parse_utc_timestamp(data.get("finished_at"))
    if started_at is None:
        errors.append("started_at must be a strict UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)")
    if finished_at is None:
        errors.append("finished_at must be a strict UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)")
    if started_at is not None and finished_at is not None and finished_at < started_at:
        errors.append("finished_at must not precede started_at")

    duration_s = data.get("duration_s")
    valid_duration = (
        isinstance(duration_s, (int, float))
        and not isinstance(duration_s, bool)
        and (not isinstance(duration_s, float) or math.isfinite(duration_s))
        and duration_s >= 0
    )
    if not valid_duration:
        errors.append("duration_s must be a finite non-negative number")

    exit_code = data.get("exit_code")
    valid_exit_code = (
        isinstance(exit_code, int)
        and not isinstance(exit_code, bool)
        and 0 <= exit_code <= 255
    )
    if not valid_exit_code:
        errors.append("exit_code must be an integer from 0 through 255")

    if not isinstance(data.get("counts"), dict):
        errors.append("counts must be an object")

    findings = data.get("findings")
    has_error_finding = False
    if not isinstance(findings, list):
        errors.append("findings must be an array of structured findings")
    else:
        for index, finding in enumerate(findings):
            prefix = f"findings[{index}]"
            if not isinstance(finding, dict):
                errors.append(f"{prefix} must be an object")
                continue
            category = finding.get("category")
            severity = finding.get("severity")
            message = finding.get("message")
            if not isinstance(category, str) or not category.strip():
                errors.append(f"{prefix}.category must be a non-empty string")
            if not isinstance(severity, str) or severity not in ALLOWED_FINDING_SEVERITIES:
                errors.append(
                    f"{prefix}.severity must be one of {tuple(sorted(ALLOWED_FINDING_SEVERITIES))!r}"
                )
            if not isinstance(message, str) or not message.strip():
                errors.append(f"{prefix}.message must be a non-empty string")
            if "ref" in finding and not isinstance(finding["ref"], str):
                errors.append(f"{prefix}.ref must be a string when present")
            if severity == "error" and isinstance(message, str) and message.strip():
                has_error_finding = True

    report_ref = data.get("run_archive_ref")
    if not _has_run_archive_ref(report_ref):
        errors.append("run_archive_ref must be a non-empty string for a correlated producer report")
    elif report_ref != selected_ref:
        errors.append(f"run_archive_ref must exactly match the selected cohort {selected_ref!r}")

    if valid_exit_code and exit_code != 0 and not has_error_finding:
        errors.append("nonzero exit_code requires at least one error finding with a message")

    return errors


def load_latest_subreports(since_ts=None, run_archive_ref=None):
    """Load schema-valid producer reports from one exact non-empty run cohort."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    candidates = []
    findings = []
    pattern = os.path.join(REPORTS_DIR, "*.json")
    for f in sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True):
        if os.path.basename(f).startswith("combined-"):
            continue
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
            if not isinstance(data, dict):
                raise ValueError("top-level JSON value must be an object")
        except (OSError, UnicodeError, ValueError) as exc:
            findings.append({
                "category": "malformed-build-report",
                "severity": "error",
                "message": f"{os.path.basename(f)} is not a readable report: {exc}",
                "ref": os.path.relpath(f, ROOT),
            })
            continue
        candidates.append((f, data))

    selected_ref = run_archive_ref
    if selected_ref is None:
        selected_ref = next(
            (data.get("run_archive_ref") for _, data in candidates
             if _has_run_archive_ref(data.get("run_archive_ref"))),
            None,
        )
    elif not _has_run_archive_ref(selected_ref):
        findings.append({
            "category": "malformed-build-report",
            "severity": "error",
            "message": "Requested run_archive_ref must be a non-empty string; no reports were selected.",
            "ref": "run_archive_ref",
        })
        return {}, findings

    if selected_ref is None:
        findings.append({
            "category": "malformed-build-report",
            "severity": "error",
            "message": (
                "No producer report has a non-empty run_archive_ref; identity-less reports "
                "cannot form a correlated build."
            ),
            "ref": os.path.relpath(REPORTS_DIR, ROOT),
        })
        return {}, findings

    by_kind = {}
    for f, data in candidates:
        if data.get("run_archive_ref") != selected_ref:
            continue
        validation_errors = _validate_subreport(data, selected_ref)
        if validation_errors:
            findings.append({
                "category": "malformed-build-report",
                "severity": "error",
                "message": (
                    f"{os.path.basename(f)} violates the build-report schema: "
                    + "; ".join(validation_errors)
                ),
                "ref": os.path.relpath(f, ROOT),
            })
            continue
        if since_ts is not None and data["started_at"] < since_ts:
            continue
        kind = data["report_kind"]
        if kind not in by_kind:
            by_kind[kind] = data
    return by_kind, findings


def combine_reports(run_archive_ref=None, diagnostic_no_ledger=False):
    """Combine one correlated producer-report cohort into a canonical report."""
    requested_ref = run_archive_ref if run_archive_ref is not None else os.environ.get("RUN_ARCHIVE_REF")
    subreports, load_findings = load_latest_subreports(run_archive_ref=requested_ref)
    if _has_run_archive_ref(requested_ref):
        ref = requested_ref
    else:
        ref = next(
            (sub.get("run_archive_ref") for sub in subreports.values()
             if _has_run_archive_ref(sub.get("run_archive_ref"))),
            None,
        )
    now = time.time()
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
    valid_started_at = []
    for report in subreports.values():
        value = report.get("started_at")
        try:
            time.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError):
            continue
        valid_started_at.append(value)
    started_at = min(valid_started_at, default=now_iso)
    finished_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))

    all_inputs = []
    all_changed = []
    all_findings = list(load_findings)
    by_stage = {}
    overall_exit_code = 1 if load_findings else 0

    for kind in REQUIRED_STAGES:
        sub = subreports.get(kind)
        if sub is None:
            by_stage[kind] = {}
            cohort = f" for run_archive_ref {ref!r}" if ref is not None else " in a correlated run cohort"
            all_findings.append({
                "category": "missing-build-stage",
                "severity": "error",
                "message": f"Required build stage {kind!r} has no report{cohort}.",
                "ref": kind,
            })
            overall_exit_code = max(overall_exit_code, 1)
            continue

        counts = sub.get("counts")
        if not isinstance(counts, dict):
            counts = {}
            all_findings.append({
                "category": "malformed-build-report",
                "severity": "error",
                "message": f"Required build stage {kind!r} has missing or invalid counts.",
                "ref": kind,
            })
            overall_exit_code = max(overall_exit_code, 1)
        by_stage[kind] = counts

        for inp in sub.get("inputs", []) if isinstance(sub.get("inputs", []), list) else []:
            if inp not in all_inputs:
                all_inputs.append(inp)
        for art in sub.get("changed_artifacts", []) if isinstance(sub.get("changed_artifacts", []), list) else []:
            if art not in all_changed:
                all_changed.append(art)

        stage_findings = sub.get("findings", [])
        if not isinstance(stage_findings, list):
            all_findings.append({
                "category": "malformed-build-report",
                "severity": "error",
                "message": f"Required build stage {kind!r} has invalid findings.",
                "ref": kind,
            })
            overall_exit_code = max(overall_exit_code, 1)
        else:
            all_findings.extend(stage_findings)

        exit_code = sub.get("exit_code")
        if isinstance(exit_code, bool) or not isinstance(exit_code, int) or not 0 <= exit_code <= 255:
            all_findings.append({
                "category": "malformed-build-report",
                "severity": "error",
                "message": f"Required build stage {kind!r} has missing or invalid exit_code.",
                "ref": kind,
            })
            overall_exit_code = max(overall_exit_code, 1)
        elif exit_code != 0:
            overall_exit_code = max(overall_exit_code, exit_code)

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
    if diagnostic_no_ledger:
        # 0043-04 / DEC-0043-003: an expressly diagnostic cohort is not a
        # publication candidate. Marking it in the combined report keeps that
        # distinction machine-readable, so a *failed* ledger append (which is
        # not diagnostic) still surfaces as a missing-ledger-entry finding.
        combined["diagnostic_no_ledger"] = True

    out_file = os.path.join(REPORTS_DIR, f"combined-{int(now)}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=1)

    return combined, out_file


def publication_provenance(ledger_path=None, rendered_run_archive_ref=None, previous=None):
    """Build the structured publication-provenance object for the page model (0043-04).

    The binding is derived from the tracked ledger alone: the newest
    schema-valid entry is *the* published run, because the ledger is the only
    configuration-managed publication evidence (`DEC-0043-001`). The raw
    combined report it pins lives under git-ignored `output/` and may be absent
    in any clean checkout, so it is never required to compute this object.

    `rendered_run_archive_ref` records which cohort the page's latest-run detail
    section was rendered from, so a page whose body and whose binding disagree
    is detectable. It is `None` when the rendered run carries no cohort identity
    (the historic backfilled run does not).
    """
    entries, findings = build_ledger.read_entries(ledger_path)
    newest = entries[-1] if entries else None
    binding = None
    if newest is not None:
        binding = {
            "recorded_at": newest.get("recorded_at"),
            "run_archive_ref": newest.get("run_archive_ref"),
            "combined_report_digest": newest.get("combined_report_digest"),
            "backfilled": bool(newest.get("backfilled")),
        }
    provenance = {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "bound_at": _utc_now_iso(),
        "ledger_ref": os.path.relpath(ledger_path or build_ledger.LEDGER_PATH, ROOT),
        "ledger_entry_count": len(entries),
        "ledger_findings_count": len(findings),
        "ledger_entry": binding,
        "rendered_run_archive_ref": rendered_run_archive_ref,
    }
    # `bound_at` is when *this* binding was established, not when the generator
    # last ran: an unchanged binding keeps its original timestamp so a repeated
    # publication of the same run produces a byte-identical tracked page model.
    if isinstance(previous, dict):
        unchanged = all(
            previous.get(field) == provenance[field]
            for field in provenance if field != "bound_at"
        )
        if unchanged and isinstance(previous.get("bound_at"), str):
            provenance["bound_at"] = previous["bound_at"]
    return provenance


def _utc_now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_page_provenance(ledger_path=None, page_model=None):
    """Refresh only `publication_provenance` in an existing page model.

    Used when the page body is current but the binding must be recomputed from
    the tracked ledger — e.g. after a backfill, or in a checkout where the raw
    combined report of the recorded run is not present. Idempotent.
    """
    target = page_model or PAGE_MODEL
    with open(target, encoding="utf-8") as f:
        page_data = json.load(f)
    previous = page_data.get(PROVENANCE_KEY)
    rendered = previous.get("rendered_run_archive_ref") if isinstance(previous, dict) else None
    page_data[PROVENANCE_KEY] = publication_provenance(ledger_path, rendered, previous)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(page_data, f, ensure_ascii=False, indent=1)
    return target


def generate_report_page(combined_report=None, run_archive_ref=None, ledger_path=None):
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
    overall_success = (combined_report.get("counts") or {}).get("overall_success", False)
    if not isinstance(overall_success, bool):
        overall_success = False
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
    html_parts.append(report_page_header(generator="_src/tools/build_report.py", data_source="docs/evidence/build-ledger.jsonl und output/build-reports/combined-*.json", purpose="Zeigt die vollständige Bauhistorie aus dem Build-Ledger sowie Details des jüngsten Laufs; die Liste ist neueste zuerst zu lesen."))
    ledger_entries, ledger_findings = build_ledger.read_entries(ledger_path)
    html_parts.append('<h2 class="sect">Build-Historie</h2>')
    html_parts.append('<p>Quelle der Historie: <code>docs/evidence/build-ledger.jsonl</code>. Die Seite wurde beim aktuellen Publikationslauf erzeugt.</p>')
    if ledger_findings:
        html_parts.append('<div class="br-section"><strong>Build-Ledger-Befunde</strong><ul>')
        for finding in ledger_findings:
            html_parts.append(f'<li><code>{_esc(finding.get("category", "-"))}</code>: {_esc(finding.get("message", "-"))}</li>')
        html_parts.append('</ul></div>')
    html_parts.append('<div class="br-table-wrap"><table class="br-table"><thead><tr><th>Zeit</th><th>Ergebnis</th><th>Ref</th><th>Kennzahlen</th><th>Details</th></tr></thead><tbody>')
    for entry in reversed(ledger_entries):
        badge = '<span class="br-badge-ok">ERFOLG</span>' if entry.get("overall_success") else '<span class="br-badge-err">FEHLER</span>'
        counts = entry.get("counts_by_stage") or {}
        pages = ((counts.get("html_generate") or {}).get("pages_generated_per_lang") or {}).get("de", 0)
        checks = (counts.get("validate") or {}).get("checks_performed", 0)
        diagrams = (counts.get("i18n_diagrams") or {}).get("sources_considered", 0)
        detail_ref = entry.get("combined_report_ref") or ""
        if not detail_ref:
            detail = "–"
        elif _ref_is_published(detail_ref):
            detail = f'<a href="{_esc(detail_ref)}">JSON-Details</a>'
        else:
            # Not published (typically the git-ignored output/build-reports/ tree):
            # show the ref value as plain text instead of a dead link.
            detail = f'<code>{_esc(detail_ref)}</code>'
        html_parts.append(f'<tr><td>{_esc(entry.get("run_finished_at", ""))}</td><td>{badge}</td><td><code>{_esc(entry.get("run_archive_ref") or "historisch nachgetragen")}</code></td><td>Seiten: {pages}; Prüfungen: {checks}; Diagramme: {diagrams}; Befunde: {entry.get("findings_count", 0)}</td><td>{detail}</td></tr>')
    if not ledger_entries:
        html_parts.append('<tr><td colspan="5">Keine schemakonformen Ledger-Einträge vorhanden.</td></tr>')
    html_parts.append('</tbody></table></div>')
    html_parts.append(f"""<h1 id="latest-run">Traceable Build- & Publikations-Report</h1>
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

    rendered_ref = combined_report.get("run_archive_ref")
    if not _has_run_archive_ref(rendered_ref):
        rendered_ref = None
    try:
        with open(PAGE_MODEL, encoding="utf-8") as f:
            previous_provenance = json.load(f).get(PROVENANCE_KEY)
    except (OSError, UnicodeError, ValueError):
        previous_provenance = None

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
        ],
        # 0043-04 / DEC-0043-003: binds this published page to exactly one
        # schema-valid tracked ledger entry; validate.py checks the binding.
        PROVENANCE_KEY: publication_provenance(ledger_path, rendered_ref, previous_provenance),
    }

    os.makedirs(os.path.dirname(PAGE_MODEL), exist_ok=True)
    with open(PAGE_MODEL, "w", encoding="utf-8") as f:
        json.dump(page_data, f, ensure_ascii=False, indent=1)

    return PAGE_MODEL


def record_in_ledger(combined, combined_path, ledger_path=None):
    """Append this run to the tracked build ledger (0043-02).

    Returns ``(ok, message)``. A failure is never swallowed: the ledger is the
    configuration-managed build evidence required by `DEC-0043-001`, and
    `0043-04` will treat a run without a ledger entry as a finding, so a failed
    append must be visible in the exit code of the run that caused it.
    """
    try:
        status, entry = build_ledger.record_run(combined, combined_path, path=ledger_path)
    except (build_ledger.LedgerError, OSError, ValueError) as exc:
        return False, f"Build-Ledger NICHT aktualisiert: {exc}"
    target = ledger_path or build_ledger.LEDGER_PATH
    rel = os.path.relpath(target, ROOT)
    if rel.startswith(os.pardir):  # a ledger outside the repository (tests, diagnostics)
        rel = target
    if status == "duplicate":
        return True, (
            f"Build-Ledger unveraendert: Lauf {entry['run_archive_ref']!r} ist in {rel} "
            "bereits verzeichnet (ein Eintrag je Lauf)."
        )
    return True, f"Build-Ledger ergaenzt: {rel} (+1 Eintrag, Lauf {entry['run_archive_ref']!r})"


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "combine"
    ref = None
    use_ledger = "--no-ledger" not in args
    for a in args:
        if a.startswith("--run-archive-ref="):
            ref = a.split("=", 1)[1]

    if cmd == "combine":
        combined, out = combine_reports(ref, diagnostic_no_ledger=not use_ledger)
        print(f"Aggregierter Build-Report geschrieben: {out} (Exit-Code {combined['exit_code']})")
        exit_code = combined["exit_code"]
        if use_ledger:
            ok, message = record_in_ledger(combined, out)
            print(message, file=sys.stdout if ok else sys.stderr)
            if not ok:
                exit_code = max(exit_code, 1)
        return exit_code
    if cmd == "provenance":
        target = write_page_provenance()
        print(f"Publikations-Provenienz im Seitenmodell aktualisiert: {target}")
        return 0
    if cmd in ("publish", "page"):
        combined, out = combine_reports(ref, diagnostic_no_ledger=not use_ledger)
        exit_code = combined["exit_code"]
        if use_ledger:
            ok, message = record_in_ledger(combined, out)
            print(message, file=sys.stdout if ok else sys.stderr)
            if not ok:
                exit_code = max(exit_code, 1)
        page_path = generate_report_page(combined, ref)
        print(f"Seitenmodell fuer Build-Report erzeugt: {page_path} (Exit-Code {combined['exit_code']})")
        return exit_code
    if cmd == "mint-ref":
        print(mint_manual_run_archive_ref())
        return 0
    print(f"Unbekannter Befehl: {cmd}. Erlaubt: combine, publish, provenance, mint-ref")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
