#!/usr/bin/env python3
"""Local preview and demonstration server.

Serves the documentation tree and the issue preview, and adds the
experience API used by ``demo.html``. Static paths include ``classic/``,
``score/``, ``mutation-ledger.html``, and the localized ``{lang}/classic``
and ``{lang}/score`` trees.

Queue writes stay under ``_src/spec/feedback-queue/``. Curator decisions,
including stereotype changes and unbind requests, are envelopes only.
Classic (``CP_*``) and S-Core (``SCORE_*``) record ids are accepted by the
feedback, curate, discuss, and feedback-loop routes. Every mutation appends
one audit-ledger receipt. Canonical HTML, spec records, and existing
curation-queue files are not modified.

Usage:
    python3 _src/serve.py
    python3 _src/serve.py --port 8100
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
MAX_BODY_BYTES = 1048576
LOOP_TIMEOUT_SECONDS = 30
TARGET_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9:_.-]{0,199}")
UNIVERSE_SPECS: Tuple[Tuple[str, str, str], ...] = (
    ("adaptive", "AUTOSAR Adaptive", "index.html"),
    ("classic", "AUTOSAR Classic", "classic/index.html"),
    ("score", "S-Core", "eclipse-score-v0.6.0-curation-review/index.html"),
)
CONTEXT_KEYS = ("page", "universe", "component_id")

_WRITE_LOCK = threading.Lock()
_CATALOG_CACHE: list[dict] | None = None


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    # Dataclasses on Python 3.14 resolve the class module through sys.modules
    # while the class body is being processed.
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


PREVIEW = _load("issue_preview_for_serve", HERE / "tools" / "issue_preview.py")
FEEDBACK = _load("agent_feedback_form_for_serve", HERE / "tools" / "agent_feedback_form.py")
LOOP = _load("feedback_loop_for_serve", HERE / "feedback_loop.py")
MUTATION = _load("mutation_ledger_for_serve", HERE / "tools" / "mutation_ledger.py")
DISCUSS = _load("ai_discuss_for_serve", HERE / "tools" / "ai_discuss.py")
ASOF = _load("asof_view_for_serve", HERE / "tools" / "asof_view.py")
DELTA = _load("delta_view_for_serve", HERE / "tools" / "delta_view.py")
VS = _load("version_store_for_serve", HERE / "tools" / "version_store.py")
AI_BRIDGE = _load("ai_agent_bridge_for_serve", HERE / "tools" / "ai_agent_bridge.py")
DG = _load("dependency_graph_for_serve", HERE / "tools" / "dependency_graph.py")



class PayloadError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def universe_rows(repo: Path) -> list:
    """Report the three documentation universes without scanning the tree."""
    root = repo.resolve()
    rows = []
    for ident, label, relative in UNIVERSE_SPECS:
        path = root / relative
        present = False
        if path.is_file() and not path.is_symlink():
            try:
                LOOP.inside(root, path)
                present = True
            except ValueError:
                present = False
        rows.append(
            {
                "id": ident,
                "label": label,
                "present": present,
                "entry": ("/" + relative) if present else None,
                "note": None if present else "corpus not imported",
            }
        )
    return rows


def _count_json(repo: Path, relative: str) -> int:
    root = repo.resolve()
    directory = root / relative
    if not directory.exists() or directory.is_symlink() or not directory.is_dir():
        return 0
    try:
        LOOP.inside(root, directory)
    except ValueError:
        return 0
    total = 0
    for child in directory.iterdir():
        if child.is_symlink() or not child.is_file():
            continue
        if child.suffix == ".json" and not child.name.startswith("."):
            total += 1
    return total


def status_payload(repo: Path) -> Dict[str, Any]:
    root = repo.resolve()
    return {
        "ok": True,
        "canonical_mutation": False,
        "server": "demo-orchestrator",
        "universes": universe_rows(root),
        "pending_feedback": _count_json(root, "_src/spec/feedback-queue/open"),
        "decision_envelopes": _count_json(root, "_src/spec/feedback-queue/decisions"),
        "curation_queue": {
            "open": _count_json(root, "_src/spec/curation-queue/open"),
            "quarantine": _count_json(root, "_src/spec/curation-queue/quarantine"),
        },
    }


def _context_from(data: Mapping[str, Any]) -> Dict[str, str]:
    context: Dict[str, str] = {}
    for key in CONTEXT_KEYS:
        if key not in data or data[key] in (None, ""):
            continue
        value = data[key]
        if not isinstance(value, str):
            raise PayloadError(400, f"{key} must be a string")
        if len(value) > 500 or "\x00" in value:
            raise PayloadError(400, f"{key} is invalid")
        context[key] = value
    return context


def _contexts_conflict(stored: Mapping[str, Any], incoming: Mapping[str, str]) -> bool:
    for key, value in incoming.items():
        if stored.get(key) != value:
            return True
    return False


def _find_idempotent(open_dir: Path, key: str) -> Optional[Tuple[Path, Dict[str, Any]]]:
    if not open_dir.is_dir() or open_dir.is_symlink():
        return None
    for path in sorted(open_dir.iterdir()):
        if (
            not path.is_file()
            or path.is_symlink()
            or path.suffix != ".json"
            or path.name.startswith(".")
        ):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("idempotency_key") == key:
            return path, data
    return None


def _receipt(repo: Path, path: Path, data: Mapping[str, Any], replay: bool) -> Dict[str, Any]:
    return {
        "ok": True,
        "idempotent_replay": replay,
        "envelope_id": data.get("envelope_id"),
        "idempotency_key": data.get("idempotency_key"),
        "content_digest": data.get("content_digest"),
        "path": path.relative_to(repo.resolve()).as_posix(),
        "recorded_at": data.get("recorded_at"),
        "canonical_mutation": False,
    }


def _normalize_feedback(data: Mapping[str, Any]) -> Dict[str, Any]:
    payload = dict(data)
    if "feedback_text" not in payload and "text" in payload:
        payload["feedback_text"] = payload.pop("text")
    return payload


def _validate_target(target: Any) -> str:
    if not isinstance(target, str) or not TARGET_ID_RE.fullmatch(target.strip()):
        raise PayloadError(400, "target_id is invalid")
    cleaned = target.strip()
    if cleaned in {".", ".."} or any(part == ".." for part in cleaned.split(":")):
        raise PayloadError(400, "target_id is invalid")
    return cleaned


def _proposal_text(prompt: str, context: Mapping[str, Any]) -> Tuple[str, Dict[str, Any], list]:
    encoded = json.dumps(context, ensure_ascii=False, sort_keys=True)[:2000]
    haystack = prompt + "\n" + encoded
    found = re.findall(
        r"\b(?:SWS_[A-Z0-9_]+|RS_[A-Z0-9_]+|CP_[A-Z0-9_]+|SCORE_[A-Z0-9_]+|ara::[A-Za-z0-9_]+)\b",
        haystack,
    )
    identifiers = list(dict.fromkeys(found))[:12]
    quoted = prompt.strip()[:500]
    reply_parts = [
        "Lokaler Kontextvorschlag. Es wurde kein externes Modell aufgerufen.",
        "Die Antwort verwendet nur den mitgeschickten Prompt und Kontext.",
        f"Prompt: {quoted}",
    ]
    if identifiers:
        reply_parts.append("Erkannte Bezeichner: " + ", ".join(identifiers) + ".")
    proposal = (
        "Vorschlag für einen KI-Kommentar: "
        + quoted
        + (" Bezogen auf " + ", ".join(identifiers) + "." if identifiers else "")
        + " Dieser Text ist eine Umschreibung der Eingabe, keine neue Spezifikationsaussage."
    )
    warnings = []
    lowered = haystack.lower()
    if any(token in lowered for token in ("api_key", "begin private key", "secret")):
        warnings.append("text may contain credential keywords; nothing was forwarded to an external model")
    return (
        " ".join(reply_parts),
        {
            "kind": "ai-comment",
            "text": proposal,
            "grounded_in": ["prompt", "context"],
            "identifiers": identifiers,
            "generator": "local-context-proposer",
            "model": None,
        },
        warnings,
    )


def _is_sidecar_discuss(data: Mapping[str, Any]) -> bool:
    """The product sidecar posts ``action`` and ``record_id``, not ``prompt``."""
    action = data.get("action")
    if isinstance(action, str) and action.strip():
        return True
    prompt = data.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        return False
    return any(key in data for key in ("record_id", "target_record", "message"))


def _with_canonical_flag(payload: Mapping[str, Any]) -> Dict[str, Any]:
    body = dict(payload)
    body.setdefault("canonical_mutation", False)
    return body


def _run_feedback_loop(repo: Path) -> Tuple[int, Dict[str, Any]]:
    script = HERE / "feedback_loop.py"
    if not script.is_file():
        return 500, {"ok": False, "error": "feedback_loop.py is missing", "canonical_mutation": False}
    try:
        completed = subprocess.run(
            [sys.executable, str(script), "--repo", str(repo.resolve())],
            capture_output=True,
            text=True,
            timeout=LOOP_TIMEOUT_SECONDS,
            cwd=str(repo.resolve()),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 504, {
            "ok": False,
            "error": "feedback loop timed out",
            "canonical_mutation": False,
        }
    stdout = completed.stdout.strip()
    try:
        summary = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        return 500, {
            "ok": False,
            "error": "feedback loop returned non-JSON output",
            "returncode": completed.returncode,
            "canonical_mutation": False,
        }
    if not isinstance(summary, dict):
        return 500, {
            "ok": False,
            "error": "feedback loop returned an unexpected payload",
            "returncode": completed.returncode,
            "canonical_mutation": False,
        }
    if completed.returncode != 0 or not summary.get("ok"):
        return 500, {
            "ok": False,
            "error": summary.get("error") or "feedback loop failed",
            "returncode": completed.returncode,
            "summary": summary,
            "canonical_mutation": False,
        }
    return 200, {"ok": True, "returncode": 0, "summary": summary, "canonical_mutation": False}


class DemoHandler(PREVIEW.IssuePreviewHandler):
    """Issue preview plus the demonstration API."""

    repo: Path = PREVIEW.ROOT

    def _route(self) -> str:
        path = urlparse(self.path).path
        if len(path) > 1:
            path = path.rstrip("/")
        return path or "/"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def _json(self, status: int, payload: Mapping[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> bytes:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise PayloadError(400, "Content-Length is required")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise PayloadError(400, "Content-Length is invalid") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise PayloadError(413, "payload too large")
        return self.rfile.read(length)

    def _read_object(self, allow_empty: bool = False) -> Dict[str, Any]:
        raw = self._read_body()
        if not raw:
            if allow_empty:
                return {}
            raise PayloadError(400, "empty body")
        content_type = self.headers.get("Content-Type", "")
        if "application/x-www-form-urlencoded" in content_type:
            parsed = parse_qs(raw.decode("utf-8"), keep_blank_values=False)
            return {key: values[0] for key, values in parsed.items() if values}
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PayloadError(400, "body must be JSON") from exc
        if not isinstance(data, dict):
            raise PayloadError(400, "JSON object required")
        return data

    def do_GET(self) -> None:
        route = self._route()
        if route == "/api/status":
            self._json(200, status_payload(Path(self.repo)))
            return
        if route == "/api/curation/votes":
            self._get_curation_votes()
            return
        if route == "/api/discuss":
            self._get_discuss()
            return
        if route == "/api/versions":
            self._get_versions()
            return
        if route == "/api/asof":
            self._get_asof()
            return
        if route == "/api/delta":
            self._get_delta()
            return
        if route == "/api/diff":
            self._get_diff()
            return
        if route == "/api/ai/status":
            self._get_ai_status()
            return
        if route.startswith("/api/"):
            self._json(405, {"ok": False, "error": "method not allowed"})
            return
        target = self._repo() / route.lstrip("/")
        if route.startswith("/eclipse-score-v0.6.0-curation-review/") and not target.exists():
            self.send_response(302)
            self.send_header("Location", "/score/index.html")
            self.end_headers()
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        route = self._route()
        if route.startswith("/api/"):
            if route in ("/api/status", "/api/versions", "/api/asof", "/api/delta", "/api/ai/status", "/api/diff", "/api/curation/votes"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            self.send_response(405)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        target = self._repo() / route.lstrip("/")
        if route.startswith("/eclipse-score-v0.6.0-curation-review/") and not target.exists():
            self.send_response(302)
            self.send_header("Location", "/score/index.html")
            self.end_headers()
            return
        super().do_HEAD()

    def do_POST(self) -> None:
        route = self._route()
        try:
            if route == "/api/feedback":
                self._post_feedback()
                return
            if route == "/api/curate":
                self._post_curate()
                return
            if route == "/api/curation/vote":
                self._post_curation_vote()
                return
            if route == "/api/discuss":
                self._post_discuss()
                return
            if route == "/api/feedback-loop/run":
                self._post_loop()
                return
            if route == "/api/ai/check":
                self._post_ai_check()
                return
            if route == "/api/ai/execute_prompt":
                self._post_ai_execute_prompt()
                return

        except PayloadError as exc:
            self._json(exc.status, {"ok": False, "error": exc.message})
            return
        except FEEDBACK.FeedbackValidationError as exc:
            self._json(400, {"ok": False, "error": str(exc)})
            return
        except ValueError:
            self._json(500, {"ok": False, "error": "queue path is not inside the repository"})
            return
        if route.startswith("/api/"):
            self._json(405, {"ok": False, "error": "method not allowed"})
            return
        super().do_POST()

    def _repo(self) -> Path:
        return Path(self.repo).resolve()

    def _record_mutation(
        self,
        action: str,
        operator: str,
        details: dict,
        outputs=None,
        root=None,
    ) -> None:
        try:
            MUTATION.record_mutation(
                action,
                operator,
                details,
                outputs=outputs,
                success=True,
                root=root or self._repo(),
                metadata={"source": "serve.py"},
            )
        except Exception:
            return

    def _post_feedback(self) -> None:
        incoming = _normalize_feedback(self._read_object())
        context = _context_from(incoming)
        envelope = FEEDBACK.validate_feedback(incoming)
        repo = self._repo()
        open_dir = LOOP.queue_dir(repo, "open")
        with _WRITE_LOCK:
            found = _find_idempotent(open_dir, envelope.idempotency_key)
            if found is not None:
                path, stored = found
                stored_context = stored.get("demo_context")
                stored_context = stored_context if isinstance(stored_context, dict) else {}
                if _contexts_conflict(stored_context, context):
                    self._json(
                        409,
                        {
                            "ok": False,
                            "error": "idempotency key reused with a different page context",
                            "envelope_id": stored.get("envelope_id"),
                            "canonical_mutation": False,
                        },
                    )
                    return
                self._json(200, _receipt(repo, path, stored, replay=True))
                return
            record = envelope.to_dict()
            if context:
                record["demo_context"] = context
            path = open_dir / f"{envelope.envelope_id}.json"
            LOOP.atomic_write(
                repo,
                path,
                json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
        self._record_mutation(
            "user-feedback-received",
            str(incoming.get("submitter") or "anonymous"),
            {
                "envelope_id": envelope.envelope_id,
                "category": incoming.get("category"),
                "page": context.get("page") if context else None,
                "universe": context.get("universe") if context else None,
                "component_id": context.get("component_id") if context else None,
                "canonical_mutation": False,
            },
            outputs=[path],
            root=repo,
        )
        self._json(201, _receipt(repo, path, record, replay=False))

    def _post_curate(self) -> None:
        data = self._read_object()
        decision = data.get("decision")
        if decision not in LOOP.DECISIONS:
            raise PayloadError(400, "decision must be accept, reject, change_stereotype, or delete_mapping")
        target_id = _validate_target(data.get("target_id"))
        stereotype = None
        if decision == "change_stereotype":
            stereotype = data.get("stereotype")
            if stereotype not in LOOP.STEREOTYPES:
                raise PayloadError(400, "stereotype is invalid")
        rationale = data.get("rationale") or ""
        if not isinstance(rationale, str) or len(rationale) > 2000 or "\x00" in rationale:
            raise PayloadError(400, "rationale is invalid")
        repo = self._repo()
        envelope_id = FEEDBACK._new_envelope_id()
        record = {
            "schema": "demo-curator-decision@v1",
            "envelope_id": envelope_id,
            "recorded_at": FEEDBACK._now_iso_utc(),
            "decision": decision,
            "target_id": target_id,
            "stereotype": stereotype,
            "rationale": rationale,
            "effect": "envelope-only",
            "canonical_mutation": False,
        }
        path = LOOP.queue_dir(repo, "decisions") / f"{envelope_id}.json"
        with _WRITE_LOCK:
            LOOP.atomic_write(
                repo,
                path,
                json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
        self._record_mutation(
            "curation-decision-applied",
            "curator",
            {
                "envelope_id": envelope_id,
                "decision": decision,
                "target_id": target_id,
                "stereotype": stereotype,
                "canonical_mutation": False,
            },
            outputs=[path],
            root=repo,
        )
        self._json(
            200,
            {
                "ok": True,
                "envelope_id": envelope_id,
                "decision": decision,
                "target_id": target_id,
                "stereotype": stereotype,
                "path": path.relative_to(repo).as_posix(),
                "effect": "envelope-only",
                "canonical_mutation": False,
            },
        )

    def _get_curation_votes(self) -> None:
        edges = DG.list_edges()
        votes: Dict[str, Any] = {}
        for e in edges:
            to_id = e.get("to")
            etype = e.get("edge_type")
            if etype in ("confirms", "dismisses"):
                if to_id not in votes:
                    votes[to_id] = {
                        "confirms": 0,
                        "dismisses": 0,
                        "is_dismissed": DG.is_dismissed(to_id),
                    }
                if etype == "confirms":
                    votes[to_id]["confirms"] += 1
                elif etype == "dismisses":
                    votes[to_id]["dismisses"] += 1
        self._json(200, {"ok": True, "votes": votes})

    def _post_curation_vote(self) -> None:
        data = self._read_object()
        snippet_id = str(data.get("snippet_id") or data.get("record_id") or data.get("item_id") or "").strip()
        vote = str(data.get("vote") or "").strip().lower()
        rationale = str(data.get("rationale") or "").strip()
        reviewer = str(data.get("reviewer") or "curator").strip()

        if not snippet_id:
            raise PayloadError(400, "snippet_id or record_id is required")
        if vote not in ("confirm", "dismiss", "reset", "unrated"):
            raise PayloadError(400, "vote must be 'confirm', 'dismiss', or 'reset'")

        if vote in ("reset", "unrated"):
            if hasattr(DG, "undismiss_node"):
                DG.undismiss_node(snippet_id)
            self._record_mutation(
                "snippet-vote-reset",
                reviewer,
                {
                    "snippet_id": snippet_id,
                    "vote": "reset",
                    "canonical_mutation": False,
                },
                root=self._repo(),
            )
            self._json(200, {
                "ok": True,
                "snippet_id": snippet_id,
                "vote": "reset",
                "is_dismissed": False,
            })
            return

        edge_type = "confirms" if vote == "confirm" else "dismisses"
        from_id = f"reviewer:{reviewer}"
        to_id = snippet_id

        edge = DG.add_edge(
            from_id,
            to_id,
            edge_type,
            meta={"rationale": rationale, "voted_at": FEEDBACK._now_iso_utc()},
        )

        if vote == "dismiss":
            DG.dismiss_node(snippet_id, reason=rationale or "User curation vote: dismissed")

        self._record_mutation(
            f"snippet-vote-{vote}",
            reviewer,
            {
                "snippet_id": snippet_id,
                "vote": vote,
                "edge_type": edge_type,
                "rationale": rationale,
                "canonical_mutation": False,
            },
            root=self._repo(),
        )
        self._json(200, {
            "ok": True,
            "snippet_id": snippet_id,
            "vote": vote,
            "edge_type": edge_type,
            "is_dismissed": DG.is_dismissed(snippet_id),
            "edge": edge,
        })

    def _get_discuss(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        try:
            status, payload = DISCUSS.handle_http("GET", query, None, self._repo())
        except Exception:
            self._json(500, {"ok": False, "error": "discuss-failed", "canonical_mutation": False})
            return
        self._json(status, _with_canonical_flag(payload))

    def _get_versions(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        record_id = (query.get("id") or query.get("canonical_id") or [""])[0].strip()
        if not record_id:
            # Catalog listing / search mode
            global _CATALOG_CACHE
            refresh = (query.get("refresh") or query.get("reload") or [""])[0].strip() in ("1", "true")
            if _CATALOG_CACHE is None or refresh:
                root = Path(self.repo) / "_src" / "spec" / "versions"
                items = []
                if root.exists():
                    for p in root.rglob("*.jsonl"):
                        try:
                            lines = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
                        except Exception:
                            continue
                        if lines:
                            cid = lines[0].get("canonical_id", "")
                            rels = [l.get("release", "") for l in lines]
                            lc = VS.get_requirement_lifecycle(cid, lines)
                            items.append({
                                "id": p.stem,
                                "canonical_id": cid,
                                "platform": "CP" if "AUTOSAR/CP" in cid else "AP",
                                "version_count": len(lines),
                                "releases": rels,
                                "latest_release": rels[-1] if rels else "",
                                "is_dropped": lc["is_dropped"],
                                "first_dropped_release": lc["first_dropped_release"]
                            })
                items.sort(key=lambda x: (-x["version_count"], x["id"]))
                _CATALOG_CACHE = items

            search = (query.get("search") or query.get("q") or [""])[0].strip().lower()
            multi_only = (query.get("multi_only") or [""])[0].strip() in ("1", "true")
            platform = (query.get("platform") or [""])[0].strip().upper()
            filtered = _CATALOG_CACHE
            if multi_only:
                filtered = [c for c in filtered if c["version_count"] > 1]
            if platform in ("AP", "CP"):
                filtered = [c for c in filtered if c["platform"] == platform]
            if search:
                filtered = [c for c in filtered if search in c["id"].lower() or search in c["canonical_id"].lower()]
            limit = int((query.get("limit") or ["150"])[0])
            self._json(200, {
                "ok": True,
                "total": len(_CATALOG_CACHE),
                "matched": len(filtered),
                "items": filtered[:limit]
            })
            return
        cid = ASOF._canonicalize(record_id)
        versions = VS.list_versions(cid)
        if not versions and ASOF.parse_canonical_id(record_id) is None:
            for alt_proj in ("AUTOSAR/CP", "Eclipse/S-Core"):
                alt_cid = f"{alt_proj}/record/{record_id}"
                alt_vers = VS.list_versions(alt_cid)
                if alt_vers:
                    cid = alt_cid
                    versions = alt_vers
                    break
        lifecycle = VS.get_requirement_lifecycle(cid, versions)
        self._json(200, {
            "ok": True,
            "canonical_id": cid,
            "versions": versions,
            "lifecycle": lifecycle
        })

    @staticmethod
    def _compute_word_diff(text_a: str, text_b: str) -> tuple[str, str]:
        import re, difflib, html
        tokens_a = re.findall(r"\S+|\n|\s+", text_a)
        tokens_b = re.findall(r"\S+|\n|\s+", text_b)
        matcher = difflib.SequenceMatcher(None, tokens_a, tokens_b)
        out_a = []
        out_b = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            sub_a = "".join(tokens_a[i1:i2])
            sub_b = "".join(tokens_b[j1:j2])
            if tag == "equal":
                out_a.append(html.escape(sub_a))
                out_b.append(html.escape(sub_b))
            elif tag == "replace":
                if sub_a.strip():
                    out_a.append(f'<del class="ve-word-deleted">{html.escape(sub_a)}</del>')
                else:
                    out_a.append(sub_a)
                if sub_b.strip():
                    out_b.append(f'<ins class="ve-word-added">{html.escape(sub_b)}</ins>')
                else:
                    out_b.append(sub_b)
            elif tag == "delete":
                if sub_a.strip():
                    out_a.append(f'<del class="ve-word-deleted">{html.escape(sub_a)}</del>')
                else:
                    out_a.append(sub_a)
            elif tag == "insert":
                if sub_b.strip():
                    out_b.append(f'<ins class="ve-word-added">{html.escape(sub_b)}</ins>')
                else:
                    out_b.append(sub_b)
        return "".join(out_a), "".join(out_b)

    def _get_diff(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        record_id = (query.get("id") or query.get("canonical_id") or [""])[0].strip()
        if not record_id:
            self._json(400, {"ok": False, "error": "id parameter required"})
            return
        cid = ASOF._canonicalize(record_id)
        from_rel = (query.get("from") or query.get("from_release") or [""])[0].strip()
        to_rel = (query.get("to") or query.get("to_release") or [""])[0].strip()
        if not from_rel or not to_rel:
            self._json(400, {"ok": False, "error": "from and to parameters required"})
            return
        res_a = ASOF.as_of_release(cid, from_rel)
        res_b = ASOF.as_of_release(cid, to_rel)
        v_a = res_a.get("version")
        v_b = res_b.get("version")
        is_dropped_a = res_a.get("is_dropped", False)
        is_dropped_b = res_b.get("is_dropped", False)
        raw_a = "" if is_dropped_a else (v_a.get("content", "") if v_a else "")
        raw_b = "" if is_dropped_b else (v_b.get("content", "") if v_b else "")
        lines_a = ASOF._format_req_lines(raw_a)
        lines_b = ASOF._format_req_lines(raw_b)
        import difflib
        import html
        diff_lines = []
        aligned_blocks = []
        matcher = difflib.SequenceMatcher(None, [l.strip() for l in lines_a], [l.strip() for l in lines_b])
        block_idx = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            left_chunk = [l.strip() for l in lines_a[i1:i2]]
            right_chunk = [l.strip() for l in lines_b[j1:j2]]
            left_html = ""
            right_html = ""
            if tag == "equal":
                left_html = html.escape("\n".join(left_chunk))
                right_html = html.escape("\n".join(right_chunk))
                for line in left_chunk:
                    diff_lines.append({"type": "unchanged", "text": line})
            elif tag == "replace":
                left_html, right_html = self._compute_word_diff("\n".join(left_chunk), "\n".join(right_chunk))
                for line in left_chunk:
                    diff_lines.append({"type": "deleted", "text": line})
                for line in right_chunk:
                    diff_lines.append({"type": "added", "text": line})
            elif tag == "delete":
                left_html = html.escape("\n".join(left_chunk))
                right_html = ""
                for line in left_chunk:
                    diff_lines.append({"type": "deleted", "text": line})
            elif tag == "insert":
                left_html = ""
                right_html = html.escape("\n".join(right_chunk))
                for line in right_chunk:
                    diff_lines.append({"type": "added", "text": line})
            aligned_blocks.append({
                "id": f"block-{block_idx}",
                "tag": tag,
                "left_lines": left_chunk,
                "right_lines": right_chunk,
                "left_html": left_html,
                "right_html": right_html
            })
            block_idx += 1
        self._json(200, {
            "ok": True,
            "canonical_id": cid,
            "from": {"release": from_rel, "version": None if is_dropped_a else v_a, "is_dropped": is_dropped_a},
            "to": {"release": to_rel, "version": None if is_dropped_b else v_b, "is_dropped": is_dropped_b},
            "diff_lines": diff_lines,
            "aligned_blocks": aligned_blocks
        })

    def _get_asof(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        record_id = (query.get("id") or query.get("canonical_id") or [""])[0].strip()
        if not record_id:
            self._json(400, {"ok": False, "error": "id parameter required"})
            return
        cid = ASOF._canonicalize(record_id)
        release = (query.get("release") or [""])[0].strip() or None
        date = (query.get("date") or [""])[0].strip() or None
        if not release and not date:
            latest = VS.latest_version(cid)
            release = latest["release"] if latest else "R25-11"
        try:
            if date:
                res = ASOF.as_of_date(cid, date)
            else:
                res = ASOF.as_of_release(cid, release)
            self._json(200, {"ok": True, **res})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def _get_delta(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        release = (query.get("release") or [""])[0].strip() or None
        date = (query.get("date") or [""])[0].strip() or None
        if not release and not date:
            self._json(400, {"ok": False, "error": "release or date parameter required"})
            return
        try:
            res = DELTA.delta_view(release=release, date=date)
            self._json(200, {"ok": True, **res})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def _get_ai_status(self) -> None:
        try:
            status = AI_BRIDGE.get_health_status()
            self._json(200, status)
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def _post_ai_check(self) -> None:
        try:
            AI_BRIDGE.trigger_health_check_async()
            status = AI_BRIDGE.get_health_status()
            self._json(200, status)
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def _parse_agent_html(self, raw_output: str) -> Tuple[Optional[dict], str]:
        parsed_json = None
        generated_html = ""
        m_fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_output, re.DOTALL)
        if m_fence:
            try:
                parsed_json = json.loads(m_fence.group(1).strip())
            except Exception:
                pass
        if not parsed_json:
            cleaned_out = raw_output.strip()
            try:
                start = cleaned_out.find("{")
                end = cleaned_out.rfind("}")
                if start != -1 and end != -1 and end > start:
                    parsed_json = json.loads(cleaned_out[start:end+1])
            except Exception:
                pass
        if isinstance(parsed_json, dict):
            if "ergebnisse" in parsed_json and len(parsed_json["ergebnisse"]) > 0:
                generated_html = parsed_json["ergebnisse"][0].get("html", "")
            elif "html" in parsed_json:
                generated_html = parsed_json.get("html", "")
        if not generated_html:
            m = re.search(r'(<div class=["\']ai\b[^>]*>.*?</div>\s*<p class=["\']ai-note["\']>.*?</p>\s*</div>)', raw_output, re.DOTALL)
            if m:
                generated_html = m.group(1).strip()
            elif "<div class=" in raw_output:
                m2 = re.search(r'(<div class=["\']ai\b.*)', raw_output, re.DOTALL)
                if m2:
                    generated_html = m2.group(1).strip()
        return parsed_json, generated_html

    def _post_ai_execute_prompt(self) -> None:
        data = self._read_object()
        prompt = str(data.get("prompt") or "").strip()
        modul = str(data.get("module") or "LinIf").strip()
        fragment_rel = str(data.get("fragment") or f"content/ai/classic/modules/{modul.lower()}/main_01.html").strip()

        if not prompt:
            raise PayloadError(400, "prompt is required")

        repo = self._repo()
        frag_file = repo / "_src" / fragment_rel
        if not frag_file.exists():
            frag_file = repo / fragment_rel
        original_html = frag_file.read_text(encoding="utf-8") if frag_file.is_file() else ""

        t0 = time.monotonic()
        status = AI_BRIDGE.get_health_status()
        subs = AI_BRIDGE.check_subscriptions()

        active_prov = status.get("active_provider") or "agy"
        agy_conf = status.get("providers", {}).get("agy", {})
        cur_conf = status.get("providers", {}).get("cursor", {})

        req_model = str(data.get("model") or "").strip()
        req_prov = str(data.get("provider") or "").strip()

        if req_prov == "cursor" or req_model == "composer-2.5":
            providers_to_try = ["cursor"]
        elif req_prov == "agy" or req_model.startswith("gemini-"):
            providers_to_try = ["agy"]
        else:
            providers_to_try = ["agy", "cursor"] if active_prov == "agy" else ["cursor", "agy"]

        is_stream = bool(data.get("stream")) or ("text/event-stream" in self.headers.get("Accept", ""))

        if is_stream:
            self.close_connection = True
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            def sse(ev_obj):
                try:
                    payload = f"data: {json.dumps(ev_obj, ensure_ascii=False)}\n\n".encode("utf-8")
                    self.wfile.write(payload)
                    self.wfile.flush()
                except Exception:
                    pass

            if os.environ.get("AI_MOCK_DIFF") == "1" or data.get("mock"):
                replacement = "Abstracts LIN hardware and manages schedule tables and frame transmission (mit deterministischer Validierung durch SWS_Lin_00098)."
                mock_html = original_html.replace("Abstracts LIN hardware and manages schedule tables and frame transmission.", replacement) if original_html else f"<div class=\"ai module-guide\"><p>{replacement}</p><p class=\"ai-note\">KI-Hinweis</p></div>"
                raw_mock = json.dumps({
                    "ergebnisse": [{
                        "fragment": fragment_rel,
                        "html": mock_html,
                        "diagramme": {},
                        "trace": {"modell": "mock-generator-v1"}
                    }]
                })
                sse({"event": "start", "provider": "mock", "model": "mock-generator-v1", "min_hz": 4.0, "elapsed_ms": 0, "phase": "thinking"})
                time.sleep(0.25)
                sse({"event": "tick", "phase": "thinking", "elapsed_ms": 250, "hz": 4.0, "tokens": 0})
                time.sleep(0.25)
                half = len(raw_mock) // 2
                sse({"event": "delta", "delta": raw_mock[:half], "accumulated": raw_mock[:half], "phase": "generating", "elapsed_ms": 500, "hz": 4.0, "tokens": 50})
                time.sleep(0.25)
                sse({"event": "delta", "delta": raw_mock[half:], "accumulated": raw_mock, "phase": "generating", "elapsed_ms": 750, "hz": 4.0, "tokens": 100})
                time.sleep(0.25)
                dur_ms = int((time.monotonic() - t0) * 1000)
                sse({
                    "event": "complete",
                    "ok": True,
                    "provider": "mock",
                    "model": "mock-generator-v1",
                    "original_html": original_html,
                    "generated_html": mock_html,
                    "parsed_json": json.loads(raw_mock),
                    "raw_output": raw_mock,
                    "duration_ms": dur_ms,
                    "effective_hz": 4.0,
                })
                return

            chosen_prov = None
            chosen_model = None
            stream_gen = None
            for prov in providers_to_try:
                if prov == "agy" and subs.get("gemini", {}).get("available"):
                    cli = subs["gemini"]["cli_path"] or "agy"
                    m = req_model if (req_model and req_model.startswith("gemini-")) else agy_conf.get("model", "gemini-3.8-flash-medium")
                    cmd = AI_BRIDGE.build_stream_cmd("agy", cli, m, effort="medium", prompt=prompt)
                    stream_gen = AI_BRIDGE.stream_agent_cli(cmd, provider="agy", min_hz=4.0)
                    chosen_prov = "agy"
                    chosen_model = m
                    break
                elif prov == "cursor" and subs.get("cursor", {}).get("available"):
                    cli = subs["cursor"]["cli_path"] or "agent"
                    m = req_model if (req_model and "composer" in req_model) else cur_conf.get("model", "composer-2.5")
                    cmd = AI_BRIDGE.build_stream_cmd("cursor", cli, m, prompt=prompt)
                    stream_gen = AI_BRIDGE.stream_agent_cli(cmd, provider="cursor", min_hz=4.0)
                    chosen_prov = "cursor"
                    chosen_model = m
                    break

            if not stream_gen:
                sse({
                    "event": "error",
                    "error": "Kein KI-Provider (agy / cursor) verfügbar.",
                    "duration_ms": int((time.monotonic() - t0) * 1000)
                })
                return

            raw_accum = ""
            for ev in stream_gen:
                ev_name = ev.get("event")
                if ev_name == "complete":
                    raw_accum = ev.get("output", "")
                    dur_ms = ev.get("duration_ms") or int((time.monotonic() - t0) * 1000)
                    parsed_json, generated_html = self._parse_agent_html(raw_accum)
                    is_ok = bool(generated_html and generated_html.strip())
                    err_msg = None if is_ok else "Modell lieferte kein gültiges HTML-Fragment im erwarteten Schema."
                    self._record_mutation(
                        "ai-prompt-executed",
                        "prompt-workbench",
                        {
                            "module": modul,
                            "fragment": fragment_rel,
                            "provider": chosen_prov,
                            "model": chosen_model,
                            "duration_ms": dur_ms,
                            "canonical_mutation": False,
                        },
                        root=repo,
                    )
                    sse({
                        "event": "complete",
                        "ok": is_ok,
                        "error": err_msg,
                        "provider": chosen_prov,
                        "model": chosen_model,
                        "original_html": original_html,
                        "generated_html": generated_html,
                        "parsed_json": parsed_json,
                        "raw_output": raw_accum[:3000] if raw_accum else "",
                        "duration_ms": dur_ms,
                        "effective_hz": ev.get("effective_hz", 4.0),
                    })
                    return
                elif ev_name == "error":
                    sse(ev)
                    return
                else:
                    sse(ev)
            return

        # Synchronous fallback for non-streaming callers
        raw_output = None
        used_prov = None
        used_model = None
        last_error = None

        if os.environ.get("AI_MOCK_DIFF") == "1" or data.get("mock"):
            used_prov = "mock"
            used_model = "mock-generator-v1"
            replacement = "Abstracts LIN hardware and manages schedule tables and frame transmission (mit deterministischer Validierung durch SWS_Lin_00098)."
            mock_html = original_html.replace("Abstracts LIN hardware and manages schedule tables and frame transmission.", replacement) if original_html else f"<div class=\"ai module-guide\"><p>{replacement}</p><p class=\"ai-note\">KI-Hinweis</p></div>"
            raw_output = json.dumps({
                "ergebnisse": [{
                    "fragment": fragment_rel,
                    "html": mock_html,
                    "diagramme": {},
                    "trace": {"modell": "mock-generator-v1"}
                }]
            })
        else:
            for prov in providers_to_try:
                if prov == "agy" and subs.get("gemini", {}).get("available"):
                    cli = subs["gemini"]["cli_path"] or "agy"
                    m = req_model if (req_model and req_model.startswith("gemini-")) else agy_conf.get("model", "gemini-3.8-flash-medium")
                    cmd = [cli, "--model", m, "--dangerously-skip-permissions", "--print", prompt]
                    ok, out = AI_BRIDGE._run_cli_prompt(cmd, timeout=180)
                    if ok and out:
                        raw_output = out
                        used_prov = "agy"
                        used_model = m
                        break
                    else:
                        last_error = out
                elif prov == "cursor" and subs.get("cursor", {}).get("available"):
                    cli = subs["cursor"]["cli_path"] or "agent"
                    m = req_model if (req_model and "composer" in req_model) else cur_conf.get("model", "composer-2.5")
                    cmd = [
                        cli,
                        "--print",
                        "--trust",
                        "--mode", "ask",
                        "--model", m,
                        prompt,
                    ]
                    ok, out = AI_BRIDGE._run_cli_prompt(cmd, timeout=180)
                    if ok and out:
                        raw_output = out
                        used_prov = "cursor"
                        used_model = m
                        break
                    else:
                        last_error = out

        duration_ms = int((time.monotonic() - t0) * 1000)

        if not raw_output:
            self._json(502, {
                "ok": False,
                "error": last_error or "Keine Antwort vom konfigurierten Modell erhalten. Prüfe CLI-Installation und Authentifizierung ('agy' / 'agent').",
                "duration_ms": duration_ms
            })
            return

        parsed_json, generated_html = self._parse_agent_html(raw_output)
        is_ok = bool(generated_html and generated_html.strip())
        err_msg = None if is_ok else "Modell lieferte kein gültiges HTML-Fragment im erwarteten Schema."

        self._record_mutation(
            "ai-prompt-executed",
            "prompt-workbench",
            {
                "module": modul,
                "fragment": fragment_rel,
                "provider": used_prov,
                "model": used_model,
                "duration_ms": duration_ms,
                "canonical_mutation": False,
            },
            root=repo,
        )

        self._json(200, {
            "ok": is_ok,
            "error": err_msg,
            "provider": used_prov,
            "model": used_model,
            "original_html": original_html,
            "generated_html": generated_html,
            "parsed_json": parsed_json,
            "raw_output": raw_output[:3000] if raw_output else "",
            "duration_ms": duration_ms,
        })

    def _post_discuss_sidecar(self, data: Dict[str, Any]) -> None:
        repo = self._repo()
        action = str(data.get("action") or "chat")
        is_stream = bool(data.get("stream")) or ("text/event-stream" in self.headers.get("Accept", ""))

        if is_stream and action in ("chat", "stream"):
            src = DISCUSS.src_dir(repo)
            rec_id = str(data.get("record_id") or "")
            try:
                context = DISCUSS.package_context(src, rec_id)
            except Exception:
                context = {"record_id": rec_id, "found": False}
            msg = str(data.get("message") or "")

            self.close_connection = True
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            try:
                for ev in DISCUSS.stream_discuss_reply(msg, context, min_hz=4.0):
                    chunk = f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode("utf-8")
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        try:
            status, payload = DISCUSS.handle_http("POST", {}, raw, repo)
        except Exception:
            self._json(500, {"ok": False, "error": "discuss-failed", "canonical_mutation": False})
            return
        payload = _with_canonical_flag(payload)
        if status == 200 and payload.get("ok") and action == "submit":
            written = payload.get("path")
            outputs = []
            if isinstance(written, str) and written and not written.startswith(("/", "\\")):
                candidate = repo / written
                if candidate.is_file():
                    outputs = [candidate]
            context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
            self._record_mutation(
                "discuss-proposal-submitted",
                "ai-discuss",
                {
                    "record_id": context.get("record_id") or data.get("record_id"),
                    "path": written if isinstance(written, str) else None,
                    "canonical_mutation": False,
                },
                outputs=outputs,
                root=repo,
            )
        self._json(status, payload)

    def _post_discuss(self) -> None:
        data = self._read_object()
        if _is_sidecar_discuss(data):
            self._post_discuss_sidecar(data)
            return
        prompt = data.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000 or "\x00" in prompt:
            raise PayloadError(400, "prompt is required")
        context = data.get("context", {})
        if isinstance(context, str):
            if len(context) > 4000 or "\x00" in context:
                raise PayloadError(400, "context is invalid")
            context = {"text": context}
        elif context is None:
            context = {}
        elif not isinstance(context, dict):
            raise PayloadError(400, "context must be an object or a string")
        reply, proposal, warnings = _proposal_text(prompt.strip(), context)
        repo = self._repo()
        proposal_id = FEEDBACK._new_envelope_id()
        record = {
            "schema": "demo-discuss-proposal@v1",
            "proposal_id": proposal_id,
            "recorded_at": FEEDBACK._now_iso_utc(),
            "prompt": prompt.strip(),
            "context": context,
            "reply": reply,
            "proposal": proposal,
            "warnings": warnings,
            "generator": "local-context-proposer",
            "model": None,
            "canonical_mutation": False,
        }
        path = LOOP.queue_dir(repo, "proposals") / f"{proposal_id}.json"
        with _WRITE_LOCK:
            LOOP.atomic_write(
                repo,
                path,
                json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
        self._record_mutation(
            "discuss-proposal-recorded",
            "demo-visitor",
            {
                "proposal_id": proposal_id,
                "identifiers": proposal.get("identifiers"),
                "canonical_mutation": False,
            },
            outputs=[path],
            root=repo,
        )
        self._json(
            200,
            {
                "ok": True,
                "proposal_id": proposal_id,
                "reply": reply,
                "proposal": proposal,
                "warnings": warnings,
                "context": context,
                "path": path.relative_to(repo).as_posix(),
                "generator": "local-context-proposer",
                "model": None,
                "canonical_mutation": False,
            },
        )

    def _post_loop(self) -> None:
        if self.headers.get("Content-Length") not in (None, "0"):
            self._read_object(allow_empty=True)
        repo = self._repo()
        status, payload = _run_feedback_loop(repo)
        if status == 200 and payload.get("ok"):
            summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
            self._record_mutation(
                "feedback-loop-regenerated",
                "feedback-loop",
                {
                    "comments_written": summary.get("comments_written"),
                    "pages_rebuilt": summary.get("pages_rebuilt"),
                    "canonical_mutation": False,
                },
                root=repo,
            )
        self._json(status, payload)


def build_server(repo: Path, host: str, port: int) -> DemoServer:
    root = Path(repo).resolve()
    handler = DemoHandler
    handler.repo = root
    handler.preview = PREVIEW.Preview(root)
    try:
        AI_BRIDGE.start_health_monitor(interval_seconds=120)
    except Exception as exc:
        print(f"Warning: could not start AI health monitor: {exc}", file=sys.stderr)
    return DemoServer((host, port), handler)


def serve(repo: Path, host: str, port: int) -> None:
    httpd = build_server(repo, host, port)
    print(f"Local preview at http://{host}:{port}/", file=sys.stderr)
    print(f"Walkthrough at http://{host}:{port}/demo.html", file=sys.stderr)
    httpd.serve_forever()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="_src/serve.sh",
        description="Canonical local preview server for the HTML tree and issue store.",
    )
    parser.add_argument("--repo", default=str(PREVIEW.ROOT), help="repository root")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    serve(Path(args.repo).resolve(), args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
