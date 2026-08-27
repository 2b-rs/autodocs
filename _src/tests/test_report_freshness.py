#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hermetic tests for the report-staleness check (Task 0043-04, DEC-0043-003).

Every test drives `validate.check_report_freshness()` against a throwaway page
model, ledger and `output/build-reports/` directory. Nothing here touches the
real repository state: the real ledger is append-only permanent history and must
never gain a test entry.

The bound B-06 case list from the Architect scope review is covered explicitly:

  * frozen page (the motivating pre-Feature state) ................ must fire
  * complete cohort without a ledger entry ....................... must fire
  * incomplete / in-flight cohort ................................ must not fire
  * aligned current page ......................................... must not fire
  * fresh clone, empty `output/` ................................. must not fire
"""
import json
import os
import sys

import pytest

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
for _p in (SRC, os.path.join(SRC, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import build_ledger  # noqa: E402
import build_report  # noqa: E402
import validate  # noqa: E402


DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


# --------------------------------------------------------------------------
# fixture helpers
# --------------------------------------------------------------------------
def _ledger_entry(recorded_at, ref, digest, backfilled=False):
    return {
        "schema_version": "1.0",
        "entry_kind": "publication-run",
        "recorded_at": recorded_at,
        "run_started_at": "2026-08-20T10:00:00Z",
        "run_finished_at": "2026-08-20T10:30:00Z",
        "run_archive_ref": ref,
        "repo_commit": None,
        "exit_code": 0,
        "overall_success": True,
        "counts_by_stage": {k: {} for k in build_report.REQUIRED_STAGES},
        "findings_count": 0,
        "findings_by_severity": {"info": 0, "warning": 0, "error": 0},
        "combined_report_digest": digest,
        "combined_report_ref": "output/build-reports/combined-1.json",
        "backfilled": backfilled,
    }


def _subreport(kind, ref, finished_at="2026-08-20T10:30:00Z"):
    return {
        "schema_version": "1.0",
        "report_kind": kind,
        "tool": f"{kind}.py",
        "command": f"{kind}.py",
        "inputs": ["_src/"],
        "started_at": "2026-08-20T10:00:00Z",
        "finished_at": finished_at,
        "duration_s": 1.0,
        "exit_code": 0,
        "changed_artifacts": [],
        "counts": {},
        "findings": [],
        "run_archive_ref": ref,
    }


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated page model, ledger and raw-report directory."""
    page_model = tmp_path / "build-reports.json"
    ledger = tmp_path / "build-ledger.jsonl"
    reports = tmp_path / "build-reports"
    reports.mkdir()

    monkeypatch.setattr(validate, "BUILD_REPORT_PAGE_MODEL", str(page_model))
    monkeypatch.setattr(validate, "BUILD_REPORTS_DIR", str(reports))
    monkeypatch.setattr(build_ledger, "LEDGER_PATH", str(ledger))
    monkeypatch.setattr(validate, "problems", [])
    monkeypatch.setattr(validate, "structured_findings", [])
    monkeypatch.setattr(validate, "checks_performed", [])

    class Env:
        def __init__(self):
            self.page_model = page_model
            self.ledger = ledger
            self.reports = reports

        def write_ledger(self, *entries):
            with open(self.ledger, "w", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        def write_page(self, provenance="auto", rendered_ref=None):
            page = {"file": "build-reports.html", "title": "t", "main": []}
            if provenance == "auto":
                provenance = build_report.publication_provenance(
                    str(self.ledger), rendered_ref)
            if provenance is not None:
                page[build_report.PROVENANCE_KEY] = provenance
            with open(self.page_model, "w", encoding="utf-8") as f:
                json.dump(page, f, ensure_ascii=False, indent=1)

        def write_cohort(self, ref, stages, diagnostic=False,
                         finished_at="2026-08-20T10:30:00Z"):
            for kind in stages:
                path = self.reports / f"{kind}-{ref.replace('/', '_')}.json"
                path.write_text(json.dumps(_subreport(kind, ref, finished_at)),
                                encoding="utf-8")
            combined = {"report_kind": "combined", "run_archive_ref": ref}
            if diagnostic:
                combined["diagnostic_no_ledger"] = True
            (self.reports / f"combined-{ref.replace('/', '_')}.json").write_text(
                json.dumps(combined), encoding="utf-8")

        def run(self):
            validate.check_report_freshness()
            return list(validate.structured_findings)

    return Env()


def _categories(findings):
    return sorted(f["category"] for f in findings)


# --------------------------------------------------------------------------
# B-06: must fire
# --------------------------------------------------------------------------
def test_frozen_page_without_provenance_fires(env):
    """The motivating pre-Feature state: a published page bound to nothing."""
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page(provenance=None)

    findings = env.run()

    assert _categories(findings) == ["stale-build-report"]
    assert findings[0]["severity"] == "error"
    assert build_report.PROVENANCE_KEY in findings[0]["message"]
    assert validate.problems, "an error finding must reach the exit-status list"


def test_page_bound_to_superseded_entry_fires(env):
    """A newer publication was recorded; the page still names the older run."""
    old = _ledger_entry("2026-08-21T12:00:00Z", "manual-old-1111aaaa", DIGEST_A)
    new = _ledger_entry("2026-08-22T12:00:00Z", "manual-new-2222bbbb", DIGEST_B)
    env.write_ledger(old)
    env.write_page()                      # binds to `old`
    env.write_ledger(old, new)            # ... then `new` is published

    findings = env.run()

    assert _categories(findings) == ["stale-build-report"]
    assert "manual-old-1111aaaa" in findings[0]["message"]
    assert "manual-new-2222bbbb" in findings[0]["message"]


def test_complete_cohort_without_ledger_entry_fires(env):
    """A finished publication run that never reached the tracked ledger."""
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page()
    env.write_cohort("manual-20260822T090000Z-cafebabe",
                     build_report.REQUIRED_STAGES)

    findings = env.run()

    assert _categories(findings) == ["unrecorded-publication-run"]
    assert findings[0]["severity"] == "error"
    assert "manual-20260822T090000Z-cafebabe" in findings[0]["message"]


def test_null_ref_binding_not_marked_backfilled_fires(env):
    """A null cohort ref is honest only when it mirrors the backfilled entry.

    The ledger itself refuses a non-backfilled entry with a null
    `run_archive_ref`, so this state can only arise in the page model — a page
    claiming a live publication that names no cohort. The check refuses it
    rather than accepting an unverifiable identity.
    """
    entry = _ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A, backfilled=True)
    env.write_ledger(entry)
    env.write_page(provenance={
        "schema_version": build_report.PROVENANCE_SCHEMA_VERSION,
        "bound_at": "2026-08-21T12:00:00Z",
        "ledger_ref": "docs/evidence/build-ledger.jsonl",
        "ledger_entry_count": 1,
        "ledger_findings_count": 0,
        "ledger_entry": {
            "recorded_at": entry["recorded_at"],
            "run_archive_ref": None,
            "combined_report_digest": DIGEST_A,
            "backfilled": False,
        },
        "rendered_run_archive_ref": None,
    })

    findings = env.run()

    assert _categories(findings) == ["stale-build-report"]
    assert "backfilled" in findings[0]["message"]


