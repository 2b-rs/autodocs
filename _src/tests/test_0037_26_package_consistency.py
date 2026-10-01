"""Parent-package consistency for Task 0037-26 (no sibling product rewrite).

DoD: the six Subtask families pass cross-producer reverse-trace and
backward-disposition checks. AC gaps (inventory producers that do not yet
bind the shared 0037-17/19 schemas) are collected as findings.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
sys.path.insert(0, str(TOOLS))

import campaign_manifest as cm  # noqa: E402
import db_snapshot as snap  # noqa: E402
import evidence_version_provenance as evp  # noqa: E402
import provenance_query as pq  # noqa: E402
import provenance_store as ps  # noqa: E402

sep_spec = importlib.util.spec_from_file_location(
    "scrape_extraction_provenance", TOOLS / "scrape_extraction_provenance.py"
)
sep = importlib.util.module_from_spec(sep_spec)
sep_spec.loader.exec_module(sep)

cp_spec = importlib.util.spec_from_file_location(
    "curation_provenance", TOOLS / "curation_provenance.py"
)
cp = importlib.util.module_from_spec(cp_spec)
sys.modules["curation_provenance"] = cp
cp_spec.loader.exec_module(cp)

bre_spec = importlib.util.spec_from_file_location(
    "build_report_envelope", TOOLS / "build_report_envelope.py"
)
bre = importlib.util.module_from_spec(bre_spec)
bre_spec.loader.exec_module(bre)

COMMIT = "c" * 40
ISSUE = "0037-26"
CRITERION = "AC-package-cross-producer"
CAMPAIGN = "package-0037-26"
RUN = "018f4a31-2600-7abc-8def-0123456789aa"

# Exact 0037-37 / chore inventory producers owned by this package's six families.
INVENTORY = (
    ("0037-26.01", "_src/tools/spec_scrape.py"),
    ("0037-26.01", "_src/tools/extraction_report.py"),
    ("0037-26.01", "_src/tools/score_scrape.py"),
    ("0037-26.01", "_src/tools/scrape_extraction_provenance.py"),
    ("0037-26.02", "_src/tools/campaign_manifest.py"),
    ("0037-26.03", "_src/tools/evidence_version_provenance.py"),
    ("0037-26.03", "_src/tools/evidence_snippet.py"),
    ("0037-26.03", "_src/tools/version_store.py"),
    ("0037-26.04", "_src/tools/db_snapshot.py"),
    ("0037-26.05", "_src/tools/curation_provenance.py"),
    ("0037-26.06", "_src/tools/build_report.py"),
    ("0037-26.06", "_src/tools/build_report_envelope.py"),
)

SHARED_SCHEMA_IMPORTS = ("provenance_store", "provenance_query")
REQUIRED_ENVELOPE_TOKENS = (
    "issue",
    "criterion",
    "run",
    "campaign",
    "artifact",
)


def _copy_query_support(dest: Path) -> None:
    (dest / "_src" / "tools").mkdir(parents=True, exist_ok=True)
    (dest / "provenance" / "_schema").mkdir(parents=True, exist_ok=True)
    for name in ("provenance_store.py", "provenance_views.py", "provenance_query.py"):
        shutil.copy(TOOLS / name, dest / "_src" / "tools" / name)
    for schema in (
        "provenance-graph-v1.schema.json",
        "provenance-reverse-v1.schema.json",
        "typed-reference-v1.schema.json",
        "run-v1.schema.json",
        "finding-v1.schema.json",
        "artifact-set-v1.schema.json",
        "provenance-event-v1.schema.json",
    ):
        src = ROOT / "provenance" / "_schema" / schema
        if src.is_file():
            shutil.copy(src, dest / "provenance" / "_schema" / schema)


def inventory_findings() -> list[dict]:
    findings = []
    for family, rel in INVENTORY:
        path = ROOT / rel
        if not path.is_file():
            findings.append(
                {
                    "code": "INV-MISSING-FILE",
                    "family": family,
                    "path": rel,
                    "detail": "inventory path absent after child merge",
                }
            )
            continue
        text = path.read_text(encoding="utf-8")
        missing_tokens = [tok for tok in REQUIRED_ENVELOPE_TOKENS if tok not in text]
        uses_store = "provenance_store" in text or "import provenance_store" in text
        uses_query = "provenance_query" in text or "query_trace" in text
        if missing_tokens:
            findings.append(
                {
                    "code": "INV-ENVELOPE-TOKENS",
                    "family": family,
                    "path": rel,
                    "detail": "source does not mention " + ",".join(missing_tokens),
                    "owner": family,
                }
            )
        if not uses_store or not uses_query:
            findings.append(
                {
                    "code": "INV-SHARED-SCHEMA",
                    "family": family,
                    "path": rel,
                    "detail": "does not import provenance_store and/or provenance_query",
                    "owner": family,
                }
            )
        local_schema = path.parent / "_schema"
        if local_schema.is_dir():
            findings.append(
                {
                    "code": "INV-LOCAL-SCHEMA-FORK",
                    "family": family,
                    "path": rel,
                    "detail": "local _schema directory next to adapter",
                    "owner": family,
                }
            )
    return findings


class PackageConsistencyTests(unittest.TestCase):
    def test_inventory_producers_exist_and_schema_gaps_are_findings_not_forks(self):
        findings = inventory_findings()
        missing = [f for f in findings if f["code"] == "INV-MISSING-FILE"]
        forks = [f for f in findings if f["code"] == "INV-LOCAL-SCHEMA-FORK"]
        self.assertEqual(missing, [])
        self.assertEqual(forks, [])
        # Shared-schema / token gaps stay with original child owners.
        schema_gaps = [f for f in findings if f["code"] == "INV-SHARED-SCHEMA"]
        token_gaps = [f for f in findings if f["code"] == "INV-ENVELOPE-TOKENS"]
        self.assertTrue(
            any(g["path"].endswith("campaign_manifest.py") for g in schema_gaps),
            msg="expected campaign_manifest shared-schema finding",
        )
        self.assertTrue(
            any(g["path"].endswith("db_snapshot.py") for g in schema_gaps),
            msg="expected db_snapshot shared-schema finding",
        )
        bound = ROOT / "provenance" / "_schema"
        for name in (
            "run-v1.schema.json",
            "finding-v1.schema.json",
            "artifact-set-v1.schema.json",
            "typed-reference-v1.schema.json",
        ):
            self.assertTrue((bound / name).is_file(), name)

    def test_cross_producer_reverse_trace_and_backward_disposition(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _copy_query_support(root)
        pdf = b"%PDF-1.4 package cross-producer fixture\n"
        files = {"fixtures/source.pdf": pdf}

        scrape = sep.persist_scrape_extraction_report(
            store_root=root,
            producer="spec_scrape.phase_crosscheck",
            source_commit=COMMIT,
            tool_commit=COMMIT,
            config_commit=COMMIT,
            input_files=files,
            report_path="output/reports/spec-scrape-crosscheck.json",
            report_bytes=b'{"backends":["pypdf"],"backend_deviations":[]}',
            issue=ISSUE,
            criterion=CRITERION,
            campaign=CAMPAIGN,
            trigger_kind="issue",
            trigger_id=ISSUE,
            cause="package-cross-producer",
            status="succeeded",
            run_id=RUN,
            started_at="2026-08-27T12:00:00Z",
            ended_at="2026-08-27T12:00:01Z",
        )
        rev_scrape = sep.trace_report_to_source(
            root,
            report_path="output/reports/spec-scrape-crosscheck.json",
            report_digest=scrape["report_digest"],
        )
        self.assertTrue(rev_scrape.get("found"), msg=json.dumps(rev_scrape)[:1500])
        self.assertIn(f"issue:{ISSUE}", rev_scrape.get("issues") or [])

        version = evp.attach_record_version_provenance(
            version_id="AUTOSAR/AP/record/RS_PER_00010@rel:R25-11#pkg",
            content="persistency label",
            request={
                "store_root": root / "evidence",
                "environment": "development-test",
                "issue": ISSUE,
                "criterion": CRITERION,
                "campaign": CAMPAIGN,
                "tool_commit": COMMIT,
                "config_commit": COMMIT,
                "source_commit": COMMIT,
                "run_id": "018f4a31-2603-7abc-8def-0123456789aa",
                "input_members": [
                    {
                        "path": "fixtures/source.pdf",
                        "bytes": pdf,
                        "media_type": "application/pdf",
                    }
                ],
            },
        )
        self.assertEqual(version["issue"], ISSUE)
        self.assertEqual(version["run_id"], "018f4a31-2603-7abc-8def-0123456789aa")

        session = cp.CurationProvenanceSession(root / "curation")
        ctx = session.seed_context(
            run_id="018f4a31-2605-7abc-8def-0123456789aa",
            finding_id="018f4a31-32ab-7abc-8def-0123456789ab",
            issue=ISSUE,
            criterion=CRITERION,
            campaign=CAMPAIGN,
        )
        opened = session.apply_transition(
            "RS_PER_00010",
            "open",
            actor="curator-pkg",
            authority_role="curator",
            requester="github-user",
            context=ctx,
            finding_digest=ctx["report_digest"],
            source_version=ctx["version"]["uri"],
        )
        links = session.reverse_links("RS_PER_00010")
        self.assertEqual(links["issue"], f"issue:{ISSUE}")
        self.assertEqual(links["run"], "run:018f4a31-2605-7abc-8def-0123456789aa")
        self.assertEqual(links["campaign"], f"campaign:{CAMPAIGN}")
        self.assertEqual(opened["status"], "open")

        rec = b'{"id":"RS_PER_00010"}'
        payload = {
            "operation": "rebuild",
            "schema_commit": COMMIT,
            "migration_commit": COMMIT,
            "tool_commit": COMMIT,
            "config_commit": COMMIT,
            "schema_digest": snap.sha256_bytes(b"schema"),
            "config_digest": snap.sha256_bytes(b"config"),
            "tool_digest": snap.sha256_bytes(b"tool"),
            "inputs": [
                {
                    "path": "records/RS_PER_00010.json",
                    "digest": snap.sha256_bytes(rec),
                    "size_bytes": len(rec),
                }
            ],
            "records": [
                {
                    "record_id": "RS_PER_00010",
                    "op": "added",
                    "evidence": {
                        "kind": "evidence",
                        "uri": "evidence:RS_PER_00010",
                        "digest": snap.sha256_bytes(rec),
                    },
                    "trigger": {"kind": "issue", "uri": f"issue:{ISSUE}"},
                    "to_version": "v1",
                }
            ],
            "trigger": {
                "issue": f"issue:{ISSUE}",
                "run": f"run:{RUN}",
                "campaign": f"campaign:{CAMPAIGN}",
            },
            "environment": "development-test",
        }
        store = snap.DatabaseSnapshotStore(root / "db")
        envelope = store.promote(
            payload,
            source_files={"records/RS_PER_00010.json": rec},
            schema_bytes=b"schema",
            config_bytes=b"config",
            tool_bytes=b"tool",
            record_blobs={"records/RS_PER_00010.json": rec},
        )
        traced = snap.reverse_trace(envelope, "RS_PER_00010")
        self.assertEqual(traced["trigger"]["issue"], f"issue:{ISSUE}")
        self.assertEqual(traced["trigger"]["run"], f"run:{RUN}")

        files_map = {
            "src/generate.txt": b"src/generate.txt",
            "out/generate.txt": b"out/generate.txt",
        }
        members_in = bre.members_for_paths(["src/generate.txt"], COMMIT)
        members_out = bre.members_for_paths(["out/generate.txt"], COMMIT)
        in_set = bre.artifact_set_from_members(members_in)
        out_set = bre.artifact_set_from_members(members_out)
        pstore = ps.ProvenanceStore(root / "build", file_bytes=files_map.__getitem__)
        bre.persist_combined_provenance(
            pstore,
            run_id="018f4a31-2606-7abc-8def-0123456789aa",
            started_at="2026-08-27T12:00:00Z",
            ended_at="2026-08-27T12:01:00Z",
            success=True,
            trigger={"kind": "issue", "id": ISSUE},
            input_set=in_set,
            output_set=out_set,
            findings=[],
            set_id_input="018f4a31-2606-7abc-8def-0123456789a1",
            set_id_output="018f4a31-2606-7abc-8def-0123456789a2",
            event_ids={
                "triggered": "018f4a31-2606-7abc-8def-0123456789e1",
                "produced": "018f4a31-2606-7abc-8def-0123456789e2",
                "derived": "018f4a31-2606-7abc-8def-0123456789e3",
            },
        )
        _copy_query_support(root / "build")
        rev_build = pq.query_trace(
            root / "build",
            kind="run",
            identifier="018f4a31-2606-7abc-8def-0123456789aa",
            direction="reverse",
        )
        self.assertTrue(rev_build.get("found"), msg=json.dumps(rev_build)[:1500])
        self.assertIn(f"issue:{ISSUE}", rev_build.get("issues") or [])

        # Backward disposition: campaign listing/mtime identity and evidence unknown/legacy.
        adapted = cm.adapt_manifest(
            {
                "schema": "campaign-manifest@v1",
                "campaign": CAMPAIGN,
                "corpus_hash": "deadbeef",
                "trigger": "legacy listing",
            }
        )
        self.assertEqual(adapted["disposition"]["kind"], "legacy")
        self.assertNotEqual(adapted["disposition"]["kind"], "current")
        legacy_ev = evp.legacy_disposition({"note": "pre-envelope line"})
        self.assertFalse(legacy_ev.get("backfill"))
        self.assertIn(legacy_ev.get("confidence") or "unknown", ("unknown", "legacy"))
        self.assertIsNone(legacy_ev.get("envelope"))

        # Adjacent: current campaign snapshot is not rewritten as legacy.
        orig_c = cm.CAMPAIGNS_DIR
        orig_r = cm.RECORDS_DIR
        orig_s = cm.SPEC_ROOT
        try:
            base = root / "campaigns-pkg"
            cm.SPEC_ROOT = base
            cm.CAMPAIGNS_DIR = base / "campaigns"
            cm.RECORDS_DIR = base / "records"
            cm.RECORDS_DIR.mkdir(parents=True)
            (cm.RECORDS_DIR / "a.json").write_text("{}", encoding="utf-8")
            path = cm.write_manifest(
                "pkg-current",
                trigger="package",
                trigger_issue=ISSUE,
                trigger_criterion=CRITERION,
                runs=[f"run:{RUN}"],
                source_commit=COMMIT,
                config_commit=COMMIT,
                overwrite=True,
            )
            current = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(current["disposition"]["kind"], "current")
            self.assertEqual(current["trigger_issue"], ISSUE)
            self.assertIn("content_set_digest", current)
        finally:
            cm.SPEC_ROOT = orig_s
            cm.CAMPAIGNS_DIR = orig_c
            cm.RECORDS_DIR = orig_r


if __name__ == "__main__":
    unittest.main()
