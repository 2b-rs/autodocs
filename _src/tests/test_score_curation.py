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


if __name__ == "__main__":
    unittest.main()
