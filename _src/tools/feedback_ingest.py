#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feedback_ingest.py — User-feedback envelope ingest (user-feedback-envelope@v1).

Validates browser/form submissions without GitHub PATs, builds a canonical
envelope, attaches a SHA-256 receipt hash over the envelope excluding
``receipt_hash``, and appends an atomic queue file under
``_src/spec/feedback-queue/<timestamp>-<id>.json``.

This module is the server-side counterpart of the dialog in ``review_request.js``.
It never reads or writes browser tokens.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

SCHEMA = "user-feedback-envelope@v1"
DEFAULT_QUEUE_DIR = Path(__file__).resolve().parents[1] / "spec" / "feedback-queue"

CATEGORIES: dict[str, str] = {
    "inhaltlich": "Inhaltlich",
    "fehlende_information": "Fehlende Information",
    "uebersetzungsfehler": "Übersetzungsfehler",
    "unklarheit": "Unklarheit",
    "typo": "Typo",
}
_CATEGORY_BY_LABEL = {label.casefold(): key for key, label in CATEGORIES.items()}

SEVERITIES: dict[str, str] = {
    "blocker": "Blocker",
    "major": "Major",
    "minor": "Minor",
    "editorial": "Editorial",
}
_SEVERITY_BY_LABEL = {label.casefold(): key for key, label in SEVERITIES.items()}

ENVELOPE_FIELDS = (
    "schema",
    "feedback_id",
    "submitted_at",
    "target_id",
    "category",
    "severity",
    "title",
    "description",
    "proposed_change",
    "submitter",
    "status",
    "receipt_hash",
)
INPUT_FIELDS = (
    "target_id",
    "category",
    "severity",
    "title",
    "description",
    "proposed_change",
    "submitter",
)
STATUSES = ("queued", "submitted")

