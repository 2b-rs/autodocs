#!/usr/bin/env python3
"""End-to-end lifecycle tests for Task 0019-07 S-Core exception curation."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_src" / "tools"
sys.path.insert(0, str(TOOLS))

import curation_item  # noqa: E402
import curation_report  # noqa: E402
import score_curation  # noqa: E402

NOW = "2026-08-20T00:13:00Z"


def candidate(exception_kind: str = "ambiguous") -> dict:
    return {
        "schema": "score-normalization-exception-candidate@v1",
        "candidate_id": "score-normalization-exception:0019cafe00000001",
        "exception_kind": exception_kind,
        "condition_id": "SCORE-AMBIGUOUS-SOURCE",
        "lifecycle_state": "discovered",
        "physical_queue_writer": "0019-07",
        "queue_written": False,
        "project": "ECLIPSE/S-CORE",
        "canonical_id": "ECLIPSE/S-CORE/design-doc/dec_rec__infra__dev_tools",
        "release": "v0.6.0",
        "subject": "Two release-pinned S-Core sources disagree about the design record.",
        "source": {
            "repository": "eclipse-score",
            "repository_url": "https://github.com/eclipse-score/score.git",
            "release_ref": "v0.6.0",
            "ref_kind": "tag",
            "resolved_commit": "a" * 40,
            "locator": {"path": "docs/design.md", "line_start": 10, "line_end": 14, "anchor": "dec_rec__infra__dev_tools"},
            "source_content_sha256": "b" * 64,
        },
        "existing_version_id": "ECLIPSE/S-CORE/design-doc/dec_rec__infra__dev_tools@rel:v0.6.0#11111111",
        "competing_version_id": "ECLIPSE/S-CORE/design-doc/dec_rec__infra__dev_tools@rel:v0.6.0#22222222",
    }


class ScoreCurationLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.queue = Path(self.temporary.name) / "curation-queue"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _queued(self) -> Path:
        return score_curation.queue_candidates([candidate()], self.queue, created=NOW)[0]

    def test_accepted_path_requires_curator_then_publishes(self) -> None:
        queued = self._queued()
        claimed = score_curation.claim(queued, actor_role="ai", actor_identity="research-agent", at=NOW)
        proposed = score_curation.propose(claimed, {"resolution": "retain existing version", "evidence": "source comparison"}, actor_role="ai", actor_identity="research-agent", at=NOW)

        for prohibited_role in ("ai", "tool"):
            with self.subTest(prohibited_role=prohibited_role), self.assertRaisesRegex(score_curation.CurationLifecycleError, "final curation decision requires role curator"):
                score_curation.record_curator_decision(proposed, "accepted", "automation must not decide", actor_role=prohibited_role, actor_identity="automation", at=NOW)

        accepted = score_curation.record_curator_decision(proposed, "accepted", "Curator verified the pinned sources and selected the existing version.", actor_role="curator", actor_identity="human-curator", at=NOW)
        for prohibited_role in ("ai", "tool"):
            with self.subTest(prohibited_role=prohibited_role), self.assertRaisesRegex(score_curation.CurationLifecycleError, "application requires role curator"):
                score_curation.apply(accepted, {"record_version": "11111111"}, actor_role=prohibited_role, actor_identity="automation", at=NOW)

        applied = score_curation.apply(accepted, {"record_version": "11111111", "operation": "retain"}, actor_role="curator", actor_identity="human-curator", at=NOW)
        published = score_curation.publish(applied, {"generated_view": "score-design.html#dec_rec__infra__dev_tools"}, actor_role="tool", actor_identity="generate.py", at=NOW)
        item = json.loads(published.read_text(encoding="utf-8"))

        self.assertTrue(curation_item.is_conformant(item))
        self.assertEqual("applied", item["status"])
        self.assertEqual("published", item["lifecycle_state"])
        self.assertEqual(
            ["queued", "claimed", "proposed", "accepted", "applied", "published"],
            [entry["to"] for entry in item["history"]],
        )
        self.assertEqual("curator", item["decision"]["actor_role"])
        self.assertIn("/blob/", item["links"]["source"])
        self.assertEqual(2, len(item["links"]["versions"]))

    def test_rejected_path_is_retained_and_never_applied_or_published(self) -> None:
        queued = self._queued()
        claimed = score_curation.claim(queued, actor_role="ai", actor_identity="research-agent", at=NOW)
        proposed = score_curation.propose(claimed, {"resolution": "discard conflicting observation"}, actor_role="ai", actor_identity="research-agent", at=NOW)
        rejected = score_curation.record_curator_decision(proposed, "rejected", "The proposed resolution lacks source support.", actor_role="curator", actor_identity="human-curator", at=NOW)
        item = json.loads(rejected.read_text(encoding="utf-8"))

        self.assertTrue(rejected.is_file())
        self.assertIn("done", rejected.parts)
        self.assertTrue(curation_item.is_conformant(item))
        self.assertEqual(("rejected", "rejected"), (item["status"], item["lifecycle_state"]))
        self.assertNotIn("application", item)
        self.assertNotIn("publication", item)
        with self.assertRaisesRegex(score_curation.CurationLifecycleError, "expected lifecycle state 'accepted'"):
            score_curation.apply(rejected, {"operation": "must not happen"}, actor_role="curator", actor_identity="human-curator", at=NOW)
        with self.assertRaisesRegex(score_curation.CurationLifecycleError, "expected lifecycle state 'applied'"):
            score_curation.publish(rejected, {"generated_view": "must not happen"}, actor_role="tool", actor_identity="generate.py", at=NOW)

    def test_all_required_exception_classes_queue_as_canonical_items(self) -> None:
        required_kinds = ("unsupported", "ambiguous", "conflicting", "missing-provenance", "non-auto-verifiable")
        candidates = []
        for index, exception_kind in enumerate(required_kinds):
            item = candidate(exception_kind)
            item["candidate_id"] = f"score-normalization-exception:0019cafe{index:08d}"
            candidates.append(item)
        paths = score_curation.queue_candidates(candidates, self.queue, created=NOW)
        self.assertEqual(len(required_kinds), len(paths))
        for path, exception_kind in zip(paths, required_kinds):
            item = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(curation_item.is_conformant(item))
            self.assertEqual(exception_kind, item["current_state"]["exception_kind"])

    def test_only_supported_discovered_candidates_can_be_queued(self) -> None:
        unsupported = candidate("not-a-real-kind")
        with self.assertRaisesRegex(score_curation.CurationLifecycleError, "unsupported S-Core exception kind"):
            score_curation.queue_candidates([unsupported], self.queue, created=NOW)
        already_queued = candidate()
        already_queued["queue_written"] = True
        with self.assertRaisesRegex(score_curation.CurationLifecycleError, "discovered, unqueued"):
            score_curation.queue_candidates([already_queued], self.queue, created=NOW)
        self.assertFalse(self.queue.exists())

    def test_queueing_requires_a_passing_validation_report_bound_to_the_corpus(self) -> None:
        corpus = {"schema": "score-normalized-corpus@v1", "exception_candidates": [candidate()]}
        corpus_path = Path(self.temporary.name) / "corpus.json"
        report_path = Path(self.temporary.name) / "report.json"
        corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
        report_path.write_text(json.dumps({"schema": "score-validation-report@v1", "passed": True, "input": {"corpus_sha256": "wrong"}}), encoding="utf-8")
        with self.assertRaisesRegex(score_curation.CurationLifecycleError, "not bound"):
            score_curation.queue_validated_corpus(corpus_path, report_path, self.queue, created=NOW)

        digest = hashlib.sha256((json.dumps(corpus, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")).hexdigest()
        report_path.write_text(json.dumps({"schema": "score-validation-report@v1", "passed": True, "input": {"corpus_sha256": digest}}), encoding="utf-8")
        paths = score_curation.queue_validated_corpus(corpus_path, report_path, self.queue, created=NOW)
        self.assertEqual(1, len(paths))

    def test_user_facing_report_preserves_rejection_and_links_record_version_source(self) -> None:
        queued = self._queued()
        claimed = score_curation.claim(queued, actor_role="ai", actor_identity="research-agent", at=NOW)
        proposed = score_curation.propose(claimed, {"resolution": "discard"}, actor_role="ai", actor_identity="research-agent", at=NOW)
        score_curation.record_curator_decision(proposed, "rejected", "Curator rejects the unsupported proposal.", actor_role="curator", actor_identity="human-curator", at=NOW)

        original = (curation_report.SPEC, curation_report.RECORDS_CSV, curation_report.PAGE_MODEL, curation_report.DATASET_JSON)
        try:
            curation_report.SPEC = str(self.queue.parent)
            curation_report.RECORDS_CSV = str(Path(self.temporary.name) / "records.csv")
            curation_report.PAGE_MODEL = str(Path(self.temporary.name) / "page.json")
            curation_report.DATASET_JSON = str(Path(self.temporary.name) / "items.json")
            items = curation_report.collect_all_curation_items()
            self.assertEqual(1, len(items))
            self.assertEqual("rejected", items[0]["display_status"])
            curation_report.generate_curation_report_page(items)
            page = json.loads(Path(curation_report.PAGE_MODEL).read_text(encoding="utf-8"))
            markup = page["main"][0]["html"]
            self.assertIn("Record</a>", markup)
            self.assertIn("Version</a>", markup)
            self.assertIn("Source locator</a>", markup)
            self.assertIn("https://github.com/eclipse-score/score/blob/", markup)
            self.assertIn("rejected", markup)
        finally:
            curation_report.SPEC, curation_report.RECORDS_CSV, curation_report.PAGE_MODEL, curation_report.DATASET_JSON = original

    def test_feedback_recipe_handoff_curation_lifecycle_integration(self) -> None:
        """Verify that feedback-recipe-contract@v1 handoff ingests into curation-queue
        and progresses through AI claim/proposal and curator decision without mutating record bytes."""
        import feedback_recipe_contract as frc
        import curation_flags as cf_module

        # Redirect queue
        orig_queue = cf_module.QUEUE
        orig_open = cf_module.OPEN_DIR
        orig_claimed = cf_module.CLAIMED_DIR
        orig_done = cf_module.DONE_DIR
        cf_module.QUEUE = self.queue
        cf_module.OPEN_DIR = self.queue / "open"
        cf_module.CLAIMED_DIR = self.queue / "claimed"
        cf_module.DONE_DIR = self.queue / "done"

        # Redirect records and versions
        records_dir = Path(self.temporary.name) / "records"
        versions_dir = Path(self.temporary.name) / "versions"
        records_dir.mkdir(parents=True, exist_ok=True)
        versions_dir.mkdir(parents=True, exist_ok=True)

        rec_file = records_dir / "ECLIPSE/S-CORE/record" / "score_module.json"
        rec_file.parent.mkdir(parents=True, exist_ok=True)
        rec_data = {
            "id": "score_module",
            "canonical_id": "ECLIPSE/S-CORE/record/score_module",
            "status": {"state": "valid/published"},
            "version_id": "ECLIPSE/S-CORE/record/score_module@rel:v0.6.0#12345678",
            "target_content_hash": "12345678",
            "source_url": "https://github.com/eclipse-score/score/blob/v0.6.0/docs/module.md",
        }
        rec_bytes_initial = json.dumps(rec_data, indent=2).encode("utf-8")
        rec_file.write_bytes(rec_bytes_initial)

        payload_data = {"text": "Clarify S-Core module requirements", "suggested_change": "Update section"}
        payload_digest = hashlib.sha256((json.dumps(payload_data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")).hexdigest()

        handoff = {
            "schema": "feedback-recipe-contract@v1",
            "contract_version": "v1.0.0",
            "producer_repository": "2b-rs/agent-inbox",
            "producer_commit": "9776291cc5f02086db6be5830176301367ee565d",
            "consumer_baseline": "5c6068537aa4a304c940ca82f62b466a08d72136",
            "scheduling_decision_id": "dec-score-202",
            "assignment_id": "asg-recipe-202",
            "idempotence_key": "feedback:eclipse-score/score:issue-10:ECLIPSE/S-CORE/record/score_module",
            "normalized_input_digest": payload_digest,
            "status": "succeeded",
            "recipe_name": "feedback_ingestion",
            "trusted_envelope": {
                "schema": "github-event-envelope@v1",
                "event_id": "018f2e1a-9999-7c21-9a4e-2f6b1d8c9a01",
                "event_kind": "curation_feedback",
                "repository": "eclipse-score/score",
                "source_id": "issue-10",
                "record_id": "ECLIPSE/S-CORE/record/score_module",
                "record_version": "ECLIPSE/S-CORE/record/score_module@rel:v0.6.0#12345678",
                "sender": "contributor-bob",
                "created_at": NOW,
                "payload": payload_data,
            },
            "ingestion_result": {
                "schema": "feedback-ingestion-result@v1",
                "queue_item_id": "queue-item-score_module-018f2e1a",
                "queue_item_version": "v1.0.0",
                "deduplication_disposition": "new",
                "submitted_record_version": "ECLIPSE/S-CORE/record/score_module@rel:v0.6.0#12345678",
                "current_record_version": "ECLIPSE/S-CORE/record/score_module@rel:v0.6.0#12345678",
            },
            "durable_receipt": {
                "receipt_id": "rcpt-asg-recipe-202",
                "receipt_digest": "3b7d6e8b2c1f9a0e3d5b7c8a1e2f3d4c5b6a7e8f9a0b1c2d3e4f5a6b7c8d9e01",
                "recorded_at": NOW,
            },
            "retry_ancestry": [],
            "next_event": "proposal_scheduling_continuation:queue-item-score_module-018f2e1a",
            "error_details": None,
            "created_at": NOW,
        }

        try:
            report = frc.consume_feedback_recipe_handoff(
                handoff=handoff,
                apply=True,
                records_root=records_dir,
                versions_root=versions_dir,
                allowed_repositories=("eclipse-score/score",),
            )
            self.assertEqual(report["status"], frc.FeedbackConsumerOutcome.OK)
            self.assertFalse(report["target_record_mutated"])
            self.assertEqual(rec_file.read_bytes(), rec_bytes_initial)

            # Check committed queue flag
            queue_item_path = Path(report["queue_item_path"])
            self.assertTrue(queue_item_path.exists())
            flag_data = json.loads(queue_item_path.read_text(encoding="utf-8"))
            c_item = curation_item.from_curation_flag(flag_data)
            self.assertTrue(curation_item.is_conformant(c_item))
            self.assertEqual(c_item["status"], "open")
            self.assertEqual(c_item["canonical_id"], "ECLIPSE/S-CORE/record/score_module")
        finally:
            cf_module.QUEUE = orig_queue
            cf_module.OPEN_DIR = orig_open
            cf_module.CLAIMED_DIR = orig_claimed
            cf_module.DONE_DIR = orig_done


if __name__ == "__main__":
    unittest.main()
