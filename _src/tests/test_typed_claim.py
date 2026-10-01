import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import typed_claim as tc  # noqa: E402


class TypedClaimTests(unittest.TestCase):
    def test_new_claim_has_expected_schema_and_fields(self):
        claim = tc.new_claim("artifact:abc", "hard_fact", "The API exposes X.")
        self.assertEqual(claim["schema"], "typed-claim@v1")
        for key in (
            "claim_id", "parent_artifact_id", "claim_type", "content",
            "evidence_refs", "dependency_refs", "current_confidence",
            "confidence_history", "invalidation",
            "dismissed_from_future_synthesis", "supersedes_claim_ids",
            "superseded_by_claim_ids", "created", "updated",
        ):
            self.assertIn(key, claim)

    def test_new_claim_rejects_unknown_claim_type(self):
        with self.assertRaises(ValueError):
            tc.new_claim("artifact:abc", "unknown", "x")

    def test_validate_claim_rejects_missing_field(self):
        claim = tc.new_claim("artifact:abc", "hard_fact", "x")
        del claim["content"]
        with self.assertRaises(ValueError):
            tc.validate_claim(claim)

    def test_append_confidence_is_append_only_and_updates_current_confidence(self):
        claim = tc.new_claim("artifact:abc", "ai_inferred", "x", current_confidence=0.2)
        tc.append_confidence(claim, 0.7, "cascade_invalidation", {"node": "n1"})
        self.assertEqual(len(claim["confidence_history"]), 1)
        self.assertEqual(claim["current_confidence"], 0.7)

    def test_mark_invalidated_sets_structured_invalidation_state(self):
        claim = tc.new_claim("artifact:abc", "curated_fact", "x")
        tc.mark_invalidated(claim, "source changed")
        self.assertTrue(claim["invalidation"]["invalidated"])
        self.assertEqual(claim["invalidation"]["reason"], "source changed")

    def test_dismiss_from_future_synthesis_sets_flag_without_removing_claim(self):
        claim = tc.new_claim("artifact:abc", "user_comment", "x")
        tc.dismiss_from_future_synthesis(claim)
        self.assertTrue(claim["dismissed_from_future_synthesis"])

    def test_link_supersession_updates_both_old_and_new_claims(self):
        old = tc.new_claim("artifact:a", "ai_inferred", "old")
        new = tc.new_claim("artifact:b", "ai_inferred", "new")
        tc.link_supersession(old, new)
        self.assertIn(old["claim_id"], new["supersedes_claim_ids"])
        self.assertIn(new["claim_id"], old["superseded_by_claim_ids"])

    def test_validate_claim_rejects_invalid_confidence_range(self):
        claim = tc.new_claim("artifact:abc", "hard_fact", "x")
        claim["current_confidence"] = 9.9
        with self.assertRaises(ValueError):
            tc.validate_claim(claim)

    def test_all_four_task_required_claim_types_are_supported(self):
        self.assertEqual(
            set(tc.VALID_CLAIM_TYPES),
            {"hard_fact", "curated_fact", "user_comment", "ai_inferred"},
        )

    def test_constructor_accepts_evidence_and_dependency_refs(self):
        claim = tc.new_claim(
            "artifact:abc", "hard_fact", "x",
            evidence_refs=["evidence:1", "curation:2"],
            dependency_refs=["version:3"],
        )
        self.assertEqual(claim["evidence_refs"], ["evidence:1", "curation:2"])
        self.assertEqual(claim["dependency_refs"], ["version:3"])


if __name__ == "__main__":
    unittest.main()
