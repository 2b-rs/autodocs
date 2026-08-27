"""Hermetic tests for Task `0037-27.01` AI workflow-run and typed-claim persistence.

Adversarial completion evidence (`DEC-0038-004`):
- Pre-change baseline: `0037-19` tip `2064704457f98c66fb6f77ad3c263415864fe2ff`
- Candidate: this working tree (`0037-27.01`)
- Falsification: typed claims mint `claim:<uuid7>`, not `hypothesis:<uuid7>`
  (red on the baseline `typed_claim.new_claim`, green here).
- Adjacent: (1) legacy traces with null prompt/model stay unknown/legacy and
  do not mint a run; (2) a governed pin digest change invalidates without
  deleting the prior claim file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "2064704457f98c66fb6f77ad3c263415864fe2ff"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ps = _load("provenance_store", ROOT / "_src" / "tools" / "provenance_store.py")
awp = _load("ai_workflow_persist", ROOT / "_src" / "tools" / "ai_workflow_persist.py")
tc = _load("typed_claim", ROOT / "_src" / "tools" / "typed_claim.py")

COMMIT = "c" * 40
RUN_A = "0193a001-0001-7000-8000-00000000000a"
RUN_B = "0193a001-0002-7000-8000-00000000000b"
CLAIM_A = "claim:0193a001-0003-7000-8000-00000000000c"
STAMP = "2026-08-27T12:39:00Z"
STAMP2 = "2026-08-27T13:00:00Z"


def _sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _present(name: str, body: str, kind: str = "artifact") -> dict:
    return {"present": True, "kind": kind, "uri": f"{kind}:{name}", "digest": _sha(body)}


def _absent(name: str, reason: str = "unknown") -> dict:
    return {"name": name, "present": False, "invented": False, "reason": reason}


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


class AIWorkflowPersistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.persist = awp.AIWorkflowPersist(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, run_id=RUN_A, pins=None, **kwargs):
        return self.persist.persist_run(
            run_id=run_id,
            started_at=kwargs.get("started_at", STAMP),
            ended_at=kwargs.get("ended_at", STAMP2),
            commit=kwargs.get("commit", COMMIT),
            issue=kwargs.get("issue", "0037-27.01"),
            criterion=kwargs.get("criterion", "AC-persist"),
            campaign=kwargs.get("campaign", "camp-ai"),
            pins=pins or _pins(),
        )

    def test_claim_id_family_is_claim_not_hypothesis(self):
        claim = tc.new_claim("artifact:parent", "ai_inferred", "text")
        self.assertTrue(claim["claim_id"].startswith("claim:"))
        self.assertFalse(claim["claim_id"].startswith("hypothesis:"))
        parsed = __import__("version_id", fromlist=["parse_prefixed_id"]).parse_prefixed_id(
            claim["claim_id"]
        )
        self.assertEqual(parsed["prefix"], "claim")

    def test_ae3_claim_family_red_on_baseline_green_here(self):
        """Falsification: baseline mints hypothesis: ids; candidate mints claim:."""
        src = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"{BASELINE}:_src/tools/typed_claim.py"],
            text=True,
        )
        baseline_dir = Path(self.tmp.name) / "baseline"
        baseline_dir.mkdir()
        (baseline_dir / "typed_claim.py").write_text(src, encoding="utf-8")
        vid_src = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"{BASELINE}:_src/tools/version_id.py"],
            text=True,
        )
        (baseline_dir / "version_id.py").write_text(vid_src, encoding="utf-8")
        saved_vid = sys.modules.get("version_id")
        saved_tc = sys.modules.get("typed_claim")
        sys.path.insert(0, str(baseline_dir))
        try:
            sys.modules.pop("version_id", None)
            sys.modules.pop("typed_claim", None)
            spec = importlib.util.spec_from_file_location(
                "typed_claim_baseline", baseline_dir / "typed_claim.py"
            )
            assert spec and spec.loader
            baseline = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(baseline)
            old = baseline.new_claim("artifact:parent", "ai_inferred", "text")
        finally:
            sys.path.pop(0)
            if saved_vid is not None:
                sys.modules["version_id"] = saved_vid
            if saved_tc is not None:
                sys.modules["typed_claim"] = saved_tc
        self.assertTrue(
            old["claim_id"].startswith("hypothesis:"),
            msg=f"baseline should mint hypothesis: ids, got {old['claim_id']}",
        )
        new = tc.new_claim("artifact:parent", "ai_inferred", "text")
        self.assertTrue(new["claim_id"].startswith("claim:"))

    def test_persist_run_and_claim_trace_to_evidence(self):
        self._run()
        record = self.persist.persist_claim(
            content="Persistency stores keys in KVS.",
            parent_artifact_id="artifact:fragment-1",
            pins=_pins(),
            run_id=RUN_A,
            issue="0037-27.01",
            criterion="AC-persist",
            campaign="camp-ai",
            evidence_refs=["evidence:src-1"],
            claim_id=CLAIM_A,
            confidence=0.8,
            created=STAMP,
        )
        self.assertEqual(record["schema"], "typed-claim-persistence@v1")
        self.assertEqual(record["claim"]["claim_id"], CLAIM_A)
        self.assertTrue(self.persist.claim_path(CLAIM_A).is_file())
        traced = self.persist.trace_claim(CLAIM_A)
        self.assertEqual(traced["run"]["run_id"], RUN_A)
        self.assertIn("evidence:src-1", traced["evidence_refs"])
        self.assertEqual(traced["issue"], "issue:0037-27.01")
        input_uris = {item["uri"] for item in traced["run"]["inputs"]}
        self.assertIn("issue:0037-27.01", input_uris)
        self.assertIn("criterion:AC-persist", input_uris)
        self.assertIn("campaign:camp-ai", input_uris)
        self.assertTrue(any(u.startswith("artifact:prompt") for u in input_uris))

    def test_each_governed_pin_change_invalidates_and_keeps_prior_file(self):
        self._run()
        self.persist.persist_claim(
            content="original",
            parent_artifact_id="artifact:f",
            pins=_pins(),
            run_id=RUN_A,
            issue="0037-27.01",
            criterion="AC-persist",
            campaign="camp-ai",
            claim_id=CLAIM_A,
            created=STAMP,
        )
        prior = self.persist.claim_path(CLAIM_A).read_bytes()
        self._run(run_id=RUN_B, started_at="2026-08-27T13:10:00Z", ended_at="2026-08-27T13:11:00Z")
        for key in awp.GOVERNED_PINS:
            live = _pins()
            live[key] = _present(key, f"{key}-changed")
            result = self.persist.invalidate_for_pin_change(
                CLAIM_A,
                live,
                occurred_at="2026-08-27T13:12:00Z",
                invalidating_run_id=RUN_B,
            )
            self.assertEqual(result["status"], "invalidated")
            self.assertEqual(result["changed"], [key])
            self.assertTrue(self.persist.claim_path(CLAIM_A).is_file())
            current = self.persist.read_claim(CLAIM_A)
            self.assertTrue(current["claim"]["invalidation"]["invalidated"])
            # restore un-invalidated file to test the next pin in isolation
            self.persist.claim_path(CLAIM_A).write_bytes(prior)

    def test_supersession_preserves_old_claim_file(self):
        self._run()
        self._run(run_id=RUN_B, started_at="2026-08-27T13:10:00Z", ended_at="2026-08-27T13:11:00Z")
        old = self.persist.persist_claim(
            content="old text",
            parent_artifact_id="artifact:f",
            pins=_pins(),
            run_id=RUN_A,
            issue="0037-27.01",
            criterion="AC-persist",
            campaign="camp-ai",
            claim_id=CLAIM_A,
        )
        new = self.persist.supersede_claim(
            CLAIM_A,
            content="new text",
            run_id=RUN_B,
            pins=_pins(prompt=_present("prompt", "prompt-v2")),
        )
        self.assertNotEqual(new["claim"]["claim_id"], CLAIM_A)
        self.assertTrue(self.persist.claim_path(CLAIM_A).is_file())
        self.assertTrue(self.persist.claim_path(new["claim"]["claim_id"]).is_file())
        reloaded_old = self.persist.read_claim(CLAIM_A)
        self.assertIn(new["claim"]["claim_id"], reloaded_old["claim"]["superseded_by_claim_ids"])
        self.assertEqual(old["claim"]["content"], "old text")

    def test_legacy_trace_unknown_confidence_no_invented_run(self):
        trace = {
            "fragment": "content/ai/example/main_01.html",
            "prompt": None,
            "modell": None,
            "policy_version": None,
            "laeufe": [],
            "status": "legacy",
        }
        adapted = awp.adapt_legacy_trace(trace)
        self.assertEqual(adapted["confidence"], "legacy")
        self.assertIsNone(adapted["run_id"])
        self.assertFalse(adapted["prompt"]["present"])
        self.assertFalse(adapted["model"]["present"])
        pins = _pins(prompt=adapted["prompt"], model=adapted["model"])
        record = self.persist.persist_from_legacy_trace(
            trace,
            pins=pins,
            issue="0037-27.01",
            criterion="AC-persist",
            campaign="camp-ai",
            parent_artifact_id="artifact:legacy",
            content="legacy fragment claim",
        )
        self.assertIsNone(record["run_id"])
        self.assertEqual(record["confidence"], "legacy")
        self.assertFalse(self.persist.store.run_path(RUN_A).is_file())

    def test_legacy_adapter_rejects_invented_prompt_model_run(self):
        with self.assertRaises(awp.AIWorkflowPersistError) as ctx:
            awp.adapt_legacy_trace({"prompt": None, "invent_prompt": True})
        self.assertEqual(ctx.exception.code, "AWP-INVENTED")

    def test_refuse_minting_run_for_legacy_without_explicit_run(self):
        trace = {"prompt": None, "modell": None, "status": "legacy"}
        pins = _pins(prompt=_absent("prompt"), model=_absent("model"))
        with self.assertRaises(awp.AIWorkflowPersistError) as ctx:
            self.persist.persist_from_legacy_trace(
                trace,
                pins=pins,
                issue="0037-27.01",
                criterion="AC-persist",
                campaign="camp-ai",
                parent_artifact_id="artifact:x",
                content="x",
                commit=COMMIT,
                run_id=None,
            )
        self.assertEqual(ctx.exception.code, "AWP-INVENTED")

    def test_reject_bare_id_pins_and_run_ids(self):
        with self.assertRaises(awp.AIWorkflowPersistError) as ctx:
            awp.validate_pins(
                {
                    "record": {"present": True, "kind": "artifact", "uri": "artifact:r"},
                    "evidence": _present("e", "e"),
                    "policy": _present("p", "p"),
                    "prompt": _present("pr", "pr"),
                    "model": _present("m", "m"),
                    "config": _present("c", "c"),
                    "input": _present("i", "i"),
                }
            )
        self.assertEqual(ctx.exception.code, "AWP-BARE-ID")
        with self.assertRaises(awp.AIWorkflowPersistError) as ctx2:
            self.persist.persist_run(
                run_id="not-a-uuid",
                started_at=STAMP,
                ended_at=STAMP2,
                commit=COMMIT,
                issue="0037-27.01",
                criterion="AC-persist",
                campaign="camp-ai",
                pins=_pins(),
            )
        self.assertEqual(ctx2.exception.code, "AWP-BARE-ID")
        with self.assertRaises(awp.AIWorkflowPersistError) as ctx3:
            awp.typed_ref("issue", "issue")
        self.assertEqual(ctx3.exception.code, "AWP-BARE-ID")

    def test_reject_fabricated_run_on_claim(self):
        with self.assertRaises(awp.AIWorkflowPersistError) as ctx:
            self.persist.persist_claim(
                content="x",
                parent_artifact_id="artifact:f",
                pins=_pins(),
                run_id=RUN_A,
                issue="0037-27.01",
                criterion="AC-persist",
                campaign="camp-ai",
            )
        self.assertEqual(ctx.exception.code, "AWP-FABRICATED")

    def test_legacy_trace_with_non_uuid_run_id_is_fabricated(self):
        with self.assertRaises(awp.AIWorkflowPersistError) as ctx:
            awp.adapt_legacy_trace({"prompt": "p", "run_id": "run-1", "status": "aktuell"})
        self.assertEqual(ctx.exception.code, "AWP-FABRICATED")

    def test_one_file_per_claim_collision(self):
        self._run()
        self.persist.persist_claim(
            content="a",
            parent_artifact_id="artifact:f",
            pins=_pins(),
            run_id=RUN_A,
            issue="0037-27.01",
            criterion="AC-persist",
            campaign="camp-ai",
            claim_id=CLAIM_A,
        )
        with self.assertRaises(awp.AIWorkflowPersistError) as ctx:
            self.persist.persist_claim(
                content="b",
                parent_artifact_id="artifact:f",
                pins=_pins(),
                run_id=RUN_A,
                issue="0037-27.01",
                criterion="AC-persist",
                campaign="camp-ai",
                claim_id=CLAIM_A,
            )
        self.assertEqual(ctx.exception.code, "AWP-COLLISION")

    def test_unchanged_pins_do_not_invalidate(self):
        self._run()
        self.persist.persist_claim(
            content="a",
            parent_artifact_id="artifact:f",
            pins=_pins(),
            run_id=RUN_A,
            issue="0037-27.01",
            criterion="AC-persist",
            campaign="camp-ai",
            claim_id=CLAIM_A,
        )
        result = self.persist.invalidate_for_pin_change(CLAIM_A, _pins())
        self.assertEqual(result["status"], "unchanged")
        self.assertFalse(self.persist.read_claim(CLAIM_A)["claim"]["invalidation"]["invalidated"])

    def test_property_claim_ids_unique_and_files_match_set(self):
        """Set invariant: each persisted claim_id maps to exactly one file."""
        self._run()
        ids = []
        for i in range(8):
            rec = self.persist.persist_claim(
                content=f"c{i}",
                parent_artifact_id="artifact:f",
                pins=_pins(),
                run_id=RUN_A,
                issue="0037-27.01",
                criterion="AC-persist",
                campaign="camp-ai",
            )
            ids.append(rec["claim"]["claim_id"])
        listed = self.persist.list_claim_ids()
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), set(listed))
        self.assertEqual(len(listed), 8)

    def test_writers_bind_existing_provenance_schema(self):
        self.assertTrue((ROOT / "provenance/_schema/run-v1.schema.json").is_file())
        self.assertTrue((ROOT / "provenance/_schema/finding-v1.schema.json").is_file())
        self.assertTrue((ROOT / "provenance/_schema/provenance-event-v1.schema.json").is_file())
        self.assertTrue((ROOT / "provenance/_schema/artifact-set-v1.schema.json").is_file())
        self.assertTrue((ROOT / "provenance/_schema/typed-reference-v1.schema.json").is_file())
        self._run()
        run = json.loads(
            (self.root / "provenance" / "runs" / f"{RUN_A}.json").read_text(encoding="utf-8")
        )
        awp.validate_against_bound_schema("run", run)
        with self.assertRaises(awp.AIWorkflowPersistError) as ctx:
            awp.validate_against_bound_schema("run", {**run, "local_fork_field": 1})
        self.assertEqual(ctx.exception.code, "AWP-SCHEMA-DEVIATION")


if __name__ == "__main__":
    unittest.main()
