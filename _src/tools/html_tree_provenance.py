#!/usr/bin/env python3
"""Page generation and language-tree HTML artifact-set provenance (Task `0037-27.05`).

Records page-model / template / AI / diagram / i18n inputs, issue/criterion/run,
per-language HTML outputs and tree digest, validation/release relations, and
invalidation/regeneration cause. Manifests live under `provenance/`; generated
HTML must not contain provenance markers. Mixed-run language trees are rejected.

Writers bind to `provenance_store.SCHEMA_VERSION` and existing endpoint kinds.
Schema gaps are findings, not local schema forks.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import provenance_query as pq  # noqa: E402
import provenance_store as ps  # noqa: E402
import provenance_views as pv  # noqa: E402
import version_id as vid  # noqa: E402

SCHEMA = "html-tree-provenance@v1"
INPUT_ROLES = ("page-model", "template", "ai", "diagram", "i18n")
HTML_ROLE = "language-html"
MEMBER_ROLES = INPUT_ROLES + (HTML_ROLE,)
PRODUCER_FAMILIES = INPUT_ROLES
HTML_PROVENANCE_MARKERS = (
    "html-tree-provenance@",
    "provenance/runs/",
    "run_id",
    "set_digest",
    "invalidated-by",
    "regenerated-by",
    "page-composition-provenance@",
    "diagram-provenance@",
)


class HtmlTreeProvenanceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ref(kind: str, ident: str, **extra: Any) -> Dict[str, Any]:
    uri = ident if str(ident).startswith(kind + ":") else f"{kind}:{ident}"
    value = {
        "schema_version": ps.SCHEMA_VERSION,
        "kind": kind,
        "uri": uri,
        "classification": extra.pop("classification", "internal"),
    }
    value.update(extra)
    return value


def _artifact_ref(path: str, digest: str) -> Dict[str, Any]:
    return _ref("artifact", f"{path}@{digest}", digest=digest)


def _member(
    path: str,
    content: bytes,
    *,
    source_commit: str,
    media_type: str,
    role: str,
) -> Dict[str, Any]:
    if role not in MEMBER_ROLES:
        raise HtmlTreeProvenanceError("HTP-ROLE", f"unknown member role {role}")
    return {
        "path": path,
        "digest": ps.sha256_bytes(content),
        "size_bytes": len(content),
        "media_type": media_type,
        "source_commit": source_commit,
        "role": role,
    }


def input_identity(members: Sequence[Mapping[str, Any]]) -> str:
    keyed = {}
    for member in members:
        role = member.get("role")
        if role in INPUT_ROLES:
            keyed[role] = member["digest"]
    missing = [role for role in INPUT_ROLES if role not in keyed]
    if missing:
        raise HtmlTreeProvenanceError("HTP-IDENTITY", f"missing identity roles: {missing}")
    return ps.sha256_bytes(ps.canonical_bytes(keyed))


def assert_html_without_provenance(html_text: str) -> None:
    lowered = html_text.lower()
    for marker in HTML_PROVENANCE_MARKERS:
        if marker.lower() in lowered:
            raise HtmlTreeProvenanceError(
                "HTP-HTML-INJECT",
                f"HTML contains provenance marker {marker!r}",
            )


def render_representative_html(
    *,
    page_model: Mapping[str, Any],
    template: str,
    ai_html: str,
    diagram_svg: str,
    i18n: Mapping[str, Any],
    language: str,
) -> str:
    """Deterministic fixture renderer. Production generate.py remains the site generator."""
    title = page_model.get("title") or "untitled"
    localized = (i18n.get("titles") or {}).get(language, title)
    body = (
        template.replace("{{title}}", localized)
        .replace("{{ai}}", ai_html)
        .replace("{{diagram}}", diagram_svg)
    )
    html = (
        "<!DOCTYPE html>\n<html lang=\"%s\">\n<head><title>%s</title></head>\n"
        "<body><p class=\"page-model-title\">%s</p>%s</body>\n</html>\n"
        % (language, localized, title, body)
    )
    assert_html_without_provenance(html)
    return html


class HtmlTreeWorkflow:
    def __init__(self, root: Path, *, clock: Any = utc_now) -> None:
        self.root = Path(root)
        self.store = ps.ProvenanceStore(self.root)
        self.clock = clock
        self._index: List[Dict[str, Any]] = []
        self._load_index()

    def _stamp(self) -> str:
        return self.clock() if callable(self.clock) else str(self.clock)

    def _put_file(self, path: str, content: bytes) -> None:
        if path.endswith(".html"):
            assert_html_without_provenance(content.decode("utf-8", errors="replace"))
        disk = self.root / path
        disk.parent.mkdir(parents=True, exist_ok=True)
        disk.write_bytes(content)

    def _event(
        self,
        *,
        relation: str,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
        run_id: str,
        occurred_at: str,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "schema_version": ps.SCHEMA_VERSION,
            "event_id": vid.uuid7(),
            "occurred_at": occurred_at,
            "relation": relation,
            "source": dict(source),
            "target": dict(target),
            "environment": "development-test",
            "classification": "internal",
            "run": _ref("run", run_id),
        }
        if extra:
            payload.update(dict(extra))
        return self.store.create_event(payload)

    def _load_index(self) -> None:
        sets_dir = self.root / "provenance" / "artifact-sets"
        if not sets_dir.is_dir():
            return
        for path in sorted(sets_dir.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            members = record.get("members") or []
            html = [m for m in members if m.get("role") == HTML_ROLE]
            inputs = [m for m in members if m.get("role") in INPUT_ROLES]
            if not html or len(inputs) < len(INPUT_ROLES):
                continue
            language = None
            for member in html:
                parts = Path(member["path"]).parts
                language = parts[0] if parts and parts[0] not in {"_src", "provenance"} else "de"
            self._index.append(
                {
                    "schema": SCHEMA,
                    "run_id": ((record.get("producer") or {}).get("uri") or "run:").split(":", 1)[-1],
                    "set_id": record.get("set_id"),
                    "identity": input_identity(members),
                    "language": language,
                    "html_paths": [m["path"] for m in html],
                    "members": members,
                    "artifact_set": {"record": record},
                    "tree_digest": ps.tree_digest(html),
                }
            )

    def detect_mixed_run(self, language: str) -> List[str]:
        runs = sorted(
            {
                rec["run_id"]
                for rec in self._index
                if rec.get("language") == language and not rec.get("invalidated")
            }
        )
        if len(runs) > 1:
            raise HtmlTreeProvenanceError(
                "HTP-MIXED-RUN",
                f"language tree {language!r} mixes producer runs {runs}",
            )
        return runs

    def generate_language_tree(
        self,
        *,
        language: str,
        page_model_path: str,
        page_model_bytes: bytes,
        template_path: str,
        template_bytes: bytes,
        ai_path: str,
        ai_bytes: bytes,
        diagram_path: str,
        diagram_bytes: bytes,
        i18n_path: str,
        i18n_bytes: bytes,
        html_relpath: str,
        issue: str,
        criterion: str,
        source_commit: str,
        tool_commit: str,
        config_commit: str,
        campaign: str = "0037-27.05-html",
        validation_id: str = "validate-html-tree",
        release_id: str = "release-html-tree",
        previous: Optional[Mapping[str, Any]] = None,
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
        html_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        live = [
            rec
            for rec in self._index
            if rec.get("language") == language and not rec.get("invalidated")
        ]
        live_runs = sorted({rec["run_id"] for rec in live})
        if len(live_runs) > 1:
            raise HtmlTreeProvenanceError(
                "HTP-MIXED-RUN",
                f"language tree {language!r} mixes producer runs {live_runs}",
            )
        if previous is None and live:
            raise HtmlTreeProvenanceError(
                "HTP-MIXED-RUN",
                f"language tree {language!r} already has live run {live_runs}",
            )
        if previous is not None and live_runs and previous.get("run_id") not in live_runs:
            raise HtmlTreeProvenanceError(
                "HTP-MIXED-RUN",
                f"language tree {language!r} already has a foreign live run",
            )

        page_model = json.loads(page_model_bytes.decode("utf-8"))
        i18n = json.loads(i18n_bytes.decode("utf-8"))
        if html_bytes is None:
            html_text = render_representative_html(
                page_model=page_model,
                template=template_bytes.decode("utf-8"),
                ai_html=ai_bytes.decode("utf-8"),
                diagram_svg=diagram_bytes.decode("utf-8"),
                i18n=i18n,
                language=language,
            )
            html_bytes = html_text.encode("utf-8")
        else:
            assert_html_without_provenance(html_bytes.decode("utf-8", errors="replace"))

        started = started_at or self._stamp()
        ended = ended_at or self._stamp()
        run_id = vid.uuid7()
        set_id = vid.uuid7()

        self._put_file(page_model_path, page_model_bytes)
        self._put_file(template_path, template_bytes)
        self._put_file(ai_path, ai_bytes)
        self._put_file(diagram_path, diagram_bytes)
        self._put_file(i18n_path, i18n_bytes)
        self._put_file(html_relpath, html_bytes)

        members = [
            _member(page_model_path, page_model_bytes, source_commit=source_commit, media_type="application/json", role="page-model"),
            _member(template_path, template_bytes, source_commit=source_commit, media_type="text/html", role="template"),
            _member(ai_path, ai_bytes, source_commit=source_commit, media_type="text/html", role="ai"),
            _member(diagram_path, diagram_bytes, source_commit=source_commit, media_type="image/svg+xml", role="diagram"),
            _member(i18n_path, i18n_bytes, source_commit=source_commit, media_type="application/json", role="i18n"),
            _member(html_relpath, html_bytes, source_commit=source_commit, media_type="text/html", role=HTML_ROLE),
        ]
        identity = input_identity(members)
        html_members = [m for m in members if m["role"] == HTML_ROLE]
        tree = ps.tree_digest(html_members)
        html_digest = ps.sha256_bytes(html_bytes)

        run_inputs = [
            _ref("commit", source_commit),
            _ref("commit", tool_commit),
            _ref("commit", config_commit),
            _ref("issue", issue),
            _ref("criterion", criterion),
            _ref("campaign", campaign),
            _artifact_ref(page_model_path, ps.sha256_bytes(page_model_bytes)),
            _artifact_ref(template_path, ps.sha256_bytes(template_bytes)),
            _artifact_ref(ai_path, ps.sha256_bytes(ai_bytes)),
            _artifact_ref(diagram_path, ps.sha256_bytes(diagram_bytes)),
            _artifact_ref(i18n_path, ps.sha256_bytes(i18n_bytes)),
        ]

        run = self.store.create_run(
            {
                "schema_version": ps.SCHEMA_VERSION,
                "run_id": run_id,
                "started_at": started,
                "ended_at": ended,
                "environment": "development-test",
                "classification": "internal",
                "status": "succeeded",
                "producer": _ref("commit", tool_commit),
                "inputs": run_inputs,
                "outputs": [_ref("artifact-set", set_id)],
            }
        )
        aset = self.store.create_artifact_set(
            {
                "schema_version": ps.SCHEMA_VERSION,
                "set_id": set_id,
                "created_at": ended,
                "classification": "internal",
                "environment": "development-test",
                "producer": _ref("run", run_id),
                "members": members,
            }
        )
        html_ref = _artifact_ref(html_relpath, html_digest)
        set_ref = _ref("artifact-set", set_id, digest=aset["record"]["set_digest"])
        self._event(relation="produced-by", source=html_ref, target=_ref("run", run_id), run_id=run_id, occurred_at=ended)
        self._event(relation="produced-by", source=set_ref, target=_ref("run", run_id), run_id=run_id, occurred_at=ended)
        for role, path, blob in (
            ("page-model", page_model_path, page_model_bytes),
            ("template", template_path, template_bytes),
            ("ai", ai_path, ai_bytes),
            ("diagram", diagram_path, diagram_bytes),
            ("i18n", i18n_path, i18n_bytes),
        ):
            self._event(
                relation="derived-from",
                source=html_ref,
                target=_artifact_ref(path, ps.sha256_bytes(blob)),
                run_id=run_id,
                occurred_at=ended,
            )
        self._event(relation="implements", source=html_ref, target=_ref("issue", issue), run_id=run_id, occurred_at=ended)
        self._event(relation="triggered", source=_ref("issue", issue), target=_ref("run", run_id), run_id=run_id, occurred_at=ended)
        self._event(
            relation="verifies",
            source=_ref("run", run_id),
            target=_ref("criterion", criterion),
            run_id=run_id,
            occurred_at=ended,
        )
        self._event(
            relation="verifies",
            source=_ref("run", run_id),
            target=html_ref,
            run_id=run_id,
            occurred_at=ended,
        )
        release_path = f"provenance/releases/{release_id}.json"
        release_blob = ps.canonical_bytes(
            {
                "schema_version": ps.SCHEMA_VERSION,
                "release_id": release_id,
                "language": language,
                "tree_digest": tree,
                "set_id": set_id,
                "run_id": run_id,
            }
        )
        self._put_file(release_path, release_blob)
        self._event(
            relation="published-as",
            source=set_ref,
            target=_artifact_ref(release_path, ps.sha256_bytes(release_blob)),
            run_id=run_id,
            occurred_at=ended,
        )

        envelope = {
            "schema": SCHEMA,
            "schema_version": ps.SCHEMA_VERSION,
            "run_id": run_id,
            "set_id": set_id,
            "language": language,
            "issue": issue,
            "criterion": criterion,
            "identity": identity,
            "tree_digest": tree,
            "validation_id": validation_id,
            "release_id": release_id,
            "html_path": html_relpath,
            "html_digest": html_digest,
            "members": members,
        }
        env_path = f"provenance/html-trees/{language}/{run_id}.json"
        self._put_file(env_path, (json.dumps(envelope, sort_keys=True, indent=2) + "\n").encode("utf-8"))

        invalidation = None
        if previous is not None:
            invalidation = self._link_replacement(previous, html_ref, set_ref, run_id, ended, identity, language)

        record = {
            "schema": SCHEMA,
            "schema_version": ps.SCHEMA_VERSION,
            "run_id": run_id,
            "set_id": set_id,
            "identity": identity,
            "language": language,
            "issue": issue,
            "criterion": criterion,
            "html_path": html_relpath,
            "html_digest": html_digest,
            "tree_digest": tree,
            "validation_id": validation_id,
            "release_id": release_id,
            "members": members,
            "run": run,
            "artifact_set": aset,
            "invalidation": invalidation,
            "envelope_path": env_path,
        }
        self._index.append(record)
        if previous is not None:
            for rec in self._index:
                if rec.get("run_id") == previous.get("run_id"):
                    rec["invalidated"] = True
        return record

    def _link_replacement(
        self,
        previous: Mapping[str, Any],
        new_html: Mapping[str, Any],
        new_set: Mapping[str, Any],
        run_id: str,
        occurred_at: str,
        new_identity: str,
        language: str,
    ) -> Dict[str, Any]:
        old_html = _artifact_ref(previous["html_path"], previous["html_digest"])
        finding_id = vid.uuid7()
        finding = self.store.create_finding(
            {
                "schema_version": ps.SCHEMA_VERSION,
                "finding_id": finding_id,
                "detected_at": occurred_at,
                "state": "invalidated",
                "classification": "internal",
                "environment": "development-test",
                "subject": old_html,
                "detected_during": _ref("run", run_id),
                "evidence": [old_html, dict(new_html)],
            }
        )
        self._event(
            relation="invalidated-by",
            source=old_html,
            target=_ref("run", run_id),
            run_id=run_id,
            occurred_at=occurred_at,
        )
        self._event(
            relation="regenerated-by",
            source=new_html,
            target=_ref("run", run_id),
            run_id=run_id,
            occurred_at=occurred_at,
        )
        self._event(
            relation="supersedes",
            source=new_html,
            target=old_html,
            run_id=run_id,
            occurred_at=occurred_at,
        )
        self._event(
            relation="supersedes",
            source=new_set,
            target=_ref("artifact-set", previous["set_id"]),
            run_id=run_id,
            occurred_at=occurred_at,
        )
        return {
            "previous_html": old_html,
            "replacement_html": dict(new_html),
            "finding": finding,
            "previous_identity": previous.get("identity"),
            "new_identity": new_identity,
            "language": language,
            "cause": "governed page-generation input change",
        }

    def stale_trees(
        self,
        *,
        page_model_bytes: bytes,
        template_bytes: bytes,
        ai_bytes: bytes,
        diagram_bytes: bytes,
        i18n_bytes: bytes,
        language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        current = {
            "page-model": ps.sha256_bytes(page_model_bytes),
            "template": ps.sha256_bytes(template_bytes),
            "ai": ps.sha256_bytes(ai_bytes),
            "diagram": ps.sha256_bytes(diagram_bytes),
            "i18n": ps.sha256_bytes(i18n_bytes),
        }
        stale: List[Dict[str, Any]] = []
        for record in self._index:
            if record.get("invalidated"):
                continue
            if language is not None and record.get("language") != language:
                continue
            keyed = {
                m["role"]: m["digest"]
                for m in record["members"]
                if m.get("role") in INPUT_ROLES
            }
            if keyed != current:
                stale.append(
                    {
                        "html_path": record["html_path"],
                        "html_digest": record["html_digest"],
                        "run_id": record["run_id"],
                        "language": record["language"],
                        "previous_identity": record["identity"],
                    }
                )
        return stale

    def regeneration_work(self, **kwargs: Any) -> List[Dict[str, Any]]:
        return self.stale_trees(**kwargs)

    def trace_html_to_families(self, html_path: str) -> Dict[str, Any]:
        pv.build_views(self.root)
        families: Dict[str, Any] = {}
        for record in self._index:
            if record.get("html_path") != html_path:
                continue
            for member in record["members"]:
                role = member.get("role")
                if role in PRODUCER_FAMILIES:
                    families[role] = {
                        "path": member["path"],
                        "digest": member["digest"],
                    }
            reverse = pq.query_trace(
                self.root,
                kind="artifact",
                identifier=f"{html_path}@{record['html_digest']}",
                direction="reverse",
            )
            return {
                "html_path": html_path,
                "run_id": record["run_id"],
                "families": families,
                "missing_families": [f for f in PRODUCER_FAMILIES if f not in families],
                "reverse": reverse,
            }
        raise HtmlTreeProvenanceError("HTP-HTML", f"no artifact-set for {html_path}")

    def trace(self, *, kind: str, identifier: str, direction: str = "reverse") -> Dict[str, Any]:
        pv.build_views(self.root)
        return pq.query_trace(self.root, kind=kind, identifier=identifier, direction=direction)


def provenance_requested(argv: Optional[Sequence[str]] = None, env: Optional[Mapping[str, str]] = None) -> bool:
    args = list(argv if argv is not None else sys.argv[1:])
    environ = env if env is not None else os.environ
    return "--provenance" in args or environ.get("HTML_TREE_PROVENANCE") == "1"


def record_after_generate(
    *,
    repo_root: Path,
    languages: Sequence[str],
    issue: str = "0037-27.05",
    criterion: str = "AC-html-tree-provenance",
    source_commit: str,
    tool_commit: str,
    config_commit: str,
) -> None:
    """Optional generate.py hook. Gaps (missing input families) are findings, not schema forks."""
    wf = HtmlTreeWorkflow(repo_root)
    missing = []
    for required in (
        "_src/sources/pages",
        "_src/templates",
        "_src/content/ai",
        "_src/diagrams",
        "_src/i18n",
    ):
        if not (repo_root / required).exists():
            missing.append(required)
    if missing:
        finding = {
            "schema_version": ps.SCHEMA_VERSION,
            "code": "HTP-INPUT-GAP",
            "message": "page-generation input family path missing; not inventing a local schema",
            "missing": missing,
        }
        dest = repo_root / "provenance" / "findings" / "html-tree-input-gap.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(finding, indent=2) + "\n", encoding="utf-8")
        return
    wf.detect_mixed_run(languages[0] if languages else "de")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Record HTML language-tree provenance")
    parser.add_argument("--root", required=True)
    parser.add_argument("--language", required=True)
    args = parser.parse_args(argv)
    print(json.dumps({"root": args.root, "language": args.language, "schema": SCHEMA}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
