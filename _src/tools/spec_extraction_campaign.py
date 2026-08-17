#!/usr/bin/env python3
"""Reproducible side-by-side PDF extraction campaign reports.

The create/report commands perform no PDF extraction themselves.  ``run-job``
executes one exact manifest-bound extractor command and emits a structured result
envelope for runner redirection; reports accept only those envelopes.
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
from importlib import metadata
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]
sys.path.insert(0, str(TOOLS))
import spec_scrape

BACKENDS = ("pypdf", "builtin")
FIELDS = ("heading", "requirement_text", "Description", "Rationale", "AppliesTo",
          "Dependencies", "Use Case", "Supporting Material")
MANIFEST_SCHEMA = 3
IDENTITY_SCHEMA = 1
JOB_SCHEMA = 2
EXTRACTOR_CONTRACT_SCHEMA = 1
RESULT_SCHEMA = 1


from canonical_id import DEFAULT_PROJECT, DEFAULT_KIND  # noqa: E402 (0006-02 propagation)


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


def _json_digest(value) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _runtime_contract() -> dict:
    return {
        "implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "executable": str(Path(sys.executable).resolve()),
        "cache_tag": sys.implementation.cache_tag,
        "os_name": os.name,
        "platform": platform.platform(),
    }


def _tool_contract() -> dict:
    extractor = (TOOLS / "spec_scrape.py").resolve()
    harness = Path(__file__).resolve()
    return {
        "extractor": {"path": str(extractor), "sha256": _sha256(extractor)},
        "harness": {"path": str(harness), "sha256": _sha256(harness)},
    }


def _backend_contract(tool_contract: dict) -> list[dict]:
    return [
        {
            "name": "pypdf",
            "implementation": "pypdf.PdfReader",
            "distribution": "pypdf",
            "version": _distribution_version("pypdf"),
        },
        {
            "name": "builtin",
            "implementation": "spec_scrape.py builtin PDF extractor",
            "tool_sha256": tool_contract["extractor"]["sha256"],
        },
    ]


def _command_contract() -> dict:
    return {
        "phase": "props",
        "document_selector": "stem",
        "json": True,
    }


def _manifest_identity_payload(manifest: dict) -> dict:
    return {
        "schema": IDENTITY_SCHEMA,
        "manifest_schema": manifest["schema"],
        "campaign": manifest["campaign"],
        "created_by": manifest["created_by"],
        "pdf_dir": manifest["pdf_dir"],
        "git_revision": manifest["git_revision"],
        "python": manifest["python"],
        "platform": manifest["platform"],
        "pattern": manifest["pattern"],
        "backends": manifest["backends"],
        "backend_contract": manifest["backend_contract"],
        "tool_contract": manifest["tool_contract"],
        "runtime_contract": manifest["runtime_contract"],
        "command_contract": manifest["command_contract"],
        "documents": manifest["documents"],
    }


def _extractor_argv(manifest: dict, document: dict, backend: str) -> list[str]:
    return [
        manifest["runtime_contract"]["executable"],
        manifest["tool_contract"]["extractor"]["path"],
        "props",
        "--pdf-dir", manifest["pdf_dir"],
        "--doc", document["name"],
        "--pattern", manifest["pattern"],
        "--backend", backend,
        "--json",
    ]


def _extractor_contract_payload(manifest: dict, document: dict, backend: str,
                                extractor_argv: list[str]) -> dict:
    backend_contract = next(
        item for item in manifest["backend_contract"] if item["name"] == backend
    )
    return {
        "schema": EXTRACTOR_CONTRACT_SCHEMA,
        "attempt_id": manifest["attempt_id"],
        "git_revision": manifest["git_revision"],
        "document": document,
        "backend": backend,
        "extractor_argv": extractor_argv,
        "extractor_tool": manifest["tool_contract"]["extractor"],
        "runtime_contract": manifest["runtime_contract"],
        "backend_contract": backend_contract,
        "command_contract": manifest["command_contract"],
    }


def _job_contract(campaign_dir: Path, manifest: dict, document: dict,
                  backend: str) -> dict:
    extractor_argv = _extractor_argv(manifest, document, backend)
    extractor_contract_digest = _json_digest(
        _extractor_contract_payload(manifest, document, backend, extractor_argv)
    )
    identity = {
        "schema": JOB_SCHEMA,
        "attempt_id": manifest["attempt_id"],
        "document": document,
        "backend": backend,
        "extractor_contract_digest": extractor_contract_digest,
    }
    job_id = _json_digest(identity)
    attempt_dir = campaign_dir / "attempts" / manifest["attempt_id"]
    attempt_manifest = attempt_dir / "manifest.json"
    return {
        "schema": JOB_SCHEMA,
        "job_id": job_id,
        "attempt_id": manifest["attempt_id"],
        "document": document["name"],
        "document_sha256": document["sha256"],
        "backend": backend,
        "extractor_argv": extractor_argv,
        "extractor_contract_digest": extractor_contract_digest,
        "output": str(attempt_dir / "raw" / f"{job_id}.json"),
        "log": str(attempt_dir / "logs" / f"{job_id}.log"),
        "argv": [
            manifest["runtime_contract"]["executable"],
            manifest["tool_contract"]["harness"]["path"],
            "run-job",
            str(attempt_manifest),
            "--job-id", job_id,
        ],
    }


def _expected_jobs(campaign_dir: Path, manifest: dict) -> list[dict]:
    return [
        _job_contract(campaign_dir, manifest, document, backend)
        for document in manifest["documents"]
        for backend in manifest["backends"]
    ]


def _documents(pdf_dir: Path, docs: list[str] | None, rs_docs: bool) -> list[Path]:
    selected = list(docs or [])
    if rs_docs:
        selected.extend(value[1] for value in spec_scrape.RS_DOCS.values())
    return spec_scrape.discover_pdfs(pdf_dir, docs=list(dict.fromkeys(selected)) or None)


def create(campaign_dir: Path, pdf_dir: Path, documents: list[Path], pattern: str) -> dict:
    campaign_dir = campaign_dir.resolve()
    pdf_dir = pdf_dir.resolve()
    campaign_dir.mkdir(parents=True, exist_ok=True)

    docs = []
    for pdf in documents:
        source = pdf.resolve()
        docs.append({
            "name": source.stem,
            "path": str(source),
            "sha256": _sha256(source),
            "size": source.stat().st_size,
        })
    names = [document["name"] for document in docs]
    if len(names) != len(set(names)):
        raise ValueError("campaign documents must have unique PDF stems")

    git_revision = _git_revision()
    if not git_revision:
        raise RuntimeError("cannot create an extraction attempt without a Git revision")
    runtime_contract = _runtime_contract()
    tool_contract = _tool_contract()
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "campaign": campaign_dir.name,
        "created_by": "spec_extraction_campaign.py",
        "pdf_dir": str(pdf_dir),
        "git_revision": git_revision,
        "python": runtime_contract["python_version"],
        "platform": runtime_contract["platform"],
        "pattern": pattern,
        "backends": list(BACKENDS),
        "backend_contract": _backend_contract(tool_contract),
        "tool_contract": tool_contract,
        "runtime_contract": runtime_contract,
        "command_contract": _command_contract(),
        "documents": docs,
    }
    manifest["attempt_id"] = _json_digest(_manifest_identity_payload(manifest))
    manifest["jobs"] = _expected_jobs(campaign_dir, manifest)

    attempt_dir = campaign_dir / "attempts" / manifest["attempt_id"]
    (attempt_dir / "raw").mkdir(parents=True, exist_ok=True)
    (attempt_dir / "logs").mkdir(parents=True, exist_ok=True)
    serialized = _stable_json(manifest)
    (attempt_dir / "manifest.json").write_text(serialized, encoding="utf-8")
    (campaign_dir / "manifest.json").write_text(serialized, encoding="utf-8")
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
            "project": DEFAULT_PROJECT,  # 0006-02: default until multi-project extraction lands
            "kind": DEFAULT_KIND,
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


def _manifest_document_names(manifest: object) -> list[str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("documents"), list):
        return []
    return [
        document["name"]
        for document in manifest["documents"]
        if isinstance(document, dict) and isinstance(document.get("name"), str)
    ]


def _validate_manifest(campaign_dir: Path, manifest: object) -> tuple[list[str], list[dict] | None]:
    if not isinstance(manifest, dict):
        return ["manifest root must be an object"], None
    if manifest.get("schema") != MANIFEST_SCHEMA:
        return [f"unsupported manifest schema {manifest.get('schema')!r}; expected {MANIFEST_SCHEMA}"], None

    errors = []
    if manifest.get("campaign") != campaign_dir.name:
        errors.append("campaign name does not match the campaign directory")
    if manifest.get("created_by") != "spec_extraction_campaign.py":
        errors.append("created_by is not the campaign harness")
    if not isinstance(manifest.get("pdf_dir"), str) or not Path(manifest["pdf_dir"]).is_absolute():
        errors.append("pdf_dir must be an absolute path")
    if not isinstance(manifest.get("git_revision"), str) or not manifest["git_revision"]:
        errors.append("git_revision must be a non-empty string")
    if not isinstance(manifest.get("pattern"), str):
        errors.append("pattern must be a string")
    if manifest.get("backends") != list(BACKENDS):
        errors.append("backends do not match the supported backend contract")
    if manifest.get("command_contract") != _command_contract():
        errors.append("command contract does not match this manifest schema")

    runtime = manifest.get("runtime_contract")
    if not isinstance(runtime, dict):
        errors.append("runtime_contract must be an object")
    else:
        for key in ("implementation", "python_version", "executable", "cache_tag",
                    "os_name", "platform"):
            if not isinstance(runtime.get(key), str) or not runtime[key]:
                errors.append(f"runtime_contract.{key} must be a non-empty string")
        if manifest.get("python") != runtime.get("python_version"):
            errors.append("python does not match runtime_contract.python_version")
        if manifest.get("platform") != runtime.get("platform"):
            errors.append("platform does not match runtime_contract.platform")

    tools = manifest.get("tool_contract")
    if not isinstance(tools, dict):
        errors.append("tool_contract must be an object")
    else:
        for role in ("extractor", "harness"):
            tool = tools.get(role)
            if not isinstance(tool, dict):
                errors.append(f"tool_contract.{role} must be an object")
                continue
            if not isinstance(tool.get("path"), str) or not Path(tool["path"]).is_absolute():
                errors.append(f"tool_contract.{role}.path must be an absolute path")
            if not isinstance(tool.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", tool["sha256"]):
                errors.append(f"tool_contract.{role}.sha256 must be a SHA-256 digest")

    backend_contract = manifest.get("backend_contract")
    if not isinstance(backend_contract, list):
        errors.append("backend_contract must be a list")
    elif [item.get("name") if isinstance(item, dict) else None
          for item in backend_contract] != list(BACKENDS):
        errors.append("backend_contract names do not match backends")
    elif isinstance(tools, dict) and isinstance(tools.get("extractor"), dict):
        builtin_contract = backend_contract[1]
        if builtin_contract.get("tool_sha256") != tools["extractor"].get("sha256"):
            errors.append("builtin backend contract does not match the extractor tool")

    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        errors.append("documents must be a non-empty list")
    else:
        names = []
        for index, document in enumerate(documents):
            if not isinstance(document, dict):
                errors.append(f"documents[{index}] must be an object")
                continue
            name = document.get("name")
            path = document.get("path")
            digest = document.get("sha256")
            size = document.get("size")
            if not isinstance(name, str) or not name:
                errors.append(f"documents[{index}].name must be a non-empty string")
            else:
                names.append(name)
            if not isinstance(path, str) or not Path(path).is_absolute():
                errors.append(f"documents[{index}].path must be an absolute path")
            elif isinstance(name, str) and Path(path).stem != name:
                errors.append(f"documents[{index}].name does not match its path")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                errors.append(f"documents[{index}].sha256 must be a SHA-256 digest")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                errors.append(f"documents[{index}].size must be a non-negative integer")
        if len(names) != len(set(names)):
            errors.append("document names must be unique")

    attempt_id = manifest.get("attempt_id")
    if not isinstance(attempt_id, str) or not re.fullmatch(r"[0-9a-f]{64}", attempt_id):
        errors.append("attempt_id must be a SHA-256 digest")

    if errors:
        return errors, None

    assert isinstance(attempt_id, str)
    expected_attempt_id = _json_digest(_manifest_identity_payload(manifest))
    if attempt_id != expected_attempt_id:
        errors.append("attempt_id does not match the exact extraction inputs")

    expected_jobs = _expected_jobs(campaign_dir, manifest)
    if manifest.get("jobs") != expected_jobs:
        errors.append("jobs do not match the deterministic current-attempt job contract")

    attempt_manifest = campaign_dir / "attempts" / attempt_id / "manifest.json"
    if attempt_manifest.is_symlink() or not attempt_manifest.is_file():
        errors.append("attempt-bound manifest snapshot is missing")
    else:
        try:
            if _load(attempt_manifest) != manifest:
                errors.append("current manifest does not match its attempt-bound snapshot")
        except (OSError, UnicodeError, ValueError):
            errors.append("attempt-bound manifest snapshot is unreadable")

    try:
        current_tools = _tool_contract()
        current_runtime = _runtime_contract()
        current_backends = _backend_contract(current_tools)
    except OSError as exc:
        errors.append(f"current extraction contract is unreadable: {exc}")
    else:
        if manifest["tool_contract"] != current_tools:
            errors.append("current extractor/harness tool contract differs from the manifest")
        if manifest["runtime_contract"] != current_runtime:
            errors.append("current runtime contract differs from the manifest")
        if manifest["backend_contract"] != current_backends:
            errors.append("current backend contract differs from the manifest")

    return (errors, None) if errors else ([], expected_jobs)


def _write_report_artifacts(campaign_dir: Path, manifest: object,
                            documents: list[dict], total: Counter,
                            failures: list[dict]) -> dict:
    campaign_name = campaign_dir.name
    attempt_id = None
    document_count = len(_manifest_document_names(manifest))
    if isinstance(manifest, dict):
        if isinstance(manifest.get("campaign"), str):
            campaign_name = manifest["campaign"]
        if isinstance(manifest.get("attempt_id"), str):
            attempt_id = manifest["attempt_id"]
    scorecard = {
        "schema": 1,
        "campaign": campaign_name,
        "attempt_id": attempt_id,
        "documents_total": document_count,
        "documents_complete": len(documents),
        "failures": failures,
        "summary": dict(total),
    }
    payload = {"scorecard": scorecard, "documents": documents}
    (campaign_dir / "comparison.json").write_text(_stable_json(payload), encoding="utf-8")
    (campaign_dir / "scorecard.json").write_text(_stable_json(scorecard), encoding="utf-8")
    _write_csv(campaign_dir / "comparison.csv", documents)
    _write_html(campaign_dir / "comparison.html", documents, scorecard)
    return scorecard


def _document_input_errors(document: dict) -> list[dict]:
    source = Path(document["path"])
    if not source.is_file():
        return [{"reason": "source-document-missing", "path": str(source)}]
    try:
        actual_size = source.stat().st_size
        actual_digest = _sha256(source)
    except OSError as exc:
        return [{"reason": "source-document-unreadable", "path": str(source),
                 "detail": str(exc)}]

    errors = []
    if actual_size != document["size"]:
        errors.append({
            "reason": "source-document-size-changed",
            "expected": document["size"],
            "actual": actual_size,
        })
    if actual_digest != document["sha256"]:
        errors.append({
            "reason": "source-document-hash-changed",
            "expected": document["sha256"],
            "actual": actual_digest,
        })
    return errors


def _result_metadata(job: dict, exit_code: int) -> dict:
    return {
        "schema": RESULT_SCHEMA,
        "attempt_id": job["attempt_id"],
        "job_id": job["job_id"],
        "document": job["document"],
        "document_sha256": job["document_sha256"],
        "backend": job["backend"],
        "extractor_argv": job["extractor_argv"],
        "extractor_contract_digest": job["extractor_contract_digest"],
        "exit_code": exit_code,
    }


def _validated_result_records(value: object, job: dict) -> tuple[dict | None, dict | None]:
    if not isinstance(value, dict):
        return None, {"reason": "result-envelope-root-not-object"}

    expected = _result_metadata(job, 0)
    identity_fields = tuple(key for key in expected if key != "exit_code")
    mismatched = [
        key for key in identity_fields
        if type(value.get(key)) is not type(expected[key]) or value.get(key) != expected[key]
    ]
    if mismatched:
        return None, {
            "reason": "result-envelope-job-mismatch",
            "fields": sorted(mismatched),
        }

    exit_code = value.get("exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        return None, {"reason": "result-envelope-invalid-exit-code"}
    if exit_code != 0:
        return None, {"reason": "extractor-exit-nonzero", "exit_code": exit_code}

    expected_keys = set(expected) | {"records"}
    actual_keys = set(value)
    if actual_keys != expected_keys:
        return None, {
            "reason": "result-envelope-invalid-fields",
            "missing": sorted(expected_keys - actual_keys),
            "unexpected": sorted(actual_keys - expected_keys),
        }
    if not isinstance(value["records"], dict):
        return None, {"reason": "result-envelope-records-not-object"}
    if any(not isinstance(key, str) or not isinstance(record, dict)
           for key, record in value["records"].items()):
        return None, {"reason": "result-envelope-records-invalid"}
    return value["records"], None


def _worker_failure(job: dict, exit_code: int, reason: str) -> dict:
    envelope = _result_metadata(job, exit_code)
    envelope["error"] = reason
    return envelope


def run_job(manifest_path: Path, job_id: str) -> int:
    manifest_path = manifest_path.resolve()
    if (manifest_path.name != "manifest.json"
            or manifest_path.parent.parent.name != "attempts"):
        print("run-job requires an attempt-bound manifest path", file=sys.stderr)
        return 2
    campaign_dir = manifest_path.parents[2]
    try:
        manifest = _load(manifest_path)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"run-job cannot read manifest: {exc}", file=sys.stderr)
        return 2
    if not isinstance(manifest, dict) or manifest.get("attempt_id") != manifest_path.parent.name:
        print("run-job manifest path does not match its attempt_id", file=sys.stderr)
        return 2

    manifest_errors, jobs = _validate_manifest(campaign_dir, manifest)
    if manifest_errors:
        print("run-job rejected manifest: " + "; ".join(manifest_errors), file=sys.stderr)
        return 2
    job = next((item for item in jobs or [] if item["job_id"] == job_id), None)
    if job is None:
        print(f"run-job unknown job_id: {job_id}", file=sys.stderr)
        return 2

    try:
        completed = subprocess.run(
            job["extractor_argv"], cwd=ROOT, check=False,
            capture_output=True, text=True,
        )
    except OSError as exc:
        print(f"run-job extractor launch failed: {exc}", file=sys.stderr)
        print(_stable_json(_worker_failure(job, 127, "extractor-launch-failed")), end="")
        return 127

    if completed.stderr:
        sys.stderr.write(completed.stderr)
    if completed.returncode != 0:
        envelope = _worker_failure(job, completed.returncode, "extractor-nonzero")
        print(_stable_json(envelope), end="")
        return completed.returncode if 1 <= completed.returncode <= 255 else 1

    try:
        records = json.loads(completed.stdout)
    except (TypeError, ValueError):
        envelope = _worker_failure(job, completed.returncode, "extractor-output-invalid-json")
        print(_stable_json(envelope), end="")
        return 2
    if not isinstance(records, dict):
        envelope = _worker_failure(job, completed.returncode,
                                   "extractor-output-root-not-object")
        print(_stable_json(envelope), end="")
        return 2
    if any(not isinstance(key, str) or not isinstance(record, dict)
           for key, record in records.items()):
        envelope = _worker_failure(job, completed.returncode,
                                   "extractor-records-invalid")
        print(_stable_json(envelope), end="")
        return 2

    envelope = _result_metadata(job, completed.returncode)
    envelope["records"] = records
    print(_stable_json(envelope), end="")
    return 0


def report(campaign_dir: Path) -> dict:
    campaign_dir = campaign_dir.resolve()
    documents = []
    total = Counter()
    failures = []
    try:
        manifest = _load(campaign_dir / "manifest.json")
    except (OSError, UnicodeError, ValueError) as exc:
        manifest = None
        failures.append({"reason": "manifest-unreadable", "detail": str(exc)})
        return _write_report_artifacts(campaign_dir, manifest, documents, total, failures)

    manifest_errors, jobs = _validate_manifest(campaign_dir, manifest)
    if manifest_errors:
        names = _manifest_document_names(manifest)
        if names:
            failures.extend({"document": name, "reason": "invalid-manifest",
                             "errors": manifest_errors} for name in names)
        else:
            failures.append({"reason": "invalid-manifest", "errors": manifest_errors})
        return _write_report_artifacts(campaign_dir, manifest, documents, total, failures)

    job_map = {(job["document"], job["backend"]): job for job in jobs or []}
    for document in manifest["documents"]:
        name = document["name"]
        input_errors = _document_input_errors(document)
        if input_errors:
            failures.append({"document": name, "reason": "document-input-mismatch",
                             "input_errors": input_errors})
            continue

        paths = {
            backend: Path(job_map[(name, backend)]["output"])
            for backend in manifest["backends"]
        }
        missing = [
            backend for backend, path in paths.items()
            if path.is_symlink() or not path.is_file()
        ]
        if missing:
            failures.append({"document": name, "attempt_id": manifest["attempt_id"],
                             "missing_backends": missing})
            continue

        backend_records = {}
        backend_errors = []
        for backend, path in paths.items():
            try:
                value = _load(path)
            except (OSError, UnicodeError, ValueError) as exc:
                backend_errors.append({"backend": backend, "reason": "output-unreadable",
                                       "detail": str(exc)})
                continue
            records, result_error = _validated_result_records(
                value, job_map[(name, backend)]
            )
            if result_error:
                backend_errors.append({"backend": backend, **result_error})
                continue
            backend_records[backend] = records
        if backend_errors:
            failures.append({"document": name, "backend_errors": backend_errors})
            continue

        try:
            rows, summary = compare_records(backend_records["pypdf"],
                                            backend_records["builtin"])
        except (AttributeError, TypeError, ValueError) as exc:
            failures.append({"document": name, "reason": "invalid-backend-records",
                             "detail": str(exc)})
            continue
        documents.append({"document": name, "summary": summary, "records": rows})
        total.update(summary)

    return _write_report_artifacts(campaign_dir, manifest, documents, total, failures)


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
    worker_parser = sub.add_parser("run-job")
    worker_parser.add_argument("manifest", type=Path)
    worker_parser.add_argument("--job-id", required=True)
    args = parser.parse_args(argv)
    if args.action == "create":
        documents = _documents(args.pdf_dir, args.doc, args.rs_docs)
        result = create(args.campaign_dir, args.pdf_dir, documents, args.pattern)
        print(_stable_json({"attempt_id": result["attempt_id"],
                            "documents": len(result["documents"]),
                            "jobs": len(result["jobs"])}), end="")
    elif args.action == "run-job":
        return run_job(args.manifest, args.job_id)
    else:
        scorecard = report(args.campaign_dir)
        print(_stable_json(scorecard), end="")
        return 1 if scorecard["failures"] else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