def test_body_and_binding_disagree_fires(env):
    """The rendered detail section and the binding must name the same cohort."""
    entry = _ledger_entry("2026-08-21T12:00:00Z", "manual-bound-1111aaaa", DIGEST_A)
    env.write_ledger(entry)
    env.write_page(rendered_ref="manual-rendered-9999zzzz")

    findings = env.run()

    assert _categories(findings) == ["stale-build-report"]
    assert "manual-rendered-9999zzzz" in findings[0]["message"]


def test_malformed_ledger_is_reported(env):
    """A corrupt tracked history is never read as a short, healthy history."""
    env.ledger.write_text("{not json}\n", encoding="utf-8")
    env.write_page(provenance={
        "schema_version": build_report.PROVENANCE_SCHEMA_VERSION,
        "bound_at": "2026-08-21T12:00:00Z",
        "ledger_ref": "docs/evidence/build-ledger.jsonl",
        "ledger_entry_count": 0,
        "ledger_findings_count": 1,
        "ledger_entry": None,
        "rendered_run_archive_ref": None,
    })

    findings = env.run()

    assert "malformed-build-ledger" in _categories(findings)


def test_unknown_provenance_schema_version_fires(env):
    """An unknown binding format is refused, never guessed at."""
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page(provenance={"schema_version": "99.0"})

    findings = env.run()

    assert _categories(findings) == ["stale-build-report"]
    assert "schema_version" in findings[0]["message"]


# --------------------------------------------------------------------------
# B-06 / B-03: must not fire
# --------------------------------------------------------------------------
def test_aligned_current_page_passes(env):
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", "manual-cur-1111aaaa",
                                   DIGEST_A))
    env.write_page(rendered_ref="manual-cur-1111aaaa")
    env.write_cohort("manual-cur-1111aaaa", build_report.REQUIRED_STAGES)

    assert env.run() == []
    assert validate.problems == []


