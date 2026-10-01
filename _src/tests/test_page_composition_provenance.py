"""Tests for user-guide/process-page composition provenance (Task `0037-27.03`).

Adversarial completion evidence (`DEC-0038-004`):
- Pre-change baseline: `0037-27.01` tip `9c1a1c86f612996cbb975ec289b9a8456d090d90`
- Candidate: this working tree (`0037-27.03`)
- Falsification: governed fragment/records change emits linked `invalidated-by` /
  `regenerated-by` work (module absent on baseline → ImportError/red; green here).
- Adjacent: (1) unpublished claim without decision/evidence is rejected;
  (2) byte-identical inputs (mtime-only) do not mark the page stale.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "page_composition_provenance.py"
STORE = ROOT / "_src" / "tools" / "provenance_store.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "page_composition"
BASELINE = "9c1a1c86f612996cbb975ec289b9a8456d090d90"
COMMIT = "c" * 40
COMMIT_TOOL = "d" * 40
COMMIT_CFG = "e" * 40
RUN_A = "0193a027-0001-7000-8000-00000000003a"
DECISION = "rev-0037-27-03-ok"
STAMP = "2026-08-27T13:04:00Z"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


pcp = _load("page_composition_provenance", TOOL)
ps = _load("provenance_store", STORE)
awp = _load("ai_workflow_persist", ROOT / "_src" / "tools" / "ai_workflow_persist.py")

FRAGMENT = FIXTURES.joinpath("fragment.json").read_bytes()
RECORDS = FIXTURES.joinpath("records.json").read_bytes()
EVIDENCE = FIXTURES.joinpath("evidence.json").read_bytes()
INSTRUCTIONS = FIXTURES.joinpath("instructions.txt").read_bytes()
POLICY = FIXTURES.joinpath("policy.json").read_bytes()
CONFIG = FIXTURES.joinpath("config.json").read_bytes()
COMPOSED = FIXTURES.joinpath("composed.json").read_bytes()


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _present(name: str, body: str, kind: str = "artifact") -> dict:
    return {"present": True, "kind": kind, "uri": f"{kind}:{name}", "digest": _sha(body)}


def _pins(**overrides) -> dict:
    value = {
        "record": _present("record", "record-v1"),
        "evidence": _present("evidence", "evidence-v1"),
        "policy": _present("policy", "policy-v1"),
        "prompt": _present("prompt", "prompt-v1"),
        "model": _present("model", "gpt-test"),
        "config": _present("config", "config-v1"),
        "input": _present("input", "input-v1"),
    }
    value.update(overrides)
    return value


class PageCompositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "_src" / "tools").mkdir(parents=True)
        (self.root / "provenance" / "_schema").mkdir(parents=True)
        shutil.copy(STORE, self.root / "_src" / "tools" / "provenance_store.py")
        for name in (
            "provenance_views.py",
            "provenance_query.py",
            "ai_workflow_persist.py",
            "typed_claim.py",
            "version_id.py",
        ):
            shutil.copy(ROOT / "_src" / "tools" / name, self.root / "_src" / "tools" / name)
        shutil.copy(
            ROOT / "provenance/_schema/provenance-graph-v1.schema.json",
            self.root / "provenance/_schema/provenance-graph-v1.schema.json",
        )
        shutil.copy(
            ROOT / "provenance/_schema/provenance-reverse-v1.schema.json",
            self.root / "provenance/_schema/provenance-reverse-v1.schema.json",
        )
        self.wf = pcp.PageCompositionWorkflow(self.root, clock=lambda: STAMP)
        self.persist = self.wf.persist

    def tearDown(self):
        self.tmp.cleanup()

    def _seed_approved_claim(self, content="The pipeline is deterministic.", claim_id=None):
        self.persist.persist_run(
            run_id=RUN_A,
            started_at=STAMP,
            ended_at=STAMP,
            commit=COMMIT,
            issue="0037-27.03",
            criterion="AC-page-composition",
            campaign="0037-27.03-pages",
            pins=_pins(),
        )
        return self.persist.persist_claim(
            content=content,
            parent_artifact_id="artifact:guide-fragment",
            pins=_pins(),
            run_id=RUN_A,
            issue="0037-27.03",
            criterion="AC-page-composition",
            campaign="0037-27.03-pages",
            evidence_refs=[f"decision:{DECISION}", "artifact:record:demo"],
            claim_type="curated_fact",
            confidence=1.0,
            claim_id=claim_id,
        )

    def _compose(self, **overrides):
        claim = overrides.pop("claim", None)
        if claim is None:
            claim = self._seed_approved_claim()
        args = dict(
            fragment_path="_src/sources/pages/guide-fragment.json",
            fragment_bytes=FRAGMENT,
            records_path="_src/spec/records/demo.json",
            records_bytes=RECORDS,
            evidence_path="provenance/_page-inputs/evidence.json",
            evidence_bytes=EVIDENCE,
            instructions_path="AGENTS.md",
            instructions_bytes=INSTRUCTIONS,
            policy_path="_src/sources/pages/policy.json",
            policy_bytes=POLICY,
            config_path="_src/sources/pages/config.json",
            config_bytes=CONFIG,
            output_path="_src/sources/pages/guide.json",
            output_bytes=COMPOSED,
            claim_ids=[claim["claim"]["claim_id"]],
            issue="0037-27.03",
            criterion="AC-page-composition",
            decision_id=DECISION,
            source_commit=COMMIT,
            tool_commit=COMMIT_TOOL,
            config_commit=COMMIT_CFG,
        )
        args.update(overrides)
        return self.wf.compose(**args)

    def test_binds_provenance_store_schema_version(self):
        self.assertEqual(pcp.ps.SCHEMA_VERSION, ps.SCHEMA_VERSION)
        rec = self._compose()
        self.assertEqual(rec["schema_version"], ps.SCHEMA_VERSION)
        run = json.loads((self.root / "provenance" / "runs" / f"{rec['run_id']}.json").read_text())
        self.assertEqual(run["schema_version"], ps.SCHEMA_VERSION)

    def test_writers_bind_existing_provenance_schema(self):
        self.assertTrue((ROOT / "provenance/_schema/run-v1.schema.json").is_file())
        rec = self._compose()
        run = json.loads(
            (self.root / "provenance" / "runs" / f"{rec['run_id']}.json").read_text()
        )
        pcp.validate_against_bound_schema("run", run)
        with self.assertRaises(pcp.PageCompositionError) as ctx:
            pcp.validate_against_bound_schema("run", {**run, "local_fork_field": 1})
        self.assertEqual(ctx.exception.code, "PCP-SCHEMA-DEVIATION")

    def test_records_envelope_links_and_hashes(self):
        rec = self._compose()
        roles = {m["role"] for m in rec["members"]}
        self.assertEqual(
            roles,
            {"fragment", "records", "evidence", "claims", "instructions", "policy", "config", "composed-page"},
        )
        self.assertTrue(rec["input_hash"].startswith("sha256:"))
        self.assertTrue(rec["output_hash"].startswith("sha256:"))
        self.assertEqual(rec["issue"], "0037-27.03")
        self.assertEqual(rec["decision_id"], f"decision:{DECISION}")
        self.assertTrue(rec["claim_traces"])

    def test_published_claims_trace_to_approved_source_and_decision(self):
        rec = self._compose()
        for trace in rec["claim_traces"]:
            self.assertIn(f"decision:{DECISION}", trace["evidence_refs"])
            self.assertTrue(trace["record_pin"]["digest"].startswith("sha256:"))
            self.assertTrue(trace["evidence_pin"]["digest"].startswith("sha256:"))
        fwd = self.wf.trace(kind="issue", identifier="0037-27.03", direction="forward")
        self.assertTrue(fwd["found"])
        paths = {f["path"] for f in fwd["files"]}
        self.assertIn("_src/sources/pages/guide.json", paths)
        self.assertIn("_src/sources/pages/guide-fragment.json", paths)
        rev = self.wf.trace(
            kind="artifact",
            identifier=f"{rec['output_path']}@{rec['output_hash']}",
            direction="reverse",
        )
        self.assertTrue(rev["found"])

    def test_rejects_unapproved_claim(self):
        self.persist.persist_run(
            run_id=RUN_A,
            started_at=STAMP,
            ended_at=STAMP,
            commit=COMMIT,
            issue="0037-27.03",
            criterion="AC-page-composition",
            campaign="0037-27.03-pages",
            pins=_pins(),
        )
        bare = self.persist.persist_claim(
            content="invented",
            parent_artifact_id="artifact:guide-fragment",
            pins=_pins(),
            run_id=RUN_A,
            issue="0037-27.03",
            criterion="AC-page-composition",
            campaign="0037-27.03-pages",
            evidence_refs=[],
            claim_type="ai_inferred",
            confidence=0.1,
        )
        with self.assertRaises(pcp.PageCompositionError) as ctx:
            self._compose(claim=bare)
        self.assertEqual(ctx.exception.code, "PCP-UNAPPROVED")

    def test_rejects_generated_html_output(self):
        claim = self._seed_approved_claim()
        with self.assertRaises(pcp.PageCompositionError) as ctx:
            self._compose(
                claim=claim,
                output_path="en/guide.html",
                output_bytes=b"<html><body>run_id=secret</body></html>",
            )
        self.assertIn(ctx.exception.code, {"PCP-HTML-INJECT", "PCP-HTML-SOURCE"})

    def test_input_change_creates_bounded_linked_regeneration(self):
        first = self._compose()
        work = self.wf.regeneration_work(
            fragment_path=first["fragment_path"],
            fragment_bytes=FRAGMENT + b"\n",
            records_bytes=RECORDS,
            evidence_bytes=EVIDENCE,
            instructions_bytes=INSTRUCTIONS,
            policy_bytes=POLICY,
            config_bytes=CONFIG,
        )
        self.assertEqual([w["output_path"] for w in work], [first["output_path"]])
        second = self._compose(
            claim={"claim": {"claim_id": first["claim_ids"][0]}},
            fragment_bytes=FRAGMENT + b"\n",
            output_bytes=COMPOSED + b" ",
            previous=first,
        )
        self.assertIsNotNone(second["invalidation"])
        self.assertEqual(second["invalidation"]["cause"], "governed composition input change")
        relations = [
            json.loads(p.read_text(encoding="utf-8"))["relation"]
            for p in (self.root / "provenance" / "events").rglob("*.json")
        ]
        self.assertIn("invalidated-by", relations)
        self.assertIn("regenerated-by", relations)
        self.assertIn("supersedes", relations)

    def test_mtime_only_does_not_mark_stale(self):
        first = self._compose()
        work = self.wf.regeneration_work(
            fragment_path=first["fragment_path"],
            fragment_bytes=FRAGMENT,
            records_bytes=RECORDS,
            evidence_bytes=EVIDENCE,
            instructions_bytes=INSTRUCTIONS,
            policy_bytes=POLICY,
            config_bytes=CONFIG,
        )
        self.assertEqual(work, [])

    def test_identity_property_over_input_roles(self):
        first = self._compose()
        rng = random.Random(27)
        executed = 0
        for role, original in (
            ("fragment_bytes", FRAGMENT),
            ("records_bytes", RECORDS),
            ("evidence_bytes", EVIDENCE),
            ("instructions_bytes", INSTRUCTIONS),
            ("policy_bytes", POLICY),
            ("config_bytes", CONFIG),
        ):
            mutated = original + bytes([rng.randint(1, 255)])
            kwargs = dict(
                fragment_path=first["fragment_path"],
                fragment_bytes=FRAGMENT,
                records_bytes=RECORDS,
                evidence_bytes=EVIDENCE,
                instructions_bytes=INSTRUCTIONS,
                policy_bytes=POLICY,
                config_bytes=CONFIG,
            )
            kwargs[role] = mutated
            work = self.wf.regeneration_work(**kwargs)
            self.assertEqual(len(work), 1, msg=role)
            executed += 1
        self.assertEqual(executed, 6)

    def test_falsification_module_absent_on_baseline(self):
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{BASELINE}:_src/tools/page_composition_provenance.py"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(listed.returncode, 0)
        self.assertTrue(TOOL.is_file())


if __name__ == "__main__":
    unittest.main()
