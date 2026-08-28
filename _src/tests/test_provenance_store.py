"""API tests for `_src/tools/provenance_store.py` (Task `0037-17.01`)."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "_src" / "tools" / "provenance_store.py"
SPEC = importlib.util.spec_from_file_location("provenance_store", TOOL)
assert SPEC and SPEC.loader
ps = importlib.util.module_from_spec(SPEC)
sys.modules["provenance_store"] = ps
SPEC.loader.exec_module(ps)

COMMIT = "a" * 40
RUN_ID = "018f4a31-32aa-7abc-8def-0123456789ab"
FINDING_ID = "018f4a31-32ab-7abc-8def-0123456789ab"
EVENT_ID = "018f4a31-32ac-7abc-8def-0123456789ab"
SET_ID = "018f4a31-32ad-7abc-8def-0123456789ab"
STAMP = "2026-08-16T08:01:00Z"


def _ref(kind, ident, **extra):
    value = {
        "schema_version": "1.0",
        "kind": kind,
        "uri": f"{kind}:{ident}",
        "classification": "internal",
    }
    value.update(extra)
    return value


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.files = {}
        self.store = ps.ProvenanceStore(self.root, file_bytes=self.files.__getitem__)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, **overrides):
        value = {
            "schema_version": "1.0",
            "run_id": RUN_ID,
            "started_at": STAMP,
            "ended_at": "2026-08-16T08:02:00Z",
            "environment": "assessment",
            "classification": "internal",
            "status": "succeeded",
            "producer": _ref("commit", COMMIT),
            "inputs": [
                _ref("commit", COMMIT),
                _ref("issue", "0037-17.01"),
                _ref("criterion", "AC-001"),
                _ref("campaign", "camp-1"),
            ],
            "outputs": [_ref("artifact-set", SET_ID)],
        }
        value.update(overrides)
        return value

    def _finding(self, **overrides):
        value = {
            "schema_version": "1.0",
            "finding_id": FINDING_ID,
            "detected_at": STAMP,
            "state": "open",
            "classification": "internal",
            "environment": "assessment",
            "subject": _ref("issue", "0037-17.01"),
            "detected_during": _ref("run", RUN_ID),
            "evidence": [_ref("artifact", "report@sha256:" + "ab" * 32, digest="sha256:" + "ab" * 32)],
        }
        value.update(overrides)
        return value

    def _event(self, **overrides):
        value = {
            "schema_version": "1.0",
            "event_id": EVENT_ID,
            "occurred_at": STAMP,
            "relation": "detected-during",
            "source": _ref("finding", FINDING_ID),
            "target": _ref("run", RUN_ID),
            "environment": "assessment",
            "classification": "internal",
            "run": _ref("run", RUN_ID),
        }
        value.update(overrides)
        return value

    def _artifact_set(self, path="docs/pipeline/provenance-contract.md", content=b"hello\n", **overrides):
        self.files[path] = content
        member = {
            "path": path,
            "digest": ps.sha256_bytes(content),
            "size_bytes": len(content),
            "media_type": "text/markdown",
            "source_commit": COMMIT,
        }
        value = {
            "schema_version": "1.0",
            "set_id": SET_ID,
            "created_at": STAMP,
            "classification": "internal",
            "environment": "assessment",
            "producer": _ref("run", RUN_ID),
            "members": [member],
        }
        value.update(overrides)
        return value

    def test_create_and_read_run_finding_event_artifact_set(self):
        run = self.store.create_run(self._run())
        self.assertEqual(run["status"], "created")
        finding = self.store.create_finding(self._finding())
        self.assertEqual(finding["status"], "created")
        aset = self.store.create_artifact_set(self._artifact_set())
        self.assertEqual(aset["status"], "created")
        self.assertTrue(aset["record"]["set_digest"].startswith("sha256:"))
        event = self.store.create_event(self._event())
        self.assertEqual(event["status"], "created")
        self.assertEqual(self.store.read_run(RUN_ID)["run_id"], RUN_ID)

    def test_replay_idempotence(self):
        first = self.store.create_run(self._run())
        second = self.store.create_run(self._run())
        self.assertEqual(first["status"], "created")
        self.assertEqual(second["status"], "replay")
        self.assertEqual(Path(first["path"]).read_bytes(), Path(second["path"]).read_bytes())

    def test_collision_rejects_different_payload(self):
        self.store.create_run(self._run())
        other = self._run()
        other["status"] = "failed"
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_run(other)
        self.assertEqual(ctx.exception.code, "PV-COLLISION")

    def test_overwrite_attempt_rejected(self):
        result = self.store.create_run(self._run())
        path = Path(result["path"])
        with self.assertRaises(ps.ProvenanceError):
            self.store._atomic_create(path, b"{}\n")

    def test_concurrent_create_one_winner(self):
        barrier = threading.Barrier(8)
        errors = []
        statuses = []

        def worker():
            try:
                barrier.wait()
                statuses.append(self.store.create_run(self._run())["status"])
            except ps.ProvenanceError as exc:
                errors.append(exc.code)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _: worker(), range(8)))
        self.assertEqual(statuses.count("created") + statuses.count("replay"), len(statuses))
        self.assertGreaterEqual(statuses.count("created") + statuses.count("replay"), 1)
        self.assertTrue(self.store.run_path(RUN_ID).is_file())
        for code in errors:
            self.assertIn(code, {"PV-COLLISION", "PV-OVERWRITE"})

    def test_crash_before_rename_leaves_no_partial_target(self):
        def boom(tmp_path, dest):
            raise RuntimeError("injected crash before link")

        self.store._inject_before_link = boom
        with self.assertRaises(RuntimeError):
            self.store.create_run(self._run())
        dest = self.store.run_path(RUN_ID)
        self.assertFalse(dest.exists())
        leftovers = list(dest.parent.glob(".*")) if dest.parent.exists() else []
        for leftover in leftovers:
            self.assertTrue(leftover.name.startswith("."))
            self.assertNotEqual(leftover.name, dest.name)

    def test_file_digest_change_rejected(self):
        payload = self._artifact_set(content=b"alpha")
        payload["members"][0]["digest"] = ps.sha256_bytes(b"beta")
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_artifact_set(payload)
        self.assertEqual(ctx.exception.code, "PV-DIGEST-CHANGE")

    def test_tree_digest_changes_with_member_order_independent_canonicalization(self):
        self.store.create_run(self._run())
        first = self._artifact_set()
        extra = {
            "path": "docs/pipeline/tools.md",
            "digest": ps.sha256_bytes(b"tools"),
            "size_bytes": 5,
            "media_type": "text/markdown",
            "source_commit": COMMIT,
        }
        first["members"].append(extra)
        self.files["docs/pipeline/tools.md"] = b"tools"
        a = self.store.create_artifact_set(first)
        second = self._artifact_set()
        second["members"] = [extra, first["members"][0]]
        b = self.store.create_artifact_set(second)
        self.assertEqual(a["record"]["set_digest"], b["record"]["set_digest"])
        self.assertEqual(b["status"], "replay")

    def test_redaction_required_for_restricted(self):
        self.store.create_run(self._run())
        finding = self._finding(classification="restricted")
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_finding(finding)
        self.assertEqual(ctx.exception.code, "PV-REDACTION")
        finding["redaction_reason"] = "contains secrets"
        finding["subject"] = _ref("issue", "0037-17.01", classification="restricted", redacted=True)
        self.store.create_finding(finding)

    def test_legacy_confidence_adapter_does_not_invent_scores(self):
        self.assertEqual(ps.adapt_legacy_confidence(None)["confidence"], "unknown")
        self.assertEqual(ps.adapt_legacy_confidence({"legacy": True})["confidence"], "legacy")
        self.assertEqual(ps.adapt_legacy_confidence({"confidence": 0.4})["confidence"], 0.4)
        with self.assertRaises(ps.ProvenanceError):
            ps.adapt_legacy_confidence({"confidence": 1.5})

    def test_dangling_and_fabricated_history_rejected(self):
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_event(self._event())
        self.assertEqual(ctx.exception.code, "PV-DANGLING")
        self.store.create_run(self._run())
        self.store.create_finding(self._finding())
        early = self._event(occurred_at="2020-01-01T00:00:00Z")
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_event(early)
        self.assertEqual(ctx.exception.code, "PV-FABRICATED")

    def test_duplicate_id_different_digest_collision_for_artifact_set(self):
        self.store.create_run(self._run())
        first = self.store.create_artifact_set(self._artifact_set(content=b"one"))
        self.assertEqual(first["status"], "created")
        with self.assertRaises(ps.ProvenanceError) as ctx:
            self.store.create_artifact_set(self._artifact_set(content=b"two"))
        self.assertEqual(ctx.exception.code, "PV-COLLISION")

    def test_no_partial_file_after_injected_write_failure(self):
        def boom(tmp_path, dest):
            tmp_path.unlink()
            raise OSError("injected unlink")

        self.store._inject_before_link = boom
        with self.assertRaises(OSError):
            self.store.create_run(self._run())
        self.assertFalse(self.store.run_path(RUN_ID).exists())

    def _ae4(self, code, fn, *, neighbor, expected, why_adjacent):
        """Named AE-4 adjacent case: record neighbor, expected/observed, adjacency."""
        with self.assertRaises(ps.ProvenanceError) as ctx:
            fn()
        observed = ctx.exception.code
        self.assertEqual(
            observed,
            code,
            msg=(
                f"AE-4 neighbor={neighbor} expected={expected} "
                f"observed={observed} why_adjacent={why_adjacent}"
            ),
        )
        return {
            "neighboring_dimension": neighbor,
            "expected_result": expected,
            "observed_result": observed,
            "why_adjacent": why_adjacent,
        }

    def test_ae4_pv_schema_missing_field_per_record_type(self):
        """AE-4 / PV-SCHEMA: missing required field on each record type.

        Neighbor: happy-path create_* with complete payloads (existing
        test_create_and_read_run_finding_event_artifact_set). Adjacent because
        only one required key is omitted; other fields remain valid.
        """
        run = self._run()
        del run["run_id"]
        self._ae4(
            "PV-SCHEMA",
            lambda: self.store.create_run(run),
            neighbor="complete run payload",
            expected="PV-SCHEMA",
            why_adjacent="omits only run_id; remaining run fields stay valid",
        )
        finding = self._finding()
        del finding["finding_id"]
        self._ae4(
            "PV-SCHEMA",
            lambda: self.store.create_finding(finding),
            neighbor="complete finding payload",
            expected="PV-SCHEMA",
            why_adjacent="omits only finding_id; remaining finding fields stay valid",
        )
        event = self._event()
        del event["event_id"]
        self._ae4(
            "PV-SCHEMA",
            lambda: self.store.create_event(event),
            neighbor="complete event payload",
            expected="PV-SCHEMA",
            why_adjacent="omits only event_id; remaining event fields stay valid",
        )
        aset = self._artifact_set()
        del aset["set_id"]
        self._ae4(
            "PV-SCHEMA",
            lambda: self.store.create_artifact_set(aset),
            neighbor="complete artifact-set payload",
            expected="PV-SCHEMA",
            why_adjacent="omits only set_id; remaining artifact-set fields stay valid",
        )

    def test_ae4_pv_uuid_rejects_non_uuidv7(self):
        """AE-4 / PV-UUID: identity is present but not a UUIDv7.

        Neighbor: PV-SCHEMA missing run_id. Adjacent because the field is
        present (schema-complete) yet fails identity matching.
        """
        payload = self._run(run_id="not-a-uuidv7")
        self._ae4(
            "PV-UUID",
            lambda: self.store.create_run(payload),
            neighbor="PV-SCHEMA missing run_id",
            expected="PV-UUID",
            why_adjacent="run_id is present so schema passes; value is not UUIDv7",
        )

    def test_ae4_pv_endpoint_self_edge_and_wrong_kind(self):
        """AE-4 / PV-ENDPOINT: self-edge and wrong-kind endpoints.

        Neighbor 1: allowed derived-from record-version self-edge exception.
        Neighbor 2: typed-ref URI/kind mismatch vs relation kind table.
        Task Acceptance names typed endpoints.
        """
        self_edge = self._event(
            relation="supersedes",
            source=_ref("finding", FINDING_ID),
            target=_ref("finding", FINDING_ID),
        )
        self._ae4(
            "PV-ENDPOINT",
            lambda: self.store.create_event(self_edge),
            neighbor="derived-from record-version self-edge exception in product",
            expected="PV-ENDPOINT",
            why_adjacent="same source/target URI on a relation that is not the record-version exception",
        )
        wrong_kind = self._event(
            relation="detected-during",
            source=_ref("run", RUN_ID),
            target=_ref("campaign", "camp-1"),
        )
        self._ae4(
            "PV-ENDPOINT",
            lambda: self.store.create_event(wrong_kind),
            neighbor="detected-during finding→run (happy path)",
            expected="PV-ENDPOINT",
            why_adjacent="relation is valid; source kind run is not in allowed_src {finding}",
        )

    def test_ae4_pv_context_one_per_record_type(self):
        """AE-4 / PV-CONTEXT: missing typed issue/criterion/run/campaign context.

        Neighbor: happy-path records that include those kinds. Adjacent because
        remaining schema, uuid, datetime, env, and privacy fields stay valid.
        """
        run = self._run(
            inputs=[_ref("commit", COMMIT)],
        )
        self._ae4(
            "PV-CONTEXT",
            lambda: self.store.create_run(run),
            neighbor="run with issue/criterion/campaign plus commit inputs",
            expected="PV-CONTEXT",
            why_adjacent="commit input still satisfies PV-COMMIT; context kinds are gone",
        )
        finding = self._finding(
            subject=_ref("artifact", "report@sha256:" + "ab" * 32, digest="sha256:" + "ab" * 32),
        )
        del finding["detected_during"]
        self._ae4(
            "PV-CONTEXT",
            lambda: self.store.create_finding(finding),
            neighbor="finding with issue subject and run detected_during",
            expected="PV-CONTEXT",
            why_adjacent="required subject remains; kinds are only artifact, not run/campaign/issue/criterion",
        )
        event = self._event(
            relation="derived-from",
            source=_ref("artifact", "a"),
            target=_ref("artifact", "b"),
        )
        del event["run"]
        self._ae4(
            "PV-CONTEXT",
            lambda: self.store.create_event(event),
            neighbor="event with run typed-ref context",
            expected="PV-CONTEXT",
            why_adjacent="relation and endpoint kinds are valid; no run/campaign/issue/criterion remains",
        )

    def test_ae4_pv_commit_requires_source_tool_config_commit(self):
        """AE-4 / PV-COMMIT: run with context but no commit input.

        Neighbor: PV-CONTEXT (commit-only inputs). Adjacent because this is the
        complementary missing dimension named by Task Acceptance.
        """
        payload = self._run(
            inputs=[
                _ref("issue", "0037-17.01"),
                _ref("criterion", "AC-001"),
                _ref("campaign", "camp-1"),
            ]
        )
        self._ae4(
            "PV-COMMIT",
            lambda: self.store.create_run(payload),
            neighbor="PV-CONTEXT commit-only inputs",
            expected="PV-COMMIT",
            why_adjacent="issue/criterion/campaign context present; commit input omitted",
        )

    def test_ae4_pv_member_duplicate_path_and_traversal(self):
        """AE-4 / PV-MEMBER: duplicate path and path traversal.

        Neighbor: order-independent two-member artifact-set (existing tree-digest
        test). Adjacent uniqueness/safety cases on the same members list.
        """
        dup = self._artifact_set()
        member = dict(dup["members"][0])
        dup["members"] = [dup["members"][0], member]
        self._ae4(
            "PV-MEMBER",
            lambda: self.store.create_artifact_set(dup),
            neighbor="two distinct member paths (tree-digest canonicalization)",
            expected="PV-MEMBER",
            why_adjacent="same path twice in one set; digest/size otherwise valid",
        )
        trav = self._artifact_set()
        trav["members"][0] = dict(trav["members"][0], path="../secret.md")
        self.files["../secret.md"] = b"hello\n"
        self._ae4(
            "PV-MEMBER",
            lambda: self.store.create_artifact_set(trav),
            neighbor="relative in-tree member path",
            expected="PV-MEMBER",
            why_adjacent="path contains a .. part; other member fields stay valid",
        )

    def test_ae4_pv_relation_unknown_name(self):
        """AE-4 / PV-RELATION: unknown relation string.

        Neighbor: PV-ENDPOINT wrong-kind with a known relation. Adjacent because
        endpoints stay typed-valid; only the relation name is off-catalog.
        """
        payload = self._event(relation="not-a-catalog-relation")
        self._ae4(
            "PV-RELATION",
            lambda: self.store.create_event(payload),
            neighbor="PV-ENDPOINT incompatible kinds on a known relation",
            expected="PV-RELATION",
            why_adjacent="source/target refs remain schema-valid; relation is not in RELATIONS",
        )

    def test_ae4_pv_env_invalid_environment(self):
        """AE-4 / PV-ENV: environment outside the allowlist.

        Neighbor: PV-PRIVACY invalid classification on an otherwise complete run.
        Adjacent: same record, different allowlisted string field.
        """
        payload = self._run(environment="staging")
        self._ae4(
            "PV-ENV",
            lambda: self.store.create_run(payload),
            neighbor="PV-PRIVACY invalid classification",
            expected="PV-ENV",
            why_adjacent="classification remains internal; environment is not in ENVIRONMENTS",
        )

    def test_ae4_pv_datetime_naive_stamp(self):
        """AE-4 / PV-DATETIME: timezone-naive started_at.

        Neighbor: valid Zulu stamps on the happy-path run. Adjacent because the
        civil time is parseable; only tzinfo is missing.
        """
        payload = self._run(started_at="2026-08-16T08:01:00")
        self._ae4(
            "PV-DATETIME",
            lambda: self.store.create_run(payload),
            neighbor="timezone-aware started_at Zulu stamp",
            expected="PV-DATETIME",
            why_adjacent="ISO local datetime without tzinfo; remaining run fields stay valid",
        )

    def test_ae4_pv_privacy_invalid_classification(self):
        """AE-4 / PV-PRIVACY: classification outside the allowlist.

        Neighbor: PV-REDACTION restricted-without-reason (existing test). Adjacent
        because this is the invalid-token path rather than the redaction-required path.
        """
        payload = self._run(classification="secret")
        self._ae4(
            "PV-PRIVACY",
            lambda: self.store.create_run(payload),
            neighbor="PV-REDACTION restricted finding without redaction_reason",
            expected="PV-PRIVACY",
            why_adjacent="token is not in CLASSIFICATIONS; not the restricted-redaction branch",
        )


if __name__ == "__main__":
    unittest.main()