MAX_TARGET = 256
MAX_TITLE = 200
MIN_TITLE = 3
MAX_DESCRIPTION = 20000
MIN_DESCRIPTION = 10
MAX_PROPOSED = 20000
MAX_SUBMITTER = 120
MAX_BODY_BYTES = 256 * 1024

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_FEEDBACK_ID_RE = re.compile(
    r"^uf-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


class FeedbackIngestError(ValueError):
    """Raised when a submission fails validation before any queue write."""


def canonical_json_bytes(value: Any) -> bytes:
    """Deterministic UTF-8 JSON used as the receipt-hash preimage."""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def compute_receipt_hash(envelope_without_hash: Mapping[str, Any]) -> str:
    if "receipt_hash" in envelope_without_hash:
        envelope_without_hash = {
            key: val
            for key, val in envelope_without_hash.items()
            if key != "receipt_hash"
        }
    return hashlib.sha256(canonical_json_bytes(envelope_without_hash)).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_feedback_id() -> str:
    return "uf-" + str(uuid.uuid4())


def _clean_text(value: Any, *, field: str, max_len: int, required: bool) -> str:
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    else:
        raise FeedbackIngestError(f"{field}: string required")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if _CONTROL_RE.search(text):
        raise FeedbackIngestError(f"{field}: control characters are not allowed")
    text = text.strip()
    if required and not text:
        raise FeedbackIngestError(f"{field}: required")
    if len(text) > max_len:
        raise FeedbackIngestError(f"{field}: exceeds {max_len} characters")
    return text


def normalize_category(value: Any) -> str:
    text = _clean_text(value, field="category", max_len=64, required=True)
    key = text.casefold().replace(" ", "_").replace("-", "_")
    if key in CATEGORIES:
        return key
    mapped = _CATEGORY_BY_LABEL.get(text.casefold())
    if mapped:
        return mapped
    raise FeedbackIngestError("category: must be one of " + ", ".join(CATEGORIES))


def normalize_severity(value: Any) -> str:
    text = _clean_text(value, field="severity", max_len=32, required=True)
    key = text.casefold()
    if key in SEVERITIES:
        return key
    mapped = _SEVERITY_BY_LABEL.get(text.casefold())
    if mapped:
        return mapped
    raise FeedbackIngestError("severity: must be one of " + ", ".join(SEVERITIES))


def validate_form(payload: Mapping[str, Any]) -> dict[str, str]:
    """Return normalized form fields or raise FeedbackIngestError."""
    if not isinstance(payload, Mapping):
        raise FeedbackIngestError("payload: object required")
    unknown = sorted(
        set(payload)
        - set(INPUT_FIELDS)
        - {"schema", "feedback_id", "submitted_at", "status", "page_url", "receipt_hash"}
    )
    if unknown:
        raise FeedbackIngestError(f"unknown field: {unknown[0]}")
    target_id = _clean_text(payload.get("target_id"), field="target_id", max_len=MAX_TARGET, required=True)
    title = _clean_text(payload.get("title"), field="title", max_len=MAX_TITLE, required=True)
    if len(title) < MIN_TITLE:
        raise FeedbackIngestError(f"title: at least {MIN_TITLE} characters")
    description = _clean_text(
        payload.get("description"), field="description", max_len=MAX_DESCRIPTION, required=True
    )
    if len(description) < MIN_DESCRIPTION:
        raise FeedbackIngestError(f"description: at least {MIN_DESCRIPTION} characters")
    proposed = _clean_text(
        payload.get("proposed_change"), field="proposed_change", max_len=MAX_PROPOSED, required=False
    )
    submitter = _clean_text(
        payload.get("submitter"), field="submitter", max_len=MAX_SUBMITTER, required=False
    )
    return {
        "target_id": target_id,
        "category": normalize_category(payload.get("category")),
        "severity": normalize_severity(payload.get("severity")),
        "title": title,
        "description": description,
        "proposed_change": proposed,
        "submitter": submitter,
    }


def build_envelope(
    payload: Mapping[str, Any],
    *,
    feedback_id: str | None = None,
    submitted_at: str | None = None,
    status: str = "queued",
) -> dict[str, str]:
    fields = validate_form(payload)
    fid = feedback_id or _new_feedback_id()
    if not _FEEDBACK_ID_RE.fullmatch(fid):
        raise FeedbackIngestError("feedback_id: malformed")
    ts = submitted_at or _now_iso()
    if not _ISO_RE.fullmatch(ts):
        raise FeedbackIngestError("submitted_at: ISO-8601 UTC required")
    if status not in STATUSES:
        raise FeedbackIngestError("status: must be queued or submitted")
    body = {
        "schema": SCHEMA,
        "feedback_id": fid,
        "submitted_at": ts,
        "target_id": fields["target_id"],
        "category": fields["category"],
        "severity": fields["severity"],
        "title": fields["title"],
        "description": fields["description"],
        "proposed_change": fields["proposed_change"],
        "submitter": fields["submitter"],
        "status": status,
    }
    body["receipt_hash"] = compute_receipt_hash(body)
    return body


def verify_receipt(envelope: Mapping[str, Any]) -> bool:
    if not isinstance(envelope, Mapping) or envelope.get("schema") != SCHEMA:
        return False
    claimed = envelope.get("receipt_hash")
    if not isinstance(claimed, str) or len(claimed) != 64:
        return False
    try:
        int(claimed, 16)
    except ValueError:
        return False
    actual = compute_receipt_hash(
        {key: val for key, val in envelope.items() if key != "receipt_hash"}
    )
    return actual == claimed


def queue_filename(envelope: Mapping[str, str]) -> str:
    stamp = str(envelope["submitted_at"]).replace("-", "").replace(":", "")
    return f"{stamp}-{envelope['feedback_id']}.json"


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=".fb-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def write_queue_file(
    envelope: Mapping[str, Any],
    queue_dir: Path | None = None,
) -> Path:
    if not verify_receipt(envelope):
        raise FeedbackIngestError("receipt_hash: mismatch")
    directory = Path(queue_dir) if queue_dir is not None else DEFAULT_QUEUE_DIR
    directory = directory.resolve()
    name = queue_filename(envelope)
    if "/" in name or "\\" in name or name in {".", ".."}:
        raise FeedbackIngestError("queue filename: rejected")
    path = (directory / name).resolve()
    if path.parent != directory:
        raise FeedbackIngestError("queue path: escaped directory")
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing != dict(envelope):
            raise FeedbackIngestError("queue file: conflicting envelope for the same id")
        return path
    atomic_write_json(path, envelope)
    return path


