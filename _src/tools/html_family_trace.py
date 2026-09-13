#!/usr/bin/env python3
"""Package-level HTML→family provenance trace for Task `0037-27`.

Orchestrates the five Subtask producers (AI claims, diagrams, page composition,
i18n, HTML trees) in one hermetic store. Does not rewrite those producer
modules. Generated HTML/SVG stay free of provenance injection; metadata lives
in `provenance/` envelopes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import ai_workflow_persist as awp  # noqa: E402
import diagram_provenance as dp  # noqa: E402
import html_tree_provenance as htp  # noqa: E402
import i18n_translation_provenance as i18n  # noqa: E402
import page_composition_provenance as pcp  # noqa: E402
import provenance_store as ps  # noqa: E402
import version_id as vid  # noqa: E402

SCHEMA = "html-family-trace@v1"
FAMILIES = ("ai", "diagram", "guides", "i18n", "html")
DECISION = "rev-0037-27-package-ok"
STAMP = "2026-08-27T13:25:00Z"


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _present(name: str, body: str, kind: str = "artifact") -> dict:
    return {"present": True, "kind": kind, "uri": f"{kind}:{name}", "digest": _sha(body)}


def default_pins() -> Dict[str, Any]:
    return {
        "record": _present("record", "record-v1"),
        "evidence": _present("evidence", "evidence-v1"),
        "policy": _present("policy", "policy-v1"),
        "prompt": _present("prompt", "prompt-v1"),
        "model": _present("model", "gpt-test"),
        "config": _present("config", "config-v1"),
        "input": _present("input", "input-v1"),
    }


def assemble_cross_family(
    root: Path,
    *,
    source_commit: str,
    tool_commit: str,
    config_commit: str,
    clock: str = STAMP,
    pins: Optional[Mapping[str, Any]] = None,
    fragment_bytes: bytes,
    records_bytes: bytes,
    evidence_bytes: bytes,
    instructions_bytes: bytes,
    policy_bytes: bytes,
    config_bytes: bytes,
    composed_bytes: bytes,
    template_bytes: bytes,
    source_dot: bytes,
    svg_text: str,
    labels_bytes: bytes,
    segment_source: str,
    segment_translation: str,
) -> Dict[str, Any]:
    """Run all five producers against one store and reverse-trace HTML."""
    root = Path(root)
    pinset = dict(pins or default_pins())
    persist = awp.AIWorkflowPersist(root)
    ai_run_id = vid.uuid7()
    persist.persist_run(
        run_id=ai_run_id,
        started_at=clock,
        ended_at=clock,
        commit=source_commit,
        issue="0037-27.01",
        criterion="AC-ai-workflow",
        campaign="0037-27-package",
        pins=pinset,
    )
    claim = persist.persist_claim(
        content="The pipeline is deterministic.",
        parent_artifact_id="artifact:guide-fragment",
        pins=pinset,
        run_id=ai_run_id,
        issue="0037-27.01",
        criterion="AC-ai-workflow",
        campaign="0037-27-package",
        evidence_refs=[f"decision:{DECISION}", "artifact:record:demo"],
        claim_type="curated_fact",
        confidence=1.0,
    )
    claim_id = claim["claim"]["claim_id"]
    claim_trace = persist.trace_claim(claim_id)

    diagrams = dp.DiagramProvenanceWorkflow(root, clock=lambda: clock)
    diagram = diagrams.record_render(
        source_path="_src/diagrams/demo/svg_01.dot",
        source_bytes=source_dot,
        svg_path="_src/diagrams/demo/svg_01.svg",
        svg_text=svg_text,
        language="en",
        issue="0037-27.02",
        criterion="AC-diagram-provenance",
        source_commit=source_commit,
        tool_commit=tool_commit,
        config_commit=config_commit,
        labels_path="_src/diagrams/demo/en.labels.json",
        labels_bytes=labels_bytes,
        campaign="0037-27-package",
    )
    diagram_rev = diagrams.trace(
        kind="artifact",
        identifier=f"{diagram['svg_path']}@{diagram['svg_digest']}",
        direction="reverse",
    )
    diagram_fwd = diagrams.trace(kind="issue", identifier="0037-27.02", direction="forward")

    pages = pcp.PageCompositionWorkflow(root, clock=lambda: clock)
    composed = pages.compose(
        fragment_path="_src/sources/pages/guide-fragment.json",
        fragment_bytes=fragment_bytes,
        records_path="_src/spec/records/demo.json",
        records_bytes=records_bytes,
        evidence_path="provenance/_page-inputs/evidence.json",
        evidence_bytes=evidence_bytes,
        instructions_path="AGENTS.md",
        instructions_bytes=instructions_bytes,
        policy_path="_src/sources/pages/policy.json",
        policy_bytes=policy_bytes,
        config_path="_src/sources/pages/config.json",
        config_bytes=config_bytes,
        output_path="_src/sources/pages/guide.json",
        output_bytes=composed_bytes,
        claim_ids=[claim_id],
        issue="0037-27.03",
        criterion="AC-page-composition",
        decision_id=DECISION,
        source_commit=source_commit,
        tool_commit=tool_commit,
        config_commit=config_commit,
        campaign="0037-27-package",
    )

    i18n_store = ps.ProvenanceStore(root)
    i18n_run_id = vid.uuid7()
    i18n_rec = i18n.record_translation_run(
        i18n_store,
        run_id=i18n_run_id,
        set_id=vid.uuid7(),
        event_ids={
            "produced-by": vid.uuid7(),
            "derived-from": vid.uuid7(),
            "invalidated-by": vid.uuid7(),
        },
        started_at=clock,
        ended_at=clock,
        commit=source_commit,
        issue="0037-27.04",
        criterion="AC-i18n-provenance",
        producer_path="_src/i18n_translate.py",
        family="segment",
        target_locale="en",
        translator={"id": "human-curator", "method": "human"},
        model={"id": "none", "kind": "human-authored"},
        policy={"id": "i18n-protected-tokens@v1"},
        config={"merge": "i18n_translate.merge", "preserve_registers": True},
        register_path="_src/i18n/en/segments.json",
        entries=[
            {
                "family": "segment",
                "source_id": "seg-prose-01",
                "source_text": segment_source,
                "source_locale": "de",
                "target_locale": "en",
                "translation": segment_translation,
                "merge_decision": "accepted",
            }
        ],
    )
    i18n_trace = i18n.trace_to_run(i18n_rec["envelope"], "seg-prose-01")

    html_wf = htp.HtmlTreeWorkflow(root, clock=lambda: clock)
    ai_html = f"<p>{claim['claim']['content']}</p>".encode("utf-8")
    i18n_bytes = json.dumps({"title": "Pipeline Guide"}, separators=(",", ":")).encode("utf-8")
    html_rec = html_wf.generate_language_tree(
        language="en",
        page_model_path=composed["output_path"],
        page_model_bytes=composed_bytes,
        template_path="_src/templates/page.html",
        template_bytes=template_bytes,
        ai_path="_src/content/ai/guide-claim.html",
        ai_bytes=ai_html,
        diagram_path=diagram["svg_path"],
        diagram_bytes=svg_text.encode("utf-8"),
        i18n_path="_src/i18n/en/titles.json",
        i18n_bytes=i18n_bytes,
        html_relpath="en/guide.html",
        issue="0037-27",
        criterion="DoD-html-family-trace",
        source_commit=source_commit,
        tool_commit=tool_commit,
        config_commit=config_commit,
        campaign="0037-27-package",
    )
    html_text = (root / html_rec["html_path"]).read_text(encoding="utf-8")
    htp.assert_html_without_provenance(html_text)
    dp.assert_svg_without_provenance(svg_text)

    html_families = html_wf.trace_html_to_families(html_rec["html_path"])
    html_fwd = html_wf.trace(kind="issue", identifier="0037-27", direction="forward")
    html_rev = html_families["reverse"]

    report = {
        "schema": SCHEMA,
        "html_path": html_rec["html_path"],
        "html_run_id": html_rec["run_id"],
        "issue": html_rec["issue"],
        "criterion": html_rec["criterion"],
        "source_commit": source_commit,
        "tool_commit": tool_commit,
        "config_commit": config_commit,
        "families": {
            "ai": {
                "issue": "0037-27.01",
                "run_id": ai_run_id,
                "claim_id": claim_id,
                "source_versions": {k: pinset[k]["digest"] for k in pinset if pinset[k].get("digest")},
            },
            "diagram": {
                "issue": "0037-27.02",
                "run_id": diagram["run_id"],
                "source_versions": {
                    "source": diagram["source_digest"],
                    "svg": diagram["svg_digest"],
                },
            },
            "guides": {
                "issue": "0037-27.03",
                "run_id": composed["run_id"],
                "source_versions": {"identity": composed["identity"]},
            },
            "i18n": {
                "issue": "0037-27.04",
                "run_id": i18n_trace["run_id"],
                "source_versions": {"source_hash": i18n_trace["source_hash"]},
            },
            "html": {
                "issue": "0037-27",
                "run_id": html_rec["run_id"],
                "source_versions": {"tree": html_rec["tree_digest"]},
            },
        },
        "html_input_roles": html_families["families"],
        "missing_html_roles": html_families["missing_families"],
        "forward": {
            "html_issue": html_fwd,
            "diagram_issue": diagram_fwd,
        },
        "reverse": {
            "html": html_rev,
            "diagram": diagram_rev,
            "claim": {
                "found": claim_trace["run"] is not None,
                "run_id": (claim_trace["run"] or {}).get("run_id"),
                "issue": claim_trace["issue"],
            },
            "i18n": i18n_trace,
        },
    }
    dest = root / "provenance" / "html-family-trace.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report["envelope_path"] = str(dest)
    return report
