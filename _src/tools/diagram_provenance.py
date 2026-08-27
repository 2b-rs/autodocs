#!/usr/bin/env python3
"""Diagram source and rendered-SVG provenance (Task `0037-27.02`).

Extends the Graphviz/sequence render workflows with common provenance
manifests. Generated-file metadata lives in artifact-sets and events, never
as uncontrolled injection into SVG markup.

Schema: diagram-provenance@v1
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import provenance_query as pq  # noqa: E402
import provenance_store as ps  # noqa: E402
import provenance_views as pv  # noqa: E402
import version_id as vid  # noqa: E402

SCHEMA = "diagram-provenance@v1"
SOURCE_ROLES = ("source-model", "labels", "theme", "tool", "config")
SVG_ROLE = "rendered-svg"
MEMBER_ROLES = SOURCE_ROLES + (SVG_ROLE,)
THEME_PATH = "provenance/_diagram-inputs/theme-v1.json"
TOOL_PATH = "provenance/_diagram-inputs/diagram_provenance.py"
CONFIG_PATH = "provenance/_diagram-inputs/lib_svgdiag.py"
PROVENANCE_MARKERS = (
    "diagram-provenance@",
    "provenance/runs/",
    "run_id",
    "set_digest",
    "invalidated-by",
    "regenerated-by",
)


class DiagramProvenanceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def theme_payload(constants: Mapping[str, str] | None = None) -> Dict[str, str]:
    if constants is not None:
        return dict(constants)
    try:
        sys.path.insert(0, str(_TOOLS.parent))
        import lib_svgdiag as diag  # type: ignore
    except Exception:
        return {
            "C_BG": "#f9f8f5",
            "C_TEXT": "#28251d",
            "C_ACCENT": "#01696f",
            "C_MUTED": "#7a7974",
            "C_FRAME": "#d4d1ca",
            "FONT": "Helvetica,sans-Serif",
        }
    return {
        "C_BG": diag.C_BG,
        "C_TEXT": diag.C_TEXT,
        "C_ACCENT": diag.C_ACCENT,
        "C_MUTED": diag.C_MUTED,
        "C_FRAME": diag.C_FRAME,
        "FONT": diag.FONT,
    }


def theme_bytes(constants: Mapping[str, str] | None = None) -> bytes:
    return ps.canonical_bytes(theme_payload(constants))


def assert_svg_without_provenance(svg_text: str) -> None:
    """Reject uncontrolled provenance injection into SVG markup."""
    lowered = svg_text.lower()
    if "<metadata" in lowered:
        raise DiagramProvenanceError("DP-SVG-INJECT", "SVG metadata element is not allowed")
    for marker in PROVENANCE_MARKERS:
        if marker.lower() in lowered:
            raise DiagramProvenanceError(
                "DP-SVG-INJECT",
                f"SVG markup contains provenance marker {marker!r}",
            )


def _ref(kind: str, ident: str, **extra: Any) -> Dict[str, Any]:
    uri = ident if str(ident).startswith(kind + ":") else f"{kind}:{ident}"
    value = {
        "schema_version": "1.0",
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
    language: Optional[str] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    if role not in MEMBER_ROLES:
        raise DiagramProvenanceError("DP-ROLE", f"unknown member role {role}")
    member: Dict[str, Any] = {
        "path": path,
        "digest": ps.sha256_bytes(content),
        "size_bytes": len(content),
        "media_type": media_type,
        "source_commit": source_commit,
        "role": role,
    }
    if language is not None:
        member["language"] = language
    if extra:
        member.update(dict(extra))
    return member


def input_identity(members: Sequence[Mapping[str, Any]]) -> str:
    """Content identity of source model, labels, and theme (not mtime, not SVG)."""
    keyed = {}
    for member in members:
        role = member.get("role")
        if role in {"source-model", "labels", "theme"}:
            keyed[role] = member["digest"]
    if "source-model" not in keyed or "theme" not in keyed:
        raise DiagramProvenanceError("DP-IDENTITY", "source-model and theme required for identity")
    return ps.sha256_bytes(ps.canonical_bytes(keyed))


class DiagramProvenanceWorkflow:
    def __init__(
        self,
        root: Path,
        *,
        file_bytes: Optional[Any] = None,
        clock: Any = utc_now,
    ) -> None:
        self.root = Path(root)
        self.files: Dict[str, bytes] = {} if file_bytes is None else file_bytes
        self.store = ps.ProvenanceStore(self.root, file_bytes=self._file_bytes)
        self.clock = clock
        self._index: List[Dict[str, Any]] = []
        self._load_index()

    def _file_bytes(self, path: str) -> bytes:
        if path in self.files:
            return self.files[path]
        disk = self.root / path
        if disk.is_file():
            return disk.read_bytes()
        raise KeyError(path)

    def _load_index(self) -> None:
        sets_dir = self.root / "provenance" / "artifact-sets"
        if not sets_dir.is_dir():
            return
        for path in sorted(sets_dir.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            members = record.get("members") or []
            svg_members = [m for m in members if m.get("role") == SVG_ROLE]
            source_members = [m for m in members if m.get("role") == "source-model"]
            if not svg_members or not source_members:
                continue
            svg_m = svg_members[0]
            src_m = source_members[0]
            labels = next((m for m in members if m.get("role") == "labels"), None)
            theme = next((m for m in members if m.get("role") == "theme"), None)
            self._index.append(
                {
                    "schema": SCHEMA,
                    "run_id": ((record.get("producer") or {}).get("uri") or "run:").split(":", 1)[-1],
                    "set_id": record.get("set_id"),
                    "identity": input_identity(members) if theme else "",
                    "language": svg_m.get("language") or "de",
                    "source_path": src_m["path"],
                    "svg_path": svg_m["path"],
                    "svg_digest": svg_m["digest"],
                    "source_digest": src_m["digest"],
                    "labels_digest": labels["digest"] if labels else None,
                    "theme_digest": theme["digest"] if theme else None,
                    "members": members,
                    "artifact_set": {"record": record},
                }
            )

    def _stamp(self) -> str:
        return self.clock() if callable(self.clock) else str(self.clock)

    def _put_file(self, path: str, content: bytes) -> None:
        self.files[path] = content
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
            "schema_version": "1.0",
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

    def record_render(
        self,
        *,
        source_path: str,
        source_bytes: bytes,
        svg_path: str,
        svg_text: str,
        language: str,
        issue: str,
        criterion: str,
        source_commit: str,
        tool_commit: str,
        config_commit: str,
        labels_path: Optional[str] = None,
        labels_bytes: Optional[bytes] = None,
        theme_constants: Optional[Mapping[str, str]] = None,
        campaign: str = "0037-27.02-diagrams",
        previous: Optional[Mapping[str, Any]] = None,
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        assert_svg_without_provenance(svg_text)
        svg_bytes = svg_text.encode("utf-8")
        theme = theme_bytes(theme_constants)
        tool_bytes = Path(__file__).read_bytes()
        try:
            config_bytes = (_TOOLS.parent / "lib_svgdiag.py").read_bytes()
        except OSError:
            config_bytes = b"lib_svgdiag-absent\n"
        started = started_at or self._stamp()
        ended = ended_at or self._stamp()
        run_id = vid.uuid7()
        set_id = vid.uuid7()

        self._put_file(source_path, source_bytes)
        self._put_file(svg_path, svg_bytes)
        self._put_file(THEME_PATH, theme)
        self._put_file(TOOL_PATH, tool_bytes)
        self._put_file(CONFIG_PATH, config_bytes)
        if labels_path is not None:
            if labels_bytes is None:
                raise DiagramProvenanceError("DP-LABELS", "labels_path requires labels_bytes")
            self._put_file(labels_path, labels_bytes)

        members = [
            _member(
                source_path,
                source_bytes,
                source_commit=source_commit,
                media_type="text/plain",
                role="source-model",
                language=language,
            ),
            _member(
                THEME_PATH,
                theme,
                source_commit=config_commit,
                media_type="application/json",
                role="theme",
            ),
            _member(
                TOOL_PATH,
                tool_bytes,
                source_commit=tool_commit,
                media_type="text/x-python",
                role="tool",
            ),
            _member(
                CONFIG_PATH,
                config_bytes,
                source_commit=config_commit,
                media_type="text/x-python",
                role="config",
            ),
            _member(
                svg_path,
                svg_bytes,
                source_commit=source_commit,
                media_type="image/svg+xml",
                role=SVG_ROLE,
                language=language,
            ),
        ]
        if labels_path is not None and labels_bytes is not None:
            members.insert(
                1,
                _member(
                    labels_path,
                    labels_bytes,
                    source_commit=source_commit,
                    media_type="application/json",
                    role="labels",
                    language=language,
                ),
            )

        identity = input_identity(members)
        svg_digest = ps.sha256_bytes(svg_bytes)
        source_digest = ps.sha256_bytes(source_bytes)

        run_inputs = [
            _ref("commit", source_commit),
            _ref("commit", tool_commit),
            _ref("commit", config_commit),
            _ref("issue", issue),
            _ref("criterion", criterion),
            _ref("campaign", campaign),
            _artifact_ref(source_path, source_digest),
        ]
        if labels_path is not None and labels_bytes is not None:
            run_inputs.append(_artifact_ref(labels_path, ps.sha256_bytes(labels_bytes)))
        run_inputs.append(_artifact_ref(THEME_PATH, ps.sha256_bytes(theme)))

        run = self.store.create_run(
            {
                "schema_version": "1.0",
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
                "schema_version": "1.0",
                "set_id": set_id,
                "created_at": ended,
                "classification": "internal",
                "environment": "development-test",
                "producer": _ref("run", run_id),
                "members": members,
            }
        )
        svg_ref = _artifact_ref(svg_path, svg_digest)
        source_ref = _artifact_ref(source_path, source_digest)
        self._event(
            relation="produced-by",
            source=svg_ref,
            target=_ref("run", run_id),
            run_id=run_id,
            occurred_at=ended,
        )
        self._event(
            relation="derived-from",
            source=svg_ref,
            target=source_ref,
            run_id=run_id,
            occurred_at=ended,
        )
        self._event(
            relation="implements",
            source=svg_ref,
            target=_ref("issue", issue),
            run_id=run_id,
            occurred_at=ended,
        )
        self._event(
            relation="verifies",
            source=_ref("run", run_id),
            target=_ref("criterion", criterion),
            run_id=run_id,
            occurred_at=ended,
        )

        invalidation = None
        if previous is not None:
            invalidation = self._link_replacement(previous, svg_ref, run_id, ended, identity)

        record = {
            "schema": SCHEMA,
            "run_id": run_id,
            "set_id": set_id,
            "identity": identity,
            "language": language,
            "issue": issue,
            "criterion": criterion,
            "source_path": source_path,
            "svg_path": svg_path,
            "svg_digest": svg_digest,
            "source_digest": source_digest,
            "labels_digest": ps.sha256_bytes(labels_bytes) if labels_bytes is not None else None,
            "theme_digest": ps.sha256_bytes(theme),
            "tool_commit": tool_commit,
            "config_commit": config_commit,
            "source_commit": source_commit,
            "members": members,
            "run": run,
            "artifact_set": aset,
            "invalidation": invalidation,
        }
        self._index.append(record)
        return record

    def _link_replacement(
        self,
        previous: Mapping[str, Any],
        new_svg: Mapping[str, Any],
        run_id: str,
        occurred_at: str,
        new_identity: str,
    ) -> Dict[str, Any]:
        old_svg = _artifact_ref(previous["svg_path"], previous["svg_digest"])
        finding_id = vid.uuid7()
        finding = self.store.create_finding(
            {
                "schema_version": "1.0",
                "finding_id": finding_id,
                "detected_at": occurred_at,
                "state": "invalidated",
                "classification": "internal",
                "environment": "development-test",
                "subject": old_svg,
                "detected_during": _ref("run", run_id),
                "evidence": [old_svg, new_svg],
            }
        )
        self._event(
            relation="invalidated-by",
            source=old_svg,
            target=_ref("run", run_id),
            run_id=run_id,
            occurred_at=occurred_at,
        )
        self._event(
            relation="regenerated-by",
            source=new_svg,
            target=_ref("run", run_id),
            run_id=run_id,
            occurred_at=occurred_at,
        )
        self._event(
            relation="supersedes",
            source=new_svg,
            target=old_svg,
            run_id=run_id,
            occurred_at=occurred_at,
        )
        return {
            "previous_svg": old_svg,
            "replacement_svg": dict(new_svg),
            "finding": finding,
            "previous_identity": previous.get("identity"),
            "new_identity": new_identity,
        }

    def stale_svgs(
        self,
        *,
        source_path: str,
        source_bytes: bytes,
        labels_bytes: Optional[bytes],
        theme_constants: Optional[Mapping[str, str]] = None,
        language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return exact rendered SVGs whose source/label/theme identity drifted."""
        current = {
            "source-model": ps.sha256_bytes(source_bytes),
            "theme": ps.sha256_bytes(theme_bytes(theme_constants)),
        }
        if labels_bytes is not None:
            current["labels"] = ps.sha256_bytes(labels_bytes)
        stale: List[Dict[str, Any]] = []
        for record in self._index:
            if record["source_path"] != source_path:
                continue
            if language is not None and record["language"] != language:
                continue
            keyed = {}
            for member in record["members"]:
                if member.get("role") in {"source-model", "labels", "theme"}:
                    keyed[member["role"]] = member["digest"]
            if keyed != current:
                stale.append(
                    {
                        "svg_path": record["svg_path"],
                        "svg_digest": record["svg_digest"],
                        "language": record["language"],
                        "run_id": record["run_id"],
                        "previous_identity": record["identity"],
                    }
                )
        return stale

    def trace(self, *, kind: str, identifier: str, direction: str = "reverse") -> Dict[str, Any]:
        pv.build_views(self.root)
        return pq.query_trace(self.root, kind=kind, identifier=identifier, direction=direction)


