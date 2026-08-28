#!/usr/bin/env python3
"""Generate digest-bound Eclipse S-Core curation-candidate views.

The generator exposes release-pinned S-Core material only as unvalidated
candidates. It never writes canonical records or curation-queue state and
never labels a candidate as confirmed, accepted, authoritative, or factual.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

from lxml import html as lxml_html

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import score_extraction_adapter as extraction
import score_normalization as normalization
import score_curation as curation
import validate_score as validation
from prepare_score_curation_export import Links, ensure_link_scope

PROJECT = "ECLIPSE/S-CORE"
RELEASE = "v0.6.0"
IMPORT_DATE = "2026-08-19"
UNVALIDATED_MARKER = "UNVALIDATED — AWAITING CURATOR CONFIRMATION"
PACKAGE = ROOT / "docs/pipeline/eclipse-score-v0.6.0-phase6-curator-package.md"
MANIFEST = ROOT / "_src/spec/campaigns/eclipse-score-v0.6.0.json"
PROFILE = ROOT / "_src/spec/import-profiles/eclipse-score-v0.6.0.json"
PERSISTED_JSON = ROOT / "_src/spec/campaigns/reports/eclipse-score-v0.6.0.validation.json"
PERSISTED_MD = ROOT / "_src/spec/campaigns/reports/eclipse-score-v0.6.0.validation.md"
EXPECTED = {
    "corpus_sha256": "b2898d9c666ac86235875e3230c902908be44a2208c4085a0ec584b8a6e73692",
    "validation_json_sha256": "586158d6386c5858bf45a55c507b861814c1ec3aa0bdd4a368b9fa1eedca30f7",
    "validation_markdown_sha256": "96073d040858245e7c44ba4c4c4c03f22ede7e9ac7f2b17c428140c6f74dd85e",
    "queue_snapshot_sha256": "494662e83e3d4a1e0f97909437d5e09c2965413b500a047a8946ee711b486df7",
    "curator_package_sha256": "368c7a2234286d621b73749541afcf023ca9f07966bd15b0e5a11838ed605700",
}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def reproduce() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest, profile = load(MANIFEST), load(PROFILE)
    raw = extraction.extract(manifest, profile, ROOT)
    corpus = normalization.normalize(raw, IMPORT_DATE)
    report = validation.validate_corpus(corpus, manifest)
    if not report.get("passed"):
        raise ValueError("reproduced Phase-6 validation did not pass")
    if sha256(canonical(corpus)) != EXPECTED["corpus_sha256"]:
        raise ValueError("corpus digest drift expires the curator decision")
    if sha256(canonical(report)) != EXPECTED["validation_json_sha256"]:
        raise ValueError("validation JSON digest drift expires the curator decision")
    if sha256(validation.render_markdown(report).encode("utf-8")) != EXPECTED["validation_markdown_sha256"]:
        raise ValueError("validation Markdown digest drift expires the curator decision")
    if PERSISTED_JSON.read_bytes() != canonical(report) or PERSISTED_MD.read_text(encoding="utf-8") != validation.render_markdown(report):
        raise ValueError("persisted validation report differs from reproduced evidence")
    package = PACKAGE.read_text(encoding="utf-8")
    for digest in EXPECTED.values():
        if digest not in package:
            raise ValueError(f"Phase-6 package is missing required binding {digest}")
    candidate = corpus.get("exception_candidates", [])
    if len(candidate) != 1:
        raise ValueError("the pinned corpus requires exactly one unresolved exception candidate")
    queue = curation._candidate_item(candidate[0], "2026-08-20T00:13:00Z")
    if sha256(canonical(queue)) != EXPECTED["queue_snapshot_sha256"]:
        raise ValueError("queue snapshot digest drift expires the curator decision")
    return corpus, report, queue


def source_locator(record: Mapping[str, Any]) -> str:
    provenance = record.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("candidate lacks provenance")
    repository = provenance.get("source_repo_url")
    commit = provenance.get("source_commit")
    locator = provenance.get("source_locator")
    if not isinstance(repository, str) or not isinstance(commit, str) or not isinstance(locator, Mapping):
        raise ValueError("candidate lacks a release-pinned source locator")
    path, start, end = locator.get("path"), locator.get("line_start"), locator.get("line_end")
    if not isinstance(path, str) or not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("candidate source locator is malformed")
    return f"{repository.removesuffix('.git')}/blob/{commit}/{path}#L{start}-L{end}"


def record_path(record: Mapping[str, Any]) -> str:
    version_id = record.get("version_id")
    if not isinstance(version_id, str) or not version_id:
        raise ValueError("candidate lacks version_id")
    return "records/" + hashlib.sha256(version_id.encode("utf-8")).hexdigest()[:24] + ".html"


def public_record(record: Mapping[str, Any], collision_canonical_id: str) -> dict[str, Any]:
    status = record.get("status")
    provenance = record.get("provenance")
    history = record.get("history")
    if not isinstance(status, Mapping) or status.get("state") != "invalid/to-be-confirmed":
        raise ValueError("every public candidate must remain invalid/to-be-confirmed")
    if not isinstance(provenance, Mapping) or not isinstance(history, list):
        raise ValueError("candidate provenance/history is malformed")
    canonical_id = record.get("canonical_id")
    version_id = record.get("version_id")
    description = record.get("description")
    if not isinstance(canonical_id, str) or not isinstance(version_id, str):
        raise ValueError("candidate identity is malformed")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("candidate lacks extracted source-derived content")
    return {
        "canonical_id": canonical_id,
        "version_id": version_id,
        "title": str(record.get("title") or record.get("id") or canonical_id),
        "kind": record.get("kind"),
        "source_derived_content": "\n".join(line.rstrip() for line in description.splitlines()),
        "status": {"state": status["state"], "reason": status.get("reason")},
        "history": history,
        "source_locator": source_locator(record),
        "provenance": {
            "source_repo_origin": provenance.get("source_repo_origin"),
            "source_ref": provenance.get("source_ref"),
            "source_ref_kind": provenance.get("source_ref_kind"),
            "source_commit": provenance.get("source_commit"),
            "source_path": provenance.get("source_path"),
        },
        "page": record_path(record),
        "unresolved_collision": canonical_id == collision_canonical_id,
    }


def view_model(corpus: Mapping[str, Any], report: Mapping[str, Any], queue: Mapping[str, Any]) -> dict[str, Any]:
    totals = report["totals"]
    kinds = totals["records_by_kind"]
    statuses = totals["records_by_status"]
    if totals["records"] != 2239 or statuses != {"invalid/to-be-confirmed": 2239}:
        raise ValueError("only the exact all-unvalidated pinned corpus is authorized")
    if set(kinds) != {"module", "component", "design-doc", "process-doc"}:
        raise ValueError("all four candidate-kind summaries are required")
    unresolved = queue["decision_basis"]
    collision = unresolved["record_locator"]["canonical_id"]
    raw_records = corpus.get("records")
    if not isinstance(raw_records, list) or len(raw_records) != 2239:
        raise ValueError("the pinned corpus must contain exactly 2,239 records")
    records = sorted((public_record(record, collision) for record in raw_records), key=lambda item: (item["canonical_id"], item["version_id"]))
    if len({record["page"] for record in records}) != 2239:
        raise ValueError("candidate page paths must be unique")
    collision_records = [record for record in records if record["unresolved_collision"]]
    if len(collision_records) != 1:
        raise ValueError("the existing unresolved collision must map to exactly one candidate page")
    manifest = [{key: record[key] for key in ("canonical_id", "version_id", "page", "status", "source_locator", "unresolved_collision")} for record in records]
    return {
        "schema": "score-curation-candidate-view@v2",
        "scope": "unvalidated-curation-candidates",
        "project": PROJECT,
        "release": RELEASE,
        "decision_id": "CUR-0019-08-20260820",
        "validation_marker": UNVALIDATED_MARKER,
        "input_digests": EXPECTED,
        "counts": {"records": 2239, "candidate_pages": 2239, "by_kind": kinds, "by_status": statuses, "exceptions": 1, "queue_items": 1, "source_exclusions": 2},
        "candidate_manifest_sha256": sha256(canonical(manifest)),
        "records": records,
        "unresolved": {
            "candidate_id": unresolved["exception_candidate_id"],
            "queue_id": queue["queue_id"], "canonical_id": collision,
            "version_ids": unresolved["record_locator"]["version_ids"], "status": "invalid/to-be-confirmed",
            "review_state": queue["lifecycle_state"], "history": queue["history"],
            "source_locator": queue["decision_basis"]["source_locator_url"],
            "exception_kind": queue["current_state"]["exception_kind"],
            "candidate_page": collision_records[0]["page"],
        },
        "exclusions": ["tooling", "docs-as-code"],
    }


def document(title: str, body: str, *, local_prefix: str, root_prefix: str, review_request: bool = False) -> str:
    review_script = f'<script src="{root_prefix}review_request.js" defer></script>' if review_request else ""
    return f'''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="review-github-repo" content="2b-rs/autodocs"><title>{html.escape(title)}</title>
<link rel="stylesheet" href="{local_prefix}style.css">{review_script}</head>
<body data-view-scope="unvalidated-curation-candidates" data-validation-state="unvalidated"><main>
<p class="scope unvalidated-marker" data-unvalidated-marker="awaiting-curator-confirmation"><strong>{UNVALIDATED_MARKER}</strong> This release-pinned candidate has not been confirmed by a curator.</p>
<nav><a href="{local_prefix}index.html">Summary</a> <a href="{local_prefix}records/index.html">All candidates</a> <a href="{local_prefix}participate.html">Participate in curation</a> <a href="{local_prefix}unresolved.html">Unresolved collision</a> <a href="{local_prefix}evidence.json">Evidence</a></nav>
{body}
<p id="client-render-state" data-client-render="pending">Static unvalidated-candidate marker loaded.</p>
</main><script src="{local_prefix}assets/view.js"></script></body></html>
'''


def detail_list(label: str, value: str) -> str:
    return f"<dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd>"


def render_record(record: Mapping[str, Any]) -> bytes:
    history = "".join("<li>" + html.escape(f"{item.get('from')} → {item.get('to')} by {item.get('actor')} on {item.get('date')}: {item.get('reason')}") + "</li>" for item in record["history"])
    provenance = record["provenance"]
    rows = "".join((
        detail_list("Canonical ID", record["canonical_id"]),
        detail_list("Version ID", record["version_id"]),
        detail_list("Candidate kind", str(record["kind"])),
        detail_list("Source repository", str(provenance["source_repo_origin"])),
        detail_list("Release ref", f"{provenance['source_ref_kind']}: {provenance['source_ref']}"),
        detail_list("Pinned commit", str(provenance["source_commit"])),
        detail_list("Source path", str(provenance["source_path"])),
    ))
    collision = '<p data-unresolved-collision="true"><strong>Known unresolved collision:</strong> this candidate is also linked from the collision review page.</p>' if record["unresolved_collision"] else ""
    request_data = json.dumps({"canonical_id": record["canonical_id"], "version_id": record["version_id"], "status": record["status"]["state"], "source_url": record["source_locator"], "category_default": "factual-accuracy"}, ensure_ascii=False).replace("</", "<\\/")
    participation = f'''<section id="participate" data-curation-route="review-request">
<h2>Participate in curation</h2><p>Use the established review-request flow to provide evidence or flag a concern. Exporting a package does not change this candidate. Direct issue submission is available only after the viewer explicitly authenticates with GitHub.</p>
<div data-review-request-root><script type="application/json" class="review-request-data">{request_data}</script><button type="button" data-review-request-open>Flag this unvalidated candidate for review</button><p data-review-request-state hidden></p></div></section>'''
    body = f'''<h1>{html.escape(str(record["title"]))}</h1>
<section id="candidate-status" data-validation-state="unvalidated"><h2>Validation status</h2><p><strong>{UNVALIDATED_MARKER}</strong></p><p>{html.escape(str(record["status"]["reason"]))}</p></section>
<section id="source-derived-content" data-validation-state="unvalidated"><h2>Source-derived candidate content — unvalidated</h2><p><strong>{UNVALIDATED_MARKER}</strong> Extracted directly from the release-pinned source; it has not been curator-confirmed.</p><pre>{html.escape(str(record["source_derived_content"]))}</pre></section>
<section id="source-provenance"><h2>Release-pinned source provenance</h2><dl>{rows}<dt>Source locator</dt><dd><a id="source-locator" href="{html.escape(record["source_locator"], quote=True)}">Open release-pinned source</a></dd></dl></section>
<section id="record-history"><h2>Candidate history</h2><ol>{history}</ol></section>{collision}{participation}'''
    return document(str(record["title"]), body, local_prefix="../", root_prefix="../", review_request=True).encode("utf-8")


def render(model: Mapping[str, Any]) -> dict[str, bytes]:
    records = model["records"]
    cards = "".join(f'<article data-kind="{html.escape(kind)}"><h2>{html.escape(kind)}</h2><p>{count} unvalidated candidates</p></article>' for kind, count in model["counts"]["by_kind"].items())
    listing = "".join(f'<li data-candidate="unvalidated"><a href="{html.escape(record["page"].removeprefix("records/"), quote=True)}">{html.escape(record["canonical_id"])}</a><br><code>{html.escape(record["version_id"])}</code></li>' for record in records)
    summary = f'''<h1>Eclipse S-Core v0.6.0 candidate review summary</h1>
<section id="kind-summary" data-record-count="2239">{cards}</section>
<section id="reconciliation"><h2>Reconciliation</h2><p>2,239 release-pinned candidates; all 2,239 are <code>invalid/to-be-confirmed</code>; 1 unresolved collision; 2 source exclusions.</p><p><a href="records/index.html">Browse all 2,239 unvalidated candidates</a>.</p></section>
<section id="authority"><h2>Scope and provenance</h2><p>Decision <code>{model["decision_id"]}</code> binds the pinned corpus and input digests. Source provenance identifies where a candidate came from; it is separate from its unvalidated status.</p></section>'''
    all_candidates = f'''<h1>All 2,239 unvalidated S-Core candidates</h1><p id="candidate-list-marker">Every item below is {UNVALIDATED_MARKER.lower()}.</p><ol id="candidate-list">{listing}</ol>'''
    unresolved = model["unresolved"]
    history = "".join(f"<li>{html.escape(item['from'])} → {html.escape(item['to'])} by {html.escape(item['actor'])} at {html.escape(item['at'])}</li>" for item in unresolved["history"])
    versions = "<br>".join(f"<code>{html.escape(version)}</code>" for version in unresolved["version_ids"])
    detail = f'''<h1>Unresolved S-Core collision review case</h1><section id="unresolved-case" data-review-indicator="unresolved" data-validation-state="unvalidated"><p><strong>{UNVALIDATED_MARKER}</strong></p><dl><dt>Canonical identity</dt><dd><code>{html.escape(unresolved["canonical_id"])}</code></dd><dt>Version identity</dt><dd>{versions}</dd><dt>Queue state</dt><dd><code>{html.escape(unresolved["review_state"])}</code></dd><dt>Traceability</dt><dd><a id="source-locator" href="{html.escape(unresolved["source_locator"], quote=True)}">Release-pinned source locator</a></dd></dl><p><a href="{html.escape(unresolved["candidate_page"], quote=True)}">Open its candidate record view</a></p><h2>History</h2><ol id="record-history">{history}</ol></section>'''
    participate = '''<h1>Participate in S-Core curation</h1><section id="participation-route" data-curation-route="review-request"><p>Each candidate record provides the established browser review-request action. It identifies the pinned canonical ID, version ID, source locator, and current unvalidated status. Without GitHub authentication, the action only exports a review-request package; it does not alter any candidate, queue, or decision. A viewer may explicitly authenticate to submit that package as a GitHub issue for the existing review process.</p><p><a href="process.html">Open the local curation process report</a>.</p></section>'''
    process_report = '''<h1>S-Core curation process</h1><section id="flag-for-review-protocol"><h2>Flag-for-review protocol</h2><p>The review-request action exports a local JSON package when no verified GitHub token is supplied. Direct issue submission requires an explicitly supplied token and successful GitHub identity verification.</p></section><section id="storage-and-privacy"><h2>Storage and privacy</h2><p>The established client stores a token only in the viewer's browser local storage. This generated candidate contains no credential and grants no review, publication, or acceptance authority.</p></section>'''
    manifest = [{key: record[key] for key in ("canonical_id", "version_id", "page", "status", "source_locator", "unresolved_collision")} for record in records]
    evidence = canonical({"schema": model["schema"], "scope": model["scope"], "validation_marker": model["validation_marker"], "counts": model["counts"], "input_digests": model["input_digests"], "candidate_manifest_sha256": model["candidate_manifest_sha256"], "candidate_manifest": manifest, "exclusions": model["exclusions"], "unresolved": model["unresolved"]})
    validation_evidence = canonical({"schema": "score-curation-candidate-validation@v2", "result": "PASS", "scope": model["scope"], "counts": model["counts"], "candidate_manifest_sha256": model["candidate_manifest_sha256"], "input_digests": model["input_digests"], "checks": {"reproduced_pinned_inputs": "PASS", "every_candidate_unvalidated": "PASS", "listing_marker": "PASS", "individual_marker": "PASS", "source_and_validation_separated": "PASS", "no_javascript_marker": "PASS", "client_render_marker": "required during check --client-check", "participation_route": "existing review-request flow", "known_collision": "PASS"}})
    assertions = canonical({"schema": "score-curation-candidate-dom-assertions@v2", "marker": UNVALIDATED_MARKER, "pages": {"index.html": ["body[data-validation-state='unvalidated']", "#kind-summary", "#client-render-state[data-client-render='pending']"], "records/index.html": ["#candidate-list", "#candidate-list-marker"], "unresolved.html": ["#unresolved-case[data-validation-state='unvalidated']", "#record-history"]}, "population": {"record_pages": 2239, "record_selector": "#candidate-status[data-validation-state='unvalidated']", "participation_selector": "[data-curation-route='review-request']"}})
    css = b"body{font-family:system-ui;line-height:1.45;margin:2rem;max-width:75rem}.scope{padding:1rem;background:#fff3cd;border:3px solid #8a5200;font-weight:700;font-size:1.1rem}article{border:1px solid #bbb;padding:1rem;margin:.5rem;display:inline-block}code{overflow-wrap:anywhere}dt{font-weight:bold;margin-top:.7rem}li[data-candidate]{margin:.7rem 0}button{font:inherit;padding:.5rem .8rem}\n"
    js = b"document.addEventListener('DOMContentLoaded',()=>{const state=document.getElementById('client-render-state');state.dataset.clientRender='verified';state.textContent='Client rendering verified; unvalidated marker remains visible.';});\n"
    snapshot = lambda title: f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"><rect width="100%" height="100%" fill="#fff"/><text x="50" y="90" font-family="sans-serif" font-size="36">{html.escape(title)}</text><text x="50" y="170" font-family="sans-serif" font-size="24">{UNVALIDATED_MARKER}</text><text x="50" y="220" font-family="sans-serif" font-size="24">2,239 release-pinned curation candidates; one unresolved collision</text></svg>\n'''.encode()
    files: dict[str, bytes] = {
        "index.html": document("S-Core candidate review summary", summary, local_prefix="", root_prefix="../../../").encode(),
        "en/index.html": document("S-Core candidate review summary", summary.replace('href="records/index.html"', 'href="../records/index.html"'), local_prefix="../", root_prefix="../../../../").encode(),
        "records/index.html": document("All S-Core candidates", all_candidates, local_prefix="../", root_prefix="../../../../").encode(),
        "participate.html": document("Participate in S-Core curation", participate, local_prefix="", root_prefix="../../../").encode(),
        "process.html": document("S-Core curation process", process_report, local_prefix="", root_prefix="").encode(),
        "unresolved.html": document("S-Core unresolved collision", detail, local_prefix="", root_prefix="../../../").encode(),
        "en/unresolved.html": document("S-Core unresolved collision", detail.replace(f'href="{unresolved["candidate_page"]}"', f'href="../{unresolved["candidate_page"]}"'), local_prefix="../", root_prefix="../../../../").encode(),
        "evidence.json": evidence, "validation.json": validation_evidence, "dom-assertions.json": assertions,
        "style.css": css, "assets/view.js": js,
        "screenshots/summary.svg": snapshot("S-Core candidate review summary"),
        "screenshots/unresolved.svg": snapshot("S-Core unresolved collision"),
    }
    review_client = (ROOT / "review_request.js").read_bytes()
    if hashlib.sha256(review_client).hexdigest() != "bd6e23ae7454e7dee4daba98a104fa76db0ef9cdf54713ef35569a6c992ef0e2":
        raise ValueError("canonical review_request.js identity mismatch")
    if hashlib.sha256(css).hexdigest() != "7fa99621f52bac786f6793024eda694f0d54454cd8715bc346292c6c5d0d133c":
        raise ValueError("generated stylesheet identity mismatch")
    files["review_request.js"] = review_client
    for record in records:
        files[record["page"]] = render_record(record)
    # The Feature integrator placed its independent review evidence in this
    # directory after 0019-09. Carry it through atomic rebuilds verbatim; it is
    # historical review evidence, not an output regenerated from the corpus.
    retained = ROOT / "docs/campaign-evidence/eclipse-score-v0.6.0-curation-review"
    for review in sorted(retained.glob("integration-review-*.md")):
        files[review.name] = review.read_bytes()
    for receipt_dir in sorted(retained.glob("publication-*")):
        if not receipt_dir.is_dir() or receipt_dir.is_symlink():
            raise ValueError(f"unsafe retained publication receipt: {receipt_dir.name}")
        for receipt in sorted(receipt_dir.rglob("*")):
            if receipt.is_symlink() or (not receipt.is_dir() and not receipt.is_file()):
                raise ValueError(f"unsafe retained publication receipt path: {receipt.relative_to(retained)}")
            if receipt.is_file():
                files[receipt.relative_to(retained).as_posix()] = receipt.read_bytes()
    return files


def write_tree(output: Path, files: Mapping[str, bytes]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    try:
        for name, payload in files.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        if output.exists():
            shutil.rmtree(output)
        os.replace(staging, output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def selector_xpath(selector: str) -> str:
    import re
    if selector.startswith("#"):
        identifier = selector[1:].split("[", 1)[0]
        attrs = re.findall(r"\[([^=]+)='([^']+)'\]", selector)
        terms = [f"@id='{identifier}'"] + [f"@{name}='{value}'" for name, value in attrs]
        return "//*[" + " and ".join(terms) + "]"
    match = re.fullmatch(r"([A-Za-z]+)(?:\[([^=]+)='([^']+)'\])?", selector)
    if not match:
        raise ValueError(f"unsupported DOM assertion selector: {selector}")
    tag, name, value = match.groups()
    return f"//{tag}" if name is None else f"//{tag}[@{name}='{value}']"


def validate_tree(output: Path, expected: Mapping[str, bytes], client: bool) -> None:
    actual = {path.relative_to(output).as_posix(): path.read_bytes() for path in output.rglob("*") if path.is_file()}
    if actual != dict(expected):
        raise ValueError("generated tree differs from deterministic expected output")
    assertions = json.loads(actual["dom-assertions.json"])
    for page, selectors in assertions["pages"].items():
        doc = lxml_html.fromstring(actual[page])
        for selector in selectors:
            if not doc.xpath(selector_xpath(selector)):
                raise ValueError(f"DOM assertion failed: {page} {selector}")
    pages = sorted(path for path in (output / "records").glob("*.html") if path.name != "index.html")
    if len(pages) != 2239:
        raise ValueError(f"expected 2,239 candidate pages, found {len(pages)}")
    marker = assertions["marker"]
    for page in pages:
        text = page.read_text(encoding="utf-8")
        doc = lxml_html.fromstring(text)
        if marker not in text or not doc.xpath("//*[@data-unvalidated-marker='awaiting-curator-confirmation']"):
            raise ValueError(f"candidate marker missing: {page.relative_to(output)}")
        if not doc.xpath("//*[@id='candidate-status' and @data-validation-state='unvalidated']"):
            raise ValueError(f"candidate status marker missing: {page.relative_to(output)}")
        source_content = doc.xpath("//*[@id='source-derived-content' and @data-validation-state='unvalidated']/pre")
        if len(source_content) != 1 or not source_content[0].text_content().strip():
            raise ValueError(f"candidate source-derived content missing: {page.relative_to(output)}")
        if doc.xpath("//*[@id='source-derived-content']//script"):
            raise ValueError(f"unsafe candidate source-derived content: {page.relative_to(output)}")
        if not doc.xpath("//*[@id='source-provenance']//*[@id='source-locator']"):
            raise ValueError(f"candidate source provenance missing: {page.relative_to(output)}")
        if not doc.xpath("//*[@id='record-history']") or not doc.xpath("//*[@data-curation-route='review-request']"):
            raise ValueError(f"candidate history or curation route missing: {page.relative_to(output)}")
        for prohibited in ('data-validation-state="valid"', 'data-validation-state="accepted"', 'data-factual-publication="true"', 'data-authoritative="true"'):
            if prohibited in text:
                raise ValueError(f"misleading candidate marker: {page.relative_to(output)}")
    for page, payload in actual.items():
        if not page.endswith(".html"):
            continue
        doc = lxml_html.fromstring(payload)
        if marker not in payload.decode("utf-8"):
            raise ValueError(f"no-JavaScript marker missing: {page}")
        links = Links()
        links.feed(payload.decode("utf-8"))
        ensure_link_scope(output, page, links)
    if client:
        checker = ROOT / "_src/tools/check_score_curation_views.cjs"
        run = subprocess.run(["node", str(checker), str(output)], text=True, capture_output=True, timeout=180, check=False)
        if run.returncode:
            raise ValueError(f"client-render check failed: {run.stderr.strip()}")
        result = json.loads(run.stdout)
        if result.get("checked") != len([name for name in actual if name.endswith(".html")]) or result.get("state") != "verified":
            raise ValueError("client-render coverage is incomplete")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--client-check", action="store_true")
    args = parser.parse_args()
    corpus, report, queue = reproduce()
    files = render(view_model(corpus, report, queue))
    if args.command == "build":
        write_tree(args.output, files)
    validate_tree(args.output, files, args.client_check)
    print(f"PASS {args.command}: {len(files)} files; 2,239 unvalidated candidate pages; 1 unresolved collision")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
