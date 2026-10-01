#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Universal mutation audit ledger (`mutation-audit-ledger@v1`).

Every data-altering operation (feedback, curation, regeneration, ingest)
appends one JSONL receipt. Existing bytes are never rewritten.

Primary file:  `_src/output/mutation-audit-ledger.jsonl` (runtime, typically
git-ignored via the `output/` rule).
Mirror file:   `docs/evidence/mutation-audit-ledger.jsonl` (tracked evidence).

The mirror is an exact byte copy of the primary after each append, so a lost
runtime file can be recovered from the tracked replica.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import html
import json
import os
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

SCHEMA = "mutation-audit-ledger@v1"
SCHEMA_FIELD = "schema"
LEDGER_NAME = "mutation-audit-ledger.jsonl"
PAGE_NAME = "mutation-ledger.html"

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
PRIMARY_REL = Path("_src") / "output" / LEDGER_NAME
MIRROR_REL = Path("docs") / "evidence" / LEDGER_NAME

PathLike = Union[str, os.PathLike]
_APPEND_LOCK = threading.Lock()

try:
    import fcntl
except ImportError:  # pragma: no cover — non-POSIX fallback
    fcntl = None  # type: ignore[assignment]


class LedgerError(Exception):
    """Raised when a ledger append would lose or corrupt evidence."""


def _utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def discover_root(start: Optional[PathLike] = None) -> Path:
    """Walk from `start` (or this module's repository) to a checkout root.

    A directory counts as a root when it contains `.git` or the existing
    tracked build ledger. Callers that already know their repository pass it
    explicitly to `record_mutation(root=...)` instead of relying on this.
    """
    if start is None:
        return ROOT
    here = Path(start).resolve()
    if here.is_file():
        here = here.parent
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists():
            return candidate
        if (candidate / "docs" / "evidence" / "build-ledger.jsonl").is_file():
            return candidate
    return here


def ledger_paths(root: Optional[PathLike] = None) -> tuple[Path, Path]:
    base = Path(root) if root is not None else ROOT
    base = base.resolve()
    return base / PRIMARY_REL, base / MIRROR_REL


def resolve_ledger_path(root: Optional[PathLike] = None, path: Optional[PathLike] = None) -> Path:
    """Prefer the primary file; fall back to the mirror if the runtime copy is gone."""
    if path is not None:
        return Path(path)
    primary, mirror = ledger_paths(root)
    if primary.is_file():
        return primary
    if mirror.is_file():
        return mirror
    return primary