def record_file_diagram(
    workflow: DiagramProvenanceWorkflow,
    src: Path,
    svg_text: str,
    *,
    language: str,
    issue: str,
    criterion: str,
    source_commit: str,
    tool_commit: str,
    config_commit: str,
    labels_path: Optional[Path] = None,
    repository_root: Optional[Path] = None,
    svg_path: Optional[Path] = None,
) -> Dict[str, Any]:
    root = Path(repository_root or workflow.root)
    rel_src = src.resolve().relative_to(root.resolve()).as_posix()
    if svg_path is None:
        svg_path = src.with_suffix(".svg")
        if src.name.endswith(".seq.json"):
            svg_path = src.parent / (src.name[: -len(".seq.json")] + ".svg")
    rel_svg = Path(svg_path).resolve().relative_to(root.resolve()).as_posix()
    labels_rel = None
    labels_bytes = None
    if labels_path is not None:
        labels_rel = labels_path.resolve().relative_to(root.resolve()).as_posix()
        labels_bytes = labels_path.read_bytes()
    previous = None
    stale = workflow.stale_svgs(
        source_path=rel_src,
        source_bytes=src.read_bytes(),
        labels_bytes=labels_bytes,
        language=language,
    )
    if stale:
        for rec in reversed(workflow._index):
            if rec["svg_path"] == stale[0]["svg_path"]:
                previous = rec
                break
    return workflow.record_render(
        source_path=rel_src,
        source_bytes=src.read_bytes(),
        svg_path=rel_svg,
        svg_text=svg_text,
        language=language,
        issue=issue,
        criterion=criterion,
        source_commit=source_commit,
        tool_commit=tool_commit,
        config_commit=config_commit,
        labels_path=labels_rel,
        labels_bytes=labels_bytes,
        previous=previous,
    )