def ingest_existing_envelope(
    payload: Mapping[str, Any],
    *,
    queue_dir: Path | None = None,
) -> dict[str, Any]:
    """Store a client-built envelope after re-validating fields and receipt."""
    if payload.get("schema") != SCHEMA:
        raise FeedbackIngestError("schema: user-feedback-envelope@v1 required")
    validate_form(payload)
    fid = payload.get("feedback_id")
    ts = payload.get("submitted_at")
    st = payload.get("status")
    if not isinstance(fid, str) or not _FEEDBACK_ID_RE.fullmatch(fid):
        raise FeedbackIngestError("feedback_id: malformed")
    if not isinstance(ts, str) or not _ISO_RE.fullmatch(ts):
        raise FeedbackIngestError("submitted_at: ISO-8601 UTC required")
    if st not in STATUSES:
        raise FeedbackIngestError("status: must be queued or submitted")
    envelope = {
        "schema": SCHEMA,
        "feedback_id": fid,
        "submitted_at": ts,
        "target_id": _clean_text(payload.get("target_id"), field="target_id", max_len=MAX_TARGET, required=True),
        "category": normalize_category(payload.get("category")),
        "severity": normalize_severity(payload.get("severity")),
        "title": _clean_text(payload.get("title"), field="title", max_len=MAX_TITLE, required=True),
        "description": _clean_text(payload.get("description"), field="description", max_len=MAX_DESCRIPTION, required=True),
        "proposed_change": _clean_text(payload.get("proposed_change"), field="proposed_change", max_len=MAX_PROPOSED, required=False),
        "submitter": _clean_text(payload.get("submitter"), field="submitter", max_len=MAX_SUBMITTER, required=False),
        "status": st,
        "receipt_hash": payload.get("receipt_hash"),
    }
    if not verify_receipt(envelope):
        raise FeedbackIngestError("receipt_hash: mismatch")
    path = write_queue_file(envelope, queue_dir)
    return {
        "ok": True,
        "feedback_id": envelope["feedback_id"],
        "receipt_hash": envelope["receipt_hash"],
        "status": envelope["status"],
        "path": str(path),
        "envelope": envelope,
    }


def ingest(
    payload: Mapping[str, Any],
    *,
    queue_dir: Path | None = None,
    status: str = "submitted",
) -> dict[str, Any]:
    if isinstance(payload, Mapping) and payload.get("schema") == SCHEMA:
        return ingest_existing_envelope(payload, queue_dir=queue_dir)
    envelope = build_envelope(payload, status=status)
    path = write_queue_file(envelope, queue_dir)
    return {
        "ok": True,
        "feedback_id": envelope["feedback_id"],
        "receipt_hash": envelope["receipt_hash"],
        "status": envelope["status"],
        "path": str(path),
        "envelope": envelope,
    }


class FeedbackHandler(BaseHTTPRequestHandler):
    queue_dir: Path = DEFAULT_QUEUE_DIR

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, {})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/api/user-feedback/health", "/health"}:
            self._send(200, {"ok": True, "schema": SCHEMA})
            return
        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/user-feedback", "/api/user-feedback/"}:
            self._send(404, {"ok": False, "error": "not found"})
            return
        length = self.headers.get("Content-Length", "")
        try:
            size = int(length)
        except ValueError:
            self._send(400, {"ok": False, "error": "Content-Length required"})
            return
        if size < 0 or size > MAX_BODY_BYTES:
            self._send(413, {"ok": False, "error": "payload too large"})
            return
        raw = self.rfile.read(size)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send(400, {"ok": False, "error": "invalid JSON"})
            return
        if not isinstance(payload, dict):
            self._send(400, {"ok": False, "error": "object required"})
            return
        try:
            result = ingest(payload, queue_dir=self.queue_dir, status="submitted")
        except FeedbackIngestError as exc:
            self._send(400, {"ok": False, "error": str(exc)})
            return
        self._send(
            201,
            {
                "ok": True,
                "feedback_id": result["feedback_id"],
                "receipt_hash": result["receipt_hash"],
                "status": result["status"],
                "schema": SCHEMA,
            },
        )


def serve(host: str, port: int, queue_dir: Path) -> None:
    FeedbackHandler.queue_dir = queue_dir.resolve()
    queue_dir.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((host, port), FeedbackHandler)
    print(f"feedback ingest listening on http://{host}:{port}/api/user-feedback", flush=True)
    httpd.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest user-feedback-envelope@v1 submissions")
    parser.add_argument("--queue-dir", type=Path, default=DEFAULT_QUEUE_DIR)
    parser.add_argument("--check", type=Path, help="validate a JSON payload without writing")
    parser.add_argument("--apply", type=Path, help="validate and write a queue file")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if args.serve:
        serve(args.host, args.port, args.queue_dir)
        return 0
    path = args.check or args.apply
    if path is None:
        parser.print_help()
        return 2
    payload = json.loads(path.read_text(encoding="utf-8"))
    if args.check:
        envelope = build_envelope(payload, status="queued")
        json.dump({"ok": True, "envelope": envelope}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    result = ingest(payload, queue_dir=args.queue_dir, status="submitted")
    json.dump(
        {
            "ok": True,
            "feedback_id": result["feedback_id"],
            "receipt_hash": result["receipt_hash"],
            "path": result["path"],
        },
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
