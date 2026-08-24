import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "legacy_task_editor"
SPEC = importlib.util.spec_from_file_location("legacy_task_editor", TOOLS / "legacy_task_editor.py")
assert SPEC is not None and SPEC.loader is not None
editor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = editor
SPEC.loader.exec_module(editor)

FIXTURE_DATA = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))
DOCUMENTS = FIXTURE_DATA["documents"]
A = "a" * 40
B = "b" * 40
C = "c" * 40
TS = "2026-08-17T08:00:00Z"


def source_bytes(name):
    return {path: text.encode("utf-8") for path, text in DOCUMENTS[name].items()}


def operation_for(
    sources,
    kind,
    *,
    feature_id="1000",
    task_id="1000-01",
    marker="p",
    payload=None,
    claim_path=None,
    actor_agent="alpha",
    actor_request="req-alpha-001",
    operation_id=None,
):
    backlog_path = "TODO.md"
    document = editor.parse_backlog(backlog_path, sources[backlog_path])
    feature, task = editor._unique_task(document, feature_id, task_id)
    feature_bytes = document.text[feature.span.start:feature.span.end].encode("utf-8")
    task_bytes = document.text[task.span.start:task.span.end].encode("utf-8")
    operation_id = operation_id or f"fixture-{kind}-001"
    data = {
        "schema": editor.OPERATION_SCHEMA,
        "operation_id": operation_id,
        "kind": kind,
        "recorded_at": TS,
        "subject": {"feature_id": feature_id, "task_id": task_id},
        "actor": {
            "request_id": actor_request,
            "owner_token": f"agent:{actor_agent}:{task_id}:{actor_request}",
        },
        "backlog": {
            "path": backlog_path,
            "expected_document_sha256": editor._sha256(sources[backlog_path]),
            "expected_feature_sha256": editor._sha256(feature_bytes),
            "expected_task_sha256": editor._sha256(task_bytes),
            "expected_marker": marker,
        },
        "payload": payload or {},
    }
    if claim_path is not None:
        claim = editor.parse_claim(claim_path, sources[claim_path])
        data["claim"] = {
            "path": claim_path,
            "expected_document_sha256": editor._sha256(sources[claim_path]),
            "expected_task_id": claim.task_id,
            "expected_request_id": claim.request_id,
            "expected_owner_token": claim.owner_token,
            "expected_state": claim.state,
        }
    raw = (json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    return editor.load_operation(raw)


def planned_change(plan, path):
    return next(change for change in plan.changes if change.path == path)


class StructuralParserTests(unittest.TestCase):
    def test_fixture_manifest_is_complete(self):
        manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "legacy-task-editor-fixture-manifest@v1")
        self.assertEqual(FIXTURE_DATA["schema"], "legacy-task-editor-fixtures@v1")
        self.assertEqual(
            manifest["historical_sources"]["corruption-chain"]["commits"],
            [
                "9e033f327762e26ba8730ae8ac3e09b388017295",
                "9c4795bb8cd5220b33b337bd0e7d236e91a4b04e",
                "cd6d8db17341cf2616b016c7a0b80f5912e96673",
            ],
        )
        self.assertEqual(
            set(manifest["historical_sources"]["stale-amend-ref"]["commits"]),
            {
                "723b485d675ea57a104f05dd10ed84af75548b05",
                "a1cbbbdc3e45fb8a62d52ec53816a4af74105ec6",
            },
        )
        self.assertIn(
            "run-2026-08-16_19-47-16-n0361.sh",
            manifest["historical_sources"]["wrong-claim-deletion"]["evidence"][0],
        )

    def test_exact_task_boundaries_stop_before_neighbor_and_campaign(self):
        for name, task_id in (("active", "1000-01"), ("corruption-chain", "0037-03.01")):
            with self.subTest(name=name):
                raw = source_bytes(name)["TODO.md"]
                document = editor.parse_backlog("TODO.md", raw)
                task = next(item for item in document.tasks if item.id == task_id)
                block = document.text[task.span.start:task.span.end]
                self.assertNotIn("Neighbor Task", block)
                self.assertNotIn("0037-03.02", block)
                self.assertNotIn("Campaign B", block)

    def test_fenced_duplicate_is_ignored_but_structural_duplicate_rejects(self):
        fenced = editor.parse_backlog("TODO.md", source_bytes("fenced-decoy")["TODO.md"])
        self.assertEqual([task.id for task in fenced.tasks].count("1000-01"), 1)
        duplicate = source_bytes("duplicate")
        document = editor.parse_backlog("TODO.md", duplicate["TODO.md"])
        first = next(task for task in document.tasks if task.id == "1000-01")
        feature = document.features[0]
        data = {
            "schema": editor.OPERATION_SCHEMA,
            "operation_id": "fixture-duplicate-001",
            "kind": "append-correction",
            "recorded_at": TS,
            "subject": {"feature_id": "1000", "task_id": "1000-01"},
            "actor": {"request_id": "req-alpha-001", "owner_token": "agent:alpha:1000-01:req-alpha-001"},
            "backlog": {
                "path": "TODO.md",
                "expected_document_sha256": editor._sha256(duplicate["TODO.md"]),
                "expected_feature_sha256": editor._sha256(document.text[feature.span.start:feature.span.end].encode()),
                "expected_task_sha256": editor._sha256(document.text[first.span.start:first.span.end].encode()),
                "expected_marker": "p",
            },
            "payload": {"target": "backlog", "correction_id": "correction-001", "message": "Do not select a duplicate."},
        }
        operation = editor.load_operation((json.dumps(data) + "\n").encode())
        with self.assertRaisesRegex(editor.EditorError, "expected one Task") as raised:
            editor.plan_operation(operation, duplicate)
        self.assertEqual(raised.exception.rule, "LTE-TASK-NOT-UNIQUE")

    def test_neighbor_dod_is_not_captured(self):
        sources = source_bytes("neighbor")
        operation = operation_for(
            sources,
            "closure",
            payload={"substantive_ref": B, "summary": "Must reject."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        with self.assertRaises(editor.EditorError) as raised:
            editor.plan_operation(operation, sources)
        self.assertEqual(raised.exception.rule, "LTE-SECTION-NOT-UNIQUE")
        self.assertEqual(sources, source_bytes("neighbor"))

    def test_fenced_definition_and_hidden_ref_are_not_authoritative(self):
        sources = source_bytes("active")
        sources["TODO.md"] = sources["TODO.md"].replace(
            b"  - **Definition of Done:** Validate the exact result.\n",
            b"  ```text\n  - **Definition of Done:** fenced decoy\n  ```\n",
        )
        operation = operation_for(
            sources,
            "closure",
            payload={"substantive_ref": B, "summary": "Must reject decoy."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        with self.assertRaises(editor.EditorError) as raised:
            editor.plan_operation(operation, sources)
        self.assertEqual(raised.exception.rule, "LTE-SECTION-NOT-UNIQUE")

        hidden = source_bytes("stale-ref")
        hidden["TODO.md"] = hidden["TODO.md"].replace(
            f"REF: {A}".encode(),
            f"<!-- REF: {A} -->".encode(),
            1,
        )
        insertion = operation_for(
            hidden,
            "ref-injection",
            marker="x",
            payload={"new_ref": B, "reason": "Hidden REF has no authority."},
            actor_request="req-hidden-001",
        )
        after = editor.plan_operation(insertion, hidden).changes[0].after.decode()
        self.assertIn(f"<!-- REF: {A} --> REF: {B}", after)

    def test_mixed_fences_and_comment_markers_do_not_expose_decoys(self):
        raw = """# TODO

## Feature: 1000 — Mixed fixture

- [p] **1000-01** Real Task.
  - **Definition of Done:** Real section.

```text
<!-- literal comment opener
~~~ mismatched fence
```not-a-close
- [p] **1000-01** Decoy.
    ```
- [ ] **1000-03** Over-indented fence decoy.
-->
```

- [ ] **1000-02** Real neighbor.
""".encode("utf-8")
        document = editor.parse_backlog("TODO.md", raw)
        self.assertEqual([task.id for task in document.tasks], ["1000-01", "1000-02"])

        claim = b"""# Claim

## Claim identity

<!--
task_id: 9999-99
owner_token: agent:fake:9999-99:req-fake-001
-->
```text
request_id: req-fenced-001
```
task_id: 1000-01
request_id: req-alpha-001
owner_token: agent:alpha:1000-01:req-alpha-001
base_commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
capability_class: sandboxed/grunt
state: [p]
"""
        parsed = editor.parse_claim("TODO-alpha-1000-01-req-alpha-001.md", claim)
        self.assertEqual(parsed.task_id, "1000-01")
        self.assertEqual(parsed.request_id, "req-alpha-001")

    def test_claim_without_task_field_infers_task_from_owner_token(self):
        claim = source_bytes("active")["TODO-alpha-1000-01-req-alpha-001.md"].replace(
            b"task_id: 1000-01\n",
            b"",
        )
        parsed = editor.parse_claim("TODO-alpha-1000-01-req-alpha-001.md", claim)
        self.assertEqual(parsed.task_id, "1000-01")
        sources = source_bytes("open")
        sources["TODO-alpha-1000-01-req-alpha-001.md"] = claim
        operation = operation_for(
            sources,
            "pickup",
            marker=" ",
            actor_agent="beta",
            actor_request="req-beta-001",
            payload={
                "claim_path": "TODO-beta-1000-01-req-beta-001.md",
                "base_commit": "pending-discovery",
                "capability_class": "sandboxed/grunt",
                "scope": ["src/a.py"],
                "next_step": "Discover.",
            },
        )
        with self.assertRaises(editor.EditorError) as raised:
            editor.plan_operation(operation, sources)
        self.assertEqual(raised.exception.rule, "LTE-CLAIM-CONFLICT")

    def test_claim_variants_parse_without_reformatting(self):
        canonical = source_bytes("active")["TODO-alpha-1000-01-req-alpha-001.md"]
        legacy = canonical.replace(b"owner_token: agent:alpha", b"- `owner_token`: agent:alpha")
        hybrid = canonical.replace(b"state: [p]", b"- state: [p]")
        for raw in (canonical, legacy, hybrid):
            with self.subTest(raw=raw[-30:]):
                claim = editor.parse_claim("claim.md", raw)
                self.assertEqual(claim.task_id, "1000-01")
                self.assertEqual(claim.owner_token, "agent:alpha:1000-01:req-alpha-001")
                self.assertEqual(claim.raw, raw)


class OperationValidationTests(unittest.TestCase):
    def test_duplicate_json_and_unknown_fields_reject(self):
        duplicate = b'{"schema":"x","schema":"y"}\n'
        with self.assertRaises(editor.EditorError) as raised:
            editor.load_operation(duplicate)
        self.assertEqual(raised.exception.rule, "LTE-OP-JSON")
        sources = source_bytes("open")
        operation = operation_for(
            sources,
            "pickup",
            marker=" ",
            actor_agent="beta",
            actor_request="req-beta-001",
            payload={
                "claim_path": "TODO-beta-1000-01-req-beta-001.md",
                "base_commit": A,
                "capability_class": "privileged",
                "scope": ["src/a.py"],
                "next_step": "Implement.",
            },
        )
        value = dict(operation.data)
        value["unknown"] = True
        with self.assertRaises(editor.EditorError) as raised:
            editor.load_operation((json.dumps(value) + "\n").encode())
        self.assertEqual(raised.exception.rule, "LTE-OP-UNKNOWN-FIELD")

    def test_operation_actor_must_be_exact_claim_owner(self):
        sources = source_bytes("active")
        operation = operation_for(
            sources,
            "closure",
            payload={"substantive_ref": B, "summary": "Done."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        value = dict(operation.data)
        value["actor"] = {
            "request_id": "req-foreign-001",
            "owner_token": "agent:foreign:1000-01:req-foreign-001",
        }
        with self.assertRaises(editor.EditorError) as raised:
            editor.load_operation((json.dumps(value) + "\n").encode())
        self.assertEqual(raised.exception.rule, "LTE-CLAIM-IDENTITY")

    def test_foreign_existing_claim_cannot_be_finalized_by_other_actor(self):
        sources = source_bytes("active")
        alpha = sources.pop("TODO-alpha-1000-01-req-alpha-001.md")
        beta = (
            alpha.replace(b"Alpha claim", b"Beta claim")
            .replace(b"req-alpha-001", b"req-beta-001")
            .replace(b"agent:alpha", b"agent:beta")
        )
        beta_path = "TODO-beta-1000-01-req-beta-001.md"
        sources[beta_path] = beta
        sources["TODO.md"] = sources["TODO.md"].replace(
            b"TODO-alpha-1000-01-req-alpha-001.md",
            beta_path.encode(),
        ).replace(
            b"agent:alpha:1000-01:req-alpha-001",
            b"agent:beta:1000-01:req-beta-001",
        )
        with self.assertRaises(editor.EditorError) as raised:
            operation_for(
                sources,
                "claim-finalization",
                payload={"archive_path": "logs/claims/beta.md"},
                claim_path=beta_path,
                actor_agent="alpha",
                actor_request="req-alpha-001",
            )
        self.assertEqual(raised.exception.rule, "LTE-CLAIM-IDENTITY")

    def test_claim_archive_and_destination_roles_must_be_disjoint(self):
        sources = source_bytes("active")
        for kind, payload in (
            (
                "claim-finalization",
                {"archive_path": "TODO.md"},
            ),
            (
                "claim-handoff",
                {
                    "destination_claim_path": "TODO-beta-1000-01-req-beta-001.md",
                    "new_request_id": "req-beta-001",
                    "new_owner_token": "agent:beta:1000-01:req-beta-001",
                    "new_capability_class": "privileged",
                    "new_base_commit": B,
                    "scope": ["src/a.py"],
                    "next_step": "Continue.",
                    "authorization": "explicit-owner-release-or-authorized-decision",
                    "archive_path": "TODO-beta-1000-01-req-beta-001.md",
                },
            ),
        ):
            with self.subTest(kind=kind):
                with self.assertRaises(editor.EditorError) as raised:
                    operation_for(
                        sources,
                        kind,
                        payload=payload,
                        claim_path="TODO-alpha-1000-01-req-alpha-001.md",
                    )
                self.assertEqual(raised.exception.rule, "LTE-PATH-UNSAFE")

    def test_pickup_accepts_pending_discovery_base(self):
        sources = source_bytes("open")
        operation = operation_for(
            sources,
            "pickup",
            marker=" ",
            actor_agent="beta",
            actor_request="req-beta-001",
            payload={
                "claim_path": "TODO-beta-1000-01-req-beta-001.md",
                "base_commit": "pending-discovery",
                "capability_class": "sandboxed/grunt",
                "scope": ["src/a.py"],
                "next_step": "Publish fixed read-only discovery.",
            },
        )
        plan = editor.plan_operation(operation, sources)
        claim = planned_change(plan, "TODO-beta-1000-01-req-beta-001.md").after.decode()
        self.assertIn("base_commit: pending-discovery", claim)

    def test_unsafe_paths_narratives_and_refs_reject(self):
        sources = source_bytes("open")
        bad_payloads = [
            {
                "claim_path": "../claim.md",
                "base_commit": A,
                "capability_class": "privileged",
                "scope": ["src/a.py"],
                "next_step": "Implement.",
            },
            {
                "claim_path": "TODO-beta-1000-01-req-beta-001.md",
                "base_commit": "short",
                "capability_class": "privileged",
                "scope": ["src/*.py"],
                "next_step": "Implement.\nEscape",
            },
        ]
        for payload in bad_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(editor.EditorError):
                    operation_for(
                        sources,
                        "pickup",
                        marker=" ",
                        actor_agent="beta",
                        actor_request="req-beta-001",
                        payload=payload,
                    )
        for unsafe in ("hide <!-- rest", "unicode\u0085separator", "unicode\u2028separator", "```fence"):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(editor.EditorError) as raised:
                    operation_for(
                        source_bytes("active"),
                        "progress",
                        payload={"target": "backlog", "message": unsafe},
                    )
                self.assertEqual(raised.exception.rule, "LTE-OP-UNSAFE-VALUE")


class CheckpointAuthorityTests(unittest.TestCase):
    """Task 0038-23: the digest-bound editor must refuse any change to an
    ``- **Integration review: ...`` attribute bullet unless the operation
    carries an explicit ``architect_authority`` assertion, and the resulting
    bullet must itself be a well-formed, (architect)-tagged declaration.
    """

    WELL_FORMED_MANDATORY = "  - **Integration review:** mandatory. **Rationale (architect):** fixture checkpoint."
    WELL_FORMED_NOT_MANDATORY = (
        "  - **Integration review:** not mandatory. **No-checkpoint justification (architect):** fixture exemption."
    )
    UNTAGGED_MANDATORY = "  - **Integration review:** mandatory. **Rationale:** missing the architect tag."
    MALFORMED_POLARITY = "  - **Integration review:** unclear. **Rationale (architect):** ambiguous."

    def _operation_with_authority(self, role="architect", rationale="fixture rationale"):
        sources = source_bytes("active")
        operation = operation_for(
            sources,
            "progress",
            payload={"target": "backlog", "message": "Unrelated status update."},
        )
        value = dict(operation.data)
        value["architect_authority"] = {"role": role, "rationale": rationale}
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        return editor.load_operation(raw)

    def test_checkpoint_attribute_line_recognizes_both_polarities(self):
        mandatory = editor._checkpoint_attribute_line(self.WELL_FORMED_MANDATORY)
        self.assertEqual(mandatory["mandatory"], True)
        self.assertTrue(mandatory["architect_tagged"])
        not_mandatory = editor._checkpoint_attribute_line(self.WELL_FORMED_NOT_MANDATORY)
        self.assertEqual(not_mandatory["mandatory"], False)
        self.assertTrue(not_mandatory["architect_tagged"])

    def test_checkpoint_attribute_line_ignores_prose_mentions(self):
        prose = "  - **Acceptance criteria:** discusses the `Integration review: mandatory` attribute in passing."
        self.assertIsNone(editor._checkpoint_attribute_line(prose))

    def test_unchanged_checkpoint_bullet_is_not_gated(self):
        before = f"block\n{self.WELL_FORMED_MANDATORY}\nmore text\n"
        after = f"block\n{self.WELL_FORMED_MANDATORY}\nmore text changed\n"
        editor._enforce_checkpoint_authority(
            editor.Operation({"architect_authority": None}, "raw", "contract"),
            before,
            after,
            "1000-01",
            "TODO.md",
        )  # no exception: the attribute bullet itself did not change

    def test_new_checkpoint_bullet_without_authority_is_rejected(self):
        operation = editor.Operation({}, "raw", "contract")
        with self.assertRaises(editor.EditorError) as raised:
            editor._enforce_checkpoint_authority(
                operation,
                "block\nmore text\n",
                f"block\n{self.WELL_FORMED_MANDATORY}\nmore text\n",
                "1000-01",
                "TODO.md",
            )
        self.assertEqual(raised.exception.rule, "LTE-CHECKPOINT-AUTHORITY-REQUIRED")

    def test_removed_checkpoint_bullet_without_authority_is_rejected(self):
        operation = editor.Operation({}, "raw", "contract")
        with self.assertRaises(editor.EditorError) as raised:
            editor._enforce_checkpoint_authority(
                operation,
                f"block\n{self.WELL_FORMED_MANDATORY}\nmore text\n",
                "block\nmore text\n",
                "1000-01",
                "TODO.md",
            )
        self.assertEqual(raised.exception.rule, "LTE-CHECKPOINT-AUTHORITY-REQUIRED")

    def test_authorized_but_untagged_result_is_still_rejected(self):
        operation = editor.Operation(
            {"architect_authority": {"role": "architect", "rationale": "fixture"}}, "raw", "contract"
        )
        with self.assertRaises(editor.EditorError) as raised:
            editor._enforce_checkpoint_authority(
                operation,
                "block\nmore text\n",
                f"block\n{self.UNTAGGED_MANDATORY}\nmore text\n",
                "1000-01",
                "TODO.md",
            )
        self.assertEqual(raised.exception.rule, "LTE-CHECKPOINT-MALFORMED")

    def test_authorized_but_malformed_polarity_is_still_rejected(self):
        operation = editor.Operation(
            {"architect_authority": {"role": "architect", "rationale": "fixture"}}, "raw", "contract"
        )
        with self.assertRaises(editor.EditorError) as raised:
            editor._enforce_checkpoint_authority(
                operation,
                "block\nmore text\n",
                f"block\n{self.MALFORMED_POLARITY}\nmore text\n",
                "1000-01",
                "TODO.md",
            )
        self.assertEqual(raised.exception.rule, "LTE-CHECKPOINT-MALFORMED")

    def test_authorized_well_formed_change_is_accepted(self):
        operation = editor.Operation(
            {"architect_authority": {"role": "architect", "rationale": "fixture"}}, "raw", "contract"
        )
        editor._enforce_checkpoint_authority(
            operation,
            "block\nmore text\n",
            f"block\n{self.WELL_FORMED_MANDATORY}\nmore text\n",
            "1000-01",
            "TODO.md",
        )  # no exception

    def test_load_operation_accepts_valid_architect_authority(self):
        operation = self._operation_with_authority()
        self.assertEqual(operation.data["architect_authority"], {"role": "architect", "rationale": "fixture rationale"})

    def test_load_operation_rejects_non_architect_role(self):
        with self.assertRaises(editor.EditorError) as raised:
            self._operation_with_authority(role="grunt")
        self.assertEqual(raised.exception.rule, "LTE-CHECKPOINT-AUTHORITY-REQUIRED")

    def test_load_operation_rejects_empty_rationale(self):
        with self.assertRaises(editor.EditorError):
            self._operation_with_authority(rationale="")

    def test_load_operation_rejects_unknown_architect_authority_field(self):
        sources = source_bytes("active")
        operation = operation_for(
            sources,
            "progress",
            payload={"target": "backlog", "message": "Unrelated status update."},
        )
        value = dict(operation.data)
        value["architect_authority"] = {"role": "architect", "rationale": "fixture", "extra": True}
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        with self.assertRaises(editor.EditorError) as raised:
            editor.load_operation(raw)
        self.assertEqual(raised.exception.rule, "LTE-OP-UNKNOWN-FIELD")

    def test_ordinary_operation_without_architect_authority_is_unaffected(self):
        sources = source_bytes("active")
        operation = operation_for(
            sources,
            "progress",
            payload={"target": "backlog", "message": "Phase one passed."},
        )
        plan = editor.plan_operation(operation, sources)
        after = planned_change(plan, "TODO.md").after.decode()
        self.assertIn("Phase one passed.", after)


class RenderingTests(unittest.TestCase):
    def test_pickup_creates_exact_claim_and_preserves_neighbor(self):
        sources = source_bytes("open")
        before = dict(sources)
        operation = operation_for(
            sources,
            "pickup",
            marker=" ",
            actor_agent="beta",
            actor_request="req-beta-001",
            payload={
                "claim_path": "TODO-beta-1000-01-req-beta-001.md",
                "base_commit": A,
                "capability_class": "privileged",
                "scope": ["src/a.py", "docs/a.md"],
                "next_step": "Implement exact editor behavior.",
            },
        )
        plan = editor.plan_operation(operation, sources)
        self.assertEqual(sources, before)
        self.assertEqual({change.action for change in plan.changes}, {"replace", "create"})
        todo = planned_change(plan, "TODO.md").after.decode()
        self.assertIn("- [p] **1000-01**", todo)
        self.assertIn("TODO-beta-1000-01-req-beta-001.md", todo)
        self.assertIn("- [ ] **1000-02** Neighbor.", todo)
        claim = planned_change(plan, "TODO-beta-1000-01-req-beta-001.md").after.decode()
        self.assertIn("owner_token: agent:beta:1000-01:req-beta-001", claim)
        self.assertTrue(claim.endswith("Implement exact editor behavior.\n"))

    def test_pickup_rejects_existing_active_claim(self):
        sources = source_bytes("open")
        sources["TODO-alpha-1000-01-req-alpha-001.md"] = source_bytes("active")["TODO-alpha-1000-01-req-alpha-001.md"]
        operation = operation_for(
            sources,
            "pickup",
            marker=" ",
            actor_agent="beta",
            actor_request="req-beta-001",
            payload={
                "claim_path": "TODO-beta-1000-01-req-beta-001.md",
                "base_commit": A,
                "capability_class": "privileged",
                "scope": ["src/a.py"],
                "next_step": "Implement.",
            },
        )
        with self.assertRaises(editor.EditorError) as raised:
            editor.plan_operation(operation, sources)
        self.assertEqual(raised.exception.rule, "LTE-CLAIM-CONFLICT")

    def test_progress_supports_backlog_and_claim(self):
        sources = source_bytes("active")
        backlog_operation = operation_for(
            sources,
            "progress",
            payload={"target": "backlog", "message": "Phase one passed."},
        )
        backlog_plan = editor.plan_operation(backlog_operation, sources)
        after = planned_change(backlog_plan, "TODO.md").after.decode()
        self.assertIn("Progress (2026-08-17, fixture-progress-001)", after)
        self.assertIn("- [ ] **1000-02** Neighbor Task.", after)
        claim_operation = operation_for(
            sources,
            "progress",
            payload={"target": "claim", "message": "Phase one passed.", "next_step": "Run phase two."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
            operation_id="fixture-progress-claim-001",
        )
        claim_plan = editor.plan_operation(claim_operation, sources)
        self.assertEqual(len(claim_plan.changes), 1)
        claim_after = claim_plan.changes[0].after.decode()
        self.assertIn("## Progress fixture-progress-claim-001", claim_after)
        self.assertTrue(claim_after.endswith("Run phase two.\n"))

    def test_closure_adds_one_ref_and_bound_closure(self):
        sources = source_bytes("active")
        operation = operation_for(
            sources,
            "closure",
            payload={"substantive_ref": B, "summary": "Implementation and validation passed."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        plan = editor.plan_operation(operation, sources)
        self.assertEqual(len(plan.changes), 1)
        after = plan.changes[0].after.decode()
        self.assertIn(f"- [x] **1000-01** Target Task. REF: {B}", after)
        self.assertEqual(after.count(f"REF: {B}"), 1)
        self.assertIn("Closure (2026-08-17, fixture-closure-001)", after)
        self.assertIn("- [ ] **1000-02** Neighbor Task.", after)
        self.assertFalse(
            any(
                change.path == "TODO-alpha-1000-01-req-alpha-001.md"
                for change in plan.changes
            )
        )

    def test_wontfix_requires_claim_reason_and_full_ref(self):
        sources = source_bytes("active")
        operation = operation_for(
            sources,
            "wontfix",
            payload={"disposition_ref": B, "reason": "The defect does not reproduce."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        plan = editor.plan_operation(operation, sources)
        after = planned_change(plan, "TODO.md").after.decode()
        self.assertIn(f"- [w] **1000-01** Target Task. REF: {B}", after)
        self.assertIn("Reason (2026-08-17, fixture-wontfix-001)", after)

    def test_parent_aggregation_binds_complete_terminal_child_set_without_closing(self):
        sources = source_bytes("parent")
        document = editor.parse_backlog("TODO.md", sources["TODO.md"])
        children = []
        for task in document.tasks:
            if task.id.startswith("1000-05."):
                raw = document.text[task.span.start:task.span.end].encode()
                ref = A if task.id.endswith("01") else B
                children.append({"task_id": task.id, "marker": task.marker, "ref": ref, "expected_task_sha256": editor._sha256(raw)})
        operation = operation_for(
            sources,
            "parent-aggregation",
            task_id="1000-05",
            marker="p",
            payload={"children": children, "summary": "parent validation remains pending."},
            actor_request="req-parent-001",
        )
        plan = editor.plan_operation(operation, sources)
        after = plan.changes[0].after.decode()
        self.assertIn("- [p] **1000-05** Parent package.", after)
        self.assertIn("Aggregation (2026-08-17, fixture-parent-aggregation-001)", after)
        for child in ("1000-05.01", "1000-05.02"):
            self.assertEqual(after.count(f"**{child}**"), 1)
        bad = dict(operation.data)
        bad_payload = dict(bad["payload"])
        bad_payload["children"] = bad_payload["children"][:-1]
        bad["payload"] = bad_payload
        bad_operation = editor.load_operation((json.dumps(bad) + "\n").encode())
        with self.assertRaises(editor.EditorError) as raised:
            editor.plan_operation(bad_operation, sources)
        self.assertEqual(raised.exception.rule, "LTE-PARENT-CHILD-SET")

    def test_ref_injection_and_stale_ref_correction_are_explicit(self):
        sources = source_bytes("corruption-chain")
        insertion = operation_for(
            sources,
            "ref-injection",
            feature_id="0037",
            task_id="0037-03.01",
            marker="x",
            actor_request="req-ref-001",
            payload={"new_ref": B, "reason": "Missing header REF."},
        )
        plan = editor.plan_operation(insertion, sources)
        after = plan.changes[0].after.decode()
        self.assertIn(f"**0037-03.01** Lifecycle contract. REF: {B}", after)
        self.assertEqual(after.count("- [ ] **0037-03.02**"), 1)
        self.assertIn("### Campaign B", after)

        stale = source_bytes("stale-ref")
        correction = operation_for(
            stale,
            "ref-injection",
            marker="x",
            payload={"new_ref": B, "expected_old_ref": A, "reason": "Old pre-amend REF is unreachable."},
            actor_request="req-ref-002",
        )
        corrected = editor.plan_operation(correction, stale).changes[0].after.decode()
        self.assertIn(f"Closed. REF: {B}", corrected)
        self.assertIn(f"from `{A}` to `{B}`", corrected)
        self.assertIn(f"Original assertion retains `{A}`", corrected)

    def test_append_correction_preserves_corruption_chain_neighbor_bytes(self):
        sources = source_bytes("corruption-chain")
        operation = operation_for(
            sources,
            "append-correction",
            feature_id="0037",
            task_id="0037-03.01",
            marker="x",
            actor_request="req-correct-001",
            payload={"target": "backlog", "correction_id": "correction-001", "message": "Missing closure evidence restored additively."},
        )
        document = editor.parse_backlog("TODO.md", sources["TODO.md"])
        task = next(item for item in document.tasks if item.id == "0037-03.01")
        suffix = document.text[task.span.end:]
        plan = editor.plan_operation(operation, sources)
        after = plan.changes[0].after.decode()
        self.assertTrue(after.endswith(suffix))
        self.assertIn("Correction correction-001", after)
        self.assertEqual(after.count("- [ ] **0037-03.02**"), 1)
        with self.assertRaises(editor.EditorError) as raised:
            editor.plan_operation(operation, {"TODO.md": plan.changes[0].after})
        self.assertIn(raised.exception.rule, {"LTE-DOCUMENT-DRIFT", "LTE-NOOP"})

    def test_claim_handoff_and_finalization_bind_exact_claim(self):
        sources = source_bytes("active")
        handoff = operation_for(
            sources,
            "claim-handoff",
            payload={
                "destination_claim_path": "TODO-beta-1000-01-req-beta-001.md",
                "new_request_id": "req-beta-001",
                "new_owner_token": "agent:beta:1000-01:req-beta-001",
                "new_capability_class": "privileged",
                "new_base_commit": B,
                "scope": ["src/target.py"],
                "next_step": "Continue beta work.",
                "authorization": "explicit-owner-release-or-authorized-decision",
                "archive_path": "logs/claims/alpha.md",
            },
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        handoff_plan = editor.plan_operation(handoff, sources)
        self.assertEqual({change.action for change in handoff_plan.changes}, {"replace", "create", "delete"})
        todo = planned_change(handoff_plan, "TODO.md").after.decode()
        self.assertIn("TODO-beta-1000-01-req-beta-001.md", todo)
        self.assertNotIn("Claimed via `TODO-alpha", todo)
        self.assertEqual(planned_change(handoff_plan, "logs/claims/alpha.md").after, sources["TODO-alpha-1000-01-req-alpha-001.md"])

        wrong = dict(handoff.data)
        wrong_claim = dict(wrong["claim"])
        wrong_claim["path"] = "TODO-beta-1000-01-req-alpha-001.md"
        wrong["claim"] = wrong_claim
        wrong_op = editor.load_operation((json.dumps(wrong) + "\n").encode())
        with self.assertRaises(editor.EditorError):
            editor.plan_operation(wrong_op, sources)

        closure = operation_for(
            sources,
            "closure",
            payload={"substantive_ref": B, "summary": "Done."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        closed_todo = planned_change(editor.plan_operation(closure, sources), "TODO.md").after
        final_sources = dict(sources)
        final_sources["TODO.md"] = closed_todo
        finalization = operation_for(
            final_sources,
            "claim-finalization",
            marker="x",
            payload={"archive_path": "logs/claims/final-alpha.md"},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        final_plan = editor.plan_operation(finalization, final_sources)
        self.assertEqual({change.action for change in final_plan.changes}, {"replace", "create", "delete"})
        self.assertIn("Claim finalized", planned_change(final_plan, "TODO.md").after.decode())

    def test_all_nine_operation_plans_preserve_bytes_outside_declared_task_span(self):
        plans = []
        open_sources = source_bytes("open")
        plans.append(
            editor.plan_operation(
                operation_for(
                    open_sources,
                    "pickup",
                    marker=" ",
                    actor_agent="beta",
                    actor_request="req-beta-001",
                    payload={
                        "claim_path": "TODO-beta-1000-01-req-beta-001.md",
                        "base_commit": "pending-discovery",
                        "capability_class": "sandboxed/grunt",
                        "scope": ["src/a.py"],
                        "next_step": "Discover.",
                    },
                ),
                open_sources,
            )
        )
        active = source_bytes("active")
        plans.append(editor.plan_operation(operation_for(active, "progress", payload={"target": "backlog", "message": "Progress."}), active))
        plans.append(editor.plan_operation(operation_for(active, "closure", payload={"substantive_ref": B, "summary": "Done."}, claim_path="TODO-alpha-1000-01-req-alpha-001.md"), active))
        plans.append(editor.plan_operation(operation_for(active, "wontfix", payload={"disposition_ref": B, "reason": "No repro."}, claim_path="TODO-alpha-1000-01-req-alpha-001.md"), active))
        parent = source_bytes("parent")
        parent_doc = editor.parse_backlog("TODO.md", parent["TODO.md"])
        children = []
        for child in parent_doc.tasks[1:]:
            children.append({
                "task_id": child.id,
                "marker": child.marker,
                "ref": A if child.id.endswith("01") else B,
                "expected_task_sha256": editor._sha256(parent_doc.text[child.span.start:child.span.end].encode()),
            })
        plans.append(editor.plan_operation(operation_for(parent, "parent-aggregation", task_id="1000-05", marker="p", actor_request="req-parent-001", payload={"children": children, "summary": "audit pending."}), parent))
        stale = source_bytes("stale-ref")
        plans.append(editor.plan_operation(operation_for(stale, "ref-injection", marker="x", actor_request="req-ref-001", payload={"new_ref": B, "expected_old_ref": A, "reason": "Correct stale."}), stale))
        plans.append(editor.plan_operation(operation_for(active, "claim-handoff", claim_path="TODO-alpha-1000-01-req-alpha-001.md", payload={"destination_claim_path": "TODO-beta-1000-01-req-beta-001.md", "new_request_id": "req-beta-001", "new_owner_token": "agent:beta:1000-01:req-beta-001", "new_capability_class": "privileged", "new_base_commit": B, "scope": ["src/target.py"], "next_step": "Continue.", "authorization": "explicit-owner-release-or-authorized-decision", "archive_path": "logs/claims/alpha.md"}), active))
        chain = source_bytes("corruption-chain")
        plans.append(editor.plan_operation(operation_for(chain, "append-correction", feature_id="0037", task_id="0037-03.01", marker="x", actor_request="req-correction-001", payload={"target": "backlog", "correction_id": "correction-001", "message": "Restore evidence."}), chain))
        closure_plan = plans[2]
        final_sources = dict(active)
        final_sources["TODO.md"] = planned_change(closure_plan, "TODO.md").after
        plans.append(editor.plan_operation(operation_for(final_sources, "claim-finalization", marker="x", claim_path="TODO-alpha-1000-01-req-alpha-001.md", payload={"archive_path": "logs/claims/final.md"}), final_sources))

        self.assertEqual(len(plans), 9)
        for plan in plans:
            with self.subTest(kind=plan.operation.data["kind"]):
                change = next(item for item in plan.changes if item.path == "TODO.md")
                self.assertIsNotNone(change.declared_span)
                span = change.declared_span
                self.assertEqual(change.before[: span.start], change.after[: span.start])
                self.assertTrue(change.after.endswith(change.before[span.end :]))

    def test_illegal_operation_states_reject(self):
        open_sources = source_bytes("open")
        progress = operation_for(
            open_sources,
            "progress",
            marker=" ",
            payload={"target": "backlog", "message": "Not active."},
        )
        with self.assertRaises(editor.EditorError) as raised:
            editor.plan_operation(progress, open_sources)
        self.assertEqual(raised.exception.rule, "LTE-STATE-TRANSITION")

        ref_operation = operation_for(
            open_sources,
            "ref-injection",
            marker=" ",
            payload={"new_ref": B, "reason": "Not terminal."},
            actor_request="req-ref-open-001",
        )
        with self.assertRaises(editor.EditorError) as raised:
            editor.plan_operation(ref_operation, open_sources)
        self.assertEqual(raised.exception.rule, "LTE-STATE-TRANSITION")

        closed_claim_sources = source_bytes("active")
        closed_claim_sources["TODO-alpha-1000-01-req-alpha-001.md"] = closed_claim_sources[
            "TODO-alpha-1000-01-req-alpha-001.md"
        ].replace(b"state: [p]", b"state: [x]")
        closure = operation_for(
            closed_claim_sources,
            "closure",
            payload={"substantive_ref": B, "summary": "Claim is not active."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        with self.assertRaises(editor.EditorError) as raised:
            editor.plan_operation(closure, closed_claim_sources)
        self.assertEqual(raised.exception.rule, "LTE-STATE-TRANSITION")

    def test_wrong_claim_digest_owner_and_pointer_reject_without_change(self):
        sources = source_bytes("active")
        operation = operation_for(
            sources,
            "closure",
            payload={"substantive_ref": B, "summary": "Done."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        variants = []
        changed_claim = dict(sources)
        changed_claim["TODO-alpha-1000-01-req-alpha-001.md"] += b"\nconcurrent\n"
        variants.append(changed_claim)
        changed_pointer = dict(sources)
        changed_pointer["TODO.md"] = changed_pointer["TODO.md"].replace(b"TODO-alpha", b"TODO-beta", 1)
        variants.append(changed_pointer)
        for variant in variants:
            with self.subTest(keys=variant.keys()):
                with self.assertRaises(editor.EditorError):
                    editor.plan_operation(operation, variant)
        self.assertEqual(sources, source_bytes("active"))


class CandidateAndPromotionTests(unittest.TestCase):
    def make_root(self, sources):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative, raw in sources.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        return root

    def closure_plan(self, sources):
        operation = operation_for(
            sources,
            "closure",
            payload={"substantive_ref": B, "summary": "Done."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        return editor.plan_operation(operation, sources)

    def test_candidate_contains_bounded_diff_and_content_addressed_blobs(self):
        sources = source_bytes("active")
        before = dict(sources)
        plan = self.closure_plan(sources)
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "candidate"
            receipt = editor.write_candidate(plan, candidate)
            self.assertEqual(sources, before)
            self.assertEqual(receipt.manifest_path, "candidate.json")
            manifest = json.loads((candidate / "candidate.json").read_text())
            self.assertEqual(manifest["schema"], editor.CANDIDATE_SCHEMA)
            self.assertFalse(manifest["promotion"]["standalone_allowed"])
            self.assertEqual(
                {entry["path"] for entry in manifest["read_set"]},
                set(sources),
            )
            self.assertTrue((candidate / "diff.patch").read_text().startswith("--- a/TODO.md"))
            self.assertEqual(editor._sha256((candidate / "diff.patch").read_bytes()), receipt.diff_sha256)
            for change in manifest["changes"]:
                if change["before_blob"]:
                    self.assertTrue((candidate / change["before_blob"]).is_file())
                if change["after_blob"]:
                    self.assertTrue((candidate / change["after_blob"]).is_file())

    def test_valid_single_file_candidate_preflight_requires_coordinator_without_mutation(self):
        sources = source_bytes("active")
        root = self.make_root(sources)
        plan = self.closure_plan(sources)
        candidate = root / "candidate-promote"
        receipt = editor.write_candidate(plan, candidate)
        verified = editor.verify_candidate_for_promotion(
            root,
            candidate / "candidate.json",
            receipt.manifest_sha256,
        )
        self.assertEqual(verified["schema"], editor.CANDIDATE_SCHEMA)
        before = (root / "TODO.md").read_bytes()
        result = editor.promote_candidate(
            root,
            candidate / "candidate.json",
            receipt.manifest_sha256,
        )
        self.assertEqual(result.verdict, "verified-coordinator-required")
        self.assertEqual(result.findings[0]["rule"], "LTE-PROMOTE-COORDINATOR-REQUIRED")
        self.assertTrue(result.candidate["preflight_verified"])
        self.assertEqual(
            {entry["path"] for entry in result.candidate["read_set"]},
            set(sources),
        )
        self.assertEqual((root / "TODO.md").read_bytes(), before)

    def test_claim_and_backlog_read_set_drift_both_reject_promotion(self):
        sources = source_bytes("active")
        root = self.make_root(sources)
        closure_plan = self.closure_plan(sources)
        closure_candidate = root / "candidate-claim-drift"
        closure_receipt = editor.write_candidate(closure_plan, closure_candidate)
        claim_path = root / "TODO-alpha-1000-01-req-alpha-001.md"
        claim_path.write_bytes(claim_path.read_bytes() + b"\nconcurrent claim edit\n")
        todo_before = (root / "TODO.md").read_bytes()
        with self.assertRaises(editor.EditorError) as raised:
            editor.promote_candidate(
                root,
                closure_candidate / "candidate.json",
                closure_receipt.manifest_sha256,
            )
        self.assertEqual(raised.exception.rule, "LTE-PROMOTE-DRIFT")
        self.assertEqual((root / "TODO.md").read_bytes(), todo_before)

        fresh_sources = source_bytes("active")
        second_root = self.make_root(fresh_sources)
        progress_operation = operation_for(
            fresh_sources,
            "progress",
            payload={"target": "claim", "message": "Claim progress.", "next_step": "Continue."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
            operation_id="fixture-readset-progress-001",
        )
        progress_plan = editor.plan_operation(progress_operation, fresh_sources)
        progress_candidate = second_root / "candidate-todo-drift"
        progress_receipt = editor.write_candidate(progress_plan, progress_candidate)
        todo_path = second_root / "TODO.md"
        todo_path.write_bytes(todo_path.read_bytes().replace(b"Neighbor Task", b"Neighbor changed"))
        claim_before = (second_root / "TODO-alpha-1000-01-req-alpha-001.md").read_bytes()
        with self.assertRaises(editor.EditorError) as raised:
            editor.promote_candidate(
                second_root,
                progress_candidate / "candidate.json",
                progress_receipt.manifest_sha256,
            )
        self.assertEqual(raised.exception.rule, "LTE-PROMOTE-DRIFT")
        self.assertEqual((second_root / "TODO-alpha-1000-01-req-alpha-001.md").read_bytes(), claim_before)

    def test_concurrent_outside_task_edit_rejects_promotion(self):
        sources = source_bytes("active")
        root = self.make_root(sources)
        plan = self.closure_plan(sources)
        candidate = root / "candidate-drift"
        receipt = editor.write_candidate(plan, candidate)
        todo = root / "TODO.md"
        todo.write_bytes(todo.read_bytes().replace(b"Neighbor Task", b"Neighbor edited concurrently"))
        before = todo.read_bytes()
        with self.assertRaises(editor.EditorError) as raised:
            editor.promote_candidate(root, candidate / "candidate.json", receipt.manifest_sha256)
        self.assertEqual(raised.exception.rule, "LTE-PROMOTE-DRIFT")
        self.assertEqual(todo.read_bytes(), before)

    def test_preflight_replans_embedded_operation_and_rediscovers_claims(self):
        sources = source_bytes("active")
        root = self.make_root(sources)
        plan = self.closure_plan(sources)
        candidate = root / "candidate-semantic"
        receipt = editor.write_candidate(plan, candidate)
        manifest = json.loads((candidate / "candidate.json").read_text())
        change = manifest["changes"][0]
        before = (candidate / change["before_blob"]).read_bytes()
        original_after = (candidate / change["after_blob"]).read_bytes()
        altered_after = original_after.replace(
            b"fixture-closure-001):** Done.",
            b"fixture-closure-001):** Different but internally consistent output.",
        )
        self.assertNotEqual(altered_after, original_after)
        altered_sha = editor._sha256(altered_after)
        altered_blob = f"blobs/{altered_sha}.after"
        (candidate / altered_blob).write_bytes(altered_after)
        change["after_sha256"] = altered_sha
        change["after_blob"] = altered_blob
        change["bytes_after"] = len(altered_after)
        changed = editor.Change(
            change["path"],
            change["action"],
            before,
            altered_after,
            editor.Span(
                change["declared_span"]["start"],
                change["declared_span"]["end"],
            ),
        )
        diff = editor._diff_for_changes([changed])
        (candidate / "diff.patch").write_bytes(diff)
        manifest["diff"] = {
            "path": "diff.patch",
            "sha256": editor._sha256(diff),
            "bytes": len(diff),
        }
        encoded = editor._json_bytes(manifest)
        (candidate / "candidate.json").write_bytes(encoded)
        with self.assertRaises(editor.EditorError) as raised:
            editor.verify_candidate_for_promotion(
                root,
                candidate / "candidate.json",
                editor._sha256(encoded),
            )
        self.assertEqual(raised.exception.rule, "LTE-CANDIDATE-TAMPERED")
        self.assertEqual((root / "TODO.md").read_bytes(), sources["TODO.md"])

        fresh_root = self.make_root(sources)
        fresh_candidate = fresh_root / "candidate-new-claim"
        fresh_receipt = editor.write_candidate(self.closure_plan(sources), fresh_candidate)
        extra_claim = sources["TODO-alpha-1000-01-req-alpha-001.md"].replace(
            b"Alpha claim",
            b"Gamma claim",
        ).replace(
            b"req-alpha-001",
            b"req-gamma-001",
        ).replace(
            b"agent:alpha",
            b"agent:gamma",
        )
        (fresh_root / "TODO-gamma-1000-01-req-gamma-001.md").write_bytes(extra_claim)
        with self.assertRaises(editor.EditorError) as raised:
            editor.verify_candidate_for_promotion(
                fresh_root,
                fresh_candidate / "candidate.json",
                fresh_receipt.manifest_sha256,
            )
        self.assertEqual(raised.exception.rule, "LTE-CANDIDATE-TAMPERED")

    def test_manifest_diff_and_blob_tampering_reject(self):
        sources = source_bytes("active")
        for tamper in ("manifest", "diff", "before-blob", "blob", "nested-operation", "blob-path", "readset-omit"):
            with self.subTest(tamper=tamper):
                root = self.make_root(sources)
                plan = self.closure_plan(sources)
                candidate = root / f"candidate-{tamper}"
                receipt = editor.write_candidate(plan, candidate)
                if tamper == "manifest":
                    (candidate / "candidate.json").write_bytes((candidate / "candidate.json").read_bytes() + b" ")
                elif tamper == "diff":
                    (candidate / "diff.patch").write_bytes(b"tampered")
                elif tamper == "before-blob":
                    manifest = json.loads((candidate / "candidate.json").read_text())
                    (candidate / manifest["changes"][0]["before_blob"]).write_bytes(b"tampered")
                elif tamper == "blob":
                    manifest = json.loads((candidate / "candidate.json").read_text())
                    (candidate / manifest["changes"][0]["after_blob"]).write_bytes(b"tampered")
                elif tamper == "nested-operation":
                    manifest = json.loads((candidate / "candidate.json").read_text())
                    manifest["operation"] = "invalid"
                    encoded = editor._json_bytes(manifest)
                    (candidate / "candidate.json").write_bytes(encoded)
                    receipt = editor.CandidateReceipt(
                        receipt.manifest_path,
                        editor._sha256(encoded),
                        receipt.diff_path,
                        receipt.diff_sha256,
                        receipt.changes,
                    )
                elif tamper == "blob-path":
                    manifest = json.loads((candidate / "candidate.json").read_text())
                    manifest["changes"][0]["after_blob"] = "../outside"
                    encoded = editor._json_bytes(manifest)
                    (candidate / "candidate.json").write_bytes(encoded)
                    receipt = editor.CandidateReceipt(
                        receipt.manifest_path,
                        editor._sha256(encoded),
                        receipt.diff_path,
                        receipt.diff_sha256,
                        receipt.changes,
                    )
                else:
                    manifest = json.loads((candidate / "candidate.json").read_text())
                    manifest["read_set"] = [
                        entry
                        for entry in manifest["read_set"]
                        if entry["path"] != "TODO-alpha-1000-01-req-alpha-001.md"
                    ]
                    encoded = editor._json_bytes(manifest)
                    (candidate / "candidate.json").write_bytes(encoded)
                    receipt = editor.CandidateReceipt(
                        receipt.manifest_path,
                        editor._sha256(encoded),
                        receipt.diff_path,
                        receipt.diff_sha256,
                        receipt.changes,
                    )
                before = (root / "TODO.md").read_bytes()
                with self.assertRaises(editor.EditorError) as raised:
                    editor.promote_candidate(root, candidate / "candidate.json", receipt.manifest_sha256)
                self.assertEqual(raised.exception.rule, "LTE-CANDIDATE-TAMPERED")
                self.assertEqual((root / "TODO.md").read_bytes(), before)

    def test_create_precondition_cannot_be_omitted_from_candidate(self):
        sources = source_bytes("open")
        root = self.make_root(sources)
        operation = operation_for(
            sources,
            "pickup",
            marker=" ",
            actor_agent="beta",
            actor_request="req-beta-001",
            payload={
                "claim_path": "TODO-beta-1000-01-req-beta-001.md",
                "base_commit": "pending-discovery",
                "capability_class": "sandboxed/grunt",
                "scope": ["src/a.py"],
                "next_step": "Discover.",
            },
        )
        plan = editor.plan_operation(operation, sources)
        candidate = root / "candidate-absent-omit"
        receipt = editor.write_candidate(plan, candidate)
        manifest = json.loads((candidate / "candidate.json").read_text())
        manifest["absent_paths"] = []
        encoded = editor._json_bytes(manifest)
        (candidate / "candidate.json").write_bytes(encoded)
        before = (root / "TODO.md").read_bytes()
        with self.assertRaises(editor.EditorError) as raised:
            editor.verify_candidate_for_promotion(
                root,
                candidate / "candidate.json",
                editor._sha256(encoded),
            )
        self.assertEqual(raised.exception.rule, "LTE-CANDIDATE-TAMPERED")
        self.assertEqual((root / "TODO.md").read_bytes(), before)

    def test_promotion_preflight_never_calls_authoritative_write(self):
        sources = source_bytes("active")
        root = self.make_root(sources)
        plan = self.closure_plan(sources)
        candidate = root / "candidate-no-write"
        receipt = editor.write_candidate(plan, candidate)
        target = root / "TODO.md"
        before = target.read_bytes()
        with mock.patch.object(editor, "_atomic_write", side_effect=AssertionError("must not write")) as writer:
            result = editor.promote_candidate(
                root,
                candidate / "candidate.json",
                receipt.manifest_sha256,
            )
        self.assertEqual(result.verdict, "verified-coordinator-required")
        self.assertEqual(result.findings[0]["rule"], "LTE-PROMOTE-COORDINATOR-REQUIRED")
        writer.assert_not_called()
        self.assertEqual(target.read_bytes(), before)

    def test_candidate_intermediate_symlink_is_rejected(self):
        sources = source_bytes("active")
        root = self.make_root(sources)
        plan = self.closure_plan(sources)
        candidate = root / "candidate-symlink"
        receipt = editor.write_candidate(plan, candidate)
        real = candidate / "real-blobs"
        (candidate / "blobs").rename(real)
        try:
            (candidate / "blobs").symlink_to(real, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        before = (root / "TODO.md").read_bytes()
        with self.assertRaises(editor.EditorError) as raised:
            editor.promote_candidate(root, candidate / "candidate.json", receipt.manifest_sha256)
        self.assertIn(raised.exception.rule, {"LTE-CANDIDATE-TAMPERED", "LTE-INPUT-NONREGULAR"})
        self.assertEqual((root / "TODO.md").read_bytes(), before)

    def test_multi_file_handoff_requires_transaction_coordinator(self):
        sources = source_bytes("active")
        root = self.make_root(sources)
        operation = operation_for(
            sources,
            "claim-handoff",
            payload={
                "destination_claim_path": "TODO-beta-1000-01-req-beta-001.md",
                "new_request_id": "req-beta-001",
                "new_owner_token": "agent:beta:1000-01:req-beta-001",
                "new_capability_class": "privileged",
                "new_base_commit": B,
                "scope": ["src/target.py"],
                "next_step": "Continue.",
                "authorization": "explicit-owner-release-or-authorized-decision",
                "archive_path": "logs/claims/alpha.md",
            },
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        plan = editor.plan_operation(operation, sources)
        candidate = root / "candidate-handoff"
        receipt = editor.write_candidate(plan, candidate)
        result = editor.promote_candidate(
            root,
            candidate / "candidate.json",
            receipt.manifest_sha256,
        )
        self.assertEqual(result.verdict, "verified-coordinator-required")
        self.assertEqual(result.findings[0]["rule"], "LTE-PROMOTE-COORDINATOR-REQUIRED")
        self.assertEqual(len(result.changes), 4)
        self.assertEqual((root / "TODO.md").read_bytes(), sources["TODO.md"])

    def test_cli_plan_writes_candidate_without_mutating_sources(self):
        sources = source_bytes("active")
        root = self.make_root(sources)
        operation = operation_for(
            sources,
            "closure",
            payload={"substantive_ref": B, "summary": "Done."},
            claim_path="TODO-alpha-1000-01-req-alpha-001.md",
        )
        operation_path = root / "operation.json"
        operation_path.write_bytes(editor._json_bytes(operation.data))
        candidate = root / "candidate-cli"
        before = {path: (root / path).read_bytes() for path in sources}
        completed = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "legacy_task_editor.py"),
                "plan",
                "--operation",
                str(operation_path),
                "--root",
                str(root),
                "--candidate-dir",
                str(candidate),
                "--json",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        planned = json.loads(completed.stdout)
        self.assertEqual(planned["verdict"], "planned")
        self.assertTrue((candidate / "candidate.json").is_file())
        self.assertEqual({path: (root / path).read_bytes() for path in sources}, before)

        preflight = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "legacy_task_editor.py"),
                "promote",
                "--candidate-manifest",
                str(candidate / "candidate.json"),
                "--expect-candidate-sha256",
                planned["candidate"]["manifest_sha256"],
                "--root",
                str(root),
                "--json",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
        )
        self.assertEqual(preflight.returncode, editor.EXIT_PROMOTE, preflight.stderr)
        verified = json.loads(preflight.stdout)
        self.assertEqual(verified["verdict"], "verified-coordinator-required")
        self.assertEqual(verified["operation"]["id"], operation.data["operation_id"])
        self.assertTrue(verified["candidate"]["preflight_verified"])
        self.assertTrue(verified["candidate"]["read_set"])
        self.assertEqual({path: (root / path).read_bytes() for path in sources}, before)


class SafetySurfaceTests(unittest.TestCase):
    def test_no_shell_heredoc_or_ambient_clock(self):
        source = (TOOLS / "legacy_task_editor.py").read_text(encoding="utf-8")
        self.assertNotIn("shell=True", source)
        self.assertNotIn("os.popen", source)
        self.assertNotIn("date.today", source)
        self.assertNotIn("<<", source)

    def test_legacy_helper_is_retired_after_editor_lands(self):
        helper = (TOOLS / "task_bookkeeping_closure.py").read_text(encoding="utf-8")
        self.assertNotIn("write_text", helper)
        self.assertNotIn("os.popen", helper)
        self.assertIn("legacy_task_editor.py", helper)
        spec = importlib.util.spec_from_file_location(
            "task_bookkeeping_closure_retired",
            TOOLS / "task_bookkeeping_closure.py",
        )
        assert spec is not None and spec.loader is not None
        retired = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(retired)
        with tempfile.TemporaryDirectory() as temp:
            sentinel = Path(temp) / "TODO.md"
            sentinel.write_text("sentinel\n", encoding="utf-8")
            with self.assertRaises(retired.RetiredBookkeepingHelper):
                retired.update_todo(sentinel, "1000-01", B, "request", "closure")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel\n")
        completed = subprocess.run(
            [sys.executable, str(TOOLS / "task_bookkeeping_closure.py")],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("legacy_task_editor.py", completed.stdout)


if __name__ == "__main__":
    unittest.main()
