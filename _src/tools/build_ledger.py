#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ledger.py — The tracked, append-only build ledger (Task 0043-02).

Implements decision `DEC-0043-001` (see
docs/dossiers/re-intake-berichtswesen-build-evidenz.md): the build *history* of
the publication pipeline is configuration-managed evidence and therefore lives
inside the repository, while the raw run logs stay git-ignored under `output/`.

One line of `docs/evidence/build-ledger.jsonl` = one publication run. The file
is JSON Lines (UTF-8, `\n`-terminated, no trailing content) precisely because
appending a line is the only mutation the format needs: existing bytes are never
touched, so a rewrite is mechanically detectable (see `verify(..., baseline=)`).

Schema and consumer contract: docs/pipeline/build-ledger.md.

CLI:
    python3 _src/tools/build_ledger.py verify [--json] [--baseline=<git-rev>]
        Validates every entry, rejects duplicate run refs and non-monotonic
        recorded_at, and — with --baseline — proves append-only by checking that
        the committed version of the ledger is a byte-exact prefix of the
        working copy. Exit 0 = clean, 1 = findings, 2 = usage error.
    python3 _src/tools/build_ledger.py list [--json] [--limit=<n>]
        Prints the ledger newest-entry-first (the shape 0043-03 renders).
    python3 _src/tools/build_ledger.py backfill-historic --combined=<path> [--force]
        Appends a historic pre-0043-01 combined report as a `backfilled` entry.
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
LEDGER_PATH = os.path.join(ROOT, "docs", "evidence", "build-ledger.jsonl")

SCHEMA_VERSION = "1.0"
ENTRY_KIND = "publication-run"
REQUIRED_STAGES = ("i18n_merge", "i18n_diagrams", "html_generate", "validate")
SEVERITIES = ("info", "warning", "error")

# Fields every entry carries. Order is the on-disk key order (json.dumps keeps
# insertion order), so a hand-read diff of the ledger stays legible.
_REQUIRED_FIELDS = (
    "schema_version",
    "entry_kind",
    "recorded_at",
    "run_started_at",
    "run_finished_at",
    "run_archive_ref",
    "repo_commit",
    "exit_code",
    "overall_success",
    "counts_by_stage",
    "findings_count",
    "findings_by_severity",
    "combined_report_digest",
    "combined_report_ref",
    "backfilled",
)


class LedgerError(Exception):
    """Raised when an append would violate the append-only contract."""


def _utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        return None
    return parsed.replace(tzinfo=datetime.timezone.utc)