def test_fresh_clone_with_empty_output_passes(env):
    """Absence of git-ignored raw artifacts is never itself a finding."""
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page()
    assert not any(env.reports.iterdir())

    assert env.run() == []


def test_missing_output_directory_passes(env):
    """Not even the `output/build-reports/` directory needs to exist."""
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page()
    for child in env.reports.iterdir():
        child.unlink()
    env.reports.rmdir()

    assert env.run() == []


def test_incomplete_cohort_does_not_fire(env):
    """A build in flight is not a publication; it must not block anyone."""
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page()
    env.write_cohort("manual-inflight-1111aaaa", ("html_generate", "validate"))

    assert env.run() == []


def test_validator_own_subreport_does_not_self_inflict(env):
    """The validator's own report alone is an incomplete cohort, never stale."""
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page()
    env.write_cohort("manual-selftest-1111aaaa", ("validate",))

    assert env.run() == []


def test_final_validation_under_same_ref_creates_no_newer_cohort(env):
    """The canonical sequence ends with a second validate under the same ref."""
    ref = "manual-cur-1111aaaa"
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", ref, DIGEST_A))
    env.write_page(rendered_ref=ref)
    env.write_cohort(ref, build_report.REQUIRED_STAGES)
    # the post-publication validate run, later in wall-clock time, same cohort
    (env.reports / "validate-final.json").write_text(
        json.dumps(_subreport("validate", ref, finished_at="2026-08-20T11:59:00Z")),
        encoding="utf-8")

    assert env.run() == []


def test_diagnostic_no_ledger_cohort_is_not_a_publication_candidate(env):
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page()
    env.write_cohort("manual-diag-1111aaaa", build_report.REQUIRED_STAGES,
                     diagnostic=True)

    assert env.run() == []


def test_identity_less_reports_are_ignored(env):
    """Reports without a cohort identity cannot form a publication cohort."""
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page()
    for kind in build_report.REQUIRED_STAGES:
        report = _subreport(kind, "x")
        report["run_archive_ref"] = None
        (env.reports / f"{kind}-anon.json").write_text(json.dumps(report),
                                                       encoding="utf-8")

    assert env.run() == []


def test_older_cohort_already_in_ledger_passes(env):
    """A ledger newer than the newest local cohort is current, not stale."""
    old_ref = "manual-old-1111aaaa"
    env.write_ledger(
        _ledger_entry("2026-08-21T12:00:00Z", old_ref, DIGEST_A),
        _ledger_entry("2026-08-22T12:00:00Z", "manual-new-2222bbbb", DIGEST_B),
    )
    env.write_page(rendered_ref="manual-new-2222bbbb")
    env.write_cohort(old_ref, build_report.REQUIRED_STAGES)

    assert env.run() == []


# --------------------------------------------------------------------------
# producer side
# --------------------------------------------------------------------------
def test_provenance_is_idempotent(env):
    """Republishing the same run leaves the tracked page model byte-identical."""
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page()
    first = env.page_model.read_bytes()

    build_report.write_page_provenance(str(env.ledger), str(env.page_model))

    assert env.page_model.read_bytes() == first


def test_provenance_rebinds_after_a_new_publication(env):
    env.write_ledger(_ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A,
                                   backfilled=True))
    env.write_page()
    env.write_ledger(
        _ledger_entry("2026-08-21T12:00:00Z", None, DIGEST_A, backfilled=True),
        _ledger_entry("2026-08-22T12:00:00Z", "manual-new-2222bbbb", DIGEST_B),
    )

    build_report.write_page_provenance(str(env.ledger), str(env.page_model))
    page = json.loads(env.page_model.read_text(encoding="utf-8"))

    assert page[build_report.PROVENANCE_KEY]["ledger_entry"]["run_archive_ref"] == \
        "manual-new-2222bbbb"
    assert env.run() == []


def test_real_repository_page_model_is_bound_and_current():
    """The committed page model must satisfy the check as shipped (DoD)."""
    with open(os.path.join(SRC, "sources", "pages", "build-reports.json"),
              encoding="utf-8") as f:
        page = json.load(f)
    provenance = page.get(build_report.PROVENANCE_KEY)

    assert isinstance(provenance, dict)
    assert provenance["schema_version"] == build_report.PROVENANCE_SCHEMA_VERSION
    entries, findings = build_ledger.read_entries()
    assert findings == []
    assert provenance["ledger_entry"]["recorded_at"] == entries[-1]["recorded_at"]
    assert provenance["ledger_entry"]["combined_report_digest"] == \
        entries[-1]["combined_report_digest"]