def sha256_file(path: PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _posix_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _iter_paths(value: Optional[Union[PathLike, Sequence[PathLike]]]) -> list[Path]:
    if value is None:
        return []
    if isinstance(value, (str, os.PathLike)):
        return [Path(value)]
    return [Path(item) for item in value]


def _digest_inputs(paths: Sequence[Path], root: Path) -> list[dict]:
    rows = []
    for path in paths:
        rel = _posix_rel(path, root)
        row: dict[str, Any] = {"path": rel}
        try:
            resolved = path.expanduser()
            if not resolved.exists():
                row["sha256"] = None
                row["missing"] = True
            elif not resolved.is_file():
                row["sha256"] = None
                row["missing"] = True
                row["error"] = "not-a-file"
            else:
                row["sha256"] = sha256_file(resolved)
                row["size"] = resolved.stat().st_size
        except OSError as exc:
            row["sha256"] = None
            row["error"] = str(exc)
        rows.append(row)
    return rows


def _summarize_outputs(paths: Sequence[Path], root: Path) -> list[dict]:
    rows = []
    for path in paths:
        rel = _posix_rel(path, root)
        row: dict[str, Any] = {"path": rel}
        try:
            resolved = path.expanduser()
            if not resolved.exists():
                row["missing"] = True
            elif not resolved.is_file():
                row["missing"] = True
                row["error"] = "not-a-file"
            else:
                stat = resolved.stat()
                row["sha256"] = sha256_file(resolved)
                row["size"] = stat.st_size
                row["mtime"] = datetime.datetime.fromtimestamp(
                    stat.st_mtime, datetime.timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
        except OSError as exc:
            row["error"] = str(exc)
        rows.append(row)
    return rows


def _canonical_payload(entry: Mapping[str, Any]) -> bytes:
    body = {key: value for key, value in entry.items() if key != "receipt_sha256"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_receipt_sha256(entry: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_payload(entry)).hexdigest()


def verify_receipt(entry: Mapping[str, Any]) -> bool:
    expected = entry.get("receipt_sha256")
    if not (isinstance(expected, str) and len(expected) == 64):
        return False
    return expected == compute_receipt_sha256(entry)


def _jsonable(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except (TypeError, ValueError):
        return str(value)


def _serialize_line(entry: Mapping[str, Any]) -> bytes:
    line = json.dumps(entry, ensure_ascii=False, sort_keys=False) + "\n"
    if "\n" in line[:-1] or "\r" in line:
        raise LedgerError("serialized entry must occupy exactly one line")
    return line.encode("utf-8")


def _lock_fd(fd: int) -> None:
    if fcntl is None:
        return
    fcntl.flock(fd, fcntl.LOCK_EX)


def _unlock_fd(fd: int) -> None:
    if fcntl is None:
        return
    fcntl.flock(fd, fcntl.LOCK_UN)


def _append_and_mirror(primary: Path, mirror: Path, payload: bytes) -> None:
    os.makedirs(primary.parent, exist_ok=True)
    os.makedirs(mirror.parent, exist_ok=True)
    lock_path = primary.with_name(primary.name + ".lock")
    with _APPEND_LOCK:
        lock_fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT, 0o644)
        try:
            _lock_fd(lock_fd)
            fd = os.open(str(primary), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            try:
                os.write(fd, payload)
                os.fsync(fd)
            finally:
                os.close(fd)
            data = primary.read_bytes()
            tmp = mirror.with_name(mirror.name + ".tmp")
            tmp_fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            try:
                os.write(tmp_fd, data)
                os.fsync(tmp_fd)
            finally:
                os.close(tmp_fd)
            os.replace(tmp, mirror)
        finally:
            _unlock_fd(lock_fd)
            os.close(lock_fd)


def record_mutation(
    action: str,
    operator: str,
    details: Any,
    inputs: Optional[Union[PathLike, Sequence[PathLike]]] = None,
    outputs: Optional[Union[PathLike, Sequence[PathLike]]] = None,
    success: bool = True,
    metadata: Optional[Mapping[str, Any]] = None,
    root: Optional[PathLike] = None,
    path: Optional[PathLike] = None,
    mirror_path: Optional[PathLike] = None,
    run_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> dict:
    """Append one `mutation-audit-ledger@v1` receipt and return it.

    `receipt_sha256` covers every field except itself, so a later rewrite of
    action, status, or digests is mechanically detectable.
    """
    if not (isinstance(action, str) and action.strip()):
        raise LedgerError("action must be a non-empty string")
    if not (isinstance(operator, str) and operator.strip()):
        raise LedgerError("operator must be a non-empty string")

    base = Path(root).resolve() if root is not None else ROOT
    primary, default_mirror = ledger_paths(base)
    if path is not None:
        primary = Path(path)
    mirror = Path(mirror_path) if mirror_path is not None else default_mirror

    meta = dict(metadata) if metadata else {}
    effective_run_id = run_id or meta.pop("run_id", None) or str(uuid.uuid4())

    entry: dict[str, Any] = {
        SCHEMA_FIELD: SCHEMA,
        "entry_id": str(uuid.uuid4()),
        "timestamp": timestamp or _utc_now_iso(),
        "action": action.strip(),
        "operator": operator.strip(),
        "run_id": str(effective_run_id),
        "status": "ok" if success else "error",
        "details": _jsonable(details),
        "input_digests": _digest_inputs(_iter_paths(inputs), base),
        "output_summary": _summarize_outputs(_iter_paths(outputs), base),
    }
    if meta:
        entry["metadata"] = _jsonable(dict(meta))
    entry["receipt_sha256"] = compute_receipt_sha256(entry)
    _append_and_mirror(primary, mirror, _serialize_line(entry))
    return entry


def _parse_line(line: str, index: int) -> Optional[dict]:
    if not line.strip():
        return None
    try:
        entry = json.loads(line)
    except ValueError:
        return None
    if not isinstance(entry, dict):
        return None
    if entry.get(SCHEMA_FIELD) != SCHEMA:
        return None
    if not verify_receipt(entry):
        return None
    return entry


def read_mutation_entries(
    limit: Optional[int] = None,
    path: Optional[PathLike] = None,
    root: Optional[PathLike] = None,
) -> list[dict]:
    """Return conforming entries in append order (oldest first).

    `limit` keeps the N most recent entries, still in chronological order.
    Malformed or receipt-broken lines are skipped rather than truncating
    later valid history.
    """
    ledger = resolve_ledger_path(root=root, path=path)
    if not ledger.is_file():
        return []
    raw = ledger.read_text(encoding="utf-8")
    lines = raw.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    entries = []
    for index, line in enumerate(lines, start=1):
        parsed = _parse_line(line, index)
        if parsed is not None:
            entries.append(parsed)
    if limit is None:
        return entries
    if limit <= 0:
        return []
    return entries[-limit:]


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _target_files(entry: Mapping[str, Any]) -> str:
    names = []
    for row in list(entry.get("output_summary") or []) + list(entry.get("input_digests") or []):
        if isinstance(row, dict) and row.get("path"):
            names.append(str(row["path"]))
    # Preserve order, drop duplicates.
    seen = set()
    unique = []
    for name in names:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return ", ".join(unique) if unique else "—"


def _status_badge(status: str) -> str:
    kind = "ok" if status == "ok" else "err"
    label = "OK" if status == "ok" else "FEHLER"
    return f'<span class="ml-badge-{kind}">{_esc(label)}</span>'


def render_mutation_ledger_html(entries: Sequence[Mapping[str, Any]]) -> str:
    """Return a full HTML page using the 6-domain shell, Reports active."""
    rows = []
    newest_first = list(reversed(entries))
    if newest_first:
        for entry in newest_first:
            rows.append(
                "<tr>"
                f"<td>{_esc(entry.get('timestamp'))}</td>"
                f"<td><code>{_esc(entry.get('action'))}</code></td>"
                f"<td>{_esc(entry.get('operator'))}</td>"
                f"<td>{_esc(_target_files(entry))}</td>"
                f"<td>{_status_badge(str(entry.get('status') or ''))}</td>"
                f"<td><code>{_esc(entry.get('receipt_sha256'))}</code></td>"
                "</tr>"
            )
        body = "\n".join(rows)
    else:
        body = (
            '<tr><td colspan="6" class="ml-empty">Keine Mutation-Einträge vorhanden. '
            "Datenändernde Werkzeuge schreiben das Ledger beim nächsten Lauf.</td></tr>"
        )

    count = len(entries)
    return f"""<!DOCTYPE html>
<html lang="de" data-theme="light" data-density="comfortable"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="review-github-repo" content="2b-rs/autodocs">
<title>Mutation-Audit-Ledger</title><link rel="stylesheet" href="style.css">
<script>
(function(){{try{{var t=localStorage.getItem("autodocs-theme");var d=localStorage.getItem("autodocs-density");if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t);if(d==="compact"||d==="comfortable")document.documentElement.setAttribute("data-density",d);}}catch(e){{}}}})();
</script>
<script src="fold.js" defer></script><script src="review.js" defer></script><script src="review_request.js" defer></script><script src="_src/static/discuss.js" defer></script><script src="cytoscape.min.js" defer></script><script src="component-graph.js" defer></script><script src="component-inspector.js" defer></script>
<style>
.ml-head{{padding:1.15rem 1.35rem;border:1px solid var(--border-default,#d9dce3);border-radius:14px;background:linear-gradient(135deg,#f7f8ff,#eef5ff);margin:1rem 0 1.4rem}}
.ml-meta{{display:flex;gap:.5rem;flex-wrap:wrap;margin:.6rem 0 0}}
.ml-meta span{{background:#fff;border:1px solid #d7dcea;border-radius:999px;padding:.28rem .66rem;font-size:.88rem}}
.ml-table-wrap{{overflow:auto;max-height:42rem}}
.ml-table{{border-collapse:collapse;width:100%;font-size:.9rem}}
.ml-table th{{position:sticky;top:0;background:#eef1f6;text-align:left;z-index:1}}
.ml-table th,.ml-table td{{padding:.5rem .7rem;border-bottom:1px solid #e4e7ec;vertical-align:top}}
.ml-badge-ok{{color:#166534;background:#dcfce7;border-radius:999px;padding:.15rem .6rem;font-weight:bold}}
.ml-badge-err{{color:#991b1b;background:#fee2e2;border-radius:999px;padding:.15rem .6rem;font-weight:bold}}
.ml-empty{{color:#596274}}
.shell-domains a[aria-current="page"]{{background:rgba(255,255,255,.22);font-weight:600}}
</style>
</head>
<body><a class="skip-link" href="#main">Skip to content</a>
<header class="shell" role="banner"><div class="titleblock"><a class="home" href="index.html">autodocs</a></div>
<nav class="shell-domains" aria-label="Application domains"><a data-domain="explore" href="index.html">Explore</a><a data-domain="trace" href="index.html#component-graph-data">Trace</a><a data-domain="curate" href="curation-report.html">Curate</a><a data-domain="review" href="open-reviews.html">Review</a><a data-domain="work" href="process.html">Work</a><a data-domain="reports" href="mutation-ledger.html" aria-current="page">Reports</a></nav>
<div class="shell-controls"><form class="shell-search" role="search" action="index.html" method="get"><label class="visually-hidden" for="shell-search">Search</label><input id="shell-search" type="search" name="q" placeholder="Search" data-search-input autocomplete="off"><button type="submit" data-search-open>Search</button></form>
<div class="langs"><a class="cur" href="mutation-ledger.html" title="Deutsch" hreflang="de"><img src="flags/de.svg" alt="DE"></a><a href="en/index.html" title="English" hreflang="en"><img src="flags/gb.svg" alt="EN"></a><a href="es/index.html" title="Español" hreflang="es"><img src="flags/es.svg" alt="ES"></a><a href="pt/index.html" title="Português" hreflang="pt"><img src="flags/pt.svg" alt="PT"></a><a href="fr/index.html" title="Français" hreflang="fr"><img src="flags/fr.svg" alt="FR"></a><a href="ru/index.html" title="Русский" hreflang="ru"><img src="flags/ru.svg" alt="RU"></a><a href="ar/index.html" title="العربية" hreflang="ar"><img src="flags/sa.svg" alt="AR"></a><a href="hi/index.html" title="हिन्दी" hreflang="hi"><img src="flags/in.svg" alt="HI"></a><a href="ko/index.html" title="한국어" hreflang="ko"><img src="flags/kr.svg" alt="KO"></a><a href="zh/index.html" title="中文" hreflang="zh"><img src="flags/cn.svg" alt="ZH"></a><a href="nl/index.html" title="Nederlands" hreflang="nl"><img src="flags/nl.svg" alt="NL"></a></div>
<details class="shell-dropdown shell-prefs"><summary class="shell-toggle shell-prefs-toggle" aria-haspopup="true" title="Theme &amp; Density"><span class="prefs-icon" aria-hidden="true">⚙</span> <span class="prefs-label" data-prefs-label>Ansicht</span> <span class="dropdown-caret" aria-hidden="true">▾</span></summary><div class="shell-dropdown-menu"><div class="shell-pref-item"><span class="pref-label">Theme:</span><button type="button" class="shell-toggle" data-theme-toggle aria-pressed="false">Light</button></div><div class="shell-pref-item"><span class="pref-label">Dichte:</span><button type="button" class="shell-toggle" data-density-toggle aria-pressed="false">Comfortable</button></div></div></details>
<button type="button" class="feedback-open" data-feedback-open aria-haspopup="dialog" aria-expanded="false" aria-controls="feedback-dialog">Feedback</button>
</div></header>
<nav class="crumbs"><a href="index.html">Start</a> › <nav class="shell-universe" aria-label="Documentation universe"><details class="universe-dropdown"><summary class="rel" aria-haspopup="true">AUTOSAR Adaptive Platform R25-11 <span class="dropdown-caret" aria-hidden="true">▾</span></summary><div class="universes"><a class="cur" href="index.html" data-universe="autosar-adaptive" title="AUTOSAR Adaptive Platform R25-11">Adaptive</a><a href="classic/index.html" data-universe="classic" title="AUTOSAR Classic Platform R20-11">Classic</a><a href="score/index.html" data-universe="eclipse-score" title="Eclipse S-Core v0.6.0">S-Core</a><a href="eclipse-score-v0.6.0-curation-review/de/index.html" class="universe-review" title="Eclipse S-Core Curation Review Portal">Review</a></div></details></nav> / <a href="process.html">Prozess</a> / <a href="build-reports.html">Build-Bericht</a> / Mutation-Ledger</nav>
<main id="main">
<section class="ml-head">
<h1>Mutation-Audit-Ledger</h1>
<p>Unveränderliche Spur aller datenändernden Operationen: Feedback, Kurationsentscheidungen, Feedback-Loop, Ingest. Jede Zeile trägt eine SHA-256-Quittung über den Eintrag selbst.</p>
<p>Verwandte Berichte: <a href="build-reports.html">Build- &amp; Publikations-Bericht</a> · <a href="process.html">Prozessseite</a>.</p>
<p class="ml-meta"><span>Schema: <code>{_esc(SCHEMA)}</code></span><span>Einträge: <strong>{count}</strong></span><span>Quelle: <code>{_esc(PRIMARY_REL.as_posix())}</code></span><span>Spiegel: <code>{_esc(MIRROR_REL.as_posix())}</code></span></p>
</section>
<div class="ml-table-wrap"><table class="ml-table">
<thead><tr><th>Timestamp</th><th>Action</th><th>Operator</th><th>Target Files</th><th>Status</th><th>Receipt Digest</th></tr></thead>
<tbody>
{body}
</tbody></table></div>
</main>
<footer>Automatisch aus den offiziellen AUTOSAR-R25-11-Spezifikations-PDFs extrahiert
(<a href="https://www.autosar.org/standards/adaptive-platform">autosar.org</a>).
Keine offizielle AUTOSAR-Publikation; Beschreibungstexte im Original (Englisch).</footer></body></html>
"""


def render_mutation_ledger_page(
    root: Optional[PathLike] = None,
    out_path: Optional[PathLike] = None,
    path: Optional[PathLike] = None,
) -> str:
    """Render the audit report and write `mutation-ledger.html`. Returns the HTML."""
    base = Path(root).resolve() if root is not None else ROOT
    entries = read_mutation_entries(root=base, path=path)
    html_text = render_mutation_ledger_html(entries)
    target = Path(out_path) if out_path is not None else base / PAGE_NAME
    os.makedirs(target.parent, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(html_text, encoding="utf-8")
    os.replace(tmp, target)
    return html_text


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Universal mutation audit ledger.")
    sub = parser.add_subparsers(dest="cmd")
    p_render = sub.add_parser("render", help="Write mutation-ledger.html from the current ledger.")
    p_render.add_argument("--root", default=None)
    p_render.add_argument("--out", default=None)
    p_list = sub.add_parser("list", help="Print entries newest first.")
    p_list.add_argument("--root", default=None)
    p_list.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.cmd == "render":
        html_text = render_mutation_ledger_page(root=args.root, out_path=args.out)
        print(f"wrote {len(html_text)} bytes")
        return 0
    if args.cmd == "list":
        limit = args.limit or None
        entries = list(reversed(read_mutation_entries(limit=limit, root=args.root)))
        for entry in entries:
            print(
                f"{entry.get('timestamp')}  {entry.get('status'):<5}  "
                f"{entry.get('action')}  {entry.get('operator')}  "
                f"{(entry.get('receipt_sha256') or '')[:12]}"
            )
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