def sha256_file(path):
    """Return `sha256:<hex>` over the exact bytes of `path`."""
    digest = hashlib.sha256()
    with open(path, "rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def current_repo_commit(cwd=None):
    """Best-effort HEAD commit of the repository, or None outside a checkout.

    Recorded, never guessed: a run built from a dirty or detached tree still
    gets the honest HEAD id, and a run outside any checkout gets `null` rather
    than a fabricated value.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    commit = out.stdout.strip()
    if out.returncode != 0 or len(commit) != 40:
        return None
    return commit


# --------------------------------------------------------------------------
# Entry construction
# --------------------------------------------------------------------------

def _count_findings_by_severity(findings):
    counts = {severity: 0 for severity in SEVERITIES}
    for finding in findings if isinstance(findings, list) else []:
        severity = finding.get("severity") if isinstance(finding, dict) else None
        if severity in counts:
            counts[severity] += 1
    return counts


def entry_from_combined(combined, combined_path, repo_commit=None, backfilled=False,
                        recorded_at=None, note=None):
    """Project one combined build report onto its ledger entry.

    `combined` is a `report_kind: "combined"` document as produced by
    `build_report.py combine`; `combined_path` is the file it was written to
    (its bytes are digested, so the entry pins the exact evidence document).
    """
    if not isinstance(combined, dict):
        raise LedgerError("combined report must be a JSON object")
    if combined.get("report_kind") != "combined":
        raise LedgerError("combined report must have report_kind 'combined'")

    counts = combined.get("counts") if isinstance(combined.get("counts"), dict) else {}
    by_stage = counts.get("by_stage") if isinstance(counts.get("by_stage"), dict) else {}
    overall_success = counts.get("overall_success")
    if not isinstance(overall_success, bool):
        overall_success = combined.get("exit_code") == 0
    findings = combined.get("findings") if isinstance(combined.get("findings"), list) else []

    ref = combined.get("run_archive_ref")
    if not (isinstance(ref, str) and ref.strip()):
        # Only a backfilled historic run may lack a ref: it predates 0043-01's
        # correlation repair, and inventing one would fake traceability.
        if not backfilled:
            raise LedgerError(
                "run_archive_ref must be a non-empty string; only a backfilled "
                "historic entry may record null"
            )
        ref = None

    entry = {
        "schema_version": SCHEMA_VERSION,
        "entry_kind": ENTRY_KIND,
        "recorded_at": recorded_at or _utc_now_iso(),
        "run_started_at": combined.get("started_at"),
        "run_finished_at": combined.get("finished_at"),
        "run_archive_ref": ref,
        "repo_commit": repo_commit,
        "exit_code": combined.get("exit_code"),
        "overall_success": overall_success,
        "counts_by_stage": {stage: by_stage.get(stage, {}) for stage in REQUIRED_STAGES},
        "findings_count": len(findings),
        "findings_by_severity": _count_findings_by_severity(findings),
        "combined_report_digest": sha256_file(combined_path),
        "combined_report_ref": os.path.relpath(os.path.abspath(combined_path), ROOT),
        "backfilled": bool(backfilled),
    }
    if note:
        entry["note"] = note
    return entry


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def validate_entry(entry):
    """Return a list of human-readable defects; empty list means conforming."""
    errors = []
    if not isinstance(entry, dict):
        return ["entry must be a JSON object"]

    for field in _REQUIRED_FIELDS:
        if field not in entry:
            errors.append(f"missing required field {field!r}")

    if entry.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION!r}")
    if entry.get("entry_kind") != ENTRY_KIND:
        errors.append(f"entry_kind must equal {ENTRY_KIND!r}")

    backfilled = entry.get("backfilled")
    if not isinstance(backfilled, bool):
        errors.append("backfilled must be a boolean")

    for field in ("recorded_at", "run_started_at", "run_finished_at"):
        if field in entry and _parse_utc(entry.get(field)) is None:
            errors.append(f"{field} must be a strict UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)")

    started = _parse_utc(entry.get("run_started_at"))
    finished = _parse_utc(entry.get("run_finished_at"))
    if started is not None and finished is not None and finished < started:
        errors.append("run_finished_at must not precede run_started_at")

    ref = entry.get("run_archive_ref")
    if ref is None:
        if backfilled is not True:
            errors.append("run_archive_ref may only be null on a backfilled entry")
    elif not (isinstance(ref, str) and ref.strip()):
        errors.append("run_archive_ref must be a non-empty string or null")

    commit = entry.get("repo_commit")
    if commit is not None and not (
        isinstance(commit, str) and len(commit) == 40
        and all(c in "0123456789abcdef" for c in commit)
    ):
        errors.append("repo_commit must be a 40-character lowercase hex SHA-1 or null")

    exit_code = entry.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int) or not 0 <= exit_code <= 255:
        errors.append("exit_code must be an integer from 0 through 255")

    success = entry.get("overall_success")
    if not isinstance(success, bool):
        errors.append("overall_success must be a boolean")
    elif isinstance(exit_code, int) and not isinstance(exit_code, bool):
        if success != (exit_code == 0):
            errors.append("overall_success must agree with exit_code == 0")

    by_stage = entry.get("counts_by_stage")
    if not isinstance(by_stage, dict):
        errors.append("counts_by_stage must be an object")
    else:
        for stage in REQUIRED_STAGES:
            if stage not in by_stage:
                errors.append(f"counts_by_stage is missing required stage {stage!r}")
            elif not isinstance(by_stage[stage], dict):
                errors.append(f"counts_by_stage[{stage!r}] must be an object")

    findings_count = entry.get("findings_count")
    if isinstance(findings_count, bool) or not isinstance(findings_count, int) or findings_count < 0:
        errors.append("findings_count must be a non-negative integer")

    by_severity = entry.get("findings_by_severity")
    if not isinstance(by_severity, dict):
        errors.append("findings_by_severity must be an object")
    else:
        total = 0
        for severity in SEVERITIES:
            value = by_severity.get(severity)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"findings_by_severity[{severity!r}] must be a non-negative integer")
            else:
                total += value
        for unknown in sorted(set(by_severity) - set(SEVERITIES)):
            errors.append(f"findings_by_severity has unknown severity {unknown!r}")
        if not errors and isinstance(findings_count, int) and total > findings_count:
            errors.append("findings_by_severity totals more entries than findings_count")

    digest = entry.get("combined_report_digest")
    if not (isinstance(digest, str) and digest.startswith("sha256:") and len(digest) == 71
            and all(c in "0123456789abcdef" for c in digest[7:])):
        errors.append("combined_report_digest must be 'sha256:' plus 64 lowercase hex chars")

    report_ref = entry.get("combined_report_ref")
    if not (isinstance(report_ref, str) and report_ref.strip()):
        errors.append("combined_report_ref must be a non-empty string")

    if "note" in entry and not (isinstance(entry["note"], str) and entry["note"].strip()):
        errors.append("note must be a non-empty string when present")

    return errors


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------

def read_entries(path=None):
    """Read the ledger.

    Returns `(entries, findings)`. `entries` holds only conforming entries in
    file order (oldest first); `findings` uses the build-report finding shape
    (`category`/`severity`/`message`/`ref`) so `0043-03`/`0043-04` can surface a
    corrupt ledger through the machinery that already exists, instead of
    silently rendering a truncated history.
    """
    path = path or LEDGER_PATH
    entries = []
    findings = []
    if not os.path.exists(path):
        return entries, findings

    with open(path, encoding="utf-8") as fp:
        raw_lines = fp.read().split("\n")
    if raw_lines and raw_lines[-1] == "":
        raw_lines.pop()
    else:
        findings.append({
            "category": "malformed-build-ledger",
            "severity": "error",
            "message": "Ledger does not end with a newline; the last entry may be truncated.",
            "ref": os.path.relpath(path, ROOT),
        })

    for index, line in enumerate(raw_lines, start=1):
        if not line.strip():
            findings.append({
                "category": "malformed-build-ledger",
                "severity": "error",
                "message": f"Line {index} is blank; JSON Lines allows no empty records.",
                "ref": os.path.relpath(path, ROOT),
            })
            continue
        try:
            entry = json.loads(line)
        except ValueError as exc:
            findings.append({
                "category": "malformed-build-ledger",
                "severity": "error",
                "message": f"Line {index} is not valid JSON: {exc}",
                "ref": os.path.relpath(path, ROOT),
            })
            continue
        errors = validate_entry(entry)
        if errors:
            findings.append({
                "category": "malformed-build-ledger",
                "severity": "error",
                "message": f"Line {index} violates the ledger schema: " + "; ".join(errors),
                "ref": os.path.relpath(path, ROOT),
            })
            continue
        entries.append(entry)

    return entries, findings


def find_entry_by_ref(run_archive_ref, path=None):
    """Return the first entry recorded for `run_archive_ref`, or None."""
    if not (isinstance(run_archive_ref, str) and run_archive_ref.strip()):
        return None
    entries, _ = read_entries(path)
    for entry in entries:
        if entry.get("run_archive_ref") == run_archive_ref:
            return entry
    return None


# --------------------------------------------------------------------------
# Appending
# --------------------------------------------------------------------------

def append_entry(entry, path=None, allow_duplicate_ref=False):
    """Append one conforming entry.

    Returns `"appended"`, or `"duplicate"` when an entry for the same
    `run_archive_ref` already exists — appending is idempotent per publication
    run, because `publish` re-combines the same cohort that `combine` already
    recorded, and a run must appear exactly once.

    Raises `LedgerError` on a malformed entry or an already-corrupt ledger:
    the ledger is evidence, so it fails closed rather than growing garbage.
    """
    path = path or LEDGER_PATH
    errors = validate_entry(entry)
    if errors:
        raise LedgerError("refusing to append a malformed ledger entry: " + "; ".join(errors))

    existing, findings = read_entries(path)
    if findings:
        raise LedgerError(
            "refusing to append to a ledger that already has defects: "
            + "; ".join(f["message"] for f in findings)
        )

    ref = entry.get("run_archive_ref")
    if ref is not None and not allow_duplicate_ref:
        if any(previous.get("run_archive_ref") == ref for previous in existing):
            return "duplicate"

    if existing:
        last = _parse_utc(existing[-1].get("recorded_at"))
        current = _parse_utc(entry.get("recorded_at"))
        if last is not None and current is not None and current < last:
            raise LedgerError(
                "refusing to append an entry recorded before the ledger's last entry "
                f"({entry.get('recorded_at')} < {existing[-1].get('recorded_at')}); "
                "the ledger is ordered by append time"
            )

    line = json.dumps(entry, ensure_ascii=False, sort_keys=False) + "\n"
    if "\n" in line[:-1] or "\r" in line:
        raise LedgerError("serialized entry must occupy exactly one line")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    # O_APPEND: every write lands at the current end of file, so a concurrent
    # appender can never overwrite an existing entry.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    return "appended"


def record_run(combined, combined_path, path=None, repo_commit=None, backfilled=False,
               note=None):
    """Build and append the ledger entry for one combined report.

    Returns `(status, entry)` with `status` in `{"appended", "duplicate"}`.
    """
    if repo_commit is None and not backfilled:
        repo_commit = current_repo_commit()
    entry = entry_from_combined(
        combined,
        combined_path,
        repo_commit=repo_commit,
        backfilled=backfilled,
        note=note,
    )
    return append_entry(entry, path), entry


# --------------------------------------------------------------------------
# Verification (append-only proof)
# --------------------------------------------------------------------------

def _git_show_bytes(rev, path, cwd=None):
    rel = os.path.relpath(os.path.abspath(path), ROOT).replace(os.sep, "/")
    out = subprocess.run(
        ["git", "show", f"{rev}:{rel}"],
        cwd=cwd or ROOT,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if out.returncode != 0:
        return None
    return out.stdout


def verify(path=None, baseline=None, cwd=None):
    """Validate the ledger and, with `baseline`, prove it was only appended to.

    The append-only property is checked structurally: the ledger's committed
    content at `baseline` (e.g. `HEAD`) must be a byte-exact **prefix** of the
    working copy. Any edit or deletion of an existing entry breaks that prefix
    relation and is reported, even if the rewritten entry is itself well-formed.
    """
    path = path or LEDGER_PATH
    entries, findings = read_entries(path)

    seen = {}
    previous_recorded = None
    for index, entry in enumerate(entries, start=1):
        ref = entry.get("run_archive_ref")
        if ref is not None:
            if ref in seen:
                findings.append({
                    "category": "duplicate-build-ledger-entry",
                    "severity": "error",
                    "message": (
                        f"run_archive_ref {ref!r} is recorded twice "
                        f"(entries {seen[ref]} and {index}); a run appears once."
                    ),
                    "ref": os.path.relpath(path, ROOT),
                })
            else:
                seen[ref] = index
        recorded = _parse_utc(entry.get("recorded_at"))
        if recorded is not None and previous_recorded is not None and recorded < previous_recorded:
            findings.append({
                "category": "malformed-build-ledger",
                "severity": "error",
                "message": (
                    f"Entry {index} was recorded at {entry.get('recorded_at')}, before its "
                    "predecessor; ledger order must follow append time."
                ),
                "ref": os.path.relpath(path, ROOT),
            })
        if recorded is not None:
            previous_recorded = recorded

    for index, entry in enumerate(entries[1:], start=2):
        if entry.get("backfilled"):
            findings.append({
                "category": "malformed-build-ledger",
                "severity": "warning",
                "message": (
                    f"Entry {index} is marked backfilled but is not the historic first "
                    "entry; check that it is not covering up a missed live append."
                ),
                "ref": os.path.relpath(path, ROOT),
            })

    if baseline:
        committed = _git_show_bytes(baseline, path, cwd=cwd)
        if committed is None:
            findings.append({
                "category": "build-ledger-baseline-unavailable",
                "severity": "warning",
                "message": f"The ledger does not exist at baseline {baseline!r}; nothing to compare.",
                "ref": os.path.relpath(path, ROOT),
            })
        else:
            current = open(path, "rb").read() if os.path.exists(path) else b""
            if not current.startswith(committed):
                findings.append({
                    "category": "rewritten-build-ledger",
                    "severity": "error",
                    "message": (
                        f"The ledger at {baseline!r} is not a byte-exact prefix of the working "
                        "copy: existing entries were rewritten, reordered or removed. The "
                        "ledger is append-only (DEC-0043-001)."
                    ),
                    "ref": os.path.relpath(path, ROOT),
                })

    return entries, findings


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _cmd_verify(args):
    entries, findings = verify(args.path, baseline=args.baseline)
    errors = [f for f in findings if f.get("severity") == "error"]
    if args.json:
        print(json.dumps({
            "ledger": os.path.relpath(args.path or LEDGER_PATH, ROOT),
            "entries": len(entries),
            "findings": findings,
            "verdict": "FAIL" if errors else "OK",
        }, ensure_ascii=False, indent=1))
    else:
        print(f"Ledger: {os.path.relpath(args.path or LEDGER_PATH, ROOT)} ({len(entries)} Einträge)")
        for finding in findings:
            print(f"  [{finding['severity']}] {finding['category']}: {finding['message']}")
        print("Verdikt: " + ("FEHLER" if errors else "OK"))
    return 1 if errors else 0


def _cmd_list(args):
    entries, findings = read_entries(args.path)
    newest_first = list(reversed(entries))
    if args.limit:
        newest_first = newest_first[: args.limit]
    if args.json:
        print(json.dumps({"entries": newest_first, "findings": findings},
                         ensure_ascii=False, indent=1))
    else:
        for entry in newest_first:
            status = "OK   " if entry.get("overall_success") else "FEHLER"
            mark = " (backfilled)" if entry.get("backfilled") else ""
            print(f"{entry.get('run_finished_at')}  {status}  "
                  f"{entry.get('run_archive_ref') or '-'}  "
                  f"Befunde={entry.get('findings_count')}{mark}")
    return 1 if any(f.get("severity") == "error" for f in findings) else 0


def _cmd_backfill(args):
    with open(args.combined, encoding="utf-8") as fp:
        combined = json.load(fp)
    status, entry = record_run(
        combined,
        args.combined,
        path=args.path,
        repo_commit=args.repo_commit,
        backfilled=True,
        note=args.note,
    )
    print(f"{status}: {json.dumps(entry, ensure_ascii=False)}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tracked append-only build ledger (0043-02).")
    parser.add_argument("--path", default=None, help="Ledger path (default: docs/evidence/build-ledger.jsonl)")
    sub = parser.add_subparsers(dest="cmd")

    p_verify = sub.add_parser("verify", help="Validate the ledger; prove append-only against a git baseline.")
    p_verify.add_argument("--json", action="store_true")
    p_verify.add_argument("--baseline", default=None, help="git revision to compare against, e.g. HEAD")
    p_verify.set_defaults(func=_cmd_verify)

    p_list = sub.add_parser("list", help="Print the ledger newest first.")
    p_list.add_argument("--json", action="store_true")
    p_list.add_argument("--limit", type=int, default=0)
    p_list.set_defaults(func=_cmd_list)

    p_back = sub.add_parser("backfill-historic", help="Append a historic combined report as a backfilled entry.")
    p_back.add_argument("--combined", required=True)
    p_back.add_argument("--repo-commit", default=None)
    p_back.add_argument("--note", default=None)
    p_back.set_defaults(func=_cmd_backfill)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except (LedgerError, OSError, ValueError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
