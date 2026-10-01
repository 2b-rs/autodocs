#!/usr/bin/env python3
"""Rebuild/migration snapshot fixtures for Task 0037-26.04."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("db_snapshot", ROOT / "_src/tools/db_snapshot.py")
SNAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SNAP)

COMMIT_A = "a" * 40
COMMIT_B = "b" * 40
COMMIT_C = "c" * 40
COMMIT_D = "d" * 40


def _bytes_of(text: str) -> bytes:
    return text.encode("utf-8")


def _base_payload(inputs, records, schema_b, config_b, tool_b, **extra):
    payload = {
        "operation": "rebuild",
        "schema_commit": COMMIT_A,
        "migration_commit": COMMIT_B,
        "tool_commit": COMMIT_C,
        "config_commit": COMMIT_D,
        "schema_digest": SNAP.sha256_bytes(schema_b),
        "config_digest": SNAP.sha256_bytes(config_b),
        "tool_digest": SNAP.sha256_bytes(tool_b),
        "inputs": inputs,
        "records": records,
        "trigger": {
            "issue": "issue:0037-26.04",
            "run": "run:018f0000-0000-7000-8000-000000000001",
            "campaign": "campaign:db-rebuild-fixture",
        },
        "environment": "development-test",
    }
    payload.update(extra)
    return payload


def _input(path: str, data: bytes) -> dict:
    return {"path": path, "digest": SNAP.sha256_bytes(data), "size_bytes": len(data)}


def _change(record_id: str, op: str, evidence_digest: str, **versions) -> dict:
    row = {
        "record_id": record_id,
        "op": op,
        "evidence": {
            "kind": "evidence",
            "uri": f"evidence:{record_id}",
            "digest": evidence_digest,
        },
        "trigger": {"kind": "issue", "uri": "issue:0037-26.04"},
    }
    row.update(versions)
    return row


class DbSnapshotTests(unittest.TestCase):
    maxDiff = None

    def test_input_config_schema_drift_is_detected(self) -> None:
        schema = _bytes_of("schema-v1")
        config = _bytes_of("config-v1")
        tool = _bytes_of("tool-v1")
        rec = _bytes_of('{"id":"RS_A","body":"one"}')
        payload = _base_payload(
            [_input("records/RS_A.json", rec)],
            [_change("RS_A", "added", SNAP.sha256_bytes(rec), to_version="v1")],
            schema,
            config,
            tool,
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = SNAP.DatabaseSnapshotStore(Path(tmp))
            with self.assertRaises(SNAP.SnapshotError) as missing:
                store.promote(
                    payload,
                    source_files={},
                    schema_bytes=schema,
                    config_bytes=config,
                    tool_bytes=tool,
                )
            self.assertEqual(missing.exception.code, "SNAP-DRIFT")
            self.assertIn("SNAP-DRIFT-INPUT", missing.exception.message)

            drifted_input = _bytes_of('{"id":"RS_A","body":"TWO"}')
            with self.assertRaises(SNAP.SnapshotError) as input_drift:
                store.promote(
                    payload,
                    source_files={"records/RS_A.json": drifted_input},
                    schema_bytes=schema,
                    config_bytes=config,
                    tool_bytes=tool,
                )
            self.assertEqual(input_drift.exception.code, "SNAP-DRIFT")

            with self.assertRaises(SNAP.SnapshotError) as schema_drift:
                store.promote(
                    payload,
                    source_files={"records/RS_A.json": rec},
                    schema_bytes=_bytes_of("schema-v2"),
                    config_bytes=config,
                    tool_bytes=tool,
                )
            self.assertIn("SNAP-DRIFT-SCHEMA", schema_drift.exception.message)

            with self.assertRaises(SNAP.SnapshotError) as config_drift:
                store.promote(
                    payload,
                    source_files={"records/RS_A.json": rec},
                    schema_bytes=schema,
                    config_bytes=_bytes_of("config-v2"),
                    tool_bytes=tool,
                )
            self.assertIn("SNAP-DRIFT-CONFIG", config_drift.exception.message)

    def test_changed_records_trace_to_evidence_and_trigger(self) -> None:
        schema, config, tool = _bytes_of("s"), _bytes_of("c"), _bytes_of("t")
        before = _bytes_of("old")
        after = _bytes_of("new")
        payload = _base_payload(
            [_input("records/RS_B.json", after)],
            [
                _change(
                    "RS_B",
                    "changed",
                    SNAP.sha256_bytes(after),
                    from_version="rel:R24#aaaa",
                    to_version="rel:R25#bbbb",
                )
            ],
            schema,
            config,
            tool,
            operation="migrate",
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = SNAP.DatabaseSnapshotStore(Path(tmp))
            envelope = store.promote(
                payload,
                source_files={"records/RS_B.json": after},
                schema_bytes=schema,
                config_bytes=config,
                tool_bytes=tool,
                record_blobs={"records/RS_B.json": after, "prior/RS_B.json": before},
            )
            traced = SNAP.reverse_trace(envelope, "RS_B")
            self.assertEqual(traced["changes"][0]["evidence"]["uri"], "evidence:RS_B")
            self.assertEqual(traced["changes"][0]["trigger"]["uri"], "issue:0037-26.04")
            self.assertEqual(traced["trigger"]["run"], payload["trigger"]["run"])
            self.assertEqual(traced["changes"][0]["from_version"], "rel:R24#aaaa")
            live = store.live_path(envelope["semantic_identity"].split(":")[1])
            self.assertEqual((live / "records/RS_B.json").read_bytes(), after)

    def test_identical_inputs_config_yield_same_semantic_identity(self) -> None:
        schema, config, tool = _bytes_of("s"), _bytes_of("c"), _bytes_of("t")
        rec = _bytes_of("body")
        payload = _base_payload(
            [_input("records/RS_C.json", rec)],
            [_change("RS_C", "added", SNAP.sha256_bytes(rec), to_version="v1")],
            schema,
            config,
            tool,
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = SNAP.DatabaseSnapshotStore(Path(tmp))
            first = store.promote(
                payload,
                source_files={"records/RS_C.json": rec},
                schema_bytes=schema,
                config_bytes=config,
                tool_bytes=tool,
            )
            second = store.promote(
                dict(payload),
                source_files={"records/RS_C.json": rec},
                schema_bytes=schema,
                config_bytes=config,
                tool_bytes=tool,
            )
            self.assertEqual(first["semantic_identity"], second["semantic_identity"])
            other = dict(payload)
            other["config_digest"] = SNAP.sha256_bytes(_bytes_of("c2"))
            with self.assertRaises(SNAP.SnapshotError):
                store.promote(
                    other,
                    source_files={"records/RS_C.json": rec},
                    schema_bytes=schema,
                    config_bytes=config,
                    tool_bytes=tool,
                )
            other_ok = dict(payload)
            other_ok["config_digest"] = SNAP.sha256_bytes(_bytes_of("c2"))
            with tempfile.TemporaryDirectory() as tmp2:
                store2 = SNAP.DatabaseSnapshotStore(Path(tmp2))
                third = store2.promote(
                    other_ok,
                    source_files={"records/RS_C.json": rec},
                    schema_bytes=schema,
                    config_bytes=_bytes_of("c2"),
                    tool_bytes=tool,
                )
            self.assertNotEqual(first["semantic_identity"], third["semantic_identity"])

    def test_partial_snapshot_is_not_promoted(self) -> None:
        schema, config, tool = _bytes_of("s"), _bytes_of("c"), _bytes_of("t")
        rec = _bytes_of("body")
        payload = _base_payload(
            [_input("records/RS_D.json", rec)],
            [_change("RS_D", "deleted", SNAP.sha256_bytes(rec), from_version="v-old")],
            schema,
            config,
            tool,
            operation="snapshot",
            rebuilds="sha256:" + "e" * 64,
        )

        def boom(partial: Path) -> None:
            self.assertTrue(partial.exists())
            self.assertTrue((partial / "envelope.json").is_file())
            raise RuntimeError("injected crash before rename")

        with tempfile.TemporaryDirectory() as tmp:
            store = SNAP.DatabaseSnapshotStore(Path(tmp))
            with self.assertRaises(RuntimeError):
                store.promote(
                    payload,
                    source_files={"records/RS_D.json": rec},
                    schema_bytes=schema,
                    config_bytes=config,
                    tool_bytes=tool,
                    inject_before_promote=boom,
                )
            self.assertEqual(list(store.list_live()), [])
            leftovers = list(store.staging.glob(".partial-*"))
            self.assertTrue(leftovers, "staging partial must remain, not live")
            envelope = store.promote(
                payload,
                source_files={"records/RS_D.json": rec},
                schema_bytes=schema,
                config_bytes=config,
                tool_bytes=tool,
            )
            self.assertEqual(envelope["operation"], "snapshot")
            self.assertEqual(envelope["rebuilds"], payload["rebuilds"])
            self.assertTrue(store.live_path(envelope["semantic_identity"].split(":")[1]).is_dir())

    def test_record_set_identity_is_order_independent_inputs_are_not(self) -> None:
        """Property: record-set membership is order-insensitive; input sequence is identity."""
        schema, config, tool = _bytes_of("s"), _bytes_of("c"), _bytes_of("t")
        a = _bytes_of("A")
        b = _bytes_of("B")
        recs = [
            _change("RS_Z", "added", SNAP.sha256_bytes(a), to_version="v1"),
            _change("RS_Y", "added", SNAP.sha256_bytes(b), to_version="v1"),
        ]
        inputs_ab = [_input("records/RS_Z.json", a), _input("records/RS_Y.json", b)]
        inputs_ba = [_input("records/RS_Y.json", b), _input("records/RS_Z.json", a)]
        identities = []
        for rec_order in (recs, list(reversed(recs))):
            payload = _base_payload(inputs_ab, rec_order, schema, config, tool)
            identities.append(SNAP.normalize_envelope(payload)["semantic_identity"])
        self.assertEqual(identities[0], identities[1])
        env_ab = SNAP.normalize_envelope(_base_payload(inputs_ab, recs, schema, config, tool))
        env_ba = SNAP.normalize_envelope(_base_payload(inputs_ba, recs, schema, config, tool))
        self.assertNotEqual(env_ab["semantic_identity"], env_ba["semantic_identity"])
        executed = 0
        for n in range(1, 6):
            blobs = {f"records/R{i}.json": _bytes_of(str(i)) for i in range(n)}
            ins = [_input(path, blobs[path]) for path in sorted(blobs)]
            chg = [
                _change(
                    f"R{i}",
                    "added",
                    SNAP.sha256_bytes(blobs[f"records/R{i}.json"]),
                    to_version="v1",
                )
                for i in range(n)
            ]
            one = SNAP.semantic_identity(
                SNAP.normalize_envelope(_base_payload(ins, chg, schema, config, tool))
            )
            two = SNAP.semantic_identity(
                SNAP.normalize_envelope(
                    _base_payload(ins, list(reversed(chg)), schema, config, tool)
                )
            )
            self.assertEqual(one, two)
            executed += 1
        self.assertEqual(executed, 5)


if __name__ == "__main__":
    unittest.main()