def maybe_record_from_env(
    src: Path,
    svg_text: str,
    *,
    language: str,
    repository_root: Path,
    svg_path: Optional[Path] = None,
    labels_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Hook for render_diagrams.py / i18n_diagrams.py. No-op unless configured."""
    import os

    root = os.environ.get("DIAGRAM_PROVENANCE_ROOT")
    if not root:
        return None
    assert_svg_without_provenance(svg_text)
    issue = os.environ.get("DIAGRAM_PROVENANCE_ISSUE", "0037-27.02")
    criterion = os.environ.get("DIAGRAM_PROVENANCE_CRITERION", "AC-diagram-provenance")
    commit = os.environ.get("DIAGRAM_PROVENANCE_COMMIT", "0" * 40)
    labels = labels_path or os.environ.get("DIAGRAM_PROVENANCE_LABELS")
    workflow = DiagramProvenanceWorkflow(Path(root))
    return record_file_diagram(
        workflow,
        src,
        svg_text,
        language=language,
        issue=issue,
        criterion=criterion,
        source_commit=commit,
        tool_commit=commit,
        config_commit=commit,
        labels_path=Path(labels) if labels else None,
        repository_root=repository_root,
        svg_path=svg_path,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Record diagram SVG provenance manifests")
    parser.add_argument("--root", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--svg", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--issue", default="0037-27.02")
    parser.add_argument("--criterion", default="AC-diagram-provenance")
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--tool-commit", required=True)
    parser.add_argument("--config-commit", required=True)
    parser.add_argument("--labels")
    args = parser.parse_args(argv)
    root = Path(args.root)
    source = Path(args.source)
    svg = Path(args.svg)
    wf = DiagramProvenanceWorkflow(root)
    record = wf.record_render(
        source_path=source.as_posix() if source.is_absolute() else args.source,
        source_bytes=source.read_bytes(),
        svg_path=svg.as_posix() if svg.is_absolute() else args.svg,
        svg_text=svg.read_text(encoding="utf-8"),
        language=args.language,
        issue=args.issue,
        criterion=args.criterion,
        source_commit=args.source_commit,
        tool_commit=args.tool_commit,
        config_commit=args.config_commit,
        labels_path=args.labels,
        labels_bytes=Path(args.labels).read_bytes() if args.labels else None,
    )
    print(json.dumps({"run_id": record["run_id"], "set_id": record["set_id"], "svg_digest": record["svg_digest"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
